"""Thin wrapper around python-telegram-bot application setup."""
from __future__ import annotations

import logging
from typing import Optional

from telegram.ext import Application

from src.config import AppConfig
from src.core.intake_flow import IntakeFlow
from .handlers import register_handlers

logger = logging.getLogger(__name__)


class TelegramBotClient:
    """Build and run the Telegram bot application."""

    def __init__(self, config: AppConfig, intake_flow: IntakeFlow) -> None:
        self.config = config
        self.intake_flow = intake_flow
        self.application: Optional[Application] = None

    def build_application(self) -> Application:
        application = Application.builder().token(self.config.telegram_bot_token).build()
        register_handlers(application, self.intake_flow)
        logger.info("Telegram application configured")
        self.application = application
        return application

    def run(self) -> None:
        if not self.application:
            self.build_application()
        assert self.application is not None
        logger.info("Starting Telegram bot polling")
        self.application.run_polling()
