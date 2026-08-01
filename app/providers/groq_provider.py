from groq import Groq
from app.core.config import settings
class GroqProvider:
    def __init__(self):
        self.client=Groq(api_key=settings.GROQ_API_KEY)

    def generate(self,prompt:str)->str:
        response=self.client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        return response.choices[0].message.content




