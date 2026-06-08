"""Push the insight table to the Celonis data pool via the S3 ingestion API.

Gated on ``ingestion.write_back``:
  - false (default): write a local parquet to ``output/`` and skip S3 — safe for dev.
  - true:  push the parquet to the Celonis continuous-ingestion endpoint.
"""
from __future__ import annotations

import os
import tempfile
from typing import Optional

import pandas as pd

from .config import get_config

# Fixed bucket name for the Celonis continuous-ingestion endpoint — do not change.
_BUCKET = "continuous"
_OUTPUT_DIR = "output"


def _write_local(df: pd.DataFrame, table_name: str) -> str:
    os.makedirs(_OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(_OUTPUT_DIR, f"{table_name}.parquet")
    df.to_parquet(out_path, engine="pyarrow", index=False)
    return out_path


def _push_s3(df: pd.DataFrame, table_name: str, connection_id: str) -> str:
    """Upload one parquet file for the table to the Celonis ingestion endpoint."""
    import boto3

    endpoint_url = f"https://{os.environ['CELONIS_URL']}/api/data-ingestion"
    s3 = boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=os.environ["aws_access_key_id"],
        aws_secret_access_key=os.environ["aws_secret_access_key"],
    )

    tmp_path = os.path.join(tempfile.gettempdir(), f"{table_name}.parquet")
    try:
        df.to_parquet(tmp_path, engine="pyarrow", index=False)
        object_name = f"connection/{connection_id}/{table_name}/{table_name}.parquet"
        with open(tmp_path, "rb") as f:
            s3.put_object(Bucket=_BUCKET, Key=object_name, Body=f)
        return object_name
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def push_to_celonis(df: pd.DataFrame, config: Optional[dict] = None) -> str:
    """Persist the insight table.

    Returns a human-readable destination string (local path or S3 object key).
    """
    cfg = config or get_config()
    ing = cfg["ingestion"]
    table_name = ing["table_name"]

    if not ing.get("write_back", False):
        out_path = _write_local(df, table_name)
        print(f"[ingestion] write_back=false — wrote {len(df)} rows to {out_path} (S3 skipped)")
        return out_path

    object_name = _push_s3(df, table_name, ing["s3_connection_id"])
    print(f"[ingestion] write_back=true — pushed {len(df)} rows to s3://{_BUCKET}/{object_name}")
    return object_name
