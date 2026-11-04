"""Unit tests for lexical retrieval and normalization. No network."""

from __future__ import annotations

import pytest

from localevoice.knowledge.corpus import Document, load_corpus
from localevoice.knowledge.retrieve import (
    normalize_for_search,
    retrieve,
    score_document,
    tokenize,
)


def _doc(doc_id, content, aliases=(), title="T"):
    return Document(
        id=doc_id,
        title=title,
        source_name="P",
        source_url="https://example.org",
        category="Cereals",
        crop_or_species="wheat",
        excerpt=content,
        language="en",
        date_accessed="2026-10-29",
        review_status="verified-excerpt",
        keywords=tuple(aliases),
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


def test_normalize_hamza_variants():
    assert normalize_for_search("مؤمن") == "مومن"
    assert normalize_for_search("قارئ") == "قاري"


def test_idf_weighting_ranks_distinctive_terms_first():
    docs = [
        _doc("common", "wheat is grown widely"),
        _doc("rare", "wheat xerophyte"),
    ]
    count = retrieve("wheat xerophyte", docs, top_k=2)
    assert [e.document_id for e in count] == ["rare", "common"]
    assert count[0].score == 2
    weighted = retrieve("wheat xerophyte", docs, top_k=2, weighting="idf")
    assert [e.document_id for e in weighted] == ["rare", "common"]
    assert weighted[0].score > weighted[1].score
    assert isinstance(weighted[0].score, float)


def test_idf_weighting_rejects_unknown_mode():
    with pytest.raises(ValueError, match="weighting"):
        retrieve("wheat", [_doc("a", "wheat")], weighting="semantic")


def test_multiple_relevant_excerpts_returned():
    corpus = load_corpus("data/knowledge")
    found = retrieve("protein", corpus.documents, top_k=3)
    assert [e.document_id for e in found] == [
        "feedipedia-alfalfa",
        "feedipedia-olive-cake",
        "feedipedia-wheat-grain",
    ]
    assert all(e.score == 1 for e in found)


def _doc_with_status(doc_id, content, status):
    doc = _doc(doc_id, content)
    return Document(
        id=doc.id,
        title=doc.title,
        source_name=doc.source_name,
        source_url=doc.source_url,
        category=doc.category,
        crop_or_species=doc.crop_or_species,
        excerpt=doc.excerpt,
        language=doc.language,
        date_accessed=doc.date_accessed,
        review_status=status,
        keywords=doc.keywords,
    )


def test_eligible_only_excludes_non_verified_statuses():
    docs = [
        _doc_with_status("good", "wheat cattle", "verified-excerpt"),
        _doc_with_status("pend", "wheat cattle", "pending-review"),
        _doc_with_status("rej", "wheat cattle", "rejected"),
        _doc_with_status("arch", "wheat cattle", "archived"),
    ]
    found = retrieve("wheat cattle", docs, eligible_only=True)
    assert [e.document_id for e in found] == ["good"]


def test_default_ranking_preserved_for_diagnostics():
    docs = [
        _doc_with_status("good", "wheat cattle", "verified-excerpt"),
        _doc_with_status("pend", "wheat cattle", "pending-review"),
    ]
    found = retrieve("wheat cattle", docs)
    assert {e.document_id for e in found} == {"good", "pend"}


def test_eligible_only_frees_rank_slots():
    docs = [
        _doc_with_status("pend", "wheat cattle feed", "pending-review"),
        _doc_with_status("good", "wheat", "verified-excerpt"),
    ]
    # Without the filter, pend outranks good for top_k=1.
    assert retrieve("wheat cattle feed", docs, top_k=1)[0].document_id == "pend"
    assert retrieve("wheat cattle feed", docs, top_k=1, eligible_only=True)[
        0
    ].document_id == "good"


def test_score_document_empty_query_tokens():
    assert score_document([], _doc("a", "wheat")) == (0, [])


def test_stopwords_dropped_from_query_and_docs():
    assert tokenize("What is the wheat?") == ["wheat"]
    assert tokenize("How much wheat per week?") == ["how", "wheat", "per", "week"]
    assert tokenize("Le blé pour les bovins") == ["blé", "bovins"]
    assert tokenize("واش القمح مزيان؟") == ["قمح", "مزيان"]


def test_stopword_only_overlap_retrieves_nothing():
    # Regression: "is/the/of" must not match every English document.
    docs = [
        _doc("w", "Wheat is used as a source of energy for cattle."),
        _doc("o", "Olive cake is fed to sheep in times of scarcity."),
    ]
    assert retrieve("What is the capital of Morocco?", docs) == []


def test_modal_and_auxiliary_verbs_are_stopwords():
    # 6D relevance audit: "can/used" matched across excerpts.
    assert tokenize("Can olive cake be used for sheep?") == [
        "olive",
        "cake",
        "sheep",
    ]
    assert tokenize("used use using") == []
    assert (
        retrieve("Le blé est-il bon ?", [_doc("w", "Wheat", aliases=["blé"])])
        != []
    )
