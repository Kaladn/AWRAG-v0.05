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
        assert manifest["symbol_system"] == "awrag_public_6b@1"
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


def test_read_only_ui_server_serves_static_mockup(tmp_path: Path) -> None:
    runtime = build_dataset(tmp_path)
    with running_server(runtime, DATASET_ID) as base_url:
        body = get_text(base_url, "/")
    assert "Deterministic Evidence Interrogation" in body
    assert "CLI or UI option" in body


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


def http_error(base_url: str, path: str, method: str) -> int:
    request = Request(base_url + path, method=method)
    try:
        urlopen(request, timeout=5)
    except HTTPError as exc:
        return int(exc.code)
    raise AssertionError(f"{method} {path} should fail")


def file_fingerprints(root: Path) -> dict[str, tuple[int, int]]:
    return {
        str(path.relative_to(root)): (path.stat().st_size, path.stat().st_mtime_ns)
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }
