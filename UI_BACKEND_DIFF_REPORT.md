# UI / Backend Diff Report

Scope: report-only comparison of `HTML UI/awrag-intake-exfil-mockup.html` against the current AWRAG backend in `src/awrag`.

No implementation patch is included. No engine behavior, symbol behavior, count behavior, citation authority, external service, model call, old Clearbox store, or chat chain was added.

Core law:

```text
Frontend displays.
Backend bridge translates.
AWRAG decides.
```

## Backend Inventory

Current AWRAG exposes these real backend functions:

| Backend capability | Source | Existing fields / artifacts |
|---|---|---|
| Create dataset scope | `src/awrag/engine.py::ensure_dataset` | `dataset_manifest.json`, folders, empty count files, empty lexicon |
| Intake source data | `src/awrag/engine.py::intake` | lexicon, binary counts, blocks, coordinates, citations, receipt |
| Dataset status | `src/awrag/engine.py::status` | count paths, record counts, citation count, scope, no persistent memory |
| Query evidence | `src/awrag/engine.py::query` | question anchors, neighbors, answer packet, final answer, output receipt |
| Binary count write/read | `write_binary_counts`, `iter_anchor_records`, `iter_relation_records`, `read_block_anchor_rows` | `.awbin` records |
| Source blocks | `write_blocks_jsonl`, `read_blocks` | `state/blocks.jsonl` |
| Dataset lexicon | `write_lexicon`, `read_symbol_to_anchor` | `state/dataset_lexicon.json` |
| Citations | `write_citation_jsonl` | `citations/citations.jsonl` |
| Coordinates | `write_coordinate_index` | `coordinates/coordinate_index.jsonl` |
| Evidence qualification | `qualify_evidence`, `qualify_candidate` | qualification summary and receipts inside query output |
| Deterministic answer shaping | `src/awrag/nlp_resolver.py::resolve_answer` | cited final answer from locked evidence packet |
| Protected notice | `protected_notice`, `with_protected_notice` | copyright, watermark, facsimile warning |

Current CLI commands:

```text
awrag init
awrag intake
awrag status
awrag query
```

## Classification Legend

| Classification | Meaning |
|---|---|
| `BACKEND_EXISTS` | Backend already provides exact data/action. |
| `BACKEND_EXISTS_WITH_RENAME` | Backend has it, but UI label/name differs. |
| `BRIDGE_NEEDED` | Backend has raw data, but bridge must assemble/display it. |
| `NEW_BACKEND_NEEDED` | UI shows behavior/data current backend cannot provide. |
| `MOCKUP_ONLY` | Visual placeholder; not wired in this release. |
| `REMOVE_FROM_UI` | UI implies behavior we do not want. |

## Diff Table

