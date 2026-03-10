import json
import os
import sys

# Agregamos la ruta
sys.path.insert(0, r"d:\Data Science")
from src.scraper import ScorefyScraper

def main():
    url = "https://scorefy.app/cast/scoreboard/cmlmgwve1001ap4zcxnxf3ct9"
    scraper = ScorefyScraper()
    match = scraper.get_match_data(url)
    
    print("Match keys:", list(match.keys()))
    # Also look at 'team' or similar keys if they exist
    for k in match.keys():
        if 'team' in k.lower() or 'equipo' in k.lower():
            print(f"Content of {k}:", type(match[k]))

if __name__ == "__main__":
    main()
