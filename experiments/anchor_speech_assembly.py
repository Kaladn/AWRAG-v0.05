from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


class GenerationAuthority(Protocol):
    def can_emit(self, term: str) -> bool: ...
    def can_emit_meaning(self, term: str) -> bool: ...
    def authority_for(self, term: str) -> str: ...


@dataclass(frozen=True)
class EvidenceAnchor:
    text: str
    kind: str = "evidence_anchor"
    citation: str | None = None
    block_id: str | None = None
    position: int | None = None
    score: float = 0.0


@dataclass(frozen=True)
class AnchorStep:
    anchor: EvidenceAnchor
    relation: str | None = None
    direction: str | None = None


@dataclass(frozen=True)
class GlueSlot:
    left_anchor: str
    right_anchor: str
    reason: str
    glue_word: str
    authority: str


@dataclass(frozen=True)
class AnswerFrame:
    schema: str
    question_id: str
    status: str
    surface_text: str
    anchor_path: list[str]
    glue_slots: list[GlueSlot]
    citations: list[str]
    refusal_reason: str | None = None
    trace: list[dict[str, str]] = field(default_factory=list)


def _clean(value: str) -> str:
    return " ".join(str(value or "").split()).strip()


def _default_glue(left: EvidenceAnchor, right: EvidenceAnchor, authority: GenerationAuthority) -> str:
    for candidate in ("and", "with", "as"):
        if authority.can_emit(candidate):
            return candidate
    return ""


def assemble_anchor_first_answer(
    *,
    question_id: str,
    anchors: list[EvidenceAnchor],
    generation: GenerationAuthority,
    citations: list[str] | None = None,
) -> AnswerFrame:
    """
    Assemble normal speech from observed anchors plus approved glue.

    Meaning must come from anchors approved by the generation authority.
    Glue can connect but cannot add new claims.
    """

    if not anchors:
        return AnswerFrame(
            schema="awrag_anchor_first_answer_frame@0",
            question_id=question_id,
            status="not_enough_evidence",
            surface_text="",
            anchor_path=[],
            glue_slots=[],
            citations=[],
            refusal_reason="no_anchor_path",
        )

    trace: list[dict[str, str]] = []
    for anchor in anchors:
        term = _clean(anchor.text).lower()
        if not generation.can_emit_meaning(term):
            return AnswerFrame(
                schema="awrag_anchor_first_answer_frame@0",
                question_id=question_id,
                status="refused_unsupported_surface",
                surface_text="",
                anchor_path=[_clean(row.text) for row in anchors],
                glue_slots=[],
                citations=list(citations or []),
                refusal_reason=f"unsupported_meaning_anchor:{term}",
                trace=[{"term": term, "authority": generation.authority_for(term)}],
            )
        trace.append({"term": term, "authority": generation.authority_for(term)})

    output: list[str] = []
    glue_slots: list[GlueSlot] = []
    for index, anchor in enumerate(anchors):
        output.append(_clean(anchor.text))
        if index >= len(anchors) - 1:
            continue
        glue_word = _default_glue(anchor, anchors[index + 1], generation)
        if glue_word:
            output.append(glue_word)
            glue_slots.append(
                GlueSlot(
                    left_anchor=_clean(anchor.text),
                    right_anchor=_clean(anchors[index + 1].text),
                    reason="anchor_path_readability",
                    glue_word=glue_word,
                    authority=generation.authority_for(glue_word),
                )
            )

    cited = []
    for value in list(citations or []) + [anchor.citation for anchor in anchors if anchor.citation]:
        if value and value not in cited:
            cited.append(value)
    surface = _clean(" ".join(output))
    if surface and surface[-1] not in ".?!":
        surface += "."
    if cited:
        surface = f"{surface} {' '.join(cited)}"

    return AnswerFrame(
        schema="awrag_anchor_first_answer_frame@0",
        question_id=question_id,
        status="assembled_from_anchor_path",
        surface_text=surface,
        anchor_path=[_clean(row.text) for row in anchors],
        glue_slots=glue_slots,
        citations=cited,
        trace=trace,
    )
