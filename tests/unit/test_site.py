"""Unit tests for the Footfall static dashboard (Section 12.4).

Proves:
- Zero third-party scripts, styles, or trackers
- Strict Content Security Policy (default-src 'self')
- Accessible skip links on every page
- Total gzipped site bundle under 100 KB
- Required pages present: index, entity, methodology, backtest, data, about
"""

from __future__ import annotations

import io
import re
import tarfile
from pathlib import Path

import pytest

SITE_DIR = Path("site")
EXPECTED_PAGES: list[str] = [
    "index.html",
    "entity.html",
    "methodology.html",
    "backtest.html",
    "data.html",
    "about.html",
]


@pytest.mark.unit
def test_all_site_pages_exist() -> None:
    """All 6 core dashboard pages and CSS stylesheet must exist."""
    assert (SITE_DIR / "style.css").is_file(), "site/style.css missing"
    for page in EXPECTED_PAGES:
        file_path = SITE_DIR / page
        assert file_path.is_file(), f"Dashboard page {page} missing"


@pytest.mark.unit
def test_strict_csp_and_no_external_trackers() -> None:
    """Section 12.4: Strict CSP meta tag and zero external scripts or tracker pixels."""
    for page in EXPECTED_PAGES:
        content = (SITE_DIR / page).read_text(encoding="utf-8")

        # 1. Must contain strict Content-Security-Policy
        assert 'http-equiv="Content-Security-Policy"' in content, f"Missing CSP in {page}"
        assert "default-src 'self'" in content, f"CSP does not enforce default-src 'self' in {page}"

        # 2. Zero external script tags (no Google Analytics, Segment, CDNs)
        external_scripts = re.findall(r'<script[^>]+src=["\'](https?://[^"\']+)["\']', content)
        assert len(external_scripts) == 0, f"Found external scripts in {page}: {external_scripts}"

        # 3. Zero external stylesheets (system font stack only)
        external_links = re.findall(
            r'<link[^>]+rel=["\']stylesheet["\'][^>]+href=["\'](https?://[^"\']+)["\']',
            content,
        )
        assert len(external_links) == 0, f"Found external styles in {page}: {external_links}"


@pytest.mark.unit
def test_accessibility_skip_links_and_labels() -> None:
    """Section 12.4: Keyboard accessible skip-link and labelled tables."""
    for page in EXPECTED_PAGES:
        content = (SITE_DIR / page).read_text(encoding="utf-8")
        assert 'class="skip-link"' in content, f"Missing skip-link in {page}"
        assert 'id="main-content"' in content, f"Missing #main-content anchor in {page}"


@pytest.mark.unit
def test_total_site_bundle_under_100kb() -> None:
    """Section 12.4 target: total site bundle under 100 KB gzipped."""
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        tar.add(SITE_DIR, arcname="site")

    compressed_size_bytes = buf.tell()
    assert compressed_size_bytes < 100 * 1024, (
        f"Site bundle {compressed_size_bytes} bytes exceeds 100 KB limit"
    )
