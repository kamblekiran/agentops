import os
import requests
from config import is_simulation_mode
from dotenv import load_dotenv

load_dotenv()

def gemini_prompt(messages: list, model="gemini-2.0-flash") -> str:
    if is_simulation_mode():
        return "[SIMULATED GEMINI RESPONSE]"

    try:
        api_key = os.getenv("GEMINI_API_KEY")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        print("url:", url)

        # ✅ Flatten messages into a list of strings
        if isinstance(messages, list):
            flattened = []
            for msg in messages:
                if isinstance(msg, str):
                    flattened.append(msg)
                elif isinstance(msg, dict) and "parts" in msg:
                    for part in msg["parts"]:
                        if isinstance(part, str):
                            flattened.append(part)
                        elif isinstance(part, dict) and "text" in part:
                            flattened.append(part["text"])
                elif isinstance(msg, dict) and "text" in msg:
                    flattened.append(msg["text"])
                else:
                    flattened.append(str(msg))
        else:
            flattened = [str(messages)]

        prompt_text = "\n".join(flattened)

        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt_text
                        }
                    ]
                }
            ]
        }

        print("payload:", payload)
        headers = {
            "Content-Type": "application/json"
        }

        response = requests.post(url, json=payload, headers=headers)
        print("response:", response)
        response.raise_for_status()
        data = response.json()
        print("data:", data)

        return data["candidates"][0]["content"]["parts"][0]["text"].strip()

    except Exception as e:
        return f"[ERROR calling Gemini]: {e}"
