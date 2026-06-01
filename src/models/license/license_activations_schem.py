from datetime import datetime

from pydantic import BaseModel, ConfigDict


class LicenseActivationCreate(BaseModel):
    license_id: int
    device_id: str


class LicenseActivationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    license_id: int
    device_id: str
    activated_at: datetime
    deactivated_at: datetime | None
