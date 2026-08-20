"""FastAPI backend wrapping predict.py for the dashboard."""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import json
from pathlib import Path

from src.predict import predict_city, list_served_cities

app = FastAPI(title="AQI Predictor API")

# allow the vite dev server to call us
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

METRICS_PATH = Path("models/aqi_forecaster/metrics.json")


@app.get("/cities")
def cities():
    return list_served_cities()


@app.get("/forecast/{city_id}")
def forecast(city_id: str):
    try:
        return predict_city(city_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/metrics")
def metrics(city: str | None = None):
    if not METRICS_PATH.exists():
        raise HTTPException(status_code=404, detail="metrics.json not found")
    data = json.loads(METRICS_PATH.read_text())
    if city:
        data = [m for m in data if m["city"] == city]
    return data