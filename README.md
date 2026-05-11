# ToolPulse

**Agent tool reliability monitoring.** One-line decorator wraps any AI agent tool — MCP, function, API. Records latency, success/failure, and response shape; detects schema drift before your agent acts on bad data; runs synthetic health checks; alerts on Discord/Slack/email/webhook.

[![PyPI](https://img.shields.io/pypi/v/toolpulse.svg)](https://pypi.org/project/toolpulse/)
[![npm](https://img.shields.io/npm/v/toolpulse.svg)](https://www.npmjs.com/package/toolpulse)
[![Tests](https://img.shields.io/github/actions/workflow/status/toolpulse/toolpulse/test.yml?branch=main)](https://github.com/toolpulse/toolpulse/actions)
[![License: MIT](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)

## Repository layout

```
toolpulse/
├── sdk-python/          # @monitor decorator → published to PyPI as `toolpulse`
├── sdk-typescript/      # monitor() wrapper → published to npm as `toolpulse`
├── api/                 # FastAPI backend → deployed to Railway
├── frontend/            # Next.js marketing + dashboard + status → deployed to Vercel
├── content-engine/      # Weekly autonomous blog post generator
├── github-action/       # Distributable Action for CI synthetic checks
├── infra/               # Railway / Procfile / deployment config
└── .github/workflows/   # CI: test, publish, weekly content engine
```

## Quickstart (as a developer)

```bash
pip install toolpulse        # or:  npm install toolpulse
export TOOLPULSE_API_KEY=tp_live_...
```

```python
from toolpulse import monitor

@monitor(tool_name="search_web", agent_id="my-agent")
async def search_web(query: str) -> dict: ...
```

100K calls/month free at [toolpulse.io](https://toolpulse.io). See `sdk-python/README.md` and `sdk-typescript/README.md` for the full SDK docs.

---

## Deployment — full autonomous stack

This section is for whoever is deploying ToolPulse from a fresh clone. Once these steps are done, the system runs entirely without human involvement.

### One-time provisioning (~30 minutes total)

| # | Step | Why |
|---|------|-----|
| 1 | Create a GitHub repo and push this code | Source of truth |
| 2 | Provision Railway: PostgreSQL + Redis + a service from this repo | API + datastore |
| 3 | (Optional but recommended) Add the TimescaleDB extension to the Postgres add-on | Faster time-series queries on `tool_calls` |
| 4 | Provision Vercel project pointed at `frontend/` with the env vars from `.env.example` | Marketing + dashboard + status page + free tool |
| 5 | Set up Clerk: create application, configure OAuth providers, copy the publishable + secret keys | Self-serve user auth (no manual onboarding) |
| 6 | Set up Stripe: create the Indie/Pro/Team products + prices, copy the price IDs, configure webhook → `https://api.toolpulse.io/billing/webhook` | Self-serve billing |
| 7 | Create SendGrid sender + API key for `alerts@toolpulse.io` | Email alert channel |
| 8 | Create a Discord webhook (your team's #toolpulse channel) | Bootstrap fallback alerts |
| 9 | Create a PyPI trusted-publishing config for the `sdk-python` workflow | Autonomous PyPI releases |
| 10 | Create an npm token (`NPM_TOKEN` in repo secrets) | Autonomous npm releases |
| 11 | Create a GitHub PAT with `contents:write` (`CONTENT_ENGINE_PAT`) | Lets the weekly content engine commit posts |
| 12 | Add `ANTHROPIC_API_KEY` to repo secrets | Drafting source for the content engine |

After step 12 the system is fully autonomous. New users sign up via Clerk → are auto-issued an API key → can install the SDK and pay via Stripe Checkout entirely without your involvement.

### Triggering the first SDK release

```bash
git tag py-v0.1.0 && git push --tags    # publishes to PyPI
git tag ts-v0.1.0 && git push --tags    # publishes to npm
```

### Weekly content runs

The content engine runs every Monday at 13:00 UTC via `.github/workflows/content-engine.yml` and produces three new MDX posts (one comparison, one technical deep-dive, one real-failure case study). Posts auto-deploy to Vercel via the existing main-branch hook.

A second equivalent trigger lives in your Cowork scheduled tasks — useful as a backup or for ad-hoc runs.

---

## Marketing + SEO architecture

The frontend ships every page the autonomous-only GTM strategy depends on:

- **Public status page** at `/status` — live latency/uptime across popular LLM tools, fed by `/public/status/summary`. This is the live demo + social proof + permanent SEO content.
- **Free MCP health-checker** at `/tools/health-check` — no signup, ranks for the obvious search queries, top-of-funnel.
- **Programmatic comparison pages** at `/compare/[competitor]` — captures high-intent search like "ToolPulse vs Langfuse".
- **Blog at `/blog`** — auto-populated weekly by the content engine. Each post has a `.md` mirror and is referenced from `/llms.txt`.
- **Discoverability for AI crawlers**: `/robots.txt` explicitly allows GPTBot/ClaudeBot/PerplexityBot/Google-Extended. `/llms.txt` and `/llms-full.txt` are served at the standard paths.
- **GitHub Action** at `github-action/` — distributable via the GitHub Marketplace; every CI run that uses it is brand exposure.

---

## Developing locally

```bash
# Backend
cd api
pip install -r requirements.txt
cp ../.env.example .env  # edit
alembic upgrade head
uvicorn main:app --reload

# Frontend
cd frontend
npm install
npm run dev

# SDK tests
cd sdk-python && pytest
cd sdk-typescript && npx vitest run
```

## License

MIT. See [LICENSE](LICENSE).
