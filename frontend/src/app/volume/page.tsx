import { loadVolumeAnalysis, loadCategoryBenchmarkSummary } from "@/lib/csv";
import VolumeScatter from "@/components/charts/VolumeScatter";
import VolumeRankingChart from "@/components/charts/VolumeRankingChart";
import CategoryBenchmarkChart from "@/components/charts/CategoryBenchmarkChart";
import FadeIn from "@/components/FadeIn";

export default function VolumePage() {
    const airports = loadVolumeAnalysis();
    const benchmarkSummary = loadCategoryBenchmarkSummary();

    const avgSentiment =
        airports.reduce((sum, a) => sum + a.global_weighted_sentiment, 0) /
        airports.length;
    const avgComposite =
        airports.reduce((sum, a) => sum + a.composite_score, 0) /
        airports.length;
    const totalFlights = airports.reduce((sum, a) => sum + a.total_flights, 0);

    const best = [...airports].sort(
        (a, b) => b.composite_score - a.composite_score
    )[0];
    const worst = [...airports].sort(
        (a, b) => a.composite_score - b.composite_score
    )[0];

    const scatterData = airports.map((a) => ({
        airport_code: a.airport_code,
        name: a.name,
        total_flights: a.total_flights,
        global_weighted_sentiment: a.global_weighted_sentiment,
        composite_score: a.composite_score,
    }));

    const top15 = [...airports]
        .sort((a, b) => b.composite_score - a.composite_score)
        .slice(0, 15)
        .map((a) => ({
            airport_code: a.airport_code,
            composite_score: a.composite_score,
            total_flights: a.total_flights,
        }));

    return (
        <>
            <FadeIn>
                <header className="page-header">
                    <h1 className="page-header__title">Volume Analysis</h1>
                    <p className="page-header__subtitle">
                        Sentiment analysis weighted by annual flight volume, combining
                        normalized sentiment and traffic data into a composite reliability
                        score for 115 European airports.
                    </p>
                </header>
            </FadeIn>

            <div className="kpi-row">
                <FadeIn delay={0.05} className="kpi-card">
                    <div className="kpi-card__label">Avg Composite Score</div>
                    <div className="kpi-card__value">{avgComposite.toFixed(2)}</div>
                    <div className="kpi-card__sub">Sentiment × Volume</div>
                </FadeIn>
                <FadeIn delay={0.1} className="kpi-card">
                    <div className="kpi-card__label">Total Flights</div>
                    <div className="kpi-card__value">
                        {totalFlights.toLocaleString()}
                    </div>
                    <div className="kpi-card__sub">Annual volume across all airports</div>
                </FadeIn>
                <FadeIn delay={0.15} className="kpi-card">
                    <div className="kpi-card__label">Best Composite</div>
                    <div className="kpi-card__value">{best.airport_code}</div>
                    <div className="kpi-card__sub">
                        Score: {best.composite_score.toFixed(2)}
                    </div>
                </FadeIn>
                <FadeIn delay={0.2} className="kpi-card">
                    <div className="kpi-card__label">Lowest Ranked</div>
                    <div className="kpi-card__value">{worst.airport_code}</div>
                    <div className="kpi-card__sub">
                        Score: {worst.composite_score.toFixed(2)}
                    </div>
                </FadeIn>
            </div>

            <div className="bento-grid">
                <FadeIn delay={0.25} className="bento-grid__item col-span-4">
                    <div className="card-title">
                        Sentiment{" "}
                        <span className="card-title__accent">
                            vs. Flight Volume
                        </span>
                    </div>
                    <VolumeScatter data={scatterData} avgSentiment={avgSentiment} />
                </FadeIn>

                <FadeIn delay={0.3} className="bento-grid__item col-span-2">
                    <div className="card-title">
                        Top 15{" "}
                        <span className="card-title__accent">
                            by Composite Score
                        </span>
                    </div>
                    <VolumeRankingChart data={top15} />
                </FadeIn>

                <FadeIn delay={0.35} className="bento-grid__item col-span-6">
                    <div className="card-title">
                        Performance Benchmark{" "}
                        <span className="card-title__accent">
                            by Airport Size
                        </span>
                    </div>
                    <CategoryBenchmarkChart data={benchmarkSummary} />
                </FadeIn>
            </div>
        </>
    );
}