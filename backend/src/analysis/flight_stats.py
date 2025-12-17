import pandas as pd
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_FILE = os.path.join(BASE_DIR, "data", "processed", "merged", "schedule_flight_list_localized.csv")
SCHEDULE_FILE = os.path.join(BASE_DIR, "data", "processed", "schedule", "clean_schedule_23-24.csv")

def main():
    if os.path.exists(SCHEDULE_FILE):
        print(f"Caricamento dati schedulati da: {SCHEDULE_FILE}...")
        try:
            df_sched = pd.read_csv(SCHEDULE_FILE, usecols=['year', 'month', 'day'], low_memory=False)
            df_sched['date'] = pd.to_datetime(df_sched[['year', 'month', 'day']])
            
            total_sched = len(df_sched)
            sched_per_day = df_sched.groupby('date').size()
            avg_sched_daily = sched_per_day.mean()
            
            print("\n--- ANALISI VOLI SCHEDULATI ---")
            print(f"Totale voli schedulati: {total_sched}")
            print(f"Media voli schedulati al giorno: {avg_sched_daily:.2f}")
        except Exception as e:
            print(f"Errore analisi schedulati: {e}")
    else:
        print(f"[WARN] File schedulato non trovato: {SCHEDULE_FILE}")

    if not os.path.exists(DATA_FILE):
        print(f"ERRORE: File non trovato: {DATA_FILE}")
        return

    print(f"Caricamento dati da: {DATA_FILE}...")
    df = pd.read_csv(DATA_FILE)
    
    print(f"Totale righe: {len(df)}")
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
    
    if 'flt_id_sched' in df.columns:
        flights_per_day = df.groupby(df['date'].dt.date)['flt_id_sched'].nunique()
        print("\n--- NUMERO MEDIO DI VOLI AL GIORNO ---")
        print(f"{flights_per_day.mean():.2f}")
    else:
        print("\n[WARN] Colonna 'flt_id_sched' mancante, impossibile contare voli unici.")

    if 'delay_minutes' in df.columns and 'event_type' in df.columns:
        print("\n--- RITARDO MEDIO (minuti) ---")
        avg_delay = df.groupby('event_type')['delay_minutes'].mean()
        print(avg_delay)
        
        print("\n--- STATISTICHE RITARDO (minuti) ---")
        stats = df.groupby('event_type')['delay_minutes'].describe()
        pd.set_option('display.max_columns', None)
        print(stats)

        print("\n--- PERCENTUALE DI RITARDI SIGNIFICATIVI (> 15 min) ---")
        total_by_type = df.groupby('event_type').size()
        delayed_by_type = df[df['delay_minutes'] > 15].groupby('event_type').size()
        
        delayed_by_type = delayed_by_type.reindex(total_by_type.index, fill_value=0)
        
        pct_by_type = (delayed_by_type / total_by_type) * 100
        result_df = pd.DataFrame({
            'Totale Eventi': total_by_type,
            'Eventi Ritardo >15m': delayed_by_type,
            '% Ritardo': pct_by_type
        })
        print(result_df)

    else:
        print("\n[ERRORE] Colonne 'delay_minutes' o 'event_type' mancanti.")

if __name__ == "__main__":
    main()
