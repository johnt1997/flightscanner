# Flight Scout

Finde die günstigsten Wochenend-Flüge ab Wien, Bratislava und Budapest.

## Features

- **Multi-Airport Suche** -- Wien, Bratislava, Budapest gleichzeitig
- **Flexible Zeitraeume** -- Fr-So, Do-So, Mo-Mi, etc.
- **Mehrere Reisedauern** -- z.B. 2 und 3 Naechte gleichzeitig suchen
- **Preisfilter** -- Max. Preis pro Person
- **Zeitfilter** -- Fruehester Abflug einstellbar, Fruehfluege werden visuell markiert
- **Laender-Blacklist** -- Bestimmte Laender ausschliessen (mit Alle auswaehlen/abwaehlen)
- **Stadtsuche** -- Gezielt nach bestimmten Staedten suchen statt Everywhere
- **Alternative Fluege** -- Pro Deal bis zu 3 weitere Flugoptionen aufklappbar
- **PDF Report** -- Download fuer offline
- **Direkte Buchungslinks** -- Skyscanner URLs
- **Heatmap** -- Deals auf der Karte (Leaflet)
- **Kalender-Heatmap** -- Guenstigster Preis pro Tag im Monatsuberblick
- **Deal-Archiv** -- Deals speichern und verwalten (mit User-Auth)
- **Telegram Preis-Alerts** -- Benachrichtigung wenn ein Deal unter deinem Wunschpreis liegt
- **Gruppierte Ergebnisse** -- Deals nach Stadt gruppiert mit Akkordeon-UI
- **Favoriten-Staedte** -- Lieblingsstaedte markieren, werden oben angezeigt
- **Share-Button** -- Deal als formatierte Telegram-Karte in die Zwischenablage kopieren
- **Dark/Light Mode** -- Theme umschaltbar, wird gespeichert
- **403-Fallback** -- Bei API-Blockade werden Country-Level Preise als Fallback verwendet
- **Verifizierte City IDs** -- 45 Staedte mit echten Skyscanner Entity IDs (via verify_city_ids.py)

## Setup

### Backend (FastAPI)

```bash
cd backend
pip install -r requirements.txt
python main.py
```

API laeuft auf http://localhost:8000

### Frontend (React + Vite)

```bash
cd frontend
npm install
npm run dev
```

Frontend laeuft auf http://localhost:3000

## API Endpoints

| Method | Endpoint | Beschreibung |
|--------|----------|--------------|
| GET | `/airports` | Liste aller Flughaefen |
| POST | `/search` | Startet Flugsuche |
| GET | `/status/{job_id}` | Job-Status abfragen |
| GET | `/download/{job_id}` | PDF herunterladen |
| POST | `/register` | User registrieren |
| POST | `/login` | User anmelden |
| POST | `/deals/save` | Deal ins Archiv speichern (Auth) |
| GET | `/deals` | Gespeicherte Deals abrufen (Auth) |
| DELETE | `/deals/{id}` | Deal aus Archiv loeschen (Auth) |
| POST | `/alerts` | Preis-Alert erstellen (Auth) |
| GET | `/alerts` | Alerts abrufen (Auth) |
| DELETE | `/alerts/{id}` | Alert loeschen (Auth) |
| POST | `/calendar` | Kalender-Preisdaten fuer einen Monat |

## Tools

| Script | Beschreibung |
|--------|--------------|
| `verify_city_ids.py` | Verifiziert alle City Entity IDs gegen die Skyscanner API |
| `collect_city_ids.py` | Sammelt Entity IDs fuer alle Staedte weltweit (langsam) |
| `test_city_search.py` | Test-Script fuer direkte Stadtsuche und API-Debugging |

## Architektur

- **Datenbank:** SQLite (`flight_scout.db`) mit Tabellen: `users`, `saved_deals`, `price_alerts`
- **Auth:** Token-basiert (HMAC), Passwoerter mit bcrypt gehasht
- **Telegram Alerts:** Werden nach jeder manuellen Suche geprueft. Bot-Token in `backend/alerts.py` konfigurieren.
- **API-Strategie:** Everywhere-Suche -> Country-Suche -> City-Detail-Calls. Bei 403-Block wird auf Country-Level Preise zurueckgefallen.

## Konfiguration

### Neuen Flughafen hinzufuegen

In `backend/main.py`:

```python
AIRPORTS = {
    "vie": {"id": "95673444", "name": "Wien", "code": "vie"},
    "bts": {"id": "95673445", "name": "Bratislava", "code": "bts"},
    "bud": {"id": "95673439", "name": "Budapest", "code": "bud"},
    # Neu:
    "prg": {"id": "XXXXXX", "name": "Prag", "code": "prg"},
}
```

Die Entity-ID findest du in den Skyscanner Network Requests oder via `verify_city_ids.py`.

### City IDs verifizieren

```bash
cd backend
python verify_city_ids.py
```

Vergleicht alle Staedte in CITY_DATABASE mit den echten IDs aus der Skyscanner API und zeigt Abweichungen an.

### Telegram Bot einrichten

1. Bot bei [@BotFather](https://t.me/BotFather) erstellen
2. Token in `backend/alerts.py` eintragen (`TELEGRAM_BOT_TOKEN`)
3. Chat-ID ueber [@userinfobot](https://t.me/userinfobot) herausfinden
4. Im Archiv-Tab einen Alert mit der Chat-ID erstellen

## Technologie

- **Backend:** Python 3.11+, FastAPI, SQLite, bcrypt
- **Frontend:** React 18, Vite
- **Karte:** Leaflet / react-leaflet
- **PDF:** fpdf2

## Disclaimer

Dieses Tool nutzt die interne Skyscanner API. Fuer kommerziellen Einsatz empfehle ich die [offizielle Affiliate API](https://www.partners.skyscanner.net/).
