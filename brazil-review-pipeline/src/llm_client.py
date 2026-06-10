"""LLM client and per-review classification.

The ``pycelonis_llm`` import is intentionally *lazy* (inside ``get_client``) because the
package only exists inside MLWB and is not pip-installable locally. Keeping it out of
module import means unit tests and local tooling can import this module freely.
"""
from __future__ import annotations

import json
import re
from typing import Callable, List

from .schema import ReviewInsight

SYSTEM_PROMPT = (
    "You are a customer-experience analyst for a Brazilian e-commerce marketplace. "
    "You read a single product review comment (usually Portuguese) and return a "
    "structured analysis. Be objective and base the analysis only on the comment text."
)


def get_client():
    """Return a CelonisOpenAI client. MLWB-only — imports pycelonis_llm lazily."""
    import pycelonis_llm  # noqa: F401  # must be imported before openai; patches it
    from pycelonis_llm.integrations.openai import CelonisOpenAI

    return CelonisOpenAI()


def parse_json_response(content: str) -> dict:
    """Parse a JSON object from an LLM response, tolerating markdown code fences.

    Handles an optional ```json fence, a bare ``` fence, or no fence at all.
    """
    text = content.strip()
    fence = re.match(r"^```(?:json)?\s*(.*?)\s*```$", text, re.DOTALL)
    if fence:
        text = fence.group(1)
    return json.loads(text)


def _build_user_message(
    comment: str,
    themes: List[str],
    urgency_levels: List[str],
    recommend_values: List[str],
) -> str:
    """Build the extraction prompt. The allowed value lists are injected from config.yaml,
    so collaborators change what the model may return by editing config — not this code."""
    theme_list = ", ".join(themes)
    urgency_list = ", ".join(urgency_levels)
    recommend_list = ", ".join(f'"{v}"' for v in recommend_values)
    return (
        f"Review comment:\n\"\"\"\n{comment}\n\"\"\"\n\n"
        "Analyse the comment and return a JSON object with exactly these keys:\n"
        '  - "sentiment": one of "positive", "neutral", "negative"\n'
        f'  - "themes": a list of one or more tags chosen ONLY from: [{theme_list}]\n'
        '  - "summary_en": a concise one-sentence English summary of the comment\n'
        f'  - "urgency": one of [{urgency_list}] — how urgently this review needs attention\n'
        f'  - "would_recommend": one of [{recommend_list}] — whether the reviewer would '
        "recommend the product or seller\n"
        '  - "refund_or_return_request": true or false — does the customer ask for a refund, '
        "return, or exchange\n"
        '  - "actionable": true or false — does this review require a follow-up action from '
        "the seller\n\n"
        "Respond with valid JSON only."
    )


def classify_review(
    client,
    comment: str,
    model: str,
    themes: List[str],
    urgency_levels: List[str],
    recommend_values: List[str],
    temperature: float = 0,
) -> ReviewInsight:
    """Classify one review comment into a validated ReviewInsight."""
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": _build_user_message(
                    comment, themes, urgency_levels, recommend_values
                ),
            },
        ],
        temperature=temperature,
    )
    data = parse_json_response(response.choices[0].message.content)
    return ReviewInsight(**data)


# Type alias for a classifier callable — lets pipeline.run() accept a stub in tests.
Classifier = Callable[[str], ReviewInsight]
