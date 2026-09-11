from google import genai
from app.core.config import settings
from fastapi import HTTPException


class GeminiProvider:

    def __init__(self):
        self.client = genai.Client(
            api_key=settings.gemini_api_key
        )

    def generate(self, prompt: str) -> str:
        try:
            response = self.client.models.generate_content(
                model="gemini-3.8-flash",
                contents=prompt
            )

        except Exception as e:
            print("GEMINI ERROR:", type(e).__name__, str(e))
            raise HTTPException(
                status_code=500,
                detail=str(e)
            )

        return response.text