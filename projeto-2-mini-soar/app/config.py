import os


class Settings:
    def __init__(self) -> None:
        self.abuseipdb_api_key: str | None = os.getenv("ABUSEIPDB_API_KEY") or None
        self.virustotal_api_key: str | None = os.getenv("VIRUSTOTAL_API_KEY") or None
        self.slack_webhook_url: str | None = os.getenv("SLACK_WEBHOOK_URL") or None
        self.discord_webhook_url: str | None = os.getenv("DISCORD_WEBHOOK_URL") or None
        self.db_path: str = os.getenv("DB_PATH", "/data/soar.db")
        self.queue_path: str = os.getenv("QUEUE_PATH", "data/indicators_queue.json")
        self.mock_reputation_path: str = os.getenv(
            "MOCK_REPUTATION_PATH", "data/mock_reputation.json"
        )

    @property
    def webhook_enabled(self) -> bool:
        return bool(self.slack_webhook_url or self.discord_webhook_url)


settings = Settings()
