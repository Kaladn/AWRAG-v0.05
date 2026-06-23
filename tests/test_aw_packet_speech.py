from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from awrag.engine.packet_speech import run_packet_speech


def test_packet_speech_splits_evidence_trace_from_pretty_answer(tmp_path: Path) -> None:
    packet = tmp_path / "query_packet.json"
    packet.write_text(
        json.dumps({
            "schema": "awrag_query_result@1",
            "dataset_id": "unit",
            "question": "What supports alpha beta signal?",
            "question_anchors": ["what", "supports", "alpha", "beta", "signal"],
            "model_used": "none",
            "model_may_search": False,
            "answer_packet": {
                "instruction": "Use cited local evidence coordinates only.",
                "citations_owned_by": "AWRAG",
                "qualification": {"support_state": "qualified_evidence"},
                "qualification_receipts": [],
                "locations": [
                    {
                        "citation": "[AWCIT-test]",
                        "file_path": "source.md",
                        "line_start": 10,
                        "line_end": 12,
                        "score": 12.5,
                        "density_score": 4.2,
                        "direct_hit_count": 3,
                        "block_anchor_count": 44,
                        "direct_matched_anchors": ["alpha", "beta", "signal"],
                        "matched_anchors": ["alpha", "beta", "signal"],
                        "text": (
                            "SCIFACT_DOC_ID: doc-1\n"
                            "CHAT_CONVERSATION_ID: conv-1\n"
                            "CHAT_MESSAGE_ID: msg-1\n"
                            "TEXT: Alpha beta signal is supported by the cited document."
                        ),
                    }
                ],
                "rejected_locations": [],
            },
            "final_answer": {
                "status": "answered_from_awrag_locations",
                "model_used": "none",
                "model_may_search": False,
                "citations": ["[AWCIT-test]"],
            },
        }),
        encoding="utf-8",
    )

    out = tmp_path / "speech"
    result = run_packet_speech(packet_paths=[packet], out_dir=out)

    assert result["records_processed"] == 1
    assert result["retrieval_ran"] is False
    assert result["topk_ran"] is False
    assert result["intake_ran"] is False
    assert result["model_used"] == "none"
    assert result["model_may_search"] is False
    assert result["input_mutation_detected"] is False

    case_id = result["records"][0]["case_id"]
    evidence_path = out / "evidence_trace" / f"{case_id}_evidence_trace.json"
    pretty_path = out / "pretty_answer" / f"{case_id}_pretty_answer.json"
    assert evidence_path.exists()
    assert pretty_path.exists()

    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    pretty = json.loads(pretty_path.read_text(encoding="utf-8"))
    assert evidence["schema"] == "awrag_packet_speech_evidence_trace@0"
    assert pretty["schema"] == "awrag_packet_speech_pretty_answer@0"
    assert evidence["citations"][0]["citation"] == "[AWCIT-test]"
    assert evidence["citations"][0]["message_id"] == "msg-1"
    assert pretty["start_message_id"] == "msg-1"
    assert pretty["selected_answer_form"] == "SUPPORTED_CLAIM"
    assert "Alpha beta signal is supported" in pretty["answer"]
    assert "[AWCIT-test]" in pretty["answer"]
    assert pretty["rank_key_summary"][0]["direct_hit_count"] == 3

    receipt = json.loads((out / "receipts" / "run_receipt.json").read_text(encoding="utf-8"))
    assert receipt["retrieval_ran"] is False
    assert receipt["separate_evidence_trace_files"] is True
    assert receipt["separate_pretty_answer_files"] is True


def test_packet_speech_refuses_when_no_qualified_locations(tmp_path: Path) -> None:
    packet = tmp_path / "empty_packet.json"
    packet.write_text(
        json.dumps({
            "question": "Where is the missing evidence?",
            "question_anchors": ["where", "missing", "evidence"],
            "model_used": "none",
            "model_may_search": False,
            "answer_packet": {
                "qualification": {"support_state": "no_qualified_evidence"},
                "locations": [],
                "rejected_locations": [{"citation": "[AWCIT-rejected]"}],
            },
            "final_answer": {
                "status": "not_enough_information",
                "model_used": "none",
                "model_may_search": False,
                "citations": [],
            },
        }),
        encoding="utf-8",
    )

    out = tmp_path / "speech"
    result = run_packet_speech(packet_paths=[packet], out_dir=out)
    case_id = result["records"][0]["case_id"]
    pretty = json.loads((out / "pretty_answer" / f"{case_id}_pretty_answer.json").read_text(encoding="utf-8"))
    evidence = json.loads((out / "evidence_trace" / f"{case_id}_evidence_trace.json").read_text(encoding="utf-8"))

    assert pretty["selected_answer_form"] == "NO_SUPPORT_FOUND"
    assert pretty["citations"] == []
    assert "cannot support" in pretty["answer"]
    assert evidence["locations"] == []
    assert evidence["rejected_locations"]


