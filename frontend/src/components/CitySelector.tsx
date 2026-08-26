// city chips as brutalist tags; selected one fills with the band color.
import { motion } from "motion/react";
import type { ServedCity } from "@/lib/types";
import type { AqiBand } from "@/lib/aqiBands";

interface CitySelectorProps {
  cities: ServedCity[];
  selected: string;
  band: AqiBand | null;
  onSelect: (cityId: string) => void;
}

export function CitySelector({ cities, selected, band, onSelect }: CitySelectorProps) {
  const accent = band?.color ?? "#c5f82a";

  return (
    <div className="flex flex-wrap gap-2">
      {cities.map((c) => {
        const active = c.city_id === selected;
        return (
          <motion.button
            key={c.city_id}
            onClick={() => onSelect(c.city_id)}
            whileTap={{ scale: 0.96 }}
            className="border-2 px-4 py-2 font-mono text-xs font-medium uppercase tracking-wide transition-colors"
            style={
              active
                ? { background: accent, color: "#0a0a0a", borderColor: accent }
                : { background: "transparent", color: "rgba(255,255,255,0.6)", borderColor: "rgba(255,255,255,0.2)" }
            }
          >
            {c.name}
          </motion.button>
        );
      })}
    </div>
  );
}

