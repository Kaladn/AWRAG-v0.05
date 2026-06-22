from __future__ import annotations

import json
from pathlib import Path

from awrag.engine.anchors import symbol_bytes, symbol_for
from awrag.engine.storage import RELATION_RECORD
from experiments.answer_cloud_reform import run_reform
from experiments.question_cloud_preflight import run_preflight


def test_question_cloud_preflight_is_report_only(tmp_path: Path) -> None:
    query_map = tmp_path / "query_map.json"
    lexicon = tmp_path / "dataset_lexicon.json"
    relation_counts = tmp_path / "relation_counts.awbin"
    anchor_counts = tmp_path / "anchor_counts.awbin"
    block_anchor = tmp_path / "block_anchor_postings.awbin"
    out = tmp_path / "preflight"

    query_map.write_text(
        json.dumps({
            "schema": "test_query_map@1",
            "test_queries": [
                {
                    "query_id": "q1",
                    "question": "Alpha beta signal.",
                    "line_number": 1,
                    "test_line_number": 1,
                }
            ],
        }),
        encoding="utf-8",
    )
    anchors = ["alpha", "beta", "signal", "gamma"]
    lexicon.write_text(
        json.dumps({
            "schema": "awrag_dataset_lexicon@1",
            "anchors": [
                {"anchor": anchor, "symbol": symbol_for(anchor), "observations": 4}
                for anchor in anchors
            ],
        }),
        encoding="utf-8",
    )
    relation_counts.write_bytes(
        RELATION_RECORD.pack(symbol_bytes("alpha"), symbol_bytes("gamma"), 1, 7)
    )
    anchor_counts.write_bytes(b"")
    block_anchor.write_bytes(b"")

    result = run_preflight(
        query_map_path=query_map,
        lexicon_path=lexicon,
        relation_counts_path=relation_counts,
        anchor_counts_path=anchor_counts,
        block_anchor_path=block_anchor,
        out_dir=out,
        dataset="unit",
    )

    assert result["questions_processed"] == 1
    assert result["mutation_detected"] is False
    assert (out / "questions_original_vs_suggested.jsonl").exists()
    receipt = json.loads((out / "receipts" / "run_receipt.json").read_text(encoding="utf-8"))
    assert receipt["search_ran"] is False
    assert receipt["topk_ran"] is False
    assert receipt["answering_ran"] is False


def test_answer_cloud_reform_splits_evidence_from_pretty_answer(tmp_path: Path) -> None:
    aw_output = tmp_path / "query_output.json"
    comparison = tmp_path / "comparison.json"
    preflight = tmp_path / "preflight.jsonl"
    out = tmp_path / "reform"

    aw_output.write_text(
        json.dumps({
            "answer_packet": {
                "locations": [
                    {
                        "citation": "[AWCIT-test]",
                        "line_start": 10,
                        "line_end": 12,
                        "score": 12.5,
                        "density_score": 4.2,
                        "direct_hit_count": 3,
                        "block_anchor_count": 44,
                        "text": (
                            "SCIFACT_DOC_ID: doc-1\n"
                            "CHAT_CONVERSATION_ID: conv-1\n"
                            "CHAT_MESSAGE_ID: msg-1\n"
                            "TITLE: Alpha report\n"
                            "TEXT: Alpha beta signal is supported by the cited document."
                        ),
                    }
                ]
            }
        }),
        encoding="utf-8",
    )
    comparison.write_text(
        json.dumps({
            "records": [
                {
                    "question_id": "q1",
                    "expected_doc_ids": ["doc-1"],
                    "original_question": "Alpha beta signal?",
                    "suggested_question": "Alpha beta signal?",
                    "suggested_output_path": str(aw_output),
                    "suggested_hit_at_10": True,
                    "original_hit_at_10": True,
                    "suggested_answer_status": "answered_from_awrag_locations",
                    "suggested_answer_text": "TITLE: Alpha report [AWCIT-test]",
                    "gold_hit_change": "same_hit_at_10_state",
                }
            ]
        }),
        encoding="utf-8",
    )
    preflight.write_text(
        json.dumps({
            "question_id": "q1",
            "low_fit_anchors": [],
        }) + "\n",
        encoding="utf-8",
    )

    result = run_reform(comparison_path=comparison, preflight_path=preflight, out_dir=out)

    assert result["records_processed"] == 1
    assert result["mutation_detected"] is False
    evidence_path = out / "evidence_trace" / "SCIFACT_Qq1_evidence_trace.json"
    pretty_path = out / "pretty_answer" / "SCIFACT_Qq1_pretty_answer.json"
    assert evidence_path.exists()
    assert pretty_path.exists()
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    pretty = json.loads(pretty_path.read_text(encoding="utf-8"))
    assert evidence["citations"][0]["message_id"] == "msg-1"
    assert pretty["start_message_id"] == "msg-1"
    assert "Alpha beta signal is supported" in pretty["answer"]
    receipt = json.loads((out / "receipts" / "run_receipt.json").read_text(encoding="utf-8"))
    assert receipt["separate_evidence_trace_files"] is True
    assert receipt["separate_pretty_answer_files"] is True
    assert receipt["retrieval_ran"] is False
