from __future__ import annotations

from pathlib import Path

from awrag.engine import intake
from awrag.ui_read_bridge import (
    get_anchor_detail,
    get_count_backend_status,
    get_manifest,
    get_protected_notice,
    get_status,
    get_symbol_system_status,
    search_lexicon,
)


DATASET_ID = "ui_read_bridge_dataset"


def test_ui_read_bridge_status_and_metadata_are_read_only(tmp_path: Path) -> None:
    source = tmp_path / "source.txt"
    source.write_text(
        "Dataset counts stay local.\n\nAWRAG citations stay with source coordinates.",
        encoding="utf-8",
    )
    runtime = tmp_path / "runtime"
    intake(runtime, DATASET_ID, source)
    dataset_root = runtime / "datasets" / DATASET_ID
    before = file_fingerprints(dataset_root)

    status = get_status(runtime, DATASET_ID)
    manifest = get_manifest(runtime, DATASET_ID)
    count_status = get_count_backend_status(runtime, DATASET_ID)
    symbol_status = get_symbol_system_status(runtime, DATASET_ID)
    notice = get_protected_notice()

    assert status["count_backend"] == "awrag_native_binary_counts@1"
    assert status["persistent_memory"] is False
    assert status["read_only"] is True
    assert manifest["symbol_system"] == "awrag_public_6b@1"
    assert count_status["relation_count"] == status["relation_count"]
    assert symbol_status["symbol_system"] == "awrag_public_6b@1"
    assert symbol_status["symbol_bytes"] == 6
    assert notice["watermark_locked"] is True
    assert before == file_fingerprints(dataset_root)


def test_ui_read_bridge_lexicon_search_and_anchor_detail_are_read_only(tmp_path: Path) -> None:
    source = tmp_path / "source.txt"
    source.write_text(
        "Dataset counts stay local. Dataset citations stay local.",
        encoding="utf-8",
    )
    runtime = tmp_path / "runtime"
    intake(runtime, DATASET_ID, source)
    dataset_root = runtime / "datasets" / DATASET_ID
    before = file_fingerprints(dataset_root)

    results = search_lexicon(runtime, DATASET_ID, query="dataset", limit=10)
    assert results["schema"] == "awrag_ui_lexicon_search@1"
    assert results["read_only"] is True
    assert any(row["anchor"] == "dataset" for row in results["anchors"])

    detail = get_anchor_detail(runtime, DATASET_ID, anchor="dataset")
    detail_by_symbol = get_anchor_detail(runtime, DATASET_ID, symbol=detail["symbol"])
    assert detail["anchor"] == "dataset"
    assert detail["symbol_system"] == "awrag_public_6b@1"
    assert detail["observations"] >= 2
    assert detail_by_symbol["anchor"] == detail["anchor"]
    assert before == file_fingerprints(dataset_root)


def file_fingerprints(root: Path) -> dict[str, tuple[int, int]]:
    return {
        str(path.relative_to(root)): (path.stat().st_size, path.stat().st_mtime_ns)
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }
