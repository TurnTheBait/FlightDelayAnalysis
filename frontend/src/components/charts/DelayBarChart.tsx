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
    count: number;
    mean: number;
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
                Delay Reviews: {d.count}
            </div>
            <div className="custom-tooltip__value">
                Sentiment: {d.mean.toFixed(2)}
            </div>
        </div>
    );
}

function barColor(mean: number): string {
    if (mean >= 5.5) return "#3fb950";
    if (mean >= 4.5) return "#5e6ad2";
    if (mean >= 4.0) return "#d29922";
    return "#f85149";
}

export default function DelayBarChart({ data }: Props) {
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
                    <Bar dataKey="count" radius={[0, 4, 4, 0]}>
                        {data.map((entry, i) => (
                            <Cell key={i} fill={barColor(entry.mean)} fillOpacity={0.8} />
                        ))}
                    </Bar>
                </BarChart>
            </ResponsiveContainer>
        </div>
    );
}
