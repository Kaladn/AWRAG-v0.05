# Laptop Temp Intake

Purpose: prepare and verify bounded chunks on laptop hardware without writing the production dataset count spine.

This is a disposable proof path, not production ingest.

## Command

```powershell
python -B -m awrag.cli laptop-temp-intake `
  --source <file-or-folder> `
  --state-root State/laptop_temp_intake `
  --run-id proof_001 `
  --chunk-mb 25 `
  --max-chunks 3
```

## What It Does

For each bounded chunk:

- writes `chunk_000001.raw`
- assigns symbols first for raw text chunks
- writes `chunk_000001.symbols.bin`
- writes `chunk_000001.lexicon_delta.json`
- writes `chunk_000001.counts.bin`
- writes `chunk_000001.receipt.json`

It also writes:

- `manifest.json`
- `source_receipt.json`
- `chunk_receipts.jsonl`
- `run_summary.json`

## Hard Boundaries

- No production merge.
- No lifetime memory write.
- No production `awrag intake` backend replacement.
- No full dataset load.
- No global count spine build.
- No main `State` mutation except the requested temp run folder.

## Laptop Defaults

Use `--chunk-mb 25` or `--chunk-mb 50`.

Use `--max-chunks 3` for the first proof.

Review `run_summary.json` and per-chunk receipts before deciding whether the path earns a production merge stage later.

## Resume Behavior

Resume is enabled by default.

When a run is repeated with the same `--run-id`, each chunk is checked for a complete verified receipt before processing.

A chunk is skipped only when all required artifacts exist and are non-empty:

- raw chunk
- symbolized chunk
- lexicon delta
- count artifact
- chunk receipt

If verification fails, that chunk is processed again.

## Future Main-Machine Merge Shape

Merge is intentionally not implemented in this laptop lane.

A later main-machine merge tool would need to:

1. read verified chunk receipts only
2. verify count artifact headers and symbol system
3. merge chunk-local anchor counts into a new production dataset scope
4. merge relation counts in bounded batches
5. build production coordinate/citation indexes from accepted source chunks
6. write a merge receipt with before/after artifact sizes
7. refuse merge if any chunk receipt fails verification

Until that exists, `laptop-temp-intake` remains a preparation/proof lane only.