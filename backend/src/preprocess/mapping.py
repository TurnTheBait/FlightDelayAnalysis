import pandas as pd
import os
import re
import glob
from timezonefinder import TimezoneFinder
import pytz
import numpy as np
import gc

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "data")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")
RAW_DIR = os.path.join(DATA_DIR, "raw")
MERGED_DIR = os.path.join(DATA_DIR, "merged")

SCHEDULE_FILE = os.path.join(PROCESSED_DIR, "schedule", "clean_schedule_23-24.csv")
FLIGHT_LIST_FILE = os.path.join(PROCESSED_DIR, "flights_filtered", "flight_list_filtered_2023_2024.csv")
EVENTS_FILE = os.path.join(PROCESSED_DIR, "flight_events_processed", "flight_events_full.csv")

AIRPORTS_FILE = os.path.join(PROCESSED_DIR, "airports", "airports_filtered.csv")
OUTPUT_FILE = os.path.join(MERGED_DIR, "schedule_flight_list_localized.csv")

def load_data():
    print("Caricamento dati base...")
    schedule_cols = ['year', 'month', 'day', 'oapt', 'dapt', 'flt_id', 'dep_sched_time', 'arr_sched_time']
    schedule = pd.read_csv(SCHEDULE_FILE, usecols=schedule_cols, low_memory=False)

    flight_list_cols = ['dof', 'adep', 'ades', 'flt_id', 'id', 'first_seen', 'last_seen']
    flight_list = pd.read_csv(FLIGHT_LIST_FILE, usecols=flight_list_cols, low_memory=False)

    actual_lat_name = 'latitude_deg'
    actual_lon_name = 'longitude_deg'
    
    airports_cols = ['iata_code', 'icao_code', actual_lat_name, actual_lon_name]
    
    try:
        airports = pd.read_csv(AIRPORTS_FILE, usecols=airports_cols, low_memory=False)
        airports.rename(columns={
            actual_lat_name: 'latitude',
            actual_lon_name: 'longitude'
        }, inplace=True)
    except ValueError:
        airports_cols = ['iata_code', 'icao_code', 'latitude', 'longitude']
        airports = pd.read_csv(AIRPORTS_FILE, usecols=airports_cols, low_memory=False)
    
    return schedule, flight_list, airports

def load_flight_events():
    print(f"Caricamento Flight Events da CSV Unico: {EVENTS_FILE}...")
    
    if not os.path.exists(EVENTS_FILE):
        print("⚠️ File eventi non trovato. Procedo senza arricchimento.")
        return pd.DataFrame()
    
    return pd.read_csv(EVENTS_FILE, low_memory=False)

def create_airport_mapping(airports_df):
    print("Mappatura Fusi Orari Aeroporti in corso...")
    valid = airports_df.dropna(subset=['iata_code', 'icao_code', 'latitude', 'longitude'])
    iata_to_icao = pd.Series(valid.icao_code.values, index=valid.iata_code).to_dict()
    tf = TimezoneFinder()
    icao_to_tz = {}
    for _, row in valid.iterrows():
        try:
            tz_str = tf.timezone_at(lng=row['longitude'], lat=row['latitude'])
            if tz_str:
                icao_to_tz[row['icao_code']] = tz_str
        except:
            continue
    print(f"Mappati {len(icao_to_tz)} fusi orari aeroportuali.")
    return iata_to_icao, icao_to_tz

def extract_flight_number(flt_id):
    if pd.isna(flt_id): return None
    match = re.search(r'\d+', str(flt_id))
    return match.group(0) if match else None

def preprocess_schedule(schedule, iata_to_icao):
    print("Preprocessing Schedule...")
    schedule['date'] = pd.to_datetime(schedule[['year', 'month', 'day']])
    schedule['adep'] = schedule['oapt'].map(iata_to_icao)
    schedule['ades'] = schedule['dapt'].map(iata_to_icao)
    schedule['flight_number_digits'] = schedule['flt_id'].apply(extract_flight_number)
    schedule['dt_sched_dep'] = pd.to_datetime(schedule['date'].astype(str) + ' ' + schedule['dep_sched_time'])
    return schedule

