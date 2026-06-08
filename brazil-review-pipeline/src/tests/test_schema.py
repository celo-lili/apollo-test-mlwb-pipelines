import pytest
from pydantic import ValidationError

from src.schema import ReviewInsight


def test_valid_insight():
    ins = ReviewInsight(sentiment="negative", themes=["delivery"], summary_en="Late delivery.")
    assert ins.sentiment == "negative"
    assert ins.themes == ["delivery"]


def test_invalid_sentiment_rejected():
    with pytest.raises(ValidationError):
        ReviewInsight(sentiment="furious", themes=["delivery"], summary_en="x")


def test_themes_normalised_dedup_and_lowercase():
    ins = ReviewInsight(
        sentiment="positive",
        themes=["Delivery", " delivery ", "PRICE", ""],
        summary_en="ok",
    )
    assert ins.themes == ["delivery", "price"]


def test_empty_themes_default_to_other():
    ins = ReviewInsight(sentiment="neutral", themes=["", "  "], summary_en="ok")
    assert ins.themes == ["other"]
