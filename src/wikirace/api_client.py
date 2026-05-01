import json
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class APIResult:
    text: str
    usage: Optional[Dict[str, Any]] = None


class FrontierAPIClient:
    """Adapter for API-only frontier model calls.

    If OPENAI_API_KEY is unavailable, caller should use mock mode.
    """

    def __init__(self):
        self.openai_key = os.getenv("OPENAI_API_KEY")

    def available(self) -> bool:
        return bool(self.openai_key)

    def complete_json(self, model: str, system_prompt: str, user_payload: Dict[str, Any], temperature: float = 0) -> APIResult:
        try:
            from openai import OpenAI
        except Exception as e:
            raise RuntimeError("openai package unavailable; install openai to use real API") from e
        if not self.openai_key:
            raise RuntimeError("OPENAI_API_KEY is not set")
        client = OpenAI(api_key=self.openai_key)
        response = client.responses.create(
            model=model,
            temperature=temperature,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
            ],
        )
        text = response.output_text
        usage = getattr(response, "usage", None)
        return APIResult(text=text, usage=usage)
