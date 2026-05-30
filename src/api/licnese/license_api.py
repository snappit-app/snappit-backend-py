from fastapi import APIRouter
from sqlalchemy import select

from core.database import session
from models import License
from models.email.activation_email_schema import ActivationEmailRequest
from services import email_service

license_router = APIRouter(prefix="/license", tags=["license"])


@license_router.get("/get_license")
async def get_license(session: session):
    stmt = select(License)
    result = await session.execute(stmt)
    licenses = result.scalars().all()
    return licenses


@license_router.get("/send_email")
async def send_email():
    return await email_service.send_activation_email(
        ActivationEmailRequest(
            to="pinkcolorrrs@gmail.com", activation_code="ACM5E-D6ENS-GRWPJ-WQZQ3"
        )
    )
