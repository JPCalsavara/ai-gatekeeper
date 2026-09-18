# ADR 0002: Multi-Provider LLM Factory with Dynamic Imports

## Status
Accepted

## Context
Version 0.9 relied strictly on `langchain-google-genai` and Google Gemini. While optimal for zero-config free tier usage, enterprise users and air-gapped CI environments require alternative LLM providers:
- OpenAI (`gpt-4o-mini`, `gpt-4o`)
- Anthropic (`claude-3-5-haiku`, `claude-3-5-sonnet`)
- Local Ollama (`llama3.2`, `qwen2.5-coder`)

Hardcoding imports for all provider SDKs in `requirements.txt` would bloat container images and introduce version conflicts.

## Decision
We implemented `llm_factory.py` with dynamic, on-demand imports:
- Google Gemini remains the default zero-config provider.
- Alternative providers (`openai`, `anthropic`, `ollama`) are loaded dynamically when `LLM_PROVIDER` is set.
- A centralized pricing matrix tracks model costs per 1M input/output tokens.

## Consequences
- **Positive**:
  - Lean dependencies: base Docker image only requires `langchain-google-genai`.
  - Zero lock-in: seamless provider switching via environment variables.
  - Transparent LLMOps cost accounting across all providers.
- **Negative**:
  - Users choosing non-default providers must install the corresponding optional package (`langchain-openai`, `langchain-anthropic`, etc.).
