# System Architecture & Technical Specifications

## 1. Architectural Philosophy

The **Autonomous Research & Competitive Intelligence Agent** is designed around a free-first developer philosophy:
> **Deterministic scaffolding handles safety, limits, state tracking, and protocol execution; the LLM handles dynamic reasoning, tool selection, and evidence synthesis.**

Rather than implementing a hardcoded workflow (`search -> fetch -> summarize`), the system implements an explicit, inspectable state machine (`ResearchAgentGraph`) using free-tier services by default (Groq Llama-3.3-70b and Tavily Search).

---

## 2. Mermaid State & Orchestration Diagram

```mermaid
flowchart TD
    subgraph Input_Layer ["Input & Goal Deconstruction"]
        UG["User Research Goal\n(Natural Language)"] --> GV["Input Validator &\nStartup Config Check"]
        GV --> AP["Autonomous Planner\n(Decomposition into ResearchPlan)"]
        AP -->|Structured Plan| AG["Agent Controller\n(ResearchAgentGraph)"]
    end

    subgraph Orchestration_Layer ["Autonomous Execution Loop"]
        AG --> SA["Select Next Action\n(Context & State Aware)"]
        SA --> LD{"Loop Detected\nor Budget Exceeded?"}
        LD -->|Yes| PI["Pivot Strategy /\nRefine Query"]
        PI --> SA
        LD -->|No| TC["Tool Controller\n& Schema Validation"]
    end

    subgraph Tool_Ecosystem ["Pluggable Tool Suite"]
        TC -->|Query| ST["search_web\n(Tavily Default / DuckDuckGo / In-Memory Cache)"]
        TC -->|URL| FT["fetch_url\n(HTTPX / BeautifulSoup / Smart Truncate)"]
        TC -->|Arithmetic| CT["calculator\n(Safe AST Math Evaluator)"]
    end

    subgraph LLM_Layer ["LLM Provider Abstraction"]
        AP -.-> LLM["LLM Provider\n(Groq Llama-3.3-70b Default / Mock)"]
        SA -.-> LLM
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
        CS --> AS["Autonomous Synthesizer\n(Grounded Report Generation)"]
        AS --> SR["Structured ResearchReport\n(Pydantic Model)"]
        SR --> MD["output/report.md\n(Publication Markdown)"]
        SR --> JS["output/report.json\n(Validated JSON Artifact)"]
        SR --> LG["output/sample_run.log\n(Structured Trace Log)"]
    end
```

---

## 3. Core Architectural Subsystems

### 3.1. Agent State Machine (`app/agent/graph.py` & `app/agent/state.py`)
Execution is governed by the `ResearchAgentGraph` which updates an immutable, fully serializable `AgentState` object:
* `goal`: The natural language objective.
* `plan`: Structured `ResearchPlan` decomposed dynamically by the LLM.
* `current_step`: Active `PlanStep` under execution.
* `completed_steps` & `pending_steps`: Explicit task queue.
* `observations`: Chronological register of tool outputs.
* `sources`: Normalized web endpoints with authority classifications and deduplication.
* `evidence`: Verifiable factual claims linked to source URLs and direct quotes.
* `tool_history`: Complete invocation logs with millisecond timings.
* `failures` & `retries`: Explicit audit logs of network or tool exceptions.
* `calculations`: Safe arithmetic metrics calculated during the run.

### 3.2. Free-First Provider Abstractions (`app/providers/`)
* **LLM Provider (`app/providers/llm/`):** Defaults to **Groq** via OpenAI-compatible endpoints (`https://api.groq.com/openai/v1`). Features rate-limit detection with `Retry-After` backoff, and robust JSON schema repair. Includes `MockLLMProvider` for zero-cost offline testing.
* **Search Provider (`app/providers/search/`):** Defaults to **Tavily** (`https://api.tavily.com/search`) with in-memory query caching to preserve free-tier credits. Supports keyless DuckDuckGo Lite as an alternative.

### 3.3. Pluggable Tool Suite (`app/tools/`)
Every tool adheres to `BaseTool`, defining strict Pydantic input and output schemas:
1. **`search_web` (`SearchWebTool`)**: Retrieves public web links, titles, snippets, and domains with per-session query caching.
2. **`fetch_url` (`FetchUrlTool`)**: Fetches HTML via `httpx`, removes scripts/styles via `BeautifulSoup`, normalizes text, and truncates at natural sentence boundaries (`MAX_FETCH_CONTENT_LENGTH`).
3. **`calculator` (`SafeCalculator`)**: Evaluates arithmetic expressions using an Abstract Syntax Tree (AST) evaluator without `eval()` or `exec()`.

### 3.4. Failure Recovery & Adaptive Replanning (`app/agent/recovery.py`)
When a tool invocation fails (e.g. simulated timeout or remote HTTP 500):
1. **Immediate Retry Phase**: Retries the action up to `MAX_RETRIES_PER_TOOL` (default: 2) with backoff.
2. **Replanning Phase**: If retries are exhausted, the failure context is evaluated by `AutonomousReplanner`, which dynamically introduces fallback search steps or alternative documentation mirrors.

### 3.5. Evidence Grounding & Explainable Confidence (`app/services/evidence_service.py`)
Confidence is calculated deterministically via a multi-factor weighting formula:
$$\text{Confidence} = (A \times 0.40) + (D \times 0.35) + (I \times 0.25) - P_{\text{conflict}}$$
* $A$ (**Source Authority**): 0.40–0.95 based on domain tier.
* $D$ (**Evidence Directness**): 0.95 for verbatim textual quotes, 0.75 for summarized claims.
* $I$ (**Independent Sources**): 0.65–0.95 depending on corroboration across distinct domains.
* $P_{\text{conflict}}$ (**Conflict Penalty**): 0.15 deduction if contradictory claims exist between sources.

---

## 4. Security & Safety Defenses
* **Untrusted Web Data Separation**: Web content is treated strictly as passive data inside labeled delimitations (`EXTERNAL SOURCE CONTENT`), never as execution instructions.
* **AST Mathematical Sandbox**: Code execution is prohibited; the calculator only accepts binary arithmetic AST operators (`+`, `-`, `*`, `/`, `%`, `**`).
* **Secret Redaction**: Structured JSON logging automatically intercepts and masks API tokens and authorization headers.
