from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

DEFAULT_ALLOWED_GLUE = [
    "the",
    "a",
    "an",
    "this",
    "that",
    "it",
    "they",
    "he",
    "she",
    "his",
    "her",
    "and",
    "or",
    "but",
    "because",
    "with",
    "as",
    "in",
    "on",
    "by",
    "for",
    "from",
    "to",
    "of",
]

DEFAULT_FORBIDDEN_CLAIM_TERMS = [
    "proves",
    "guarantees",
    "always",
    "never",
    "cures",
]

DEFAULT_RELATION_PHRASES = {
    "supports": "supports",
    "contradicts": "contradicts",
    "related": "is related to",
    "not_enough_data": "does not provide enough evidence for",
}


@dataclass(frozen=True)
class GenerationLexiconEntry:
    term: str
    anchor_class: str
    allowed_surface_forms: list[str]
    observations: int = 0
    symbol: str | None = None
    glue_neighbors: list[str] = field(default_factory=list)
    determiner_policy: str = "auto"
    pronoun_policy: str = "repeat_if_ambiguous"
    relation_phrase_policy: str = "literal"
    evidence_authority: str = "observed_anchor_only"
    trace: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class GenerationLexicon:
    schema: str
    set_id: str
    dataset_id: str
    domain: str
    entries: dict[str, GenerationLexiconEntry]
    allowed_glue: list[str]
    forbidden_claim_terms: list[str]
    preferred_relation_phrases: dict[str, str]
    citation_policy: str = "preserve_only"
    fallback_policy: str = "refuse_if_no_aw_support"
    meaningful_term_policy: str = "must_be_observed_anchor"

    def lookup(self, term: str) -> GenerationLexiconEntry | None:
        return self.entries.get(_key(term))

    def is_glue(self, term: str) -> bool:
        return _key(term) in {_key(row) for row in self.allowed_glue}

    def is_forbidden(self, term: str) -> bool:
        return _key(term) in {_key(row) for row in self.forbidden_claim_terms}

    def can_emit(self, term: str) -> bool:
        key = _key(term)
        if not key or self.is_forbidden(key):
            return False
        return key in self.entries or self.is_glue(key)

    def can_emit_meaning(self, term: str) -> bool:
        key = _key(term)
        if not key or self.is_forbidden(key) or self.is_glue(key):
            return False
        return key in self.entries

    def authority_for(self, term: str) -> str:
        key = _key(term)
        if self.is_forbidden(key):
            return "forbidden_claim_term"
        entry = self.entries.get(key)
        if entry:
            return entry.evidence_authority
        if self.is_glue(key):
            return "speech_glue_only"
        return "not_allowed"

    def relation_phrase(self, relation_name: str) -> str:
        key = _key(relation_name)
        return self.preferred_relation_phrases.get(key, relation_name)

    def to_payload(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["entries"] = {
            key: asdict(entry) for key, entry in sorted(self.entries.items())
        }
        return payload


@dataclass(frozen=True)
class SurfaceDecision:
    term: str
    allowed: bool
    meaningful: bool
    authority: str
    reason: str


def _key(value: str) -> str:
    return str(value or "").strip().lower()


def _anchor_class(term: str, *, allowed_glue: set[str]) -> str:
    key = _key(term)
    if key in allowed_glue:
        return "glue"
    if any(ch.isdigit() for ch in key):
        return "measure_or_identifier"
    if len(key) == 1 and not key.isalnum():
        return "punctuation_or_symbol"
    return "evidence_anchor"


def _entry_from_aw_row(row: dict[str, Any], *, allowed_glue: set[str]) -> GenerationLexiconEntry | None:
    term = _key(str(row.get("anchor", "")))
    if not term:
        return None
    anchor_class = _anchor_class(term, allowed_glue=allowed_glue)
    authority = "speech_glue_observed" if anchor_class == "glue" else "observed_anchor_only"
    return GenerationLexiconEntry(
        term=term,
        anchor_class=anchor_class,
        allowed_surface_forms=[term],
        observations=int(row.get("observations") or 0),
        symbol=str(row.get("symbol")) if row.get("symbol") else None,
        evidence_authority=authority,
        trace=["built_from_aw_dataset_lexicon"],
    )


def build_generation_lexicon_from_aw_payload(
    payload: dict[str, Any],
    *,
    set_id: str | None = None,
    domain: str = "dataset_local",
    allowed_glue: list[str] | None = None,
    forbidden_claim_terms: list[str] | None = None,
    preferred_relation_phrases: dict[str, str] | None = None,
) -> GenerationLexicon:
    glue = [_key(row) for row in (allowed_glue or DEFAULT_ALLOWED_GLUE) if _key(row)]
    glue_set = set(glue)
    entries: dict[str, GenerationLexiconEntry] = {}
    for row in payload.get("anchors", []):
        if not isinstance(row, dict):
            continue
        entry = _entry_from_aw_row(row, allowed_glue=glue_set)
        if entry:
            entries[entry.term] = entry

    dataset_id = str(payload.get("dataset_id") or "unknown_dataset")
    return GenerationLexicon(
        schema="awrag_generation_helper_lexicon@0",
        set_id=set_id or f"{dataset_id}_generation_helper_v0",
        dataset_id=dataset_id,
        domain=domain,
        entries=entries,
        allowed_glue=glue,
        forbidden_claim_terms=[_key(row) for row in (forbidden_claim_terms or DEFAULT_FORBIDDEN_CLAIM_TERMS)],
        preferred_relation_phrases={
            _key(key): value for key, value in (preferred_relation_phrases or DEFAULT_RELATION_PHRASES).items()
        },
    )


def build_generation_lexicon_from_aw_file(
    lexicon_path: str | Path,
    **kwargs: Any,
) -> GenerationLexicon:
    payload = json.loads(Path(lexicon_path).read_text(encoding="utf-8"))
    return build_generation_lexicon_from_aw_payload(payload, **kwargs)


def explain_surface_decision(lexicon: GenerationLexicon, term: str) -> SurfaceDecision:
    key = _key(term)
    if not key:
        return SurfaceDecision(term=term, allowed=False, meaningful=False, authority="not_allowed", reason="empty_surface")
    if lexicon.is_forbidden(key):
        return SurfaceDecision(term=term, allowed=False, meaningful=False, authority="forbidden_claim_term", reason="forbidden_claim_term")
    if lexicon.is_glue(key):
        return SurfaceDecision(term=term, allowed=True, meaningful=False, authority=lexicon.authority_for(key), reason="allowed_glue")
    entry = lexicon.lookup(key)
    if entry:
        return SurfaceDecision(term=term, allowed=True, meaningful=True, authority=entry.evidence_authority, reason="observed_anchor")
    return SurfaceDecision(term=term, allowed=False, meaningful=False, authority="not_allowed", reason="not_observed_and_not_glue")


def write_generation_lexicon(path: str | Path, lexicon: GenerationLexicon) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(lexicon.to_payload(), ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def load_generation_lexicon(path: str | Path) -> GenerationLexicon:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    entries = {
        key: GenerationLexiconEntry(**entry)
        for key, entry in payload.get("entries", {}).items()
    }
    return GenerationLexicon(
        schema=payload["schema"],
        set_id=payload["set_id"],
        dataset_id=payload["dataset_id"],
        domain=payload["domain"],
        entries=entries,
        allowed_glue=list(payload.get("allowed_glue", [])),
        forbidden_claim_terms=list(payload.get("forbidden_claim_terms", [])),
        preferred_relation_phrases=dict(payload.get("preferred_relation_phrases", {})),
        citation_policy=payload.get("citation_policy", "preserve_only"),
        fallback_policy=payload.get("fallback_policy", "refuse_if_no_aw_support"),
        meaningful_term_policy=payload.get("meaningful_term_policy", "must_be_observed_anchor"),
    )
