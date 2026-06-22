from __future__ import annotations

import argparse
import json
from pathlib import Path

from .engine import (
    batch_questions,
    build_citation_crosslinks,
    determinism_receipt,
    ensure_dataset,
    intake,
    query,
    stage_codex_sessions,
    status,
    special_search,
    with_protected_notice,
)
from .engine.laptop_temp_intake import laptop_temp_intake


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="awrag",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="AWRAG dataset-local evidence engine CLI.",
        epilog="""
Batch walkthrough:
  1. Create a plain text file with one question per line.
  2. Make sure the dataset has already been built with awrag intake.
  3. Run: awrag batch --runtime-root <runtime> --dataset <name> --questions questions.txt
  4. Watch the tqdm progress bar in the terminal.
  5. Open the reported batch_run_summary.json when complete.
""",
    )
    parser.add_argument("--version", action="version", version="awrag 0.05")
    sub = parser.add_subparsers(dest="command", required=True)

    init_cmd = sub.add_parser("init", help="Create a dataset-local AWRAG scope")
    init_cmd.add_argument("--runtime-root", type=Path, required=True)
    init_cmd.add_argument("--dataset-id", required=True)
    init_cmd.add_argument("--owner", default="operator_defined")

    intake_cmd = sub.add_parser("intake", help="Build dataset-local lexicon, counts, coordinates, and citations")
    intake_cmd.add_argument("--runtime-root", type=Path, required=True)
    intake_cmd.add_argument("--dataset-id", required=True)
    intake_cmd.add_argument("--source", type=Path, required=True)
    intake_cmd.add_argument("--owner", default="operator_defined")
    intake_cmd.add_argument("--window", type=int, default=6)
    laptop_cmd = sub.add_parser(
        "laptop-temp-intake",
        help="Prepare bounded chunk-local symbol/count artifacts without production merge",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Laptop-safe temporary chunk prep. Writes per-chunk symbols, lexicon deltas, counts, and receipts only.",
        epilog="""
Step-by-step:
  1. Point --source at one file or a staged folder.
  2. Use --chunk-mb 25 or --chunk-mb 50 on laptop hardware.
  3. Use --workers auto unless you need a fixed worker count.
  4. Use --max-chunks 3 for the first proof run.
  5. Review resource_receipt.json, run_summary.json, chunk receipts, and failure receipts.
  6. This command does not merge counts into a dataset and does not write lifetime memory.
""",
    )
    laptop_cmd.add_argument("--source", type=Path, required=True)
    laptop_cmd.add_argument("--state-root", type=Path, default=Path("State/laptop_temp_intake"))
    laptop_cmd.add_argument("--run-id")
    laptop_cmd.add_argument("--chunk-mb", type=int, default=50)
    laptop_cmd.add_argument("--max-chunks", type=int)
    laptop_cmd.add_argument("--window", type=int, default=6)
    laptop_cmd.add_argument("--workers", default="auto", help="Worker count or auto. Auto reserves system/operator resources.")
    laptop_cmd.add_argument("--reserve-ram-fraction", type=float, default=0.50, help="Fraction of total RAM to reserve for the system/operator.")
    laptop_cmd.add_argument("--reserve-ram-gb", type=float, help="Minimum RAM, in GiB, to reserve for the system/operator.")
    laptop_cmd.add_argument("--no-progress", action="store_true")

    status_cmd = sub.add_parser("status", help="Show dataset-local status")
    status_cmd.add_argument("--runtime-root", type=Path, required=True)
    status_cmd.add_argument("--dataset-id", required=True)

    query_cmd = sub.add_parser("query", help="Return a cited local answer packet from dataset coordinates")
    query_cmd.add_argument("--runtime-root", type=Path, required=True)
    query_cmd.add_argument("--dataset-id", required=True)
    query_cmd.add_argument("--question", required=True)
    query_cmd.add_argument("--top-k", type=int, default=5)
    query_cmd.add_argument("--created-after", help="Optional chat metadata lower bound, e.g. 2024-12-14")
    query_cmd.add_argument("--created-before", help="Optional chat metadata upper bound, e.g. 2024-12-15")
    query_cmd.add_argument("--speaker", choices=["user", "assistant"], help="Optional chat metadata speaker filter")


    batch_cmd = sub.add_parser(
        "batch",
        help="Run a plain question list through dataset-local query",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Run many dataset questions through the existing AWRAG query path.",
        epilog="""
Step-by-step:
  1. Put one question per line in questions.txt.
  2. Blank lines are ignored.
  3. Run:
       awrag batch --runtime-root <runtime> --dataset <name> --questions questions.txt
  4. tqdm shows question-by-question progress.
  5. Each question writes its own query JSON output.
  6. The batch writes outputs/batch_<run_id>/batch_run_summary.json.
  7. model_used remains none.
""",
    )
    batch_cmd.add_argument("--runtime-root", type=Path, required=True)
    batch_cmd.add_argument("--dataset-id", "--dataset", dest="dataset_id", required=True)
    batch_cmd.add_argument("--questions", type=Path, required=True)
    batch_cmd.add_argument("--top-k", type=int, default=5)
    batch_cmd.add_argument("--no-progress", action="store_true", help="Disable tqdm progress display for scripted runs")

    codex_cmd = sub.add_parser("stage-codex", help="Stage Codex session JSONL as AWRAG chat-turn markdown")
    codex_cmd.add_argument("--sessions-root", type=Path, required=True)
    codex_cmd.add_argument("--output", type=Path, required=True)
    codex_cmd.add_argument("--session-index", type=Path)
    codex_cmd.add_argument("--max-files", type=int)

    crosslink_cmd = sub.add_parser("crosslink", help="Build citation crosslinks between two dataset-local scopes")
    crosslink_cmd.add_argument("--runtime-root", type=Path, required=True)
    crosslink_cmd.add_argument("--left-dataset-id", required=True)
    crosslink_cmd.add_argument("--right-dataset-id", required=True)
    crosslink_cmd.add_argument("--question", required=True)
    crosslink_cmd.add_argument("--top-k", type=int, default=8)
    crosslink_cmd.add_argument("--min-shared", type=int, default=3)


    special_cmd = sub.add_parser(
        "special-search",
        help="Run JSON-list driven anchor special search reports",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Run the locked special-search path: JSON anchors -> solo search -> expanded context -> receipts.",
        epilog="""
Step-by-step:
  1. Prepare a JSON list with anchors or entries.
  2. Make sure the dataset has already been built with awrag intake.
  3. Run:
       awrag special-search --runtime-root <runtime> --dataset-id <dataset> --trigger-list triggers.json --out reports/special_search
  4. Open trigger_anchor_summary.md and run_receipt.json when complete.
  5. Grouped phrases that cannot run as solo anchors are written to unmatched_phrases.jsonl.
""",
    )
    special_cmd.add_argument("--runtime-root", type=Path, required=True)
    special_cmd.add_argument("--dataset-id", "--dataset", dest="dataset_id", required=True)
    special_cmd.add_argument("--trigger-list", type=Path, required=True)
    special_cmd.add_argument("--out", type=Path, required=True)
    special_cmd.add_argument("--expand-prev", type=int, default=1)
    special_cmd.add_argument("--expand-next", type=int, default=1)
    special_cmd.add_argument("--max-hits-per-anchor", type=int, default=500)
    determinism_cmd = sub.add_parser("determinism", help="Write a twin-machine dataset/query determinism receipt")
    determinism_cmd.add_argument("--runtime-root", type=Path, required=True)
    determinism_cmd.add_argument("--dataset-id", "--dataset", dest="dataset_id", required=True)
    determinism_cmd.add_argument("--question", action="append", help="Question to run into the raw packet comparison receipt")
    determinism_cmd.add_argument("--questions", type=Path, help="Plain text file with one question per line")
    determinism_cmd.add_argument("--top-k", type=int, default=5)
    determinism_cmd.add_argument("--output", type=Path, help="Optional receipt JSON path")
    args = parser.parse_args()
    if args.command == "init":
        result = ensure_dataset(args.runtime_root, args.dataset_id, owner=args.owner)
    elif args.command == "intake":
        result = intake(args.runtime_root, args.dataset_id, args.source, owner=args.owner, window=args.window)
    elif args.command == "laptop-temp-intake":
        result = laptop_temp_intake(
            args.source,
            state_root=args.state_root,
            run_id=args.run_id,
            chunk_mb=args.chunk_mb,
            max_chunks=args.max_chunks,
            window=args.window,
            workers=args.workers,
            reserve_ram_fraction=args.reserve_ram_fraction,
            reserve_ram_gb=args.reserve_ram_gb,
            show_progress=not args.no_progress,
        )
    elif args.command == "status":
        result = status(args.runtime_root, args.dataset_id)
    elif args.command == "query":
        result = query(
            args.runtime_root,
            args.dataset_id,
            args.question,
            top_k=args.top_k,
            created_after=args.created_after,
            created_before=args.created_before,
            speaker=args.speaker,
        )
    elif args.command == "batch":
        result = batch_questions(args.runtime_root, args.dataset_id, args.questions, top_k=args.top_k, show_progress=not args.no_progress)
    elif args.command == "stage-codex":
        result = stage_codex_sessions(
            args.sessions_root,
            args.output,
            session_index_path=args.session_index,
            max_files=args.max_files,
        )
    elif args.command == "crosslink":
        result = build_citation_crosslinks(
            args.runtime_root,
            args.left_dataset_id,
            args.right_dataset_id,
            args.question,
            top_k=args.top_k,
            min_shared=args.min_shared,
        )
    elif args.command == "special-search":
        result = special_search(
            args.runtime_root,
            args.dataset_id,
            args.trigger_list,
            args.out,
            expand_prev=args.expand_prev,
            expand_next=args.expand_next,
            max_hits_per_anchor=args.max_hits_per_anchor,
        )
    elif args.command == "determinism":
        result = determinism_receipt(
            args.runtime_root,
            args.dataset_id,
            questions=args.question,
            questions_path=args.questions,
            top_k=args.top_k,
            output_path=args.output,
        )
    else:
        parser.error("unknown command")

    print(json.dumps(with_protected_notice(result), ensure_ascii=True))


if __name__ == "__main__":
    main()
