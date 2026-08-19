from groq import Groq

from app.core.config import settings
from app.schemas.routing import RoutingDecision


class RouterService:

    def __init__(self):
        self.client = Groq(api_key=settings.groq_api_key)

    def analyze(self, prompt: str) -> RoutingDecision:

        response = self.client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {
                    "role": "system",
                    "content": """
You are the routing brain of an AI gateway.

Analyze the user's request and classify it.

Return a JSON object containing:
- task_type
- complexity

Do NOT answer the user's request.
"""
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            response_format={
                "type": "json_object"
            }
        )

        result = response.choices[0].message.content

        return RoutingDecision.model_validate_json(result)