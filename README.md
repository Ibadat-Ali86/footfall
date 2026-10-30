# Footfall

> **Real usage, not hype.** Validated adoption signals for AI developer tools.

[![CI](https://github.com/Ibadat-Ali86/footfall/actions/workflows/ci.yml/badge.svg)](https://github.com/Ibadat-Ali86/footfall/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/)
[![Code style: ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

Footfall tracks how much **real use** named AI developer tools get, compared with how much **attention** they get. Tools means agent frameworks, SDKs, MCP servers and models — each tracked as one entity across GitHub, npm, PyPI and Hugging Face.

It stores its own daily snapshots, filters unusual star bursts, classifies each tool's lifecycle phase, and publishes a **backtest of its own past calls**.

---

## What it ships as

| Artifact | Description |
|---|---|
| Remote MCP server | Three read-only tools for agents |
| Skill | `skills/footfall/SKILL.md` — teaches the model to use the tools |
| Static dashboard | Leaderboards, methodology, backtest, dataset downloads |
| README badges | `shields.io` endpoint badges for registry entities |
| Open dataset | Daily snapshots and weekly features in Parquet |

## MCP Tools

| Tool | Purpose |
|---|---|
| `footfall_compare` | Compare 2–6 tools side by side |
| `footfall_trend` | Weekly time series for one tool |
| `footfall_find_rising` | List tools in a lifecycle phase |

---

## Status

> **Pre-build. Phase 0 (validation) has not started.**

The project is currently at **T0.3 Scaffold** — the repository structure has been created and is awaiting Gate G0 (name and namespace confirmation) from the human owner, then T0.2 (accounts and secrets).

See [`docs/BUILD.md`](docs/BUILD.md) for the full product, security and build documentation.

---

## Project Structure

```
footfall/
├── AGENTS.md                    # AI agent operating rules
├── CLAUDE.md                    # Points to AGENTS.md
├── SECURITY.md                  # Vulnerability disclosure policy
├── pyproject.toml
├── uv.lock                      # Committed, hashes included
├── registry/
│   ├── seed.yaml                # Entities and source mappings
│   └── schema.json
├── config/
│   ├── methods.yaml             # Thresholds, versioned
│   └── sources.yaml             # Allow-listed hosts, limits
├── src/footfall/
│   ├── collectors/              # github.py npm.py pypi.py hf.py hn.py base.py
│   ├── store/                   # Raw writer, parquet, duckdb views
│   ├── features/                # adoption.py attention.py normalize.py
│   ├── phase/                   # rules.py model.py
│   ├── anomaly/                 # bursts.py sampling.py
│   ├── ledger/                  # calls.py resolve.py backtest.py
│   ├── export/                  # entity_json.py leaderboards.py badges.py
│   ├── server/                  # mcp_app.py tools.py validation.py limits.py
│   └── cli.py
├── skills/footfall/             # SKILL.md and references
├── site/                        # Static dashboard source
├── phase0/                      # Notebooks, preregistration.yaml, report
├── tests/
│   ├── fixtures/                # Recorded HTTP responses
│   ├── unit/ contract/ security/ golden/
└── .github/workflows/           # ci.yml daily.yml weekly.yml release.yml
```

---

## Quick Start (Development)

```bash
# Requires uv: https://docs.astral.sh/uv/
uv sync --frozen
uv run pytest -q
uv run ruff check .
uv run mypy src
```

---

## Roadmap

| Phase | Duration | Status |
|---|---|---|
| 0 — Validate | ~2 weeks | 🔲 Not started |
| 1 — Data product | ~3–4 weeks | 🔲 Blocked on G1 |
| 2 — Serving | ~3 weeks | 🔲 Blocked on G1 |
| 3 — Launch | ~3–4 weeks | 🔲 Blocked on G3 |

---

## What this is not

- A news feed or general trend dashboard
- Investment, purchasing, or security advice — every output says so
- A fraud detector — it flags **unusual** patterns and says what it saw
- An "Ask AI" chat box

---

## Contributing

See [`AGENTS.md`](AGENTS.md) for agent rules. Human contributions follow the same task-card discipline described in [`docs/BUILD.md`](docs/BUILD.md) Section 20.

---

## License

Code: [Apache-2.0](LICENSE)  
Derived dataset: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) — *subject to terms review at Gate G2 before any release*

---

> Statistical information about public software projects. Not investment, security, or purchasing advice. Predictions are probabilistic and can be wrong. No affiliation with or endorsement by the projects listed.
