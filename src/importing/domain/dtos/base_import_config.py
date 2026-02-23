from typing import ClassVar

from pydantic import (
    BaseModel,
    Field,
    ConfigDict,
    field_validator,
    model_validator,
)
from src.importing.domain.enums.unknown_columns_policy import UnknownColumnsPolicy


class BaseImportConfig(BaseModel):
    # reject unknown fields in the config payload
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    import_type: ClassVar[str] = "base"

    # internal_key -> file_header
    required: dict[str, str] = Field(default_factory=dict)
    optional: dict[str, str] = Field(default_factory=dict)

    # variable_name -> file_header (for future templating)
    extras: dict[str, str] = Field(default_factory=dict)

    # row error behavior
    stop_on_row_error: bool = False
    max_errors: int = Field(default=500, ge=1)

    # --- generic constraints you can optionally set in subclasses ---
    unknown_columns_policy: ClassVar[UnknownColumnsPolicy] = UnknownColumnsPolicy.error
    allowed_required_keys: ClassVar[set[str] | None] = None
    allowed_optional_keys: ClassVar[set[str] | None] = None
    required_must_include: ClassVar[set[str] | frozenset[str]] = frozenset()

    @field_validator("required", "optional", "extras", mode="before")
    @classmethod
    def _ensure_dict(cls, v):
        # Pydantic already validates types, but this gives clearer error messages
        if v is None:
            return {}
        if not isinstance(v, dict):
            raise ValueError("required/optional/extras must be dicts")
        return v

    @model_validator(mode="after")
    def _validate_basic(self) -> "BaseImportConfig":
        # minimal sanity checks
        if (
            not isinstance(self.required, dict)
            or not isinstance(self.optional, dict)
            or not isinstance(self.extras, dict)
        ):
            raise ValueError("required/optional/extras must be dicts")

        # keys/values must be strings
        for name, mapping in (
            ("required", self.required),
            ("optional", self.optional),
            ("extras", self.extras),
        ):
            for k, v in mapping.items():
                if not isinstance(k, str) or not isinstance(v, str):
                    raise ValueError(f"{name} must be dict[str, str]")

        # required & optional keys must not overlap
        overlap = set(self.required.keys()) & set(self.optional.keys())
        if overlap:
            raise ValueError(
                f"Keys cannot be in both required and optional: {sorted(overlap)}"
            )

        # subclass-driven constraints (optional)
        if self.allowed_required_keys is not None:
            bad = set(self.required.keys()) - self.allowed_required_keys
            if bad:
                raise ValueError(f"Invalid required keys: {sorted(bad)}")

        if self.allowed_optional_keys is not None:
            bad = set(self.optional.keys()) - self.allowed_optional_keys
            if bad:
                raise ValueError(f"Invalid optional keys: {sorted(bad)}")

        if self.required_must_include:
            missing = set(self.required_must_include) - set(self.required.keys())
            if missing:
                raise ValueError(f"Missing required keys: {sorted(missing)}")

        return self

    def all_declared_headers(self) -> set[str]:
        headers = (
            set(self.required.values())
            | set(self.optional.values())
            | set(self.extras.values())
        )
        return {h for h in headers if h}

    def all_internal_keys(self) -> set[str]:
        return set(self.required.keys()) | set(self.optional.keys())

    def validate_basic(self) -> None:
        # compatibility with your old API
        type(self).model_validate(self.model_dump())
