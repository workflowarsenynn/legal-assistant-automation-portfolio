"""Entrypoint for running the Telegram intake bot."""
from __future__ import annotations

import logging

from src.config import load_config
from src.core.intake_flow import IntakeFlow
from src.logging_utils import setup_logging
from src.storage.db import init_db
from src.bot.telegram_client import TelegramBotClient


def main() -> None:
    config = load_config()
    setup_logging(log_level=config.log_level, log_file="logs/app.log")
    logging.getLogger(__name__).info("Config loaded. Initializing storage and bot.")

    init_db(config.db_path)

    intake_flow = IntakeFlow(openai_api_key=config.openai_api_key, db_path=config.db_path)
    bot_client = TelegramBotClient(config, intake_flow)
    bot_client.run()


if __name__ == "__main__":
    main()
