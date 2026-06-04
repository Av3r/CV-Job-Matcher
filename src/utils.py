import json
import os
from typing import Dict, Optional


_PROMPTS_CACHE: Optional[Dict[str, str]] = None


def _load_prompts() -> Dict[str, str]:
    global _PROMPTS_CACHE
    if _PROMPTS_CACHE is not None:
        return _PROMPTS_CACHE

    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "prompts.json")
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Prompts file not found: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        try:
            prompts = json.load(f)
        except Exception as exc:
            raise RuntimeError(f"Failed to parse prompts.json at {config_path}: {exc}") from exc

    if not isinstance(prompts, dict):
        raise TypeError(f"prompts.json must contain a JSON object at top level: {config_path}")

    # Normalize keys to str values
    cleaned: Dict[str, str] = {}
    for k, v in prompts.items():
        if not isinstance(k, str):
            continue
        if not isinstance(v, str):
            # skip non-string entries to avoid runtime surprises
            continue
        cleaned[k] = v

    _PROMPTS_CACHE = cleaned
    return _PROMPTS_CACHE


def load_prompt(key: str) -> str:
    """Load a system prompt by key from config/prompts.json.

    Raises a helpful KeyError listing available keys if the requested key
    does not exist.
    """
    prompts = _load_prompts()
    if key in prompts:
        return prompts[key]
    available = ", ".join(sorted(prompts.keys()))
    raise KeyError(f"Prompt key '{key}' not found in prompts.json. Available keys: {available}")
