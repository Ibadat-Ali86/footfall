# Security Policy

**Effective Date:** 2026-11-08  
**Scope:** Footfall Pipeline, MCP Server, and Data Artifacts  
**Security Contact:** security@footfall.dev  

---

## 1. Reporting a Vulnerability

Footfall takes the security of its infrastructure, public data pipelines, and downstream MCP consumers seriously. If you discover a security vulnerability, do **not** open a public issue.

Please report vulnerabilities through one of the following channels:
1. **GitHub Private Vulnerability Reporting:** Navigate to the **Security** tab of `Ibadat-Ali86/footfall` and click **Report a vulnerability**.
2. **Encrypted Email:** Send details to `security@footfall.dev`.

### Response SLA
- **Initial Acknowledgment:** Within **24 hours**.
- **Triage and Impact Assessment:** Within **72 hours**.
- **Patch Deployment & Coordinated Disclosure:** Within **14 business days** (or sooner for critical severity issues).

---

## 2. Threat Model & Architectural Controls

Footfall enforces defense-in-depth across 13 core threat vectors:

| # | Threat Vector | Architectural Mitigation |
|---|---|---|
| 1 | **Prompt Injection** via third-party text | Zero third-party free text in outputs. Package descriptions, READMEs, and HN comments are never ingested or echoed. Only computed numbers, verified names, and fixed caveat templates are emitted. |
| 2 | **Ranking Gaming** (bought stars, fake downloads) | Adoption z-score requires sustained package usage. Volume floors. Download step detection (median/MAD). Burst detection with neutral labeling. |
| 3 | **SSRF / Open Redirect** | Hardcoded upstream host allowlist (GitHub, npm, PyPI, Hugging Face, Algolia). Reject all cross-host redirects. |
| 4 | **Secret Leakage** | Read-only fine-grained tokens (`GH_READONLY_TOKEN`). Secrets restricted to protected GitHub Actions environments. Secret scanning via `gitleaks` in CI. |
| 5 | **Dependency Compromise** | Locked dependency hashes (`uv.lock`). Minimum package version age of **14 days**. Automated vulnerability scanning via `pip-audit` and OSV. |
| 6 | **CI/CD Poisoning** | Third-party GitHub Actions pinned to full commit SHAs. Least-privilege GITHUB_TOKEN permissions (`contents: read`). Concurrency locks. |
| 7 | **Data Tampering** | Cryptographically chained SHA-256 ledger (`make reproduce`). Pipeline deployment keys restricted to isolated `footfall-data` repository. |
| 8 | **Denial of Service** | Stateless architecture backed by precomputed static files. Edge rate limiting: 60 req/min, burst 20. Strict 50 KB response byte cap. |
| 9 | **Defamation / Reputational Harm** | Neutral non-accusatory terminology ("unusual", never "fake" or "fraud"). Transparent dispute and right-of-reply process. |
| 10 | **Personal Data Exposure** | Zero usernames, user IDs, or contributor PII persisted. Stargazer samples aggregated strictly in volatile memory. |
| 11 | **DNS Rebinding** | Strict `Origin` header validation in ASGI middleware. No cookies. No wildcard credentials. |
| 12 | **Misleading Claims** | Public claims verifier script (`scripts/verify_public_claims.py`). Every statistical claim is tied to an authoritative data path. |
| 13 | **Coding Agent Manipulation** | All external data treated strictly as untrusted passive data. Never execute shell scripts downloaded from external sources. |

---

## 3. Operational Runbooks

### 3.1 Kill Switch Activation
In the event of an emergency (e.g., zero-day upstream vulnerability, data corruption, or active abuse):
1. In the hosting provider environment (or container runtime), set the environment variable:
   ```bash
   FOOTFALL_KILL_SWITCH=1
   ```
2. Trigger an immediate restart or rolling deployment.
3. The server's `KillSwitchMiddleware` immediately intercepts all incoming traffic to `/mcp` and `/health/ready`, returning `HTTP 503 Service Unavailable` with structured code `"data_unavailable"`. The `/health/live` probe remains functional for container lifecycle management.

### 3.2 Secret and Deploy Key Rotation
If a GitHub PAT or Deploy Key is suspected of exposure:
1. **GitHub Deploy Key:**
   - Generate a new ED25519 keypair: `ssh-keygen -t ed25519 -C "footfall-deploy-$(date +%Y%m%d)" -f deploy_key`
   - Add public key to `footfall-data` repository Deploy Keys with write access.
   - Update `DATA_DEPLOY_KEY` secret in `footfall` repository `pipeline` Actions environment.
   - Delete the old deploy key from `footfall-data`.
2. **GitHub Read-Only Token:**
   - Generate a new Fine-Grained Personal Access Token with read-only access to public repository metadata.
   - Update `GH_READONLY_TOKEN` secret in the `pipeline` Actions environment.
   - Revoke the old token immediately.
