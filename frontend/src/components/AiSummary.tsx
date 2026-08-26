// AI briefing: brutalist box with three labeled sections.
import { motion } from "motion/react";
import type { AiSummary as AiSummaryData } from "@/lib/types";

interface AiSummaryProps {
  summary?: AiSummaryData;
  accent: string;
}

const SECTIONS: { key: keyof AiSummaryData; label: string }[] = [
  { key: "happening", label: "What's happening" },
  { key: "why", label: "Why" },
  { key: "advice", label: "What to do" },
];

export function AiSummary({ summary, accent }: AiSummaryProps) {
  if (!summary) return null;
  const parts = SECTIONS.filter((s) => summary[s.key]?.trim());
  if (parts.length === 0) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45, delay: 0.05 }}
      className="border-2 border-white/15 bg-black p-6 shadow-hard"
    >
      <div className="mb-5 inline-block px-2 py-1 font-mono text-[11px] font-bold uppercase tracking-[0.16em]"
        style={{ background: accent, color: "#0a0a0a" }}>
        AI briefing
      </div>

      <div className="space-y-5">
        {parts.map((s) => (
          <div key={s.key}>
            <div
              className="mb-1.5 font-display text-sm font-extrabold uppercase tracking-wide"
              style={{ color: accent }}
            >
              {s.label}
            </div>
            <p className="text-sm leading-relaxed text-white/75">{summary[s.key]}</p>
          </div>
        ))}
      </div>
    </motion.div>
  );
}

