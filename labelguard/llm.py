"""Thin LLM layer over Groq, with robust JSON parsing.

Higher-level modules (extract / judge / verifiers) branch on config.MOCK_MODE
and only call into here when a real key is present. Keeping the network code in
one place makes the rest of the system testable and offline-runnable.
"""
from __future__ import annotations

import base64
import json
import re
from typing import List, Optional

from labelguard import config

_CLIENT = None


def _client():
    global _CLIENT
    if _CLIENT is None:
        from groq import Groq

        _CLIENT = Groq(api_key=config.GROQ_API_KEY)
    return _CLIENT


def parse_json(text: str) -> dict:
    """Extract the first JSON object from an LLM response, defensively."""
    text = text.strip()
    try:
        return json.loads(text)
    except Exception:
        pass
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(0))
        except Exception:
            pass
    raise ValueError(f"Could not parse JSON from model output: {text[:200]}")


def chat_json(system: str, user: str, model: Optional[str] = None,
              temperature: float = 0.0) -> dict:
    resp = _client().chat.completions.create(
        model=model or config.TEXT_MODEL,
        temperature=temperature,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    return parse_json(resp.choices[0].message.content)


def vision_extract(image_bytes: bytes, prompt: str) -> str:
    b64 = base64.b64encode(image_bytes).decode()
    resp = _client().chat.completions.create(
        model=config.VISION_MODEL,
        temperature=0.0,
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url",
                 "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
            ],
        }],
    )
    return resp.choices[0].message.content
