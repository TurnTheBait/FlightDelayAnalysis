import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import os
import random
from dateutil import parser

current_script_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(current_script_dir)
backend_dir = os.path.dirname(src_dir)

AIRPORTS_CSV_PATH = os.path.join(backend_dir, 'data', 'processed', 'airports', 'airports_filtered.csv')
OUTPUT_PATH = os.path.join(backend_dir, 'data', 'raw', 'skytrax', 'skytrax_raw.csv')

ACCEPTED_YEARS = list(range(2015, 2027))
MIN_YEAR = min(ACCEPTED_YEARS)

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Cache-Control': 'max-age=0'
}

SKYTRAX_SLUGS = {
    "BIKF": "keflavik-airport",
    "EDDB": "berlin-brandenburg-airport",
    "EDDF": "frankfurt-main-airport",
    "EDDH": "hamburg-airport",
    "EDDK": "colognebonn-airport",
    "EDDL": "dusseldorf-airport",
    "EDDM": "munich-airport",
    "EDDN": "nuremburg-airport",
    "EDDP": "leipzighalle-airport",
    "EDDS": "stuttgart-airport",
    "EDDV": "hannover-airport",
    "EETN": "tallin-airport",
    "EFHK": "helsinki-vantaa-airport",
    "EGAA": "belfast-airport",
    "EGBB": "birmingham-airport",
    "EGCC": "manchester-airport",
    "EGKK": "london-gatwick-airport",
    "EGLL": "london-heathrow-airport",
    "EGGW": "luton-airport",
    "EGPF": "glasgow-airport",
    "EGPH": "edinburgh-airport",
    "EGSS": "london-stansted-airport",
    "EHAM": "amsterdam-schiphol-airport",
    "EHEH": "eindhoven-airport",
    "EIDW": "dublin-airport",
    "EINN": "shannon-airport",
    "EKBI": "billund-airport",
    "EKCH": "copenhagen-airport",
    "ELLX": "luxembourg-airport",
    "ENBR": "bergen-airport",
    "ENGM": "oslo-airport",
    "ENTC": "tromso-airport",
    "ENVA": "trondheim-airport",
    "ENZV": "stavanger-airport",
    "EPGD": "gdansk-airport",
    "EPKK": "krakow-airport",
    "EPWA": "warsaw-chopin-airport",
    "ESGG": "gothenburg-landvetter-airport",
    "ESSA": "stockholm-arlanda-airport",
    "EVLA": "", 
    "EVRA": "riga-airport",
    "EYVI": "vilnius-airport",
    "LATI": "tirana-airport",
    "LBBG": "burgas-airport",
    "LBSF": "sofia-airport",
    "LBWN": "varna-airport",
    "LDZA": "zagreb-airport",
    "LEAL": "alicante-airport",
    "LEBL": "barcelona-airport",
    "LEIB": "ibiza-airport",
    "LEMD": "madrid-barajas-airport",
    "LEMG": "malaga-airport",
    "LEPA": "palma-airport",
    "LEST": "santiago-de-compostela",
    "LEVC": "valencia-airport",
    "LFBD": "bordeaux-airport",
    "LFBO": "toulouse-airport",
    "LFLL": "lyon-saint-exupery-airport",
    "LFML": "marseille-airport",
    "LFMN": "nice-cote-dazur-airport",
    "LFPG": "paris-cdg-airport",
    "LFPO": "paris-orly-airport",
    "LFSB": "basel-mulhouse-airport",
    "LGAV": "athens-airport",
    "LGIR": "heraklion-airport",
    "LGTS": "thessaloniki-airport",
    "LHBP": "budapest-ferihegy-airport",
    "LIBD": "bari-palese-airport",
    "LIBR": "brindisi-airport",
    "LICC": "catania-airport",
    "LICJ": "palermo-airport",
    "LIEE": "cagliari-airport",
    "LIMC": "milan-malpensa-airport",
    "LIME": "milan-bergamo-airport",
    "LIMF": "turin-airport",
    "LIMJ": "genova-airport",
    "LIPE": "bologna-marconi-airport",
    "LIPX": "verona-airport",
    "LIPZ": "venice-marco-polo-airport",
    "LIRF": "rome-fiumicino-airport",
    "LIRN": "naples-airport",
    "LIRP": "pisa-airport",
    "LIRQ": "florence-airport",
    "LJLJ": "ljubljana-airport",
    "LKPR": "prague-airport",
    "LMML": "malta-airport",
    "LOWW": "vienna-airport",
    "LPFR": "faro-airport",
    "LPMA": "funchal-airport",
    "LPPD": "ponta-delgada-airport",
    "LPPR": "porto-airport",
    "LPPT": "lisbon-airport",
    "LQSA": "sarajevo-airport",
    "LROP": "bucharest-otopeni-airport",
    "LSGG": "geneva-airport",
    "LSZH": "zurich-airport",
    "LTFM": "istanbul-airport",
    "LWSK": "skopje-airport",
    "LXGB": "gibraltar-airport",
    "LYBE": "belgrade-airport",
    "LYPG": "podgorica-airport",
    "LZIB": "bratislava-airport"
}

