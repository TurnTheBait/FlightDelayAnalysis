"use client";

import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    Tooltip,
    ResponsiveContainer,
    Cell,
} from "recharts";
import type { CategoryBenchmarkSummary } from "@/lib/types";

interface Props {
    data: CategoryBenchmarkSummary[];
}

function CustomTooltip({ active, payload }: { active?: boolean; payload?: any }) {
    if (!active || !payload?.length) return null;
    const d = payload[0].payload as CategoryBenchmarkSummary;
    return (
        <div className="custom-tooltip">
            <div className="custom-tooltip__label">{d.category}</div>
            <div className="custom-tooltip__value">Airports: {d.n_airports}</div>
            <div className="custom-tooltip__value">Avg Sentiment: {d.mean_sentiment.toFixed(2)}</div>
            <div className="custom-tooltip__value" style={{ marginTop: '4px', color: '#3fb950' }}>Best: {d.best_airport}</div>
            <div className="custom-tooltip__value" style={{ color: '#f85149' }}>Worst: {d.worst_airport}</div>
        </div>
    );
}

function barColor(mean: number): string {
    if (mean >= 6) return "#3fb950";
    if (mean >= 5) return "#5e6ad2";
    if (mean >= 4) return "#d29922";
    return "#f85149";
}

export default function CategoryBenchmarkChart({ data }: Props) {
    return (
        <div className="chart-container">
            <ResponsiveContainer width="100%" height={380}>
                <BarChart data={data} margin={{ top: 10, right: 20, bottom: 20, left: 10 }}>
                    <XAxis
                        dataKey="category"
                        tick={{ fill: "rgba(255,255,255,0.4)", fontSize: 11 }}
                        axisLine={{ stroke: "rgba(255,255,255,0.06)" }}
                        tickLine={false}
                    />
                    <YAxis
                        domain={[3, 8]}
                        tick={{ fill: "rgba(255,255,255,0.4)", fontSize: 11 }}
                        axisLine={{ stroke: "rgba(255,255,255,0.06)" }}
                        tickLine={false}
                    />
                    <Tooltip content={<CustomTooltip />} cursor={{ fill: "rgba(255,255,255,0.03)" }} />
                    <Bar dataKey="mean_sentiment" radius={[4, 4, 0, 0]}>
                        {data.map((entry, i) => (
                            <Cell key={i} fill={barColor(entry.mean_sentiment)} fillOpacity={0.8} />
                        ))}
                    </Bar>
                </BarChart>
            </ResponsiveContainer>
        </div>
    );
}