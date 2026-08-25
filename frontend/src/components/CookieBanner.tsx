// consent banner: brutalist box, honest text, remembers dismissal locally.
import { useEffect, useState } from "react";
import { AnimatePresence, motion } from "motion/react";

const KEY = "aqi_cookie_ack";

export function CookieBanner() {
  const [show, setShow] = useState(false);

  useEffect(() => {
    try {
      if (!localStorage.getItem(KEY)) setShow(true);
    } catch {
      /* storage blocked */
    }
  }, []);

  function accept() {
    try {
      localStorage.setItem(KEY, "1");
    } catch {
      /* ignore */
    }
    setShow(false);
  }

  return (
    <AnimatePresence>
      {show && (
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 24 }}
          transition={{ duration: 0.35 }}
          className="fixed inset-x-4 bottom-4 z-50 mx-auto max-w-xl border-2 border-white/25 bg-black p-4 shadow-hard sm:inset-x-auto sm:left-1/2 sm:-translate-x-1/2"
        >
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <p className="font-sans text-sm text-white/65">
              This site stores a small preference on your device to remember your
              choices. No tracking, no third-party cookies.
            </p>
            <button
              onClick={accept}
              className="shrink-0 border-2 border-[#c5f82a] bg-[#c5f82a] px-5 py-1.5 font-display text-sm font-extrabold uppercase text-[#0a0a0a]"
            >
              Got it
            </button>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
