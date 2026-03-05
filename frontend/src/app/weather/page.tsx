import { loadWeatherData, loadCorrelationData } from "@/lib/csv";
import LaggedSentimentChart from "@/components/charts/LaggedSentimentChart";
import NegativeReviewsChart from "@/components/charts/NegativeReviewsChart";
import CorrelationHeatmap from "@/components/charts/CorrelationHeatmap";
import FadeIn from "@/components/FadeIn";

export default function WeatherPage() {
    const events = loadWeatherData();
    const correlation = loadCorrelationData();

    const eventTypes = ["None", "Wind", "Rain", "Rain & Wind"];
    const grouped: Record<string, { t0: number[]; t1: number[]; t2: number[]; t3: number[] }> = {};
    const groupedNeg: Record<string, { t0: number[]; t1: number[]; t2: number[]; t3: number[] }> = {};

    for (const type of eventTypes) {
        grouped[type] = { t0: [], t1: [], t2: [], t3: [] };
        groupedNeg[type] = { t0: [], t1: [], t2: [], t3: [] };
    }
    for (const e of events) {
        const type = e.event_type || "None";
        if (grouped[type]) {
            grouped[type].t0.push(e.sentiment_t0);
            grouped[type].t1.push(e.sentiment_t1);
            grouped[type].t2.push(e.sentiment_t2);
            grouped[type].t3.push(e.sentiment_t3);
            groupedNeg[type].t0.push(e.neg_count_t0);
            groupedNeg[type].t1.push(e.neg_count_t1);
            groupedNeg[type].t2.push(e.neg_count_t2);
            groupedNeg[type].t3.push(e.neg_count_t3);
        }
    }

    const avg = (arr: number[]) =>
        arr.length ? arr.reduce((a, b) => a + b, 0) / arr.length : null;

    const timeLabels = [
        { label: "Event Day (t0)" },
        { label: "Day +1 (t1)" },
        { label: "Day +2 (t2)" },
        { label: "Day +3 (t3)" },
    ];

    const laggedData = timeLabels.map((row, i) => {
        const key = `t${i}` as "t0" | "t1" | "t2" | "t3";
        const result: Record<string, string | number | null> = { label: row.label };
        for (const type of eventTypes) {
            result[type] = avg(grouped[type][key]);
        }
        return result;
    });

    const negData = timeLabels.map((row, i) => {
        const key = `t${i}` as "t0" | "t1" | "t2" | "t3";
        const result: Record<string, string | number | null> = { label: row.label };
        for (const type of eventTypes) {
            result[type] = avg(groupedNeg[type][key]);
        }
        return result;
    });

    const totalEvents = events.length;
    const windEvents = events.filter((e) => e.event_type === "Wind").length;
    const rainEvents = events.filter(
        (e) => e.event_type === "Rain" || e.event_type === "Rain & Wind"
    ).length;

    const avgT0 = avg(events.map((e) => e.sentiment_t0)) || 0;
    const avgT3 = avg(events.map((e) => e.sentiment_t3)) || 0;
    const sentimentDelta = avgT3 - avgT0;

    return (
        <>
            <FadeIn>
                <header className="page-header">
                    <h1 className="page-header__title">Weather Impact</h1>
                    <p className="page-header__subtitle">
                        Lagged analysis showing how weather events at departure airports
                        influence passenger sentiment over a 3-day window.
                    </p>
                </header>
            </FadeIn>

            <div className="kpi-row">
                <FadeIn delay={0.05} className="kpi-card">
                    <div className="kpi-card__label">Total Weather Events</div>
                    <div className="kpi-card__value">{totalEvents}</div>
                    <div className="kpi-card__sub">Analyzed in the dataset</div>
                </FadeIn>
                <FadeIn delay={0.1} className="kpi-card">
                    <div className="kpi-card__label">Wind Events</div>
                    <div className="kpi-card__value">{windEvents}</div>
                    <div className="kpi-card__sub">
                        {((windEvents / totalEvents) * 100).toFixed(1)}% of total
                    </div>
                </FadeIn>
                <FadeIn delay={0.15} className="kpi-card">
                    <div className="kpi-card__label">Rain Events</div>
                    <div className="kpi-card__value">{rainEvents}</div>
                    <div className="kpi-card__sub">Including Rain & Wind</div>
                </FadeIn>
                <FadeIn delay={0.2} className="kpi-card">
                    <div className="kpi-card__label">Sentiment Delta (t0 → t3)</div>
                    <div className="kpi-card__value">
                        {sentimentDelta > 0 ? "+" : ""}
                        {sentimentDelta.toFixed(2)}
                    </div>
                    <div className="kpi-card__sub">Average shift over 3 days</div>
                </FadeIn>
            </div>

            <div className="bento-grid">
                <FadeIn delay={0.25} className="bento-grid__item col-span-4">
                    <div className="card-title">
                        Lagged Sentiment{" "}
                        <span className="card-title__accent">by Event Type</span>
                    </div>
                    <LaggedSentimentChart data={laggedData as any} />
                </FadeIn>

                <FadeIn delay={0.3} className="bento-grid__item col-span-2">
                    <div className="card-title">
                        Correlation Matrix{" "}
                        <span className="card-title__accent">Weather & Delays</span>
                    </div>
                    <CorrelationHeatmap
                        labels={correlation.labels}
                        values={correlation.values}
                    />
                </FadeIn>

                <FadeIn delay={0.35} className="bento-grid__item col-span-6">
                    <div className="card-title">
                        Negative Review Volume{" "}
                        <span className="card-title__accent">by Event Type (Lagged)</span>
                    </div>
                    <NegativeReviewsChart data={negData as any} />
                </FadeIn>
            </div>
        </>
    );
}
