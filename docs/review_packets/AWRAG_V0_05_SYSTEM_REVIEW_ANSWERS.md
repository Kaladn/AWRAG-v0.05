# AWRAG-v0.05 System Review Answers

Review date: 2026-06-22

Reviewer stance: answer with receipts. `docs claim` means the claim came from project docs. `verified` means code, tests, or smoke output proved it in this checkout. `risk` means the repo should not pretend the item is clean.

## Repo / Git

1. Branch: `master`. Verified with `git branch --show-current`.
2. HEAD: `65a6ea64b02d44c19ebfd91eeae6b49727b15893`. Verified with `git rev-parse HEAD`.
3. Remote URL: `https://github.com/Kaladn/AWRAG-v0.05.git`. Verified with `git remote -v`.
4. Working tree at review start: clean. After review work: questionnaire doc was modified and this answer doc was added.
5. This is `master`, not an `updates/*` branch.

## Contract

6. README says AWRAG is proving the AnchorWorks evidence contract: local dataset intake, dataset-local counts/lexical values, source coordinates, AWRAG-owned citations, receipts, strict data boundaries, optional model/no-model boundary, and deterministic NLP wording from locked evidence packets. Docs claim.
7. Declared count backend: `awrag_native_binary_counts@1`. Docs claim in `README.md`; verified in `src/awrag/engine/base.py`.
8. Declared compute engine: no separate compute-engine field is declared in runtime status. README declares native fixed-width binary count backend and deterministic NLP resolver. Verified smoke status reports count backend, not a native compute engine field.
9. Declared symbol system: `awrag_public_6b@1`, `symbol_bytes = 6`. Docs claim and verified in `src/awrag/engine/base.py`.
10. Symbols are dataset-local demo symbols, not lifetime and not transferable. Docs claim and tests verify `symbol_transferable is False`, `lifetime_allowed is False`, and `anchorworks_lifetime_symbol_compatible is False`.
11. Citations are owned by AWRAG. Docs claim in README and `ARCHITECTURE_GUARDRAILS.md`; verified by query tests requiring `[AWCIT-...]` citations from AWRAG locations.
12. A model cannot search, select evidence, own truth, or create citations. Docs claim; tests verify `model_used = none` and `model_may_search = false`.
13. Python is allowed for the current package CLI, orchestration, deterministic resolver, report tools, UI server wrapper, `.awbin` read/write, and active query/intake functions. Verified from `src/awrag/cli.py`, `src/awrag/engine/*.py`, and tests.
14. Python is forbidden by contract from becoming model authority, inventing citations, replacing AWRAG evidence selection with LLM reasoning, introducing SQL backend substitution, or letting the NLP resolver search/read counts/read source files/create citations/call a model. Docs claim in guardrails; resolver code follows the no-model citation packet boundary.
15. Native component responsibility: docs claim native binary count backend. Verified code does not show a native executable or C++ component in this checkout. The actual active component is Python writing/reading fixed-width `.awbin` files and walking those files during query.

## Code Verification

16. CLI entry point: `src/awrag/cli.py`, exposed in `pyproject.toml` as `awrag = awrag.cli:main`. Verified.
17. CLI commands: `init`, `intake`, `laptop-temp-intake`, `status`, `query`, `batch`, `stage-codex`, `crosslink`, `special-search`, `determinism`, `operator-state-audit`. Verified by `python -m awrag.cli --help`.
18. Native engine launcher: none found. Verified by file scan and source search.
19. C++ count engine source: none found. Verified by scanning for native source extensions and executable source files.
20. Query/intake/status do not call a native executable. Verified: `src/awrag/engine/pipeline.py`, `storage.py`, and `querying.py` implement the paths directly in Python.
21. Python count-walking functions are active, not blocked. Verified: `top_relation_neighbors`, `score_blocks`, `iter_relation_records`, and `read_block_anchor_rows` are active in `src/awrag/engine/querying.py` and `storage.py`.
22. SQLite is not used in runtime code. Verified: `src` search shows no `sqlite3` runtime import. SQLite references remain in docs/tests as negative guardrails.
23. Tests preventing backend substitution exist. Verified: `test_demo_uses_native_binary_counts_not_sqlite` requires `.awbin` files and rejects `dataset_counts.sqlite` / `sqlite_counts_path`.
24. Tests proving native count ownership partially exist. Verified: tests prove `.awbin` count files and no SQLite. Risk: they do not prove C++/native executable ownership.
25. Tests proving citations stay AWRAG-owned exist. Verified: `test_query_returns_awrag_owned_citations` and `test_nlp_resolver_does_not_invent_citations_or_use_rejected_locations`.

## Runtime / Workspace

