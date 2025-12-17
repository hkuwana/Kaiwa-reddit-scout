"""
Gemini API client wrapper for lead analysis.
Uses REST API directly to avoid cryptography dependency issues.
"""

import json
import logging
from typing import Optional
import urllib.request
import urllib.error

from src.config.settings import gemini_config

logger = logging.getLogger(__name__)

# Gemini API endpoint
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


class GeminiClient:
    """Wrapper for Google Gemini API using REST."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize Gemini client.

        Args:
            api_key: Gemini API key (default: from env)
            model: Model name (default: from env)
        """
        self.api_key = api_key or gemini_config.api_key
        self.model_name = model or gemini_config.model

        if not self.api_key:
            logger.warning("Gemini API key not set - analysis will be skipped")

    def is_configured(self) -> bool:
        """Check if the client is properly configured."""
        return bool(self.api_key)

    def _make_request(self, prompt: str, max_tokens: int = 1024, temperature: float = 0.7, json_mode: bool = False) -> Optional[str]:
        """Make a request to Gemini API."""
        if not self.is_configured():
            return None

        url = GEMINI_API_URL.format(model=self.model_name) + f"?key={self.api_key}"

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ],
            "generationConfig": {
                "maxOutputTokens": max_tokens,
                "temperature": temperature,
            }
        }

        if json_mode:
            payload["generationConfig"]["responseMimeType"] = "application/json"

        try:
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(
                url,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST"
            )

            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode('utf-8'))

            # Extract text from response
            candidates = result.get("candidates", [])
            if candidates:
                content = candidates[0].get("content", {})
                parts = content.get("parts", [])
                if parts:
                    return parts[0].get("text", "")

            return None

        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8') if e.fp else str(e)
            logger.error(f"Gemini API HTTP error {e.code}: {error_body}")
            return None
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return None

    def generate(self, prompt: str, max_tokens: int = 1024) -> Optional[str]:
        """
        Generate text using Gemini.

        Args:
            prompt: The prompt to send
            max_tokens: Maximum tokens in response

        Returns:
            Generated text or None on error
        """
        return self._make_request(prompt, max_tokens, temperature=0.7)

    def generate_json(self, prompt: str, max_tokens: int = 1024) -> Optional[str]:
        """
        Generate JSON response using Gemini.

        Args:
            prompt: The prompt (should ask for JSON output)
            max_tokens: Maximum tokens in response

        Returns:
            Generated JSON string or None on error
        """
        return self._make_request(prompt, max_tokens, temperature=0.3, json_mode=True)


# Global client instance (lazy loaded to avoid import issues)
_gemini_client = None

def get_gemini_client() -> GeminiClient:
    """Get or create the global Gemini client."""
    global _gemini_client
    if _gemini_client is None:
        _gemini_client = GeminiClient()
    return _gemini_client

# For backwards compatibility
gemini_client = None  # Will be set on first use


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("Testing Gemini Client")
    print("=" * 50)

    client = GeminiClient()
    print(f"Configured: {client.is_configured()}")

    if client.is_configured():
        response = client.generate("Say hello in Japanese in one sentence!")
        print(f"Response: {response}")
