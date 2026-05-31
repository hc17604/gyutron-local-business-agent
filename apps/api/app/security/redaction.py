import re


EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE_RE = re.compile(r"(?<!\d)(?:\+?\d[\d\s().-]{7,}\d)(?!\d)")
AMOUNT_RE = re.compile(r"(?<!\w)(?:USD|US\$|\$|EUR|€|RMB|CNY)?\s?\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?(?!\w)")


def redact_text(text: str, policy: dict | None = None) -> str:
    policy = policy or {}
    redacted = text
    if policy.get("mask_customer_email", True):
        redacted = EMAIL_RE.sub("[email_masked]", redacted)
    if policy.get("mask_phone_number", True):
        redacted = PHONE_RE.sub("[phone_masked]", redacted)
    if policy.get("mask_amount", False):
        redacted = AMOUNT_RE.sub("[amount_masked]", redacted)
    if policy.get("mask_customer_name", False):
        redacted = re.sub(r"\b(?:Customer|Client|Buyer):\s*[A-Za-z0-9 ._-]+", "Customer: [name_masked]", redacted)
    if policy.get("mask_address", False):
        redacted = re.sub(r"\bAddress:\s*.+", "Address: [address_masked]", redacted)
    return redacted
