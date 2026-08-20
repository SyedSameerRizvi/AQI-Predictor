// per-horizon breakdown: day 1/2/3 = 24h/48h/72h prediction + that horizon's accuracy
import type { CityForecast, HorizonMetrics } from "@/lib/types";

interface HorizonPanelProps {
  data: CityForecast;
  metrics: HorizonMetrics[];   // already filtered to the selected city
}

const HORIZONS = [
  { horizon: 24, label: "Day 1", sub: "24 hours" },
  { horizon: 48, label: "Day 2", sub: "48 hours" },
  { horizon: 72, label: "Day 3", sub: "72 hours" },
] as const;

export function HorizonPanel({ data, metrics }: HorizonPanelProps) {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
      {HORIZONS.map(({ horizon, label, sub }) => {
        const point = data.forecast.find((p) => p.horizon_hours === horizon);
        const m = metrics.find((x) => x.horizon === horizon);
        if (!point) return null;

        return (
          <div
            key={horizon}
            className="rounded-xl border border-slate-700 bg-slate-800/50 p-5"
          >
            <div className="flex items-baseline justify-between">
              <span className="text-sm font-semibold text-slate-200">{label}</span>
              <span className="text-xs text-slate-500">{sub}</span>
            </div>

            <div className="mt-3 flex items-baseline gap-2">
              <span className="text-3xl font-bold" style={{ color: point.colour }}>
                {point.aqi}
              </span>
              <span className="text-sm" style={{ color: point.colour }}>
                {point.category}
              </span>
            </div>

            {m ? (
              <div className="mt-4 space-y-1 text-xs text-slate-400">
                <div className="flex justify-between">
                  <span>R²</span>
                  <span className="text-slate-200">{m.r2.toFixed(2)}</span>
                </div>
                <div className="flex justify-between">
                  <span>RMSE</span>
                  <span className="text-slate-200">{m.rmse.toFixed(1)}</span>
                </div>
                <div className="flex justify-between">
                  <span>MAE</span>
                  <span className="text-slate-200">{m.mae.toFixed(1)}</span>
                </div>
              </div>
            ) : (
              <p className="mt-4 text-xs text-slate-500">No accuracy data</p>
            )}
          </div>
        );
      })}
    </div>
  );
}