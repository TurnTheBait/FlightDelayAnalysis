import { loadAirportSummary } from "@/lib/csv";
import DelayScatter from "@/components/charts/DelayScatter";
import DelayBarChart from "@/components/charts/DelayBarChart";
import FadeIn from "@/components/FadeIn";

export default function DelaysPage() {
    const allAirports = loadAirportSummary();
    const airports = allAirports.filter(
        (a) => a.delay_weighted_sentiment != null && a.delay_reviews_count != null
    );

    const avgMean =
        airports.reduce((sum, a) => sum + a.delay_weighted_sentiment!, 0) / airports.length;
    const totalDelayReviews = airports.reduce((sum, a) => sum + a.delay_reviews_count!, 0);
    const best = [...airports].sort((a, b) => b.delay_weighted_sentiment! - a.delay_weighted_sentiment!)[0];
    const worst = [...airports].sort((a, b) => a.delay_weighted_sentiment! - b.delay_weighted_sentiment!)[0];

    const delayData = airports.map((a) => ({
        airport_code: a.airport_code,
        mean: a.delay_weighted_sentiment!,
        count: a.delay_reviews_count!,
    }));

    const top15 = [...delayData].sort((a, b) => b.count - a.count).slice(0, 15);

    return (
        <>
            <FadeIn>
                <header className="page-header">
                    <h1 className="page-header__title">Operational Delays</h1>
                    <p className="page-header__subtitle">
                        Passenger sentiment analysis for delay-related reviews across European
                        airports, measuring how flight disruptions impact public perception.
                    </p>
                </header>
            </FadeIn>

            <div className="kpi-row">
                <FadeIn delay={0.05} className="kpi-card">
                    <div className="kpi-card__label">Avg Delay Sentiment</div>
                    <div className="kpi-card__value">{avgMean.toFixed(2)}</div>
                    <div className="kpi-card__sub">Across all airports</div>
                </FadeIn>
                <FadeIn delay={0.1} className="kpi-card">
                    <div className="kpi-card__label">Total Delay Reviews</div>
                    <div className="kpi-card__value">
                        {totalDelayReviews.toLocaleString()}
                    </div>
                    <div className="kpi-card__sub">Filtered for delay topics</div>
                </FadeIn>
                <FadeIn delay={0.15} className="kpi-card">
                    <div className="kpi-card__label">Best Performance</div>
                    <div className="kpi-card__value">{best.airport_code}</div>
                    <div className="kpi-card__sub">
                        Sentiment: {best.delay_weighted_sentiment!.toFixed(2)}
                    </div>
                </FadeIn>
                <FadeIn delay={0.2} className="kpi-card">
                    <div className="kpi-card__label">Most Criticized</div>
                    <div className="kpi-card__value">{worst.airport_code}</div>
                    <div className="kpi-card__sub">
                        Sentiment: {worst.delay_weighted_sentiment!.toFixed(2)}
                    </div>
                </FadeIn>
            </div>

            <div className="bento-grid">
                <FadeIn delay={0.25} className="bento-grid__item col-span-4">
                    <div className="card-title">
                        Delay Sentiment{" "}
                        <span className="card-title__accent">
                            Review Volume vs. Quality
                        </span>
                    </div>
                    <DelayScatter data={delayData} avgMean={avgMean} />
                </FadeIn>

                <FadeIn delay={0.3} className="bento-grid__item col-span-2">
                    <div className="card-title">
                        Top 15{" "}
                        <span className="card-title__accent">by Delay Review Count</span>
                    </div>
                    <DelayBarChart data={top15} />
                </FadeIn>
            </div>
        </>
    );
}
