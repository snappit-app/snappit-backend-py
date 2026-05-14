from sqlalchemy.ext.asyncio import AsyncSession

from models import PaddleWebhookEvent
from models.license.license_orm import License


async def create_license(session: AsyncSession, event: PaddleWebhookEvent):

    license = License(
        activation_code_hash="asd",
        activation_code_last4=123,
        email="mail@gmail.com",
        paddle_event_id=event.id,
        paddle_customer_id="123",
        last_paddle_event_at=event.processed_at,
    )
    session.add(license)
    return


def generate_activation_code():
    return


def activate_license(code):
    return


def deactivate_license(code):
    return


def validate_license(code):
    return
