"""Pydantic schema for a single review's LLM-extracted insight.

Validating the LLM output through this model gives us a clean failure when the model
returns something unexpected (bad sentiment label, wrong types) instead of silently
writing garbage to the data pool.
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
