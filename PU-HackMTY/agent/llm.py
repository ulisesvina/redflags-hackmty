"""OpenAI-compatible LLM client for the investigation loop (#22).

The single place that talks to the model. It :

- talks only to the endpoint configured in ``.env`` (AGENTS.md rule 8) and never
  logs or prints the API key;
- caches responses on disk so a demo re-run costs zero network;
- retries connection errors / timeouts / HTTP 5xx / 429 with 1-2-4s backoff;
- never raises on a malformed tool call (``args={}`` and ``parse_error`` set);
- exposes :class:`FakeLLM`, a scripted stand-in with the same ``.chat`` signature,
  so #13 can be built and tested without the cluster.

This module never opens a dataset or anything under ``hidden/``.
"""
from __future__ import annotations

import hashlib
import json
import os
import threading
import time
from dataclasses import dataclass
from pathlib import Path

from .config import Settings

ROOT = Path(__file__).resolve().parents[1]

# Connection errors (APITimeoutError is a subclass of APIConnectionError), 429
# (RateLimitError) and 5xx (InternalServerError) are retryable; every other 4xx
# is a caller bug and must not be retried.
_RETRYABLE = ("APIConnectionError", "RateLimitError", "InternalServerError")


@dataclass
class ToolCall:
    id: str
    name: str
    args: dict  # parsed JSON arguments; {} when parsing failed
    parse_error: str = ""  # set when `arguments` was not valid JSON


@dataclass
class Reply:
    text: str  # assistant content; "" when the model only called tools
    tool_calls: list[ToolCall]
    cached: bool
    usage: dict  # {"prompt_tokens","completion_tokens"} when reported, else {}
    raw: dict  # the whole response as a plain dict (goes into the step log)


def assistant_message(reply: Reply) -> dict:
    """The dict to append to ``messages`` after a call, in OpenAI shape."""
    msg: dict = {"role": "assistant", "content": reply.text}
    if reply.tool_calls:
        msg["tool_calls"] = [
            {
                "id": tc.id,
                "type": "function",
                "function": {"name": tc.name, "arguments": json.dumps(tc.args, ensure_ascii=False)},
            }
            for tc in reply.tool_calls
        ]
    return msg


def tool_message(call: ToolCall, result) -> dict:
    """The dict to append to ``messages`` after a tool ran."""
    return {
        "role": "tool",
        "tool_call_id": call.id,
        "name": call.name,
        "content": json.dumps(result, ensure_ascii=False, default=str),
    }


