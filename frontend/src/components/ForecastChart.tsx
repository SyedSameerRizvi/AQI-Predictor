// the forecast chart: AQI band zones as colored backdrop, a gradient
// area under the line, and the 24/48/72h horizon points marked out.
// the line color follows the current air-quality band.
import {
  ResponsiveContainer,
  ComposedChart,
  Area,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceArea,
  ReferenceDot,
} from "recharts";
import type { CityForecast } from "@/lib/types";
import { bandForAqi, AQI_BANDS } from "@/lib/aqiBands";

interface ForecastChartProps {
  data: CityForecast;
}

interface Row {
  t: number;          // ms timestamp for the x axis
  label: string;      // short date label
  aqi: number;
  horizon: number;    // hours ahead
}

const HORIZON_HOURS = [24, 48, 72];

export function ForecastChart({ data }: ForecastChartProps) {
  const rows: Row[] = data.forecast.map((p) => ({
    t: new Date(p.valid_at).getTime(),
    label: new Date(p.valid_at).toLocaleDateString(undefined, {
      month: "short",
      day: "numeric",
    }),
    aqi: p.aqi,
    horizon: p.horizon_hours,
  }));

  const maxAqi = Math.max(...rows.map((r) => r.aqi));
  const yMax = Math.ceil((maxAqi + 20) / 25) * 25;   // headroom, rounded

  const currentBand = bandForAqi(data.current.aqi);
  const lineColor = currentBand.color;

  // the horizon points to mark
  const markers = HORIZON_HOURS.map((h) => rows.find((r) => r.horizon === h)).filter(
    (r): r is Row => Boolean(r),
  );

  const tMin = rows[0]?.t;
  const tMax = rows[rows.length - 1]?.t;

  return (
    <ResponsiveContainer width="100%" height={340}>
      <ComposedChart data={rows} margin={{ top: 10, right: 8, bottom: 4, left: -8 }}>
        <defs>
          <linearGradient id="aqiFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={lineColor} stopOpacity={0.35} />
            <stop offset="100%" stopColor={lineColor} stopOpacity={0.02} />
          </linearGradient>
        </defs>

        {/* colored AQI band zones behind everything */}
        {AQI_BANDS.map((b, i) => {
          const lower = i === 0 ? 0 : AQI_BANDS[i - 1].max;
          const upper = b.max === Infinity ? yMax : b.max;
          if (lower >= yMax) return null;
          return (
            <ReferenceArea
              key={b.id}
              y1={lower}
              y2={Math.min(upper, yMax)}
              fill={b.color}
              fillOpacity={0.06}
              ifOverflow="hidden"
            />
          );
        })}

        <CartesianGrid strokeDasharray="1 3" stroke="rgba(255,255,255,0.06)" vertical={false} />

        <XAxis
          dataKey="t"
          type="number"
          scale="time"
          domain={[tMin, tMax]}
          tickFormatter={(t) =>
            new Date(t).toLocaleDateString(undefined, { month: "short", day: "numeric" })
          }
          stroke="rgba(255,255,255,0.25)"
          tick={{ fill: "rgba(255,255,255,0.45)", fontSize: 11 }}
          tickLine={false}
          axisLine={false}
          minTickGap={40}
        />
        <YAxis
          domain={[0, yMax]}
          stroke="rgba(255,255,255,0.25)"
          tick={{ fill: "rgba(255,255,255,0.4)", fontSize: 11 }}
          tickLine={false}
          axisLine={false}
          width={38}
        />

        <Tooltip
          contentStyle={{
            background: "#0a0a0a",
            border: "2px solid rgba(255,255,255,0.2)",
            borderRadius: 0,
            fontSize: 12,
          }}
          labelStyle={{ color: "rgba(255,255,255,0.6)" }}
          labelFormatter={(t) =>
            new Date(t as number).toLocaleString(undefined, {
              month: "short",
              day: "numeric",
              hour: "numeric",
            })
          }
          formatter={(v) => [Math.round(Number(v)), "AQI"]}
        />

        <Area
          type="monotone"
          dataKey="aqi"
          stroke="none"
          fill="url(#aqiFill)"
          isAnimationActive={false}
        />
        <Line
          type="monotone"
          dataKey="aqi"
          stroke={lineColor}
          strokeWidth={2.5}
          dot={false}
          isAnimationActive={true}
          animationDuration={900}
        />

        {/* mark the 24/48/72h horizon predictions */}
        {markers.map((m) => {
          const band = bandForAqi(m.aqi);
          return (
            <ReferenceDot
              key={m.horizon}
              x={m.t}
              y={m.aqi}
              r={5}
              fill={band.color}
              stroke="#0a0e1a"
              strokeWidth={2}
              ifOverflow="visible"
              label={{
                value: `${m.horizon}h`,
                position: "top",
                fill: "rgba(255,255,255,0.55)",
                fontSize: 10,
              }}
            />
          );
        })}
      </ComposedChart>
    </ResponsiveContainer>
  );
}

