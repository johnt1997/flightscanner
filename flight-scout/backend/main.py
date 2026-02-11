#!/usr/bin/env python3
"""
Flight Scout API - FastAPI Backend
"""

from fastapi import FastAPI, BackgroundTasks, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Optional
import asyncio
import uuid
import calendar
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from scraper import SkyscannerAPI, create_pdf_report, FlightDeal, PDF_DIR, CITY_DATABASE
import os
from database import (
    create_user, authenticate_user, create_token, verify_token,
    save_deal, get_user_deals, delete_deal,
    create_alert, get_user_alerts, delete_alert,
    log_search, get_all_users, get_search_log,
)
from alerts import check_alerts

app = FastAPI(title="Flight Scout API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory job storage (für Production: Redis oder DB)
jobs: dict = {}

# Airport Database
AIRPORTS = {
    "vie": {"id": "95673444", "name": "Wien", "code": "vie"},
    "bts": {"id": "95673445", "name": "Bratislava", "code": "bts"},
    "bud": {"id": "95673439", "name": "Budapest", "code": "bud"},
}

WEEKDAYS = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]


# --- Pydantic Models ---

class SearchRequest(BaseModel):
    airports: list[str]  # ["vie", "bts"]
    start_date: str  # "2026-03-20"
    end_date: str  # "2026-04-30"
    start_weekday: int  # 0=Mo, 4=Fr
    durations: list[int] = [2]  # Anzahl Nächte (mehrere möglich)
    adults: int = 1
    max_price: float = 70.0
    min_departure_hour: int = 14
    max_return_hour: int = 23
    blacklist_countries: list[str] = []
    search_mode: str = "everywhere"  # "everywhere" oder "cities"
    selected_cities: list[str] = []  # ["London", "Rom", ...]


class JobStatus(BaseModel):
    job_id: str
    status: str  # "pending", "running", "completed", "failed", "cancelled"
    progress: int  # 0-100
    message: str
    results: Optional[list] = None
    partial_results: Optional[list] = None
    new_deals: Optional[list] = None
    destinations_found: int = 0
    deals_found: int = 0
    pdf_path: Optional[str] = None


class AuthRequest(BaseModel):
    username: str
    password: str


class SaveDealRequest(BaseModel):
    city: str
    country: str
    price: float
    departure_date: str = ""
    return_date: str = ""
    flight_time: str = ""
    is_direct: bool = False
    url: str = ""
    origin: str = ""
    latitude: float = 0.0
    longitude: float = 0.0


class AlertRequest(BaseModel):
    destination_city: str
    max_price: float
    telegram_chat_id: str


class CalendarRequest(BaseModel):
    airports: list[str]
    month: str  # "2026-03"
    duration: int = 2
    adults: int = 1
    max_price: float = 70.0
    blacklist_countries: list[str] = []


# --- Auth Helper ---

def get_user_id(request: Request) -> int:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Nicht autorisiert")
    token = auth[7:]
    user_id = verify_token(token)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Ungültiger Token")
    return user_id


# --- Basic Endpoints ---

@app.get("/")
def root():
    # Serve frontend in production, API status in dev
    index = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist", "index.html")
    if os.path.isfile(index):
        return FileResponse(index)
    return {"status": "ok", "service": "Flight Scout API"}


@app.get("/airports")
def get_airports():
    return {"airports": AIRPORTS}


@app.get("/weekdays")
def get_weekdays():
    return {"weekdays": {i: name for i, name in enumerate(WEEKDAYS)}}


@app.get("/cities")
def get_cities():
    cities = {}
    for name, info in CITY_DATABASE.items():
        country = info["country"]
        if country not in cities:
            cities[country] = []
        cities[country].append(name)
    return {"cities": cities}


# --- Auth Endpoints ---

@app.post("/register")
def register(req: AuthRequest):
    if len(req.username) < 3:
        raise HTTPException(status_code=400, detail="Username muss mindestens 3 Zeichen haben")
    if len(req.password) < 4:
        raise HTTPException(status_code=400, detail="Passwort muss mindestens 4 Zeichen haben")
    user = create_user(req.username, req.password)
    if not user:
        raise HTTPException(status_code=409, detail="Username bereits vergeben")
    token = create_token(user["id"])
    return {"user_id": user["id"], "username": user["username"], "token": token}


