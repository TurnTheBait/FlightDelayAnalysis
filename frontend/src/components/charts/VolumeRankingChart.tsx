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

interface DataPoint {
    airport_code: string;
    composite_score: number;
    total_flights: number;
}

interface Props {
    data: DataPoint[];
}

function CustomTooltip({ active, payload }: { active?: boolean; payload?: Array<{ payload: DataPoint }> }) {
    if (!active || !payload?.length) return null;
    const d = payload[0].payload;
    return (
        <div className="custom-tooltip">
            <div className="custom-tooltip__label">{d.airport_code}</div>
            <div className="custom-tooltip__value">
                Composite Score: {d.composite_score.toFixed(2)}
            </div>
            <div className="custom-tooltip__value">
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

export default function VolumeRankingChart({ data }: Props) {
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
                    <Bar dataKey="composite_score" radius={[0, 4, 4, 0]}>
                        {data.map((entry, i) => (
                            <Cell key={i} fill={barColor(entry.composite_score)} fillOpacity={0.8} />
                        ))}
                    </Bar>
                </BarChart>
            </ResponsiveContainer>
        </div>
    );
}
