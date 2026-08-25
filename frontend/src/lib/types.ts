// src/lib/types.ts

// one entry in the "forecast" array from predict_city
export interface ForecastPoint {
  horizon_hours: number;
  valid_at: string;           // ISO — parse to Date for the chart
  aqi: number;
  category: string;
  colour: string;
  model_accuracy: number;
}

// the "current" object
export interface CurrentAqi {
  aqi: number;
  category: string;
  colour: string;
}

export interface AiSummary {
  happening: string;
  why: string;
  advice: string;
}

export interface CityForecast {
  city_id: string;
  city_name: string;
  generated_at: string;
  current: CurrentAqi;
  forecast: ForecastPoint[];
  explanations: string[];
  ai_summary?: AiSummary;
}

// list_served_cities() — for the city selector
export interface ServedCity {
  city_id: string;
  name: string;
}

// metrics.json — flat array, one per city+horizon
export interface HorizonMetrics {
  city: string;
  horizon: 24 | 48 | 72;
  rmse: number;
  mae: number;
  r2: number;
  skill: number;
}

export interface NewsItem { title: string; url: string; source: string; published_at: string; }

