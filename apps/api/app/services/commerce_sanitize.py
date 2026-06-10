"""Commerce raw_payload sanitizer — privacy gate for everything entering the
commerce store (Phase 4 hard rule).

NEVER persisted: card numbers / payment credentials / third-party access
tokens / full street addresses / waybill PII. Normalized columns keep only the
minimum the reports need (country, email for merge, amounts, statuses).
"""
import re


# Keys dropped wherever they appear (case-insensitive substring match).
DENY_KEY_PARTS = (
    "card", "cvv", "cvc", "pan", "securitycode", "security_code",
    "token", "secret", "password", "credential", "authorization", "api_key", "apikey",
    "address1", "address2", "street", "address_line", "shipping_address", "billing_address",
    "phone", "fax", "ssn", "tax_id", "vat_number", "passport",
    "tracking_url", "label_url", "waybill", "signature",
)

# Card-like digit runs (13-19 digits, spaces/dashes allowed) → masked.
CARD_LIKE = re.compile(r"\b(?:\d[ -]?){13,19}\b")
# Long opaque secrets (40+ word chars) → masked.
LONG_TOKEN = re.compile(r"\b[A-Za-z0-9_\-]{40,}\b")

MAX_DEPTH = 6
MAX_STRING = 2000


def _deny_key(key: str) -> bool:
    lowered = key.lower()
    return any(part in lowered for part in DENY_KEY_PARTS)


def _clean_string(value: str) -> str:
    value = CARD_LIKE.sub("[redacted-number]", value)
    value = LONG_TOKEN.sub("[redacted-token]", value)
    if len(value) > MAX_STRING:
        value = value[:MAX_STRING] + "…[truncated]"
    return value


def sanitize_payload(value, depth: int = 0):
    """Recursively sanitize a parsed JSON value for storage in raw_payload."""
    if depth > MAX_DEPTH:
        return "[max-depth]"
    if isinstance(value, dict):
        return {k: sanitize_payload(v, depth + 1) for k, v in value.items() if not _deny_key(str(k))}
    if isinstance(value, list):
        return [sanitize_payload(v, depth + 1) for v in value[:200]]
    if isinstance(value, str):
        return _clean_string(value)
    return value
