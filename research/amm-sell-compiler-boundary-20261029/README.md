# AMM sell: recorded IR-to-machine boundary

The current sell borrow-result test is already `JNE` in the **first captured
machine-code snapshot**, before Finalize ISel. The preceding captured LLVM IR
uses `icmp eq` with equality leading to the successful borrow. This narrows the
candidate's branch-polarity boundary to the interval between those observations;
it does **not** identify an individual instruction-selection operation or explain
the original build. All 116 machine snapshots retain the inequality branch.

An earlier boundary is visible in the same capture: the borrow-success block
first becomes the next IR block after the first recorded **SimplifyCFGPass**.
Before that pass, a forwarding block sits between the borrow block and success.
Success remains adjacent in every subsequent IR snapshot. This is an observed
block-order transition, not a claim that a particular original compiler flag or
source spelling produced the captured deployment.

This packet is a passive compiler observation and two rejected controls. It
changes no maintained Rust source, selected recipe, coverage count or acceptance
gate. The original and selected meaningful ELF remain unequal.

## Inputs and output qualification

- Source revision: `a18e1e89b59bf9d734955550c92f321c97c95e62`. The 68 maintained
  inputs and mapped 69-file workspace are byte-bound in `source-binding.json`
  and retained in `sources.json.gz`, including Git blob identities. These inputs
  are unchanged at this packet's base `e476d5ad1d1b762f3a8a4e681711752e96cc609d`.
- Host: Windows, official v1.44 platform tools, Linux target libraries, MSVC
  14.44 toolchain and Windows SDK 10.0.26100.0. Exact absolute commands,
  environment and the recorded cargo/rustc/native-linker hashes are retained.
  Dependencies are locked and compiled offline from the existing vendor tree.
- One empty-target Cargo build recorded 215 rustc invocations and no `Fresh`
  lines. Four subsequent root recompiles **reuse those dependencies**; they are
  not four additional fresh builds. Total: 219 compiler invocations.
  The earlier four-stage trace records its copy operation and retained source
  hashes, but did not record a pre-launch source inventory; the full-pass trace
  does record that inventory and an unchanged-source check.
- The baseline is the default-linker-layout, unmodified compiler output
  `65a7df192ae10e25cef9789cf28b40ed1b21e2c7c6ef46446ced47355056189c`.
  It has **784 normalized / 398 raw** windows. Its 9,024-byte sell body has the
  same normalized bytes and relocation pattern as the selected layout artifact.
  The selected recipe already has **784 raw** windows: 398 is not a gain over it.
- The full trace appends only `-print-before-all`, `-print-after-all` and the
  sell function filter. Its **complete output bytes equal the baseline**. Both
  passive traces and the ATA control share that exact output. `runs.json` maps
  them to one deduplicated compressed file; decompression restores the compiler
  bytes without any normalization or allocation suffix.

The trace is 34,543,427 raw bytes, SHA-256
`22aa2d8d7801d33cccf667018e0d2f4a2e7aaf49dc1827d2130bf995111d4895`.
Gzip is storage only. Raw log line endings are preserved. All five runs retain
three existing frame-overwrite diagnostics; a zero compiler exit is not runtime
or safety acceptance.

## What the snapshots establish

`analysis.json` contains replayed byte offsets/hashes for all 392 dumps and the
relevant blocks. Snapshot numbers are zero-based and local to this capture.

| Observation | Recorded predicate / tail |
| --- | --- |
| 16: before first SimplifyCFGPass | Borrow block 337, next block 341 (forwarding), success block 342; select/switch predicate |
| 17: after first SimplifyCFGPass | Borrow block 335, next/success block 338; direct equality branch |
| 275: after Module Verifier, last captured LLVM IR | `%227 = icmp eq i64 %226, -9223372036854775782`; `br i1 %227, label %232, label %236` |
| 276: before Finalize ISel, first captured machine code | `JNE_rr %18:gpr, killed %191:gpr, %bb.26`; `JMP %bb.25` |
| Machine successor identities | `bb.25` is IR block 232 (success); `bb.26` is IR block 236 (ProgramError conversion) |
| Before / after branch-folder | 87 / 85 blocks; the final error-return block loses its inline `r6` reload |
| Before / after block-placement | 84 / 82 blocks; the final return block jumps to `bb.62`, which contains the shared `r6` reload |

At sell-relative `0xd00`, the captured original literally contains
`1d32010000000000 0500c90000000000` (JEQ then JA); the candidate contains
`5d32c90000000000` (JNE). The verifier checks these original bytes, the candidate
bytes, the actual-successor identities in the first machine snapshot and the
last IR predicate. It also handles slot-index-prefixed machine block headers.
All 276 IR dumps are parsed: the first 17 have non-adjacent success, and the
remaining 259 have adjacent success. The original bytes are not compiler IR and
do not tell us whether that same transition occurred in the original build.

The late cleanup-tail transformation and the earlier polarity boundary are
distinct observations. Neither licenses rewriting emitted instructions, treating
branch-masked similarity as equality, or attributing historical compiler flags.

## Retained unsuccessful controls

| Root recompile | Result | Disposition |
| --- | --- | --- |
| `-branch-fold-placement=false` | `862362dd08f79a88d2ba082f7b0b63e9c291ddc0e92f409774111071650e9d3d`; 684 normalized / 223 raw; sell 9,056 bytes | Loses exactly 100 normalized and 175 raw windows with no gains; rejected |
| `if ata.data_is_empty()` becomes `if !ata.data_is_empty() { } else` with the same body and line count | Complete ELF byte-identical to baseline | No effect; rejected as an explanation |

These controls are included to prevent repeated work. The distinct Ok-first
borrow-result source control from PR #717 is prior upstream work, not a new
result here. Likewise, the 77-block correspondence in
[`amm-sell-control-flow-boundary`](../amm-sell-control-flow-boundary/README.md)
and checked-constructor / returned-key recoveries predate this packet.

## Saved verification and reproduction limits

From the repository root, with Python 3.12 or newer and the original plus selected
AMM artifacts present:

```sh
python -I -B research/amm-sell-compiler-boundary-20261029/verify.py
python -I -B research/amm-sell-compiler-boundary-20261029/test_analyze.py
```

The stdlib verifier authenticates the complete packet, source archives and Git
blobs, command deltas, complete ELF identities, raw logs, all 116 machine
predicates, late-tail changes, exact normalized/raw match sets and rejected
control losses. It recomputes the parser results and compares `analysis.json`.
It never invokes rustc, a VM, the target, network access or a transaction.

`controllers/` archives the scripts used for the recorded compilations. They
retain their original local workspace dependencies and are **not a portable
one-command build entry point**. Full compilation requires those separately
provisioned SDK/sysroot/vendor/native inputs; launch records and source archives
make the recorded invocation inspectable. The saved check does not establish
that an independent fresh build has occurred on another machine.

Next useful work is a qualified earlier-lowering or block-order hypothesis with
the current source. Preserve failed evidence and compare complete compiler
outputs and exact match membership. Unique original source/compiler provenance,
full meaningful ELF equality, the separately allocated zero suffix and broad
behavior/security claims remain outside these results.
