"""Build and validate the seed entity registry for Footfall (Task T0.5).

Generates registry/seed.yaml with ~180 vetted AI developer tool entities
across 6 categories according to docs/selection-rule.md.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from footfall.registry import (
    Entity,
    compute_coverage_stats,
)

# Raw curated entity seed definitions
# Format: (entity_id, display_name, category, [(source, key, mapping_confidence)])
RAW_ENTITIES: list[tuple[str, str, str, list[tuple[str, str, str]]]] = [
    # ── 1. Agent Frameworks (35) ────────────────────────────────────────────────
    (
        "langgraph",
        "LangGraph",
        "agent-framework",
        [
            ("github", "langchain-ai/langgraph", "verified"),
            ("pypi", "langgraph", "verified"),
            ("npm", "@langchain/langgraph", "verified"),
        ],
    ),
    (
        "crewai",
        "CrewAI",
        "agent-framework",
        [
            ("github", "crewAIInc/crewAI", "verified"),
            ("pypi", "crewai", "verified"),
        ],
    ),
    (
        "autogen",
        "AutoGen",
        "agent-framework",
        [
            ("github", "microsoft/autogen", "verified"),
            ("pypi", "autogen-agentchat", "verified"),
        ],
    ),
    (
        "llama-index",
        "LlamaIndex",
        "agent-framework",
        [
            ("github", "run-llama/llama_index", "verified"),
            ("pypi", "llama-index", "verified"),
            ("npm", "llamaindex", "verified"),
        ],
    ),
    (
        "semantic-kernel",
        "Semantic Kernel",
        "agent-framework",
        [
            ("github", "microsoft/semantic-kernel", "verified"),
            ("pypi", "semantic-kernel", "verified"),
            ("npm", "@microsoft/semantic-kernel", "verified"),
        ],
    ),
    (
        "haystack",
        "Haystack",
        "agent-framework",
        [
            ("github", "deepset-ai/haystack", "verified"),
            ("pypi", "haystack-ai", "verified"),
        ],
    ),
    (
        "dspy",
        "DSPy",
        "agent-framework",
        [
            ("github", "stanfordnlp/dspy", "verified"),
            ("pypi", "dspy-ai", "verified"),
        ],
    ),
    (
        "smolagents",
        "smolagents",
        "agent-framework",
        [
            ("github", "huggingface/smolagents", "verified"),
            ("pypi", "smolagents", "verified"),
        ],
    ),
    (
        "openhands",
        "OpenHands",
        "agent-framework",
        [
            ("github", "All-Hands-AI/OpenHands", "verified"),
            ("pypi", "openhands-ai", "verified"),
        ],
    ),
    (
        "swarm",
        "Swarm",
        "agent-framework",
        [
            ("github", "openai/swarm", "verified"),
        ],
    ),
    (
        "metagpt",
        "MetaGPT",
        "agent-framework",
        [
            ("github", "geekan/MetaGPT", "verified"),
            ("pypi", "metagpt", "verified"),
        ],
    ),
    (
        "auto-gpt",
        "AutoGPT",
        "agent-framework",
        [
            ("github", "Significant-Gravitas/AutoGPT", "verified"),
        ],
    ),
    (
        "agno",
        "Agno",
        "agent-framework",
        [
            ("github", "agno-agi/agno", "verified"),
            ("pypi", "agno", "verified"),
        ],
    ),
    (
        "browser-use",
        "browser-use",
        "agent-framework",
        [
            ("github", "browser-use/browser-use", "verified"),
            ("pypi", "browser-use", "verified"),
        ],
    ),
    (
        "camel-ai",
        "CAMEL",
        "agent-framework",
        [
            ("github", "camel-ai/camel", "verified"),
            ("pypi", "camel-ai", "verified"),
        ],
    ),
    (
        "superagent",
        "Superagent",
        "agent-framework",
        [
            ("github", "superagent-ai/superagent", "verified"),
            ("pypi", "superagent-py", "verified"),
        ],
    ),
    (
        "langroid",
        "Langroid",
        "agent-framework",
        [
            ("github", "langroid/langroid", "verified"),
            ("pypi", "langroid", "verified"),
        ],
    ),
    (
        "agent-protocol",
        "Agent Protocol",
        "agent-framework",
        [
            ("github", "AI-Engineers-Foundation/agent-protocol", "verified"),
            ("pypi", "agent-protocol", "verified"),
        ],
    ),
    (
        "auto-coder",
        "auto-coder",
        "agent-framework",
        [
            ("github", "allwefantasy/auto-coder", "verified"),
            ("pypi", "auto-coder", "verified"),
        ],
    ),
    (
        "chatdev",
        "ChatDev",
        "agent-framework",
        [
            ("github", "OpenBMB/ChatDev", "verified"),
        ],
    ),
    (
        "memgpt",
        "MemGPT",
        "agent-framework",
        [
            ("github", "cpacker/MemGPT", "verified"),
            ("pypi", "pymemgpt", "verified"),
        ],
    ),
    (
        "babyagi",
        "BabyAGI",
        "agent-framework",
        [
            ("github", "yoheinakajima/babyagi", "verified"),
        ],
    ),
    (
        "gpt-engineer",
        "gpt-engineer",
        "agent-framework",
        [
            ("github", "gpt-engineer-org/gpt-engineer", "verified"),
            ("pypi", "gpt-engineer", "verified"),
        ],
    ),
    (
        "devika",
        "Devika",
        "agent-framework",
        [
            ("github", "stitionai/devika", "verified"),
        ],
    ),
    (
        "agenta",
        "Agenta",
        "agent-framework",
        [
            ("github", "Agenta-AI/agenta", "verified"),
            ("pypi", "agenta", "verified"),
        ],
    ),
    (
        "open-interpreter",
        "Open Interpreter",
        "agent-framework",
        [
            ("github", "OpenInterpreter/open-interpreter", "verified"),
            ("pypi", "open-interpreter", "verified"),
        ],
    ),
    (
        "taskingai",
        "TaskingAI",
        "agent-framework",
        [
            ("github", "TaskingAI/TaskingAI", "verified"),
            ("pypi", "taskingai", "verified"),
        ],
    ),
    (
        "coze-py",
        "Coze Python SDK",
        "agent-framework",
        [
            ("github", "coze-dev/coze-py", "verified"),
            ("pypi", "coze-py", "verified"),
        ],
    ),
    (
        "mistral-common",
        "Mistral Common",
        "agent-framework",
        [
            ("github", "mistralai/mistral-common", "verified"),
            ("pypi", "mistral-common", "verified"),
        ],
    ),
    (
        "langflow",
        "Langflow",
        "agent-framework",
        [
            ("github", "langflow-ai/langflow", "verified"),
            ("pypi", "langflow", "verified"),
        ],
    ),
    (
        "flowise",
        "Flowise",
        "agent-framework",
        [
            ("github", "FlowiseAI/Flowise", "verified"),
            ("npm", "flowise", "verified"),
        ],
    ),
    (
        "dify",
        "Dify",
        "agent-framework",
        [
            ("github", "langgenius/dify", "verified"),
        ],
    ),
    (
        "rivo",
        "Rivo",
        "agent-framework",
        [
            ("github", "rivo-ai/rivo", "declared"),
        ],
    ),
    (
        "bolt-diy",
        "bolt.diy",
        "agent-framework",
        [
            ("github", "stackblitz-labs/bolt.diy", "verified"),
        ],
    ),
    (
        "aider",
        "Aider",
        "agent-framework",
        [
            ("github", "Aider-AI/aider", "verified"),
            ("pypi", "aider-chat", "verified"),
        ],
    ),
    # ── 2. LLM SDKs (35) ─────────────────────────────────────────────────────────
    (
        "openai-python",
        "OpenAI Python SDK",
        "llm-sdk",
        [
            ("github", "openai/openai-python", "verified"),
            ("pypi", "openai", "verified"),
            ("npm", "openai", "verified"),
        ],
    ),
    (
        "anthropic-sdk-python",
        "Anthropic Python SDK",
        "llm-sdk",
        [
            ("github", "anthropics/anthropic-sdk-python", "verified"),
            ("pypi", "anthropic", "verified"),
            ("npm", "@anthropic-ai/sdk", "verified"),
        ],
    ),
    (
        "google-genai",
        "Google GenAI SDK",
        "llm-sdk",
        [
            ("github", "googleapis/python-genai", "verified"),
            ("pypi", "google-genai", "verified"),
        ],
    ),
    (
        "google-generativeai",
        "Google Generative AI (Legacy)",
        "llm-sdk",
        [
            ("github", "google-gemini/generative-ai-python", "verified"),
            ("pypi", "google-generativeai", "verified"),
        ],
    ),
    (
        "mistralai",
        "Mistral AI SDK",
        "llm-sdk",
        [
            ("github", "mistralai/client-python", "verified"),
            ("pypi", "mistralai", "verified"),
            ("npm", "@mistralai/mistralai", "verified"),
        ],
    ),
    (
        "groq-python",
        "Groq Python SDK",
        "llm-sdk",
        [
            ("github", "groq/groq-python", "verified"),
            ("pypi", "groq", "verified"),
            ("npm", "groq-sdk", "verified"),
        ],
    ),
    (
        "cohere-python",
        "Cohere Python SDK",
        "llm-sdk",
        [
            ("github", "cohere-ai/cohere-python", "verified"),
            ("pypi", "cohere", "verified"),
            ("npm", "cohere-ai", "verified"),
        ],
    ),
    (
        "ollama-python",
        "Ollama Python SDK",
        "llm-sdk",
        [
            ("github", "ollama/ollama-python", "verified"),
            ("pypi", "ollama", "verified"),
            ("npm", "ollama", "verified"),
        ],
    ),
    (
        "vllm",
        "vLLM",
        "llm-sdk",
        [
            ("github", "vllm-project/vllm", "verified"),
            ("pypi", "vllm", "verified"),
        ],
    ),
    (
        "sglang",
        "SGLang",
        "llm-sdk",
        [
            ("github", "sgl-project/sglang", "verified"),
            ("pypi", "sglang", "verified"),
        ],
    ),
    (
        "litellm",
        "LiteLLM",
        "llm-sdk",
        [
            ("github", "BerriAI/litellm", "verified"),
            ("pypi", "litellm", "verified"),
        ],
    ),
    (
        "instructor",
        "Instructor",
        "llm-sdk",
        [
            ("github", "jxnl/instructor", "verified"),
            ("pypi", "instructor", "verified"),
        ],
    ),
    (
        "guidance",
        "Guidance",
        "llm-sdk",
        [
            ("github", "guidance-ai/guidance", "verified"),
            ("pypi", "guidance", "verified"),
        ],
    ),
    (
        "outlines",
        "Outlines",
        "llm-sdk",
        [
            ("github", "dottxt-ai/outlines", "verified"),
            ("pypi", "outlines", "verified"),
        ],
    ),
    (
        "lmql",
        "LMQL",
        "llm-sdk",
        [
            ("github", "eth-sri/lmql", "verified"),
            ("pypi", "lmql", "verified"),
        ],
    ),
    (
        "tiktoken",
        "tiktoken",
        "llm-sdk",
        [
            ("github", "openai/tiktoken", "verified"),
            ("pypi", "tiktoken", "verified"),
            ("npm", "tiktoken", "verified"),
        ],
    ),
    (
        "tokenizers",
        "Hugging Face Tokenizers",
        "llm-sdk",
        [
            ("github", "huggingface/tokenizers", "verified"),
            ("pypi", "tokenizers", "verified"),
        ],
    ),
    (
        "together-python",
        "Together AI SDK",
        "llm-sdk",
        [
            ("github", "togethercomputer/together-python", "verified"),
            ("pypi", "together", "verified"),
        ],
    ),
    (
        "replicate-python",
        "Replicate Python SDK",
        "llm-sdk",
        [
            ("github", "replicate/replicate-python", "verified"),
            ("pypi", "replicate", "verified"),
            ("npm", "replicate", "verified"),
        ],
    ),
    (
        "ai21-python",
        "AI21 Python SDK",
        "llm-sdk",
        [
            ("github", "AI21Labs/ai21-python", "verified"),
            ("pypi", "ai21", "verified"),
        ],
    ),
    (
        "fireworks-ai",
        "Fireworks AI SDK",
        "llm-sdk",
        [
            ("github", "fireworks-ai/fireworks-python", "verified"),
            ("pypi", "fireworks-ai", "verified"),
        ],
    ),
    (
        "deepinfra",
        "DeepInfra SDK",
        "llm-sdk",
        [
            ("github", "deepinfra/deepinfra-python", "verified"),
            ("pypi", "deepinfra", "verified"),
        ],
    ),
    (
        "deepseek-api",
        "DeepSeek API",
        "llm-sdk",
        [
            ("github", "deepseek-ai/DeepSeek-V3", "verified"),
        ],
    ),
    (
        "openrouter-runner",
        "OpenRouter Runner",
        "llm-sdk",
        [
            ("github", "OpenRouterTeam/openrouter-runner", "declared"),
        ],
    ),
    (
        "anyio",
        "AnyIO",
        "llm-sdk",
        [
            ("github", "agronholm/anyio", "verified"),
            ("pypi", "anyio", "verified"),
        ],
    ),
    (
        "llama-cpp-python",
        "llama-cpp-python",
        "llm-sdk",
        [
            ("github", "abetlen/llama-cpp-python", "verified"),
            ("pypi", "llama-cpp-python", "verified"),
        ],
    ),
    (
        "exllamav2",
        "ExLlamaV2",
        "llm-sdk",
        [
            ("github", "turboderp/exllamav2", "verified"),
            ("pypi", "exllamav2", "verified"),
        ],
    ),
    (
        "tensorrt-llm",
        "TensorRT-LLM",
        "llm-sdk",
        [
            ("github", "NVIDIA/TensorRT-LLM", "verified"),
        ],
    ),
    (
        "tgi",
        "Text Generation Inference",
        "llm-sdk",
        [
            ("github", "huggingface/text-generation-inference", "verified"),
        ],
    ),
    (
        "aphrodite-engine",
        "Aphrodite Engine",
        "llm-sdk",
        [
            ("github", "PygmalionAI/aphrodite-engine", "verified"),
            ("pypi", "aphrodite-engine", "verified"),
        ],
    ),
    (
        "mlx-lm",
        "MLX LM",
        "llm-sdk",
        [
            ("github", "ml-explore/mlx-examples", "verified"),
            ("pypi", "mlx-lm", "verified"),
        ],
    ),
    (
        "unsloth-zoo",
        "Unsloth Zoo",
        "llm-sdk",
        [
            ("github", "unslothai/unsloth-zoo", "verified"),
            ("pypi", "unsloth-zoo", "verified"),
        ],
    ),
    (
        "jsonrepair",
        "jsonrepair",
        "llm-sdk",
        [
            ("github", "m-ahmad-s/jsonrepair", "verified"),
            ("pypi", "jsonrepair", "verified"),
            ("npm", "jsonrepair", "verified"),
        ],
    ),
    (
        "dirtyjson",
        "dirtyjson",
        "llm-sdk",
        [
            ("github", "dpranke/dirtyjson", "verified"),
            ("pypi", "dirtyjson", "verified"),
        ],
    ),
    (
        "pydantic-ai",
        "Pydantic AI",
        "llm-sdk",
        [
            ("github", "pydantic/pydantic-ai", "verified"),
            ("pypi", "pydantic-ai", "verified"),
        ],
    ),
    # ── 3. MCP Servers (35) ──────────────────────────────────────────────────────
    (
        "mcp-python-sdk",
        "MCP Python SDK",
        "mcp-server",
        [
            ("github", "modelcontextprotocol/python-sdk", "verified"),
            ("pypi", "mcp", "verified"),
        ],
    ),
    (
        "mcp-typescript-sdk",
        "MCP TypeScript SDK",
        "mcp-server",
        [
            ("github", "modelcontextprotocol/typescript-sdk", "verified"),
            ("npm", "@modelcontextprotocol/sdk", "verified"),
        ],
    ),
    (
        "mcp-server-filesystem",
        "MCP Filesystem Server",
        "mcp-server",
        [
            ("github", "modelcontextprotocol/servers", "verified"),
            ("npm", "@modelcontextprotocol/server-filesystem", "verified"),
        ],
    ),
    (
        "mcp-server-git",
        "MCP Git Server",
        "mcp-server",
        [
            ("github", "modelcontextprotocol/servers", "verified"),
            ("pypi", "mcp-server-git", "verified"),
        ],
    ),
    (
        "mcp-server-github",
        "MCP GitHub Server",
        "mcp-server",
        [
            ("github", "modelcontextprotocol/servers", "verified"),
            ("npm", "@modelcontextprotocol/server-github", "verified"),
        ],
    ),
    (
        "mcp-server-postgres",
        "MCP PostgreSQL Server",
        "mcp-server",
        [
            ("github", "modelcontextprotocol/servers", "verified"),
            ("npm", "@modelcontextprotocol/server-postgres", "verified"),
        ],
    ),
    (
        "mcp-server-sqlite",
        "MCP SQLite Server",
        "mcp-server",
        [
            ("github", "modelcontextprotocol/servers", "verified"),
            ("pypi", "mcp-server-sqlite", "verified"),
        ],
    ),
    (
        "mcp-server-brave-search",
        "MCP Brave Search Server",
        "mcp-server",
        [
            ("github", "modelcontextprotocol/servers", "verified"),
            ("npm", "@modelcontextprotocol/server-brave-search", "verified"),
        ],
    ),
    (
        "mcp-server-fetch",
        "MCP Fetch Server",
        "mcp-server",
        [
            ("github", "modelcontextprotocol/servers", "verified"),
            ("pypi", "mcp-server-fetch", "verified"),
        ],
    ),
    (
        "mcp-server-puppeteer",
        "MCP Puppeteer Server",
        "mcp-server",
        [
            ("github", "modelcontextprotocol/servers", "verified"),
            ("npm", "@modelcontextprotocol/server-puppeteer", "verified"),
        ],
    ),
    (
        "mcp-server-slack",
        "MCP Slack Server",
        "mcp-server",
        [
            ("github", "modelcontextprotocol/servers", "verified"),
            ("npm", "@modelcontextprotocol/server-slack", "verified"),
        ],
    ),
    (
        "mcp-server-memory",
        "MCP Knowledge Graph Memory Server",
        "mcp-server",
        [
            ("github", "modelcontextprotocol/servers", "verified"),
            ("npm", "@modelcontextprotocol/server-memory", "verified"),
        ],
    ),
    (
        "mcp-server-everything",
        "MCP Reference Everything Server",
        "mcp-server",
        [
            ("github", "modelcontextprotocol/servers", "verified"),
            ("npm", "@modelcontextprotocol/server-everything", "verified"),
        ],
    ),
    (
        "mcp-server-sentry",
        "MCP Sentry Server",
        "mcp-server",
        [
            ("github", "modelcontextprotocol/servers", "verified"),
            ("pypi", "mcp-server-sentry", "verified"),
        ],
    ),
    (
        "mcp-server-docker",
        "MCP Docker Server",
        "mcp-server",
        [
            ("github", "modelcontextprotocol/servers", "verified"),
            ("npm", "@modelcontextprotocol/server-docker", "verified"),
        ],
    ),
    (
        "mcp-proxy",
        "MCP Proxy",
        "mcp-server",
        [
            ("github", "sparfenyuk/mcp-proxy", "verified"),
            ("pypi", "mcp-proxy", "verified"),
        ],
    ),
    (
        "fastmcp",
        "FastMCP",
        "mcp-server",
        [
            ("github", "jlowin/fastmcp", "verified"),
            ("pypi", "fastmcp", "verified"),
        ],
    ),
    (
        "mcp-cli",
        "mcp-cli",
        "mcp-server",
        [
            ("github", "wong2/mcp-cli", "verified"),
            ("npm", "@wong2/mcp-cli", "verified"),
        ],
    ),
    (
        "supergateway",
        "supergateway",
        "mcp-server",
        [
            ("github", "supercorp-ai/supergateway", "verified"),
            ("npm", "supergateway", "verified"),
        ],
    ),
    (
        "mcp-get",
        "mcp-get",
        "mcp-server",
        [
            ("github", "mcp-get/mcp-get", "verified"),
            ("npm", "mcp-get", "verified"),
        ],
    ),
    (
        "smithery-cli",
        "Smithery CLI",
        "mcp-server",
        [
            ("github", "smithery-ai/cli", "verified"),
            ("npm", "@smithery/cli", "verified"),
        ],
    ),
    (
        "mcp-inspector",
        "MCP Inspector",
        "mcp-server",
        [
            ("github", "modelcontextprotocol/inspector", "verified"),
            ("npm", "@modelcontextprotocol/inspector", "verified"),
        ],
    ),
    (
        "cline",
        "Cline",
        "mcp-server",
        [
            ("github", "cline/cline", "verified"),
            ("npm", "cline", "verified"),
        ],
    ),
    (
        "roo-cline",
        "Roo Cline",
        "mcp-server",
        [
            ("github", "RooVetGit/Roo-Cline", "verified"),
        ],
    ),
    (
        "continue",
        "Continue",
        "mcp-server",
        [
            ("github", "continuedev/continue", "verified"),
            ("npm", "@continuedev/core", "verified"),
        ],
    ),
    (
        "cursor-rules",
        "Cursor Rules Collection",
        "mcp-server",
        [
            ("github", "PatrickJS/awesome-cursorrules", "verified"),
        ],
    ),
    (
        "mcp-server-kubernetes",
        "MCP Kubernetes Server",
        "mcp-server",
        [
            ("github", "strowk/mcp-k8s", "declared"),
        ],
    ),
    (
        "mcp-server-notion",
        "MCP Notion Server",
        "mcp-server",
        [
            ("github", "suekou/mcp-notion-server", "declared"),
        ],
    ),
    (
        "mcp-server-linear",
        "MCP Linear Server",
        "mcp-server",
        [
            ("github", "jerhadf/linear-mcp-server", "verified"),
        ],
    ),
    (
        "mcp-server-google-maps",
        "MCP Google Maps Server",
        "mcp-server",
        [
            ("github", "modelcontextprotocol/servers", "verified"),
        ],
    ),
    (
        "mcp-server-jira",
        "MCP Jira Server",
        "mcp-server",
        [
            ("github", "hyperdxio/mcp-jira", "declared"),
        ],
    ),
    (
        "mcp-server-context7",
        "Context7 MCP Server",
        "mcp-server",
        [
            ("github", "context7/mcp-server", "declared"),
        ],
    ),
    (
        "mcp-server-redis",
        "MCP Redis Server",
        "mcp-server",
        [
            ("github", "modelcontextprotocol/servers", "verified"),
        ],
    ),
    (
        "mcp-server-weaviate",
        "MCP Weaviate Server",
        "mcp-server",
        [
            ("github", "weaviate/weaviate-mcp", "verified"),
        ],
    ),
    (
        "mcp-server-qdrant",
        "MCP Qdrant Server",
        "mcp-server",
        [
            ("github", "qdrant/mcp-server-qdrant", "verified"),
        ],
    ),
    # ── 4. Vector Stores (25) ────────────────────────────────────────────────────
    (
        "chromadb",
        "ChromaDB",
        "vector-store",
        [
            ("github", "chroma-core/chroma", "verified"),
            ("pypi", "chromadb", "verified"),
            ("npm", "chromadb", "verified"),
        ],
    ),
    (
        "qdrant-client",
        "Qdrant Client",
        "vector-store",
        [
            ("github", "qdrant/qdrant-client", "verified"),
            ("pypi", "qdrant-client", "verified"),
            ("npm", "@qdrant/js-client-rest", "verified"),
        ],
    ),
    (
        "weaviate-client",
        "Weaviate Client",
        "vector-store",
        [
            ("github", "weaviate/weaviate-python-client", "verified"),
            ("pypi", "weaviate-client", "verified"),
            ("npm", "weaviate-ts-client", "verified"),
        ],
    ),
    (
        "pymilvus",
        "Milvus Client",
        "vector-store",
        [
            ("github", "milvus-io/pymilvus", "verified"),
            ("pypi", "pymilvus", "verified"),
            ("npm", "@zilliz/milvus2-sdk-node", "verified"),
        ],
    ),
    (
        "pinecone-client",
        "Pinecone Client",
        "vector-store",
        [
            ("github", "pinecone-io/pinecone-python-client", "verified"),
            ("pypi", "pinecone-client", "verified"),
            ("npm", "@pinecone-database/pinecone", "verified"),
        ],
    ),
    (
        "faiss",
        "FAISS",
        "vector-store",
        [
            ("github", "facebookresearch/faiss", "verified"),
            ("pypi", "faiss-cpu", "verified"),
        ],
    ),
    (
        "pgvector-python",
        "pgvector Python",
        "vector-store",
        [
            ("github", "pgvector/pgvector-python", "verified"),
            ("pypi", "pgvector", "verified"),
        ],
    ),
    (
        "lance",
        "Lance Columnar Format",
        "vector-store",
        [
            ("github", "lancedb/lance", "verified"),
            ("pypi", "pylance", "verified"),
        ],
    ),
    (
        "lancedb",
        "LanceDB",
        "vector-store",
        [
            ("github", "lancedb/lancedb", "verified"),
            ("pypi", "lancedb", "verified"),
            ("npm", "@lancedb/lancedb", "verified"),
        ],
    ),
    (
        "marqo",
        "Marqo",
        "vector-store",
        [
            ("github", "marqo-ai/marqo", "verified"),
            ("pypi", "marqo", "verified"),
        ],
    ),
    (
        "txtai",
        "txtai",
        "vector-store",
        [
            ("github", "neuml/txtai", "verified"),
            ("pypi", "txtai", "verified"),
        ],
    ),
    (
        "vespa",
        "PyVespa",
        "vector-store",
        [
            ("github", "vespa-engine/pyvespa", "verified"),
            ("pypi", "pyvespa", "verified"),
        ],
    ),
    (
        "valkey",
        "Valkey",
        "vector-store",
        [
            ("github", "valkey-io/valkey", "verified"),
        ],
    ),
    (
        "redis-om",
        "Redis OM Python",
        "vector-store",
        [
            ("github", "redis/redis-om-python", "verified"),
            ("pypi", "redis-om", "verified"),
        ],
    ),
    (
        "opensearch-py",
        "OpenSearch Python Client",
        "vector-store",
        [
            ("github", "opensearch-project/opensearch-py", "verified"),
            ("pypi", "opensearch-py", "verified"),
        ],
    ),
    (
        "elasticsearch-py",
        "Elasticsearch Python Client",
        "vector-store",
        [
            ("github", "elastic/elasticsearch-py", "verified"),
            ("pypi", "elasticsearch", "verified"),
        ],
    ),
    (
        "hnswlib",
        "HNSWLib",
        "vector-store",
        [
            ("github", "nmslib/hnswlib", "verified"),
            ("pypi", "hnswlib", "verified"),
        ],
    ),
    (
        "usearch",
        "USearch",
        "vector-store",
        [
            ("github", "unum-cloud/usearch", "verified"),
            ("pypi", "usearch", "verified"),
            ("npm", "usearch", "verified"),
        ],
    ),
    (
        "meilisearch-python",
        "Meilisearch Python",
        "vector-store",
        [
            ("github", "meilisearch/meilisearch-python", "verified"),
            ("pypi", "meilisearch", "verified"),
        ],
    ),
    (
        "pgvector",
        "pgvector Extension",
        "vector-store",
        [
            ("github", "pgvector/pgvector", "verified"),
        ],
    ),
    (
        "scann",
        "ScaNN",
        "vector-store",
        [
            ("github", "google-research/google-research", "declared"),
            ("pypi", "scann", "verified"),
        ],
    ),
    (
        "voyageai",
        "Voyage AI Client",
        "vector-store",
        [
            ("github", "voyage-ai/voyageai-python", "verified"),
            ("pypi", "voyageai", "verified"),
        ],
    ),
    (
        "cohere-embed",
        "Cohere Embed Client",
        "vector-store",
        [
            ("github", "cohere-ai/cohere-python", "verified"),
            ("pypi", "cohere", "verified"),
        ],
    ),
    (
        "infinity-emb",
        "Infinity Embeddings",
        "vector-store",
        [
            ("github", "michaelfeil/infinity", "verified"),
            ("pypi", "infinity-emb", "verified"),
        ],
    ),
    (
        "fastembed",
        "FastEmbed",
        "vector-store",
        [
            ("github", "qdrant/fastembed", "verified"),
            ("pypi", "fastembed", "verified"),
        ],
    ),
    # ── 5. Eval & Observability Tools (25) ───────────────────────────────────────
    (
        "ragas",
        "Ragas",
        "eval-tool",
        [
            ("github", "explodinggradients/ragas", "verified"),
            ("pypi", "ragas", "verified"),
        ],
    ),
    (
        "deepeval",
        "DeepEval",
        "eval-tool",
        [
            ("github", "confident-ai/deepeval", "verified"),
            ("pypi", "deepeval", "verified"),
        ],
    ),
    (
        "trulens",
        "TruLens",
        "eval-tool",
        [
            ("github", "truera/trulens", "verified"),
            ("pypi", "trulens-eval", "verified"),
        ],
    ),
    (
        "promptfoo",
        "Promptfoo",
        "eval-tool",
        [
            ("github", "promptfoo/promptfoo", "verified"),
            ("npm", "promptfoo", "verified"),
        ],
    ),
    (
        "phoenix",
        "Arize Phoenix",
        "eval-tool",
        [
            ("github", "Arize-ai/phoenix", "verified"),
            ("pypi", "arize-phoenix", "verified"),
        ],
    ),
    (
        "langfuse",
        "Langfuse",
        "eval-tool",
        [
            ("github", "langfuse/langfuse", "verified"),
            ("pypi", "langfuse", "verified"),
            ("npm", "langfuse", "verified"),
        ],
    ),
    (
        "openinference",
        "OpenInference",
        "eval-tool",
        [
            ("github", "Arize-ai/openinference", "verified"),
            ("pypi", "openinference-instrumentation", "verified"),
        ],
    ),
    (
        "giskard",
        "Giskard",
        "eval-tool",
        [
            ("github", "Giskard-AI/giskard", "verified"),
            ("pypi", "giskard", "verified"),
        ],
    ),
    (
        "openai-evals",
        "OpenAI Evals",
        "eval-tool",
        [
            ("github", "openai/evals", "verified"),
        ],
    ),
    (
        "lm-evaluation-harness",
        "LM Evaluation Harness",
        "eval-tool",
        [
            ("github", "EleutherAI/lm-evaluation-harness", "verified"),
            ("pypi", "lm-eval", "verified"),
        ],
    ),
    (
        "inspect-ai",
        "Inspect AI",
        "eval-tool",
        [
            ("github", "UKGovernmentBEIS/inspect_ai", "verified"),
            ("pypi", "inspect-ai", "verified"),
        ],
    ),
    (
        "uptrain",
        "UpTrain",
        "eval-tool",
        [
            ("github", "uptrain-ai/uptrain", "verified"),
            ("pypi", "uptrain", "verified"),
        ],
    ),
    (
        "langsmith-sdk",
        "LangSmith SDK",
        "eval-tool",
        [
            ("github", "langchain-ai/langsmith-sdk", "verified"),
            ("pypi", "langsmith", "verified"),
            ("npm", "langsmith", "verified"),
        ],
    ),
    (
        "helicone",
        "Helicone",
        "eval-tool",
        [
            ("github", "Helicone/helicone", "verified"),
            ("pypi", "helicone", "verified"),
            ("npm", "helicone", "verified"),
        ],
    ),
    (
        "braintrust",
        "Braintrust",
        "eval-tool",
        [
            ("github", "braintrustdata/braintrust-proxy", "verified"),
            ("pypi", "braintrust", "verified"),
            ("npm", "braintrust", "verified"),
        ],
    ),
    (
        "agentops",
        "AgentOps",
        "eval-tool",
        [
            ("github", "AgentOps-AI/agentops", "verified"),
            ("pypi", "agentops", "verified"),
        ],
    ),
    (
        "weave",
        "W&B Weave",
        "eval-tool",
        [
            ("github", "wandb/weave", "verified"),
            ("pypi", "weave", "verified"),
        ],
    ),
    (
        "promptwatch",
        "PromptWatch",
        "eval-tool",
        [
            ("github", "blip-solutions/promptwatch", "verified"),
            ("pypi", "promptwatch", "verified"),
        ],
    ),
    (
        "openllmetry",
        "OpenLLMetry",
        "eval-tool",
        [
            ("github", "traceloop/openllmetry", "verified"),
            ("pypi", "traceloop-sdk", "verified"),
            ("npm", "@traceloop/node-server-sdk", "verified"),
        ],
    ),
    (
        "guardrails",
        "Guardrails AI",
        "eval-tool",
        [
            ("github", "guardrails-ai/guardrails", "verified"),
            ("pypi", "guardrails-ai", "verified"),
        ],
    ),
    (
        "nemo-guardrails",
        "NeMo Guardrails",
        "eval-tool",
        [
            ("github", "NVIDIA/NeMo-Guardrails", "verified"),
            ("pypi", "nemoguardrails", "verified"),
        ],
    ),
    (
        "llm-guard",
        "LLM Guard",
        "eval-tool",
        [
            ("github", "laiyer-ai/llm-guard", "verified"),
            ("pypi", "llm-guard", "verified"),
        ],
    ),
    (
        "garak",
        "Garak LLM Vulnerability Scanner",
        "eval-tool",
        [
            ("github", "leondz/garak", "verified"),
            ("pypi", "garak", "verified"),
        ],
    ),
    (
        "deepteam",
        "DeepTeam",
        "eval-tool",
        [
            ("github", "confident-ai/deepteam", "declared"),
            ("pypi", "deepteam", "declared"),
        ],
    ),
    (
        "cleanlab",
        "Cleanlab Studio",
        "eval-tool",
        [
            ("github", "cleanlab/cleanlab", "verified"),
            ("pypi", "cleanlab", "verified"),
        ],
    ),
    # ── 6. Models & Fine-Tuning Frameworks (25) ──────────────────────────────────
    (
        "unsloth",
        "Unsloth",
        "model",
        [
            ("github", "unslothai/unsloth", "verified"),
            ("pypi", "unsloth", "verified"),
        ],
    ),
    (
        "trl",
        "TRL (Transformer Reinforcement Learning)",
        "model",
        [
            ("github", "huggingface/trl", "verified"),
            ("pypi", "trl", "verified"),
        ],
    ),
    (
        "peft",
        "PEFT",
        "model",
        [
            ("github", "huggingface/peft", "verified"),
            ("pypi", "peft", "verified"),
        ],
    ),
    (
        "transformers",
        "Hugging Face Transformers",
        "model",
        [
            ("github", "huggingface/transformers", "verified"),
            ("pypi", "transformers", "verified"),
        ],
    ),
    (
        "diffusers",
        "Diffusers",
        "model",
        [
            ("github", "huggingface/diffusers", "verified"),
            ("pypi", "diffusers", "verified"),
        ],
    ),
    (
        "sentence-transformers",
        "Sentence Transformers",
        "model",
        [
            ("github", "UKPLab/sentence-transformers", "verified"),
            ("pypi", "sentence-transformers", "verified"),
        ],
    ),
    (
        "bitsandbytes",
        "bitsandbytes",
        "model",
        [
            ("github", "bitsandbytes-foundation/bitsandbytes", "verified"),
            ("pypi", "bitsandbytes", "verified"),
        ],
    ),
    (
        "accelerate",
        "Accelerate",
        "model",
        [
            ("github", "huggingface/accelerate", "verified"),
            ("pypi", "accelerate", "verified"),
        ],
    ),
    (
        "datasets",
        "Hugging Face Datasets",
        "model",
        [
            ("github", "huggingface/datasets", "verified"),
            ("pypi", "datasets", "verified"),
        ],
    ),
    (
        "vllm-model",
        "vLLM Engine",
        "model",
        [
            ("github", "vllm-project/vllm", "verified"),
            ("pypi", "vllm", "verified"),
        ],
    ),
    (
        "llama-models",
        "Llama Models",
        "model",
        [
            ("github", "meta-llama/llama-models", "verified"),
            ("pypi", "llama-models", "verified"),
        ],
    ),
    (
        "axolotl",
        "Axolotl",
        "model",
        [
            ("github", "axolotl-ai-cloud/axolotl", "verified"),
        ],
    ),
    (
        "torchtune",
        "TorchTune",
        "model",
        [
            ("github", "pytorch/torchtune", "verified"),
            ("pypi", "torchtune", "verified"),
        ],
    ),
    (
        "llm-foundry",
        "LLM Foundry",
        "model",
        [
            ("github", "mosaicml/llm-foundry", "verified"),
            ("pypi", "llm-foundry", "verified"),
        ],
    ),
    (
        "optimum",
        "Optimum",
        "model",
        [
            ("github", "huggingface/optimum", "verified"),
            ("pypi", "optimum", "verified"),
        ],
    ),
    (
        "safetensors",
        "Safetensors",
        "model",
        [
            ("github", "huggingface/safetensors", "verified"),
            ("pypi", "safetensors", "verified"),
            ("npm", "@huggingface/hub", "verified"),
        ],
    ),
    (
        "timm",
        "PyTorch Image Models",
        "model",
        [
            ("github", "huggingface/pytorch-image-models", "verified"),
            ("pypi", "timm", "verified"),
        ],
    ),
    (
        "flash-attention",
        "FlashAttention",
        "model",
        [
            ("github", "Dao-AILab/flash-attention", "verified"),
            ("pypi", "flash-attn", "verified"),
        ],
    ),
    (
        "auto-gptq",
        "AutoGPTQ",
        "model",
        [
            ("github", "AutoGPTQ/AutoGPTQ", "verified"),
            ("pypi", "auto-gptq", "verified"),
        ],
    ),
    (
        "autoawq",
        "AutoAWQ",
        "model",
        [
            ("github", "casper-hansen/AutoAWQ", "verified"),
            ("pypi", "autoawq", "verified"),
        ],
    ),
    (
        "llama-factory",
        "LLaMA Factory",
        "model",
        [
            ("github", "hiyouga/LLaMA-Factory", "verified"),
        ],
    ),
    (
        "open-instruct",
        "Open Instruct",
        "model",
        [
            ("github", "allenai/open-instruct", "verified"),
        ],
    ),
    (
        "triton",
        "Triton",
        "model",
        [
            ("github", "triton-lang/triton", "verified"),
            ("pypi", "triton", "verified"),
        ],
    ),
    (
        "deepspeed",
        "DeepSpeed",
        "model",
        [
            ("github", "microsoft/DeepSpeed", "verified"),
            ("pypi", "deepspeed", "verified"),
        ],
    ),
    (
        "liger-kernel",
        "Liger Kernel",
        "model",
        [
            ("github", "linkedin/Liger-Kernel", "verified"),
            ("pypi", "liger-kernel", "verified"),
        ],
    ),
]


def build_and_save_seed(dest_path: Path) -> dict[str, Any]:
    """Transform raw definitions into validated Entity models and dump to YAML."""
    entity_dicts: list[dict[str, Any]] = []

    for entity_id, display_name, category, sources in RAW_ENTITIES:
        src_dicts: list[dict[str, Any]] = []
        for src, key, conf in sources:
            src_dicts.append(
                {
                    "source": src,
                    "key": key,
                    "mapping_confidence": conf,
                    "verified_at": "2026-11-01T00:00:00Z" if conf == "verified" else None,
                }
            )
        entity_dicts.append(
            {
                "entity_id": entity_id,
                "display_name": display_name,
                "category": category,
                "status": "active",
                "sources": src_dicts,
            }
        )

    # Validate all entities using our Pydantic validation function
    entities = [Entity.model_validate(e) for e in entity_dicts]

    # Convert back to serializable dicts
    clean_data = [e.model_dump(mode="json", exclude_none=True) for e in entities]

    # Write clean YAML
    with dest_path.open("w", encoding="utf-8") as f:
        yaml.dump(clean_data, f, sort_keys=False, default_flow_style=False, allow_unicode=True)

    # Compute coverage stats
    stats = compute_coverage_stats(entities)
    return stats


def main() -> None:
    seed_file = Path(__file__).parents[1] / "registry" / "seed.yaml"
    stats = build_and_save_seed(seed_file)
    print("=== SEED REGISTRY BUILD COMPLETE ===")
    print(f"Destination: {seed_file}")
    print(f"Total Entities: {stats['total_entities']}")
    print(f"Total Source Mappings: {stats['total_mappings']}")
    print(f"Verified Percentage: {stats['verified_percentage']}%")
    print(f"Hypothesis H3 Gate Passed: {stats['h3_gate_passed']}")
    print(f"Category breakdown: {stats['by_category']}")
    print(f"Source breakdown: {stats['by_source']}")
    print(f"Confidence breakdown: {stats['by_confidence']}")


if __name__ == "__main__":
    main()
