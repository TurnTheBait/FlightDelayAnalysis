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
} from "recharts";

interface DataPoint {
    airport_code: string;
    name: string;
    pressure_index: number;
    global_weighted_sentiment: number;
    total_mentions: number;
}

interface Props {
    data: DataPoint[];
}

function CustomTooltip({ active, payload }: { active?: boolean; payload?: Array<{ payload: DataPoint }> }) {
    if (!active || !payload?.length) return null;
    const d = payload[0].payload;
    return (
        <div className="custom-tooltip">
            <div className="custom-tooltip__label">
                {d.airport_code} &ndash; {d.name}
            </div>
            <div className="custom-tooltip__value">
                Sentiment: {d.global_weighted_sentiment.toFixed(2)}
            </div>
            <div className="custom-tooltip__value">
                Media Pressure: {d.pressure_index.toFixed(2)}
            </div>
            <div className="custom-tooltip__value">
                Mentions: {d.total_mentions.toLocaleString()}
            </div>
        </div>
    );
}

function sentimentColor(val: number): string {
    if (val >= 6) return "#3fb950";
    if (val >= 5) return "#5e6ad2";
    if (val >= 4) return "#d29922";
    return "#f85149";
}

export default function ReliabilityMatrix({ data }: Props) {
    return (
        <div className="chart-container">
            <ResponsiveContainer width="100%" height={380}>
                <ScatterChart margin={{ top: 10, right: 20, bottom: 20, left: 10 }}>
                    <XAxis
                        dataKey="pressure_index"
                        type="number"
                        name="Media Pressure"
                        tick={{ fill: "var(--chart-axis)", fontSize: 11 }}
                        axisLine={{ stroke: "var(--chart-grid)" }}
                        tickLine={false}
                        label={{
                            value: "Media Pressure Index",
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
                            value: "Global Sentiment",
                            angle: -90,
                            position: "insideLeft",
                            offset: 4,
                            fill: "var(--chart-label)",
                            fontSize: 11,
                        }}
                    />
                    <ZAxis
                        dataKey="total_mentions"
                        range={[40, 400]}
                        name="Mentions"
                    />
                    <Tooltip content={<CustomTooltip />} cursor={false} />
                    <Scatter data={data} strokeWidth={1} stroke="var(--chart-cursor)">
                        {data.map((entry, i) => (
                            <Cell
                                key={i}
                                fill={sentimentColor(entry.global_weighted_sentiment)}
                                fillOpacity={0.7}
                            />
                        ))}
                    </Scatter>
                </ScatterChart>
            </ResponsiveContainer>
        </div>
    );
}
