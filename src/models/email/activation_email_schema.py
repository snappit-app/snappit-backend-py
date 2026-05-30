from pydantic import BaseModel, EmailStr


class ActivationEmailRequest(BaseModel):
    to: EmailStr
    activation_code: str
