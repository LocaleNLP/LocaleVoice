"""Unit tests for lexical retrieval and normalization. No network."""

from __future__ import annotations

import pytest

from localevoice.knowledge.corpus import Document
from localevoice.knowledge.retrieve import (
    normalize_for_search,
    retrieve,
    score_document,
    tokenize,
)


def _doc(doc_id, content, aliases=(), title="T"):
    return Document(
        document_id=doc_id,
        title=title,
        publisher="P",
        source_url="https://example.org",
        retrieved_at="2026-10-29",
        language="en",
        crop_or_topic="topic",
        content=content,
        usage_or_license_notes="test",
        search_aliases=tuple(aliases),
    )


def test_normalize_arabic_variants():
    assert normalize_for_search("أحمد إسلام آية") == "احمد اسلام ايه"
    assert normalize_for_search("القمحُ") == "القمح"  # tashkeel stripped
    assert normalize_for_search("مـزرعة") == "مزرعه"  # tatweel + ta marbuta
    assert normalize_for_search("مستشفى") == "مستشفي"  # alef maqsura -> ya
    assert normalize_for_search("علي") == "علي"


def test_normalize_latin_and_punctuation():
    assert normalize_for_search("Blé, FRAIS!") == "blé frais"
    assert normalize_for_search("  d'olive  ") == "d olive"


def test_tokenize_strips_definite_article_and_noise():
    assert "قمح" in tokenize("القمح")
    assert "زيتون" in tokenize("الزيتون")
    assert "d" not in tokenize("tourteau d'olive")
    assert tokenize("   ") == []
    assert tokenize("") == []


def test_query_string_never_mutated():
    docs = [_doc("a", "wheat content")]
    query = "  القمح WHEAT?!  "
    before = str(query)
    retrieve(query, docs)
    assert query == before


def test_empty_query_returns_no_results():
    docs = [_doc("a", "wheat content")]
    assert retrieve("", docs) == []
    assert retrieve("   ", docs) == []


def test_no_match_returns_empty():
    docs = [_doc("a", "wheat content")]
    assert retrieve("شنو هي عاصمة المغرب", docs) == []


def test_french_term_matches_alias():
    docs = [_doc("w", "wheat is an energy source", aliases=["blé"])]
    found = retrieve("Le blé pour les bovins", docs)
    assert [e.document_id for e in found] == ["w"]
    assert "blé" in found[0].matched_terms


def test_arabic_term_matches_alias():
    docs = [_doc("w", "wheat is an energy source", aliases=["قمح"])]
    found = retrieve("القمح مزيان؟", docs)
    assert [e.document_id for e in found] == ["w"]


def test_ranking_prefers_more_matches_with_deterministic_ties():
    docs = [
        _doc("b-second", "wheat for ruminants"),
        _doc("a-first", "wheat for ruminants"),
        _doc("c-top", "wheat for ruminants and cattle"),
    ]
    found = retrieve("wheat ruminants cattle", docs, top_k=3)
    assert [e.document_id for e in found] == ["c-top", "a-first", "b-second"]
    assert found[0].score == 3
    assert found[1].score == found[2].score == 2


def test_top_k_limits_results():
    docs = [_doc(f"d{i}", "wheat") for i in range(5)]
    assert len(retrieve("wheat", docs, top_k=2)) == 2


def test_top_k_must_be_positive():
    with pytest.raises(ValueError, match="top_k"):
        retrieve("wheat", [_doc("a", "wheat")], top_k=0)


def test_metadata_preserved_on_evidence():
    docs = [
        _doc("w", "wheat is an energy source", aliases=["blé"], title="Wheat grain")
    ]
    (item,) = retrieve("blé", docs)
    assert item.title == "Wheat grain"
    assert item.publisher == "P"
    assert item.source_url == "https://example.org"
    assert "energy source" in item.content


def test_score_document_empty_query_tokens():
    assert score_document([], _doc("a", "wheat")) == (0, [])
