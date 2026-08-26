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

export function HorizonTimeline({ data, metrics }: HorizonTimelineProps) {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
      {HORIZONS.map(({ h, label, sub }, i) => {
        const point = data.forecast.find((p) => p.horizon_hours === h);
        const m = metrics.find((x) => x.horizon === h);
        if (!point) return null;
        const band = bandForAqi(point.aqi);

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
            </div>
          </motion.div>
        );
      })}
    </div>
  );
}

