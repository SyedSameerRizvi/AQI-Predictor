// city selector: picks which trained city to show
import type { ServedCity } from "@/lib/types";

interface CitySelectorProps {
  cities: ServedCity[];
  selected: string;                 // selected city_id
  onSelect: (cityId: string) => void;
}

export function CitySelector({ cities, selected, onSelect }: CitySelectorProps) {
  return (
    <div className="flex flex-wrap gap-2">
      {cities.map((c) => (
        <button
          key={c.city_id}
          onClick={() => onSelect(c.city_id)}
          className={
            "rounded-lg px-4 py-2 text-sm transition-colors " +
            (c.city_id === selected
              ? "bg-sky-500 text-white"
              : "bg-slate-800 text-slate-300 hover:bg-slate-700")
          }
        >
          {c.name}
        </button>
      ))}
    </div>
  );
}