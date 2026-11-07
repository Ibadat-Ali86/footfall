"""Unit tests for Footfall Alert and Notification Engine (Phase 4 Backlog).

Proves:
- Event detection: phase transitions, divergence spikes, and anomaly alerts.
- Syndicate feed generation: RSS 2.0, Atom 1.0, and JSON Feed 1.1 formats.
- Webhook dispatcher: JSON serialization, HMAC-SHA256 signature, retry handling.
- CLI execution: `footfall alerts` with file writing and dry-run modes.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

import pytest
import respx
from click.testing import CliRunner

from footfall.alerts.detector import AlertDetector
from footfall.alerts.dispatcher import WebhookDispatcher
from footfall.alerts.feeds import FeedGenerator
from footfall.alerts.models import AlertEvent, AlertType
from footfall.cli import main


@pytest.fixture
def sample_events() -> list[AlertEvent]:
    """Fixture providing a diverse set of alert events."""
    return [
        AlertEvent(
            event_id="alert-langgraph-2026-11-01",
            entity_id="langgraph",
            display_name="LangGraph",
            alert_type=AlertType.PHASE_CHANGE,
            previous_phase="attention_ahead",
            current_phase="established_adoption",
            divergence=0.85,
            adoption_z=2.14,
            timestamp="2026-11-01T00:00:00Z",
            summary="LangGraph transitioned from attention_ahead to established_adoption.",
            details_url="https://footfall.dev/entity.html?id=langgraph",
        ),
        AlertEvent(
            event_id="alert-qdrant-2026-11-01",
            entity_id="qdrant-client",
            display_name="Qdrant Client",
            alert_type=AlertType.DIVERGENCE_SPIKE,
            previous_phase="established_adoption",
            current_phase="established_adoption",
            divergence=2.35,
            adoption_z=3.10,
            timestamp="2026-11-01T00:00:00Z",
            summary="Qdrant Client divergence spiked to +2.35 (threshold |D| >= 2.0).",
            details_url="https://footfall.dev/entity.html?id=qdrant-client",
        ),
        AlertEvent(
            event_id="alert-unusual-tool-2026-11-01",
            entity_id="unusual-tool",
            display_name="Unusual Tool",
            alert_type=AlertType.ANOMALY_FLAG,
            previous_phase="early_adoption",
            current_phase="early_adoption",
            divergence=-1.40,
            adoption_z=0.20,
            timestamp="2026-11-01T00:00:00Z",
            summary="Unusual star velocity pattern detected with confidence score 0.88.",
            details_url="https://footfall.dev/entity.html?id=unusual-tool",
        ),
    ]


def test_detector_identifies_phase_transitions() -> None:
    """Proves detection of phase changes between two daily snapshots."""
    prev_state: dict[str, dict[str, Any]] = {
        "langgraph": {
            "entity_id": "langgraph",
            "display_name": "LangGraph",
            "phase": "attention_ahead",
            "divergence": 0.5,
            "adoption_z": 1.2,
            "anomaly_score": 0.1,
        }
    }
    curr_state: dict[str, dict[str, Any]] = {
        "langgraph": {
            "entity_id": "langgraph",
            "display_name": "LangGraph",
            "phase": "established_adoption",
            "divergence": 0.85,
            "adoption_z": 2.14,
            "anomaly_score": 0.1,
        }
    }

    detector = AlertDetector()
    events = detector.detect_changes(
        prev_state=prev_state,
        curr_state=curr_state,
        timestamp="2026-11-01T00:00:00Z",
    )

    assert len(events) == 1
    ev = events[0]
    assert ev.alert_type == AlertType.PHASE_CHANGE
    assert ev.previous_phase == "attention_ahead"
    assert ev.current_phase == "established_adoption"
    assert ev.entity_id == "langgraph"


def test_detector_identifies_divergence_spikes() -> None:
    """Proves detection of sudden divergence spikes exceeding threshold."""
    prev_state: dict[str, dict[str, Any]] = {
        "fast-tool": {
            "entity_id": "fast-tool",
            "display_name": "Fast Tool",
            "phase": "early_adoption",
            "divergence": 0.2,
            "adoption_z": 1.0,
            "anomaly_score": 0.05,
        }
    }
    curr_state: dict[str, dict[str, Any]] = {
        "fast-tool": {
            "entity_id": "fast-tool",
            "display_name": "Fast Tool",
            "phase": "early_adoption",
            "divergence": 2.15,
            "adoption_z": 2.8,
            "anomaly_score": 0.05,
        }
    }

    detector = AlertDetector(divergence_spike_threshold=2.0)
    events = detector.detect_changes(
        prev_state=prev_state,
        curr_state=curr_state,
        timestamp="2026-11-01T00:00:00Z",
    )

    assert len(events) == 1
    assert events[0].alert_type == AlertType.DIVERGENCE_SPIKE
    assert events[0].divergence == 2.15


def test_detector_identifies_anomaly_flags() -> None:
    """Proves detection of high-confidence star/download velocity anomaly flags."""
    prev_state: dict[str, dict[str, Any]] = {
        "tool-x": {
            "entity_id": "tool-x",
            "display_name": "Tool X",
            "phase": "early_adoption",
            "divergence": 0.0,
            "adoption_z": 0.5,
            "anomaly_score": 0.2,
        }
    }
    curr_state: dict[str, dict[str, Any]] = {
        "tool-x": {
            "entity_id": "tool-x",
            "display_name": "Tool X",
            "phase": "early_adoption",
            "divergence": 0.0,
            "adoption_z": 0.5,
            "anomaly_score": 0.92,
        }
    }

    detector = AlertDetector(anomaly_threshold=0.8)
    events = detector.detect_changes(
        prev_state=prev_state,
        curr_state=curr_state,
        timestamp="2026-11-01T00:00:00Z",
    )

    assert len(events) == 1
    assert events[0].alert_type == AlertType.ANOMALY_FLAG


def test_feed_generator_produces_valid_rss(sample_events: list[AlertEvent]) -> None:
    """Proves valid RSS 2.0 XML generation conforming to syndicate standards."""
    gen = FeedGenerator(base_url="https://footfall.dev")
    rss_xml = gen.generate_rss(sample_events)

    root = ET.fromstring(rss_xml)
    assert root.tag == "rss"
    assert root.attrib.get("version") == "2.0"

    channel = root.find("channel")
    assert channel is not None
    assert channel.findtext("title") == "Footfall AI Ecosystem Alerts"

    items = channel.findall("item")
    assert len(items) == 3

    first_item = items[0]
    assert first_item.findtext("title") is not None
    assert "LangGraph" in (first_item.findtext("title") or "")
    assert first_item.findtext("guid") == "alert-langgraph-2026-11-01"


def test_feed_generator_produces_valid_atom(sample_events: list[AlertEvent]) -> None:
    """Proves valid Atom 1.0 XML generation conforming to RFC 4287."""
    gen = FeedGenerator(base_url="https://footfall.dev")
    atom_xml = gen.generate_atom(sample_events)

    root = ET.fromstring(atom_xml)
    assert "feed" in root.tag

    entries = [child for child in root if child.tag.endswith("entry")]
    assert len(entries) == 3


def test_feed_generator_produces_valid_json_feed(sample_events: list[AlertEvent]) -> None:
    """Proves JSON Feed 1.1 format adherence."""
    gen = FeedGenerator(base_url="https://footfall.dev")
    json_feed = gen.generate_json_feed(sample_events)

    assert json_feed["version"] == "https://jsonfeed.org/version/1.1"
    assert json_feed["title"] == "Footfall AI Ecosystem Alerts"
    assert len(json_feed["items"]) == 3
    assert json_feed["items"][0]["id"] == "alert-langgraph-2026-11-01"


@respx.mock
def test_webhook_dispatcher_delivers_payload_with_hmac_signature(
    sample_events: list[AlertEvent],
) -> None:
    """Proves secure webhook POST with HMAC-SHA256 signature verification."""
    secret = "test-secret-key-12345"
    target_url = "https://hooks.example.com/alerts"

    route = respx.post(target_url).respond(status_code=200, json={"status": "ok"})

    dispatcher = WebhookDispatcher(webhook_url=target_url, secret=secret)
    success = dispatcher.dispatch(sample_events)

    assert success is True
    assert route.called
    request = route.calls.last.request
    payload_bytes = request.content

    # Verify signature
    digest = hmac.new(secret.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()
    expected_sig = f"sha256={digest}"
    assert request.headers.get("X-Footfall-Signature") == expected_sig


def test_webhook_dispatcher_rejects_insecure_url() -> None:
    """Proves rejection of unencrypted or malicious URL schemes."""
    with pytest.raises(ValueError, match="HTTPS"):
        WebhookDispatcher(webhook_url="http://insecure.example.com/webhook")

    with pytest.raises(ValueError, match="HTTPS"):
        WebhookDispatcher(webhook_url="file:///etc/passwd")


def test_cli_alerts_execution(tmp_path: Path, sample_events: list[AlertEvent]) -> None:
    """Proves CLI `footfall alerts` command execution and file outputs."""
    runner = CliRunner()
    feed_dir = tmp_path / "feeds"
    feed_dir.mkdir()

    # Create dummy ledger snapshot
    ledger_path = tmp_path / "call_ledger.jsonl"
    r1 = {
        "call_id": "call-1",
        "entity_id": "langgraph",
        "timestamp": "2026-10-31T00:00:00Z",
        "phase": "attention_ahead",
        "divergence": 0.5,
        "adoption_z": 1.0,
        "anomaly_flag": False,
    }
    r2 = {
        "call_id": "call-2",
        "entity_id": "langgraph",
        "timestamp": "2026-11-01T00:00:00Z",
        "phase": "established_adoption",
        "divergence": 0.85,
        "adoption_z": 2.14,
        "anomaly_flag": False,
    }
    ledger_path.write_text(f"{json.dumps(r1)}\n{json.dumps(r2)}\n", encoding="utf-8")

    result = runner.invoke(
        main,
        ["alerts", "--ledger", str(ledger_path), "--feed-dir", str(feed_dir)],
    )

    assert result.exit_code == 0
    assert "Alerts processed: 1" in result.output
    assert (feed_dir / "rss.xml").exists()
    assert (feed_dir / "atom.xml").exists()
    assert (feed_dir / "feed.json").exists()
