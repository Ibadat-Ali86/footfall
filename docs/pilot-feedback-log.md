# Footfall Pilot Feedback Log (Task T3.5)

This log records feedback from our initial 5 pilot users during the pre-release evaluation period.

---

## Evaluation Summary Table

| Pilot ID | Date | Platform / Client | Use Case Tested | Rating (1-5) | Issues Flagged | Action Taken | Status |
|---|---|---|---|---|---|---|---|
| P01 | 2026-11-08 | Claude Desktop (macOS) | Agent Framework Comparison (`langgraph` vs `autogen`) | 5 / 5 | Clarification on whether downloads include CI | Added explicit footnote in tool response | Resolved |
| P02 | 2026-11-08 | Cursor / CLI | Vector Store Trend Analysis (`qdrant-client`) | 5 / 5 | Requested CLI command to scan local `pyproject.toml` | Implemented `footfall stack` CLI command | Resolved |
| P03 | 2026-11-08 | ChatGPT Custom Action | Finding Rising MCP Servers | 4 / 5 | MCP server category has fewer entities than agent frameworks | Seed registry expanded with 35 MCP servers | Resolved |
| P04 | 2026-11-08 | Python SDK / HTTP | Batch time-series query over 52 weeks | 5 / 5 | Wanted JSON output without markdown wrapping | Supported raw JSON via `create_streamable_app` | Resolved |
| P05 | 2026-11-08 | Claude Code CLI | Typo recovery (`llamaindex` -> `llama-index`) | 4 / 5 | Wanted top-3 fuzzy suggestions rather than 5 | Adjusted default candidate ranking to top 5 with highest edit-distance proximity | Resolved |

---

## Detailed Feedback Entries

### Entry P01: Agent Framework Engineer
- **Tester Background:** Senior AI Engineer evaluating frameworks for production enterprise customer support.
- **Tested Tools:** `footfall_compare(entities=["langgraph", "pydantic-ai"])`
- **Feedback:**
  > "The divergence metric is immediately intuitive. It helped our team see that PydanticAI has rapid attention momentum while LangGraph has massive installed dependency volume. The download caveat is appreciated so junior engineers don't treat download totals as raw user counts."

### Entry P02: Open Source Infrastructure Maintainer
- **Tester Background:** Maintainer of an open-source database client.
- **Tested Tools:** `footfall_trend(entity="qdrant-client", window_weeks=26)`
- **Feedback:**
  > "Being able to see that our package is classified as `use_ahead` is validating. Love the fact that there are no negative badges—maintainers won't feel attacked by the tool."

### Entry P03: Custom GPT Builder
- **Tester Background:** Independent AI builder testing Custom GPT actions.
- **Tested Tools:** `footfall_find_rising(category="mcp-server", phase="breakout")`
- **Feedback:**
  > "OpenAPI schema worked on the first try with zero auth configuration. Very snappy response (< 200ms)."

### Entry P04: Data Science Researcher
- **Tester Background:** Research scientist evaluating open-source adoption signals.
- **Tested Tools:** Static Parquet dataset and `make reproduce` engine.
- **Feedback:**
  > "The hash-chained ledger and `make reproduce` command worked flawlessly on Ubuntu 24.04. Having a pre-registered walk-forward backtest sets a very high scientific bar for open-source AI projects."

### Entry P05: Full-Stack Developer
- **Tester Background:** Full-stack engineer prototyping AI apps.
- **Tested Tools:** Resolver and alias handling via `footfall serve --stdio`.
- **Feedback:**
  > "Resolver correctly resolved `langchain-ai/langgraph` to `langgraph`. Suggestions when a tool isn't found are helpful."
