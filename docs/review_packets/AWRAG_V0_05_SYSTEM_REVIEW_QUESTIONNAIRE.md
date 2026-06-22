# AWRAG-v0.05 System Review Questionnaire

Purpose: give another Codex or human reviewer a strict review packet for `AWRAG-v0.05`.

Answer rule:

```text
Answer with receipts.
If a claim comes from docs, label it: docs claim.
If a claim comes from code/tests/smoke output, label it: verified.
If a claim is uncertain, label it: unknown and explain what was checked.
```

Do not guess. Inspect the repo, run the agreed verification commands, and cite paths/commands/results.

## Repo / Git

1. What branch are you on?
2. What commit is HEAD?
3. What remote URL is configured?
4. Is the working tree clean? If not, list modified/untracked files.
5. Is this main/master or an updates/* branch?

## Contract

6. What does `README.md` say AWRAG is proving?
7. What is the declared count backend?
8. What is the declared compute engine?
9. What is the declared symbol system?
10. Are symbols dataset-local, lifetime, or transferable?
11. Who owns citations?
12. Can a model search, select evidence, or create citations?
13. What is Python allowed to do?
14. What is Python forbidden from doing?
15. What is the native component responsible for?

## Code Verification

16. Where is the CLI entry point?
17. What CLI commands exist?
18. Where is the native engine launcher?
19. Where is the C++ count engine source?
20. Does query/intake/status call the native executable?
21. Are Python count-walking functions active or blocked?
22. Is SQLite used anywhere in runtime code?
23. Are there tests preventing backend substitution?
24. Are there tests proving native count ownership?
25. Are there tests proving citations stay AWRAG-owned?

## Runtime / Workspace

26. Does the repo contain generated cache/build/runtime residue?
27. Are there local-only folders that should live outside the repo workspace?
28. Does `.gitignore` protect runtime outputs and binary artifacts?
29. Are there hardcoded local machine paths in tracked code/docs?
30. Does the repo assume any private local data?

## Verification

31. What exact test command did you run?
32. Did tests pass? Give exact count.
33. Did you run a tiny smoke test? If yes, where was the runtime created?
34. Did the smoke create `.awbin` files?
35. Did status report native backend and native compute engine?
36. Did query return AWRAG-owned citations?
37. Did query report `model_used=none`?
38. Did query report `model_may_search=false`?

## Risks / Concerns

39. What is the highest severity issue?
40. Is there any docs/code mismatch?
41. Is there any evidence of Python owning the count compute path?
42. Is there any evidence of SQL/database backend use?
43. Is there any evidence of lifetime/user memory writes?
44. Is there any evidence the UI contains backend/business logic?
45. Are there dirty local changes that should not be trusted yet?

## Decision

46. Is this repo safe to use as the current AWRAG base?
47. What must be fixed before handoff?
48. What must be moved outside the repo workspace?
49. What should not be touched?
50. What is the next grown-up setup step?

## Suggested Receipt Commands

Run from the repo root unless stated otherwise.

```powershell
git branch --show-current
git rev-parse HEAD
git remote -v
git status --short
python -m pytest tests -q
python -m awrag.cli --help
```

Search checks:

```powershell
rg -n "sqlite3|dataset_counts\.sqlite|model_may_search|model_used|awrag_native|native" README.md src tests docs -S
$slash = "\"
$localPathPattern = "C:" + $slash + $slash + "|D:" + $slash + $slash + "|E:" + $slash + $slash + "|Users" + $slash + $slash + "|my" + "dyi|LEX" + "AR|AnchorWorks" + "_Clean_Runtime"
rg -n $localPathPattern README.md src tests docs -S
```

Smoke test should be tiny, local, and disposable. Record every command and output path. Do not use private datasets for the handoff receipt.
