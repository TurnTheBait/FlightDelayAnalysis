
import pandas as pd
import os
import glob
import re

BASE_DIR = "../FlightDelayAnalysis/backend"
DATA_DIR = os.path.join(BASE_DIR, "data")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")
RAW_DIR = os.path.join(DATA_DIR, "raw")

SCHEDULE_FILE = os.path.join(PROCESSED_DIR, "schedule", "Schedule_23-24.csv")
FLIGHT_LIST_FILE = os.path.join(PROCESSED_DIR, "flights_filtered", "flight_list_filtered_2024.csv")
EVENTS_DIR = os.path.join(RAW_DIR, "flight_events")

def inspect():
    print("Loading Schedule...")
    if os.path.exists(SCHEDULE_FILE):
        schedule = pd.read_csv(SCHEDULE_FILE, nrows=5)
        print(f"Schedule columns: {list(schedule.columns)}")
    else:
        print("Schedule file not found.")

    print("Loading Flight List...")
    if os.path.exists(FLIGHT_LIST_FILE):
        flight_list = pd.read_csv(FLIGHT_LIST_FILE, nrows=5)
        print(f"Flight List columns: {list(flight_list.columns)}")
    else:
        print("Flight List file not found.")

    print("Loading Flight Events...")
    event_files = glob.glob(os.path.join(EVENTS_DIR, "*.parquet"))
    if event_files:
        events = pd.read_parquet(event_files[0])
        print(f"Flight Events columns: {list(events.columns)}")
        
        if os.path.exists(FLIGHT_LIST_FILE):
             flight_list = pd.read_csv(FLIGHT_LIST_FILE, nrows=100)
             common_ids = set(flight_list['id']).intersection(set(events['flight_id']))
             print(f"Number of intersecting IDs (sample): {len(common_ids)}")
             if len(common_ids) > 0:
                 print("Confirmed: Flight Events 'flight_id' matches Flight List 'id'.")
             else:
                 print("Warning: No intersection found between Flight List 'id' and Flight Events 'flight_id'. Checking 'flt_id'.")
                 common_flt_ids = set(flight_list['flt_id']).intersection(set(events['flight_id']))
                 print(f"Number of intersecting flt_ids: {len(common_flt_ids)}")

    else:
        print("No Flight Events files found.")

if __name__ == "__main__":
    inspect()
