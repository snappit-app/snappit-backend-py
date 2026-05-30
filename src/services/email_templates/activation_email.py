from pathlib import Path

DOWNLOADS_URL = "https://getsnappit.com/downloads"

_TEMPLATE_PATH = Path(__file__).with_name("activation_email.html")


def build_activation_email_html(activation_code: str) -> str:
    template = _TEMPLATE_PATH.read_text(encoding="utf-8")
    return template.replace("{{activation_code}}", activation_code).replace(
        "{{downloads_url}}", DOWNLOADS_URL
    )
