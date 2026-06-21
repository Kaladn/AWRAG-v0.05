from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SCHEMA = "bad_phrase_law_suite@1"

# Default excludes protected-class slurs. Those need a separate safety-audit list,
# not the general profanity/state trigger suite.
_PROTECTED_SLUR_POLICY = "excluded_from_default_bad_phrase_suite"

_BAD_PHRASE_ROWS = [
    # profanity / intensifiers
    ("fuck", "profanity_intensifier", "strong"),
    ("fucking", "profanity_intensifier", "strong"),
    ("fuckin", "profanity_intensifier", "strong"),
    ("fucker", "vulgar_insult", "strong"),
    ("motherfucker", "vulgar_insult", "severe"),
    ("motherfuckers", "vulgar_insult", "severe"),
    ("mother fucker", "vulgar_phrase", "severe"),
    ("what the fuck", "vulgar_phrase", "strong"),
    ("the fuck", "vulgar_phrase", "strong"),
    ("fuck off", "vulgar_phrase", "strong"),
    ("go fuck yourself", "vulgar_phrase", "severe"),
    ("shit", "profanity_intensifier", "medium"),
    ("shitty", "profanity_intensifier", "medium"),
    ("bullshit", "rejection_or_frustration", "strong"),
    ("horseshit", "rejection_or_frustration", "strong"),
    ("batshit", "profanity_intensifier", "medium"),
    ("crap", "profanity_intensifier", "low"),
    ("damn", "profanity_intensifier", "low"),
    ("goddamn", "profanity_intensifier", "medium"),
    ("hell", "profanity_intensifier", "low"),
    ("ass", "vulgarity", "medium"),
    ("asshole", "vulgar_insult", "strong"),
    ("assholes", "vulgar_insult", "strong"),
    ("dumbass", "vulgar_insult", "medium"),
    ("jackass", "vulgar_insult", "medium"),
    ("badass", "vulgar_positive_or_intensifier", "medium"),
    ("kick ass", "vulgar_positive_or_intensifier", "medium"),
    ("pain in the ass", "vulgar_phrase", "medium"),
    # insults / rejection words
    ("bitch", "vulgar_insult", "strong"),
    ("bitches", "vulgar_insult", "strong"),
    ("bastard", "vulgar_insult", "medium"),
    ("bastards", "vulgar_insult", "medium"),
    ("sonofabitch", "vulgar_insult", "strong"),
    ("son of a bitch", "vulgar_phrase", "strong"),
    ("prick", "vulgar_insult", "medium"),
    ("dick", "vulgar_insult_or_vulgarity", "medium"),
    ("dickhead", "vulgar_insult", "strong"),
    ("shithead", "vulgar_insult", "strong"),
    ("fuckhead", "vulgar_insult", "strong"),
    ("dipshit", "vulgar_insult", "strong"),
    ("douche", "vulgar_insult", "medium"),
    ("douchebag", "vulgar_insult", "strong"),
    ("idiot", "rejection_or_frustration", "medium"),
    ("idiocy", "rejection_or_frustration", "medium"),
    ("stupid", "rejection_or_frustration", "medium"),
    ("moron", "rejection_or_frustration", "medium"),
    ("clown", "rejection_or_frustration", "medium"),
    ("trash", "rejection_or_frustration", "medium"),
    ("garbage", "rejection_or_frustration", "medium"),
    ("scum", "vulgar_insult", "strong"),
    ("scumbag", "vulgar_insult", "strong"),
    # sexual/scatological vulgarity that needs context, not diagnosis
    ("cock", "sexual_vulgarity", "strong"),
    ("pussy", "sexual_vulgarity_or_insult", "strong"),
    ("balls", "vulgarity", "medium"),
    ("nuts", "vulgarity_or_idiom", "medium"),
    ("piss", "vulgarity", "medium"),
    ("pissed", "anger_or_vulgarity_candidate", "medium"),
    ("pissing", "anger_or_vulgarity_candidate", "medium"),
    ("screw", "vulgarity_or_action", "low"),
    ("screwed", "vulgarity_or_failure", "low"),
    ("screwing", "vulgarity_or_action", "low"),
    ("suck", "vulgarity_or_negative_judgment", "low"),
    ("sucks", "vulgarity_or_negative_judgment", "low"),
    ("sucked", "vulgarity_or_negative_judgment", "low"),
    ("sucking", "vulgarity_or_action", "low"),
    # boundary/threat phrases are not profanity, but are review-critical bad phrases
    ("kill", "threat_boundary_candidate", "severe"),
    ("kill you", "threat_phrase_candidate", "severe"),
    ("i want to kill", "threat_phrase_candidate", "severe"),
    ("hurt", "threat_or_pain_candidate", "medium"),
    ("hurt you", "threat_phrase_candidate", "severe"),
    ("danger", "boundary_warning", "medium"),
    ("threat", "boundary_warning", "medium"),
    ("unsafe", "boundary_warning", "medium"),
    # intentionality / blame attribution candidates need special review
    ("did it on purpose", "intentionality_attribution_candidate", "strong"),
    ("on purpose", "intentionality_attribution_candidate", "medium"),
    ("intentional", "intentionality_attribution_candidate", "medium"),
    ("intentionally", "intentionality_attribution_candidate", "medium"),
    ("deliberate", "intentionality_attribution_candidate", "medium"),
    ("deliberately", "intentionality_attribution_candidate", "medium"),
]


def build_bad_phrase_law_suite() -> dict[str, Any]:
    seen: set[str] = set()
    rows = []
    for surface, phrase_class, severity in _BAD_PHRASE_ROWS:
        key = " ".join(surface.strip().lower().split())
        if not key or key in seen:
            continue
        seen.add(key)
        rows.append({
            "surface": key,
            "anchors": key.split(),
            "class": phrase_class,
            "severity": severity,
            "authority": "corpus_state_signal_candidate",
            "needs_expanded_context": True,
            "needs_review": True,
            "confidence": 0.0,
            "interpretation_policy": "never_infer_fixed_emotion_from_phrase_alone",
            "notes": "Search candidate only. Meaning depends on previous/current/next corpus context.",
        })
    return {
        "schema": SCHEMA,
        "source": "local_chat_corpus_review_policy",
        "protected_slur_policy": _PROTECTED_SLUR_POLICY,
        "count": len(rows),
        "entries": rows,
    }


def write_bad_phrase_law_suite(path: str | Path, payload: dict[str, Any] | None = None) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    data = payload or build_bad_phrase_law_suite()
    target.write_text(json.dumps(data, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    return target


def load_bad_phrase_law_suite(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def solo_anchor_entries(payload: dict[str, Any]) -> list[dict[str, Any]]:
    return [row for row in payload.get("entries", []) if len(row.get("anchors", [])) == 1]


def phrase_entries(payload: dict[str, Any]) -> list[dict[str, Any]]:
    return [row for row in payload.get("entries", []) if len(row.get("anchors", [])) > 1]
