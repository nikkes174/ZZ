from __future__ import annotations

from typing import Optional


IIKO_HOUSE_MAX_LENGTH = 10


class IikoDeliveryAddressValidationError(ValueError):
    """A delivery address cannot be accepted by iiko as submitted."""


def normalize_optional_text(value: object) -> Optional[str] | object:
    """Trim text while retaining the distinction between absent and required fields."""
    if not isinstance(value, str):
        return value
    normalized = value.strip()
    return normalized or None


def validate_iiko_delivery_address(*, street: Optional[str], house: Optional[str]) -> None:
    normalized_street = (street or "").strip()
    normalized_house = (house or "").strip()

    if not normalized_street:
        raise IikoDeliveryAddressValidationError("Укажите улицу доставки.")
    if not normalized_house:
        raise IikoDeliveryAddressValidationError("Укажите номер дома.")
    if len(normalized_house) > IIKO_HOUSE_MAX_LENGTH:
        raise IikoDeliveryAddressValidationError(
            "Номер дома слишком длинный. Укажите номер дома длиной не более 10 символов."
        )
    if not any(char.isalnum() for char in normalized_house):
        raise IikoDeliveryAddressValidationError("Проверьте номер дома.")
    if not any(char.isalnum() for char in normalized_street):
        raise IikoDeliveryAddressValidationError("Проверьте название улицы.")
