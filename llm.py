import os
import json
from dotenv import load_dotenv
from google import genai

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")


def generate_json(prompt: str, temperature=None) -> dict:
    config = {"response_mime_type": "application/json"}
    if temperature is not None:
        config["temperature"] = temperature
    resp = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=config,
    )
    return json.loads(resp.text)