
import pandas as pd
import os

def get_icao_to_iata_mapping(airports_file):
    if not os.path.exists(airports_file):
        raise FileNotFoundError(f"Airports file not found: {airports_file}")
    
    df = pd.read_csv(airports_file, usecols=['icao_code', 'iata_code'], keep_default_na=False)
    
    df = df[df['icao_code'] != '']
    
    mapping = {}
    for _, row in df.iterrows():
        icao = row['icao_code']
        iata = row['iata_code']
        if iata:
            mapping[icao] = iata
        else:
            mapping[icao] = icao
            
    return mapping
