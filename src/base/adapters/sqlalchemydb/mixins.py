from typing import Type, TypeVar, Any

from src.base.domain.entity import BaseEntity

E = TypeVar("E", bound=BaseEntity)


class EntityModelMixin:

    entity_cls: Type[E]
    _entity_fields: list[str] = []

    def to_entity(self) -> E:
        payload: dict[str, Any] = {}

        if hasattr(self, "id"):
            payload["id"] = getattr(self, "id")
        if hasattr(self, "deleted_at"):
            payload["deleted_at"] = getattr(self, "deleted_at")

        for name in self._entity_fields:
            payload[name] = getattr(self, name)

        cleaned = {k: v for k, v in payload.items() if v is not None}
        return self.entity_cls(**cleaned)

    @classmethod
    def from_entity(cls, entity: E) -> "EntityModelMixin":
        kwargs: dict[str, Any] = {}
        for name in getattr(cls, "_entity_fields", []):
            kwargs[name] = getattr(entity, name)

        if getattr(entity, "id", None) is not None:
            kwargs["id"] = entity.id

        return cls(**kwargs)
