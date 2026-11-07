"""Tamper-evident append-only Call Ledger with hash chaining.

Implements Section 11 of docs/BUILD.md.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

GENESIS_PREV_HASH: str = "0" * 64


@dataclass(frozen=True)
class LedgerCall:
    """Represents a weekly evaluation call with tamper-evident cryptographic chaining."""

    call_id: str
    entity_id: str
    category: str
    as_of: str
    phase: str
    p_breakout_30d: float | None
    method_version: str
    features_hash: str
    prev_hash: str
    record_hash: str
    supersedes: str | None = None
    timestamp: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert call to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> LedgerCall:
        """Create LedgerCall from dictionary."""
        return cls(
            call_id=str(data["call_id"]),
            entity_id=str(data["entity_id"]),
            category=str(data["category"]),
            as_of=str(data["as_of"]),
            phase=str(data["phase"]),
            p_breakout_30d=(
                float(data["p_breakout_30d"]) if data.get("p_breakout_30d") is not None else None
            ),
            method_version=str(data["method_version"]),
            features_hash=str(data["features_hash"]),
            prev_hash=str(data["prev_hash"]),
            record_hash=str(data["record_hash"]),
            supersedes=str(data["supersedes"]) if data.get("supersedes") else None,
            timestamp=str(data.get("timestamp", "")),
        )


def compute_record_hash(prev_hash: str, payload_without_record_hash: dict[str, Any]) -> str:
    """Compute deterministic SHA-256 hash using canonical JSON encoding (Section 11.2).

    Formula: record_hash = SHA256(prev_hash || canonical_json(row_without_hashes))
    """
    clean_payload = {k: v for k, v in payload_without_record_hash.items() if k != "record_hash"}
    canonical_json = json.dumps(clean_payload, sort_keys=True, separators=(",", ":"))
    message = f"{prev_hash}||{canonical_json}".encode()
    return hashlib.sha256(message).hexdigest()


class CallLedger:
    """Append-only cryptographic call ledger backed by JSONL storage."""

    def __init__(self, ledger_path: Path | str) -> None:
        self.ledger_path = Path(ledger_path)
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        self._last_hash: str | None = None

    def load_calls(self) -> list[LedgerCall]:
        """Load all ledger calls from disk."""
        if not self.ledger_path.exists():
            return []

        calls: list[LedgerCall] = []
        with open(self.ledger_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    calls.append(LedgerCall.from_dict(json.loads(line)))
        if calls:
            self._last_hash = calls[-1].record_hash
        return calls

    def get_last_hash(self) -> str:
        """Get the record_hash of the most recent call, or GENESIS_PREV_HASH if empty."""
        if self._last_hash is not None:
            return self._last_hash
        calls = self.load_calls()
        if not calls:
            self._last_hash = GENESIS_PREV_HASH
            return GENESIS_PREV_HASH
        self._last_hash = calls[-1].record_hash
        return self._last_hash

    def append_call(
        self,
        entity_id: str,
        category: str,
        as_of: str,
        phase: str,
        method_version: str,
        features_hash: str,
        call_id: str | None = None,
        p_breakout_30d: float | None = None,
        supersedes: str | None = None,
        timestamp: str | None = None,
    ) -> LedgerCall:
        """Append a new call to the ledger with chain link and atomic write."""
        prev_hash = self.get_last_hash()
        resolved_call_id = call_id or f"call_{as_of}_{entity_id}"
        ts = timestamp or f"{as_of}T06:00:00Z"

        payload = {
            "call_id": resolved_call_id,
            "entity_id": entity_id,
            "category": category,
            "as_of": as_of,
            "phase": phase,
            "p_breakout_30d": p_breakout_30d,
            "method_version": method_version,
            "features_hash": features_hash,
            "prev_hash": prev_hash,
            "supersedes": supersedes,
            "timestamp": ts,
        }

        record_hash = compute_record_hash(prev_hash, payload)
        self._last_hash = record_hash

        call = LedgerCall(
            call_id=resolved_call_id,
            entity_id=entity_id,
            category=category,
            as_of=as_of,
            phase=phase,
            p_breakout_30d=p_breakout_30d,
            method_version=method_version,
            features_hash=features_hash,
            prev_hash=prev_hash,
            record_hash=record_hash,
            supersedes=supersedes,
            timestamp=ts,
        )

        # Append to JSONL file
        with open(self.ledger_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(call.to_dict()) + "\n")

        return call

    @staticmethod
    def verify_chain(calls: list[LedgerCall] | tuple[LedgerCall, ...]) -> tuple[bool, str | None]:
        """Verify unbroken cryptographic integrity of call sequence.

        Returns (True, None) if valid, or (False, error_message) if tampered.
        """
        if not calls:
            return True, None

        for i, call in enumerate(calls):
            expected_prev = GENESIS_PREV_HASH if i == 0 else calls[i - 1].record_hash
            if call.prev_hash != expected_prev:
                return (
                    False,
                    f"Chain break at index {i} (call {call.call_id}): "
                    f"prev_hash={call.prev_hash} expected={expected_prev}",
                )

            computed_hash = compute_record_hash(call.prev_hash, call.to_dict())
            if call.record_hash != computed_hash:
                return (
                    False,
                    f"Hash mismatch at index {i} (call {call.call_id}): "
                    f"record_hash={call.record_hash} computed={computed_hash}",
                )

        return True, None
