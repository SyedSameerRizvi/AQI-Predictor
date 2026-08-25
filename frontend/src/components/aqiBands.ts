// AQI band system: the visual spine of the dashboard.
// every color, haze, and glow in the UI derives from these bands,
// so the whole page tints to whatever air quality is being shown.

export interface AqiBand {
  id: string;
  name: string;
  max: number;          // upper AQI bound of this band
  color: string;        // the band's signature color (numbers, labels)
  glow: string;         // rgba used for glows and accents
  hazeTop: string;      // upper atmospheric wash
  hazeBottom: string;   // lower atmospheric wash, denser
}

// US EPA standard bands. these are the subject's own vernacular.
export const AQI_BANDS: AqiBand[] = [
  {
    id: "good",
    name: "Good",
    max: 50,
    color: "#4ade80",
    glow: "rgba(74,222,128,0.35)",
    hazeTop: "rgba(74,222,128,0.28)",
    hazeBottom: "rgba(34,120,80,0.38)",
  },
  {
    id: "moderate",
    name: "Moderate",
    max: 100,
    color: "#fbbf24",
    glow: "rgba(251,191,36,0.32)",
    hazeTop: "rgba(251,191,36,0.26)",
    hazeBottom: "rgba(140,90,10,0.42)",
  },
  {
    id: "sg",
    name: "Unhealthy for Sensitive Groups",
    max: 150,
    color: "#fb923c",
    glow: "rgba(251,146,60,0.34)",
    hazeTop: "rgba(251,146,60,0.28)",
    hazeBottom: "rgba(150,70,20,0.45)",
  },
  {
    id: "unhealthy",
    name: "Unhealthy",
    max: 200,
    color: "#f87171",
    glow: "rgba(248,113,113,0.36)",
    hazeTop: "rgba(248,113,113,0.30)",
    hazeBottom: "rgba(150,40,40,0.48)",
  },
  {
    id: "very-unhealthy",
    name: "Very Unhealthy",
    max: 300,
    color: "#c084fc",
    glow: "rgba(192,132,252,0.36)",
    hazeTop: "rgba(192,132,252,0.30)",
    hazeBottom: "rgba(90,40,130,0.50)",
  },
  {
    id: "hazardous",
    name: "Hazardous",
    max: Infinity,
    color: "#e879a6",
    glow: "rgba(232,121,166,0.38)",
    hazeTop: "rgba(232,121,166,0.32)",
    hazeBottom: "rgba(120,30,70,0.52)",
  },
];

// map any AQI value to its band
export function bandForAqi(aqi: number): AqiBand {
  return AQI_BANDS.find((b) => aqi <= b.max) ?? AQI_BANDS[AQI_BANDS.length - 1];
}

// fraction of the 0..300 scale a value sits at, clamped, for progress rings
export function aqiFraction(aqi: number): number {
  return Math.max(0.04, Math.min(aqi / 300, 1));
}
