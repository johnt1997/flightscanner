#!/usr/bin/env python3
"""
Skyscanner Weekend Flight Scraper - API Version & PDF Report
(Refactored for FastAPI integration)
"""

import requests
import json
import uuid
import random
import os
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict, field
from typing import Optional
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from fpdf import FPDF

PDF_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pdfs")
os.makedirs(PDF_DIR, exist_ok=True)

USER_AGENTS = [
    ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
     '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"'),
    ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
     '"Chromium";v="135", "Google Chrome";v="135", "Not.A/Brand";v="99"'),
    ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
     '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"'),
    ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36 Edg/136.0.0.0",
     '"Chromium";v="136", "Microsoft Edge";v="136", "Not.A/Brand";v="99"'),
    ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
     '"Chromium";v="135", "Google Chrome";v="135", "Not.A/Brand";v="99"'),
]

# City database: entity_id, sky_code, country, lat, lon
CITY_DATABASE = {
    # Italien (verifiziert ✓)
    "Mailand":    {"entity_id": "27544068", "sky_code": "mila", "country": "Italien", "lat": 45.4642, "lon": 9.1900},
    "Rom":        {"entity_id": "27539793", "sky_code": "rome", "country": "Italien", "lat": 41.9028, "lon": 12.4964},
    "Bologna":    {"entity_id": "27539470", "sky_code": "bolo", "country": "Italien", "lat": 44.4949, "lon": 11.3426},
    "Venedig":    {"entity_id": "27547373", "sky_code": "veni", "country": "Italien", "lat": 45.4408, "lon": 12.3155},
    "Neapel":     {"entity_id": "27545086", "sky_code": "napl", "country": "Italien", "lat": 40.8518, "lon": 14.2681},
    "Catania":    {"entity_id": "27540562", "sky_code": "cata", "country": "Italien", "lat": 37.5079, "lon": 15.0830},
    "Palermo":    {"entity_id": "27545989", "sky_code": "pale", "country": "Italien", "lat": 38.1157, "lon": 13.3615},
    "Bari":       {"entity_id": "27539556", "sky_code": "bari", "country": "Italien", "lat": 41.1171, "lon": 16.8719},
    "Pisa":       {"entity_id": "27546040", "sky_code": "pisa", "country": "Italien", "lat": 43.7228, "lon": 10.4017},
    "Turin":      {"entity_id": "27547248", "sky_code": "turi", "country": "Italien", "lat": 45.0703, "lon": 7.6869},
    "Lamezia Terme": {"entity_id": "27546311", "sky_code": "mara", "country": "Italien", "lat": 38.9684, "lon": 16.3096},
    "Trapani":    {"entity_id": "27547239", "sky_code": "trap", "country": "Italien", "lat": 38.0174, "lon": 12.5365},
    # Spanien (verifiziert ✓)
    "Barcelona":  {"entity_id": "27548283", "sky_code": "barc", "country": "Spanien", "lat": 41.3851, "lon": 2.1734},
    "Madrid":     {"entity_id": "27544850", "sky_code": "madr", "country": "Spanien", "lat": 40.4168, "lon": -3.7038},
    "Malaga":     {"entity_id": "27547484", "sky_code": "mala", "country": "Spanien", "lat": 36.7213, "lon": -4.4217},
    "Palma de Mallorca": {"entity_id": "27545988", "sky_code": "palm", "country": "Spanien", "lat": 39.5696, "lon": 2.6502},
    # UK & Irland (verifiziert ✓)
    "London":     {"entity_id": "27544008", "sky_code": "lond", "country": "Vereinigtes Königreich", "lat": 51.5074, "lon": -0.1278},
    "Edinburgh":  {"entity_id": "27540851", "sky_code": "edin", "country": "Vereinigtes Königreich", "lat": 55.9533, "lon": -3.1883},
    "Manchester": {"entity_id": "27544856", "sky_code": "manc", "country": "Vereinigtes Königreich", "lat": 53.4808, "lon": -2.2426},
    "Liverpool":  {"entity_id": "27544132", "sky_code": "live", "country": "Vereinigtes Königreich", "lat": 53.4084, "lon": -2.9916},
    "Newcastle upon Tyne": {"entity_id": "27545092", "sky_code": "newc", "country": "Vereinigtes Königreich", "lat": 54.9783, "lon": -1.6178},
    "Dublin":     {"entity_id": "27540823", "sky_code": "dubl", "country": "Irland", "lat": 53.3498, "lon": -6.2603},
    # Frankreich (verifiziert ✓)
    "Paris":      {"entity_id": "27539733", "sky_code": "pari", "country": "Frankreich", "lat": 48.8566, "lon": 2.3522},
    # Benelux (verifiziert ✓)
    "Amsterdam":  {"entity_id": "27536561", "sky_code": "amst", "country": "Niederlande", "lat": 52.3676, "lon": 4.9041},
    "Brüssel":    {"entity_id": "27539565", "sky_code": "brus", "country": "Belgien", "lat": 50.8503, "lon": 4.3517},
    # Skandinavien (verifiziert ✓)
    "Kopenhagen": {"entity_id": "27539902", "sky_code": "cope", "country": "Dänemark", "lat": 55.6761, "lon": 12.5683},
    "Stockholm":  {"entity_id": "27539477", "sky_code": "stoc", "country": "Schweden", "lat": 59.3293, "lon": 18.0686},
    "Riga":       {"entity_id": "27546172", "sky_code": "riga", "country": "Lettland", "lat": 56.9496, "lon": 24.1052},
    "Vilnius":    {"entity_id": "27547414", "sky_code": "viln", "country": "Litauen", "lat": 54.6872, "lon": 25.2797},
    "Oslo":       {"entity_id": "27538634", "sky_code": "oslo", "country": "Norwegen", "lat": 59.9139, "lon": 10.7522},
    "Helsinki":   {"entity_id": "27542027", "sky_code": "hels", "country": "Finnland", "lat": 60.1699, "lon": 24.9384},
    # Griechenland & Türkei (verifiziert ✓)
    "Athen":      {"entity_id": "27548174", "sky_code": "athe", "country": "Griechenland", "lat": 37.9838, "lon": 23.7275},
    "Thessaloniki": {"entity_id": "27546367", "sky_code": "thes", "country": "Griechenland", "lat": 40.6401, "lon": 22.9444},
    "Istanbul":   {"entity_id": "27542903", "sky_code": "ista", "country": "Türkei", "lat": 41.0082, "lon": 28.9784},
    "Antalya":    {"entity_id": "27548233", "sky_code": "anta", "country": "Türkei", "lat": 36.8969, "lon": 30.7133},
    # Balkan (verifiziert ✓)
    "Tirana":     {"entity_id": "27547183", "sky_code": "tira", "country": "Albanien", "lat": 41.3275, "lon": 19.8187},
    "Belgrad":    {"entity_id": "27538720", "sky_code": "beli", "country": "Serbien", "lat": 44.7866, "lon": 20.4489},
    "Bukarest":   {"entity_id": "27545262", "sky_code": "buch", "country": "Rumänien", "lat": 44.4268, "lon": 26.1025},
    "Sofia":      {"entity_id": "27547055", "sky_code": "sofi", "country": "Bulgarien", "lat": 42.6977, "lon": 23.3219},
    "Zagreb":     {"entity_id": "27537474", "sky_code": "zagr", "country": "Kroatien", "lat": 45.8150, "lon": 15.9819},
    "Split":      {"entity_id": "27547071", "sky_code": "spli", "country": "Kroatien", "lat": 43.5081, "lon": 16.4402},
    "Dubrovnik":  {"entity_id": "39377069", "sky_code": "dubr", "country": "Kroatien", "lat": 42.6507, "lon": 18.0944},
    "Sarajevo":   {"entity_id": "27546359", "sky_code": "sara", "country": "Bosnien und Herzegowina", "lat": 43.8563, "lon": 18.4131},
    "Podgorica":  {"entity_id": "27547166", "sky_code": "podg", "country": "Montenegro", "lat": 42.4304, "lon": 19.2594},
    "Skopje":     {"entity_id": "27546371", "sky_code": "skop", "country": "Nordmazedonien", "lat": 41.9981, "lon": 21.4254},
    "Košice":     {"entity_id": "27543810", "sky_code": "kosi", "country": "Slowakei", "lat": 48.7164, "lon": 21.2611},
    "Ljubljana":  {"entity_id": "27544078", "sky_code": "ljub", "country": "Slowenien", "lat": 46.0569, "lon": 14.5058},
    # Osteuropa (verifiziert ✓)
    "Prag":       {"entity_id": "27546033", "sky_code": "prag", "country": "Tschechische Republik", "lat": 50.0755, "lon": 14.4378},
    "Warschau":   {"entity_id": "27547454", "sky_code": "wars", "country": "Polen", "lat": 52.2297, "lon": 21.0122},
    "Krakau":     {"entity_id": "27543787", "sky_code": "krak", "country": "Polen", "lat": 50.0647, "lon": 19.9450},
    "Danzig":     {"entity_id": "27541787", "sky_code": "gada", "country": "Polen", "lat": 54.3520, "lon": 18.6466},
    "Breslau":    {"entity_id": "27536248", "sky_code": "wroc", "country": "Polen", "lat": 51.1079, "lon": 17.0385},
    "Kattowitz":  {"entity_id": "27543914", "sky_code": "kato", "country": "Polen", "lat": 50.2649, "lon": 19.0238},
    # Portugal (verifiziert ✓)
    "Lissabon":   {"entity_id": "27544072", "sky_code": "lisb", "country": "Portugal", "lat": 38.7223, "lon": -9.1393},
    # Nordafrika (verifiziert ✓)
    "Marrakesch": {"entity_id": "27546125", "sky_code": "marr", "country": "Marokko", "lat": 31.6295, "lon": -7.9811},
    "Kairo":      {"entity_id": "27539681", "sky_code": "cair", "country": "Ägypten", "lat": 30.0444, "lon": 31.2357},
    # Kaukasus
    "Kutaissi":   {"entity_id": "27543929", "sky_code": "kuta", "country": "Georgien", "lat": 42.2679, "lon": 42.6946},
    # Sonstige
    "Reykjavik":  {"entity_id": "27543786", "sky_code": "reyk", "country": "Island", "lat": 64.1466, "lon": -21.9426},
    "Malta":      {"entity_id": "33350111", "sky_code": "mlaa", "country": "Malta", "lat": 35.8989, "lon": 14.5146},
}



