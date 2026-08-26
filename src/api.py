"""FastAPI backend wrapping predict.py for the dashboard."""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import json
from pathlib import Path
import os
from src.cities import get_city
from src.predict import predict_city, list_served_cities
from src.ai_summary import summarize_forecast

from src.news import fetch_aqi_news

app = FastAPI(title="AQI Predictor API")

allowed_origins = ["http://localhost:5173"]

frontend_origin = os.getenv("FRONTEND_ORIGIN")
if frontend_origin:
    allowed_origins.append(frontend_origin)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

METRICS_PATH = Path("models/aqi_forecaster/metrics.json")


@app.get("/cities")
def cities():
    return list_served_cities()


@app.get("/news")
def get_news():
    articles = fetch_aqi_news(max_items=6)

    print("=" * 50)
    print("NEWS ARTICLES:", articles)
    print("NUMBER OF ARTICLES:", len(articles))
    print("=" * 50)

    return articles

@app.get("/metrics")
def metrics(city: str | None = None):
    if not METRICS_PATH.exists():
        raise HTTPException(status_code=404, detail="metrics.json not found")
    data = json.loads(METRICS_PATH.read_text())
    if city:
        data = [m for m in data if m["city"] == city]
    return data



@app.get("/forecast/{city_id}")
def forecast(city_id: str):
    try:
        result = predict_city(city_id)
        result["ai_summary"] = summarize_forecast(result)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))