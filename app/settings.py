from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings"""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    debug: bool = True

    # database
    database_echo: bool = False
    database_driver: str = "postgresql+asyncpg"
    database_username: str
    database_password: str
    database_host: str
    database_port: int
    database_database: str

    # security
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # cors
    cors_origins: list[str] = ["*"]

    # s3
    s3_endpoint: str | None = "http://localhost:9000"
    s3_region: str | None = "us-east-1"
    s3_bucket: str | None = "app-bucket"
    s3_access_key: str | None = None
    s3_secret_key: str | None = None
    s3_use_ssl: bool | None = False
    s3_path_style: bool | None = True
    s3_public_base_url: str | None = "http://localhost:9000/app-bucket"
    s3_presign_ttl: int = 300

    # redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: str | None = None
    redis_db: str = "0"
    default_ttl: int = 60

    # telgram
    telegram_api_id: int
    telegram_api_hash: str
    telegram_proxy_url: str | None = None

    # whatsapp
    whatsapp_base_url: str
    whatsapp_api_key: str

    # outbox -> broker dispatch strategy
    #   direct: DB outbox worker calls handlers directly (current behavior)
    #   broker: DB outbox worker publishes to broker, and consumers execute handlers
    outbox_dispatch_strategy: str = "direct"

    # broker (rabbitmq/kafka/etc)
    broker_driver: str = "none"  # "none" | "rabbitmq" (future: "kafka")
    broker_url: str | None = None

    broker_exchange: str = "events"
    broker_exchange_type: str = "topic"

    # consumer-side config (queue binding)
    broker_queue: str = "messenger.events"
    broker_routing_key: str = "#"
    broker_prefetch: int = 50
    broker_durable: bool = True

    @property
    def redis_url(self) -> str:
        """Construct the database URL from settings"""
        auth = f":{self.redis_password}@" if self.redis_password else ""
        return f"redis://{auth}{self.redis_host}:{self.redis_port}/{self.redis_db}"

    @property
    def database_url(self) -> str:
        """Construct the database URL from settings"""
        return (
            f"{self.database_driver}://"
            f"{self.database_username}:{self.database_password}@"
            f"{self.database_host}:{self.database_port}/"
            f"{self.database_database}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
