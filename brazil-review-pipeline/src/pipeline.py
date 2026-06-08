"""Pipeline orchestration: load reviews -> classify each -> assemble insight table."""
from __future__ import annotations

import os
from typing import Optional

import pandas as pd

from .config import get_config
from .data_loader import load_reviews
from .llm_client import Classifier, classify_review, get_client

# Where the Action Flow drops runtime files, and the local default for testing.
_INPUT_DIR = "input-data"
_DEFAULT_LOCAL_INPUT = os.path.join("test-data", "sample_reviews.csv")


def _resolve_input_path(input_filename: Optional[str]) -> str:
    """Resolve the reviews CSV path.

    An Action Flow delivers a file into ``input-data/``; locally we fall back to the
    synthetic sample under ``test-data/``.
    """
    if input_filename:
        return os.path.join(_INPUT_DIR, input_filename)
    return _DEFAULT_LOCAL_INPUT


def run(
    input_filename: Optional[str] = None,
    max_rows: Optional[int] = None,
    classifier: Optional[Classifier] = None,
    config: Optional[dict] = None,
) -> pd.DataFrame:
    """Run the review-analysis pipeline and return the ``review_insights`` table.

    Args:
        input_filename: file under ``input-data/`` to analyse (Action Flow param).
            When omitted, the local synthetic sample is used.
        max_rows: optional cap for cheap runs.
        classifier: optional ``comment -> ReviewInsight`` callable. Injected by tests
            and dry runs; when ``None`` a real CelonisOpenAI-backed classifier is built.
        config: optional pre-loaded config dict (defaults to get_config()).

    Returns:
        DataFrame with one row per analysed review, keyed by ``review_id``.
    """
    cfg = config or get_config()
    ra = cfg["review_analysis"]

    path = _resolve_input_path(input_filename)
    df = load_reviews(path, comment_column=ra["comment_column"], max_rows=max_rows)

    if classifier is None:
        client = get_client()
        model = cfg["llm"]["model"]
        temperature = cfg["llm"].get("temperature", 0)
        themes = ra["themes"]

        def classifier(comment: str):  # noqa: E306 — local default classifier
            return classify_review(client, comment, model, themes, temperature)

    rows = []
    for _, r in df.iterrows():
        insight = classifier(r[ra["comment_column"]])
        rows.append(
            {
                ra["id_column"]: r[ra["id_column"]],          # primary key (unique per review)
                ra["order_column"]: r[ra["order_column"]],
                ra["score_column"]: r[ra["score_column"]],
                "sentiment": insight.sentiment,
                "themes": ",".join(insight.themes),
                "summary_en": insight.summary_en,
            }
        )

    return pd.DataFrame(rows)
