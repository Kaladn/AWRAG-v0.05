from __future__ import annotations

import json
import threading
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from awrag.engine import intake
from awrag.ui_server import READ_ENDPOINTS, create_server


DATASET_ID = "ui_server_dataset"


def test_read_only_ui_server_exposes_only_read_endpoints(tmp_path: Path) -> None:
    runtime = build_dataset(tmp_path)
    dataset_root = runtime / "datasets" / DATASET_ID
    before = file_fingerprints(dataset_root)

    with running_server(runtime, DATASET_ID) as base_url:
        status = get_json(base_url, "/api/ui/status")
        manifest = get_json(base_url, "/api/ui/manifest")
        search = get_json(base_url, "/api/ui/lexicon/search?q=dataset")
        detail = get_json(base_url, "/api/ui/anchor/detail?anchor=dataset")
        locations = get_json(base_url, "/api/ui/anchor/locations?q=dataset%20local")
        count_backend = get_json(base_url, "/api/ui/count-backend")
        symbol_system = get_json(base_url, "/api/ui/symbol-system")
        notice = get_json(base_url, "/api/ui/protected-notice")

        assert status["count_backend"] == "awrag_native_binary_counts@1"
        assert manifest["symbol_system"] == "awrag_dataset_6b@1"
        assert any(row["anchor"] == "dataset" for row in search["anchors"])
        assert detail["anchor"] == "dataset"
        assert locations["schema"] == "awrag_ui_anchor_location_search@1"
        assert locations["count_files_used"] is False
        assert locations["total_locations"] >= 1
        assert count_backend["count_backend"] == "awrag_native_binary_counts@1"
        assert symbol_system["symbol_bytes"] == 6
        assert notice["watermark_locked"] is True

        for forbidden in ("/api/ui/intake", "/api/ui/query", "/api/ui/remove", "/api/ui/exfil"):
            assert http_error(base_url, forbidden, "GET") == 404
        assert http_error(base_url, "/api/ui/status", "POST") == 405

    assert before == file_fingerprints(dataset_root)


def test_read_only_ui_server_does_not_require_static_mockup(tmp_path: Path) -> None:
    runtime = build_dataset(tmp_path)
    with running_server(runtime, DATASET_ID) as base_url:
        status = get_json(base_url, "/api/ui/status")
        static_error = get_error_json(base_url, "/")
    assert status["count_backend"] == "awrag_native_binary_counts@1"
    assert static_error["error"] == "static_ui_not_installed"
    assert static_error["read_only"] is True

def test_ui_server_batch_button_endpoint_runs_cli_batch(tmp_path: Path) -> None:
    runtime = build_dataset(tmp_path)
    dataset_root = runtime / "datasets" / DATASET_ID
    counts_before = file_content_fingerprints(dataset_root / "counts")
    questions = tmp_path / "questions.txt"
    questions.write_text(
        "Where do dataset counts stay?\nWhere do dataset citations stay?\n",
        encoding="utf-8",
    )

    with running_server(runtime, DATASET_ID) as base_url:
        result = post_json(base_url, "/api/ui/batch/run", {"questions_path": str(questions), "top_k": 2})

    assert result["schema"] == "awrag_batch_run_summary@1"
    assert result["ui_action"] == "batch_run"
    assert result["question_count"] == 2
    assert result["completed"] == 2
    assert result["failed"] == 0
    assert result["model_used"] == "none"
    assert "awrag.cli" in result["cli_command"]
    assert Path(result["summary_path"]).exists()
    assert len(result["output_paths"]) == 2
    assert counts_before == file_content_fingerprints(dataset_root / "counts")

def test_read_endpoint_allowlist_is_intentionally_small() -> None:
    assert READ_ENDPOINTS == {
        "/api/ui/status",
        "/api/ui/manifest",
        "/api/ui/lexicon/search",
        "/api/ui/anchor/detail",
        "/api/ui/anchor/locations",
        "/api/ui/count-backend",
        "/api/ui/symbol-system",
        "/api/ui/protected-notice",
    }


def build_dataset(tmp_path: Path) -> Path:
    source = tmp_path / "source.txt"
    source.write_text(
        "Dataset counts stay local. Dataset citations stay local.",
        encoding="utf-8",
    )
    runtime = tmp_path / "runtime"
    intake(runtime, DATASET_ID, source)
    return runtime


class running_server:
    def __init__(self, runtime: Path, dataset_id: str):
        self.server = create_server(("127.0.0.1", 0), runtime_root=runtime, dataset_id=dataset_id)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.base_url = f"http://127.0.0.1:{self.server.server_address[1]}"

    def __enter__(self) -> str:
        self.thread.start()
        return self.base_url

    def __exit__(self, *_exc: object) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)


def get_json(base_url: str, path: str) -> dict:
    with urlopen(base_url + path, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


def get_text(base_url: str, path: str) -> str:
    with urlopen(base_url + path, timeout=5) as response:
        return response.read().decode("utf-8")


def get_error_json(base_url: str, path: str) -> dict:
    try:
        with urlopen(base_url + path, timeout=5) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        return json.loads(exc.read().decode("utf-8"))


def post_json(base_url: str, path: str, payload: dict) -> dict:
    body = json.dumps(payload).encode("utf-8")
    request = Request(
        base_url + path,
        data=body,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    with urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))

def http_error(base_url: str, path: str, method: str) -> int:
    request = Request(base_url + path, method=method)
    try:
        urlopen(request, timeout=5)
    except HTTPError as exc:
        return int(exc.code)
    raise AssertionError(f"{method} {path} should fail")


def file_content_fingerprints(root: Path) -> dict[str, tuple[int, bytes]]:
    return {
        str(path.relative_to(root)): (path.stat().st_size, path.read_bytes())
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }

def file_fingerprints(root: Path) -> dict[str, tuple[int, int]]:
    return {
        str(path.relative_to(root)): (path.stat().st_size, path.stat().st_mtime_ns)
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }
