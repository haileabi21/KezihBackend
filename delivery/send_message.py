from environ import Env
import requests

env = Env()

Env.read_env()

TELEGRAM_BOT_TOKEN    = env("TELEGRAM_BOT_TOKEN")     # customer-facing bot
TELEGRAM_PORTAL_TOKEN = env("TELEGRAM_PORTAL_TOKEN")  # delivery portal bot


def send_telegram_message(message: str, chat_id: str, use_portal_bot: bool = False):
    """
    Send a Telegram message using the appropriate bot token.

    Args:
        message:         The text to send (Markdown formatted).
        chat_id:         Recipient's Telegram chat ID.
        use_portal_bot:  If True, send via TELEGRAM_PORTAL_TOKEN (delivery staff).
                         If False (default), send via TELEGRAM_BOT_TOKEN (customers).
    """
    token = TELEGRAM_PORTAL_TOKEN if use_portal_bot else TELEGRAM_BOT_TOKEN
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown",
    }
    response = requests.post(url, data=payload)
    if response.status_code != 200:
        print(f"Failed to send message: {response.text}")
    return response.json()
