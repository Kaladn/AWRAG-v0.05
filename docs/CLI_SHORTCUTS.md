# CLI Shortcuts

Purpose: define the visible operator handles for the terminal shell.

Slash commands are accepted only at character 0 of live operator input.

| Command | Shortcut | Status | Meaning |
| --- | --- | --- | --- |
| `/intake` | `Ctrl+I` | active contract | Build a dataset-local scope from admitted files. |
| `/query` | `Ctrl+Q` | active contract | Ask one question against an existing dataset. |
| `/batch` | `Ctrl+B` | active contract | Run a plain question file through dataset-local query. |
| `/status` | `Ctrl+S` | active contract | Inspect dataset-local status. |
| `/laptop` | `Ctrl+L` | active contract | Use isolated laptop-temp-intake with resource receipts. |
| `/exfil` | `Ctrl+E` | locked | Future explicit dataset removal/export receipt lane. |
| `/receipts` | `Ctrl+R` | active contract | Open or inspect receipt locations. |
| `/settings` | `Ctrl+,` | active contract | Show operator shell settings. |
| `/help` | `Ctrl+H` | active | Show command and shortcut help. |
| `/quit` | `Ctrl+X` | active | Exit the operator shell. |

## Safety Law

```text
Corpus slash text is data.
Start-of-live-input slash text is an operator command.
Commands require registry hash acceptance.
```

## Run

```powershell
python -m awrag.operator_shell
```

Single-command check:

```powershell
python -m awrag.operator_shell --once /help
```

## Command Card Fields

Each active command card displays:

- shortcut
- summary
- mutating flag
- side-window flag
- touched folders/files
- expected receipts
- next review targets
- exact CLI handoff
