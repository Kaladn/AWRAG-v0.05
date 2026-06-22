# TrueVision Headless Effects Toolchain Roadmap

Status: roadmap only. No implementation, no tool execution, no AWRAG wiring.

Source prompt: `TRUEVISION_ENGINEERING_ROADMAP.md` / `Next TrueVision Session Prompt`.

## Purpose

TrueVision should use proven open-source video, vision, compositing, and media libraries as headless tool bodies.

TrueVision does not become an outside AI authority and Codex does not become the media artist.

The target shape is:

```text
observe effect
-> extract behavior variables
-> create reusable tool contract
-> call approved headless tool later
-> render or analyze from packet
-> write receipt
```

## Core Laws

```text
TrueVision witnesses state.
TrueVision logs state.
TrueVision may plan replay.
TrueVision may call approved headless tools later.
TrueVision does not create source truth.
TrueVision does not replace AnchorWorks.
SecureCore approves tool use.
Receipts prove every tool action.
```

No tool should execute because a model, prompt, or media file suggests it.

No implementation starts from this document.

## Candidate Library List

These are candidate tool bodies, not authorities.

### FFmpeg

Role:

```text
media probing
frame extraction
transcoding
container inspection
audio/video stream metadata
simple filtergraph operations
```

Why it fits:

```text
mature command-line tool
excellent headless behavior
stable input/output contracts
strong metadata/probe surface
```

Risks:

```text
complex filter syntax
large media files can be expensive
must avoid overwrite without explicit output path/receipt
```

### OpenCV

Role:

```text
frame reading
image transforms
feature detection
tracking helpers
basic computer vision analysis
```

Why it fits:

```text
cross-platform
scriptable/headless
useful for deterministic visual measurements
```

Risks:

```text
can become a custom vision framework if boundaries drift
must keep outputs as measurements/candidates, not truth
```

### Blender Headless

Role:

```text
3D scene render
camera/lens replay
procedural scene reconstruction
controlled visual output from packets
```

Why it fits:

```text
powerful headless renderer
strong scene graph model
can render from declared parameters
```

Risks:

```text
large dependency
slow on laptop hardware
creative freedom can exceed evidence packet if not constrained
```

### Natron / OpenFX

Role:

```text
node-based compositing
open effect plugin chains
reproducible effect graphs
```

Why it fits:

```text
open-source compositing lane
OpenFX plugin standard gives reusable effect bodies
node graphs can be serialized and receipted
```

Risks:

```text
availability/install complexity
plugin variation across machines
must receipt exact plugin versions and graph files
```

### MLT

Role:

```text
timeline assembly
cuts/transitions
render pipeline orchestration
```

Why it fits:

```text
headless-friendly multimedia framework
useful for deterministic timeline packets
```

Risks:

```text
less familiar operator surface
must avoid becoming a hidden video editor
```

### RAFT-Style Optical Flow

Role:

```text
motion field extraction
state delta estimation
movement signature candidate generation
```

Why it fits:

```text
captures motion/state changes that static frame analysis misses
```

Risks:

```text
model-backed methods can become outside AI authority
outputs must be labeled candidate measurements
requires explicit approval before any learned model dependency
```

## Action / Tool Map v0

This is a planning map only.

```text
media.probe
  tool_body: FFmpeg / ffprobe
  mutation: none
  output: metadata JSON + receipt

media.extract_frames
  tool_body: FFmpeg
  mutation: writes selected frames to declared output folder
  output: frame files + frame index + receipt

vision.measure_frame
  tool_body: OpenCV
  mutation: none or writes compact measurement JSON
  output: visual measurements + receipt

vision.track_motion
  tool_body: OpenCV or approved optical-flow body
  mutation: writes compact motion field/summary
  output: motion candidates + receipt

compose.apply_effect_graph
  tool_body: Natron/OpenFX or Blender headless
  mutation: writes rendered output from declared packet
  output: rendered media + graph receipt

timeline.render_packet
  tool_body: MLT or FFmpeg
  mutation: writes assembled timeline output
  output: rendered timeline + receipt
```

## First Five Tool Contracts

These are contract drafts. They are not implemented.

### 1. `media.probe`

Purpose:

```text
Read media metadata without changing files.
```

Tool body candidates:

```text
ffprobe
FFmpeg metadata probe
```

Input contract:

```text
input_path
allowed_extensions
max_file_size
probe_fields
```

Output contract:

```text
format
streams
duration
frame_rate
resolution
codec list
audio/video/subtitle stream summary
metadata_hash
receipt_path
```

Mutation boundary:

```text
read-only
```

Approval:

```text
operator approval optional for local trusted file
SecureCore approval required for external/untrusted path
```

### 2. `media.extract_frames`

Purpose:

```text
Extract bounded frame samples for review or measurement.
```

Tool body candidates:

```text
FFmpeg
OpenCV frame reader
```

Input contract:

```text
input_path
output_dir
frame_selection_mode
max_frames
start_time
end_time
frame_interval
```

Output contract:

