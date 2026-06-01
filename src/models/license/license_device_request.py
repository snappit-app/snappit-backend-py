from pydantic import BaseModel


class DeviceRequest(BaseModel):
    code: str
    device_id: str
