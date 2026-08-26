const BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000"

// src/lib/api.ts
import type { CityForecast, NewsItem, ServedCity } from "./types";
import type { HorizonMetrics } from "./types";

// mirrors list_served_cities() — the 5 trained tier-1 cities
export const mockCities: ServedCity[] = [
  { city_id: "pk-karachi", name: "Karachi" },
  { city_id: "pk-lahore", name: "Lahore" },
  { city_id: "pk-islamabad", name: "Islamabad" },
  { city_id: "pk-peshawar", name: "Peshawar" },
  { city_id: "pk-quetta", name: "Quetta" },
];

// mirrors metrics.json — per city, per horizon. numbers approximate the real ones.
export const mockMetrics: HorizonMetrics[] = [
  { city: "pk-karachi", horizon: 24, rmse: 10.4, mae: 7.2, r2: 0.48, skill: 0.27 },
  { city: "pk-karachi", horizon: 48, rmse: 13.1, mae: 8.9, r2: 0.41, skill: 0.22 },
  { city: "pk-karachi", horizon: 72, rmse: 15.8, mae: 10.6, r2: 0.35, skill: 0.18 },
  { city: "pk-lahore", horizon: 24, rmse: 27.3, mae: 18.2, r2: 0.59, skill: 0.41 },
  { city: "pk-lahore", horizon: 48, rmse: 31.0, mae: 21.4, r2: 0.52, skill: 0.36 },
  { city: "pk-lahore", horizon: 72, rmse: 35.2, mae: 24.8, r2: 0.46, skill: 0.31 },
  { city: "pk-islamabad", horizon: 24, rmse: 15.6, mae: 11.8, r2: 0.79, skill: 0.11 },
  { city: "pk-islamabad", horizon: 48, rmse: 18.9, mae: 14.1, r2: 0.72, skill: 0.14 },
  { city: "pk-islamabad", horizon: 72, rmse: 22.3, mae: 16.7, r2: 0.66, skill: 0.16 },
  { city: "pk-peshawar", horizon: 24, rmse: 17.9, mae: 13.8, r2: 0.67, skill: 0.23 },
  { city: "pk-peshawar", horizon: 48, rmse: 21.2, mae: 16.0, r2: 0.60, skill: 0.20 },
  { city: "pk-peshawar", horizon: 72, rmse: 24.6, mae: 18.5, r2: 0.54, skill: 0.17 },
  { city: "pk-quetta", horizon: 24, rmse: 34.8, mae: 24.2, r2: 0.12, skill: 0.44 },
  { city: "pk-quetta", horizon: 48, rmse: 38.1, mae: 27.0, r2: 0.09, skill: 0.39 },
  { city: "pk-quetta", horizon: 72, rmse: 41.5, mae: 29.8, r2: 0.06, skill: 0.34 },
];

const now = new Date();
const iso = (hoursAhead: number) =>
  new Date(now.getTime() + hoursAhead * 3600_000).toISOString();

function categoryFor(aqi: number): { category: string; colour: string } {
  if (aqi <= 50) return { category: "Good", colour: "#22c55e" };
  if (aqi <= 100) return { category: "Moderate", colour: "#f59e0b" };
  if (aqi <= 150) return { category: "Unhealthy (SG)", colour: "#f97316" };
  return { category: "Unhealthy", colour: "#ef4444" };
}

// build one city's mock forecast around a base AQI so cities differ visibly
function makeForecast(city: ServedCity, baseAqi: number): CityForecast {
  const cur = categoryFor(baseAqi);
  return {
    city_id: city.city_id,
    city_name: city.name,
    generated_at: now.toISOString(),
    current: { aqi: baseAqi, category: cur.category, colour: cur.colour },
    forecast: Array.from({ length: 72 }, (_, i) => {
      const aqi = Math.round(baseAqi + 30 * Math.sin(i / 8));
      const band = categoryFor(aqi);
      return {
        horizon_hours: i + 1,
        valid_at: iso(i + 1),
        aqi,
        category: band.category,
        colour: band.colour,
        model_accuracy: 0.65,
      };
    }),
    explanations: [
      "The current AQI level is the strongest driver of the forecast",
      "The AQI an hour ago strongly informs the next few hours",
      "Current PM2.5 levels push the forecast up",
      "The AQI at this time last week captures weekly patterns",
      "Current PM10 levels add to the prediction",
    ],
  };
}

// different base AQI per city so switching is visible
const baseAqiByCity: Record<string, number> = {
  "pk-karachi": 98,
  "pk-lahore": 165,
  "pk-islamabad": 72,
  "pk-peshawar": 120,
  "pk-quetta": 45,
};

// lookup: city_id -> CityForecast
export const mockForecasts: Record<string, CityForecast> = Object.fromEntries(
  mockCities.map((c) => [c.city_id, makeForecast(c, baseAqiByCity[c.city_id])])
);

// simulates the future GET /forecast/{city_id} call.
// later: replace the body with a real fetch to FastAPI.
const API = "http://localhost:8000";

export async function fetchForecast(cityId: string): Promise<CityForecast> {
  const res = await fetch(`${API}/forecast/${cityId}`);
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail ?? `Forecast failed (${res.status})`);
  }
  return res.json();
}

export async function fetchMetrics(cityId: string): Promise<HorizonMetrics[]> {
  const res = await fetch(`${API}/metrics?city=${cityId}`);
  if (!res.ok) throw new Error(`Metrics failed (${res.status})`);
  return res.json();
}


export async function fetchCities(): Promise<ServedCity[]> {
  const res = await fetch(`${API}/cities`);
  if (!res.ok) throw new Error(`Cities failed (${res.status})`);
  return res.json();
}

export async function fetchNews(): Promise<NewsItem[]> {
  const res = await fetch(`${API}/news`);
  if (!res.ok) throw new Error(`News failed (${res.status})`);
  return res.json();
}