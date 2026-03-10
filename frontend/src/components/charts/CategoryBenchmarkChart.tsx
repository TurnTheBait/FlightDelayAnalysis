"use client";

import {
    ComposedChart,
    Bar,
    Line,
    XAxis,
    YAxis,
    Tooltip,
    ResponsiveContainer,
} from "recharts";
import type { CategoryBenchmarkSummary } from "@/lib/types";

interface Props {
    data: CategoryBenchmarkSummary[];
}

function CustomTooltip({ active, payload }: { active?: boolean; payload?: any }) {
    if (!active || !payload?.length) return null;
    const d = payload[0].payload;
    return (
        <div className="custom-tooltip">
            <div className="custom-tooltip__label">{d.category} Airports</div>
            <div className="custom-tooltip__value">
                Count: {d.n_airports}
            </div>
            <div className="custom-tooltip__divider" style={{ margin: "8px 0", height: "1px", background: "rgba(255,255,255,0.1)" }} />
            <div className="custom-tooltip__value" style={{ color: "#3fb950" }}>
                High: {d.max_sentiment.toFixed(2)} ({d.best_airport})
            </div>
            <div className="custom-tooltip__value" style={{ fontWeight: 600, color: "#fff", margin: "4px 0" }}>
                Mean: {d.mean_sentiment.toFixed(2)}
            </div>
            <div className="custom-tooltip__value" style={{ color: "#f85149" }}>
                Low: {d.min_sentiment.toFixed(2)} ({d.worst_airport})
            </div>
        </div>
    );
}

function scoreColor(mean: number): string {
    if (mean >= 6) return "#3fb950";
    if (mean >= 5) return "#5e6ad2";
    if (mean >= 4) return "#d29922";
    return "#f85149";
}

const renderMeanDot = (props: any) => {
    const { cx, cy, payload } = props;
    if (!cx || !cy) return null;

    return (
        <circle
            cx={cx}
            cy={cy}
            r={6}
            fill={scoreColor(payload.mean_sentiment)}
            stroke="#050506"
            strokeWidth={2}
        />
    );
};

export default function CategoryBenchmarkChart({ data }: Props) {
    const chartData = data.map(d => ({
        ...d,
        sentimentRange: [d.min_sentiment, d.max_sentiment]
    }));

    return (
        <div className="chart-container">
            <ResponsiveContainer width="100%" height={380}>
                <ComposedChart
                    layout="vertical"
                    data={chartData}
                    margin={{ top: 20, right: 30, bottom: 20, left: 20 }}
                >
                    <XAxis
                        type="number"
                        domain={[1, 10]}
                        tick={{ fill: "rgba(255,255,255,0.4)", fontSize: 11 }}
                        axisLine={{ stroke: "rgba(255,255,255,0.06)" }}
                        tickLine={false}
                    />
                    <YAxis
                        dataKey="category"
                        type="category"
                        tick={{ fill: "rgba(255,255,255,0.7)", fontSize: 12, fontWeight: 500 }}
                        axisLine={false}
                        tickLine={false}
                        width={60}
                    />
                    <Tooltip content={<CustomTooltip />} cursor={{ fill: "rgba(255,255,255,0.04)" }} />

                    <Bar
                        dataKey="sentimentRange"
                        fill="rgba(255,255,255,0.1)"
                        barSize={24}
                        radius={12}
                    />

                    <Line
                        dataKey="mean_sentiment"
                        stroke="none"
                        dot={renderMeanDot}
                        activeDot={false}
                    />
                </ComposedChart>
            </ResponsiveContainer>
        </div>
    );
}