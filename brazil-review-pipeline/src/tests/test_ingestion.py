"""Ingestion gate tests — verify write_back routing without touching real S3."""
import os

import pandas as pd

from src import ingestion
from src.ingestion import push_to_celonis

_DF = pd.DataFrame(
    {"review_id": ["r1", "r2"], "sentiment": ["positive", "negative"]}
)


def test_write_back_false_writes_local_parquet(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    cfg = {"ingestion": {"write_back": False, "table_name": "review_insights"}}

    dest = push_to_celonis(_DF, config=cfg)

    assert dest == os.path.join("output", "review_insights.parquet")
    assert os.path.exists(dest)
    # Round-trips correctly.
    back = pd.read_parquet(dest)
    assert list(back["review_id"]) == ["r1", "r2"]


def test_write_back_false_never_calls_s3(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    def _boom(*a, **k):  # pragma: no cover - must not be called
        raise AssertionError("_push_s3 must not run when write_back is false")

    monkeypatch.setattr(ingestion, "_push_s3", _boom)
    cfg = {"ingestion": {"write_back": False, "table_name": "review_insights"}}
    push_to_celonis(_DF, config=cfg)  # should not raise


def test_write_back_true_routes_to_s3(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    calls = {}

    def _fake_push(df, table_name, connection_id):
        calls["table"] = table_name
        calls["conn"] = connection_id
        return f"connection/{connection_id}/{table_name}/{table_name}.parquet"

    monkeypatch.setattr(ingestion, "_push_s3", _fake_push)
    cfg = {
        "ingestion": {
            "write_back": True,
            "table_name": "review_insights",
            "s3_connection_id": "abc-123",
        }
    }

    dest = push_to_celonis(_DF, config=cfg)

    assert calls == {"table": "review_insights", "conn": "abc-123"}
    assert dest == "connection/abc-123/review_insights/review_insights.parquet"
