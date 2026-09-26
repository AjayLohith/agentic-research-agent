from typing import List
from app.providers.search.base import SearchProvider
from app.models.tool import SearchResponse, SearchResult


class MockSearchProvider(SearchProvider):
    """
    Deterministic search provider for unit testing, offline demonstrations, and CI.
    Dynamically returns results matching query subjects.
    """

    async def _execute_search(self, query: str, max_results: int = 5) -> SearchResponse:
        q_lower = query.lower()
        results: List[SearchResult] = []

        if "gpt 6" in q_lower or "astra" in q_lower:
            results = [
                SearchResult(
                    title="GPT 6 Astra: Technical Preview and Agentic Architecture",
                    url="https://openai.com/research/gpt-6-astra-preview",
                    snippet="GPT 6 Astra introduces stateful autonomous reasoning, native multi-modal tool orchestration, and long-horizon plan execution benchmarks.",
                    source="openai.com",
                    relevance=0.98
                ),
                SearchResult(
                    title="GPT 6 Astra System Evaluation & Autonomous Agent Benchmarks",
                    url="https://arxiv.org/abs/2603.astra",
                    snippet="Comprehensive evaluation of GPT 6 Astra across complex planning, multi-step code execution, and autonomous software engineering benchmarks.",
                    source="arxiv.org",
                    relevance=0.94
                ),
                SearchResult(
                    title="Integrating Agent Frameworks with GPT 6 Astra API",
                    url="https://docs.astra.ai/integration/frameworks",
                    snippet="Technical documentation on interfacing external agent orchestrators with GPT 6 Astra reasoning endpoints and memory buffers.",
                    source="docs.astra.ai",
                    relevance=0.91
                )
            ]
        elif "postgres" in q_lower or "mongo" in q_lower:
            results = [
                SearchResult(
                    title="PostgreSQL: The World's Most Advanced Open Source Relational Database",
                    url="https://www.postgresql.org/docs/current/",
                    snippet="PostgreSQL provides ACID compliance, strong relational integrity, extensible indexing (B-Tree, GIN, GiST), and advanced JSONB querying for modern backends.",
                    source="postgresql.org",
                    relevance=0.96
                ),
                SearchResult(
                    title="MongoDB Documentation: Developer Data Platform and Document Database",
                    url="https://www.mongodb.com/docs/",
                    snippet="MongoDB provides flexible schema design, horizontal sharding, distributed replica sets, and native JSON-like BSON document storage for rapid application scaling.",
                    source="mongodb.com",
                    relevance=0.94
                ),
                SearchResult(
                    title="PostgreSQL vs MongoDB: Architecture, Performance, and Scaling Benchmarks",
                    url="https://db-engines.com/en/system/MongoDB%3BPostgreSQL",
                    snippet="Technical comparison of relational SQL versus document NoSQL architectures across read-heavy, write-intensive, and hybrid AI workload patterns.",
                    source="db-engines.com",
                    relevance=0.90
                )
            ]
        elif "rag" in q_lower or "retrieval augmented" in q_lower or "retrieval-augmented" in q_lower:
            results = [
                SearchResult(
                    title="Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks",
                    url="https://arxiv.org/abs/2005.11401",
                    snippet="Foundational architecture combining dense parametric models with non-parametric dense vector index retrieval for grounded question answering.",
                    source="arxiv.org",
                    relevance=0.97
                ),
                SearchResult(
                    title="Advanced RAG Architectures: Hybrid Search, Reranking, and Graph RAG",
                    url="https://docs.llamaindex.ai/en/stable/optimizing/advanced_retrieval/",
                    snippet="In-depth technical guide on advanced RAG patterns: semantic chunking, reciprocal rank fusion, cross-encoder reranking, and knowledge graph integration.",
                    source="docs.llamaindex.ai",
                    relevance=0.93
                ),
                SearchResult(
                    title="Production RAG Benchmarks: Latency, Cost, and Retrieval Accuracy",
                    url="https://qdrant.tech/articles/rag-benchmarks/",
                    snippet="Empirical benchmarks comparing HNSW vector indices, hybrid sparse-dense search, and quantized embeddings for enterprise RAG pipelines.",
                    source="qdrant.tech",
                    relevance=0.89
                )
            ]
        elif "fastapi" in q_lower or "spring" in q_lower:
            results = [
                SearchResult(
                    title="FastAPI: High Performance Modern Python Web Framework",
                    url="https://fastapi.tiangolo.com/",
                    snippet="FastAPI is a modern, fast (high-performance) web framework for building APIs with Python based on standard Python type hints.",
                    source="fastapi.tiangolo.com",
                    relevance=0.95
                ),
                SearchResult(
                    title="Spring Boot Overview and Enterprise Architecture",
                    url="https://spring.io/projects/spring-boot",
                    snippet="Spring Boot makes it easy to create stand-alone, production-grade Spring based Applications with enterprise maturity.",
                    source="spring.io",
                    relevance=0.93
                ),
                SearchResult(
                    title="FastAPI vs Spring Boot Microservices Performance Comparison",
                    url="https://tech-benchmarks.org/fastapi-vs-springboot",
                    snippet="Benchmark analysis comparing asynchronous Python ASGI throughput with Java 21 Spring Boot Virtual Threads under high-concurrency workloads.",
                    source="tech-benchmarks.org",
                    relevance=0.91
                )
            ]
        elif "langgraph" in q_lower or "crewai" in q_lower or "autogen" in q_lower or ("agent" in q_lower and "framework" in q_lower):
            results = [
                SearchResult(
                    title="LangGraph: Building Stateful Multi-Agent Applications",
                    url="https://docs.langchain.com/langgraph/overview",
                    snippet="LangGraph is a library for building stateful, multi-actor applications with LLMs, extending LangChain with cyclicity and fine-grained agent state management.",
                    source="docs.langchain.com",
                    relevance=0.96
                ),
                SearchResult(
                    title="CrewAI Documentation - Multi-Agent Orchestration",
                    url="https://docs.crewai.com/introduction",
                    snippet="CrewAI is an open-source framework for orchestrating role-playing autonomous AI agents that collaborate as a cohesive crew to solve complex tasks.",
                    source="docs.crewai.com",
                    relevance=0.92
                ),
                SearchResult(
                    title="Microsoft AutoGen: Multi-Agent Conversation Framework",
                    url="https://microsoft.github.io/autogen/docs/Getting-Started",
                    snippet="AutoGen is a framework that enables the development of LLM applications using multiple conversational agents that can communicate to solve tasks.",
                    source="microsoft.github.io",
                    relevance=0.88
                )
            ]
        else:
            clean_term = query.replace('"', '').replace("'", "").strip()
            slug = clean_term.replace(" ", "-").lower()[:30]
            results = [
                SearchResult(
                    title=f"Technical Overview and Architecture of {clean_term}",
                    url=f"https://docs.{slug}.org/overview",
                    snippet=f"Detailed authoritative documentation, architectural specifications, and core capabilities regarding {clean_term}.",
                    source=f"docs.{slug}.org",
                    relevance=0.95
                ),
                SearchResult(
                    title=f"{clean_term} Performance Benchmarks and Production Guide",
                    url=f"https://engineering.{slug}.io/benchmarks",
                    snippet=f"Empirical benchmarks, scalability metrics, operational trade-offs, and deployment considerations for {clean_term}.",
                    source=f"engineering.{slug}.io",
                    relevance=0.90
                ),
                SearchResult(
                    title=f"Ecosystem and Feature Comparison for {clean_term}",
                    url=f"https://tech-specs.org/topics/{slug}",
                    snippet=f"Comparative analysis, feature matrices, and developer tooling ecosystem overview for {clean_term}.",
                    source="tech-specs.org",
                    relevance=0.86
                )
            ]

        return SearchResponse(query=query, results=results[:max_results], total_results=len(results[:max_results]))
