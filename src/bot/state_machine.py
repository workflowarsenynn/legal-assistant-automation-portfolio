"""Finite state machine driving the intake dialogue."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Callable, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from src.core.legal_classification import CaseClassification


class State(Enum):
    GREETING = auto()
    CASE_DESCRIPTION = auto()
    DEBT_DETAILS = auto()
    CITY = auto()
    DOCS_INFO = auto()
    CONTACTS = auto()
    CONFIRMATION = auto()
    CLOSE = auto()


@dataclass
class StageContext:
    """Holds collected data during the intake dialogue."""

    chat_id: str
    case_description: Optional[str] = None
    debt_details: Optional[str] = None
    city: Optional[str] = None
    docs_info: Optional[str] = None
    contact_info: Optional[str] = None
    client_name: Optional[str] = None
    classification: Optional["CaseClassification"] = None
    summary: Optional[str] = None
    notes: Optional[str] = None
    message_count: int = 0
    attempts: Dict[State, int] = field(default_factory=dict)


@dataclass
class StateResponse:
    """Result of processing a user message."""

    reply_text: str
    state: State
    context: StageContext
    should_save: bool = False


class IntakeStateMachine:
    """Explicit FSM controlling the intake flow."""

    def __init__(self, chat_id: str, max_total_responses: int = 10, max_attempts_per_state: int = 2) -> None:
        self.context = StageContext(chat_id=chat_id)
        self.state = State.GREETING
        self.max_total_responses = max_total_responses
        self.max_attempts_per_state = max_attempts_per_state

    def start(self) -> StateResponse:
        greeting = (
            "Hello! I am an intake assistant focused on debts and potential personal bankruptcy. "
            "I do not provide legal advice. I will ask a few questions and pass the information to a lawyer. "
            "Please briefly describe your situation with debts."
        )
        return self._reply(greeting, State.CASE_DESCRIPTION)

    def handle_user_reply(
        self, user_message: str, summary_builder: Optional[Callable[[StageContext], str]] = None
    ) -> StateResponse:
        if self.context.message_count >= self.max_total_responses:
            return self._reply(
                "We have reached the limit of questions for now. I will forward what we collected.",
                State.CLOSE,
                should_save=True,
            )

        message = (user_message or "").strip()

        if self.state == State.CASE_DESCRIPTION:
            return self._handle_case_description(message)
        if self.state == State.DEBT_DETAILS:
            return self._handle_debt_details(message)
        if self.state == State.CITY:
            return self._handle_city(message)
        if self.state == State.DOCS_INFO:
            return self._handle_docs_info(message)
        if self.state == State.CONTACTS:
            return self._handle_contacts(message, summary_builder)
        if self.state == State.CONFIRMATION:
            return self._handle_confirmation(message)

        # If user sends something unexpected, restart with greeting.
        return self.start()

    def _handle_case_description(self, message: str) -> StateResponse:
        if not message:
            return self._retry_or_move(
                State.CASE_DESCRIPTION,
                "Please describe your situation with debts in a few words (e.g., missed payments, calls from lenders).",
                fallback_state=State.DEBT_DETAILS,
            )

        self.context.case_description = message
        prompt = "Thanks for sharing. What kind of debts are involved (consumer loan, credit card, mortgage, microloan)?"
        return self._reply(prompt, State.DEBT_DETAILS)

    def _handle_debt_details(self, message: str) -> StateResponse:
        if not message:
            return self._retry_or_move(
                State.DEBT_DETAILS,
                "Which debts are we talking about? Any overdue payments or collector activity?",
                fallback_state=State.CITY,
            )

        self.context.debt_details = message
        prompt = "Got it. Which city or region are you in?"
        return self._reply(prompt, State.CITY)

    def _handle_city(self, message: str) -> StateResponse:
        if not message:
            return self._retry_or_move(State.CITY, "Please share your city or region.", fallback_state=State.DOCS_INFO)

        self.context.city = message
        prompt = "Do you have any documents (agreements, court decisions, bank letters, receipts)?"
        return self._reply(prompt, State.DOCS_INFO)

    def _handle_docs_info(self, message: str) -> StateResponse:
        if not message:
            return self._retry_or_move(
                State.DOCS_INFO,
                "Let me know if you have any documents such as contracts, court letters, or receipts.",
                fallback_state=State.CONTACTS,
            )

        self.context.docs_info = message
        prompt = "Please share your name and the best way to contact you (phone, Telegram handle, messenger)."
        return self._reply(prompt, State.CONTACTS)

    def _handle_contacts(
        self, message: str, summary_builder: Optional[Callable[[StageContext], str]] = None
    ) -> StateResponse:
        if not message:
            return self._retry_or_move(
                State.CONTACTS,
                "I need a name and a contact method (phone, @handle, messenger) to pass to the lawyer.",
                fallback_state=State.CONFIRMATION,
            )

        self.context.contact_info = message
        self.context.client_name = self._extract_name_from_contact(message)

        summary_text = None
        if summary_builder:
            summary_text = summary_builder(self.context)
        self.context.summary = summary_text or self._fallback_summary()

        confirmation_prompt = self._build_confirmation_prompt(self.context.summary)
        return self._reply(confirmation_prompt, State.CONFIRMATION)

    def _handle_confirmation(self, message: str) -> StateResponse:
        if self._is_positive(message):
            closing = "Thank you. I have forwarded the details to a lawyer. They will reach out to you soon."
            return self._reply(closing, State.CLOSE, should_save=True)

        attempts = self.context.attempts.get(State.CONFIRMATION, 0)
        self.context.attempts[State.CONFIRMATION] = attempts + 1
        self.context.notes = message or self.context.notes

        if attempts + 1 >= self.max_attempts_per_state:
            closing = (
                "I noted your remarks and will pass the current information to a lawyer. They will clarify details directly."
            )
            return self._reply(closing, State.CLOSE, should_save=True)

        prompt = (
            "Noted. If something needs correcting, share it here. "
            "When ready, reply 'yes' to confirm sending to a lawyer."
        )
        return self._reply(prompt, State.CONFIRMATION)

    def _retry_or_move(self, state: State, prompt: str, fallback_state: Optional[State] = None) -> StateResponse:
        attempts = self.context.attempts.get(state, 0)
        if attempts + 1 >= self.max_attempts_per_state:
            if fallback_state:
                notice = "I'll move forward with what we have. "
                if state == State.CONTACTS:
                    notice = "I'll move forward even without contacts. "
                combined_prompt = notice + prompt
                return self._reply(combined_prompt, fallback_state)
            return self._reply("Let's wrap up here. I'll forward the information I have.", State.CLOSE, should_save=True)

        self.context.attempts[state] = attempts + 1
        return self._reply(prompt, state)

    def _build_confirmation_prompt(self, summary_text: str) -> str:
        return (
            f"Here is a short summary of your case:\n{summary_text}\n"
            "Please confirm if this is correct (yes/ok) or share corrections."
        )

    def _fallback_summary(self) -> str:
        return (
            f"Case: {self.context.case_description or 'no description'}. "
            f"Debts: {self.context.debt_details or 'no details'}. "
            f"City: {self.context.city or 'unknown'}. "
            f"Documents: {self.context.docs_info or 'not specified'}. "
            f"Contact: {self.context.contact_info or 'not provided'}."
        )

    @staticmethod
    def _is_positive(message: str) -> bool:
        normalized = (message or "").strip().lower()
        return normalized in {"yes", "y", "ok", "okay", "да", "ага", "confirm"}

    @staticmethod
    def _extract_name_from_contact(contact: str) -> Optional[str]:
        if not contact:
            return None
        separators = [",", "/", "|"]
        for sep in separators:
            if sep in contact:
                candidate = contact.split(sep, 1)[0].strip()
                return candidate or None
        words = contact.strip().split()
        if len(words) >= 2:
            return " ".join(words[:2])
        return None

    def _reply(self, text: str, next_state: State, should_save: bool = False) -> StateResponse:
        self.context.message_count += 1
        self.state = next_state
        return StateResponse(reply_text=text.strip(), state=next_state, context=self.context, should_save=should_save)
