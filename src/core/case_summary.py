"""Case summary generation (template-based with optional LLM)."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

from .legal_classification import CaseClassification
from .prompt_templates import build_summary_prompt

logger = logging.getLogger(__name__)


@dataclass
class IntakeData:
    """Container for collected intake data."""

    case_description: str
    debt_details: str
    city: str
    docs_info: str
    contact_info: str
    classification: Optional[CaseClassification] = None
    client_name: Optional[str] = None
    notes: Optional[str] = None


def build_case_summary(data: IntakeData, api_key: Optional[str] = None) -> str:
    """Build a short human-readable summary of the case (2–4 sentences)."""

    template_summary = _template_summary(data)
    if not api_key:
        return template_summary

    try:
        from openai import OpenAI
    except ImportError:
        logger.warning("openai is not installed; using template summary.")
        return template_summary

    prompt_context = _render_context_block(data)
    prompt = build_summary_prompt(prompt_context)
    try:
        client = OpenAI(api_key=api_key)
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You generate concise summaries for debt intake without legal advice.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            max_tokens=180,
        )
        content = completion.choices[0].message.content if completion.choices else None
        if content:
            return content.strip()
    except Exception as exc:  # noqa: BLE001
        logger.exception("LLM summary failed; reverting to template. Error: %s", exc)

    return template_summary


def _template_summary(data: IntakeData) -> str:
    name_part = f"Name provided: {data.client_name}. " if data.client_name else ""
    classification_part = ""
    if data.classification:
        classification_part = (
            f"Debt type: {data.classification.type}. "
            f"Urgency: {data.classification.urgency}. "
        )

    notes_part = f"Additional notes: {data.notes}. " if data.notes else ""

    return (
        f"{name_part}The person reported: {data.case_description}. "
        f"Debt details: {data.debt_details}. City/region: {data.city or 'not provided'}. "
        f"Documents: {data.docs_info or 'not specified'}. "
        f"Contact: {data.contact_info}. "
        f"{classification_part}{notes_part}"
    ).strip()


def _render_context_block(data: IntakeData) -> str:
    parts = [
        f"Description: {data.case_description}",
        f"Debt details: {data.debt_details}",
        f"City: {data.city or 'not provided'}",
        f"Documents: {data.docs_info or 'not specified'}",
        f"Contact: {data.contact_info}",
    ]
    if data.client_name:
        parts.append(f"Name: {data.client_name}")
    if data.classification:
        parts.append(
            f"Classification: type={data.classification.type}, urgency={data.classification.urgency}"
        )
    if data.notes:
        parts.append(f"Notes: {data.notes}")
    return "\n".join(parts)
