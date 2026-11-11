"""The single place where Gemini is called.

Every model call in the project goes through `call_llm`, so token counts and latency are
recorded in one spot (this is the base for the observability feature later).
"""

import os
import time
from dataclasses import dataclass
from typing import Any

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

# Set GEMINI_MODEL in .env to change the model. Check which models your free tier
# supports (structured JSON output is required) before relying on this default.
# gemini-2.5-flash returned 404 for new users and gemini-3.8-flash returned 503 (overloaded)
# on 2026-11-11; gemini-3.5-flash worked.
DEFAULT_MODEL = "gemini-3.5-flash"
REQUEST_TIMEOUT_MS = 90_000  # a hung request must fail (and be retried), not block forever


@dataclass
class LLMResult:
    text: str
    parsed: Any  # a pydantic object if a schema was given, else None
    model: str
    prompt_tokens: int
    output_tokens: int  # includes "thinking" tokens, because they are billed as output
    latency_s: float  # total wall time including retries and waits
    attempts: int


_client: genai.Client | None = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        key = os.environ.get("GEMINI_API_KEY")
        if not key:
            raise RuntimeError("GEMINI_API_KEY is not set. Put it in .env (see .env.example).")
        _client = genai.Client(
            api_key=key, http_options=types.HttpOptions(timeout=REQUEST_TIMEOUT_MS)
        )
    return _client


def call_llm(
    prompt: str,
    *,
    system: str | None = None,
    schema: Any = None,
    temperature: float = 0.0,
    max_retries: int = 1,
    retry_wait_s: float = 5.0,
) -> LLMResult:
    """Call Gemini once (plus up to `max_retries` retries on failure).

    If `schema` (a pydantic model class) is given, the answer is forced to be JSON that
    matches it and is returned in `LLMResult.parsed`.
    """
    model = os.environ.get("GEMINI_MODEL", DEFAULT_MODEL)
    config_args: dict[str, Any] = {"temperature": temperature}
    if system:
        config_args["system_instruction"] = system
    if schema is not None:
        config_args["response_mime_type"] = "application/json"
        config_args["response_schema"] = schema
    config = types.GenerateContentConfig(**config_args)

    start = time.perf_counter()
    last_error: Exception | None = None
    for attempt in range(1, max_retries + 2):
        try:
            response = _get_client().models.generate_content(
                model=model, contents=prompt, config=config
            )
            if schema is not None and response.parsed is None:
                raise ValueError("Model answer did not match the requested JSON schema.")
            usage = response.usage_metadata
            output_tokens = (usage.candidates_token_count or 0) + (usage.thoughts_token_count or 0)
            return LLMResult(
                text=response.text or "",
                parsed=response.parsed if schema is not None else None,
                model=model,
                prompt_tokens=usage.prompt_token_count or 0,
                output_tokens=output_tokens,
                latency_s=time.perf_counter() - start,
                attempts=attempt,
            )
        except Exception as error:  # network, rate limit, bad JSON, ...
            last_error = error
            if attempt <= max_retries:
                time.sleep(retry_wait_s * attempt)  # wait a bit longer each time
    raise RuntimeError(f"Gemini call failed after {max_retries + 1} attempts: {last_error}")
