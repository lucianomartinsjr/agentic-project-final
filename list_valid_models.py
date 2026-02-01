import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

api_key = os.environ.get("GOOGLE_API_KEY")
genai.configure(api_key=api_key)

with open("valid_models.txt", "w", encoding="utf-8") as f:
    try:
        f.write("--- MODELS START ---\n")
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                f.write(f"{m.name}\n")
        f.write("--- MODELS END ---\n")
    except Exception as e:
        f.write(f"ERROR: {e}\n")
