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
    population_10km: number;
}
