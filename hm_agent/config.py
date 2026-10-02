# -*- coding: utf-8 -*-
"""Configuration management for HyperMesh AI Agent."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory for the hm_agent package and project root
BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent

# Load .env file from project root, package directory, or current working directory
load_dotenv(ROOT_DIR / ".env")
load_dotenv(BASE_DIR / ".env")
load_dotenv()


def get_env_str(key: str, default: str) -> str:
    """Retrieve string value from environment variable."""
    return os.environ.get(key, default).strip()


def get_env_int(key: str, default: int) -> int:
    """Retrieve integer value from environment variable."""
    val = os.environ.get(key, "").strip()
    if val.isdigit():
        return int(val)
    return default


def get_env_float(key: str, default: float) -> float:
    """Retrieve float value from environment variable."""
    val = os.environ.get(key, "").strip()
    try:
        return float(val)
    except ValueError:
        return default


# API Configuration (Supports any OpenAI-compatible provider)
API_KEY = (
    os.environ.get("OPENAI_API_KEY", "").strip()
    or os.environ.get("API_KEY", "").strip()
    or os.environ.get("DEEPSEEK_API_KEY", "").strip()
)
BASE_URL = get_env_str("OPENAI_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME = get_env_str("MODEL_NAME", "gpt-4o")


# HyperMesh TCP Bridge Configuration
HM_HOST = get_env_str("HM_BRIDGE_HOST", "127.0.0.1")
HM_PORT = get_env_int("HM_BRIDGE_PORT", 23456)
HM_TIMEOUT = get_env_float("HM_TIMEOUT", 300.0)

# Agent Execution Limits
MAX_AGENT_STEPS = get_env_int("MAX_AGENT_STEPS", 15)

# Paths
DOCS_DIR = BASE_DIR / "docs"
COMMAND_REF_PATH = DOCS_DIR / "hypermesh_command_reference.md"
COMMAND_INDEX_PATH = DOCS_DIR / "command_index.txt"
STATE_DIR = BASE_DIR / "state"
STATE_DIR.mkdir(parents=True, exist_ok=True)
