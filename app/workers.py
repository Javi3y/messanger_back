import argparse
import asyncio
import inspect
import logging
from typing import Any, Callable

from app.container import ApplicationContainer
from app.settings import get_settings

# Import handler modules to register them in the outbox registry
import src.messaging.application.outbox_handlers  # noqa: F401
import src.importing.application.outbox_handlers  # noqa: F401

from src.base.workers import JOBS as BASE_WORKERS
from src.messaging.workers import JOBS as MESSAGING_WORKERS

WORKER_JOBS = {**BASE_WORKERS, **MESSAGING_WORKERS}

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


def _kwargs_for_job(
    job: Callable[..., Any],
    *,
    container: ApplicationContainer,
    batch_size: int,
) -> dict[str, Any]:
    """Build kwargs for a job by inspecting its parameter names."""
    kwargs: dict[str, Any] = {}
    sig = inspect.signature(job)
    for name in sig.parameters:
        if name == "uow_factory":
            kwargs[name] = container.unit_of_work
        elif name == "messenger_registry":
            kwargs[name] = container.messenger_registry()
        elif name == "file_service":
            kwargs[name] = container.file_service()
        elif name == "batch_size":
            kwargs[name] = batch_size
        elif name == "event_bus":
            kwargs[name] = container.event_bus()
        elif name == "import_staging_repo":
            kwargs[name] = container.import_staging_repo()
        elif name == "tabular_reader":
            kwargs[name] = container.tabular_reader()
        elif name == "import_registry":
            kwargs[name] = container.import_registry()
        elif name == "outbox_registry":
            kwargs[name] = container.outbox_registry()
        elif name == "dispatch_strategy":
            kwargs[name] = container.config.outbox_dispatch_strategy()
    return kwargs


async def run_job_once(
    job: Callable[..., Any],
    *,
    container: ApplicationContainer,
    batch_size: int,
) -> Any:
    kwargs = _kwargs_for_job(job, container=container, batch_size=batch_size)
    return await job(**kwargs)


async def _run_one_job_loop(
    name: str,
    *,
    job: Callable[..., Any],
    container: ApplicationContainer,
    interval: float,
    batch_size: int,
) -> None:
    while True:
        try:
            res = await run_job_once(job, container=container, batch_size=batch_size)
            logger.info("%s: %s", name, res)
        except Exception:
            logger.exception("Job %s crashed", name)
        await asyncio.sleep(interval)


async def main() -> None:
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(description="Run background jobs")
    parser.add_argument("--job", default="all", help="Job name, or 'all'")
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    parser.add_argument(
        "--interval", type=float, default=None, help="Override interval"
    )
    parser.add_argument(
        "--batch-size", type=int, default=None, help="Override batch size"
    )
    args = parser.parse_args()

    jobs = dict(WORKER_JOBS)
    if args.job != "all":
        if args.job not in jobs:
            raise SystemExit(
                f"Unknown job '{args.job}'. Known: {', '.join(jobs.keys())}"
            )
        jobs = {args.job: jobs[args.job]}

    container = build_container()

    init_res = getattr(container, "init_resources", None)
    shutdown_res = getattr(container, "shutdown_resources", None)
    maybe = init_res() if callable(init_res) else None
    if inspect.isawaitable(maybe):
        await maybe

    try:
        if args.once:
            for name, spec in jobs.items():
                batch = args.batch_size if args.batch_size is not None else spec.batch
                logger.info("Running once: %s (batch=%s)", name, batch)
                await run_job_once(spec.job, container=container, batch_size=batch)
            return

        tasks = []
        for name, spec in jobs.items():
            interval = args.interval if args.interval is not None else spec.interval
            batch = args.batch_size if args.batch_size is not None else spec.batch
            tasks.append(
                asyncio.create_task(
                    _run_one_job_loop(
                        name,
                        job=spec.job,
                        container=container,
                        interval=interval,
                        batch_size=batch,
                    )
                )
            )

        await asyncio.gather(*tasks)
    finally:
        maybe2 = shutdown_res() if callable(shutdown_res) else None
        if inspect.isawaitable(maybe2):
            await maybe2


if __name__ == "__main__":
    asyncio.run(main())
