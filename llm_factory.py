"""
Multi-Provider LLM Factory for AI Quality Gatekeeper.
Supports Google Gemini (default), OpenAI, Anthropic Claude, and local Ollama.
Provides dynamic model loading, token cost resolution, and fallback safety.
"""

import os
from typing import Dict, Any, Tuple
from dotenv import load_dotenv

load_dotenv()

# Synchronize Gemini keys
_gemini_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
if _gemini_key and not os.getenv("GOOGLE_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = _gemini_key

# Default Reference Pricing (per 1M tokens)
PRICING_TABLE = {
    "gemini": {
        "flash": {"default_model": "gemini-3.5-flash-lite", "in": 0.075, "out": 0.30},
        "pro": {"default_model": "gemini-3.5-flash-lite", "in": 0.075, "out": 0.30}
    },
    "openai": {
        "flash": {"default_model": "gpt-4o-mini", "in": 0.15, "out": 0.60},
        "pro": {"default_model": "gpt-4o", "in": 2.50, "out": 10.00}
    },
    "anthropic": {
        "flash": {"default_model": "claude-3-5-haiku-20241022", "in": 0.80, "out": 4.00},
        "pro": {"default_model": "claude-3-5-sonnet-20241022", "in": 3.00, "out": 15.00}
    },
    "ollama": {
        "flash": {"default_model": "deepseek-coder:6.7b", "in": 0.00, "out": 0.00},
        "pro": {"default_model": "deepseek-coder:6.7b", "in": 0.00, "out": 0.00}
    }
}

def get_provider() -> str:
    """Returns the configured LLM provider in lowercase (default: gemini)."""
    return os.getenv("LLM_PROVIDER", "gemini").lower()

def get_pricing_info(role: str = "flash") -> Dict[str, Any]:
    """Resolves model name and pricing metrics for telemetry based on active provider and role."""
    provider = get_provider()
    table = PRICING_TABLE.get(provider, PRICING_TABLE["gemini"])
    info = table.get(role, table["flash"]).copy()

    # Environment variable overrides
    if provider == "gemini":
        model_name = os.getenv("GEMINI_FLASH_MODEL" if role == "flash" else "GEMINI_PRO_MODEL", info["default_model"])
    elif provider == "openai":
        model_name = os.getenv("OPENAI_FLASH_MODEL" if role == "flash" else "OPENAI_PRO_MODEL", info["default_model"])
    elif provider == "anthropic":
        model_name = os.getenv("ANTHROPIC_FLASH_MODEL" if role == "flash" else "ANTHROPIC_PRO_MODEL", info["default_model"])
    elif provider == "ollama":
        model_name = os.getenv("OLLAMA_MODEL", info["default_model"])
    else:
        model_name = info["default_model"]

    info["name"] = model_name
    return info

def get_chat_model(role: str = "flash", temperature: float = 0.1) -> Any:
    """
    Factory function returning an initialized LangChain ChatModel instance.
    Dynamically loads provider dependencies to avoid unnecessary imports.
    """
    provider = get_provider()
    pricing = get_pricing_info(role)
    model_name = pricing["name"]

    if provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY") or "mock-key-for-init"
        return ChatGoogleGenerativeAI(
            model=model_name,
            temperature=temperature,
            google_api_key=key
        )

    elif provider == "openai":
        try:
            from langchain_openai import ChatOpenAI
        except ImportError:
            raise ImportError("langchain-openai is required for LLM_PROVIDER=openai. Install it with: pip install langchain-openai")
        key = os.getenv("OPENAI_API_KEY") or "mock-key-for-init"
        return ChatOpenAI(
            model=model_name,
            temperature=temperature,
            api_key=key
        )

    elif provider == "anthropic":
        try:
            from langchain_anthropic import ChatAnthropic
        except ImportError:
            raise ImportError("langchain-anthropic is required for LLM_PROVIDER=anthropic. Install it with: pip install langchain-anthropic")
        key = os.getenv("ANTHROPIC_API_KEY") or "mock-key-for-init"
        return ChatAnthropic(
            model_name=model_name,
            temperature=temperature,
            anthropic_api_key=key
        )

    elif provider == "ollama":
        try:
            from langchain_community.chat_models import ChatOllama
        except ImportError:
            raise ImportError("langchain-community is required for LLM_PROVIDER=ollama. Install it with: pip install langchain-community")
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        return ChatOllama(
            model=model_name,
            temperature=temperature,
            base_url=base_url
        )

    else:
        raise ValueError(f"Unsupported LLM_PROVIDER: '{provider}'. Supported providers: gemini, openai, anthropic, ollama.")
