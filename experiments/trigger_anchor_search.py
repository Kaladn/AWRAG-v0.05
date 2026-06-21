from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_SRC = Path(__file__).resolve().parents[1] / "src"
if str(REPO_SRC) not in sys.path:
    sys.path.insert(0, str(REPO_SRC))

from awrag.engine import anchorize  # noqa: E402
from experiments.aw_backend_tap import AwBackendTap


@dataclass(frozen=True)
class ChatBlock:
    block_ordinal: int
    block_id: str
    citation_id: str
    marker: str
    file_path: str
    line_start: int
    line_end: int
    text: str
    conversation_id: str | None
    message_id: str | None
    title: str | None
    speaker: str | None
    timestamp: str | None
    date: str | None

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()


@dataclass(frozen=True)
class TriggerHit:
    anchor: str
    anchor_class: str
    block: ChatBlock
    positions: list[int]

    def to_dict(self) -> dict[str, Any]:
        return {
            "anchor": self.anchor,
            "anchor_class": self.anchor_class,
            "block": self.block.to_dict(),
            "positions": self.positions,
        }


def load_chat_blocks(tap: AwBackendTap, *, date: str | None = None) -> list[ChatBlock]:
    blocks = []
    for ordinal, row in sorted(tap.read_blocks().items()):
        meta = row.get("chat_metadata") or {}
        row_date = str(meta.get("date") or "") or None
        if date and row_date != date:
            continue
        blocks.append(ChatBlock(
            block_ordinal=int(ordinal),
            block_id=str(row.get("block_id") or ""),
            citation_id=str(row.get("citation_id") or ""),
            marker=str(row.get("marker") or ""),
            file_path=str(row.get("file_path") or ""),
            line_start=int(row.get("line_start") or 0),
            line_end=int(row.get("line_end") or 0),
            text=str(row.get("text") or ""),
            conversation_id=str(meta.get("conversation_id") or "") or None,
            message_id=str(meta.get("message_id") or "") or None,
            title=str(meta.get("title") or "") or None,
            speaker=str(meta.get("speaker") or "") or None,
            timestamp=str(meta.get("created_at") or meta.get("created_at_original") or "") or None,
            date=row_date,
        ))
    return blocks


def search_solo_anchor(blocks: list[ChatBlock], trigger: dict[str, Any], *, max_hits: int = 500) -> list[TriggerHit]:
    wanted = str(trigger.get("anchor") or "").strip().lower()
    if not wanted:
        return []
    hits = []
    for block in blocks:
        anchors = [str(anchor).lower() for anchor in anchorize(block.text)]
        positions = [index for index, anchor in enumerate(anchors) if anchor == wanted]
        if not positions:
            continue
        hits.append(TriggerHit(anchor=wanted, anchor_class=str(trigger.get("class") or "unknown"), block=block, positions=positions))
        if len(hits) >= max_hits:
            break
    return hits
