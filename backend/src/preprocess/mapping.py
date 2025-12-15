
import pandas as pd
import os
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "data")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")
RAW_DIR = os.path.join(DATA_DIR, "raw")

SCHEDULE_FILE = os.path.join(PROCESSED_DIR, "schedule", "Schedule_23-24.csv")
FLIGHT_LIST_FILE = os.path.join(PROCESSED_DIR, "flights_filtered", "flight_list_filtered_2024.csv")
AIRPORTS_FILE = os.path.join(RAW_DIR, "airports", "airports.csv")
OUTPUT_FILE = os.path.join(PROCESSED_DIR, "merged", "schedule_flight_list_merged.csv")

def load_data():
    """Carica i dataset necessari con colonne selezionate per efficienza."""
    print("Caricamento dati in corso...")

    schedule_cols = ['year', 'month', 'day', 'oapt', 'dapt', 'flt_id']
    schedule = pd.read_csv(SCHEDULE_FILE, usecols=schedule_cols, low_memory=False)

    flight_list_cols = ['dof', 'adep', 'ades', 'flt_id']
    flight_list = pd.read_csv(FLIGHT_LIST_FILE, usecols=flight_list_cols, low_memory=False)

    airports_cols = ['iata_code', 'icao_code']
    airports = pd.read_csv(AIRPORTS_FILE, usecols=airports_cols, low_memory=False)
    
    print(f"Dati caricati: Schedule ({len(schedule)} righe), Flight List ({len(flight_list)} righe), Airports ({len(airports)} righe).")
    return schedule, flight_list, airports

def create_airport_mapping(airports_df):
    """Crea un dizionario per mappare IATA -> ICAO."""
    valid_airports = airports_df.dropna(subset=['iata_code', 'icao_code'])
    iata_to_icao = pd.Series(valid_airports.icao_code.values, index=valid_airports.iata_code).to_dict()
    return iata_to_icao

def extract_flight_number(flt_id):
    """Estrae la parte numerica dal flight ID (callsign) della flight list."""
    if pd.isna(flt_id):
        return None

    match = re.search(r'\d+', str(flt_id))
    if match:
        return match.group(0)
    return None

def preprocess_schedule(schedule, iata_to_icao):
    """Prepara il dataframe Schedule per il merge."""
    print("Preprocessing Schedule...")

    schedule['date'] = pd.to_datetime(schedule[['year', 'month', 'day']])
    
    schedule['adep'] = schedule['oapt'].map(iata_to_icao)
    schedule['ades'] = schedule['dapt'].map(iata_to_icao)

    schedule['flight_number'] = schedule['flt_id'].astype(str).str.strip()
    
    return schedule

def preprocess_flight_list(flight_list):
    """Prepara il dataframe Flight List per il merge."""
    print("Preprocessing Flight List...")
    
    flight_list['date'] = pd.to_datetime(flight_list['dof']).dt.normalize()

    flight_list['flight_number'] = flight_list['flt_id'].apply(extract_flight_number)
    
    return flight_list

def main():
    schedule, flight_list, airports = load_data()
    iata_to_icao = create_airport_mapping(airports)
    print(f"Creato mapping per {len(iata_to_icao)} aeroporti.")
    schedule_processed = preprocess_schedule(schedule, iata_to_icao)
    flight_list_processed = preprocess_flight_list(flight_list)
    print("Esecuzione del merge...")
    
    merged = pd.merge(
        schedule_processed,
        flight_list_processed,
        how='inner',
        on=['date', 'adep', 'ades', 'flight_number'],
        suffixes=('_sched', '_real')
    )
    
    print(f"Merge completato. Righe risultanti: {len(merged)}")
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    merged.to_csv(OUTPUT_FILE, index=False)
    print(f"File salvato in: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
