from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from typing import Optional
import random

app = FastAPI(title="NagarAI SOS API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

ZONES = ["Zone A", "Zone B", "Zone C"]
readings = {}
alerts = []
reports = []
history = []
alert_counter = 1
report_counter = 1

def risk_score(water, rainfall, rise):
    # Explainable prototype score; tune thresholds with real local data before deployment.
    score = min(100, max(0, 0.40 * min(water / 100 * 100, 100) +
                         0.35 * min(rainfall / 100 * 100, 100) +
                         0.25 * min(rise / 10 * 100, 100)))
    level = "CRITICAL" if score >= 75 else "HIGH" if score >= 55 else "MODERATE" if score >= 30 else "LOW"
    return round(score), level

def recommendation(level):
    return {
        "CRITICAL": "Issue evacuation warning; notify emergency response teams immediately.",
        "HIGH": "Deploy field teams and prepare evacuation routes.",
        "MODERATE": "Increase monitoring frequency and inspect drainage.",
        "LOW": "Continue routine monitoring."
    }[level]

def make_reading(zone, water=None, rainfall=None, rise=None):
    water = round(water if water is not None else random.uniform(10, 45), 1)
    rainfall = round(rainfall if rainfall is not None else random.uniform(0, 35), 1)
    rise = round(rise if rise is not None else random.uniform(0, 2.5), 1)
    score, level = risk_score(water, rainfall, rise)
    return {"zone": zone, "water_level_cm": water, "rainfall_mm_hr": rainfall,
            "rise_rate_cm_hr": rise, "risk_score": score, "risk_level": level,
            "recommendation": recommendation(level), "timestamp": datetime.now(timezone.utc).isoformat()}

def record_reading(item):
    readings[item["zone"]] = item
    history.append(item)
    if len(history) > 500: history.pop(0)
    if item["risk_level"] in ("HIGH", "CRITICAL"):
        global alert_counter
        existing = next((a for a in alerts if a["zone"] == item["zone"] and a["status"] == "ACTIVE"), None)
        if not existing:
            alerts.insert(0, {"id": alert_counter, "zone": item["zone"], "level": item["risk_level"],
                              "score": item["risk_score"], "message": item["recommendation"],
                              "status": "ACTIVE", "created_at": item["timestamp"]})
            alert_counter += 1
    return item

for z in ZONES:
    record_reading(make_reading(z))

class SimulationRequest(BaseModel):
    scenario: str = Field(pattern="^(normal|heavy_rain|rising_water|reset)$")

class SOSRequest(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    phone: str = Field(min_length=5, max_length=20)
    zone: str
    description: str = Field(min_length=5, max_length=1000)
    latitude: Optional[float] = None
    longitude: Optional[float] = None

@app.get("/")
def root():
    return {"name": "NagarAI SOS API", "status": "running", "docs": "/docs"}

@app.get("/api/dashboard")
def dashboard():
    items = [readings[z] for z in ZONES]
    highest = max(items, key=lambda x: x["risk_score"])
    return {"zones": items, "overall_risk": highest["risk_level"],
            "overall_score": highest["risk_score"], "active_alerts": sum(a["status"] == "ACTIVE" for a in alerts),
            "updated_at": datetime.now(timezone.utc).isoformat()}

@app.get("/api/readings")
def get_readings():
    return list(readings.values())

@app.get("/api/history")
def get_history(limit: int = 50):
    return history[-max(1, min(limit, 500)):]

@app.get("/api/alerts")
def get_alerts():
    return alerts

@app.post("/api/alerts/{alert_id}/acknowledge")
def acknowledge(alert_id: int):
    alert = next((a for a in alerts if a["id"] == alert_id), None)
    if not alert: raise HTTPException(404, "Alert not found")
    alert["status"] = "ACKNOWLEDGED"
    return alert

@app.post("/api/simulate")
def simulate(req: SimulationRequest):
    for z in ZONES:
        if req.scenario == "heavy_rain":
            item = make_reading(z, random.uniform(65, 95), random.uniform(75, 120), random.uniform(3, 7))
        elif req.scenario == "rising_water":
            item = make_reading(z, random.uniform(75, 100), random.uniform(25, 55), random.uniform(7, 10))
        elif req.scenario == "reset":
            item = make_reading(z, random.uniform(8, 25), random.uniform(0, 12), random.uniform(0, 1))
        else:
            item = make_reading(z, random.uniform(10, 40), random.uniform(0, 30), random.uniform(0, 2))
        record_reading(item)
    return dashboard()

@app.post("/api/sos")
def create_sos(req: SOSRequest):
    global report_counter
    if req.zone not in ZONES: raise HTTPException(400, "Unknown zone")
    report = {"id": report_counter, **req.model_dump(), "status": "RECEIVED",
              "created_at": datetime.now(timezone.utc).isoformat()}
    report_counter += 1
    reports.insert(0, report)
    return report

@app.get("/api/sos")
def list_sos():
    return reports

@app.get("/api/health")
def health():
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}
