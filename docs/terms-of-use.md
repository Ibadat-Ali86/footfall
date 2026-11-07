# Terms of Use

**Effective Date:** 2026-11-08  
**Version:** 1.0.0  

---

## 1. Acceptance of Terms

By accessing or using the Footfall MCP server, static data exports, website, or developer tools (collectively, the "Service"), you agree to be bound by these Terms of Use. If you do not agree, do not access or use the Service.

---

## 2. Licensing

- **Code:** All source code in the Footfall repository is licensed under the [Apache License, Version 2.0](https://www.apache.org/licenses/LICENSE-2.0).
- **Data & Documentation:** The derived quantitative datasets, methodology documentation, and backtest results are licensed under the [Creative Commons Attribution 4.0 International License (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/). You are free to share and adapt the material provided appropriate attribution is maintained.

---

## 3. Disclaimers and No Professional Advice

> **IMPORTANT NOTICE:**  
> The Service provides quantitative statistical measurements and empirical historical analysis of public software repositories.
>
> - **Not Investment Advice:** Nothing provided by Footfall constitutes investment, financial, trading, or legal advice. Never make financial commitments, buy or sell equities, or allocate capital based on Footfall metrics.
> - **Not Purchasing Advice:** Footfall measurements do not evaluate code quality, security posture, compliance, or enterprise fitness.
> - **Probabilistic Outputs:** All lifecycle classifications and backtest predictions are statistical, empirical, and inherently uncertain. Past adoption growth does not guarantee future outcomes.

---

## 4. Acceptable Use and Rate Limits

To ensure availability for all developers:
1. **Rate Limiting:** MCP tool endpoints enforce a token bucket limit of **60 requests per minute** (burst allowance of 20). Automated clients must respect HTTP 429 status codes and the `Retry-After` header.
2. **Bulk Data:** If you require high-volume data analysis, download the precomputed static Parquet and JSON bundles rather than scraping MCP endpoints.
3. **No Abuse or Disruption:** You agree not to attempt denial-of-service attacks, bypass Origin header verification, perform DNS rebinding, or inject malicious payloads.

---

## 5. Trademarks and Project Names

Tool and project names (e.g., LangGraph, Qdrant, ChromaDB, AutoGen) are referenced strictly for nominative fair use to identify the corresponding open-source software packages. Footfall is an independent research project and is not affiliated with, endorsed by, or sponsored by any named project or organization.

---

## 6. Maintainer Inquiries and Disputes

Maintainers who wish to submit contextual evidence regarding unusual activity flags or request exclusion should refer to the [Dispute Process](dispute-process.md).
