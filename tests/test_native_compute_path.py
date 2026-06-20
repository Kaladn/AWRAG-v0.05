from __future__ import annotations

from pathlib import Path

from awrag.engine import build_native_counts, intake, native_executable_path, query, status


def test_compute_path_uses_native_executable_not_python_structs(tmp_path: Path) -> None:
    import awrag.engine.storage as storage

    storage_text = Path(storage.__file__).read_text(encoding="utf-8")

    assert "import struct" not in storage_text
    assert "struct.Struct" not in storage_text
    assert "ANCHOR_RECORD.pack" not in storage_text
    assert build_native_counts() == native_executable_path()
    assert native_executable_path().exists()


def test_native_executable_owns_intake_status_and_query(tmp_path: Path) -> None:
    source = tmp_path / "source.md"
    source.write_text(
        "Dataset counts stay local and citations point to source coordinates.\n\n"
        "The native C++ engine owns AWRAG count walking.",
        encoding="utf-8",
    )
    runtime = tmp_path / "runtime"

    receipt = intake(runtime, "native_contract", source)
    current = status(runtime, "native_contract")
    result = query(runtime, "native_contract", "Where do dataset counts stay?", top_k=2)

    assert receipt["compute_engine"] == "awrag_native_cpp_counts@1"
    assert current["compute_engine"] == "awrag_native_cpp_counts@1"
    assert result["compute_engine"] == "awrag_native_cpp_counts@1"
    assert result["answer_packet"]["locations"]
    assert "Dataset counts stay local" in result["answer_packet"]["locations"][0]["text"]
