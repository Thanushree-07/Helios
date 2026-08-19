from app.schemas.routing import RoutingDecision


class ProviderSelector:

    def select_provider(self, prompt: str) -> RoutingDecision:
        return RoutingDecision(
            task_type="general",
            complexity="low"
        )