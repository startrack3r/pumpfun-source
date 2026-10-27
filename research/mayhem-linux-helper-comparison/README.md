# Mayhem: Linux v1.54 helper and call-layout comparison

The [retained Linux build](../../repro/mayhem/linux-v154-recovery/README.md) resolves
the two type-ID negatives in the earlier Darwin helper comparison. Under the
**same 118-function method**, entry-bounded/call-consistent matches increase
from **106 to 108**, and raw matches from **18 to 23**. No old raw range is lost.
This packet performs no new build or target execution.

The five added raw ranges have two different explanations:

| Candidate symbol family | Linux candidate offset | Original offset | Bytes | Difference from Darwin |
|---|---:|---:|---:|---|
| core::error::Error::type_id (two symbols) | 441464 / 498600 | 599768 / 666624 | 40 each | Two returned 64-bit constants |
| __udivti3 | 529800 | 697904 | 80 | One relative-call immediate |
| compiler_builtins::int::specialized_div_rem::u128_div_rem | 529880 | 697984 | 5128 | Eleven relative-call immediates |
| compiler_builtins::float::mul::__muldf3 | 535792 | 703896 | 2008 | One relative-call immediate |

The three intrinsic bodies already matched under the older normalization.
Their Linux layout now makes every byte equal, including those call immediates.
This is a raw layout gain, not three newly identified source bodies.

All **13 direct calls** in those three bodies target complete, raw-equal
callee bodies in the capture. They reach four distinct windows: u128 division
at 697984, left shift at 706088, right shift at 706256 and multiplication at
706432. This closes these direct edges; it does not establish arbitrary indirect
calls, data meaning, program behavior or global transitive closure.

## Type-ID ambiguity and boundary evidence

Both Linux candidate type-ID symbols have the same 40-byte body. Each equals
both captured ranges, so all **four pairings remain possible**. The unique-match
count stays **66**. The source names belong to the candidate symbol table; no
original concrete error type is attributed.

The two-LDDW/EXIT bodies contain these literal register values:

| Recipe | R0 | R1 |
|---|---|---|
| Darwin v1.54 | `0xfc2cba3a8bdda727` | `0x09f7c3b95c533b40` |
| Linux v1.54 and both captured bodies | `0xb48b06e23bc32191` | `0x802914a71efcf08e` |

These are decoded instruction constants, not results of target execution.
They should not be relabeled as a recovered historical Rust type.

Neither original type-ID start is a direct-call target. Their actual boundary
evidence is retained rather than inferred from a substring match:

- The type-8 relocation at 728232 points to 599768. Its next inferred entry,
  599808, is called directly.
- The type-8 relocation at 731888 points to 666624. The relocation at 732032
  points to its end, 666664.

These three records are in `.data.rel.ro` and use the stored generic-v0
high-word pointer representation, with zero low words. The independent reader
maps virtual addresses through sections, verifies instruction boundaries,
skips LDDW continuation slots and excludes relocated external calls.
No captured loader relocation overlaps any gained body or its four direct
callee windows. These are inferred boundaries, not original debug symbols.

## Complete comparison and negative evidence

| Same helper method | Darwin | Linux |
|---|---:|---:|
| Selected candidate function groups | 118 | 118 |
| Any instruction/relocation pattern match | 106 | 108 |
| Entry-bounded, mapped-call-consistent matches | 106 | 108 |
| Unique inferred-entry matches | 66 | 66 |
| Entry-bounded raw matches | 18 | 23 |
| Distinct raw original ranges in this cohort | 18 | 23 |
| Bodies without a pattern match | 12 | 10 |

The ten remaining negatives are all retained: eight AccountInfo-array drop
specializations (array lengths 2, 4, 16, 18, 23, 25, 26 and 27), RawVec
`finish_grow` and `grow_one`. This study adds no source fix for them.

[comparison.json.gz](comparison.json.gz) contains both complete function ledgers,
including raw hashes, every match alternative, relocation patterns, bounded
data prefixes, outgoing calls and failures. [findings.json](findings.json) adds
the five gains, exact changed instruction words, explicit pointer records and
complete direct-callee comparisons.

The wrapper uses the pinned earlier `match_helpers.py` definitions, substituting
only the two build paths. It does not run the archived script's writing entrypoint.
Every Darwin function record and summary must reproduce the earlier published
ledger exactly. Report path separators alone are made portable. The helper
selection families and multiplicities must be equal between hosts.

The reference method masks relative-call and actual loader-relocation immediates
**in memory only** for its normalized scores and checks known mapped helper calls.
It does not establish all callees or full data identity. The new raw gains and
their direct callees additionally pass an independent byte/boundary check using
the [shipped-object study's reader](../mayhem-sysroot-object-provenance/README.md).
No executable bytes are rewritten or normalized.

## Provenance and limits

The five gains come from already retained artifacts:

- Linux unstripped ELF:
  `9a3d7ed93fd47670ef48c36cb3540fa6847906c9292fc138f302ca1a1aedf2bd`.
  Explicitly stripped output: 599776 bytes,
  `e59f9f970813102e04327ce0502f8359dd217cfaebec942172614ab84dd6ac88`.
- Darwin unstripped ELF:
  `f9de20e991c9e14e77f2d9cded7da9c2dff892353f06f7c6f00ea18bfa8e911e`.
  Explicitly stripped output: 599784 bytes,
  `ca5d4f54b14e2f67c4eca56fcac29b54801906cecf23c463801916fd9d6b6621`.
- Original capture: 777408 bytes,
  `a87fa9f866272514e6acb852b668c4a08aeb173d56c883039991d114d1199bdb`.

[inputs.json](inputs.json) pins 71 existing inputs to revision
`355dbe06d3c5d9eb16227516bcbe2303d6a80e05` by SHA-256, size and Git blob.
The Linux saved-artifact verifier is rerun: its original 47-member artifact
seal, driver/source/dependency/tool receipts, output binding and comparisons
all pass. The recorded fourteen source/lock hashes equal the Darwin frozen set.
This rechecks retained receipts, not the omitted compiler archives or a fresh
compiler process. Both stripped images remain bound to their symbol images.

This is a comparison of two **complete distribution recipes**, including their
compiler and sysroot. It does not isolate the causal component. In particular,
a standard-library path is evidence about library provenance, not proof of the
machine on which the final program was compiled: the repository's
[Relay cross-host recipe](../../repro/donation-relay/framework-sysroot-recovery/README.md)
already demonstrates a Darwin compiler consuming Linux target libraries.
No analogous Mayhem component-isolation experiment is claimed here.

The Linux whole file remains unequal to the capture: 323297 differing shared
positions and 177632 missing bytes. Its instruction section has 15310 different
positions versus Darwin. The original allocation tail is not added to either
compiler output. v1.54 remains a supported recipe, not a uniquely proved
historical compiler. Selected sources, artifacts, runtime status and the seven
admitted unmatched Mayhem handler windows are unchanged.

## Verify

Python 3.11 or newer; standard library only, offline:

```sh
python research/mayhem-linux-helper-comparison/verify.py
python -I research/mayhem-linux-helper-comparison/verify.py
python research/mayhem-linux-helper-comparison/test_comparison.py
```

`--repo PATH` accepts a relocated tree containing exactly the 71 pinned files.
The checker first validates those files before importing the reused readers.
No original compiler tools, downloads, RPC requests, signing, VM or target
program execution occur. The code adapts existing MIT-licensed repository
analysis; no additional third-party binaries are redistributed.
