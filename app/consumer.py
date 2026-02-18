import asyncio
from src.base.workers.consume_event_bus_messages import consume_event_bus_messages
import inspect
import logging

from app.container import ApplicationContainer
from app.settings import get_settings

logger = logging.getLogger(__name__)


def build_container() -> ApplicationContainer:
    settings = get_settings()
    container = ApplicationContainer()
    container.config.from_dict(
        {
            "database_url": settings.database_url,
            "s3_endpoint": settings.s3_endpoint,
            "s3_region": settings.s3_region,
            "s3_access_key": settings.s3_access_key,
            "s3_secret_key": settings.s3_secret_key,
            "s3_use_ssl": settings.s3_use_ssl,
            "s3_path_style": settings.s3_path_style,
            "s3_bucket": settings.s3_bucket,
            "s3_public_base_url": settings.s3_public_base_url,
            "s3_presign_ttl": settings.s3_presign_ttl,
            "redis_url": settings.redis_url,
            "default_ttl": settings.default_ttl,
            "telegram_api_id": settings.telegram_api_id,
            "telegram_api_hash": settings.telegram_api_hash,
            "whatsapp_base_url": settings.whatsapp_base_url,
            "whatsapp_api_key": settings.whatsapp_api_key,
            "outbox_dispatch_strategy": settings.outbox_dispatch_strategy,
            "broker_driver": settings.broker_driver,
            "broker_url": settings.broker_url,
            "broker_exchange": settings.broker_exchange,
            "broker_exchange_type": settings.broker_exchange_type,
            "broker_queue": settings.broker_queue,
            "broker_routing_key": settings.broker_routing_key,
            "broker_prefetch": settings.broker_prefetch,
            "broker_durable": settings.broker_durable,
        }
    )
    return container


async def main() -> None:
    logging.basicConfig(level=logging.INFO)

    settings = get_settings()
    container = build_container()

    init_res = getattr(container, "init_resources", None)
    shutdown_res = getattr(container, "shutdown_resources", None)
    maybe = init_res() if callable(init_res) else None
    if inspect.isawaitable(maybe):
        await maybe

    if settings.broker_driver == "none":
        raise SystemExit(
            "Consumer requires broker mode (set broker_driver='rabbitmq'). "
            "For direct mode (DB polling), use app/workers.py instead."
        )


    logger.info("Starting consumer (broker mode: %s)...", settings.broker_driver)
    logger.info("Queue: %s", settings.broker_queue)
    logger.info("Exchange: %s", settings.broker_exchange)

    try:
        await consume_event_bus_messages(
            uow_factory=container.unit_of_work,
            outbox_registry=container.outbox_registry(),
            container=container,
            event_bus=container.event_bus(),
        )
    finally:
        logger.info("Shutting down consumer...")
        await container.event_bus().close()
        maybe2 = shutdown_res() if callable(shutdown_res) else None
        if inspect.isawaitable(maybe2):
            await maybe2


if __name__ == "__main__":
    asyncio.run(main())
