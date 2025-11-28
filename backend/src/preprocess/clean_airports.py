import pandas as pd
from pathlib import Path

RAW_AIRPORTS = Path("backend/data/raw/airports/airports.csv")
OUTPUT_DIR = Path("backend/data/processed/airports")
OUTPUT_FILE = OUTPUT_DIR / "airports_filtered.csv"

COLUMNS_TO_DROP = ["scheduled_service", "home_link", "wikipedia_link", "keywords", "local_code"]

TARGET_AIRPORTS = {
    "BIKF", "EDDB", "EDDF", "EDDH", "EDDK", "EDDL", "EDDM", "EDDN", "EDDP", "EDDS", 
    "EDDV", "EETN", "EFHK", "EGAA", "EGBB", "EGCC", "EGGW", "EGKK", "EGLL", "EGPF", 
    "EGPH", "EGSS", "EHAM", "EHEH", "EIDW", "EINN", "EKBI", "EKCH", "ELLX", "ENBR", 
    "ENGM", "ENTC", "ENVA", "ENZV", "EPGD", "EPKK", "EPWA", "ESGG", "ESSA", "EVLA", 
    "EVRA", "EYVI", "LATI", "LBBG", "LBSF", "LBWN", "LDZA", "LEAL", "LEBL", "LEIB", 
    "LEMD", "LEMG", "LEPA", "LEST", "LEVC", "LFBD", "LFBO", "LFLL", "LFML", "LFMN", 
    "LFPG", "LFPO", "LFSB", "LGAV", "LGIR", "LGTS", "LHBP", "LIBD", "LIBR", "LICC", 
    "LICJ", "LIEE", "LIMC", "LIME", "LIMF", "LIMJ", "LIPE", "LIPX", "LIPZ", "LIRF", 
    "LIRN", "LIRP", "LIRQ", "LJLJ", "LKPR", "LMML", "LOWW", "LPFR", "LPMA", "LPPD", 
    "LPPR", "LPPT", "LQSA", "LROP", "LSGG", "LSZH", "LTFM", "LWSK", "LXGB", "LYBE", 
    "LYPG", "LZIB"
}

def clean_airports():
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Lettura del file raw: {RAW_AIRPORTS}...")
    
    if not RAW_AIRPORTS.exists():
        raise FileNotFoundError(f"Il file {RAW_AIRPORTS} non esiste. Controlla il percorso.")

    df = pd.read_csv(RAW_AIRPORTS)
    initial_count = len(df)
    print(f"Totale aeroporti nel file originale: {initial_count}")


    df_filtered = df[df["ident"].isin(TARGET_AIRPORTS)].copy()
    
    found_airports = set(df_filtered["ident"].unique())
    missing = TARGET_AIRPORTS - found_airports
    if missing:
        print(f"⚠️ Attenzione: {len(missing)} aeroporti della lista non sono stati trovati nel file CSV: {missing}")

    print(f"Aeroporti selezionati: {len(df_filtered)}")

    df_filtered = df_filtered.drop(columns=COLUMNS_TO_DROP, errors='ignore')

    df_filtered.to_csv(OUTPUT_FILE, index=False)
    print(f"File salvato correttamente in: {OUTPUT_FILE}")

if __name__ == "__main__":
    clean_airports()