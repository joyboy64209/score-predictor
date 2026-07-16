from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql://predictor:predictor@localhost:5432/match_predictor?schema=public"
    backend_url: str = "http://localhost:3001"
    model_dir: str = "/app/models"

    threshold_match_result: float = 70.0
    threshold_double_chance: float = 90.0
    threshold_other: float = 80.0
    threshold_combination: float = 80.0


settings = Settings()
