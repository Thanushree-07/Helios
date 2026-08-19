from pydantic import BaseModel


class RoutingDecision(BaseModel):
    task_type: str
    complexity: str