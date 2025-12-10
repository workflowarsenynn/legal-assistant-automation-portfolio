"""Telegram handlers mapping updates to the intake flow."""
from __future__ import annotations

import logging
from typing import Optional

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from src.core.intake_flow import IntakeFlow

logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_chat:
        return
    chat_id = str(update.effective_chat.id)
    flow = _get_flow(context)
    result = flow.start_session(chat_id)
    await update.message.reply_text(result.reply_text)  # type: ignore[union-attr]


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_chat or not update.message:
        return
    chat_id = str(update.effective_chat.id)
    flow = _get_flow(context)
    result = flow.process_message(chat_id, update.message.text)
    await update.message.reply_text(result.reply_text)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_chat or not update.message:
        return
    await update.message.reply_text(
        "I collect information about debts to pass it to a lawyer. Use /start to begin."
    )


def register_handlers(application: Application, intake_flow: IntakeFlow) -> None:
    """Attach command and message handlers to the Telegram application."""

    application.bot_data["intake_flow"] = intake_flow
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))


def _get_flow(context: ContextTypes.DEFAULT_TYPE) -> IntakeFlow:
    flow: Optional[IntakeFlow] = context.application.bot_data.get("intake_flow")
    if not flow:
        raise RuntimeError("IntakeFlow is not configured in bot_data")
    return flow
