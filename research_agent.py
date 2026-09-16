"""
research_agent.py
=================
Researches all 100 apps using Gemini (google-genai SDK) + web fetching.
Saves each result to data/raw/<id>_<slug>.json immediately (crash-safe).
Run: python research_agent.py
"""

import asyncio
import json
import os
import re
import time
from pathlib import Path

import requests
from dotenv import load_dotenv
from tqdm import tqdm
from google import genai
from google.genai import types
from pydantic import ValidationError

from schema import AppRecord

load_dotenv()

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
client = genai.Client(api_key=GEMINI_API_KEY)
MODEL = "gemini-3.5-flash-lite"   # fast, cheap, latest available

RAW_DIR = Path("data/raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)
APPS_FILE = Path("apps.json")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; ComposioResearchBot/1.0)"
}


def fetch_page(url: str, timeout: int = 10) -> str:
    """Fetch a URL, strip HTML tags, return first 6000 chars."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout)
        r.raise_for_status()
        text = re.sub(r"<[^>]+>", " ", r.text)
        text = re.sub(r"\s+", " ", text)
        return text[:6000]
    except Exception as e:
        return f"[fetch error: {e}]"


SYSTEM_PROMPT = """You are an API research analyst for Composio, which builds agent-callable toolkits from third-party apps.

Research the given app and return a JSON object matching this EXACT schema — no extra keys, no markdown:

{
  "id": <int>,
  "name": "<string>",
  "category": "<string>",
  "one_liner": "<what it does in one sentence>",
  "auth_methods": ["OAuth2" | "API Key" | "Basic Auth" | "Bearer Token" | "HMAC" | "No Auth" | "SDK Auth" | "other"],
  "self_serve": "yes" | "partial" | "gated" | "unknown",
  "self_serve_notes": "<specific plan name or gate detail, e.g. 'requires paid plan starting $X/mo' or 'free tier available'>",
  "api_type": "REST" | "GraphQL" | "REST+GraphQL" | "SDK-only" | "CLI-only" | "No-API",
  "api_breadth": "narrow" | "moderate" | "broad" | "unknown",
  "mcp_exists": true | false,
  "mcp_notes": "<MCP server URL or description, or empty string>",
  "buildability": "ready" | "needs-outreach" | "gated" | "no-api",
  "main_blocker": "<primary blocker or 'none'>",
  "evidence_url": "<the main docs URL that supports your answers>",
  "agent_confidence": <0.0 to 1.0 — your confidence in accuracy>,
  "verified": false,
  "verification_notes": ""
}

Definitions:
- self_serve=yes: dev can get free/trial API credentials without sales contact
- self_serve=partial: free app tier exists but API needs paid plan or has severe rate limits
- self_serve=gated: requires paid plan, approval, partnership, or contact-sales for API access
- self_serve=unknown: could not determine from available info
- buildability=ready: public documented API + self-serve creds = can build agent toolkit today
- buildability=needs-outreach: API exists but requires paid plan or partnership to access
- buildability=gated: no public API or requires special partnership agreement
- buildability=no-api: CLI-only tool, no HTTP API, or truly no programmatic interface

Return ONLY valid JSON. No markdown code blocks, no prose, no explanation."""


def research_one(app: dict, max_retries: int = 3) -> dict | None:
    """Research a single app with Gemini. Returns dict matching AppRecord."""
    slug = re.sub(r"[^a-z0-9]+", "_", app["name"].lower()).strip("_")
    out_path = RAW_DIR / f"{app['id']:03d}_{slug}.json"

    # Resume: skip if already done
    if out_path.exists():
        with open(out_path, encoding="utf-8") as f:
            return json.load(f)

    page_text = fetch_page(app["hint_url"])

    user_msg = f"""App to research: {app["name"]}
Category: {app["category"]}
Primary docs URL: {app["hint_url"]}

Page content (first 6000 chars of the docs page):
{page_text}

Now fill the JSON schema for this app. Base your answers on the page content above and your knowledge.
Pay special attention to: (1) exact auth method from docs, (2) whether a free trial/dev account gives API access, (3) whether an MCP server is officially listed.
"""

    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=MODEL,
                contents=user_msg,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    temperature=0.1,
                    response_mime_type="application/json",
                ),
            )
            raw = response.text.strip()
            raw = re.sub(r"^```json\s*", "", raw)
            raw = re.sub(r"\s*```$", "", raw)
            data = json.loads(raw)
            # Enforce master-list values
            data["id"] = app["id"]
            data["name"] = app["name"]
            data["category"] = app["category"]
            record = AppRecord(**data)
            result = record.model_dump()
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2)
            return result
        except (json.JSONDecodeError, ValidationError) as e:
            if attempt == max_retries - 1:
                print(f"\n  !! PARSE FAIL: {app['name']}: {e}")
                break
            time.sleep(2 ** attempt)
        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "quota" in err_str.lower():
                wait = 30 * (attempt + 1)
                print(f"\n  Rate limit on {app['name']}, waiting {wait}s...")
                time.sleep(wait)
            elif attempt == max_retries - 1:
                print(f"\n  !! ERROR: {app['name']}: {e}")
                break
            else:
                time.sleep(2 ** attempt)

    # Fallback record
    fallback = {
        "id": app["id"], "name": app["name"], "category": app["category"],
        "one_liner": "Research failed — manual check needed",
        "auth_methods": ["unknown"], "self_serve": "unknown",
        "self_serve_notes": "Research failed", "api_type": "unknown",
        "api_breadth": "unknown", "mcp_exists": False, "mcp_notes": "",
        "buildability": "gated", "main_blocker": "Research agent failed",
        "evidence_url": app["hint_url"], "agent_confidence": 0.0,
        "verified": False, "verification_notes": "RESEARCH FAILED"
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(fallback, f, indent=2)
    return fallback


async def research_batch(apps: list[dict], concurrency: int = 5) -> list[dict]:
    semaphore = asyncio.Semaphore(concurrency)
    results = []
    pbar = tqdm(total=len(apps), desc="Researching apps")

    async def bounded(app):
        async with semaphore:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, research_one, app)
            pbar.update(1)
            return result

    tasks = [bounded(app) for app in apps]
    for coro in asyncio.as_completed(tasks):
        result = await coro
        if result:
            results.append(result)

    pbar.close()
    return results


def main():
    with open(APPS_FILE, encoding="utf-8") as f:
        apps = json.load(f)

    already_done = len(list(RAW_DIR.glob("*.json")))
    print(f"Starting research for {len(apps)} apps (already done: {already_done})...")

    asyncio.run(research_batch(apps, concurrency=5))

    # Merge all raw results
    all_results = []
    for p in sorted(RAW_DIR.glob("*.json")):
        with open(p, encoding="utf-8") as f:
            all_results.append(json.load(f))
    all_results.sort(key=lambda x: x["id"])

    Path("data").mkdir(exist_ok=True)
    with open("data/results.json", "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2)

    print(f"\nDone! {len(all_results)} records -> data/results.json")


if __name__ == "__main__":
    main()
