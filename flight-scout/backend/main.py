#!/usr/bin/env python3
"""
Flight Scout API - FastAPI Backend
"""

from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
import asyncio
import uuid

from scraper import SkyscannerAPI, create_pdf_report, FlightDeal

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


class SearchRequest(BaseModel):
    airports: list[str]  # ["vie", "bts"]
    start_date: str  # "2026-03-20"
    end_date: str  # "2026-04-30"
    start_weekday: int  # 0=Mo, 4=Fr
    duration: int  # Anzahl Nächte
    adults: int = 1
    max_price: float = 70.0
    min_departure_hour: int = 14
    whitelist_countries: list[str] = []


class JobStatus(BaseModel):
    job_id: str
    status: str  # "pending", "running", "completed", "failed"
    progress: int  # 0-100
    message: str
    results: Optional[list] = None
    pdf_path: Optional[str] = None


@app.get("/")
def root():
    return {"status": "ok", "service": "Flight Scout API"}


@app.get("/airports")
def get_airports():
    return {"airports": AIRPORTS}


@app.get("/weekdays")
def get_weekdays():
    return {"weekdays": {i: name for i, name in enumerate(WEEKDAYS)}}


@app.post("/search", response_model=JobStatus)
def start_search(request: SearchRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())[:8]
    
    jobs[job_id] = {
        "status": "pending",
        "progress": 0,
        "message": "Job erstellt...",
        "results": None,
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
    return JobStatus(
        job_id=job_id,
        status=job["status"],
        progress=job["progress"],
        message=job["message"],
        results=job.get("results"),
        pdf_path=job.get("pdf_path"),
    )


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


def run_search(job_id: str, request: SearchRequest):
    """Background task für die Flugsuche"""
    try:
        jobs[job_id]["status"] = "running"
        jobs[job_id]["message"] = "Initialisiere Suche..."
        
        all_deals: list[FlightDeal] = []
        total_airports = len(request.airports)
        
        start_date = datetime.strptime(request.start_date, "%Y-%m-%d")
        end_date = datetime.strptime(request.end_date, "%Y-%m-%d")
        
        for i, airport_code in enumerate(request.airports):
            if airport_code not in AIRPORTS:
                continue
            
            airport = AIRPORTS[airport_code]
            jobs[job_id]["message"] = f"Suche Flüge ab {airport['name']}..."
            jobs[job_id]["progress"] = int((i / total_airports) * 80)
            
            scraper = SkyscannerAPI(
                origin_entity_id=airport["id"],
                adults=request.adults,
                start_hour=request.min_departure_hour,
                origin_sky_code=airport["code"],
            )
            
            # Whitelist setzen wenn vorhanden
            if request.whitelist_countries:
                scraper.WHITELIST_COUNTRIES = request.whitelist_countries
            
            scraper.MAX_PRICE = request.max_price
            
            scraper.run(
                start_date=start_date,
                end_date=end_date,
                start_weekday=request.start_weekday,
                duration=request.duration,
            )
            
            # Airport-Info zu jedem Deal hinzufügen
            for deal in scraper.deals:
                deal.origin = airport["name"]
            
            all_deals.extend(scraper.deals)
        
        jobs[job_id]["progress"] = 90
        jobs[job_id]["message"] = "Erstelle Report..."
        
        # PDF generieren
        pdf_filename = f"flight_report_{job_id}.pdf"
        origin_names = ", ".join([AIRPORTS[a]["name"] for a in request.airports if a in AIRPORTS])
        create_pdf_report(all_deals, origin_names, filename=pdf_filename)
        
        # Results formatieren
        results = [
            {
                "city": d.city,
                "country": d.country,
                "price": d.price,
                "departure_date": d.departure_date,
                "return_date": d.return_date,
                "flight_time": d.flight_time,
                "is_direct": d.is_direct,
                "url": d.url,
                "origin": getattr(d, 'origin', 'Unknown'),
                "latitude": d.latitude,    # NEU
                "longitude": d.longitude,  # NEU
            }
            for d in sorted(all_deals, key=lambda x: x.price)
        ]
        
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["progress"] = 100
        jobs[job_id]["message"] = f"Fertig! {len(results)} Deals gefunden."
        jobs[job_id]["results"] = results
        jobs[job_id]["pdf_path"] = pdf_filename
        
    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["message"] = f"Fehler: {str(e)}"
        jobs[job_id]["progress"] = 0


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
