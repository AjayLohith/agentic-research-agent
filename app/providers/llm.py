import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type, TypeVar
from pydantic import BaseModel

logger = logging.getLogger("agentic_research.llm")
T = TypeVar("T", bound=BaseModel)


class LLMProvider(ABC):
    """Abstract interface decoupling agent reasoning from specific LLM vendors."""

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2
    ) -> str:
        """Generate unstructured string response."""
        pass

    @abstractmethod
    async def structured_output(
        self,
        schema: Type[T],
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.1
    ) -> T:
        """Generate structured response guaranteed to parse into the given Pydantic model."""
        pass


class OpenAICompatibleProvider(LLMProvider):
    """
    OpenAI and OpenAI-compatible provider (e.g. OpenAI, Groq, Ollama, OpenRouter, vLLM).
    Uses the official openai client with JSON schema enforcement.
    """

    def __init__(
        self,
        api_key: Optional[str],
        model: str = "gpt-4o-mini",
        base_url: str = "https://api.openai.com/v1"
    ):
        self.api_key = api_key or "sk-dummy"
        self.model = model
        self.base_url = base_url
        from openai import AsyncOpenAI
        self.client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2
    ) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature
        )
        return response.choices[0].message.content or ""

    async def structured_output(
        self,
        schema: Type[T],
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.1
    ) -> T:
        schema_json = json.dumps(schema.model_json_schema(), indent=2)
        augmented_system = (system_prompt or "") + (
            f"\n\nCRITICAL REQUIREMENT: You MUST respond with ONLY valid JSON adhering exactly "
            f"to the following JSON Schema. Do NOT include markdown code blocks, preamble, or commentary.\n"
            f"Schema:\n{schema_json}"
        )

        messages = [
            {"role": "system", "content": augmented_system},
            {"role": "user", "content": prompt}
        ]

        try:
            # First attempt: Structured Outputs with response_format json_object
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                response_format={"type": "json_object"}
            )
            raw_text = response.choices[0].message.content or "{}"
            parsed_data = json.loads(raw_text)
            return schema.model_validate(parsed_data)

        except Exception as e:
            logger.warning(f"Structured output parsing retry triggered: {e}")
            # Fallback retry with explicit repair prompt
            repair_prompt = f"The previous response failed schema validation. Please format the answer strictly as valid JSON conforming to the schema:\n{schema_json}"
            messages.append({"role": "user", "content": repair_prompt})
            retry_resp = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.0
            )
            raw = retry_resp.choices[0].message.content or "{}"
            # Strip backticks if present
            if "```json" in raw:
                raw = raw.split("```json")[1].split("```")[0].strip()
            elif "```" in raw:
                raw = raw.split("```")[1].split("```")[0].strip()
            return schema.model_validate_json(raw)


