from __future__ import annotations

from pathlib import Path

from experiments.anchor_speech_assembly import EvidenceAnchor, assemble_anchor_first_answer
from experiments.generation_binary import load_generation_binary, write_generation_binary
from experiments.generation_lexicon import build_generation_lexicon_from_aw_payload


def _sample_aw_lexicon() -> dict:
    return {
        "schema": "awrag_dataset_lexicon@1",
        "dataset_id": "generation_dataset",
        "anchors": [
            {"anchor": "voltage", "symbol": "0x000000000001", "observations": 7},
            {"anchor": "mode", "symbol": "0x000000000002", "observations": 5},
            {"anchor": "safe", "symbol": "0x000000000003", "observations": 3},
            {"anchor": "and", "symbol": "0x000000000004", "observations": 20},
        ],
    }


def test_generation_binary_round_trip_preserves_emit_authority(tmp_path: Path) -> None:
    lexicon = build_generation_lexicon_from_aw_payload(_sample_aw_lexicon())
    binary_path = tmp_path / "generation.awgenbin"

    receipt = write_generation_binary(binary_path, lexicon)
    loaded = load_generation_binary(binary_path, dataset_id=receipt.dataset_id, set_id=receipt.set_id)

    assert receipt.record_count >= 4
    assert receipt.binary_bytes > 0
    assert loaded.can_emit("voltage") is True
    assert loaded.can_emit_meaning("voltage") is True
    assert loaded.authority_for("voltage") == "observed_anchor_only"
    assert loaded.can_emit("and") is True
    assert loaded.can_emit_meaning("and") is False
    assert loaded.can_emit("supports") is True
    assert loaded.can_emit_meaning("supports") is False
    assert loaded.authority_for("supports") == "relation_surface_only"
    assert loaded.can_emit("proves") is False


def test_generation_binary_decision_blocks_unobserved_meaning(tmp_path: Path) -> None:
    lexicon = build_generation_lexicon_from_aw_payload(_sample_aw_lexicon())
    binary_path = tmp_path / "generation.awgenbin"
    write_generation_binary(binary_path, lexicon)
    loaded = load_generation_binary(binary_path)

    assert loaded.decision("unicorn")["allowed"] is False
    assert loaded.decision("proves")["reason"] == "forbidden_claim_term"
    assert loaded.decision("because")["reason"] == "allowed_glue"


def test_anchor_first_speech_assembly_uses_binary_glue_without_inventing_meaning(tmp_path: Path) -> None:
    lexicon = build_generation_lexicon_from_aw_payload(_sample_aw_lexicon())
    binary_path = tmp_path / "generation.awgenbin"
    write_generation_binary(binary_path, lexicon)
    loaded = load_generation_binary(binary_path)

    frame = assemble_anchor_first_answer(
        question_id="q1",
        anchors=[
            EvidenceAnchor("voltage", citation="[AWCIT-1]"),
            EvidenceAnchor("mode"),
            EvidenceAnchor("safe"),
        ],
        generation=loaded,
    )

    assert frame.status == "assembled_from_anchor_path"
    assert frame.surface_text.startswith("voltage and mode and safe.")
    assert "[AWCIT-1]" in frame.surface_text
    assert frame.glue_slots
    assert all(slot.glue_word == "and" for slot in frame.glue_slots)


def test_anchor_first_speech_assembly_refuses_unsupported_anchor(tmp_path: Path) -> None:
    lexicon = build_generation_lexicon_from_aw_payload(_sample_aw_lexicon())
    binary_path = tmp_path / "generation.awgenbin"
    write_generation_binary(binary_path, lexicon)
    loaded = load_generation_binary(binary_path)

    frame = assemble_anchor_first_answer(
        question_id="q2",
        anchors=[EvidenceAnchor("voltage"), EvidenceAnchor("unicorn")],
        generation=loaded,
    )

    assert frame.status == "refused_unsupported_surface"
    assert frame.refusal_reason == "unsupported_meaning_anchor:unicorn"
    assert frame.surface_text == ""
