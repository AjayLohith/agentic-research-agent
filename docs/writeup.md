# Autonomous Research Agent — Architectural Write-up

## 1. Problem
Traditional LLM search pipelines rely on naive sequences (e.g. single-query search followed by unfiltered context dumping). This leads to three severe production failure modes:
1. **Hallucination & Provenance Gaps:** Models fabricate citations or present unverified web opinions as facts.
2. **Context Poisoning & Token Overflow:** Raw web pages are filled with boilerplate (cookie policies, navigation bars, newsletters) and duplicated syndicated articles that exceed model rate limits.
3. **Pipeline Fragility:** A single HTTP 404, 429 rate limit, or transient timeout crashes the entire execution without recourse.

## 2. Approach
The **Autonomous Research & Competitive Intelligence Agent** addresses these challenges through an **evidence-first, state-machine architecture**. Instead of treating the LLM as an unconstrained web surfer, the system pairs deterministic engineering controls (URL normalization, SHA-256 fingerprinting, Jaccard near-duplicate detection, and AST mathematical evaluation) with adaptive LLM cognition (goal decomposition, autonomous source selection, and grounded semantic synthesis).

## 3. Architecture
The agent runs an explicit state machine graph with typed node transitions:
```text
User Goal
   ↓
Autonomous Planner (Decomposition & Source Strategy Selection)
   ↓
Parallel / Multi-Tool Execution (Tavily Search, HTTPX Fetch, Safe AST Math)
   ↓
Relevance Filtering (Drops web boilerplate, cookies, off-topic sentences)
   ↓
Deduplication Engine (URL normalization + SHA-256 / Jaccard fingerprinting)
   ↓
Evidence Register (Verbatim quotes, source provenance, confidence scoring)
   ↓
Autonomous Recovery Loop (Retry with backoff → Replanning & Source Pivoting)
   ↓
Compact Evidence Packaging & Grounded LLM Synthesis
   ↓
Artifact Export (Markdown, Pydantic JSON, ReportLab PDF, Search Memory)
```

## 4. Autonomous Behavior & Source Selection
The agent accepts arbitrary natural-language research topics without domain hardcoding. During the planning phase, the agent inspects the topic's domain to formulate an **Autonomous Source Strategy**:
- *Technical & Developer Topics:* Targets official documentation, GitHub repositories, and verifiable benchmark suites.
- *Enterprise & Market Topics:* Targets official corporate portals, regulatory filings, and reputable industry publications.
- *Research & Academic Topics:* Targets arXiv preprints, technical specifications, and primary documentation.

## 5. Relevance Filtering & Deduplication
To maintain token efficiency and prevent Groq free-tier token exhaustion (8,000 TPM limit):
- **Relevance Filtering (`RelevanceFilter`):** Evaluates extracted text candidates against the research objective. Automatically drops cookie notices, navigation headers, and off-topic claims, scoring semantic alignment before evidence acceptance.
- **Two-Tier Deduplication (`DeduplicationService`):**
  - *URL-Level:* Strips tracking parameters (`utm_*`, `ref`, `source`), fragments, and normalizes paths.
  - *Content-Level:* Computes SHA-256 fingerprints of normalized text to eliminate exact duplicates and applies token-level Jaccard similarity to reject near-identical syndicated articles.

## 6. Evidence Grounding & Explainable Confidence
Every finding maps directly to a verified source URL and a verbatim quote. Confidence is computed through a deterministic mathematical formula rather than LLM guesswork:
$$\text{Confidence} = (\text{Authority} \times 0.40) + (\text{Directness} \times 0.35) + (\text{Independent Corroboration} \times 0.25) - \text{Conflict Penalty}$$

## 7. Failure Detection & Autonomous Recovery
The system handles transient network errors and rate limits via a two-tiered recovery strategy:
1. *Immediate Backoff:* Retries transient timeouts or HTTP 429s with exponential backoff and `Retry-After` header inspection.
2. *Adaptive Replanning:* If a tool or URL fails permanently (e.g., HTTP 404), the `AutonomousReplanner` catches the error, marks the step, and dynamically introduces alternative discovery steps.

## 8. Key Design Decisions
- **Custom State Graph over Heavy Black-Box Frameworks:** Provides complete visibility into state transitions, retry budgets, and observation logs without hidden reasoning chains.
- **Safe AST Calculator:** Uses Python's AST parser to evaluate arithmetic (`+`, `-`, `*`, `/`, `%`, `**`), completely blocking arbitrary code execution or `eval()` exploits.
- **Multi-Format Export & Search Memory:** Exports publication-ready Markdown (`report.md`), validated JSON (`report.json`), and formatted PDF (`report.pdf`), while preserving session history in `data/search_history.json`.

## 9. Limitations & Production Roadmap
- *Client-Side SPAs:* The HTTPX/BeautifulSoup fetch tool cannot execute client-side JavaScript (e.g. heavy React apps); integrating Playwright would solve this for SPA-only sites.
- *Free-Tier Quotas:* Bounded by Groq requests-per-minute (RPM) limits and Tavily's 1,000 monthly credits.
- *Production Enhancements:* Introduce persistent vector indices (Qdrant/Milvus) for multi-document semantic search and distributed async task queues (Temporal) for massive parallel crawls.
