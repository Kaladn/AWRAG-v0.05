from __future__ import annotations

import argparse
import json
from pathlib import Path

from .engine import batch_questions, ensure_dataset, intake, query, status, with_protected_notice


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
    parser.add_argument("--version", action="version", version="awrag 0.1.0")
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

    status_cmd = sub.add_parser("status", help="Show dataset-local status")
    status_cmd.add_argument("--runtime-root", type=Path, required=True)
    status_cmd.add_argument("--dataset-id", required=True)

    query_cmd = sub.add_parser("query", help="Return a cited local answer packet from dataset coordinates")
    query_cmd.add_argument("--runtime-root", type=Path, required=True)
    query_cmd.add_argument("--dataset-id", required=True)
    query_cmd.add_argument("--question", required=True)
    query_cmd.add_argument("--top-k", type=int, default=5)


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
    args = parser.parse_args()
    if args.command == "init":
        result = ensure_dataset(args.runtime_root, args.dataset_id, owner=args.owner)
    elif args.command == "intake":
        result = intake(args.runtime_root, args.dataset_id, args.source, owner=args.owner, window=args.window)
    elif args.command == "status":
        result = status(args.runtime_root, args.dataset_id)
    elif args.command == "query":
        result = query(args.runtime_root, args.dataset_id, args.question, top_k=args.top_k)
    elif args.command == "batch":
        result = batch_questions(args.runtime_root, args.dataset_id, args.questions, top_k=args.top_k, show_progress=not args.no_progress)
    else:
        parser.error("unknown command")

    print(json.dumps(with_protected_notice(result), ensure_ascii=True))


if __name__ == "__main__":
    main()
