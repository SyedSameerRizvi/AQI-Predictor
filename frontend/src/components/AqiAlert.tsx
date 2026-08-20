// alert banner: shows when current or any forecast hour hits the unhealthy threshold
import type { CityForecast } from "@/lib/types";

const ALERT_THRESHOLD = 150;   // matches config.py alert threshold

interface AqiAlertProps {
  data: CityForecast;
}

export function AqiAlert({ data }: AqiAlertProps) {
  const currentHigh = data.current.aqi >= ALERT_THRESHOLD;
  const peak = Math.max(...data.forecast.map((p) => p.aqi));
  const forecastHigh = peak >= ALERT_THRESHOLD;

  if (!currentHigh && !forecastHigh) return null;   // nothing to warn about

  return (
    <div className="rounded-lg border border-red-500/50 bg-red-500/10 px-4 py-3 text-sm text-red-300">
      <span className="font-semibold">Air quality alert. </span>
      {currentHigh
        ? `${data.city_name} is currently at AQI ${data.current.aqi}, above the unhealthy threshold of ${ALERT_THRESHOLD}.`
        : `${data.city_name} is forecast to reach AQI ${peak} in the next 72 hours, above the unhealthy threshold of ${ALERT_THRESHOLD}.`}
    </div>
  );
}