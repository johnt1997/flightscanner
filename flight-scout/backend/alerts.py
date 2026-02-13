"""
Flight Scout Telegram Alerts - Daily deal notifications via Telegram Bot API.
Checks all active alerts weekly (Monday) using Everywhere search.
"""

import os
import requests
import threading
import time
from datetime import datetime, timedelta

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")

AIRPORTS = {
    "vie": {"id": "95673444", "name": "Wien", "code": "vie"},
    "bts": {"id": "95673445", "name": "Bratislava", "code": "bts"},
    "bud": {"id": "95673439", "name": "Budapest", "code": "bud"},
}


def send_telegram_message(chat_id: str, message: str) -> bool:
    if not TELEGRAM_BOT_TOKEN:
        print(f"[ALERT] Telegram nicht konfiguriert. Nachricht: {message[:80]}...")
        return False
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        resp = requests.post(url, json={"chat_id": chat_id, "text": message, "parse_mode": "HTML"}, timeout=10)
        if resp.status_code == 200:
            print(f"[ALERT] Telegram gesendet an {chat_id}")
            return True
        print(f"[ALERT] Telegram Fehler: {resp.status_code} {resp.text[:100]}")
        return False
    except Exception as e:
        print(f"[ALERT] Telegram Fehler: {e}")
        return False


def run_daily_alert_check():
    """Check all airports for public deals + send Telegram alerts to users with active alerts."""
    from database import get_all_active_deal_alerts, save_public_deals
    from scraper import SkyscannerAPI

    alerts = get_all_active_deal_alerts()

    # Group alerts by airport
    alerts_by_airport = {}
    for alert in alerts:
        ap = alert["airport"]
        if ap not in alerts_by_airport:
            alerts_by_airport[ap] = []
        alerts_by_airport[ap].append(alert)

    print(f"[ALERT] {len(alerts)} Alert(s), crawle alle {len(AIRPORTS)} Airports für Public Deals")

    # Check next 4 weekends (Fr-So)
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    weekends = []
    current = today
    while current.weekday() != 4:  # Find next Friday
        current += timedelta(days=1)
    for _ in range(4):
        friday = current
        sunday = friday + timedelta(days=2)
        weekends.append((friday, sunday))
        current += timedelta(days=7)

    # Collect public deals for all airports
    public_deals_by_airport = {}

    for airport_code, airport in AIRPORTS.items():
        scraper = SkyscannerAPI(
            origin_entity_id=airport["id"],
            adults=1,
            start_hour=0,
            origin_sky_code=airport["code"],
        )

        airport_alerts = alerts_by_airport.get(airport_code, [])

        for friday, sunday in weekends:
            data = scraper.search_flights(friday, sunday)
            if not data:
                continue

            results = data.get("everywhereDestination", {}).get("results", [])

            for result in results:
                if result.get("type") != "LOCATION":
                    continue
                content = result.get("content", {})
                location = content.get("location", {})
                fq = content.get("flightQuotes", {})
                if not fq:
                    continue
                raw_price = fq.get("cheapest", {}).get("rawPrice", 9999)
                city_name = location.get("name", "?")
                country_name = location.get("countryName", "")
                sky_code = location.get("skyCode", "")
                url = (
                    f"https://www.skyscanner.at/transport/fluge/{airport_code}/{sky_code.lower()}/"
                    f"{friday.strftime('%y%m%d')}/{sunday.strftime('%y%m%d')}/"
                    f"?adultsv2=1&cabinclass=economy&rtn=1&preferdirects=true"
                )

                # Collect for public deals (under 100€)
                if raw_price <= 100:
                    if airport_code not in public_deals_by_airport:
                        public_deals_by_airport[airport_code] = []
                    public_deals_by_airport[airport_code].append({
                        "city": city_name, "country": country_name, "price": raw_price,
                        "departure_date": friday.strftime("%Y-%m-%d"), "return_date": sunday.strftime("%Y-%m-%d"),
                        "url": url, "sky_code": sky_code,
                    })

                # Send Telegram alerts for matching user alerts
                for alert in airport_alerts:
                    if raw_price <= alert["max_price"]:
                        if not hasattr(alert, '_deals'):
                            alert['_deals'] = []
                        alert['_deals'].append({"city": city_name, "price": raw_price, "url": url,
                                                "date_str": f"{friday.strftime('%d.%m.')} – {sunday.strftime('%d.%m.')}"})

            time.sleep(1)  # Pause between weekends

    # Send Telegram messages for user alerts
    for airport_code, airport_alerts in alerts_by_airport.items():
        airport = AIRPORTS.get(airport_code)
        if not airport:
            continue
        for alert in airport_alerts:
            deals = alert.get('_deals', [])
            if not deals:
                continue
            deals.sort(key=lambda x: x["price"])
            chat_id = alert["telegram_chat_id"]
            max_price = alert["max_price"]
            # Group by date
            by_date = {}
            for d in deals:
                by_date.setdefault(d["date_str"], []).append(d)
            for date_str, date_deals in by_date.items():
                lines = [f"✈️ <b>Flight Scout Alert</b> — {date_str}\nAb {airport['name']}, unter {max_price:.0f}€:\n"]
                for d in date_deals[:10]:
                    lines.append(f"• <b>{d['city']}</b> {d['price']:.0f}€ — <a href=\"{d['url']}\">Buchen</a>")
                send_telegram_message(chat_id, "\n".join(lines))

    # Deduplicate public deals (keep cheapest per city per airport) and save
    for ap_code in public_deals_by_airport:
        seen = {}
        for d in sorted(public_deals_by_airport[ap_code], key=lambda x: x["price"]):
            key = d["city"]
            if key not in seen:
                seen[key] = d
        public_deals_by_airport[ap_code] = list(seen.values())

    save_public_deals(public_deals_by_airport)
    total = sum(len(v) for v in public_deals_by_airport.values())
    print(f"[ALERT] {total} Public Deals gespeichert für {len(public_deals_by_airport)} Airport(s)")


def start_alert_scheduler():
    """Start background thread that runs alert check weekly on Monday at 7:00 UTC (8:00 Wien)."""
    def scheduler_loop():
        while True:
            now = datetime.utcnow()
            # Next Monday at 7:00 UTC
            days_until_monday = (7 - now.weekday()) % 7  # 0=Monday
            if days_until_monday == 0 and now.hour >= 7:
                days_until_monday = 7
            next_run = (now + timedelta(days=days_until_monday)).replace(hour=7, minute=0, second=0, microsecond=0)
            wait_seconds = (next_run - now).total_seconds()
            print(f"[ALERT] Nächster Check: {next_run.strftime('%Y-%m-%d %H:%M')} UTC (Montag, in {wait_seconds/3600:.1f}h)")
            time.sleep(wait_seconds)
            try:
                run_daily_alert_check()
            except Exception as e:
                print(f"[ALERT] Fehler beim wöchentlichen Check: {e}")

    thread = threading.Thread(target=scheduler_loop, daemon=True)
    thread.start()
    print("[ALERT] Scheduler gestartet")
