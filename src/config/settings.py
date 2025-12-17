"""
Application settings loaded from environment variables.
"""

import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root
PROJECT_ROOT = Path(__file__).parent.parent.parent
load_dotenv(PROJECT_ROOT / ".env")


@dataclass
class RedditConfig:
    """Reddit API configuration."""
    client_id: str
    client_secret: str
    user_agent: str
    username: str
    password: str

    @classmethod
    def from_env(cls) -> "RedditConfig":
        return cls(
            client_id=os.getenv("REDDIT_CLIENT_ID", ""),
            client_secret=os.getenv("REDDIT_CLIENT_SECRET", ""),
            user_agent=os.getenv("REDDIT_USER_AGENT", "KaiwaScout/1.0"),
            username=os.getenv("REDDIT_USERNAME", ""),
            password=os.getenv("REDDIT_PASSWORD", ""),
        )

    def is_valid(self) -> bool:
        """Check if required credentials are set."""
        return bool(self.client_id and self.client_secret)


@dataclass
class GeminiConfig:
    """Gemini API configuration."""
    api_key: str
    model: str
    signal_threshold: int

    @classmethod
    def from_env(cls) -> "GeminiConfig":
        return cls(
            api_key=os.getenv("GEMINI_API_KEY", ""),
            model=os.getenv("GEMINI_MODEL", "gemma-3-27b-it"),
            signal_threshold=int(os.getenv("SIGNAL_THRESHOLD", "7")),
        )

    def is_valid(self) -> bool:
        """Check if API key is set."""
        return bool(self.api_key)


@dataclass
class SheetsConfig:
    """Google Sheets configuration."""
    credentials_json: str  # Inline JSON credentials
    credentials_file: str  # Path to credentials file (fallback)
    sheet_name: str
    folder_id: str  # Optional Google Drive folder ID
    impersonate_email: str  # Email to impersonate (domain-wide delegation)

    @classmethod
    def from_env(cls) -> "SheetsConfig":
        return cls(
            credentials_json=os.getenv("GOOGLE_CREDENTIALS_JSON", ""),
            credentials_file=os.getenv("GOOGLE_CREDENTIALS_FILE", "google_creds.json"),
            sheet_name=os.getenv("GOOGLE_SHEET_NAME", "Kaiwa Leads Dashboard"),
            folder_id=os.getenv("GOOGLE_FOLDER_ID", ""),
            impersonate_email=os.getenv("GOOGLE_IMPERSONATE_EMAIL", ""),
        )

    def has_inline_json(self) -> bool:
        """Check if inline JSON credentials are provided."""
        return bool(self.credentials_json.strip())

    def is_valid(self) -> bool:
        """Check if credentials are available (inline JSON or file exists)."""
        if self.has_inline_json():
            return True
        creds_path = PROJECT_ROOT / self.credentials_file
        return creds_path.exists()

    def get_credentials_path(self) -> Path:
        """Get the path to credentials file."""
        return PROJECT_ROOT / self.credentials_file


@dataclass
class AppConfig:
    """Application configuration."""
    log_level: str
    max_posts_per_run: int
    data_dir: Path

    @classmethod
    def from_env(cls) -> "AppConfig":
        return cls(
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            max_posts_per_run=int(os.getenv("MAX_POSTS_PER_RUN", "100")),
            data_dir=PROJECT_ROOT / "data",
        )


# Global config instances
reddit_config = RedditConfig.from_env()
gemini_config = GeminiConfig.from_env()
sheets_config = SheetsConfig.from_env()
app_config = AppConfig.from_env()


def print_config_status():
    """Print configuration status for debugging."""
    print("=" * 50)
    print("Configuration Status")
    print("=" * 50)
    print(f"Reddit API configured: {reddit_config.is_valid()}")
    print(f"  - Client ID: {'***' + reddit_config.client_id[-4:] if len(reddit_config.client_id) > 4 else '(not set)'}")
    print(f"  - Username: {reddit_config.username or '(not set)'}")
    print(f"Gemini API configured: {gemini_config.is_valid()}")
    print(f"  - Model: {gemini_config.model}")
    print(f"  - Signal threshold: {gemini_config.signal_threshold}")
    print(f"Google Sheets configured: {sheets_config.is_valid()}")
    print(f"  - Credentials: {'(inline JSON)' if sheets_config.has_inline_json() else sheets_config.credentials_file}")
    print(f"  - Sheet name: {sheets_config.sheet_name}")
    print(f"Log level: {app_config.log_level}")
    print(f"Max posts per run: {app_config.max_posts_per_run}")
    print(f"Data directory: {app_config.data_dir}")
    print("=" * 50)


if __name__ == "__main__":
    print_config_status()
