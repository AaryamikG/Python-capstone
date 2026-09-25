from typing import TypeVar

from google import genai
from google.genai import types
from pydantic import BaseModel

SchemaT = TypeVar("SchemaT", bound=BaseModel)


class GeminiClient:
    """Thin wrapper around the google-genai SDK.

    Every agent depends on this narrow interface (generate_text / generate_json) rather than
    on the SDK directly, so tests can swap in a fake implementation and never hit the network
    or spend real API quota.
    """

    def __init__(self, api_key: str, model: str = "gemini-3.5-flash-lite"):
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not set.")
        self._client = genai.Client(api_key=api_key)
        self._model = model

    def generate_text(
        self,
        prompt: str,
        system_instruction: str | None = None,
        temperature: float = 0.0,
    ) -> str:
        response = self._client.models.generate_content(
            model=self._model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=temperature,
            ),
        )
        return (response.text or "").strip()

    def generate_json(
        self,
        prompt: str,
        schema: type[SchemaT],
        system_instruction: str | None = None,
        temperature: float = 0.0,
    ) -> SchemaT:
        response = self._client.models.generate_content(
            model=self._model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=temperature,
                response_mime_type="application/json",
                response_schema=schema,
            ),
        )
        parsed = getattr(response, "parsed", None)
        if isinstance(parsed, schema):
            return parsed
        return schema.model_validate_json(response.text)
