# Gate G2 — Upstream Data Sources Terms of Service Review

**Date of Review:** 2026-11-07  
**Author:** AI Coding Agent (draft)  
**Approver:** Human Owner (Gate G2 requirement)  
**Status:** PENDING HUMAN APPROVAL (Required before any public data release)

---

## 1. Terms Review Summary Table (Section 7.4)

| Source | Official Terms URL | Redistribution of Derived Aggregates | Mandatory Attribution | Rate-Limit Policy | Verdict |
|---|---|---|---|---|---|
| **GitHub** | [GitHub Acceptable Use Policies](https://docs.github.com/en/site-policy/acceptable-use-policies/github-acceptable-use-policies) & [REST/GraphQL API Terms](https://docs.github.com/en/rest/overview/resources-in-the-rest-api#rate-limiting) | **Permitted for Aggregates.** Storing public repo metrics (stars, forks, open issues) is permitted. Mass-harvesting personal profiles or raw user data is prohibited. | Not strictly required for raw metrics, but recommended: *"Data from GitHub API"*. Respect repository licenses. | **5,000 req/hr** (authenticated with `GH_READONLY_TOKEN`). Secondary limits apply on burst/expensive GraphQL queries. | **PERMITTED** (with strict privacy guard: discard stargazer IDs in memory) |
| **npm** | [npm Open Source Terms](https://docs.npmjs.com/policies/open-source-terms) & [API Limits](https://github.com/npm/feedback/discussions) | **Permitted.** Public download statistics (`api.npmjs.org/downloads`) are public telemetry. Redistribution of daily download aggregates is permitted for analytics and badges. | None legally mandated. Standard attribution: *"Download statistics provided by npm public API"*. | **No static documented limit**, but IP-based throttling triggers HTTP 429. Range queries silently truncate past **18 months**. Capped at **128 packages** per bulk query. | **PERMITTED** (enforce 200–500ms delay, chunk ranges to ≤18 months, cache daily) |
| **PyPI & pypistats** | [Python Software Foundation Terms](https://www.python.org/psf/terms/) & [pypistats About / Etiquette](https://pypistats.org/about) | **Permitted with Etiquette.** Daily download statistics are derived from the public `bigquery-public-data.pypi` dataset. Redistribution of aggregates is permitted. | Acknowledge: *"PyPI download data sourced from pypistats.org and PSF BigQuery public dataset"*. | **pypistats.org:** Strict IP-based limit (~1 req/sec). Explicit rule: **Do NOT bulk-download full history via JSON API**. Must use BigQuery for backfills (1 TB/mo free tier). | **PERMITTED** (daily updates via pypistats with 1 RPS throttle; historical backfill via BigQuery) |
| **Hugging Face** | [Hugging Face Terms of Service](https://huggingface.co/terms) & [Hub API Rate Limits](https://huggingface.co/docs/hub/rate-limits) | **Permitted.** Querying and redistributing public model metadata (downloads, likes) is permitted. Do not bulk-scrape raw repository assets or weights. | Credit *"Data sourced from Hugging Face Hub"*. Individual model licenses must be respected if distributing descriptions. | **Anonymous:** ~500 Hub API requests per 5-min window. **Free Authenticated:** ~1,000 requests per 5-min window. HTTP 429 with standard `ratelimit` headers. | **PERMITTED** (query metadata only; respect HTTP 429 and exponential backoff) |
| **Hacker News & Algolia** | [Algolia Terms of Service](https://www.algolia.com/policies/terms/) & [HN Search API](https://hn.algolia.com/api) | **Permitted for Aggregates.** Aggregating story counts and points linking to specific repository URLs is permitted. No user comment text or personal identifiers stored. | **Mandatory**: Must display *"Search by Algolia"* and link to `https://www.algolia.com` when presenting search-derived metrics. | **10,000 requests/hour per IP**. Pagination capped at first 1,000 hits per query. | **PERMITTED** (URL matching only, mandatory "Search by Algolia" attribution) |

---

## 2. In-Depth Source Analysis & Operational Safeguards

### 2.1 GitHub
- **Risk:** Star-burst anomaly sampling (Section 10.3) inspects stargazer account age and repository count.
- **Safeguard (Threat #10):** Stargazer IDs (usernames, user IDs) are processed **in-memory only** to compute `low_quality_share`. **Never** write usernames or per-person data to disk, Parquet files, or logs.
- **API Guard:** Monitor `X-RateLimit-Remaining` header. Back off exponentially if remaining calls fall below 100.

### 2.2 npm
- **Risk:** Silent truncation on date ranges exceeding 18 months, causing false signals of declining adoption.
- **Safeguard (Section 7.1 rule 7):** Verify `response.start == request.start`. If npm returns a later start date than requested, mark the snapshot `quality = truncated`.
- **API Guard:** Use bulk endpoint for up to 128 unscoped packages. For scoped packages (`@org/pkg`), query individually with a 250ms inter-request sleep.

### 2.3 PyPI & pypistats
- **Risk:** Getting IP-banned by pypistats.org for aggressive bulk historical scraping.
- **Safeguard (Section 7.2 & 15.4):** 
  - Daily incremental collector uses `pypistats.org` at ≤ 1 request per second.
  - Phase 0 backfill (T0.7) queries the Google BigQuery public dataset `bigquery-public-data.pypi.file_downloads` with a strict `maximum_bytes_billed` cap (dry-run first).

### 2.4 Hugging Face
- **Risk:** Cloud runner IP addresses sharing NAT egress can hit the 500 requests/5-min anonymous limit.
- **Safeguard:** Cache responses locally per observation date. Enforce collector retry with `tenacity` on HTTP 429 adhering to `ratelimit-reset`.

### 2.5 Hacker News / Algolia
- **Risk:** Attribution breach or noisy name matches.
- **Safeguard (Section 7.2):** 
  - Restrict queries to exact repository URL matching (`restrictSearchableAttributes=url`).
  - Render "Search by Algolia" in the dashboard methodology page, MCP tool documentation, and open dataset card.

---

## 3. Human Approval & Release Gate (Gate G2)

Per Section 19.2 of `docs/BUILD.md`, Gate G2 must be explicitly authorized by the human owner before any public dataset or MCP server endpoint is released.

- [ ] Reviewed terms URLs and redistribution boundaries.
- [ ] Confirmed privacy policy requirements (in-memory aggregation only).
- [ ] Approved Algolia attribution placement.
- [ ] **Verdict:** [ ] APPROVED FOR PUBLIC DATA RELEASE  /  [ ] REVISE RESTRICTIONS

**Human Sign-off Date:** ___________________  
**Signature:** ___________________
