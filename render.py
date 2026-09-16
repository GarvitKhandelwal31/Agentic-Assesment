"""
render.py
=========
Reads data/results.json and data/analysis.json,
renders a single self-contained output.html.

Run: python render.py
"""

import json
from pathlib import Path
from jinja2 import Template

RESULTS = Path("data/results.json")
ANALYSIS = Path("data/analysis.json")
OUTPUT = Path("index.html")

TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Composio App Research — 100 Apps</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
  :root{--bg:#0d0d0d;--surface:#1a1a1a;--border:#2a2a2a;--text:#e8e8e8;--muted:#888;
    --green:#22c55e;--yellow:#f59e0b;--red:#ef4444;--blue:#3b82f6;--purple:#a855f7;}
  *{box-sizing:border-box;margin:0;padding:0;}
  body{font-family:system-ui,-apple-system,sans-serif;background:var(--bg);color:var(--text);font-size:14px;}
  a{color:var(--blue);text-decoration:none;}a:hover{text-decoration:underline;}
  h1{font-size:2rem;font-weight:800;}h2{font-size:1.25rem;font-weight:700;margin-bottom:1rem;}
  h3{font-size:1rem;font-weight:600;margin-bottom:.5rem;}
  .hero{padding:3rem 2rem;max-width:1400px;margin:auto;}
  .tagline{color:var(--muted);font-size:.95rem;margin-top:.5rem;}
  .findings-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:1rem;margin-top:2rem;}
  .finding-card{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:1.25rem;}
  .finding-card .num{font-size:2rem;font-weight:800;color:var(--blue);}
  .finding-card p{color:var(--muted);margin-top:.25rem;font-size:.85rem;}
  .section{padding:2rem;max-width:1400px;margin:auto;}
  .charts-row{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:1.5rem;margin-bottom:2rem;}
  .chart-box{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:1.25rem;}
  canvas{max-height:260px;}
  /* Table */
  .table-wrap{overflow-x:auto;}
  .filters{display:flex;gap:.5rem;flex-wrap:wrap;margin-bottom:1rem;}
  .filter-btn{background:var(--surface);border:1px solid var(--border);color:var(--text);padding:.35rem .75rem;
    border-radius:6px;cursor:pointer;font-size:.8rem;transition:all .15s;}
  .filter-btn.active,.filter-btn:hover{background:var(--blue);border-color:var(--blue);color:#fff;}
  input[type=search]{background:var(--surface);border:1px solid var(--border);color:var(--text);
    padding:.4rem .8rem;border-radius:6px;font-size:.85rem;width:240px;}
  table{width:100%;border-collapse:collapse;font-size:.82rem;}
  thead th{text-align:left;padding:.6rem .75rem;background:var(--surface);border-bottom:1px solid var(--border);
    position:sticky;top:0;z-index:10;white-space:nowrap;}
  tbody tr{border-bottom:1px solid var(--border);}
  tbody tr:hover{background:rgba(255,255,255,.03);}
  td{padding:.55rem .75rem;vertical-align:top;max-width:260px;}
  .badge{display:inline-block;padding:.2rem .5rem;border-radius:4px;font-size:.72rem;font-weight:600;
    white-space:nowrap;}
  .badge-ready{background:#14532d;color:var(--green);}
  .badge-outreach{background:#451a03;color:var(--yellow);}
  .badge-gated{background:#450a0a;color:var(--red);}
  .badge-noapi{background:#1e1b4b;color:var(--purple);}
  .badge-yes{background:#14532d;color:var(--green);}
  .badge-partial{background:#451a03;color:var(--yellow);}
  .badge-self_serve_gated{background:#450a0a;color:var(--red);}
  .badge-unknown{background:#27272a;color:var(--muted);}
  .auth-tag{display:inline-block;background:#1e293b;color:#94a3b8;padding:.1rem .4rem;border-radius:3px;
    font-size:.7rem;margin:.1rem;}
  .conf{font-size:.75rem;color:var(--muted);}
  .mcp-yes{color:var(--green);}
  .mcp-no{color:var(--muted);}
  /* Agent section */
  .agent-grid{display:grid;grid-template-columns:1fr 1fr;gap:1.5rem;}
  @media(max-width:720px){.agent-grid{grid-template-columns:1fr;}}
  .agent-box{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:1.25rem;}
  .agent-box ul{list-style:disc;padding-left:1.2rem;line-height:1.8;color:var(--muted);font-size:.85rem;}
  .agent-box .human{color:var(--yellow);}
  /* Verification */
  .ver-table table{font-size:.8rem;}
  .agree{color:var(--green);}
  .disagree{color:var(--red);}
  .accuracy-bar-wrap{margin:1rem 0;}
  .accuracy-bar{height:20px;border-radius:10px;background:linear-gradient(90deg,var(--green),var(--blue));
    position:relative;transition:width .8s;}
  .accuracy-label{font-size:.85rem;margin-bottom:.3rem;color:var(--muted);}
  footer{text-align:center;padding:2rem;color:var(--muted);font-size:.8rem;border-top:1px solid var(--border);}
  .section-label{display:inline-block;background:var(--blue);color:#fff;font-size:.7rem;padding:.15rem .5rem;
    border-radius:4px;margin-bottom:.5rem;text-transform:uppercase;letter-spacing:.05em;}
  .heatmap{overflow-x:auto;}
  .heatmap table{border-collapse:separate;border-spacing:2px;}
  .heatmap td,.heatmap th{padding:.4rem .6rem;border-radius:4px;text-align:center;font-size:.75rem;}
  .heatmap th{background:transparent;color:var(--muted);}
  .cell-0{background:#1a1a1a;color:var(--muted);}
  .cell-1{background:#14532d66;color:var(--green);}
  .cell-2{background:#14532d99;color:var(--green);}
  .cell-3{background:#14532dcc;color:var(--green);}
  .cell-high{background:#14532d;color:var(--green);}
</style>
</head>
<body>

<!-- ══ HERO ══════════════════════════════════════════════════════════════ -->
<div class="hero">
  <span class="section-label">Composio App Research</span>
  <h1>100 Apps. Every Auth Pattern. Real Findings.</h1>
  <p class="tagline">An AI research agent surveyed 100 apps across 10 categories to find where agent toolkits can be built today — and where they can't.</p>

  <div class="findings-grid">
    {% for f in analysis.headline_findings %}
    <div class="finding-card">
      <div class="num">{{ loop.index }}</div>
      <p>{{ f }}</p>
    </div>
    {% endfor %}
  </div>
</div>

<!-- ══ PATTERNS ══════════════════════════════════════════════════════════ -->
<div class="section">
  <span class="section-label">Patterns</span>
  <h2>Key Patterns Across 100 Apps</h2>
  <div class="charts-row">

    <div class="chart-box">
      <h3>Auth Method Distribution</h3>
      <canvas id="authChart"></canvas>
    </div>

    <div class="chart-box">
      <h3>Buildability Split</h3>
      <canvas id="buildChart"></canvas>
    </div>

    <div class="chart-box">
      <h3>API Type Distribution</h3>
      <canvas id="apiChart"></canvas>
    </div>

    <div class="chart-box">
      <h3>Self-Serve Access by Category</h3>
      <canvas id="selfServeChart"></canvas>
    </div>

  </div>

  <!-- Heatmap: Category × Buildability -->
  <h3 style="margin-bottom:.75rem;">Category × Buildability Heatmap</h3>
  <div class="heatmap">
    <table>
      <thead>
        <tr>
          <th style="text-align:left;">Category</th>
          <th>ready</th><th>needs-outreach</th><th>gated</th><th>no-api</th>
        </tr>
      </thead>
      <tbody>
        {% for cat, counts in analysis.category_buildability.items() %}
        <tr>
          <td style="text-align:left;color:var(--text);">{{ cat }}</td>
          {% for status in ["ready","needs-outreach","gated","no-api"] %}
          {% set n = counts.get(status, 0) %}
          <td class="cell-{{ ['0','1','2','3','high'][([0,1,2,3,4]|select('le',n)|list|length - 1)] }}">
            {{ n if n > 0 else "·" }}
          </td>
          {% endfor %}
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
</div>

<!-- ══ FULL TABLE ═════════════════════════════════════════════════════════ -->
<div class="section">
  <span class="section-label">Full Data</span>
  <h2>All 100 Apps</h2>
  <div class="filters">
    <input type="search" id="searchBox" placeholder="Search apps..." oninput="filterTable()"/>
    <button class="filter-btn active" onclick="filterBy('all',this)">All</button>
    <button class="filter-btn" onclick="filterBy('ready',this)">✅ Ready</button>
    <button class="filter-btn" onclick="filterBy('needs-outreach',this)">⚠️ Needs Outreach</button>
    <button class="filter-btn" onclick="filterBy('gated',this)">🔒 Gated</button>
    <button class="filter-btn" onclick="filterBy('no-api',this)">🚫 No API</button>
  </div>
  <div class="table-wrap">
    <table id="appsTable">
      <thead>
        <tr>
          <th>#</th><th>App</th><th>Category</th><th>What it does</th>
          <th>Auth</th><th>Self-Serve</th><th>API Type</th>
          <th>MCP</th><th>Buildability</th><th>Blocker</th><th>Confidence</th><th>Docs</th>
        </tr>
      </thead>
      <tbody>
        {% for r in results %}
        <tr data-build="{{ r.buildability }}" data-name="{{ r.name|lower }}" data-cat="{{ r.category|lower }}">
          <td>{{ r.id }}</td>
          <td><strong>{{ r.name }}</strong></td>
          <td style="color:var(--muted);">{{ r.category }}</td>
          <td>{{ r.one_liner }}</td>
          <td>{% for a in r.auth_methods %}<span class="auth-tag">{{ a }}</span>{% endfor %}</td>
          <td>
            {% if r.self_serve == "yes" %}
              <span class="badge badge-yes">Yes</span>
            {% elif r.self_serve == "partial" %}
              <span class="badge badge-partial">Partial</span>
            {% elif r.self_serve == "gated" %}
              <span class="badge badge-self_serve_gated">Gated</span>
            {% else %}
              <span class="badge badge-unknown">?</span>
            {% endif %}
          </td>
          <td>{{ r.api_type }}</td>
          <td>
            {% if r.mcp_exists %}
              <span class="mcp-yes" title="{{ r.mcp_notes }}">✓</span>
            {% else %}
              <span class="mcp-no">–</span>
            {% endif %}
          </td>
          <td>
            {% if r.buildability == "ready" %}
              <span class="badge badge-ready">Ready</span>
            {% elif r.buildability == "needs-outreach" %}
              <span class="badge badge-outreach">Needs Outreach</span>
            {% elif r.buildability == "gated" %}
              <span class="badge badge-gated">Gated</span>
            {% else %}
              <span class="badge badge-noapi">No API</span>
            {% endif %}
          </td>
          <td style="color:var(--muted);font-size:.78rem;">{{ r.main_blocker if r.main_blocker != "none" else "–" }}</td>
          <td class="conf">{{ "%.0f"|format(r.agent_confidence * 100) }}%</td>
          <td><a href="{{ r.evidence_url }}" target="_blank">docs ↗</a></td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
</div>

<!-- ══ AGENT ══════════════════════════════════════════════════════════════ -->
<div class="section">
  <span class="section-label">The Agent</span>
  <h2>What We Built & Where a Human Was Needed</h2>
  <div class="agent-grid">
    <div class="agent-box">
      <h3>🤖 What the Agent Does</h3>
      <ul>
        <li>Loads <code>apps.json</code> (100 apps with hint URLs)</li>
        <li>For each app: fetches the hint URL (6k chars), sends to <strong>Gemini 3.5 Flash Lite</strong></li>
        <li>Structured output enforced via <code>response_mime_type=application/json</code></li>
        <li>5 concurrent workers with exponential backoff on failures</li>
        <li>Crash-safe: each result written to <code>data/raw/</code> immediately</li>
        <li>Verification: independent second-pass Gemini call on 20 stratified samples</li>
        <li>Analysis: <code>analyse.py</code> computes all patterns (auth, buildability, blockers)</li>
        <li>Render: <code>render.py</code> + Jinja2 → single self-contained <code>output.html</code></li>
        <li>Built using <strong>Composio SDK</strong> for toolset integration</li>
      </ul>
    </div>
    <div class="agent-box">
      <h3>🧑 Where a Human Was Needed (Honest)</h3>
      <ul>
        <li><strong>Providing API keys</strong> — GEMINI_API_KEY and COMPOSIO_API_KEY supplied by the human to run the pipeline.</li>
        <li class="human"><strong>#97 Higgsfield</strong> — Agent said <em>needs-outreach, no MCP</em>. Human found: REST API + API Key, MCP server, self-serve. <strong>Agent was wrong.</strong></li>
        <li class="human"><strong>#25 Pumble</strong> — Agent said <em>needs-outreach, no MCP</em>. Human found: REST API + API Key, MCP server, free tier. <strong>Agent was wrong.</strong></li>
        <li class="human"><strong>#85 iPayX</strong> — Agent said <em>no-api, no public docs</em>. Human found: REST API + API Key, MCP server, self-serve. <strong>Agent was wrong.</strong></li>
        <li><strong>#24 Lark</strong> — Second-pass verifier flagged auth as incomplete. Human confirmed: OAuth2 flow required, not just static Bearer Token. Correction applied.</li>
        <li><strong>#91 NotebookLM, #58 Sherlock, #92 Otter AI, #81 Stripe, #61 GitHub, #90 PitchBook</strong> — Human checked all 6. Agent findings confirmed correct.</li>
        <li style="color:var(--muted);font-size:.82rem;"><em>Everything else was fully automated: research, second-pass LLM verification, pattern analysis, HTML render. No other human review was done.</em></li>
      </ul>
    </div>
  </div>
</div>

<!-- ══ VERIFICATION ═══════════════════════════════════════════════════════ -->
<div class="section ver-table">
  <span class="section-label">Verification</span>
  <h2>Accuracy Check — Sample of {{ analysis.verification.get("sample_size", 20) }}</h2>

  {% set acc = analysis.verification.get("first_pass_accuracy", 0) %}
  {% set post_acc = analysis.verification.get("post_correction_accuracy", acc) %}

  <!-- Accuracy bars -->
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:1.5rem;max-width:820px;margin-bottom:2rem;">
    <div>
      <div class="accuracy-label">🤖 Agent-only (first pass): <strong>{{ "%.0f"|format(acc * 100) }}%</strong> on 20-app sample</div>
      <div style="background:var(--surface);border-radius:10px;height:22px;width:100%;overflow:hidden;">
        <div style="height:100%;width:{{ "%.0f"|format(acc * 100) }}%;background:linear-gradient(90deg,#f59e0b,#3b82f6);border-radius:10px;"></div>
      </div>
    </div>
    <div>
      <div class="accuracy-label">✅ After human corrections: <strong style="color:var(--green);">{{ "%.0f"|format(post_acc * 100) }}%</strong></div>
      <div style="background:var(--surface);border-radius:10px;height:22px;width:100%;overflow:hidden;">
        <div style="height:100%;width:{{ "%.0f"|format(post_acc * 100) }}%;background:linear-gradient(90deg,#22c55e,#16a34a);border-radius:10px;"></div>
      </div>
    </div>
  </div>

  <!-- How verification worked -->
  <div style="background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:1.1rem 1.25rem;margin-bottom:2rem;font-size:.85rem;color:var(--muted);max-width:820px;">
    <strong style="color:var(--text);">How verification worked:</strong>
    Step 1 — A second independent Gemini call reviewed all 20 sampled apps and flagged any field it disagreed with.
    Step 2 — The human reviewer (Garvi) manually checked 10 apps against real docs, confirmed or overruled the agent, and applied corrections.
    Step 3 — Corrected records were written back to <code>data/results.json</code> and the HTML was re-rendered.
  </div>

  <!-- What the agent got WRONG — full story cards -->
  <h3 style="margin-bottom:1rem;color:var(--red);">❌ Where the Agent Was Wrong (3 apps)</h3>
  <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:1rem;margin-bottom:2rem;">

    <div style="background:#1a0a0a;border:1px solid var(--red);border-radius:10px;padding:1.1rem;">
      <div style="font-size:.75rem;color:var(--red);text-transform:uppercase;letter-spacing:.05em;margin-bottom:.4rem;">Agent wrong</div>
      <strong style="font-size:1rem;">#97 Higgsfield</strong>
      <div style="margin-top:.75rem;font-size:.82rem;">
        <div style="color:var(--red);margin-bottom:.3rem;">❌ Agent said: <code>needs-outreach</code>, no MCP, low confidence (40%)</div>
        <div style="color:var(--green);">✅ Human found: REST API available, API Key auth, <strong>MCP server exists</strong>, fully self-serve</div>
        <div style="margin-top:.5rem;color:var(--muted);">Impact: buildability changed <code>needs-outreach → ready</code></div>
      </div>
    </div>

    <div style="background:#1a0a0a;border:1px solid var(--red);border-radius:10px;padding:1.1rem;">
      <div style="font-size:.75rem;color:var(--red);text-transform:uppercase;letter-spacing:.05em;margin-bottom:.4rem;">Agent wrong</div>
      <strong style="font-size:1rem;">#25 Pumble</strong>
      <div style="margin-top:.75rem;font-size:.82rem;">
        <div style="color:var(--red);margin-bottom:.3rem;">❌ Agent said: <code>needs-outreach</code>, no MCP, confidence 70%</div>
        <div style="color:var(--green);">✅ Human found: REST API with API Key, <strong>MCP server exists</strong>, free tier self-serve</div>
        <div style="margin-top:.5rem;color:var(--muted);">Impact: buildability changed <code>needs-outreach → ready</code></div>
      </div>
    </div>

    <div style="background:#1a0a0a;border:1px solid var(--red);border-radius:10px;padding:1.1rem;">
      <div style="font-size:.75rem;color:var(--red);text-transform:uppercase;letter-spacing:.05em;margin-bottom:.4rem;">Agent wrong</div>
      <strong style="font-size:1rem;">#85 iPayX</strong>
      <div style="margin-top:.75rem;font-size:.82rem;">
        <div style="color:var(--red);margin-bottom:.3rem;">❌ Agent said: <code>no-api</code>, no public docs found</div>
        <div style="color:var(--green);">✅ Human found: REST API with API Key, <strong>MCP server exists</strong>, self-serve credentials available</div>
        <div style="margin-top:.5rem;color:var(--muted);">Impact: buildability changed <code>no-api → ready</code></div>
      </div>
    </div>

  </div>

  <!-- What the verifier caught -->
  <h3 style="margin-bottom:1rem;color:var(--yellow);">⚠️ What the Second-Pass Verifier Caught (1 field)</h3>
  <div style="background:#1a1000;border:1px solid var(--yellow);border-radius:10px;padding:1.1rem;max-width:640px;font-size:.85rem;margin-bottom:2rem;">
    <strong>#24 Lark (Larksuite) — auth_methods field</strong>
    <div style="margin-top:.6rem;color:var(--red);">❌ Primary agent said: <code>Bearer Token</code> only</div>
    <div style="margin-top:.3rem;color:var(--green);">✅ Verifier + human confirmed: authentication uses OAuth2 flow (App ID + App Secret → token exchange), then Bearer Token. Both methods should be listed.</div>
    <div style="margin-top:.5rem;color:var(--muted);">Correction: <code>["Bearer Token"] → ["OAuth2", "Bearer Token"]</code></div>
  </div>

  <!-- What was confirmed correct -->
  <h3 style="margin-bottom:1rem;color:var(--green);">✅ Human-Confirmed Correct (6 apps)</h3>
  <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:.75rem;margin-bottom:2rem;">
    {% for app in [("#91 NotebookLM","Gated — Enterprise only via Google Cloud. No consumer API.",True),("#58 Sherlock","No-API — CLI tool only, no HTTP API.",True),("#92 Otter AI","Gated — Enterprise plan required for API access.",True),("#81 Stripe","Ready — free test mode, instant API Key, broad REST.",True),("#61 GitHub","Ready — OAuth2/PAT, broad REST, official MCP server.",True),("#90 PitchBook","Needs-outreach — partner/contract gated.",True)] %}
    <div style="background:var(--surface);border:1px solid #14532d;border-radius:8px;padding:.85rem;font-size:.82rem;">
      <strong style="color:var(--green);">{{ app[0] }}</strong>
      <div style="color:var(--muted);margin-top:.3rem;">{{ app[1] }}</div>
    </div>
    {% endfor %}
  </div>

  <!-- Field-level accuracy table -->
  {% if analysis.verification.get("field_accuracy") %}
  <h3 style="margin-top:1.5rem;margin-bottom:.75rem;">Field-Level Accuracy (agent-only pass, 20 apps × 5 fields)</h3>
  <div class="table-wrap" style="max-width:500px;">
    <table>
      <thead><tr><th>Field</th><th>Accuracy</th><th>Agree</th><th>Disagree</th></tr></thead>
      <tbody>
        {% for field, stats in analysis.verification.field_accuracy.items() %}
        <tr>
          <td>{{ field }}</td>
          <td><strong>{{ "%.0f"|format(stats.accuracy * 100) }}%</strong></td>
          <td class="agree">{{ stats.agree }}</td>
          <td class="disagree">{{ stats.disagree }}</td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
  {% endif %}

  <div style="margin-top:1.5rem;padding:1rem;background:var(--surface);border:1px solid var(--border);border-radius:8px;color:var(--muted);font-size:.83rem;max-width:820px;">
    <strong style="color:var(--text);">Root cause of errors:</strong> Higgsfield, Pumble, and iPayX all have minimal web presence — their docs pages returned sparse content (or fetch errors), so the agent defaulted to conservative "can't confirm → gated/no-api" judgements. This is the correct failure mode (conservative over optimistic), but human verification is needed for thin-docs apps. MCP existence was the most commonly missed field.
  </div>



  {% if analysis.verification.get("human_checks_needed") %}
  <div style="margin-top:1.5rem;padding:1rem;background:#451a0322;border:1px solid var(--yellow);border-radius:8px;">
    <strong style="color:var(--yellow);">⚠ Apps flagged for human review:</strong>
    <span style="color:var(--muted);">{{ analysis.verification.human_checks_needed | join(", ") }}</span>
  </div>
  {% endif %}

  <div style="margin-top:1.5rem;padding:1rem;background:var(--surface);border:1px solid var(--border);border-radius:8px;color:var(--muted);font-size:.85rem;">
    <strong style="color:var(--text);">Honest misses:</strong> Apps with thin public documentation (DealCloud, Fanbasis, iPayX) had the lowest confidence scores and were flagged by the verification agent. Where the second-pass LLM disagreed with the primary finding, the human reviewer was the tiebreaker. Final accuracy reflects post-correction values.
  </div>
</div>

<footer>
  Built with Gemini 2.0 Flash · Composio SDK · Python · Jinja2 &nbsp;|&nbsp;
  Research agent: <code>research_agent.py</code> · Verification: <code>verify_agent.py</code> · Analysis: <code>analyse.py</code>
</footer>

<script>
// ── Chart data injected from Python ────────────────────────────────────
const authData = {{ auth_data | tojson }};
const buildData = {{ build_data | tojson }};
const apiData = {{ api_data | tojson }};
const selfServeData = {{ self_serve_data | tojson }};

const COLORS = ['#3b82f6','#22c55e','#f59e0b','#ef4444','#a855f7','#06b6d4','#f97316','#ec4899','#84cc16','#6366f1'];

function makeChart(id, type, labels, values, colors) {
  new Chart(document.getElementById(id), {
    type,
    data: {
      labels,
      datasets: [{data: values, backgroundColor: colors || COLORS.slice(0, labels.length),
        borderWidth: 0}]
    },
    options: {
      responsive: true,
      plugins: {legend: {labels: {color: '#e8e8e8', font: {size: 11}}}},
      scales: type === 'bar' ? {
        x: {ticks: {color: '#888'}, grid: {color: '#2a2a2a'}},
        y: {ticks: {color: '#888'}, grid: {color: '#2a2a2a'}}
      } : {}
    }
  });
}

makeChart('authChart', 'bar', authData.labels, authData.values);
makeChart('buildChart', 'doughnut', buildData.labels, buildData.values,
  ['#22c55e','#f59e0b','#ef4444','#a855f7']);
makeChart('apiChart', 'bar', apiData.labels, apiData.values);
makeChart('selfServeChart', 'bar', selfServeData.labels, selfServeData.values,
  ['#22c55e','#f59e0b','#ef4444','#888']);

// ── Table filtering ─────────────────────────────────────────────────────
let currentBuild = 'all';
function filterTable() {
  const q = document.getElementById('searchBox').value.toLowerCase();
  document.querySelectorAll('#appsTable tbody tr').forEach(tr => {
    const name = tr.dataset.name || '';
    const cat = tr.dataset.cat || '';
    const build = tr.dataset.build || '';
    const matchSearch = !q || name.includes(q) || cat.includes(q);
    const matchBuild = currentBuild === 'all' || build === currentBuild;
    tr.style.display = matchSearch && matchBuild ? '' : 'none';
  });
}
function filterBy(build, btn) {
  currentBuild = build;
  document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  filterTable();
}
</script>
</body>
</html>
"""


def build_chart_data(analysis: dict) -> dict:
    auth = analysis["auth_distribution"]
    build = analysis["buildability_distribution"]
    api = analysis["api_type_distribution"]

    # Self-serve by category: count "yes" across categories
    ss_by_cat = analysis["self_serve_by_category"]
    cat_labels = list(ss_by_cat.keys())
    # Show % ready per category for a grouped view
    ss_yes = [ss_by_cat[c].get("yes", 0) for c in cat_labels]
    ss_partial = [ss_by_cat[c].get("partial", 0) for c in cat_labels]
    ss_gated = [ss_by_cat[c].get("gated", 0) for c in cat_labels]
    ss_unknown = [ss_by_cat[c].get("unknown", 0) for c in cat_labels]

    return {
        "auth_data": {"labels": list(auth.keys()), "values": list(auth.values())},
        "build_data": {
            "labels": list(build.keys()),
            "values": list(build.values()),
        },
        "api_data": {"labels": list(api.keys()), "values": list(api.values())},
        "self_serve_data": {
            "labels": cat_labels,
            "values": ss_yes,
        },
    }


def to_json_str(obj) -> str:
    return json.dumps(obj, ensure_ascii=False)


def main():
    with open(RESULTS, encoding="utf-8") as f:
        results = json.load(f)
    with open(ANALYSIS, encoding="utf-8") as f:
        analysis = json.load(f)

    chart_data = build_chart_data(analysis)

    # Jinja2 does not have tojson built-in as a filter — add it
    from jinja2 import Environment
    env = Environment()
    env.filters["tojson"] = to_json_str

    tmpl = env.from_string(TEMPLATE)
    html = tmpl.render(
        results=results,
        analysis=analysis,
        **chart_data,
    )

    OUTPUT.write_text(html, encoding="utf-8")
    print(f"Rendered -> {OUTPUT.resolve()}")


if __name__ == "__main__":
    main()
