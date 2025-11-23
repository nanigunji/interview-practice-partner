import os
from google import genai
from google.genai.types import GenerationConfig   # ✅ correct import
from dotenv import load_dotenv

load_dotenv()

class LLMService:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in .env")

        self.client = genai.Client(api_key=api_key)
        print("🔧 LLMService initialized with Gemini API key.")

    def generate(self, prompt: str, model="models/gemini-2.0-flash"):
        try:
            print("📩 LLM INPUT PROMPT:", prompt)

            response = self.client.models.generate_content(
                model=model,
                contents=prompt,
                config={
                    "temperature": 0.9,
                    "top_p": 0.9,
                    "top_k": 40,
                    "max_output_tokens": 300
                }
            )

            print("📤 LLM RAW RESPONSE:", response)
            print("📤 LLM TEXT:", response.text)

            return response.text

        except Exception as e:
            print("❌ LLMService.generate ERROR:", e)
            raise
