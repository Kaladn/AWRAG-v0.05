from __future__ import annotations

from pathlib import Path
from time import perf_counter
from typing import Any, Iterable

from .base import safe_id, unique_stamp, utc_now, with_protected_notice, write_json
from .native import run_native_counts
from .storage import ensure_dataset


def query(
    runtime_root: str | Path,
    dataset_id: str,
    question: str,
    *,
    top_k: int = 5,
    created_after: str | None = None,
    created_before: str | None = None,
    speaker: str | None = None,
) -> dict[str, Any]:
    args = [
        "query",
        "--runtime-root",
        str(runtime_root),
        "--dataset-id",
        dataset_id,
        "--question",
        question,
        "--top-k",
        str(top_k),
    ]
    if created_after:
        args.extend(["--created-after", created_after])
    if created_before:
        args.extend(["--created-before", created_before])
    if speaker:
        args.extend(["--speaker", speaker])
    return run_native_counts(args)


def batch_questions(
    runtime_root: str | Path,
    dataset_id: str,
    questions_path: str | Path,
    *,
    top_k: int = 5,
    show_progress: bool = False,
) -> dict[str, Any]:
    paths = __import__("awrag.engine.base", fromlist=["dataset_paths"]).dataset_paths(runtime_root, dataset_id)
    ensure_dataset(runtime_root, dataset_id)
    source = Path(questions_path).expanduser().resolve()
    questions = [line.strip() for line in source.read_text(encoding="utf-8").splitlines() if line.strip()]
    run_id = unique_stamp()
    run_dir = paths.outputs / f"batch_{run_id}"
    run_dir.mkdir(parents=True, exist_ok=True)

    started = perf_counter()
    completed = 0
    failures: list[dict[str, Any]] = []
    output_paths: list[str] = []
    question_results: list[dict[str, Any]] = []

    items = _progress_iter(enumerate(questions, start=1), total=len(questions), enabled=show_progress)
    for index, item_question in items:
        item_started = perf_counter()
        try:
            result = query(runtime_root, dataset_id, item_question, top_k=top_k)
            elapsed = perf_counter() - item_started
            completed += 1
            output_path = str(result["output_path"])
            output_paths.append(output_path)
            question_results.append({
                "index": index,
                "question": item_question,
                "status": "completed",
                "output_path": output_path,
                "query_time_seconds": elapsed,
                "model_used": result.get("model_used", "none"),
            })
        except Exception as exc:  # pragma: no cover
            elapsed = perf_counter() - item_started
            failure = {
                "index": index,
                "question": item_question,
                "status": "failed",
                "error": str(exc),
                "query_time_seconds": elapsed,
                "model_used": "none",
            }
            failures.append(failure)
            question_results.append(failure)

    total_elapsed = perf_counter() - started
    average = total_elapsed / len(questions) if questions else 0.0
    summary = with_protected_notice({
        "schema": "awrag_batch_run_summary@1",
        "run_id": run_id,
        "created_at": utc_now(),
        "dataset": safe_id(dataset_id),
        "dataset_id": safe_id(dataset_id),
        "scope": "dataset_local",
        "questions_path": str(source),
        "question_count": len(questions),
        "completed": completed,
        "failed": len(failures),
        "output_paths": output_paths,
        "question_results": question_results,
        "failures": failures,
        "avg_query_time": average,
        "avg_query_time_seconds": average,
        "total_time_seconds": total_elapsed,
        "model_used": "none",
        "model_may_search": False,
        "persistent_memory": False,
    })
    summary_path = run_dir / "batch_run_summary.json"
    write_json(summary_path, summary)
    summary["summary_path"] = str(summary_path)
    return summary


def top_relation_neighbors(*_args: Any, **_kwargs: Any) -> list[dict[str, Any]]:
    raise RuntimeError("AWRAG relation walking is owned by the native C++ compute engine")


def score_blocks(*_args: Any, **_kwargs: Any) -> list[dict[str, Any]]:
    raise RuntimeError("AWRAG block scoring is owned by the native C++ compute engine")


def _progress_iter(iterable: Iterable[Any], *, total: int, enabled: bool) -> Iterable[Any]:
    if not enabled:
        return iterable
    try:
        from tqdm import tqdm
    except Exception:  # pragma: no cover
        return iterable
    return tqdm(iterable, total=total, desc="AWRAG batch", unit="question")
