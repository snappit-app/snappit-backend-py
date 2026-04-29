from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PaddleWebhookEventCreate(BaseModel):
    model_config = ConfigDict(extra="allow")

    event_id: str
    event_type: str
    notification_id: str = Field(alias="notification_id")
    occurred_at: datetime
    data: dict[str, Any] = Field(default_factory=dict)


class PaddleWebhookEventRead(BaseModel):
    model_config = ConfigDict(extra="allow")

    event_id: str
    event_type: str
    notification_id: str = Field(alias="notification_id")
    occurred_at: datetime
    data: dict[str, Any] = Field(default_factory=dict)
