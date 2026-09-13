#!/usr/bin/env python3
"""Round-trip one prompt through the LLM endpoint configured in .env. Stdlib only.

  python scripts/check_llm.py            # uses .env in the repo root
  python scripts/check_llm.py --models   # also list the models the endpoint serves
  python scripts/check_llm.py --tools    # also verify the endpoint returns *structured*
                                         # tool calls (the investigation loop needs them)

Exit 0 on success, 1 otherwise. Run it from the venue before the demo.

`--tools` matters: vLLM needs ``--enable-auto-tool-choice --tool-call-parser <name>``
matching the model; without it the model prints ``<tool_call>`` text and the loop
cannot work. We must find that out from the venue, not on stage.

``load_env`` and ``KEYS`` live in ``agent.config`` so the client (#22) and the loop
(#13) share one reader. This script stays stdlib-only (it does not import ``openai``).
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent.config import KEYS, load_env  # noqa: E402


def request(env: dict[str, str], path: str, payload: dict | None = None, timeout: float = 60) -> dict:
    url = env["LLM_BASE_URL"].rstrip("/") + path
    headers = {"Authorization": f"Bearer {env.get('LLM_API_KEY', '')}", "Content-Type": "application/json"}
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method="POST" if data else "GET")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


ADD_TOOL = {
    "type": "function",
    "function": {
        "name": "add",
        "description": "Add two integers",
        "parameters": {
            "type": "object",
            "properties": {"a": {"type": "integer"}, "b": {"type": "integer"}},
            "required": ["a", "b"],
        },
    },
}


def check_tools(env: dict[str, str]) -> int:
    """POST a chat completion with one tool; report whether it came back structured."""
    res = request(env, "/chat/completions", {
        "model": env["LLM_MODEL"],
        "messages": [{"role": "user", "content": "Use the add tool to add 2 and 3."}],
        "tools": [ADD_TOOL],
        "tool_choice": "auto",
        "temperature": 0,
        "max_tokens": 4096,  # headroom for reasoning models that think before calling the tool
    })
    message = res["choices"][0]["message"]
    calls = message.get("tool_calls") or []
    if calls:
        fn = calls[0].get("function", {}) or {}
        args_raw = fn.get("arguments") or ""
        try:
            args = json.loads(args_raw)
        except json.JSONDecodeError:
            args = None
        if fn.get("name") == "add" and args == {"a": 2, "b": 3}:
            print(f"OK tools  name=add args={json.dumps(args, ensure_ascii=False)}")
            return 0
    print("raw message:", json.dumps(message, ensure_ascii=False))
    print(
        "endpoint did not return a structured tool call; vLLM needs "
        "--enable-auto-tool-choice --tool-call-parser <hermes|llama3_json|mistral|...> "
        "matching the model"
    )
    return 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--models", action="store_true", help="list models served by the endpoint")
    ap.add_argument("--tools", action="store_true", help="also verify structured tool calls")
    args = ap.parse_args()
    env = load_env()
    missing = [k for k in KEYS if not env.get(k)]
    if missing:
        print(f"missing in .env: {', '.join(missing)}  (cp .env.example .env and fill it in)")
        return 1
    try:
        if args.models:
            ms = request(env, "/models")
            print("models:", ", ".join(m["id"] for m in ms.get("data", [])) or ms)
        t0 = time.time()
        res = request(env, "/chat/completions", {
            "model": env["LLM_MODEL"],
            "messages": [{"role": "user", "content": "Reply with the single word OK."}],
            "max_tokens": 4096,  # reasoning models burn tokens before content; 8 made content come back null
            "temperature": 0,
        })
        message = res["choices"][0]["message"]
        text = message.get("content")
        if text is None:
            print(f"WARNING: {env['LLM_MODEL']} returned content=null (reasoning ate all tokens?) "
                  f"reasoning={message.get('reasoning_content')!r}")
            text = ""
        text = text.strip()
        print(f"OK  {env['LLM_MODEL']} @ {env['LLM_BASE_URL']}  {time.time() - t0:.1f}s  reply={text!r}")
        if args.tools:
            return check_tools(env)
        return 0
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code} from {e.url}: {e.read()[:300]!r}")
    except Exception as e:  # noqa: BLE001
        print(f"FAILED: {type(e).__name__}: {e}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
