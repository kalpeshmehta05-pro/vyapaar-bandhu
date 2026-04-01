"""
Tests for audit log hash chain and race condition fix.
"""

import hashlib
import json
import pytest


GENESIS_HASH = "0000000000000000000000000000000000000000000000000000000000000000"


def _compute_row_hash(prev_id, prev_hash, event_data):
    """Mirror of the function from app.utils.audit -- avoids importing models."""
    payload = f"{prev_id or 0}|{prev_hash}|{json.dumps(event_data, sort_keys=True, default=str)}"
    return hashlib.sha256(payload.encode()).hexdigest()


class TestAuditHashChain:
    """Tests for audit log hash chain computation."""

    def test_genesis_hash_is_64_zeros(self):
        assert len(GENESIS_HASH) == 64
        assert all(c == "0" for c in GENESIS_HASH)

    def test_compute_row_hash_deterministic(self):
        event_data = {
            "actor_type": "ca",
            "action": "invoice.approved",
            "actor_id": "test-uuid",
            "entity_type": "invoice",
            "entity_id": "inv-uuid",
            "old_value": None,
            "new_value": {"status": "approved"},
        }
        hash1 = _compute_row_hash(1, GENESIS_HASH, event_data)
        hash2 = _compute_row_hash(1, GENESIS_HASH, event_data)
        assert hash1 == hash2

    def test_compute_row_hash_is_sha256(self):
        event_data = {"action": "test"}
        result = _compute_row_hash(None, GENESIS_HASH, event_data)
        assert len(result) == 64  # SHA-256 hex digest
        assert all(c in "0123456789abcdef" for c in result)

    def test_different_prev_hash_produces_different_row_hash(self):
        event_data = {"action": "test"}
        hash1 = _compute_row_hash(1, GENESIS_HASH, event_data)
        hash2 = _compute_row_hash(1, "a" * 64, event_data)
        assert hash1 != hash2

    def test_different_prev_id_produces_different_row_hash(self):
        event_data = {"action": "test"}
        hash1 = _compute_row_hash(1, GENESIS_HASH, event_data)
        hash2 = _compute_row_hash(2, GENESIS_HASH, event_data)
        assert hash1 != hash2

    def test_different_event_data_produces_different_row_hash(self):
        hash1 = _compute_row_hash(1, GENESIS_HASH, {"action": "login"})
        hash2 = _compute_row_hash(1, GENESIS_HASH, {"action": "logout"})
        assert hash1 != hash2

    def test_chain_continuity(self):
        """Simulate a 3-row chain and verify each link."""
        prev_id = None
        prev_hash = GENESIS_HASH

        events = [
            {"action": "ca.registered"},
            {"action": "client.created"},
            {"action": "invoice.uploaded"},
        ]

        hashes = []
        for i, event in enumerate(events):
            row_hash = _compute_row_hash(prev_id, prev_hash, event)
            hashes.append(row_hash)
            prev_id = i + 1
            prev_hash = row_hash

        # All hashes should be unique
        assert len(set(hashes)) == 3

        # Verify chain by recomputing
        prev_id = None
        prev_hash = GENESIS_HASH
        for i, event in enumerate(events):
            expected = _compute_row_hash(prev_id, prev_hash, event)
            assert expected == hashes[i]
            prev_id = i + 1
            prev_hash = hashes[i]

    def test_for_update_in_write_audit_log(self):
        """Verify that the audit write function source uses FOR UPDATE."""
        import pathlib

        audit_path = pathlib.Path(__file__).resolve().parent.parent.parent / "backend" / "app" / "utils" / "audit.py"
        source = audit_path.read_text()
        assert "with_for_update" in source, (
            "write_audit_log must use .with_for_update() to prevent race conditions"
        )

    def test_tampered_row_detected(self):
        """Verify that modifying event data breaks chain verification."""
        events = [
            {"action": "ca.registered"},
            {"action": "client.created"},
        ]

        # Build chain
        prev_id = None
        prev_hash = GENESIS_HASH
        chain = []

        for i, event in enumerate(events):
            row_hash = _compute_row_hash(prev_id, prev_hash, event)
            chain.append({"prev_id": prev_id, "prev_hash": prev_hash, "event": event, "row_hash": row_hash})
            prev_id = i + 1
            prev_hash = row_hash

        # Tamper with second row's event
        chain[1]["event"] = {"action": "TAMPERED"}

        # Verify chain detects tampering
        prev_id = None
        prev_hash = GENESIS_HASH
        broken = False
        for i, row in enumerate(chain):
            expected = _compute_row_hash(prev_id, prev_hash, row["event"])
            if expected != row["row_hash"]:
                broken = True
                break
            prev_id = i + 1
            prev_hash = row["row_hash"]

        assert broken, "Tampered row should be detected"
