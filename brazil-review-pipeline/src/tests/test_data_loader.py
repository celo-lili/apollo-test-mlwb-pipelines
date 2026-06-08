import pandas as pd

from src.data_loader import load_reviews

_CSV = (
    "review_id,review_comment_message\n"
    "r1,Bom produto\n"
    "r2,\n"            # empty -> dropped
    "r3,   \n"         # whitespace -> dropped
    "r4,Chegou tarde\n"
    "r5,Otimo\n"
)


def _write(tmp_path):
    p = tmp_path / "reviews.csv"
    p.write_text(_CSV)
    return str(p)


def test_drops_empty_and_whitespace_comments(tmp_path):
    df = load_reviews(_write(tmp_path))
    assert list(df["review_id"]) == ["r1", "r4", "r5"]


def test_max_rows_cap(tmp_path):
    df = load_reviews(_write(tmp_path), max_rows=2)
    assert len(df) == 2
    assert list(df["review_id"]) == ["r1", "r4"]


def test_index_reset(tmp_path):
    df = load_reviews(_write(tmp_path))
    assert list(df.index) == [0, 1, 2]
