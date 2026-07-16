import os


class Settings:
    def __init__(self) -> None:
        self.anthropic_api_key: str | None = os.getenv("ANTHROPIC_API_KEY") or None
        self.anthropic_model: str = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5")
        self.db_path: str = os.getenv("DB_PATH", "/data/events.db")

    @property
    def llm_enabled(self) -> bool:
        return bool(self.anthropic_api_key)


settings = Settings()
