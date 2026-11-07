# Claude Connectors Directory — Evaluation Prompts & Verification

This document lists the 10 scripted evaluation scenarios tested in CI against the Footfall MCP server (implemented in `tests/unit/test_skill_prompts.py`).

---

### Scenario 1: Direct Tool Comparison
- **User Prompt:** "How do LangGraph and Qdrant compare in real developer usage?"
- **Tool Called:** `footfall_compare(entities=["langgraph", "qdrant-client"], window_weeks=12)`
- **Evaluation Criteria:**
  - Response contains `as_of`, `method_version: "m1.0"`.
  - Both tools returned with `adoption_z`, `attention_z`, `divergence`, and `phase`.
  - Standard caveats included regarding CI traffic and social stars.
  - Zero financial or investment advice words ("buy", "invest", "bet").

### Scenario 2: Historical Trend Lookback
- **User Prompt:** "Show me the adoption trend for LangGraph over the last 26 weeks."
- **Tool Called:** `footfall_trend(entity="langgraph", window_weeks=26)`
- **Evaluation Criteria:**
  - Returns `series` array of weekly observation points with `downloads` and `stars`.
  - Provenance headers present.

### Scenario 3: Category Breakout Discovery
- **User Prompt:** "What AI tools are breaking out in agent frameworks?"
- **Tool Called:** `footfall_find_rising(category="agent-framework", phase="breakout", limit=5)`
- **Evaluation Criteria:**
  - Returns accelerating entities filtered to `category == "agent-framework"`.
  - Excludes tools with unverified download spikes.

### Scenario 4: Workhorse Utility Discovery (Use Ahead)
- **User Prompt:** "What vector stores have use ahead of attention?"
- **Tool Called:** `footfall_find_rising(category="vector-store", phase="use_ahead", limit=5)`
- **Evaluation Criteria:**
  - Returns tools with negative divergence ($D < -1.0$) indicating adoption outpaces hype.

### Scenario 5: Alias & Package Name Resolution
- **User Prompt:** "Compare `langchain-ai/langgraph` with `@qdrant/js-client-rest`."
- **Tool Called:** `footfall_compare` with raw repository and npm package strings.
- **Evaluation Criteria:**
  - In-memory resolver maps both to canonical `langgraph` and `qdrant-client`.

### Scenario 6: Entity Upper Bound Rejection
- **User Prompt:** Comparison query with 7 entity names.
- **Evaluation Criteria:**
  - Pydantic schema validation rejects input with `ValidationError` (`maxItems: 6`).

### Scenario 7: Entity Lower Bound Rejection
- **User Prompt:** Comparison query with only 1 entity name.
- **Evaluation Criteria:**
  - Schema rejects with `ValidationError` (`minItems: 2`).

### Scenario 8: Unknown Entity Handling
- **User Prompt:** Look up non-existent entity `unknown-ai-package-xyz`.
- **Evaluation Criteria:**
  - Returns structured `{ "code": "not_found", "message": "Entity not found in registry.", "candidates": [...] }`.
  - Does NOT echo raw user input or prompt injection attempts.

### Scenario 9: Prompt Injection & Path Traversal Rejection
- **User Prompt:** Payload containing shell separators, SQL keywords, or path traversal.
- **Evaluation Criteria:**
  - Schema pattern `^[A-Za-z0-9@._/\-]{1,100}$` rejects invalid characters before server dispatch.

### Scenario 10: Neutral Terminology standard
- **User Prompt:** Inquire about an entity with an anomaly flag.
- **Evaluation Criteria:**
  - Response labels event as "unusual velocity" (never "fake", "fraudulent", or "bought").
