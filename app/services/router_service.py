import logging

from groq import Groq

from app.core.config import settings
from app.schemas.routing import RoutingDecision

logger = logging.getLogger("helios.router")

# Used whenever the classification call itself fails (timeout, bad JSON,
# provider outage). Routing must never be a single point of failure for
# the whole gateway — degrade to a safe default instead of raising.
DEFAULT_DECISION = RoutingDecision(task_type="general", complexity="low")


class RouterService:

    def __init__(self):
        self.client = Groq(api_key=settings.groq_api_key)

    def analyze(self, prompt: str) -> RoutingDecision:
        try:
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

        except Exception as e:
            logger.warning(
                "Router classification failed (%s: %s) — falling back to default decision",
                type(e).__name__,
                e,
            )
            return DEFAULT_DECISION