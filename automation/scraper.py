import requests
import json
import time
from bs4 import BeautifulSoup
import os

# --- CONFIGURATION ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_FILE = os.path.join(DATA_DIR, "requirements.json")

# Ensure the data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

# APIs
STEAM_SPY_URL = "https://steamspy.com/api.php?request=top100in2weeks"
STEAM_STORE_URL = "https://store.steampowered.com/api/appdetails"

def fetch_steamspy_ids():
    """Internal helper: Fetches the top 100 AppIDs from SteamSpy."""
    print("Fetching top 100 games list from SteamSpy...")
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(STEAM_SPY_URL, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            game_ids = list(data.keys())
            print(f"Found {len(game_ids)} games.")
            return game_ids
        else:
            print(f"Error fetching Top Games: {response.status_code}")
            return []
    except Exception as e:
        print(f"Connection Error (SteamSpy): {e}")
        return []

def clean_html(html_text):
    """Removes HTML tags and cleans up whitespace."""
    if not html_text:
        return "N/A"
    soup = BeautifulSoup(html_text, "html.parser")
    for br in soup.find_all("br"):
        br.replace_with("\n")
    text = soup.get_text(separator=" ").strip()
    return text

def fetch_game_details(app_id):
    """Fetches requirements for a single AppID from Steam Store."""
    params = {"appids": app_id}
    try:
        response = requests.get(STEAM_STORE_URL, params=params)
        data = response.json()
        
        if data and str(app_id) in data and data[str(app_id)]['success']:
            game_data = data[str(app_id)]['data']
            
            name = game_data.get('name', 'Unknown')
            pc_reqs = game_data.get('pc_requirements', {})
            
            if isinstance(pc_reqs, list):
                return None

            min_html = pc_reqs.get('minimum', '')
            rec_html = pc_reqs.get('recommended', '')
            
            if not rec_html:
                rec_html = min_html

            return {
                "id": app_id,
                "name": name,
                "category": "Game",
                "min_specs_text": clean_html(min_html),
                "rec_specs_text": clean_html(rec_html)
            }
        else:
            return None
    except Exception as e:
        print(f"Error fetching AppID {app_id}: {e}")
        return None

def get_top_games(limit=20):
    """
    MAIN FUNCTION called by generator.py.
    Fetches IDs, details, and returns a list of game dictionaries.
    """
    game_ids = fetch_steamspy_ids()
    
    if not game_ids:
        print("No games found.")
        return []

    # Apply limit
    target_ids = game_ids[:limit]
    results = []
    
    print(f"Starting scrape for {len(target_ids)} games...")
    
    for i, app_id in enumerate(target_ids):
        # Optional: Print progress
        print(f"   [{i+1}/{len(target_ids)}] Scraper fetching: {app_id}...", end="\r")
        
        details = fetch_game_details(app_id)
        if details:
            if details['rec_specs_text'] != "N/A":
                results.append(details)
        
        # Rate Limiting
        time.sleep(1.0)

    print("") # New line after loop

    # Save to JSON (as a backup/cache)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4)
    
    print(f"✅ Scraper finished. Found {len(results)} valid games.")
    
    # RETURN the list so generator.py can use it
    return results

# This allows you to run the scraper alone for testing
if __name__ == "__main__":
    get_top_games(limit=20)
