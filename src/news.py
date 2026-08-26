"""GNews-backed Pakistan air-quality news."""

import os
import time
import logging
from datetime import datetime, timedelta, timezone

import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://gnews.io/api/v4/search"
API_KEY = os.getenv("GNEWS_API_KEY")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cache the feed; free tier data is 12h delayed so 1h costs us nothing.
_CACHE = {"ts": 0.0, "data": []}
_CACHE_TTL = 3600


# Focused queries beat one huge OR query. Trimmed to cut request cost.
AQI_QUERIES = [
    '"Pakistan" AND "air quality"',
    '"Pakistan" AND smog',
    '"Pakistan" AND AQI',
    '"Lahore" AND smog',
    '"Karachi" AND "air quality"',
]


def _fetch_query(query: str, max_items: int = 10) -> list[dict]:
    """Fetch articles for one GNews search query."""

    if not API_KEY:
        logger.error("GNEWS_API_KEY is missing from .env")
        return []

    # Only get fairly recent news.
    from_date = (
        datetime.now(timezone.utc) - timedelta(days=14)
    ).isoformat(timespec="seconds").replace("+00:00", "Z")

    params = {
        "q": query,
        "lang": "en",
        "max": max_items,
        "sortby": "publishedAt",
        "from": from_date,
        "apikey": API_KEY,
    }

    try:
        response = requests.get(
            BASE_URL,
            params=params,
            timeout=10,
        )

        # Helpful during development.
        if not response.ok:
            logger.error(
                "GNews request failed | status=%s | query=%s | response=%s",
                response.status_code,
                query,
                response.text[:500],
            )

        response.raise_for_status()

        data = response.json()

        logger.info(
            "Query '%s' returned %s available articles",
            query,
            data.get("totalArticles", 0),
        )

        return data.get("articles", [])

    except requests.exceptions.Timeout:
        logger.error("GNews timeout for query: %s", query)

    except requests.exceptions.HTTPError as exc:
        logger.error("GNews HTTP error for '%s': %s", query, exc)

    except requests.exceptions.RequestException as exc:
        logger.error("GNews request error for '%s': %s", query, exc)

    except ValueError:
        logger.error("GNews returned invalid JSON for query: %s", query)

    return []


def _is_relevant_article(article: dict) -> bool:
    """Filter articles that don't appear related to Pakistan AQI."""

    title = article.get("title", "")
    description = article.get("description", "")

    text = f"{title} {description}".lower()

    pakistan_terms = [
        "pakistan",
        "lahore",
        "karachi",
        "punjab",
        "islamabad",
        "rawalpindi",
        "peshawar",
    ]

    air_quality_terms = [
        "air quality",
        "aqi",
        "smog",
        "air pollution",
        "pollution",
        "particulate matter",
        "pm2.5",
        "pm10",
    ]

    has_location = any(term in text for term in pakistan_terms)
    has_aqi_topic = any(term in text for term in air_quality_terms)

    return has_location and has_aqi_topic


def fetch_aqi_news(max_items: int = 6) -> list[dict]:
    """
    Return recent Pakistan air-quality news.

    Output:
    [
        {
            "title": "...",
            "url": "...",
            "source": "...",
            "published_at": "...",
            "description": "...",
            "image": "..."
        }
    ]
    """

    if not API_KEY:
        logger.error(
            "GNEWS_API_KEY was not found. "
            "Make sure your .env contains GNEWS_API_KEY=your_key"
        )
        return []

    # Serve from cache when fresh; slice per caller.
    now = time.time()
    if _CACHE["data"] and now - _CACHE["ts"] < _CACHE_TTL:
        logger.info("Serving AQI news from cache (%d items)", len(_CACHE["data"]))
        return _CACHE["data"][:max_items]

    all_articles = []

    # Get several results from each query.
    per_query = min(max(max_items, 5), 10)

    for query in AQI_QUERIES:
        articles = _fetch_query(
            query=query,
            max_items=per_query,
        )

        all_articles.extend(articles)

    # -------------------------------------------------
    # Remove duplicates
    # -------------------------------------------------

    unique_articles = {}

    for article in all_articles:
        url = article.get("url")

        if not url:
            continue

        if not _is_relevant_article(article):
            continue

        # URL provides a convenient unique identifier.
        if url not in unique_articles:
            unique_articles[url] = article

    articles = list(unique_articles.values())

    # -------------------------------------------------
    # Sort newest first
    # -------------------------------------------------

    articles.sort(
        key=lambda x: x.get("publishedAt", ""),
        reverse=True,
    )

    # -------------------------------------------------
    # Return clean dashboard-friendly structure
    # -------------------------------------------------

    results = []

    for article in articles:
        source = article.get("source") or {}

        results.append(
            {
                "title": article.get("title") or "Untitled article",
                "description": article.get("description") or "",
                "url": article.get("url") or "",
                "source": source.get("name") or "Unknown source",
                "published_at": article.get("publishedAt") or "",
                "image": article.get("image") or "",
            }
        )

    # Cache only non-empty feeds, so a bad fetch never sticks.
    if results:
        _CACHE["ts"] = now
        _CACHE["data"] = results

    logger.info("Returning %d AQI news articles", len(results))

    return results[:max_items]