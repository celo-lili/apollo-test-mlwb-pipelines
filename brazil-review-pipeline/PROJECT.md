# PROJECT — Brazil review pipeline: enrichment + first Celonis draft

This is the **plan, status, and operating instructions** for the current iteration. For what
the pipeline *is* and how to run it, see [README.md](README.md); for repo-wide Claude
conventions see [../CLAUDE.md](../CLAUDE.md); for the collaboration workflow see
[../CONTRIBUTING.md](../CONTRIBUTING.md).

## Goal of this iteration

1. **Enrich the extracted schema** (done — see below).
2. **Push a first real draft of `review_insights` into a Celonis data pool** via a manual
   MLWB notebook run.
3. **Prove the low-code, multi-Claude collaboration loop**: several people edit the same
   shared repo, each with their own Claude Code; MLWB runs `main`.

> **Why MLWB for the real run:** the LLM step (`pycelonis_llm`) and the S3 push only work
> inside MLWB. Locally we run a deterministic **stub** classifier and write parquet to
> `output/`. Real insights are produced when the notebook runs in MLWB.

## Output schema (`review_insights` table)

Keyed by `review_id`. The Data Ingestion app must define exactly these columns:

| Column | Type | Source |
|--------|------|--------|
| `review_id` | string (**primary key**) | input |
| `order_id` | string | input |
| `review_score` | string/int | input |
| `sentiment` | string (`positive`/`neutral`/`negative`) | LLM |
| `themes` | string (comma-joined tags) | LLM |
| `summary_en` | string | LLM |
| `urgency` | string (`low`/`medium`/`high`) | LLM — **new** |
| `would_recommend` | string (`yes`/`no`/`unclear`) | LLM — **new** |
| `refund_or_return_request` | bool | LLM — **new** |
| `actionable` | bool | LLM — **new** |

## Low-code editing guide (for collaborators)

You can change the pipeline's behaviour **without touching Python** — edit `config.yaml`:

- **Add/remove a theme** → `review_analysis.themes`. The prompt is generated from this list.
- **Change urgency levels / recommend values** → `review_analysis.urgency_levels` /
  `recommend_values`. (Quote `"yes"`/`"no"` — unquoted they become YAML booleans.)
- **Switch model** → `llm.model` (verify it exists on your tenant — see below).
- **Toggle the real push** → `ingestion.write_back` (keep `false`; flip to `true` only to
  test the push, then reset before merging).

The closed sets are enforced through the **prompt**; the schema normalises and falls back to
safe defaults, so editing these lists never requires a code change. Deeper changes (a brand
new field) do need edits to `src/schema.py`, `src/llm_client.py`, and `src/pipeline.py` —
use the `mlwb-python-pipeline` skill when doing so.

## Status

- [x] Schema enriched (4 new fields + 2 new themes), config-driven
- [x] Stub/tests/sample data updated — `pytest` green (19 passing), dry-run writes enriched parquet
- [ ] `dev/lili` pushed → PR → merged to `main`
- [ ] Celonis Data Ingestion connection created (UUID into `config.yaml`)
- [ ] First real draft run in MLWB → rows in the pool
- [ ] Collaboration test: a colleague edits via their own Claude → PR → merge

## What you prepare in Celonis (checklist)

1. **Target data pool** — pick or create the pool that will hold `review_insights`.
2. **Data Ingestion connection** — in that pool, create a Data Ingestion ("push"/continuous)
   connection. Note the **connection UUID**.
3. **Define the `review_insights` table** on that connection with the columns/types in the
   table above; set `review_id` as the **primary key**.
4. **Connection UUID** → `config.yaml → ingestion.s3_connection_id`.
5. **Ingestion (AWS) keys** for the connection → MLWB `.env`
   (`aws_access_key_id` / `aws_secret_access_key`). Never commit these.
6. **LLM access** — ensure the workbench has LLM access enabled and `azure-openai-gpt-4-1`
   is in the model list (verify in MLWB):
   ```python
   from pycelonis import get_celonis
   from pycelonis_llm.llm import LLM
   print([m.id for m in LLM(get_celonis().client).get_models()])
   ```

## Running the first real draft in MLWB

1. Set up the workbench clone (one-time): `git config --global user.name "MLWB"`,
   `git config --global credential.helper store`, clone with a fine-grained PAT.
2. In a notebook cell: `%pip install -r requirements.txt`.
3. Create `.env` from `.env.example` with the AWS keys (`CELONIS_URL` is pre-set in MLWB).
4. Open `pipeline.ipynb`, run all cells (manual run — no Action Flow needed yet). Inspect the
   assembled `review_insights` DataFrame.
5. Set `config.yaml → ingestion.write_back: true`, re-run the push cell, confirm rows land in
   the pool, then **reset `write_back` to `false`** before committing.

## Collaboration test (multi-Claude)

1. Push and merge this work so `main` is the shared source of truth.
2. A colleague: `git clone` the repo → `git checkout -b dev/<name>` → open the folder in their
   own Claude Code (the `mlwb-python-pipeline` skill guides them) → make a small low-code edit
   (e.g. add a theme in `config.yaml`) → commit → push → open a PR into `main`.
3. You review the PR / pull `main` after merge — that's how everyone "sees" each other's work.
4. MLWB picks up the change by pulling `main`.
