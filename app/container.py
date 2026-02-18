from dependency_injector import containers, providers
from redis.asyncio import Redis
from src.base.application.outbox.registry import OutboxRegistry
from src.base.adapters.http.httpx_client import HttpxAsyncClient
from src.base.adapters.redis.repository import RedisCacheRepository
from src.base.adapters.sqlalchemydb.database import AsyncSqlalchemyDatabase
from src.base.adapters.sqlalchemydb.unit_of_work import AsyncSqlalchemyUnitOfWork
from src.base.infrastructure.lazy_entity_cache import LazyEntityCache
from src.files.adapters.s3_file_service import S3FileService, S3Settings
from src.messaging.adapters.clients.telethon_client import TelethonClient
from src.messaging.adapters.clients.whatsapp_http_service import WhatsappHttpService
from src.messaging.adapters.messengers.telegram_messenger import TelegramMessenger
from src.messaging.application.registry.messenger_registry import MessengerRegistry
from src.messaging.domain.enums.messenger_type import MessengerType
from src.users.adapters.security.jose_jwt_service import JwtSettings, JoseJwtService
from src.messaging.adapters.messengers.whatsapp_messenger import WhatsappMessenger
from src.users.adapters.security.password_hasher import PasslibPasswordHasher
from src.importing.adapters.redis.import_staging_repo import (
    RedisImportStagingRepository,
)
from src.importing.adapters.tabular.csv_reader import CsvTabularReader
from src.importing.adapters.tabular.xlsx_reader import XlsxTabularReader
from src.importing.adapters.tabular.resolver import TabularReaderResolver
from src.importing.application.registry.import_registry import ImportRegistry
from src.base.adapters.event_bus.noop_event_bus import NoopEventBus
from src.base.adapters.rabbitmq.event_bus import (
    RabbitMQEventBus,
    RabbitMQSettings,
)


class ApplicationContainer(containers.DeclarativeContainer):
    config = providers.Configuration()

    # Infrastructure (lowest level)
    database = providers.Factory(
        AsyncSqlalchemyDatabase,
        database_url=config.database_url,
    )
    redis_client = providers.Singleton(Redis.from_url, url=config.redis_url)
    cache_repo = providers.Factory(
        RedisCacheRepository,
        redis_client=redis_client,
        key_prefix="app",
    )

    # Unit of Work (depends on database and cache)
    unit_of_work = providers.Factory(
        AsyncSqlalchemyUnitOfWork,
        database=database,
        cache_repo=cache_repo,
    )

    # S3
    s3_settings = providers.Factory(
        S3Settings,
        endpoint=config.s3_endpoint,
        region=config.s3_region,
        access_key=config.s3_access_key,
        secret_key=config.s3_secret_key,
        use_ssl=config.s3_use_ssl,
        path_style=config.s3_path_style,
        default_bucket=config.s3_bucket,
        public_base_url=config.s3_public_base_url,
        presign_ttl=config.s3_presign_ttl,
    )
    file_service = providers.Factory(
        S3FileService,
        settings=s3_settings,
    )

    lazy_entity_cache = providers.Factory(
        LazyEntityCache,
        cache_repo=cache_repo,
        key_prefix="entity",
        default_ttl=config.default_ttl,
    )
    # Telegram: TelethonClient adapter + TelegramMessenger domain service
    telethon_client = providers.Factory(
        TelethonClient,
        api_id=config.telegram_api_id,
        api_hash=config.telegram_api_hash,
        proxy_url=config.telegram_proxy_url,
    )

    telegram_messenger = providers.Factory(
        TelegramMessenger,
        client=telethon_client,
        file_service=file_service,
    )

    whatsapp_http_client = providers.Factory(
        HttpxAsyncClient,
        base_url=config.whatsapp_base_url,
        timeout=120,
    )

    whatsapp_http_service = providers.Factory(
        WhatsappHttpService,
        client=whatsapp_http_client,
        key=config.whatsapp_api_key,
    )

    whatsapp_messenger = providers.Factory(
        WhatsappMessenger,
        service=whatsapp_http_service,
        file_service=file_service,
    )

    messenger_registry = providers.Factory(
        MessengerRegistry,
        messengers=providers.Dict(
            {
                MessengerType.telegram: telegram_messenger,
                MessengerType.whatsapp: whatsapp_messenger,
            }
        ),
    )

    jwt_settings = providers.Factory(
        JwtSettings,
        secret_key=config.secret_key,
        algorithm=config.algorithm,
        access_token_expire_minutes=config.access_token_expire_minutes,
    )

    password_hasher = providers.Singleton(PasslibPasswordHasher)

    jwt_service = providers.Singleton(
        JoseJwtService,
        settings=jwt_settings,
    )

    # Importing BC: staging repo + tabular readers
    import_staging_repo = providers.Factory(
        RedisImportStagingRepository,
        redis_client=redis_client,
    )

    tabular_reader = providers.Singleton(
        TabularReaderResolver,
        readers=providers.List(
            providers.Factory(CsvTabularReader),
            providers.Factory(XlsxTabularReader),
        ),
    )

    import_registry = providers.Singleton(ImportRegistry)

    # Event bus (broker)

    rabbitmq_settings = providers.Factory(
        RabbitMQSettings,
        url=config.broker_url,
        exchange=config.broker_exchange,
        exchange_type=config.broker_exchange_type,
        queue=config.broker_queue,
        routing_key=config.broker_routing_key,
        prefetch=config.broker_prefetch,
        durable=config.broker_durable,
    )

    event_bus = providers.Selector(
        config.broker_driver,
        none=providers.Singleton(NoopEventBus),
        rabbitmq=providers.Singleton(RabbitMQEventBus, settings=rabbitmq_settings),
    )

    outbox_registry = providers.Singleton(OutboxRegistry)
