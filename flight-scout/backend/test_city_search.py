#!/usr/bin/env python3
"""
Test: Gezielte Stadtsuche über die Skyscanner API
Testet ob man direkt nach einer bestimmten Stadt suchen kann,
ohne den Umweg über die Everywhere-Suche.
"""

import json
import sys
from datetime import datetime, timedelta
from scraper import SkyscannerAPI

# Bekannte Entity IDs (aus der Everywhere-/Country-Suche gesammelt)
# Wenn wir keine kennen, testen wir auch ob man sie per Autosuggest finden kann
KNOWN_CITIES = {
    "London":    {"entity_id": "27544008", "sky_code": "lond"},
    "Barcelona": {"entity_id": "27548283", "sky_code": "bcn"},
    "Athen":     {"entity_id": "27539604", "sky_code": "ath"},
    "Paris":     {"entity_id": "27539733", "sky_code": "pari"},
    "Rom":       {"entity_id": "27539793", "sky_code": "rome"},
    "Mailand":   {"entity_id": "27544068", "sky_code": "mila"},
    "Bologna":   {"entity_id": "27539470", "sky_code": "bolo"},
}

def test_autosuggest(query: str):
    """Test: Kann man Stadtnamen -> Entity ID auflösen über Skyscanner Autosuggest?"""
    import requests
    print(f"\n{'='*60}")
    print(f"TEST 1: Autosuggest für '{query}'")
    print(f"{'='*60}")

    url = "https://www.skyscanner.at/g/autosuggest-search/api/v1/search-flight/UK/en-GB/GBP/"
    # Alternative URL die auch funktionieren könnte:
    urls_to_try = [
        f"https://www.skyscanner.at/g/autosuggest-flights/AT/de-DE/EUR/{query}",
        f"https://www.skyscanner.at/g/autosuggest-search/api/v1/search-flight/AT/de-DE/EUR/{query}",
    ]

    headers = {
        "accept": "application/json",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0.0.0",
        "referer": "https://www.skyscanner.at/",
    }

    for url in urls_to_try:
        try:
            print(f"\n  Versuche: {url}")
            resp = requests.get(url, headers=headers, timeout=10)
            print(f"  Status: {resp.status_code}")
            if resp.status_code == 200:
                data = resp.json()
                print(f"  Response-Typ: {type(data)}")
                if isinstance(data, list):
                    for item in data[:5]:
                        print(f"    -> {json.dumps(item, indent=2, ensure_ascii=False)[:200]}")
                elif isinstance(data, dict):
                    print(f"  Keys: {list(data.keys())}")
                    # Schaue nach relevanten Daten
                    for key in ['places', 'results', 'data', 'suggestions']:
                        if key in data:
                            items = data[key]
                            if isinstance(items, list):
                                for item in items[:3]:
                                    print(f"    [{key}] -> {json.dumps(item, indent=2, ensure_ascii=False)[:300]}")
                return data
            else:
                print(f"  Body: {resp.text[:200]}")
        except Exception as e:
            print(f"  Fehler: {e}")

    return None


def test_direct_city_search(city_name: str, entity_id: str, sky_code: str):
    """Test: Direkte Flugsuche nach einer bestimmten Stadt"""
    print(f"\n{'='*60}")
    print(f"TEST 2: Direkte Suche VIE -> {city_name} (entity: {entity_id})")
    print(f"{'='*60}")

    scraper = SkyscannerAPI(
        origin_entity_id="95673444",  # Wien
        adults=1,
        start_hour=0,
        origin_sky_code="vie",
    )
    scraper.MAX_PRICE = 9999  # Kein Preislimit für den Test

    # Nächsten Freitag finden
    today = datetime.now()
    days_until_friday = (4 - today.weekday()) % 7
    if days_until_friday == 0:
        days_until_friday = 7
    friday = today + timedelta(days=days_until_friday + 14)  # Übernächsten Freitag
    sunday = friday + timedelta(days=2)

    print(f"  Datum: {friday.strftime('%d.%m.%Y')} - {sunday.strftime('%d.%m.%Y')}")

    # Test get_specific_flight_details direkt
    print(f"\n  Rufe get_specific_flight_details auf... (entity_id={entity_id})")

    # Erst mal direkt den rohen Call machen um den HTTP-Status zu sehen
    clean_dest_id = str(entity_id).replace("location-", "")
    body = {
        "cabinClass": "ECONOMY",
        "childAges": [],
        "adults": 1,
        "legs": [
            {
                "legOrigin": {"@type": "entity", "entityId": "95673444"},
                "legDestination": {"@type": "entity", "entityId": clean_dest_id},
                "dates": {"@type": "date", "year": str(friday.year), "month": str(friday.month).zfill(2), "day": str(friday.day).zfill(2)},
                "placeOfStay": clean_dest_id
            },
            {
                "legOrigin": {"@type": "entity", "entityId": clean_dest_id},
                "legDestination": {"@type": "entity", "entityId": "95673444"},
                "dates": {"@type": "date", "year": str(sunday.year), "month": str(sunday.month).zfill(2), "day": str(sunday.day).zfill(2)}
            }
        ]
    }
    headers = scraper.session.headers.copy()
    headers.pop("x-radar-combined-explore-generic-results", None)
    headers.pop("x-radar-combined-explore-unfocused-locations-use-real-data", None)
    try:
        resp = scraper.session.post(scraper.API_URL, json=body, headers=headers, timeout=30)
        print(f"  Debug: HTTP {resp.status_code}")
        if resp.status_code != 200:
            print(f"  Debug: {resp.text[:300]}")
    except Exception as e:
        print(f"  Debug: Exception {e}")

    details = scraper.get_specific_flight_details(entity_id, friday, sunday)

    if details is None:
        print(f"  Ergebnis: None (API-Fehler oder kein Response)")
    elif details.get("status") == "ok":
        print(f"  ERFOLG!")
        print(f"  Preis:        {details['price']:.2f}€")
        print(f"  Hinflug:      {details.get('time', '?')}")
        print(f"  Rückflug:     {details.get('return_time', '?')}")
    else:
        print(f"  Status: {details.get('status')} (zu teuer oder zu früh)")

    return details


