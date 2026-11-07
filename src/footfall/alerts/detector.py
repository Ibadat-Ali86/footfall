"""Change and anomaly detection engine for alert event generation."""

from __future__ import annotations

from typing import Any

from footfall.alerts.models import AlertEvent, AlertType


class AlertDetector:
    """Detects phase changes, divergence surges, and anomaly flags across snapshots."""

    def __init__(
        self,
        divergence_spike_threshold: float = 2.0,
        anomaly_threshold: float = 0.8,
        base_url: str = "https://footfall.dev",
    ) -> None:
        """Initialize detector with analytical threshold parameters."""
        self.divergence_spike_threshold = divergence_spike_threshold
        self.anomaly_threshold = anomaly_threshold
        self.base_url = base_url.rstrip("/")

    def detect_changes(
        self,
        prev_state: dict[str, dict[str, Any]],
        curr_state: dict[str, dict[str, Any]],
        timestamp: str,
    ) -> list[AlertEvent]:
        """Compare two consecutive entity state maps and produce alert events."""
        events: list[AlertEvent] = []

        for entity_id, curr in curr_state.items():
            if entity_id not in prev_state:
                continue

            prev = prev_state[entity_id]
            display_name = str(curr.get("display_name", entity_id))
            curr_phase = str(curr.get("phase", "unknown"))
            prev_phase = str(prev.get("phase", "unknown"))
            curr_div = float(curr.get("divergence", 0.0))
            prev_div = float(prev.get("divergence", 0.0))
            curr_z = float(curr.get("adoption_z", 0.0))
            curr_anomaly = float(curr.get("anomaly_score", 0.0))
            prev_anomaly = float(prev.get("anomaly_score", 0.0))
            details_url = f"{self.base_url}/entity.html?id={entity_id}"

            # 1. Phase transition detection
            if curr_phase != prev_phase:
                event_id = f"alert-{entity_id}-phase-{timestamp[:10]}"
                summary = f"{display_name} transitioned from {prev_phase} to {curr_phase}."
                events.append(
                    AlertEvent(
                        event_id=event_id,
                        entity_id=entity_id,
                        display_name=display_name,
                        alert_type=AlertType.PHASE_CHANGE,
                        previous_phase=prev_phase,
                        current_phase=curr_phase,
                        divergence=curr_div,
                        adoption_z=curr_z,
                        timestamp=timestamp,
                        summary=summary,
                        details_url=details_url,
                    )
                )

            # 2. Divergence spike detection
            div_spike = abs(curr_div) >= self.divergence_spike_threshold and (
                abs(curr_div) - abs(prev_div) >= 1.0
                or abs(prev_div) < self.divergence_spike_threshold
            )
            if div_spike:
                event_id = f"alert-{entity_id}-divergence-{timestamp[:10]}"
                sign = "+" if curr_div >= 0 else ""
                summary = (
                    f"{display_name} divergence spiked to {sign}{curr_div:.2f} "
                    f"(threshold |D| >= {self.divergence_spike_threshold:.1f})."
                )
                events.append(
                    AlertEvent(
                        event_id=event_id,
                        entity_id=entity_id,
                        display_name=display_name,
                        alert_type=AlertType.DIVERGENCE_SPIKE,
                        previous_phase=prev_phase,
                        current_phase=curr_phase,
                        divergence=curr_div,
                        adoption_z=curr_z,
                        timestamp=timestamp,
                        summary=summary,
                        details_url=details_url,
                    )
                )

            # 3. High-confidence anomaly detection
            anomaly_detected = (
                curr_anomaly >= self.anomaly_threshold and prev_anomaly < self.anomaly_threshold
            )
            if anomaly_detected:
                event_id = f"alert-{entity_id}-anomaly-{timestamp[:10]}"
                summary = (
                    f"Unusual star/download velocity detected for {display_name} "
                    f"with confidence score {curr_anomaly:.2f}."
                )
                events.append(
                    AlertEvent(
                        event_id=event_id,
                        entity_id=entity_id,
                        display_name=display_name,
                        alert_type=AlertType.ANOMALY_FLAG,
                        previous_phase=prev_phase,
                        current_phase=curr_phase,
                        divergence=curr_div,
                        adoption_z=curr_z,
                        timestamp=timestamp,
                        summary=summary,
                        details_url=details_url,
                    )
                )

        return sorted(events, key=lambda e: (e.timestamp, e.entity_id))
