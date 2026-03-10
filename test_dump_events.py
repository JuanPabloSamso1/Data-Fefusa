import re
import sys
sys.path.insert(0, r"d:\Data Science")
from src.scraper import ScorefyScraper
import requests

def main():
    url = "https://scorefy.app/cast/scoreboard/cmlmgwve1001ap4zcxnxf3ct9"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "text/html"
    }
    r = requests.get(url, headers=headers)
    
    # 1. Search for tournament id in URL first
    # URL format: maybe it's not even in the URL we hit? We hit /cast/scoreboard/... 
    # Ah, the user navigated from https://scorefy.app/futsal/mendoza/fefusa-mendoza/FFM-P-M-FSP-A-2026/results
    # The scoreboard page URL itself doesn't have FFM-P-M-FSP-A-2026!
    # Let's search inside the HTML for the tournament ID.
    matches = re.findall(r'(.{0,30}Primera FSP.{0,30})', r.text)
    for m in matches[:5]:
        print("Match Primera FSP:", m)
        
    matches2 = re.findall(r'(.{0,30}FFM-P-M-FSP-A-2026.{0,30})', r.text)
    for m in matches2[:5]:
        print("Match ID:", m)
        
    # Search for season text
    matches3 = re.findall(r'(.{0,30}Apertura.{0,30})', r.text)
    for m in matches3[:5]:
        print("Match Apertura:", m)

if __name__ == "__main__":
    main()
