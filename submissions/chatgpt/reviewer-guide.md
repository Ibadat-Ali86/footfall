# ChatGPT App Directory — Reviewer Guide

**App Name:** Footfall Developer Tools  
**Developer Organization:** Footfall Research  
**OpenAPI Specification:** `https://mcp.footfall.dev/openapi.yaml`  
**Authentication:** None (Public read-only developer adoption data)  
**Support Contact:** `support@footfall.dev`  

---

## 1. Submission Overview

Footfall provides empirical measurements of AI developer tool adoption. It compares verified package downloads (npm, PyPI) with social bookmarks and star velocity (GitHub, Hacker News).

- **Zero User Authentication Required:** All endpoints serve public, aggregated open-source metrics.
- **Zero Personal Data:** The app processes only package and repository names; it never stores, transmits, or accesses user accounts or personal data.
- **Not Financial/Investment Advice:** All outputs include caveats stating that predictions are probabilistic and do not constitute purchasing or investment advice.

---

## 2. Reviewer Test Instructions

In the Custom GPT or ChatGPT action configuration:
1. Import the OpenAPI specification from `https://mcp.footfall.dev/openapi.yaml` or paste the schema from `submissions/chatgpt/openapi.yaml`.
2. Ensure Authentication is set to **None**.
3. Run the following test prompts:
   - *"Compare LangGraph and Qdrant."* &rarr; calls `compareTools`.
   - *"Show adoption trend for LangGraph over the last 12 weeks."* &rarr; calls `getToolTrend`.
   - *"Find rising AI agent frameworks in breakout phase."* &rarr; calls `findRisingTools`.

---

## 3. Compliance and Security Declarations

- **Data Minimization:** No personal data collected, stored, or processed.
- **Rate Limiting:** Enforces 60 requests/minute per client IP at the edge.
- **Response Size:** Output payloads are capped at 50 KB.
- **Privacy Policy:** Published at [https://footfall.dev/about.html#privacy](https://footfall.dev/about.html#privacy).
- **Terms of Service:** Published at [https://footfall.dev/about.html](https://footfall.dev/about.html).
