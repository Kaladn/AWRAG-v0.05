from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from experiments.scaffold_records import (
    ScaffoldAttemptRecord,
    ScaffoldBehaviorRecord,
    ScaffoldCorrectionRecord,
    ScaffoldFailureRecord,
    ScaffoldRunSummary,
)


class ScaffoldReceiptWriter:
    def __init__(self, output_dir: str | Path) -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.packets_dir = self.output_dir / "packets"
        self.packets_dir.mkdir(parents=True, exist_ok=True)
        self.questions_path = self.output_dir / "questions.jsonl"
        self.attempts_path = self.output_dir / "attempts.jsonl"
        self.failures_path = self.output_dir / "failures.jsonl"
        self.corrections_path = self.output_dir / "corrections.jsonl"
        self.behaviors_path = self.output_dir / "behaviors.jsonl"
        self.citation_mirror_path = self.output_dir / "citation_mirror.jsonl"
        self.crosslinks_path = self.output_dir / "crosslinks.jsonl"

    def write_manifest(self, payload: dict[str, Any]) -> Path:
        path = self.output_dir / "run_manifest.json"
        path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
        return path

    def append_question(self, payload: dict[str, Any]) -> None:
        self._append_jsonl(self.questions_path, payload)

    def append_attempt(self, record: ScaffoldAttemptRecord) -> None:
        self._append_jsonl(self.attempts_path, record.to_dict())

    def append_failure(self, record: ScaffoldFailureRecord) -> None:
        self._append_jsonl(self.failures_path, record.to_dict())

    def append_correction(self, record: ScaffoldCorrectionRecord) -> None:
        self._append_jsonl(self.corrections_path, record.to_dict())

    def append_behavior(self, record: ScaffoldBehaviorRecord) -> None:
        self._append_jsonl(self.behaviors_path, record.to_dict())

    def append_citation_mirror(self, row: dict[str, Any]) -> None:
        self._append_jsonl(self.citation_mirror_path, row)

    def append_crosslink(self, row: dict[str, Any]) -> None:
        self._append_jsonl(self.crosslinks_path, row)

    def write_packet(self, packet_index: int, payload: dict[str, Any]) -> Path:
        path = self.packets_dir / f"packet_{packet_index:03d}.json"
        path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
        return path

    def write_summary(self, summary: ScaffoldRunSummary) -> tuple[Path, Path]:
        payload = summary.to_dict()
        json_path = self.output_dir / "summary.json"
        md_path = self.output_dir / "summary.md"
        json_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
        md_path.write_text(_summary_markdown(payload), encoding="utf-8")
        return json_path, md_path

    @staticmethod
    def _append_jsonl(path: Path, payload: dict[str, Any]) -> None:
        with path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(payload, ensure_ascii=True) + "\n")


def _summary_markdown(payload: dict[str, Any]) -> str:
    return "\n".join([
        "# Scaffold Loop v0 Summary",
        "",
        f"Run: `{payload.get('run_id')}`",
        f"Dataset: `{payload.get('dataset_id')}`",
        f"Questions: {payload.get('question_count')}",
        f"Attempts: {payload.get('attempt_count')}",
        f"Failures: {payload.get('failure_count')}",
        f"Corrections: {payload.get('correction_count')}",
        f"Behaviors: {payload.get('behavior_count')}",
        f"Recommendation: `{payload.get('recommendation')}`",
        "",
    ])
