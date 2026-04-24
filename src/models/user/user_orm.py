from datetime import datetime
from typing import ClassVar

from pydantic import BaseModel, ConfigDict, EmailStr


class UserCreate(BaseModel):
    first_name: str
    second_name: str
    third_name: str | None = None
    email: EmailStr


class UserUpdate(BaseModel):
    first_name: str | None = None
    second_name: str | None = None
    third_name: str | None = None
    email: EmailStr | None = None


class UserRead(BaseModel):
    id: int
    first_name: str
    email: EmailStr
    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)
    created_at: datetime
    updated_at: datetime
