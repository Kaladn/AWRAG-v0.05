# OSRL v0 Receipt

Status: implemented as audit-only operator input routing.

Entry points:

```text
python -m awrag.cli operator-state-audit --input <text>
python -m awrag.operator_shell
```

Implemented files:

```text
src/awrag/operator_state/__init__.py
src/awrag/operator_state/anchors.py
src/awrag/operator_state/rules.py
src/awrag/operator_state/modes.py
src/awrag/operator_state/audit.py
src/awrag/operator_state/schemas.py
```

Current behavior:

```text
raw input
-> deterministic anchor extraction
-> anchor scores
-> structural analysis
-> operational routing
-> audit-only receipt
```

Conversation shell behavior:

```text
every input to awrag.operator_shell receives an OSRL audit
slash command handling remains explicit
non-command input receives OSRL mode output
no backend state is mutated by OSRL
```

Boundaries:

```text
production_command_execution = false
backend_mutation = false
count_mutation = false
lifetime_memory_write = false
model_classifier = false
```

OSRL audit is not evidence audit.

OSRL audit:

```text
what kind of operator input is this?
```

Evidence audit:

```text
what does the admitted dataset prove?
```
