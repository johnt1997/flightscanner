#!/usr/bin/env python3
"""
Skyscanner Weekend Flight Scraper - API Version & PDF Report
(Refactored for FastAPI integration)
"""

import requests
import json
import uuid
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict, field
from typing import Optional
import time
from fpdf import FPDF

CITY_COORDS = {
    "London": (51.5074, -0.1278),
    "Paris": (48.8566, 2.3522),
    "Athen": (37.9838, 23.7275),
    "Barcelona": (41.3851, 2.1734),
    "Tirana": (41.3275, 19.8187),
    "Rom": (41.9028, 12.4964),
    "Mailand": (45.4642, 9.1900),
    "Amsterdam": (52.3676, 4.9041),
    "Brüssel": (50.8503, 4.3517),
    "Dublin": (53.3498, -6.2603),
    "Edinburgh": (55.9533, -3.1883),
    "Manchester": (53.4808, -2.2426),
    "Kopenhagen": (55.6761, 12.5683),
    "Stockholm": (59.3293, 18.0686),
    "Oslo": (59.9139, 10.7522),
    "Helsinki": (60.1699, 24.9384),
    "Reykjavik": (64.1466, -21.9426),
    "Lissabon": (38.7223, -9.1393),
    "Madrid": (40.4168, -3.7038),
    "Malaga": (36.7213, -4.4217),
    "Palma de Mallorca": (39.5696, 2.6502),
    "Zagreb": (45.8150, 15.9819),
    "Split": (43.5081, 16.4402),
    "Dubrovnik": (42.6507, 18.0944),
    "Belgrad": (44.7866, 20.4489),
    "Bukarest": (44.4268, 26.1025),
    "Sofia": (42.6977, 23.3219),
    "Thessaloniki": (40.6401, 22.9444),
    "Istanbul": (41.0082, 28.9784),
    "Antalya": (36.8969, 30.7133),
    "Podgorica": (42.4304, 19.2594),
    "Skopje": (41.9981, 21.4254),
    "Sarajevo": (43.8563, 18.4131),
    "Ljubljana": (46.0569, 14.5058),
    "Prag": (50.0755, 14.4378),
    "Warschau": (52.2297, 21.0122),
    "Krakau": (50.0647, 19.9450),
    "Marrakesch": (31.6295, -7.9811),
    "Kairo": (30.0444, 31.2357),
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
    origin: str = ""  # Neues Feld für multi-airport support
    latitude: float = 0.0   # NEU
    longitude: float = 0.0  # NEU


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

    col_w = [25, 25, 20, 45, 40, 35]

    pdf.cell(col_w[0], 10, "Datum", 1, 0, 'C', True)
    pdf.cell(col_w[1], 10, "Abflug", 1, 0, 'C', True)
    pdf.cell(col_w[2], 10, "Zeit", 1, 0, 'C', True)
    pdf.cell(col_w[3], 10, "Stadt", 1, 0, 'L', True)
    pdf.cell(col_w[4], 10, "Land", 1, 0, 'L', True)
    pdf.cell(col_w[5], 10, "Preis", 1, 1, 'C', True)

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

        pdf.cell(col_w[0], 8, date_nice, "LR", 0, 'C', fill)
        pdf.cell(col_w[1], 8, origin_short, "LR", 0, 'C', fill)
        pdf.cell(col_w[2], 8, deal.flight_time or "??:??", "LR", 0, 'C', fill)
        pdf.cell(col_w[3], 8, city_clean, "LR", 0, 'L', fill)
        pdf.cell(col_w[4], 8, country_clean, "LR", 0, 'L', fill)

        if is_cheap:
            pdf.set_text_color(*COLOR_GREEN)
        else:
            pdf.set_text_color(60)
        pdf.cell(col_w[5], 8, f"{deal.price:.0f} EUR", "LR", 1, 'C', fill, link=deal.url)

        pdf.set_text_color(60)
        fill = not fill

    pdf.cell(sum(col_w), 0, '', 'T')
    pdf.output(filename)


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
        self._setup_session()
        self.ADULTS = adults
        self.START_HOUR = start_hour
        self.MAX_RETURN_HOUR = max_return_hour
        self.deals: list[FlightDeal] = []

    def _setup_session(self):
        self.session.headers.update({
            "accept": "application/json",
            "accept-language": "de-DE,de;q=0.9",
            "content-type": "application/json",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "x-radar-combined-explore-generic-results": "1",
            "x-radar-combined-explore-unfocused-locations-use-real-data": "1",
            "x-skyscanner-channelid": "banana",
            "x-skyscanner-currency": "EUR",
            "x-skyscanner-locale": "de-DE",
            "x-skyscanner-market": "AT",
            "x-skyscanner-traveller-context": f"{self.traveller_context};1",
            "x-skyscanner-viewid": self.view_id,
        })

    def generate_trips(self, start_date: datetime, end_date: datetime, start_weekday: int, duration: int) -> list[tuple[datetime, datetime]]:
        trips = []
        current = start_date
        while current.weekday() != start_weekday:
            current += timedelta(days=1)
        while current <= end_date:
            dep = current
            ret = dep + timedelta(days=duration)
            if ret <= end_date:
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

    def search_flights(self, departure: datetime, return_date: datetime) -> dict:
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
        try:
            response = self.session.post(self.API_URL, json=body, timeout=30)
            if response.status_code == 403:
                time.sleep(60)
                response = self.session.post(self.API_URL, json=body, timeout=30)
            if response.status_code == 200:
                return response.json()
            return {}
        except:
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
        headers = self.session.headers.copy()
        headers.pop("x-radar-combined-explore-generic-results", None)
        headers.pop("x-radar-combined-explore-unfocused-locations-use-real-data", None)

        try:
            response = self.session.post(self.API_URL, json=body, headers=headers, timeout=30)
            if response.status_code != 200:
                return None
            data = response.json()
            itineraries = data.get("itineraries", {}).get("results", [])

            best_price = 9999.0
            best_time = ""
            valid_option_found = False

            for itinerary in itineraries:
                total_price = float(itinerary.get("price", {}).get("raw", 9999))
                price_per_person = total_price / self.ADULTS

                if price_per_person > self.MAX_PRICE:
                    continue

                legs = itinerary.get("legs", [])
                if not legs:
                    continue

                departure_str = legs[0].get("departure", "")
                if not departure_str:
                    continue

                try:
                    dep_dt = datetime.fromisoformat(departure_str)
                    min_hour = 7 if self.is_easter_period(departure) else self.START_HOUR

                    if dep_dt.hour < min_hour:
                        continue

                    # Check return arrival time
                    if len(legs) >= 2 and self.MAX_RETURN_HOUR < 23:
                        arrival_str = legs[1].get("arrival", "")
                        if arrival_str:
                            arr_dt = datetime.fromisoformat(arrival_str)
                            if arr_dt.hour > self.MAX_RETURN_HOUR:
                                continue

                    if price_per_person < best_price:
                        best_price = price_per_person
                        best_time = dep_dt.strftime("%H:%M")
                        valid_option_found = True
                except ValueError:
                    continue

            if valid_option_found:
                return {"price": best_price, "status": "ok", "time": best_time}
            return {"status": "too_early_or_expensive"}
        except:
            return None

    def search_country_cities(self, country_entity_id: str, departure: datetime, return_date: datetime) -> dict:
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
            response = self.session.post(self.API_URL, json=body, timeout=30)
            if response.status_code == 200:
                return response.json()
            return {}
        except:
            return {}

    def scrape_weekend(self, friday: datetime, sunday: datetime) -> list[FlightDeal]:
        data = self.search_flights(friday, sunday)
        if not data:
            return []

        results = data.get("everywhereDestination", {}).get("results", [])
        deals = []
        cheap_countries = []

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

            if price_per_person <= self.MAX_PRICE and location.get("type") == "Nation":
                cheap_countries.append({
                    "name": country_name,
                    "entity_id": location.get("id"),
                    "price": price_per_person
                })

        for country in cheap_countries:
            city_data = self.search_country_cities(country["entity_id"], friday, sunday)
            city_results = city_data.get("countryDestination", {}).get("results", [])

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

                details = self.get_specific_flight_details(city_entity_id, friday, sunday)
                final_price = price_per_person
                final_time = "??:??"
                keep_deal = False

                if details is None:
                    keep_deal = False
                elif details.get("status") == "ok":
                    final_price = details['price']
                    final_time = details['time']
                    keep_deal = True

                if keep_deal:
                    print(f"DEBUG {location.get('name')}: {location.get('coordinates')}")

                    deal = FlightDeal(
                        city=location.get('name', 'Unknown'),
                        country=country["name"],
                        price=final_price,
                        departure_date=friday.strftime("%Y-%m-%d"),
                        return_date=sunday.strftime("%Y-%m-%d"),
                        is_direct=cheapest.get("direct", False),
                        url=self.build_flight_url(location.get("skyCode", ""), friday, sunday),
                        flight_time=final_time,
                        # Neu:
latitude=CITY_COORDS.get(location.get('name', ''), (0, 0))[0],
longitude=CITY_COORDS.get(location.get('name', ''), (0, 0))[1],
                    )
                    deals.append(deal)

                time.sleep(0.5)

            time.sleep(1)

        return deals

    def run(self, start_date: datetime, end_date: datetime, start_weekday: int = 4, duration: int = 2):
        trips = self.generate_trips(start_date, end_date, start_weekday, duration)

        for dep_date, ret_date in trips:
            try:
                trip_deals = self.scrape_weekend(dep_date, ret_date)
                self.deals.extend(trip_deals)
                time.sleep(2)
            except Exception as e:
                print(f"Error: {e}")
                continue

        return self.deals
