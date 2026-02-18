import os
from dotenv import load_dotenv

load_dotenv()

# ==============================
# LLM configuration
# ==============================
# Goal: support "free/local" usage (Ollama) without requiring an OpenAI key.
# This project uses two call paths:
# - `openai` python client (in RAG)
# - `openai-agents` SDK (`from agents import Agent/Runner`), which typically reads OpenAI env vars.

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama").strip().lower()

# Backwards compat: keep reading OPENAI_API_KEY, but don't require it unless provider=openai.
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if LLM_PROVIDER == "ollama":
    # Ollama exposes an OpenAI-compatible API at /v1 when enabled (default on localhost).
    LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://localhost:11434/v1")
    LLM_MODEL = os.getenv("LLM_MODEL", "llama3.1:8b")
    LLM_API_KEY = os.getenv("LLM_API_KEY", "ollama")  # dummy value for OpenAI-compatible clients
elif LLM_PROVIDER == "groq":
    # Groq exposes an OpenAI-compatible API under /openai/v1.
    # See: `https://api.groq.com/openai/v1`
    LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1")
    LLM_MODEL = os.getenv("LLM_MODEL", "llama-3.1-8b-instant")
    # Prefer GROQ_API_KEY, but allow LLM_API_KEY as a generic override.
    LLM_API_KEY = os.getenv("GROQ_API_KEY") or os.getenv("LLM_API_KEY")
    if not LLM_API_KEY:
        raise ValueError("GROQ_API_KEY not set (required when LLM_PROVIDER=groq)")
elif LLM_PROVIDER == "openai":
    LLM_BASE_URL = os.getenv("LLM_BASE_URL")  # optional
    LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
    LLM_API_KEY = OPENAI_API_KEY
    if not LLM_API_KEY:
        raise ValueError("OPENAI_API_KEY not set (required when LLM_PROVIDER=openai)")
else:
    raise ValueError(f"Unsupported LLM_PROVIDER: {LLM_PROVIDER}. Use 'ollama', 'groq', or 'openai'.")

# Ensure downstream libs that rely on OpenAI env vars (like `openai-agents`) work consistently.
# IMPORTANT: we ALWAYS override OPENAI_API_KEY/OPENAI_BASE_URL so that providers like Groq don't
# accidentally keep using a stale real OpenAI key from the shell environment.
os.environ["OPENAI_API_KEY"] = LLM_API_KEY or ""
if LLM_BASE_URL:
    os.environ["OPENAI_BASE_URL"] = LLM_BASE_URL

# Ollama/Groq (and most OpenAI-compatible endpoints) implement Chat Completions, not the newer
# Responses API. The Agents SDK defaults to Responses, so we force Chat Completions here.
if LLM_PROVIDER in {"ollama", "groq"}:
    try:
        from agents import set_default_openai_api

        set_default_openai_api("chat_completions")
    except Exception:
        # If the agents SDK isn't installed yet (e.g., during minimal tooling), don't fail import.
        pass

# ==============================
# MySQL configuration
# ==============================
MYSQL_CONFIG = {
    "host": os.getenv("MYSQL_HOST"),
    "user": os.getenv("MYSQL_USER"),
    "password": os.getenv("MYSQL_PASSWORD"),
    "database": os.getenv("MYSQL_DATABASE"),
    "port": int(os.getenv("MYSQL_PORT", 3306)),
}

# ==============================
# Feature flags
# ==============================
NOTIFICATION_ENABLED = os.getenv("NOTIFICATION_ENABLED", "true").lower() == "true"
AUTO_EXECUTE_ACTIONS = os.getenv("AUTO_EXECUTE_ACTIONS", "false").lower() == "true"


def get_llm_openai_client():
    """
    Returns an OpenAI-compatible client configured for the chosen provider.
    - With Ollama: points to http://localhost:11434/v1 and uses a dummy key.
    - With Groq: points to https://api.groq.com/openai/v1 and uses GROQ_API_KEY.
    - With OpenAI: uses OPENAI_API_KEY (and optional base URL override).
    """
    from openai import OpenAI

    kwargs = {"api_key": LLM_API_KEY}
    if LLM_BASE_URL:
        kwargs["base_url"] = LLM_BASE_URL
    return OpenAI(**kwargs)
