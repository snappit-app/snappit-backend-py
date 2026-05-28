from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PaddleEventData(BaseModel):
    model_config = ConfigDict(extra="ignore")
    customer_id: str | None = None


class PaddleTransactionData(BaseModel):
    model_config = ConfigDict(extra="ignore")
    customer_id: str


class PaddleWebhookEventCreate(BaseModel):
    event_id: str
    event_type: str
    notification_id: str
    occurred_at: datetime
    data: PaddleEventData


class PaddleWebhookEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_id: str
    event_type: str
    notification_id: str
    occurred_at: datetime
    payload: PaddleWebhookEventCreate
