import requests
import json
import time
import os
import re
from bs4 import BeautifulSoup

# --- CONFIGURATION ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_FILE = os.path.join(DATA_DIR, "requirements.json")
os.makedirs(DATA_DIR, exist_ok=True)

GAMESPOT_URL = "https://www.gamespot.com/articles/2026-upcoming-games-release-schedule/1100-6534941/"
STEAM_SPY_URL = "https://steamspy.com/api.php?request=top100in2weeks"
STEAM_STORE_URL = "https://store.steampowered.com/api/appdetails"
STEAM_SEARCH_URL = "https://store.steampowered.com/search/results/"

# Manual override for games Steam Search might miss
PRIORITY_MAP = {
    "Arknights: Endfield": "2783580",
    "Resident Evil Requiem": "3000000", # Placeholder if page is hidden
    "Crimson Desert": "1443440"
}

def clean_html(html_text):
    if not html_text or html_text == "N/A": return "N/A"
    soup = BeautifulSoup(html_text, "html.parser")
    for br in soup.find_all("br"): br.replace_with("\n")
    return soup.get_text(separator=" ").strip()

def extract_gpu(html_text):
    if not html_text or html_text == "N/A": return "N/A"
    match = re.search(r'(?:Graphics|Video Card):\s*(.*?)(?:<br>|<li>|</li>|\n|$)', html_text, re.IGNORECASE)
    if match:
        gpu_info = match.group(1).strip()
        return BeautifulSoup(gpu_info, "html.parser").get_text().strip()
    return "N/A"

def fetch_gamespot_upcoming():
    """Scrapes GameSpot for Jan, Feb, and March 2026."""
    print("🌐 Scraping GameSpot releases...")
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(GAMESPOT_URL, headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')
        article_body = soup.find('div', class_='content-entity-body')
        
        upcoming_games = []
        capture = False
        for element in article_body.find_all(['h3', 'p']):
            text = element.get_text().strip()
            # EXTENDED WINDOW: Catch January through March
            if "January" in text: capture = True
            if "April" in text: capture = False 
            
            if capture and "(" in text and " - " in text:
                game_name = text.split("(")[0].strip()
                upcoming_games.append({"name": game_name})
        return upcoming_games
    except: return []

def fetch_game_details(app_id, name_override=None):
    """Fetches specs while forcing English."""
    params = {"appids": app_id, "l": "english", "cc": "US"}
    try:
        res = requests.get(STEAM_STORE_URL, params=params)
        data = res.json()
        if data and str(app_id) in data and data[str(app_id)]['success']:
            g_data = data[str(app_id)]['data']
            pc = g_data.get('pc_requirements', {})
            rec = pc.get('recommended', '') or pc.get('minimum', '')
            return {
                "id": str(app_id),
                "name": g_data.get('name', name_override),
                "gpu_recommendation": extract_gpu(rec),
                "min_specs_text": clean_html(pc.get('minimum', '')),
                "rec_specs_text": clean_html(rec)
            }
    except: return None

def get_top_games(limit=20):
    upcoming_list = fetch_gamespot_upcoming()
    results = []
    
    # 1. Process Upcoming First
    for game in upcoming_list:
        if len(results) >= limit: break
        
        # Check priority map first, then search Steam
        app_id = PRIORITY_MAP.get(game['name'])
        if not app_id:
            search_res = requests.get(STEAM_SEARCH_URL, params={"term": game['name'], "cc": "US"})
            soup = BeautifulSoup(search_res.content, 'html.parser')
            row = soup.find('a', class_='search_result_row')
            if row: app_id = row['data-ds-appid']
        
        if app_id:
            details = fetch_game_details(app_id, game['name'])
            if details: results.append(details)
        time.sleep(1.0)

    # 2. Fill remaining with SteamSpy
    if len(results) < limit:
        spy_res = requests.get(STEAM_SPY_URL)
        spy_ids = list(spy_res.json().keys())
        for sid in spy_ids:
            if len(results) >= limit: break
            details = fetch_game_details(sid)
            if details: results.append(details)
            time.sleep(1.0)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4, ensure_ascii=False)
    return results

if __name__ == "__main__":
    get_top_games(limit=20)
