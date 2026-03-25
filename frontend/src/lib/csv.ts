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
    BenchmarkAirport,
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
        "population_analysis/population_sentiment_noise_raster.csv"
    );
}

export function loadAirportsWithCoords(): AirportWithCoords[] {
    const summaries = loadAirportSummary();
    const volumeData = loadVolumeAnalysis();
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

    const volumeMap = new Map(
        volumeData.map((v) => [v.airport_code, v])
    );

    return summaries
        .filter((a) => coordsMap.has(a.airport_code))
        .map((a) => {
            const c = coordsMap.get(a.airport_code)!;
            const v = volumeMap.get(a.airport_code);
            return {
                ...a,
                latitude_deg: c.latitude_deg,
                longitude_deg: c.longitude_deg,
                total_flights: v?.total_flights ?? 0,
                sentiment_norm: v?.sentiment_norm ?? 0,
                volume_norm: v?.volume_norm ?? 0,
                composite_score: v?.composite_score ?? a.global_weighted_sentiment,
            };
        });
}

export function loadVolumeAnalysis(): AirportVolumeAnalysis[] {
    return loadCSV<AirportVolumeAnalysis>("airport_volume_analysis_summary.csv");
}

export function loadCategoryBenchmarkSummary(): import("./types").CategoryBenchmarkSummary[] {
    return loadCSV<import("./types").CategoryBenchmarkSummary>("category_benchmarking/summary_general.csv");
}

type BenchmarkMode = "general" | "delay" | "noise";
type CategoryName = "hub" | "large" | "medium" | "small";

const CATEGORIES: CategoryName[] = ["hub", "large", "medium", "small"];
const MODES: BenchmarkMode[] = ["general", "delay", "noise"];

export function loadBenchmarkDetail(mode: BenchmarkMode, category: CategoryName): BenchmarkAirport[] {
    return loadCSV<BenchmarkAirport>(`category_benchmarking/benchmarking_${mode}_${category}.csv`);
}

export interface AllBenchmarkData {
    summaries: Record<BenchmarkMode, import("./types").CategoryBenchmarkSummary[]>;
    details: Record<BenchmarkMode, Record<CategoryName, BenchmarkAirport[]>>;
}

export function loadAllBenchmarkData(): AllBenchmarkData {
    const summaries = {} as Record<BenchmarkMode, import("./types").CategoryBenchmarkSummary[]>;
    const details = {} as Record<BenchmarkMode, Record<CategoryName, BenchmarkAirport[]>>;

    for (const mode of MODES) {
        summaries[mode] = loadCSV<import("./types").CategoryBenchmarkSummary>(`category_benchmarking/summary_${mode}.csv`);
        details[mode] = {} as Record<CategoryName, BenchmarkAirport[]>;
        for (const cat of CATEGORIES) {
            try {
                details[mode][cat] = loadBenchmarkDetail(mode, cat);
            } catch {
                details[mode][cat] = [];
            }
        }
    }

    return { summaries, details };
}

