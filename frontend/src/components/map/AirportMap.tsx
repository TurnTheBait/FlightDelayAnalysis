"use client";

import { useState, useMemo, useRef, useCallback } from "react";
import { MapContainer, TileLayer, CircleMarker, ZoomControl, useMap } from "react-leaflet";
import type { AirportWithCoords } from "@/lib/types";
import AirportSearch from "./AirportSearch";
import AirportDetailPanel from "./AirportDetailPanel";
import "leaflet/dist/leaflet.css";

interface Props {
    airports: AirportWithCoords[];
}

function sentimentColor(val: number): string {
    if (val >= 6) return "#3fb950";
    if (val >= 5) return "#5e6ad2";
    if (val >= 4) return "#d29922";
    return "#f85149";
}

function markerRadius(mentions: number, max: number): number {
    const min = 4;
    const maxR = 18;
    return min + (mentions / max) * (maxR - min);
}

function FlyTo({ lat, lng, zoom }: { lat: number; lng: number; zoom: number }) {
    const map = useMap();
    map.flyTo([lat, lng], zoom, { duration: 1.2 });
    return null;
}

export default function AirportMap({ airports }: Props) {
    const [selected, setSelected] = useState<AirportWithCoords | null>(null);
    const [flyTarget, setFlyTarget] = useState<{ lat: number; lng: number; zoom: number } | null>(null);
    const flyTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

    const maxMentions = useMemo(
        () => Math.max(...airports.map((a) => a.total_mentions), 1),
        [airports]
    );

    const handleSelect = useCallback((airport: AirportWithCoords) => {
        setSelected(airport);
        setFlyTarget({ lat: airport.latitude_deg, lng: airport.longitude_deg, zoom: 8 });
        if (flyTimeoutRef.current) clearTimeout(flyTimeoutRef.current);
        flyTimeoutRef.current = setTimeout(() => setFlyTarget(null), 1500);
    }, []);

    const handleClose = useCallback(() => {
        setSelected(null);
    }, []);

    return (
        <div className="map-page">
            <AirportSearch airports={airports} onSelect={handleSelect} />
            <MapContainer
                center={[50.5, 12]}
                zoom={5}
                className="map-container"
                zoomControl={false}
                attributionControl={false}
            >
                <ZoomControl position="bottomright" />
                <TileLayer url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png" />
                {flyTarget && (
                    <FlyTo lat={flyTarget.lat} lng={flyTarget.lng} zoom={flyTarget.zoom} />
                )}
                {airports.map((a) => (
                    <CircleMarker
                        key={a.airport_code}
                        center={[a.latitude_deg, a.longitude_deg]}
                        radius={markerRadius(a.total_mentions, maxMentions)}
                        pathOptions={{
                            fillColor: sentimentColor(a.global_weighted_sentiment),
                            fillOpacity: 0.75,
                            color: "rgba(255,255,255,0.2)",
                            weight: 1,
                        }}
                        eventHandlers={{
                            click: () => handleSelect(a),
                        }}
                    />
                ))}
            </MapContainer>
            {selected && (
                <AirportDetailPanel airport={selected} onClose={handleClose} />
            )}
            <div className="map-legend">
                <div className="map-legend__title">Sentiment</div>
                <div className="map-legend__items">
                    <div className="map-legend__item">
                        <span className="map-legend__dot" style={{ background: "#3fb950" }} />
                        <span>&ge; 6</span>
                    </div>
                    <div className="map-legend__item">
                        <span className="map-legend__dot" style={{ background: "#5e6ad2" }} />
                        <span>5 &ndash; 6</span>
                    </div>
                    <div className="map-legend__item">
                        <span className="map-legend__dot" style={{ background: "#d29922" }} />
                        <span>4 &ndash; 5</span>
                    </div>
                    <div className="map-legend__item">
                        <span className="map-legend__dot" style={{ background: "#f85149" }} />
                        <span>&lt; 4</span>
                    </div>
                </div>
            </div>
        </div>
    );
}