class LLM:
    """Thin wrapper over ``openai.OpenAI`` with caching and retries."""

    def __init__(
        self,
        settings: Settings,
        *,
        client=None,
        cache_dir: Path | None = ROOT / ".cache" / "llm",
        temperature: float = 0.0,
        timeout: float = 120.0,
        max_retries: int = 3,
    ) -> None:
        import openai

        self._openai = openai
        self.settings = settings
        self.client = client if client is not None else openai.OpenAI(
            base_url=settings.base_url, api_key=settings.api_key, timeout=timeout
        )
        self.cache_dir = cache_dir
        self.temperature = temperature
        self.timeout = timeout
        self.max_retries = max_retries

        # #89 run-metadata counters. `prompt_tokens` / `completion_tokens` count
        # only *uncached* calls (a cached call cost 0), so mxn_cost is simply
        # tokens x rates / 1000. `by_role` is keyed by the optional `role` kwarg
        # on chat() ("investigator", "challenger", ...).
        self.calls = 0
        self.cached_calls = 0
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.by_role: dict[str, dict] = {}
        # #71: the client is shared across worker threads; guard the counter
        # mutations and the on-disk cache write so concurrent replies cannot
        # corrupt run-metadata totals or leave a torn cache file.
        self._lock = threading.Lock()

    def stats(self) -> dict:
        """#89: the run-metadata counters (calls, tokens, cost-relevant splits)."""
        return {
            "calls": self.calls,
            "cached_calls": self.cached_calls,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "by_role": {k: dict(v) for k, v in self.by_role.items()},
        }

    def _count(self, reply: "Reply", role: str) -> None:
        """Fold one reply into the #89 counters (uncached tokens only)."""
        with self._lock:
            self.calls += 1
            usage = reply.usage or {}
            p = int(usage.get("prompt_tokens", 0) or 0)
            c = int(usage.get("completion_tokens", 0) or 0)
            if reply.cached:
                self.cached_calls += 1
            else:
                self.prompt_tokens += p
                self.completion_tokens += c
            if role:
                r = self.by_role.setdefault(
                    role, {"calls": 0, "cached_calls": 0, "prompt_tokens": 0, "completion_tokens": 0}
                )
                r["calls"] += 1
                if reply.cached:
                    r["cached_calls"] += 1
                else:
                    r["prompt_tokens"] += p
                    r["completion_tokens"] += c

    # -- cache -------------------------------------------------------------
    def _cache_enabled(self) -> bool:
        return self.cache_dir is not None and os.environ.get("LLM_CACHE", "1") != "0"

    def _cache_key(self, messages, tools, tool_choice, max_tokens) -> str:
        data = {
            "model": self.settings.model,
            "messages": messages,
            "tools": tools,
            "tool_choice": tool_choice,
            "temperature": self.temperature,
            "max_tokens": max_tokens,
        }
        s = json.dumps(data, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(s.encode("utf-8")).hexdigest()

    @staticmethod
    def _normalise(resp) -> dict:
        """Return the response as a plain dict (model_dump when it is an object)."""
        if hasattr(resp, "model_dump"):
            return resp.model_dump()
        return dict(resp)

    @staticmethod
    def _build_reply(raw: dict, *, cached: bool) -> Reply:
        choice = raw.get("choices") or [{}]
        msg = choice[0].get("message", {}) if isinstance(choice[0], dict) else {}
        text = msg.get("content") or ""
        tool_calls: list[ToolCall] = []
        for tc in msg.get("tool_calls") or []:
            func = tc.get("function", {}) if isinstance(tc, dict) else {}
            args_str = func.get("arguments") if isinstance(func, dict) else ""
            args_str = args_str or ""
            try:
                args = json.loads(args_str) if args_str else {}
                parse_error = ""
            except json.JSONDecodeError:
                args = {}
                parse_error = args_str
            tool_calls.append(
                ToolCall(
                    id=tc.get("id", "") if isinstance(tc, dict) else "",
                    name=func.get("name", "") if isinstance(func, dict) else "",
                    args=args,
                    parse_error=parse_error,
                )
            )
        usage = raw.get("usage", {})
        if not isinstance(usage, dict):
            usage = {}
        return Reply(text=text, tool_calls=tool_calls, cached=cached, usage=usage, raw=raw)

    # -- chat --------------------------------------------------------------
    def _request(self, messages, tools, tool_choice, max_tokens) -> dict:
        """Talk to the server, retrying retryable failures. Always returns a plain dict."""
        retryable = tuple(getattr(self._openai, name) for name in _RETRYABLE)
        for attempt in range(self.max_retries + 1):
            try:
                kwargs = {
                    "model": self.settings.model,
                    "messages": messages,
                    "temperature": self.temperature,
                    "max_tokens": max_tokens,
                    "seed": 0,
                }
                if tools is not None:
                    kwargs["tools"] = tools
                    kwargs["tool_choice"] = tool_choice
                resp = self.client.chat.completions.create(**kwargs)
                return self._normalise(resp)
            except retryable:  # connection / timeout / 429 / 5xx
                if attempt >= self.max_retries:
                    raise
                time.sleep(2 ** attempt)
        # Unreachable: on the last attempt the retryable branch re-raises, so the
        # loop can only exit via `return`. Kept for type checkers.
        raise RuntimeError("unreachable: all LLM retries exhausted")

    def chat(self, messages, tools: list[dict] | None = None, *, tool_choice: str | dict = "auto",
             max_tokens: int = 8192, role: str = "") -> Reply:
        # generous: reasoning models burn completion tokens on reasoning_content
        # before the answer starts, so a tight cap makes content come back null
        key = self._cache_key(messages, tools, tool_choice, max_tokens)
        cache_file = self.cache_dir / f"{key}.json" if self.cache_dir is not None else None

        if self._cache_enabled() and cache_file is not None:
            raw = None
            if cache_file.exists():
                try:
                    raw = json.loads(cache_file.read_text(encoding="utf-8"))
                except (json.JSONDecodeError, OSError):
                    # A torn file (a crash mid-write under the old non-atomic scheme)
                    # is treated as a cache miss: fall through to a network call.
                    raw = None
            if raw is not None:
                reply = self._build_reply(raw, cached=True)
                self._count(reply, role)
                return reply

        raw = self._request(messages, tools, tool_choice, max_tokens)

        if self._cache_enabled() and cache_file is not None:
            cache_file.parent.mkdir(parents=True, exist_ok=True)
            # #71: write to a per-thread temp then atomically replace, so two
            # threads finishing the same key cannot leave a torn file (and a
            # concurrent reader never sees a half-written one).
            tmp = cache_file.with_name(f"{cache_file.name}.{threading.get_ident()}.tmp")
            tmp.write_text(json.dumps(raw, ensure_ascii=False, default=str), encoding="utf-8")
            os.replace(tmp, cache_file)

        reply = self._build_reply(raw, cached=False)
        self._count(reply, role)
        return reply


class FakeLLM:
    """Scripted stand-in for :class:`LLM` with the same ``.chat`` signature.

    Takes a list of :class:`Reply` objects (or callables ``messages -> Reply``) and
    returns them in order. Records every call in ``.calls``. Raises ``RuntimeError``
    when it runs out. Used by tests of #13. Mirrors the #89 run-metadata counters
    so ``stats()`` works the same as :class:`LLM`.
    """

    def __init__(self, replies) -> None:
        self._replies = list(replies)
        self.calls: list[dict] = []
        self.cached_calls = 0
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.by_role: dict[str, dict] = {}

    def stats(self) -> dict:
        return {
            "calls": len(self.calls),
            "cached_calls": self.cached_calls,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "by_role": {k: dict(v) for k, v in self.by_role.items()},
        }

    def _count(self, reply: Reply, role: str) -> None:
        usage = reply.usage or {}
        p = int(usage.get("prompt_tokens", 0) or 0)
        c = int(usage.get("completion_tokens", 0) or 0)
        if reply.cached:
            self.cached_calls += 1
        else:
            self.prompt_tokens += p
            self.completion_tokens += c
        if role:
            r = self.by_role.setdefault(
                role, {"calls": 0, "cached_calls": 0, "prompt_tokens": 0, "completion_tokens": 0}
            )
            r["calls"] += 1
            if reply.cached:
                r["cached_calls"] += 1
            else:
                r["prompt_tokens"] += p
                r["completion_tokens"] += c

    def chat(self, messages, tools: list[dict] | None = None, *, tool_choice: str | dict = "auto",
             max_tokens: int = 8192, role: str = "") -> Reply:
        self.calls.append(
            {"messages": list(messages), "tools": tools, "tool_choice": tool_choice, "max_tokens": max_tokens}
        )
        if not self._replies:
            raise RuntimeError("FakeLLM exhausted")
        # #71: a lone callable is treated as a persistent reply function. Concurrent
        # units each drive it with their own messages, so it is never popped and
        # consumed (the parallel test uses a message-content-driven callable).
        if len(self._replies) == 1 and callable(self._replies[0]):
            reply = self._replies[0]
        else:
            reply = self._replies.pop(0)
        if callable(reply):
            reply = reply(messages)
        if not isinstance(reply, Reply):
            raise TypeError(f"FakeLLM callable must return a Reply, got {type(reply).__name__}")
        self._count(reply, role)
        return reply
