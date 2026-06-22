# TrueVision Engineering Roadmap

Status: roadmap document only.

This directory is tracked, but it is not part of AWRAG runtime.

This document is based on the supplied TrueVision headless-effects input.

No implementation is approved by this document.

## Boundary

```text
TrueVision engineering != AWRAG backend
TrueVision engineering != AWRAG retrieval
TrueVision engineering != AWRAG count engine
TrueVision engineering != AWRAG evidence authority
```

TrueVision may later connect to AWRAG and SecureCore through explicit contracts, but it does not live inside AWRAG.

## Current Truth

The current decision is:

```text
do not make Codex hand-build effects one by one
do not bring in outside AI as authority
do use existing open-source visual/video engines as headless tool bodies
do let TrueVision / AW / SecureCore control them through maps, contracts, and receipts
```

Codex's role:

```text
tool-builder
contract-writer
receipt-writer
test-builder
operator helper
```

Codex is not:

```text
media authority
visual truth source
final effects designer
silent renderer
unreceipted automation layer
```

## Core Law

```text
No outside AI authority.
Open-source libraries are allowed as tools.
TrueVision remains the witness/planner.
SecureCore approves tools.
AnchorWorks records/explains/cites.
Receipts prove what happened.
```

## Correct Flow

Target future shape:

```text
TrueVision observes/logs state
-> detects effect behavior
-> maps behavior to available headless tools/libraries
-> writes a render/effect packet
-> SecureCore approves tool use
-> headless tool executes one declared action
-> receipt returns
```

Rejected shape:

```text
Codex writes a custom video every time
```

## Roadmap Item

Name:

```text
TrueVision Headless Effects Toolchain
```

Purpose:

```text
reuse existing open-source video/vision/compositing libraries as headless tools
observe visual effects
extract behavior variables
map variables to tool contracts
execute only approved declared actions later
receipt everything
```

This is future roadmap work.

No implementation yet.

## Candidate Tool Bodies

Candidate libraries / engines from the supplied source:

```text
FFmpeg
OpenCV
Blender headless
Natron / OpenFX
MLT / Flowblade-style stack
Kornia / PyTorch vision ops
RAFT-class optical flow / segmentation tools
```

### FFmpeg

Possible role:

```text
headless video/audio encode
filter graphs
transforms
basic compositing
```

### OpenCV

Possible role:

```text
frame analysis
tracking
masks
optical flow
image transforms
cross-platform visual operations
```

### Blender Headless

Possible role:

```text
headless render engine
camera work
3D scenes
particles
lighting
procedural scenes
```

### Natron / OpenFX

Possible role:

```text
node-based compositing
OpenFX plugin world
2D visual effects/compositing
```

### MLT / Flowblade-Style Stack

Possible role:

```text
timeline operations
editing backend
effects backend
```

### Kornia / PyTorch Vision Ops

Possible role:

```text
tensor/image operations
GPU-friendly differentiable vision tools later
```

### RAFT-Class Optical Flow / Segmentation Tools

Possible role:

```text
motion fields
object movement
fog/occlusion behavior
depth-ish motion cues
state extraction
```

## First Phase: Tool Survey And Action Map

First pass is a survey and map, not implementation.

For each candidate tool body, create:

```text
action_map.json
help_map.json
tool_contracts.json
receipt examples
```

Each map should answer:

```text
what can this tool do?
what inputs does it accept?
what outputs does it produce?
what files can it touch?
what failures can happen?
what receipt proves the action?
```

## One-Action Tool Contracts

Initial one-action tools to define:

```text
extract_frames
compute_optical_flow
segment_motion
detect_occlusion
apply_fog_transform
composite_layer
render_packet_to_video
encode_video
```

Each one-action tool must declare:

```text
tool_name
tool_body
inputs
outputs
mutation_rights
file_paths_touched
required_binaries_or_packages
failure_modes
receipt_fields
approval_required
```

