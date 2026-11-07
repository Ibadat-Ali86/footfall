---
annotations_creators:
- machine-generated
language_creators:
- machine-generated
language:
- en
license: cc-by-4.0
multilinguality:
- monolingual
size_categories:
- 100K<n<1M
source_datasets:
- original
task_categories:
- tabular-classification
- time-series-forecasting
task_ids:
- time-series-forecasting
pretty_name: Footfall AI Developer Tool Adoption Index
tags:
- developer-tools
- time-series
- software-analytics
- adoption
- mcp
---

# Footfall: AI Developer Tool Adoption Index

**Version:** `m1.0`  
**License:** Creative Commons Attribution 4.0 International (CC BY 4.0)  
**Homepage:** [https://footfall.dev](https://footfall.dev)  
**Code Repository:** [https://github.com/Ibadat-Ali86/footfall](https://github.com/Ibadat-Ali86/footfall)  
**Data Repository:** [https://github.com/Ibadat-Ali86/footfall-data](https://github.com/Ibadat-Ali86/footfall-data)  

---

## 1. Dataset Summary

Footfall tracks real software adoption across the AI developer ecosystem by measuring package download volume and repository activity rather than vanity metrics. It pairs daily public registry observations (PyPI, npm, GitHub, Hugging Face, Hacker News) with temporal econometric feature engineering to classify tools into clear lifecycle phases (`breakout`, `use_ahead`, `attention_ahead`, `mainstream`, `plateau`, `fading`, `emerging`).

The dataset contains [[195,800]](phase0/data/snapshots.parquet) historical daily observation snapshots across [[180]](registry/seed.yaml) curated AI developer tools, covering 104 historical weeks (2024-11-04 to 2026-10-26).

---

## 2. Ingestion & Privacy Standards

- **Ingestion Cadence:** Daily snapshots ingested at 03:17 UTC.
- **Privacy Enforcement:** **Zero per-person data**. Usernames, user account IDs, and free text from third-party issues/pull requests are strictly discarded in volatile memory before persistence. Snapshots record aggregate counts only.
- **Lookahead Prevention:** Sequential point-in-time calculation ensures zero leakage across walk-forward boundaries.
- **Trust Layer:** Star bursts are flagged as "unusual star activity" through privacy-preserving in-memory analysis; download steps are detected with rolling robust median/MAD z-scores.

---

## 3. Dataset Structure

The published dataset consists of:
- `snapshots.parquet`: Daily tabular metrics across all monitored entities (Snappy-compressed).
- `calls.jsonl`: Weekly tamper-evident SHA-256 hash-chained evaluation ledger.
- `latest.json`: Backtest resolution report evaluating realized 4-week forward growth.
- `entities/<id>.json`: Static per-entity adoption profiles.

---

## 4. Known Caveats & Biases

1. **CI / Mirror Traffic:** Package manager download numbers include automated CI runs, container image builds, and registry mirrors. Download step anomalies flag unexplained jumps without corresponding community activity.
2. **Npm Query Truncation:** Npm range queries older than approximately 18 months silently truncate query start dates to the server retention window. These are explicitly tagged with `quality = truncated`.
3. **Star Discrepancies:** GitHub stars reflect social bookmarking and awareness; they often diverge from active code dependencies.

---

## 5. Dispute & Correction Process

Maintainers who believe an entity mapping or anomaly classification is in error can open an issue on the repository. Reviewed disputes receive `dispute_status = disputed`, hiding public anomaly flags pending resolution.
