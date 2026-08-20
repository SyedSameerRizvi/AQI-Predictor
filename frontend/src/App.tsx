import { useState } from "react";
import LineChart, { Line } from "@/components/charts/line-chart";
import { Grid } from "@/components/charts/grid";
import { XAxis } from "@/components/charts/x-axis";
import { ChartTooltip } from "@/components/charts/tooltip";
import { CurrentAqiCard } from "@/components/CurrentAqiCard";
import { CitySelector } from "@/components/CitySelector";
import { AqiAlert } from "@/components/AqiAlert";
import { HorizonPanel } from "@/components/HorizonPanel";
import { mockCities, fetchForecast, fetchMetrics } from "@/lib/mockForecast";
import type { CityForecast, HorizonMetrics } from "@/lib/types";

function App() {
  const [selectedCity, setSelectedCity] = useState(mockCities[0].city_id);
  const [data, setData] = useState<CityForecast | null>(null);
  const [metrics, setMetrics] = useState<HorizonMetrics[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handlePredict() {
    setLoading(true);
    setError(null);
    setData(null);
    try {
      const [forecast, cityMetrics] = await Promise.all([
        fetchForecast(selectedCity),
        fetchMetrics(selectedCity),
      ]);
      setData(forecast);
      setMetrics(cityMetrics);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Prediction failed");
    } finally {
      setLoading(false);
    }
  }

  const chartData =
    data?.forecast.map((p) => ({ ...p, date: new Date(p.valid_at) })) ?? [];

  return (
    <div className="min-h-screen bg-slate-900 p-10 text-white">
      <h1 className="mb-6 text-2xl font-bold">Pakistan AQI Forecast</h1>

      <div className="mb-4">
        <CitySelector
          cities={mockCities}
          selected={selectedCity}
          onSelect={(id) => {
            setSelectedCity(id);
            setData(null);        // clear stale forecast when city changes
            setError(null);
          }}
        />
      </div>

      <button
        onClick={handlePredict}
        disabled={loading}
        className="mb-8 rounded-lg bg-sky-500 px-6 py-2 font-semibold text-white transition-colors hover:bg-sky-400 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {loading ? "Predicting..." : "Predict next 3 days"}
      </button>

      {/* idle: nothing chosen yet */}
      {!loading && !data && !error && (
        <p className="text-slate-500">
          Select a city and click Predict to see the next 72 hours.
        </p>
      )}

      {/* loading */}
      {loading && (
        <div className="flex items-center gap-3 text-slate-400">
          <span className="h-4 w-4 animate-spin rounded-full border-2 border-slate-600 border-t-sky-400" />
          Fetching forecast...
        </div>
      )}

      {/* error */}
      {error && (
        <div className="rounded-lg border border-red-500/50 bg-red-500/10 px-4 py-3 text-red-300">
          {error}
        </div>
      )}

      {/* loaded */}
      {data && !loading && (
        <div className="space-y-6">
          <div className="max-w-2xl">
            <AqiAlert data={data} />
          </div>

          <div className="max-w-xs">
            <CurrentAqiCard cityName={data.city_name} current={data.current} />
          </div>

          <div className="max-w-3xl">
            <HorizonPanel data={data} metrics={metrics} />
          </div>

          <div className="h-[500px] w-full max-w-3xl">
            <LineChart data={chartData} xDataKey="date">
              <Grid horizontal />
              <Line dataKey="aqi" />
              <XAxis />
              <ChartTooltip />
            </LineChart>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;