import { loadAirportSummary, loadNoisePopulationData } from "@/lib/csv";
import NoisePopulationScatter from "@/components/charts/NoisePopulationScatter";
import NoiseRankingChart from "@/components/charts/NoiseRankingChart";

export default function NoisePage() {
    const allAirports = loadAirportSummary();
    const airports = allAirports.filter(
        (a) => a.noise_weighted_sentiment != null && a.noise_reviews_count != null
    );
    const population = loadNoisePopulationData();

    const avgNoiseSentiment =
        airports.reduce((sum, a) => sum + a.noise_weighted_sentiment!, 0) /
        airports.length;

    const highestPop = [...population].sort(
        (a, b) => b.population_10km - a.population_10km
    )[0];

    const lowestSentiment = [...airports].sort(
        (a, b) => a.noise_weighted_sentiment! - b.noise_weighted_sentiment!
    )[0];

    const top15Noise = [...airports]
        .sort((a, b) => b.noise_weighted_sentiment! - a.noise_weighted_sentiment!)
        .slice(0, 15)
        .map((a) => ({
            airport_code: a.airport_code,
            mean: a.noise_weighted_sentiment!,
            count: a.noise_reviews_count!,
        }));

    return (
        <>
            <header className="page-header">
                <h1 className="page-header__title">Noise & Population</h1>
                <p className="page-header__subtitle">
                    Analyzing the relationship between airport noise sentiment and the
                    population living within a 10km radius, calculated using WorldPop
                    GeoTIFF raster data.
                </p>
            </header>

            <div className="kpi-row">
                <div className="kpi-card">
                    <div className="kpi-card__label">Avg Noise Sentiment</div>
                    <div className="kpi-card__value">{avgNoiseSentiment.toFixed(2)}</div>
                    <div className="kpi-card__sub">Across {airports.length} airports</div>
                </div>
                <div className="kpi-card">
                    <div className="kpi-card__label">Highest Population Exposure</div>
                    <div className="kpi-card__value">{highestPop.airport_code}</div>
                    <div className="kpi-card__sub">
                        {Math.round(highestPop.population_10km).toLocaleString()} residents
                    </div>
                </div>
                <div className="kpi-card">
                    <div className="kpi-card__label">Lowest Noise Sentiment</div>
                    <div className="kpi-card__value">
                        {lowestSentiment.airport_code}
                    </div>
                    <div className="kpi-card__sub">
                        Score: {lowestSentiment.noise_weighted_sentiment!.toFixed(2)}
                    </div>
                </div>
            </div>

            <div className="bento-grid">
                <div className="bento-grid__item col-span-4">
                    <div className="card-title">
                        Noise Sentiment{" "}
                        <span className="card-title__accent">
                            vs. Population Exposure
                        </span>
                    </div>
                    <NoisePopulationScatter data={population} />
                </div>

                <div className="bento-grid__item col-span-2">
                    <div className="card-title">
                        Top 15{" "}
                        <span className="card-title__accent">
                            by Noise Review Sentiment
                        </span>
                    </div>
                    <NoiseRankingChart data={top15Noise} />
                </div>
            </div>
        </>
    );
}
