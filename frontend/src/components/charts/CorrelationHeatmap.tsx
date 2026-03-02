"use client";

interface Props {
    labels: string[];
    values: number[][];
}

function cellColor(val: number): string {
    if (val >= 0.8) return "rgba(63, 185, 80, 0.7)";
    if (val >= 0.4) return "rgba(63, 185, 80, 0.35)";
    if (val >= 0.1) return "rgba(63, 185, 80, 0.15)";
    if (val >= -0.1) return "rgba(255, 255, 255, 0.04)";
    if (val >= -0.4) return "rgba(248, 81, 73, 0.15)";
    if (val >= -0.8) return "rgba(248, 81, 73, 0.35)";
    return "rgba(248, 81, 73, 0.7)";
}

function textColor(val: number): string {
    const abs = Math.abs(val);
    if (abs >= 0.4) return "rgba(255,255,255,0.9)";
    return "rgba(255,255,255,0.5)";
}

const SHORT_LABELS: Record<string, string> = {
    global_sentiment: "Sentiment",
    MinLateDeparted: "Dep Delay",
    MinLateArrived: "Arr Delay",
    Dep_prcp: "Precip",
    Dep_wspd: "Wind Spd",
    Dep_temp: "Temp",
};

export default function CorrelationHeatmap({ labels, values }: Props) {
    return (
        <table className="heatmap-table">
            <thead>
                <tr>
                    <th />
                    {labels.map((l) => (
                        <th key={l}>{SHORT_LABELS[l] || l}</th>
                    ))}
                </tr>
            </thead>
            <tbody>
                {labels.map((rowLabel, ri) => (
                    <tr key={rowLabel}>
                        <td className="heatmap-table__row-label">
                            {SHORT_LABELS[rowLabel] || rowLabel}
                        </td>
                        {values[ri].map((val, ci) => (
                            <td
                                key={ci}
                                style={{
                                    background: cellColor(val),
                                    color: textColor(val),
                                }}
                            >
                                {val.toFixed(2)}
                            </td>
                        ))}
                    </tr>
                ))}
            </tbody>
        </table>
    );
}
