import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

interface TelemetryChartProps {
  data: Record<string, number>[];
  dataKey: string;
  color: string;
  unit?: string;
  height?: number;
}

export function TelemetryChart({ data, dataKey, color, unit = "", height = 120 }: TelemetryChartProps) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={data} margin={{ top: 4, right: 8, bottom: 0, left: -18 }}>
        <XAxis dataKey="t" hide />
        <YAxis
          tick={{ fill: "var(--color-text-tertiary)", fontSize: 10 }}
          axisLine={false}
          tickLine={false}
          width={40}
        />
        <Tooltip
          contentStyle={{
            background: "var(--color-bg-panel-raised)",
            border: "1px solid var(--color-line-strong)",
            borderRadius: 4,
            fontSize: 11,
          }}
          labelFormatter={(t) => `t=${Number(t).toFixed(1)}s`}
          formatter={((value: unknown) => [`${Number(value).toFixed(2)} ${unit}`, dataKey]) as any}
        />
        <Line type="monotone" dataKey={dataKey} stroke={color} strokeWidth={1.75} dot={false} isAnimationActive={false} />
      </LineChart>
    </ResponsiveContainer>
  );
}
