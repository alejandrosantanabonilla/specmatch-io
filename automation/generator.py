import google.generativeai as genai
import json
import os
import re
import time
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

# --- CONFIGURATION ---
# Now we get the keys safely from the OS
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
AMAZON_TAG = os.getenv("AMAZON_TAG")

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE = os.path.join(BASE_DIR, "data", "requirements.json")
# Output to the Hugo 'content/posts' directory (one level up from automation)
OUTPUT_DIR = os.path.join(BASE_DIR, "..", "content", "posts")

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

def clean_slug(text):
    """Converts title to url-friendly-slug."""
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'\s+', '-', text)
    return text

def extract_search_keywords(specs_text):
    """Parses messy specs to find GPU/RAM for the Amazon search link."""
    specs_text = specs_text.lower()
    
    # Simple regex to find common GPU names
    gpu_match = re.search(r'(rtx\s?\d{4}|gtx\s?\d{4}|rx\s?\d{4})', specs_text)
    # Find RAM amount
    ram_match = re.search(r'(\d+)\s?gb', specs_text)
    
    parts = ["Laptop"]
    
    if gpu_match:
        parts.append(gpu_match.group(1).upper())
    else:
        parts.append("Gaming")
        
    if ram_match:
        parts.append(f"{ram_match.group(1)}GB RAM")
        
    return "+".join(parts)

def generate_article_text(game_name, rec_specs):
    """Calls Gemini API to write the analysis."""
    print(f"   > Asking Gemini about {game_name}...")
    
    prompt = f"""
    Act as a PC hardware expert. Write a technical blog section about the laptop requirements for the game "{game_name}".
    
    Official Recommended Specs:
    {rec_specs}

    Write 3 distinct paragraphs in Markdown:
    1. **CPU Analysis**: Briefly explain the CPU needs.
    2. **GPU Breakdown**: Analyze the graphical demands (textures, lighting) and why this level of GPU is needed.
    3. **The Verdict**: A concluding sentence on what kind of laptop budget is needed (Entry-level, Mid-range, or High-end).

    Do not use a H1 title. Keep it concise.
    """
    
    try:
        # Rate limit safety: 4s delay for Free Tier
        time.sleep(4)
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"   > API Error: {e}")
        return "Analysis currently unavailable."

def generate_markdown(game_data):
    """Assembles the final .md file content."""
    name = game_data['name']
    min_specs = game_data.get('min_specs_text', 'N/A')
    rec_specs = game_data.get('rec_specs_text', 'N/A')
    
    # 1. Create Affiliate Link
    search_keywords = extract_search_keywords(rec_specs)
    affiliate_link = f"https://www.amazon.com/s?k={search_keywords}&tag={AMAZON_TAG}"
    
    # 2. Get AI Content
    ai_content = generate_article_text(name, rec_specs)

    # 3. Build the File String
    content = f"""---
title: "Best Laptop for {name} (2025 Requirements)"
date: {datetime.now().strftime('%Y-%m-%d')}
draft: false
image: "/images/hud-{clean_slug(name)}.jpg" 
categories: ["Laptop Guides"]
tags: ["{name}", "System Requirements", "Gaming Laptop"]
---

Are you looking to play **{name}** but don't know if your laptop can handle it? We've analyzed the official system requirements to help you find the perfect machine.

## Official Specs Reference

To run {name} smoothly, the developers recommend:

> **Recommended Specs:**
> {rec_specs}

## Hardware Analysis

{ai_content}

## Our Recommendation

Based on these benchmarks, you need a laptop equipped with at least a **{search_keywords.replace('+', ' ')}**.

<div style="background-color: #222; padding: 20px; border-radius: 8px; text-align: center; margin: 30px 0;">
    <h3 style="margin-top:0; color: #fff;">Top Compatible Laptops</h3>
    <p style="color: #ccc;">Check current prices for laptops capable of running {name}:</p>
    <a href="{affiliate_link}" target="_blank" rel="nofollow" style="background-color: #f90; color: #000; padding: 12px 24px; text-decoration: none; font-weight: bold; border-radius: 4px; display: inline-block;">
        View Compatible Laptops on Amazon &rarr;
    </a>
</div>

"""
    return content

def main():
    # 1. Load Data
    if not os.path.exists(INPUT_FILE):
        print(f"Error: {INPUT_FILE} not found. Run scraper.py first!")
        return

    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        games = json.load(f)

    print(f"Generating content for {len(games)} games...")

    # 2. Loop through games
    for game in games:
        slug = clean_slug(game['name'])
        filename = os.path.join(OUTPUT_DIR, f"{slug}.md")
        
        # Optional: Skip if exists to avoid overwriting
        # if os.path.exists(filename):
        #     print(f"Skipping {slug} (Exists)")
        #     continue
        
        markdown_content = generate_markdown(game)
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
            
        print(f"Created: {filename}")

    print("\nDone! Content is ready in /content/posts/")

if __name__ == "__main__":
    main()
