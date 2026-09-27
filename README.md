# Autonomous Research Agent

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Pydantic v2](https://img.shields.io/badge/validation-Pydantic%20v2-green.svg)](https://docs.pydantic.dev/)
[![Tests: 39 Passed](https://img.shields.io/badge/tests-39%20passed-brightgreen.svg)](tests/)

An autonomous AI research agent that decomposes natural-language goals into multi-step plans, orchestrates web search and content extraction, validates evidence, removes duplicates and boilerplate, and synthesizes structured intelligence reports — all from first principles.

Built for **Assessment Option 1 — Autonomous Research Agent**. Runs on **free-tier** resources by default ([Groq](https://groq.com) + [Tavily](https://tavily.com)).

---

## Table of Contents

- [Quick Start](#quick-start)
- [Assessment Compliance](#assessment-compliance)
- [Overview](#overview)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Environment Variables](#environment-variables)
- [Project Structure](#project-structure)
- [Usage](#usage)
  - [Live Research](#live-research)
  - [Mock Mode](#mock-mode)
  - [Failure Recovery Demo](#failure-recovery-demo)
- [Testing](#testing)
- [Output Artifacts](#output-artifacts)
- [Deliverables](#deliverables)
- [Design Decisions](#design-decisions)
- [Limitations & Future Work](#limitations--future-work)

---

## Quick Start

```bash
# 1. Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux / macOS

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure API keys
copy .env.example .env          # Windows
# cp .env.example .env          # Linux / macOS
```

Add your free keys to `.env`:

```env
GROQ_API_KEY=gsk_your_key_here
TAVILY_API_KEY=tvly-your_key_here
```

```bash
# 4. Run a research query
python -m app.main --goal "Analyze the current competitive landscape for AI agent frameworks"

# 5. Run without API keys (offline mock mode)
python -m app.main --mock --goal "Compare FastAPI and Spring Boot for microservices"
```

---

## Assessment Compliance

| Requirement | Component | Status |
|---|---|---|
| Accept user query / topic | CLI (`app/main.py`) via `--goal` | ✅ Pass |
| Search external sources | `TavilyProvider`, `DuckDuckGoProvider` | ✅ Pass |
| Extract relevant information | `EvidenceService` + `RelevanceFilter` | ✅ Pass |
| Remove duplicate content | `DeduplicationService` (URL norm + SHA-256 + Jaccard) | ✅ Pass |
| Remove irrelevant content | `RelevanceFilter` (boilerplate + goal scoring) | ✅ Pass |
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

> Full diagrams: [`docs/architecture.md`](docs/architecture.md) · [`docs/architecture.mmd`](docs/architecture.mmd) · [`docs/architecture_diagram.jpg`](docs/architecture_diagram.jpg)

---

## Tech Stack

| Layer | Technology | Why |
|---|---|---|
| Runtime | Python 3.11+ | Async support, type hints, broad ecosystem |
| LLM Provider | Groq (`openai/gpt-oss-120b`) | Free tier, OpenAI-compatible API, fast inference |
| Search Provider | Tavily | Free tier (1,000/mo), structured results, no scraping |
| Web Fetching | HTTPX + BeautifulSoup4 | Async HTTP client + robust HTML parsing |
| Data Validation | Pydantic v2 | Strict typed schemas for all inputs/outputs |
| Math Evaluation | Python AST parser | Safe arithmetic — blocks `eval()` and code injection |
| CLI | Typer + Rich | Clean interface with colored tables and progress |
| PDF Export | ReportLab | Publication-quality PDF generation |
| Testing | Pytest + Pytest-Asyncio | Async-compatible, fixture-based test framework |

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

*\*Not required when `MOCK_MODE=true`*

---

## Project Structure

```
agentic-research-agent/
├── app/
│   ├── main.py                      # CLI entry point
│   ├── config.py                    # Settings + credential validation
│   ├── exceptions.py                # Custom exceptions
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
│   └── integration/                 # 6 integration tests (3 files)
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

## Usage

### Live Research

```bash
python -m app.main --goal "Analyze the current competitive landscape for AI agent frameworks"
```

```bash
python -m app.main --goal "Compare FastAPI and Spring Boot for production microservices"
```

### Mock Mode

Run completely offline with zero API keys:

```bash
python -m app.main --mock --goal "Research recent developments in agentic AI"
```

### Failure Recovery Demo

Demonstrates autonomous error detection, retry, and replanning:

```bash
python -m app.main --mock --demo-failure --goal "Investigate open-source model evaluation frameworks"
```

**What happens:**
1. Planner decomposes the goal into 5 steps
2. `FailureInjector` triggers a simulated timeout on the first tool call
3. Recovery module retries with exponential backoff (attempt 1/2)
4. Retry succeeds → agent continues executing remaining steps
5. If retries exhaust, `AutonomousReplanner` pivots to alternative sources

---

## Testing

```bash
# Run full test suite (39 tests)
python -m pytest -v

# With coverage report
python -m pytest --cov=app --cov-report=term-missing
```

**39/39 tests pass** across these categories:

| Category | Tests | What It Validates |
|---|---|---|
| Integration — Full Pipeline | 1 | End-to-end mock execution |
| Integration — Failure Recovery | 1 | Injected failures → retry → completion |
| Integration — Loop Detection | 1 | Cycle budget enforcement |
| Calculator | 7 | Arithmetic, edge cases, security sandbox |
| Deduplication | 4 | URL normalization, SHA-256, Jaccard |
| Relevance Filtering | 4 | Boilerplate removal, topic scoring |
| Query Independence | 3 | Different goals → different plans |
| Models & Config | 6 | Pydantic schemas, config validation |
| Tools | 6 | Search, fetch, caching, error handling |
| PDF Export | 1 | Valid PDF generation |
| Search Memory | 2 | Session save/load, history lookup |
| Failure Recovery | 2 | Injector behavior, retry policy |

---

## Output Artifacts

Every run produces:

| File | Format | Contents |
|---|---|---|
| [`output/report.md`](output/report.md) | Markdown | Executive summary, findings, evidence register, entity comparisons, metrics |
| [`output/report.json`](output/report.json) | JSON | Pydantic-validated machine-readable report |
| [`output/report.pdf`](output/report.pdf) | PDF | Publication-quality formatted report |
| [`output/sample_run.log`](output/sample_run.log) | JSON Lines | Structured execution trace with timestamps |
| [`data/search_history.json`](data/search_history.json) | JSON | Session memory (goals, sources, metrics) |

---

## Deliverables

| Document | Path |
|---|---|
| Architectural Write-up | [`docs/writeup.md`](docs/writeup.md) |
| Architecture Diagram | [`docs/architecture_diagram.jpg`](docs/architecture_diagram.jpg) |
| Architecture Documentation | [`docs/architecture.md`](docs/architecture.md) |
| Mermaid Diagram Source | [`docs/architecture.mmd`](docs/architecture.mmd) |
| Assessment Checklist | [`docs/assessment_checklist.md`](docs/assessment_checklist.md) |
| Tech Stack & Testing Guide | [`docs/tech_stack_and_testing_guide.md`](docs/tech_stack_and_testing_guide.md) |
| Design Decisions | [`docs/design_decisions.md`](docs/design_decisions.md) |
| Sample Run 1 — Normal Execution | [`docs/sample_run_1.txt`](docs/sample_run_1.txt) |
| Sample Run 2 — Failure Recovery | [`docs/sample_run_2.txt`](docs/sample_run_2.txt) |
| Sample Run 3 — Query Independence | [`docs/sample_run_3.txt`](docs/sample_run_3.txt) |
| Synthetic Test Traces | [`docs/synthetic_test_traces_with_labels.txt`](docs/synthetic_test_traces_with_labels.txt) |
| Monitoring Dashboard | [`docs/monitoring_report_dashboard_output.txt`](docs/monitoring_report_dashboard_output.txt) |

---

## Design Decisions

| Decision | Rationale |
|---|---|
| **Custom state graph** over LangChain/CrewAI | Full visibility into transitions, retries, and observation logs |
| **Evidence-first pipeline** | Content passes through relevance + dedup filters *before* reaching the LLM |
| **AST calculator sandbox** | `eval()` is dangerous — AST parsing blocks arbitrary code execution |
| **Vendor-neutral providers** | `LLMProvider` and `SearchProvider` interfaces decouple from Groq/Tavily |
| **Explainable confidence** | Deterministic formula instead of LLM self-scoring guesses |

> Confidence = (Authority × 0.40) + (Directness × 0.35) + (Corroboration × 0.25) − Conflict Penalty

See [`docs/design_decisions.md`](docs/design_decisions.md) for full rationale.

---

## Limitations & Future Work

| Limitation | Mitigation / Future Path |
|---|---|
| JavaScript-rendered SPAs | HTTPX+BS4 can't execute JS — integrate Playwright for SPA support |
| Free-tier rate limits | In-memory caching + backoff retries conserve quota; upgrade tiers for production |
| Single-session memory | Add persistent vector store (Qdrant/Milvus) for multi-document semantic search |

---

<p align="center">
  <strong>Built for the Agentic AI Engineer Intern Assessment</strong><br>
  Assessment Option 1 — Autonomous Research Agent
</p>
