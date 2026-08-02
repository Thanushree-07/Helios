from groq import Groq
from app.core.config import settings
from fastapi import HTTPException


class GroqProvider:
    def __init__(self):
        # print(settings.GROQ_API_KEY)
        self.client=Groq(api_key=settings.GROQ_API_KEY)

    def generate(self,prompt:str)->str:
        try:
            # print("Using key:", settings.groq_api_key)
            response=self.client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail="Unable to connect to Groq Provider"
            )
        return response.choices[0].message.content




