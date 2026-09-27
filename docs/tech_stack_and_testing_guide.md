# Technology Stack & Feature Testing Guide

This guide provides an exhaustive breakdown of every library, framework, provider, and built-in Python module used across the **Autonomous Research Agent**, explains **why** each component was chosen, and provides **copy-pasteable runnable commands** with expected outputs so you can test each feature yourself.

---

## 1. Complete Technology Stack & Rationale

| Category | Technology / Library | Version | Purpose in Codebase | Why We Chose It (Engineering Rationale) |
|---|---|---|---|---|
| **Language & Runtime** | **Python** | `3.11+` | Core execution environment | Industry standard for AI agent development; first-class async runtime, typing support, and rich AI ecosystem. |
| **Data Validation** | **Pydantic v2** | `>=2.7.0` | Schemas for Plans, Tools, Evidence, and Reports | High-performance Rust-backed validation. Guarantees strict type safety and schema conformance for LLM inputs/outputs. |
| **Settings Management** | **pydantic-settings** | `>=2.2.0` | App configuration and `.env` parsing | Validates API credentials at startup with clean error messages rather than cryptic runtime crashes. |
| **LLM Client / SDK** | **OpenAI Python SDK** | `>=1.20.0` | Client for Groq OpenAI-compatible API | Groq exposes standard OpenAI-compatible endpoints (`/chat/completions`). Using `openai` avoids proprietary vendor lock-in. |
| **LLM Provider** | **Groq API** | `Cloud` | Free-tier high-speed LLM inference (`openai/gpt-oss-120b`) | Extremely low latency (200–400 tokens/sec) and generous free developer tier. Makes agent iteration fast with zero cost. |
| **Search Provider** | **Tavily AI Search** | `Cloud` | External web search & snippet retrieval | Specifically designed for AI agents: returns clean, extracted page content rather than noisy SEO links (1,000 free queries/mo). |
| **Search Fallback** | **DuckDuckGo Lite** | `Built-in HTTP` | Keyless search alternative | Zero-configuration fallback if Tavily credentials are missing or monthly quota is exhausted. |
| **Web Fetching** | **HTTPX** | `>=0.27.0` | Async HTTP client for web page fetching | Supports async/await, HTTP/2, connection pooling, and granular timeout configurations; far more modern and robust than `requests`. |
| **HTML Parsing** | **BeautifulSoup4** | `>=4.12.0` | HTML content cleaning and tag stripping | Fast, reliable parsing of arbitrary web HTML; strips `<script>`, `<style>`, navigation, and header noise to preserve clean text. |
| **Document Generation** | **ReportLab** | `>=4.0.0` | PDF report compilation (`Platypus`) | Pure-Python PDF builder without heavy external binary dependencies (e.g. `wkhtmltopdf`, Chrome, or Playwright). Fast and portable. |
| **CLI Framework** | **Typer** | `>=0.12.0` | Command-line interface and argument parsing | Built on Click with Python type hints. Generates automatic `--help` flags, type validation, and clean CLI structure. |
| **Terminal Output** | **Rich** | `>=13.7.0` | Terminal formatting, colors, and tables | Renders publication-grade tables, status spinners, and progress logs during research execution. |
| **Environment Loader** | **python-dotenv** | `>=1.0.0` | Local `.env` secret injection | Safely loads API keys from local `.env` files outside version control. |
| **Test Framework** | **Pytest** | `>=8.0.0` | Unit & integration testing | Standard Python test runner. Supports parameterization, fixtures, and assertions. |
| **Async Testing** | **pytest-asyncio** | `>=0.23.0` | Testing asynchronous agent tools and graphs | Allows native `async def test_*` functions for testing async tools and agent graphs. |
| **Safe Mathematics** | **Python `ast`** | `Built-in` | Sandboxed arithmetic evaluation | Evaluates mathematical expressions using an Abstract Syntax Tree. Prevents arbitrary code execution vulnerabilities caused by `eval()`. |
| **Concurrency Control** | **Python `asyncio`** | `Built-in` | Parallel URL gathering with `Semaphore` | Implements bounded concurrency (`max_concurrency=4`) for fetching multiple URLs simultaneously without overwhelming servers. |
| **Deduplication** | **Python `hashlib`** | `Built-in` | Exact content SHA-256 fingerprinting | Computes cryptographic text digests to catch and reject duplicate articles and copy-pasted content with zero external overhead. |
| **URL Normalization** | **Python `urllib.parse`** | `Built-in` | URL sanitation and tracking removal | Strips tracking query parameters (`utm_*`, `fbclid`, `ref`), fragments (`#`), and trailing slashes to eliminate duplicate web sources. |
| **Search Memory** | **Python `json` + `pathlib`** | `Built-in` | Persistent research session store | Lightweight persistence in `data/search_history.json`. Avoids the operational overhead of a database while providing search reuse. |

