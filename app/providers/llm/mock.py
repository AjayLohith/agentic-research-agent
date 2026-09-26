import re
from typing import Optional, Type, List
from pydantic import BaseModel

from app.providers.llm.base import LLMProvider, T


class MockLLMProvider(LLMProvider):
    """
    Deterministic mock provider for offline testing and reviewer evaluations.
    Generates query-driven structured Pydantic models matching goal inputs without external API calls.
    """

    def __init__(self, model_name: str = "mock-groq-llama"):
        self.model_name = model_name

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2
    ) -> str:
        goal = self._extract_goal_from_prompt(prompt)
        return f"Deterministic research reasoning completed for: {goal}"

    async def structured_output(
        self,
        schema: Type[T],
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.1
    ) -> T:
        schema_name = schema.__name__

        if schema_name == "ResearchPlan":
            return self._plan(prompt, schema)
        elif schema_name == "ReplanningDecision":
            return self._replanning(prompt, schema)
        elif schema_name == "ResearchReport":
            return self._report(prompt, schema)
        elif schema_name == "ToolCall":
            return self._tool_call(prompt, schema)

        return schema.model_validate({})

    def _extract_goal_from_prompt(self, prompt: str) -> str:
        """Extracts the active user research goal from the prompt text."""
        patterns = [
            r"CURRENT RESEARCH GOAL:\s*\n([^\n]+)",
            r"Original user goal:\s*\n([^\n]+)",
            r"GOAL:\s*\n([^\n]+)",
            r"goal:\s*'([^']+)'",
            r"goal:\s*\"([^\"]+)\"",
            r"for goal:\s*'([^']+)'",
        ]
        for pat in patterns:
            m = re.search(pat, prompt, re.IGNORECASE)
            if m and m.group(1).strip():
                return m.group(1).strip()

        for line in prompt.split("\n"):
            line_str = line.strip()
            if line_str.lower().startswith("goal:") and len(line_str) > 6:
                return line_str[5:].strip()

        return "Analyze technology architecture and capabilities"

    def _extract_subjects(self, goal: str) -> List[str]:
        """Identifies candidate subjects/entities directly from the goal string."""
        g_lower = goal.lower()
        if "gpt 6" in g_lower or "astra" in g_lower:
            return ["GPT 6 Astra", "Agent Orchestration"]
        elif "postgres" in g_lower or "mongo" in g_lower:
            return ["PostgreSQL", "MongoDB"]
        elif "rag" in g_lower or "retrieval augmented" in g_lower or "retrieval-augmented" in g_lower:
            return ["Dense Vector Retrieval", "Hybrid Search RAG"]
        elif "fastapi" in g_lower or "spring" in g_lower:
            return ["FastAPI", "Spring Boot"]
        elif "langgraph" in g_lower or "crewai" in g_lower or "autogen" in g_lower or ("agent" in g_lower and "framework" in g_lower):
            return ["LangGraph", "CrewAI", "AutoGen"]

        # Split comparison queries (e.g. "Kafka versus RabbitMQ" or "Postgres vs MySQL")
        vs_split = re.split(r"(?i)\s+(?:versus|vs\.?)\s+", goal)
        if len(vs_split) >= 2:
            def _clean_side(text: str) -> str:
                c = re.sub(r"(?i)\b(analyze|compare|research|the|current|landscape|for|and|in|of|latest|developments|identify|major|players|building|production|an|a|to)\b", " ", text)
                words = [w.strip() for w in c.split() if len(w.strip()) > 1]
                return " ".join(words[:2]).title() if words else "System"
            side1 = _clean_side(vs_split[0])
            side2 = _clean_side(vs_split[1])
            return [side1, side2]

        cleaned = re.sub(
            r"(?i)\b(analyze|compare|research|the|current|landscape|for|versus|vs|and|in|of|latest|developments|identify|major|players|building|production|an|a|to)\b",
            " ",
            goal
        )
        words = [w.strip() for w in cleaned.split() if len(w.strip()) > 1]
        if len(words) >= 2:
            return [words[0].title(), words[1].title()]
        elif len(words) == 1:
            return [words[0].title(), f"{words[0].title()} Architecture"]
        return ["Primary Architecture", "Secondary Component"]

    def _plan(self, prompt: str, schema: Type[T]) -> T:
        goal = self._extract_goal_from_prompt(prompt)
        subjects = self._extract_subjects(goal)
        subj_str = ", ".join(subjects)

        g_lower = goal.lower()
        if "gpt 6" in g_lower or "astra" in g_lower:
            strategy = "Official frontier AI model research publications, architectural previews, and autonomous agent benchmarks."
            source_types = ["research preview", "benchmark reports", "technical specifications"]
        elif "postgres" in g_lower or "mongo" in g_lower:
            strategy = "Official database documentation, ACID transaction specifications, and verified throughput benchmarks."
            source_types = ["official documentation", "database engine specs", "performance benchmarks"]
        elif "rag" in g_lower or "retrieval" in g_lower:
            strategy = "Peer-reviewed information retrieval papers, vector database documentation, and hybrid search evaluations."
            source_types = ["research papers", "vector database docs", "benchmarks"]
        elif "fastapi" in g_lower or "spring" in g_lower:
            strategy = "Official web framework documentation, ASGI/Virtual Thread specifications, and verified concurrency benchmarks."
            source_types = ["official documentation", "runtime specifications", "benchmarks"]
        else:
            strategy = f"Authoritative documentation, official engineering specifications, and verified benchmarks for {subj_str}."
            source_types = ["official documentation", "technical specifications", "empirical benchmarks"]

        steps = [
            {
                "id": 1,
                "description": f"Identify core architectural principles, features, and official documentation for {subj_str}.",
                "purpose": f"Establish foundational technical paradigms and discover primary documentation URLs.",
                "expected_output": f"List of primary entities and documentation endpoints for {subj_str}.",
                "preferred_tools": ["search_web", "fetch_url"],
                "status": "pending"
            },
            {
                "id": 2,
                "description": f"Retrieve and analyze verified technical documentation and architecture for {subjects[0]}.",
                "purpose": f"Extract concrete capabilities, design patterns, and evidence for {subjects[0]}.",
                "expected_output": f"Technical specifications and grounded evidence for {subjects[0]}.",
                "preferred_tools": ["fetch_url", "search_web"],
                "status": "pending"
            },
            {
                "id": 3,
                "description": f"Retrieve and analyze verified technical documentation and architecture for {subjects[1] if len(subjects) > 1 else 'ecosystem integrations'}.",
                "purpose": f"Extract concrete capabilities, operational tradeoffs, and integration patterns.",
                "expected_output": f"Technical specifications and grounded evidence.",
                "preferred_tools": ["fetch_url", "search_web"],
                "status": "pending"
            },
            {
                "id": 4,
                "description": f"Calculate quantitative comparison ratios and capability coverage metrics for {subj_str}.",
                "purpose": f"Compute objective quantitative metrics across evaluated subjects.",
                "expected_output": f"Derived quantitative metrics and AST calculation records.",
                "preferred_tools": ["calculator"],
                "status": "pending"
            },
            {
                "id": 5,
                "description": f"Synthesize evidence-grounded findings, operational trade-offs, and actionable recommendations for {goal.strip('.')}.",
                "purpose": f"Compile grounded intelligence report with verifiable citations answering the exact goal.",
                "expected_output": f"Final structured report answering '{goal}'.",
                "preferred_tools": ["calculator"],
                "status": "pending"
            }
        ]

        plan_dict = {
            "objective": f"Investigate and analyze {goal.strip('.')} across architecture, capabilities, and production readiness.",
            "source_strategy": strategy,
            "target_source_types": source_types,
            "assumptions": [f"Evaluation based on latest verified documentation for {subj_str}", "Production cloud deployment baseline"],
            "constraints": ["Every statement backed by verified technical documentation or benchmarks"],
            "steps": steps
        }
        return schema.model_validate(plan_dict)

    def _replanning(self, prompt: str, schema: Type[T]) -> T:
        p_lower = prompt.lower()
        if "timeout" in p_lower or "failed" in p_lower or "error" in p_lower:
            return schema.model_validate({
                "needs_replanning": True,
                "reason": "Target endpoint timed out. Switching to alternative authoritative mirror.",
                "suggested_action": "alternative_source",
                "new_steps": [
                    {
                        "id": 99,
                        "description": "Search for secondary authoritative mirror documentation.",
                        "purpose": "Recover from primary endpoint failure.",
                        "expected_output": "Alternative verified source URL.",
                        "preferred_tools": ["search_web", "fetch_url"],
                        "status": "pending"
                    }
                ],
                "step_id_to_modify": None
            })
        return schema.model_validate({
            "needs_replanning": False,
            "reason": "Step completed successfully.",
            "suggested_action": "continue",
            "new_steps": [],
            "step_id_to_modify": None
        })

    def _tool_call(self, prompt: str, schema: Type[T]) -> T:
        goal = self._extract_goal_from_prompt(prompt)
        subjects = self._extract_subjects(goal)

        step_desc = prompt.lower()
        if "current plan step" in prompt.lower():
            try:
                step_desc = prompt.lower().split("current plan step")[1].split("recent observations")[0]
            except Exception:
                step_desc = prompt.lower()

        # 1. Calculator tool call
        if re.search(r"\b(calculate|percentage|ratios?|coverage|metric)\b", step_desc):
            return schema.model_validate({
                "tool_name": "calculator",
                "arguments": {"expression": "4 / 5 * 100"},
                "rationale": f"Calculate quantitative capability coverage percentage for {', '.join(subjects)}."
            })

        # 2. Fetch URL tool call
        if "fetch" in step_desc or "retrieve" in step_desc or "inspect" in step_desc:
            target_url = None
            if "spring" in step_desc:
                target_url = "https://spring.io/projects/spring-boot"
            elif "fastapi" in step_desc:
                target_url = "https://fastapi.tiangolo.com/"
            elif "mongo" in step_desc:
                target_url = "https://www.mongodb.com/docs/"
            elif "postgres" in step_desc:
                target_url = "https://www.postgresql.org/docs/current/"
            elif "gpt 6" in step_desc or "astra" in step_desc:
                target_url = "https://openai.com/research/gpt-6-astra-preview"
            elif "rag" in step_desc or "retrieval" in step_desc:
                target_url = "https://arxiv.org/abs/2005.11401"
            elif "langgraph" in step_desc:
                target_url = "https://docs.langchain.com/langgraph/overview"
            elif "crewai" in step_desc:
                target_url = "https://docs.crewai.com/introduction"
            elif "autogen" in step_desc:
                target_url = "https://microsoft.github.io/autogen/docs/Getting-Started"
            elif "gpt 6" in goal.lower() or "astra" in goal.lower():
                target_url = "https://openai.com/research/gpt-6-astra-preview"
            elif "postgres" in goal.lower():
                target_url = "https://www.postgresql.org/docs/current/"
            elif "mongo" in goal.lower():
                target_url = "https://www.mongodb.com/docs/"
            elif "rag" in goal.lower():
                target_url = "https://arxiv.org/abs/2005.11401"
            elif "fastapi" in goal.lower():
                target_url = "https://fastapi.tiangolo.com/"
            elif "spring" in goal.lower():
                target_url = "https://spring.io/projects/spring-boot"
            else:
                slug = subjects[0].lower().replace(" ", "-")[:25]
                target_url = f"https://docs.{slug}.org/overview"

            return schema.model_validate({
                "tool_name": "fetch_url",
                "arguments": {"url": target_url},
                "rationale": f"Fetch authoritative technical documentation for {subjects[0]}."
            })

        # 3. Search Web tool call
        query = f"{' '.join(subjects)} technical architecture documentation capabilities"
        return schema.model_validate({
            "tool_name": "search_web",
            "arguments": {"query": query, "max_results": 4},
            "rationale": f"Search public documentation and benchmarks answering '{goal}'."
        })

    def _report(self, prompt: str, schema: Type[T]) -> T:
        goal = self._extract_goal_from_prompt(prompt)
        subjects = self._extract_subjects(goal)
        g_lower = goal.lower()

        if "gpt 6" in g_lower or "astra" in g_lower:
            return schema.model_validate({
                "metadata": {
                    "goal": goal,
                    "generated_at": "2026-09-26T15:00:00Z",
                    "execution_time_seconds": 2.5,
                    "agent_version": "0.1.0"
                },
                "executive_summary": (
                    f"Technical research on '{goal}' highlights major architectural advancements in GPT 6 Astra. "
                    "Engineered specifically for autonomous agent workflows, GPT 6 Astra features native cyclic reasoning buffers, "
                    "sub-second multi-modal tool calling, and active hypothesis verification. Benchmark evaluations indicate substantial "
                    "improvements in long-horizon task execution compared to prior frontier models."
                ),
                "methodology": "Autonomous goal decomposition, multi-source external search, content relevance filtering, deduplication, AST calculation, and grounded evidence synthesis.",
                "research_scope": {
                    "assumptions": ["Focus on GPT 6 Astra technical preview specifications", "Production agent orchestration environments"],
                    "constraints": ["Verified against official technical publications"]
                },
                "key_points": [
                    "GPT 6 Astra introduces built-in cyclic reasoning buffers, preventing infinite agent execution loops.",
                    "Provides native multi-modal tool orchestration with strict JSON schema compliance.",
                    "Achieves an 80% reduction in state drift over long-horizon autonomous tasks."
                ],
                "key_findings": [
                    {
                        "title": "Native Agentic Reasoning Loop",
                        "summary": "GPT 6 Astra incorporates stateful reasoning directly into its inference pipeline, reducing reliance on external scaffolding.",
                        "category": "Architecture",
                        "supporting_evidence_ids": ["ev-1"],
                        "confidence": 0.96
                    },
                    {
                        "title": "Tool Calling Latency & Reliability",
                        "summary": "Benchmarking demonstrates sub-100ms tool dispatch with verifiable schema adherence across parallel function calls.",
                        "category": "Performance",
                        "supporting_evidence_ids": ["ev-2"],
                        "confidence": 0.93
                    }
                ],
                "entities": [
                    {
                        "name": "GPT 6 Astra",
                        "category": "Frontier AI Agent Model",
                        "description": "Frontier multimodal reasoning model optimized for autonomous agent control loops.",
                        "key_capabilities": ["Stateful reasoning buffers", "Multi-modal tool calling", "Verification engine"],
                        "strengths": ["Reduced planning drift", "Low-latency tool execution"],
                        "tradeoffs": ["Requires specialized prompt schemas for optimal memory persistence"],
                        "authoritative_source_url": "https://openai.com/research/gpt-6-astra-preview",
                        "confidence": 0.96
                    }
                ],
                "comparison": [
                    {
                        "dimension": "Autonomous Horizon",
                        "analysis": "GPT 6 Astra maintains coherent execution across >50 consecutive tool actions without context degradation.",
                        "entity_ratings_or_notes": {"GPT 6 Astra": "Long Horizon (>50 actions)"}
                    }
                ],
                "actionable_insights": [
                    "Adopt GPT 6 Astra reasoning endpoints for multi-step agent workflows requiring complex tool dependencies.",
                    "Implement state checkpointing alongside native reasoning buffers for mission-critical recovery.",
                    "Benchmark token efficiency under representative production agent prompts."
                ],
                "evidence": [
                    {
                        "id": "ev-1",
                        "claim": "GPT 6 Astra represents next-generation frontier intelligence engineered for autonomous agent systems.",
                        "supporting_quote_or_excerpt": "GPT 6 Astra represents next-generation frontier intelligence engineered for autonomous agent systems with native cyclic reasoning buffers.",
                        "source_url": "https://openai.com/research/gpt-6-astra-preview",
                        "source_title": "GPT 6 Astra Technical Preview",
                        "source_type": "official documentation",
                        "confidence": 0.96,
                        "confidence_factors": {"source_authority": 0.98, "evidence_directness": 0.95, "independent_sources": 0.90, "conflict_penalty": 0.0, "overall": 0.96},
                        "entity_name": "GPT 6 Astra"
                    }
                ],
                "calculations": [
                    {
                        "description": "Autonomous Capability Benchmark Score",
                        "expression": "4 / 5 * 100",
                        "result": 80.0,
                        "interpretation": "GPT 6 Astra achieves 80% coverage on standardized autonomous execution benchmarks."
                    }
                ],
                "conflicts": [],
                "limitations": [
                    {
                        "factor": "Preview Availability",
                        "impact": "Production rollout is gated behind technical preview access tiers.",
                        "mitigation_or_note": "Evaluated against authoritative preview documentation and public evaluations."
                    }
                ],
                "sources": [
                    {
                        "url": "https://openai.com/research/gpt-6-astra-preview",
                        "title": "GPT 6 Astra: Technical Preview and Agentic Architecture",
                        "source_type": "official documentation",
                        "authority_score": 0.98,
                        "retrieved_at": "2026-09-26T15:00:00Z"
                    }
                ],
                "execution_summary": {
                    "steps_planned": 5,
                    "steps_completed": 5,
                    "tool_calls_total": 5,
                    "search_queries_executed": 2,
                    "pages_fetched": 2,
                    "calculations_performed": 1,
                    "failures_detected": 0,
                    "recoveries_performed": 0,
                    "loop_detections_triggered": 0
                },
                "confidence_summary": {"overall_confidence": "96%", "primary_source_tier": "Official Documentation"}
            })

        elif "postgres" in g_lower or "mongo" in g_lower:
            return schema.model_validate({
                "metadata": {
                    "goal": goal,
                    "generated_at": "2026-09-26T15:00:00Z",
                    "execution_time_seconds": 2.6,
                    "agent_version": "0.1.0"
                },
                "executive_summary": (
                    f"Architectural comparison for '{goal}'. PostgreSQL provides rigorous relational ACID consistency, "
                    "extensible indexing (B-Tree, GIN, GiST), and advanced JSONB operations. MongoDB offers horizontal scale-out "
                    "via automated sharding, flexible document modeling (BSON), and rapid iterative developer velocity."
                ),
                "methodology": "Autonomous goal decomposition, multi-source external search, content relevance filtering, deduplication, AST calculation, and grounded evidence synthesis.",
                "research_scope": {
                    "assumptions": ["Containerized cloud database deployments", "High-concurrency modern workloads"],
                    "constraints": ["Verified against official documentation and published benchmarks"]
                },
                "key_points": [
                    "PostgreSQL is optimal for structured data, complex relational queries, and strict transactional ACID requirements.",
                    "MongoDB excels in dynamic schema design, high-velocity ingestion, and horizontal sharding.",
                    "Modern PostgreSQL JSONB bridges document storage requirements while preserving relational integrity."
                ],
                "key_findings": [
                    {
                        "title": "Transactional Consistency vs Horizontal Partitioning",
                        "summary": "PostgreSQL provides battle-tested ACID compliance for relational schemas, whereas MongoDB prioritizes distributed sharding and document flexibility.",
                        "category": "Architecture",
                        "supporting_evidence_ids": ["ev-1"],
                        "confidence": 0.95
                    }
                ],
                "entities": [
                    {
                        "name": "PostgreSQL",
                        "category": "Relational Database Management System",
                        "description": "Open-source object-relational database with strong ACID guarantees.",
                        "key_capabilities": ["ACID compliance", "GIN/GiST indexing", "JSONB storage"],
                        "strengths": ["Data integrity", "Extensible ecosystem"],
                        "tradeoffs": ["Vertical scaling preferred over native sharding"],
                        "authoritative_source_url": "https://www.postgresql.org/docs/current/",
                        "confidence": 0.96
                    },
                    {
                        "name": "MongoDB",
                        "category": "Document NoSQL Database",
                        "description": "Distributed document database with dynamic BSON schema modeling.",
                        "key_capabilities": ["Horizontal sharding", "Replica sets", "Aggregation pipeline"],
                        "strengths": ["Rapid prototyping", "Horizontal scale-out"],
                        "tradeoffs": ["Eventual consistency tuning required for distributed multi-document writes"],
                        "authoritative_source_url": "https://www.mongodb.com/docs/",
                        "confidence": 0.94
                    }
                ],
                "comparison": [
                    {
                        "dimension": "Data Model & Schema",
                        "analysis": "PostgreSQL enforces rigid relational schemas with optional JSONB; MongoDB uses schema-free BSON documents.",
                        "entity_ratings_or_notes": {"PostgreSQL": "Relational + JSONB", "MongoDB": "Document (BSON)"}
                    }
                ],
                "actionable_insights": [
                    "Select PostgreSQL when strong financial/relational integrity and complex joins are primary architectural requirements.",
                    "Select MongoDB for real-time document stores requiring distributed horizontal scaling and flexible schema iterations.",
                    "Evaluate PostgreSQL JSONB before introducing a secondary NoSQL datastore to reduce operational complexity."
                ],
                "evidence": [
                    {
                        "id": "ev-1",
                        "claim": "PostgreSQL features full ACID transaction compliance and sophisticated query optimization.",
                        "supporting_quote_or_excerpt": "PostgreSQL is a powerful, open-source object-relational database system with full ACID transaction compliance.",
                        "source_url": "https://www.postgresql.org/docs/current/",
                        "source_title": "PostgreSQL Documentation",
                        "source_type": "official documentation",
                        "confidence": 0.96,
                        "confidence_factors": {"source_authority": 0.98, "evidence_directness": 0.95, "independent_sources": 0.90, "conflict_penalty": 0.0, "overall": 0.96},
                        "entity_name": "PostgreSQL"
                    }
                ],
                "calculations": [
                    {
                        "description": "ACID Integrity Coverage Ratio",
                        "expression": "4 / 5 * 100",
                        "result": 80.0,
                        "interpretation": "Evaluated database architectures satisfy 80% of core enterprise scaling criteria."
                    }
                ],
                "conflicts": [],
                "limitations": [
                    {
                        "factor": "Storage Engine Configuration",
                        "impact": "Throughput varies depending on write-ahead logging (WAL) and memory caching configs.",
                        "mitigation_or_note": "Evaluated under standard production container resource limits."
                    }
                ],
                "sources": [
                    {
                        "url": "https://www.postgresql.org/docs/current/",
                        "title": "PostgreSQL Documentation - Architectural Fundamentals",
                        "source_type": "official documentation",
                        "authority_score": 0.98,
                        "retrieved_at": "2026-09-26T15:00:00Z"
                    },
                    {
                        "url": "https://www.mongodb.com/docs/",
                        "title": "MongoDB Documentation - Document Model & Distributed Scaling",
                        "source_type": "official documentation",
                        "authority_score": 0.94,
                        "retrieved_at": "2026-09-26T15:00:00Z"
                    }
                ],
                "execution_summary": {
                    "steps_planned": 5,
                    "steps_completed": 5,
                    "tool_calls_total": 5,
                    "search_queries_executed": 2,
                    "pages_fetched": 2,
                    "calculations_performed": 1,
                    "failures_detected": 0,
                    "recoveries_performed": 0,
                    "loop_detections_triggered": 0
                },
                "confidence_summary": {"overall_confidence": "95%", "primary_source_tier": "Official Documentation"}
            })

        elif "fastapi" in g_lower or "spring" in g_lower:
            return schema.model_validate({
                "metadata": {
                    "goal": goal,
                    "generated_at": "2026-09-26T15:00:00Z",
                    "execution_time_seconds": 2.8,
                    "agent_version": "0.1.0"
                },
                "executive_summary": "FastAPI and Spring Boot represent two distinct architectural paradigms for production backend services. FastAPI provides extreme developer productivity, native asynchronous I/O, and automated OpenAPI documentation within the Python ecosystem. Spring Boot represents enterprise-grade Java engineering with unmatched dependency injection maturity, rigorous governance, and high-concurrency throughput via Virtual Threads (Loom).",
                "methodology": "Autonomous goal decomposition, multi-source external search, content relevance filtering, deduplication, AST calculation, and grounded evidence synthesis.",
                "research_scope": {
                    "assumptions": ["Containerized microservices", "Modern Python 3.12+ (Uvicorn) vs Java 21+ (Spring Boot 3.3+)"],
                    "constraints": ["Verified official documentation and benchmarks"]
                },
                "key_points": [
                    "FastAPI enables rapid API prototyping and native async I/O with Python type hints.",
                    "Spring Boot provides enterprise-grade governance, dependency injection, and Virtual Threads.",
                    "Throughput scaling favors Spring Boot 3 on multi-core hardware, while developer velocity favors FastAPI."
                ],
                "key_findings": [
                    {
                        "title": "Developer Velocity vs Architectural Governance",
                        "summary": "FastAPI enables faster prototyping for API-first services, while Spring Boot provides strict type safety, dependency injection, and enterprise governance.",
                        "category": "Productivity",
                        "supporting_evidence_ids": ["ev-1"],
                        "confidence": 0.94
                    }
                ],
                "entities": [
                    {
                        "name": "FastAPI",
                        "category": "Asynchronous Web Framework",
                        "description": "High-performance Python API framework based on Starlette and Pydantic.",
                        "key_capabilities": ["Native async/await", "Pydantic validation", "Auto OpenAPI docs"],
                        "strengths": ["Rapid prototyping", "AI/ML native integration"],
                        "tradeoffs": ["CPU tasks require process pooling due to Python GIL"],
                        "authoritative_source_url": "https://fastapi.tiangolo.com/",
                        "confidence": 0.95
                    },
                    {
                        "name": "Spring Boot",
                        "category": "Enterprise Java Framework",
                        "description": "Production-grade Java framework featuring auto-configuration and enterprise integration.",
                        "key_capabilities": ["Dependency Injection", "Spring Data", "Virtual Threads (Loom)"],
                        "strengths": ["Enterprise maturity", "High concurrency throughput"],
                        "tradeoffs": ["Higher initial configuration overhead"],
                        "authoritative_source_url": "https://spring.io/projects/spring-boot",
                        "confidence": 0.94
                    }
                ],
                "comparison": [
                    {
                        "dimension": "Concurrency Model",
                        "analysis": "FastAPI uses an event loop (asyncio); Spring Boot 3 uses Project Loom Virtual Threads.",
                        "entity_ratings_or_notes": {"FastAPI": "Event-loop async", "Spring Boot": "Virtual Threads"}
                    }
                ],
                "actionable_insights": [
                    "Adopt FastAPI for AI/ML service layers and teams prioritizing rapid Python delivery.",
                    "Adopt Spring Boot for core enterprise transactional services requiring strict governance.",
                    "Conduct load benchmarks with representative ASGI/JVM worker configurations."
                ],
                "evidence": [
                    {
                        "id": "ev-1",
                        "claim": "FastAPI provides automatic data validation and OpenAPI generation based on Python type hints.",
                        "supporting_quote_or_excerpt": "FastAPI is a modern, fast (high-performance), web framework for building APIs with Python based on standard Python type hints.",
                        "source_url": "https://fastapi.tiangolo.com/",
                        "source_title": "FastAPI Framework",
                        "source_type": "official documentation",
                        "confidence": 0.95,
                        "confidence_factors": {"source_authority": 0.95, "evidence_directness": 0.95, "independent_sources": 0.85, "conflict_penalty": 0.0, "overall": 0.95},
                        "entity_name": "FastAPI"
                    }
                ],
                "calculations": [
                    {
                        "description": "Developer Velocity Index (Estimated Lines of Code Factor)",
                        "expression": "120 / 350 * 100",
                        "result": 34.29,
                        "interpretation": "FastAPI requires ~34.3% of the boilerplate lines of code compared to equivalent Spring Boot REST endpoints."
                    }
                ],
                "conflicts": [],
                "limitations": [
                    {
                        "factor": "Runtime Variance",
                        "impact": "Benchmarks depend on JIT warmup and ASGI worker counts.",
                        "mitigation_or_note": "Evaluations reflect containerized microservices under standard Kubernetes limits."
                    }
                ],
                "sources": [
                    {
                        "url": "https://fastapi.tiangolo.com/",
                        "title": "FastAPI Framework Documentation",
                        "source_type": "official documentation",
                        "authority_score": 0.95,
                        "retrieved_at": "2026-09-26T15:00:00Z"
                    },
                    {
                        "url": "https://spring.io/projects/spring-boot",
                        "title": "Spring Boot Enterprise Documentation",
                        "source_type": "official documentation",
                        "authority_score": 0.93,
                        "retrieved_at": "2026-09-26T15:00:00Z"
                    }
                ],
                "execution_summary": {
                    "steps_planned": 4,
                    "steps_completed": 4,
                    "tool_calls_total": 4,
                    "search_queries_executed": 2,
                    "pages_fetched": 1,
                    "calculations_performed": 1,
                    "failures_detected": 0,
                    "recoveries_performed": 0,
                    "loop_detections_triggered": 0
                },
                "confidence_summary": {"overall_confidence": "94%", "primary_source_tier": "Official Documentation"}
            })

        elif "langgraph" in g_lower or "crewai" in g_lower or "autogen" in g_lower or ("agent" in g_lower and "framework" in g_lower and "astra" not in g_lower):
            return schema.model_validate({
                "metadata": {
                    "goal": goal,
                    "generated_at": "2026-09-26T15:00:00Z",
                    "execution_time_seconds": 3.2,
                    "agent_version": "0.1.0"
                },
                "executive_summary": "The autonomous AI agent ecosystem in 2026 has shifted toward deterministic, stateful graph architectures. LangGraph leads enterprise workflows requiring cyclic state and human-in-the-loop controls. CrewAI excels in intuitive role-playing agent orchestration and rapid prototyping. Microsoft AutoGen maintains a strong presence in conversational multi-agent research.",
                "methodology": "Autonomous goal decomposition, multi-source external search, content relevance filtering, deduplication, AST calculation, and grounded evidence synthesis.",
                "research_scope": {
                    "assumptions": ["Focus on actively maintained open-source agent frameworks in 2024-2026"],
                    "constraints": ["Every statement backed by official documentation or verified benchmarks"]
                },
                "key_points": [
                    "State graphs (LangGraph) have become the de facto enterprise standard for agent resilience.",
                    "Role-playing frameworks (CrewAI) maximize developer velocity for collaborative workflows.",
                    "Conversational patterns (AutoGen) support flexible multi-agent research simulations."
                ],
                "key_findings": [
                    {
                        "title": "State Graphs as the Production Standard",
                        "summary": "Enterprises favor graph-based state machines (LangGraph) over opaque autonomous loops due to determinism, auditability, and replayability.",
                        "category": "Architecture",
                        "supporting_evidence_ids": ["ev-1"],
                        "confidence": 0.94
                    }
                ],
                "entities": [
                    {
                        "name": "LangGraph",
                        "category": "Graph-based Agent Orchestration",
                        "description": "Library for building stateful multi-actor applications with LLMs using explicit graph computation.",
                        "key_capabilities": ["Cyclic graphs", "State checkpointing", "Human-in-the-loop interruption", "Streaming"],
                        "strengths": ["Deterministic control", "Production-grade resilience"],
                        "tradeoffs": ["Requires explicit state schema management"],
                        "authoritative_source_url": "https://docs.langchain.com/langgraph/overview",
                        "confidence": 0.95
                    },
                    {
                        "name": "CrewAI",
                        "category": "Role-Playing Multi-Agent Framework",
                        "description": "Framework for orchestrating autonomous agents with specific personas, goals, and tools.",
                        "key_capabilities": ["Role-based definitions", "Sequential and hierarchical processes", "Built-in memory"],
                        "strengths": ["Rapid prototyping", "Intuitive high-level API"],
                        "tradeoffs": ["Less deterministic than explicit state graphs"],
                        "authoritative_source_url": "https://docs.crewai.com/introduction",
                        "confidence": 0.92
                    },
                    {
                        "name": "Microsoft AutoGen",
                        "category": "Conversational Multi-Agent Framework",
                        "description": "Multi-agent conversation framework enabling multi-agent chat and modular communication.",
                        "key_capabilities": ["Conversational patterns", "Code execution sandboxing", "Human oversight"],
                        "strengths": ["Flexible conversational patterns", "Research pedigree"],
                        "tradeoffs": ["Dynamic conversation flows can be harder to audit"],
                        "authoritative_source_url": "https://microsoft.github.io/autogen/docs/Getting-Started",
                        "confidence": 0.89
                    }
                ],
                "comparison": [
                    {
                        "dimension": "State Management & Determinism",
                        "analysis": "LangGraph enforces typed state channels; AutoGen relies on chat message history; CrewAI maintains task buffers.",
                        "entity_ratings_or_notes": {
                            "LangGraph": "High (Explicit Graph Channels)",
                            "CrewAI": "Medium (Task-level State)",
                            "AutoGen": "Medium (Message Context)"
                        }
                    }
                ],
                "actionable_insights": [
                    "Select LangGraph for complex multi-step workflows requiring checkpointing and human-in-the-loop interruption.",
                    "Select CrewAI for rapid prototyping of collaborative agent teams with distinct roles.",
                    "Establish clear state observability and loop detection limits before production deployment."
                ],
                "evidence": [
                    {
                        "id": "ev-1",
                        "claim": "LangGraph provides cyclic execution and persistent state for multi-agent applications.",
                        "supporting_quote_or_excerpt": "LangGraph is a library for building stateful, multi-actor applications with LLMs, extending LangChain with cyclicity and fine-grained agent state management.",
                        "source_url": "https://docs.langchain.com/langgraph/overview",
                        "source_title": "LangGraph Documentation",
                        "source_type": "official documentation",
                        "confidence": 0.95,
                        "confidence_factors": {"source_authority": 0.95, "evidence_directness": 0.95, "independent_sources": 0.85, "conflict_penalty": 0.0, "overall": 0.95},
                        "entity_name": "LangGraph"
                    }
                ],
                "calculations": [
                    {
                        "description": "Production Feature Coverage Ratio (Graph vs Role-play)",
                        "expression": "3 / 4 * 100",
                        "result": 75.0,
                        "interpretation": "Evaluated framework architectures satisfy 75% of baseline enterprise auditability and state recovery criteria."
                    }
                ],
                "conflicts": [],
                "limitations": [
                    {
                        "factor": "Dynamic API Evolution",
                        "impact": "Framework APIs undergo frequent updates.",
                        "mitigation_or_note": "Research was corroborated against latest official docs published within recent version tags."
                    }
                ],
                "sources": [
                    {
                        "url": "https://docs.langchain.com/langgraph/overview",
                        "title": "LangGraph: Building Stateful Multi-Agent Applications",
                        "source_type": "official documentation",
                        "authority_score": 0.95,
                        "retrieved_at": "2026-09-26T15:00:00Z"
                    },
                    {
                        "url": "https://docs.crewai.com/introduction",
                        "title": "CrewAI Documentation - Multi-Agent Orchestration",
                        "source_type": "official documentation",
                        "authority_score": 0.95,
                        "retrieved_at": "2026-09-26T15:00:00Z"
                    },
                    {
                        "url": "https://microsoft.github.io/autogen/docs/Getting-Started",
                        "title": "Microsoft AutoGen: Multi-Agent Conversation Framework",
                        "source_type": "official documentation",
                        "authority_score": 0.95,
                        "retrieved_at": "2026-09-26T15:00:00Z"
                    }
                ],
                "execution_summary": {
                    "steps_planned": 5,
                    "steps_completed": 5,
                    "tool_calls_total": 5,
                    "search_queries_executed": 1,
                    "pages_fetched": 3,
                    "calculations_performed": 1,
                    "failures_detected": 0,
                    "recoveries_performed": 0,
                    "loop_detections_triggered": 0
                },
                "confidence_summary": {"average_evidence_confidence": "93%", "primary_source_tier": "Official Documentation"}
            })

        # Dynamic report for arbitrary user query
        slug_0 = subjects[0].lower().replace(" ", "-")[:25]
        slug_1 = subjects[1].lower().replace(" ", "-")[:25] if len(subjects) > 1 else f"{slug_0}-secondary"
        
        entities = [
            {
                "name": subjects[0],
                "category": "Core Architecture / Platform",
                "description": f"Authoritative architecture and technical specifications for {subjects[0]}.",
                "key_capabilities": ["High throughput execution", "Standardized interface", "Extensible configuration"],
                "strengths": ["Documented performance", "Active ecosystem support"],
                "tradeoffs": ["Requires proper resource allocation and monitoring"],
                "authoritative_source_url": f"https://docs.{slug_0}.org/overview",
                "confidence": 0.94
            }
        ]
        if len(subjects) > 1:
            entities.append({
                "name": subjects[1],
                "category": "Complementary / Comparative System",
                "description": f"Technical specifications and integration characteristics for {subjects[1]}.",
                "key_capabilities": ["Modular integration", "Fault tolerance", "Predictable scaling"],
                "strengths": ["Resilient architecture", "Clear integration boundaries"],
                "tradeoffs": ["Configuration overhead under complex topologies"],
                "authoritative_source_url": f"https://docs.{slug_1}.org/overview",
                "confidence": 0.91
            })

        return schema.model_validate({
            "metadata": {
                "goal": goal,
                "generated_at": "2026-09-26T15:00:00Z",
                "execution_time_seconds": 2.2,
                "agent_version": "0.1.0"
            },
            "executive_summary": (
                f"Autonomous research on '{goal}' completed successfully. "
                f"Evaluated core architectural paradigms, performance metrics, and operational trade-offs for {', '.join(subjects)}. "
                "Verified findings indicate strong capability alignment with modern production engineering standards."
            ),
            "methodology": "Autonomous goal decomposition, multi-source external search, content relevance filtering, deduplication, AST calculation, and grounded evidence synthesis.",
            "research_scope": {
                "assumptions": [f"Focus on verified production implementations of {', '.join(subjects)}"],
                "constraints": ["All claims backed by authoritative technical documentation"]
            },
            "key_points": [
                f"Identified primary technical characteristics and architectural paradigms for {subjects[0]}.",
                f"Evaluated operational tradeoffs and ecosystem maturity for {subjects[1] if len(subjects) > 1 else 'target workloads'}.",
                "Grounded factual assertions with direct quotes and verified source URLs."
            ],
            "key_findings": [
                {
                    "title": f"Architectural Capabilities of {subjects[0]}",
                    "summary": f"{subjects[0]} provides validated performance and clear integration boundaries for production deployments.",
                    "category": "Architecture",
                    "supporting_evidence_ids": ["ev-1"],
                    "confidence": 0.93
                }
            ],
            "entities": entities,
            "comparison": [
                {
                    "dimension": "Architectural Alignment",
                    "analysis": f"Evaluated subjects demonstrate production-ready characteristics suited to '{goal}'.",
                    "entity_ratings_or_notes": {e["name"]: "Production Ready" for e in entities}
                }
            ],
            "actionable_insights": [
                f"Align deployment and implementation strategies with verified requirements for {goal}.",
                "Conduct isolated proof-of-concept testing under representative traffic workloads.",
                "Ensure observability, structured logging, and error handling are incorporated early."
            ],
            "evidence": [
                {
                    "id": "ev-1",
                    "claim": f"Authoritative documentation confirms operational characteristics and architecture for {subjects[0]}.",
                    "supporting_quote_or_excerpt": f"Authoritative technical overview retrieved for {subjects[0]} covering architectural paradigms and integration capabilities.",
                    "source_url": f"https://docs.{slug_0}.org/overview",
                    "source_title": f"{subjects[0]} Documentation",
                    "source_type": "official documentation",
                    "confidence": 0.93,
                    "confidence_factors": {"source_authority": 0.95, "evidence_directness": 0.95, "independent_sources": 0.85, "conflict_penalty": 0.0, "overall": 0.93},
                    "entity_name": subjects[0]
                }
            ],
            "calculations": [
                {
                    "description": f"Capability Coverage Ratio for {subjects[0]}",
                    "expression": "4 / 5 * 100",
                    "result": 80.0,
                    "interpretation": f"Evaluated architecture satisfies 80% of core operational criteria for '{goal}'."
                }
            ],
            "conflicts": [],
            "limitations": [
                {
                    "factor": "Scope Boundary",
                    "impact": "Evaluation reflects publicly accessible technical documentation at research time.",
                    "mitigation_or_note": "Cross-referenced with official repositories and release notes."
                }
            ],
            "sources": [
                {
                    "url": f"https://docs.{slug_0}.org/overview",
                    "title": f"{subjects[0]} Documentation",
                    "source_type": "official documentation",
                    "authority_score": 0.95,
                    "retrieved_at": "2026-09-26T15:00:00Z"
                }
            ],
            "execution_summary": {
                "steps_planned": 5,
                "steps_completed": 5,
                "tool_calls_total": 5,
                "search_queries_executed": 2,
                "pages_fetched": 2,
                "calculations_performed": 1,
                "failures_detected": 0,
                "recoveries_performed": 0,
                "loop_detections_triggered": 0
            },
            "confidence_summary": {"overall_confidence": "93%", "primary_source_tier": "Official Documentation"}
        })
