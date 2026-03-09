"use client";

import { X } from "lucide-react";
import type { AirportWithCoords } from "@/lib/types";

interface Props {
    airport: AirportWithCoords;
    onClose: () => void;
}

function Badge({ value, label }: { value: number | null; label: string }) {
    if (value == null) return null;
    let color = "#5e6ad2";
    if (value >= 6) color = "#3fb950";
    else if (value >= 5) color = "#5e6ad2";
    else if (value >= 4) color = "#d29922";
    else color = "#f85149";

    return (
        <div className="detail-metric">
            <div className="detail-metric__value" style={{ color }}>
                {value.toFixed(1)}
            </div>
            <div className="detail-metric__label">{label}</div>
        </div>
    );
}

function Stat({ value, label }: { value: string; label: string }) {
    return (
        <div className="detail-stat">
            <span className="detail-stat__value">{value}</span>
            <span className="detail-stat__label">{label}</span>
        </div>
    );
}

export default function AirportDetailPanel({ airport, onClose }: Props) {
    const a = airport;

    return (
        <div className="detail-panel">
            <div className="detail-panel__header">
                <div>
                    <div className="detail-panel__code">{a.airport_code}</div>
                    <div className="detail-panel__name">{a.name}</div>
                    <div className="detail-panel__location">
                        {a.municipality}, {a.iso_country}
                    </div>
                </div>
                <button className="detail-panel__close" onClick={onClose}>
                    <X size={18} />
                </button>
            </div>

            <div className="detail-panel__section">
                <div className="detail-panel__section-title">Sentiment Scores</div>
                <div className="detail-metrics-row">
                    <Badge value={a.composite_score} label="Composite" />
                    <Badge value={a.global_weighted_sentiment} label="Global" />
                    <Badge value={a.delay_weighted_sentiment} label="Delay" />
                    <Badge value={a.noise_weighted_sentiment} label="Noise" />
                </div>
            </div>

            <div className="detail-panel__divider" />

            <div className="detail-panel__section">
                <div className="detail-panel__section-title">Media Pressure</div>
                <div className="detail-metrics-row">
                    <Stat value={a.media_pressure_index.toFixed(2)} label="Global" />
                    <Stat value={a.media_pressure_index_delay?.toFixed(2) ?? "N/A"} label="Delay" />
                    <Stat value={a.media_pressure_index_noise?.toFixed(2) ?? "N/A"} label="Noise" />
                </div>
            </div>

            <div className="detail-panel__divider" />

            <div className="detail-panel__section">
                <div className="detail-panel__section-title">Review Volume & Flights</div>
                <div className="detail-stats-grid" style={{ gridTemplateColumns: 'repeat(4, 1fr)' }}>
                    <Stat value={a.total_flights.toLocaleString()} label="Flights" />
                    <Stat value={a.total_mentions.toLocaleString()} label="Mentions" />
                    <Stat value={a.delay_reviews_count?.toLocaleString() ?? "N/A"} label="Delay" />
                    <Stat value={a.noise_reviews_count?.toLocaleString() ?? "N/A"} label="Noise" />
                </div>
            </div>

            <div className="detail-panel__divider" />

            <div className="detail-panel__section">
                <div className="detail-panel__section-title">Source Breakdown</div>
                <div className="detail-sources">
                    <div className="detail-source">
                        <div className="detail-source__bar" style={{
                            width: `${(a.skytrax_count / a.total_mentions) * 100}%`,
                            background: "#5e6ad2"
                        }} />
                        <span className="detail-source__label">Skytrax</span>
                        <span className="detail-source__count">{a.skytrax_count}</span>
                    </div>
                    <div className="detail-source">
                        <div className="detail-source__bar" style={{
                            width: `${(a.google_news_count / a.total_mentions) * 100}%`,
                            background: "#8b5cf6"
                        }} />
                        <span className="detail-source__label">Google News</span>
                        <span className="detail-source__count">{a.google_news_count}</span>
                    </div>
                    <div className="detail-source">
                        <div className="detail-source__bar" style={{
                            width: `${(a.reddit_count / a.total_mentions) * 100}%`,
                            background: "#3fb950"
                        }} />
                        <span className="detail-source__label">Reddit</span>
                        <span className="detail-source__count">{a.reddit_count}</span>
                    </div>
                </div>
            </div>
        </div>
    );
}
