from app.providers.groq_provider import GroqProvider 
class ProviderFactory:
    @staticmethod
    def get_provider():
        return GroqProvider()
