// current AQI display: reads the "current" object from a CityForecast
import type { CurrentAqi } from "@/lib/types";

interface CurrentAqiCardProps {
  cityName: string;
  current: CurrentAqi;
}

export function CurrentAqiCard({ cityName, current }: CurrentAqiCardProps) {
  return (
    <div className="rounded-xl border border-slate-700 bg-slate-800/50 p-6">
      <p className="text-sm text-slate-400">{cityName}</p>
      <div className="mt-2 flex items-baseline gap-3">
        <span className="text-5xl font-bold" style={{ color: current.colour }}>
          {current.aqi}
        </span>
        <span className="text-lg" style={{ color: current.colour }}>
          {current.category}
        </span>
      </div>
      <p className="mt-1 text-xs text-slate-500">Current US EPA AQI</p>
    </div>
  );
}
