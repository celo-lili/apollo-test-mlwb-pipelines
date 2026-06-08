# Contributing — collaborating on this repo with Claude

This repo is the **single source of truth** for our Celonis MLWB pipelines. Several people
work on it, each using their own Claude Code, plus the shared MLWB environment. Nobody's
Claude can see anyone else's session directly — **you share work through this git repo**.
The rules below keep that smooth.

## Repo structure: one subfolder per pipeline

```
apollo-test-mlwb-pipelines/
├── README.md              # repo overview
├── CONTRIBUTING.md        # this file — the shared workflow
└── <pipeline-name>/       # one self-contained pipeline per folder
    ├── pipeline.ipynb     # that pipeline's MLWB entry point
    ├── config.yaml  src/  scripts/  requirements.txt  ...
```

Each pipeline lives in **its own folder** so people don't collide on `pipeline.ipynb`,
`config.yaml`, or `src/`. Current pipelines: `brazil-review-pipeline/`.

## The model

```
        ┌─────────────┐      ┌─────────────┐      ┌─────────────┐
        │  Colleague  │      │  Colleague  │      │     You     │
        │   + Claude  │      │   + Claude  │      │   + Claude  │
        └──────┬──────┘      └──────┬──────┘      └──────┬──────┘
           dev/ana             dev/bob              dev/lili
               └────────────────────┼────────────────────┘
                          Pull Requests into
                        ┌────────────────────┐
                        │   main  (GitHub)    │ ◄── single source of truth
                        └──────────┬──────────┘
                                   │ clone + pull
                            ┌──────▼──────┐
                            │    MLWB     │  runs main in production
                            └─────────────┘
```

- You **see each other's edits** by pulling `main` (after PRs merge) and reviewing open PRs.
- You **do not** edit on the same branch simultaneously — each person owns a `dev/<name>` branch.

## Branch convention

- `main` — stable; what MLWB runs in production. Never commit directly; merge via PR.
- `dev/<name>` — your personal working branch (e.g. `dev/lili`, `dev/ana`).

## Daily workflow (each colleague, on their own machine)

```bash
# one-time
git clone https://github.com/celo-lili/apollo-test-mlwb-pipelines.git
cd apollo-test-mlwb-pipelines
git checkout -b dev/<name>

# each session
git checkout dev/<name>
git pull origin main          # pick up everyone's merged work BEFORE you start
# ... work with Claude Code in the relevant pipeline folder ...
git add -A
git commit -m "feat: short description (<Name>)"
git push -u origin dev/<name>
# then open a PR: dev/<name> -> main  (gh pr create --base main --fill)
```

Tips that prevent collisions:
- **Pull `main` before you start** so your Claude works against the latest shared state.
- Keep PRs small and frequent — easier to review, fewer merge conflicts.
- Put your name in commit messages so authorship is clear even when MLWB commits as `MLWB`.
- Prefer working in your **own pipeline folder**; coordinate before touching someone else's.

## MLWB setup (shared workbench)

MLWB has no browser credential helper and commits under one shared identity:

```bash
git config --global user.name "MLWB"
git config --global credential.helper store
git clone https://<github-user>:<PAT>@github.com/celo-lili/apollo-test-mlwb-pipelines.git
```

- Use a **fine-grained PAT** scoped to this repo with **Contents: Read and write**; short
  expiry; rotate when collaborators change. The token is stored in plaintext
  (`~/.git-credentials`) — treat it as low-trust.
- MLWB normally runs `main`. To test a branch in MLWB: `git fetch && git checkout dev/<name>`.
- The Action Flow's `executionFileName` points at the pipeline inside its folder, e.g.
  `brazil-review-pipeline/pipeline.ipynb`.

## Notebook hygiene (REQUIRED before committing)

Executed notebooks embed their outputs — which can leak data. Always clear outputs first:

```bash
jupyter nbconvert --clear-output --inplace <pipeline-folder>/pipeline.ipynb
```

or in the UI: Kernel → Restart & Clear Output, then save.

## Before you open a PR

- The pipeline's tests pass (`.venv/bin/pytest -q` inside the pipeline folder).
- `config.yaml → ingestion.write_back` is back to `false`.
- No secrets committed (`.env` is gitignored; only `.env.example` is tracked).
- Notebook outputs cleared.
