from __future__ import annotations

import hashlib
import json
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from experiments.generation_lexicon import GenerationLexicon, explain_surface_decision

MAGIC = b"AWGENB1\0"
HEADER = struct.Struct(">8sHHQQ")
RECORD = struct.Struct(">6sBBHQII")
SCHEMA = "awrag_generation_binary@0"
VERSION = 1

CLASS_IDS = {
    "evidence_anchor": 1,
    "measure_or_identifier": 2,
    "punctuation_or_symbol": 3,
    "glue": 4,
    "relation_phrase": 5,
    "forbidden": 250,
}
AUTHORITY_IDS = {
    "observed_anchor_only": 1,
    "speech_glue_observed": 2,
    "speech_glue_only": 3,
    "relation_surface_only": 4,
    "forbidden_claim_term": 250,
}
FLAG_CAN_EMIT = 1 << 0
FLAG_MEANINGFUL = 1 << 1
FLAG_GLUE = 1 << 2
FLAG_FORBIDDEN = 1 << 3


@dataclass(frozen=True)
class GenerationBinaryRecord:
    term: str
    symbol_bytes: bytes
    anchor_class: str
    authority: str
    observations: int
    can_emit: bool
    meaningful: bool
    glue: bool
    forbidden: bool


@dataclass(frozen=True)
class GenerationBinaryReceipt:
    schema: str
    path: str
    manifest_path: str
    dataset_id: str
    set_id: str
    record_count: int
    string_table_bytes: int
    binary_bytes: int


class LoadedGenerationBinary:
    def __init__(self, *, dataset_id: str, set_id: str, records: dict[str, GenerationBinaryRecord]) -> None:
        self.dataset_id = dataset_id
        self.set_id = set_id
        self.records = records

    def lookup(self, term: str) -> GenerationBinaryRecord | None:
        return self.records.get(_key(term))

    def can_emit(self, term: str) -> bool:
        row = self.lookup(term)
        return bool(row and row.can_emit and not row.forbidden)

    def can_emit_meaning(self, term: str) -> bool:
        row = self.lookup(term)
        return bool(row and row.meaningful and not row.forbidden)

    def authority_for(self, term: str) -> str:
        row = self.lookup(term)
        if not row:
            return "not_allowed"
        return row.authority

    def decision(self, term: str) -> dict[str, Any]:
        row = self.lookup(term)
        if not row:
            return {
                "term": term,
                "allowed": False,
                "meaningful": False,
                "authority": "not_allowed",
                "reason": "not_in_generation_binary",
            }
        if row.forbidden:
            reason = "forbidden_claim_term"
        elif row.glue:
            reason = "allowed_glue"
        elif row.meaningful:
            reason = "observed_anchor"
        else:
            reason = "allowed_surface"
        return {
            "term": term,
            "allowed": row.can_emit and not row.forbidden,
            "meaningful": row.meaningful and not row.forbidden,
            "authority": row.authority,
            "reason": reason,
        }


def _key(value: str) -> str:
    return str(value or "").strip().lower()


def _symbol_from_hex(value: str | None, term: str) -> bytes:
    if value and value.startswith("0x"):
        raw = bytes.fromhex(value[2:])
        if len(raw) == 6:
            return raw
    return hashlib.sha256(term.encode("utf-8", errors="replace")).digest()[:6]


def _record_from_term(
    *,
    term: str,
    symbol: str | None,
    anchor_class: str,
    authority: str,
    observations: int,
    can_emit: bool,
    meaningful: bool,
    glue: bool,
    forbidden: bool,
) -> GenerationBinaryRecord:
    return GenerationBinaryRecord(
        term=_key(term),
        symbol_bytes=_symbol_from_hex(symbol, _key(term)),
        anchor_class=anchor_class,
        authority=authority,
        observations=max(0, int(observations or 0)),
        can_emit=can_emit,
        meaningful=meaningful,
        glue=glue,
        forbidden=forbidden,
    )


def records_from_generation_lexicon(lexicon: GenerationLexicon) -> list[GenerationBinaryRecord]:
    rows: dict[str, GenerationBinaryRecord] = {}
    for term, entry in lexicon.entries.items():
        decision = explain_surface_decision(lexicon, term)
        rows[_key(term)] = _record_from_term(
            term=term,
            symbol=entry.symbol,
            anchor_class=entry.anchor_class,
            authority=decision.authority,
            observations=entry.observations,
            can_emit=decision.allowed,
            meaningful=decision.meaningful,
            glue=entry.anchor_class == "glue",
            forbidden=False,
        )

    for term in lexicon.allowed_glue:
        key = _key(term)
        if key in rows:
            continue
        rows[key] = _record_from_term(
            term=key,
            symbol=None,
            anchor_class="glue",
            authority="speech_glue_only",
            observations=0,
            can_emit=True,
            meaningful=False,
            glue=True,
            forbidden=False,
        )

    for term in lexicon.preferred_relation_phrases.values():
        key = _key(term)
        if not key or key in rows:
            continue
        rows[key] = _record_from_term(
            term=key,
            symbol=None,
            anchor_class="relation_phrase",
            authority="relation_surface_only",
            observations=0,
            can_emit=True,
            meaningful=False,
            glue=True,
            forbidden=False,
        )

    for term in lexicon.forbidden_claim_terms:
        key = _key(term)
        rows[key] = _record_from_term(
            term=key,
            symbol=None,
            anchor_class="forbidden",
            authority="forbidden_claim_term",
            observations=0,
            can_emit=False,
            meaningful=False,
            glue=False,
            forbidden=True,
        )

    return [rows[key] for key in sorted(rows)]


