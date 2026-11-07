# Footfall

> **Real usage, not hype.** Validated adoption signals for AI developer tools.

[![CI](https://github.com/Ibadat-Ali86/footfall/actions/workflows/ci.yml/badge.svg)](https://github.com/Ibadat-Ali86/footfall/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.12%20%7C%203.14-blue.svg)](https://www.python.org/)
[![Code style: ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Security: Bandit](https://img.shields.io/badge/security-bandit-green.svg)](https://github.com/PyCQA/bandit)
[![Coverage](https://img.shields.io/badge/tests-118%20passed-brightgreen.svg)](tests/)

Footfall tracks how much **real use** named AI developer tools get, compared with how much **attention** they get. Tools means agent frameworks, SDKs, MCP servers and models — each tracked as one entity across GitHub, npm, PyPI and Hugging Face.

It stores immutable daily snapshots, filters unusual star bursts without per-person tracking, classifies each tool's lifecycle phase, and publishes a **cryptographically hashed backtest of its own past calls**.

---

## Deliverables & Architecture

| Deliverable | Location | Description |
|---|---|---|
| **Remote MCP Server** | `src/footfall/server/` | FastMCP streamable server (`footfall_compare`, `footfall_trend`, `footfall_find_rising`) with DNS rebinding security and byte capping. |
| **Agent Skill** | `skills/footfall/SKILL.md` | Teaches coding agents (Claude Code, Cursor, Windsurf) how to query the tools with provenance caveats. |
| **Static Dashboard** | `site/` | Zero-tracker dashboard (< 11 KB gzipped, strict CSP `default-src 'self'`, WCAG AA contrast). |
| **Syndicate Alerts** | `site/feeds/` | Automated RSS 2.0, Atom 1.0, and JSON Feed 1.1 notifications on lifecycle phase transitions. |
| **Stack Health Analyzer** | `src/footfall/stack/` | CLI utility analyzing `pyproject.toml`, `requirements.txt`, and `package.json` against AI ecosystem momentum. |
| **Adoption Depth Engine** | `src/footfall/dependents/` | Downstream dependent packages analyzer via `packages.ecosyste.ms` measuring true architectural commitment. |
| **Directory Submissions** | `submissions/` | Complete application packs for Claude Connectors, ChatGPT Plugins, and the MCP Community Registry. |
| **Open Dataset** | `dataset/` | Parquet snapshots and data dictionary published under CC BY 4.0. |

---

## MCP Server Tools

| Tool | Parameters | Description |
|---|---|---|
| `footfall_compare` | `entities: list[str]` (2–6) | Side-by-side comparison of adoption $z$-score, attention $z$-score, divergence ($D$), and lifecycle phase. |
| `footfall_trend` | `entity: str`, `weeks: int` (4–52) | Historical weekly timeseries for a single tool with velocity rates and anomaly flags. |
| `footfall_find_rising` | `phase: str`, `category?: str`, `limit?: int` | Filter tools currently breaking out or accelerating. |

---

## CLI Reference

Footfall provides a unified CLI installed via `uv`:

```bash
# 1. Verify cryptographic hash chain of historical calls and backtest
uv run footfall reproduce --verify

# 2. Analyze developer dependencies in your project
uv run footfall stack pyproject.toml
uv run footfall stack package.json --json-out

# 3. Check ecosystem adoption depth (dependent packages vs download traffic)
uv run footfall dependents --source pypi --package langchain-core
uv run footfall dependents --source npm --package @modelcontextprotocol/sdk

# 4. Generate syndicate feeds and dispatch HMAC-signed webhooks
uv run footfall alerts --ledger data/ledger/calls.jsonl --feed-dir site/feeds/

# 5. Export static JSON bundles and shields.io badge endpoints
uv run footfall export --output-dir exports/v1

# 6. Launch the production MCP server (SSE or stdio transport)
uv run footfall server --transport sse --port 8000
```

---

## Development & Verification

```bash
# Install frozen dependencies
uv sync --frozen

# Run full test suite (118 unit, contract, and site tests)
uv run pytest tests/ -v

# Run Ruff linter and formatter
uv run ruff check . && uv run ruff format --check .

# Run static type checking in strict mode
uv run mypy src

# Reproduce backtest from raw data
make reproduce
```

---

## Status & Roadmap

| Phase | Description | Status |
|---|---|---|
| **0 — Validate** | Hypothesis H1/H2 walk-forward evaluation, pre-registration SHA-256 seal, rate-limit verifications. | ✅ **Passed (Gate G1 Approved)** |
| **1 — Data Product** | Idempotent collectors, raw store, feature engine, anomaly filter, call ledger, backtest reproduction. | ✅ **Complete & Hash-Chained** |
| **2 — Serving Layer** | FastMCP server, container deployment (OIDC), static dashboard, skill prompt suite, security audit. | ✅ **Passed (Gate G3 Approved)** |
| **3 — Launch & Distribution** | Claude directory pack, ChatGPT pack, MCP registry entry, launch assets, pilot user guide. | ✅ **Complete (Gate G4 Approved)** |
| **4 — Backlog** | Stack analyzer, alert syndication feeds, dependents depth engine, learned classifier benchmark. | ✅ **Implemented & Verified** |

---

## Security & Ethics Policy

- **Zero autonomous inspection of secrets:** Footfall never stores, inspects, or logs credentials or `.env` files.
- **Aggregates only:** Zero per-person data, GitHub usernames, or individual accounts are stored or logged.
- **Strict Allow-Listing:** All API and CLI inputs are validated against strict regex allow-lists (`^[A-Za-z0-9@._/\-]{1,100}$`).
- **Cryptographic Provenance:** Backtest reports and call ledgers are immutable and cryptographically verified via SHA-256 hash chains.
- **Tone Standard:** Repositories with inorganic growth are termed **unusual**, never defamatory.

---

## License

- Code: [Apache-2.0](LICENSE)
- Dataset & Backtest Ledger: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)

> Statistical information derived from public software repositories and package registries. Not investment, purchasing, or software architecture advice.
