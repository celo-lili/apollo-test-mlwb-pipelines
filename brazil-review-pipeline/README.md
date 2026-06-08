# Brazil Review-Analysis Pipeline (Celonis MLWB)

An LLM pipeline for the Celonis ML Workbench that analyses **Olist** order-review comments
(Portuguese free text) and writes structured insights back to a Celonis data pool.

For each review with a non-empty comment it extracts:

| Field        | Meaning                                                        |
|--------------|----------------------------------------------------------------|
| `sentiment`  | `positive` / `neutral` / `negative` (from the text, not stars) |
| `themes`     | tags from a closed set: delivery, product_quality, price, customer_service, packaging, other |
| `summary_en` | one-sentence English summary of the comment                    |

Output table: **`review_insights`**, keyed by `review_id`.

> Built following the `mlwb-python-pipeline` skill. New to the repo? Read the
> repo-level **[../CONTRIBUTING.md](../CONTRIBUTING.md)** — it explains how the team
> collaborates with Claude.

## Project layout

```
pipeline.ipynb     # MLWB entry point — first cell tagged "parameters"
config.yaml        # model, columns, theme list, ingestion flags (no secrets)
src/               # pipeline logic
  config.py        # get_config() — reloads each call (no caching)
  schema.py        # ReviewInsight pydantic model
  data_loader.py   # load reviews CSV, drop empty comments
  llm_client.py    # CelonisOpenAI client + classify_review (+ JSON parsing)
  pipeline.py      # run() — orchestration
  ingestion.py     # push_to_celonis() — gated on write_back
  tests/           # deterministic unit tests (no LLM calls)
test-data/         # local synthetic sample (gitignored)
input-data/        # runtime files from the Action Flow (gitignored)
output/            # local dry-run output (gitignored)
```

## Run locally (no LLM, no Celonis)

LLM calls (`pycelonis_llm`) and the S3 push only work inside MLWB, so local runs use a
stub classifier and write parquet to `output/`. Run these **from this folder**:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt    # pycelonis_llm is commented out — MLWB-only
.venv/bin/pytest -q                           # deterministic unit tests
.venv/bin/python -m scripts.dry_run           # stub run -> output/review_insights.parquet
```

## Run in MLWB

1. Clone the repo into the workbench (see [../CONTRIBUTING.md](../CONTRIBUTING.md) → MLWB setup).
2. `%pip install -r requirements.txt` (in a notebook cell).
3. Create a `.env` with `aws_access_key_id` / `aws_secret_access_key` (see `.env.example`).
   `CELONIS_URL` is pre-set in MLWB.
4. Open `pipeline.ipynb`. The first cell is tagged `parameters`; the Action Flow overrides
   `input_filename` and `max_rows` at runtime.
5. Point the Action Flow's `executionFileName` at `brazil-review-pipeline/pipeline.ipynb`.

### Writing back to Celonis

`config.yaml → ingestion.write_back` gates the push:

- `false` (default): writes `output/review_insights.parquet` locally, **skips S3**. Use
  this during development.
- `true`: pushes the parquet to the Celonis data pool. Flip to `true` **only** to test the
  real push, then reset to `false` before merging to `main`.

Set `ingestion.s3_connection_id` to the UUID from the Celonis Data Ingestion app, which
must define the `review_insights` table with `review_id` as its primary key.
