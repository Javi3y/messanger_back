"""
Base DTO (Data Transfer Object) class.

Provides serialization capabilities similar to BaseEntity for use in
request/response models and other data transfer objects.
"""

from datetime import datetime, date
from enum import Enum
from json import dumps as json_dumps
from typing import Any, ClassVar, Literal, Mapping
from uuid import UUID


class BaseDTO:
    # Per-DTO override hook: {"password", "secret", ...}
    __serialize_exclude__: ClassVar[set[str]] = set()

    def dump(
        self,
        *,
        mode: Literal["json", "python"] = "json",
        exclude_none: bool = True,
        exclude: set[str] | None = None,
        include: set[str] | None = None,
    ) -> dict[str, Any]:
        data = {k: v for k, v in vars(self).items() if not k.startswith("_")}

        # Combine exclusions
        all_exclude = set(self.__serialize_exclude__)
        if exclude:
            all_exclude |= set(exclude)

        if include is not None:
            data = {k: v for k, v in data.items() if k in include}

        if all_exclude:
            for k in all_exclude:
                data.pop(k, None)

        if exclude_none:
            data = {k: v for k, v in data.items() if v is not None}

        if mode == "python":
            return data

        return self._to_jsonable(data)

    def dumps(
        self,
        *,
        exclude_none: bool = True,
        exclude: set[str] | None = None,
        include: set[str] | None = None,
        ensure_ascii: bool = False,
        **json_kwargs: Any,
    ) -> str:
        payload = self.dump(
            mode="json",
            exclude_none=exclude_none,
            exclude=exclude,
            include=include,
        )
        return json_dumps(payload, ensure_ascii=ensure_ascii, **json_kwargs)

    @classmethod
    def dump_list(
        cls,
        dtos: list["BaseDTO"],
        *,
        mode: Literal["json", "python"] = "json",
        exclude_none: bool = True,
        exclude: set[str] | None = None,
        include: set[str] | None = None,
    ) -> list[dict[str, Any]]:
        return [
            dto.dump(
                mode=mode, exclude_none=exclude_none, exclude=exclude, include=include
            )
            for dto in dtos
        ]

    @classmethod
    def _to_jsonable(cls, obj: Any) -> Any:
        if obj is None:
            return None

        # BaseDTO instances (nested)
        if isinstance(obj, BaseDTO):
            return obj.dump(mode="json")

        # BaseEntity instances (domain entities)
        # Import here to avoid circular dependency
        try:
            from src.base.domain.entity import BaseEntity

            if isinstance(obj, BaseEntity):
                return obj.dump(mode="json")
        except ImportError:
            pass

        # Pydantic models (optional convenience)
        if hasattr(obj, "model_dump") and callable(getattr(obj, "model_dump")):
            return obj.model_dump(mode="json", exclude_none=True)

        # datetime/date/UUID
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, UUID):
            return str(obj)

        # Enums
        if isinstance(obj, Enum):
            return obj.value

        # Mappings / Iterables
        if isinstance(obj, Mapping):
            return {str(k): cls._to_jsonable(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple, set)):
            return [cls._to_jsonable(v) for v in obj]

        # Fallback: basic JSON types should pass through
        return obj
