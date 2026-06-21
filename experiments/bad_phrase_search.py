from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import sys
from pathlib import Path

REPO_SRC = Path(__file__).resolve().parents[1] / "src"
if str(REPO_SRC) not in sys.path:
    sys.path.insert(0, str(REPO_SRC))

from awrag.engine import anchorize  # noqa: E402
from experiments.trigger_anchor_search import ChatBlock


@dataclass(frozen=True)
class BadPhraseHit:
    surface: str
    phrase_class: str
    severity: str
    block: ChatBlock
    positions: list[int]
    matched_anchor_width: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "surface": self.surface,
            "phrase_class": self.phrase_class,
            "severity": self.severity,
            "block": self.block.to_dict(),
            "positions": self.positions,
            "matched_anchor_width": self.matched_anchor_width,
            "needs_review": True,
            "confidence": 0.0,
        }


def search_bad_phrase_entry(blocks: list[ChatBlock], entry: dict[str, Any], *, max_hits: int | None = None) -> list[BadPhraseHit]:
    surface = str(entry.get("surface") or "").strip().lower()
    raw_words = [part for part in surface.split() if part]
    is_grouped_phrase = len(raw_words) > 1
    wanted = [str(anchor).strip().lower() for anchor in anchorize(surface)]
    if not wanted:
        wanted = [str(anchor).strip().lower() for anchor in entry.get("anchors", []) if str(anchor).strip()]
    if not wanted:
        return []
    hits: list[BadPhraseHit] = []
    width = len(wanted)
    for block in blocks:
        text_lower = " ".join(str(block.text or "").lower().split())
        if is_grouped_phrase and surface not in text_lower:
            continue
        anchors = [str(anchor).strip().lower() for anchor in anchorize(block.text)]
        positions = _sequence_positions(anchors, wanted)
        if is_grouped_phrase and not positions:
            positions = [-1]
        if not positions:
            continue
        hits.append(BadPhraseHit(
            surface=surface or " ".join(wanted),
            phrase_class=str(entry.get("class") or "unknown"),
            severity=str(entry.get("severity") or "unknown"),
            block=block,
            positions=positions,
            matched_anchor_width=width,
        ))
        if max_hits is not None and len(hits) >= max_hits:
            break
    return hits

def _sequence_positions(anchors: list[str], wanted: list[str]) -> list[int]:
    if not wanted or len(wanted) > len(anchors):
        return []
    positions: list[int] = []
    width = len(wanted)
    for index in range(0, len(anchors) - width + 1):
        if anchors[index:index + width] == wanted:
            positions.append(index)
    return positions
