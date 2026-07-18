from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- Core ---
    database_url: str = "postgresql://predictor:predictor@localhost:5432/match_predictor?schema=public"
    backend_url: str = "http://localhost:3001"
    model_dir: str = "models"
    datasets_dir: str = "datasets/kaggle"
    
    @property
    def model_dir_abs(self) -> str:
        """Get absolute path to model directory."""
        import os
        return os.path.join(os.path.dirname(os.path.dirname(__file__)), self.model_dir)
    log_level: str = "INFO"

    # --- Confidence thresholds (configurable) ---
    threshold_match_result: float = 70.0
    threshold_double_chance: float = 90.0
    threshold_other: float = 80.0
    threshold_combination: float = 80.0

    # --- Provider API keys (never hardcoded) ---
    football_data_api_key: str = ""
    api_football_api_key: str = ""
    kaggle_username: str = ""
    kaggle_key: str = ""

    # --- HTTP behaviour ---
    http_timeout: float = 20.0
    http_max_retries: int = 3
    http_cache_ttl: int = 3600  # seconds
    http_cache_dir: str = ".http_cache"

    # --- Scheduler ---
    sync_cron_fixtures: str = "0 */6 * * *"
    sync_cron_elo: str = "0 3 * * *"

    @property
    def has_football_data(self) -> bool:
        return bool(self.football_data_api_key)

    @property
    def has_api_football(self) -> bool:
        return bool(self.api_football_api_key)

    @property
    def has_kaggle(self) -> bool:
        return bool(self.kaggle_username and self.kaggle_key)


settings = Settings()
