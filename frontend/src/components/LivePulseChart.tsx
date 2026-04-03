import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";


interface LivePoint {
  time: string;
  price: number;
  sentiment: number;
}

interface LivePulseChartProps {
  points: LivePoint[];
  connectionState: string;
}


export function LivePulseChart({ points, connectionState }: LivePulseChartProps) {
  return (
    <section className="glass-card chart-card">
      <div className="panel-header">
        <div>
          <div className="section-kicker">Live Pulse</div>
          <h2>Price vs sentiment</h2>
        </div>
        <p>WebSocket state: <span className="status-pill">{connectionState}</span></p>
      </div>

      <div className="chart-shell">
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={points} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="4 4" stroke="var(--line-soft)" />
            <XAxis dataKey="time" stroke="var(--text-soft)" />
            <YAxis yAxisId="left" stroke="var(--text-soft)" />
            <YAxis yAxisId="right" orientation="right" stroke="var(--text-soft)" domain={[-1, 1]} />
            <Tooltip
              contentStyle={{
                background: "var(--surface-elevated)",
                border: "1px solid var(--line-strong)",
                borderRadius: 18,
                color: "var(--text-main)"
              }}
            />
            <Legend />
            <Line
              yAxisId="left"
              type="monotone"
              dataKey="price"
              stroke="var(--accent-ember)"
              strokeWidth={3}
              dot={{ r: 4 }}
              activeDot={{ r: 6 }}
            />
            <Line
              yAxisId="right"
              type="monotone"
              dataKey="sentiment"
              stroke="var(--accent-aqua)"
              strokeWidth={3}
              dot={{ r: 4 }}
              activeDot={{ r: 6 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}