def write_generation_binary(
    path: str | Path,
    lexicon: GenerationLexicon,
    *,
    manifest_path: str | Path | None = None,
) -> GenerationBinaryReceipt:
    target = Path(path)
    manifest = Path(manifest_path) if manifest_path else target.with_suffix(target.suffix + ".manifest.json")
    target.parent.mkdir(parents=True, exist_ok=True)
    manifest.parent.mkdir(parents=True, exist_ok=True)

    rows = records_from_generation_lexicon(lexicon)
    string_table = bytearray()
    encoded_rows: list[tuple[GenerationBinaryRecord, int, int]] = []
    for row in rows:
        raw = row.term.encode("utf-8")
        offset = len(string_table)
        string_table.extend(raw)
        encoded_rows.append((row, offset, len(raw)))

    with target.open("wb") as handle:
        handle.write(HEADER.pack(MAGIC, VERSION, 0, len(encoded_rows), len(string_table)))
        for row, offset, length in encoded_rows:
            flags = 0
            if row.can_emit:
                flags |= FLAG_CAN_EMIT
            if row.meaningful:
                flags |= FLAG_MEANINGFUL
            if row.glue:
                flags |= FLAG_GLUE
            if row.forbidden:
                flags |= FLAG_FORBIDDEN
            handle.write(
                RECORD.pack(
                    row.symbol_bytes,
                    CLASS_IDS.get(row.anchor_class, 0),
                    AUTHORITY_IDS.get(row.authority, 0),
                    flags,
                    row.observations,
                    offset,
                    length,
                )
            )
        handle.write(string_table)

    manifest_payload = {
        "schema": SCHEMA,
        "dataset_id": lexicon.dataset_id,
        "set_id": lexicon.set_id,
        "binary_path": str(target),
        "record_count": len(rows),
        "string_table_bytes": len(string_table),
        "binary_bytes": target.stat().st_size,
        "policy": {
            "citation_policy": lexicon.citation_policy,
            "fallback_policy": lexicon.fallback_policy,
            "meaningful_term_policy": lexicon.meaningful_term_policy,
        },
    }
    manifest.write_text(json.dumps(manifest_payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    return GenerationBinaryReceipt(
        schema=SCHEMA,
        path=str(target),
        manifest_path=str(manifest),
        dataset_id=lexicon.dataset_id,
        set_id=lexicon.set_id,
        record_count=len(rows),
        string_table_bytes=len(string_table),
        binary_bytes=target.stat().st_size,
    )


def load_generation_binary(path: str | Path, *, dataset_id: str = "unknown_dataset", set_id: str = "unknown_set") -> LoadedGenerationBinary:
    source = Path(path)
    data = source.read_bytes()
    if len(data) < HEADER.size:
        raise ValueError("generation binary is too small")
    magic, version, _reserved, record_count, string_table_bytes = HEADER.unpack_from(data, 0)
    if magic != MAGIC:
        raise ValueError("not an AWRAG generation binary")
    if version != VERSION:
        raise ValueError(f"unsupported generation binary version: {version}")

    records_start = HEADER.size
    strings_start = records_start + (RECORD.size * record_count)
    strings_end = strings_start + string_table_bytes
    if strings_end > len(data):
        raise ValueError("generation binary string table is truncated")
    string_table = data[strings_start:strings_end]

    class_names = {value: key for key, value in CLASS_IDS.items()}
    authority_names = {value: key for key, value in AUTHORITY_IDS.items()}
    rows: dict[str, GenerationBinaryRecord] = {}
    for index in range(record_count):
        offset = records_start + (index * RECORD.size)
        symbol, class_id, authority_id, flags, observations, term_offset, term_len = RECORD.unpack_from(data, offset)
        term = string_table[term_offset: term_offset + term_len].decode("utf-8")
        rows[term] = GenerationBinaryRecord(
            term=term,
            symbol_bytes=symbol,
            anchor_class=class_names.get(class_id, "unknown"),
            authority=authority_names.get(authority_id, "unknown"),
            observations=int(observations),
            can_emit=bool(flags & FLAG_CAN_EMIT),
            meaningful=bool(flags & FLAG_MEANINGFUL),
            glue=bool(flags & FLAG_GLUE),
            forbidden=bool(flags & FLAG_FORBIDDEN),
        )
    return LoadedGenerationBinary(dataset_id=dataset_id, set_id=set_id, records=rows)
