"""Data models for Footfall Alerts & Notifications."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import StrEnum
from typing import Any


class AlertType(StrEnum):
    """Enumeration of alert event trigger categories."""

    PHASE_CHANGE = "phase_change"
    DIVERGENCE_SPIKE = "divergence_spike"
    ANOMALY_FLAG = "anomaly_flag"


@dataclass(frozen=True)
class AlertEvent:
    """Represents a discrete ecosystem alert or notification event."""

    event_id: str
    entity_id: str
    display_name: str
    alert_type: AlertType
    previous_phase: str
    current_phase: str
    divergence: float
    adoption_z: float
    timestamp: str
    summary: str
    details_url: str

    def to_dict(self) -> dict[str, Any]:
        """Convert alert event to a JSON-serializable dictionary."""
        data = asdict(self)
        data["alert_type"] = self.alert_type.value
        return data
