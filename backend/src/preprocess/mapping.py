import pandas as pd
import os
import re
import glob
from timezonefinder import TimezoneFinder
import pytz

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "data")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")
RAW_DIR = os.path.join(DATA_DIR, "raw")

SCHEDULE_FILE = os.path.join(PROCESSED_DIR, "schedule", "Schedule_23-24.csv")
FLIGHT_LIST_FILE = os.path.join(PROCESSED_DIR, "flights_filtered", "flight_list_filtered_2023_2024.csv")
EVENTS_DIR = os.path.join(RAW_DIR, "flight_events")
AIRPORTS_FILE = os.path.join(RAW_DIR, "airports", "airports.csv")
OUTPUT_FILE = os.path.join(PROCESSED_DIR, "merged", "schedule_flight_list_localized.csv")

def load_data():
    print("Caricamento dati base...")
    schedule_cols = ['year', 'month', 'day', 'oapt', 'dapt', 'flt_id', 'dep_sched_time', 'arr_sched_time']
    schedule = pd.read_csv(SCHEDULE_FILE, usecols=schedule_cols, low_memory=False)

    flight_list_cols = ['dof', 'adep', 'ades', 'flt_id', 'id']
    flight_list = pd.read_csv(FLIGHT_LIST_FILE, usecols=flight_list_cols, low_memory=False)

    actual_lat_name = 'latitude_deg'
    actual_lon_name = 'longitude_deg'
    
    airports_cols = ['iata_code', 'icao_code', actual_lat_name, actual_lon_name]
    
    airports = pd.read_csv(AIRPORTS_FILE, usecols=airports_cols, low_memory=False)
    
    airports.rename(columns={
        actual_lat_name: 'latitude',
        actual_lon_name: 'longitude'
    }, inplace=True)
    
    return schedule, flight_list, airports

def load_flight_events():
    print("Caricamento Flight Events...")
    event_files = glob.glob(os.path.join(EVENTS_DIR, "*.parquet"))
    if not event_files: return pd.DataFrame()
    events_list = [pd.read_parquet(f) for f in event_files]
    return pd.concat(events_list, ignore_index=True)

def create_airport_mapping(airports_df):
    """Crea due mappe: IATA->ICAO e ICAO->TimezoneString"""
    print("Mappatura Fusi Orari Aeroporti in corso (richiede qualche secondo)...")
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
    schedule['flight_number'] = schedule['flt_id'].astype(str).str.strip()
    return schedule

def preprocess_flight_list(flight_list):
    print("Preprocessing Flight List...")
    flight_list['date'] = pd.to_datetime(flight_list['dof']).dt.normalize()
    flight_list['flight_number'] = flight_list['flt_id'].apply(extract_flight_number)
    return flight_list

def convert_utc_to_local(row, icao_to_tz):
    """Funzione che converte un timestamp UTC nel locale dell'aeroporto specifico"""
    utc_time = row['actual_time_utc']
    airport_code = row['airport_ref']
    
    if pd.isna(utc_time) or pd.isna(airport_code):
        return None
    
    tz_name = icao_to_tz.get(airport_code)
    if not tz_name:
        return utc_time
    
    try:
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
    
    print("Merge Base...")
    merged_base = pd.merge(
        schedule_processed,
        flight_list_processed,
        how='inner',
        on=['date', 'adep', 'ades', 'flight_number'],
        suffixes=('_sched', '_real')
    )
    
    print("Separazione Partenze e Arrivi...")
    df_dep = merged_base.copy()
    df_dep['event_type'] = 'take-off'
    df_dep['scheduled_time'] = df_dep['dep_sched_time']
    df_dep['airport_ref'] = df_dep['adep']
    df_dep = df_dep.drop(columns=['arr_sched_time', 'dep_sched_time']) 

    df_arr = merged_base.copy()
    df_arr['event_type'] = 'landing'
    df_arr['scheduled_time'] = df_arr['arr_sched_time']
    df_arr['airport_ref'] = df_arr['ades']
    df_arr = df_arr.drop(columns=['dep_sched_time', 'arr_sched_time'])

    merged_long = pd.concat([df_dep, df_arr], ignore_index=True)

    events = load_flight_events()
    
    if not events.empty:
        print("Unione eventi...")
        events = events[events['type'].isin(['take-off', 'landing'])]
        events.sort_values(by=['flight_id', 'type', 'event_time'], inplace=True)
        events_dedup = events.drop_duplicates(subset=['flight_id', 'type'], keep='first')

        final_df = pd.merge(
            merged_long,
            events_dedup[['flight_id', 'type', 'event_time']], 
            how='left',
            left_on=['id', 'event_type'],
            right_on=['flight_id', 'type']
        )
        
        final_df.rename(columns={'event_time': 'actual_time_utc'}, inplace=True)
        final_df.drop(columns=['flight_id_y', 'type'], inplace=True, errors='ignore')
        if 'flight_id_x' in final_df.columns:
             final_df.rename(columns={'flight_id_x': 'flt_id_real'}, inplace=True)
    else:
        final_df = merged_long
        final_df['actual_time_utc'] = None

    final_df.dropna(subset=['actual_time_utc'], inplace=True)
    
    final_df['actual_time_utc'] = pd.to_datetime(final_df['actual_time_utc'])

    print("Conversione da UTC a Local Time (geo-referenziata)...")
    
    final_df['actual_time_local'] = final_df.apply(
        lambda row: convert_utc_to_local(row, icao_to_tz), axis=1
    )
    
    print("Conversione completata.")

    final_df['dt_sched'] = pd.to_datetime(final_df['date'].astype(str) + ' ' + final_df['scheduled_time'])
    final_df['dt_actual'] = pd.to_datetime(final_df['actual_time_local'])
    
    final_df['dt_actual'] = final_df['dt_actual'].dt.tz_localize(None)

    final_df['delay_minutes'] = (final_df['dt_actual'] - final_df['dt_sched']).dt.total_seconds() / 60
    
    rows_before = len(final_df)
    final_df = final_df[
        (final_df['delay_minutes'] > -60) & 
        (final_df['delay_minutes'] < 1440)
    ]
    print(f"Rimossi {rows_before - len(final_df)} record anomali dopo conversione locale.")

    cols_to_drop = [
        'seats', 'ac_code', 'freq', 'id', 'dof', 'registration', 
        'model', 'typecode', 'version', 'source', 
        'dt_sched', 'dt_actual', 'airport_ref'
    ]
    existing_cols = [c for c in cols_to_drop if c in final_df.columns]
    final_df.drop(columns=existing_cols, inplace=True)

    final_df.sort_values(by=['date', 'flt_id_sched', 'event_type'], inplace=True)

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    final_df.to_csv(OUTPUT_FILE, index=False)
    print(f"File salvato: {OUTPUT_FILE}")
    print(final_df[['flt_id_sched', 'event_type', 'scheduled_time', 'actual_time_local', 'delay_minutes']].head())

if __name__ == "__main__":
    main()