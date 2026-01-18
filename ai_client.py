import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)


MODELS = [
    "openai/gpt-4.1-mini",       # User specifically requested this
    "openai/gpt-4o-mini",        # Fallback closest to likely intent
    "google/gemini-2.0-flash-exp:free",
    "qwen/qwen-2-7b-instruct:free",
    "meta-llama/llama-3.1-8b-instruct:free",
    "mistralai/mistral-7b-instruct:free",
]

def get_definition(word: str) -> str:
    for model in MODELS:
        try:
            print(f"Trying model: {model}...")
            completion = client.chat.completions.create(
                extra_headers={
                    "HTTP-Referer": "https://telegram-bot-app.com",
                    "X-Title": "WordDefinitionBot",
                },
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a dictionary bot. "
                            "RULES:\n"
                            "1. If the input word is Russian, you MUST output in Russian.\n"
                            "2. If the input word is English, you MUST output in English.\n"
                            "3. Provide a simple definition and an example sentence.\n"
                            "4. Format clearly:\n"
                            "Definition: ...\n"
                            "Context: ...\n"
                        )
                    },
                    {
                        "role": "user",
                        "content": f"Word: '{word}'. Define this word in the same language as the word itself."
                    }
                ]
            )
            content = completion.choices[0].message.content
            if not content or content.strip() == "":
                print(f"Model {model} returned empty content.")
                continue
                
            return content
        except Exception as e:
            print(f"Error with {model}: {e}")
            continue
            
    return "Sorry, I couldn't find a definition for that word right now. Please try again later."
