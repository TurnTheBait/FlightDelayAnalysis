import polars as pl
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
DATA_DIR = BASE_DIR / "backend" / "data"
RAW_SCHEDULE_FILE = DATA_DIR / "raw" / "schedule" / "Schedule_23-24.csv"
PROCESSED_AIRPORTS_FILE = DATA_DIR / "processed" / "airports" / "airports_filtered.csv"
OUTPUT_DIR = DATA_DIR / "processed" / "schedule"
OUTPUT_FILE = OUTPUT_DIR / "clean_schedule_23-24.csv"

COLS_TO_DROP = ['ac_code', 'ac_name', 'ac_code_spec', 'ac_name_spec', 'freq', 'seats']

def main():
    if not RAW_SCHEDULE_FILE.exists():
        print(f"ERRORE: File schedulato non trovato: {RAW_SCHEDULE_FILE}")
        return
    
    if not PROCESSED_AIRPORTS_FILE.exists():
        print(f"ERRORE: File aeroporti filtrati non trovato: {PROCESSED_AIRPORTS_FILE}")
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Caricamento schedulato (Polars): {RAW_SCHEDULE_FILE}")
    df_sched = pl.read_csv(RAW_SCHEDULE_FILE, ignore_errors=True)
    
    print(f"Caricamento aeroporti filtrati: {PROCESSED_AIRPORTS_FILE}")
    df_airports = pl.read_csv(PROCESSED_AIRPORTS_FILE)
    
    if 'iata_code' not in df_airports.columns:
        print("ERRORE: Colonna 'iata_code' mancante nel file aeroporti.")
        return
        
    valid_iata = df_airports['iata_code'].drop_nulls().unique()
    print(f"Aeroporti validi (IATA): {len(valid_iata)}")

    initial_count = len(df_sched)
    
    if all(col in df_sched.columns for col in ['year', 'month', 'day']):
        df_sched = df_sched.with_columns(
            pl.date(pl.col('year'), pl.col('month'), pl.col('day')).alias('date_temp')
        )
        daily_counts_init = df_sched.group_by('date_temp').len()
        daily_avg_initial = daily_counts_init['len'].mean()
    else:
        daily_avg_initial = 0
        print("[WARN] Impossibile calcolare media giornaliera (colonne data mancanti)")

    print("Filtraggio voli (origine E destinazione devono essere nel dataset aeroporti)...")
    
    df_clean = df_sched.filter(
        pl.col('oapt').is_in(valid_iata) & 
        pl.col('dapt').is_in(valid_iata)
    )

    print(f"Rimozione colonne inutili: {COLS_TO_DROP}")
    cols_present = [c for c in COLS_TO_DROP if c in df_clean.columns]
    df_clean = df_clean.drop(cols_present)

    final_count = len(df_clean)
    if final_count > 0:
        daily_counts_final = df_clean.group_by('date_temp').len()
        daily_avg_final = daily_counts_final['len'].mean()
    else:
        daily_avg_final = 0

    if 'date_temp' in df_clean.columns:
        df_clean = df_clean.drop('date_temp')

    print(f"Salvataggio in corso su: {OUTPUT_FILE}")
    df_clean.write_csv(OUTPUT_FILE)
    print(f"File salvato: {OUTPUT_FILE}")

    print("\n--- RIEPILOGO ---")
    print(f"Voli iniziali: {initial_count}")
    print(f"Media giornaliera iniziale: {daily_avg_initial:.2f}")
    print(f"Voli finali (filtrati): {final_count}")
    print(f"Media giornaliera finale: {daily_avg_final:.2f}")
    print(f"Voli rimossi: {initial_count - final_count}")

if __name__ == "__main__":
    main()
