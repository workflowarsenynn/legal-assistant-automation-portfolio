"""Prompt templates for optional LLM usage."""

CLASSIFICATION_PROMPT = """
You are a legal intake assistant who classifies debt or potential personal bankruptcy cases.
Read the user description and respond with a compact JSON object using the following shape:
{
  "type": "consumer_loan | credit_card | mortgage | microloan | other",
  "urgency": "normal | high"
}
Keep the response strictly as JSON without extra text.
If information is missing, choose the closest option.

User description:
"{description}"
"""

SUMMARY_PROMPT = """
You are drafting a short, respectful summary of a debt or potential bankruptcy intake.
Use a concise tone (2-4 sentences). Do not provide legal advice. Include:
- short restatement of the situation;
- key debt details;
- city/region;
- documents mentioned;
- contact method provided.

Return only the summary text without bullet points.

Context:
{context}
"""


def build_classification_prompt(description: str) -> str:
    """Render a prompt instructing the model to classify a case."""

    return CLASSIFICATION_PROMPT.format(description=description)


def build_summary_prompt(context: str) -> str:
    """Render a prompt instructing the model to produce a short summary."""

    return SUMMARY_PROMPT.format(context=context)
