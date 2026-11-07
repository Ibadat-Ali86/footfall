# Claude Connectors Directory — Reviewer Guide

**Connector Name:** Footfall  
**Remote Endpoint:** `https://mcp.footfall.dev/mcp`  
**Protocol:** Model Context Protocol (MCP) Streamable HTTP  
**Auth:** None required in v1 (Public aggregated developer metrics only)  
**Support Contact:** `support@footfall.dev`  

---

## 1. Quick Verification & Testing

The Footfall MCP server is public, read-only, and requires no API keys, accounts, or credentials.

### Connecting in Claude Desktop or Claude Code
Add the following to your MCP configuration:

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

Or connect directly to the public remote Streamable HTTP endpoint:
- **Server URL:** `https://mcp.footfall.dev/mcp`
- **Liveness Probe:** `GET https://mcp.footfall.dev/health/live` &rarr; `{"status": "live"}`
- **Readiness Probe:** `GET https://mcp.footfall.dev/health/ready` &rarr; `{"status": "ready", "as_of": "2026-11-02", "method_version": "m1.0"}`

---

## 2. Security & Safety Checklist

- [x] **Read-Only Enforced:** All tools are read-only in fact. There are zero mutation endpoints, zero database write credentials, and zero file upload facilities.
- [x] **Tool Safety Annotations:** Every tool declares `readOnlyHint: true`, `destructiveHint: false`, `idempotentHint: true`, `openWorldHint: false`.
- [x] **DNS Rebinding Defense:** The server inspects the HTTP `Origin` header and rejects unauthorized external web origins with HTTP 403 Forbidden.
- [x] **Zero Personal Data:** We store and return zero GitHub usernames, individual account IDs, or contributor PII. All data consists of aggregate package manager statistics.
- [x] **Prompt Injection Defense:** Outputs contain zero third-party free text (no READMEs, package descriptions, or comments). All responses are strictly formatted numerical values, dates, and project-controlled caveat strings.
- [x] **50 KB Response Cap:** Tool responses are capped at 50 KB to prevent context window exhaustion.
- [x] **Rate Limiting:** Edge token bucket limits requests to 60/minute (burst 20) with HTTP 429 and `Retry-After`.

---

## 3. Sample Reviewer Prompts

Reviewers can test the connector using these natural language queries:

1. **Compare Tools:**  
   *"Compare LangGraph and Qdrant on Footfall."*  
   *Expected behavior:* Claude resolves `langgraph` and `qdrant-client`, calls `footfall_compare`, and outputs the adoption z-scores, divergence, and standard download caveats.

2. **Trend Analysis:**  
   *"What does the download history look like for LangGraph over the last 26 weeks?"*  
   *Expected behavior:* Claude calls `footfall_trend` for `langgraph`, reporting weekly metrics and `as_of` date.

3. **Ecosystem Discovery:**  
   *"Which agent frameworks are currently in the breakout phase on Footfall?"*  
   *Expected behavior:* Claude calls `footfall_find_rising` with category `agent-framework` and phase `breakout`.

4. **Error Handling (Unknown Tool):**  
   *"Check adoption for some-fake-tool-xyz123."*  
   *Expected behavior:* The server returns a structured `not_found` error with nearest candidates without echoing raw text.

---

## 4. Documentation & Legal Links

- **Documentation & Methodology:** [https://footfall.dev/methodology.html](https://footfall.dev/methodology.html)
- **Privacy Policy:** [https://footfall.dev/about.html#privacy](https://footfall.dev/about.html#privacy)
- **Terms of Use:** [https://footfall.dev/about.html](https://footfall.dev/about.html)
- **Dispute Process:** [https://footfall.dev/about.html#disputes](https://footfall.dev/about.html#disputes)
- **Open-Source Codebase:** [https://github.com/Ibadat-Ali86/footfall](https://github.com/Ibadat-Ali86/footfall)
