"""Load the Olist reviews CSV and keep only rows with a usable comment."""
from __future__ import annotations

import pandas as pd


def load_reviews(
    path: str,
    comment_column: str = "review_comment_message",
    max_rows: int | None = None,
) -> pd.DataFrame:
    """Read a reviews CSV and drop rows with no (or whitespace-only) comment.

    Args:
        path: CSV file path.
        comment_column: name of the free-text comment column to analyse.
        max_rows: optional cap on the number of rows returned (after filtering) —
            handy for cheap test runs.

    Returns:
        A DataFrame with a non-empty ``comment_column``, index reset.
    """
    df = pd.read_csv(path, dtype=str)
    comments = df[comment_column].fillna("").str.strip()
    df = df[comments != ""].copy()
    if max_rows is not None:
        df = df.head(max_rows)
    return df.reset_index(drop=True)
