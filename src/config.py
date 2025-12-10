"""Application configuration loading utilities."""
from dataclasses import dataclass
import os
from pathlib import Path
from typing import Optional

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    # python-dotenv is optional; environment variables can be provided externally.
    pass


@dataclass
class AppConfig:
    """Container for application settings sourced from environment variables."""

    telegram_bot_token: str
    openai_api_key: Optional[str]
    db_path: str
    log_level: str = "INFO"


def load_config() -> AppConfig:
    """Load configuration from environment variables and provide sensible defaults."""

    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN is required. Set it in the environment or .env file.")

    db_path = os.getenv("DB_PATH", str(Path("data") / "legal_cases.db"))
    openai_api_key = os.getenv("OPENAI_API_KEY") or None
    log_level = os.getenv("LOG_LEVEL", "INFO")

    return AppConfig(
        telegram_bot_token=token,
        openai_api_key=openai_api_key,
        db_path=db_path,
        log_level=log_level,
    )
