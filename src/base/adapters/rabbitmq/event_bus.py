import asyncio
import json
import logging
from dataclasses import dataclass
from typing import Any

import aio_pika
from aio_pika import DeliveryMode

from src.base.ports.services.event_bus import (
    EventBusHandler,
    EventBusMessage,
    EventBusPort,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class RabbitMQSettings:
    url: str
    exchange: str = "events"
    exchange_type: str = "topic"
    queue: str = "app.events"
    routing_key: str = "#"
    prefetch: int = 50
    durable: bool = True


class RabbitMQEventBus(EventBusPort):
    def __init__(self, settings: RabbitMQSettings) -> None:
        if not settings.url:
            raise ValueError("RabbitMQSettings.url is required")
        self._s = settings

        self._lock = asyncio.Lock()
        self._conn: aio_pika.RobustConnection | None = None
        self._channel: aio_pika.abc.AbstractChannel | None = None
        self._exchange: aio_pika.abc.AbstractExchange | None = None

    def is_enabled(self) -> bool:
        return True

    async def _ensure(self) -> None:
        if self._conn and self._channel and self._exchange:
            return

        async with self._lock:
            if self._conn and self._channel and self._exchange:
                return

            self._conn = await aio_pika.connect_robust(self._s.url)
            self._channel = await self._conn.channel()
            await self._channel.set_qos(prefetch_count=self._s.prefetch)

            self._exchange = await self._channel.declare_exchange(
                name=self._s.exchange,
                type=self._s.exchange_type,
                durable=self._s.durable,
            )

    async def publish(self, message: EventBusMessage) -> None:
        await self._ensure()
        assert self._exchange is not None

        body_dict: dict[str, Any] = {
            "event_type": message.event_type,
            "payload": message.payload,
            "headers": dict(message.headers or {}),
            "message_id": message.message_id,
        }
        body = json.dumps(body_dict, default=str).encode("utf-8")

        amqp_msg = aio_pika.Message(
            body=body,
            content_type="application/json",
            message_id=message.message_id,
            headers=dict(message.headers or {}),
            delivery_mode=(
                DeliveryMode.PERSISTENT
                if self._s.durable
                else DeliveryMode.NOT_PERSISTENT
            ),
        )

        await self._exchange.publish(amqp_msg, routing_key=message.event_type)

    async def consume(self, *, handler: EventBusHandler) -> None:
        await self._ensure()
        assert self._channel is not None
        assert self._exchange is not None

        queue = await self._channel.declare_queue(
            name=self._s.queue,
            durable=self._s.durable,
        )

        await queue.bind(self._exchange, routing_key=self._s.routing_key)

        async def _on_message(incoming: aio_pika.IncomingMessage) -> None:
            async with incoming.process(requeue=True):
                payload = json.loads(incoming.body.decode("utf-8"))

                msg = EventBusMessage(
                    event_type=payload.get("event_type", ""),
                    payload=payload.get("payload") or {},
                    headers=payload.get("headers") or {},
                    message_id=payload.get("message_id") or incoming.message_id,
                )

                if not msg.event_type:
                    logger.warning(
                        "Dropping message without event_type (message_id=%s)",
                        incoming.message_id,
                    )
                    return

                await handler(msg)

        await queue.consume(_on_message)

        stop = asyncio.Event()
        try:
            await stop.wait()
        except asyncio.CancelledError:
            raise

    async def close(self) -> None:
        try:
            if self._channel:
                await self._channel.close()
        finally:
            self._channel = None
            self._exchange = None
            if self._conn:
                await self._conn.close()
            self._conn = None
