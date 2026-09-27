# Autonomous Research Agent

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Pydantic v2](https://img.shields.io/badge/validation-Pydantic%20v2-green.svg)](https://docs.pydantic.dev/)
[![Tests: 39 Passed](https://img.shields.io/badge/tests-39%20passed-brightgreen.svg)](tests/)

An autonomous AI research agent that decomposes natural-language goals into multi-step plans, orchestrates web search and content extraction, validates evidence, removes duplicates and boilerplate, and synthesizes structured intelligence reports — built completely from first principles.

Built for **Assessment Option 1 — Autonomous Research Agent**. Runs on **free-tier** resources by default ([Groq](https://groq.com) + [Tavily](https://tavily.com)) with an offline deterministic mock mode requiring **zero API keys**.

---

## Table of Contents

- [Setup and Installation](#setup-and-installation)
- [Execution Flow (Step-by-Step)](#execution-flow-step-by-step)
  - [1. Verification and Tests](#1-verification-and-tests)
  - [2. Zero-Config Run (Offline Mock Mode)](#2-zero-config-run-offline-mock-mode)
  - [3. Failure Recovery and Self-Healing Demo](#3-failure-recovery-and-self-healing-demo)
  - [4. Live Web Research (Real APIs)](#4-live-web-research-real-apis)
  - [5. Inspect Generated Artifacts](#5-inspect-generated-artifacts)
- [Assessment Compliance](#assessment-compliance)
- [Overview](#overview)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Environment Variables](#environment-variables)
- [Project Structure](#project-structure)
- [Testing Suite](#testing-suite)
- [Output Artifacts](#output-artifacts)
- [Submission Deliverables](#submission-deliverables)
- [Design Decisions](#design-decisions)
- [Limitations and Future Work](#limitations-and-future-work)

---

## Setup and Installation

Follow these steps sequentially to set up and run the solution on your machine without any external guidance.

### Prerequisites

- **Python 3.11+** installed (`python --version`)
- **Git** installed (`git --version`)

---

### Step 1: Clone the Repository

```bash
git clone https://github.com/AjayLohith/agentic-research-agent.git
cd agentic-research-agent
```

---

### Step 2: Create a Virtual Environment

```bash
python -m venv .venv
```

---

### Step 3: Activate the Virtual Environment

- **Windows (PowerShell):**
  ```powershell
  .venv\Scripts\Activate.ps1
  ```
  *(If script execution is disabled, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned`)*

- **Windows (Command Prompt):**
  ```cmd
  .venv\Scripts\activate.bat
  ```

- **Linux / macOS:**
  ```bash
  source .venv/bin/activate
  ```

---

### Step 4: Upgrade Pip & Install Dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

---

### Step 5: Configure Environment Variables

Create your local `.env` configuration file from the template:

- **Windows:**
  ```cmd
  copy .env.example .env
  ```
- **Linux / macOS:**
  ```bash
  cp .env.example .env
  ```

#### Choose Your Mode:

| Mode | What to Do | Cost / Setup |
|---|---|---|
| **A. Offline Mock Mode (Zero-Config)** | **No changes needed!** The solution is immediately executable out of the box with zero external dependencies. | $0.00 / Instant |
| **B. Live Web Research** | Open `.env` in an editor and enter your free API keys: <br>`GROQ_API_KEY=gsk_...`<br>`TAVILY_API_KEY=tvly-...` | $0.00 (Free Tiers)<br>[Groq Console](https://console.groq.com) · [Tavily](https://tavily.com) |

---

## Execution Flow (Step-by-Step)

Execute the following commands one by one to validate and explore every capability of the agent:

### 1. Verification and Tests

Run the complete test suite to confirm all units, integration flows, and sandboxes are healthy:

```bash
python -m pytest -v
```

> **Expected output:** All `39 passed` in ~20 seconds across integration, deduplication, relevance, AST calculator, query independence, and PDF export tests.

---

### 2. Zero-Config Run (Offline Mock Mode)

Run the agent on an objective without needing any API keys. This exercises the full planning, scraping, deduplication, relevance scoring, and synthesis pipeline using deterministic fixtures:

```bash
python -m app.main --mock --goal "Analyze the current competitive landscape for AI agent frameworks"
```

> **What happens:**
> 1. The planner decomposes the goal into 5 structured sub-tasks.
> 2. Search and extraction tools gather candidate evidence.
> 3. Deduplication (URL normalization + SHA-256 + Jaccard) strips redundant data.
> 4. Relevance filtering eliminates boilerplate, cookies, and off-topic fragments.
> 5. Synthesizer generates structured findings with source citations and confidence scores.
> 6. Outputs are saved to Markdown, JSON, and PDF formats.

---

### 3. Failure Recovery and Self-Healing Demo

Demonstrate the agent's autonomous resilience against transient network faults and timeouts:

```bash
python -m app.main --mock --demo-failure --goal "Investigate open-source model evaluation frameworks"
```

> **What happens:**
> 1. Planner initializes the execution state graph.
> 2. `FailureInjector` triggers a simulated timeout failure during the initial tool invocation.
> 3. Recovery supervisor intercepts the failure, logs the incident, and invokes exponential backoff retry (attempt 1/2).
> 4. Retry succeeds and the execution graph resumes cleanly to final report generation without human intervention.
> 5. Full incident timeline is recorded in the execution trace.

---

### 4. Live Web Research (Real APIs)

*(Requires `GROQ_API_KEY` and `TAVILY_API_KEY` set in `.env`)*

Execute real-time internet research using Tavily web search and Groq's high-speed inference engine (`openai/gpt-oss-120b`):

```bash
python -m app.main --goal "Analyze recent breakthroughs in multimodal AI agents"
```

You can pass any custom research topic:

```bash
python -m app.main --goal "Compare FastAPI and Spring Boot for production microservices"
```

---

### 5. Inspect Generated Artifacts

Once an execution completes, all artifacts are structured in `output/` and `data/`:

```bash
# View the synthesized Markdown report
# (Windows PowerShell)
Get-Content output/report.md -TotalCount 50

# (Linux / macOS)
head -n 50 output/report.md
```

Artifact paths:
- [`output/report.md`](output/report.md) — Human-readable executive summary, key findings, and source evidence.
- [`output/report.json`](output/report.json) — Pydantic-validated machine-readable JSON schema.
- [`output/report.pdf`](output/report.pdf) — Publication-grade formatted PDF report.
- [`output/sample_run.log`](output/sample_run.log) — Structured event logs with step-by-step latency & tool traces.
- [`data/search_history.json`](data/search_history.json) — Persistent search memory recording queries and sources across runs.

---

## Assessment Compliance

| Requirement | Component | Status |
|---|---|---|
| Accept user query / topic | CLI (`app/main.py`) via `--goal` parameter | ✅ Pass |
| Search external sources | `TavilyProvider`, `DuckDuckGoProvider` | ✅ Pass |
| Extract relevant information | `EvidenceService` + `RelevanceFilter` | ✅ Pass |
| Remove duplicate content | `DeduplicationService` (URL norm + SHA-256 + Jaccard) | ✅ Pass |
| Remove irrelevant content | `RelevanceFilter` (boilerplate + goal relevance scoring) | ✅ Pass |
| Structured summary — Key points | `ResearchReport.key_points` | ✅ Pass |
| Structured summary — Findings | `ResearchReport.findings` with source provenance | ✅ Pass |
| Structured summary — References | `ResearchReport.sources` with direct URLs | ✅ Pass |
| Structured summary — Insights | `ResearchReport.actionable_insights` | ✅ Pass |
| *Bonus:* Autonomous source selection | `AutonomousPlanner` source strategies | ✅ Pass |
| *Bonus:* Parallel gathering | `parallel_fetch_urls` (async semaphore) | ✅ Pass |
| *Bonus:* Markdown export | `ReportService` → `output/report.md` | ✅ Pass |
| *Bonus:* PDF export | `PdfExportService` → `output/report.pdf` | ✅ Pass |
| *Bonus:* Search memory | `SearchMemoryStore` → `data/search_history.json` | ✅ Pass |

---

## Overview

The agent accepts any natural-language research goal and autonomously:

1. **Decomposes** the objective into a structured `ResearchPlan` with typed steps
2. **Selects tools** (`search_web`, `fetch_url`, `calculator`) dynamically per step
3. **Extracts evidence** — verbatim quotes, source classifications, authority scores
4. **Filters noise** — removes cookie notices, nav bars, and off-topic content
5. **Deduplicates** — URL normalization + SHA-256 fingerprinting + Jaccard similarity
6. **Recovers from failures** — exponential backoff retries + autonomous replanning
7. **Synthesizes** a grounded report with explainable confidence scores
8. **Exports** Markdown, JSON, and PDF artifacts with search history persistence

---

## Architecture

```
User Research Goal
       │
       ▼
┌─────────────────────────────────────────────┐
│  Agent Entry Point (app/main.py)            │
│  Config Validation + Provider Setup         │
└──────────────────┬──────────────────────────┘
                   ▼
┌─────────────────────────────────────────────┐
│  Autonomous Planner (agent/planner.py)      │
│  Goal decomposition + source strategy       │
└──────────────────┬──────────────────────────┘
                   ▼
┌─────────────────────────────────────────────┐
│  Execution Graph (agent/graph.py)           │
│  State machine with typed transitions       │
│                                             │
│  ┌─────────────┐  ┌─────────────┐           │
│  │ search_web  │  │  fetch_url  │  Tools    │
│  │ (Tavily)    │  │ (HTTPX+BS4) │           │
│  └─────────────┘  └─────────────┘           │
│  ┌─────────────┐                            │
│  │ calculator  │  (Safe AST)                │
│  └─────────────┘                            │
│                                             │
│  ┌──────────────────────────────────────┐   │
│  │ Quality Pipeline                     │   │
│  │ Relevance Filter → Dedup → Evidence  │   │
│  └──────────────────────────────────────┘   │
│                                             │
│  ┌──────────────────────────────────────┐   │
│  │ Failure Recovery (agent/recovery.py) │   │
│  │ Backoff retries → Replanning         │   │
│  └──────────────────────────────────────┘   │
└──────────────────┬──────────────────────────┘
                   ▼
┌─────────────────────────────────────────────┐
│  Synthesizer (agent/synthesizer.py)         │
│  Evidence-grounded report generation        │
└──────────────────┬──────────────────────────┘
                   ▼
       ┌───────────┼───────────┐
       ▼           ▼           ▼
   report.md   report.json  report.pdf
```

> Detailed diagrams: [`docs/architecture.md`](docs/architecture.md) · [`docs/architecture.mmd`](docs/architecture.mmd) · [`docs/architecture_diagram.jpg`](docs/architecture_diagram.jpg)

---

## Tech Stack

| Layer | Technology | Why |
|---|---|---|
| Runtime | Python 3.11+ | Native async I/O, modern type hints, cross-platform |
| LLM Provider | Groq (`openai/gpt-oss-120b`) | Free tier, high-throughput inference, OpenAI-compatible API |
| Search Provider | Tavily | Free tier (1,000/mo), structured factual results, zero scraping blockers |
| Web Fetching | HTTPX + BeautifulSoup4 | Async HTTP client + robust HTML text parsing |
| Data Validation | Pydantic v2 | Strict schema validation for plans, tools, evidence, and reports |
| Math Evaluation | Python AST parser | Safe arithmetic evaluation blocking `eval()` and code injection |
| CLI Interface | Typer + Rich | Clean command-line interface with interactive progress bars & tables |
| PDF Export | ReportLab | Publication-quality PDF layout and document generation |
| Testing | Pytest + Pytest-Asyncio | Fixture-based async test execution and coverage reporting |

---

## Environment Variables

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `GROQ_API_KEY` | Yes* | — | Groq API key |
| `TAVILY_API_KEY` | Yes* | — | Tavily search key |
| `LLM_PROVIDER` | No | `groq` | LLM backend (`groq` / `mock`) |
| `GROQ_MODEL` | No | `openai/gpt-oss-120b` | Model identifier |
| `SEARCH_PROVIDER` | No | `tavily` | Search backend (`tavily` / `duckduckgo` / `mock`) |
| `MOCK_MODE` | No | `false` | Offline deterministic mode (no keys needed) |
| `DEMO_FAILURE_MODE` | No | `none` | Failure injection (`none` / `timeout` / `http_500`) |
| `MAX_AGENT_STEPS` | No | `15` | Max state transitions per run |
| `MAX_TOOL_CALLS` | No | `25` | Max tool invocations per run |
| `MAX_RETRIES_PER_TOOL` | No | `2` | Retry budget per failed tool call |
| `LOG_LEVEL` | No | `INFO` | Logging verbosity |

*\*Not required when `--mock` is used or `MOCK_MODE=true`.*

---

## Project Structure

```
agentic-research-agent/
├── app/
│   ├── main.py                      # CLI entry point
│   ├── config.py                    # Settings + credential validation
│   ├── exceptions.py                # Custom domain exceptions
│   ├── logging_config.py            # Structured JSON logging
│   ├── agent/
│   │   ├── graph.py                 # State machine controller
│   │   ├── state.py                 # Typed agent state
│   │   ├── planner.py               # Goal → ResearchPlan
│   │   ├── executor.py              # Tool dispatch + loop detection
│   │   ├── recovery.py              # Retry + replanning
│   │   ├── synthesizer.py           # Evidence → Report
│   │   └── prompts/                 # LLM prompt templates
│   ├── models/
│   │   ├── plan.py                  # ResearchPlan, PlanStep
│   │   ├── tool.py                  # SearchResult, FetchResult
│   │   ├── evidence.py              # Evidence, ConfidenceBreakdown
│   │   └── report.py                # ResearchReport schema
│   ├── providers/
│   │   ├── llm/                     # Groq + Mock LLM providers
│   │   └── search/                  # Tavily + DuckDuckGo + Mock
│   ├── tools/
│   │   ├── search.py                # search_web tool
│   │   ├── fetch.py                 # fetch_url tool
│   │   ├── calculator.py            # Safe AST calculator
│   │   └── failure_injector.py      # Failure injection hook
│   └── services/
│       ├── evidence.py              # Confidence scoring
│       ├── deduplication.py         # URL norm + SHA-256 + Jaccard
│       ├── relevance.py             # Boilerplate + topic filtering
│       ├── reports.py               # Markdown + JSON rendering
│       ├── pdf_export.py            # ReportLab PDF generation
│       └── search_memory.py         # Session persistence
├── tests/
│   ├── unit/                        # 33 unit tests
│   └── integration/                 # 6 integration tests
├── docs/
│   ├── architecture.md              # Full architecture documentation
│   ├── architecture.mmd             # Mermaid diagram source
│   ├── architecture_diagram.jpg     # Rendered pipeline diagram
│   ├── writeup.md                   # One-page architectural write-up
│   ├── design_decisions.md          # Design rationale
│   ├── assessment_checklist.md      # Requirement traceability
│   ├── tech_stack_and_testing_guide.md
│   ├── sample_run_1.txt             # Normal execution transcript
│   ├── sample_run_2.txt             # Failure recovery transcript
│   ├── sample_run_3.txt             # Query independence transcript
│   ├── synthetic_test_traces_with_labels.txt
│   └── monitoring_report_dashboard_output.txt
├── output/                          # Generated reports
│   ├── report.md
│   ├── report.json
│   ├── report.pdf
│   └── sample_run.log
├── data/
│   └── search_history.json          # Search session memory
├── .env.example                     # Environment template
├── requirements.txt                 # Dependencies
├── pyproject.toml                   # Package + pytest config
└── LICENSE                          # MIT License
```

---

## Testing Suite

Execute tests by category or run the entire suite with coverage:

```bash
# Full test suite (39 tests)
python -m pytest -v

# With coverage report
python -m pytest --cov=app --cov-report=term-missing

# Run only integration tests
python -m pytest tests/integration/ -v

# Run only unit tests
python -m pytest tests/unit/ -v
```

### Test Breakdown

| Category | Tests | What It Validates |
|---|---|---|
| Integration — Full Pipeline | 1 | End-to-end mock execution through all phases |
| Integration — Failure Recovery | 1 | Injected failure → exponential retry → completion |
| Integration — Loop Detection | 1 | Cycle budget enforcement preventing infinite loops |
| Calculator Sandbox | 7 | Arithmetic operations, precedence, divide-by-zero, AST security |
| Deduplication | 4 | Exact URL normalization, SHA-256 hash match, Jaccard near-duplicate |
| Relevance Filtering | 4 | Boilerplate removal, cookie/nav stripping, goal keyword relevance |
| Query Independence | 3 | Dynamic planning ensuring different goals produce distinct plans |
| Models & Configuration | 6 | Pydantic v2 schemas, environment parsing, validation |
| Tools & Caching | 6 | Search, fetch, caching behavior, error handling |
| PDF Export | 1 | Valid PDF generation and ReportLab styling |
| Search Memory | 2 | Session save/load, search history persistence |
| Failure Recovery Unit | 2 | Injector behavior and retry policy execution |

---

## Output Artifacts

Every execution automatically generates the following deliverables:

| File | Format | Contents |
|---|---|---|
| [`output/report.md`](output/report.md) | Markdown | Executive summary, structured findings, evidence register, entity comparisons, metrics |
| [`output/report.json`](output/report.json) | JSON | Machine-readable report adhering strictly to the Pydantic `ResearchReport` schema |
| [`output/report.pdf`](output/report.pdf) | PDF | Publication-quality formatted report |
| [`output/sample_run.log`](output/sample_run.log) | JSON Lines | Structured execution trace with timestamps, state transitions, and tool calls |
| [`data/search_history.json`](data/search_history.json) | JSON | Search memory storing queries, visited URLs, and run summaries |

---

## Submission Deliverables

All documentation and assessment evidence files are committed in the repository:

| Deliverable | Path | Description |
|---|---|---|
| Architectural Write-up | [`docs/writeup.md`](docs/writeup.md) | One-page architectural overview, decisions, and trade-offs |
| Architecture Diagram | [`docs/architecture_diagram.jpg`](docs/architecture_diagram.jpg) | High-resolution visual architecture diagram |
| Architecture Documentation | [`docs/architecture.md`](docs/architecture.md) | In-depth technical architecture document |
| Mermaid Diagram Source | [`docs/architecture.mmd`](docs/architecture.mmd) | Raw Mermaid code for the architecture diagram |
| Assessment Checklist | [`docs/assessment_checklist.md`](docs/assessment_checklist.md) | Full requirement traceability mapping |
| Tech Stack & Testing Guide | [`docs/tech_stack_and_testing_guide.md`](docs/tech_stack_and_testing_guide.md) | Complete technology explanations and testing guide |
| Design Decisions | [`docs/design_decisions.md`](docs/design_decisions.md) | Detailed justification for architectural choices |
| Sample Run 1 — Normal Execution | [`docs/sample_run_1.txt`](docs/sample_run_1.txt) | Complete log transcript of successful standard run |
| Sample Run 2 — Failure Recovery | [`docs/sample_run_2.txt`](docs/sample_run_2.txt) | Transcript showing injected error, retry, and recovery |
| Sample Run 3 — Query Independence | [`docs/sample_run_3.txt`](docs/sample_run_3.txt) | Transcript proving dynamic planning across different queries |
| Synthetic Test Traces | [`docs/synthetic_test_traces_with_labels.txt`](docs/synthetic_test_traces_with_labels.txt) | 18 labeled traces across all agent capabilities |
| Monitoring Dashboard | [`docs/monitoring_report_dashboard_output.txt`](docs/monitoring_report_dashboard_output.txt) | Pipeline metrics, source quality, and grounding analysis |

---

## Design Decisions

| Decision | Rationale |
|---|---|
| **Custom state graph** over LangChain/CrewAI | Complete control and transparency over state transitions, retries, and cycle limits without framework bloat. |
| **Evidence-first pipeline** | Content passes through relevance filtering and deduplication *before* LLM synthesis, conserving context window and reducing hallucinations. |
| **AST calculator sandbox** | `eval()` poses severe security hazards; AST parsing restricts evaluation strictly to safe mathematical operations. |
| **Vendor-neutral provider abstractions** | Abstract `LLMProvider` and `SearchProvider` interfaces enable swapping models or backends without touching agent logic. |
| **Explainable confidence scoring** | Deterministic mathematical formulation instead of relying on subjective LLM self-evaluation. |

$$\text{Confidence} = (\text{Authority} \times 0.40) + (\text{Directness} \times 0.35) + (\text{Corroboration} \times 0.25) - \text{Conflict Penalty}$$

---

## Limitations and Future Work

| Limitation | Mitigation / Future Path |
|---|---|
| JavaScript-rendered SPAs | HTTPX + BeautifulSoup4 cannot execute client-side JavaScript. Future integration with Playwright or headless browser for dynamic pages. |
| Free-tier rate limits | In-memory search caching and exponential backoff mitigate rate exhaustion. Production deployments can connect paid tiers or local Ollama instances. |
| Single-session search memory | Current search history is JSON-based. Future integration with vector databases (e.g., ChromaDB, Qdrant) would enable cross-session semantic retrieval. |

---

<p align="center">
  <strong>Autonomous Research Agent</strong><br>
  Built for Assessment Option 1 — Autonomous Research Agent
</p>
