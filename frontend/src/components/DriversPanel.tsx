// drivers: brutalist box, mono-tagged list of SHAP explanation sentences.
import { motion } from "motion/react";

interface DriversPanelProps {
  explanations: string[];
  accent: string;
}

export function DriversPanel({ explanations, accent }: DriversPanelProps) {
  if (!explanations || explanations.length === 0) return null;

  return (
    <div className="border-2 border-white/15 bg-black p-6 shadow-hard">
      <h2 className="font-display text-lg font-extrabold uppercase text-white">
        What is driving this
      </h2>
      <ul className="mt-4 space-y-3">
        {explanations.map((text, i) => (
          <motion.li
            key={i}
            initial={{ opacity: 0, x: -6 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.35, delay: 0.08 * i }}
            className="flex gap-3 text-sm text-white/65"
          >
            <span
              className="mt-0.5 shrink-0 font-mono text-xs font-bold"
              style={{ color: accent }}
            >
              {String(i + 1).padStart(2, "0")}
            </span>
            <span>{text}</span>
          </motion.li>
        ))}
      </ul>
    </div>
  );
}