class MockLLMProvider(LLMProvider):
    """
    Deterministic mock provider for testing, evaluation, and offline demonstrations.
    Produces rich, realistic Pydantic models and responses without requiring network access.
    """

    def __init__(self, model_name: str = "mock-gpt-4o"):
        self.model_name = model_name

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2
    ) -> str:
        if "summary" in prompt.lower():
            return "Autonomous research indicates clear architectural differentiation across examined frameworks, with distinct trade-offs in state management, memory, and orchestration complexity."
        return "Deterministic mock reasoning trace completed successfully."

    async def structured_output(
        self,
        schema: Type[T],
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.1
    ) -> T:
        schema_name = schema.__name__
        p_lower = prompt.lower()

        if schema_name == "ResearchPlan":
            return self._generate_mock_plan(prompt, schema)
        elif schema_name == "ReplanningDecision":
            return self._generate_mock_replanning(prompt, schema)
        elif schema_name == "ResearchReport":
            return self._generate_mock_report(prompt, schema)
        elif schema_name == "ToolCall":
            return self._generate_mock_tool_call(prompt, schema)

        # Fallback to schema default instantiation
        try:
            return schema.model_validate({})
        except Exception:
            raise ValueError(f"MockLLMProvider does not have a fixture generator for schema {schema_name}")

    def _generate_mock_plan(self, prompt: str, schema: Type[T]) -> T:
        # Dynamically inspect goal topic
        is_backend = "fastapi" in prompt.lower() or "spring" in prompt.lower()
        if is_backend:
            plan_dict = {
                "objective": "Compare FastAPI and Spring Boot across performance, developer velocity, ecosystem maturity, and enterprise readiness.",
                "assumptions": [
                    "Evaluation focuses on modern versions (FastAPI with Python 3.11+, Spring Boot 3+ with Java 21+).",
                    "Target environment involves containerized cloud-native microservices."
                ],
                "constraints": [
                    "Rely on authoritative official documentation and verified benchmarks.",
                    "Exclude unmaintained community libraries."
                ],
                "steps": [
                    {
                        "id": 1,
                        "description": "Identify official architecture and design principles of FastAPI and Spring Boot.",
                        "purpose": "Establish foundational technical paradigms (ASGI async vs Servlet/Netty Virtual Threads).",
                        "expected_output": "Architectural overview and core specifications.",
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
                        "description": "Compare ecosystem maturity, enterprise governance, and developer productivity.",
                        "purpose": "Evaluate dependency ecosystems (Pydantic/SQLAlchemy vs Spring Data/Security).",
                        "expected_output": "Strengths, limitations, and ecosystem maturity findings.",
                        "preferred_tools": ["search_web", "fetch_url"],
                        "status": "pending"
                    },
                    {
                        "id": 4,
                        "description": "Calculate efficiency ratios and synthesize final competitive report.",
                        "purpose": "Verify evidence coverage and generate comparative intelligence matrix.",
                        "expected_output": "Comprehensive structured report with citations.",
                        "preferred_tools": ["calculator"],
                        "status": "pending"
                    }
                ]
            }
        else:
            plan_dict = {
                "objective": "Analyze the competitive landscape for AI agent frameworks, identifying major frameworks, core capabilities, and trade-offs.",
                "assumptions": [
                    "Focus is on production-grade autonomous agent frameworks active in 2024-2026.",
                    "Authoritative documentation and official repositories serve as primary truth."
                ],
                "constraints": [
                    "No reliance on unverified blog rumours.",
                    "Every claim must tie to an authoritative source URL."
                ],
                "steps": [
                    {
                        "id": 1,
                        "description": "Identify primary autonomous AI agent frameworks and market leaders.",
                        "purpose": "Determine top contenders (LangGraph, CrewAI, AutoGen, etc.) for in-depth analysis.",
                        "expected_output": "List of major agent frameworks with primary URLs.",
                        "preferred_tools": ["search_web"],
                        "status": "pending"
                    },
                    {
                        "id": 2,
                        "description": "Retrieve official architecture documentation for LangGraph and state management.",
                        "purpose": "Examine state graph transitions, cyclic execution, and checkpointing.",
                        "expected_output": "Technical architecture details and capability proofs.",
                        "preferred_tools": ["fetch_url"],
                        "status": "pending"
                    },
                    {
                        "id": 3,
                        "description": "Retrieve CrewAI documentation on role-playing collaboration and tooling.",
                        "purpose": "Analyze collaborative agent structures and multi-agent coordination.",
                        "expected_output": "Capabilities, strengths, and ecosystem integrations.",
                        "preferred_tools": ["fetch_url"],
                        "status": "pending"
                    },
                    {
                        "id": 4,
                        "description": "Retrieve Microsoft AutoGen documentation on conversational patterns.",
                        "purpose": "Inspect multi-agent event loop and human-in-the-loop support.",
                        "expected_output": "Strengths, trade-offs, and enterprise adoption posture.",
                        "preferred_tools": ["fetch_url"],
                        "status": "pending"
                    },
                    {
                        "id": 5,
                        "description": "Calculate framework capability coverage ratios and synthesize comparative findings.",
                        "purpose": "Compute quantitative metric comparisons and validate evidence grounding.",
                        "expected_output": "Synthesized intelligence report with structured tables and references.",
                        "preferred_tools": ["calculator"],
                        "status": "pending"
                    }
                ]
            }
        return schema.model_validate(plan_dict)

    def _generate_mock_replanning(self, prompt: str, schema: Type[T]) -> T:
        p_lower = prompt.lower()
        if "timeout" in p_lower or "failed" in p_lower or "error" in p_lower:
            return schema.model_validate({
                "needs_replanning": True,
                "reason": "Primary source endpoint encountered a network timeout or failure. Pivoting to alternative authoritative mirror.",
                "suggested_action": "alternative_source",
                "new_steps": [
                    {
                        "id": 99,
                        "description": "Search for secondary authoritative mirror documentation.",
                        "purpose": "Recover missing technical details without halting research.",
                        "expected_output": "Alternative verified source URL.",
                        "preferred_tools": ["search_web", "fetch_url"],
                        "status": "pending"
                    }
                ],
                "step_id_to_modify": None
            })
        return schema.model_validate({
            "needs_replanning": False,
            "reason": "Step succeeded and returned adequate evidence to satisfy the objective.",
            "suggested_action": "continue",
            "new_steps": [],
            "step_id_to_modify": None
        })

    def _generate_mock_tool_call(self, prompt: str, schema: Type[T]) -> T:
        step_desc = prompt.lower()
        if "current plan step" in prompt.lower():
            try:
                step_desc = prompt.lower().split("current plan step")[1].split("recent observations")[0]
            except Exception:
                step_desc = prompt.lower()

        import re
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

    def _generate_mock_report(self, prompt: str, schema: Type[T]) -> T:
        is_backend = "fastapi" in prompt.lower() or "spring" in prompt.lower()
        if is_backend:
            report_dict = {
                "metadata": {
                    "goal": "Compare FastAPI and Spring Boot for building production backend APIs.",
                    "generated_at": "2026-09-26T15:00:00Z",
                    "execution_time_seconds": 3.85,
                    "agent_version": "0.1.0"
                },
                "executive_summary": "FastAPI and Spring Boot represent two distinct architectural paradigms for production backend services. FastAPI provides extreme developer productivity, native asynchronous I/O, and automated OpenAPI documentation within the Python data/AI ecosystem. Spring Boot represents the pinnacle of enterprise-grade Java backend engineering, boasting unmatched dependency injection maturity, rigorous governance, and high-concurrency throughput via Virtual Threads (Loom).",
                "research_scope": {
                    "assumptions": [
                        "Target workloads involve microservices deployed in cloud-native containerized environments.",
                        "Comparison benchmarks modern runtimes: Python 3.12+ (Uvicorn ASGI) and Java 21+ (Spring Boot 3.3+ with Loom)."
                    ],
                    "constraints": [
                        "Only verified official documentation and authoritative architectural analyses are referenced."
                    ]
                },
                "key_findings": [
                    {
                        "title": "Developer Velocity vs Architectural Governance",
                        "summary": "FastAPI delivers 2-3x faster prototyping cycles for API-first microservices, whereas Spring Boot provides robust type safety, dependency injection, and centralized enterprise governance.",
                        "category": "Developer Productivity",
                        "supporting_evidence_ids": ["ev-1"],
                        "confidence": 0.94
                    },
                    {
                        "title": "Throughput and Concurrency Scaling",
                        "summary": "With Java 21 Virtual Threads, Spring Boot achieves superior peak requests-per-second and deterministic memory boundaries under massive multi-thousand concurrent I/O loads compared to Python's single-process GIL model.",
                        "category": "Performance",
                        "supporting_evidence_ids": ["ev-2"],
                        "confidence": 0.92
                    },
                    {
                        "title": "AI and Data Science Ecosystem Alignment",
                        "summary": "FastAPI integrates natively with NumPy, PyTorch, Hugging Face, and Pydantic, making it the uncontested standard for AI/ML inference gateways and agent backends.",
                        "category": "Ecosystem",
                        "supporting_evidence_ids": ["ev-3"],
                        "confidence": 0.96
                    }
                ],
                "entities": [
                    {
                        "name": "FastAPI",
                        "category": "Modern Python Asynchronous Web Framework",
                        "description": "High-performance API framework based on Starlette and Pydantic with native async/await syntax.",
                        "key_capabilities": [
                            "Native Python type hints and Pydantic data validation",
                            "Automatic interactive OpenAPI (Swagger) and ReDoc generation",
                            "Asynchronous request pipeline via ASGI (Uvicorn/Hypercorn)",
                            "Zero-boilerplate dependency injection system"
                        ],
                        "strengths": [
                            "Unrivaled developer ergonomics and minimal lines of code",
                            "Seamless integration with modern Python AI/ML ecosystem",
                            "Fast startup and lean memory footprint"
                        ],
                        "tradeoffs": [
                            "CPU-bound tasks require external process pooling due to Python GIL",
                            "Smaller suite of enterprise-grade ORM tooling compared to Spring Data/Hibernate"
                        ],
                        "authoritative_source_url": "https://fastapi.tiangolo.com/",
                        "confidence": 0.95
                    },
                    {
                        "name": "Spring Boot",
                        "category": "Enterprise Java Application Framework",
                        "description": "Production-ready, opinionated Java framework featuring auto-configuration and comprehensive enterprise integration.",
                        "key_capabilities": [
                            "Inversion of Control (IoC) and dependency injection",
                            "Spring Data JPA, Hibernate, and declarative transactions",
                            "Project Loom Virtual Threads for lightweight asynchronous concurrency",
                            "Spring Security with enterprise OAuth2, SAML, and RBAC support"
                        ],
                        "strengths": [
                            "Unmatched enterprise ecosystem and battle-tested stability",
                            "Exceptional throughput under high-concurrency enterprise workloads",
                            "GraalVM Native Image compilation support for sub-second cold starts"
                        ],
                        "tradeoffs": [
                            "Higher cognitive overhead and boilerplate configuration",
                            "Steeper onboarding curve for novice developers"
                        ],
                        "authoritative_source_url": "https://spring.io/projects/spring-boot",
                        "confidence": 0.94
                    }
                ],
                "comparison": [
                    {
                        "dimension": "Concurrency Model & Performance",
                        "analysis": "FastAPI uses an event loop (asyncio) on top of single-threaded Python processes. Spring Boot uses Java 21 Virtual Threads allowing lightweight thread-per-request blocking I/O without thread pool exhaustion.",
                        "entity_ratings_or_notes": {
                            "FastAPI": "High I/O concurrency; CPU-bound requires multiprocessing",
                            "Spring Boot": "Very High throughput via Virtual Threads and JVM optimizations"
                        }
                    },
                    {
                        "dimension": "Ecosystem & AI Readiness",
                        "analysis": "FastAPI is the standard for LLM serving, RAG pipelines, and agent orchestration. Spring Boot leads enterprise finance, banking, and high-security transactional domains.",
                        "entity_ratings_or_notes": {
                            "FastAPI": "Dominant in AI/ML and rapid microservices",
                            "Spring Boot": "Dominant in enterprise transactions and legacy integration"
                        }
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
                        "confidence_factors": {
                            "source_authority": 0.95,
                            "evidence_directness": 0.95,
                            "independent_sources": 0.85,
                            "conflict_penalty": 0.0,
                            "overall": 0.95
                        },
                        "entity_name": "FastAPI"
                    },
                    {
                        "id": "ev-2",
                        "claim": "Spring Boot 3 natively leverages Project Loom virtual threads and enterprise transaction management.",
                        "supporting_quote_or_excerpt": "Spring Boot makes it easy to create stand-alone, production-grade Spring based Applications that you can just run with enterprise maturity.",
                        "source_url": "https://spring.io/projects/spring-boot",
                        "source_title": "Spring Boot Overview",
                        "source_type": "official documentation",
                        "confidence": 0.94,
                        "confidence_factors": {
                            "source_authority": 0.95,
                            "evidence_directness": 0.95,
                            "independent_sources": 0.85,
                            "conflict_penalty": 0.0,
                            "overall": 0.94
                        },
                        "entity_name": "Spring Boot"
                    }
                ],
                "calculations": [
                    {
                        "description": "Developer Velocity Index (Estimated Lines of Code Factor)",
                        "expression": "120 / 350 * 100",
                        "result": 34.29,
                        "interpretation": "FastAPI requires approximately 34.3% of the boilerplate lines of code compared to an equivalent Spring Boot enterprise REST endpoint setup."
                    }
                ],
                "conflicts": [],
                "limitations": [
                    {
                        "factor": "Runtime Variance",
                        "impact": "Benchmarks vary widely based on JIT warmup and ASGI worker process counts.",
                        "mitigation_or_note": "Evaluations reflect containerized microservices under standard Kubernetes CPU allocations."
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
                "confidence_summary": {
                    "average_evidence_confidence": "94%",
                    "primary_source_tier": "Official Documentation (95% Authority)",
                    "evidence_validation_status": "Directly grounded with citations"
                }
            }
            return schema.model_validate(report_dict)

        report_dict = {
            "metadata": {
                "goal": "Analyze the current competitive landscape for AI agent frameworks.",
                "generated_at": "2026-09-26T15:00:00Z",
                "execution_time_seconds": 4.25,
                "agent_version": "0.1.0"
            },
            "executive_summary": "The autonomous AI agent ecosystem in 2026 is characterized by a paradigm shift from loose, unpredictable prompt-chaining to deterministic, stateful graph architectures. LangGraph dominates enterprise workflows requiring strict cyclic state and human-in-the-loop controls. CrewAI excels in intuitive role-playing agent orchestration and rapid prototyping. Microsoft AutoGen maintains a strong footprint in asynchronous conversational multi-agent research.",
            "research_scope": {
                "assumptions": [
                    "Production readiness requires state persistence, deterministic tool execution, and observability.",
                    "Analysis focuses on actively maintained frameworks with open-source codebases."
                ],
                "constraints": [
                    "All factual statements must trace directly to official documentation or verified benchmarks.",
                    "Unsubstantiated marketing claims are explicitly excluded."
                ]
            },
            "key_findings": [
                {
                    "title": "State Graphs as the Dominant Production Standard",
                    "summary": "Enterprises overwhelmingly prefer graph-based state machines (LangGraph) over opaque autonomous loops due to determinism, auditability, and replayability.",
                    "category": "Architecture",
                    "supporting_evidence_ids": ["ev-1", "ev-2"],
                    "confidence": 0.94
                },
                {
                    "title": "Role-Playing Multi-Agent Simplicity",
                    "summary": "CrewAI captures top developer velocity for collaborative workflows through clear abstractions (Agents, Tasks, Crews) but requires external guardrails for complex cycles.",
                    "category": "Developer Experience",
                    "supporting_evidence_ids": ["ev-3"],
                    "confidence": 0.91
                },
                {
                    "title": "Conversational Event-Driven Coordination",
                    "summary": "AutoGen offers flexible event-driven multi-agent conversations, particularly favored in academic and experimental simulations.",
                    "category": "Orchestration",
                    "supporting_evidence_ids": ["ev-4"],
                    "confidence": 0.88
                }
            ],
            "entities": [
                {
                    "name": "LangGraph",
                    "category": "Graph-based Agent Orchestration",
                    "description": "Library built by LangChain to build stateful multi-actor applications with LLMs using explicit graph computation, cycles, and persistence.",
                    "key_capabilities": [
                        "Cyclic graph topologies",
                        "Built-in state persistence and checkpointing",
                        "Human-in-the-loop interruption & time-travel debugging",
                        "Streaming of node events and tool states"
                    ],
                    "strengths": [
                        "Deterministic control over complex workflows",
                        "Extensive LangChain and LangSmith integration",
                        "Production-ready resilience"
                    ],
                    "tradeoffs": [
                        "Higher initial learning curve than role-play frameworks",
                        "Requires explicit state schema management"
                    ],
                    "authoritative_source_url": "https://docs.langchain.com/langgraph/overview",
                    "confidence": 0.95
                },
                {
                    "name": "CrewAI",
                    "category": "Role-Playing Multi-Agent Framework",
                    "description": "Framework designed for orchestrating autonomous agents assigned specific personas, goals, and tools that collaborate sequentially or hierarchically.",
                    "key_capabilities": [
                        "Role-based agent definitions (Role, Goal, Backstory)",
                        "Hierarchical and sequential crew execution processes",
                        "Native support for custom tools and memory caching",
                        "Pluggable LLM backends"
                    ],
                    "strengths": [
                        "Rapid time to prototype complex collaborative agent teams",
                        "Intuitive high-level API",
                        "Strong community adoption"
                    ],
                    "tradeoffs": [
                        "Less deterministic than explicit state machine graphs",
                        "Potential for runaway token loops without strict max iteration limits"
                    ],
                    "authoritative_source_url": "https://docs.crewai.com/introduction",
                    "confidence": 0.92
                },
                {
                    "name": "Microsoft AutoGen",
                    "category": "Conversational Multi-Agent Framework",
                    "description": "Multi-agent conversation framework enabling multi-agent chat, code execution, and modular agent communication.",
                    "key_capabilities": [
                        "Conversational multi-agent patterns",
                        "Dockerized code execution sandboxing",
                        "Human-in-the-loop participation modes",
                        "Asynchronous event-driven messaging"
                    ],
                    "strengths": [
                        "Flexible conversational choreography",
                        "Deep research pedigree from Microsoft",
                        "Built-in code generation and validation loops"
                    ],
                    "tradeoffs": [
                        "Dynamic conversational flows can be harder to audit in enterprise compliance",
                        "Architectural shifts between AutoGen v0.2 and v0.4"
                    ],
                    "authoritative_source_url": "https://microsoft.github.io/autogen/docs/Getting-Started",
                    "confidence": 0.89
                }
            ],
            "comparison": [
                {
                    "dimension": "State Management & Determinism",
                    "analysis": "LangGraph enforces typed, explicit state channels with checkpointing; AutoGen relies on chat message history; CrewAI maintains task output buffers.",
                    "entity_ratings_or_notes": {
                        "LangGraph": "High (Explicit Graph Channels & Checkpointers)",
                        "CrewAI": "Medium (Sequential / Hierarchical Task State)",
                        "AutoGen": "Medium (Message Thread Context)"
                    }
                },
                {
                    "dimension": "Developer Velocity & Learning Curve",
                    "analysis": "CrewAI provides fastest developer onboarding with role-playing declarative classes, whereas LangGraph requires state diagram modeling.",
                    "entity_ratings_or_notes": {
                        "CrewAI": "Highest (Intuitive persona abstraction)",
                        "LangGraph": "Moderate (Engineering rigor required)",
                        "AutoGen": "Moderate (Config-driven multi-agent setup)"
                    }
                },
                {
                    "dimension": "Human-in-the-Loop & Auditability",
                    "analysis": "LangGraph provides first-class support for breaking at graph nodes, editing state, and resuming. AutoGen supports interactive human user proxy.",
                    "entity_ratings_or_notes": {
                        "LangGraph": "Comprehensive (Native breakpoints & state overrides)",
                        "CrewAI": "Basic (Task level human input approval)",
                        "AutoGen": "Flexible (UserProxy agent intervention)"
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
                    "confidence_factors": {
                        "source_authority": 0.95,
                        "evidence_directness": 0.95,
                        "independent_sources": 0.85,
                        "conflict_penalty": 0.0,
                        "overall": 0.95
                    },
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
                    "confidence_factors": {
                        "source_authority": 0.95,
                        "evidence_directness": 0.95,
                        "independent_sources": 0.85,
                        "conflict_penalty": 0.0,
                        "overall": 0.93
                    },
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
                    "confidence_factors": {
                        "source_authority": 0.95,
                        "evidence_directness": 0.95,
                        "independent_sources": 0.85,
                        "conflict_penalty": 0.0,
                        "overall": 0.91
                    },
                    "entity_name": "Microsoft AutoGen"
                }
            ],
            "calculations": [
                {
                    "description": "Production Feature Coverage Ratio (Graph vs Role-play)",
                    "expression": "3 / 4 * 100",
                    "result": 75.0,
                    "interpretation": "Evaluated framework architectures satisfy 75% of baseline enterprise auditability and state recovery criteria without external bolt-on tooling."
                }
            ],
            "conflicts": [],
            "limitations": [
                {
                    "factor": "Dynamic API Evolution",
                    "impact": "Framework APIs (such as AutoGen 0.4 rewrite) undergo rapid structural updates.",
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
                "tool_calls_total": 7,
                "search_queries_executed": 2,
                "pages_fetched": 4,
                "calculations_performed": 1,
                "failures_detected": 0,
                "recoveries_performed": 0,
                "loop_detections_triggered": 0
            },
            "confidence_summary": {
                "average_evidence_confidence": "93%",
                "primary_source_tier": "Official Documentation (95% Authority)",
                "evidence_validation_status": "All claims backed by direct citations with verified URLs"
            }
        }
        return schema.model_validate(report_dict)


def get_llm_provider(
    provider_name: str,
    api_key: Optional[str] = None,
    model: str = "gpt-4o-mini",
    base_url: str = "https://api.openai.com/v1",
    mock_mode: bool = False
) -> LLMProvider:
    """Instantiate the appropriate LLM provider."""
    if mock_mode or provider_name.lower() == "mock" or not api_key:
        return MockLLMProvider(model_name=model)
    return OpenAICompatibleProvider(api_key=api_key, model=model, base_url=base_url)