26. Generated local residue exists in the workspace but is ignored: `runtime/`, `.pytest_cache/`, and `__pycache__/` folders. Verified by filesystem scan. These should not be pushed.
27. Local-only folders that should live outside the repo workspace: `runtime/` and any large local benchmark/intake output. Ignored cache folders may be deleted, but runtime data should not be deleted casually.
28. `.gitignore` protects many runtime outputs: `runtime/`, `datasets/`, `outputs/`, `receipts/`, `State/`, `*.sqlite`, `*.db`, `*.bin`, `*.jsonl`, bytecode/cache folders, and private chat exports. Risk: `.awbin` is protected when under ignored runtime dirs, but not globally ignored by extension.
29. Hardcoded local machine paths in tracked code/docs: full hygiene test passes after fixing the questionnaire. Risk: `AWRAG_TRUE_HISTORY_FOR_COMPARISON.local` is tracked and intentionally contains historical local run paths, but it is a `.local` history artifact and not scanned as release docs.
30. The repo does not require private local data for tests or smoke. Risk: tracked historical comparison file preserves local run history and should be reviewed before public handoff.

## Verification

31. Exact test command run:

```powershell
$env:PYTHONPATH='src'
$env:PYTHONDONTWRITEBYTECODE='1'
python -m pytest tests -q
```

32. Test result: `82 passed in 5.94s`. Verified.
33. Tiny smoke test: yes. Runtime was created under `%TEMP%/awrag_review_smoke_20260622171140/runtime`. Private absolute path intentionally not recorded in this tracked doc.
34. Smoke created `.awbin` files: yes. Verified `anchor_counts.awbin`, `relation_counts.awbin`, and `block_anchor_postings.awbin`.
35. Smoke status reported native backend: yes, `awrag_native_binary_counts@1`. Smoke status did not report a separate native compute engine field.
36. Smoke query returned AWRAG-owned citation: yes, `[AWCIT-e2823e159b]`.
37. Smoke query reported `model_used=none`: yes.
38. Smoke query reported `model_may_search=false`: yes.

## Risks / Concerns

39. Highest severity issue: docs/branding say native backend, but this checkout has no native executable/C++ source. Verified active compute is Python-managed fixed-width `.awbin` storage and Python count walking/scoring. This is a contract-language risk and should be clarified before handoff.
40. Docs/code mismatch: yes. README/guardrails call the backend native fixed-width binary counts; code verifies `.awbin` binary storage but not native compiled compute. Also active `STOP_ANCHORS` filtering exists in `src/awrag/engine/anchors.py`, which conflicts with the stricter all-anchors doctrine if that doctrine is now required for this repo.
41. Evidence of Python owning count compute path: yes. Verified in `pipeline.py`, `storage.py`, and `querying.py`.
42. Evidence of SQL/database backend use: no runtime evidence. Only negative historical docs/tests mention SQLite.
43. Evidence of lifetime/user memory writes: no production evidence. Tests and code repeatedly mark `persistent_memory = false`, `global_lifetime_write = false`, and `lifetime_allowed = false`.
44. Evidence UI contains backend/business logic: HTML is static/mockup, but `src/awrag/ui_server.py` contains a server-side `/api/ui/batch/run` endpoint that calls CLI batch through Python subprocess. This is not frontend HTML business logic, but it is more than read-only UI. Tests verify it does not mutate count files.
45. Dirty local changes that should not be trusted yet: yes, this answer doc and the questionnaire hygiene fix are local changes until committed. Ignored runtime/cache residue also exists and should not be treated as release content.

## Decision

46. Safe to use as current AWRAG base: yes for public-review evidence-contract work, CLI use, tests, `.awbin` dataset-local storage, citations, receipts, and report tools. No if the claim is "native C++ compute engine is present in this checkout."
47. Must be fixed before handoff: clarify native wording, decide whether Python count walking is acceptable for v0.05, decide whether `STOP_ANCHORS` remains allowed, add/verify global `.awbin` ignore if needed, and decide what to do with `AWRAG_TRUE_HISTORY_FOR_COMPARISON.local`.
48. Must be moved outside repo workspace: ignored `runtime/` local workbench data and any benchmark/intake outputs. Consider moving the tracked `.local` truth-history artifact to private handoff storage or redacting it if public hygiene is strict.
49. Should not be touched: AWRAG-owned citations, coordinate records, `.awbin` count file contract, dataset-local public symbol namespace, `model_used=none` / `model_may_search=false`, and current passing tests unless a specific bug is proven.
50. Next grown-up setup step: split the review base into two explicit lanes. Lane 1: keep current Python-managed `.awbin` AWRAG v0.05 as a stable public-review package with corrected wording. Lane 2: build or attach the real native count engine as a separate explicit upgrade branch with tests proving query/intake/status call the native executable/library.

## Final Verdict

This repo is a working AWRAG v0.05 evidence-contract package. It passes tests and smoke. It produces dataset-local `.awbin` counts, AWRAG citations, coordinates, receipts, and no-model query packets.

The honest correction is that this checkout does not contain or call a native C++ count engine. It contains Python code that creates and walks fixed-width binary `.awbin` count files. Treat that as the main handoff issue, not a hidden success.