def preprocess_flight_list(flight_list):
    print("Preprocessing Flight List...")
    flight_list['date'] = pd.to_datetime(flight_list['dof']).dt.normalize()
    flight_list['flight_number_real_digits'] = flight_list['flt_id'].apply(extract_flight_number)
    flight_list['first_seen'] = pd.to_datetime(flight_list['first_seen'])
    flight_list['last_seen'] = pd.to_datetime(flight_list['last_seen'])
    return flight_list

def convert_utc_to_local(row, icao_to_tz):
    utc_time = row['actual_time_utc']
    airport_code = row['airport_ref']
    if pd.isna(utc_time) or pd.isna(airport_code):
        return None
    tz_name = icao_to_tz.get(airport_code)
    if not tz_name:
        return utc_time
    try:
        if isinstance(utc_time, str):
            utc_dt = pd.to_datetime(utc_time).replace(tzinfo=pytz.utc)
        else:
            utc_dt = utc_time.replace(tzinfo=pytz.utc)
            
        local_dt = utc_dt.astimezone(pytz.timezone(tz_name))
        return local_dt.strftime('%Y-%m-%d %H:%M:%S')
    except Exception as e:
        return utc_time

def main():
    schedule, flight_list, airports = load_data()
    iata_to_icao, icao_to_tz = create_airport_mapping(airports)
    
    schedule_processed = preprocess_schedule(schedule, iata_to_icao)
    flight_list_processed = preprocess_flight_list(flight_list)
    
    print("Avvio Join Euristica (Date + Route)...")
    
    merged_broad = pd.merge(
        schedule_processed,
        flight_list_processed,
        how='inner',
        on=['date', 'adep', 'ades'],
        suffixes=('_sched', '_real')
    )
    
    print(f"Candidati potenziali trovati: {len(merged_broad)}")
    
    print("Filtraggio finestra temporale (+/- 12h)...")
    merged_broad['time_diff_min'] = (merged_broad['first_seen'] - merged_broad['dt_sched_dep']).dt.total_seconds() / 60.0
    
    mask_window = merged_broad['time_diff_min'].abs() < 720
    valid_candidates = merged_broad[mask_window].copy()
    
    del merged_broad
    gc.collect()

    print("Calcolo Match Score...")
    valid_candidates['match_score'] = -valid_candidates['time_diff_min'].abs()
    
    mask_flt_match = (
        valid_candidates['flight_number_digits'].notna() & 
        valid_candidates['flight_number_real_digits'].notna() & 
        (valid_candidates['flight_number_digits'] == valid_candidates['flight_number_real_digits'])
    )
    
    valid_candidates.loc[mask_flt_match, 'match_score'] += 1000
    
    print("Selezione best match...")
    unique_keys_sched = ['date', 'oapt', 'dapt', 'flt_id_sched']
    
    best_matches = valid_candidates.sort_values(by=unique_keys_sched + ['match_score'], ascending=[True, True, True, True, False]) \
                                   .drop_duplicates(subset=unique_keys_sched, keep='first')
                                   
    print(f"Voli univoci mappati: {len(best_matches)}")
    merged_base = best_matches
    
    del valid_candidates
    gc.collect()

    print("Separazione Partenze e Arrivi...")
    
    df_dep = merged_base.copy()
    df_dep['event_type'] = 'take-off'
    df_dep['scheduled_time'] = df_dep['dep_sched_time']
    df_dep['airport_ref'] = df_dep['adep']
    df_dep['fallback_time_utc'] = df_dep['first_seen']
    
    keep_cols_dep = ['event_type', 'scheduled_time', 'airport_ref', 'fallback_time_utc', 'date', 'flt_id_sched', 'oapt', 'dapt', 'id']
    df_dep = df_dep[keep_cols_dep]

    df_arr = merged_base.copy()
    df_arr['event_type'] = 'landing'
    df_arr['scheduled_time'] = df_arr['arr_sched_time']
    df_arr['airport_ref'] = df_arr['ades']
    df_arr['fallback_time_utc'] = df_arr['last_seen']
    
    keep_cols_arr = ['event_type', 'scheduled_time', 'airport_ref', 'fallback_time_utc', 'date', 'flt_id_sched', 'oapt', 'dapt', 'id']
    df_arr = df_arr[keep_cols_arr]

    merged_long = pd.concat([df_dep, df_arr], ignore_index=True)
    
    del merged_base, df_dep, df_arr
    gc.collect()

    events = load_flight_events()
    
    if not events.empty:
        print("Arricchimento con eventi dal CSV...")
        events = events[events['type'].isin(['take-off', 'landing'])]
        events.sort_values(by=['flight_id', 'type', 'event_time'], inplace=True)
        events_dedup = events.drop_duplicates(subset=['flight_id', 'type'], keep='first')
        events_dedup = events_dedup[['flight_id', 'type', 'event_time']]

        final_df = pd.merge(
            merged_long,
            events_dedup, 
            how='left',
            left_on=['id', 'event_type'], 
            right_on=['flight_id', 'type']
        )
        final_df.rename(columns={'event_time': 'event_time_real'}, inplace=True)
        final_df.drop(columns=['flight_id', 'type'], inplace=True, errors='ignore')
    else:
        final_df = merged_long
        final_df['event_time_real'] = None

    print("Applicazione Logica Temporale (Evento preciso -> Fallback)...")
    final_df['actual_time_utc'] = final_df['event_time_real'].combine_first(final_df['fallback_time_utc'])
    
    final_df.dropna(subset=['actual_time_utc'], inplace=True)
    final_df['actual_time_utc'] = pd.to_datetime(final_df['actual_time_utc'])

    print("Conversione UTC -> Local Time...")
    final_df['actual_time_local'] = final_df.apply(
        lambda row: convert_utc_to_local(row, icao_to_tz), axis=1
    )
    
    print("Calcolo Ritardi...")
    final_df['dt_sched'] = pd.to_datetime(final_df['date'].astype(str) + ' ' + final_df['scheduled_time'])
    final_df['dt_actual'] = pd.to_datetime(final_df['actual_time_local'])
    final_df['dt_actual'] = final_df['dt_actual'].apply(lambda x: x.replace(tzinfo=None) if pd.notnull(x) else x)

    final_df['delay_minutes'] = (final_df['dt_actual'] - final_df['dt_sched']).dt.total_seconds() / 60
    
    rows_before = len(final_df)
    final_df = final_df[
        (final_df['delay_minutes'] > -60) & 
        (final_df['delay_minutes'] < 1440)
    ]
    print(f"Rimossi {rows_before - len(final_df)} outliers.")

    if 'flt_id_sched' in final_df.columns:
        final_df.rename(columns={'flt_id_sched': 'flt_id'}, inplace=True)
        
    final_cols = ['date', 'flt_id', 'event_type', 'oapt', 'dapt', 'scheduled_time', 'actual_time_local', 'delay_minutes']
    final_df = final_df[final_cols]

    final_df.sort_values(by=['date', 'flt_id', 'event_type'], inplace=True)

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    final_df.to_csv(OUTPUT_FILE, index=False)
    print(f"File salvato: {OUTPUT_FILE}")

    # Statistiche finali
    print("\n--- STATISTICHE MAPPING ---")
    print(f"Totale eventi mappati: {len(final_df)}")
    
    if 'delay_minutes' in final_df.columns:
        avg_delay = final_df.groupby('event_type')['delay_minutes'].mean()
        print("\n[Ritardo Medio (minuti)]")
        print(avg_delay)

        total_by_type = final_df.groupby('event_type').size()
        delayed = final_df[final_df['delay_minutes'] > 15].groupby('event_type').size()
        delayed = delayed.reindex(total_by_type.index, fill_value=0)
        pct_delayed = (delayed / total_by_type) * 100
        
        print("\n[Percentuale Ritardi > 15 min]")
        stats_df = pd.DataFrame({
            'Totale': total_by_type,
            'In Ritardo': delayed,
            '%': pct_delayed.round(2)
        })
        print(stats_df)

if __name__ == "__main__":
    main()