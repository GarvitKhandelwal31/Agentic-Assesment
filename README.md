# Composio App Research Agent

> AI Product Ops Intern take-home assignment — researches 100 apps for agent buildability.

## What this does

A Gemini 2.0 Flash-powered research pipeline that:
1. Fetches each app docs page
2. Extracts: auth method, self-serve status, API surface, MCP existence, buildability
3. Runs a second verification pass on 20 stratified samples
4. Computes patterns (auth dominance, category heatmaps, easy wins)
5. Renders a single self-contained `index.html` report

## Quick start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Add your API keys to .env (already set if you received the repo)
# GEMINI_API_KEY=...
# COMPOSIO_API_KEY=...

# 3. Run the full pipeline
python research_agent.py   # ~10-15 min for 100 apps
python verify_agent.py     # ~3 min for 20-app verification
python analyse.py          # instant
python render.py           # instant ? index.html

# 4. Open index.html in your browser
```

## Files

| File | Purpose |
|------|---------|
| `apps.json` | Master list of 100 apps |
| `schema.py` | Pydantic AppRecord model |
| `research_agent.py` | Main research agent (Gemini + web fetch) |
| `verify_agent.py` | Independent verification pass |
| `analyse.py` | Pattern analysis |
| `render.py` | HTML report renderer |
| `data/raw/` | Per-app JSON results (crash-safe) |
| `data/results.json` | Merged results |
| `data/analysis.json` | Pattern analysis output |
| `data/verification_report.json` | Verification report |
| `index.html` | Final deliverable |

## Agent architecture

```
apps.json ? research_agent.py (Gemini 2.0 Flash, 5 concurrent workers)
                ? per-app: fetch hint URL + structured LLM call
            data/raw/*.json (crash-safe)
                ?
            verify_agent.py (independent second-pass, 20 apps)
                ?
            analyse.py (patterns, clusters, headline findings)
                ?
            render.py ? index.html
```

## Where a human was needed

- Verified 10 of 20 sampled apps manually against real docs
- Confirmed gating for DealCloud, PitchBook, Fanbasis (thin/no public docs)
- Final HTML visual QA pass

## Built with

- **Gemini 2.0 Flash** via `google-generativeai`
- **Composio SDK** (`composio` package) for tool integration
- **Pydantic v2** for structured output validation
- **Jinja2** for HTML rendering
