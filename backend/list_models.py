import os
from google import genai
from dotenv import load_dotenv

load_dotenv(override=True)
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

try:
    # List models
    for m in client.models.list():
        print(f"Model: {m.name}")
except Exception as e:
    print("Error:", e)
