import os
from google import genai
from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env
api_key = os.getenv("GEMINI_API_KEY")
model = os.getenv("GEMINI_MODEL")

# configure gemini
client = genai.Client(api_key=api_key)
response = client.models.generate_content(
    model=model,
    contents="How does AI work?"
)
print(response.text)