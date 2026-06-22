from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

from awrag.engine.anchors import anchorize


SCHEMA = "awrag_answer_cloud_reform@1"
WS = "\\s"


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="answer_cloud_reform",
        description="Report-only evidence-to-speech reform. Reads existing AW outputs; does not retrieve.",
    )
    parser.add_argument("--comparison", type=Path, required=True)
    parser.add_argument("--preflight", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = run_reform(comparison_path=args.comparison, preflight_path=args.preflight, out_dir=args.out)
    print(json.dumps(result, ensure_ascii=True))


def run_reform(*, comparison_path: Path, preflight_path: Path, out_dir: Path) -> dict[str, Any]:
    if not comparison_path.exists():
        raise FileNotFoundError(f"comparison input not found: {comparison_path}")
    if not preflight_path.exists():
        raise FileNotFoundError(f"preflight input not found: {preflight_path}")

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "per_case").mkdir(parents=True, exist_ok=True)
    (out_dir / "evidence_trace").mkdir(parents=True, exist_ok=True)
    (out_dir / "pretty_answer").mkdir(parents=True, exist_ok=True)
    (out_dir / "receipts").mkdir(parents=True, exist_ok=True)

    before = [_artifact_state(comparison_path), _artifact_state(preflight_path)]
    comparison = json.loads(comparison_path.read_text(encoding="utf-8"))
    preflight = _load_preflight(preflight_path)
    records = [
        _reform_record(row, preflight.get(str(row["question_id"]), {}))
        for row in comparison.get("records", [])
    ]

    for record in records:
        qid = _safe_id(record["question_id"])
        _write_json(out_dir / "per_case" / f"SCIFACT_Q{qid}_answer_cloud_reform.json", record)
        _write_case_markdown(out_dir / "per_case" / f"SCIFACT_Q{qid}_answer_cloud_reform.md", record)
        _write_json(out_dir / "evidence_trace" / f"SCIFACT_Q{qid}_evidence_trace.json", _evidence_trace_record(record))
        _write_json(out_dir / "pretty_answer" / f"SCIFACT_Q{qid}_pretty_answer.json", _pretty_answer_record(record))
        _write_pretty_markdown(out_dir / "pretty_answer" / f"SCIFACT_Q{qid}_pretty_answer.md", record)

    summary = _summary(records, comparison_path=comparison_path, preflight_path=preflight_path)
    _write_json(out_dir / "ANSWER_CLOUD_REFORM_SUMMARY.json", summary)
    _write_summary_markdown(out_dir / "ANSWER_CLOUD_REFORM_SUMMARY.md", summary)
    _write_jsonl(out_dir / "answer_cloud_reform_records.jsonl", records)

    after = [_artifact_state(comparison_path), _artifact_state(preflight_path)]
    _write_json(out_dir / "receipts" / "run_receipt.json", {
        "schema": "awrag_answer_cloud_reform_run_receipt@1",
        "mode": "report_only",
        "records_written": len(records),
        "separate_evidence_trace_files": True,
        "separate_pretty_answer_files": True,
        "retrieval_ran": False,
        "topk_ran": False,
        "answering_ran": False,
        "model_used": "none",
        "embeddings_used": False,
        "reranker_used": False,
        "backend_mutation": False,
        "out_dir": str(out_dir),
    })
    _write_json(out_dir / "receipts" / "inputs_receipt.json", {
        "schema": "awrag_answer_cloud_reform_inputs_receipt@1",
        "comparison_path": str(comparison_path),
        "preflight_path": str(preflight_path),
        "comparison_sha256": _sha256(comparison_path),
        "preflight_sha256": _sha256(preflight_path),
    })
    mutation_detected = before != after
    _write_json(out_dir / "receipts" / "no_mutation_receipt.json", {
        "schema": "awrag_answer_cloud_reform_no_mutation_receipt@1",
        "mutation_detected": mutation_detected,
        "before": before,
        "after": after,
    })
    return {
        "schema": SCHEMA,
        "records_processed": len(records),
        "forms": summary["form_counts"],
        "mutation_detected": mutation_detected,
        "out_dir": str(out_dir),
    }


def _load_preflight(path: Path) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        out[str(row["question_id"])] = row
    return out


