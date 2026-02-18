from abc import ABC
from datetime import datetime, date
from enum import Enum
from json import dumps as json_dumps
from typing import Any, ClassVar, Literal, Mapping
from uuid import UUID


class BaseEntity(ABC):
    repo_attr: str
    id: int | None = None
    deleted_at: datetime | None = None

    # Per-entity override hook: {"password", "secret", ...}
    __serialize_exclude__: ClassVar[set[str]] = set()

    def __init__(
        self,
        id: int | None = None,
        deleted_at: datetime | None = None,
    ) -> None:
        self.id = id
        self.deleted_at = deleted_at

    # ----------------------------
    # Serialization
    # ----------------------------
    def dump(
        self,
        *,
        mode: Literal["json", "python"] = "json",
        exclude_none: bool = True,
        exclude: set[str] | None = None,
        include: set[str] | None = None,
    ) -> dict[str, Any]:
        data = {k: v for k, v in vars(self).items() if not k.startswith("_")}

        # combine exclusions
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
        """Serialize entity to JSON string."""
        payload = self.dump(
            mode="json",
            exclude_none=exclude_none,
            exclude=exclude,
            include=include,
        )
        return json_dumps(payload, ensure_ascii=ensure_ascii, **json_kwargs)

    @classmethod
    def _to_jsonable(cls, obj: Any) -> Any:
        """Recursively convert object to JSON-safe primitives."""
        if obj is None:
            return None

        # Entities (nested)
        if isinstance(obj, BaseEntity):
            return obj.dump(mode="json")

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
