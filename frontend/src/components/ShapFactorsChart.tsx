import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import type { Factor } from "../types";


interface ShapFactorsChartProps {
  factors: Factor[];
}


export function ShapFactorsChart({ factors }: ShapFactorsChartProps) {
  return (
    <section className="glass-card chart-card">
      <div className="panel-header">
        <div>
          <div className="section-kicker">Explainability</div>
          <h2>SHAP factor pressure</h2>
        </div>
        <p>Top drivers behind the current signal, ranked by model impact.</p>
      </div>

      <div className="chart-shell">
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={factors} layout="vertical" margin={{ top: 10, right: 20, left: 8, bottom: 0 }}>
            <CartesianGrid strokeDasharray="4 4" stroke="var(--line-soft)" />
            <XAxis type="number" stroke="var(--text-soft)" />
            <YAxis dataKey="label" type="category" width={124} stroke="var(--text-soft)" />
            <Tooltip
              cursor={{ fill: "rgba(255,255,255,0.04)" }}
              contentStyle={{
                background: "var(--surface-elevated)",
                border: "1px solid var(--line-strong)",
                borderRadius: 18,
                color: "var(--text-main)"
              }}
            />
            <Bar dataKey="shap_value" radius={[10, 10, 10, 10]}>
              {factors.map((factor) => (
                <Cell
                  key={factor.feature}
                  fill={factor.effect === "supports" ? "var(--accent-support)" : "var(--accent-risk)"}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="factor-list">
        {factors.map((factor) => (
          <div key={factor.feature} className="factor-item">
            <span>{factor.label}</span>
            <strong>{factor.display_value}</strong>
          </div>
        ))}
      </div>
    </section>
  );
}