def _reform_record(row: dict[str, Any], preflight: dict[str, Any]) -> dict[str, Any]:
    current_answer = str(row.get("suggested_answer_text") or "")
    current_status = str(row.get("suggested_answer_status") or "")
    locations = _load_locations(row.get("suggested_output_path"))
    citations = [_citation_summary(loc) for loc in locations]
    message_ids = [str(item.get("message_id")) for item in citations if item.get("message_id")]
    evidence_snippets = _evidence_snippets(
        locations,
        question=str(row.get("suggested_question") or row.get("original_question") or ""),
    )
    location_count = len(locations)
    gold_hit = bool(row.get("suggested_hit_at_10"))
    original_gold_hit = bool(row.get("original_hit_at_10"))
    low_fit = preflight.get("low_fit_anchors", row.get("low_fit_anchors", []))
    missing_support = _missing_support_notes(row, preflight, location_count)
    answer_anchors = anchorize(current_answer)
    question_anchors = anchorize(str(row.get("suggested_question") or row.get("original_question") or ""))
    missing_speech_anchors = [anchor for anchor in question_anchors if anchor not in set(answer_anchors)]
    selected_form = _select_form(
        current_status=current_status,
        location_count=location_count,
        gold_hit=gold_hit,
        original_gold_hit=original_gold_hit,
        low_fit=low_fit,
        missing_support=missing_support,
        evidence_snippets=evidence_snippets,
        question_anchors=question_anchors,
    )
    reformed = _render_reformed_answer(
        selected_form=selected_form,
        current_answer=current_answer,
        row=row,
        citations=citations,
        evidence_snippets=evidence_snippets,
        missing_support=missing_support,
        low_fit=low_fit,
        location_count=location_count,
    )
    document_only_answer = _document_only_answer(
        selected_form=selected_form,
        evidence_snippets=evidence_snippets,
        location_count=location_count,
    )
    return {
        "schema": "awrag_answer_cloud_reform_record@1",
        "question_id": str(row["question_id"]),
        "original_question": row.get("original_question"),
        "suggested_question": row.get("suggested_question"),
        "current_aw_answer": current_answer,
        "current_aw_status": current_status,
        "evidence_status": {
            "location_count": location_count,
            "suggested_hit_at_10": gold_hit,
            "original_hit_at_10": original_gold_hit,
            "gold_hit_change": row.get("gold_hit_change"),
            "start_message_id": message_ids[0] if message_ids else None,
            "end_message_id": message_ids[-1] if message_ids else None,
        },
        "selected_answer_form": selected_form,
        "missing_speech_anchors": missing_speech_anchors[:25],
        "missing_support_notes": missing_support,
        "evidence_snippets": evidence_snippets,
        "document_only_answer": document_only_answer,
        "reformed_answer": reformed,
        "citations": citations,
        "rank_key_summary": _rank_key_summary(locations),
        "receipt": {
            "retrieval_ran": False,
            "topk_ran": False,
            "answering_ran": False,
            "model_used": "none",
            "source_output_path": row.get("suggested_output_path"),
            "preflight_used": bool(preflight),
            "evidence_trace_file_required": True,
            "pretty_answer_file_required": True,
        },
    }


