"""Normalize phone numbers for OTP and user lookup (Ghana-focused)."""
import re
from typing import Optional


def normalize_phone(phone: Optional[str]) -> str:
    """Return a canonical phone string, or empty if input is blank."""
    if phone is None:
        return ""
    raw = str(phone).strip()
    if not raw:
        return ""

    digits = re.sub(r"\D", "", raw)

    if digits.startswith("233") and len(digits) >= 12:
        return f"+{digits[:12]}"

    if digits.startswith("0") and len(digits) == 10:
        return f"+233{digits[1:]}"

    if len(digits) == 9:
        return f"+233{digits}"

    if raw.startswith("+") and digits:
        return f"+{digits}"

    return digits or raw
