# CLAUDE.md — guidance for Claude Code in this repo

This file is read by every collaborator's Claude Code session. Keep it accurate.

## What this repo is

`apollo-test-mlwb-pipelines` — a **shared** repository of Python pipelines that run in the
**Celonis ML Workbench (MLWB)**, receive parameters from Action Flows, and write results
back to a Celonis data pool. It is the single source of truth that each collaborator clones
locally (each with their own Claude) and that MLWB clones to run.

## Structure: one self-contained pipeline per subfolder

```
<pipeline-name>/        # e.g. brazil-review-pipeline/
  pipeline.ipynb        # MLWB entry point — first cell tagged "parameters"
  config.yaml  src/  scripts/  requirements.txt  README.md
```

When adding a new pipeline, create a **new subfolder** — never put pipeline files at the
repo root (that's where people collide). Repo root holds only `README.md`,
`CONTRIBUTING.md`, and this file.

## Use the skill

When building or modifying any pipeline here, **use the `mlwb-python-pipeline` skill** — it
documents the MLWB git setup, notebook entry point, Action Flow params, `pycelonis_llm`
usage, and the S3 ingestion pattern. Don't reinvent these from memory.

## Conventions (apply to every pipeline)

- **LLM access is MLWB-only.** Import `pycelonis_llm` *lazily* (inside a function, never at
  module top) so local tests/tooling work without it. Use `CelonisOpenAI`; default model
  `azure-openai-gpt-4-1` (verify against the tenant's model list).
- **Local runs use a stub, not the real LLM** — see each pipeline's `scripts/dry_run.py`.
- **`config.yaml` carries settings, never secrets.** Credentials live in `.env` (gitignored);
  `.env.example` is the committed template. Don't add `@lru_cache` to `get_config()`.
- **Ingestion is gated on `config.yaml → ingestion.write_back`.** Keep it `false`; flip to
  `true` only to test the real push, and reset to `false` before merging.
- **Clear notebook outputs before committing:**
  `jupyter nbconvert --clear-output --inplace <folder>/pipeline.ipynb` (avoids leaking data).

## Collaboration workflow

See **[CONTRIBUTING.md](CONTRIBUTING.md)**. In short: `main` is production (what MLWB runs);
each person works on `dev/<name>` and merges via PR; pull `main` before starting so your
Claude works against the latest shared state. Claude sessions don't share state with each
other — the repo is how everyone "sees" each other's edits.

## Verifying a pipeline locally

From inside the pipeline's folder:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt   # pycelonis_llm is commented — MLWB-only
.venv/bin/pytest -q
.venv/bin/python -m scripts.dry_run
```
