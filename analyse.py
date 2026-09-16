"""
analyse.py
==========
Reads data/results.json and data/verification_report.json,
computes patterns, and writes data/analysis.json for the HTML renderer.

Run: python analyse.py
"""

import json
from collections import Counter, defaultdict
from pathlib import Path

RESULTS = Path("data/results.json")
VERIFY = Path("data/verification_report.json")
OUT = Path("data/analysis.json")


def flatten_auth(records):
    """Flatten auth_methods list across all records."""
    auth_list = []
    for r in records:
        auth_list.extend(r.get("auth_methods", []))
    return auth_list


def main():
    with open(RESULTS, encoding="utf-8") as f:
        records = json.load(f)

    # ── Auth dominance ─────────────────────────────────────────────
    auth_flat = flatten_auth(records)
    auth_counter = Counter(auth_flat)

    # ── Self-serve by category ─────────────────────────────────────
    cat_self_serve = defaultdict(lambda: Counter())
    for r in records:
        cat_self_serve[r["category"]][r["self_serve"]] += 1

    # ── Buildability distribution ──────────────────────────────────
    buildability_counter = Counter(r["buildability"] for r in records)

    # ── MCP coverage ──────────────────────────────────────────────
    mcp_count = sum(1 for r in records if r.get("mcp_exists"))

    # ── Easy wins (ready + self-serve yes) ────────────────────────
    easy_wins = [r for r in records if r["buildability"] == "ready" and r["self_serve"] == "yes"]

    # ── Needs outreach ─────────────────────────────────────────────
    needs_outreach = [r for r in records if r["buildability"] in ("needs-outreach", "gated")]

    # ── Common blockers ────────────────────────────────────────────
    blockers = [r["main_blocker"] for r in records if r.get("main_blocker") and r["main_blocker"] != "none"]
    blocker_counter = Counter(blockers)

    # ── API type distribution ──────────────────────────────────────
    api_type_counter = Counter(r.get("api_type", "unknown") for r in records)

    # ── Category summary ──────────────────────────────────────────
    categories = list({r["category"] for r in records})
    cat_buildability = defaultdict(lambda: Counter())
    for r in records:
        cat_buildability[r["category"]][r["buildability"]] += 1

    # ── Verification stats ─────────────────────────────────────────
    verify_stats = {}
    if VERIFY.exists():
        with open(VERIFY, encoding="utf-8") as f:
            vdata = json.load(f)
        verify_stats = {
            "sample_size": vdata.get("sample_size", 0),
            "first_pass_accuracy": vdata.get("first_pass_accuracy", 0),
            "post_correction_accuracy": vdata.get("post_correction_accuracy", vdata.get("first_pass_accuracy", 0)),
            "field_accuracy": vdata.get("field_accuracy", {}),
            "human_checks_needed": vdata.get("human_checks_needed", []),
            "corrections_made": vdata.get("corrections_made", []),
        }

    analysis = {
        "total_apps": len(records),
        "auth_distribution": dict(auth_counter.most_common()),
        "self_serve_by_category": {
            cat: dict(counts) for cat, counts in cat_self_serve.items()
        },
        "buildability_distribution": dict(buildability_counter),
        "api_type_distribution": dict(api_type_counter),
        "mcp_coverage": {
            "count": mcp_count,
            "pct": round(mcp_count / len(records) * 100, 1)
        },
        "easy_wins": [
            {"id": r["id"], "name": r["name"], "category": r["category"],
             "evidence_url": r.get("evidence_url", "")}
            for r in easy_wins
        ],
        "needs_outreach": [
            {"id": r["id"], "name": r["name"], "category": r["category"],
             "main_blocker": r["main_blocker"]}
            for r in needs_outreach
        ],
        "top_blockers": dict(blocker_counter.most_common(10)),
        "category_buildability": {
            cat: dict(counts) for cat, counts in cat_buildability.items()
        },
        "verification": verify_stats,
        "headline_findings": _headline_findings(
            auth_counter, buildability_counter, easy_wins, mcp_count, len(records)
        ),
    }

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(analysis, f, indent=2)

    print(f"Analysis saved to {OUT}")
    for finding in analysis["headline_findings"]:
        print(f"  • {finding}")


def _headline_findings(auth_counter, build_counter, easy_wins, mcp_count, total):
    findings = []
    top_auth = auth_counter.most_common(1)[0] if auth_counter else ("?", 0)
    findings.append(
        f"{top_auth[0]} is the dominant auth method ({top_auth[1]} of {sum(auth_counter.values())} auth occurrences)"
    )
    ready_pct = round(build_counter.get("ready", 0) / total * 100)
    findings.append(f"{ready_pct}% of apps are buildable today (public API + self-serve creds)")
    findings.append(f"{len(easy_wins)} easy wins: ready AND fully self-serve")
    mcp_pct = round(mcp_count / total * 100)
    findings.append(f"Only {mcp_pct}% of apps have an existing MCP server")
    gated_pct = round((build_counter.get("gated", 0) + build_counter.get("needs-outreach", 0)) / total * 100)
    findings.append(f"{gated_pct}% require outreach or are gated behind paid/partner plans")
    return findings


if __name__ == "__main__":
    main()
