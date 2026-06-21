from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from experiments.trigger_anchor_search import ChatBlock, TriggerHit


@dataclass(frozen=True)
class ExpandedTriggerHit:
    anchor: str
    anchor_class: str
    hit: TriggerHit
    previous_blocks: list[ChatBlock]
    next_blocks: list[ChatBlock]

    def to_record(self) -> dict[str, Any]:
        block = self.hit.block
        return {
            "schema": "trigger_expanded_block@1",
            "anchor": self.anchor,
            "anchor_class": self.anchor_class,
            "hit_message_id": block.message_id,
            "conversation_id": block.conversation_id,
            "timestamp": block.timestamp,
            "date": block.date,
            "role": block.speaker,
            "positions": self.hit.positions,
            "previous_blocks": [row.to_dict() for row in self.previous_blocks],
            "hit_block": block.to_dict(),
            "next_blocks": [row.to_dict() for row in self.next_blocks],
            "citation": make_chat_citation(block),
            "needs_review": True,
            "confidence": 0.0,
        }


def expand_hit_neighborhood(
    blocks_by_ordinal: dict[int, ChatBlock],
    hit: TriggerHit,
    *,
    previous_blocks: int = 1,
    next_blocks: int = 1,
) -> ExpandedTriggerHit:
    ordinal = hit.block.block_ordinal
    prev = []
    nxt = []
    for offset in range(previous_blocks, 0, -1):
        block = blocks_by_ordinal.get(ordinal - offset)
        if block:
            prev.append(block)
    for offset in range(1, next_blocks + 1):
        block = blocks_by_ordinal.get(ordinal + offset)
        if block:
            nxt.append(block)
    return ExpandedTriggerHit(hit.anchor, hit.anchor_class, hit, prev, nxt)


def make_chat_citation(block: ChatBlock) -> dict[str, Any]:
    return {
        "citation_id": block.citation_id,
        "marker": block.marker,
        "block_ordinal": block.block_ordinal,
        "block_id": block.block_id,
        "file_path": block.file_path,
        "line_start": block.line_start,
        "line_end": block.line_end,
        "timestamp": block.timestamp,
        "date": block.date,
        "conversation_id": block.conversation_id,
        "message_id": block.message_id,
    }
