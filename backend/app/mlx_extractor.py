"""oMLX multimodal adapter for extraction-only document reading."""

from __future__ import annotations

import asyncio
import base64
import json
import os
import urllib.error
import urllib.request
from typing import Any

OMLX_URL = os.getenv("OMLX_URL", "http://localhost:8000/v1/chat/completions")
OMLX_MODEL = os.getenv("OMLX_MODEL", "Qwen2.5-VL-3B-Instruct-4bit")


def _request_omlx(files: list[tuple[str, bytes]]) -> dict[str, Any]:
    content: list[dict[str, Any]] = [{
        "type": "text",
        "text": (
            "Extract only accounting facts from these company books. Return strict JSON with "
            'keys companyName and entries. Each entry must have date, description, amount, currency. '
            "Do not infer fraud, anomalies, intent, or risk."
        ),
    }]
    for filename, data in files:
        lower_name = filename.lower()
        if lower_name.endswith(".pdf"):
            content.append({"type": "text", "text": f"PDF source supplied: {filename}"})
            continue
        if not lower_name.endswith((".png", ".jpg", ".jpeg")):
            continue
        media_type = "image/png" if lower_name.endswith(".png") else "image/jpeg"
        encoded = base64.b64encode(data).decode("ascii")
        content.append({"type": "image_url", "image_url": {"url": f"data:{media_type};base64,{encoded}"}})

    payload = json.dumps({
        "model": OMLX_MODEL,
        "temperature": 0,
        "response_format": {"type": "json_object"},
        "messages": [{"role": "user", "content": content}],
    }).encode("utf-8")
    request = urllib.request.Request(OMLX_URL, data=payload, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(request, timeout=180) as response:
        response_payload = json.loads(response.read().decode("utf-8"))
    message = response_payload["choices"][0]["message"]["content"]
    return json.loads(message) if isinstance(message, str) else message


async def extract_with_mlx(files: list[tuple[str, bytes]]) -> dict[str, Any]:
    """Ask oMLX to read visual books, returning an empty result when offline."""
    visual_files = [file for file in files if file[0].lower().endswith((".pdf", ".png", ".jpg", ".jpeg"))]
    if not visual_files or os.getenv("ENABLE_OMLX", "0") != "1":
        return {"companyName": None, "entries": []}
    try:
        return await asyncio.to_thread(_request_omlx, visual_files)
    except (OSError, urllib.error.URLError, KeyError, TypeError, json.JSONDecodeError):
        return {"companyName": None, "entries": []}
