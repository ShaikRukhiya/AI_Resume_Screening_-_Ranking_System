from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional

import requests


class LLMAdapter:
    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or os.getenv("MODEL_NAME", "gpt-4o-mini")
        self.api_key = os.getenv("OPENAI_API_KEY")

    def generate_structured(self, prompt: str, schema: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        if not self.api_key:
            return None
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "response_format": {"type": "json_object"},
        }
        if schema:
            payload["functions"] = [{"name": "return_json", "parameters": schema}]
        try:
            response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=20)
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            return json.loads(content)
        except Exception:
            return None
