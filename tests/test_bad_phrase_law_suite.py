from __future__ import annotations

import json
from pathlib import Path

from experiments.bad_phrase_law_suite import (
    build_bad_phrase_law_suite,
    load_bad_phrase_law_suite,
    phrase_entries,
    solo_anchor_entries,
    write_bad_phrase_law_suite,
)


def test_bad_phrase_law_suite_keeps_candidates_review_only() -> None:
    payload = build_bad_phrase_law_suite()
    assert payload["schema"] == "bad_phrase_law_suite@1"
    assert payload["count"] >= 60
    entries = payload["entries"]
    assert any(row["surface"] == "motherfucker" for row in entries)
    assert any(row["surface"] == "mother fucker" for row in entries)
    assert any(row["surface"] == "did it on purpose" for row in entries)
    assert all(row["needs_review"] is True for row in entries)
    assert all(row["confidence"] == 0.0 for row in entries)
    assert all(row["needs_expanded_context"] is True for row in entries)
    assert payload["protected_slur_policy"] == "excluded_from_default_bad_phrase_suite"


def test_bad_phrase_law_suite_splits_solo_and_phrase_entries() -> None:
    payload = build_bad_phrase_law_suite()
    solos = solo_anchor_entries(payload)
    phrases = phrase_entries(payload)
    assert any(row["surface"] == "fuck" for row in solos)
    assert any(row["surface"] == "go fuck yourself" for row in phrases)
    assert any(row["surface"] == "did it on purpose" for row in phrases)
    assert all(len(row["anchors"]) == 1 for row in solos)
    assert all(len(row["anchors"]) > 1 for row in phrases)


def test_bad_phrase_law_suite_round_trip(tmp_path: Path) -> None:
    path = write_bad_phrase_law_suite(tmp_path / "bad_phrase_law_suite.json")
    loaded = load_bad_phrase_law_suite(path)
    assert loaded["schema"] == "bad_phrase_law_suite@1"
    assert loaded["count"] == build_bad_phrase_law_suite()["count"]
