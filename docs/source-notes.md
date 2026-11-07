# Upstream Source Facts & Empirical Specifications (Task T0.6)

**Last Updated:** 2026-11-08  
**Scope:** Verified empirical behavior, rate limits, pagination boundaries, and technical caveats for all 5 Footfall collectors. Replaces previous `[Unknown]` and `[Likely]` labels from `docs/BUILD.md` Section 7.2.

---

## 1. GitHub API

### 1.1 Authentication & Quotas
- **Personal Access Token (`GH_READONLY_TOKEN`):** 5,000 points/hour for GraphQL and REST APIs.
- **Actions Runner Default (`GITHUB_TOKEN`):** 1,000 points/hour per repository (in GHE/standard public repos). Using a dedicated fine-grained PAT is mandatory to ensure reliable daily runs without quota collisions.
- **Rate Limit Headers:** Every response provides `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and `X-RateLimit-Reset` (Unix epoch seconds).

### 1.2 GraphQL Batching (Daily Snapshots)
- Endpoint: `https://api.github.com/graphql`
- Strategy: Use GraphQL aliases to batch up to **50 repositories per query**.
- Payload Cost: ~1 GraphQL point per batch of 50 repositories (approximately 4–6 points total per daily run for 200 entities).
- Metrics queried: `stargazerCount`, `forkCount`, `openIssues: issues(states: OPEN)`, `pushedAt`, `isArchived`, `createdAt`, `latestRelease`.

### 1.3 REST Stargazers & Star-Burst Sampling
- Endpoint: `https://api.github.com/repos/{owner}/{repo}/stargazers`
- Media Type: `Accept: application/vnd.github.star+json` (required to receive `starred_at` timestamps).
- **Pagination Boundary (Empirical Fact):** GitHub's REST API paginates up to a maximum of 100 items per page and strictly caps pagination depth at **40,000 stargazers** (400 pages). Repositories with > 40,000 stars cannot be fully backfilled via public REST.
- **Privacy Enforcement:** Account age and public repo counts are sampled in volatile memory only. **Zero usernames or IDs are written to disk or logs.**

---

## 2. npm Downloads API

### 2.1 Endpoints & Depth Limits
- Point endpoint: `https://api.npmjs.org/downloads/point/{period}/{package}`
- Range endpoint: `https://api.npmjs.org/downloads/range/{start}:{end}/{package}`
- Bulk endpoint: `https://api.npmjs.org/downloads/range/{start}:{end}/{pkg1},{pkg2}...`

### 2.2 Critical Operational Gotchas
- **Silent Truncation:** The range endpoint returns at most ~**18 months** of daily history. If a requested `start` date precedes the 18-month rolling window, the API returns HTTP 200 but silently sets `start` in the JSON body to the truncated cutoff date.
- **Truncation Detection Rule:** The collector asserts `response["start"] == requested_start`. Any mismatch sets `quality = truncated`.
- **Bulk Limits:** Maximum of **128 packages** and **365 days** per bulk call. Scoped packages (e.g. `@langchain/langgraph`) are **not supported in bulk** and must be queried individually.
- **Timing:** Daily metrics for day $T$ are settled after 03:00 UTC on day $T+1$.

---

## 3. PyPI & pypistats

### 3.1 Daily Incremental (`pypistats.org`)
- Endpoint: `https://pypistats.org/api/packages/{package}/overall`
- Limits: IP-based throttling. Requests exceeding **1 request per second** risk HTTP 429.
- Name Normalization: PEP 503 normalization applies (lowercase, replace `_` with `-`).
- Depth: Approximately 180 days of rolling data.

### 3.2 Historical Backfill (`Google BigQuery`)
- Dataset: `bigquery-public-data.pypi.file_downloads`
- Free Quota: Google Cloud provides **1 TB of query processing free per month**.
- Dry-Run Guard: All BigQuery backfill queries must run `dry_run = True` first to calculate bytes scanned before execution.
- Partition Filter: Always filter on `file.project = '{package}'` and `DATE(timestamp) >= '{start_date}'` to prevent full table scans.

---

## 4. Hugging Face Hub API

### 4.1 Endpoints & Verified Fields
- Endpoint: `https://huggingface.co/api/models/{model_id}`
- Verified Payload Fields:
  - `downloads`: Total aggregate downloads across all files.
  - `likes`: Upstream community like count.
  - `lastModified`: ISO 8601 update timestamp.
- Quotas: ~500 requests per 5-minute window for unauthenticated IP; ~1,000 for authenticated.
- Response Headers: Standard `ratelimit` headers (`ratelimit-remaining`, `ratelimit-reset`).

---

## 5. Hacker News (Algolia Search API)

### 5.1 Endpoints & Precision Matching
- Endpoint: `https://hn.algolia.com/api/v1/search_by_date`
- Parameters:
  - `query={repo_url}` (e.g. `github.com/langchain-ai/langgraph`)
  - `restrictSearchableAttributes=url`
  - `tags=story`
  - `numericFilters=created_at_i>={timestamp}`
- Limits: **10,000 requests/hour per IP**.
- Attribution Requirement: **Mandatory display of "Search by Algolia"** with link to `https://www.algolia.com`.
