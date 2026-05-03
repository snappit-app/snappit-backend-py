from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PaddleWebhookEventCreate(BaseModel):
    event_id: str
    event_type: str
    notification_id: str
    occurred_at: datetime


class PaddleWebhookEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_id: str
    event_type: str
    notification_id: str
    occurred_at: datetime
    payload: dict[str, Any] = Field(default_factory=dict)
