"""Thin multimodal LLM wrapper that always returns validated JSON."""
import base64
import json
import re
from typing import TypeVar

from anthropic import Anthropic
from pydantic import BaseModel, ValidationError

from .config import settings

T = TypeVar("T", bound=BaseModel)
_client: Anthropic | None = None


class LLMError(Exception):
    pass


def _get_client() -> Anthropic:
    global _client
    if not settings.anthropic_api_key:
        raise LLMError("ANTHROPIC_API_KEY is not configured on the server.")
    if _client is None:
        _client = Anthropic(api_key=settings.anthropic_api_key)
    return _client


def _extract_json(text: str) -> dict:
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("No JSON object found")
    return json.loads(text[start : end + 1])


def ask_json(
    system: str,
    prompt: str,
    model_cls: type[T],
    images: list[tuple[str, bytes]] | None = None,
) -> T:
    """Send text (+ optional images) and return a validated pydantic object."""
    client = _get_client()
    content: list[dict] = []
    for mime, data in images or []:
        content.append(
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": mime,
                    "data": base64.b64encode(data).decode(),
                },
            }
        )
    schema = json.dumps(model_cls.model_json_schema())
    content.append(
        {
            "type": "text",
            "text": f"{prompt}\n\nRespond with ONLY a JSON object (no markdown) "
            f"that conforms to this JSON Schema:\n{schema}",
        }
    )
    messages = [{"role": "user", "content": content}]
    last_err: Exception | None = None
    for _ in range(2):  # one retry on malformed output
        try:
            resp = client.messages.create(
                model=settings.model, max_tokens=3000, system=system, messages=messages
            )
            raw = "".join(b.text for b in resp.content if b.type == "text")
            return model_cls.model_validate(_extract_json(raw))
        except (ValueError, ValidationError) as e:
            last_err = e
    raise LLMError(f"Model returned invalid JSON: {last_err}")
