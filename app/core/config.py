from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "JobRadar"
    environment: str = "development"
    secret_key: str = "dev-only-change-me"
    database_url: str = "sqlite:///./jobradar.db"
    cors_origins: str = "http://localhost:3000"
    # Clé partagée avec n8n pour les routes /internal (en-tête X-API-Key). Vide = routes refusées.
    jobradar_internal_key: str = ""
    scheduler_enabled: bool = True
    collection_interval_minutes: int = 60
    collection_sources: str = "demo"
    ai_enabled: bool = False
    ai_base_url: str = "https://api.openai.com/v1"
    ai_api_key: str = ""
    ai_model: str = ""
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from: str = ""
    smtp_to: str = ""
    smtp_use_tls: bool = True
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def source_list(self) -> list[str]:
        return [source.strip() for source in self.collection_sources.split(",") if source.strip()]

@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