---

## 2. Feature-by-Feature Testing Guide & Runnable Commands

You can test every single capability of the agent directly from your terminal.

### Feature 1: CLI Interface & Options
Verify the CLI argument parser, option flags, and default configurations.
```bash
python -m app.main --help
```
* **Expected Result:** Typer outputs formatted help text detailing `--goal`, `--mock`, `--demo-failure`, and optional flags.

---

### Feature 2: Deterministic Mock Mode (Offline / Zero-Cost)
Tests the complete end-to-end agent graph completely offline without requiring any API keys or internet connection.
```bash
python -m app.main --mock --goal "Analyze the current competitive landscape for AI agent frameworks"
```
* **Expected Result:**
  * Agent creates a structured research plan.
  * Search and fetch tools return pre-configured mock fixtures.
  * Evidence is extracted, deduplicated, and synthesized.
  * Outputs generated: `output/report.md`, `output/report.json`, and `output/report.pdf`.

---

### Feature 3: Live End-to-End Research (Groq + Tavily)
Tests live web search, real-time scraping, deduplication, and synthesis using Groq and Tavily.
```bash
python -m app.main --goal "Analyze the current competitive landscape for AI agent frameworks"
```
* **Expected Result:**
  * Terminal displays live execution steps: planning, Tavily search queries, page fetches, relevance filtering, and report generation.
  * Report files are created or updated in `output/`.

---

### Feature 4: Arbitrary Multi-Domain Research Queries
Verifies that the agent is **general-purpose** and not hardcoded to AI frameworks.

**Scenario A: Technical Architecture Comparison**
```bash
python -m app.main --goal "Compare FastAPI and Spring Boot for building production microservices"
```

**Scenario B: Technology Deep-Dive**
```bash
python -m app.main --goal "Research recent developments in agentic AI and summarize key findings"
```
* **Expected Result:** The agent adapts its research strategy, dynamically chooses source types, and generates comprehensive, grounded findings tailored to the specific query.

---

### Feature 5: Failure Recovery & Adaptive Replanning
Demonstrates how the agent autonomously detects tool failures (simulated network timeout/HTTP 500) and recovers without crashing.
```bash
python -m app.main --goal "Analyze AI agent frameworks" --demo-failure
```
* **Expected Result:**
  * Terminal shows a warning on the first tool call:
    `WARNING Tool fetch failed: Simulated HTTP connection timeout`
  * The agent detects the failure and initiates exponential backoff:
    `INFO Retrying fetch_url (attempt 1/2)...`
  * The retry succeeds or triggers an adaptive replan, and research finishes successfully.
  * In the final summary: `Failures Detected: 1`, `Recoveries Performed: 1`.

---

### Feature 6: Relevance Filtering & Boilerplate Stripping
Tests that cookie banners, navigation menus, and off-topic paragraphs are discarded while goal-aligned evidence is retained.
```bash
python -m pytest tests/unit/test_relevance.py -v
```
* **Expected Result:** All 4 relevance tests pass:
  * `test_relevance_filter_retains_goal_aligned_content`: Verified.
  * `test_relevance_filter_rejects_web_boilerplate`: Strips cookies, footers, headers.
  * `test_relevance_filter_rejects_off_topic_text`: Off-topic sentences discarded.
  * `test_filter_sentences_orders_by_relevance`: Highest-density sentences ranked first.

