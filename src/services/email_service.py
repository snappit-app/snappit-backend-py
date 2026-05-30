import resend
from loguru import logger
from resend.exceptions import InvalidApiKeyError, RateLimitError, ResendError

from core.settings import get_settings
from models.email.activation_email_schema import ActivationEmailRequest
from services.email_templates.activation_email import build_activation_email_html


async def send_activation_email(schema: ActivationEmailRequest) -> None:
    settings = get_settings()
    try:
        await resend.Emails.send_async(
            {
                "from": settings.email_from,
                "to": schema.to,
                "subject": "Your Snappit activation code",
                "html": build_activation_email_html(schema.activation_code),
            }
        )
    except InvalidApiKeyError:
        logger.exception("Resend: invalid API key")
        raise
    except RateLimitError as e:
        logger.warning(f"Resend rate limit exceeded: {e.message}")
        raise
    except ResendError as e:
        logger.exception(f"Resend error [{e.code}]: {e.message}")
        raise
