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


def test_enriched_fields_default_when_omitted():
    # urgency/would_recommend/refund/actionable are optional with safe defaults.
    ins = ReviewInsight(sentiment="positive", themes=["price"], summary_en="ok")
    assert ins.urgency == "medium"
    assert ins.would_recommend == "unclear"
    assert ins.refund_or_return_request is False
    assert ins.actionable is False


def test_label_fields_normalised_and_blank_falls_back():
    ins = ReviewInsight(
        sentiment="negative",
        themes=["delivery"],
        summary_en="ok",
        urgency=" HIGH ",
        would_recommend="",          # blank -> default
    )
    assert ins.urgency == "high"
    assert ins.would_recommend == "unclear"


def test_bool_fields_coerced_from_json_like_values():
    ins = ReviewInsight(
        sentiment="negative",
        themes=["product_quality"],
        summary_en="ok",
        refund_or_return_request=True,
        actionable="true",          # pydantic coerces common truthy strings
    )
    assert ins.refund_or_return_request is True
    assert ins.actionable is True
