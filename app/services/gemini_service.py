import os
import json
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger("GeminiService")

class GeminiService:
    def __init__(self):
        self.api_key = os.environ.get("GEMINI_API_KEY") or ""
        self.client = None
        self._init_client()

    def _init_client(self):
        if not self.api_key:
            from app.config import settings
            self.api_key = settings.GEMINI_API_KEY or ""

        if self.api_key:
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
                logger.info("google-genai client initialized successfully.")
            except ImportError:
                try:
                    import google.generativeai as legacy_genai
                    legacy_genai.configure(api_key=self.api_key)
                    self.client = "legacy"
                    logger.info("google.generativeai legacy client configured.")
                except Exception as e:
                    logger.warning(f"Failed to configure Gemini legacy client: {e}")
            except Exception as e:
                logger.warning(f"Failed to configure google-genai client: {e}")

    def is_available(self) -> bool:
        return bool(self.api_key and self.client is not None)

    def set_api_key(self, api_key: str):
        self.api_key = api_key
        self._init_client()

    async def generate_json(self, prompt: str, system_instruction: Optional[str] = None) -> Dict[str, Any]:
        """Calls Gemini API requesting structured JSON output."""
        if not self.is_available():
            logger.info("Gemini API key not configured; using offline fallback.")
            return {}

        try:
            if self.client != "legacy":
                from google.genai import types
                config = types.GenerateContentConfig(
                    response_mime_type="application/json",
                    system_instruction=system_instruction,
                    temperature=0.2
                )
                response = self.client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                    config=config
                )
                raw_text = response.text.strip()
            else:
                import google.generativeai as legacy_genai
                model = legacy_genai.GenerativeModel(
                    model_name="gemini-1.5-flash",
                    system_instruction=system_instruction,
                    generation_config={"response_mime_type": "application/json", "temperature": 0.2}
                )
                response = await model.generate_content_async(prompt)
                raw_text = response.text.strip()

            if raw_text.startswith("```json"):
                raw_text = raw_text[7:]
            if raw_text.startswith("```"):
                raw_text = raw_text[3:]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]

            return json.loads(raw_text.strip())
        except Exception as e:
            logger.error(f"Error calling Gemini generate_json: {e}")
            return {}

    async def generate_text(self, prompt: str, system_instruction: Optional[str] = None, temperature: float = 0.5) -> str:
        """Calls Gemini API for freeform text generation (e.g. cover letters)."""
        if not self.is_available():
            return ""

        try:
            if self.client != "legacy":
                from google.genai import types
                config = types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=temperature
                )
                response = self.client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                    config=config
                )
                return response.text.strip()
            else:
                import google.generativeai as legacy_genai
                model = legacy_genai.GenerativeModel(
                    model_name="gemini-1.5-flash",
                    system_instruction=system_instruction,
                    generation_config={"temperature": temperature}
                )
                response = await model.generate_content_async(prompt)
                return response.text.strip()
        except Exception as e:
            logger.error(f"Error calling Gemini generate_text: {e}")
            return ""

gemini_service = GeminiService()