---

### Feature 7: Deduplication (URL Normalization & Content Hashing)
Tests duplicate removal across identical URLs, syndicated articles, and near-duplicate text.
```bash
python -m pytest tests/unit/test_deduplication.py -v
```
* **Expected Result:** All 5 deduplication tests pass:
  * `test_url_normalization_strips_tracking_and_slashes`: Strips `utm_source`, fragments, trailing slashes.
  * `test_content_hash_exact_duplicate_detection`: SHA-256 fingerprinting catches exact duplicates.
  * `test_jaccard_similarity_near_duplicate_detection`: Token overlap detects syndicated content.
  * `test_deduplicate_sources_preserves_highest_authority`: Keeps the highest authority domain.
  * `test_deduplicate_evidence_eliminates_duplicate_quotes`: Eliminates redundant evidence quotes.

---

### Feature 8: AST Calculator Security Sandbox
Verifies that arithmetic calculations are safe and that arbitrary code execution is strictly blocked.
```bash
python -m pytest tests/unit/test_calculator.py -v
```
* **Expected Result:** All 7 calculator tests pass:
  * Arithmetic expressions (`(120 - 45) / 2`, `25% of 800`) calculate accurately.
  * `test_calculator_security_sandbox_blocks_arbitrary_code` asserts that `__import__('os').system('...')` and file access calls raise security errors.

---

### Feature 9: Publication PDF Report Generation
Verifies that ReportLab Platypus compiles clean, multi-page PDF documents.
```bash
python -m pytest tests/unit/test_pdf_export.py -v
```
* **Expected Result:**
  * `test_pdf_export_generates_valid_pdf_file` passes.
  * Validates that `output/report.pdf` is created with valid PDF headers (`%PDF-1.4`) and non-zero byte size.

---

### Feature 10: Persistent Search Memory Store
Verifies that prior research runs are stored in `data/search_history.json` and can be retrieved.
```bash
python -m pytest tests/unit/test_search_memory.py -v
```
* **Expected Result:**
  * `test_search_memory_save_and_lookup` passes.
  * `test_search_memory_lists_recent_sessions` passes.

---

### Feature 11: Run Full Test Suite with Coverage
Runs all 36 unit and integration tests across all modules.
```bash
python -m pytest -v
```
To run with code coverage:
```bash
python -m pytest --cov=app --cov-report=term-missing
```
* **Expected Result:** `39 passed in ~4.0s` with zero failures.

---

## 3. How to Inspect Output Artifacts

After running any research goal, inspect the generated artifacts:

### 1. View Markdown Report
```bash
# On Windows
type output\report.md | more

# Or open in VS Code / default editor
code output/report.md
```
Contains:
* Executive Summary
* Research Methodology & Objective
* Key Points & Grounded Findings
* Entity Comparison Table
* Actionable Insights
* References & Sources with URLs
* Execution Audit (sources considered, deduplicated, relevance-filtered)

### 2. View Machine-Readable JSON
```bash
# Inspect JSON metadata and structure
python -c "import json; data=json.load(open('output/report.json')); print('Goal:', data['metadata']['goal']); print('Sources:', len(data['sources'])); print('Key Points:', len(data['key_points']))"
```

### 3. View Generated PDF
Open `output/report.pdf` in any PDF reader or browser.
```bash
# Windows
start output\report.pdf
```

### 4. View Search History Memory
```bash
# Inspect saved sessions
python -c "import json; hist=json.load(open('data/search_history.json')); print(f'Stored sessions: {len(hist)}'); [print('-', s['goal'], f'({s[\"timestamp\"]})') for s in hist[-3:]]"
```
