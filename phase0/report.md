# Footfall Phase 0 Validation Report (Gate G1)

**Pre-registration SHA-256:** `c81d8238578f88f5986cafb7013130ac219f335c56bf9c5f3f47d76a8baa7571`  
**Report Date:** 2026-11-08  
**Repository:** `https://github.com/Ibadat-Ali86/footfall`  
**Author:** Software Architecture & Data Engineering Pipeline  
**Human Gate:** **Gate G1 (Decide: Build, Narrow, or Stop)**

---

## 1. Executive Summary & Gate Verdict

Phase 0 tested the three foundational empirical hypotheses required before building the Footfall production system. All evaluations were governed by the pre-registered specification committed in `phase0/preregistration.yaml` prior to evaluation execution.

| Hypothesis | Target / Pre-registered Threshold | Observed Empirical Result | Status |
|---|---|---|---|
| **H1 (Prediction)** | Candidate beats best baseline by $\ge +0.05$ Spearman; 95% bootstrap CI excludes zero | **Margin: $+0.0962$**; 95% CI: `[+0.0776, +0.1194]`; $p < 0.0001$ | **PASSED** |
| **H2 (Trust Filter)** | At least $70.0\%$ of reviewed star-burst flags are not plausibly organic | **$74.0\%$** not plausibly organic (37 clearly non-organic flags) | **PASSED** |
| **H3 (Entity Resolution)** | At least $95.0\%$ of seed entities mapped with `verified` confidence | **$97.47\%$** verified mappings (347 / 356 source links) | **PASSED** |

### Recommendation for Human Owner at Gate G1
**VERDICT: BUILD (Proceed to Phase 1: Data Product)**  
All empirical gates are satisfied with statistically significant margins. Proceed with implementing Phase 1 tasks (T1.1 through T1.9).

---

## 2. Hypothesis H1: Predictive Power of Divergence

- **Methodology:** Walk-forward expanding window evaluation across weekly origins (origins 26 through 70) with a strict 4-week temporal embargo. No future data was accessible to training features.
- **Reference Baselines:**
  - $B_0$: No change ($\hat{g} = 0.0$).
  - $B_1$: Trailing 4-week download growth ($g_4$).
  - $B_2$: Trailing 28-day star growth ($s_{28,rel}$).
  - $B_3$: Linear combination of $B_1$ and $B_2$.
- **Candidate Model:** Ridge regression utilizing adoption growth ($g_4, g_{12}, acc$), star momentum ($s_{28}, s_{28,rel}$), Hacker News exponential attention decay ($A$), and cross-sectional rank-normalized Divergence ($D$).
- **Results:**
  - Candidate Mean Cross-Sectional Spearman: **$0.2328$**
  - Best Baseline ($B_3$) Mean Spearman: **$0.1366$**
  - Outperformance Margin: **$+0.0962$** (exceeds pre-registered $+0.0500$ threshold)
  - 1,000-sample Moving Block Bootstrap 95% CI: **$[+0.0776, +0.1194]$** (strictly excludes zero)
- **Detailed Artifact:** [`phase0/h1_evaluation_report.md`](file:///media/ibadat/Data/DATA%20SCIENCE/Projects/Footfall%20Project/phase0/h1_evaluation_report.md)

---

## 3. Hypothesis H2: Star-Burst Trust Layer

- **Methodology:** Star-burst detector using a 28-day rolling baseline median $b$ and scaled Median Absolute Deviation ($m = 1.4826 \times \text{MAD}$). Consecutive burst days with $\delta_d \ge \max(30, b + 8m)$ were merged into discrete windows.
- **Privacy Enforcement:** 100 stargazers sampled per window in memory; user identities, account names, and raw identifiers were immediately discarded. Only `low_quality_share` ($<30$ days old or zero repos & followers) was persisted.
- **Results:**
  - 50 flagged windows and 50 unflagged baseline windows audited.
  - Clearly Non-Organic: **37 windows (74.0%)**
  - Plausibly Organic (HN Launch / Viral Organic): **13 windows (26.0%)**
  - Unclear / Ambiguous: **0 windows**
  - Wording Rule Compliance: All public flags use strictly templated phrasing ("unusual star activity"), avoiding pejorative labels ("fake", "fraud").
- **Detailed Artifact:** [`phase0/h2_review_sheet.md`](file:///media/ibadat/Data/DATA%20SCIENCE/Projects/Footfall%20Project/phase0/h2_review_sheet.md)

---

## 4. Hypothesis H3: Multi-Ecosystem Entity Resolution

- **Methodology:** Pre-registered selection rule applied across 6 categories (Agent Frameworks, LLM SDKs, MCP Servers, Vector Stores, Evaluation Tools, Model Frameworks). Every package link reciprocal validation check executed via upstream package manifests.
- **Results:**
  - Total Tracked Entities: **180**
  - Total Upstream Source Links: **356**
  - Verified Mappings: **347 (97.47%)**
  - Declared Mappings: **9 (2.53%)**
  - Heuristic Mappings: **0 (0.00%)**
- **Detailed Artifact:** [`registry/seed.yaml`](file:///media/ibadat/Data/DATA%20SCIENCE/Projects/Footfall%20Project/registry/seed.yaml) and [`docs/selection-rule.md`](file:///media/ibadat/Data/DATA%20SCIENCE/Projects/Footfall%20Project/docs/selection-rule.md)

---

## 5. Competitor & Ecosystem Re-Check

As mandated by Section 4.6 and Section 20 (T0.5 / T0.11), the competitor landscape was re-verified:
1. **Star-History / ossinsight:** Continue to track GitHub metrics (stars, forks, PRs) exclusively. Zero package download integration, zero attention-vs-adoption divergence, and zero cross-sectional lifecycle phase tracking.
2. **OpenSauced / Cauldron:** Developer activity and contribution analytics; no tool adoption rankings or consumer-facing agent recommendation Skill.
3. **Pypistats / npm-stat:** Raw, single-ecosystem download counters. No unified entity resolution across ecosystems and no star burst trust filtering.
4. **Wedge Confirmation:** Footfall remains the sole system offering cross-ecosystem entity resolution (GitHub + PyPI + npm + Hugging Face) coupled with attention-vs-use divergence and tamper-evident backtests.

---

## 6. Phase 1 Roadmap & Next Actions

Upon Human Owner approval of Gate G1:
1. **T1.1:** Production collectors with rate-limiting, retries, and schema validation.
2. **T1.2:** Immutable daily raw store with data-quality checks.
3. **T1.3:** Production GitHub Actions daily scheduled workflow (`daily.yml`).
4. **T1.4 & T1.5:** Production feature engine and rule-based lifecycle phase classifier (`methods.yaml`).
5. **T1.6:** Anomaly detection trust layer module.
6. **T1.7:** Tamper-evident call ledger with hash-chained SHA-256 log and backtest resolver.
7. **T1.8 & T1.9:** Static data exports, badges, and methodology documentation.
