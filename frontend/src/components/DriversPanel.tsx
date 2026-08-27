// drivers: brutalist SHAP bar chart, real per-horizon importance.
import { motion } from "motion/react";
import type { ShapDriver } from "../lib/types";

interface DriversPanelProps {
  explanations: Record<number, ShapDriver[]>;
  horizon: number;
  accent: string;
}

const INCREASE = "#ef4444"; // pushes AQI up
const DECREASE = "#22c55e"; // pushes AQI down

export function DriversPanel({ explanations, horizon, accent }: DriversPanelProps) {
  const drivers = explanations?.[horizon] ?? [];
  if (drivers.length === 0) return null;

  const max = Math.max(...drivers.map((d) => d.importance), 0.0001);

  return (
    <div className="border-2 border-white/15 bg-black p-6 shadow-hard">
      <h2 className="font-display text-lg font-extrabold uppercase text-white">
        What is driving this
      </h2>
      <p className="mt-1 font-mono text-xs text-white/40">
        SHAP feature importance for the {horizon}h forecast
      </p>

      <ul className="mt-4 space-y-2">
        {drivers.map((d, i) => {
          const pct = (d.importance / max) * 100;
          const colour = d.direction >= 0 ? INCREASE : DECREASE;
          return (
            <motion.li
              key={d.feature}
              initial={{ opacity: 0, x: -6 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.3, delay: 0.05 * i }}
              className="flex items-center gap-3"
            >
              <span className="w-40 shrink-0 truncate text-right font-mono text-xs text-white/70">
                {d.label}
              </span>
              <div className="relative h-5 flex-1 bg-white/5">
                <div
                  className="h-full"
                  style={{ width: `${pct}%`, backgroundColor: colour }}
                />
              </div>
              <span
                className="w-10 shrink-0 font-mono text-xs font-bold"
                style={{ color: accent }}
              >
                {d.importance.toFixed(1)}
              </span>
            </motion.li>
          );
        })}
      </ul>

      <div className="mt-4 flex gap-4 font-mono text-[10px] uppercase text-white/40">
        <span><span style={{ color: INCREASE }}>■</span> raises AQI</span>
        <span><span style={{ color: DECREASE }}>■</span> lowers AQI</span>
      </div>
    </div>
  );
}