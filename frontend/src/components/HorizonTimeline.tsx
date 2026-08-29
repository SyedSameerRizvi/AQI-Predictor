// 3-day sequence as brutalist boxes, each with an AQI-colored top bar.
import { motion } from "motion/react";
import type { CityForecast, HorizonMetrics } from "@/lib/types";
import { bandForAqi } from "@/lib/aqiBands";
import { CountUp } from "./CountUp";

interface HorizonTimelineProps {
  data: CityForecast;
  metrics: HorizonMetrics[];
}

const HORIZONS = [
  { h: 24, label: "Day 1", sub: "24H" },
  { h: 48, label: "Day 2", sub: "48H" },
  { h: 72, label: "Day 3", sub: "72H" },
] as const;

const POLLUTANT_LABELS: Record<string, string> = {
  pm2_5: "PM2.5",
  pm10: "PM10",
  ozone: "Ozone",
  carbon_monoxide: "CO",
  nitrogen_dioxide: "NO2",
  sulphur_dioxide: "SO2",
};

// one metric cell in the conditions strip
function Cond({
  label,
  value,
  unit,
  strong,
}: {
  label: string;
  value: number | null;
  unit?: string;
  strong?: boolean;
}) {
  return (
    <div className={strong ? "text-white" : ""}>
      <div className="text-white/30">{label}</div>
      <div className="font-semibold">
        {value == null ? "—" : value}
        {unit ? <span className="ml-0.5 text-white/30">{unit}</span> : null}
      </div>
    </div>
  );
}

export function HorizonTimeline({ data, metrics }: HorizonTimelineProps) {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
      {HORIZONS.map(({ h, label, sub }, i) => {
        const point = data.forecast.find((p) => p.horizon_hours === h);
        const m = metrics.find((x) => x.horizon === h);
        if (!point) return null;
        const band = bandForAqi(point.aqi);
        const c = point.conditions;

        return (
          <motion.div
            key={h}
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.45, delay: 0.1 + i * 0.08 }}
            className="border-2 border-white/15 bg-black shadow-hard"
          >
            {/* colored top bar */}
            <div className="h-2" style={{ background: band.color }} />
            <div className="p-5">
              <div className="flex items-baseline justify-between">
                <span className="font-display text-lg font-extrabold uppercase text-white">
                  {label}
                </span>
                <span className="font-mono text-xs text-white/40">{sub}</span>
              </div>

              <div className="mt-3 flex items-baseline gap-2">
                <CountUp
                  value={point.aqi}
                  duration={800}
                  className="font-display text-4xl font-black"
                  style={{ color: band.color }}
                />
                <span
                  className="font-mono text-[11px] uppercase"
                  style={{ color: band.color }}
                >
                  {point.category || band.name}
                </span>
              </div>

              {m ? (
                <div className="mt-4 flex flex-wrap gap-x-4 gap-y-1 font-mono text-[11px] text-white/45">
                  <span>R2 {m.r2.toFixed(2)}</span>
                  <span>RMSE {m.rmse.toFixed(1)}</span>
                  <span>MAE {m.mae.toFixed(1)}</span>
                </div>
              ) : (
                <div className="mt-4 font-mono text-[11px] text-white/30">
                  no accuracy data
                </div>
              )}

              {/* forecast conditions strip: Open-Meteo weather + pollutants at this horizon */}
              {c && (
                <div className="mt-4 border-t border-white/10 pt-3">
                  <div className="font-mono text-[10px] uppercase tracking-wide text-white/30">
                    forecast conditions
                  </div>
                  <div className="mt-2 grid grid-cols-3 gap-x-3 gap-y-2 font-mono text-[11px] text-white/55">
                    <Cond label="TEMP" value={c.temperature} unit="°C" />
                    <Cond label="HUM" value={c.humidity} unit="%" />
                    <Cond label="WIND" value={c.wind} unit="km/h" />
                    <Cond label="PM2.5" value={c.pm2_5} strong={c.dominant === "pm2_5"} />
                    <Cond label="PM10" value={c.pm10} strong={c.dominant === "pm10"} />
                    <Cond label="O3" value={c.ozone} strong={c.dominant === "ozone"} />
                  </div>
                  <div className="mt-2 font-mono text-[10px] uppercase text-white/35">
                    µg/m³
                    {c.dominant
                      ? ` · dominant ${POLLUTANT_LABELS[c.dominant] ?? c.dominant}`
                      : ""}
                  </div>
                </div>
              )}
            </div>
          </motion.div>
        );
      })}
    </div>
  );
}