import asyncio
import logging
import os
from typing import Dict, List, Optional

from dotenv import load_dotenv
from openai import OpenAI, OpenAIError

load_dotenv()

DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


async def generate_reply(
    messages: List[Dict[str, str]],
    *,
    model: Optional[str] = None,
    temperature: float = 0.3,
) -> str:
    """
    Execute a chat completion request using the provided history.
    This call runs in a background thread to keep the async bot responsive.
    """

    if _client.api_key is None:
        raise RuntimeError("OPENAI_API_KEY is not configured")

    model_name = model or DEFAULT_MODEL

    def _call_openai() -> str:
        try:
            response = _client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=temperature,
            )
        except OpenAIError as exc:
            logging.exception("OpenAI chat completion failed")
            raise RuntimeError("OpenAI request failed") from exc

        choice = response.choices[0].message
        return (choice.content or "").strip()

    return await asyncio.to_thread(_call_openai)

