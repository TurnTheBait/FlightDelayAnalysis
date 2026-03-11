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
    label: string;
    count: number;
}

interface Props {
    data: DataPoint[];
}

function CustomTooltip({ active, payload }: { active?: boolean; payload?: Array<{ payload: DataPoint }> }) {
    if (!active || !payload?.length) return null;
    const d = payload[0].payload;
    return (
        <div className="custom-tooltip">
            <div className="custom-tooltip__label">{d.label}</div>
            <div className="custom-tooltip__value">Airports: {d.count}</div>
        </div>
    );
}

export default function PressureDistribution({ data }: Props) {
    return (
        <div className="chart-container">
            <ResponsiveContainer width="100%" height={380}>
                <BarChart data={data} margin={{ top: 10, right: 20, bottom: 20, left: 10 }}>
                    <XAxis
                        dataKey="label"
                        tick={{ fill: "var(--chart-axis)", fontSize: 11 }}
                        axisLine={{ stroke: "var(--chart-grid)" }}
                        tickLine={false}
                        label={{
                            value: "Pressure Index Range",
                            position: "bottom",
                            offset: 4,
                            fill: "var(--chart-label)",
                            fontSize: 11,
                        }}
                    />
                    <YAxis
                        tick={{ fill: "var(--chart-axis)", fontSize: 11 }}
                        axisLine={{ stroke: "var(--chart-grid)" }}
                        tickLine={false}
                    />
                    <Tooltip content={<CustomTooltip />} cursor={{ fill: "var(--chart-cursor)" }} />
                    <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                        {data.map((_, i) => (
                            <Cell
                                key={i}
                                fill={`rgba(94, 106, 210, ${0.3 + (i / data.length) * 0.6})`}
                            />
                        ))}
                    </Bar>
                </BarChart>
            </ResponsiveContainer>
        </div>
    );
}
