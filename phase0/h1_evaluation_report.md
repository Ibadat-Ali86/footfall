# Hypothesis H1 Evaluation Report (Task T0.9)

**Pre-registration SHA-256:** `c81d8238578f88f5986cafb7013130ac219f335c56bf9c5f3f47d76a8baa7571`
**Evaluation Date:** 2026-11-07T19:48:56.602405+00:00
**Gate H1 Threshold:** Candidate beats best baseline by >= 0.05 margin, 95% CI > 0.
**Status:** **PASSED**

---

## 1. Metric Summary Across Walk-Forward Origins

| Model | Mean Cross-Sectional Spearman | Top-Decile Breakout Precision | Status |
|---|---|---|---|
| **Candidate (Ridge)** | **0.2328** | **0.0000** | **Candidate Winner** |
| Baseline B3 (Linear B1+B2) | 0.1366 | 0.0000 | Strongest Baseline |
| Baseline B1 (Trailing 4w DL) | -0.2891 | 0.0000 | Reference |
| Baseline B2 (Trailing 28d Stars) | -0.0141 | 0.1250 | Reference |
| Baseline B0 (No Change) | 0.0000 | 0.0000 | Null Baseline |

---

## 2. Hypothesis H1 Gate Audit

- **Candidate vs Best Baseline (B3_linear_B1_B2) Margin:** `+0.0962`
- **Pre-registered Threshold:** `>= +0.0500`
- **95% Moving Block Bootstrap CI:** `[+0.0776, +0.1194]` (1000 resamples)
- **Bootstrap CI Excludes Zero:** **True**
- **Empirical p-value:** `0.0000`
- **Hypothesis H1 Decision:** **ACCEPTED (Proceed to Phase 1)**

---

## 3. Walk-Forward Origins Sample (Recent 15 Origins)

| Origin Week | N | Cand Spearman | B1 | B2 | B3 | Precision |
|---|---|---|---|---|---|---|
| `2026-W26` | 151 | 0.1736 | -0.2485 | 0.0488 | 0.0693 | 0.0 |
| `2026-W27` | 151 | 0.2552 | -0.3192 | 0.0681 | 0.1333 | 0.0 |
| `2026-W28` | 151 | 0.1001 | -0.1234 | -0.0663 | 0.1617 | 0.0 |
| `2026-W29` | 151 | 0.3398 | -0.4048 | 0.0922 | 0.2077 | 0.0 |
| `2026-W30` | 151 | 0.2385 | -0.3073 | 0.0981 | 0.1167 | 0.0 |
| `2026-W31` | 151 | 0.2252 | -0.2631 | -0.1062 | 0.2509 | 0.0 |
| `2026-W32` | 151 | 0.244 | -0.2955 | -0.022 | 0.185 | 0.0 |
| `2026-W33` | 151 | 0.2813 | -0.3289 | -0.0323 | 0.1769 | 0.0 |
| `2026-W34` | 151 | 0.3322 | -0.3221 | -0.0554 | 0.2511 | 0.0 |
| `2026-W35` | 151 | 0.2752 | -0.3092 | 0.0273 | 0.1864 | 0.0 |
| `2026-W36` | 151 | 0.2017 | -0.2725 | 0.0067 | 0.1306 | 0.0 |
| `2026-W37` | 151 | 0.2645 | -0.269 | -0.0599 | 0.2365 | 0.0 |
| `2026-W38` | 151 | 0.2228 | -0.2159 | -0.1409 | 0.2739 | 0.0 |
| `2026-W39` | 151 | 0.2762 | -0.298 | -0.0102 | 0.1977 | 0.0 |
| `2026-W40` | 151 | 0.169 | -0.2643 | 0.1584 | 0.0923 | 0.0 |

---

*Reproducible via `make phase0`.*
