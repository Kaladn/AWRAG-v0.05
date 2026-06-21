from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from experiments.scaffold_records import ScaffoldAttemptRecord


class GenerationAuthority(Protocol):
    def can_emit_meaning(self, term: str) -> bool: ...
    def authority_for(self, term: str) -> str: ...


@dataclass(frozen=True)
class ScaffoldGrade:
    status: str
    failure_types: list[str]
    failure_explanation: str
    retry_guidance: list[str]
    unsupported_terms: list[str] = field(default_factory=list)
    missing_variables: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    @property
    def passed(self) -> bool: return self.status == "passed"


OUTSIDE_BOUNDARY_PHRASES = ["as an ai", "from general knowledge", "i know that", "it is well known", "outside the dataset"]
BOUNDARY_LEAK_TERMS = ["proves", "guarantees", "always", "never", "cures"]


def grade_attempt(attempt: ScaffoldAttemptRecord, *, generation: GenerationAuthority | None = None) -> ScaffoldGrade:
    failures: list[str] = []
    guidance: list[str] = []
    unsupported: list[str] = []
    missing: list[str] = []
    text = attempt.answer_text.strip()
    lower = text.lower()
    if not text:
        failures.append("bad_answer_frame"); guidance.append("retry with the strongest cited evidence frame")
    if not attempt.citations:
        failures.append("missing_citation"); guidance.append("require at least one AW citation marker before accepting the scaffold")
    if attempt.evidence_frame_count <= 0:
        failures.append("weak_crossing"); guidance.append("retry with broader anchor crossings or mark not enough evidence")
    if any(phrase in lower for phrase in OUTSIDE_BOUNDARY_PHRASES):
        failures.append("outside_dataset_boundary"); guidance.append("remove world knowledge phrasing and return only cited dataset claims")
    leaked = [term for term in BOUNDARY_LEAK_TERMS if term in lower]
    if leaked:
        failures.append("evidence_speech_boundary_leak"); unsupported.extend(leaked); guidance.append("replace claim-heavy wording with observed/cited wording")
    if generation is not None:
        for term in attempt.major_anchors:
            key = str(term or "").strip().lower()
            if key and not generation.can_emit_meaning(key):
                unsupported.append(key)
        if unsupported:
            failures.append("unsupported_term"); guidance.append("drop unsupported meaning anchors or rebuild the generation helper for this dataset")
    if not attempt.major_anchors:
        missing.append("major_anchors"); failures.append("missing_variables"); guidance.append("extract major anchors from evidence frames before retrying")
    failures = _unique(failures)
    status = "passed" if not failures else "failed"
    return ScaffoldGrade(
        status=status,
        failure_types=failures,
        failure_explanation="passed scaffold gate" if status == "passed" else "; ".join(failures),
        retry_guidance=_unique(guidance),
        unsupported_terms=_unique(unsupported),
        missing_variables=_unique(missing),
        metadata={"grader": "deterministic_scaffold_grader_v0"},
    )


def _unique(values: list[str]) -> list[str]:
    out: list[str] = []
    for value in values:
        if value not in out: out.append(value)
    return out
