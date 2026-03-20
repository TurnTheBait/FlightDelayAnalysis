"use client";

import type { CategoryBenchmarkSummary } from "@/lib/types";

interface Props {
    data: CategoryBenchmarkSummary[];
}

const CATEGORY_COLORS: Record<string, string> = {
    Hub: "#e74c3c",
    Large: "#f39c12",
    Medium: "#3498db",
    Small: "#2ecc71",
};

export default function BenchmarkClassificationTable({ data }: Props) {
    return (
        <div className="benchmark-table-wrap">
            <table className="benchmark-table">
                <thead>
                    <tr>
                        <th>Category</th>
                        <th>Airports</th>
                        <th>Mean</th>
                        <th>Std</th>
                        <th>Min</th>
                        <th>Max</th>
                        <th>Best</th>
                        <th>Worst</th>
                    </tr>
                </thead>
                <tbody>
                    {data.map((row) => (
                        <tr key={row.category}>
                            <td>
                                <span
                                    className="benchmark-table__cat-badge"
                                    style={{ background: `${CATEGORY_COLORS[row.category] ?? "var(--accent)"}22`, color: CATEGORY_COLORS[row.category] ?? "var(--accent)" }}
                                >
                                    {row.category}
                                </span>
                            </td>
                            <td>{row.n_airports}</td>
                            <td><strong>{row.mean_sentiment.toFixed(2)}</strong></td>
                            <td>{row.std_sentiment.toFixed(2)}</td>
                            <td style={{ color: "#f85149" }}>{row.min_sentiment.toFixed(2)}</td>
                            <td style={{ color: "#3fb950" }}>{row.max_sentiment.toFixed(2)}</td>
                            <td className="benchmark-table__airport">{row.best_airport}</td>
                            <td className="benchmark-table__airport">{row.worst_airport}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}
