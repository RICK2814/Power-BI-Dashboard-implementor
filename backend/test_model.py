import os
import time
from google import genai
from dotenv import load_dotenv

load_dotenv(override=True)
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

model_name = "gemini-2.5-flash"

print(f"Testing model: {model_name}")
for i in range(3):
    try:
        response = client.models.generate_content(
            model="models/gemini-1.5-flash",
            contents="Say hello"
        )
        print(f"Success on attempt {i+1}:", response.text)
        break
    except Exception as e:
        print(f"Attempt {i+1} failed:", str(e))
        if "429" in str(e):
            print("Sleeping 15s...")
            time.sleep(15)
        else:
            break
