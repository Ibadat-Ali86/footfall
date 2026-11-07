# Footfall Data Dictionary

Version: `m1.0`  
Authoritative schema reference for all tabular, Parquet, and static JSON data artifacts.

---

## 1. Raw Snapshots (`snapshots.parquet` / `data/raw/YYYY-MM-DD.parquet`)

The append-only immutable daily snapshot table recording observations across all external developer platforms.

| Column | Type | Nullable | Description | Allowed Values / Format |
|---|---|---|---|---|
| `entity_id` | VARCHAR | No | Canonical identifier of the tool or library | `^[a-z0-9-]+$` |
| `source` | VARCHAR | No | Originating platform | `github`, `pypi`, `npm`, `hf`, `hn` |
| `metric` | VARCHAR | No | Name of the observed metric | `downloads`, `stars`, `mentions`, `models` |
| `obs_date` | VARCHAR | No | Observation date (UTC calendar date) | `YYYY-MM-DD` |
| `value` | DOUBLE | No | Quantitative measurement | $\ge 0.0$, non-negative, finite |
| `quality` | VARCHAR | No | Ingestion quality flag | `ok`, `truncated`, `provisional`, `interpolated` |
| `collected_at` | VARCHAR | No | Ingestion timestamp | ISO 8601 UTC `YYYY-MM-DDTHH:MM:SSZ` |
| `collector_version` | VARCHAR | No | Collector module code version | `v1.0.0` |

---

## 2. Seed Registry (`registry/seed.yaml`)

Catalog of all monitored AI developer tools, frameworks, and model libraries.

| Field | Type | Description |
|---|---|---|
| `entity_id` | string | Unique primary key (e.g. `langchain`, `qdrant`) |
| `display_name` | string | Human-readable name |
| `category` | string | Functional category (`agent-framework`, `llm-sdk`, `vector-store`, `eval-tool`, `mcp-server`, `model`) |
| `tags` | list[string] | Descriptive keywords |
| `sources` | list[SourceMapping] | Platform identifiers and confidence tiers (`verified`, `declared`, `heuristic`) |
| `notes` | string | Curation and provenance rationale |

---

## 3. Weekly Features (`src/footfall/features/`)

Point-in-time sequential weekly features calculated every Monday 06:00 UTC with zero lookahead.

| Feature | Definition | Range | Purpose |
|---|---|---|---|
| `W` | Total weekly downloads (ISO Monday to Sunday) | $[0, \infty)$ | Raw weekly adoption volume |
| `L` | Log-transformed volume: $\ln(W + 1)$ | $[0, \infty)$ | Scale-stabilized adoption metric |
| `g4` | 4-week growth: $\ln((W_t + 1) / (W_{t-4} + 1))$ | $(-\infty, \infty)$ | Short-term momentum |
| `g12` | 12-week growth: $\ln((W_t + 1) / (W_{t-12} + 1))$ | $(-\infty, \infty)$ | Quarterly trend |
| `s28` | Net star gain over prior 28 days | $[0, \infty)$ | 4-week public attention |
| `adoption_z` | Robust z-score of $g_4$ normalized within category | $(-\infty, \infty)$ | Category-relative adoption acceleration |
| `attention_z` | Robust z-score of $s_{28}$ normalized within category | $(-\infty, \infty)$ | Category-relative attention surge |
| `divergence` | $D = \text{attention\_z} - \text{adoption\_z}$ | $(-\infty, \infty)$ | Gap between public attention and actual package usage |

---

## 4. Lifecycle Phases (`src/footfall/phase/`)

Table-driven discrete classification evaluated strictly in first-match-wins order:

1. `insufficient_data`: Fewer than 12 weeks of downloads or 56 days of stars.
2. `breakout`: $\text{adoption\_z} \ge 1.0$ and $g_4 \ge \ln(1.25)$ and $W \ge 500$.
3. `attention_ahead`: $D \ge 1.0$ and $\text{adoption\_z} < 0.5$ (high buzz, lagging usage).
4. `use_ahead`: $D \le -1.0$ and $\text{adoption\_z} \ge 0.5$ (high real adoption, quiet social buzz).
5. `fading`: $\text{adoption\_z} \le -1.0$ and $g_{12} < 0$ for 4 consecutive weeks.
6. `emerging`: Age under 6 months and none of the above.
7. `mainstream`: $W$ in top quartile of category and $|g_4| < 0.1$.
8. `plateau`: $|g_{12}| < 0.1$ for 8 consecutive weeks.

---

## 5. Call Ledger (`data/ledger/calls.jsonl`)

Cryptographically chained append-only evaluation ledger.

| Field | Type | Description |
|---|---|---|
| `call_id` | string | Unique call identifier: `call_{as_of}_{entity_id}` |
| `entity_id` | string | Target tool ID |
| `category` | string | Tool category |
| `as_of` | string | Evaluation date (`YYYY-MM-DD`) |
| `phase` | string | Assigned lifecycle phase |
| `p_breakout_30d` | float / null | Calibrated breakout probability |
| `method_version` | string | Pipeline method version (`m1.0`) |
| `features_hash` | string | SHA-256 of input feature vector |
| `prev_hash` | string | SHA-256 hash of previous ledger row |
| `record_hash` | string | SHA-256 of current record: `SHA256(prev_hash \|\| canonical_json)` |
| `supersedes` | string / null | Pointer to replaced call_id if corrected |
| `timestamp` | string | Generation timestamp in ISO 8601 |
