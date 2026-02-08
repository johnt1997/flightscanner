# Flight Scout

Finde die günstigsten Wochenend-Flüge ab Wien, Bratislava und Budapest.

## Features

- **Multi-Airport Suche** – Wien, Bratislava, Budapest gleichzeitig
- **Flexible Zeiträume** – Fr-So, Do-So, Mo-Mi, etc.
- **Preisfilter** – Max. Preis pro Person
- **Zeitfilter** – Keine Flüge vor X Uhr
- **Länder-Blacklist** – Bestimmte Länder ausschließen
- **PDF Report** – Download für offline
- **Direkte Buchungslinks** – Skyscanner URLs
- **Heatmap** – Deals auf der Karte (Leaflet)
- **Kalender-Heatmap** – Günstigster Preis pro Tag im Monatsüberblick
- **Deal-Archiv** – Deals speichern und verwalten (mit User-Auth)
- **Telegram Preis-Alerts** – Benachrichtigung wenn ein Deal unter deinem Wunschpreis liegt

## Setup

### Backend (FastAPI)

```bash
cd backend
pip install -r requirements.txt
python main.py
```

API läuft auf http://localhost:8000

### Frontend (React + Vite)

```bash
cd frontend
npm install
npm run dev
```

Frontend läuft auf http://localhost:3000

## API Endpoints

| Method | Endpoint | Beschreibung |
|--------|----------|--------------|
| GET | `/airports` | Liste aller Flughäfen |
| POST | `/search` | Startet Flugsuche |
| GET | `/status/{job_id}` | Job-Status abfragen |
| GET | `/download/{job_id}` | PDF herunterladen |
| POST | `/register` | User registrieren |
| POST | `/login` | User anmelden |
| POST | `/deals/save` | Deal ins Archiv speichern (Auth) |
| GET | `/deals` | Gespeicherte Deals abrufen (Auth) |
| DELETE | `/deals/{id}` | Deal aus Archiv löschen (Auth) |
| POST | `/alerts` | Preis-Alert erstellen (Auth) |
| GET | `/alerts` | Alerts abrufen (Auth) |
| DELETE | `/alerts/{id}` | Alert löschen (Auth) |
| POST | `/calendar` | Kalender-Preisdaten für einen Monat |

## Architektur

- **Datenbank:** SQLite (`flight_scout.db`) mit Tabellen: `users`, `saved_deals`, `price_alerts`
- **Auth:** Token-basiert (HMAC), Passwörter mit bcrypt gehasht
- **Telegram Alerts:** Werden nach jeder manuellen Suche geprüft. Bot-Token in `backend/alerts.py` konfigurieren.

## Konfiguration

### Neuen Flughafen hinzufügen

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

Die Entity-ID findest du in den Skyscanner Network Requests.

### Telegram Bot einrichten

1. Bot bei [@BotFather](https://t.me/BotFather) erstellen
2. Token in `backend/alerts.py` eintragen (`TELEGRAM_BOT_TOKEN`)
3. Chat-ID über [@userinfobot](https://t.me/userinfobot) herausfinden
4. Im Archiv-Tab einen Alert mit der Chat-ID erstellen

## Technologie

- **Backend:** Python 3.11+, FastAPI, SQLite, bcrypt
- **Frontend:** React 18, Vite
- **Karte:** Leaflet / react-leaflet
- **PDF:** fpdf2

## Disclaimer

Dieses Tool nutzt die interne Skyscanner API. Für kommerziellen Einsatz empfehle ich die [offizielle Affiliate API](https://www.partners.skyscanner.net/).
