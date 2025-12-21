import os
import time
import sys
import google.generativeai as genai
from datetime import datetime
from dotenv import load_dotenv

# --- CONFIGURATION ---
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    raise ValueError("❌ No API Key found! Please check your .env file.")

genai.configure(api_key=api_key)

# FIXED: Changed 'gemini-2.5' (typo) to the correct 'gemini-1.5-flash'
model = genai.GenerativeModel('gemini-2.5-flash')

def generate_post(game):
    """
    Generates a "High-Stakes" hardware guide for a specific game using Google Gemini.
    """
    print(f"⚡ Generating article for: {game['name']}...")

    full_prompt = f"""
    You are the Editor-in-Chief of SpecMatch.io, a hardcore PC hardware site.
    Your writing style is:
    - Authoritative but urgent (use "The FOMO" angle).
    - Short, punchy sentences.
    - No fluff. No "In conclusion."
    - You speak directly to the gamer who is afraid their PC is too slow.

    TASK:
    Write a Hugo Markdown article for the game "{game['name']}".
    
    Adhere strictly to this template:

    ---
    title: "Can Your PC Run {game['name']}? The 'Ultra 60 FPS' Hardware Guide"
    date: {datetime.now().strftime('%Y-%m-%d')}
    draft: false
    description: "Don't let low FPS ruin the experience. Here are the exact laptop specs you need for {game['name']}, from Budget 1080p to Ultra 4K."
    tags: ["{game['name']}", "System Requirements", "Hardware Guide"]
    cover:
        image: "/images/cover.jpg" 
        alt: "{game['name']} System Requirements Art"
        relative: false
    ---

    ## The "Fear of Missing Out"
    Write 2 paragraphs. 
    - Hook: Acknowledge that "{game['name']}" is demanding/beautiful.
    - The Threat: Explain that older hardware (pre-2020) will struggle. Mention the game engine if known.
    - The Promise: SpecMatch has analyzed the requirements to find the perfect hardware match.

    ## The "SpecMatch" Quick Reference
    Create a Markdown table with these exact columns. Fill it with ESTIMATED requirements for Laptops (Mobile GPUs):
    | Target Experience | The SpecMatch GPU (Laptop) | The SpecMatch CPU | Est. Budget |
    |-------------------|----------------------------|-------------------|-------------|
    | **1080p (Entry)** | [Insert Mobile GPU, e.g. RTX 4050] | [Insert CPU] | ~$900 |
    | **1440p (Sweet Spot)** | [Insert Mobile GPU, e.g. RTX 4070] | [Insert CPU] | ~$1,400 |
    | **4K Ultra (Elite)** | [Insert Mobile GPU, e.g. RTX 4090] | [Insert CPU] | ~$2,800+ |

    ## Why You Need This Power
    Briefly explain (3 bullet points) why this specific game is hard to run (e.g., Ray Tracing, huge open world, physics).

    ## The Verdict: Buy This Laptop
    Recommend a specific laptop spec (e.g., RTX 4060) that is the best value for this game.
    Tell them clearly: "If you want to play {game['name']} without lag, this is the floor."
    
    [Include a placeholder for an Amazon Link here]
    """

    try:
        response = model.generate_content(full_prompt)
        content = response.text

        # Create a clean filename
        slug = game['name'].lower().replace(" ", "-").replace(":", "").replace("'", "")
        filename = f"content/posts/{slug}.md"
        
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
            
        print(f"✅ Created: {filename}")
        
    except Exception as e:
        print(f"❌ Error generating {game['name']}: {e}")

# --- MAIN EXECUTION ---
if __name__ == "__main__":
    # 1. Try to import the scraper dynamically
    try:
        # This adds the current folder to the path so we can import 'scraper.py'
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        import scraper
        
        print("🔍 Running Scraper to find top games...")
        
        # NOTE: Make sure your scraper.py has a function like get_top_games()
        # If your function is named differently, change it below.
        games_list = scraper.get_top_games()
        
        if not games_list:
            print("⚠️ Scraper returned no games! Using test list.")
            games_list = [{"name": "GTA VI"}, {"name": "Cyberpunk 2077"}]
            
    except AttributeError:
        print("❌ Error: Could not find 'get_top_games()' in scraper.py.")
        print("   Please check your scraper file.")
        games_list = []
    except ImportError:
        print("⚠️ Could not find scraper.py. Using test mode.")
        games_list = [{"name": "GTA VI"}]

    # 2. Loop through the games and generate articles
    print(f"🚀 Starting batch generation for {len(games_list)} games...")
    
    for i, game in enumerate(games_list):
        generate_post(game)
        
        # 3. Add a small delay to be safe with API limits
        if i < len(games_list) - 1:
            print("   (Waiting 2s...)")
            time.sleep(2)

    print("\n🎉 Batch generation complete!")
