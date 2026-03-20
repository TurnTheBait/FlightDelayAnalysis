"use client";

import {
    ComposedChart,
    Scatter,
    Line,
    XAxis,
    YAxis,
    Tooltip,
    ResponsiveContainer,
    Cell,
    ZAxis,
} from "recharts";
import { useMemo } from "react";

interface DataPoint {
    airport_code: string;
    name: string;
    avg_sentiment: number;
    population_20km: number;
    noise_review_count: number;
    total_flights: number;
}

interface Props {
    data: DataPoint[];
}

function CustomTooltip({ active, payload }: { active?: boolean; payload?: any[] }) {
    if (!active || !payload?.length) return null;
    const d = payload[0].payload as DataPoint;
    if (!d.airport_code) return null;
    return (
        <div className="custom-tooltip">
            <div className="custom-tooltip__label">
                {d.airport_code} &ndash; {d.name}
            </div>
            <div className="custom-tooltip__value">
                Noise Reviews: {d.noise_review_count}
            </div>
            <div className="custom-tooltip__value">
                Population (20km): {Math.round(d.population_20km).toLocaleString()}
            </div>
            <div className="custom-tooltip__value">
                Total Flights: {d.total_flights.toLocaleString()}
            </div>
            <div className="custom-tooltip__value" style={{ marginTop: "4px", color: sentimentColor(d.avg_sentiment) }}>
                Avg Sentiment: {d.avg_sentiment.toFixed(2)}
            </div>
        </div>
    );
}

function sentimentColor(val: number): string {
    if (val >= 6.0) return "#3fb950";
    if (val >= 4.5) return "#5e6ad2";
    if (val >= 3.0) return "#d29922";
    return "#f85149";
}

// Log-log linear regression → power-law trend line
function computeTrendLine(data: DataPoint[], numPoints = 40) {
    const valid = data.filter(d => d.population_20km > 0 && d.noise_review_count > 0);
    if (valid.length < 3) return [];

    const logX = valid.map(d => Math.log(d.population_20km));
    const logY = valid.map(d => Math.log(d.noise_review_count));
    const n = logX.length;

    const sumX = logX.reduce((a, b) => a + b, 0);
    const sumY = logY.reduce((a, b) => a + b, 0);
    const sumXY = logX.reduce((a, x, i) => a + x * logY[i], 0);
    const sumX2 = logX.reduce((a, x) => a + x * x, 0);

    const slope = (n * sumXY - sumX * sumY) / (n * sumX2 - sumX * sumX);
    const intercept = (sumY - slope * sumX) / n;

    const minX = Math.min(...valid.map(d => d.population_20km));
    const maxX = Math.max(...valid.map(d => d.population_20km));
    const logMin = Math.log(minX);
    const logMax = Math.log(maxX);
    const step = (logMax - logMin) / (numPoints - 1);

    return Array.from({ length: numPoints }, (_, i) => {
        const lx = logMin + i * step;
        const ly = intercept + slope * lx;
        return {
            population_20km: Math.exp(lx),
            noise_review_count: Math.exp(ly),
        };
    });
}

export default function NoisePopulationScatter({ data }: Props) {
    const trendData = useMemo(() => computeTrendLine(data), [data]);

    return (
        <div className="chart-container">
            <ResponsiveContainer width="100%" height={380}>
                <ComposedChart margin={{ top: 10, right: 20, bottom: 20, left: 10 }}>
                    <XAxis
                        dataKey="population_20km"
                        type="number"
                        scale="log"
                        domain={["auto", "auto"]}
                        name="Population"
                        tick={{ fill: "var(--chart-axis)", fontSize: 11 }}
                        axisLine={{ stroke: "var(--chart-grid)" }}
                        tickLine={false}
                        allowDuplicatedCategory={false}
                        tickFormatter={(v: number) =>
                            v >= 1000000
                                ? `${(v / 1000000).toFixed(1)}M`
                                : `${(v / 1000).toFixed(0)}K`
                        }
                        label={{
                            value: "Population within 20km (log scale)",
                            position: "bottom",
                            offset: 4,
                            fill: "var(--chart-label)",
                            fontSize: 11,
                        }}
                    />
                    <YAxis
                        dataKey="noise_review_count"
                        type="number"
                        scale="log"
                        domain={["auto", "auto"]}
                        name="Noise Reviews"
                        tick={{ fill: "var(--chart-axis)", fontSize: 11 }}
                        axisLine={{ stroke: "var(--chart-grid)" }}
                        tickLine={false}
                        label={{
                            value: "Total Noise Reviews (log scale)",
                            angle: -90,
                            position: "insideLeft",
                            offset: 4,
                            fill: "var(--chart-label)",
                            fontSize: 11,
                        }}
                    />
                    <ZAxis dataKey="total_flights" range={[40, 600]} name="Flights" />
                    <Tooltip content={<CustomTooltip />} cursor={false} />
                    <Line
                        data={trendData}
                        dataKey="noise_review_count"
                        stroke="var(--accent)"
                        strokeWidth={2}
                        strokeDasharray="8 4"
                        dot={false}
                        activeDot={false}
                        opacity={0.6}
                        name="Trend"
                        legendType="none"
                    />
                    <Scatter data={data} strokeWidth={1} stroke="var(--chart-cursor)">
                        {data.map((entry, i) => (
                            <Cell
                                key={i}
                                fill={sentimentColor(entry.avg_sentiment)}
                                fillOpacity={0.75}
                            />
                        ))}
                    </Scatter>
                </ComposedChart>
            </ResponsiveContainer>
        </div>
    );
}