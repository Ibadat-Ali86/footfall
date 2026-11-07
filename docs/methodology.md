# Footfall Methodology

Authoritative specification of econometric models, feature definitions, lifecycle phase rules, and trust layers.

---

## 1. Principles

1. **Adoption Over Attention**: Real developers run `pip install` or `npm install` inside their applications and CI environments. Social stars indicate curiosity, while downloads represent real dependencies.
2. **Deterministic & Auditable**: Every lifecycle phase is determined by an allowlist table-driven rule with zero arbitrary heuristics.
3. **Cryptographic Proof**: Historical evaluation calls are recorded in a SHA-256 tamper-evident append-only ledger (`data/ledger/calls.jsonl`).
4. **Zero Per-Person Data**: No personal data, usernames, or account IDs are ever stored or logged.

---

## 2. Ingestion & Data Sources

Footfall tracks packages across multiple developer repositories:
- **PyPI & npm**: Daily download volume. Range queries are validated for server-side truncation flags.
- **GitHub**: Repository stars, fork counts, and release cadence.
- **Hugging Face**: Model downloads, likes, and spatial adoption metrics.
- **Hacker News (Algolia API)**: Discussion attention and front-page stories used to explain benign attention bursts.

Across our seed registry of [`180`](registry/seed.yaml) curated tools, [`97.47%`](phase0/report.md) of source mappings are confirmed through explicit verified repository links.

---

## 3. Sequential Feature Engineering

All features are calculated sequentially with point-in-time causality, mathematically eliminating lookahead leakage:

- **Weekly Volume ($W$)**: Monday-to-Sunday download sum.
- **Log-Adoption ($L$)**: $L = \ln(W + 1)$, providing variance stabilization across small and massive libraries.
- **4-Week Growth ($g_4$)**:
  $$g_4 = \ln\left(\frac{W_t + 1}{W_{t-4} + 1}\right)$$
- **12-Week Growth ($g_{12}$)**:
  $$g_{12} = \ln\left(\frac{W_t + 1}{W_{t-12} + 1}\right)$$
- **Adoption Acceleration (`adoption_z`)**: Robust z-score of $g_4$ computed against the cross-sectional median and MAD of all entities within the same category.
- **Attention Surge (`attention_z`)**: Robust z-score of net 28-day star gains within category.
- **Divergence ($D$)**: $D = \text{attention\_z} - \text{adoption\_z}$. Positive values indicate hype outpacing usage; negative values indicate silent adoption outpacing social buzz.

---

## 4. Discrete Lifecycle Phases

Phase classification evaluates the following rules in first-match-wins order:

| Order | Phase | Mathematical Condition | Interpretation |
|---|---|---|---|
| 1 | `insufficient_data` | History $< 12$ weeks or stars $< 56$ days | Inadequate sample for stable normalization |
| 2 | `breakout` | $\text{adoption\_z} \ge 1.0 \land g_4 \ge \ln(1.25) \land W \ge 500$ | Rapid real-world adoption acceleration |
| 3 | `attention_ahead` | $D \ge 1.0 \land \text{adoption\_z} < 0.5$ | Social curiosity running ahead of production use |
| 4 | `use_ahead` | $D \le -1.0 \land \text{adoption\_z} \ge 0.5$ | Heavy usage without proportional social attention |
| 5 | `fading` | $\text{adoption\_z} \le -1.0 \land g_{12} < 0$ for 4 consecutive weeks | Multi-month negative momentum |
| 6 | `emerging` | Age $< 6$ months and none of the above | Early-stage active new entrant |
| 7 | `mainstream` | $W$ in category top quartile $\land |g_4| < 0.1$ | Established industry baseline with stable scale |
| 8 | `plateau` | $|g_{12}| < 0.1$ for 8 consecutive weeks | Mature stable plateau |

---

## 5. Trust Layer & Anomaly Detection

### Star Bursts (Section 10)
Spikes in star gains exceeding $\max(30, \text{median}_{28} + 8 \times \text{MAD})$ are flagged for in-memory stargazer audit.
- In-memory sampling computes the share of low-activity accounts (account age $< 30$ days or zero repos and zero followers).
- **All account identities and usernames are discarded immediately**.
- Bursts are reported neutrally as "unusual star activity" when low-quality share $\ge 0.5$. Wording like "fake" or "fraud" is strictly prohibited.
- If a Hacker News launch story occurred within 48 hours, `explained_by = 'hn_story'` is attached to account for genuine launch attention.
- In Phase 0 audit sheets, [`74.0%`](phase0/h2_review_sheet.md) of examined spikes exhibited non-organic account characteristics.

### Download Steps (Section 9.9)
A rolling 26-week median and scaled MAD detects sudden volume jumps where $|z| \ge 4.0$. If no corresponding star or discussion activity occurred within 14 days, the jump is marked `download_step` with caveat "possible CI, mirror or bot traffic".

---

## 6. Backtest & Empirical Validation

In empirical walk-forward evaluation pre-registered under SHA-256 `c81d8238...`:
- Footfall's composite model outperformed the best baseline with a positive Spearman correlation margin of [`+0.0962`](phase0/h1_evaluation_report.md) ($95\%$ bootstrap confidence interval `[+0.0776, +0.1194]`).
- Across [`7,248`](data/backtest/manifest.json) sequential Monday evaluations, the backtest resolved [`100.0%`](data/backtest/manifest.json) of eligible forward windows.

---

## 7. Dispute Process

Package maintainers can dispute any classification or anomaly flag by submitting a review request via GitHub issues. Upon filing, the flag status is updated to `disputed` and hidden from public badges and endpoints until independent manual audit is concluded.
