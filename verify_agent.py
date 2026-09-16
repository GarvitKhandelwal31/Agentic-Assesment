"""
verify_agent.py
===============
Independent second-pass verification on 20 stratified apps.
Run: python verify_agent.py
"""

import json
import os
import random
import re
import time
from pathlib import Path
from collections import defaultdict

from google import genai
from google.genai import types
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
MODEL = "gemini-3.5-flash-lite"

RESULTS_FILE = Path("data/results.json")
VERIFY_OUT = Path("data/verification_report.json")
FIELDS_TO_CHECK = ["auth_methods", "self_serve", "api_type", "buildability", "mcp_exists"]

VERIFY_PROMPT = """You are an independent API research fact-checker for Composio.

Given the primary agent's findings about an app, independently assess each field using your knowledge of the app's official documentation.

For each field, return "AGREE" if correct or "DISAGREE" with your finding.

App: {name}
Docs URL: {evidence_url}

Primary agent's findings:
- auth_methods: {auth_methods}
- self_serve: {self_serve} (notes: {self_serve_notes})
- api_type: {api_type}
- buildability: {buildability} (blocker: {main_blocker})
- mcp_exists: {mcp_exists}

Return ONLY this JSON:
{{
  "auth_methods": {{"verdict": "AGREE" or "DISAGREE", "note": "<your finding if DISAGREE>"}},
  "self_serve": {{"verdict": "AGREE" or "DISAGREE", "note": "<your finding if DISAGREE>"}},
  "api_type": {{"verdict": "AGREE" or "DISAGREE", "note": "<your finding if DISAGREE>"}},
  "buildability": {{"verdict": "AGREE" or "DISAGREE", "note": "<your finding if DISAGREE>"}},
  "mcp_exists": {{"verdict": "AGREE" or "DISAGREE", "note": "<your finding if DISAGREE>"}},
  "overall_confidence": <0.0-1.0>,
  "corrected_values": {{}}
}}"""


def stratified_sample(results, n_per_category=2):
    by_cat = defaultdict(list)
    for r in results:
        by_cat[r["category"]].append(r)
    sample = []
    for cat, items in by_cat.items():
        sample.extend(random.sample(items, min(n_per_category, len(items))))
    return sample


def verify_one(record):
    prompt = VERIFY_PROMPT.format(
        name=record["name"],
        evidence_url=record.get("evidence_url", ""),
        auth_methods=record.get("auth_methods", []),
        self_serve=record.get("self_serve", ""),
        self_serve_notes=record.get("self_serve_notes", ""),
        api_type=record.get("api_type", ""),
        buildability=record.get("buildability", ""),
        main_blocker=record.get("main_blocker", ""),
        mcp_exists=record.get("mcp_exists", False),
    )
    for attempt in range(3):
        try:
            resp = client.models.generate_content(
                model=MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.0,
                    response_mime_type="application/json",
                ),
            )
            raw = resp.text.strip()
            raw = re.sub(r"^```json\s*", "", raw)
            raw = re.sub(r"\s*```$", "", raw)
            return json.loads(raw)
        except Exception as e:
            if attempt == 2:
                return {"error": str(e)}
            time.sleep(2 ** attempt)
    return {}


def score_check(check):
    scores = {}
    for field in FIELDS_TO_CHECK:
        if field in check and isinstance(check[field], dict) and "verdict" in check[field]:
            scores[field] = check[field]["verdict"].upper() == "AGREE"
        else:
            scores[field] = None
    return scores


def main():
    random.seed(42)
    with open(RESULTS_FILE, encoding="utf-8") as f:
        results = json.load(f)

    sample = stratified_sample(results, n_per_category=2)
    print(f"Verifying {len(sample)} apps (2 per category)...")

    verification_records = []
    field_tallies = defaultdict(lambda: {"agree": 0, "disagree": 0, "unknown": 0})

    for record in tqdm(sample, desc="Verifying"):
        check = verify_one(record)
        scores = score_check(check)
        for field, agreed in scores.items():
            if agreed is True:
                field_tallies[field]["agree"] += 1
            elif agreed is False:
                field_tallies[field]["disagree"] += 1
            else:
                field_tallies[field]["unknown"] += 1

        verification_records.append({
            "id": record["id"],
            "name": record["name"],
            "category": record["category"],
            "primary_findings": {f: record.get(f) for f in FIELDS_TO_CHECK},
            "verification_check": check,
            "field_scores": {k: ("AGREE" if v else ("DISAGREE" if v is False else "UNKNOWN"))
                             for k, v in scores.items()},
        })
        time.sleep(0.3)

    total_checks = sum(t["agree"] + t["disagree"] for t in field_tallies.values())
    total_agrees = sum(t["agree"] for t in field_tallies.values())
    accuracy = total_agrees / total_checks if total_checks > 0 else 0

    report = {
        "sample_size": len(sample),
        "first_pass_accuracy": round(accuracy, 3),
        "field_accuracy": {
            field: {
                "accuracy": round(t["agree"] / max(1, t["agree"] + t["disagree"]), 3),
                **t,
            }
            for field, t in field_tallies.items()
        },
        "records": verification_records,
        "human_checks_needed": [
            r["name"] for r in verification_records
            if "DISAGREE" in r["field_scores"].values()
        ],
    }

    with open(VERIFY_OUT, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"\nFirst-pass accuracy: {accuracy:.1%}")
    print(f"Report saved to {VERIFY_OUT}")
    if report["human_checks_needed"]:
        print(f"Apps needing human review: {', '.join(report['human_checks_needed'])}")


if __name__ == "__main__":
    main()
