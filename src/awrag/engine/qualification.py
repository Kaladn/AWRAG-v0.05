from __future__ import annotations

import re
from collections import Counter
from typing import Any

from .anchors import STOP_ANCHORS, anchorize


def qualify_evidence(question: str, q_counter: Counter[str], candidates: list[dict[str, Any]], *, top_k: int) -> dict[str, Any]:
    question_terms = [anchor for anchor in q_counter if anchor not in STOP_ANCHORS]
    required_terms = significant_question_terms(question_terms)
    path_intent = has_path_or_config_intent(question)
    unsupported_intent = len(required_terms) >= 4

    receipts: list[dict[str, Any]] = []
    qualified_rows: list[tuple[float, dict[str, Any]]] = []
    rejected: list[dict[str, Any]] = []

    for candidate in candidates:
        receipt = qualify_candidate(candidate, required_terms, path_intent, unsupported_intent)
        receipts.append(receipt)
        enriched = dict(candidate)
        enriched["qualification"] = receipt
        if receipt["qualified"]:
            qualified_rows.append((float(receipt["qualified_score"]), enriched))
        else:
            rejected.append(enriched)

    qualified_rows.sort(key=lambda item: (-item[0], -float(item[1].get("density_score", 0)), -float(item[1].get("score", 0))))
    locations = [item[1] for item in qualified_rows[:top_k]]
    support_state = "qualified_evidence" if locations else "no_qualified_evidence"
    return {
        "summary": {
            "schema": "awrag_evidence_qualification_summary@1",
            "support_state": support_state,
            "raw_candidate_count": len(candidates),
            "qualified_count": len(qualified_rows),
            "rejected_count": len(rejected),
            "required_terms": required_terms,
            "path_or_config_intent": path_intent,
        },
        "receipts": receipts,
        "locations": locations,
        "rejected": rejected[:top_k],
    }

def qualify_candidate(candidate: dict[str, Any], required_terms: list[str], path_intent: bool, unsupported_intent: bool) -> dict[str, Any]:
    text = str(candidate.get("text", ""))
    text_anchors = set(anchorize(text))
    direct = set(candidate.get("direct_matched_anchors") or [])
    covered = sorted(anchor for anchor in required_terms if anchor in text_anchors or anchor in direct)
    missing = sorted(anchor for anchor in required_terms if anchor not in covered)
    coverage = len(covered) / max(1, len(required_terms))
    heading_only = is_heading_only(text)
    broad_heading = heading_only and is_broad_heading(text)
    slash_phrase = contains_unqualified_slash_phrase(text)

    reject_reasons: list[str] = []
    if broad_heading:
        reject_reasons.append("section_heading_ambiguity")
    if heading_only and coverage < 0.75:
        reject_reasons.append("heading_without_content")
    if path_intent and slash_phrase and not contains_true_path_or_endpoint(text):
        reject_reasons.append("path_config_classifier_miss")
    if unsupported_intent and coverage < 0.50:
        reject_reasons.append("unsupported_refusal_threshold")
    if len(required_terms) >= 3 and coverage < 0.34:
        reject_reasons.append("predicate_object_coverage_miss")

    qualified = not reject_reasons
    score = float(candidate.get("density_score", 0)) + 8.0 * coverage + min(4.0, float(candidate.get("direct_hit_count", 0))) - (3.0 if heading_only else 0.0)
    return {
        "schema": "awrag_candidate_qualification@1",
        "candidate": candidate.get("citation"),
        "qualified": qualified,
        "reject_reasons": reject_reasons,
        "covered_terms": covered,
        "missing_terms": missing[:20],
        "coverage": round(coverage, 4),
        "heading_only": heading_only,
        "broad_heading": broad_heading,
        "path_or_config_candidate": contains_true_path_or_endpoint(text),
        "qualified_score": round(score, 4),
    }

def significant_question_terms(anchors: list[str]) -> list[str]:
    low_value = STOP_ANCHORS | {
        "answer", "ask", "asked", "claim", "data", "dataset", "describe", "described",
        "evidence", "find", "found", "give", "local", "provide", "question", "row",
        "section", "show", "staged", "under", "value", "was", "were",
    }
    out: list[str] = []
    seen: set[str] = set()
    for anchor in anchors:
        if anchor in low_value:
            continue
        if len(anchor) == 1 and not anchor.isdigit():
            continue
        if anchor not in seen:
            out.append(anchor)
            seen.add(anchor)
    return out

def is_heading_only(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return False
    lines = [line.strip() for line in stripped.splitlines() if line.strip()]
    return len(lines) == 1 and (lines[0].startswith("#") or len(lines[0]) <= 80)

def is_broad_heading(text: str) -> bool:
    stripped = text.strip().strip("#*` ").casefold()
    broad = {
        "conclusion", "discussion", "implemented", "next steps", "governance",
        "overview", "summary", "background", "results", "methods", "user upload",
        "what it opens", "citation integration", "citations pane",
    }
    return stripped in broad or stripped.startswith(("implemented", "next steps"))

def has_path_or_config_intent(question: str) -> bool:
    q = question.casefold()
    return any(token in q for token in ("path", "config", "endpoint", "api", "route", "url", "file"))

def contains_unqualified_slash_phrase(text: str) -> bool:
    return bool(re.search(r"\b[a-zA-Z]{2,}/[a-zA-Z]{2,}\b", text))

def contains_true_path_or_endpoint(text: str) -> bool:
    patterns = [
        r"[A-Za-z]:\\",
        r"[/\\][A-Za-z0-9_.-]+[/\\]",
        r"\bapi/[A-Za-z0-9_./{}-]+",
        r"/api/[A-Za-z0-9_./{}-]+",
        r"\b[A-Za-z0-9_.-]+\.(json|toml|yaml|yml|py|md|txt|csv)\b",
    ]
    return any(re.search(pattern, text) for pattern in patterns)