```text
frame_index.json
selected frame files
source media hash
frame hashes
receipt_path
```

Mutation boundary:

```text
writes only inside declared output_dir
never overwrites unless explicit overwrite=true and receipt says so
```

Approval:

```text
operator confirmation required
SecureCore approval required for overwrite or large extraction
```

### 3. `vision.measure_frame`

Purpose:

```text
Produce deterministic frame measurements from extracted frames.
```

Tool body candidates:

```text
OpenCV
custom deterministic measurement wrapper
```

Input contract:

```text
frame_path
measurement_profile
region_of_interest optional
output_path
```

Output contract:

```text
frame_dimensions
color/statistics summary
edge/feature candidates
region measurements
measurement_profile
receipt_path
```

Mutation boundary:

```text
writes compact JSON report only
source frames unchanged
```

Approval:

```text
operator approval optional for small local frame set
```

### 4. `vision.extract_motion_candidates`

Purpose:

```text
Extract candidate motion/state changes from a bounded frame sequence.
```

Tool body candidates:

```text
OpenCV optical flow
approved RAFT-style optical flow later
```

Input contract:

```text
frame_index
motion_profile
max_frames
output_dir
```

Output contract:

```text
motion_summary.json
motion_vectors or compact field reference
confidence/candidate labels
review_required=true
receipt_path
```

Mutation boundary:

```text
writes only compact candidate reports unless explicit field export approved
```

Approval:

```text
operator confirmation required
SecureCore approval required for learned/model-backed optical flow
```

### 5. `compose.render_effect_packet`

Purpose:

```text
Render a declared effect packet through an approved headless compositor/render body.
```

Tool body candidates:

```text
Blender headless
Natron/OpenFX
FFmpeg filtergraph for simple cases
```

Input contract:

```text
effect_packet.json
source_assets
output_path
render_profile
max_runtime
```

Output contract:

```text
rendered_output
render_log
effect_packet_hash
source_asset_hashes
output_hash
receipt_path
```

Mutation boundary:

```text
writes only declared output_path and receipt/log paths
never modifies source assets
```

Approval:

```text
operator approval required
SecureCore approval required for external assets, overwrite, or long render
```

## Receipt Schema v0

Minimum fields:

```json
{
  "schema": "truevision_tool_receipt@1",
  "receipt_id": "",
  "tool_name": "",
  "tool_body": "",
  "tool_body_version": "",
  "action": "",
  "input_paths": [],
  "output_paths": [],
  "input_hashes": {},
  "output_hashes": {},
  "parameters": {},
  "mutation_boundary": "",
  "operator_approval_id": null,
  "securecore_approval_id": null,
  "started_at": "",
  "completed_at": "",
  "exit_status": "",
  "failure_mode": null,
  "stdout_log": null,
  "stderr_log": null,
  "review_required": true
}
```

Receipt law:

```text
If a tool touches a file, the receipt names it.
If a tool writes a file, the receipt hashes it.
If a tool fails, the receipt says where and why.
If a tool uses a learned/model-backed method, the receipt labels it candidate-only.
```

## Output Folder Shape

Future output should separate evidence, presentation, and receipts:

```text
truevision_runs/<run_id>/
  evidence_trace/
    observed_state.json
    frame_index.json
    measurements.json
    motion_candidates.json
  pretty_report/
    summary.md
    selected_frames.md
  receipts/
    run_receipt.json
    media_probe_receipt.json
    extraction_receipt.json
    measurement_receipt.json
```

## SecureCore Contract Notes

SecureCore should eventually validate:

```text
tool is registered
input path is allowed
output path is declared
mutation boundary matches action
overwrite policy is explicit
runtime/resource limits are set
operator approval exists when needed
receipt path is declared before execution
```

SecureCore should block:

```text
hidden overwrite
source asset mutation
unbounded media extraction
unbounded render
external path without approval
tool execution from corpus/prompt content
model-backed authority claims
```

## What Other Codex Needs To Know

1. This file is a roadmap packet, not an implementation ticket.
2. Do not wire TrueVision into AWRAG runtime.
3. Do not modify AWRAG backend, scoring, citations, counts, symbols, or intake.
4. Do not install libraries from this document without explicit approval.
5. Do not run FFmpeg, OpenCV, Blender, Natron/OpenFX, MLT, or optical-flow tooling from this document yet.
6. Do not let generated video/media become evidence authority.
7. Keep TrueVision in `truevision_engineering/` unless the operator points somewhere else.
8. Keep outputs separated as `evidence_trace/`, `pretty_report/`, and `receipts/`.
9. Treat model-backed optical flow or image understanding as candidate-only unless later approved and receipted.
10. If asked to implement later, start with `media.probe` as a read-only harmless probe.

## Review Gate Before Implementation

Before any implementation starts, review and approve:

```text
candidate library list
action/tool map
first 5 tool contracts
receipt schema
SecureCore validation notes
output folder shape
```

Only after review should the first implementation target be considered:

```text
one harmless read-only media.probe command
```

Do not start with video generation.
