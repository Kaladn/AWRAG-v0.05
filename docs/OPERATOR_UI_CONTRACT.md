# Operator UI Contract

Purpose: define the terminal-first operator surface without moving business logic into a UI.

## Shape

The operator surface is chat-first:

```text
chat/input stays central
slash command starts at character 0
command registry accepts or rejects
existing AW CLI command does the work
receipts prove the result
```

The shell is not a backend replacement. It is a command cockpit.

## Command Law

```text
Corpus slash text is data.
Start-of-live-input slash text is an operator command.
Commands require registry hash acceptance.
```

Accepted command source:

```text
active_operator_chat
```

Rejected sources:

- corpus replay
- logs
- reports
- staged documents
- old chat text
- any slash text not at character 0

## Authority Boundary

The shell may:

- show available commands
- show shortcuts
- show exact CLI handoff commands
- launch approved side-window helpers
- show locked commands as locked

The shell may not:

- decide evidence truth
- mutate dataset state by itself
- change count/ranking behavior
- change citation authority
- bypass receipts
- hide mutating operations

## Current Entry Point

```powershell
python -m awrag.operator_shell
```

Single-command check:

```powershell
python -m awrag.operator_shell --once /status
```

Installed script, when installed from package metadata:

```powershell
awrag-operator
```

## Side Windows

Side windows are helpers, not authorities.

Allowed first helper:

```text
/laptop -> Start_Laptop_Temp_Intake.ps1
```

Side-window launch is disabled unless explicitly enabled:

```powershell
python -m awrag.operator_shell --launch-side-windows
```

Every side operation must still write receipts.

## Locked Commands

Commands can exist in the operator surface before they are enabled.

Locked commands must say they are locked and must not mutate state.

Current locked command:

```text
/exfil
```

Reason:

```text
action bridge not enabled
```
