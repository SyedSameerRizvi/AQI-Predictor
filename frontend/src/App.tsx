import { useState, useEffect } from "react";
import { AnimatePresence, motion } from "motion/react";
import { ForecastChart } from "@/components/ForecastChart";
import { Hero } from "@/components/Hero";
import { CitySelector } from "@/components/CitySelector";
import { AqiAlert } from "@/components/AqiAlert";
import { HorizonTimeline } from "@/components/HorizonTimeline";
import { AiSummary } from "@/components/AiSummary";
import { Footer } from "@/components/Footer";
import { CookieBanner } from "@/components/CookieBanner";
import { NewsPanel } from "@/components/NewsPanel";
import { fetchForecast, fetchMetrics, fetchCities } from "@/lib/api";
import { bandForAqi } from "@/lib/aqiBands";
import type { CityForecast, HorizonMetrics, ServedCity } from "@/lib/types";

const BRAND = "#c5f82a"; // lime, used before a city is picked

function App() {
  const [cities, setCities] = useState<ServedCity[]>([]);
  const [selectedCity, setSelectedCity] = useState<string>("");
  const [data, setData] = useState<CityForecast | null>(null);
  const [metrics, setMetrics] = useState<HorizonMetrics[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchCities()
      .then((list) => {
        setCities(list);
        if (list.length > 0) setSelectedCity(list[0].city_id);
      })
      .catch(() => setCities([]));
  }, []);

  async function handlePredict() {
    if (!selectedCity) return;
    setLoading(true);
    setError(null);
    setData(null);
    try {
      const [forecast, cityMetrics] = await Promise.all([
        fetchForecast(selectedCity),
        fetchMetrics(selectedCity),
      ]);
      setData(forecast);
      setMetrics(cityMetrics);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Prediction failed");
    } finally {
      setLoading(false);
    }
  }

  const band = data ? bandForAqi(data.current.aqi) : null;
  const accent = band?.color ?? BRAND;

  return (
    <div className="relative min-h-screen bg-[#0a0a0a] text-white">
      <CookieBanner />

      <div className="mx-auto max-w-5xl px-6 py-14 sm:px-10">
        {/* masthead - portfolio-style: mono tag + big display title with highlight marker */}
        <header className="mb-12">
          <div className="mb-4 inline-block bg-white/10 px-2 py-1 font-mono text-[11px] uppercase tracking-[0.2em] text-white/60">
            Pakistan air quality
          </div>
          <h1 className="font-display text-5xl font-black uppercase leading-[0.9] tracking-tight sm:text-7xl">
            Three-day{" "}
            <span
              className="box-decoration-clone px-2"
              style={{ background: accent, color: "#0a0a0a" }}
            >
              AQI forecast
            </span>
          </h1>
          <p className="mt-5 max-w-xl font-sans text-base text-white/50">
            Hourly air-quality predictions for the next 72 hours, from a machine-learning
            model trained on two years of data.
          </p>
        </header>

        {/* controls */}
        <div className="mb-5">
          <CitySelector
            cities={cities}
            selected={selectedCity}
            band={band}
            onSelect={(id) => {
              setSelectedCity(id);
              setData(null);
              setError(null);
            }}
          />
        </div>

        <motion.button
          onClick={handlePredict}
          disabled={loading || !selectedCity}
          whileTap={{ scale: 0.97 }}
          className="mb-14 border-2 px-8 py-3 font-display text-sm font-extrabold uppercase tracking-wide transition-opacity disabled:cursor-not-allowed disabled:opacity-40"
          style={{ background: accent, color: "#0a0a0a", borderColor: accent }}
        >
          {loading ? "Predicting..." : "Predict next 3 days >"}
        </motion.button>

        {/* idle */}
        {!loading && !data && !error && (
          <p className="font-mono text-sm uppercase tracking-wide text-white/35">
            Pick a city and predict to see the next 72 hours.
          </p>
        )}

        {/* loading */}
        {loading && (
          <div className="flex items-center gap-3 font-mono text-sm uppercase tracking-wide text-white/50">
            <span
              className="h-4 w-4 animate-spin border-2 border-white/15"
              style={{ borderTopColor: accent }}
            />
            Reading the air...
          </div>
        )}

        {/* error */}
        {error && (
          <div className="border-2 border-red-500 bg-red-500/10 px-5 py-3 font-mono text-sm text-red-300">
            {error}
          </div>
        )}

        {/* loaded */}
        <AnimatePresence>
          {data && !loading && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.35 }}
              className="space-y-10"
            >
              <AqiAlert data={data} />
              <Hero data={data} />
              <AiSummary summary={data.ai_summary} accent={accent} />

              <div>
                <SectionTag n="01" label="Three-day outlook" accent={accent} />
                <HorizonTimeline data={data} metrics={metrics} />
              </div>

              <div>
                <SectionTag n="02" label="Hourly forecast" accent={accent} />
                <div className="border-2 border-white/15 bg-black p-5 shadow-hard">
                  <ForecastChart data={data} />
                </div>
              </div>

              <div>
                <SectionTag n="03" label="In the news" accent={accent} />
                <NewsPanel accent={accent} />
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        <Footer />
      </div>
    </div>
  );
}

// portfolio-style numbered section tag
function SectionTag({ n, label, accent }: { n: string; label: string; accent: string }) {
  return (
    <div className="mb-4 flex items-center gap-3">
      <span
        className="px-2 py-0.5 font-mono text-[11px] font-bold uppercase tracking-wide"
        style={{ background: accent, color: "#0a0a0a" }}
      >
        {n}
      </span>
      <span className="font-mono text-[11px] uppercase tracking-[0.18em] text-white/45">
        {label}
      </span>
    </div>
  );
}

export default App;

