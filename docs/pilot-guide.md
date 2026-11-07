# Footfall Pilot User Guide (Task T3.5)

Welcome to the Footfall pilot evaluation! This guide provides testing instructions for our initial cohort of 5 pilot users (AI developers, open-source maintainers, and engineering leads).

---

## 1. Pilot Objectives

The goal of this pilot is to test:
1. **Tool Accuracy & Relevance:** Do the lifecycle phases (`breakout`, `use_ahead`, `mainstream`, `plateau`, `fading`) accurately reflect real-world developer experience?
2. **Resolution Quality:** Does the entity resolver find the tools you expect, including aliases and repository names (e.g., `langgraph`, `qdrant-client`, `chromadb`)?
3. **Caveat Clarity:** Do the responses clearly convey that measurements are empirical indicators rather than financial or purchasing advice?
4. **Latency & Reliability:** Is tool response time consistently under 1 second?

---

## 2. Setup & Connection

### Option A: In Claude Desktop / Claude Code
Add Footfall to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "footfall": {
      "command": "uvx",
      "args": ["footfall", "serve", "--stdio"]
    }
  }
}
```

Or connect via the remote Streamable HTTP endpoint:
```json
{
  "mcpServers": {
    "footfall": {
      "type": "streamable-http",
      "url": "https://mcp.footfall.dev/mcp"
    }
  }
}
```

### Option B: In ChatGPT
1. Go to **Explore GPTs** &rarr; **Create a GPT** &rarr; **Configure** &rarr; **Actions**.
2. Import OpenAPI schema from `https://mcp.footfall.dev/openapi.yaml` (or copy from `submissions/chatgpt/openapi.yaml`).
3. Set Authentication to **None**.

### Option C: Footfall CLI
Run commands locally:
```bash
# Compare tools directly
uv run footfall compare langgraph qdrant-client

# Check your own repository's dependencies
uv run footfall stack pyproject.toml
```

---

## 3. Test Scenarios to Try

Try asking your AI assistant the following queries and observe how Footfall responds:

1. **Direct Tool Comparison:**  
   *"Compare LangGraph and AutoGen on real adoption versus attention."*  
   *Look for:* Adoption z-scores, 4-week growth rates, divergence, and standard download caveats.

2. **Trend Exploration:**  
   *"What does the download trajectory look like for ChromaDB over the last 6 months?"*  
   *Look for:* Weekly observation points, seasonal trends, and `as_of` date.

3. **Ecosystem Discovery:**  
   *"What AI tools are currently in the breakout phase in the agent framework category?"*  
   *Look for:* Filtered results ranked by adoption acceleration.

4. **Under-the-Radar Utility Search:**  
   *"Are there any vector stores where real usage leads attention (use_ahead)?"*  
   *Look for:* Negative divergence ($D < -1.0$) indicating silent production adoption.

5. **Boundary & Typo Resolution:**  
   *"Check adoption for 'lang-chain' or 'qdrant/qdrant'."*  
   *Look for:* In-memory alias resolution or structured candidate suggestions.

---

## 4. Submitting Your Feedback

Please log your feedback using any of the following methods:
- **GitHub Issue:** Open an issue using the [Pilot Feedback Form](https://github.com/Ibadat-Ali86/footfall/issues/new?template=pilot-feedback.yml).
- **Direct Feedback Log:** Add your entry directly to [`docs/pilot-feedback-log.md`](pilot-feedback-log.md).
- **Email:** Send thoughts to `pilot@footfall.dev`.

Thank you for helping us ensure Footfall is robust, scientifically defensible, and useful to the open-source developer ecosystem!
