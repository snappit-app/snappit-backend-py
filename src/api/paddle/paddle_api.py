from fastapi import APIRouter, HTTPException, status
from fastapi.requests import Request
from paddle_billing.Notifications import Secret, Verifier

from services import paddle_service
from src.api.paddle._adapters import _PaddleRequest
from src.core.database import session
from src.core.settings import get_settings

paddle_router = APIRouter(prefix="/v1/paddle", tags=["paddle"])


@paddle_router.post("/webhook", status_code=status.HTTP_204_NO_CONTENT)
async def handle_paddle_webhook_event(request: Request, session: session):
    raw_body = await request.body()
    paddle_request = _PaddleRequest(
        body=raw_body,
        headers=request.headers,
    )
    secret = get_settings().paddle_secret_key
    integrity_check = Verifier().verify(paddle_request, Secret(secret))

    if not integrity_check:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Paddle signature",
        )

    return await paddle_service.create_webhook_event(session, raw_body)


@paddle_router.get("/webhook")
async def read_paddle_webhook_events(session: session):
    return await paddle_service.read_paddle_webhook_events(session)
