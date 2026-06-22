param(
    [Parameter(Mandatory=$true)]
    [string]$Source,

    [string]$StateRoot = "$env:USERPROFILE\AWRAG_Laptop_Temp_Intake",
    [string]$RunId = "",
    [int]$ChunkMb = 25,
    [int]$MaxChunks = 3,
    [string]$Workers = "auto",
    [double]$ReserveRamFraction = 0.50,
    [double]$ReserveRamGb = -1,
    [double]$ProgressSnapshotIntervalSec = 5.0
)

$ErrorActionPreference = "Stop"
$PackageRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

function Quote-Arg([string]$Value) {
    return "'" + ($Value -replace "'", "''") + "'"
}

$commandParts = @(
    '$ErrorActionPreference = "Stop"',
    '$env:PYTHONPATH = ' + (Quote-Arg (Join-Path $PackageRoot "src")),
    'Set-Location ' + (Quote-Arg $PackageRoot),
    'Write-Host ""',
    'Write-Host "AWRAG laptop-temp-intake external run" -ForegroundColor Cyan',
    'Write-Host "Source: ' + ($Source -replace '"', '\"') + '"',
    'Write-Host "State root: ' + ($StateRoot -replace '"', '\"') + '"',
    'Write-Host "Progress: tqdm meter on screen; receipts and progress.json on disk" -ForegroundColor Yellow',
    'Write-Host ""'
)

$awArgs = @(
    '-B',
    '-m', 'awrag.cli',
    'laptop-temp-intake',
    '--source', $Source,
    '--state-root', $StateRoot,
    '--chunk-mb', [string]$ChunkMb,
    '--max-chunks', [string]$MaxChunks,
    '--workers', $Workers,
    '--reserve-ram-fraction', [string]$ReserveRamFraction,
    '--progress-snapshot-interval-sec', [string]$ProgressSnapshotIntervalSec
)

if ($RunId -ne "") {
    $awArgs += @('--run-id', $RunId)
}

if ($ReserveRamGb -ge 0) {
    $awArgs += @('--reserve-ram-gb', [string]$ReserveRamGb)
}

$pythonCommand = 'python ' + (($awArgs | ForEach-Object { Quote-Arg $_ }) -join ' ')
$commandParts += @(
    $pythonCommand,
    '$exitCode = $LASTEXITCODE',
    'Write-Host ""',
    'Write-Host "AWRAG laptop-temp-intake exit code: $exitCode"',
    'Write-Host "Review run_summary.json, resource_receipt.json, progress.json, and chunk receipts under the run folder."',
    'Read-Host "Press Enter to close this window"',
    'exit $exitCode'
)

$encoded = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes(($commandParts -join "`n")))
Start-Process -FilePath "powershell.exe" -ArgumentList @("-NoExit", "-EncodedCommand", $encoded) -WindowStyle Normal
