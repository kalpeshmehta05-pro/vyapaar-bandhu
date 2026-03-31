"""
VyapaarBandhu — Post-OCR Field Extraction
Regex + heuristics to parse 9 required fields from raw OCR text.
"""

import re
from dataclasses import dataclass
from datetime import date

import structlog

logger = structlog.get_logger()


@dataclass
class ExtractedFields:
    seller_gstin: str | None = None
    seller_name: str | None = None
    invoice_number: str | None = None
    invoice_date: str | None = None  # DD-MM-YYYY string
    taxable_amount: float | None = None
    cgst_amount: float | None = None
    sgst_amount: float | None = None
    igst_amount: float | None = None
    total_amount: float | None = None
    product_description: str | None = None
    gstin_was_autocorrected: bool = False
    gstin_original_ocr: str | None = None
    fields_extracted_count: int = 0


# ── GSTIN pattern ─────────────────────────────────────────────────────
GSTIN_RE = re.compile(r"\b(\d{2}[A-Z]{5}\d{4}[A-Z][A-Z0-9]Z[A-Z0-9])\b", re.IGNORECASE)

# ── Invoice number patterns ───────────────────────────────────────────
INVOICE_NO_PATTERNS = [
    re.compile(r"(?:invoice|inv|bill)\s*(?:no|number|#|num)[\s.:]*([A-Z0-9/\-]{3,30})", re.IGNORECASE),
    re.compile(r"(?:invoice|inv)\s*[.:]\s*([A-Z0-9/\-]{3,30})", re.IGNORECASE),
    re.compile(r"(?:bill|receipt)\s*(?:no|#)[\s.:]*([A-Z0-9/\-]{3,30})", re.IGNORECASE),
]

# ── Date patterns ─────────────────────────────────────────────────────
DATE_PATTERNS = [
    # DD-MM-YYYY, DD/MM/YYYY, DD.MM.YYYY
    re.compile(r"(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{4})"),
    # YYYY-MM-DD
    re.compile(r"(\d{4})[/\-.](\d{1,2})[/\-.](\d{1,2})"),
]

# ── Amount patterns ───────────────────────────────────────────────────
AMOUNT_RE = re.compile(r"[\d,]+\.?\d*")

TAXABLE_KEYWORDS = ["taxable", "assessable", "base amount", "sub total", "subtotal"]
CGST_KEYWORDS = ["cgst", "c.g.s.t", "central gst", "central tax"]
SGST_KEYWORDS = ["sgst", "s.g.s.t", "state gst", "state tax"]
IGST_KEYWORDS = ["igst", "i.g.s.t", "integrated gst", "integrated tax"]
TOTAL_KEYWORDS = ["total", "grand total", "net amount", "amount payable", "invoice total"]


def extract_fields_from_raw(text: str) -> ExtractedFields:
    """
    Extract 9 invoice fields from raw OCR text using regex + heuristics.
    This is deterministic — no AI involved.
    """
    fields = ExtractedFields()
    lines = text.split("\n")
    text_lower = text.lower()

    # 1. GSTIN
    gstin_match = GSTIN_RE.search(text)
    if gstin_match:
        fields.seller_gstin = gstin_match.group(1).upper()

    # 2. Invoice number
    for pattern in INVOICE_NO_PATTERNS:
        match = pattern.search(text)
        if match:
            fields.invoice_number = match.group(1).strip()
            break

    # 3. Date
    fields.invoice_date = _extract_date(text)

    # 4. Seller name — heuristic: line after/near GSTIN, or first non-empty line
    fields.seller_name = _extract_seller_name(lines, fields.seller_gstin)

    # 5-8. Tax amounts
    fields.taxable_amount = _extract_amount(lines, TAXABLE_KEYWORDS)
    fields.cgst_amount = _extract_amount(lines, CGST_KEYWORDS)
    fields.sgst_amount = _extract_amount(lines, SGST_KEYWORDS)
    fields.igst_amount = _extract_amount(lines, IGST_KEYWORDS)

    # 9. Total amount
    fields.total_amount = _extract_amount(lines, TOTAL_KEYWORDS)

    # 10. Product description — heuristic: longest non-header line with product-like content
    fields.product_description = _extract_description(lines)

    # Count extracted fields
    count = sum(1 for v in [
        fields.seller_gstin, fields.seller_name, fields.invoice_number,
        fields.invoice_date, fields.taxable_amount, fields.cgst_amount,
        fields.sgst_amount, fields.igst_amount, fields.total_amount,
    ] if v is not None)
    fields.fields_extracted_count = count

    logger.info("ocr.fields.extracted", count=count)
    return fields


def _extract_date(text: str) -> str | None:
    """Extract date from OCR text. Returns DD-MM-YYYY format."""
    # Look for date near keywords first
    date_keywords = ["date", "dated", "invoice date", "bill date"]
    lines = text.split("\n")

    for line in lines:
        line_lower = line.lower()
        if any(kw in line_lower for kw in date_keywords):
            for pattern in DATE_PATTERNS:
                match = pattern.search(line)
                if match:
                    return _normalize_date(match)

    # Fallback: find any date in text
    for pattern in DATE_PATTERNS:
        match = pattern.search(text)
        if match:
            return _normalize_date(match)

    return None


def _normalize_date(match: re.Match) -> str:
    """Normalize matched date to DD-MM-YYYY."""
    groups = match.groups()
    if len(groups[0]) == 4:
        # YYYY-MM-DD format
        return f"{groups[2].zfill(2)}-{groups[1].zfill(2)}-{groups[0]}"
    else:
        # DD-MM-YYYY format
        return f"{groups[0].zfill(2)}-{groups[1].zfill(2)}-{groups[2]}"


def _extract_amount(lines: list[str], keywords: list[str]) -> float | None:
    """Extract an amount from lines matching keywords."""
    for line in lines:
        line_lower = line.lower()
        if any(kw in line_lower for kw in keywords):
            amounts = AMOUNT_RE.findall(line)
            if amounts:
                # Take the last amount on the line (usually the value)
                try:
                    val = float(amounts[-1].replace(",", ""))
                    if val > 0:
                        return val
                except ValueError:
                    continue
    return None


def _extract_seller_name(lines: list[str], gstin: str | None) -> str | None:
    """Extract seller name — usually near the top or near GSTIN."""
    # Skip common header words
    skip_words = {"tax invoice", "invoice", "bill", "receipt", "gstin", "date", "original"}

    for line in lines[:10]:  # Check first 10 lines
        clean = line.strip()
        if len(clean) < 3 or len(clean) > 100:
            continue
        if clean.lower() in skip_words:
            continue
        if GSTIN_RE.search(clean):
            continue
        if re.match(r"^[\d/\-.:]+$", clean):
            continue
        # Likely a business name
        if any(c.isalpha() for c in clean):
            return clean[:100]

    return None


def _extract_description(lines: list[str]) -> str | None:
    """Extract product/service description from invoice lines."""
    skip_words = {
        "invoice", "bill", "gstin", "date", "total", "cgst", "sgst",
        "igst", "tax", "amount", "subtotal", "grand", "receipt",
    }

    candidates = []
    for line in lines:
        clean = line.strip()
        if len(clean) < 5 or len(clean) > 200:
            continue
        lower = clean.lower()
        if any(sw in lower for sw in skip_words):
            continue
        if GSTIN_RE.search(clean):
            continue
        if re.match(r"^[\d,.\s]+$", clean):
            continue
        candidates.append(clean)

    if candidates:
        # Return the longest candidate (likely the product description)
        return max(candidates, key=len)[:200]

    return None
