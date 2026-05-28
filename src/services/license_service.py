import asyncio
import hashlib
import hmac
import secrets

from paddle_billing.Notifications.Entities.Transaction import Transaction
from sqlalchemy.ext.asyncio import AsyncSession

from core.paddle_client import get_paddle_client
from core.settings import get_settings
from models import PaddleWebhookEvent
from models.license.license_orm import License

# Crockford-like base32 alphabet without ambiguous chars (0/O, 1/I/L)
_CODE_ALPHABET = "ABCDEFGHJKMNPQRSTVWXYZ23456789"


async def create_license(session: AsyncSession, event: PaddleWebhookEvent):
    transaction = Transaction.from_dict(event.payload.get("data", {}))

    if not transaction.customer_id:
        raise ValueError(f"Transaction {transaction.id} has no customer_id")

    paddle = get_paddle_client()
    customer = await asyncio.to_thread(paddle.customers.get, transaction.customer_id)

    code = generate_activation_code()
    license = License(
        activation_code_hash=hash_activation_code(code),
        activation_code_last4=code[-4:],
        email=customer.email,
        paddle_event_id=event.id,
        paddle_customer_id=transaction.customer_id,
        last_paddle_event_at=event.occurred_at,
    )
    session.add(license)
    return code


def generate_activation_code() -> str:
    raw = "".join(secrets.choice(_CODE_ALPHABET) for _ in range(20))
    return "-".join(raw[i : i + 5] for i in range(0, len(raw), 5))


def hash_activation_code(code: str) -> str:
    secret = get_settings().license_secret_key
    return hmac.new(secret.encode(), code.encode(), hashlib.sha256).hexdigest()


def activate_license(code):
    return


def deactivate_license(code):
    return


def validate_license(code):
    return
