import { loadAirportSummary } from "@/lib/csv";
import ReliabilityMatrix from "@/components/charts/ReliabilityMatrix";
import ReviewSourcesChart from "@/components/charts/ReviewSourcesChart";
import PressureDistribution from "@/components/charts/PressureDistribution";
import FadeIn from "@/components/FadeIn";

export default function HomePage() {
  const airports = loadAirportSummary();

  const avgSentiment =
    airports.reduce((sum, a) => sum + a.global_weighted_sentiment, 0) /
    airports.length;
  const totalReviews = airports.reduce((sum, a) => sum + a.total_mentions, 0);
  const avgPressure =
    airports.reduce((sum, a) => sum + a.media_pressure_index, 0) / airports.length;

  const scatterData = airports.map((a) => ({
    airport_code: a.airport_code,
    name: a.name,
    pressure_index: a.media_pressure_index,
    global_weighted_sentiment: a.global_weighted_sentiment,
    total_mentions: a.total_mentions,
  }));

  const top10 = [...airports]
    .sort((a, b) => b.global_weighted_sentiment - a.global_weighted_sentiment)
    .slice(0, 10);

  const reviewSourcesData = [...airports]
    .sort((a, b) => b.total_mentions - a.total_mentions)
    .slice(0, 12)
    .map((a) => ({
      airport_code: a.airport_code,
      google_news: a.google_news_count,
      reddit: a.reddit_count,
      skytrax: a.skytrax_count,
      total: a.total_mentions,
    }));

  const buckets = [
    { label: "0-1", min: 0, max: 1 },
    { label: "1-2", min: 1, max: 2 },
    { label: "2-3", min: 2, max: 3 },
    { label: "3-4", min: 3, max: 4 },
    { label: "4-5", min: 4, max: 5 },
    { label: "5-6", min: 5, max: 6 },
    { label: "6-7", min: 6, max: 7 },
    { label: "7+", min: 7, max: Infinity },
  ];
  const pressureDistData = buckets.map((b) => ({
    label: b.label,
    count: airports.filter(
      (a) => a.media_pressure_index >= b.min && a.media_pressure_index < b.max
    ).length,
  }));

  return (
    <>
      <FadeIn>
        <header className="page-header">
          <h1 className="page-header__title">Global Summary</h1>
          <p className="page-header__subtitle">
            Comprehensive overview of European airport performance combining NLP
            sentiment analysis, media pressure indexing, and review volume across
            {" "}{airports.length} airports.
          </p>
        </header>
      </FadeIn>

      <div className="kpi-row">
        <FadeIn delay={0.05} className="kpi-card">
          <div className="kpi-card__label">Avg Global Sentiment</div>
          <div className="kpi-card__value">{avgSentiment.toFixed(2)}</div>
          <div className="kpi-card__sub">Scale 1-10 across all airports</div>
        </FadeIn>
        <FadeIn delay={0.1} className="kpi-card">
          <div className="kpi-card__label">Total Verified Reviews</div>
          <div className="kpi-card__value">
            {totalReviews.toLocaleString()}
          </div>
          <div className="kpi-card__sub">
            Google News + Reddit + Skytrax
          </div>
        </FadeIn>
        <FadeIn delay={0.15} className="kpi-card">
          <div className="kpi-card__label">Avg Media Pressure</div>
          <div className="kpi-card__value">{avgPressure.toFixed(2)}</div>
          <div className="kpi-card__sub">Logarithmic index of media pressure</div>
        </FadeIn>
      </div>

      <div className="bento-grid">
        <FadeIn delay={0.2} className="bento-grid__item col-span-4">
          <div className="card-title">
            Reliability Matrix{" "}
            <span className="card-title__accent">
              Sentiment vs. Media Pressure
            </span>
          </div>
          <ReliabilityMatrix data={scatterData} />
        </FadeIn>

        <FadeIn delay={0.25} className="bento-grid__item col-span-2">
          <div className="card-title">Top Airports by Sentiment</div>
          <div className="ranking-list">
            {top10.map((a, i) => (
              <div key={a.airport_code} className="ranking-item">
                <span className="ranking-item__rank">{i + 1}</span>
                <span className="ranking-item__code">{a.airport_code}</span>
                <span className="ranking-item__name">{a.name}</span>
                <span className="ranking-item__badge">
                  {a.global_weighted_sentiment.toFixed(1)}
                </span>
              </div>
            ))}
          </div>
        </FadeIn>

        <FadeIn delay={0.3} className="bento-grid__item col-span-3">
          <div className="card-title">
            Review Sources{" "}
            <span className="card-title__accent">Top 12 Airports</span>
          </div>
          <ReviewSourcesChart data={reviewSourcesData} />
        </FadeIn>

        <FadeIn delay={0.35} className="bento-grid__item col-span-3">
          <div className="card-title">
            Pressure Distribution{" "}
            <span className="card-title__accent">Airport Count by Range</span>
          </div>
          <PressureDistribution data={pressureDistData} />
        </FadeIn>
      </div>
    </>
  );
}
