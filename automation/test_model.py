import google.generativeai as genai
from dotenv import load_dotenv
import os

# --- CONFIGURATION ---
# 1. Load environment variables from .env
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

# SAFETY CHECK: Ensure the key was actually found
if not api_key:
    print("❌ ERROR: Could not find 'GOOGLE_API_KEY'.")
    print("   Make sure you have a file named .env in this folder.")
    print("   And inside it says: GOOGLE_API_KEY=your_key_here")
    exit()

# 2. Configure the library (MUST use 'api_key=' explicitly)
try:
    genai.configure(api_key=api_key)
    print(f"✅ API Key configured successfully.")
except Exception as e:
    print(f"❌ Configuration failed: {e}")
    exit()

# 3. List Models
print("\nListing available models...")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"- {m.name}")
except Exception as e:
    print(f"❌ Connection error: {e}")