@app.post("/login")
def login(req: AuthRequest):
    user = authenticate_user(req.username, req.password)
    if not user:
        raise HTTPException(status_code=401, detail="Ungültige Anmeldedaten")
    token = create_token(user["id"])
    return {"user_id": user["id"], "username": user["username"], "token": token}


# --- Deal Archive Endpoints ---

@app.post("/deals/save")
def save_deal_endpoint(deal: SaveDealRequest, request: Request):
    user_id = get_user_id(request)
    deal_id = save_deal(user_id, deal.model_dump())
    return {"id": deal_id, "message": "Deal gespeichert"}


@app.get("/deals")
def get_deals(request: Request):
    user_id = get_user_id(request)
    deals = get_user_deals(user_id)
    return {"deals": deals}


@app.delete("/deals/{deal_id}")
def delete_deal_endpoint(deal_id: int, request: Request):
    user_id = get_user_id(request)
    if not delete_deal(user_id, deal_id):
        raise HTTPException(status_code=404, detail="Deal nicht gefunden")
    return {"message": "Deal gelöscht"}


# --- Alert Endpoints ---

@app.post("/alerts")
def create_alert_endpoint(alert: AlertRequest, request: Request):
    user_id = get_user_id(request)
    alert_id = create_alert(user_id, alert.destination_city, alert.max_price, alert.telegram_chat_id)
    return {"id": alert_id, "message": "Alert erstellt"}


@app.get("/alerts")
def get_alerts(request: Request):
    user_id = get_user_id(request)
    alerts = get_user_alerts(user_id)
    return {"alerts": alerts}


@app.delete("/alerts/{alert_id}")
def delete_alert_endpoint(alert_id: int, request: Request):
    user_id = get_user_id(request)
    if not delete_alert(user_id, alert_id):
        raise HTTPException(status_code=404, detail="Alert nicht gefunden")
    return {"message": "Alert gelöscht"}


# --- Search Endpoints ---

# Rate limiting: max 3 searches per user per hour
search_history: dict[int, list[float]] = {}  # user_id -> list of timestamps
SEARCH_LIMIT = 3
SEARCH_WINDOW = 1800  # 30 minutes in seconds
ADMIN_USERS = {"john1997"}  # No rate limit for these users


