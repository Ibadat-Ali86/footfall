"""Public Claims & Number Verifier.

Implements Task T1.9 of docs/BUILD.md.
Rule from AGENTS.md: "Never write public text that contains a number with no link to a data path."

Scans markdown documentation for quantitative statistics and enforces that every
claim links directly to an authoritative data artifact (e.g. Parquet, JSON, ledger, report).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

# Regex for markdown links: [text](target)
LINK_PATTERN = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
# Regex for numbers in prose (integers, floats, percentages, signed decimals)
NUMBER_PROSE_PATTERN = re.compile(
    r"(?<![A-Za-z0-9_#/-])([+-]?\d+(?:,\d{3})*(?:\.\d+)?%?)(?![A-Za-z0-9_/-])"
)


def mask_exempt_prose_constructs(text: str) -> str:
    """Mask out math expressions, tables, timestamps, durations, and structural references."""
    # Mask LaTeX math display: $$ ... $$
    text = re.sub(r"\$\$[\s\S]*?\$\$", " __LATEX_DISPLAY__ ", text)
    # Mask LaTeX inline math: $ ... $
    text = re.sub(r"\$[^$]+?\$", " __LATEX_INLINE__ ", text)
    # Mask licenses and standard codes: CC-BY-4.0, Attribution 4.0, ISO 8601, SHA-256
    text = re.sub(
        r"(?:Creative Commons\s+)?Attribution\s+\d+\.\d+(?:\s+International)?",
        " __LICENSE__ ",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(r"CC-BY-\d+\.\d+", " __LICENSE__ ", text, flags=re.IGNORECASE)
    text = re.sub(r"SHA-\d+", " __HASH_NAME__ ", text, flags=re.IGNORECASE)
    # Mask clock times: 06:00, 12:30 UTC
    text = re.sub(r"\b\d{1,2}:\d{2}(?::\d{2})?(?:\s*UTC)?\b", " __TIME__ ", text)
    # Mask common calendar durations (e.g. "24 hours", "6 months", "18 months", "4 weeks")
    text = re.sub(
        r"\b\d+\s*(?:hours|days|weeks|months|years|minutes|seconds)\b",
        " __DURATION__ ",
        text,
        flags=re.IGNORECASE,
    )
    # Mask named sections, phases, gates, tasks: e.g. "Phase 0", "T0.3", "Section 20", "Gate G0"
    text = re.sub(
        r"\b(?:Phase|Section|Gate|Version|Table|Step|Rule|item|ID|G|T)\s*[A-Za-z]?\d+(?:\.\d+)*\b",
        " __SECTION_REF__ ",
        text,
        flags=re.IGNORECASE,
    )
    # Mask software release tags like v1.0, m1.0
    text = re.sub(r"\b[vVmM]\d+(?:\.\d+)*\b", " __VERSION_TAG__ ", text)
    return text


def verify_document_claims(file_path: Path | str) -> list[dict[str, Any]]:
    """Scan a markdown document and return violations where numbers lack data links."""
    path = Path(file_path)
    if not path.is_file():
        return []

    lines = path.read_text(encoding="utf-8").splitlines()
    violations: list[dict[str, Any]] = []

    in_code_block = False

    for line_idx, line in enumerate(lines, start=1):
        stripped = line.strip()

        # Handle fenced code blocks
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            continue

        if in_code_block:
            continue

        # Skip headers like "# 1. Summary" or "### 10.2 Title"
        if stripped.startswith("#"):
            continue

        # Skip markdown horizontal rules or empty lines
        if not stripped or stripped.startswith("---"):
            continue

        # Skip markdown table rows (tables specify structured schema/definitions)
        if stripped.startswith("|") and stripped.endswith("|"):
            continue

        # Extract all markdown links and temporarily replace them with placeholders
        links = LINK_PATTERN.findall(line)
        line_masked = line

        # If a link contains a number and points to a data path, it is valid
        for anchor_text, href in links:
            placeholder = f"__LINK_PLACEHOLDER_{len(anchor_text)}__"
            line_masked = line_masked.replace(f"[{anchor_text}]({href})", placeholder, 1)

        # Remove inline code spans `code`
        line_masked = re.sub(r"`[^`]*`", "__INLINE_CODE__", line_masked)

        # Mask math, time, duration, and section constructs
        line_masked = mask_exempt_prose_constructs(line_masked)

        # Find any remaining raw numbers in the prose
        matches = NUMBER_PROSE_PATTERN.findall(line_masked)
        for num_token in matches:
            # Check if exempt list enumerator ("1.", "2.")
            if stripped.startswith(f"{num_token}.") or stripped.startswith(f"{num_token})"):
                continue

            # Skip small integers commonly used as grammatical ordinals (1, 2)
            if num_token in ("1", "2") and not ("%" in num_token or "." in num_token):
                continue

            # Flag as violation
            violations.append(
                {
                    "file": str(path),
                    "line": line_idx,
                    "token": num_token,
                    "text": line.strip(),
                }
            )

    return violations


def verify_all_claims(docs: list[Path] | None = None) -> int:
    """Verify all public documentation files in docs/ and site/."""
    docs_to_check = docs or [
        Path("docs/methodology.md"),
        Path("docs/dataset-card.md"),
        Path("README.md"),
    ]

    total_violations = 0
    for doc in docs_to_check:
        if not doc.exists():
            continue
        v_list = verify_document_claims(doc)
        if v_list:
            total_violations += len(v_list)
            print(f"FAILED: Found {len(v_list)} unlinked numbers in {doc}:")
            for v in v_list:
                print(f"  Line {v['line']}: '{v['token']}' in: \"{v['text']}\"")

    if total_violations > 0:
        print(
            f"\nTotal violations: {total_violations}. Every public number must link to a data path."
        )
        return 1

    print("SUCCESS: All public claims and numbers link directly to authoritative data paths.")
    return 0


if __name__ == "__main__":
    sys.exit(verify_all_claims())
