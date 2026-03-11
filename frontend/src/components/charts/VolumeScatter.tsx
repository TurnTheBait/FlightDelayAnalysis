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
    name: string;
    total_flights: number;
    global_weighted_sentiment: number;
    composite_score: number;
}

interface Props {
    data: DataPoint[];
    avgSentiment: number;
}

function CustomTooltip({ active, payload }: { active?: boolean; payload?: Array<{ payload: DataPoint }> }) {
    if (!active || !payload?.length) return null;
    const d = payload[0].payload;
    return (
        <div className="custom-tooltip">
            <div className="custom-tooltip__label">{d.airport_code} &ndash; {d.name}</div>
            <div className="custom-tooltip__value">
                Sentiment: {d.global_weighted_sentiment.toFixed(2)}
            </div>
            <div className="custom-tooltip__value">
                Flights: {d.total_flights.toLocaleString()}
            </div>
            <div className="custom-tooltip__value">
                Composite: {d.composite_score.toFixed(2)}
            </div>
        </div>
    );
}

function scoreColor(val: number): string {
    if (val >= 6) return "#3fb950";
    if (val >= 5) return "#5e6ad2";
    if (val >= 4) return "#d29922";
    return "#f85149";
}

export default function VolumeScatter({ data, avgSentiment }: Props) {
    return (
        <div className="chart-container">
            <ResponsiveContainer width="100%" height={380}>
                <ScatterChart margin={{ top: 10, right: 20, bottom: 20, left: 10 }}>
                    <XAxis
                        dataKey="total_flights"
                        type="number"
                        name="Total Flights"
                        tick={{ fill: "var(--chart-axis)", fontSize: 11 }}
                        axisLine={{ stroke: "var(--chart-grid)" }}
                        tickLine={false}
                        tickFormatter={(v: number) => v >= 1000 ? `${(v / 1000).toFixed(0)}k` : String(v)}
                        label={{
                            value: "Annual Flight Volume",
                            position: "bottom",
                            offset: 4,
                            fill: "var(--chart-label)",
                            fontSize: 11,
                        }}
                    />
                    <YAxis
                        dataKey="global_weighted_sentiment"
                        type="number"
                        name="Sentiment"
                        domain={[3, 8]}
                        tick={{ fill: "var(--chart-axis)", fontSize: 11 }}
                        axisLine={{ stroke: "var(--chart-grid)" }}
                        tickLine={false}
                        label={{
                            value: "Global Weighted Sentiment",
                            angle: -90,
                            position: "insideLeft",
                            offset: 4,
                            fill: "var(--chart-label)",
                            fontSize: 11,
                        }}
                    />
                    <ZAxis
                        dataKey="composite_score"
                        range={[40, 300]}
                        name="Composite Score"
                    />
                    <ReferenceLine
                        y={avgSentiment}
                        stroke="var(--accent-glow-strong)"
                        strokeDasharray="6 4"
                    />
                    <Tooltip content={<CustomTooltip />} cursor={false} />
                    <Scatter data={data} strokeWidth={1} stroke="var(--chart-cursor)">
                        {data.map((entry, i) => (
                            <Cell
                                key={i}
                                fill={scoreColor(entry.composite_score)}
                                fillOpacity={0.75}
                            />
                        ))}
                    </Scatter>
                </ScatterChart>
            </ResponsiveContainer>
        </div>
    );
}
