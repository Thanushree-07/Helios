from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )

    app_name: str
    version: str
    debug: bool
    groq_api_key: str
    gemini_api_key:str


settings = Settings()