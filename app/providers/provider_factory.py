from app.providers.groq_provider import GroqProvider
from app.providers.gemini_provider import GeminiProvider


class ProviderFactory:

    @staticmethod
    def get_provider(provider_name: str):

        if provider_name == "groq":
            return GroqProvider()
        if provider_name=="gemini":
            return GeminiProvider()

        raise ValueError("Unsupported provider")