Rules:

```text
one tool call = one declared action
no hidden multi-step work
no unapproved file mutation
no authority transfer to the tool body
```

## Effect Observation Pipeline

For the "find effects from videos/movies" idea:

```text
effect observation
-> effect signature
-> variable extraction
-> reusable effect tool contract
```

This is how TrueVision learns effect behavior without hand-building every effect.

## Example: Fog

Observation:

```text
object enters fog and visibility drops over distance/time
```

Signature:

```text
occlusion increases
contrast decreases
edges soften
saturation shifts
depth/motion relation changes
```

Variables:

```text
fog_density
distance_decay
time_decay
edge_softening
color_shift
visibility_threshold
```

Future tool contract:

```text
apply_fog_transform(packet)
```

Meaning:

```text
see the fog
extract the variables
make the fog through an approved headless tool
receipt the action
```

## SecureCore Approval Boundary

SecureCore approval is required before a headless tool executes.

Approval should check:

```text
tool is registered
action is declared
input files are allowed
output paths are allowed
mutation rights are explicit
resource use is bounded
receipt schema is known
operator approval exists when required
```

No tool should execute because a model, prompt, or media file suggests it.

## Receipt Requirements

Every future tool action must return a receipt.

Minimum receipt fields:

```text
receipt_id
tool_name
tool_body
action
input_paths
output_paths
input_hashes
output_hashes
parameters
started_at
completed_at
exit_status
failure_mode
operator_approval_id
securecore_approval_id
```

## Output Separation Law

TrueVision follows the same separation now being used by AWRAG report tools:

```text
evidence_trace/
pretty_report/
receipts/
```

Evidence trace contains:

```text
observed state
effect signatures
variables
coordinates
frame references
tool packet
raw tool output references
```

Pretty report contains:

```text
human-readable summary
selected frame references
effect explanation
links to receipts
```

Receipts contain:

```text
what ran
what tool was used
what files were touched
what changed
what did not change
who/what approved
hashes before and after
```

## Future Build Order

Do this later, after the roadmap is reviewed:

```text
1. Create candidate tool inventory.
2. Draft action_map.json for FFmpeg, OpenCV, Blender headless, Natron/OpenFX, and MLT.
3. Draft first five tool contracts.
4. Draft receipt schema.
5. Review before implementing.
6. Implement one harmless read-only probe.
7. Implement one bounded frame extraction action.
8. Implement one deterministic analysis action.
9. Implement one render/effect packet action only after approval.
```

Do not start with video generation.

Start with maps, contracts, and receipts.

## Non-Goals

Not now:

```text
no custom video hand-builds
no outside AI authority
no model-owned visual truth
no AWRAG backend changes
no SecureCore bypass
no hidden tool execution
no framework beyond this document
no implementation before review
```

## Next TrueVision Session Prompt

Use this as the next-session target:

```text
Before more video generation, build the TrueVision Headless Effects Toolchain roadmap.

Goal:
Reuse existing open-source video/vision/compositing libraries as headless tools.
Do not bring in outside AI authority.
Do not hand-code one-off videos.
Build action maps and SecureCore tool contracts so TrueVision can observe effects,
extract behavior variables, and call the correct rendering/effect tools later.

Output:
- candidate library list
- action/tool map
- first 5 tool contracts
- receipt schema
- no implementation until reviewed
```

## Reference Notes From Source Input

The supplied input referenced:

```text
OpenCV as cross-platform computer vision tooling.
Natron/OpenFX as open-source node compositing / plugin-standard tooling.
RAFT-style optical flow as motion/state extraction tooling.
```

These are reference notes only.

They do not create authority.

## Generated Companion Roadmap

The next-session prompt has been expanded into:

```text
truevision_engineering/TRUEVISION_HEADLESS_EFFECTS_TOOLCHAIN_ROADMAP.md
```

This companion remains roadmap-only. It does not implement or wire tools.