def _get_username(user_id: int) -> str | None:
    from database import get_db
    conn = get_db()
    row = conn.execute("SELECT username FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return row["username"] if row else None


@app.post("/search", response_model=JobStatus)
def start_search(request: SearchRequest, background_tasks: BackgroundTasks, req: Request):
    # Auth check
    auth = req.headers.get("authorization", "")
    token = auth.replace("Bearer ", "") if auth.startswith("Bearer ") else ""
    user_id = verify_token(token) if token else None
    if not user_id:
        raise HTTPException(status_code=401, detail="Bitte zuerst anmelden.")

    # Rate limit check (skip for admins)
    username = _get_username(user_id)
    if username not in ADMIN_USERS:
        now = time.time()
        user_searches = search_history.get(user_id, [])
        user_searches = [t for t in user_searches if now - t < SEARCH_WINDOW]
        if len(user_searches) >= SEARCH_LIMIT:
            wait_minutes = int((SEARCH_WINDOW - (now - user_searches[0])) / 60) + 1
            raise HTTPException(status_code=429, detail=f"Maximal {SEARCH_LIMIT} Suchen pro Stunde. Warte noch {wait_minutes} Min.")
        user_searches.append(now)
        search_history[user_id] = user_searches

    # Log search to DB
    airports_str = ",".join(request.airports)
    log_search(user_id, request.search_mode, airports_str, request.start_date, request.end_date, request.max_price)

    job_id = str(uuid.uuid4())[:8]

    jobs[job_id] = {
        "status": "pending",
        "progress": 0,
        "message": "Job erstellt...",
        "results": None,
        "partial_results": [],
        "new_deals": [],
        "destinations_found": 0,
        "deals_found": 0,
        "cancelled": False,
        "pdf_path": None,
    }

    background_tasks.add_task(run_search, job_id, request)

    return JobStatus(
        job_id=job_id,
        status="pending",
        progress=0,
        message="Suche gestartet..."
    )


@app.get("/status/{job_id}", response_model=JobStatus)
def get_status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job nicht gefunden")

    job = jobs[job_id]
    new_deals = list(job.get("new_deals", []))
    job["new_deals"] = []

    return JobStatus(
        job_id=job_id,
        status=job["status"],
        progress=job["progress"],
        message=job["message"],
        results=job.get("results"),
        partial_results=job.get("partial_results") if job["status"] == "running" else None,
        new_deals=new_deals if new_deals else None,
        destinations_found=job.get("destinations_found", 0),
        deals_found=job.get("deals_found", 0),
        pdf_path=job.get("pdf_path"),
    )


@app.post("/stop/{job_id}")
def stop_search(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job nicht gefunden")
    jobs[job_id]["cancelled"] = True
    return {"message": "Suche wird gestoppt..."}


@app.get("/download/{job_id}")
def download_pdf(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job nicht gefunden")

    job = jobs[job_id]
    if not job.get("pdf_path"):
        raise HTTPException(status_code=400, detail="PDF noch nicht bereit")

    return FileResponse(
        job["pdf_path"],
        media_type="application/pdf",
        filename=f"FlightScout_{job_id}.pdf"
    )


# --- Admin Endpoints ---

def _require_admin(request: Request):
    user_id = get_user_id(request)
    username = _get_username(user_id)
    if username not in ADMIN_USERS:
        raise HTTPException(status_code=403, detail="Kein Zugriff")
    return user_id


@app.get("/admin/users")
def admin_users(request: Request):
    _require_admin(request)
    return {"users": get_all_users()}


@app.get("/admin/searches")
def admin_searches(request: Request, limit: int = 50):
    _require_admin(request)
    return {"searches": get_search_log(limit)}


# --- Calendar Endpoint ---

@app.post("/calendar")
def calendar_search(req: CalendarRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())[:8]

    jobs[job_id] = {
        "status": "pending",
        "progress": 0,
        "message": "Kalender-Suche gestartet...",
        "results": None,
        "pdf_path": None,
    }

    background_tasks.add_task(run_calendar_search, job_id, req)

    return {"job_id": job_id, "status": "pending", "message": "Kalender-Suche gestartet..."}


# --- Background Tasks ---

def _deal_to_dict(d: FlightDeal) -> dict:
    return {
        "city": d.city,
        "country": d.country,
        "price": d.price,
        "departure_date": d.departure_date,
        "return_date": d.return_date,
        "flight_time": d.flight_time,
        "return_flight_time": d.return_flight_time,
        "is_direct": d.is_direct,
        "url": d.url,
        "origin": getattr(d, 'origin', 'Unknown'),
        "latitude": d.latitude,
        "longitude": d.longitude,
        "early_departure": d.early_departure,
        "alternatives": d.alternatives,
    }


def run_search(job_id: str, request: SearchRequest):
    """Background task für die Flugsuche"""
    try:
        job = jobs[job_id]
        job["status"] = "running"
        job["message"] = "Initialisiere Suche..."

        all_deals: list[FlightDeal] = []
        seen_cities: set[str] = set()
        progress_lock = threading.Lock()

        start_date = datetime.strptime(request.start_date, "%Y-%m-%d")
        end_date = datetime.strptime(request.end_date, "%Y-%m-%d")

        durations = request.durations or [2]

        # Berechne totale Trips für granulares Progress
        valid_airports = [a for a in request.airports if a in AIRPORTS]
        total_trips = 0
        for airport_code in valid_airports:
            airport = AIRPORTS[airport_code]
            temp_scraper = SkyscannerAPI(origin_entity_id=airport["id"], origin_sky_code=airport["code"])
            for dur in durations:
                total_trips += len(temp_scraper.generate_trips(start_date, end_date, request.start_weekday, dur))
        completed_trips = 0

        def on_deals(trip_deals: list[FlightDeal], airport_name: str):
            nonlocal seen_cities
            with progress_lock:
                for deal in trip_deals:
                    deal.origin = airport_name
                all_deals.extend(trip_deals)
                new_dicts = [_deal_to_dict(d) for d in trip_deals]
                job["partial_results"] = [_deal_to_dict(d) for d in sorted(all_deals, key=lambda x: x.price)]
                job["new_deals"].extend(new_dicts)
                job["deals_found"] = len(all_deals)
                for d in trip_deals:
                    seen_cities.add(d.city)
                job["destinations_found"] = len(seen_cities)

        def on_status(message: str):
            with progress_lock:
                job["message"] = message

        def on_progress(trip_idx: int, trip_total: int):
            nonlocal completed_trips
            with progress_lock:
                completed_trips += 1
                job["progress"] = min(int((completed_trips / max(total_trips, 1)) * 90), 90)

        def cancel_check():
            return job.get("cancelled", False)

        is_city_mode = request.search_mode == "cities" and request.selected_cities

        for airport_code in valid_airports:
            if cancel_check():
                break
            airport = AIRPORTS[airport_code]

            for dur in durations:
                if cancel_check():
                    break

                scraper = SkyscannerAPI(
                    origin_entity_id=airport["id"],
                    adults=request.adults,
                    start_hour=request.min_departure_hour,
                    origin_sky_code=airport["code"],
                    max_return_hour=request.max_return_hour,
                )
                scraper.MAX_PRICE = request.max_price

                if is_city_mode:
                    city_names = ", ".join(request.selected_cities[:3])
                    if len(request.selected_cities) > 3:
                        city_names += f" +{len(request.selected_cities) - 3}"
                    job["message"] = f"Suche {city_names} ab {airport['name']} ({dur} {'Nacht' if dur == 1 else 'Nächte'})..."

                    scraper.run_city_search(
                        cities=request.selected_cities,
                        start_date=start_date,
                        end_date=end_date,
                        start_weekday=request.start_weekday,
                        duration=dur,
                        cancel_check=cancel_check,
                        on_deals=lambda deals, an=airport["name"]: on_deals(deals, an),
                        on_progress=on_progress,
                        on_status=on_status,
                    )
                else:
                    job["message"] = f"Suche ab {airport['name']} ({dur} {'Nacht' if dur == 1 else 'Nächte'})..."

                    if request.blacklist_countries:
                        scraper.BLACKLIST_COUNTRIES = request.blacklist_countries

                    scraper.run(
                        start_date=start_date,
                        end_date=end_date,
                        start_weekday=request.start_weekday,
                        duration=dur,
                        cancel_check=cancel_check,
                        on_deals=lambda deals, an=airport["name"]: on_deals(deals, an),
                        on_progress=on_progress,
                        on_status=on_status,
                    )

        was_cancelled = job.get("cancelled", False)

        job["progress"] = 95
        job["message"] = "Erstelle Report..."

        # PDF generieren
        pdf_filename = os.path.join(PDF_DIR, f"flight_report_{job_id}.pdf")
        origin_names = ", ".join([AIRPORTS[a]["name"] for a in valid_airports])
        create_pdf_report(all_deals, origin_names, filename=pdf_filename)

        # Final results
        results = [_deal_to_dict(d) for d in sorted(all_deals, key=lambda x: x.price)]

        job["status"] = "cancelled" if was_cancelled else "completed"
        job["progress"] = 100
        job["message"] = f"{'Gestoppt' if was_cancelled else 'Fertig'}! {len(results)} Deals gefunden."
        job["results"] = results
        job["pdf_path"] = pdf_filename

        # Check Telegram alerts
        try:
            check_alerts(results)
        except Exception as e:
            print(f"Alert check error: {e}")

    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["message"] = f"Fehler: {str(e)}"
        jobs[job_id]["progress"] = 0


def _search_calendar_day(dep_date: datetime, ret_date: datetime, req: CalendarRequest) -> dict:
    """Sucht Deals für einen einzelnen Tag (wird parallel aufgerufen)."""
    day_deals = []

    for airport_code in req.airports:
        if airport_code not in AIRPORTS:
            continue
        airport = AIRPORTS[airport_code]

        scraper = SkyscannerAPI(
            origin_entity_id=airport["id"],
            adults=req.adults,
            start_hour=0,
            origin_sky_code=airport["code"],
        )
        if req.blacklist_countries:
            scraper.BLACKLIST_COUNTRIES = req.blacklist_countries
        scraper.MAX_PRICE = req.max_price

        data = scraper.search_flights(dep_date, ret_date)
        if not data:
            continue

        results = data.get("everywhereDestination", {}).get("results", [])
        for result in results:
            if result.get("type") != "LOCATION":
                continue
            content = result.get("content", {})
            location = content.get("location", {})
            fq = content.get("flightQuotes", {})
            if not fq:
                continue
            raw_price = fq.get("cheapest", {}).get("rawPrice", 9999)
            price_pp = raw_price / req.adults
            if price_pp <= req.max_price and location.get("type") == "Nation":
                # Skyscanner-Link bauen
                sky_code = location.get("skyCode", "")
                url = (
                    f"https://www.skyscanner.at/transport/fluge/{airport['code']}/{sky_code.lower()}/"
                    f"{dep_date.strftime('%y%m%d')}/{ret_date.strftime('%y%m%d')}/"
                    f"?adultsv2={req.adults}&cabinclass=economy&rtn=1&preferdirects=true"
                )
                day_deals.append({
                    "country": location.get("name", "?"),
                    "price": round(price_pp, 2),
                    "origin": airport["name"],
                    "url": url,
                })

    if day_deals:
        min_price = min(d["price"] for d in day_deals)
        return {
            "date": dep_date.strftime("%Y-%m-%d"),
            "min_price": round(min_price, 2),
            "deals_count": len(day_deals),
            "deals": sorted(day_deals, key=lambda x: x["price"])[:5],
        }
    else:
        return {
            "date": dep_date.strftime("%Y-%m-%d"),
            "min_price": None,
            "deals_count": 0,
            "deals": [],
        }


def run_calendar_search(job_id: str, req: CalendarRequest):
    """Background task für die Kalender-Suche - scannt jeden Tag im Monat (parallel)"""
    try:
        jobs[job_id]["status"] = "running"

        year, month = map(int, req.month.split("-"))
        num_days = calendar.monthrange(year, month)[1]
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        # Vergangene Tage sofort abfertigen, zukünftige sammeln
        results_by_day = {}
        future_days = []

        for day in range(1, num_days + 1):
            dep_date = datetime(year, month, day)
            if dep_date < today:
                results_by_day[day] = {
                    "date": dep_date.strftime("%Y-%m-%d"),
                    "min_price": None,
                    "deals_count": 0,
                    "deals": [],
                }
            else:
                future_days.append(day)

        total_future = len(future_days)
        processed = 0

        # Parallel mit max 3 gleichzeitigen Requests
        with ThreadPoolExecutor(max_workers=3) as executor:
            future_to_day = {}
            for day in future_days:
                dep_date = datetime(year, month, day)
                ret_date = dep_date + timedelta(days=req.duration)
                future = executor.submit(_search_calendar_day, dep_date, ret_date, req)
                future_to_day[future] = day

            for future in as_completed(future_to_day):
                day = future_to_day[future]
                try:
                    results_by_day[day] = future.result()
                except Exception as e:
                    print(f"[CALENDAR] Fehler Tag {day}: {e}")
                    results_by_day[day] = {
                        "date": datetime(year, month, day).strftime("%Y-%m-%d"),
                        "min_price": None,
                        "deals_count": 0,
                        "deals": [],
                    }
                processed += 1
                jobs[job_id]["progress"] = int((processed / total_future) * 95) if total_future else 95
                jobs[job_id]["message"] = f"Prüfe Tage... ({processed}/{total_future})"

        # Ergebnisse in Reihenfolge sortieren
        dates_data = [results_by_day[day] for day in range(1, num_days + 1)]

        jobs[job_id]["status"] = "completed"
        jobs[job_id]["progress"] = 100
        jobs[job_id]["message"] = f"Kalender fertig!"
        jobs[job_id]["results"] = dates_data

    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["message"] = f"Fehler: {str(e)}"
        jobs[job_id]["progress"] = 0


# Serve frontend static files (production build)
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.isdir(FRONTEND_DIR):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIR, "assets")), name="static")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        """Serve frontend for all non-API routes (SPA fallback)."""
        file_path = os.path.join(FRONTEND_DIR, full_path)
        if full_path and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
