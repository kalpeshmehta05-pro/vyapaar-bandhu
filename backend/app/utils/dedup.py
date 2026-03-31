"""
VyapaarBandhu — Invoice Deduplication
SHA-256 hash of (seller_gstin + invoice_number + client_id) prevents duplicate invoices.
"""

import hashlib
import uuid


def compute_dedup_hash(
    seller_gstin: str | None,
    invoice_number: str | None,
    client_id: uuid.UUID,
) -> str:
    """
    Compute deterministic deduplication hash for an invoice.
    Uses SHA-256 of normalised (seller_gstin || invoice_number || client_id).

    Normalisation:
    - GSTIN uppercased, whitespace stripped
    - Invoice number uppercased, whitespace stripped
    - Client ID as lowercase hex string

    Returns 64-char hex string.
    """
    gstin = (seller_gstin or "UNKNOWN").upper().strip()
    inv_no = (invoice_number or "UNKNOWN").upper().strip()
    cid = str(client_id).lower()

    payload = f"{gstin}|{inv_no}|{cid}"
    return hashlib.sha256(payload.encode()).hexdigest()