@dataclass
class FlightDeal:
    city: str
    country: str
    price: float
    departure_date: str
    return_date: str
    is_direct: bool = False
    url: str = ""
    flight_time: str = ""
    return_flight_time: str = ""
    origin: str = ""  # Neues Feld für multi-airport support
    latitude: float = 0.0
    longitude: float = 0.0
    early_departure: bool = False  # True = Abflug vor gewünschter Uhrzeit
    alternatives: list = field(default_factory=list)  # Weitere Flugoptionen


class FlightReport(FPDF):
    def header(self):
        if self.page_no() > 1:
            self.set_font('Helvetica', 'I', 8)
            self.set_text_color(128)
            self.cell(0, 10, 'Flight Scout Report - Seite ' + str(self.page_no()), 0, 0, 'R')
            self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(128)
        self.cell(0, 10, f'Erstellt am {datetime.now().strftime("%d.%m.%Y")} | Flight Scout', 0, 0, 'C')


def create_pdf_report(deals: list[FlightDeal], origin: str, filename="Flight_Report.pdf"):
    if not deals:
        return

    total_deals = len(deals)
    cheapest_deal = min(deals, key=lambda x: x.price)
    avg_price = sum(d.price for d in deals) / total_deals

    countries = {}
    for d in deals:
        countries[d.country] = countries.get(d.country, 0) + 1

    pdf = FlightReport()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    COLOR_PRIMARY = (99, 102, 241)  # Indigo
    COLOR_BG = (30, 41, 59)
    COLOR_TEXT = (248, 250, 252)
    COLOR_GREEN = (34, 197, 94)

    pdf.set_font("Helvetica", "B", 24)
    pdf.set_text_color(*COLOR_PRIMARY)
    pdf.cell(0, 15, "Flight Scout Report", 0, 1, "L")

    pdf.set_font("Helvetica", "", 12)
    pdf.set_text_color(100)
    pdf.cell(0, 10, f"Abflug von: {origin}", 0, 1, "L")
    pdf.ln(5)

    pdf.set_font("Helvetica", "B", 10)

    def draw_stat_box(x, label, value, value_color=COLOR_TEXT):
        pdf.set_xy(x, 45)
        pdf.set_fill_color(241, 245, 249)
        pdf.rect(x, 45, 60, 25, 'F')
        pdf.set_xy(x + 2, 48)
        pdf.set_text_color(100)
        pdf.cell(56, 5, label, 0, 1, 'C')
        pdf.set_xy(x + 2, 58)
        pdf.set_font("Helvetica", "B", 14)
        pdf.set_text_color(*value_color)
        pdf.cell(56, 5, value, 0, 1, 'C')

    draw_stat_box(10, "Guenstigster", f"{cheapest_deal.price:.0f} EUR", COLOR_GREEN)
    draw_stat_box(75, "Durchschnitt", f"{avg_price:.0f} EUR", (100, 100, 100))
    draw_stat_box(140, "Gefunden", f"{total_deals} Deals", COLOR_PRIMARY)

    pdf.ln(35)

    pdf.set_fill_color(*COLOR_PRIMARY)
    pdf.set_text_color(255)
    pdf.set_font("Helvetica", "B", 9)

    col_w = [25, 20, 20, 20, 40, 35, 30]

    pdf.cell(col_w[0], 10, "Datum", 1, 0, 'C', True)
    pdf.cell(col_w[1], 10, "Ab", 1, 0, 'C', True)
    pdf.cell(col_w[2], 10, "Hin", 1, 0, 'C', True)
    pdf.cell(col_w[3], 10, "Rueck", 1, 0, 'C', True)
    pdf.cell(col_w[4], 10, "Stadt", 1, 0, 'L', True)
    pdf.cell(col_w[5], 10, "Land", 1, 0, 'L', True)
    pdf.cell(col_w[6], 10, "Preis", 1, 1, 'C', True)

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(60)

    fill = False
    sorted_deals = sorted(deals, key=lambda x: x.price)

    for deal in sorted_deals[:50]:  # Max 50 im PDF
        try:
            date_obj = datetime.strptime(deal.departure_date, "%Y-%m-%d")
            date_nice = date_obj.strftime("%d.%m.")
        except:
            date_nice = deal.departure_date

        if fill:
            pdf.set_fill_color(248, 250, 252)
        else:
            pdf.set_fill_color(255, 255, 255)

        is_cheap = deal.price < 40
        pdf.set_font("Helvetica", "B" if is_cheap else "", 9)

        city_clean = deal.city.encode('latin-1', 'replace').decode('latin-1')[:20]
        country_clean = deal.country.encode('latin-1', 'replace').decode('latin-1')[:18]
        origin_short = getattr(deal, 'origin', '')[:3].upper() or "???"

        return_time = getattr(deal, 'return_flight_time', '??:??') or '??:??'

        pdf.cell(col_w[0], 8, date_nice, "LR", 0, 'C', fill)
        pdf.cell(col_w[1], 8, origin_short, "LR", 0, 'C', fill)
        flight_time_str = deal.flight_time or "??:??"
        if deal.early_departure:
            flight_time_str = f"*{flight_time_str}"
        pdf.cell(col_w[2], 8, flight_time_str, "LR", 0, 'C', fill)
        pdf.cell(col_w[3], 8, return_time, "LR", 0, 'C', fill)
        pdf.cell(col_w[4], 8, city_clean, "LR", 0, 'L', fill)
        pdf.cell(col_w[5], 8, country_clean, "LR", 0, 'L', fill)

        if is_cheap:
            pdf.set_text_color(*COLOR_GREEN)
        else:
            pdf.set_text_color(60)
        pdf.cell(col_w[6], 8, f"{deal.price:.0f} EUR", "LR", 1, 'C', fill, link=deal.url)

        pdf.set_text_color(60)
        fill = not fill

    pdf.cell(sum(col_w), 0, '', 'T')
    pdf.output(filename)


