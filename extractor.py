import easyocr
from openai import OpenAI
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    print("⚠️ Warning: OPENAI_API_KEY not found. Please set it as an environment variable or in .env file")
    # For development, you can set a default or handle gracefully
    OPENAI_API_KEY = "your-api-key-here"

client = OpenAI(api_key=OPENAI_API_KEY)
reader = easyocr.Reader(['en'])

def extract_text_from_image(image_path):
    result = reader.readtext(image_path, detail=0)
    return "\n".join(result)

def extract_medicines_from_text(text):
    prompt = f"""
Extract the medicine details from this text. For each medicine, give:
- name
- dosage
- frequency (like 1-0-1 or times per day)
Format your response as a JSON list of dictionaries:
[
  {{
    "name": "...",
    "dosage": "...",
    "frequency": "..."
  }}
]
Text:
{text}
"""


    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )

    try:
        content = response.choices[0].message.content.strip()
        return eval(content) if content.startswith("[") else []
    except Exception as e:
        print("OpenAI parsing failed:", e)
        return []
