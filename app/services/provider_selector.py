from app.services.router_service import RouterService


class ProviderSelector:

    def __init__(self):
        self.router = RouterService()

    def select_provider(self, prompt: str) -> str:

        decision = self.router.analyze(prompt)

        print("Router decision:", decision)

        # TEMP: Ollama isn't installed on this machine yet.
        # Tonight, once it's set up, change these two "gemini" returns
        # back to "ollama".
        if decision.task_type == "general" and decision.complexity == "low":
            print("general,low so = gemini (temp, ollama not installed yet)")
            return "gemini"

        elif decision.task_type == "coding" and decision.complexity == "medium":
            print("coding,medium so = gemini")
            return "gemini"

        elif decision.complexity == "high":
            print("high complexity so = groq")
            return "groq"

        else:
            print("else part = gemini (temp, ollama not installed yet)")
            return "gemini"