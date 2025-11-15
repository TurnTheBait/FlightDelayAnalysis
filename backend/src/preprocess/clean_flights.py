import os
import pandas as pd
from pathlib import Path

RAW_FLIGHTS = Path("backend/data/raw/flights")
RAW_AIRPORTS = Path("backend/data/raw/airports/airports.csv")
OUTPUT_DIR = Path("backend/data/processed/flights_filtered")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = OUTPUT_DIR / "flight_list_filtered_2024.csv"

# 👇 colonne da rimuovere
COLUMNS_TO_DROP = ["ades_p", "adep_p", "version"]


def load_european_airports():
    """Carica e filtra aeroporti europei di grandi dimensioni."""
    df_air = pd.read_csv(RAW_AIRPORTS)

    df_air = df_air[
        (df_air["type"] == "large_airport") &
        (df_air["continent"] == "EU")
    ]

    return df_air[["ident", "name", "continent"]].rename(columns={"ident": "icao"})


def filter_and_merge_flights():
    """Unisce e filtra tutti i flight_list_2024*.parquet producendo un unico CSV."""
    european_airports = load_european_airports()
    valid_icao = set(european_airports["icao"].unique())

    all_flights = []

    for file in RAW_FLIGHTS.glob("flight_list_2024*.parquet"):
        print(f"Loading {file}...")
        df = pd.read_parquet(file)

        # Controllo colonne necessarie
        required = {"adep", "ades"}
        missing = required - set(df.columns)
        if missing:
            raise ValueError(f"Missing columns in {file}: {missing}")

        # Filtra voli con adep e ades non nulli
        df = df[(df["adep"].notna()) & (df["ades"].notna())]

        # Filtra solo aeroporti europei grandi
        df = df[df["adep"].isin(valid_icao) & df["ades"].isin(valid_icao)]

        # 👇 Rimuove le colonne inutili (senza errori se mancano)
        df = df.drop(columns=[c for c in COLUMNS_TO_DROP if c in df.columns])

        all_flights.append(df)

    if not all_flights:
        raise RuntimeError("No flights loaded for 2024.")

    df_all = pd.concat(all_flights, ignore_index=True)
    print(f"Total flights after filtering: {len(df_all)}")

    df_all.to_csv(OUTPUT_FILE, index=False)
    print(f"Saved merged file → {OUTPUT_FILE}")


if __name__ == "__main__":
    filter_and_merge_flights()