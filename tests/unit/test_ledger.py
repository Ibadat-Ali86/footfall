"""Unit tests for the Call Ledger and Tamper Evidence (Section 11).

Follows AGENTS.md:
- Tests first
- Proves tamper-evident hash chaining (SHA-256 prev_hash link)
- Proves append-only property with supersedes support
- Proves canonical JSON encoding invariance
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from footfall.ledger.chain import (
    CallLedger,
    compute_record_hash,
)


@pytest.mark.unit
def test_canonical_record_hash_deterministic() -> None:
    """Section 11.2: record_hash = SHA256(prev_hash || canonical_json(row_without_hashes))."""
    prev_hash = "0" * 64
    payload = {
        "call_id": "test:call:1",
        "entity_id": "fast-agent",
        "category": "agent-framework",
        "as_of": "2026-06-01",
        "phase": "breakout",
        "p_breakout_30d": 0.85,
        "method_version": "m1.0",
        "features_hash": "a" * 64,
        "supersedes": None,
        "timestamp": "2026-06-01T06:00:00Z",
    }

    hash1 = compute_record_hash(prev_hash, payload)
    hash2 = compute_record_hash(prev_hash, payload)

    assert len(hash1) == 64
    assert hash1 == hash2


@pytest.mark.unit
def test_hash_chain_tamper_detection(tmp_path: Path) -> None:
    """Section 11.2: Any tampering with a row invalidates the chain from that row forward."""
    ledger_file = tmp_path / "calls.jsonl"
    ledger = CallLedger(ledger_path=ledger_file)

    # Append 3 valid calls
    ledger.append_call(
        entity_id="entity-1",
        category="agent-framework",
        as_of="2026-06-01",
        phase="emerging",
        p_breakout_30d=0.2,
        method_version="m1.0",
        features_hash="1" * 64,
    )

    ledger.append_call(
        entity_id="entity-2",
        category="llm-sdk",
        as_of="2026-06-01",
        phase="breakout",
        p_breakout_30d=0.88,
        method_version="m1.0",
        features_hash="2" * 64,
    )

    ledger.append_call(
        entity_id="entity-3",
        category="vector-store",
        as_of="2026-06-01",
        phase="mainstream",
        p_breakout_30d=None,
        method_version="m1.0",
        features_hash="3" * 64,
    )

    # Chain must be valid initially
    calls = ledger.load_calls()
    assert len(calls) == 3
    is_valid, err = CallLedger.verify_chain(calls)
    assert is_valid is True
    assert err is None

    # Tamper with call 2 in file (change phase from breakout to plateau)
    lines = ledger_file.read_text(encoding="utf-8").strip().split("\n")
    row2 = json.loads(lines[1])
    row2["phase"] = "plateau"
    lines[1] = json.dumps(row2)
    ledger_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

    # Reload and verify tampering is detected
    tampered_calls = ledger.load_calls()
    is_valid_tampered, err_tampered = CallLedger.verify_chain(tampered_calls)
    assert is_valid_tampered is False
    assert err_tampered is not None
    assert "Hash mismatch at index 1" in err_tampered


@pytest.mark.unit
def test_supersedes_creates_new_row_without_editing(tmp_path: Path) -> None:
    """Section 11.2: Never edit or delete a row; a correction is a new row with 'supersedes'."""
    ledger_file = tmp_path / "calls.jsonl"
    ledger = CallLedger(ledger_path=ledger_file)

    orig_call = ledger.append_call(
        entity_id="pkg-err",
        category="mcp-server",
        as_of="2026-06-01",
        phase="emerging",
        p_breakout_30d=0.3,
        method_version="m1.0",
        features_hash="e" * 64,
    )

    # Correction row
    ledger.append_call(
        entity_id="pkg-err",
        category="mcp-server",
        as_of="2026-06-01",
        phase="breakout",
        p_breakout_30d=0.8,
        method_version="m1.0",
        features_hash="f" * 64,
        supersedes=orig_call.call_id,
    )

    calls = ledger.load_calls()
    assert len(calls) == 2
    assert calls[1].supersedes == orig_call.call_id
    assert calls[1].prev_hash == orig_call.record_hash

    is_valid, err = CallLedger.verify_chain(calls)
    assert is_valid is True
    assert err is None
