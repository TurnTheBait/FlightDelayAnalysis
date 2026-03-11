"use client";

import {
    ScatterChart,
    Scatter,
    XAxis,
    YAxis,
    Tooltip,
    ResponsiveContainer,
    Cell,
    ZAxis,
    ReferenceLine,
} from "recharts";

interface DataPoint {
    airport_code: string;
    mean: number;
    count: number;
}

interface Props {
    data: DataPoint[];
    avgMean: number;
}

function CustomTooltip({ active, payload }: { active?: boolean; payload?: Array<{ payload: DataPoint }> }) {
    if (!active || !payload?.length) return null;
    const d = payload[0].payload;
    return (
        <div className="custom-tooltip">
            <div className="custom-tooltip__label">{d.airport_code}</div>
            <div className="custom-tooltip__value">
                Delay Sentiment: {d.mean.toFixed(2)}
            </div>
            <div className="custom-tooltip__value">
                Delay Reviews: {d.count}
            </div>
        </div>
    );
}

function sentimentColor(val: number): string {
    if (val >= 5.5) return "#3fb950";
    if (val >= 4.5) return "#5e6ad2";
    if (val >= 4.0) return "#d29922";
    return "#f85149";
}

export default function DelayScatter({ data, avgMean }: Props) {
    return (
        <div className="chart-container">
            <ResponsiveContainer width="100%" height={380}>
                <ScatterChart margin={{ top: 10, right: 20, bottom: 20, left: 10 }}>
                    <XAxis
                        dataKey="count"
                        type="number"
                        name="Delay Reviews"
                        tick={{ fill: "var(--chart-axis)", fontSize: 11 }}
                        axisLine={{ stroke: "var(--chart-grid)" }}
                        tickLine={false}
                        label={{
                            value: "Delay Review Count",
                            position: "bottom",
                            offset: 4,
                            fill: "var(--chart-label)",
                            fontSize: 11,
                        }}
                    />
                    <YAxis
                        dataKey="mean"
                        type="number"
                        name="Sentiment"
                        domain={[3, 8]}
                        tick={{ fill: "var(--chart-axis)", fontSize: 11 }}
                        axisLine={{ stroke: "var(--chart-grid)" }}
                        tickLine={false}
                        label={{
                            value: "Delay Sentiment Mean",
                            angle: -90,
                            position: "insideLeft",
                            offset: 4,
                            fill: "var(--chart-label)",
                            fontSize: 11,
                        }}
                    />
                    <ZAxis range={[50, 200]} />
                    <ReferenceLine
                        y={avgMean}
                        stroke="var(--accent-glow-strong)"
                        strokeDasharray="6 4"
                    />
                    <Tooltip content={<CustomTooltip />} cursor={false} />
                    <Scatter data={data} strokeWidth={1} stroke="var(--chart-cursor)">
                        {data.map((entry, i) => (
                            <Cell
                                key={i}
                                fill={sentimentColor(entry.mean)}
                                fillOpacity={0.75}
                            />
                        ))}
                    </Scatter>
                </ScatterChart>
            </ResponsiveContainer>
        </div>
    );
}