def test_raw_api_call(city_name: str, entity_id: str):
    """Test: Roher API-Call um die volle Response zu sehen"""
    print(f"\n{'='*60}")
    print(f"TEST 3: Roher API-Call VIE -> {city_name} (volle Response)")
    print(f"{'='*60}")

    scraper = SkyscannerAPI(
        origin_entity_id="95673444",
        adults=1,
        start_hour=0,
        origin_sky_code="vie",
    )
    scraper.MAX_PRICE = 9999  # Kein Preislimit für den Test

    today = datetime.now()
    days_until_friday = (4 - today.weekday()) % 7
    if days_until_friday == 0:
        days_until_friday = 7
    friday = today + timedelta(days=days_until_friday + 14)
    sunday = friday + timedelta(days=2)

    clean_dest_id = str(entity_id).replace("location-", "")
    body = {
        "cabinClass": "ECONOMY",
        "childAges": [],
        "adults": 1,
        "legs": [
            {
                "legOrigin": {"@type": "entity", "entityId": "95673444"},
                "legDestination": {"@type": "entity", "entityId": clean_dest_id},
                "dates": {"@type": "date", "year": str(friday.year), "month": str(friday.month).zfill(2), "day": str(friday.day).zfill(2)},
                "placeOfStay": clean_dest_id
            },
            {
                "legOrigin": {"@type": "entity", "entityId": clean_dest_id},
                "legDestination": {"@type": "entity", "entityId": "95673444"},
                "dates": {"@type": "date", "year": str(sunday.year), "month": str(sunday.month).zfill(2), "day": str(sunday.day).zfill(2)}
            }
        ]
    }

    headers = scraper.session.headers.copy()
    headers.pop("x-radar-combined-explore-generic-results", None)
    headers.pop("x-radar-combined-explore-unfocused-locations-use-real-data", None)

    try:
        response = scraper.session.post(scraper.API_URL, json=body, headers=headers, timeout=30)
        print(f"  Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()

            # Response-Struktur analysieren
            print(f"  Top-Level Keys: {list(data.keys())}")

            itineraries = data.get("itineraries", {})
            results = itineraries.get("results", [])
            print(f"  Anzahl Itineraries: {len(results)}")

            if results:
                # Zeige die 3 günstigsten
                sorted_results = sorted(results, key=lambda x: float(x.get("price", {}).get("raw", 9999)))
                for i, itin in enumerate(sorted_results[:3]):
                    price = float(itin.get("price", {}).get("raw", 0))
                    legs = itin.get("legs", [])

                    print(f"\n  --- Itinerary {i+1} ---")
                    print(f"  Gesamtpreis: {price:.2f}€")

                    for j, leg in enumerate(legs):
                        dep = leg.get("departure", "?")
                        arr = leg.get("arrival", "?")
                        origin_name = leg.get("origin", {}).get("name", "?")
                        dest_name = leg.get("destination", {}).get("name", "?")
                        stops = leg.get("stopCount", 0)
                        carriers = [c.get("name", "?") for c in leg.get("carriers", {}).get("marketing", [])]

                        direction = "HIN" if j == 0 else "RÜCK"
                        print(f"  [{direction}] {origin_name} -> {dest_name}")
                        print(f"         {dep} -> {arr}")
                        print(f"         Stops: {stops}, Airlines: {', '.join(carriers)}")
            else:
                print(f"  Keine Ergebnisse gefunden!")
                # Schaue ob es andere Daten gibt
                for key in data:
                    if key != "itineraries":
                        val = data[key]
                        if isinstance(val, dict):
                            print(f"  [{key}] keys: {list(val.keys())[:10]}")
                        elif isinstance(val, list):
                            print(f"  [{key}] {len(val)} items")
        else:
            print(f"  Fehler-Body: {response.text[:300]}")

    except Exception as e:
        print(f"  Exception: {e}")


def test_everywhere_to_find_ids():
    """Test: Everywhere-Suche nutzen um Entity IDs für Städte zu sammeln"""
    print(f"\n{'='*60}")
    print(f"TEST 4: Everywhere-Suche -> Entity IDs sammeln")
    print(f"{'='*60}")

    scraper = SkyscannerAPI(
        origin_entity_id="95673444",
        adults=1,
        start_hour=0,
        origin_sky_code="vie",
    )
    scraper.MAX_PRICE = 9999

    today = datetime.now()
    days_until_friday = (4 - today.weekday()) % 7
    if days_until_friday == 0:
        days_until_friday = 7
    friday = today + timedelta(days=days_until_friday + 14)
    sunday = friday + timedelta(days=2)

    print(f"  Datum: {friday.strftime('%d.%m.%Y')} - {sunday.strftime('%d.%m.%Y')}")

    # Debug: rohen API-Call sehen
    body = {
        "cabinClass": "ECONOMY",
        "childAges": [],
        "adults": 1,
        "legs": [
            {
                "legOrigin": {"@type": "entity", "entityId": "95673444"},
                "legDestination": {"@type": "everywhere"},
                "dates": {"@type": "date", "year": friday.year, "month": friday.month, "day": friday.day}
            },
            {
                "legOrigin": {"@type": "everywhere"},
                "legDestination": {"@type": "entity", "entityId": "95673444"},
                "dates": {"@type": "date", "year": sunday.year, "month": sunday.month, "day": sunday.day}
            }
        ],
        "options": {"fareAttributes": {"selectedFareAttributes": []}}
    }
    try:
        response = scraper.session.post(scraper.API_URL, json=body, timeout=30)
        print(f"  HTTP Status: {response.status_code}")
        if response.status_code != 200:
            print(f"  Response: {response.text[:500]}")
            return
        data = response.json()
        print(f"  Top-Level Keys: {list(data.keys())}")
    except Exception as e:
        print(f"  Request Exception: {e}")
        return

    if not data:
        print("  Keine Daten!")
        return

    results = data.get("everywhereDestination", {}).get("results", [])
    print(f"  {len(results)} Ergebnisse")

    countries_found = []
    for result in results:
        if result.get("type") != "LOCATION":
            continue
        content = result.get("content", {})
        location = content.get("location", {})
        fq = content.get("flightQuotes", {})
        price = fq.get("cheapest", {}).get("rawPrice", 9999) if fq else 9999

        loc_type = location.get("type")
        name = location.get("name")
        entity_id = location.get("id")
        sky_code = location.get("skyCode", "")

        if loc_type == "Nation":
            countries_found.append({
                "name": name,
                "entity_id": entity_id,
                "sky_code": sky_code,
                "price": price,
            })
            print(f"  Land: {name:25s} entity={entity_id:15s} sky={sky_code:6s} ab {price:.0f}€")

    # Für das erste günstige Land: Städte suchen
    if countries_found:
        country = sorted(countries_found, key=lambda x: x["price"])[0]
        print(f"\n  Suche Städte in {country['name']}...")

        city_data = scraper.search_country_cities(country["entity_id"], friday, sunday)
        city_results = city_data.get("countryDestination", {}).get("results", [])

        for result in city_results:
            if result.get("type") != "LOCATION":
                continue
            content = result.get("content", {})
            location = content.get("location", {})
            fq = content.get("flightQuotes", {})

            if location.get("type") == "City":
                name = location.get("name")
                eid = location.get("entityId") or location.get("id")
                sky = location.get("skyCode", "")
                price = fq.get("cheapest", {}).get("rawPrice", 9999) if fq else 9999
                coords = location.get("coordinates", {})

                print(f"  Stadt: {name:25s} entity={str(eid):15s} sky={sky:6s} ab {price:.0f}€  coords={coords}")


if __name__ == "__main__":
    print("=" * 60)
    print("  FLIGHT SCOUT - Test: Gezielte Stadtsuche")
    print("=" * 60)

    # Welchen Test ausführen?
    if len(sys.argv) > 1:
        test = sys.argv[1]
    else:
        print("\nVerfügbare Tests:")
        print("  1 - Autosuggest (Stadtname -> Entity ID)")
        print("  2 - Direkte Stadtsuche (bekannte Entity ID)")
        print("  3 - Roher API-Call (volle Response)")
        print("  4 - Everywhere -> Entity IDs sammeln")
        print("  all - Alle Tests")
        print()
        test = input("Test auswählen (1/2/3/4/all): ").strip()

    city = "London"
    if len(sys.argv) > 2:
        city = sys.argv[2]

    city_info = KNOWN_CITIES.get(city, KNOWN_CITIES["London"])

    if test in ("1", "all"):
        test_autosuggest(city)

    if test in ("2", "all"):
        test_direct_city_search(city, city_info["entity_id"], city_info["sky_code"])

    if test in ("3", "all"):
        test_raw_api_call(city, city_info["entity_id"])

    if test in ("4", "all"):
        test_everywhere_to_find_ids()

    print(f"\n{'='*60}")
    print("  Tests abgeschlossen!")
    print("=" * 60)
