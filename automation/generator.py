import os
import time
import sys
import re
import random
from datetime import datetime
from google import genai
from google.api_core import exceptions # Needed for 429 error handling
from dotenv import load_dotenv

# --- CONFIGURATION ---
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key: 
    raise ValueError("❌ No API Key found in .env! Please check your configuration.")

client = genai.Client(api_key=api_key)
MODEL_NAME = "gemini-2.0-flash-lite" 
POSTS_DIR = "content/posts"

def get_existing_slugs():
    if not os.path.exists(POSTS_DIR):
        return []
    return [f.replace('.md', '') for f in os.listdir(POSTS_DIR) if f.endswith('.md')]

def generate_post_with_retry(game, max_retries=5):
    """Generates the article with exponential backoff for rate limits."""
    
    clean_name = re.sub(r'[^a-zA-Z0-9\s]', '', game['name'])
    slug = clean_name.lower().replace(" ", "-")
    filename = f"{POSTS_DIR}/{slug}.md"

    if slug in get_existing_slugs():
        print(f"✅ Skipping: '{game['name']}' (Already exists)")
        return

    # Data Preparation
    rec_specs = game.get('rec_specs_text', 'No official specs available yet.')
    gpu_recommendation = game.get('gpu_recommendation', 'N/A')
    if gpu_recommendation == "N/A":
        gpu_recommendation = "Hardware requirements pending. SpecMatch Prediction: RTX 3060 / RX 6600 or equivalent."

    full_prompt = f"""
    You are the Editor-in-Chief of SpecMatch.io. Writing style: Authoritative, FOMO-driven, short sentences.
    TASK: Write a Hugo Markdown article for "{game['name']}".
    Target GPU: {gpu_recommendation} | Specs: {rec_specs}
    ... [Rest of your punchy prompt remains the same] ...
    """

    # RETRY LOOP
    for attempt in range(max_retries):
        try:
            print(f"⚡ Attempt {attempt+1}: Generating {game['name']}...")
            response = client.models.generate_content(model=MODEL_NAME, contents=full_prompt)
            
            os.makedirs(POSTS_DIR, exist_ok=True)
            with open(filename, "w", encoding="utf-8") as f:
                f.write(response.text)
            print(f"✅ Created: {filename}")
            return # Success! Exit the function.

        except Exception as e:
            # Handle 429 Resource Exhausted
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                # Exponential backoff: 2^attempt + jitter
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                print(f"⚠️ Rate limit hit. Retrying in {wait_time:.1f}s...")
                time.sleep(wait_time)
            else:
                print(f"❌ Non-retryable error for {game['name']}: {e}")
                break

if __name__ == "__main__":
    try:
        import scraper
        games_list = scraper.get_top_games(limit=20)
        
        for game in games_list:
            generate_post_with_retry(game)
            # Baseline delay to stay near 4-5 RPM safely
            time.sleep(12) 

        print("\n🎉 Batch generation complete!")
    except Exception as e:
        print(f"❌ Automation Error: {e}")
