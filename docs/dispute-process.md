# Maintainer Dispute & Flag Review Process

**Effective Date:** 2026-11-08  
**Contact:** disputes@footfall.dev  

---

## 1. Purpose and Philosophy

Footfall identifies quantitative statistical shifts, including sudden star velocity surges (star bursts) and package download step functions. These statistical anomalies are labeled as **unusual activity** (never "fake", "fraudulent", or "bought").

We recognize that legitimate, organic developer events—such as trending on social platforms, major product launches, conference keynotes, or automated benchmark integrations—can generate sharp statistical spikes. 

Maintainers have a clear, transparent, and prompt right of reply.

---

## 2. Grounds for Dispute

You may submit a dispute if:
1. **Unusual Star Activity:** A star burst flag was assigned to your repository, but you have evidence of organic viral exposure (e.g., product launch link, HN frontpage URL, newsletter feature).
2. **Download Step Function:** A download surge was flagged, but reflects legitimate automated CI/CD runners, container base image inclusions, or mirror deployments.
3. **Entity Metadata:** Entity category, source repository, or package mappings are incorrect or outdated.

---

## 3. How to Submit a Dispute

To initiate a review:
1. Open a GitHub Issue using the `Dispute Flag` template, or email `disputes@footfall.dev`.
2. Provide the following information:
   - **Entity Identifier:** Canonical ID or repository URL (e.g., `owner/repo`).
   - **Flag in Question:** Specific date, window, or anomaly type.
   - **Supporting Evidence:** Public links explaining the surge (e.g., Hacker News submission, Reddit post, viral launch tweet, container registry adoption stats).
   - **Verification:** Proof of maintainership (e.g., commit signing, email matching Git commit author domain, or comment from an official organization account).

---

## 4. Review Timeline and Interim Status

- **Acknowledgment:** Within **48 hours** of submission.
- **Interim Masking:** During the active review period, the anomaly flag's `dispute_status` is updated to `disputed`. Disputed flags are masked from public badge outputs and marked with a neutral review note in MCP responses.
- **Final Determination:** Within **7 business days**.

---

## 5. Dispute Outcomes

Following empirical review, one of three outcomes is recorded:
1. **Flag Withdrawn:** Evidence confirms external organic cause. The flag is permanently removed from the ledger and export datasets.
2. **Flag Updated with Context:** The statistical anomaly remains mathematically verified, but a factual explanation is attached to `explained_by` in the public entity profile.
3. **Flag Sustained:** If evidence is insufficient to account for the velocity divergence, the neutral statistical flag is maintained with the standard caveats.

All dispute determinations are recorded transparently in the public dispute log in our repository.
