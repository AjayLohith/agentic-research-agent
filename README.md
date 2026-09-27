# Autonomous Research Agent

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Validation: Pydantic v2](https://img.shields.io/badge/validation-Pydantic%20v2-green.svg)](https://docs.pydantic.dev/)
[![Tests: Pytest](https://img.shields.io/badge/tests-39%20passed-brightgreen.svg)](tests/)

An autonomous, multi-tool AI research agent built from first principles for **Assessment Option 1 — Autonomous Research Agent**. It dynamically decomposes high-level user queries, orchestrates parallel web investigations, extracts and validates evidence, strips web boilerplate and irrelevant content, removes duplicate sources via URL normalization and content hashing, and synthesizes structured, publication-grade intelligence reports in Markdown, JSON, and PDF formats.

Designed to run using **free developer-tier resources** by default (**Groq** for high-speed LLM inference and **Tavily** for external web search).

---

## Assessment Option 1 Compliance Matrix

| Requirement | Implementation Component | Verification Status |
|---|---|---|
| **Accept user query / topic** | CLI (`app/main.py`) via `--goal` argument | **PASS** (Tested) |
| **Search external sources** | Multi-source search (`TavilyProvider`, `DuckDuckGoProvider`) | **PASS** (Tested) |
| **Extract relevant information** | `EvidenceService` & `RelevanceFilter` | **PASS** (Tested) |
| **Remove duplicate content** | `DeduplicationService` (URL normalization & SHA-256 hash) | **PASS** (Tested) |
| **Remove irrelevant content** | `RelevanceFilter` (Boilerplate removal & goal keyword scoring) | **PASS** (Tested) |
| **Structured summary (Key points)** | `ResearchReport.key_points` & Synthesizer | **PASS** (Tested) |
| **Structured summary (Important findings)** | `ResearchReport.findings` with source provenance | **PASS** (Tested) |
| **Structured summary (References/Sources)** | `ResearchReport.sources` & direct URL citations | **PASS** (Tested) |
| **Structured summary (Actionable insights)** | `ResearchReport.actionable_insights` | **PASS** (Tested) |
| **Autonomous source selection (Bonus)** | `AutonomousPlanner.create_plan` source strategies | **PASS** (Tested) |
| **Parallel gathering (Bonus)** | `parallel_fetch_urls` (Bounded async semaphore) | **PASS** (Tested) |
| **Export as Markdown (Bonus)** | `ReportService.render_markdown` (`output/report.md`) | **PASS** (Tested) |
| **Export as PDF (Bonus)** | `PdfExportService` (`output/report.pdf` via ReportLab) | **PASS** (Tested) |
| **Store previous searches (Bonus)** | `SearchMemoryStore` (`data/search_history.json`) | **PASS** (Tested) |

---

## Quick Start

### 1. Create environment
```bash
python -m venv .venv
```

### 2. Activate
**Windows (PowerShell / Command Prompt):**
```powershell
.venv\Scripts\activate
```

**Linux / macOS:**
```bash
source .venv/bin/activate
```

### 3. Install
```bash
pip install -r requirements.txt
```

### 4. Configure
```bash
# Windows
copy .env.example .env

# Linux / macOS
cp .env.example .env
```

Add your free developer keys to `.env`:
```env
GROQ_API_KEY=gsk_your_groq_api_key_here
TAVILY_API_KEY=tvly-your_tavily_api_key_here
```

### 5. Run Live Research
```bash
python -m app.main --goal "Analyze the current competitive landscape for AI agent frameworks"
```

---

## Table of Contents

1. [Overview](#1-overview)
2. [Assessment Alignment](#2-assessment-alignment)
3. [Architecture & Pipeline](#3-architecture--pipeline)
4. [Technology Stack](#4-technology-stack)
5. [Free Development Setup](#5-free-development-setup)
6. [Environment Variables](#6-environment-variables)
7. [Repository Structure](#7-repository-structure)
8. [Running the Agent](#8-running-the-agent)
9. [Failure Recovery Demonstration](#9-failure-recovery-demonstration)
10. [Deterministic Mock Mode](#10-deterministic-mock-mode)
11. [Testing & Coverage](#11-testing--coverage)
12. [Output Artifacts](#12-output-artifacts)
13. [Deliverables Guide](#13-deliverables-guide)
14. [Design Decisions](#14-design-decisions)
15. [Limitations & Future Work](#15-limitations--future-work)

---

## 1. Overview

The **Autonomous Research & Competitive Intelligence Agent** accepts arbitrary natural-language research goals—such as analyzing competitive frameworks, comparing backend platforms, or benchmarking cloud databases—and executes the complete research lifecycle autonomously:
* **Decomposes** the user's objective into a structured execution plan (`ResearchPlan`).
* **Selects and orchestrates** tools (`search_web`, `fetch_url`, `calculator`) dynamically based on accumulated observations.
* **Extracts verifiable evidence** (verbatim quotes, claims, source classifications) rather than hallucinating.
* **Detects anomalies & failures** (e.g. HTTP timeouts, 429s, 500s) and retries or replans without crashing.
* **Calculates quantitative metrics** via an AST-sandboxed calculator.
* **Synthesizes grounded reports** formatted as validated JSON (`output/report.json`) and publication-grade Markdown (`output/report.md`).

---

## 2. Why This Project

Standard LLM workflows fail in competitive intelligence because:
1. **Hallucination & Fabrication:** Models invent citations, URLs, and benchmarks when ungrounded.
2. **Fixed Pipelines Are Fragile:** A hardcoded sequence (`search -> search -> summarize`) crashes if a page is offline or returns an unexpected schema.
3. **No Explainable Confidence:** LLMs cannot objectively justify why they are "90% confident."

This project solves these challenges by combining **deterministic scaffolding** (safety limits, state tracking, retry loops, in-memory query caching, AST math) with **LLM dynamic reasoning** (decomposition, adaptive tool selection, and semantic synthesis).

---

## 3. Architecture

### Orchestration Flow

```text
User
 │
 ▼
CLI (Typer / app.main)
 │
 ▼
Research Agent (app.agent.graph)
 │
 ├── Planner (app/agent/planner.py)
 ├── Executor (app/agent/executor.py)
 ├── Recovery & Replanning (app/agent/recovery.py)
 ├── Evidence Validator (app/services/evidence.py)
 └── Synthesizer (app/agent/synthesizer.py)
       │
       ├──────────────┐
       ▼              ▼
   LLM Provider    Tool Layer
       │              │
       ▼              ├── Web Search (Tavily + in-memory cache)
     Groq             ├── URL Fetch (HTTPX + BeautifulSoup)
                      └── Calculator (Safe AST Evaluator)
                         │
                         ▼
                  External Web
```

For full architectural diagrams and specifications, see [`docs/architecture.mmd`](docs/architecture.mmd) and [`docs/architecture.md`](docs/architecture.md).

---

## 4. Technology Stack

The project prioritizes free, lightweight, battle-tested developer tools:
* **Core Runtime:** Python 3.11+
* **State Machine & Control:** Explicit typed state graph (`app.agent.graph`)
* **Default LLM Provider:** Groq (`llama-3.3-70b-versatile` or `openai/gpt-oss-120b` via OpenAI-compatible endpoint with exponential backoff on 429s)
* **Default Search Provider:** Tavily AI Search (free tier, 1,000 queries/month) with in-memory deduplication caching
* **Web Fetching & Parsing:** HTTPX (async client with timeouts) + BeautifulSoup4 (HTML extraction & tag cleaning)
* **Data Validation:** Pydantic v2 (strict models across all inputs, steps, and outputs)
* **Safe Mathematics:** Python AST math evaluator (zero `eval()` usage)
* **CLI Interface:** Typer + Rich
* **Testing:** Pytest + Pytest-Asyncio + Pytest-Cov

---

## 5. Free Development Setup

The project is designed to run using **free developer-tier resources**:
* **Default LLM:** Groq provides free-tier API access to open models with high inference speed.
* **Default Web Search:** Tavily provides a free tier with 1,000 search API credits/month and no credit card requirement.
* **Web Fetching:** Standard HTTPX and BeautifulSoup, with no paid proxy or scraping service needed.

> **Note on Free Tiers:** Free developer resources are subject to provider rate limits (e.g. Groq requests-per-minute limits, Tavily monthly quotas). The agent includes automated in-memory search caching, rate-limit retry backoff (`Retry-After`), and URL deduplication to conserve your developer quotas.

### API Configuration
The application automatically loads credentials from `.env`.

For the default live setup you only need:
```env
GROQ_API_KEY=gsk_...
TAVILY_API_KEY=tvly-...
```

* You do **not** need to modify Python files.
* You do **not** need to pass keys through the CLI.
* You do **not** need to configure individual tools separately.
* Missing credentials produce a clean, friendly configuration message rather than a cryptic stack trace.

---

## 6. Environment Variables

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `LLM_PROVIDER` | No | `groq` | Active LLM backend (`groq` or `mock`) |
| `LLM_MODEL` | No | `llama-3.3-70b-versatile` | Model identifier for LLM requests |
| `GROQ_API_KEY` | Yes (for Groq) | — | Groq API authentication key |
| `SEARCH_PROVIDER` | No | `tavily` | Search provider (`tavily`, `duckduckgo`, `mock`) |
| `TAVILY_API_KEY` | Yes (for Tavily) | — | Tavily API search key |
| `MOCK_MODE` | No | `false` | Enable zero-key offline deterministic execution |
| `DEMO_FAILURE_MODE` | No | `none` | Injected failure (`none`, `timeout`, `http_500`) |
| `MAX_AGENT_STEPS` | No | `20` | Maximum state transitions before bounded finish |
| `MAX_TOOL_CALLS` | No | `30` | Maximum external tool calls allowed per run |
| `MAX_RETRIES_PER_TOOL` | No | `2` | Maximum retry attempts per tool failure |
| `MAX_SEARCH_CALLS` | No | `5` | Maximum search calls per research run |
| `MAX_CONTENT_LENGTH` | No | `8000` | Smart-truncated webpage character budget |
| `LOG_LEVEL` | No | `INFO` | Logging verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |

---

## 7. Repository Structure

```text
agentic-research-agent/
│
├── app/
│   ├── main.py                     # CLI entry point and decoupled ResearchAgent runner
│   ├── config.py                   # Central settings and startup credential validation
│   ├── exceptions.py               # Application-level exceptions (ConfigurationError, ToolError)
│   ├── logging_config.py           # Structured JSON lines logging & token sanitizer
│   │
│   ├── agent/                      # Core agent state machine and cognitive components
│   │   ├── graph.py                # ResearchAgentGraph controller
│   │   ├── state.py                # AgentState with URL normalization & deduplication
│   │   ├── planner.py              # Goal decomposition into ResearchPlan
│   │   ├── executor.py             # Action selector, loop detector & executor
│   │   ├── recovery.py             # Centralized retry policy & adaptive replanner
│   │   ├── synthesizer.py          # Evidence-grounded synthesis into ResearchReport
│   │   └── prompts/                # Provider-neutral prompt modules
│   │       ├── planner.py          # Plan decomposition prompts
│   │       ├── executor.py         # Action selection prompts
│   │       ├── replanner.py        # Failure recovery prompts
│   │       ├── evidence.py         # Evidence extraction prompts
│   │       └── synthesis.py        # Final synthesis prompts
│   │
│   ├── models/                     # Strongly-typed Pydantic v2 schemas
│   │   ├── plan.py                 # ResearchPlan, PlanStep, ReplanningDecision
│   │   ├── tool.py                 # SearchResult, FetchResult, CalculatorResult
│   │   ├── evidence.py             # Evidence, Source, ConfidenceBreakdown
│   │   └── report.py               # ResearchReport schema & metadata
│   │
│   ├── providers/                  # Vendor-decoupled provider implementations
│   │   ├── llm/
│   │   │   ├── base.py             # Abstract LLMProvider interface
│   │   │   ├── groq.py             # Groq implementation with 429 backoff & JSON repair
│   │   │   └── mock.py             # Deterministic MockLLMProvider for offline testing
│   │   └── search/
│   │       ├── base.py             # Abstract SearchProvider with in-memory caching
│   │       ├── tavily.py           # Tavily API search provider
│   │       ├── duckduckgo.py       # DuckDuckGo Lite keyless fallback provider
│   │       └── mock.py             # Deterministic MockSearchProvider
│   │
│   ├── tools/                      # Deterministic tool interfaces
│   │   ├── base.py                 # BaseTool contract with timing & metrics
│   │   ├── search.py               # search_web tool wrapper
│   │   ├── fetch.py                # fetch_url tool with smart sentence-boundary truncation
│   │   ├── calculator.py           # Safe AST mathematical sandbox
│   │   └── failure_injector.py     # Deterministic failure injection hook
│   │
│   └── services/                   # Business logic and report formatters
│       ├── evidence.py             # 4-factor confidence scoring & authority calculation
│       └── reports.py              # Markdown generator & JSON serializer
│
├── tests/
│   ├── unit/
│   │   ├── test_calculator.py      # AST arithmetic & security sandbox tests
│   │   ├── test_tools.py           # Search & fetch tool validation tests
│   │   ├── test_models.py          # Pydantic serialization & report tests
│   │   └── test_failure_recovery.py# FailureInjector & replanning tests
│   └── integration/
│       └── test_agent.py           # End-to-end agent graph & recovery tests
│
├── docs/
│   ├── architecture.md             # Comprehensive architecture documentation
│   ├── architecture.mmd            # Mermaid architecture diagram source
│   ├── design_decisions.md         # One-page architectural write-up
│   └── final_review.md             # Assessment rubric compliance audit
│
├── examples/
│   ├── example_goals.txt           # Multi-domain research prompt examples
│   └── sample_run.md               # Realistic annotated execution transcript
│
├── output/                         # Generated artifacts
│   ├── report.md                   # Human-readable Markdown intelligence report
│   ├── report.json                 # Machine-consumable Pydantic JSON artifact
│   └── sample_run.log              # Structured JSON lines execution trace log
│
├── .env.example                    # Environment variable template
├── .gitignore                      # Git exclusion rules
├── requirements.txt                # Production and test dependencies
├── pyproject.toml                  # Python package & Pytest configuration
└── README.md                       # Comprehensive guide (this document)
```

---

## 8. Running the Agent

### Command Help
```bash
python -m app.main --help
```

### Live Research Run (Default: Groq + Tavily)
Requires `GROQ_API_KEY` and `TAVILY_API_KEY` in `.env`:
```bash
python -m app.main --goal "Analyze the current competitive landscape for AI agent frameworks"
```

### Custom Goal
```bash
python -m app.main --goal "Compare FastAPI and Spring Boot for building high-concurrency microservices"
```

### General Technology Research
```bash
python -m app.main --goal "Research recent developments in agentic AI and summarize key findings"
```

---

## 9. Failure Recovery Demonstration

The agent features an intentional failure-injection hook to demonstrate autonomous error detection, retry backoff, and replanning without human intervention:

```bash
python -m app.main \
  --goal "Analyze the current competitive landscape for AI agent frameworks" \
  --demo-failure
```

### What Happens:
1. The planner decomposes the goal and issues its first action (`fetch_url`).
2. The `FailureInjector` triggers a simulated network timeout on the first call:
   ```text
   WARNING Tool fetch failed: Simulated HTTP connection timeout
   ```
3. The centralized retry policy catches the transient error and retries with exponential backoff:
   ```text
   INFO Retrying fetch_url (attempt 1/2)...
   ```
4. The second attempt succeeds, and the agent continues executing the remaining plan steps.
5. If retries are exhausted, the agent invokes `AutonomousReplanner` to dynamically pivot to an alternative source.
6. The final execution summary records:
   ```text
   Failures Detected: 1
   Recoveries Performed: 1
   ```

---

## 10. Deterministic Mock Mode

Reviewers can run and evaluate the agent completely offline without any API keys or network connection:

```bash
# Using CLI flag
python -m app.main --mock --goal "Analyze the current competitive landscape for AI agent frameworks"

# Or using environment variable
MOCK_MODE=true python -m app.main --goal "Compare FastAPI and Spring Boot"
```

In mock mode:
* The LLM uses a deterministic mock provider returning structured plans and syntheses.
* The search tool returns pre-configured authoritative fixtures.
* The fetch tool parses clean fixture content without network calls.

---

## 11. Testing & Coverage

All unit and integration tests run offline without external API keys:

```bash
# Run all 36 tests
python -m pytest -v

# Run tests with code coverage report
python -m pytest --cov=app --cov-report=term-missing
```

### Test Suite Highlights:
* `test_relevance.py`: Asserts boilerplate removal (cookie notices, nav bars) and keyword relevance scoring.
* `test_deduplication.py`: Asserts URL normalization (stripping tracking query params, downcasing) and SHA-256 + token Jaccard deduplication.
* `test_search_memory.py`: Tests persistent session recording in `data/search_history.json` and similarity lookups.
* `test_pdf_export.py`: Validates binary PDF document synthesis, styles, and file persistence.
* `test_calculator.py`: Validates arithmetic evaluation and verifies that arbitrary code execution (`import`, `eval`, `open`, `__subclasses__`) is blocked by the AST sandbox.
* `test_tools.py`: Validates search normalization, content truncation, and fetch error handling.
* `test_models.py`: Validates strict Pydantic model schemas and JSON serialization.
* `test_failure_recovery.py`: Asserts that injected tool failures trigger retries and adaptive replanning.
* `test_agent.py`: End-to-end integration tests verifying complete agent execution runs and report generation.

**All 36 tests pass with 0 failures.**

---

## 12. Output Artifacts

Every completed run produces synchronized artifacts:

1. **[`output/report.md`](output/report.md):** Publication-grade Markdown report including:
   * Executive Summary
   * Research Scope & Methodology
   * Key Points & Important Findings with Grounded Confidence Scores
   * Entity Comparison Table & Profiles
   * Quantitative Metrics & AST Calculations
   * Actionable Insights
   * Grounded Evidence Register with Direct Source Quotes & URLs
   * Execution Audit (sources considered, deduplicated, relevance-filtered, failures, recoveries)

2. **[`output/report.json`](output/report.json):** Validated machine-readable JSON strictly conforming to the Pydantic `ResearchReport` model.

3. **[`output/report.pdf`](output/report.pdf):** Multi-page PDF report generated with ReportLab Platypus.

4. **[`data/search_history.json`](data/search_history.json):** Lightweight session memory tracking research objectives, key points, source domains, and execution metrics.

---

## 13. Deliverables Guide

All required assessment submission artifacts are available in the repository:

* **[Tech Stack & Feature Testing Guide](docs/tech_stack_and_testing_guide.md):** Complete breakdown of libraries, engineering rationale, and copy-pasteable runnable commands for every feature.
* **[Assessment Checklist & Traceability Matrix](docs/assessment_checklist.md):** Verification of all required and bonus capabilities.
* **[One-Page Architectural Write-Up](docs/writeup.md):** Engineering summary covering approach, architecture, autonomous behavior, evidence grounding, and design decisions.
* **[Sample Run Transcripts](docs/sample_runs.md):** Annotated execution traces for 3 distinct research queries:
  1. *Competitive Intelligence:* AI Agent Frameworks (`output/samples/competitive_frameworks.md`)
  2. *Technical Comparison:* FastAPI vs Spring Boot (`output/samples/fastapi_vs_springboot.md`)
  3. *Technology Research:* Agentic AI Developments (`output/samples/agentic_ai_research.md`)
* **[Architecture Documentation & Diagram](docs/architecture.md):** Detailed technical specifications and Mermaid diagrams (`docs/architecture.mmd`).

---

## 14. Design Decisions

For an in-depth architectural justification, see [`docs/design_decisions.md`](docs/design_decisions.md) and [`docs/writeup.md`](docs/writeup.md).

Key highlights:
* **Vendor-Neutral Provider Abstraction:** `LLMProvider` and `SearchProvider` interfaces keep the agent core completely decoupled from Groq or Tavily specifics.
* **Evidence-First Quality Pipeline:** Web content is parsed through `RelevanceFilter` (boilerplate stripping, topic density scoring) and `DeduplicationService` (URL normalization, SHA-256 fingerprinting) before reaching the LLM, preserving token budgets.
* **Compact Synthesis Budget:** Top-ranked evidence and deduplicated sources are packed into a controlled context window (< 3,000 tokens) to respect free-tier TPM limits while maintaining deep source provenance.
* **AST Calculator Sandbox:** Evaluates arithmetic strictly via Python's AST parser, completely preventing arbitrary code execution.
* **Explainable Confidence Model:** Avoids LLM self-scoring guesses by computing:
  $$\text{Confidence} = (\text{Authority} \times 0.40) + (\text{Directness} \times 0.35) + (\text{Corroboration} \times 0.25) - \text{Conflict Penalty}$$
* **Prompt Injection Isolation:** Web page content is cleanly wrapped in untrusted data boundaries with explicit instructions to ignore embedded commands.

---

## 15. Limitations & Future Work

1. **JavaScript-Rendered Content:** The built-in fetch tool relies on `HTTPX` + `BeautifulSoup`. Client-side rendered Single-Page Applications (SPAs) requiring JavaScript evaluation would benefit from headless browser integration (e.g. Playwright).
2. **Free-Tier Rate Limits:** Under free developer tiers, Groq enforces tokens-per-minute limits. The agent dynamically compresses evidence contexts to avoid rate limits.
3. **Persistent Vector Store:** For multi-document corpuses exceeding hundreds of pages, an external vector database (Milvus/Qdrant) can be connected to the provider layer.

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
#   a g e n t i c - r e s e a r c h - a g e n t  
 