from typing import Any

from pydantic import BaseModel, ConfigDict
from src.base.domain.dto import BaseDTO


class AbstractBaseModel(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    def model_dump(
        self,
        *,
        mode: str = "json",
        include: Any = None,
        exclude: Any = None,
        context: Any = None,
        by_alias: bool = False,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
        round_trip: bool = False,
        warnings: bool = True,
    ) -> dict[str, Any]:
        # Get the default dump from Pydantic
        data = super().model_dump(
            mode=mode,
            include=include,
            exclude=exclude,
            context=context,
            by_alias=by_alias,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
            round_trip=round_trip,
            warnings=warnings,
        )

        return self._convert_dtos(data)

    def _convert_dtos(self, data: dict[str, Any]) -> dict[str, Any]:
        result = {}
        for key, value in data.items():
            if isinstance(value, BaseDTO):
                result[key] = value.dump(mode="json", exclude_none=True)
            elif isinstance(value, dict):
                result[key] = self._convert_dtos(value)
            elif isinstance(value, list):
                if value and all(isinstance(item, BaseDTO) for item in value):
                    result[key] = BaseDTO.dump_list(
                        value, mode="json", exclude_none=True
                    )
                else:
                    result[key] = [
                        (
                            self._convert_dtos(item)
                            if isinstance(item, dict)
                            else (
                                item.dump(mode="json", exclude_none=True)
                                if isinstance(item, BaseDTO)
                                else item
                            )
                        )
                        for item in value
                    ]
            else:
                result[key] = value
        return result

    @classmethod
    def from_dto_list(cls, dtos: list[BaseDTO]) -> list["AbstractBaseModel"]:
        return [cls(**dto.dump(exclude_none=True)) for dto in dtos]
