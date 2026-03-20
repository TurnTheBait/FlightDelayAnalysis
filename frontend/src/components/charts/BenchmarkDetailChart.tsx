"use client";

import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    Tooltip,
    ResponsiveContainer,
    Cell,
    ReferenceLine,
} from "recharts";
import type { BenchmarkAirport } from "@/lib/types";

interface Props {
    data: BenchmarkAirport[];
    categoryName: string;
}

function CustomTooltip({ active, payload }: { active?: boolean; payload?: any }) {
    if (!active || !payload?.length) return null;
    const d = payload[0].payload as BenchmarkAirport;
    return (
        <div className="custom-tooltip">
            <div className="custom-tooltip__label">
                #{d.rank} {d.airport_code}
            </div>
            <div className="custom-tooltip__value">{d.name}</div>
            <div className="custom-tooltip__divider" style={{ margin: "6px 0", height: "1px", background: "var(--chart-grid)" }} />
            <div className="custom-tooltip__value">
                Score: <strong>{d.sentiment_score.toFixed(2)}</strong>
            </div>
            <div className="custom-tooltip__value">
                Z-Score: {d.z_score.toFixed(2)}
            </div>
            <div className="custom-tooltip__value" style={{ color: "var(--text-tertiary)" }}>
                Flights: {d.total_flights.toLocaleString()}
            </div>
        </div>
    );
}

function barColor(score: number): string {
    if (score >= 6) return "#3fb950";
    if (score >= 5) return "#5e6ad2";
    if (score >= 4) return "#d29922";
    return "#f85149";
}

export default function BenchmarkDetailChart({ data, categoryName }: Props) {
    if (!data.length) {
        return (
            <div className="chart-container" style={{ display: "flex", alignItems: "center", justifyContent: "center" }}>
                <span style={{ color: "var(--text-tertiary)" }}>No data for {categoryName}</span>
            </div>
        );
    }

    const sorted = [...data].sort((a, b) => b.sentiment_score - a.sentiment_score);
    const catMean = sorted[0]?.category_mean ?? 0;
    const chartHeight = Math.max(280, sorted.length * 32 + 60);

    return (
        <div className="chart-container" style={{ minHeight: chartHeight }}>
            <ResponsiveContainer width="100%" height={chartHeight}>
                <BarChart
                    data={sorted}
                    layout="vertical"
                    margin={{ top: 10, right: 40, bottom: 10, left: 10 }}
                >
                    <XAxis
                        type="number"
                        domain={[0, 10]}
                        tick={{ fill: "var(--chart-axis)", fontSize: 11 }}
                        axisLine={{ stroke: "var(--chart-grid)" }}
                        tickLine={false}
                    />
                    <YAxis
                        dataKey="airport_code"
                        type="category"
                        width={45}
                        tick={{ fill: "var(--chart-axis)", fontSize: 11, fontWeight: 500 }}
                        axisLine={false}
                        tickLine={false}
                    />
                    <Tooltip content={<CustomTooltip />} cursor={{ fill: "var(--chart-cursor)" }} />
                    <ReferenceLine
                        x={catMean}
                        stroke="var(--text-secondary)"
                        strokeDasharray="6 4"
                        strokeWidth={2}
                        label={{
                            value: `Mean ${catMean.toFixed(2)}`,
                            position: "top",
                            fill: "var(--text-secondary)",
                            fontSize: 11,
                        }}
                    />
                    <Bar dataKey="sentiment_score" radius={[0, 4, 4, 0]} barSize={20}>
                        {sorted.map((entry, i) => (
                            <Cell key={i} fill={barColor(entry.sentiment_score)} fillOpacity={0.85} />
                        ))}
                    </Bar>
                </BarChart>
            </ResponsiveContainer>
        </div>
    );
}
