# Autonomous Research Agent — Design Decisions & Trade-Offs

## 1. Problem Statement
Automated competitive intelligence and technical research require synthesizing dynamic public data across unstructured web pages, technical documentation, and quantitative benchmarks. Traditional LLM prompting suffers from three fatal flaws: **hallucination of non-existent facts/URLs**, **stale pre-training cutoff**, and **inability to recover when network requests fail**. This project designs and implements an autonomous agent that plans, verifies, calculates, recovers, and grounds research in verifiable evidence.

## 2. Architectural Design & Orchestration
Rather than introducing heavy agent abstractions (CrewAI, AutoGen) that obscure state transitions, this solution implements an explicit, typed state graph (`ResearchAgentGraph`).
* **Explicit State Transitions:** The loop moves through discrete stages: `GOAL` $\rightarrow$ `PLAN` $\rightarrow$ `SELECT ACTION` $\rightarrow$ `TOOL EXECUTION` $\rightarrow$ `OBSERVE` $\rightarrow$ `EVALUATE/REPLAN` $\rightarrow$ `EVIDENCE VALIDATION` $\rightarrow$ `SYNTHESIS`.
* **Provider Abstraction:** Decoupled interfaces (`LLMProvider`, `SearchProvider`) allow swapping between OpenAI, Ollama, Groq, DuckDuckGo, Tavily, and offline Mock fixtures with zero agent modifications.

## 3. Genuine Agentic Behavior vs. Hardcoded Workflows
The agent avoids static scripted sequences (e.g. `search() -> fetch() -> summarize()`). Instead:
1. **Dynamic Decomposition:** The LLM inspects the unique goal to generate custom plan steps, assumptions, and constraints.
2. **Context-Aware Tool Selection:** At every cycle, the agent determines the next action based on prior observations.
3. **Execution Budgets & Loop Detection:** Protects against runaway token burn by enforcing step limits and intercepting repeated identical tool calls.

## 4. Multi-Tool Ecosystem & Safety
* **`search_web`:** Retrieves public sources without mandatory paid API keys (DuckDuckGo Lite), with Tavily support.
* **`fetch_url`:** Strips scripts, navigation chrome, and styles using BeautifulSoup; enforces content length limits (`MAX_FETCH_CONTENT_LENGTH`).
* **`calculator`:** Implements an AST evaluator for `+`, `-`, `*`, `/`, `%`, `**`. Strictly rejects function invocations, imports, and variables to prevent arbitrary code execution vulnerabilities.

## 5. Failure Detection & Autonomous Recovery
Real-world networks are unreliable. The agent demonstrates resilience through a two-tiered recovery strategy:
1. **Transient Retries:** Failed calls (e.g. timeouts, 500s) are retried with exponential backoff up to `MAX_RETRIES_PER_TOOL`.
2. **Adaptive Replanning:** When retries fail, `AutonomousReplanner` analyzes the failure reason, discovers alternative authoritative mirrors, or reformulates search queries without crashing.
*A dedicated failure injection mode (`--demo-failure` or `DEMO_FAILURE_MODE=timeout`) deliberately triggers a first-attempt timeout to prove autonomous recovery in live demonstrations.*

## 6. Evidence Grounding & Explainable Confidence
To eliminate hallucination:
* Every factual claim must be backed by a verbatim excerpt, classified source URL, and authority score.
* Confidence is not an arbitrary LLM estimate; it is calculated deterministically:
  $$\text{Confidence} = (\text{Authority} \times 0.40) + (\text{Directness} \times 0.35) + (\text{Corroboration} \times 0.25) - \text{Conflict Penalty}$$
* Conflicts between disagreeing sources are detected, presented transparently, and resolved methodologically.

## 7. Limitations & Production Roadmap
* **Current Limitations:** Web scraping is bound by robot exclusions and anti-bot challenges; JS-rendered single-page apps (SPAs) require headless browser integration.
* **Production Improvements:** Distributed worker queues (Celery/Temporal), persistent vector memory stores, real-time OpenTelemetry tracing, and human-in-the-loop checkpoints for critical strategic assessments.
