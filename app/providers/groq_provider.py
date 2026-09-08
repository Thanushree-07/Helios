from groq import Groq
from app.core.config import settings
from fastapi import HTTPException


class GroqProvider:
    def __init__(self):
        # print(settings.GROQ_API_KEY)
        self.client=Groq(api_key=settings.groq_api_key)

    def generate(self,prompt:str)->str:
        try:
            # print("Using key:", settings.groq_api_key)
            response=self.client.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
        except Exception as e:
            print("GROQ ERROR:", type(e).__name__, str(e))
            raise HTTPException(
                status_code=500,
                detail=str(e)
            )

        return response.choices[0].message.content




