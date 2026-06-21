from __future__ import annotations

from pathlib import Path

from experiments.generation_lexicon import (
    build_generation_lexicon_from_aw_payload,
    explain_surface_decision,
    load_generation_lexicon,
    write_generation_lexicon,
)


def _sample_aw_lexicon() -> dict:
    return {
        "schema": "awrag_dataset_lexicon@1",
        "dataset_id": "dataset_under_test",
        "anchors": [
            {"anchor": "voltage", "symbol": "0x000000000001", "observations": 7},
            {"anchor": "mode", "symbol": "0x000000000002", "observations": 5},
            {"anchor": "1024", "symbol": "0x000000000003", "observations": 2},
            {"anchor": "the", "symbol": "0x000000000004", "observations": 99},
        ],
    }


def test_generation_lexicon_separates_meaning_anchors_from_glue() -> None:
    lexicon = build_generation_lexicon_from_aw_payload(_sample_aw_lexicon())

    assert lexicon.can_emit("voltage") is True
    assert lexicon.can_emit_meaning("voltage") is True
    assert lexicon.authority_for("voltage") == "observed_anchor_only"
    assert lexicon.lookup("voltage").observations == 7

    assert lexicon.can_emit("the") is True
    assert lexicon.can_emit_meaning("the") is False
    assert lexicon.authority_for("the") == "speech_glue_observed"

    assert lexicon.can_emit("because") is True
    assert lexicon.can_emit_meaning("because") is False
    assert lexicon.authority_for("because") == "speech_glue_only"


def test_generation_lexicon_refuses_forbidden_and_unobserved_claim_terms() -> None:
    lexicon = build_generation_lexicon_from_aw_payload(_sample_aw_lexicon())

    forbidden = explain_surface_decision(lexicon, "proves")
    missing = explain_surface_decision(lexicon, "unicorn")

    assert forbidden.allowed is False
    assert forbidden.meaningful is False
    assert forbidden.authority == "forbidden_claim_term"
    assert missing.allowed is False
    assert missing.meaningful is False
    assert missing.reason == "not_observed_and_not_glue"


def test_generation_lexicon_classifies_measure_or_identifier_anchor() -> None:
    lexicon = build_generation_lexicon_from_aw_payload(_sample_aw_lexicon())
    entry = lexicon.lookup("1024")

    assert entry is not None
    assert entry.anchor_class == "measure_or_identifier"
    assert lexicon.can_emit_meaning("1024") is True


def test_generation_lexicon_round_trips_to_json(tmp_path: Path) -> None:
    lexicon = build_generation_lexicon_from_aw_payload(_sample_aw_lexicon())
    path = tmp_path / "generation_helper.json"

    write_generation_lexicon(path, lexicon)
    loaded = load_generation_lexicon(path)

    assert loaded.schema == "awrag_generation_helper_lexicon@0"
    assert loaded.dataset_id == "dataset_under_test"
    assert loaded.can_emit_meaning("mode") is True
    assert loaded.can_emit("and") is True
    assert loaded.can_emit("guarantees") is False
