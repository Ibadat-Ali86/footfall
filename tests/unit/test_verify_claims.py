"""Unit tests for Public Claims and Number Verification Script (Task T1.9).

Follows AGENTS.md:
- Tests first
- Rule: "Never write public text that contains a number with no link to a data path"
- Proves detection of unlinked quantitative figures
- Proves allowance of linked figures, code blocks, tables, and section identifiers
"""

from __future__ import annotations

from pathlib import Path

import pytest

from footfall.export.claims import (
    verify_document_claims,
)


@pytest.mark.unit
def test_claims_verifier_passes_on_linked_numbers(tmp_path: Path) -> None:
    """Numbers that link directly to data paths or are in code blocks must pass."""
    doc_content = """# Verified Public Document
In backtest evaluation, margin was [+0.0962](phase0/h1_evaluation_report.md)
across [7,248](data/backtest/manifest.json) resolved calls.

```python
# Code blocks can contain raw literals
x = 42
y = 1000
```

| Metric | Value | Reference |
|---|---|---|
| Precision | [50.0%](data/backtest/latest.json) | latest.json |
"""
    doc_file = tmp_path / "valid_claims.md"
    doc_file.write_text(doc_content, encoding="utf-8")

    violations = verify_document_claims(doc_file)
    assert len(violations) == 0


@pytest.mark.unit
def test_claims_verifier_fails_on_unlinked_numbers(tmp_path: Path) -> None:
    """Unlinked statistics or quantitative metrics must fail."""
    doc_content = """# Bad Document

Our model predicts that 85% of breakout tools achieve 50000 downloads in 30 days.
"""
    doc_file = tmp_path / "invalid_claims.md"
    doc_file.write_text(doc_content, encoding="utf-8")

    violations = verify_document_claims(doc_file)
    assert len(violations) > 0
    # Must flag the unlinked percentage and quantities
    flagged_tokens = [v["token"] for v in violations]
    assert any("85%" in t for t in flagged_tokens)
    assert any("50000" in t for t in flagged_tokens)