def test_packet_speech_qualifies_weak_generic_evidence(tmp_path: Path) -> None:
    packet = tmp_path / "weak_packet.json"
    packet.write_text(
        json.dumps({
            "question": "Who won the 2026 world cup final?",
            "question_anchors": ["who", "won", "the", "2026", "world", "cup", "final"],
            "model_used": "none",
            "model_may_search": False,
            "answer_packet": {
                "qualification": {"support_state": "qualified_evidence"},
                "locations": [
                    {
                        "citation": "[AWCIT-generic]",
                        "file_path": "generic.md",
                        "line_start": 1,
                        "line_end": 2,
                        "score": 3.1,
                        "density_score": 0.4,
                        "direct_hit_count": 1,
                        "direct_matched_anchors": ["final"],
                        "matched_anchors": ["final"],
                        "text": "TEXT: The final report describes a local software release.",
                    }
                ],
            },
            "final_answer": {"status": "answered_from_awrag_locations", "model_used": "none", "model_may_search": False},
        }),
        encoding="utf-8",
    )

    out = tmp_path / "speech"
    result = run_packet_speech(packet_paths=[packet], out_dir=out)
    case_id = result["records"][0]["case_id"]
    pretty = json.loads((out / "pretty_answer" / f"{case_id}_pretty_answer.json").read_text(encoding="utf-8"))

    assert pretty["selected_answer_form"] == "WEAK_GENERIC_EVIDENCE"
    assert "too generic" in pretty["answer"]
    assert "[AWCIT-generic]" in pretty["answer"]


def test_packet_speech_uses_aw_qualification_terms_before_expanded_anchor_noise(tmp_path: Path) -> None:
    packet = tmp_path / "speech_contract_packet.json"
    packet.write_text(
        json.dumps({
            "question": "What is the AW speech contract for evidence trace and pretty answer?",
            "question_anchors": [
                "aw",
                "speech",
                "speechs",
                "contract",
                "contracts",
                "evidence",
                "evidences",
                "trace",
                "traces",
                "pretty",
                "prettys",
                "answer",
                "answers",
            ],
            "model_used": "none",
            "model_may_search": False,
            "answer_packet": {
                "qualification": {
                    "support_state": "qualified_evidence",
                    "required_terms": ["aw", "speech", "contract", "trace", "pretty"],
                },
                "qualification_receipts": [
                    {
                        "candidate": "[AWCIT-contract]",
                        "qualified": True,
                        "covered_terms": ["aw", "speech", "contract", "trace", "pretty"],
                        "missing_terms": [],
                        "coverage": 1.0,
                    }
                ],
                "locations": [
                    {
                        "citation": "[AWCIT-contract]",
                        "file_path": "roadmap.md",
                        "line_start": 20,
                        "line_end": 26,
                        "score": 19.3,
                        "density_score": 0.39,
                        "direct_hit_count": 7,
                        "direct_matched_anchors": ["aw", "speech", "contract", "trace", "pretty"],
                        "matched_anchors": ["aw", "speech", "contract", "trace", "pretty"],
                        "text": (
                            "TEXT: The current product shape keeps evidence trace and pretty answer separation "
                            "inside the AW speech contract."
                        ),
                    }
                ],
            },
            "final_answer": {"status": "answered_from_awrag_locations", "model_used": "none", "model_may_search": False},
        }),
        encoding="utf-8",
    )

    out = tmp_path / "speech"
    result = run_packet_speech(packet_paths=[packet], out_dir=out)
    case_id = result["records"][0]["case_id"]
    pretty = json.loads((out / "pretty_answer" / f"{case_id}_pretty_answer.json").read_text(encoding="utf-8"))
    evidence = json.loads((out / "evidence_trace" / f"{case_id}_evidence_trace.json").read_text(encoding="utf-8"))

    assert pretty["selected_answer_form"] == "SUPPORTED_CLAIM"
    assert pretty["support_reasons"] == ["AW qualification receipts cover the required question terms"]
    assert evidence["support_metrics"]["qualification_required_term_coverage"] == 1.0
    assert evidence["support_metrics"]["wider_context_policy"] == "verification_only_unless_additional_required_terms_are_supported"


def test_packet_speech_is_promoted_to_awrag_cli(tmp_path: Path) -> None:
    packet = tmp_path / "cli_packet.json"
    packet.write_text(
        json.dumps({
            "question": "What supports alpha beta signal?",
            "question_anchors": ["what", "supports", "alpha", "beta", "signal"],
            "model_used": "none",
            "model_may_search": False,
            "answer_packet": {
                "qualification": {"support_state": "qualified_evidence", "required_terms": ["alpha", "beta", "signal"]},
                "qualification_receipts": [
                    {
                        "candidate": "[AWCIT-cli]",
                        "qualified": True,
                        "covered_terms": ["alpha", "beta", "signal"],
                        "missing_terms": [],
                    }
                ],
                "locations": [
                    {
                        "citation": "[AWCIT-cli]",
                        "file_path": "source.md",
                        "line_start": 1,
                        "line_end": 2,
                        "score": 10.0,
                        "density_score": 2.0,
                        "direct_hit_count": 3,
                        "direct_matched_anchors": ["alpha", "beta", "signal"],
                        "matched_anchors": ["alpha", "beta", "signal"],
                        "text": "TEXT: Alpha beta signal is supported by the cited packet.",
                    }
                ],
            },
            "final_answer": {"status": "answered_from_awrag_locations", "model_used": "none", "model_may_search": False},
        }),
        encoding="utf-8",
    )
    out = tmp_path / "cli_speech"

    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "awrag.cli",
            "packet-speech",
            "--packet",
            str(packet),
            "--out",
            str(out),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(proc.stdout)
    assert payload["records_processed"] == 1
    assert payload["retrieval_ran"] is False
    assert payload["topk_ran"] is False
    assert payload["intake_ran"] is False
    assert payload["model_used"] == "none"
    case_id = payload["records"][0]["case_id"]
    assert (out / "evidence_trace" / f"{case_id}_evidence_trace.json").is_file()
    assert (out / "pretty_answer" / f"{case_id}_pretty_answer.json").is_file()
