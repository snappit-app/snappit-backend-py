from pydantic import BaseModel, EmailStr


class PaddleWebhookData(BaseModel):
    event_id: str
    customer_id: str
    email: EmailStr
