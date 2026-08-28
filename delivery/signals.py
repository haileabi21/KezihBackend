from django.db.models import F
from django.db.models.signals import post_save
from django.dispatch import receiver
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from .models import Order, Giveaway, Profile, GIVEAWAY_TARGET
from .serializers import GiveawaySerializer

from django.db.models import F


@receiver(post_save, sender=Order)
def grant_spin_chance_on_delivery(sender, instance, **kwargs):
    if instance.status != "delivered" or instance.spin_chance_granted:
        return
    Order.objects.filter(pk=instance.pk).update(spin_chance_granted=True)
    Profile.objects.filter(pk=instance.owner_id).update(
        available_spins=F("available_spins") + 1
    )

@receiver(post_save, sender=Order)
def order_giveaway_processor(sender, instance, created, **kwargs):
    """
    Every delivered order counts toward the *owning customer's own*
    progress bar, not a shared pool. The moment a single customer's
    delivered-order count (since their last win) reaches GIVEAWAY_TARGET,
    they win automatically — no pooling across customers, no randomness.
    """
    if instance.status != "delivered" or instance.counted_for_giveaway:
        return

    # Mark counted first so re-saves of this same order (e.g. attaching a
    # payment screenshot after delivery) never double-count it.
    Order.objects.filter(pk=instance.pk).update(counted_for_giveaway=True)

    profile = instance.owner
    Profile.objects.filter(pk=profile.pk).update(
        giveaway_progress=F("giveaway_progress") + 1
    )
    profile.refresh_from_db(fields=["giveaway_progress", "giveaway_wins_count"])

    winner_announced = None

    # 2. Check threshold — this customer alone, not a shared pool
    if profile.giveaway_progress >= GIVEAWAY_TARGET:
        recent_orders = Order.objects.filter(
            owner=profile, counted_for_giveaway=True
        ).order_by("-created_at")[:GIVEAWAY_TARGET]

        giveaway = Giveaway.objects.create(
            winner=profile,
            milestone=(profile.giveaway_wins_count + 1) * GIVEAWAY_TARGET,
        )
        giveaway.delivered_orders.set(list(recent_orders))

        Profile.objects.filter(pk=profile.pk).update(
            giveaway_progress=0,
            giveaway_wins_count=F("giveaway_wins_count") + 1,
        )
        profile.refresh_from_db(fields=["giveaway_progress", "giveaway_wins_count"])

        winner_announced = {
            "name": profile.name or profile.user.username,
            "phone": profile.phone or "",
            "price": giveaway.price,
            "milestone": giveaway.milestone,
        }

    # 3. Gather payload for real-time push
    history = Giveaway.objects.order_by("-completed_at")[:5]
    history_data = GiveawaySerializer(history, many=True).data

    payload = {
        "winner_announced": winner_announced,
        "history": history_data,
    }

    # 4. Broadcast outside consumer using Channel Layer
    channel_layer = get_channel_layer()
    # Must match the group name your OrderConsumer joins for giveaway updates
    async_to_sync(channel_layer.group_send)(
        "giveaway_updates",
        {
            "type": "giveaway_update",
            "data": payload,
        },
    )
