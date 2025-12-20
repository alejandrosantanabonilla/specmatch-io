import requests
import json
import time
from bs4 import BeautifulSoup
import os

# --- CONFIGURATION ---
# Define where to save the data. 
# We use os.path.join to work on both Windows and Mac/Linux.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_FILE = os.path.join(DATA_DIR, "requirements.json")

# Ensure the data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

# APIs
STEAM_SPY_URL = "https://steamspy.com/api.php?request=top100in2weeks"
STEAM_STORE_URL = "https://store.steampowered.com/api/appdetails"

def get_top_games():
    """Fetches the top 100 AppIDs from SteamSpy."""
    print("Fetching top 100 games list from SteamSpy...")
    try:
        # User-Agent is sometimes required to avoid 403 errors
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(STEAM_SPY_URL, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            # SteamSpy returns a dict where keys are AppIDs
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
    
    # Replace <br> with newlines for better readability
    for br in soup.find_all("br"):
        br.replace_with("\n")
        
    # Get text and strip extra whitespace
    text = soup.get_text(separator=" ").strip()
    return text

def fetch_game_details(app_id):
    """Fetches requirements for a single AppID from Steam Store."""
    params = {"appids": app_id}
    try:
        response = requests.get(STEAM_STORE_URL, params=params)
        data = response.json()
        
        # Check if query was successful
        if data and str(app_id) in data and data[str(app_id)]['success']:
            game_data = data[str(app_id)]['data']
            
            # Extract basic info
            name = game_data.get('name', 'Unknown')
            
            # Extract PC Requirements (They come as HTML strings or lists)
            pc_reqs = game_data.get('pc_requirements', {})
            
            # Sometimes pc_requirements is an empty list [] instead of a dict {}
            if isinstance(pc_reqs, list):
                return None

            min_html = pc_reqs.get('minimum', '')
            rec_html = pc_reqs.get('recommended', '')
            
            # If there are no recommended specs, fall back to minimum
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

def main():
    game_ids = get_top_games()
    
    if not game_ids:
        print("No games found. Exiting.")
        return

    # Limit to first 20 for testing (Remove [:20] to get all 100)
    target_ids = game_ids[:20] 
    
    results = []
    
    print(f"Starting scrape for {len(target_ids)} games...")
    print("Note: Adding delay to prevent Steam API ban...")
    
    for i, app_id in enumerate(target_ids):
        print(f"[{i+1}/{len(target_ids)}] Fetching: {app_id}")
        
        details = fetch_game_details(app_id)
        if details:
            # Simple filter: Only save games that actually listed requirements
            if details['rec_specs_text'] != "N/A":
                results.append(details)
            else:
                print(f"Skipping {app_id} (No specs found)")
        
        # IMPORTANT: Rate Limiting
        # Steam is strict. 1.5s delay is safe.
        time.sleep(1.5)

    # Save to JSON
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4)
    
    print(f"\nSuccess! Saved {len(results)} games to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
