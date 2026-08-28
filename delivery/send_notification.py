"""
Kezih Delivery — Telegram Bot
------------------------------
Sends a welcome message when a user clicks "Start" (/start command)
and logs every user's chat_id (no database writes — just logging,
either to console or a log file).

Requirements:
    pip install python-telegram-bot==21.*

Run:
    export KEZIH_BOT_TOKEN="your-bot-token-here"
    python kezih_telegram_bot.py
"""

import os
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# --------------------------------------------------------------------------
# Logging setup — logs to both console and a file (chat_ids.log)
# --------------------------------------------------------------------------
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("chat_ids.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")  # set this in your environment / .env

WELCOME_MESSAGE = (
    "👋 Welcome to Kezih Delivery!\n\n"
    "Order food from your favorite restaurants and get it delivered "
    "right to your door. Tap the menu button below to get started."
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start — send welcome message and log the user's chat_id."""
    chat = update.effective_chat
    user = update.effective_user

    chat_id = chat.id
    username = user.username or "N/A"
    first_name = user.first_name or ""
    last_name = user.last_name or ""

    logger.info(
        "New /start — chat_id=%s username=%s name=%s %s",
        chat_id, username, first_name, last_name,
    )

    await context.bot.send_message(chat_id=chat_id, text=WELCOME_MESSAGE)


async def debug_all(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Catches EVERY update so you can confirm Telegram is reaching this bot at all."""
    logger.info("RAW UPDATE RECEIVED: %s", update.to_dict())


def main() -> None:
    if not BOT_TOKEN:
        raise RuntimeError("Set the TELEGRAM_BOT_TOKEN environment variable before running the bot.")

    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.ALL, debug_all), group=1)

    logger.info("Kezih Delivery bot is starting (polling)...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
