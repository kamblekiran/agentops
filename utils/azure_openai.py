import os
import requests
from config import is_simulation_mode
from dotenv import load_dotenv

load_dotenv()

def azure_openai_prompt(messages: list, model="gpt-4") -> str:
    """
    Uses Azure OpenAI Service instead of Google Gemini
    """
    if is_simulation_mode():
        return "[SIMULATED AZURE OPENAI RESPONSE]"

    try:
        api_key = os.getenv("AZURE_OPENAI_API_KEY")
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", model)
        api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
        
        if not api_key or not endpoint:
            raise ValueError("Azure OpenAI API key and endpoint must be set")

        url = f"{endpoint}/openai/deployments/{deployment_name}/chat/completions?api-version={api_version}"

        # Convert messages to OpenAI format
        formatted_messages = []
        for msg in messages:
            if isinstance(msg, str):
                formatted_messages.append({"role": "user", "content": msg})
            elif isinstance(msg, dict):
                if "text" in msg:
                    formatted_messages.append({"role": "user", "content": msg["text"]})
                elif "parts" in msg:
                    content = ""
                    for part in msg["parts"]:
                        if isinstance(part, str):
                            content += part
                        elif isinstance(part, dict) and "text" in part:
                            content += part["text"]
                    formatted_messages.append({"role": "user", "content": content})
                else:
                    formatted_messages.append({"role": "user", "content": str(msg)})

        payload = {
            "messages": formatted_messages,
            "max_tokens": 4000,
            "temperature": 0.7
        }

        headers = {
            "Content-Type": "application/json",
            "api-key": api_key
        }

        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()

        return data["choices"][0]["message"]["content"].strip()

    except Exception as e:
        return f"[ERROR calling Azure OpenAI]: {e}"