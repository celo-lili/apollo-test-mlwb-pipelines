# apollo-test-mlwb-pipelines

Shared repository for **Celonis ML Workbench (MLWB)** Python pipelines. This is the single
source of truth that each collaborator clones locally (with their own Claude Code) and that
the MLWB environment clones to run in production.

## How it's organised

One **self-contained pipeline per subfolder**:

| Pipeline | What it does |
|----------|--------------|
| [`brazil-review-pipeline/`](brazil-review-pipeline/) | LLM analysis of Olist order reviews — sentiment, theme tags, English summary → `review_insights` table |

Each folder has its own `pipeline.ipynb` (MLWB entry point), `config.yaml`, `src/`, tests,
and README.

## Working here

Read **[CONTRIBUTING.md](CONTRIBUTING.md)** first — it explains the branch model
(`main` + `dev/<name>`), the per-collaborator Claude workflow, MLWB git setup, and notebook
hygiene. In short:

```bash
git clone https://github.com/celo-lili/apollo-test-mlwb-pipelines.git
cd apollo-test-mlwb-pipelines
git checkout -b dev/<name>
# work in a pipeline folder, then push and open a PR into main
```

To run or develop a specific pipeline, see that folder's own README.
