from __future__ import annotations

import json
from pathlib import Path

import pytest

import awrag.engine as engine
from awrag.engine import batch_questions, determinism_receipt, intake, query, status, symbol_for

DATASET_ID = "dataset_under_test"


def assert_protected_notice(payload: dict) -> None:
    assert payload["copyright"] == "Copyright (c) 2026 Lee Mercey. Owner: Cortex Evolved Systems. All rights reserved."
    assert payload["owner"] == "Cortex Evolved Systems"
    assert payload["license"] == "AWRAG Public Review License"
    assert payload["watermark_locked"] is True
    assert payload["removal_prohibited"] is True
    assert "facsimile" in payload["watermark"].lower()
    assert "not source evidence" in payload["watermark"].lower()


def test_intake_writes_dataset_local_counts_and_lexicon(tmp_path: Path) -> None:
    source = tmp_path / "source.txt"
    source.write_text(
        "AWRAG REVIEW FACSIMILE.\nDataset counts stay local.\n\nThe dataset lexicon stays with the dataset.",
        encoding="utf-8",
    )

    result = intake(tmp_path / "runtime", DATASET_ID, source)

    dataset_root = tmp_path / "runtime" / "datasets" / DATASET_ID
    assert result["scope"] == "dataset_local"
    assert result["persistent_memory"] is False
    assert (dataset_root / "counts" / "anchor_counts.awbin").exists()
    assert (dataset_root / "counts" / "relation_counts.awbin").exists()
    assert (dataset_root / "counts" / "block_anchor_postings.awbin").exists()
    assert (dataset_root / "state" / "dataset_lexicon.json").exists()
    assert (dataset_root / "coordinates" / "coordinate_index.jsonl").exists()
    assert (dataset_root / "citations" / "citations.jsonl").exists()

    lexicon = json.loads((dataset_root / "state" / "dataset_lexicon.json").read_text(encoding="utf-8"))
    manifest = json.loads((dataset_root / "dataset_manifest.json").read_text(encoding="utf-8"))
    assert lexicon["scope"] == "dataset_local"
    assert lexicon["symbol_system"] == "awrag_dataset_6b@1"
    assert lexicon["symbol_bytes"] == 6
    assert lexicon["symbol_transferable"] is False
    assert lexicon["anchorworks_lifetime_symbol_compatible"] is False
    assert lexicon["anchor_count"] > 0
    assert lexicon["anchors"][0]["symbol_system"] == "awrag_dataset_6b@1"
    assert lexicon["anchors"][0]["transferable"] is False
    assert lexicon["anchors"][0]["lifetime_allowed"] is False
    assert_protected_notice(result)
    assert_protected_notice(lexicon)
    assert_protected_notice(manifest)
    assert manifest["symbol_system"] == "awrag_dataset_6b@1"
    assert manifest["symbol_bytes"] == 6
    assert manifest["count_backend"] == "awrag_native_binary_counts@1"
    assert manifest["symbol_transferable"] is False
    assert manifest["anchorworks_lifetime_symbol_compatible"] is False


def test_demo_uses_native_binary_counts_not_sqlite(tmp_path: Path) -> None:
    source = tmp_path / "source.txt"
    source.write_text("Native binary counts stay dataset-local.", encoding="utf-8")

    result = intake(tmp_path / "runtime", DATASET_ID, source)
    dataset_root = tmp_path / "runtime" / "datasets" / DATASET_ID
    status_result = status(tmp_path / "runtime", DATASET_ID)

    assert result["count_backend"] == "awrag_native_binary_counts@1"
    assert status_result["count_backend"] == "awrag_native_binary_counts@1"
    assert status_result["index_status"] == "INDEX_READY"
    assert status_result["query_allowed"] is True
    assert status_result["index_readiness"]["counts"]["anchor_count"] > 0
    assert status_result["index_readiness"]["counts"]["relation_count"] > 0
    assert status_result["index_readiness"]["counts"]["block_anchor_posting_count"] > 0
    assert not (dataset_root / "counts" / "dataset_counts.sqlite").exists()
    assert "sqlite_counts_path" not in status_result
    assert status_result["anchor_counts_path"].endswith("anchor_counts.awbin")
    assert status_result["relation_counts_path"].endswith("relation_counts.awbin")
    assert status_result["block_anchor_postings_path"].endswith("block_anchor_postings.awbin")


