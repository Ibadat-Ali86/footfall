# Privacy Policy

**Effective Date:** 2026-11-08  
**Version:** 1.0.0  
**Contact:** privacy@footfall.dev  

---

## 1. Overview and Scope

Footfall ("we", "our", or "the Service") provides public software adoption analytics and model-context protocol (MCP) serving for AI developer tools. This Privacy Policy explains our commitment to data minimization, privacy by design, and how we process information when you interact with our public APIs, MCP server, and static documentation.

---

## 2. Information We Process

### 2.1 Public Software Metadata (Aggregates Only)
- Footfall aggregates publicly available software metadata from GitHub, PyPI, npm, and Hugging Face.
- **Strict Data Minimization:** We store **zero** per-person data. We do not store GitHub usernames, account identifiers, stargazer profile information, commit author emails, or contributor identities. All stargazers and downloads are processed strictly in volatile memory as numerical aggregates (counts, dates, and distributions).
- Our published datasets and hash-chained ledgers contain only aggregate metrics, repository names, and package identifiers.

### 2.2 Server and Network Logs
When you connect to the Footfall MCP server or static dashboard:
- **Tool Inputs:** The server processes tool inputs (e.g., entity names such as `langgraph` or `qdrant-client`) strictly in volatile memory to construct query responses. Tool inputs are never associated with user accounts.
- **Client IP Addresses:** IP addresses are processed at the edge strictly for rate limiting (token bucket: 60 requests/minute, burst 20) and DDoS defense. If edge logs are retained for security auditing, IP addresses are cryptographically hashed with a rotating salt and deleted within **14 days**.
- **No Cookies or Trackers:** Footfall uses **zero** cookies, zero third-party tracking scripts, zero web beacons, and zero telemetry SDKs. We do not support credentialed CORS.

---

## 3. How We Use Information

Information processed by Footfall is used solely for:
1. Serving empirical adoption and attention metrics via read-only MCP endpoints.
2. Defending API infrastructure against abuse, denial-of-service, and DNS rebinding attacks.
3. Conducting reproducible scientific backtesting of developer tool adoption.

We **never** sell, rent, monetize, or broker any data to third parties.

---

## 4. Third-Party Services and Attribution

- **Hacker News Search:** Mention data from Hacker News is retrieved via the Algolia API. Aggregates and counts are attributed ("Search by Algolia").
- **Upstream Registries:** Package metadata is retrieved from npm, PyPI, and GitHub under their respective public API terms of service.

---

## 5. Maintainer Rights and Right of Removal

Maintainers of tracked open-source repositories possess explicit rights:
- **Badge Removal:** Maintainers may opt out of repository tracking or request badge removal at any time by opening an issue on GitHub or emailing `privacy@footfall.dev`. Removal requests are honored within 5 business days.
- **Dispute Process:** If your repository displays an unusual activity flag, you have an immediate right of reply and dispute resolution under our [Dispute Process](dispute-process.md).

---

## 6. Security and Compliance

We implement administrative and technical controls to safeguard infrastructure:
- All communications enforce TLS 1.2+ and HSTS.
- Our MCP server is stateless, read-only, and enforces strict Origin header verification against DNS rebinding.
- See our [SECURITY.md](../SECURITY.md) for full vulnerability disclosure and threat model documentation.

---

## 7. Changes to this Policy

Any updates to this policy will be documented in our public version-controlled repository with a bumped version number and timestamp.
