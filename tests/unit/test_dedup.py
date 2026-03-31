"""
VyapaarBandhu — Invoice Deduplication Hash Tests
"""

import uuid

import pytest

from app.utils.dedup import compute_dedup_hash


class TestDedupHash:
    def test_same_inputs_same_hash(self):
        cid = uuid.uuid4()
        h1 = compute_dedup_hash("27AAPFU0939F1ZV", "INV001", cid)
        h2 = compute_dedup_hash("27AAPFU0939F1ZV", "INV001", cid)
        assert h1 == h2

    def test_different_invoice_different_hash(self):
        cid = uuid.uuid4()
        h1 = compute_dedup_hash("27AAPFU0939F1ZV", "INV001", cid)
        h2 = compute_dedup_hash("27AAPFU0939F1ZV", "INV002", cid)
        assert h1 != h2

    def test_different_client_different_hash(self):
        h1 = compute_dedup_hash("27AAPFU0939F1ZV", "INV001", uuid.uuid4())
        h2 = compute_dedup_hash("27AAPFU0939F1ZV", "INV001", uuid.uuid4())
        assert h1 != h2

    def test_case_insensitive_gstin(self):
        cid = uuid.uuid4()
        h1 = compute_dedup_hash("27aapfu0939f1zv", "INV001", cid)
        h2 = compute_dedup_hash("27AAPFU0939F1ZV", "INV001", cid)
        assert h1 == h2

    def test_none_gstin_handled(self):
        cid = uuid.uuid4()
        h = compute_dedup_hash(None, "INV001", cid)
        assert len(h) == 64  # SHA-256 hex

    def test_none_invoice_number_handled(self):
        cid = uuid.uuid4()
        h = compute_dedup_hash("27AAPFU0939F1ZV", None, cid)
        assert len(h) == 64

    def test_hash_is_64_hex_chars(self):
        h = compute_dedup_hash("27AAPFU0939F1ZV", "INV001", uuid.uuid4())
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)

    def test_whitespace_stripped(self):
        cid = uuid.uuid4()
        h1 = compute_dedup_hash("  27AAPFU0939F1ZV  ", "  INV001  ", cid)
        h2 = compute_dedup_hash("27AAPFU0939F1ZV", "INV001", cid)
        assert h1 == h2
