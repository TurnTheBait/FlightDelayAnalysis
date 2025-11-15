import os
import pandas as pd
from pathlib import Path

RAW_DIR = Path("backend/data/raw/flights")
OUTPUT_DIR = Path("backend/data/processed/flights_filtered")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def filter_flights_with_airports(input_path: str, output_path: str):
    df = pd.read_parquet(input_path)

    required_columns = {"adep", "ades"}

    missing = required_columns - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    df_filtered = df[(df["adep"].notna()) & (df["ades"].notna())]

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df_filtered.to_csv(output_path, index=False)

    print(f"Saved {output_path}")


def process_all_months():
    """Processa tutti i file flight_list_YYYYMM.parquet presenti nella cartella raw."""
    for file in RAW_DIR.glob("flight_list_*.parquet"):
        month = file.stem.replace("flight_list_", "")
        output_file = OUTPUT_DIR / f"flight_list_filtered_{month}.csv"
        print(f"Processing {file} -> {output_file}")
        filter_flights_with_airports(file, output_file)


if __name__ == "__main__":
    process_all_months()