if not os.path.exists(AIRPORTS_CSV_PATH):
    print(f"Error: Airports file not found at {AIRPORTS_CSV_PATH}")
    exit()

try:
    df_airports = pd.read_csv(AIRPORTS_CSV_PATH)
except Exception as e:
    print(f"Error reading CSV: {e}")
    exit()

def get_year_from_date(date_str):
    try:
        dt = parser.parse(date_str)
        return dt.year
    except:
        return None

all_reviews = []

print(f"\nStarting scraping for {len(df_airports)} target airports using PAGINATION...")

for index, row in df_airports.iterrows():
    full_name = str(row['name'])
    code = row['ident']
    city = str(row['municipality']) if 'municipality' in row and pd.notna(row['municipality']) else ""
    
    slug = SKYTRAX_SLUGS.get(code)
    if not slug:
        continue

    base_url = f"https://www.airlinequality.com/airport-reviews/{slug}/"
    print(f"[{index+1}/{len(df_airports)}] {code}: Scrape target -> {base_url}")
    
    page_num = 1
    reviews_count_airport = 0
    keep_scraping = True
    
    while keep_scraping:
        page_url = f"{base_url}page/{page_num}/?sortby=post_date%3ADesc&pagesize=100"
        
        try:
            response = requests.get(page_url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'lxml')
                articles = soup.find_all("article", itemprop="review")
                
                if not articles:
                    articles = soup.find_all("article", class_="comp_media-review-rated")
                
                if not articles:
                    keep_scraping = False
                    break
                
                reviews_on_page = 0
                for article in articles:
                    try:
                        date_element = article.find("time", itemprop="datePublished")
                        date_text = date_element["datetime"] if date_element else ""
                        
                        review_year = get_year_from_date(date_text)
                        
                        if review_year and review_year < MIN_YEAR:
                            keep_scraping = False
                            break
                        
                        if review_year not in ACCEPTED_YEARS:
                            continue

                        title_element = article.find("h2", class_="text_header")
                        review_title = title_element.get_text(strip=True) if title_element else ""
                        
                        content_element = article.find("div", class_="text_content")
                        if content_element:
                            review_text = content_element.get_text(strip=True)
                            for trash in ["✅ Trip Verified |", "Not Verified |", "cTrip Verified |", "Trip Verified |"]:
                                review_text = review_text.replace(trash, "")
                            review_text = review_text.strip()
                        else:
                            review_text = ""
                        
                        rating = "N/A"
                        rating_element = article.find("span", itemprop="ratingValue")
                        if rating_element:
                            rating = rating_element.get_text(strip=True)
                        
                        all_reviews.append({
                            "airport_code": code,
                            "search_term": city,
                            "source": "Skytrax",
                            "title": review_title,
                            "text": f"{review_title}. {review_text}",
                            "rating": rating,
                            "date": date_text
                        })
                        reviews_count_airport += 1
                        reviews_on_page += 1
                    except:
                        continue
                
                print(f"   Page {page_num}: Found {reviews_on_page} relevant reviews.")
                page_num += 1
                time.sleep(random.uniform(0.5, 1.0))
                
            else:
                keep_scraping = False
        
        except Exception as e:
            print(f"   Error on page {page_num}: {e}")
            keep_scraping = False
            
    print(f"   Total extracted for {code}: {reviews_count_airport}")

df_reviews = pd.DataFrame(all_reviews)
os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
df_reviews.to_csv(OUTPUT_PATH, index=False)

print(f"\nDone. Collected {len(df_reviews)} total reviews.")
print(f"File saved to: {OUTPUT_PATH}")