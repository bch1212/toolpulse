# Content engine

Autonomous weekly content generator. Produces three MDX posts per run and commits them to the frontend repo.

## What it produces each week

1. **Comparison** — ToolPulse vs a rotating competitor (Langfuse, Helicone, Arize Phoenix, AgentOps, Langtrace).
2. **Technical deep-dive** — rotating engineering topic from a curated pool.
3. **Real-failure case study** — synthesized from real drift events and latency anomalies in the ToolPulse production DB.

Posts are tagged with `generatedBy: "content-engine v1"` in frontmatter so they're identifiable. Slugs include the ISO week, so re-running the engine in the same week is a safe no-op (the GitHub commit step is idempotent — it skips if the file already exists).

## How it runs

Two equivalent ways:

**Option A — Cowork scheduled task (default).** A Monday-morning task wakes up Claude, runs the equivalent of `python generate.py`, and reports the URLs of the new posts in your activity log.

**Option B — GitHub Action on a cron.** `.github/workflows/content-engine.yml` runs the script weekly on GitHub-hosted runners.

## Required env vars

| Variable | Purpose |
|---|---|
| `ANTHROPIC_API_KEY` | Drafting via Claude. If unset, posts contain stub content. |
| `DATABASE_URL` | Read-only Postgres URL to pull real drift / latency data for case studies. |
| `GITHUB_TOKEN` | PAT or fine-grained token with `contents:write` on the frontend repo. |
| `GITHUB_REPO` | e.g. `toolpulse/toolpulse` |
| `GITHUB_BRANCH` | Default `main`. |

## Running locally

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=...
export DATABASE_URL=postgresql://... # read-only role recommended
export GITHUB_TOKEN=...
python generate.py
```

The script logs every action and exits non-zero on failure.

## SEO + agentic-AI discoverability

Each generated post includes:

- frontmatter that drives `sitemap.xml` and `feed.xml`
- structured-data fields surfaced as JSON-LD on the rendered page
- a markdown mirror at `/blog/<slug>.md` (linked from `/llms.txt` and `/llms-full.txt`)

In other words: every post becomes both a Google-indexable page and an LLM-fetchable raw document the moment it's committed.
