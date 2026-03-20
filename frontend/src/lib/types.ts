export interface AirportSummary {
    airport_code: string;
    name: string;
    iso_country: string;
    municipality: string;
    google_news_count: number;
    reddit_count: number;
    skytrax_count: number;
    total_mentions: number;
    delay_reviews_count: number | null;
    noise_reviews_count: number | null;
    media_pressure_index: number;
    media_pressure_index_delay: number | null;
    media_pressure_index_noise: number | null;
    global_weighted_sentiment: number;
    delay_weighted_sentiment: number | null;
    noise_weighted_sentiment: number | null;
}

export interface WeatherLaggedEvent {
    airport_code: string;
    event_date: string;
    event_type: string;
    precip: number | null;
    wind: number;
    sentiment_t0: number;
    sentiment_t1: number;
    sentiment_t2: number;
    sentiment_t3: number;
    neg_count_t0: number;
    neg_count_t1: number;
    neg_count_t2: number;
    neg_count_t3: number;
}

export interface CorrelationMatrix {
    labels: string[];
    values: number[][];
}

export interface NoiseSentimentPopulation {
    airport_code: string;
    name: string;
    avg_sentiment: number;
    population_20km: number;
    noise_review_count: number;
    total_flights: number;
}

export interface CategoryBenchmarkSummary {
    category: string;
    n_airports: number;
    mean_sentiment: number;
    std_sentiment: number;
    min_sentiment: number;
    max_sentiment: number;
    best_airport: string;
    worst_airport: string;
}

export interface AirportWithCoords extends AirportVolumeAnalysis {
    latitude_deg: number;
    longitude_deg: number;
}

export interface AirportVolumeAnalysis {
    airport_code: string;
    name: string;
    iso_country: string;
    municipality: string;
    google_news_count: number;
    reddit_count: number;
    skytrax_count: number;
    total_mentions: number;
    delay_reviews_count: number | null;
    noise_reviews_count: number | null;
    media_pressure_index: number;
    media_pressure_index_delay: number | null;
    media_pressure_index_noise: number | null;
    global_weighted_sentiment: number;
    delay_weighted_sentiment: number | null;
    noise_weighted_sentiment: number | null;
    total_flights: number;
    sentiment_norm: number;
    volume_norm: number;
    composite_score: number;
}

export interface BenchmarkAirport {
    airport_code: string;
    name: string;
    total_flights: number;
    sentiment_score: number;
    category_mean: number;
    z_score: number;
    rank: number;
}