def test_dataset_symbols_are_fixed_six_byte_dataset_local_ids() -> None:
    symbol = symbol_for("dataset")

    assert symbol.startswith("0x")
    assert len(symbol) == 14
    int(symbol[2:], 16)


def test_intake_fails_on_dataset_symbol_collision(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "source.txt"
    source.write_text("alpha beta", encoding="utf-8")

    monkeypatch.setattr(engine, "symbol_for", lambda _anchor: "0x000000000001")

    try:
        intake(tmp_path / "runtime", DATASET_ID, source)
    except ValueError as exc:
        assert "symbol collision" in str(exc)
    else:
        raise AssertionError("intake should fail when two anchors share one dataset symbol")


def test_query_returns_awrag_owned_citations(tmp_path: Path) -> None:
    source = tmp_path / "source.txt"
    source.write_text("Dataset counts stay local and provided data is not persistent memory.", encoding="utf-8")
    intake(tmp_path / "runtime", DATASET_ID, source)

    result = query(tmp_path / "runtime", DATASET_ID, "Where do dataset counts stay?", top_k=2)

    assert result["scope"] == "dataset_local"
    assert result["model_used"] == "none"
    assert result["model_may_search"] is False
    assert_protected_notice(result)
    locations = result["answer_packet"]["locations"]
    assert locations
    assert locations[0]["citation"].startswith("[AWCIT-")
    assert "Dataset counts stay local" in locations[0]["text"]
    assert result["final_answer"]["resolver"] == "awrag_deterministic_nlp_resolver@1"
    assert result["final_answer"]["model_used"] == "none"
    assert result["final_answer"]["model_may_search"] is False
    assert result["final_answer"]["status"] == "answered_from_awrag_locations"
    assert result["final_answer"]["citations"] == [locations[0]["citation"]]
    assert locations[0]["citation"] in result["final_answer"]["text"]
    assert result["index_readiness"]["status"] == "INDEX_READY"
    assert result["index_readiness"]["query_allowed"] is True
    output_path = Path(result["output_path"])
    assert_protected_notice(json.loads(output_path.read_text(encoding="utf-8")))


def test_query_refuses_when_index_is_not_ready(tmp_path: Path) -> None:
    try:
        query(tmp_path / "runtime", DATASET_ID, "Can I query before intake?", top_k=1)
    except RuntimeError as exc:
        assert "INDEX_NOT_READY" in str(exc)
        assert "query_allowed=false" in str(exc)
    else:
        raise AssertionError("query should refuse before the dataset index is built")

    status_result = status(tmp_path / "runtime", DATASET_ID)
    assert status_result["index_status"] == "INDEX_NOT_READY"
    assert status_result["query_allowed"] is False
    assert "latest_intake_receipt_missing" in status_result["index_readiness"]["reasons"]


def test_determinism_receipt_hashes_dataset_artifacts_and_raw_packets(tmp_path: Path) -> None:
    source = tmp_path / "source.txt"
    source.write_text("Dataset counts stay local and citations point to source coordinates.", encoding="utf-8")
    runtime = tmp_path / "runtime"
    intake(runtime, DATASET_ID, source)

    receipt = determinism_receipt(
        runtime,
        DATASET_ID,
        questions=["Where do dataset counts stay?"],
        top_k=2,
    )

    assert receipt["schema"] == "awrag_twin_machine_determinism_receipt@1"
    assert receipt["dataset_id"] == DATASET_ID
    assert receipt["runtime"]["status"]["count_backend"] == "awrag_native_binary_counts@1"
    files = receipt["dataset_artifacts"]["files"]
    assert files["anchor_counts"]["exists"] is True
    assert files["anchor_counts"]["sha256"]
    assert files["relation_counts"]["exists"] is True
    assert files["block_anchor_postings"]["exists"] is True
    assert files["citations"]["sha256"]
    assert files["coordinate_index"]["sha256"]
    assert receipt["questions"]["count"] == 1
    assert receipt["query_packets"][0]["raw_packet_sha256"]
    assert receipt["query_packets"][0]["citation_order"]
    assert receipt["comparison_rule"]["raw_packets_match"].startswith("AW/runtime/data")
    assert Path(receipt["receipt_path"]).exists()
    assert_protected_notice(receipt)


def test_status_reports_no_persistent_memory(tmp_path: Path) -> None:
    source = tmp_path / "source.txt"
    source.write_text("Local counts only.", encoding="utf-8")
    intake(tmp_path / "runtime", DATASET_ID, source)

    result = status(tmp_path / "runtime", DATASET_ID)

    assert result["scope"] == "dataset_local"
    assert result["persistent_memory"] is False
    assert result["anchor_count"] > 0
    assert_protected_notice(result)


def test_every_persisted_artifact_has_indelible_watermark(tmp_path: Path) -> None:
    source = tmp_path / "source.txt"
    source.write_text("AWRAG citations point to local lines.\n\nCoordinates stay with the dataset.", encoding="utf-8")

    receipt = intake(tmp_path / "runtime", DATASET_ID, source)
    query_result = query(tmp_path / "runtime", DATASET_ID, "Where do citations point?")
    dataset_root = tmp_path / "runtime" / "datasets" / DATASET_ID

    json_paths = [
        dataset_root / "dataset_manifest.json",
        dataset_root / "state" / "dataset_lexicon.json",
        Path(receipt["receipt_path"]),
        Path(query_result["output_path"]),
    ]
    for path in json_paths:
        assert_protected_notice(json.loads(path.read_text(encoding="utf-8")))

    jsonl_paths = [
        dataset_root / "citations" / "citations.jsonl",
        dataset_root / "coordinates" / "coordinate_index.jsonl",
    ]
    for path in jsonl_paths:
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        assert rows
        for row in rows:
            assert_protected_notice(row)


def test_query_prefers_compact_direct_evidence_over_large_noisy_block(tmp_path: Path) -> None:
    source = tmp_path / "source.md"
    noisy_lines = ["| Title | Link | Notes |", "| --- | --- | --- |"]
    noisy_lines.extend(f"| Generic model adapter table row {index} | link | filler data boundary citation installer |" for index in range(90))
    source.write_text(
        "\n".join(noisy_lines)
        + "\n\n"
        + "Dataset-local counts are explained here. The dataset lexicon and counts stay with the dataset.",
        encoding="utf-8",
    )
    intake(tmp_path / "runtime", DATASET_ID, source)

    result = query(tmp_path / "runtime", DATASET_ID, "What explains dataset-local counts?", top_k=3)
    top = result["answer_packet"]["locations"][0]

    assert "Dataset-local counts are explained here" in top["text"]
    assert top["direct_hit_count"] >= 2


def test_query_ignores_standalone_punctuation_anchors(tmp_path: Path) -> None:
    source = tmp_path / "source.md"
    source.write_text(
        "Question marks and table pipes should not dominate retrieval.\n\n"
        "Dataset-local citation rules are explained in this compact block.",
        encoding="utf-8",
    )
    intake(tmp_path / "runtime", DATASET_ID, source)

    result = query(tmp_path / "runtime", DATASET_ID, "What are the citation rules?", top_k=2)
    top = result["answer_packet"]["locations"][0]

    assert "Dataset-local citation rules" in top["text"]
    assert "?" not in top["matched_anchors"]
    assert "|" not in top["matched_anchors"]


def test_rapid_queries_write_distinct_outputs(tmp_path: Path) -> None:
    source = tmp_path / "source.txt"
    source.write_text("Dataset counts stay local. Citations point to source coordinates.", encoding="utf-8")
    intake(tmp_path / "runtime", DATASET_ID, source)

    first = query(tmp_path / "runtime", DATASET_ID, "Where do dataset counts stay?")
    second = query(tmp_path / "runtime", DATASET_ID, "Where do citations point?")

    assert first["output_path"] != second["output_path"]
    assert Path(first["output_path"]).exists()
    assert Path(second["output_path"]).exists()


def test_generic_question_words_do_not_outrank_content_anchors(tmp_path: Path) -> None:
    source = tmp_path / "source.md"
    source.write_text(
        "The project says many things about files and documents.\n\n"
        "AWRAG citations are owned by the system and point to dataset-local coordinates.",
        encoding="utf-8",
    )
    intake(tmp_path / "runtime", DATASET_ID, source)

    result = query(tmp_path / "runtime", DATASET_ID, "What does the project say about citations?", top_k=2)
    top = result["answer_packet"]["locations"][0]

    assert "AWRAG citations are owned" in top["text"]
    assert "say" not in top["matched_anchors"]
    assert "project" not in top["matched_anchors"]


def test_acronym_surfaces_are_casefolded_anchors_not_letter_streams(tmp_path: Path) -> None:
    source = tmp_path / "source.md"
    source.write_text(
        "Local ABC providers are configured through the model adapter.",
        encoding="utf-8",
    )
    intake(tmp_path / "runtime", DATASET_ID, source)

    result = query(tmp_path / "runtime", DATASET_ID, "Where are abc providers configured?", top_k=1)
    top = result["answer_packet"]["locations"][0]

    assert "Local ABC providers" in top["text"]
    assert "abc" in top["matched_anchors"]
    assert "l" not in top["matched_anchors"]
    assert "m" not in top["matched_anchors"]


def test_evidence_qualifier_demotes_broad_heading_for_content(tmp_path: Path) -> None:
    source = tmp_path / "source.md"
    source.write_text(
        "## Next Steps\n\n"
        "The next production step is to attach the evidence qualifier before final citation packet selection.",
        encoding="utf-8",
    )
    intake(tmp_path / "runtime", DATASET_ID, source)

    result = query(tmp_path / "runtime", DATASET_ID, "What are the next production steps?", top_k=2)
    locations = result["answer_packet"]["locations"]

    assert locations
    assert "evidence qualifier" in locations[0]["text"]
    assert result["answer_packet"]["qualification"]["qualified_count"] >= 1
    rejected_text = "\n".join(row["text"] for row in result["answer_packet"]["rejected_locations"])
    assert "## Next Steps" in rejected_text


def test_evidence_qualifier_refuses_unsupported_low_coverage_query(tmp_path: Path) -> None:
    source = tmp_path / "source.md"
    source.write_text(
        "Compliance policy updates are documented for local datasets.",
        encoding="utf-8",
    )
    intake(tmp_path / "runtime", DATASET_ID, source)

    result = query(tmp_path / "runtime", DATASET_ID, "Where is the unavailable database compliance policy defined?", top_k=3)

    assert result["answer_packet"]["locations"] == []
    assert result["final_answer"]["status"] == "not_enough_information"
    assert result["final_answer"]["citations"] == []
    assert result["final_answer"]["model_used"] == "none"
    assert result["answer_packet"]["qualification"]["support_state"] == "no_qualified_evidence"
    assert result["answer_packet"]["rejected_locations"]
    assert "unsupported_refusal_threshold" in result["answer_packet"]["rejected_locations"][0]["qualification"]["reject_reasons"]


def test_nlp_resolver_does_not_invent_citations_or_use_rejected_locations(tmp_path: Path) -> None:
    source = tmp_path / "source.md"
    source.write_text(
        "AWRAG citation ownership is controlled by the evidence packet.\n\n"
        "Rejected text mentions unavailable database policy but should not answer unsupported policy questions.",
        encoding="utf-8",
    )
    intake(tmp_path / "runtime", DATASET_ID, source)

    result = query(tmp_path / "runtime", DATASET_ID, "What controls citation ownership evidence packet?", top_k=1)
    location_citations = [row["citation"] for row in result["answer_packet"]["locations"]]

    assert result["final_answer"]["citations"] == location_citations
    assert all(citation in result["final_answer"]["text"] for citation in location_citations)
    assert "[CIT" not in result["final_answer"]["text"]
    assert "[AWCIT-" in result["final_answer"]["text"]

def test_batch_questions_writes_summary_and_individual_outputs(tmp_path: Path) -> None:
    source = tmp_path / "source.txt"
    source.write_text(
        "Dataset counts stay local. Citations point to source coordinates.",
        encoding="utf-8",
    )
    runtime = tmp_path / "runtime"
    intake(runtime, DATASET_ID, source)
    questions = tmp_path / "questions.txt"
    questions.write_text(
        "Where do dataset counts stay?\n\nWhere do citations point?\n",
        encoding="utf-8",
    )

    result = batch_questions(runtime, DATASET_ID, questions, top_k=2, workers=4)

    assert result["schema"] == "awrag_batch_run_summary@1"
    assert result["dataset"] == DATASET_ID
    assert result["question_count"] == 2
    assert result["completed"] == 2
    assert result["failed"] == 0
    assert result["model_used"] == "none"
    assert result["persistent_memory"] is False
    assert result["workers_effective"] == 4
    assert result["parallel_execution"] is True
    assert result["avg_query_time"] >= 0
    assert len(result["output_paths"]) == 2
    assert len(set(result["output_paths"])) == 2
    assert Path(result["summary_path"]).exists()
    for output_path in result["output_paths"]:
        payload = json.loads(Path(output_path).read_text(encoding="utf-8"))
        assert payload["schema"] == "awrag_query_result@1"
        assert payload["model_used"] == "none"


def test_batch_questions_rejects_single_worker(tmp_path: Path) -> None:
    source = tmp_path / "source.txt"
    source.write_text("Dataset counts stay local.", encoding="utf-8")
    runtime = tmp_path / "runtime"
    intake(runtime, DATASET_ID, source)
    questions = tmp_path / "questions.txt"
    questions.write_text("Where do dataset counts stay?\n", encoding="utf-8")

    with pytest.raises(ValueError, match="single-core/low-core execution is not allowed"):
        batch_questions(runtime, DATASET_ID, questions, top_k=1, workers=3)


def test_query_refuses_dataset_cloud_mismatch_before_topk(tmp_path: Path) -> None:
    source = tmp_path / "source.txt"
    source.write_text(
        "Prion protein evidence appears in appendix samples. Abnormal PrP prevalence is measured.",
        encoding="utf-8",
    )
    runtime = tmp_path / "runtime"
    intake(runtime, DATASET_ID, source)

    result = query(runtime, DATASET_ID, "How do I make apple pie?", top_k=3)

    assert result["final_answer"]["status"] == "dataset_cloud_mismatch"
    assert result["answer_packet"]["qualification"]["support_state"] == "dataset_cloud_mismatch"
    assert result["dataset_cloud_gate"]["approved"] is False
    assert result["dataset_cloud_gate"]["topk_ran"] is False
    assert result["relation_neighbors"] == []
    assert result["answer_packet"]["locations"] == []
    assert result["output_path"].endswith("_cloud_mismatch.json")


def test_query_runs_when_question_fits_dataset_cloud(tmp_path: Path) -> None:
    source = tmp_path / "source.txt"
    source.write_text(
        "Prion protein evidence appears in appendix samples. Abnormal PrP prevalence is measured.",
        encoding="utf-8",
    )
    runtime = tmp_path / "runtime"
    intake(runtime, DATASET_ID, source)

    result = query(runtime, DATASET_ID, "What measured abnormal PrP prevalence?", top_k=1)

    assert result["dataset_cloud_gate"]["approved"] is True
    assert result["relation_neighbors"]
    assert result["answer_packet"]["qualification"]["support_state"] == "qualified_evidence"


def test_chat_intake_writes_metadata_index_and_block_metadata(tmp_path: Path) -> None:
    source = tmp_path / "chat.md"
    source.write_text(
        "## CHAT_TURN_1\n"
        "CHAT_CONVERSATION_ID: conv-a\n"
        "CHAT_MESSAGE_ID: msg-a\n"
        "CHAT_TITLE: Hardware Settings\n"
        "CHAT_CREATED_AT: 12/14/2024 10:29:26 AM\n"
        "CHAT_SPEAKER: user\n"
        "CHAT_TRUTH_SCOPE: system_doctrine_not_world_truth\n"
        "CHAT_LIFETIME_ALLOWED: false\n"
        "CHAT_TEXT:\n"
        "IA Voltage Mode PCU adaptive. Agent Voltage Target 1024 mV.\n\n"
        "## CHAT_TURN_2\n"
        "CHAT_CONVERSATION_ID: conv-a\n"
        "CHAT_MESSAGE_ID: msg-b\n"
        "CHAT_TITLE: Hardware Settings\n"
        "CHAT_CREATED_AT: 12/15/2024 10:29:26 AM\n"
        "CHAT_SPEAKER: assistant\n"
        "CHAT_TRUTH_SCOPE: system_doctrine_not_world_truth\n"
        "CHAT_LIFETIME_ALLOWED: false\n"
        "CHAT_TEXT:\n"
        "Citations are owned by AWRAG.\n",
        encoding="utf-8",
    )

    result = intake(tmp_path / "runtime", DATASET_ID, source)
    dataset_root = tmp_path / "runtime" / "datasets" / DATASET_ID
    index_path = dataset_root / "state" / "chat_metadata_index.jsonl"

    assert result["chat_metadata_row_count"] == 2
    rows = [json.loads(line) for line in index_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(rows) == 2
    assert rows[0]["schema"] == "awrag_chat_metadata_index_row@1"
    assert rows[0]["conversation_id"] == "conv-a"
    assert rows[0]["message_id"] == "msg-a"
    assert rows[0]["date"] == "2024-12-14"
    assert rows[0]["speaker"] == "user"
    assert rows[0]["lifetime_allowed"] is False
    assert rows[0]["citation_id"].startswith("AWCIT-")


def test_chat_query_can_narrow_by_date_and_speaker(tmp_path: Path) -> None:
    source = tmp_path / "chat.md"
    source.write_text(
        "## CHAT_TURN_1\n"
        "CHAT_CONVERSATION_ID: conv-a\n"
        "CHAT_MESSAGE_ID: msg-a\n"
        "CHAT_TITLE: Hardware Settings\n"
        "CHAT_CREATED_AT: 12/14/2024 10:29:26 AM\n"
        "CHAT_SPEAKER: user\n"
        "CHAT_TRUTH_SCOPE: system_doctrine_not_world_truth\n"
        "CHAT_LIFETIME_ALLOWED: false\n"
        "CHAT_TEXT:\n"
        "IA Voltage Mode PCU adaptive. Agent Voltage Target 1024 mV.\n\n"
        "## CHAT_TURN_2\n"
        "CHAT_CONVERSATION_ID: conv-a\n"
        "CHAT_MESSAGE_ID: msg-b\n"
        "CHAT_TITLE: Hardware Settings\n"
        "CHAT_CREATED_AT: 12/15/2024 10:29:26 AM\n"
        "CHAT_SPEAKER: assistant\n"
        "CHAT_TRUTH_SCOPE: system_doctrine_not_world_truth\n"
        "CHAT_LIFETIME_ALLOWED: false\n"
        "CHAT_TEXT:\n"
        "IA Voltage Mode should be checked later by the assistant.\n",
        encoding="utf-8",
    )
    runtime = tmp_path / "runtime"
    intake(runtime, DATASET_ID, source)

    user_result = query(
        runtime,
        DATASET_ID,
        "voltage mode",
        top_k=2,
        created_before="2024-12-14T23:59:59+00:00",
        speaker="user",
    )
    assistant_result = query(
        runtime,
        DATASET_ID,
        "voltage mode",
        top_k=2,
        created_after="2024-12-15",
        speaker="assistant",
    )

    assert user_result["metadata_filter"]["active"] is True
    assert user_result["answer_packet"]["locations"]
    assert "Agent Voltage Target 1024 mV" in user_result["answer_packet"]["locations"][0]["text"]
    assert assistant_result["answer_packet"]["locations"]
    assert "checked later by the assistant" in assistant_result["answer_packet"]["locations"][0]["text"]


def test_forensic_support_receipt_reconstructs_without_accusing(tmp_path: Path) -> None:
    source = tmp_path / "source.md"
    source.write_text(
        "The operator discussed a 200 module scaffold for emergency continuity.\n"
        "The same record says the scaffold was rejected and deleted before use.\n",
        encoding="utf-8",
    )
    runtime = tmp_path / "runtime"
    intake(runtime, DATASET_ID, source)

    result = query(runtime, DATASET_ID, "Was the 200 module scaffold created and deleted?", top_k=2)
    receipt = result["forensic_support_receipt"]

    assert receipt["schema"] == "awrag_forensic_support_receipt@1"
    assert receipt["mode"] == "reconstructive_not_accusatory"
    assert receipt["support_level"] == "partial"
    assert "L1" in receipt["ladder_hits"]
    assert "L6" in receipt["ladder_hits"]
    assert "artifact_or_subject_referenced" in receipt["supported"]
    assert "deletion_or_rejection_discussed" in receipt["supported"]
    assert "execution_or_deployment_evidenced" in receipt["not_supported"]
    assert receipt["citations"]
    assert receipt["conclusion"].startswith("The record supports")


def test_forensic_support_receipt_marks_absent_evidence_insufficient(tmp_path: Path) -> None:
    source = tmp_path / "source.md"
    source.write_text("Dataset-local counts stay with the dataset.", encoding="utf-8")
    runtime = tmp_path / "runtime"
    intake(runtime, DATASET_ID, source)

    result = query(runtime, DATASET_ID, "Was the missing artifact deployed?", top_k=2)
    receipt = result["forensic_support_receipt"]

    assert result["final_answer"]["status"] == "dataset_cloud_mismatch"
    assert result["dataset_cloud_gate"]["approved"] is False
    assert result["dataset_cloud_gate"]["topk_ran"] is False
    assert receipt["support_level"] == "insufficient"
    assert result["relation_neighbors"] == []
    assert "artifact_or_subject_referenced" in receipt["not_supported"]
    assert receipt["citations"] == []


def test_forensic_support_does_not_treat_conceptual_run_language_as_deployment(tmp_path: Path) -> None:
    source = tmp_path / "source.md"
    source.write_text(
        "The concept was described as modules meant to run infrastructure during an emergency.\n"
        "The operator later said it was not a build plan and rejected it.\n",
        encoding="utf-8",
    )
    runtime = tmp_path / "runtime"
    intake(runtime, DATASET_ID, source)

    result = query(runtime, DATASET_ID, "Were the emergency modules deployed?", top_k=2)
    receipt = result["forensic_support_receipt"]

    assert "L6" in receipt["ladder_hits"]
    assert "L9" not in receipt["ladder_hits"]
    assert "execution_or_deployment_evidenced" in receipt["not_supported"]
