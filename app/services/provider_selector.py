from app.services.router_service import RouterService


class ProviderSelector:

    def __init__(self):
        self.router = RouterService()

    def select_provider(self, prompt: str) -> str:

        decision = self.router.analyze(prompt)

        print("Router decision:", decision)

        if decision.task_type == "general" and decision.complexity == "low":
            print("general,low so = groq")
            return "groq"

        elif decision.task_type == "coding" and decision.complexity == "medium":
            print("coding,medium so = gemini")

            return "gemini"

        else:
            print("else part")

            return "gemini"