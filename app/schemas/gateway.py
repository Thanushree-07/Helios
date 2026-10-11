from pydantic import BaseModel, ConfigDict


def to_camel(s: str) -> str:
    parts = s.split("_")
    return parts[0] + "".join(p.title() for p in parts[1:])


class CamelModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class ProviderOut(CamelModel):
    id: int
    name: str
    model: str
    priority: int
    enabled: bool
    status: str
    cost_per_1k: float
    region: str


class ProviderUpdate(BaseModel):
    enabled: bool | None = None
    status: str | None = None


class APIKeyCreate(BaseModel):
    name: str
    rate_limit: int = 60
    monthly_budget: float = 5.0


class APIKeyOut(CamelModel):
    id: int
    name: str
    key: str
    rate_limit: int
    monthly_budget: float
    spent: float
    active: bool
    created_at: str


class ChatPlaygroundRequest(BaseModel):
    api_key: str
    prompt: str