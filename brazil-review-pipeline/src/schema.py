"""Pydantic schema for a single review's LLM-extracted insight.

Validating the LLM output through this model gives us a clean failure when the model
returns something unexpected (bad sentiment label, wrong types) instead of silently
writing garbage to the data pool.

Design note — closed sets vs. strict types:
- ``sentiment`` is a strict ``Literal``: it is the core field and its three values never
  change, so an out-of-set value should fail loudly.
- ``themes``, ``urgency`` and ``would_recommend`` are *prompt-enforced* closed sets whose
  allowed values live in ``config.yaml`` (low-code: collaborators edit the lists, not this
  file). Here we only normalise (lowercase/strip) and fall back to a safe default, so adding
  a new allowed value in config never requires a schema change.
"""
from __future__ import annotations

from typing import List, Literal

from pydantic import BaseModel, field_validator

Sentiment = Literal["positive", "neutral", "negative"]


class ReviewInsight(BaseModel):
    """Structured result of analysing one review comment."""

    sentiment: Sentiment
    themes: List[str]
    summary_en: str
    # Enriched fields (prompt-enforced closed sets / booleans). Defaults are safe fallbacks
    # used when the model omits a field or returns a blank value.
    urgency: str = "medium"
    would_recommend: str = "unclear"
    refund_or_return_request: bool = False
    actionable: bool = False

    @field_validator("themes")
    @classmethod
    def _non_empty_unique(cls, v: List[str]) -> List[str]:
        # Normalise: lowercase, strip, drop blanks, de-duplicate, keep order.
        seen: set[str] = set()
        out: List[str] = []
        for t in v:
            t = (t or "").strip().lower()
            if t and t not in seen:
                seen.add(t)
                out.append(t)
        return out or ["other"]

    @field_validator("urgency", "would_recommend", mode="before")
    @classmethod
    def _normalise_label(cls, v, info):
        """Lowercase/strip a single-choice label; fall back to the field default if blank.

        Membership in the allowed set is enforced by the prompt (values come from
        config.yaml), so we deliberately do NOT reject unknown values here — that keeps the
        closed sets editable in config without touching this model.
        """
        default = cls.model_fields[info.field_name].default
        if v is None:
            return default
        s = str(v).strip().lower()
        return s or default
