"""Footfall Alerts & Notification System.

Provides change detection, syndication feeds (RSS 2.0, Atom 1.0, JSON Feed),
and HMAC-authenticated webhook notifications for AI ecosystem lifecycle shifts.
"""

from __future__ import annotations

from footfall.alerts.detector import AlertDetector
from footfall.alerts.dispatcher import WebhookDispatcher
from footfall.alerts.feeds import FeedGenerator
from footfall.alerts.models import AlertEvent, AlertType

__all__ = [
    "AlertDetector",
    "AlertEvent",
    "AlertType",
    "FeedGenerator",
    "WebhookDispatcher",
]
