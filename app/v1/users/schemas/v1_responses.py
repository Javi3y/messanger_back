from app.schemas.base import AbstractBaseModel


class V1LoginResponse(AbstractBaseModel):
    access_token: str
    token_type: str = "bearer"


class V1BaseUserResponse(AbstractBaseModel):
    id: int
    username: str
    first_name: str
    sur_name: str
    phone_number: str
