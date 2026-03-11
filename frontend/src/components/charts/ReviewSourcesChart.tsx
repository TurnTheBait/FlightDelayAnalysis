"use client";

import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    Tooltip,
    ResponsiveContainer,
    Legend,
} from "recharts";

interface DataPoint {
    airport_code: string;
    google_news: number;
    reddit: number;
    skytrax: number;
    total: number;
}

interface Props {
    data: DataPoint[];
}

function CustomTooltip({ active, payload, label }: { active?: boolean; payload?: Array<{ name: string; value: number; color: string }>; label?: string }) {
    if (!active || !payload?.length) return null;
    return (
        <div className="custom-tooltip">
            <div className="custom-tooltip__label">{label}</div>
            {payload.map((p) => (
                <div key={p.name} className="custom-tooltip__value">
                    <span style={{ color: p.color }}>&#9679;</span> {p.name}: {p.value}
                </div>
            ))}
        </div>
    );
}

export default function ReviewSourcesChart({ data }: Props) {
    return (
        <div className="chart-container">
            <ResponsiveContainer width="100%" height={380}>
                <BarChart
                    data={data}
                    layout="vertical"
                    margin={{ top: 0, right: 20, bottom: 0, left: 10 }}
                >
                    <XAxis
                        type="number"
                        tick={{ fill: "var(--chart-axis)", fontSize: 11 }}
                        axisLine={{ stroke: "var(--chart-grid)" }}
                        tickLine={false}
                    />
                    <YAxis
                        dataKey="airport_code"
                        type="category"
                        width={40}
                        tick={{ fill: "var(--chart-axis)", fontSize: 11 }}
                        axisLine={false}
                        tickLine={false}
                    />
                    <Tooltip content={<CustomTooltip />} cursor={{ fill: "var(--chart-cursor)" }} />
                    <Legend
                        wrapperStyle={{ fontSize: 11, color: "var(--chart-label)" }}
                    />
                    <Bar
                        dataKey="skytrax"
                        name="Skytrax"
                        stackId="a"
                        fill="#5e6ad2"
                        radius={[0, 0, 0, 0]}
                    />
                    <Bar
                        dataKey="google_news"
                        name="Google News"
                        stackId="a"
                        fill="#8b5cf6"
                    />
                    <Bar
                        dataKey="reddit"
                        name="Reddit"
                        stackId="a"
                        fill="#3fb950"
                        radius={[0, 4, 4, 0]}
                    />
                </BarChart>
            </ResponsiveContainer>
        </div>
    );
}
