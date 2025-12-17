"""
Gemini API client wrapper for lead analysis.
"""

import logging
from typing import Optional

import google.generativeai as genai

from src.config.settings import gemini_config

logger = logging.getLogger(__name__)


class GeminiClient:
    """Wrapper for Google Gemini API."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize Gemini client.

        Args:
            api_key: Gemini API key (default: from env)
            model: Model name (default: from env)
        """
        self.api_key = api_key or gemini_config.api_key
        self.model_name = model or gemini_config.model
        self._model = None

        if not self.api_key:
            logger.warning("Gemini API key not set - analysis will be skipped")

    def _get_model(self):
        """Lazy initialization of the model."""
        if self._model is None:
            genai.configure(api_key=self.api_key)
            self._model = genai.GenerativeModel(self.model_name)
        return self._model

    def is_configured(self) -> bool:
        """Check if the client is properly configured."""
        return bool(self.api_key)

    def generate(self, prompt: str, max_tokens: int = 1024) -> Optional[str]:
        """
        Generate text using Gemini.

        Args:
            prompt: The prompt to send
            max_tokens: Maximum tokens in response

        Returns:
            Generated text or None on error
        """
        if not self.is_configured():
            return None

        try:
            model = self._get_model()
            response = model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    max_output_tokens=max_tokens,
                    temperature=0.7,
                ),
            )
            return response.text
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return None

    def generate_json(self, prompt: str, max_tokens: int = 1024) -> Optional[str]:
        """
        Generate JSON response using Gemini.

        Args:
            prompt: The prompt (should ask for JSON output)
            max_tokens: Maximum tokens in response

        Returns:
            Generated JSON string or None on error
        """
        if not self.is_configured():
            return None

        try:
            model = self._get_model()
            response = model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    max_output_tokens=max_tokens,
                    temperature=0.3,  # Lower temperature for structured output
                    response_mime_type="application/json",
                ),
            )
            return response.text
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return None


# Global client instance
gemini_client = GeminiClient()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("Testing Gemini Client")
    print("=" * 50)

    client = GeminiClient()
    print(f"Configured: {client.is_configured()}")

    if client.is_configured():
        response = client.generate("Say hello in Japanese!")
        print(f"Response: {response}")