| # | UI label | Intended meaning | Backend source | Backend field/artifact | Mode | Receipt | Safe demo | Classification | Recommended action |
|---:|---|---|---|---|---|---|---|---|---|
| 1 | Deterministic Evidence Interrogation | Page identity and evidence boundary | `protected_notice`, docs | watermark/facsimile fields | read-only | no | yes | BACKEND_EXISTS | Display from backend notice, not hardcoded long-term. |
| 2 | CSS-only tab navigation | Switch visual panels | none | none | read-only | no | yes | MOCKUP_ONLY | Keep as UI-only navigation. |
| 3 | Chat + Evidence Tool Lane | Chat-like evidence query surface | none | none | mixed | future | partial | NEW_BACKEND_NEEDED | Needs bounded chat backend if retained. |
| 4 | AWRAG Tool Use / query | Query selected dataset | `query` | query result JSON | read-only action | output receipt exists | yes | BACKEND_EXISTS_WITH_RENAME | Route to `query`; call it evidence query, not model chat. |
| 5 | Allowed Sources | Shows query source boundaries | `query`, guardrails | lexicon, counts, coordinates, citations | read-only | no | yes | BACKEND_EXISTS | Display from manifest/status. |
| 6 | Blocked external search / invented citations | Shows authority boundary | guardrails, tests, resolver | `model_may_search=false`, citation source | read-only | no | yes | BACKEND_EXISTS | Display as policy card. |
| 7 | AWRAG cited answer | Display cited deterministic answer | `query`, `resolve_answer` | `final_answer`, `answer_packet` | read-only | query output receipt | yes | BACKEND_EXISTS | Render answer packet and final answer. |
| 8 | Chat draft field | User message entry | none | none | mutating later | future | partial | MOCKUP_ONLY | Keep disabled until chat backend exists. |
| 9 | Request Query | Run dataset query | `query` | `output_path`, `answer_packet` | mutating output file | yes | yes | BACKEND_EXISTS | `ui_action_bridge.query_dataset`. |
| 10 | View Evidence Packet | Inspect answer packet | `query` | `answer_packet` | read-only | no | yes | BACKEND_EXISTS | Read query output JSON by id/path. |
| 11 | Finalize Chat As Counted Source | Store chat as counted dataset source | none | none | mutating | required | no current support | NEW_BACKEND_NEEDED | Do not wire until chat storage/finalize spec exists. |
| 12 | Dataset Intake | Intake selected source | `intake` | intake receipt | mutating | yes | yes | BACKEND_EXISTS_WITH_RENAME | Route to `intake`; label as source intake. |
| 13 | Selected Source | Source path shown to operator | `intake` | `source`, `sources[].path` | read-only input/request | no | yes | BACKEND_EXISTS_WITH_RENAME | Bridge validates path before calling backend. |
| 14 | Selected Dataset | Dataset id | `safe_id`, `dataset_paths` | `dataset_id` | read-only/input | no | yes | BACKEND_EXISTS | Use backend-safe dataset id. |
| 15 | Files | Source file count | `intake` | `source_file_count` | read-only | intake receipt | yes | BACKEND_EXISTS | Display from receipt. |
| 16 | Blocks | Paragraph/block count | `intake`, `status` | `block_count` | read-only | intake receipt | yes | BACKEND_EXISTS | Display from receipt/status. |
| 17 | Coverage locked | Pre-intake coverage gate | none | none | read-only gate | future | not current | NEW_BACKEND_NEEDED | Do not imply active gate until backend supports dry coverage. |
| 18 | Request Add Source | Create/open dataset source context | `ensure_dataset` | dataset root/status | mutating dataset shell | status output | yes | BACKEND_EXISTS_WITH_RENAME | Use as init/open dataset, not file copy. |
| 19 | Request Dry Inspection | Read/extract/compare without writing | none | none | read-only action | no | no current support | NEW_BACKEND_NEEDED | Add later only if approved. |
| 20 | Run Intake After Review | Intake behind UI gate | `intake` plus missing gate absent | receipt | mutating | yes | partial | BRIDGE_NEEDED | Bridge can call intake, but review gate is not real yet. |
| 21 | Raw Source Preview | Display source/blocks before mapping | post-intake `blocks.jsonl` only | `state/blocks.jsonl` | read-only | no | partial | NEW_BACKEND_NEEDED | Existing backend can show post-intake blocks; dry pre-intake preview needs new support. |
| 22 | Unique Anchor List | Show unique anchors before approval | post-intake lexicon only | `dataset_lexicon.json` | read-only | no | partial | NEW_BACKEND_NEEDED | Current backend creates lexicon during intake; pre-intake list needs new read-only function. |
| 23 | Missing Anchor Review | Coverage misses requiring review | none | none | mutating review | required | not current | NEW_BACKEND_NEEDED | Keep disabled; current backend has no separate coverage model. |
| 24 | Request Approval Packet | Operator approval request | none | none | mutating request | required | not current | NEW_BACKEND_NEEDED | Do not implement until coverage/approval spec is approved. |
| 25 | Request Rejection Packet | Operator rejection request | none | none | mutating request | required | not current | NEW_BACKEND_NEEDED | Same as approval packet. |
| 26 | Proceed When Coverage Complete | Coverage completion gate | none | none | gate | future | not current | NEW_BACKEND_NEEDED | Remove active look until coverage backend exists. |
| 27 | Lexicon Viewer / Search | Search dataset lexicon | `read_symbol_to_anchor`, lexicon file | `state/dataset_lexicon.json` | read-only | no | yes | BRIDGE_NEEDED | Add read bridge search over lexicon JSON. |
| 28 | Search anchor/symbol/citation/block/source path | Multi-field search | lexicon, blocks, citations, coordinates | JSON/JSONL files | read-only | no | yes | BRIDGE_NEEDED | Bridge joins raw artifacts for display. |
| 29 | All Dataset Anchors / Observed filters | Filter lexicon rows | lexicon file | `anchors[]`, `observations` | read-only | no | yes | BRIDGE_NEEDED | Bridge filters rows. |
| 30 | Structural filter | Show structural anchor class | none | none | read-only | no | not current | NEW_BACKEND_NEEDED | Remove or define backend field later. |
| 31 | Source Bound filter | Show anchors with source occurrences | block postings + blocks | `.awbin`, `blocks.jsonl` | read-only | no | yes | BRIDGE_NEEDED | Bridge resolves symbol postings to source blocks. |
| 32 | With Citations filter | Show anchors linked to citations | blocks, citations | `citations.jsonl` | read-only | no | yes | BRIDGE_NEEDED | Bridge groups citation refs. |
| 33 | No User Edits filter | Policy indicator | none | none | read-only | no | yes | MOCKUP_ONLY | Keep as visual lock, not backend query. |
| 34 | Browse By Leading Character | Letter browse | lexicon file | `anchors[].anchor` | read-only | no | yes | BRIDGE_NEEDED | Bridge supports prefix query. |
| 35 | Dataset anchor stats | Lexicon/count summary | `status`, lexicon, count files | `anchor_count`, observations | read-only | no | yes | BRIDGE_NEEDED | Status has record counts; bridge sums display totals. |
| 36 | Selected Anchor Detail | One anchor detail card | lexicon/count files | anchor row, count record | read-only | no | yes | BRIDGE_NEEDED | Bridge resolves anchor or symbol. |
| 37 | Anchor text | Anchor display | `write_lexicon` output | `anchors[].anchor` | read-only | no | yes | BACKEND_EXISTS | Display as-is from lexicon. |
| 38 | Symbol | Symbol display | `symbol_for`, lexicon | `anchors[].symbol` | read-only | no | yes | BACKEND_EXISTS | Display existing public demo symbol. |
| 39 | Observation count | Count for anchor | lexicon/count files | `observations` | read-only | no | yes | BACKEND_EXISTS | Display stored count. |
| 40 | Source scope | Dataset scope | manifest/lexicon/status | `scope` | read-only | no | yes | BACKEND_EXISTS | Display scope. |
| 41 | Open Citations | Show citations for selected anchor | citations + blocks + postings | `citations.jsonl`, `.awbin` | read-only | no | yes | BRIDGE_NEEDED | Bridge maps anchor symbol to blocks and citations. |
| 42 | Show 6-1-6 Context | Show nearby relation/position context | relation counts + postings | `relation_counts.awbin`, `block_anchor_postings.awbin` | read-only | no | yes | BRIDGE_NEEDED | Bridge assembles display window without new ranking. |
| 43 | Edit Disabled Forever | UI policy lock | none | none | read-only | no | yes | MOCKUP_ONLY | Keep as explicit surface policy. |
| 44 | Search Result Cards | Result display cards | lexicon/status/count artifacts | joined display object | read-only | no | yes | BRIDGE_NEEDED | Bridge formats lexicon rows. |
| 45 | Distribution | Letter distribution chart | lexicon file | anchors grouped by leading char | read-only | no | yes | BRIDGE_NEEDED | Bridge groups counts; no engine change. |
| 46 | 6-1-6 Map Viewer | Inspect occurrence window | postings + blocks | `.awbin`, `blocks.jsonl` | read-only | no | yes | BRIDGE_NEEDED | Bridge reconstructs occurrence windows. |
| 47 | Previous Occurrence | Navigate occurrence list | postings | block/position rows | read-only | no | yes | BRIDGE_NEEDED | Bridge paginates occurrence rows. |
| 48 | Next Occurrence | Navigate occurrence list | postings | block/position rows | read-only | no | yes | BRIDGE_NEEDED | Same as previous. |
| 49 | Open Citation | Open citation for occurrence | citations/coordinates | citation marker/id | read-only | no | yes | BRIDGE_NEEDED | Bridge lookup by citation id. |
| 50 | Counts Lattice stats | Count file summary | `status` | anchor/relation/posting/citation counts | read-only | no | yes | BACKEND_EXISTS | Display from status. |
| 51 | Count Backend Status | Backend count format | constants/status/manifest | `awrag_native_binary_counts@1` | read-only | no | yes | BACKEND_EXISTS | Display from status/manifest. |
| 52 | Evidence Mode | Coordinate-cited deterministic status | query/guardrails | answer packet/citations | read-only | no | yes | BACKEND_EXISTS | Display as policy/status. |
| 53 | Graph Exfil | Export graph forms | none | none | mutating export | required | not current | NEW_BACKEND_NEEDED | Not in first bridge patch unless approved. |
| 54 | Request Neo4j Exfil | Export Neo4j CSV | none | none | mutating export | required | not current | NEW_BACKEND_NEEDED | Future graph exporter. |
| 55 | Request GraphML Exfil | Export GraphML | none | none | mutating export | required | not current | NEW_BACKEND_NEEDED | Future graph exporter. |
| 56 | View Exfil Receipt | Inspect export receipt | none | none | read-only after export | yes | not current | NEW_BACKEND_NEEDED | Needs exfil backend first. |
| 57 | Dataset Removal + Symbol Return | Remove dataset and return symbols | none | none | destructive | required | not current | NEW_BACKEND_NEEDED | Future, high-risk, not first patch. |
| 58 | Returned symbols file | Reuse returned symbols next ingest | none | `state/symbols_returned.awbin` mock only | mutating ledger | required | not current | NEW_BACKEND_NEEDED | Requires approved symbol ledger spec. |
| 59 | Removal receipt | Audit removal/digestion | none | mock `receipts/removal_*.json` | mutating receipt | yes | not current | NEW_BACKEND_NEEDED | Future deletion workflow. |
| 60 | Next ingest reuse returned symbols | Reassignment rule | none | none | symbol behavior | yes | not current | NEW_BACKEND_NEEDED | Do not touch current symbol behavior in first bridge. |
| 61 | Preview Removal | Show delete impact | none | none | read-only/destructive preview | required | not current | NEW_BACKEND_NEEDED | Future only. |
| 62 | Request Dataset Removal | Remove dataset | none | none | destructive | required | not current | NEW_BACKEND_NEEDED | Remove from active UI until backend exists. |
| 63 | System Ledger | Install-local symbol ledger | none | none | read-only/mutating backend | required | not current | NEW_BACKEND_NEEDED | Future symbol ledger module, not bridge-only. |
| 64 | Install ID | Machine install identifier | none | none | read-only | no | not current | NEW_BACKEND_NEEDED | Future system state. |
| 65 | Last Out | Last distributed symbol | none | none | read-only | no | not current | NEW_BACKEND_NEEDED | Future ledger state. |
| 66 | Next To Assign | Next symbol pointer | none | none | read-only | no | not current | NEW_BACKEND_NEEDED | Future ledger state. |
| 67 | Returned Waiting | Returned symbol count | none | none | read-only | no | not current | NEW_BACKEND_NEEDED | Future ledger state. |
| 68 | Backend module contract / intake | Surface lists backend intake | `intake` | receipt | read-only | no | yes | BACKEND_EXISTS | Keep as docs/status. |
| 69 | Backend module contract / lexicon approval | Approval packet module | none | none | mutating request | required | not current | NEW_BACKEND_NEEDED | Future only. |
| 70 | Backend module contract / ledger | Ledger module | none | none | mutating backend | required | not current | NEW_BACKEND_NEEDED | Future only. |
| 71 | Backend module contract / maps | Map records display | existing raw files | postings/relations/blocks | read-only | no | yes | BRIDGE_NEEDED | Read bridge can expose maps. |
| 72 | Backend module contract / chat | Counted chat finalization | none | none | mutating | required | not current | NEW_BACKEND_NEEDED | Future only. |
| 73 | Miss Diagnosis | Explain rejected/low evidence | `qualify_evidence`, `qualify_candidate` | `qualification`, `qualification_receipts`, `rejected_locations` | read-only | query receipt | yes | BRIDGE_NEEDED | Bridge formats existing evidence receipts. |
| 74 | Citation Cards | Citation display cards | citations + query locations | `citations.jsonl`, `answer_packet.locations` | read-only | no | yes | BRIDGE_NEEDED | Bridge formats citation lookup. |
| 75 | Coordinate Cards | Coordinate display cards | coordinate index + blocks | `coordinate_index.jsonl`, `blocks.jsonl` | read-only | no | yes | BRIDGE_NEEDED | Bridge formats coordinate lookup. |
| 76 | Dataset Manifest | Manifest inspection | `ensure_dataset` | `dataset_manifest.json` | read-only | no | yes | BACKEND_EXISTS | Read bridge can expose manifest. |
| 77 | Dataset-local Lexicon | Lexicon inspection | `write_lexicon` | `state/dataset_lexicon.json` | read-only | no | yes | BACKEND_EXISTS | Read bridge can expose/search it. |
| 78 | Dataset Scope / Memory Boundary | Show no persistent memory | `status`, manifest | `persistent_memory=false`, `scope` | read-only | no | yes | BACKEND_EXISTS | Display from status/manifest. |
| 79 | Symbol System Status | Dataset symbol namespace display | constants/manifest/lexicon | `symbol_system`, `symbol_bytes`, symbol flags | read-only | no | yes | BACKEND_EXISTS | Display from manifest/lexicon. |
| 80 | Watermark / Facsimile Notice | Protected notice display | `protected_notice` | watermark fields | read-only | no | yes | BACKEND_EXISTS | Display on all generated backend payloads. |
| 81 | Theme Controls | Appearance switching | none in mockup/backend | none | UI-only | no | yes | MOCKUP_ONLY | Keep out of first bridge; pure UI later if desired. |
| 82 | Old Clearbox mutation controls | Assign, clear, return, rewrite from old page | old copied HTML only | none in AWRAG | mutating | high risk | no | REMOVE_FROM_UI | Do not bring old edit/assign/clear controls into AWRAG. |
| 83 | Frontend evidence decisions | Any browser-side truth/ranking/citation decision | none | none | forbidden | no | no | REMOVE_FROM_UI | Keep out permanently. |
| 84 | Frontend symbol assignment | Browser assigns/returns symbols | none | none | forbidden | required | no | REMOVE_FROM_UI | Backend only, future approved ledger only. |

## Summary Counts

| Classification | Count |
|---|---:|
| BACKEND_EXISTS | 22 |
| BACKEND_EXISTS_WITH_RENAME | 4 |
| BRIDGE_NEEDED | 21 |
| NEW_BACKEND_NEEDED | 29 |
| MOCKUP_ONLY | 5 |
| REMOVE_FROM_UI | 3 |
| Total UI items found | 84 |

## Safest Bridge Slice

The smallest safe patch is read-only:

```text
ui_read_bridge
  status
  manifest
  lexicon search
  anchor detail
  citation lookup
  coordinate lookup
  evidence packet display
  count backend status
  symbol system status
  miss diagnosis display from existing query fields
```

Do not start with chat, approval packets, graph exfil, dataset removal, symbol return, or dry inspection. Those require new backend behavior and receipts.
