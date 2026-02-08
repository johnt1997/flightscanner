"""
Flight Scout Telegram Alerts - Sends price notifications via Telegram Bot API.
"""

import requests
from database import get_all_active_alerts

TELEGRAM_BOT_TOKEN = "PLACEHOLDER_BOT_TOKEN"


def send_telegram_message(chat_id: str, message: str) -> bool:
    if TELEGRAM_BOT_TOKEN == "PLACEHOLDER_BOT_TOKEN":
        print(f"[Alert] Telegram not configured. Would send to {chat_id}: {message}")
        return False
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        resp = requests.post(url, json={"chat_id": chat_id, "text": message, "parse_mode": "HTML"}, timeout=10)
        return resp.status_code == 200
    except Exception as e:
        print(f"[Alert] Telegram send error: {e}")
        return False


def check_alerts(deals: list[dict]):
    alerts = get_all_active_alerts()
    if not alerts:
        return

    for alert in alerts:
        dest_city = alert["destination_city"].lower()
        max_price = alert["max_price"]
        chat_id = alert["telegram_chat_id"]

        matching = [
            d for d in deals
            if d.get("city", "").lower() == dest_city and d.get("price", 9999) <= max_price
        ]

        if matching:
            cheapest = min(matching, key=lambda x: x["price"])
            msg = (
                f"<b>Flight Scout Alert!</b>\n"
                f"{cheapest['city']} ({cheapest.get('country', '')})\n"
                f"Preis: <b>{cheapest['price']:.0f}€</b>\n"
                f"Datum: {cheapest.get('departure_date', '?')} – {cheapest.get('return_date', '?')}\n"
                f"Ab: {cheapest.get('origin', '?')}\n"
                f"<a href=\"{cheapest.get('url', '')}\">Buchen</a>"
            )
            send_telegram_message(chat_id, msg)
