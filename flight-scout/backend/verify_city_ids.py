#!/usr/bin/env python3
"""
Verifiziert und sammelt die echten Entity IDs für alle Städte in CITY_DATABASE.
Schlanke Version: nur die Länder abfragen die wir brauchen.
"""

import json
import time
import random
import sys
from datetime import datetime, timedelta
from scraper import SkyscannerAPI, CITY_DATABASE

# Force UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

def verify():
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

    # Welche Länder brauchen wir?
    needed_countries = set()
    for city_info in CITY_DATABASE.values():
        needed_countries.add(city_info["country"])
    print(f"\nBenötigte Länder: {sorted(needed_countries)}")

    # Schritt 1: Everywhere-Suche -> Länder-IDs holen
    print("\n=== Schritt 1: Everywhere-Suche -> Länder ===")
    data = scraper.search_flights(friday, sunday)
    if not data:
        print("FEHLER: Keine Daten!")
        return

    results = data.get("everywhereDestination", {}).get("results", [])

    # Mapping: API-Ländername -> unsere Ländernamen (können abweichen)
    country_name_map = {
        "Italy": "Italien",
        "Spain": "Spanien",
        "United Kingdom": "Vereinigtes Königreich",
        "Ireland": "Irland",
        "France": "Frankreich",
        "Netherlands": "Niederlande",
        "Belgium": "Belgien",
        "Denmark": "Dänemark",
        "Sweden": "Schweden",
        "Norway": "Norwegen",
        "Finland": "Finnland",
        "Greece": "Griechenland",
        "Turkey": "Türkei",
        "Türkiye": "Türkei",
        "Albania": "Albanien",
        "Serbia": "Serbien",
        "Romania": "Rumänien",
        "Bulgaria": "Bulgarien",
        "Croatia": "Kroatien",
        "Bosnia and Herzegovina": "Bosnien und Herzegowina",
        "Bosnia & Herzegovina": "Bosnien und Herzegowina",
        "Montenegro": "Montenegro",
        "North Macedonia": "Nordmazedonien",
        "Slovenia": "Slowenien",
        "Czech Republic": "Tschechische Republik",
        "Czechia": "Tschechische Republik",
        "Poland": "Polen",
        "Portugal": "Portugal",
        "Morocco": "Marokko",
        "Egypt": "Ägypten",
        "Iceland": "Island",
        "Malta": "Malta",
        "Hungary": "Ungarn",
    }

    countries = []
    for result in results:
        if result.get("type") != "LOCATION":
            continue
        content = result.get("content", {})
        location = content.get("location", {})
        if location.get("type") == "Nation":
            api_name = location.get("name", "")
            our_name = country_name_map.get(api_name, api_name)
            if our_name in needed_countries:
                countries.append({
                    "api_name": api_name,
                    "our_name": our_name,
                    "entity_id": location.get("id"),
                })
                print(f"  ✓ {api_name} -> {our_name} (entity: {location.get('id')})")

    print(f"\n{len(countries)} von {len(needed_countries)} Ländern gefunden")

    missing = needed_countries - {c["our_name"] for c in countries}
    if missing:
        print(f"  FEHLT: {missing}")

    # Schritt 2: Für jedes Land die Städte holen
    print("\n=== Schritt 2: Städte pro Land ===")

    # Was haben wir aktuell?
    current_cities = {}
    for name, info in CITY_DATABASE.items():
        current_cities[name] = info

    api_cities = {}  # name -> {entity_id, sky_code, country, lat, lon}

    for country in countries:
        print(f"\n--- {country['our_name']} ({country['api_name']}) ---")
        time.sleep(random.uniform(2, 4))
        scraper._setup_session()

        city_data = scraper.search_country_cities(country["entity_id"], friday, sunday)
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

            if not eid:
                continue

            api_cities[name] = {
                "entity_id": eid,
                "sky_code": sky.lower(),
                "country": country["our_name"],
                "lat": round(lat, 4) if lat else 0,
                "lon": round(lon, 4) if lon else 0,
            }

            # Ist diese Stadt in unserer DB?
            marker = ""
            if name in current_cities:
                old_eid = current_cities[name]["entity_id"]
                if old_eid != eid:
                    marker = f" *** FALSCH! alt={old_eid}"
                else:
                    marker = " ✓"

            print(f"  {name:25s} entity={eid:15s} sky={sky:6s} lat={lat:.2f} lon={lon:.2f}{marker}")

    # Zusammenfassung
    print("\n" + "=" * 60)
    print("ZUSAMMENFASSUNG")
    print("=" * 60)

    wrong = []
    missing_cities = []
    correct = []

    for name, info in current_cities.items():
        if name in api_cities:
            api = api_cities[name]
            if info["entity_id"] != api["entity_id"]:
                wrong.append((name, info["entity_id"], api["entity_id"], api["sky_code"], api["lat"], api["lon"]))
            else:
                correct.append(name)
        else:
            missing_cities.append(name)

    print(f"\n✓ Korrekt: {len(correct)} Städte")
    for name in correct:
        print(f"    {name}")

    if wrong:
        print(f"\n✗ FALSCHE IDs: {len(wrong)} Städte")
        for name, old_id, new_id, sky, lat, lon in wrong:
            print(f'    "{name}": alt={old_id} -> NEU={new_id} (sky={sky}, lat={lat}, lon={lon})')

    if missing_cities:
        print(f"\n? Nicht in API gefunden: {len(missing_cities)} Städte")
        for name in missing_cities:
            print(f"    {name} (behalten: {current_cities[name]['entity_id']})")

    # Neue Städte die wir nicht haben
    new_cities = []
    for name, info in api_cities.items():
        if name not in current_cities:
            new_cities.append((name, info))

    if new_cities:
        print(f"\n+ Neue Städte verfügbar: {len(new_cities)}")
        for name, info in sorted(new_cities, key=lambda x: x[1]["country"]):
            print(f'    "{name}": {json.dumps(info, ensure_ascii=False)}')

    # Fix-Code ausgeben
    if wrong:
        print("\n" + "=" * 60)
        print("FIX-CODE (kopierbar):")
        print("=" * 60)
        for name, old_id, new_id, sky, lat, lon in wrong:
            country = current_cities[name]["country"]
            print(f'    "{name}": {{"entity_id": "{new_id}", "sky_code": "{sky}", "country": "{country}", "lat": {lat}, "lon": {lon}}},')


if __name__ == "__main__":
    verify()
