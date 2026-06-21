from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class ScaffoldQuestionRecord:
    schema: str
    question_id: str
    parent_id: str | None
    depth: int
    question: str
    source_dataset: str
    source: str = "chat_dataset_scaffold"
    major_anchors: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    def to_dict(self) -> dict[str, Any]: return asdict(self)


@dataclass(frozen=True)
class ScaffoldAttemptRecord:
    schema: str
    attempt_id: str
    question_id: str
    parent_id: str | None
    depth: int
    question: str
    answer_text: str
    major_anchors: list[str]
    citations: list[str]
    crossings: list[dict[str, Any]]
    evidence_frame_count: int
    source_dataset: str
    output_path: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    def to_dict(self) -> dict[str, Any]: return asdict(self)


@dataclass(frozen=True)
class ScaffoldFailureRecord:
    schema: str
    failure_id: str
    attempt_id: str
    question_id: str
    failure_types: list[str]
    failure_explanation: str
    retry_guidance: list[str]
    missing_variables: list[str] = field(default_factory=list)
    unsupported_terms: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    def to_dict(self) -> dict[str, Any]: return asdict(self)


@dataclass(frozen=True)
class ScaffoldCorrectionRecord:
    schema: str
    correction_id: str
    failure_id: str
    question_id: str
    correction_notes: list[str]
    next_question: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    def to_dict(self) -> dict[str, Any]: return asdict(self)


@dataclass(frozen=True)
class ScaffoldBehaviorRecord:
    schema: str
    behavior_id: str
    attempt_id: str
    question_id: str
    status: str
    reason: str
    promotable: bool
    metadata: dict[str, Any] = field(default_factory=dict)
    def to_dict(self) -> dict[str, Any]: return asdict(self)


@dataclass(frozen=True)
class ScaffoldRunSummary:
    schema: str
    run_id: str
    dataset_id: str
    runtime_root: str
    output_dir: str
    question_count: int
    attempt_count: int
    failure_count: int
    correction_count: int
    behavior_count: int
    max_records: int
    completed: bool
    recommendation: str
    metadata: dict[str, Any] = field(default_factory=dict)
    def to_dict(self) -> dict[str, Any]: return asdict(self)
