import asyncio
import hashlib
import hmac
import secrets
from datetime import UTC, datetime

from fastapi import HTTPException, status
from loguru import logger
from paddle_billing.Notifications.Entities.Transaction import Transaction
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.paddle_client import get_paddle_client
from core.settings import get_settings
from models import PaddleWebhookEvent
from models.license.license_activations_orm import LicenseActivation
from models.license.license_activations_schem import LicenseActivationCreate
from models.license.license_orm import License, LicenseStatus

# Crockford-like base32 alphabet without ambiguous chars (0/O, 1/I/L)
_CODE_ALPHABET = "ABCDEFGHJKMNPQRSTVWXYZ23456789"


def _generate_activation_code() -> str:
    raw = "".join(secrets.choice(_CODE_ALPHABET) for _ in range(20))
    return "-".join(raw[i : i + 5] for i in range(0, len(raw), 5))


def _hash_activation_code(code: str) -> str:
    secret = get_settings().license_secret_key
    return hmac.new(secret.encode(), code.encode(), hashlib.sha256).hexdigest()


async def create_license(
    session: AsyncSession, event: PaddleWebhookEvent
) -> tuple[License, str]:
    transaction = Transaction.from_dict(event.payload.get("data", {}))

    if not transaction.customer_id:
        raise ValueError(f"Transaction {transaction.id} has no customer_id")

    paddle = get_paddle_client()
    customer = await asyncio.to_thread(paddle.customers.get, transaction.customer_id)

    code = _generate_activation_code()
    license = License(
        activation_code_hash=_hash_activation_code(code),
        activation_code_last4=code[-4:],
        email=customer.email,
        paddle_event_id=event.id,
        paddle_customer_id=transaction.customer_id,
        last_paddle_event_at=event.occurred_at,
    )
    session.add(license)
    return license, code


async def activate_device(
    session: AsyncSession, code: str, device_id: str
) -> LicenseActivation:
    license = await get_license(session, code)

    if license.status != LicenseStatus.ACTIVE:
        raise HTTPException(
            status_code=400, detail=f"license {code} is {license.status}"
        )

    active_count = sum(1 for a in license.activations if a.deactivated_at is None)
    if active_count >= license.max_activations:
        raise HTTPException(
            status_code=400,
            detail=f"license {code} has exceeded the maximum number of activations",
        )

    try:
        payload = LicenseActivationCreate(license_id=license.id, device_id=device_id)
    except ValidationError as exc:
        logger.warning("License activation: invalid payload: {}", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid license activation payload",
        ) from exc

    activation = LicenseActivation(
        license_id=payload.license_id,
        device_id=payload.device_id,
        license=license,
    )
    session.add(activation)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        logger.exception("Device already activated")
    return activation


async def deactivate_device(session: AsyncSession, code: str, device_id: str) -> None:
    license = await get_license(session, code)
    result = await session.execute(
        select(LicenseActivation).where(
            LicenseActivation.license_id == license.id,
            LicenseActivation.device_id == device_id,
            LicenseActivation.deactivated_at.is_(None),
        )
    )
    activation = result.scalar_one_or_none()
    if activation is None:
        raise HTTPException(status_code=404, detail="Active activation not found")

    activation.deactivated_at = datetime.now(UTC)
    await session.commit()
    return


async def validate_device(session: AsyncSession, code: str, device_id: str) -> bool:
    license = await get_license(session, code)

    if license.status != LicenseStatus.ACTIVE:
        return False

    result = await session.execute(
        select(LicenseActivation).where(
            LicenseActivation.license_id == license.id,
            LicenseActivation.device_id == device_id,
            LicenseActivation.deactivated_at.is_(None),
        )
    )
    return result.scalar_one_or_none() is not None


async def get_license(session: AsyncSession, code: str) -> License:
    code_hash = _hash_activation_code(code)
    result = await session.execute(
        select(License)
        .where(License.activation_code_hash == code_hash)
        .options(selectinload(License.activations))
    )
    license = result.scalar_one_or_none()
    if license is None:
        raise HTTPException(status_code=404, detail=f"license {code} not found")
    return license
