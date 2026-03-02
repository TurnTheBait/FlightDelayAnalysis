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
    avg_sentiment: number;
    population_10km: number;
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
                Noise Sentiment: {d.avg_sentiment.toFixed(2)}
            </div>
            <div className="custom-tooltip__value">
                Population (10km): {Math.round(d.population_10km).toLocaleString()}
            </div>
        </div>
    );
}

function sentimentColor(val: number): string {
    if (val >= 3.0) return "#3fb950";
    if (val >= 2.5) return "#5e6ad2";
    if (val >= 2.0) return "#d29922";
    return "#f85149";
}

export default function NoisePopulationScatter({ data }: Props) {
    return (
        <div className="chart-container">
            <ResponsiveContainer width="100%" height={380}>
                <ScatterChart margin={{ top: 10, right: 20, bottom: 20, left: 10 }}>
                    <XAxis
                        dataKey="population_10km"
                        type="number"
                        scale="log"
                        domain={["auto", "auto"]}
                        name="Population"
                        tick={{ fill: "rgba(255,255,255,0.4)", fontSize: 11 }}
                        axisLine={{ stroke: "rgba(255,255,255,0.06)" }}
                        tickLine={false}
                        tickFormatter={(v: number) =>
                            v >= 1000000
                                ? `${(v / 1000000).toFixed(1)}M`
                                : `${(v / 1000).toFixed(0)}K`
                        }
                        label={{
                            value: "Population within 10km (log scale)",
                            position: "bottom",
                            offset: 4,
                            fill: "rgba(255,255,255,0.35)",
                            fontSize: 11,
                        }}
                    />
                    <YAxis
                        dataKey="avg_sentiment"
                        type="number"
                        name="Noise Sentiment"
                        tick={{ fill: "rgba(255,255,255,0.4)", fontSize: 11 }}
                        axisLine={{ stroke: "rgba(255,255,255,0.06)" }}
                        tickLine={false}
                        label={{
                            value: "Avg Noise Sentiment",
                            angle: -90,
                            position: "insideLeft",
                            offset: 4,
                            fill: "rgba(255,255,255,0.35)",
                            fontSize: 11,
                        }}
                    />
                    <ZAxis range={[50, 150]} />
                    <Tooltip content={<CustomTooltip />} cursor={false} />
                    <Scatter data={data} strokeWidth={1} stroke="rgba(255,255,255,0.1)">
                        {data.map((entry, i) => (
                            <Cell
                                key={i}
                                fill={sentimentColor(entry.avg_sentiment)}
                                fillOpacity={0.75}
                            />
                        ))}
                    </Scatter>
                </ScatterChart>
            </ResponsiveContainer>
        </div>
    );
}
