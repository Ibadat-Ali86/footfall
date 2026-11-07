# Entity Selection Rule — Seed Registry v0 (Task T0.5)

**Pre-registration Date:** 2026-11-01  
**Target Entity Count:** ~150–200 entities  
**Scope:** AI Developer Tools, Agents, SDKs, MCP Servers, Vector Stores, Evaluation Frameworks, and Open Model Frameworks.

---

## 1. Selection Methodology

To avoid survivorship and selection bias in Phase 0 validation (Hypothesis H1 & H3), entities are selected according to a **deterministic two-tier rule**:

### Tier 1: Core Stratified Sampling (Top $N$ by Stargazer Count)
Within each of the 6 core categories, select the top $N$ publicly established repositories by GitHub stars as of 2026-11-01:
- **Agent Frameworks:** Top 35 repositories
- **LLM SDKs & Serving:** Top 35 repositories
- **MCP Servers & Tooling:** Top 35 repositories
- **Vector Stores & Indexes:** Top 25 repositories
- **Evaluation, Observability & Guardrails:** Top 25 repositories
- **Models & Fine-Tuning Frameworks:** Top 25 repositories

### Tier 2: Emerging / Randomized Sampling (Tail $M$)
To ensure the backtest is not evaluated solely on mature breakout tools:
- Select 5–10 emerging tools per category created within the last 6 months having between 100 and 2,000 GitHub stars.

---

## 2. Eligibility & Boundary Criteria

1. **Category Relevance:** The repository must directly support developer workflows with LLMs, autonomous agents, prompt execution, vector embeddings, model serving, or MCP connectivity.
2. **Multi-Ecosystem Presence:** Must possess at least one primary GitHub repository and at least one package distribution registry (PyPI, npm, or Hugging Face Hub).
3. **Exclusion Criteria:**
   - General-purpose utility libraries (e.g. `requests`, `numpy`, `express`) without specific LLM bindings.
   - Closed-source commercial products with no public repository or open package client.
   - Obvious clones or school assignment forks with < 50 stars.

---

## 3. Mapping Confidence Standards (Hypothesis H3)

Every entity mapping is assigned one of three mutually exclusive confidence grades:

1. **`verified` (Highest Standard):**
   - The package registry metadata (e.g. `pyproject.toml` / `package.json` `repository` or `homepage` URL) points explicitly to the GitHub repository **AND** the GitHub repository README / documentation links back to the package, OR confirmed by official organization namespace ownership (e.g. `langchain-ai` owning `langgraph`).
   - *Only `verified` mappings feed published Footfall metrics and backtest scores.*
2. **`declared`:**
   - One-way metadata link only (e.g. package states GitHub repo, but GitHub repo does not link the package, or vice versa).
3. **`heuristic`:**
   - Name match or fuzzy match without verifiable reciprocal metadata links.
   - Reported only in coverage audit tables; excluded from index calculations.

**H3 Success Gate:** At least **95%** of seed registry mappings must achieve `verified` status.
