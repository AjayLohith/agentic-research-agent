import pytest
from app.services.relevance import RelevanceFilter


def test_relevance_filter_retains_goal_aligned_content():
    rf = RelevanceFilter(min_relevance_score=0.30)
    goal = "Compare FastAPI and Spring Boot for microservices"
    content = "FastAPI provides high-performance asynchronous request handling and automated OpenAPI documentation for Python microservices."

    is_rel, score, reason = rf.evaluate_relevance(content, goal)
    assert is_rel is True
    assert score >= 0.30
    assert "fastapi" in reason.lower() or "microservices" in reason.lower()


def test_relevance_filter_rejects_web_boilerplate():
    rf = RelevanceFilter(min_relevance_score=0.30)
    goal = "Compare FastAPI and Spring Boot for microservices"
    boilerplate = "We use cookies on this site. Please click Accept to agree to our privacy policy and terms of service."

    is_rel, score, reason = rf.evaluate_relevance(boilerplate, goal)
    assert is_rel is False
    assert score < 0.20
    assert "boilerplate" in reason.lower() or "cookie" in reason.lower()


def test_relevance_filter_rejects_off_topic_text():
    rf = RelevanceFilter(min_relevance_score=0.35)
    goal = "Compare FastAPI and Spring Boot for microservices"
    off_topic = "The recipe requires two cups of unbleached flour, fresh yeast, organic honey, and warm filtered water."

    is_rel, score, reason = rf.evaluate_relevance(off_topic, goal)
    assert is_rel is False
    assert score < 0.35


def test_filter_sentences_orders_by_relevance():
    rf = RelevanceFilter(min_relevance_score=0.30)
    goal = "AI agent frameworks LangGraph and CrewAI"
    sentences = [
        "All rights reserved. Copyright 2026 Corporation.",
        "LangGraph offers stateful cyclic graph orchestration for multi-agent workflows.",
        "CrewAI simplifies agent collaboration through role-playing autonomous agents.",
        "Today's weather in California is sunny with mild breeze."
    ]

    filtered = rf.filter_sentences(sentences, goal, max_sentences=3)
    assert len(filtered) == 2
    claims = [item[0] for item in filtered]
    assert any("LangGraph" in c for c in claims)
    assert any("CrewAI" in c for c in claims)
    assert not any("rights reserved" in c for c in claims)
