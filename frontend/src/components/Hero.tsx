// hero: brutalist box with an AQI-colored accent bar and big display number.
import { motion } from "motion/react";
import type { CityForecast } from "@/lib/types";
import { bandForAqi, aqiFraction } from "@/lib/aqiBands";
import { CountUp } from "./CountUp";

interface HeroProps {
  data: CityForecast;
}

export function Hero({ data }: HeroProps) {
  const aqi = data.current.aqi;
  const band = bandForAqi(aqi);
  const frac = aqiFraction(aqi);

  return (
    <motion.section
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
      className="flex border-2 border-white/15 bg-black shadow-hard-accent"
      style={{ ["--accent" as string]: band.color }}
    >
      {/* AQI-colored accent bar on the left, like the portfolio's color blocks */}
      <div className="w-3 shrink-0" style={{ background: band.color }} />

      <div className="flex-1 p-6 sm:p-8">
        <div className="mb-3 inline-block bg-white/10 px-2 py-1 font-mono text-[11px] uppercase tracking-[0.16em] text-white/60">
          {data.city_name} / next 72h
        </div>

        <div className="flex flex-wrap items-end gap-x-6 gap-y-2">
          <CountUp
            value={aqi}
            className="font-display font-black leading-[0.85] tracking-tight"
            style={{ fontSize: "clamp(84px, 15vw, 150px)", color: band.color }}
          />
          <div className="pb-3">
            <div
              className="font-display text-2xl font-extrabold uppercase sm:text-3xl"
              style={{ color: band.color }}
            >
              {data.current.category || band.name}
            </div>
            <div className="mt-1 font-mono text-xs uppercase tracking-wide text-white/45">
              US EPA AQI / PM2.5 driven
            </div>
          </div>
        </div>

        {/* hard scale bar */}
        <div className="mt-6 h-3 w-full border border-white/15 bg-black">
          <motion.div
            className="h-full"
            initial={{ width: 0 }}
            animate={{ width: `${frac * 100}%` }}
            transition={{ duration: 0.9, ease: "easeInOut" }}
            style={{ background: band.color }}
          />
        </div>
      </div>
    </motion.section>
  );
}
