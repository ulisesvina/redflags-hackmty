"""LLM endpoint configuration (#22).

One place that decides *where* the model lives, so the investigation loop (#13) only
cares about leads and evidence and never builds an HTTP client. Reads plain
``KEY=VALUE`` lines from ``.env``; real environment variables win over the file.
No python-dotenv (AGENTS.md rule 4).

The body of :func:`load_env` was moved here from ``scripts/check_llm.py`` so the
script and anything else that needs the settings share a single reader.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KEYS = ("LLM_BASE_URL", "LLM_API_KEY", "LLM_MODEL")

# Reference hosted-API price for a comparable open-weight model, in MXN per 1K
# tokens (#89). The HPC cluster's marginal cost is 0, so these are only for the
# case-file header figure "if this run had been served by a hosted API it would
# cost about X MXN" (Feasibility). Source: DeepSeek's published API pricing
# (https://api-docs.deepseek.com/quick_start/pricing), ~$0.27/1M input and
# ~$1.10/1M output at 18.5 MXN/USD, captured 2026-09-12:
#   0.00027 * 18.5 = 0.004995 ~ 0.0050
#   0.00110 * 18.5 = 0.020350 ~ 0.0204
MXN_PER_1K_PROMPT_TOKENS = 0.0050
MXN_PER_1K_COMPLETION_TOKENS = 0.0204


def load_env(path: Path = ROOT / ".env") -> dict[str, str]:
    """Read ``.env``: ``KEY=VALUE`` lines, ``#`` comments, optional quotes.

    Real environment variables win over the file (so an operator can override the
    endpoint per-run without touching `.env`).
    """
    env: dict[str, str] = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip("'\"")
    env.update({k: os.environ[k] for k in KEYS if os.environ.get(k)})
    return env


@dataclass(frozen=True)
class Settings:
    base_url: str
    api_key: str
    model: str
    # Cost of the run "if served by a hosted API" (#89); the cluster's marginal
    # cost is 0. Overridable via LLM_MXN_PER_1K_PROMPT / LLM_MXN_PER_1K_COMPLETION.
    mxn_per_1k_prompt: float = MXN_PER_1K_PROMPT_TOKENS
    mxn_per_1k_completion: float = MXN_PER_1K_COMPLETION_TOKENS


def settings(path: Path = ROOT / ".env") -> Settings | None:
    """Return :class:`Settings` when every key is present and non-empty, else ``None``.

    ``None`` is the CI signal (there is no ``.env`` on CI) that the caller should
    fall back to the deterministic offline path rather than attempt a network call.
    """
    env = load_env(path)
    if any(not env.get(k) for k in KEYS):
        return None
    def _mxn(key: str, default: float) -> float:
        raw = env.get(key) or os.environ.get(key)
        if raw is None or raw == "":
            return default
        try:
            return float(raw)
        except ValueError:
            return default
    return Settings(
        base_url=env["LLM_BASE_URL"],
        api_key=env["LLM_API_KEY"],
        model=env["LLM_MODEL"],
        mxn_per_1k_prompt=_mxn("LLM_MXN_PER_1K_PROMPT", MXN_PER_1K_PROMPT_TOKENS),
        mxn_per_1k_completion=_mxn("LLM_MXN_PER_1K_COMPLETION", MXN_PER_1K_COMPLETION_TOKENS),
    )
