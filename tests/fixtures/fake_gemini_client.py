from pydantic import BaseModel


class FakeGeminiClient:
    """Drop-in stand-in for GeminiClient. Returns pre-programmed responses in call order and
    records every call so tests can assert on prompts/counts without touching the network."""

    def __init__(self, text_responses: list[str] | None = None, json_responses: list[BaseModel] | None = None):
        self._text_responses = list(text_responses or [])
        self._json_responses = list(json_responses or [])
        self.text_calls: list[dict] = []
        self.json_calls: list[dict] = []

    def generate_text(self, prompt: str, system_instruction: str | None = None, temperature: float = 0.0) -> str:
        self.text_calls.append({"prompt": prompt, "system_instruction": system_instruction})
        if not self._text_responses:
            raise AssertionError("FakeGeminiClient.generate_text called with no queued response.")
        return self._text_responses.pop(0)

    def generate_json(self, prompt: str, schema, system_instruction: str | None = None, temperature: float = 0.0):
        self.json_calls.append({"prompt": prompt, "schema": schema, "system_instruction": system_instruction})
        if not self._json_responses:
            raise AssertionError("FakeGeminiClient.generate_json called with no queued response.")
        return self._json_responses.pop(0)
