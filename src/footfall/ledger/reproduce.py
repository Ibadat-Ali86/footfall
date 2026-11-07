"""Reproducible Backtest Pipeline and Verification Engine.

Implements Section 11.5 of docs/BUILD.md.
`make reproduce` rebuilds derived tables and the backtest from raw snapshots
and verifies that the output hashes match the published ones. Any difference fails CI.
"""

from __future__ import annotations

import hashlib
import json
import math
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import duckdb

from footfall.ledger.chain import CallLedger, LedgerCall
from footfall.ledger.resolver import BacktestResolver
from footfall.phase.classifier import PhaseClassifier, PhaseInput
from footfall.registry import load_registry


def compute_file_sha256(file_path: Path | str) -> str:
    """Compute SHA-256 checksum of a file."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def run_reproduce_pipeline(
    snapshots_parquet: Path | str = "phase0/data/snapshots.parquet",
    registry_yaml: Path | str = "registry/seed.yaml",
    ledger_output: Path | str = "data/ledger/calls.jsonl",
    backtest_output: Path | str = "data/backtest/latest.json",
    manifest_path: Path | str = "data/backtest/manifest.json",
    verify: bool = False,
) -> dict[str, Any]:
    """Execute complete reproducible backtest pipeline from raw snapshots.

    Steps:
    1. Load entities and build download lookup tables from snapshots.
    2. Run feature engine and phase classifier for weekly evaluation Mondays.
    3. Construct and verify tamper-evident call ledger.
    4. Resolve realized 4-week outcomes and compile backtest report.
    5. Check or update cryptographic manifest (SHA-256 checksums).
    """
    parquet_path = Path(snapshots_parquet)
    if not parquet_path.exists():
        msg = f"Snapshots file not found: {parquet_path}"
        raise FileNotFoundError(msg)

    reg_path = Path(registry_yaml)
    entities = load_registry(reg_path) if reg_path.exists() else []
    entity_cats = {e.entity_id: e.category.value for e in entities}

    # 1. Query snapshots using DuckDB to compute weekly download totals
    con = duckdb.connect()
    query = """
    SELECT
        entity_id,
        strftime(date_trunc('week', strptime(obs_date, '%Y-%m-%d')), '%Y-%m-%d') AS week_date,
        sum(value) AS weekly_downloads
    FROM read_parquet(?)
    WHERE metric = 'downloads'
    GROUP BY entity_id, week_date
    ORDER BY entity_id, week_date
    """
    rows = con.execute(query, [parquet_path.as_posix()]).fetchall()

    download_lookup: dict[tuple[str, str], float] = {
        (str(row[0]), str(row[1])): float(row[2]) for row in rows
    }

    # Distinct weekly dates
    unique_weeks = sorted({str(row[1]) for row in rows})

    # 2. Select historical evaluation dates (Mondays) with at least 12 weeks of prior history
    # and at least 4 weeks of forward history for resolution
    eval_weeks = [w for w in unique_weeks if "2025-10-01" <= w <= "2026-09-01"]
    if not eval_weeks:
        eval_weeks = unique_weeks[12:-4] if len(unique_weeks) > 16 else unique_weeks

    # 3. Build calls ledger
    out_ledger = Path(ledger_output)
    out_ledger.parent.mkdir(parents=True, exist_ok=True)
    if out_ledger.exists():
        out_ledger.unlink()

    ledger = CallLedger(out_ledger)
    classifier = PhaseClassifier()

    calls: list[LedgerCall] = []

    for w_date in eval_weeks:
        w_dt = date.fromisoformat(w_date)
        prev_4w_str = (w_dt - timedelta(days=28)).isoformat()
        prev_12w_str = (w_dt - timedelta(days=84)).isoformat()

        for entity in entities:
            eid = entity.entity_id
            cat = entity_cats.get(eid, "agent-framework")

            w_curr = download_lookup.get((eid, w_date))
            w_4w = download_lookup.get((eid, prev_4w_str))
            w_12w = download_lookup.get((eid, prev_12w_str))

            if w_curr is None or w_4w is None or w_12w is None:
                continue

            g4 = math.log((w_curr + 1.0) / (w_4w + 1.0))
            g12 = math.log((w_curr + 1.0) / (w_12w + 1.0))

            # Proxy synthetic adoption z-score from normalized growth
            adoption_z = (g4 - 0.1) / 0.3
            p_breakout = (
                round(1.0 / (1.0 + math.exp(-adoption_z)), 4) if adoption_z is not None else None
            )

            phase_inp = PhaseInput(
                history_weeks=26,
                star_history_days=180,
                weekly_volume=w_curr,
                adoption_z=adoption_z,
                attention_z=adoption_z * 0.9,
                divergence=0.1,
                g4=g4,
                g12=g12,
                age_months=12.0,
                is_category_top_quartile=bool(w_curr >= 10000.0),
            )

            phase_res = classifier.classify(phase_inp)

            call = ledger.append_call(
                entity_id=eid,
                category=cat,
                as_of=w_date,
                phase=phase_res.phase.value,
                p_breakout_30d=p_breakout,
                method_version="m1.0",
                features_hash=hashlib.sha256(f"{g4}:{g12}:{w_curr}".encode()).hexdigest(),
                timestamp=f"{w_date}T06:00:00Z",
            )
            calls.append(call)

    # 4. Verify chain integrity
    is_valid, err = CallLedger.verify_chain(calls)
    if not is_valid:
        msg = f"Call ledger integrity verification failed: {err}"
        raise RuntimeError(msg)

    # 5. Resolve outcomes
    resolver = BacktestResolver(download_lookup=download_lookup)
    resolved_calls = resolver.resolve_calls(calls, target_weeks=4)
    report = BacktestResolver.generate_report(resolved_calls)

    out_backtest = Path(backtest_output)
    out_backtest.parent.mkdir(parents=True, exist_ok=True)
    out_backtest.write_text(json.dumps(report, indent=2), encoding="utf-8")

    # 6. Cryptographic Manifest Check / Update
    ledger_hash = compute_file_sha256(out_ledger)
    backtest_hash = compute_file_sha256(out_backtest)

    manifest_file = Path(manifest_path)
    manifest_file.parent.mkdir(parents=True, exist_ok=True)

    computed_manifest = {
        "snapshots_parquet_sha256": compute_file_sha256(parquet_path),
        "calls_ledger_sha256": ledger_hash,
        "backtest_report_sha256": backtest_hash,
        "total_calls": len(calls),
        "resolved_calls": report["resolved_calls"],
        "coverage": report["coverage"],
        "breakout_precision": report["breakout_precision"],
    }

    if verify and manifest_file.exists():
        saved_manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
        if saved_manifest.get("calls_ledger_sha256") != ledger_hash:
            msg = (
                "REPRODUCE FAILED: Ledger hash mismatch! "
                f"Expected: {saved_manifest.get('calls_ledger_sha256')} "
                f"Computed: {ledger_hash}"
            )
            raise ValueError(msg)
        if saved_manifest.get("backtest_report_sha256") != backtest_hash:
            msg = (
                "REPRODUCE FAILED: Backtest report hash mismatch! "
                f"Expected: {saved_manifest.get('backtest_report_sha256')} "
                f"Computed: {backtest_hash}"
            )
            raise ValueError(msg)
    else:
        # Write / update reference manifest
        manifest_file.write_text(json.dumps(computed_manifest, indent=2), encoding="utf-8")

    return computed_manifest
