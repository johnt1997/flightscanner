# ✈️ Flight Scout

Finde die günstigsten Wochenend-Flüge ab Wien, Bratislava und Budapest.

![Flight Scout](https://via.placeholder.com/800x400/0f172a/6366f1?text=Flight+Scout)

## Features

- 🛫 **Multi-Airport Suche** – Wien, Bratislava, Budapest gleichzeitig
- 📅 **Flexible Zeiträume** – Fr-So, Do-So, Mo-Mi, etc.
- 💰 **Preisfilter** – Max. Preis pro Person
- ⏰ **Zeitfilter** – Keine Flüge vor X Uhr
- 🌍 **Länder-Whitelist** – Nur bestimmte Ziele
- 📄 **PDF Report** – Download für offline
- 🔗 **Direkte Buchungslinks** – Skyscanner URLs

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

## Technologie

- **Backend:** Python 3.11+, FastAPI, Requests
- **Frontend:** React 18, Vite, Tailwind-inspired CSS
- **PDF:** fpdf2

## Disclaimer

Dieses Tool nutzt die interne Skyscanner API. Für kommerziellen Einsatz empfehle ich die [offizielle Affiliate API](https://www.partners.skyscanner.net/).

---

Made with ☕ and Python
