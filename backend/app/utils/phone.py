"""
VyapaarBandhu — Phone Number Utilities
E.164 normalisation and PII masking for logs.
"""

import re


def normalize_phone(phone: str) -> str:
    """
    Normalise an Indian phone number to E.164 format (+91XXXXXXXXXX).

    Handles:
    - "9876543210"       -> "+919876543210"
    - "09876543210"      -> "+919876543210"
    - "+919876543210"    -> "+919876543210"
    - "91 9876 543 210"  -> "+919876543210"
    - "919876543210"     -> "+919876543210"
    """
    # Strip all non-digit characters except leading +
    cleaned = re.sub(r"[^\d+]", "", phone.strip())

    # Remove leading +
    if cleaned.startswith("+"):
        cleaned = cleaned[1:]

    # Remove leading 0 (trunk prefix)
    if cleaned.startswith("0"):
        cleaned = cleaned[1:]

    # If starts with 91 and has 12 digits, it already has country code
    if cleaned.startswith("91") and len(cleaned) == 12:
        return f"+{cleaned}"

    # If 10 digits, add +91
    if len(cleaned) == 10:
        return f"+91{cleaned}"

    # Fallback: return with + prefix
    return f"+{cleaned}"


def mask_phone(phone: str) -> str:
    """
    Mask a phone number for logging. PII protection under DPDP Act.

    "+919876543210" -> "+91XXXXX3210"
    """
    normalized = normalize_phone(phone)
    if len(normalized) >= 8:
        return normalized[:3] + "XXXXX" + normalized[-4:]
    return "XXXXX"


def mask_gstin(gstin: str) -> str:
    """
    Mask a GSTIN for logging. PII protection under DPDP Act.

    "27AAPFU0939F1ZV" -> "27XXXXX0939X1ZV"
    """
    if not gstin or len(gstin) < 15:
        return "XXXXXXXXXXXXXXX"
    return gstin[:2] + "XXXXX" + gstin[7:11] + "X" + gstin[12:]
