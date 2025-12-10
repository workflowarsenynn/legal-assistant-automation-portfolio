"""Orchestration layer combining FSM, classification, summary, and storage."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict

from ..bot.state_machine import IntakeStateMachine, StageContext, State
from .case_summary import IntakeData, build_case_summary
from .legal_classification import CaseClassification, classify_case
from ..storage.db import save_case

logger = logging.getLogger(__name__)


@dataclass
class FlowResult:
    reply_text: str
    state: State
    saved: bool = False


class IntakeFlow:
    """Coordinates the FSM with optional classification, summary, and persistence."""

    def __init__(self, openai_api_key: str | None, db_path: str) -> None:
        self.openai_api_key = openai_api_key
        self.db_path = db_path
        self.sessions: Dict[str, IntakeStateMachine] = {}

    def start_session(self, chat_id: str) -> FlowResult:
        machine = IntakeStateMachine(chat_id=chat_id)
        self.sessions[chat_id] = machine
        response = machine.start()
        return FlowResult(reply_text=response.reply_text, state=response.state)

    def process_message(self, chat_id: str, text: str) -> FlowResult:
        machine = self.sessions.get(chat_id)
        if not machine:
            machine = IntakeStateMachine(chat_id=chat_id)
            self.sessions[chat_id] = machine
            response = machine.start()
            return FlowResult(reply_text=response.reply_text, state=response.state)

        response = machine.handle_user_reply(text, summary_builder=self._build_summary_from_context)
        saved = False
        if response.should_save:
            try:
                self._persist_case(response.context)
                saved = True
            except Exception as exc:  # noqa: BLE001
                logger.exception("Failed to save case for chat %s: %s", chat_id, exc)
        return FlowResult(reply_text=response.reply_text, state=response.state, saved=saved)

    def _build_summary_from_context(self, context: StageContext) -> str:
        description_basis = context.case_description or context.debt_details or ""
        classification: CaseClassification = classify_case(description_basis, api_key=self.openai_api_key)
        context.classification = classification

        intake_data = IntakeData(
            case_description=context.case_description or "",
            debt_details=context.debt_details or "",
            city=context.city or "",
            docs_info=context.docs_info or "",
            contact_info=context.contact_info or "",
            classification=classification,
            client_name=context.client_name,
            notes=context.notes,
        )
        summary = build_case_summary(intake_data, api_key=self.openai_api_key)
        context.summary = summary
        return summary

    def _persist_case(self, context: StageContext) -> None:
        classification = context.classification or classify_case(
            context.case_description or context.debt_details or "",
            api_key=self.openai_api_key,
        )
        intake_data = IntakeData(
            case_description=context.case_description or "",
            debt_details=context.debt_details or "",
            city=context.city or "",
            docs_info=context.docs_info or "",
            contact_info=context.contact_info or "",
            classification=classification,
            client_name=context.client_name,
            notes=context.notes,
        )
        save_case(self.db_path, context.chat_id, intake_data, summary_text=context.summary)
