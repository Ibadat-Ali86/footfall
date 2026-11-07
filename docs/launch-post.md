# Introducing Footfall: Measuring Real Developer Adoption vs Attention

**Published:** 2026-11-08  
**Method Version:** [`m1.0`](docs/methodology.md)  
**Ledger Proof:** [SHA-256 Chained](data/ledger/chain.jsonl)  

---

### The Vanity Metric Problem in AI Developer Tools

GitHub stars and social buzz dominate modern open-source discussions. However, social bookmarks do not equal production software deployments. A project can accumulate thousands of stars over a weekend through launch hype, paid campaigns, or viral demos while maintaining near-zero active dependency integration. Conversely, essential utility libraries quietly power mission-critical software pipelines with minimal social visibility.

**Footfall** is an open-source, reproducible measurement system and Model Context Protocol (MCP) server designed to separate real production adoption from social attention across [`180`](registry/seed.yaml) curated AI developer tools.

---

### Core Methodology

Footfall operates on weekly calendar boundaries (Monday 00:00 UTC) with zero lookahead bias. The system tracks two primary orthogonal dimensions:

1. **Adoption Velocity ($W, L, g_4$):** Weekly download volumes from verified package manager registries (npm and PyPI). Log-ratio growth $L = \ln\left(\frac{W_t + 1}{W_{t-4} + 1}\right)$ is normalized into an adoption z-score using robust rolling statistics (Median and Median Absolute Deviation) within each ecosystem category.
2. **Attention Velocity ($s_{28}$):** [`28-day`](docs/methodology.md) net GitHub star gains, filtered through an automated Poisson burst detector to exclude sudden non-organic spikes.
3. **Divergence ($D$):** Computed as $D = \text{attention\_z} - \text{adoption\_z}$. 
   - A negative divergence ($D < -1.0$) flags `use_ahead` tools where real usage leads social buzz.
   - A positive divergence ($D > 1.0$) flags `attention_ahead` tools where hype substantially exceeds package installs.

Full mathematical formulas are documented in our [Methodology](docs/methodology.md).

---

### Walk-Forward Empirical Evidence

We evaluate predictive performance through an expanding-window walk-forward backtest across [`104`](data/backtest/manifest.json) historical weeks, covering [`7,248`](data/backtest/manifest.json) resolved classification decisions.

- **Hypothesis H1 Verification:** The multi-signal candidate achieved a mean Spearman rank correlation margin of [`+0.0962`](phase0/h1_evaluation_report.md) over the best single-signal baseline, with a [`95%`](phase0/h1_evaluation_report.md) bootstrap confidence interval of `[+0.0776, +0.1194]`.
- **Breakout Hit Rate:** Tools classified into the `breakout` phase sustained adoption velocity above the category median in [`68.4%`](data/backtest/latest.json) of instances over the subsequent [`12`](data/backtest/latest.json) weeks (compared to a random baseline of [`32.1%`](data/backtest/latest.json)).
- **Cryptographic Reproducibility:** Every backtest prediction is committed to a SHA-256 hash-chained ledger. Anyone can verify the exact bit-for-bit results by cloning the repository and running:
  ```bash
  make reproduce
  ```

---

### Accessing Footfall

1. **Model Context Protocol (MCP) Server:**  
   Connect your AI assistant (Claude, Cursor, ChatGPT) to our read-only Streamable HTTP endpoint:
   ```json
   {
     "mcpServers": {
       "footfall": {
         "command": "uvx",
         "args": ["footfall", "serve", "--stdio"]
       }
     }
   }
   ```
   Tools provided: `footfall_compare`, `footfall_trend`, and `footfall_find_rising`.

2. **Static Dashboard:**  
   Inspect interactive leaderboards and time-series charts at [https://footfall.dev](https://footfall.dev). Fully static, zero third-party trackers, and keyboard accessible.

3. **Public Data Exports:**  
   Daily Parquet datasets, JSON profiles, and Shields.io maintainer badges are published under Creative Commons Attribution 4.0 International ([CC BY 4.0](docs/terms-of-use.md)).

---

### Limitations & Ethical Commitments

- **Not Financial Advice:** Footfall provides quantitative measurements of software repository activity. Outputs do not constitute investment, financial, or purchasing advice. Predictions are probabilistic and can be wrong.
- **Objective Wording:** Outlier events are labeled objectively as "unusual velocity" and never use accusatory phrasing.
- **Maintainer Right of Reply:** Maintainers can review flags, provide context, or request removal under our [Dispute Process](docs/dispute-process.md).
- **Data Minimization:** Footfall persists aggregates only. Zero individual stargazers, user IDs, or contributor names are ever stored.
