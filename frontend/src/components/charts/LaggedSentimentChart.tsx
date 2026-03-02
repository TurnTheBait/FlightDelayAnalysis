"use client";

import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    Tooltip,
    ResponsiveContainer,
    Legend,
} from "recharts";

interface DataPoint {
    label: string;
    None: number | null;
    Wind: number | null;
    Rain: number | null;
    "Rain & Wind": number | null;
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
                    <span style={{ color: p.color }}>&#9679;</span> {p.name}:{" "}
                    {p.value?.toFixed(2) ?? "N/A"}
                </div>
            ))}
        </div>
    );
}

const LINES = [
    { key: "None", color: "rgba(255,255,255,0.5)", label: "No Event" },
    { key: "Wind", color: "#5e6ad2", label: "Wind" },
    { key: "Rain", color: "#3fb950", label: "Rain" },
    { key: "Rain & Wind", color: "#f85149", label: "Rain & Wind" },
];

export default function LaggedSentimentChart({ data }: Props) {
    return (
        <div className="chart-container">
            <ResponsiveContainer width="100%" height={380}>
                <LineChart
                    data={data}
                    margin={{ top: 10, right: 20, bottom: 20, left: 10 }}
                >
                    <XAxis
                        dataKey="label"
                        tick={{ fill: "rgba(255,255,255,0.4)", fontSize: 11 }}
                        axisLine={{ stroke: "rgba(255,255,255,0.06)" }}
                        tickLine={false}
                    />
                    <YAxis
                        tick={{ fill: "rgba(255,255,255,0.4)", fontSize: 11 }}
                        axisLine={{ stroke: "rgba(255,255,255,0.06)" }}
                        tickLine={false}
                        label={{
                            value: "Avg Sentiment",
                            angle: -90,
                            position: "insideLeft",
                            offset: 4,
                            fill: "rgba(255,255,255,0.35)",
                            fontSize: 11,
                        }}
                    />
                    <Tooltip content={<CustomTooltip />} />
                    <Legend
                        wrapperStyle={{ fontSize: 11, color: "rgba(255,255,255,0.5)" }}
                    />
                    {LINES.map((l) => (
                        <Line
                            key={l.key}
                            type="monotone"
                            dataKey={l.key}
                            name={l.label}
                            stroke={l.color}
                            strokeWidth={2}
                            dot={{ r: 4, fill: l.color }}
                            activeDot={{ r: 6, stroke: l.color, strokeWidth: 2, fill: "#050506" }}
                            connectNulls
                        />
                    ))}
                </LineChart>
            </ResponsiveContainer>
        </div>
    );
}
