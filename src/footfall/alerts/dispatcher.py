"""Webhook Dispatcher with HMAC-SHA256 authentication and retry resilience."""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import time
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import httpx

if TYPE_CHECKING:
    from footfall.alerts.models import AlertEvent

logger = logging.getLogger(__name__)


class WebhookDispatcher:
    """Dispatches alert notifications to external webhook endpoints securely."""

    def __init__(
        self,
        webhook_url: str,
        secret: str | None = None,
        timeout: float = 10.0,
        max_retries: int = 3,
    ) -> None:
        """Validate URL scheme and initialize dispatcher."""
        if not webhook_url.startswith("https://"):
            raise ValueError(f"Webhook URL must use secure HTTPS scheme: {webhook_url}")

        self.webhook_url = webhook_url
        self.secret = secret
        self.timeout = timeout
        self.max_retries = max_retries

    def dispatch(self, events: list[AlertEvent]) -> bool:
        """Serialize events and deliver to the configured webhook endpoint."""
        if not events:
            return True

        now_str = datetime.now(UTC).isoformat()
        payload = {
            "version": "1.0",
            "generated_at": now_str,
            "count": len(events),
            "events": [e.to_dict() for e in events],
        }

        payload_bytes = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Footfall-Alerts/1.0",
        }

        if self.secret:
            sig = hmac.new(self.secret.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()
            headers["X-Footfall-Signature"] = f"sha256={sig}"

        for attempt in range(1, self.max_retries + 1):
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    resp = client.post(self.webhook_url, content=payload_bytes, headers=headers)
                    if resp.status_code in (200, 201, 202, 204):
                        return True
                    if resp.status_code < 500:
                        logger.warning(
                            "Webhook rejected with client error status %d",
                            resp.status_code,
                        )
                        return False
            except (httpx.RequestError, httpx.TimeoutException) as exc:
                logger.warning("Webhook dispatch attempt %d failed: %s", attempt, str(exc))

            if attempt < self.max_retries:
                time.sleep(0.5 * (2 ** (attempt - 1)))

        return False