# Proxy configuration: file first, then env var fallback
PROXY_URLS = []
_proxy_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "proxies_europe.txt")
if os.path.isfile(_proxy_file):
    with open(_proxy_file, "r") as _f:
        for _line in _f:
            _line = _line.strip()
            if not _line:
                continue
            _parts = _line.split(":")
            if len(_parts) == 4:
                _host, _port, _user, _pw = _parts
                PROXY_URLS.append(f"http://{_user}:{_pw}@{_host}:{_port}")
    print(f"[PROXY] {len(PROXY_URLS)} Proxy(s) aus proxies_europe.txt geladen")
else:
    _proxy_env = os.environ.get("PROXY_URL", "")
    if _proxy_env:
        PROXY_URLS = [p.strip() for p in _proxy_env.split(",") if p.strip()]
        print(f"[PROXY] {len(PROXY_URLS)} Proxy(s) aus Umgebungsvariable")


class SkyscannerAPI:
    API_URL = "https://www.skyscanner.at/g/radar/api/v2/web-unified-search/"
    MAX_PRICE = 70
    BLACKLIST_COUNTRIES: list[str] = []  # Leer = keine ausgeschlossen

    EASTER_START = datetime(2026, 3, 28)
    EASTER_END = datetime(2026, 4, 6)

    def __init__(self, origin_entity_id="95673444", adults=1, start_hour=14, origin_sky_code="vie", max_return_hour=23):
        self.session = requests.Session()
        self.traveller_context = str(uuid.uuid4())
        self.view_id = str(uuid.uuid4())
        self.VIENNA_ENTITY_ID = origin_entity_id
        self.ORIGIN_SKY_CODE = origin_sky_code.lower()
        self._apply_proxy()
        self._setup_session()
        self.ADULTS = adults
        self.START_HOUR = start_hour
        self.MAX_RETURN_HOUR = max_return_hour
        self.deals: list[FlightDeal] = []
        self._is_blocked = False

    def _apply_proxy(self):
        """Apply a random proxy from the configured list."""
        if PROXY_URLS:
            proxy_url = random.choice(PROXY_URLS)
            self.session.proxies = {
                "http": proxy_url,
                "https": proxy_url,
            }
            print(f"  [PROXY] Verwende Proxy")

    def _is_proxy_error(self, exc):
        """Check if an exception is a proxy connectivity/auth error."""
        msg = str(exc).lower()
        return "proxyerror" in msg or "407" in msg or "tunnel connection failed" in msg

    def _setup_session(self, max_proxy_retries=5):
        # Komplett neue Session mit frischen IDs
        for attempt in range(max_proxy_retries):
            self.session = requests.Session()
            self._apply_proxy()
            self.traveller_context = str(uuid.uuid4())
            self.view_id = str(uuid.uuid4())
            ua, sec_ch_ua = random.choice(USER_AGENTS)
            platform = '"macOS"' if 'Macintosh' in ua else '"Windows"'

            # Schritt 1: Homepage besuchen wie ein echter Browser
            browser_headers = {
                "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                "accept-encoding": "gzip, deflate, br, zstd",
                "accept-language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
                "cache-control": "max-age=0",
                "sec-ch-ua": sec_ch_ua,
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": platform,
                "sec-fetch-dest": "document",
                "sec-fetch-mode": "navigate",
                "sec-fetch-site": "none",
                "sec-fetch-user": "?1",
                "upgrade-insecure-requests": "1",
                "user-agent": ua,
            }
            try:
                self.session.get("https://www.skyscanner.at/", timeout=15, headers=browser_headers)
                time.sleep(random.uniform(1.5, 3.0))

                # Schritt 2: Flugsuche-Seite besuchen (simuliert echten Nutzer)
                browser_headers["referer"] = "https://www.skyscanner.at/"
                browser_headers["sec-fetch-site"] = "same-origin"
                self.session.get(
                    "https://www.skyscanner.at/transport/fluge/vie/?adultsv2=1&cabinclass=economy",
                    timeout=15, headers=browser_headers
                )
                time.sleep(random.uniform(1.0, 2.5))
                break  # Warmup OK
            except Exception as e:
                if self._is_proxy_error(e) and attempt < max_proxy_retries - 1:
                    print(f"  [SESSION] Proxy-Fehler, versuche anderen Proxy... ({attempt + 1}/{max_proxy_retries})")
                    continue
                print(f"  [SESSION] Warmup-Fehler: {e}")

        # Schritt 3: API-Headers setzen (jetzt mit echten Cookies)
        self.session.headers.update({
            "accept": "application/json",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
            "content-type": "application/json",
            "origin": "https://www.skyscanner.at",
            "referer": "https://www.skyscanner.at/transport/fluge/vie/?adultsv2=1&cabinclass=economy",
            "sec-ch-ua": sec_ch_ua,
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": platform,
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": ua,
            "x-radar-combined-explore-generic-results": "1",
            "x-radar-combined-explore-unfocused-locations-use-real-data": "1",
            "x-skyscanner-channelid": "website",
            "x-skyscanner-currency": "EUR",
            "x-skyscanner-locale": "de-DE",
            "x-skyscanner-market": "AT",
            "x-skyscanner-traveller-context": f"{self.traveller_context};1",
            "x-skyscanner-viewid": self.view_id,
        })
        print(f"  [SESSION] Neue Session bereit (Cookies: {len(self.session.cookies)})")

    def generate_trips(self, start_date: datetime, end_date: datetime, start_weekday: int, duration: int) -> list[tuple[datetime, datetime]]:
        trips = []
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        current = start_date
        while current.weekday() != start_weekday:
            current += timedelta(days=1)
        while current <= end_date:
            dep = current
            ret = dep + timedelta(days=duration)
            if ret <= end_date and dep >= today:
                trips.append((dep, ret))
            current += timedelta(days=7)
        return trips

    def is_easter_period(self, date: datetime) -> bool:
        return self.EASTER_START <= date <= self.EASTER_END

    def build_flight_url(self, sky_code: str, departure: datetime, return_date: datetime) -> str:
        dep_str = departure.strftime("%y%m%d")
        ret_str = return_date.strftime("%y%m%d")
        start_minutes = self.START_HOUR * 60
        return (
            f"https://www.skyscanner.at/transport/fluge/{self.ORIGIN_SKY_CODE}/{sky_code.lower()}/"
            f"{dep_str}/{ret_str}/"
            f"?adultsv2={self.ADULTS}&cabinclass=economy&rtn=1"
            f"&preferdirects=true&departure-times={start_minutes}-1439"
        )

    def _retry_on_403(self, make_request, label="API", cancel_check=None):
        """Gemeinsame 403-Retry-Logik mit Wartezeiten"""
        # Proxy-Fehler: sofort neuen Proxy probieren (max 5x)
        for proxy_attempt in range(5):
            try:
                response = make_request()
                break
            except Exception as e:
                if self._is_proxy_error(e) and proxy_attempt < 4:
                    print(f"  [{label}] Proxy-Fehler, wechsle Proxy... ({proxy_attempt + 1}/5)")
                    self._setup_session()
                    continue
                raise
        else:
            return response

        if response.status_code != 403:
            return response

        for retry_wait in [30, 60]:
            if cancel_check and cancel_check():
                print(f"  [{label}] Abbruch während Retry")
                return response
            print(f"  [{label}] 403 BLOCKED - Warte {retry_wait}s, neue Session...")
            for _ in range(retry_wait):
                if cancel_check and cancel_check():
                    print(f"  [{label}] Abbruch während Warten")
                    return response
                time.sleep(1)
            self._setup_session()
            time.sleep(random.uniform(2, 4))
            try:
                response = make_request()
            except Exception as e:
                if self._is_proxy_error(e):
                    print(f"  [{label}] Proxy-Fehler beim Retry, neue Session...")
                    self._setup_session()
                    continue
                raise
            print(f"  [{label}] Retry -> HTTP {response.status_code}")
            if response.status_code != 403:
                self._is_blocked = False
                return response

        return response

    def search_flights(self, departure: datetime, return_date: datetime, cancel_check=None) -> dict:
        from database import get_cache, set_cache
        cache_key = f"{self.ORIGIN_SKY_CODE}_{departure.strftime('%Y-%m-%d')}_{return_date.strftime('%Y-%m-%d')}_{self.ADULTS}"
        cached = get_cache(cache_key)
        if cached:
            results = cached.get("everywhereDestination", {}).get("results", [])
            print(f"[CACHE HIT] {self.ORIGIN_SKY_CODE} {departure.strftime('%d.%m.')} -> {len(results)} Ergebnisse")
            return cached

        body = {
            "cabinClass": "ECONOMY",
            "childAges": [],
            "adults": self.ADULTS,
            "legs": [
                {
                    "legOrigin": {"@type": "entity", "entityId": self.VIENNA_ENTITY_ID},
                    "legDestination": {"@type": "everywhere"},
                    "dates": {"@type": "date", "year": departure.year, "month": departure.month, "day": departure.day}
                },
                {
                    "legOrigin": {"@type": "everywhere"},
                    "legDestination": {"@type": "entity", "entityId": self.VIENNA_ENTITY_ID},
                    "dates": {"@type": "date", "year": return_date.year, "month": return_date.month, "day": return_date.day}
                }
            ],
            "options": {"fareAttributes": {"selectedFareAttributes": []}}
        }
        label = f"EVERYWHERE {self.ORIGIN_SKY_CODE} {departure.strftime('%d.%m.')}"
        try:
            response = self._retry_on_403(
                lambda: self.session.post(self.API_URL, json=body, timeout=30),
                label=label,
                cancel_check=cancel_check,
            )
            print(f"[{label}] -> HTTP {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                results = data.get("everywhereDestination", {}).get("results", [])
                print(f"[{label}] {len(results)} Ergebnisse")
                set_cache(cache_key, data)
                return data
            print(f"[{label}] Fehlgeschlagen! Status {response.status_code}")
            return {}
        except Exception as e:
            print(f"[{label}] Exception: {e}")
            return {}

    def get_specific_flight_details(self, destination_entity_id: str, departure: datetime, return_date: datetime) -> Optional[dict]:
        clean_dest_id = str(destination_entity_id).replace("location-", "")
        body = {
            "cabinClass": "ECONOMY",
            "childAges": [],
            "adults": self.ADULTS,
            "legs": [
                {
                    "legOrigin": {"@type": "entity", "entityId": self.VIENNA_ENTITY_ID},
                    "legDestination": {"@type": "entity", "entityId": clean_dest_id},
                    "dates": {"@type": "date", "year": str(departure.year), "month": str(departure.month).zfill(2), "day": str(departure.day).zfill(2)},
                    "placeOfStay": clean_dest_id
                },
                {
                    "legOrigin": {"@type": "entity", "entityId": clean_dest_id},
                    "legDestination": {"@type": "entity", "entityId": self.VIENNA_ENTITY_ID},
                    "dates": {"@type": "date", "year": str(return_date.year), "month": str(return_date.month).zfill(2), "day": str(return_date.day).zfill(2)}
                }
            ]
        }
        try:
            h = self.session.headers.copy()
            h.pop("x-radar-combined-explore-generic-results", None)
            h.pop("x-radar-combined-explore-unfocused-locations-use-real-data", None)
            response = self.session.post(self.API_URL, json=body, headers=h, timeout=30)
            print(f"  [API] {clean_dest_id} -> HTTP {response.status_code}")
            if response.status_code == 403:
                # Sofort aufgeben statt minutenlang warten - Caller nutzt Country-Preis
                print(f"  [API] 403 -> Skip (Country-Preis wird verwendet)")
                return {"status": "blocked"}
            if response.status_code != 200:
                return None
            data = response.json()
            itineraries = data.get("itineraries", {}).get("results", [])
            print(f"  [API] {len(itineraries)} Itineraries gefunden")

            valid_options = []  # (price, dep_time, ret_time, early)
            early_options = []
            skipped_price = 0

            min_hour = 7 if self.is_easter_period(departure) else self.START_HOUR

            for itinerary in itineraries:
                total_price = float(itinerary.get("price", {}).get("raw", 9999))
                price_per_person = total_price / self.ADULTS

                if price_per_person > self.MAX_PRICE:
                    skipped_price += 1
                    continue

                legs = itinerary.get("legs", [])
                if not legs:
                    continue

                departure_str = legs[0].get("departure", "")
                if not departure_str:
                    continue

                try:
                    dep_dt = datetime.fromisoformat(departure_str)
                    ret_time = ""
                    ret_arr_time = ""
                    if len(legs) >= 2:
                        ret_dep_str = legs[1].get("departure", "")
                        if ret_dep_str:
                            ret_time = datetime.fromisoformat(ret_dep_str).strftime("%H:%M")
                        ret_arr_str = legs[1].get("arrival", "")
                        if ret_arr_str:
                            ret_arr_time = datetime.fromisoformat(ret_arr_str).strftime("%H:%M")

                    dep_time = dep_dt.strftime("%H:%M")
                    option = {"price": price_per_person, "time": dep_time, "return_time": ret_time, "return_arrival": ret_arr_time}

                    if dep_dt.hour < min_hour:
                        option["early_departure"] = True
                        early_options.append(option)
                    else:
                        option["early_departure"] = False
                        valid_options.append(option)
                except ValueError:
                    continue

            # Nach Preis sortieren
            valid_options.sort(key=lambda x: x["price"])
            early_options.sort(key=lambda x: x["price"])

            if valid_options:
                best = valid_options[0]
                # Alternativen: die nächsten 2 (andere Preis/Zeit-Kombination)
                alternatives = []
                seen = {(best["time"], best["return_time"])}
                for opt in valid_options[1:]:
                    key = (opt["time"], opt["return_time"])
                    if key not in seen:
                        alternatives.append(opt)
                        seen.add(key)
                    if len(alternatives) >= 3:
                        break

                return {
                    "price": best["price"], "status": "ok",
                    "time": best["time"], "return_time": best["return_time"],
                    "early_departure": False, "alternatives": alternatives,
                }

            if not valid_options and itineraries:
                print(f"  [FILTER] Alle rausgefiltert! Preis>{self.MAX_PRICE}€: {skipped_price}, Abflug<{min_hour}h: {len(early_options)}")

            # Fallback: Frühflüge
            if early_options:
                best = early_options[0]
                print(f"  [FILTER] Frühflug-Fallback: {best['price']:.0f}€ um {best['time']} (vor {min_hour}h)")
                alternatives = []
                seen = {(best["time"], best["return_time"])}
                for opt in early_options[1:]:
                    key = (opt["time"], opt["return_time"])
                    if key not in seen:
                        opt["early_departure"] = True
                        alternatives.append(opt)
                        seen.add(key)
                    if len(alternatives) >= 3:
                        break

                return {
                    "price": best["price"], "status": "ok",
                    "time": best["time"], "return_time": best["return_time"],
                    "early_departure": True, "alternatives": alternatives,
                }

            return {"status": "too_early_or_expensive"}
        except Exception as e:
            print(f"  [API] Exception: {e}")
            return None

    def search_country_cities(self, country_entity_id: str, departure: datetime, return_date: datetime, cancel_check=None) -> dict:
        body = {
            "cabinClass": "ECONOMY",
            "childAges": [],
            "adults": self.ADULTS,
            "legs": [
                {
                    "legOrigin": {"@type": "entity", "entityId": self.VIENNA_ENTITY_ID},
                    "legDestination": {"@type": "entity", "entityId": country_entity_id},
                    "dates": {"@type": "date", "year": departure.year, "month": departure.month, "day": departure.day},
                    "placeOfStay": country_entity_id
                },
                {
                    "legOrigin": {"@type": "entity", "entityId": country_entity_id},
                    "legDestination": {"@type": "entity", "entityId": self.VIENNA_ENTITY_ID},
                    "dates": {"@type": "date", "year": return_date.year, "month": return_date.month, "day": return_date.day}
                }
            ],
            "options": {"fareAttributes": {"selectedFareAttributes": []}}
        }
        try:
            response = self._retry_on_403(
                lambda: self.session.post(self.API_URL, json=body, timeout=30),
                label=f"COUNTRY {country_entity_id}",
                cancel_check=cancel_check,
            )
            print(f"  [COUNTRY] {country_entity_id} -> HTTP {response.status_code}")
            if response.status_code == 200:
                return response.json()
            return {}
        except Exception as e:
            print(f"  [COUNTRY] Exception: {e}")
            return {}

    def scrape_weekend(self, friday: datetime, sunday: datetime, cancel_check=None,
                       on_deals=None, on_status=None) -> list[FlightDeal]:
        self._is_blocked = False  # Reset pro Trip
        if cancel_check and cancel_check():
            return []

        date_str = friday.strftime('%d.%m.')
        if on_status:
            on_status(f"🔍 {date_str} Everywhere-Suche...")

        data = self.search_flights(friday, sunday, cancel_check=cancel_check)
        if not data:
            return []

        results = data.get("everywhereDestination", {}).get("results", [])
        deals = []
        cheap_countries = []
        skipped_countries = []

        for result in results:
            if result.get("type") != "LOCATION":
                continue
            content = result.get("content", {})
            location = content.get("location", {})
            flight_quotes = content.get("flightQuotes", {})
            if not flight_quotes:
                continue

            raw_price = flight_quotes.get("cheapest", {}).get("rawPrice", 999)
            price_per_person = raw_price / self.ADULTS
            country_name = location.get("name")

            # Blacklist check
            if self.BLACKLIST_COUNTRIES and country_name in self.BLACKLIST_COUNTRIES:
                continue

            if location.get("type") == "Nation":
                if price_per_person <= self.MAX_PRICE:
                    cheap_countries.append({
                        "name": country_name,
                        "entity_id": location.get("id"),
                        "price": price_per_person
                    })
                else:
                    skipped_countries.append(f"{country_name} ({price_per_person:.0f}€)")

        if on_status:
            on_status(f"🌍 {date_str} {len(cheap_countries)} günstige Länder gefunden, {len(skipped_countries)} zu teuer")

        for ci, country in enumerate(cheap_countries):
            if cancel_check and cancel_check():
                break

            if on_status:
                on_status(f"🔎 {date_str} {country['name']} durchsuchen... ({ci+1}/{len(cheap_countries)})")

            city_data = self.search_country_cities(country["entity_id"], friday, sunday, cancel_check=cancel_check)
            city_results = city_data.get("countryDestination", {}).get("results", [])

            cities_in_country = []
            for result in city_results:
                if result.get("type") != "LOCATION":
                    continue
                content = result.get("content", {})
                location = content.get("location", {})
                flight_quotes = content.get("flightQuotes", {})

                if not flight_quotes or location.get("type") != "City":
                    continue

                cheapest = flight_quotes.get("cheapest", {})
                raw_price = cheapest.get("rawPrice", 999)
                price_per_person = raw_price / self.ADULTS

                if price_per_person > self.MAX_PRICE:
                    continue

                city_entity_id = location.get("entityId") or location.get("id")
                if not city_entity_id:
                    continue

                cities_in_country.append((location, cheapest, price_per_person, city_entity_id))

            for cj, (location, cheapest, price_per_person, city_entity_id) in enumerate(cities_in_country):
                if cancel_check and cancel_check():
                    break

                city_name_api = location.get('name', '?')
                if on_status:
                    on_status(f"✈️ {date_str} {city_name_api}, {country['name']} prüfen... ({cj+1}/{len(cities_in_country)})")

                # Detail-Call nur versuchen wenn nicht schon geblockt
                if not self._is_blocked:
                    details = self.get_specific_flight_details(city_entity_id, friday, sunday)
                else:
                    details = {"status": "blocked"}

                final_price = price_per_person
                final_time = "??:??"
                final_return_time = "??:??"
                is_early = False
                alts = []

                if details is None:
                    if on_status:
                        on_status(f"⚠️ {city_name_api} – kein API-Response")
                    continue
                elif details.get("status") == "ok":
                    final_price = details['price']
                    final_time = details['time']
                    final_return_time = details.get('return_time', '??:??')
                    is_early = details.get('early_departure', False)
                    alts = details.get('alternatives', [])
                elif details.get("status") == "blocked":
                    self._is_blocked = True
                    if on_status:
                        on_status(f"🛡️ API-Limit erreicht, nutze Fallback-Preise")
                    print(f"  [FALLBACK] {city_name_api} -> Country-Preis {price_per_person:.0f}€ (ohne Uhrzeiten)")
                elif details.get("status") == "too_early_or_expensive":
                    if on_status:
                        on_status(f"💸 {city_name_api} – zu teuer oder ungünstige Zeiten")
                    continue

                coords = location.get('coordinates', {})
                lat = coords.get('latitude', 0) or 0
                lon = coords.get('longitude', 0) or 0

                # Fallback: Koordinaten aus CITY_DATABASE wenn API keine liefert
                if lat == 0 and lon == 0:
                    city_name = location.get('name', '')
                    db_entry = CITY_DATABASE.get(city_name)
                    if db_entry:
                        lat = db_entry["lat"]
                        lon = db_entry["lon"]

                deal = FlightDeal(
                    city=location.get('name', 'Unknown'),
                    country=country["name"],
                    price=final_price,
                    departure_date=friday.strftime("%Y-%m-%d"),
                    return_date=sunday.strftime("%Y-%m-%d"),
                    is_direct=cheapest.get("direct", False),
                    url=self.build_flight_url(location.get("skyCode", ""), friday, sunday),
                    flight_time=final_time,
                    return_flight_time=final_return_time,
                    latitude=lat,
                    longitude=lon,
                    early_departure=is_early,
                    alternatives=alts,
                )
                deals.append(deal)

                # Sofort an Callback melden statt am Ende
                if on_deals:
                    on_deals([deal])

                if not self._is_blocked:
                    time.sleep(random.uniform(0.5, 1.5))

            time.sleep(random.uniform(0.5, 1.5))

        return deals

    def run(self, start_date: datetime, end_date: datetime, start_weekday: int = 4, duration: int = 2,
            cancel_check=None, on_deals=None, on_progress=None, on_status=None):
        trips = self.generate_trips(start_date, end_date, start_weekday, duration)

        def process_trip(dep_date, ret_date):
            if cancel_check and cancel_check():
                return []
            # Eigene Session pro Worker → kein 403-Konflikt
            worker = SkyscannerAPI(
                origin_entity_id=self.VIENNA_ENTITY_ID,
                adults=self.ADULTS,
                start_hour=self.START_HOUR,
                origin_sky_code=self.ORIGIN_SKY_CODE,
                max_return_hour=self.MAX_RETURN_HOUR,
            )
            worker.MAX_PRICE = self.MAX_PRICE
            worker.BLACKLIST_COUNTRIES = self.BLACKLIST_COUNTRIES
            try:
                # on_deals wird jetzt direkt in scrape_weekend pro Stadt gefeuert
                return worker.scrape_weekend(dep_date, ret_date, cancel_check=cancel_check,
                                             on_deals=on_deals, on_status=on_status)
            except Exception as e:
                print(f"Error: {e}")
                return []

        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {}
            for dep_date, ret_date in trips:
                if cancel_check and cancel_check():
                    break
                future = executor.submit(process_trip, dep_date, ret_date)
                futures[future] = (dep_date, ret_date)

            for future in as_completed(futures):
                trip_deals = future.result()
                self.deals.extend(trip_deals)
                # on_deals wird bereits in scrape_weekend gefeuert, hier nur progress
                if on_progress:
                    on_progress(0, len(trips))

        return self.deals

    def search_specific_cities(self, cities: list[str], departure: datetime, return_date: datetime,
                               cancel_check=None, on_deals=None, on_status=None) -> list[FlightDeal]:
        """Gezielte Suche nach bestimmten Städten statt Everywhere"""
        deals = []
        self._is_blocked = False
        self._setup_session()
        date_str = departure.strftime('%d.%m.')
        print(f"\n[CITY-SEARCH] {departure.strftime('%d.%m.%Y')}-{return_date.strftime('%d.%m.%Y')} | {len(cities)} Städte | Origin: {self.ORIGIN_SKY_CODE} | MaxPrice: {self.MAX_PRICE}€ | MinHour: {self.START_HOUR} | MaxReturnHour: {self.MAX_RETURN_HOUR}")
        for ci, city_name in enumerate(cities):
            if cancel_check and cancel_check():
                print(f"  [CITY-SEARCH] Abgebrochen durch Benutzer")
                break
            if self._is_blocked:
                print(f"  [SKIP] {city_name} -> übersprungen (403-Block aktiv)")
                if on_status:
                    on_status(f"🛡️ {city_name} übersprungen (API-Limit)")
                continue

            city_info = CITY_DATABASE.get(city_name)
            if not city_info:
                print(f"  [SKIP] {city_name} - nicht in CITY_DATABASE!")
                continue

            if on_status:
                on_status(f"✈️ {date_str} {city_name} prüfen... ({ci+1}/{len(cities)})")

            print(f"  [SEARCH] {city_name} (entity={city_info['entity_id']})...")
            details = self.get_specific_flight_details(city_info["entity_id"], departure, return_date)

            if details is None:
                print(f"  [RESULT] {city_name} -> None (API-Fehler)")
                if on_status:
                    on_status(f"⚠️ {city_name} – kein Response")
            elif details.get("status") == "blocked":
                self._is_blocked = True
                print(f"  [RESULT] {city_name} -> 403 geblockt, restliche Cities übersprungen")
                if on_status:
                    on_status(f"🛡️ API-Limit erreicht bei {city_name}")
            elif details.get("status") == "ok":
                is_early = details.get('early_departure', False)
                early_tag = " [FRÜH]" if is_early else ""
                print(f"  [RESULT] {city_name} -> {details['price']:.0f}€, Hin: {details.get('time')}, Rück: {details.get('return_time')}{early_tag}")
                deal = FlightDeal(
                    city=city_name,
                    country=city_info["country"],
                    price=details["price"],
                    departure_date=departure.strftime("%Y-%m-%d"),
                    return_date=return_date.strftime("%Y-%m-%d"),
                    is_direct=False,
                    url=self.build_flight_url(city_info["sky_code"], departure, return_date),
                    flight_time=details.get("time", "??:??"),
                    return_flight_time=details.get("return_time", "??:??"),
                    latitude=city_info["lat"],
                    longitude=city_info["lon"],
                    early_departure=is_early,
                    alternatives=details.get("alternatives", []),
                )
                deals.append(deal)
                if on_deals:
                    on_deals([deal])
            else:
                print(f"  [RESULT] {city_name} -> {details.get('status')} (kein passender Flug)")
                if on_status:
                    on_status(f"💸 {city_name} – kein passender Flug")

            time.sleep(random.uniform(0.5, 1.5))

        print(f"[CITY-SEARCH] Ergebnis: {len(deals)}/{len(cities)} Deals für {departure.strftime('%d.%m.')}")
        return deals

    def run_city_search(self, cities: list[str], start_date: datetime, end_date: datetime,
                        start_weekday: int = 4, duration: int = 2,
                        cancel_check=None, on_deals=None, on_progress=None, on_status=None):
        """Run-Methode für gezielte Stadtsuche"""
        trips = self.generate_trips(start_date, end_date, start_weekday, duration)

        def process_city_trip(dep_date, ret_date):
            if cancel_check and cancel_check():
                return []
            # Eigene Session pro Worker → kein 403-Konflikt
            worker = SkyscannerAPI(
                origin_entity_id=self.VIENNA_ENTITY_ID,
                adults=self.ADULTS,
                start_hour=self.START_HOUR,
                origin_sky_code=self.ORIGIN_SKY_CODE,
                max_return_hour=self.MAX_RETURN_HOUR,
            )
            worker.MAX_PRICE = self.MAX_PRICE
            try:
                # on_deals wird direkt in search_specific_cities pro Stadt gefeuert
                return worker.search_specific_cities(cities, dep_date, ret_date,
                                                     cancel_check=cancel_check,
                                                     on_deals=on_deals, on_status=on_status)
            except Exception as e:
                print(f"Error city search: {e}")
                return []

        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {}
            for dep_date, ret_date in trips:
                if cancel_check and cancel_check():
                    break
                future = executor.submit(process_city_trip, dep_date, ret_date)
                futures[future] = (dep_date, ret_date)

            for future in as_completed(futures):
                trip_deals = future.result()
                self.deals.extend(trip_deals)
                # on_deals wird bereits in search_specific_cities gefeuert, hier nur progress
                if on_progress:
                    on_progress(0, len(trips))

        return self.deals
