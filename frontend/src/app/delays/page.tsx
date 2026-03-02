import { loadDelayData } from "@/lib/csv";
import DelayScatter from "@/components/charts/DelayScatter";
import DelayBarChart from "@/components/charts/DelayBarChart";

export default function DelaysPage() {
    const delays = loadDelayData();

    const avgMean =
        delays.reduce((sum, d) => sum + d.mean, 0) / delays.length;
    const totalDelayReviews = delays.reduce((sum, d) => sum + d.count, 0);
    const best = [...delays].sort((a, b) => b.mean - a.mean)[0];
    const worst = [...delays].sort((a, b) => a.mean - b.mean)[0];

    const top15 = [...delays].sort((a, b) => b.count - a.count).slice(0, 15);

    return (
        <>
            <header className="page-header">
                <h1 className="page-header__title">Operational Delays</h1>
                <p className="page-header__subtitle">
                    Passenger sentiment analysis for delay-related reviews across European
                    airports, measuring how flight disruptions impact public perception.
                </p>
            </header>

            <div className="kpi-row">
                <div className="kpi-card">
                    <div className="kpi-card__label">Avg Delay Sentiment</div>
                    <div className="kpi-card__value">{avgMean.toFixed(2)}</div>
                    <div className="kpi-card__sub">Across all airports</div>
                </div>
                <div className="kpi-card">
                    <div className="kpi-card__label">Total Delay Reviews</div>
                    <div className="kpi-card__value">
                        {totalDelayReviews.toLocaleString()}
                    </div>
                    <div className="kpi-card__sub">Filtered for delay topics</div>
                </div>
                <div className="kpi-card">
                    <div className="kpi-card__label">Best Performance</div>
                    <div className="kpi-card__value">{best.airport_code}</div>
                    <div className="kpi-card__sub">
                        Sentiment: {best.mean.toFixed(2)}
                    </div>
                </div>
                <div className="kpi-card">
                    <div className="kpi-card__label">Most Criticized</div>
                    <div className="kpi-card__value">{worst.airport_code}</div>
                    <div className="kpi-card__sub">
                        Sentiment: {worst.mean.toFixed(2)}
                    </div>
                </div>
            </div>

            <div className="bento-grid">
                <div className="bento-grid__item col-span-4">
                    <div className="card-title">
                        Delay Sentiment{" "}
                        <span className="card-title__accent">
                            Review Volume vs. Quality
                        </span>
                    </div>
                    <DelayScatter data={delays} avgMean={avgMean} />
                </div>

                <div className="bento-grid__item col-span-2">
                    <div className="card-title">
                        Top 15{" "}
                        <span className="card-title__accent">by Delay Review Count</span>
                    </div>
                    <DelayBarChart data={top15} />
                </div>
            </div>
        </>
    );
}
