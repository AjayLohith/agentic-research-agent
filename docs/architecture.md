# System Architecture & Technical Specifications

## 1. Architectural Philosophy

The **Autonomous Research & Competitive Intelligence Agent** is designed around a single guiding principle:
> **Deterministic scaffolding handles safety, limits, state tracking, and protocol execution; the LLM handles dynamic reasoning, tool selection, and evidence synthesis.**

Rather than implementing a hardcoded workflow (`search -> fetch -> summarize`), the system implements an explicit, inspectable state machine (`ResearchAgentGraph`) where each execution step is determined by the agent's observation history and goals.

---

## 2. Mermaid State & Orchestration Diagram

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

---

## 3. Core Architectural Subsystems

### 3.1. Agent State Machine (`app/agent/graph.py` & `app/agent/state.py`)
Execution is governed by the `ResearchAgentGraph` which updates an immutable, fully serializable `AgentState` object:
* `goal`: The natural language objective.
* `plan`: Structured `ResearchPlan` decomposed dynamically by the LLM.
* `current_step`: Active `PlanStep` under execution.
* `completed_steps` & `pending_steps`: Explicit task queue.
* `observations`: Chronological register of tool outputs.
* `sources`: Classified web endpoints with metadata and authority scores.
* `evidence`: Verifiable factual claims linked to source URLs and direct quotes.
* `tool_history`: Complete invocation logs with millisecond timings.
* `failures` & `retries`: Explicit audit logs of network or tool exceptions.
* `calculations`: Safe arithmetic metrics calculated during the run.

### 3.2. Pluggable Tool Abstraction (`app/tools/`)
Every tool adheres to `BaseTool`, defining strict Pydantic input and output schemas:
1. **`search_web` (`SearchWebTool`)**: Retrieves public web links, titles, snippets, and domains via pluggable providers (DuckDuckGo, Tavily, or Mock).
2. **`fetch_url` (`FetchUrlTool`)**: Fetches HTML via `httpx`, removes scripts/styles via `BeautifulSoup`, enforces character length limits (`MAX_FETCH_CONTENT_LENGTH`), and normalizes text.
3. **`calculator` (`SafeCalculator`)**: Evaluates arithmetic expressions using an Abstract Syntax Tree (AST) evaluator without `eval()` or `exec()`.

### 3.3. Failure Recovery & Adaptive Replanning (`app/agent/replanner.py`)
When a tool invocation fails (e.g. simulated timeout or remote HTTP 500):
1. **Immediate Retry Phase**: Retries the action up to `MAX_RETRIES_PER_TOOL` (default: 2) with backoff.
2. **Replanning Phase**: If retries are exhausted, the failure context is evaluated by `AutonomousReplanner`, which dynamically introduces fallback search steps or alternative documentation mirrors.

### 3.4. Evidence Grounding & Explainable Confidence (`app/services/evidence_service.py`)
Confidence is not a hallucinated number. It is calculated deterministically via a multi-factor weighting formula:
$$\text{Confidence} = (A \times 0.40) + (D \times 0.35) + (I \times 0.25) - P_{\text{conflict}}$$
* $A$ (**Source Authority**): 0.40–0.95 based on domain tier (official docs, academic, reputable pub, community).
* $D$ (**Evidence Directness**): 0.95 for verbatim textual quotes, 0.75 for summarized claims.
* $I$ (**Independent Sources**): 0.65–0.95 depending on corroboration across distinct domains.
* $P_{\text{conflict}}$ (**Conflict Penalty**): 0.15 deduction if contradictory claims exist between sources.

---

## 4. Security & Prompt Injection Defenses
* **Untrusted Web Data Separation**: Web content is treated strictly as passive data inside labeled delimitations (`FETCHED UNTRUSTED WEB DATA`), never as execution instructions.
* **AST Mathematical Sandbox**: Code execution is prohibited; the calculator only accepts binary arithmetic AST operators (`+`, `-`, `*`, `/`, `%`, `**`).
* **Secret Redaction**: Structured JSON logging automatically intercepts and masks API tokens and authorization headers.
