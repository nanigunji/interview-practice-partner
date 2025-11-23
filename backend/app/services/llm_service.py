import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

class LLMService:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in .env")

        self.client = genai.Client(api_key=api_key)

    # def generate(self, prompt: str, model="gemini-1.5-flash"):
    #     response = self.client.models.generate_content(
    #         model=model,
    #         contents=prompt
    #     )
    #     return response.text
    def generate(self, prompt: str, model="models/gemini-2.0-flash"):
        response = self.client.models.generate_content(
            model=model,
            contents=prompt
        )
        return response.text