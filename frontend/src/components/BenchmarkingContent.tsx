"use client";

import { useState } from "react";
import BenchmarkDetailChart from "@/components/charts/BenchmarkDetailChart";
import BenchmarkClassificationTable from "@/components/charts/BenchmarkClassificationTable";
import type { CategoryBenchmarkSummary, BenchmarkAirport } from "@/lib/types";
import FadeIn from "@/components/FadeIn";

type BenchmarkMode = "general" | "delay" | "noise";
type CategoryName = "hub" | "large" | "medium" | "small";

const MODE_LABELS: Record<BenchmarkMode, string> = {
    general: "General",
    delay: "Delay",
    noise: "Noise",
};

const CATEGORY_LABELS: Record<CategoryName, string> = {
    hub: "Hub",
    large: "Large",
    medium: "Medium",
    small: "Small",
};

const CATEGORY_COLORS: Record<CategoryName, string> = {
    hub: "#e74c3c",
    large: "#f39c12",
    medium: "#3498db",
    small: "#2ecc71",
};

interface Props {
    summaries: Record<BenchmarkMode, CategoryBenchmarkSummary[]>;
    details: Record<BenchmarkMode, Record<CategoryName, BenchmarkAirport[]>>;
    categoryCounts: Record<CategoryName, number>;
}

export default function BenchmarkingContent({ summaries, details, categoryCounts }: Props) {
    const [mode, setMode] = useState<BenchmarkMode>("general");

    const MODES: BenchmarkMode[] = ["general", "delay", "noise"];
    const CATEGORIES: CategoryName[] = ["hub", "large", "medium", "small"];

    return (
        <>
            {/* KPI row */}
            <div className="kpi-row">
                {CATEGORIES.map((cat, i) => (
                    <FadeIn key={cat} delay={0.05 + i * 0.05} className="kpi-card">
                        <div className="kpi-card__label">{CATEGORY_LABELS[cat]} Airports</div>
                        <div className="kpi-card__value" style={{ color: CATEGORY_COLORS[cat] }}>
                            {categoryCounts[cat]}
                        </div>
                        <div className="kpi-card__sub">
                            {cat === "hub" && "≥ 100k flights/year"}
                            {cat === "large" && "40k – 99k flights/year"}
                            {cat === "medium" && "5k – 39k flights/year"}
                            {cat === "small" && "< 5k flights/year"}
                        </div>
                    </FadeIn>
                ))}
            </div>

            {/* Mode selector */}
            <FadeIn delay={0.25}>
                <div className="mode-selector">
                    {MODES.map((m) => (
                        <button
                            key={m}
                            className={`mode-selector__btn ${mode === m ? "mode-selector__btn--active" : ""}`}
                            onClick={() => setMode(m)}
                        >
                            {MODE_LABELS[m]}
                        </button>
                    ))}
                </div>
            </FadeIn>

            {/* Summary table */}
            <FadeIn delay={0.3}>
                <div className="bento-grid">
                    <div className="bento-grid__item col-span-6">
                        <div className="card-title">
                            Airport Classification{" "}
                            <span className="card-title__accent">
                                — {MODE_LABELS[mode]} Sentiment
                            </span>
                        </div>
                        <BenchmarkClassificationTable data={summaries[mode]} />
                    </div>
                </div>
            </FadeIn>

            {/* Detail charts */}
            <div className="bento-grid">
                {CATEGORIES.map((cat, i) => {
                    const catData = details[mode]?.[cat] ?? [];
                    if (catData.length === 0) return null;
                    return (
                        <FadeIn key={cat} delay={0.35 + i * 0.05} className="bento-grid__item col-span-3">
                            <div className="card-title">
                                <span
                                    className="benchmark-table__cat-badge"
                                    style={{
                                        background: `${CATEGORY_COLORS[cat]}22`,
                                        color: CATEGORY_COLORS[cat],
                                        marginRight: 8,
                                    }}
                                >
                                    {CATEGORY_LABELS[cat]}
                                </span>
                                <span className="card-title__accent">
                                    Sentiment Ranking
                                </span>
                            </div>
                            <BenchmarkDetailChart data={catData} categoryName={CATEGORY_LABELS[cat]} />
                        </FadeIn>
                    );
                })}
            </div>
        </>
    );
}
