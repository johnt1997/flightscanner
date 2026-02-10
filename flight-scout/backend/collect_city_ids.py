#!/usr/bin/env python3
"""
Sammelt echte Entity IDs für alle Städte aus der Skyscanner API.
Schritt 1: Everywhere -> Länder-IDs
Schritt 2: Für jedes Land -> Stadt-IDs
Gibt am Ende ein fertiges CITY_DATABASE dict aus.
"""

import json
import time
import random
from datetime import datetime, timedelta
from scraper import SkyscannerAPI

def collect():
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

    # Schritt 1: Länder holen
    print("\n=== Schritt 1: Everywhere-Suche -> Länder ===")
    data = scraper.search_flights(friday, sunday)
    if not data:
        print("FEHLER: Keine Daten von Everywhere-Suche!")
        return

    results = data.get("everywhereDestination", {}).get("results", [])
    countries = []
    for result in results:
        if result.get("type") != "LOCATION":
            continue
        content = result.get("content", {})
        location = content.get("location", {})
        if location.get("type") == "Nation":
            countries.append({
                "name": location.get("name"),
                "entity_id": location.get("id"),
            })

    print(f"{len(countries)} Länder gefunden")

    # Schritt 2: Für jedes Land die Städte holen
    print("\n=== Schritt 2: Städte pro Land ===")
    city_database = {}

    for country in countries:
        print(f"\n--- {country['name']} ---")
        time.sleep(random.uniform(2, 4))

        # Frische Session
        scraper._setup_session()

        city_data = scraper.search_country_cities(country["entity_id"], friday, sunday)
        city_results = city_data.get("countryDestination", {}).get("results", [])

        for result in city_results:
            if result.get("type") != "LOCATION":
                continue
            content = result.get("content", {})
            location = content.get("location", {})
            fq = content.get("flightQuotes", {})

            if location.get("type") != "City":
                continue

            name = location.get("name", "?")
            eid = str(location.get("entityId") or location.get("id", ""))
            sky = location.get("skyCode", "")
            price = fq.get("cheapest", {}).get("rawPrice", 9999) if fq else 9999

            if not eid:
                continue

            city_database[name] = {
                "entity_id": eid,
                "sky_code": sky.lower(),
                "country": country["name"],
                "price": price,
            }
            print(f"  {name:25s} entity={eid:15s} sky={sky:6s} ab {price:.0f}")

    # Ausgabe als Python dict
    print("\n\n" + "=" * 60)
    print("FERTIGES CITY_DATABASE (kopieren!):")
    print("=" * 60)

    # Gruppiere nach Land
    by_country = {}
    for name, info in city_database.items():
        c = info["country"]
        if c not in by_country:
            by_country[c] = []
        by_country[c].append((name, info))

    print("CITY_DATABASE = {")
    for country, cities in sorted(by_country.items()):
        print(f"    # {country}")
        for name, info in sorted(cities, key=lambda x: x[1]["price"]):
            print(f'    "{name}": {{"entity_id": "{info["entity_id"]}", "sky_code": "{info["sky_code"]}", "country": "{country}", "lat": 0, "lon": 0}},')
    print("}")


if __name__ == "__main__":
    collect()
