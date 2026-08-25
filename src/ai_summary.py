"""Groq-generated structured summary of a city's AQI forecast."""
import os
from groq import Groq
from dotenv import load_dotenv
import json
from datetime import datetime

load_dotenv()

_MODEL = "openai/gpt-oss-120b"


def _client() -> Groq | None:
    key = os.getenv("GROQ_API_KEY")
    if not key:
        return None
    return Groq(api_key=key, timeout=12.0)


def _build_context(payload: dict) -> str:
    from datetime import datetime

    def nice_time(iso: str) -> str:
        try:
            dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
            return dt.strftime("%a %d %b, %I%p").lstrip("0")
        except Exception:
            return iso

    city = payload["city_name"]
    current = payload["current"]
    fc = payload["forecast"]

    horizons = {p["horizon_hours"]: p for p in fc if p["horizon_hours"] in (24, 48, 72)}
    peak_point = max(fc, key=lambda p: p["aqi"])
    low_point = min(fc, key=lambda p: p["aqi"])

    end_aqi = horizons.get(72, {}).get("aqi", current["aqi"])
    if end_aqi < current["aqi"] - 5:
        trend = "improving over the three days"
    elif end_aqi > current["aqi"] + 5:
        trend = "worsening over the three days"
    else:
        trend = "staying broadly steady over the three days"

    lines = [
        f"City: {city}",
        f"Current AQI: {current['aqi']} ({current['category']})",
    ]
    for h in (24, 48, 72):
        if h in horizons:
            p = horizons[h]
            lines.append(f"Forecast at {h}h: AQI {p['aqi']} ({p['category']})")

    lines.append(
        f"Highest point in next 72h: AQI {peak_point['aqi']} "
        f"({peak_point['category']}) on {nice_time(peak_point['valid_at'])}"
    )
    lines.append(
        f"Lowest point in next 72h: AQI {low_point['aqi']} "
        f"on {nice_time(low_point['valid_at'])}"
    )
    lines.append(f"Overall trend: {trend}")

    drivers = payload.get("explanations", [])
    if drivers:
        lines.append("Model feature drivers behind this forecast (from SHAP):")
        for d in drivers:
            lines.append(f"- {d}")
    else:
        lines.append("Model drivers: not available for this city.")

    return "\n".join(lines)

def summarize_forecast(payload: dict) -> dict:
    """Return {happening, why, advice} dict, or empty dict if unavailable."""
    print("=== summarize_forecast CALLED ===")
    client = _client()
    print("=== client is:", "None" if client is None else "OK", "===")
    if client is None:
        return {}

    context = _build_context(payload)

    prompt = (
        "You are an air-quality analyst writing a public briefing for a city in "
        "Pakistan. Use ONLY the data below. Respond with a single JSON object and "
        "nothing else, with exactly these three string keys:\n"
        '  "happening": 3-4 sentences describing the current air quality, the health '
        "category, how the AQI moves across the next 24, 48 and 72 hours, when it "
        "peaks and how low it gets. Reference the specific numbers.\n"
        '  "why": 3-4 sentences explaining what is driving the forecast, based '
        "strictly on the listed model feature drivers. Name the specific features "
        "(for example recent AQI, PM2.5, PM10, weekly patterns) and explain in plain "
        "language what each contributes. If drivers are not available, say the model "
        "relies on recent AQI history and pollutant levels.\n"
        '  "advice": 3-4 sentences of practical guidance for different groups '
        "(sensitive individuals, children and elderly, general public, outdoor "
        "workers), matched to how unhealthy the air is. Stronger precautions only if "
        "AQI is 150 or above.\n\n"
        "Write in clear, calm, plain English. Do not invent numbers beyond those "
        "given. Do not use markdown symbols.\n\n"
        "DATA:\n" + context
    )

    try:
        resp = client.chat.completions.create(
            model=_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2500,
            temperature=0.4,
            response_format={"type": "json_object"},
        )
        raw = resp.choices[0].message.content.strip()
        data = json.loads(raw)

        # be tolerant of key-name variations the model might use
        def pick(d: dict, *names: str) -> str:
            for n in names:
                for k in d:
                    if k.lower().strip().replace("'", "").replace("_", " ") == n:
                        return str(d[k]).strip()
            return ""

        return {
            "happening": pick(data, "happening", "whats happening", "what is happening"),
            "why": pick(data, "why", "reason", "cause"),
            "advice": pick(data, "advice", "what to do", "recommendation"),
        }
    except Exception as e:
        return {}