from app.providers.groq_provider import GroqProvider
from app.providers.gemini_provider import GeminiProvider
from app.providers.llama_provider import LlamaProvider


class ProviderFactory:

    @staticmethod
    def get_provider(provider_name: str):

        if provider_name == "groq":
            return GroqProvider()
        if provider_name=="gemini":
            return GeminiProvider()
        if provider_name=="ollama":
            return LlamaProvider()

        raise ValueError("Unsupported provider")