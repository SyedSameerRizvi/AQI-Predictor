// alert: brutalist warning box, band-colored border and fill.
import { AnimatePresence, motion } from "motion/react";
import type { CityForecast } from "@/lib/types";
import { bandForAqi } from "@/lib/aqiBands";

const ALERT_THRESHOLD = 150;

interface AqiAlertProps {
  data: CityForecast;
}

export function AqiAlert({ data }: AqiAlertProps) {
  const currentHigh = data.current.aqi >= ALERT_THRESHOLD;
  const peak = Math.max(...data.forecast.map((p) => p.aqi));
  const forecastHigh = peak >= ALERT_THRESHOLD;
  const show = currentHigh || forecastHigh;
  const band = bandForAqi(currentHigh ? data.current.aqi : peak);

  return (
    <AnimatePresence>
      {show && (
        <motion.div
          initial={{ opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -8 }}
          transition={{ duration: 0.35 }}
          className="border-2 px-5 py-3"
          style={{ borderColor: band.color, background: `${band.color}1a` }}
        >
          <span
            className="font-display text-sm font-extrabold uppercase tracking-wide"
            style={{ color: band.color }}
          >
            ! Air quality alert
          </span>
          <span className="ml-2 font-sans text-sm text-white/75">
            {currentHigh
              ? `${data.city_name} is at AQI ${data.current.aqi} now, above the unhealthy threshold of ${ALERT_THRESHOLD}.`
              : `${data.city_name} is forecast to reach AQI ${peak} within 72 hours, above ${ALERT_THRESHOLD}.`}
          </span>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

