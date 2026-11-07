# Gate G0 — Naming & Namespace Clearance Audit

**Date of Audit:** 2026-10-31  
**Auditor:** Human Owner (assisted by automated inspection)  
**Status:** PENDING HUMAN DECISION

---

## 1. Registry Availability Audit

| Registry / Namespace | Identifier | Status | Notes |
|---|---|---|---|
| **PyPI** | `footfall` | **AVAILABLE (404)** | Primary package name free |
| **PyPI** | `footfall-core` | **AVAILABLE (404)** | Fallback package name free |
| **PyPI** | `footfall-mcp` | **AVAILABLE (404)** | MCP server package name free |
| **npm** | `footfall` | ❌ **TAKEN (200)** | Owned by `nitinm21` (v0.1.1, July 2026): *"Agent-experience analytics — install, verify, and report on the AI agents in your site's traffic"* |
| **npm** | `footfall-core` | **AVAILABLE (404)** | Clean fallback |
| **npm** | `@footfall/core` | **AVAILABLE (Org free)** | Requires claiming npm org `footfall` |
| **GitHub** | `Ibadat-Ali86/footfall` | **CLAIMED** | Current repository |
| **GitHub** | `Ibadat-Ali86/footfall-data` | **AVAILABLE** | Ready to create in T0.2 |
| **MCP Registry** | `io.github.Ibadat-Ali86/footfall` | **AVAILABLE** | Official reverse-DNS namespace free |

---

## 2. Competitive & Collision Analysis

1. **`npm footfall` (`nitinm21/footfall`):**
   - Active package on npm in adjacent domain ("AI agent traffic analytics").
   - Action required: Do **not** attempt to publish un-scoped `footfall` on npm.
   - Recommended resolution: Use `footfall-core` on npm, or register the `@footfall` npm scope.

2. **Prior Art (from section 2 of BUILD.md):**
   - `WatershedArts/Footfall`: Camera-based physical people-counter (C++, distinct domain).
   - `varyform/footfall`: Ruby gem for web visit analytics (distinct domain).

---

## 3. External Checks (Action Required by Human)

### 3.1 Domains
Run `whois` or check registrar (Cloudflare / Namecheap / Google Domains):
- [ ] `footfall.dev`
- [ ] `getfootfall.dev`
- [ ] `footfall-analytics.dev`

### 3.2 Trademark Search
Verify no active registration in software/SaaS classes (IC 009 / IC 042):
- [ ] **USPTO TESS:** [https://tmsearch.uspto.gov](https://tmsearch.uspto.gov)
- [ ] **EUIPO eSearch:** [https://euipo.europa.eu/eSearch/](https://euipo.europa.eu/eSearch/)
- [ ] **WIPO Global Brand Database:** [https://branddb.wipo.int/](https://branddb.wipo.int/)

---

## 4. Human Decision Record (Gate G0)

- **Selected Project Name:** `Footfall`
- **PyPI Namespaces:** `footfall` (or `footfall-core`, `footfall-mcp`)
- **npm Namespaces:** `footfall-core` / `@footfall/core`
- **Fallback Consideration:** `Ridership` / `Turnout` (rejected / retained)
- **Approved Date:** ___________________
- **Signature:** ___________________
