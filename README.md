# Autonomous Research & Competitive Intelligence Agent

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Code style: Pydantic](https://img.shields.io/badge/validation-Pydantic%20v2-green.svg)](https://docs.pydantic.dev/)
[![Tests: Pytest](https://img.shields.io/badge/tests-21%20passed-brightgreen.svg)](tests/)

An autonomous, multi-tool AI research agent built from first principles for competitive intelligence, architectural benchmarking, and deep domain research. It dynamically decomposes high-level user goals, orchestrates live web searches and HTTP page inspections, performs verifiable mathematical calculations, autonomously detects and recovers from tool failures, and synthesizes structured, citation-grounded intelligence reports.

---

## Table of Contents

1. [Overview](#1-overview)
2. [Why This Project](#2-why-this-project)
3. [Key Features](#3-features)
4. [Architecture](#4-architecture)
5. [Repository Structure](#5-project-structure)
6. [Requirements](#6-requirements)
7. [Installation](#7-installation)
8. [Configuration](#8-configuration)
9. [Running the Agent](#9-running)
10. [Main Demonstration](#10-demo)
11. [Failure Recovery Demonstration](#11-failure-recovery-demo)
12. [Testing & Coverage](#12-testing)
13. [Output Artifacts](#13-output)
14. [Design Decisions](#14-design-decisions)
15. [Limitations](#15-limitations)
16. [Production Roadmap](#16-production-improvements)

---

## 1. Overview

The **Autonomous Research & Competitive Intelligence Agent** accepts arbitrary natural-language research goals—such as analyzing competitive frameworks, comparing backend platforms, or benchmarking cloud databases—and executes the complete research lifecycle autonomously:
* **Decomposes** the user's objective into a structured execution plan.
* **Selects and orchestrates** tools (`search_web`, `fetch_url`, `calculator`) dynamically based on accumulated observations.
* **Extracts verifiable evidence** (verbatim quotes, claims, source classifications) rather than hallucinating.
* **Detects anomalies & failures** (e.g. HTTP timeouts, 500s) and replans or retries without halting.
* **Calculates quantitative metrics** via an AST-sandboxed calculator.
* **Synthesizes grounded reports** formatted as validated JSON (`report.json`) and publication-grade Markdown (`report.md`).

---

## 2. Why This Project

Standard LLM workflows fail in competitive intelligence because:
1. **Hallucination & Fabrication:** Models invent citations, URLs, and benchmarks when ungrounded.
2. **Fixed Pipelines Are Fragile:** A hardcoded sequence (`search -> search -> summarize`) crashes if a page is offline or returns an unexpected schema.
3. **No Explainable Confidence:** LLMs cannot objectively justify why they are "90% confident."

This project solves these challenges by combining **deterministic scaffolding** (safety limits, state tracking, retry loops, AST math) with **LLM dynamic reasoning** (decomposition, adaptive tool selection, and semantic synthesis).

---

## 3. Features

* **Autonomous Planning:** Dynamic goal decomposition into an inspectable `ResearchPlan` without exposing private chain-of-thought.
* **Dynamic Tool Orchestration:** Agent autonomously determines which tool to call based on intermediate findings.
* **3 Distinct Production Tools:**
  * `search_web`: Live public web search via DuckDuckGo Lite (no API key required) or Tavily.
  * `fetch_url`: Robust HTTP page fetching with BeautifulSoup HTML normalization and content bounding.
  * `calculator`: Safe AST mathematical evaluator for ratios, percentages, and metrics.
* **Failure Recovery & Replanning:** Two-tiered resilience: automatic retry with backoff, followed by adaptive replanning to alternative sources if a tool remains unresponsive.
* **Failure Injection Hook:** CLI flag (`--demo-failure`) deliberately simulates a timeout on the first call to demonstrate real-time autonomous recovery.
* **Evidence Grounding:** Every factual finding references a source URL and verbatim supporting quote.
* **Explainable Confidence Model:** Mathematical weighting combining Source Authority, Evidence Directness, Independent Corroboration, and Conflict Penalties.
* **Loop Detection & Research Budget:** Automatically detects repetitive queries and enforces step/tool limits to prevent token burn.
* **Prompt Injection Defense:** Web content is treated strictly as passive data, stripping adversarial prompt override attempts.
* **Deterministic Mock Mode:** Zero-cost offline mode (`--mock`) utilizing rich fixtures for testing and CI without external network access.

---

## 4. Architecture

### Orchestration Diagram

```mermaid
flowchart TD
    subgraph Input_Layer ["Input & Goal Deconstruction"]
        UG["User Research Goal\n(Natural Language)"] --> GV["Input Validator &\nSanitizer"]
        GV --> AP["Autonomous Planner\n(LLM Decomposition)"]
        AP -->|Structured ResearchPlan| AG["Agent Controller\n(ResearchAgentGraph)"]
    end

    subgraph Orchestration_Layer ["Autonomous Execution Loop"]
        AG --> SA["Select Next Action\n(Context & State Aware)"]
        SA --> LD{"Loop Detected\nor Budget Exceeded?"}
        LD -->|Yes| PI["Pivot Strategy /\nRefine Query"]
        PI --> SA
        LD -->|No| TC["Tool Controller\n& Schema Validation"]
    end

    subgraph Tool_Ecosystem ["Pluggable Tool Suite"]
        TC -->|Query| ST["search_web\n(DuckDuckGo / Tavily / Mock)"]
        TC -->|URL| FT["fetch_url\n(HTTPX / BeautifulSoup / Sanitizer)"]
        TC -->|Arithmetic| CT["calculator\n(Safe AST Math Evaluator)"]
    end

    subgraph Observation_Layer ["Observation & Anomaly Handling"]
        ST --> OBS["Observation Collector"]
        FT --> OBS
        CT --> OBS
        OBS --> SC["Source Classifier &\nAuthority Scorer"]
        OBS --> EE["Evidence Extractor &\nQuote Verifier"]
        OBS --> FD{"Tool Failure\nor Timeout?"}
    end

    subgraph Recovery_Layer ["Failure Recovery & Adaptive Replanning"]
        FD -->|Failure| RC{"Retry Count < Max?"}
        RC -->|Yes| RT["Exponential Backoff\n& Retry Tool"]
        RT --> TC
        RC -->|No (Exceeded)| RP["Autonomous Replanner\n(Alternative Source / Replan)"]
        RP -->|Updated Steps| AG
    end

    subgraph Synthesis_Layer ["Evidence Grounding & Structured Reporting"]
        FD -->|Success| CHK{"Remaining Steps\nor Budget Left?"}
        CHK -->|Yes| AG
        CHK -->|No| EV["Evidence Coverage\n& Discrepancy Validator"]
        EV --> CS["Explainable Confidence\nScoring Engine"]
        CS --> AS["Autonomous Synthesizer\n(LLM Synthesis)"]
        AS --> SR["Structured ResearchReport\n(Pydantic Model)"]
        SR --> MD["output/report.md\n(Publication Markdown)"]
        SR --> JS["output/report.json\n(Validated JSON Artifact)"]
        SR --> LG["output/sample_run.log\n(Structured Trace Log)"]
    end
```

For full architectural specifications, see [`docs/architecture.md`](docs/architecture.md).

---

## 5. Project Structure

```text
agentic-research-agent/
│
├── app/
│   ├── __init__.py
│   ├── main.py                     # Typer CLI application entry point
│   ├── config.py                   # Pydantic BaseSettings management
│   ├── logging_config.py           # Structured JSON logging & token sanitizer
│   │
│   ├── agent/                      # Core agent state machine & cognitive nodes
│   │   ├── __init__.py
│   │   ├── graph.py                # ResearchAgentGraph state machine controller
│   │   ├── state.py                # AgentState representation
│   │   ├── planner.py              # Goal decomposition into ResearchPlan
│   │   ├── executor.py             # Action selector, loop detector & executor
│   │   ├── replanner.py            # Failure recovery & adaptive replanner
│   │   ├── synthesizer.py          # Evidence synthesis into ResearchReport
│   │   └── prompts.py              # Standardized prompt templates & schemas
│   │
│   ├── tools/                      # Deterministic tool interfaces
│   │   ├── __init__.py
│   │   ├── base.py                 # BaseTool contract with timing & validation
│   │   ├── search.py               # search_web tool
│   │   ├── fetch.py                # fetch_url tool with BeautifulSoup sanitizer
│   │   ├── calculator.py           # Safe AST mathematical evaluator
│   │   └── failure_injector.py     # Deterministic failure injection hook
│   │
│   ├── models/                     # Strongly-typed Pydantic v2 data models
│   │   ├── __init__.py
│   │   ├── plan.py                 # ResearchPlan, PlanStep, ReplanningDecision
│   │   ├── tool.py                 # SearchResult, FetchResult, CalculatorResult
│   │   ├── evidence.py             # Evidence, Source, ConfidenceBreakdown
│   │   └── report.py               # ResearchReport schema & metadata
│   │
│   ├── providers/                  # Vendor-decoupled provider abstractions
│   │   ├── __init__.py
│   │   ├── llm.py                  # OpenAI-compatible & MockLLMProvider
│   │   └── search.py               # DuckDuckGo, Tavily & MockSearchProvider
│   │
│   └── services/                   # Business logic services
│       ├── __init__.py
│       ├── source_service.py       # Domain classification & authority scoring
│       ├── evidence_service.py     # Confidence formula & conflict detection
│       └── report_service.py       # Markdown renderer & JSON serializer
│
├── tests/
│   ├── unit/
│   │   ├── test_calculator.py      # AST arithmetic & security sandbox tests
│   │   ├── test_tools.py           # Search & fetch tool validation tests
│   │   ├── test_models.py          # Pydantic serialization & report tests
│   │   └── test_failure_recovery.py# FailureInjector & replanning tests
│   │
│   └── integration/
│       └── test_agent.py           # End-to-end agent graph & recovery tests
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
├── docs/
│   ├── architecture.md             # Comprehensive architecture documentation
│   ├── architecture.mmd            # Raw Mermaid source file
│   ├── design_decisions.md         # One-page architectural write-up
│   └── final_review.md             # Assessment rubric compliance audit
│
├── .env.example                    # Environment variable template
├── .gitignore                      # Git exclusion rules
├── requirements.txt                # Production and test dependencies
├── pyproject.toml                  # Python package & Pytest configuration
├── LICENSE                         # MIT License
└── README.md                       # Comprehensive guide (this document)
```

---

## 6. Requirements

* **Python:** 3.11 or higher
* **Operating System:** Windows, macOS, or Linux
* **Optional API Keys:**
  * `OPENAI_API_KEY`: Required only for live LLM mode. (Deterministic mock mode works out of the box with zero keys!)
  * `TAVILY_API_KEY`: Optional; live web search defaults to keyless DuckDuckGo Lite.

---

## 7. Installation

Clone the repository and set up a virtual environment:

```bash
git clone <repo-url>
cd agentic-research-agent

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows (PowerShell / Command Prompt):
.venv\Scripts\activate
# Linux / macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

Create your `.env` configuration file:

```bash
# Windows:
copy .env.example .env

# Linux / macOS:
cp .env.example .env
```

---

## 8. Configuration

Edit `.env` to configure your preferred execution settings:

| Variable | Default | Description |
|---|---|---|
| `LLM_PROVIDER` | `openai` | LLM backend: `openai` or `mock`. |
| `LLM_MODEL` | `gpt-4o-mini` | Model name (e.g. `gpt-4o-mini`, `gpt-4o`, `llama3`). |
| `OPENAI_API_KEY` | *(empty)* | OpenAI or OpenAI-compatible provider API key. |
| `OPENAI_BASE_URL` | `https://api.openai.com/v1` | Endpoint URL (supports Ollama, Groq, OpenRouter). |
| `SEARCH_PROVIDER` | `duckduckgo` | Public search: `duckduckgo` (free, keyless), `tavily`, or `mock`. |
| `MOCK_MODE` | `false` | Set to `true` for offline deterministic test runs without keys. |
| `DEMO_FAILURE_MODE` | `none` | Failure simulation: `none`, `timeout`, `http_500`, `empty_response`. |
| `MAX_AGENT_STEPS` | `15` | Maximum execution cycles before forced termination. |
| `MAX_TOOL_CALLS` | `25` | Maximum tool calls allowed per session. |
| `MAX_RETRIES_PER_TOOL`| `2` | Maximum retry attempts on tool failure before replanning. |
| `MAX_RESEARCH_TIME_SECONDS`| `300`| Total execution timeout in seconds. |

---

## 9. Running

Show command-line options:

```bash
python -m app.main --help
```

### Command Flags:
* `--goal` / `-g`: The natural-language research goal to investigate.
* `--mock` / `-m`: Run in deterministic offline mock mode (zero cost, zero keys needed).
* `--demo-failure` / `-d`: Intentionally induce a first-attempt tool timeout to demonstrate autonomous recovery.
* `--output` / `-o`: Directory to write `report.md`, `report.json`, and `sample_run.log` (default: `output/`).
* `--interactive` / `-i`: Launch interactive prompt to type research goals dynamically.

---

## 10. Demo

### Demo 1: Primary Competitive Intelligence Goal (Offline / Mock)
Runs instantly with zero configuration:

```bash
python -m app.main --mock \
  --goal "Analyze the current competitive landscape for AI agent frameworks and identify the major players, their capabilities, positioning, recent developments, and important differences."
```

### Demo 2: Cross-Domain Architecture Comparison
Demonstrating that the agent autonomously adapts its plan to arbitrary technical topics:

```bash
python -m app.main --mock \
  --goal "Compare FastAPI and Spring Boot for building production backend APIs."
```

### Demo 3: Live Mode with Real External Web Data
Provide your `OPENAI_API_KEY` in `.env` and run:

```bash
python -m app.main \
  --goal "Research recent developments in AI agent frameworks in 2026."
```

---

## 11. Failure Recovery Demo

To deliberately verify autonomous failure detection, retry backoff, and replanning, run with `--demo-failure`:

```bash
python -m app.main --mock --demo-failure
```

### What Happens:
1. The agent decomposes the goal and issues its first fetch action.
2. The `FailureInjector` triggers a simulated network timeout:
   ```text
   [FAILURE DETECTED] Tool: fetch_url | Error: Simulated HTTP connection timeout (read timed out after 10.0s)
   ```
3. The `AutonomousReplanner` catches the failure, logs the incident, and initiates retry 1/2.
4. The second attempt succeeds, and the agent continues its execution plan without crashing.
5. The final execution summary records:
   ```text
   Failures Detected: 1
   Recoveries Performed: 1
   ```

---

## 12. Testing

The repository includes a comprehensive Pytest test suite covering tool validation, AST sandboxing, model serialization, failure injection, and end-to-end integration:

```bash
# Run full test suite
pytest

# Run tests with coverage report
pytest --cov=app
```

All 21 tests pass with zero network dependency requirements.

---

## 13. Output

After each run, the agent writes artifacts to the specified output folder (`output/`):

1. **[`output/report.md`](output/report.md):** Publication-ready Markdown report including:
   * Executive Summary
   * Research Objective, Scope & Assumptions
   * Key Findings with Category & Grounded Confidence Scores
   * Entity / Competitor Comparison Table & Detailed Profiles
   * Comparative Matrix across technical dimensions
   * Safe Quantitative Calculations
   * Grounded Evidence Register & Numbered Source Directory (`[1]`, `[2]`, `[3]`)
   * Agent Execution Summary (steps, tool calls, failures, recoveries)
   * Limitations & Production Improvements

2. **[`output/report.json`](output/report.json):** Validated machine-consumable JSON conforming directly to the Pydantic `ResearchReport` schema.

3. **[`output/sample_run.log`](output/sample_run.log):** Structured JSON lines log tracing every plan generation, tool execution, observation, failure, and recovery event with timestamp and sanitized tokens.

---

## 14. Design Decisions

For an in-depth architectural justification, see [`docs/design_decisions.md`](docs/design_decisions.md).

Key highlights:
* **Custom State Graph over Heavy Frameworks:** Rather than hiding agent state inside black-box agent frameworks (CrewAI/AutoGen), a lightweight state graph makes every cycle, failure, and transition inspectable.
* **AST Calculator Sandbox:** Evaluates arithmetic expressions strictly via Python's AST parser, completely blocking arbitrary execution, imports, and system calls.
* **Explainable Confidence:** Avoids arbitrary LLM confidence guessing by evaluating:
  $$\text{Confidence} = (\text{Authority} \times 0.40) + (\text{Directness} \times 0.35) + (\text{Corroboration} \times 0.25) - \text{Conflict Penalty}$$

---

## 15. Limitations

1. **JavaScript-Heavy SPAs:** The built-in fetch tool relies on `httpx` and `BeautifulSoup`. Pages that require dynamic client-side JavaScript execution (React/Vue SPAs) require a headless browser (e.g. Playwright).
2. **Rate Limits & Anti-Bot Shields:** Public websites may present Cloudflare CAPTCHAs or strict IP rate limits during heavy scraping.
3. **Temporal Horizon:** Information is bounded by publicly indexed documentation available at the time of execution.

---

## 16. Production Improvements

To scale this agent to an enterprise production environment:
* **Persistent Vector & Document Graph:** Introduce Milvus or Qdrant for semantic chunk retrieval across multi-page documentation trees.
* **Distributed Task Execution:** Migrate graph nodes to distributed async workflows (Temporal or Celery) with parallel proxy rotation.
* **Continuous Fact Verification:** Integrate automated hallucination benchmarking frameworks (Ragas, TruLens) into CI/CD pipelines.
* **Human-in-the-Loop Gateways:** Add interactive checkpoints allowing human domain experts to approve strategic decisions or increase tool budgets.
* **OpenTelemetry Instrumentation:** Stream live spans and token costs to Datadog or LangSmith.

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
