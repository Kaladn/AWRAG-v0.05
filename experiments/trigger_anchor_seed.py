from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SCHEMA = "trigger_anchors@1"

_TRIGGER_ROWS = [
    ("good", "praise"), ("great", "praise"), ("awesome", "praise"), ("nice", "praise"),
    ("perfect", "praise"), ("brilliant", "praise"), ("correct", "praise"), ("exactly", "praise"),
    ("approve", "praise"), ("works", "praise"), ("win", "praise"), ("beast", "praise"),
    ("love", "praise"), ("fun", "praise"), ("strong", "praise"),
    ("wrong", "anger_frustration"), ("trash", "anger_frustration"), ("bullshit", "anger_frustration"),
    ("idiocy", "anger_frustration"), ("stupid", "anger_frustration"), ("dope", "anger_frustration"),
    ("clown", "anger_frustration"), ("garbage", "anger_frustration"), ("swamp", "anger_frustration"),
    ("fighting", "anger_frustration"), ("stop", "anger_frustration"), ("nope", "anger_frustration"),
    ("no", "anger_frustration"), ("delete", "anger_frustration"), ("fuck", "anger_frustration"),
    ("fucking", "anger_frustration"),
    ("correction", "correction_control"), ("retry", "correction_control"), ("fix", "correction_control"),
    ("remove", "correction_control"), ("boundary", "correction_control"), ("not", "correction_control"),
    ("violates", "correction_control"), ("mistake", "correction_control"), ("failed", "correction_control"),
    ("bad", "correction_control"), ("rejected", "correction_control"), ("promote", "correction_control"),
    ("diagnostic", "correction_control"),
    ("sad", "sadness_heartache"), ("hurt", "sadness_heartache"), ("pain", "sadness_heartache"),
    ("loss", "sadness_heartache"), ("heartache", "sadness_heartache"), ("tired", "sadness_heartache"),
    ("exhausted", "sadness_heartache"), ("alone", "sadness_heartache"), ("forgive", "sadness_heartache"),
    ("guilt", "sadness_heartache"), ("regret", "sadness_heartache"), ("grief", "sadness_heartache"),
    ("broken", "sadness_heartache"),
    ("trust", "trust_loyalty"), ("loyal", "trust_loyalty"), ("protect", "trust_loyalty"),
    ("family", "trust_loyalty"), ("grandson", "trust_loyalty"), ("jason", "trust_loyalty"),
    ("partner", "trust_loyalty"), ("team", "trust_loyalty"), ("respect", "trust_loyalty"),
    ("honest", "trust_loyalty"),
    ("work", "work_pressure"), ("painting", "work_pressure"), ("job", "work_pressure"),
    ("underpaid", "work_pressure"), ("rain", "work_pressure"), ("physical", "work_pressure"),
    ("labor", "work_pressure"), ("customer", "work_pressure"), ("finish", "work_pressure"),
    ("cleanup", "work_pressure"),
    ("build", "coding_building"), ("code", "coding_building"), ("module", "coding_building"),
    ("binary", "coding_building"), ("anchor", "coding_building"), ("counts", "coding_building"),
    ("citations", "coding_building"), ("receipts", "coding_building"), ("backend", "coding_building"),
    ("ui", "coding_building"), ("bridge", "coding_building"), ("worker", "coding_building"),
    ("lexicon", "coding_building"), ("memory", "coding_building"),
    ("there", "breakthrough"), ("landed", "breakthrough"), ("slotting", "breakthrough"),
    ("socket", "breakthrough"), ("learned", "breakthrough"), ("remembered", "breakthrough"),
    ("recovered", "breakthrough"), ("found", "breakthrough"), ("receipt", "breakthrough"),
    ("threat", "threat_boundary"), ("unsafe", "threat_boundary"), ("danger", "threat_boundary"),
    ("warning", "threat_boundary"), ("block", "threat_boundary"), ("refuse", "threat_boundary"),
    ("trap", "threat_boundary"), ("quarantine", "threat_boundary"), ("forbid", "threat_boundary"),
    ("hard", "threat_boundary"), ("ban", "threat_boundary"),
    ("lee", "identity"), ("shadow", "identity"), ("wolf", "identity"), ("yournightmare", "identity"),
    ("kaladn", "identity"), ("assistant", "identity"), ("codex", "identity"), ("aw", "identity"),
    ("anchorworks", "identity"), ("clearspeak", "identity"),
    ("music", "love_value"), ("social", "love_value"), ("anger", "love_value"),
    ("frustration", "love_value"), ("pride", "love_value"), ("relief", "love_value"),
]


def build_trigger_anchors(*, top_anchors: int = 100) -> dict[str, Any]:
    seen: set[str] = set()
    anchors = []
    for anchor, anchor_class in _TRIGGER_ROWS:
        key = anchor.strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        anchors.append({
            "anchor": key,
            "class": anchor_class,
            "authority": "corpus_state_signal",
            "notes": "Candidate state signal. Must be confirmed by expanded previous/current/next context.",
            "needs_review": True,
            "diagnostic_warning": "Do not diagnose emotional state from this anchor alone.",
        })
        if len(anchors) >= top_anchors:
            break
    return {"schema": SCHEMA, "source": "local_chat_corpus", "count": len(anchors), "anchors": anchors}


def write_trigger_anchors(path: str | Path, payload: dict[str, Any]) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    return target


def load_trigger_anchors(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))
