import pandas as pd
import os
import glob

current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.abspath(os.path.join(current_dir, "..", ".."))

INPUT_DIR = os.path.join(backend_dir, "data", "raw", "flight_events")
OUTPUT_DIR = os.path.join(backend_dir, "data", "processed", "flight_events_processed")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "flight_events_full.csv")

def convert_parquet_to_csv():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    files = glob.glob(os.path.join(INPUT_DIR, "*.parquet"))
    
    if not files:
        print(f"Nessun file trovato in: {INPUT_DIR}")
        return

    print(f"Trovati {len(files)} file. Inizio elaborazione...")
    dataframes = []
    
    for file in files:
        try:
            df = pd.read_parquet(file)
            dataframes.append(df)
            print(f"Letto: {os.path.basename(file)}")
        except Exception as e:
            print(f"Errore su {file}: {e}")

    if not dataframes:
        return

    full_df = pd.concat(dataframes, ignore_index=True)

    if 'event_time' in full_df.columns:
        full_df.sort_values(by='event_time', inplace=True)

    full_df.to_csv(OUTPUT_FILE, index=False)
    print(f"Salvato con successo: {OUTPUT_FILE}")
    print(f"Righe totali: {len(full_df)}")

if __name__ == "__main__":
    convert_parquet_to_csv()