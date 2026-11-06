import os
import json
from typing import Generator, Dict, Any, List, Optional
from core.trust_engine import trust_engine
from core.audit import audit_ledger

class BaseAgent:
    def __init__(self, name: str, role: str, default_model: str = "mistral-large-latest", system_prompt: str = ""):
        self.name = name
        self.role = role
        self.default_model = default_model
        self.system_prompt = system_prompt
        self.api_key = os.getenv("MISTRAL_API_KEY", "").strip()
        self.client = None
        self._init_client()

    def _init_client(self):
        if self.api_key:
            try:
                from mistralai import Mistral
                self.client = Mistral(api_key=self.api_key)
            except Exception as e:
                print(f"Warning [{self.name}]: Mistral client init failed: {e}")
                self.client = None

    def update_api_key(self, api_key: str):
        key = api_key.strip()
        if key != self.api_key:
            self.api_key = key
            self._init_client()

    def execute_turn(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        model_override: Optional[str] = None
    ) -> Dict[str, Any]:
        """Runs a single inference turn with the Mistral API."""
        if not self.client:
            return {"error": "NO_CLIENT"}

        model = model_override or self.default_model
        try:
            kwargs = {
                "model": model,
                "messages": messages,
            }
            if tools:
                kwargs["tools"] = tools
                kwargs["tool_choice"] = "auto"

            response = self.client.chat.complete(**kwargs)
            return {"success": True, "message": response.choices[0].message}
        except Exception as e:
            return {"error": str(e)}
