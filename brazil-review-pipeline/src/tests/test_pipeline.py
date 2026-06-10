"""Pipeline assembly test — uses a stub classifier so no LLM is needed."""
import os

from src.pipeline import run
from src.schema import ReviewInsight

_CFG = {
    "llm": {"model": "stub", "temperature": 0},
    "review_analysis": {
        "id_column": "review_id",
        "order_column": "order_id",
        "score_column": "review_score",
        "comment_column": "review_comment_message",
        "themes": ["delivery", "product_quality", "price", "other"],
        "urgency_levels": ["low", "medium", "high"],
        "recommend_values": ["yes", "no", "unclear"],
    },
    "ingestion": {"write_back": False, "table_name": "review_insights"},
}

_CSV = (
    "review_id,order_id,review_score,review_comment_message\n"
    "r1,o1,5,Muito bom\n"
    "r2,o2,1,\n"               # dropped (empty comment)
    "r3,o3,2,Chegou quebrado\n"
)


def _stub_classifier(comment: str) -> ReviewInsight:
    # Deterministic: a negative case sets the enriched fields so the assembly is exercised.
    if "quebrado" in comment:
        return ReviewInsight(
            sentiment="negative",
            themes=["product_quality"],
            summary_en="stub",
            urgency="high",
            would_recommend="no",
            refund_or_return_request=True,
            actionable=True,
        )
    return ReviewInsight(sentiment="positive", themes=["other"], summary_en="stub")


def test_run_assembles_expected_table(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    os.makedirs("input-data")
    (tmp_path / "input-data" / "reviews.csv").write_text(_CSV)

    df = run(
        input_filename="reviews.csv",
        classifier=_stub_classifier,
        config=_CFG,
    )

    # Empty-comment row dropped -> 2 rows.
    assert list(df["review_id"]) == ["r1", "r3"]
    assert set(df.columns) == {
        "review_id", "order_id", "review_score",
        "sentiment", "themes", "summary_en",
        "urgency", "would_recommend", "refund_or_return_request", "actionable",
    }
    assert df.loc[df["review_id"] == "r3", "sentiment"].iloc[0] == "negative"
    assert df.loc[df["review_id"] == "r1", "themes"].iloc[0] == "other"
    # Enriched fields flow through assembly (pandas stores bools as numpy.bool_, so test
    # truthiness rather than identity).
    r3 = df.loc[df["review_id"] == "r3"].iloc[0]
    assert r3["urgency"] == "high"
    assert bool(r3["refund_or_return_request"]) is True
    assert bool(r3["actionable"]) is True
    r1 = df.loc[df["review_id"] == "r1"].iloc[0]
    assert r1["urgency"] == "medium"           # default for the positive stub
    assert bool(r1["refund_or_return_request"]) is False
