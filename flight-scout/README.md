# Flight Scout

Finde die guenstigsten Wochenend-Fluege ab Wien, Bratislava und Budapest.

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
- **Heatmap** -- Deals auf der Karte (Leaflet) mit Routenlinien
- **Kalender-Heatmap** -- Guenstigster Preis pro Tag im Monatsuberblick
- **Deal-Archiv** -- Deals speichern und verwalten (mit User-Auth)
- **Telegram Deal-Alerts** -- Taegliche Benachrichtigung ueber guenstige Wochenend-Fluege per Telegram (7:00 UTC)
- **Wetter-Anzeige** -- Wetter-Icons mit Temperatur-Tooltip pro Destination (Open-Meteo API)
- **Gruppierte Ergebnisse** -- Deals nach Stadt gruppiert mit Akkordeon-UI
- **Favoriten-Staedte** -- Lieblingsstaedte markieren, werden oben angezeigt
- **Share-Button** -- Deal als formatierte Telegram-Karte in die Zwischenablage kopieren
- **Dark/Light Mode** -- Theme umschaltbar, wird gespeichert
- **Caching** -- SQLite-Cache fuer Everywhere-Ergebnisse (3h TTL), spart Proxy-Bandbreite
- **Proxy-Support** -- Residential Proxies mit automatischer Rotation und 407-Retry
- **403-Fallback** -- Bei API-Blockade werden Country-Level Preise als Fallback verwendet
- **Rate Limiting** -- Max. 3 Suchen pro 30 Min. pro User (Admins ausgenommen)
- **Admin Dashboard** -- User-Uebersicht und Suchverlauf (nur fuer Admins)
- **About Me** -- Persoenliche Info-Seite

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

### Umgebungsvariablen

| Variable | Beschreibung |
|----------|--------------|
| `PROXY_URL` | Residential Proxies (mehrere mit `;` getrennt) |
| `TELEGRAM_BOT_TOKEN` | Telegram Bot Token fuer Deal-Alerts |
| `FLIGHT_SCOUT_SECRET` | Secret fuer Auth-Token-Signierung |
| `PORT` | Server-Port (Standard: 8000) |

## API Endpoints

| Method | Endpoint | Beschreibung |
|--------|----------|--------------|
| GET | `/airports` | Liste aller Flughaefen |
| GET | `/cities` | Liste aller Staedte nach Land |
| POST | `/search` | Startet Flugsuche (Auth) |
| GET | `/status/{job_id}` | Job-Status abfragen |
| POST | `/stop/{job_id}` | Laufende Suche abbrechen |
| GET | `/download/{job_id}` | PDF herunterladen |
| POST | `/register` | User registrieren |
| POST | `/login` | User anmelden |
| POST | `/deals/save` | Deal ins Archiv speichern (Auth) |
| GET | `/deals` | Gespeicherte Deals abrufen (Auth) |
| DELETE | `/deals/{id}` | Deal aus Archiv loeschen (Auth) |
| POST | `/deal-alerts` | Deal-Alert erstellen (Auth, max. 2) |
| GET | `/deal-alerts` | Deal-Alerts abrufen (Auth) |
| DELETE | `/deal-alerts/{id}` | Deal-Alert loeschen (Auth) |
| POST | `/calendar` | Kalender-Preisdaten fuer einen Monat |
| GET | `/admin/users` | User-Liste (Admin) |
| GET | `/admin/searches` | Suchverlauf (Admin) |
| POST | `/admin/test-alerts` | Alert-Check manuell ausloesen (Admin) |

## Architektur

- **Datenbank:** SQLite (`flight_scout.db`) mit Tabellen: `users`, `saved_deals`, `deal_alerts`, `search_cache`, `search_log`
- **Auth:** Token-basiert (HMAC), Passwoerter mit bcrypt gehasht
- **Telegram Alerts:** Hintergrund-Thread checkt taeglich um 7:00 UTC alle aktiven Alerts via Everywhere-Suche. Bot-Token als Umgebungsvariable `TELEGRAM_BOT_TOKEN`.
- **Caching:** Everywhere-Ergebnisse werden 3h in SQLite gecached. Gleiche Suche = kein erneuter API-Call.
- **Proxies:** Residential Proxies mit automatischer Rotation. 407-Fehler werden sofort mit neuem Proxy wiederholt, 403-Fehler (Skyscanner-Block) mit Wartezeit.
- **API-Strategie:** Everywhere-Suche -> Country-Suche -> City-Detail-Calls. Bei 403-Block wird auf Country-Level Preise zurueckgefallen.
- **Parallelisierung:** Bis zu 3 Trips gleichzeitig (ThreadPoolExecutor), Kalendersuche ebenfalls parallel.

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

### Telegram Bot einrichten

1. Bot bei [@BotFather](https://t.me/BotFather) erstellen
2. `TELEGRAM_BOT_TOKEN` als Umgebungsvariable setzen
3. Chat-ID ueber [@userinfobot](https://t.me/userinfobot) herausfinden
4. Im Archiv-Tab einen Alert mit der Chat-ID erstellen

## Technologie

- **Backend:** Python 3.11+, FastAPI, SQLite, bcrypt
- **Frontend:** React 18, Vite
- **Karte:** Leaflet / react-leaflet
- **Wetter:** Open-Meteo API (kostenlos, kein Key)
- **PDF:** fpdf2
- **Deployment:** Docker, Railway

## Disclaimer

Dieses Tool nutzt die interne Skyscanner API. Fuer kommerziellen Einsatz empfehle ich die [offizielle Affiliate API](https://www.partners.skyscanner.net/).
