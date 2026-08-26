// the atmospheric background: two soft haze washes that tint to the
// active AQI band and drift slowly. this is what makes the page "feel"
// like the air quality it's showing.
import { motion } from "motion/react";
import type { AqiBand } from "@/lib/aqiBands";

interface AtmosphereProps {
  band: AqiBand | null;   // null before any prediction -> neutral night
}

const NEUTRAL_TOP = "rgba(80,110,160,0.14)";
const NEUTRAL_BOTTOM = "rgba(30,45,80,0.30)";

export function Atmosphere({ band }: AtmosphereProps) {
  const top = band?.hazeTop ?? NEUTRAL_TOP;
  const bottom = band?.hazeBottom ?? NEUTRAL_BOTTOM;

  return (
    <div className="pointer-events-none fixed inset-0 -z-10 overflow-hidden bg-[#070b14]">
      {/* upper wash */}
      <motion.div
        className="absolute -inset-x-[20%] -top-[20%] h-[80%] blur-[70px]"
        animate={{
          background: `radial-gradient(ellipse at 30% 0%, ${top}, transparent 70%)`,
          x: [0, 30, 0],
          y: [0, 16, 0],
        }}
        transition={{
          background: { duration: 1.2, ease: "easeInOut" },
          x: { duration: 26, repeat: Infinity, ease: "easeInOut" },
          y: { duration: 22, repeat: Infinity, ease: "easeInOut" },
        }}
        style={{ opacity: 0.6 }}
      />
      {/* lower, denser wash */}
      <motion.div
        className="absolute -inset-x-[20%] -bottom-[20%] h-[72%] blur-[80px]"
        animate={{
          background: `radial-gradient(ellipse at 70% 100%, ${bottom}, transparent 70%)`,
          x: [0, -28, 0],
          y: [0, -14, 0],
        }}
        transition={{
          background: { duration: 1.2, ease: "easeInOut" },
          x: { duration: 30, repeat: Infinity, ease: "easeInOut" },
          y: { duration: 24, repeat: Infinity, ease: "easeInOut" },
        }}
        style={{ opacity: 0.5 }}
      />
      {/* fine grain so the gradients don't band */}
      <div
        className="absolute inset-0 opacity-[0.04]"
        style={{
          backgroundImage: "radial-gradient(circle at 1px 1px, #fff 1px, transparent 0)",
          backgroundSize: "3px 3px",
        }}
      />
    </div>
  );
}

