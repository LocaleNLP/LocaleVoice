"""Unit tests for citation syntax + answer hygiene (Milestone 6C).

The problem-answer fixture reconstructs the reported screenshot
symptoms from their written description (no screenshot was provided):
malformed citation, English fragments, a repeated sentence, and
topic mixing. Flags are advisory; natural Darija still needs a
human reviewer.
"""

from __future__ import annotations

import os

from localevoice.pipeline.hygiene import (
    find_latin_fragments,
    find_repeated_sentences,
    hygiene_report,
)
from localevoice.pipeline.trace import find_malformed_citations, validate_citations

FIXTURE = os.path.join(os.path.dirname(__file__), "fixtures", "answer_6c_problem.txt")


def _problem_text():
    with open(FIXTURE, encoding="utf-8") as fh:
        return fh.read()


def test_malformed_citation_fragments_detected():
    assert find_malformed_citations("القمح مزيان olive-cake] بزاف.") == ["olive-cake]"]
    assert find_malformed_citations("ends with [feedipedia-wheat-grain") == [
        "[feedipedia-wheat-grain"
    ]
    assert find_malformed_citations("see [wheat grain] here") == ["[wheat grain]"]
    assert find_malformed_citations("empty [] brackets") == ["[]"]


def test_wellformed_citations_not_flagged_as_malformed():
    text = "Good. [feedipedia-wheat-grain] Also [feedipedia-olive-cake]."
    assert find_malformed_citations(text) == []
    check = validate_citations(
        text, ["feedipedia-wheat-grain", "feedipedia-olive-cake"]
    )
    assert check["contained"] is True
    assert check["syntax_ok"] is True


def test_validate_citations_reports_syntax_separately():
    check = validate_citations("مزيان olive-cake]", ["feedipedia-olive-cake"])
    assert check["contained"] is True  # nothing well-formed to contain
    assert check["syntax_ok"] is False
    assert check["malformed"] == ["olive-cake]"]


def test_latin_fragments_flagged_but_known_terms_kept():
    assert find_latin_fragments("القمح seres مهم.") == ["seres"]
    assert find_latin_fragments("Wheat is good for cattle.") == []
    assert find_latin_fragments("واش blé و niébé مزيانين؟") == []
    assert find_latin_fragments("واش tourteau d'olive مزيان؟") == []
    assert find_latin_fragments("القمح d'olive مهم.") == []
    assert find_latin_fragments("المصدر Feedipedia عندو.") == []
    assert find_latin_fragments("go 12 ox") == []  # short tokens ignored


def test_repeated_sentences_detected():
    text = "التربة مهمة للفلاحة. الجو زوين. التربة مهمة للفلاحة."
    assert find_repeated_sentences(text) == ["التربة مهمة للفلاحة"]
    assert find_repeated_sentences("جملة وحدة بلا تكرار.") == []


def test_problem_fixture_triggers_all_flags():
    text = _problem_text()
    check = validate_citations(text, ["feedipedia-wheat-grain"])
    assert check["syntax_ok"] is False
    assert "olive-cake]" in check["malformed"]
    report = hygiene_report(text)
    assert report["clean"] is False
    assert "seres" in report["latin_fragments"]
    assert len(report["repeated_sentences"]) == 1


def test_clean_darija_answer_passes():
    text = "القمح مزيان للبقر كمصدر ديال الطاقة. سول التقني على الكمية."
    assert hygiene_report(text)["clean"] is True
    assert find_malformed_citations(text + " [feedipedia-wheat-grain]") == []
