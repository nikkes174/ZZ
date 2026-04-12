import hmac
import hashlib
from urllib.parse import parse_qsl

from backend.exceptions import InvalidTelegramInitDataError


def validate_telegram_init_data(init_data: str, bot_token: str) -> dict:
    parsed_data = dict(parse_qsl(init_data))

    received_hash = parsed_data.pop("hash", None)
    if not received_hash:
        raise InvalidTelegramInitDataError()

    data_check_string = "\n".join(
        f"{k}={v}" for k, v in sorted(parsed_data.items())
    )

    secret_key = hmac.new(
        b"WebAppData",
        bot_token.encode(),
        hashlib.sha256,
    ).digest()

    calculated_hash = hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(calculated_hash, received_hash):
        raise InvalidTelegramInitDataError()

    return parsed_data
