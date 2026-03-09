import fs from "fs";
import path from "path";
import Papa from "papaparse";
import type {
    AirportSummary,
    AirportWithCoords,
    AirportVolumeAnalysis,
    WeatherLaggedEvent,
    NoiseSentimentPopulation,
    CorrelationMatrix,
} from "./types";

const TABLES_DIR = path.resolve(
    process.cwd(),
    "..",
    "backend",
    "results",
    "tables"
);

function loadCSV<T>(relativePath: string): T[] {
    const filePath = path.join(TABLES_DIR, relativePath);
    const raw = fs.readFileSync(filePath, "utf-8");
    const result = Papa.parse<T>(raw, {
        header: true,
        dynamicTyping: true,
        skipEmptyLines: true,
    });
    return result.data;
}

export function loadAirportSummary(): AirportSummary[] {
    return loadCSV<AirportSummary>("airport_analysis_summary.csv");
}

export function loadWeatherData(): WeatherLaggedEvent[] {
    return loadCSV<WeatherLaggedEvent>("weather_event_lagged_analysis.csv");
}

export function loadCorrelationData(): CorrelationMatrix {
    const filePath = path.join(TABLES_DIR, "correlation_delay_weather_summary.csv");
    const raw = fs.readFileSync(filePath, "utf-8");
    const result = Papa.parse<Record<string, string | number>>(raw, {
        header: true,
        dynamicTyping: true,
        skipEmptyLines: true,
    });

    const labels = Object.keys(result.data[0]).filter((k) => k !== "");
    const values = result.data.map((row) =>
        labels.map((label) => Number(row[label]))
    );

    return { labels, values };
}

export function loadNoisePopulationData(): NoiseSentimentPopulation[] {
    return loadCSV<NoiseSentimentPopulation>(
        "noise_sentiment_10km_population.csv"
    );
}

export function loadAirportsWithCoords(): AirportWithCoords[] {
    const airports = loadVolumeAnalysis();
    const coordsPath = path.resolve(
        process.cwd(),
        "..",
        "backend",
        "data",
        "processed",
        "airports",
        "airports_filtered.csv"
    );
    const raw = fs.readFileSync(coordsPath, "utf-8");
    const coordsResult = Papa.parse<{
        iata_code: string;
        latitude_deg: number;
        longitude_deg: number;
    }>(raw, { header: true, dynamicTyping: true, skipEmptyLines: true });

    const coordsMap = new Map(
        coordsResult.data.map((c) => [c.iata_code, c])
    );

    return airports
        .filter((a) => coordsMap.has(a.airport_code))
        .map((a) => {
            const c = coordsMap.get(a.airport_code)!;
            return { ...a, latitude_deg: c.latitude_deg, longitude_deg: c.longitude_deg };
        });
}

export function loadVolumeAnalysis(): AirportVolumeAnalysis[] {
    return loadCSV<AirportVolumeAnalysis>("airport_volume_analysis_summary.csv");
}

