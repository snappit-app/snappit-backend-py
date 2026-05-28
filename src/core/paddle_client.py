from functools import lru_cache

from paddle_billing import Client, Environment, Options

from core.logger import logger
from core.settings import get_settings


@lru_cache
def get_paddle_client() -> Client:
    settings = get_settings()
    env = (
        Environment.SANDBOX
        if settings.paddle_env == "sandbox"
        else Environment.PRODUCTION
    )

    logger.info(settings.paddle_api_key)

    logger.info(env)
    return Client(
        settings.paddle_api_key,
        options=Options(env),
    )
