import asyncio

from paddle_billing.Notifications.Entities.Transaction import Transaction
from sqlalchemy.ext.asyncio import AsyncSession

from core.paddle_client import get_paddle_client
from models import PaddleWebhookEvent
from models.license.license_orm import License


async def create_license(session: AsyncSession, event: PaddleWebhookEvent):
    transaction = Transaction.from_dict(event.payload.get("data", {}))

    if not transaction.customer_id:
        raise ValueError(f"Transaction {transaction.id} has no customer_id")

    paddle = get_paddle_client()
    customer = await asyncio.to_thread(paddle.customers.get, transaction.customer_id)

    license = License(
        activation_code_hash="asd",
        activation_code_last4=123,
        email=customer.email,
        paddle_event_id=event.id,
        paddle_customer_id=transaction.customer_id,
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
