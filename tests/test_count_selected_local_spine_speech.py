from __future__ import annotations

from collections import Counter
from pathlib import Path

from awrag.engine import intake
from awrag.engine.anchors import anchorize
from awrag.engine.querying import score_blocks, top_relation_neighbors
from awrag.engine.storage import (
    BLOCK_ANCHOR_RECORD,
    RELATION_RECORD,
    dataset_paths,
    iter_relation_records,
    read_block_anchor_rows,
    read_blocks,
    read_symbol_to_anchor,
)
from awrag.engine.anchors import symbol_hex


def test_count_selected_block_postings_are_the_local_speech_spine(tmp_path: Path) -> None:
    runtime = tmp_path / "runtime"
    dataset_id = "local_spine_speech"
    starter = (
        "sample 32441 archived appendix samples fixed in formalin and embedded "
        "in paraffin and tested for the presence of abnormal"
    )
    source = tmp_path / "source.md"
    source.write_text(
        "\n\n".join(
            [
                "control block discusses unrelated archive material and not the target prp finding.",
                (
                    f"{starter} prion protein prp result sixteen were positive abnormal prp "
                    "indicating overall prevalence per million population."
                ),
            ]
        ),
        encoding="utf-8",
    )
    intake(runtime, dataset_id, source)

    paths = dataset_paths(runtime, dataset_id)
    blocks = read_blocks(paths)
    block_anchor_rows = read_block_anchor_rows(paths)
    symbol_to_anchor = read_symbol_to_anchor(paths)
    q_counter = Counter(anchorize("abnormal prp positive prevalence"))
    relation_neighbors = top_relation_neighbors(paths, q_counter, limit=16)
    ranked = score_blocks(paths, blocks, block_anchor_rows, q_counter, relation_neighbors, top_k=2)

    assert ranked
    rank1 = ranked[0]
    assert rank1["direct_hit_count"] >= 3
    assert rank1["score"] > 0
    assert rank1["density_score"] > 0

    block_ordinal = _candidate_block_ordinal(blocks, rank1)
    local_spine = _block_anchor_spine(block_anchor_rows, symbol_to_anchor, block_ordinal)
    starter_anchors = anchorize(starter)
    start_index = _find_subsequence(local_spine, starter_anchors)

    assert start_index is not None
    continuation = local_spine[start_index + len(starter_anchors): start_index + len(starter_anchors) + 4]
    assert continuation == ["prion", "protein", "prp", "result"]


def test_count_file_shapes_separate_global_pressure_from_local_spine(tmp_path: Path) -> None:
    runtime = tmp_path / "runtime"
    dataset_id = "count_file_shapes"
    source = tmp_path / "source.md"
    source.write_text(
        "alpha beta gamma.\n\nalpha beta delta.",
        encoding="utf-8",
    )
    intake(runtime, dataset_id, source)

    paths = dataset_paths(runtime, dataset_id)
    relation_row = next(iter_relation_records(paths))
    block_row = read_block_anchor_rows(paths)[0]

    assert RELATION_RECORD.format == ">6s6shI"
    assert BLOCK_ANCHOR_RECORD.format == ">6sIH"
    assert len(relation_row) == 4
    assert len(block_row) == 3
    assert isinstance(relation_row[2], int)  # offset, not a block-local position
    assert isinstance(relation_row[3], int)  # aggregate observations across the dataset
    assert isinstance(block_row[1], int)  # block ordinal
    assert isinstance(block_row[2], int)  # position inside that block


def _candidate_block_ordinal(blocks: dict[int, dict[str, object]], candidate: dict[str, object]) -> int:
    for ordinal, block in blocks.items():
        if (
            str(block["marker"]) == str(candidate["citation"])
            and str(block["file_path"]) == str(candidate["file_path"])
            and int(block["line_start"]) == int(candidate["line_start"])
        ):
            return int(ordinal)
    raise AssertionError("candidate did not map back to a block ordinal")


def _block_anchor_spine(
    block_anchor_rows: list[tuple[bytes, int, int]],
    symbol_to_anchor: dict[str, str],
    block_ordinal: int,
) -> list[str]:
    rows = sorted(
        [
            (position, symbol_to_anchor.get(symbol_hex(symbol), symbol_hex(symbol)))
            for symbol, row_block, position in block_anchor_rows
            if row_block == block_ordinal
        ],
        key=lambda row: row[0],
    )
    return [anchor for _position, anchor in rows]


def _find_subsequence(haystack: list[str], needle: list[str]) -> int | None:
    for start in range(0, len(haystack) - len(needle) + 1):
        if haystack[start:start + len(needle)] == needle:
            return start
    return None
