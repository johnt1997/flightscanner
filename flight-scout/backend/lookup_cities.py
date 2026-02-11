#!/usr/bin/env python3
"""
Gezieltes Nachschlagen von Entity IDs für fehlende Städte.
Nutzt dieselbe API wie collect_city_ids.py, fragt aber nur die relevanten Länder ab.
"""

import sys
import io
import time
import random
from datetime import datetime, timedelta
from scraper import SkyscannerAPI

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Fehlende Städte gruppiert nach Land
MISSING_CITIES = {
    "Italien": ["Lamezia Terme", "Trapani"],
    "Lettland": ["Riga"],
    "Polen": ["Kattowitz", "Danzig", "Breslau"],
    "Vereinigtes Königreich": ["Newcastle upon Tyne", "Liverpool"],
    "Slowakei": ["Košice"],
    "Litauen": ["Vilnius"],
    "Georgien": ["Kutaissi"],
}

# Alternative Namen die die API zurückgeben könnte
ALT_NAMES = {
    "Katowice": "Kattowitz",
    "Gdańsk": "Danzig",
    "Gdansk": "Danzig",
    "Wrocław": "Breslau",
    "Wroclaw": "Breslau",
    "Newcastle": "Newcastle upon Tyne",
    "Kutaisi": "Kutaissi",
    "Kutaissi": "Kutaissi",
    "Lamezia": "Lamezia Terme",
    "Košice": "Košice",
    "Kosice": "Košice",
}

def collect_missing():
    scraper = SkyscannerAPI(
        origin_entity_id="95673444",
        adults=1,
        start_hour=0,
        origin_sky_code="vie",
    )
    scraper.MAX_PRICE = 9999

    # Übernächsten Freitag
    today = datetime.now()
    days_until_friday = (4 - today.weekday()) % 7
    if days_until_friday == 0:
        days_until_friday = 7
    friday = today + timedelta(days=days_until_friday + 14)
    sunday = friday + timedelta(days=2)

    print(f"Datum: {friday.strftime('%d.%m.%Y')} - {sunday.strftime('%d.%m.%Y')}")

    # Schritt 1: Everywhere-Suche -> Länder-IDs
    print("\n=== Schritt 1: Everywhere-Suche -> Länder ===")
    data = scraper.search_flights(friday, sunday)
    if not data:
        print("FEHLER: Keine Daten!")
        return

    results = data.get("everywhereDestination", {}).get("results", [])
    country_ids = {}
    for result in results:
        if result.get("type") != "LOCATION":
            continue
        content = result.get("content", {})
        location = content.get("location", {})
        if location.get("type") == "Nation":
            name = location.get("name")
            country_ids[name] = location.get("id")

    print(f"{len(country_ids)} Länder gefunden")

    # Nur die Länder abfragen die wir brauchen
    needed_countries = set(MISSING_CITIES.keys())
    print(f"\nBrauche: {needed_countries}")
    print(f"Gefunden: {needed_countries & set(country_ids.keys())}")
    missing_countries = needed_countries - set(country_ids.keys())
    if missing_countries:
        print(f"NICHT gefunden: {missing_countries}")

    # Schritt 2: Nur relevante Länder abfragen
    print("\n=== Schritt 2: Städte der relevanten Länder ===")
    found_cities = {}

    for country_name, city_list in MISSING_CITIES.items():
        if country_name not in country_ids:
            print(f"\n--- {country_name}: ÜBERSPRUNGEN (kein Entity ID) ---")
            continue

        print(f"\n--- {country_name} (suche: {', '.join(city_list)}) ---")
        time.sleep(random.uniform(2, 4))
        scraper._setup_session()

        city_data = scraper.search_country_cities(country_ids[country_name], friday, sunday)
        city_results = city_data.get("countryDestination", {}).get("results", [])

        for result in city_results:
            if result.get("type") != "LOCATION":
                continue
            content = result.get("content", {})
            location = content.get("location", {})

            if location.get("type") != "City":
                continue

            name = location.get("name", "?")
            eid = str(location.get("entityId") or location.get("id", ""))
            sky = location.get("skyCode", "")
            coords = location.get("coordinates", {})
            lat = coords.get("latitude", 0)
            lon = coords.get("longitude", 0)

            # Check ob das eine gesuchte Stadt ist (direkt oder über Alt-Name)
            mapped_name = ALT_NAMES.get(name, name)
            is_wanted = mapped_name in city_list or name in city_list

            marker = " <<<< GESUCHT!" if is_wanted else ""
            print(f"  {name:25s} entity={eid:15s} sky={sky:6s} lat={lat:.4f} lon={lon:.4f}{marker}")

            if is_wanted:
                found_cities[mapped_name] = {
                    "entity_id": eid,
                    "sky_code": sky.lower(),
                    "country": country_name,
                    "lat": round(lat, 4),
                    "lon": round(lon, 4),
                    "api_name": name,
                }

    # Ergebnis
    print("\n" + "=" * 60)
    print("GEFUNDENE STÄDTE (für CITY_DATABASE):")
    print("=" * 60)

    for name, info in sorted(found_cities.items()):
        print(f'    "{name}": {{"entity_id": "{info["entity_id"]}", "sky_code": "{info["sky_code"]}", "country": "{info["country"]}", "lat": {info["lat"]}, "lon": {info["lon"]}}},')

    # Was fehlt noch?
    all_wanted = [city for cities in MISSING_CITIES.values() for city in cities]
    still_missing = [c for c in all_wanted if c not in found_cities]
    if still_missing:
        print(f"\nNOCH NICHT GEFUNDEN: {still_missing}")


if __name__ == "__main__":
    collect_missing()