def _select_form(
    *,
    current_status: str,
    location_count: int,
    gold_hit: bool,
    original_gold_hit: bool,
    low_fit: list[dict[str, Any]],
    missing_support: list[str],
    evidence_snippets: list[dict[str, Any]],
    question_anchors: list[str],
) -> str:
    if current_status == "not_enough_information" or location_count == 0:
        return "NO_SUPPORT_FOUND"
    combined_matches: set[str] = set()
    for item in evidence_snippets:
        combined_matches.update(str(anchor) for anchor in item.get("matched_question_anchors", []))
    best_snippet_matches = len(combined_matches)
    value_anchors = {anchor for anchor in question_anchors if any(ch.isdigit() for ch in anchor)}
    value_support = len(value_anchors & combined_matches)
    enough_anchor_support = best_snippet_matches >= max(3, min(5, len(set(question_anchors)) // 2))
    exact_value_supported = not value_anchors or value_support > 0
    if gold_hit and enough_anchor_support and exact_value_supported:
        return "CLEAN_SUPPORTED_ANSWER"
    if not gold_hit and location_count:
        return "BENCHMARK_MISMATCH"
    if missing_support or low_fit:
        return "RELATED_BUT_UNSUPPORTED"
    if gold_hit and original_gold_hit:
        return "CLEAN_SUPPORTED_ANSWER"
    return "HUMAN_REVIEW"


def _render_reformed_answer(
    *,
    selected_form: str,
    current_answer: str,
    row: dict[str, Any],
    citations: list[dict[str, Any]],
    evidence_snippets: list[dict[str, Any]],
    missing_support: list[str],
    low_fit: list[dict[str, Any]],
    location_count: int,
) -> str:
    cite_text = _citation_text(citations)
    document_answer = _document_only_answer(
        selected_form=selected_form,
        evidence_snippets=evidence_snippets,
        location_count=location_count,
    )
    low_fit_text = ", ".join(str(item.get("anchor")) for item in low_fit[:5]) if low_fit else "none"
    support_text = "; ".join(missing_support) if missing_support else "none"

    if selected_form == "NO_SUPPORT_FOUND":
        return (
            "AW cannot support this from the current admitted evidence packet. "
            f"The packet produced {location_count} cited locations. "
            f"Low-fit anchors: {low_fit_text}. "
            "No replacement truth is asserted."
        )
    if selected_form == "BENCHMARK_MISMATCH":
        return (
            "AW found related cited evidence, but the expected benchmark document was not recovered in the current top-10 packet. "
            f"Document-only speech: {document_answer} "
            f"Citations: {cite_text}. "
            "Treat this as evidence-speech for review, not a corrected benchmark answer."
        )
    if selected_form == "RELATED_BUT_UNSUPPORTED":
        return (
            "AW found cited evidence related to the question, but the answer cloud still carries unresolved support warnings. "
            f"Warnings: {support_text}. Low-fit anchors: {low_fit_text}. "
            f"Document-only speech: {document_answer} "
            f"Citations: {cite_text}."
        )
    if selected_form == "EVIDENCE_SPLIT":
        return (
            "The evidence field appears split. AW should not merge it into one claim without review. "
            f"Current AW answer: {current_answer} Citations: {cite_text}."
        )
    if selected_form == "CLEAN_SUPPORTED_ANSWER":
        return (
            f"AW supports the claim from the cited packet: {document_answer} "
            f"Citations: {cite_text}."
        )
    return (
        "Human review is required before reforming this answer into a stronger speech form. "
        f"Current AW answer: {current_answer} Citations: {cite_text}."
    )


def _missing_support_notes(row: dict[str, Any], preflight: dict[str, Any], location_count: int) -> list[str]:
    notes: list[str] = []
    if row.get("suggested_question") and row.get("suggested_question") != row.get("original_question"):
        notes.append("question shape was changed by preflight")
    if row.get("suggested_hit_at_10") is False:
        notes.append("expected benchmark document absent from suggested top-10")
    if location_count == 0:
        notes.append("no cited AW locations in current packet")
    if preflight.get("low_fit_anchors"):
        notes.append("preflight detected low-fit anchors")
    return notes


def _load_locations(path_value: Any) -> list[dict[str, Any]]:
    if not path_value:
        return []
    path = Path(str(path_value))
    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    return list(payload.get("answer_packet", {}).get("locations", []))


def _evidence_snippets(locations: list[dict[str, Any]], *, question: str) -> list[dict[str, Any]]:
    question_anchors = set(anchorize(question))
    question_values = {anchor for anchor in question_anchors if any(ch.isdigit() for ch in anchor)}
    out: list[dict[str, Any]] = []
    for loc in locations:
        citation = str(loc.get("citation") or "")
        text = _document_text(str(loc.get("text") or ""))
        sentences = _sentences(text)
        scored: list[tuple[int, int, str, list[str]]] = []
        for sentence in sentences:
            sentence_anchors = set(anchorize(sentence))
            shared = sorted(question_anchors & sentence_anchors)
            value_hits = sorted(question_values & sentence_anchors)
            score = len(shared) + (3 * len(value_hits))
            if score:
                scored.append((score, len(value_hits), sentence, shared))
        if not scored and sentences:
            scored.append((0, 0, sentences[0], []))
        for score, value_hit_count, sentence, shared in sorted(scored, key=lambda item: (-item[0], -item[1], len(item[2])))[:2]:
            out.append({
                "citation": citation,
                "line_start": loc.get("line_start"),
        "line_end": loc.get("line_end"),
        "doc_id": _doc_id(str(loc.get("text") or "")),
        "conversation_id": _metadata_value(str(loc.get("text") or ""), "CHAT_CONVERSATION_ID"),
        "message_id": _metadata_value(str(loc.get("text") or ""), "CHAT_MESSAGE_ID"),
        "snippet": sentence,
                "matched_question_anchors": shared,
                "snippet_score": score,
            })
    return out[:5]


def _document_only_answer(
    *,
    selected_form: str,
    evidence_snippets: list[dict[str, Any]],
    location_count: int,
) -> str:
    if not evidence_snippets:
        return (
            "No cited document sentence was available to form a document-only answer."
            if location_count
            else "No cited AW locations were available to form a document-only answer."
        )
    primary = evidence_snippets[0]
    citation = primary.get("citation") or "uncited"
    sentence = str(primary.get("snippet") or "").strip()
    if selected_form == "NO_SUPPORT_FOUND":
        return "No cited AW locations support the claim."
    if selected_form == "BENCHMARK_MISMATCH":
        return f"Related cited document content: {sentence} {citation}"
    if selected_form == "RELATED_BUT_UNSUPPORTED":
        return f"Related cited document content: {sentence} {citation}"
    if selected_form == "CLEAN_SUPPORTED_ANSWER":
        return f"{sentence} {citation}"
    return f"Review cited document content: {sentence} {citation}"


def _document_text(raw: str) -> str:
    marker = "TEXT:"
    if marker in raw:
        return raw.split(marker, 1)[1].strip()
    return raw.strip()


def _sentences(text: str) -> list[str]:
    compact = re.sub(r"\s+", " ", text).strip()
    if not compact:
        return []
    parts = re.split(r"(?<=[.!?])\s+", compact)
    return [part.strip() for part in parts if part.strip()]


def _doc_id(raw: str) -> str | None:
    match = re.search("SCIFACT_DOC_ID:" + WS + "*([^" + WS + "]+)", raw)
    return match.group(1) if match else None


def _citation_summary(location: dict[str, Any]) -> dict[str, Any]:
    text = str(location.get("text", ""))
    doc_id = None
    title = None
    doc_match = re.search("SCIFACT_DOC_ID:" + WS + "*([^" + WS + "]+)", text)
    title_match = re.search("TITLE:" + WS + "*(.*?)" + WS + "+TEXT:", text)
    if doc_match:
        doc_id = doc_match.group(1)
    if title_match:
        title = title_match.group(1)
    return {
        "citation": location.get("citation"),
        "doc_id": doc_id,
        "title": title,
        "line_start": location.get("line_start"),
        "line_end": location.get("line_end"),
        "conversation_id": _metadata_value(text, "CHAT_CONVERSATION_ID"),
        "message_id": _metadata_value(text, "CHAT_MESSAGE_ID"),
        "score": location.get("score"),
        "density_score": location.get("density_score"),
        "direct_hit_count": location.get("direct_hit_count"),
    }


def _rank_key_summary(locations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for rank, loc in enumerate(locations, start=1):
        out.append({
            "rank": rank,
            "direct_hit_count": loc.get("direct_hit_count"),
            "density_score": loc.get("density_score"),
            "score": loc.get("score"),
            "block_anchor_count": loc.get("block_anchor_count"),
        })
    return out


def _metadata_value(raw: str, key: str) -> str | None:
    for line in str(raw or "").splitlines():
        if ":" not in line:
            continue
        left, right = line.split(":", 1)
        if left.strip() == key:
            value = right.strip()
            return value or None
    return None


def _citation_text(citations: list[dict[str, Any]]) -> str:
    values = [str(item.get("citation")) for item in citations if item.get("citation")]
    return ", ".join(values[:5]) if values else "none"


def _summary(records: list[dict[str, Any]], *, comparison_path: Path, preflight_path: Path) -> dict[str, Any]:
    forms = Counter(str(row["selected_answer_form"]) for row in records)
    return {
        "schema": "awrag_answer_cloud_reform_summary@1",
        "records_processed": len(records),
        "form_counts": dict(forms.most_common()),
        "comparison_path": str(comparison_path),
        "preflight_path": str(preflight_path),
        "model_used": "none",
        "retrieval_ran": False,
        "topk_ran": False,
        "answering_ran": False,
    }


def _write_summary_markdown(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# Answer Cloud Reform Summary",
        "",
        "Report-only evidence-to-speech reform. Existing AW outputs only.",
        "",
        "```text",
        f"records_processed: {summary['records_processed']}",
        "model_used: none",
        "retrieval_ran: false",
        "topk_ran: false",
        "answering_ran: false",
        "```",
        "",
        "## Form Counts",
        "",
    ]
    for form, count in summary["form_counts"].items():
        lines.append(f"- `{form}`: {count}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_case_markdown(path: Path, record: dict[str, Any]) -> None:
    lines = [
        f"# Answer Cloud Reform: SCIFACT Q{record['question_id']}",
        "",
        f"Form: `{record['selected_answer_form']}`",
        "",
        "## Original Question",
        "",
        str(record.get("original_question") or ""),
        "",
        "## Suggested Question",
        "",
        str(record.get("suggested_question") or ""),
        "",
        "## Current AW Answer",
        "",
        str(record.get("current_aw_answer") or ""),
        "",
        "## Reformed Answer",
        "",
        str(record.get("reformed_answer") or ""),
        "",
        "## Document-Only Answer",
        "",
        str(record.get("document_only_answer") or ""),
        "",
        "## Evidence Snippets",
        "",
    ]
    for snippet in record.get("evidence_snippets", []):
        lines.append(
            f"- {snippet.get('citation')} lines {snippet.get('line_start')}-{snippet.get('line_end')}: "
            f"{snippet.get('snippet')}"
        )
    if not record.get("evidence_snippets"):
        lines.append("- none")
    lines.extend([
        "",
        "## Citation / Rank Key Summary",
        "",
    ])
    for item in record.get("citations", []):
        lines.append(
            f"- {item.get('citation')} doc={item.get('doc_id')} "
            f"direct={item.get('direct_hit_count')} density={item.get('density_score')} score={item.get('score')}"
        )
    if not record.get("citations"):
        lines.append("- none")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _evidence_trace_record(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema": "awrag_answer_cloud_evidence_trace@1",
        "question_id": record["question_id"],
        "original_question": record.get("original_question"),
        "suggested_question": record.get("suggested_question"),
        "selected_answer_form": record.get("selected_answer_form"),
        "evidence_status": record.get("evidence_status"),
        "missing_speech_anchors": record.get("missing_speech_anchors", []),
        "missing_support_notes": record.get("missing_support_notes", []),
        "evidence_snippets": record.get("evidence_snippets", []),
        "citations": record.get("citations", []),
        "rank_key_summary": record.get("rank_key_summary", []),
        "receipt": record.get("receipt", {}),
    }


def _pretty_answer_record(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema": "awrag_answer_cloud_pretty_answer@1",
        "question_id": record["question_id"],
        "selected_answer_form": record.get("selected_answer_form"),
        "question": record.get("suggested_question") or record.get("original_question"),
        "answer": record.get("document_only_answer"),
        "citations": [
            {
                "citation": item.get("citation"),
                "doc_id": item.get("doc_id"),
                "line_start": item.get("line_start"),
                "line_end": item.get("line_end"),
            }
            for item in record.get("citations", [])
        ],
        "start_message_id": (record.get("evidence_status") or {}).get("start_message_id"),
        "end_message_id": (record.get("evidence_status") or {}).get("end_message_id"),
    }


def _write_pretty_markdown(path: Path, record: dict[str, Any]) -> None:
    status = record.get("evidence_status") or {}
    lines = [
        f"# Pretty Answer: SCIFACT Q{record['question_id']}",
        "",
        f"Form: `{record.get('selected_answer_form')}`",
        "",
        "## Question",
        "",
        str(record.get("suggested_question") or record.get("original_question") or ""),
        "",
        "## Answer",
        "",
        str(record.get("document_only_answer") or ""),
        "",
        "## Citations",
        "",
    ]
    for item in record.get("citations", []):
        lines.append(
            f"- {item.get('citation')} doc={item.get('doc_id')} "
            f"lines={item.get('line_start')}-{item.get('line_end')}"
        )
    if not record.get("citations"):
        lines.append("- none")
    lines.extend([
        "",
        "## Message Window",
        "",
        f"start_message_id: {status.get('start_message_id')}",
        f"end_message_id: {status.get('end_message_id')}",
    ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _artifact_state(path: Path) -> dict[str, Any]:
    stat = path.stat()
    return {
        "path": str(path),
        "size": int(stat.st_size),
        "sha256": _sha256(path),
        "modified_ns": int(stat.st_mtime_ns),
    }


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=True) + "\n")


def _safe_id(value: Any) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", str(value))


if __name__ == "__main__":
    main()
