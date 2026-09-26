import pytest
from app.services.deduplication import DeduplicationService
from app.models.evidence import Source, Evidence, SourceType


def test_url_normalization_strips_tracking_and_slashes():
    url_a = "https://Docs.LangChain.com/langgraph/overview/?utm_source=twitter&utm_medium=social#section-1"
    url_b = "https://docs.langchain.com/langgraph/overview"

    norm_a = DeduplicationService.normalize_url(url_a)
    norm_b = DeduplicationService.normalize_url(url_b)

    assert norm_a == norm_b
    assert "utm_source" not in norm_a
    assert "#section-1" not in norm_a


def test_content_hash_exact_duplicate_detection():
    text_1 = "FastAPI is a modern, fast web framework for building APIs with Python."
    text_2 = "  fastapi is a modern,  fast web framework for building APIs with Python.  "

    hash_1 = DeduplicationService.compute_content_hash(text_1)
    hash_2 = DeduplicationService.compute_content_hash(text_2)

    assert hash_1 == hash_2

    seen_hashes = {hash_1}
    is_dup, reason = DeduplicationService.is_duplicate_content(text_2, seen_hashes=seen_hashes)
    assert is_dup is True
    assert "Exact duplicate" in reason


def test_jaccard_similarity_near_duplicate_detection():
    passage_1 = "CrewAI orchestrates autonomous AI agents using structured role-playing patterns and hierarchical task delegation."
    passage_2 = "CrewAI orchestrates autonomous AI agents using structured role-playing patterns and hierarchical task processes."

    sim = DeduplicationService.calculate_jaccard_similarity(passage_1, passage_2)
    assert sim >= 0.75

    is_dup, reason = DeduplicationService.is_duplicate_content(
        passage_2,
        seen_hashes=set(),
        seen_texts=[passage_1],
        similarity_threshold=0.75
    )
    assert is_dup is True
    assert "Near-duplicate" in reason


def test_deduplicate_sources_preserves_highest_authority():
    src_1 = Source(
        url="https://docs.crewai.com/introduction/?utm_source=news",
        title="CrewAI Docs",
        source_type=SourceType.COMMUNITY,
        authority_score=0.60
    )
    src_2 = Source(
        url="https://docs.crewai.com/introduction",
        title="Official CrewAI Documentation",
        source_type=SourceType.OFFICIAL_DOCS,
        authority_score=0.95
    )

    deduped, count = DeduplicationService.deduplicate_sources([src_1, src_2])
    assert len(deduped) == 1
    assert count == 1
    assert deduped[0].authority_score == 0.95
    assert deduped[0].title == "Official CrewAI Documentation"


def test_deduplicate_evidence_eliminates_duplicate_quotes():
    ev_1 = Evidence(
        claim="LangGraph supports cyclic state graphs",
        supporting_quote_or_excerpt="LangGraph enables cyclic graphs and checkpoints.",
        source_url="https://docs.langchain.com/langgraph",
        confidence=0.88
    )
    ev_2 = Evidence(
        claim="LangGraph provides cyclic state machine graphs",
        supporting_quote_or_excerpt="LangGraph enables cyclic graphs and checkpoints.",
        source_url="https://docs.langchain.com/langgraph?ref=blog",
        confidence=0.85
    )
    ev_3 = Evidence(
        claim="AutoGen provides multi-agent event loops",
        supporting_quote_or_excerpt="AutoGen supports conversational event loops.",
        source_url="https://microsoft.github.io/autogen",
        confidence=0.85
    )

    deduped, count = DeduplicationService.deduplicate_evidence([ev_1, ev_2, ev_3])
    assert len(deduped) == 2
    assert count == 1
    claims = [e.claim for e in deduped]
    assert any("AutoGen" in c for c in claims)
