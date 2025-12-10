"""Case classification utilities with rule-based and optional LLM flows."""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Optional

from .prompt_templates import build_classification_prompt

logger = logging.getLogger(__name__)


@dataclass
class CaseClassification:
    """Represents a classified debt/bankruptcy case."""

    type: str
    urgency: str


RULE_KEYWORDS = {
    "mortgage": "mortgage",
    "ипот": "mortgage",
    "credit card": "credit_card",
    "card": "credit_card",
    "карт": "credit_card",
    "microloan": "microloan",
    "микро": "microloan",
    "payday": "microloan",
    "consumer": "consumer_loan",
    "кредит": "consumer_loan",
    "loan": "consumer_loan",
}

HIGH_URGENCY_MARKERS = [
    "court",
    "lawsuit",
    "bailiff",
    "enforcement",
    "collector",
    "threat",
    "urgent",
    "tomorrow",
    "суд",
    "пристав",
    "коллект",
    "срочно",
]


def classify_case(description: str, api_key: Optional[str] = None) -> CaseClassification:
    """
    Classify a legal debt/bankruptcy case by type and urgency.

    Returns:
        CaseClassification(type: str, urgency: str)
    """

    description = description.strip()
    if not description:
        return CaseClassification(type="other", urgency="normal")

    if not api_key:
        return _rule_based_classification(description)

    try:
        from openai import OpenAI
    except ImportError:
        logger.warning("openai is not installed; falling back to rule-based classification.")
        return _rule_based_classification(description)

    prompt = build_classification_prompt(description)
    try:
        client = OpenAI(api_key=api_key)
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You classify short debt intake descriptions into JSON labels only.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0,
            max_tokens=128,
        )
        message_content = completion.choices[0].message.content if completion.choices else ""
        parsed = _parse_model_response(message_content)
        if parsed:
            return parsed
    except Exception as exc:  # noqa: BLE001
        logger.exception("LLM classification failed; reverting to rule-based. Error: %s", exc)

    return _rule_based_classification(description)


def _rule_based_classification(description: str) -> CaseClassification:
    lowered = description.lower()
    debt_type = "other"
    for marker, label in RULE_KEYWORDS.items():
        if marker in lowered:
            debt_type = label
            break

    urgency = "high" if any(marker in lowered for marker in HIGH_URGENCY_MARKERS) else "normal"
    return CaseClassification(type=debt_type, urgency=urgency)


def _parse_model_response(content: Optional[str]) -> Optional[CaseClassification]:
    if not content:
        return None

    try:
        data = json.loads(content)
        debt_type = str(data.get("type", "other"))
        urgency = str(data.get("urgency", "normal"))
        return CaseClassification(type=debt_type, urgency=urgency)
    except json.JSONDecodeError:
        logger.warning("Model response was not valid JSON: %s", content)
        return None
