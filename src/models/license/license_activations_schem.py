from pydantic import BaseModel


class LicenseActivationCreate(BaseModel):
    license_id: int
    device_id: str
