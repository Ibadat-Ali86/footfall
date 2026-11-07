"""Syndication Feed Generators (RSS 2.0, Atom 1.0, JSON Feed 1.1)."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from footfall.alerts.models import AlertEvent


class FeedGenerator:
    """Generates standard syndication feeds for Footfall alert events."""

    def __init__(
        self,
        base_url: str = "https://footfall.dev",
        title: str = "Footfall AI Ecosystem Alerts",
        description: str = (
            "Empirical lifecycle phase shifts, divergence surges, and anomaly "
            "alerts across AI developer frameworks and libraries."
        ),
    ) -> None:
        """Initialize feed metadata."""
        self.base_url = base_url.rstrip("/")
        self.title = title
        self.description = description

    def generate_rss(self, events: list[AlertEvent]) -> str:
        """Generate RSS 2.0 XML document."""
        rss = ET.Element("rss", {"version": "2.0"})
        channel = ET.SubElement(rss, "channel")

        ET.SubElement(channel, "title").text = self.title
        ET.SubElement(channel, "link").text = self.base_url
        ET.SubElement(channel, "description").text = self.description
        ET.SubElement(channel, "language").text = "en-US"

        for ev in events:
            item = ET.SubElement(channel, "item")
            ET.SubElement(item, "title").text = f"[{ev.alert_type.value}] {ev.display_name}"
            ET.SubElement(item, "link").text = ev.details_url
            ET.SubElement(
                item, "description"
            ).text = (
                f"{ev.summary} (Adoption z={ev.adoption_z:.2f}, Divergence={ev.divergence:+.2f})"
            )
            guid = ET.SubElement(item, "guid", {"isPermaLink": "false"})
            guid.text = ev.event_id
            ET.SubElement(item, "pubDate").text = ev.timestamp

        raw_bytes = ET.tostring(rss, encoding="utf-8", xml_declaration=True)
        return str(raw_bytes.decode("utf-8"))

    def generate_atom(self, events: list[AlertEvent]) -> str:
        """Generate Atom 1.0 XML document."""
        atom_ns = "http://www.w3.org/2005/Atom"
        feed = ET.Element("feed", {"xmlns": atom_ns})

        ET.SubElement(feed, "title").text = self.title
        ET.SubElement(feed, "id").text = f"{self.base_url}/atom.xml"
        latest_time = events[0].timestamp if events else "2026-11-01T00:00:00Z"
        ET.SubElement(feed, "updated").text = latest_time
        ET.SubElement(feed, "link", {"href": self.base_url, "rel": "alternate"})
        ET.SubElement(feed, "link", {"href": f"{self.base_url}/atom.xml", "rel": "self"})

        for ev in events:
            entry = ET.SubElement(feed, "entry")
            ET.SubElement(entry, "title").text = f"[{ev.alert_type.value}] {ev.display_name}"
            ET.SubElement(entry, "id").text = ev.event_id
            ET.SubElement(entry, "updated").text = ev.timestamp
            ET.SubElement(entry, "link", {"href": ev.details_url})
            content = ET.SubElement(entry, "content", {"type": "text"})
            content.text = ev.summary

        raw_atom = ET.tostring(feed, encoding="utf-8", xml_declaration=True)
        return str(raw_atom.decode("utf-8"))

    def generate_json_feed(self, events: list[AlertEvent]) -> dict[str, Any]:
        """Generate JSON Feed 1.1 structured dictionary."""
        items = []
        for ev in events:
            items.append(
                {
                    "id": ev.event_id,
                    "url": ev.details_url,
                    "title": f"[{ev.alert_type.value}] {ev.display_name}",
                    "content_text": ev.summary,
                    "date_published": ev.timestamp,
                    "tags": [ev.alert_type.value, ev.current_phase],
                    "_footfall": {
                        "entity_id": ev.entity_id,
                        "previous_phase": ev.previous_phase,
                        "current_phase": ev.current_phase,
                        "divergence": ev.divergence,
                        "adoption_z": ev.adoption_z,
                    },
                }
            )

        return {
            "version": "https://jsonfeed.org/version/1.1",
            "title": self.title,
            "home_page_url": self.base_url,
            "feed_url": f"{self.base_url}/feed.json",
            "description": self.description,
            "items": items,
        }
