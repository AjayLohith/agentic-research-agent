import re
from typing import Optional, Type
from pydantic import BaseModel

from app.providers.llm.base import LLMProvider, T


class MockLLMProvider(LLMProvider):
    """
    Deterministic mock provider for offline testing and reviewer evaluations.
    Generates structured Pydantic models matching goal inputs without external API calls.
    """

    def __init__(self, model_name: str = "mock-groq-llama"):
        self.model_name = model_name

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2
    ) -> str:
        return "Deterministic research reasoning completed."

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

    def _plan(self, prompt: str, schema: Type[T]) -> T:
        if "fastapi" in prompt.lower() or "spring" in prompt.lower():
            plan_dict = {
                "objective": "Compare FastAPI and Spring Boot across architecture, performance, and developer velocity.",
                "assumptions": ["Containerized cloud deployments", "Modern Python 3.12+ and Java 21+"],
                "constraints": ["Rely on verified official benchmarks and documentation"],
                "steps": [
                    {
                        "id": 1,
                        "description": "Identify official architecture and design principles of FastAPI and Spring Boot.",
                        "purpose": "Establish foundational technical paradigms.",
                        "expected_output": "Architectural specifications.",
                        "preferred_tools": ["search_web", "fetch_url"],
                        "status": "pending"
                    },
                    {
                        "id": 2,
                        "description": "Retrieve verified benchmarks and performance characteristics.",
                        "purpose": "Gather authoritative throughput and latency comparisons.",
                        "expected_output": "Quantitative comparison metrics.",
                        "preferred_tools": ["search_web", "calculator"],
                        "status": "pending"
                    },
                    {
                        "id": 3,
                        "description": "Compare ecosystem maturity and developer productivity.",
                        "purpose": "Evaluate dependency ecosystems.",
                        "expected_output": "Strengths and limitations.",
                        "preferred_tools": ["search_web", "fetch_url"],
                        "status": "pending"
                    },
                    {
                        "id": 4,
                        "description": "Calculate efficiency ratios and synthesize final competitive report.",
                        "purpose": "Compute quantitative metric comparisons.",
                        "expected_output": "Structured report with citations.",
                        "preferred_tools": ["calculator"],
                        "status": "pending"
                    }
                ]
            }
        else:
            plan_dict = {
                "objective": "Analyze the competitive landscape for AI agent frameworks, identifying key capabilities and differences.",
                "assumptions": ["Focus on actively maintained open-source agent frameworks in 2024-2026"],
                "constraints": ["Every claim must link to an authoritative source URL"],
                "steps": [
                    {
                        "id": 1,
                        "description": "Identify primary autonomous AI agent frameworks and market leaders.",
                        "purpose": "Determine top contenders for deep inspection.",
                        "expected_output": "List of major agent frameworks with primary URLs.",
                        "preferred_tools": ["search_web"],
                        "status": "pending"
                    },
                    {
                        "id": 2,
                        "description": "Retrieve official architecture documentation for LangGraph and state management.",
                        "purpose": "Examine state graph transitions and checkpointing.",
                        "expected_output": "Technical architecture details.",
                        "preferred_tools": ["fetch_url"],
                        "status": "pending"
                    },
                    {
                        "id": 3,
                        "description": "Retrieve CrewAI documentation on role-playing collaboration and tooling.",
                        "purpose": "Analyze collaborative multi-agent structures.",
                        "expected_output": "Capabilities and ecosystem integrations.",
                        "preferred_tools": ["fetch_url"],
                        "status": "pending"
                    },
                    {
                        "id": 4,
                        "description": "Retrieve Microsoft AutoGen documentation on conversational patterns.",
                        "purpose": "Inspect multi-agent event loop and oversight.",
                        "expected_output": "Strengths, trade-offs, and adoption.",
                        "preferred_tools": ["fetch_url"],
                        "status": "pending"
                    },
                    {
                        "id": 5,
                        "description": "Calculate framework capability coverage ratios and synthesize comparative findings.",
                        "purpose": "Compute quantitative metric comparisons.",
                        "expected_output": "Synthesized intelligence report.",
                        "preferred_tools": ["calculator"],
                        "status": "pending"
                    }
                ]
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
        step_desc = prompt.lower()
        if "current plan step" in prompt.lower():
            try:
                step_desc = prompt.lower().split("current plan step")[1].split("recent observations")[0]
            except Exception:
                step_desc = prompt.lower()

        if re.search(r"\b(calculate|percentage|ratios?|coverage)\b", step_desc):
            return schema.model_validate({
                "tool_name": "calculator",
                "arguments": {"expression": "3 / 4 * 100"},
                "rationale": "Calculate framework capability adoption percentage."
            })
        elif re.search(r"\b(identify|search|discover|market leaders)\b", step_desc) and "fetch" not in step_desc:
            return schema.model_validate({
                "tool_name": "search_web",
                "arguments": {"query": "AI agent frameworks comparison LangGraph CrewAI AutoGen", "max_results": 4},
                "rationale": "Search public sources to uncover major entities and ecosystem traits."
            })
        elif "langgraph" in step_desc:
            return schema.model_validate({
                "tool_name": "fetch_url",
                "arguments": {"url": "https://docs.langchain.com/langgraph/overview"},
                "rationale": "Fetch official LangGraph documentation regarding cyclic state management."
            })
        elif "crewai" in step_desc:
            return schema.model_validate({
                "tool_name": "fetch_url",
                "arguments": {"url": "https://docs.crewai.com/introduction"},
                "rationale": "Fetch official CrewAI documentation on role-playing collaboration."
            })
        elif "autogen" in step_desc:
            return schema.model_validate({
                "tool_name": "fetch_url",
                "arguments": {"url": "https://microsoft.github.io/autogen/docs/Getting-Started"},
                "rationale": "Fetch Microsoft AutoGen documentation on conversational multi-agent systems."
            })
        elif "fastapi" in step_desc and "fetch" in step_desc:
            return schema.model_validate({
                "tool_name": "fetch_url",
                "arguments": {"url": "https://fastapi.tiangolo.com/"},
                "rationale": "Fetch FastAPI architecture documentation."
            })
        elif "spring" in step_desc and "fetch" in step_desc:
            return schema.model_validate({
                "tool_name": "fetch_url",
                "arguments": {"url": "https://spring.io/projects/spring-boot"},
                "rationale": "Fetch Spring Boot documentation."
            })
        elif "fetch" in step_desc or "inspect" in step_desc or "retrieve" in step_desc:
            return schema.model_validate({
                "tool_name": "fetch_url",
                "arguments": {"url": "https://docs.langchain.com/langgraph/overview"},
                "rationale": "Fetch authoritative documentation."
            })
        else:
            return schema.model_validate({
                "tool_name": "search_web",
                "arguments": {"query": "AI agent frameworks comparison LangGraph CrewAI AutoGen", "max_results": 4},
                "rationale": "Search public sources to uncover major entities and ecosystem traits."
            })

    def _report(self, prompt: str, schema: Type[T]) -> T:
        if "fastapi" in prompt.lower() or "spring" in prompt.lower():
            report_dict = {
                "metadata": {
                    "goal": "Compare FastAPI and Spring Boot for building production backend APIs.",
                    "generated_at": "2026-09-26T15:00:00Z",
                    "execution_time_seconds": 2.8,
                    "agent_version": "0.1.0"
                },
                "executive_summary": "FastAPI and Spring Boot represent two distinct architectural paradigms for production backend services. FastAPI provides extreme developer productivity, native asynchronous I/O, and automated OpenAPI documentation within the Python ecosystem. Spring Boot represents enterprise-grade Java engineering with unmatched dependency injection maturity, rigorous governance, and high-concurrency throughput via Virtual Threads (Loom).",
                "research_scope": {
                    "assumptions": ["Containerized microservices", "Modern Python 3.12+ (Uvicorn) vs Java 21+ (Spring Boot 3.3+)"],
                    "constraints": ["Verified official documentation and benchmarks"]
                },
                "key_findings": [
                    {
                        "title": "Developer Velocity vs Architectural Governance",
                        "summary": "FastAPI enables faster prototyping for API-first services, while Spring Boot provides strict type safety, dependency injection, and enterprise governance.",
                        "category": "Productivity",
                        "supporting_evidence_ids": ["ev-1"],
                        "confidence": 0.94
                    },
                    {
                        "title": "Throughput and Concurrency Scaling",
                        "summary": "Java 21 Virtual Threads allow Spring Boot to handle high-concurrency blocking I/O without thread pool starvation.",
                        "category": "Performance",
                        "supporting_evidence_ids": ["ev-2"],
                        "confidence": 0.92
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
                "confidence_summary": {"average_evidence_confidence": "94%", "primary_source_tier": "Official Documentation"}
            }
            return schema.model_validate(report_dict)

        report_dict = {
            "metadata": {
                "goal": "Analyze the current competitive landscape for AI agent frameworks.",
                "generated_at": "2026-09-26T15:00:00Z",
                "execution_time_seconds": 3.2,
                "agent_version": "0.1.0"
            },
            "executive_summary": "The autonomous AI agent ecosystem in 2026 has shifted toward deterministic, stateful graph architectures. LangGraph leads enterprise workflows requiring cyclic state and human-in-the-loop controls. CrewAI excels in intuitive role-playing agent orchestration and rapid prototyping. Microsoft AutoGen maintains a strong presence in conversational multi-agent research.",
            "research_scope": {
                "assumptions": ["Focus on actively maintained open-source agent frameworks in 2024-2026"],
                "constraints": ["Every statement backed by official documentation or verified benchmarks"]
            },
            "key_findings": [
                {
                    "title": "State Graphs as the Production Standard",
                    "summary": "Enterprises favor graph-based state machines (LangGraph) over opaque autonomous loops due to determinism, auditability, and replayability.",
                    "category": "Architecture",
                    "supporting_evidence_ids": ["ev-1"],
                    "confidence": 0.94
                },
                {
                    "title": "Role-Playing Multi-Agent Simplicity",
                    "summary": "CrewAI captures high developer velocity for collaborative workflows through clear persona abstractions.",
                    "category": "Developer Experience",
                    "supporting_evidence_ids": ["ev-2"],
                    "confidence": 0.91
                },
                {
                    "title": "Conversational Coordination",
                    "summary": "AutoGen offers flexible event-driven multi-agent conversations, particularly in research and simulations.",
                    "category": "Orchestration",
                    "supporting_evidence_ids": ["ev-3"],
                    "confidence": 0.88
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
                },
                {
                    "id": "ev-2",
                    "claim": "CrewAI enables role-playing autonomous agents collaborating as a cohesive crew.",
                    "supporting_quote_or_excerpt": "CrewAI is an open-source framework for orchestrating role-playing autonomous AI agents that collaborate as a cohesive crew to solve complex tasks.",
                    "source_url": "https://docs.crewai.com/introduction",
                    "source_title": "CrewAI Documentation",
                    "source_type": "official documentation",
                    "confidence": 0.93,
                    "confidence_factors": {"source_authority": 0.95, "evidence_directness": 0.95, "independent_sources": 0.85, "conflict_penalty": 0.0, "overall": 0.93},
                    "entity_name": "CrewAI"
                },
                {
                    "id": "ev-3",
                    "claim": "Microsoft AutoGen allows multiple agents to cooperate through conversational message exchanges.",
                    "supporting_quote_or_excerpt": "AutoGen is a framework that enables the development of LLM applications using multiple conversational agents that can communicate to solve tasks.",
                    "source_url": "https://microsoft.github.io/autogen/docs/Getting-Started",
                    "source_title": "Microsoft AutoGen Documentation",
                    "source_type": "official documentation",
                    "confidence": 0.91,
                    "confidence_factors": {"source_authority": 0.95, "evidence_directness": 0.95, "independent_sources": 0.85, "conflict_penalty": 0.0, "overall": 0.91},
                    "entity_name": "Microsoft AutoGen"
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
        }
        return schema.model_validate(report_dict)
