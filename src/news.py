"""Pakistan air-quality news via GNews."""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

_BASE = "https://gnews.io/api/v4/search"


def fetch_aqi_news(max_items: int = 6) -> list[dict]:
    """Return recent Pakistan air-quality news: title, url, source, date."""
    key = os.getenv("GNEWS_API_KEY")
    if not key:
        return []

    query = "Pakistan air quality OR Pakistan smog OR Pakistan AQI OR Pakistan pollution"
    params = {
        "q": query,
        "lang": "en",
        "max": max_items,
        "sortby": "publishedAt",
        "apikey": key,
    }
    try:
        resp = requests.get(_BASE, params=params, timeout=8)
        resp.raise_for_status()
        articles = resp.json().get("articles", [])
        return [
            {
                "title": a.get("title", ""),
                "url": a.get("url", ""),
                "source": a.get("source", {}).get("name", ""),
                "published_at": a.get("publishedAt", ""),
            }
            for a in articles
            if a.get("url")
        ]
    except Exception:
        return []