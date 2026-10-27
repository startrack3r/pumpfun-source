# Remaining work — artifact-backed Relay worker review, 26 October 2026

This is the action list for the [current reconstruction audit](RECONSTRUCTION-AUDIT.md),
with current research reviewed through evidence revision `ba788351`. The [current review](RECONSTRUCTION-STATUS.md)
and [complete refreshed inventory](../repro/reconstruction-status-2026-10-26/README.md)
list every raw match and unresolved window; selected artifacts retain the
`1463bd22` audit bindings. The historical
[completion ledger](COMPLETION.md) remains a selected-checkpoint record; its old
candidate paths and “current” prose must not override newer evidence.

Subsequent gains are in the [byte-identity progress log](BYTE-IDENTITY-PROGRESS.md):
Relay research now has **492/492 normalized counterparts and no unmatched windows**; current Fees research
has **34 unmatched windows and 404 unique structural pairs**. The [Relay framework study](../repro/donation-relay/framework-sysroot-recovery/README.md)
recovers the three repeated type-ID bodies with official Linux target libraries,
adds the Anchor 0.32 framework matches and restores share-total compared values.
The subsequent [mint-predicate study](../repro/donation-relay/mint-fee-pair-recovery/README.md)
recovers window 106; the preceding remaining windows were 92–95 after the
[Jupiter](../repro/donation-relay/jupiter-option-source-recovery/README.md) and
[burn/close ownership](../repro/donation-relay/burn-mint-ownership-recovery/README.md) recoveries. A
[fully Linux reproduction](../repro/donation-relay/linux-canonical-reproduction/README.md)
previously confirmed the 480-window frontier; the optional-seed study independently
confirms 481 with the full Linux compiler, and the burn/close recovery confirms
482 on both compiler recipes. The baseline counts below remain those
of the dated audit.

The earlier [compiled location recovery](../repro/donation-relay/source-location-recovery/README.md)
subsequently resolves all 43 source-location value differences in the audited
346-pair cohort, retaining 480 matched windows and 12 unmatched on both tested
compiler recipes, each with fresh replay. Other data,
absolute pointers, relocations and excluded/ambiguous functions still need work.

The [optional-seed recovery](../repro/donation-relay/jupiter-option-source-recovery/README.md)
closes Jupiter window 90 on both compiler recipes, taking the current frontier
to 481/492 without losing matches. The prior four instruction differences were
resolved by the optional-slice pointer test and Rust `match` structure. The
original location cohort remains equal and expands from 346 to 348 pairs.
The subsequent [burn/close ownership recovery](../repro/donation-relay/burn-mint-ownership-recovery/README.md)
closes window 109 on both compiler recipes, advancing to 482/492. All 348 location
pairs remain equal. Thirty-six epoch-close variants remain negative. The later
[artifact-backed worker recovery](../repro/donation-relay/shared-worker-artifact-recovery/README.md)
closes window 112 with no loss, reaching 483/492 and leaving nine donation and
settlement business bodies.

The [donation source controls](../repro/donation-relay/donation-source-controls/README.md)
retain 59 unsuccessful builds covering 173 targeted window comparisons. Some
ownership changes remove the already-matched context-drop helper; the recovered
worker preserves that path. The subsequent
[worker-flow audit](../repro/donation-relay/shared-worker-flow-audit/README.md)
confirms that every explicit-return path in both decoded graphs crosses that
helper, including paths after transfer. Linear code offsets do not establish
different ownership boundaries. Five mint-key/whitelist trials add no matches.
No experimental candidate from this study is promoted.
The [32-subset argument study](../repro/donation-relay/partial-argument-controls/README.md)
also excludes partial argument binding alone under the tested recipe (128
unmatched target comparisons). Further wrapper work needs evidence beyond
repeating those subsets, such as tracing the live values passed to the shared
worker and returned event. The subsequent
[conditional caller diagnostic](../repro/donation-relay/wrapper-value-flow/README.md)
finds matching selected boundary/return fields for regular and payer wrappers
under explicit callee and alias assumptions. Preserve that limited scope: it
does not validate actual worker effects, all input aliases or byte identity.

The [epoch-close field/error controls](../repro/donation-relay/epoch-source-controls/README.md)
add fourteen rejected source builds without changing the ten-window residual.
Avoid repeating those cache, conversion and intermediate-Result forms in isolation.
The historical compiler inputs and remaining instruction/value-flow differences
still need investigation. The cached v1.50-compiler/v1.48-library substitution
loses 256 matches without gaining any; do not substitute that rejected output
for the current checkpoint.

The [root-profile/Result controls](../repro/donation-relay/profile-result-controls/README.md)
reject four root compiler overrides without adding a match. Unit-result helpers
can duplicate the already-matched error body but do not recover its callers.
Retain the current opt-level 3 / one-codegen-unit recipe while investigating the
remaining bodies; local helper matches alone do not identify source types.

The [shared-worker arithmetic controls](../repro/donation-relay/arithmetic-order-controls/README.md)
reject the tested in-place arithmetic and tip-local forms. Naming the tip division
alone compiles to the unchanged candidate. The worker still needs a complete
source/body recovery, not promotion of a locally similar trial.

The [swap-caller layout/constructor study](../repro/donation-relay/swap-caller-controls/README.md)
removes an extra copy and passes fresh bounded replay, but does not recover the
full `just_swap` body. Retain the corrected source as a partial experiment while
resolving the remaining argument/Vec handling and instruction differences;
compiler layout of reconstructed types is not original debug information.

The [settlement call ledger](../repro/donation-relay/settlement-call-audit/README.md)
finds matching direct callee-body multiplicities for windows 97, 98 and 100,
and for 99 after the constructor-order correction. Their caller bodies still
differ. Prioritize argument/value flow, inline checks, data references and CFG
comparison rather than assuming absent out-of-line helper calls.

The [optional-account ownership recovery](../research/fees-optional-account-ownership/README.md)
adds the optional account parser and raw-equal cleanup without lost matches.
Keep their real caller wired to owned `AccountInfo`; the larger account parser
still needs full reconstruction. The subsequent [seed-vector recovery](../research/fees-social-seed-vector/README.md)
recovers a 296-byte clone helper; its V2 claim caller remains unmatched. Current
Fees attribution totals 473 pairs. The [extension-size log recovery](../research/fees-extend-size-logs/README.md)
restores the no-resize messages and formatting helper; the larger resize handler
remains unmatched.

The [Relay metadata study](../repro/donation-relay/security-metadata-source-recovery/README.md)
recovers the complete security payload and dynamic string table from ordinary
source. Preserve these results while solving the ten residual instruction
windows and remaining data/layout/relocation differences. The 482-window body
inventory retains its own artifact binding; the new Linux metadata variant is
separately identified in the current analysis.

The [boxed interface-mint recovery](../research/fees-crank-interface-mint/README.md)
recovers one crank parser and removes two structural ambiguities. Preserve the
corrected mint owner/length behavior; the enclosing parser and other crank
logic still need full recovery. Local parser agreement does not prove downstream
transfer support for additional token programs.

The [common quote-predicate recovery](../research/fees-curve-zero-helper/README.md)
adds the complete 504-byte helper and its two panic-location records. Its two
fee-sharing callers still need full recovery. Preserve the Borsh-expression
result; the tested array and `TryFrom` expressions are retained negative controls.

The [slice-origin contract study](../research/fees-slice-origin-contract/README.md)
provided four tier-copy panic location corrections on the older PR #149
candidate. The [current integration](../research/fees-slice-origin-integration/README.md)
now applies them with all intervening gains retained, identical instruction
bytes and exactly eight corrected data bytes. Other data and transitive identity
remain open; these four records no longer need a separate integration step.

The [buyback context recovery](../research/fees-buyback-context-ownership/README.md)
closed the 7,184-byte account parser, 5,512-byte initialization closure and
560-byte exit. The [source-origin follow-up](../research/fees-buyback-context-origin/README.md)
now also closes the 6,256-byte closure at original 358,312, with all 104 direct
callee bodies matching across that set. Preserve both field ownership and the
recovered source coordinates while addressing other residuals and transitive data.

## Crank caller work after event-account recovery

The [owned event-account recovery](../research/fees-crank-event-ownership/README.md)
changes one context field from `UncheckedAccount` to `AccountInfo`, retaining its
seed constraint. This recovers the complete 952-byte crank exit and 840-byte
dispatch wrapper, without losing any match. Both original exit field offsets,
the owner bytes and three error labels agree; all 12 direct exit callees match.
The wrapper still calls the unmatched parser at 408,640 and business handler at
147,944. These two local gains do not close the public handler's full call tree.

The [root codegen controls](../research/fees-wrapper-codegen-controls/README.md)
reproduce the prior candidate exactly at one unit. Two, four, eight and sixteen
units recover no new bodies and lose 127, 133, 163 and 163 covered windows,
respectively. They retain a bump default store but do not recover the buyback
wrapper. Keep the one-unit recipe; the wrapper's original extra initialization
instruction still needs a source/build explanation.

## Sweep work after context recovery

The [sweep context ownership study](../research/fees-sweep-context-ownership/README.md)
boxes the vault and both token accounts, and owns the event/program account
infos. The destination remains borrowed. This recovers the complete 9,280-byte
parser, 944-byte exit and 1,320-byte dispatch wrapper, without losing a match.
All 89 direct parser/exit callees match. The wrapper has five matching direct
callees and one remaining business-body frontier at original 120,816.

The three separate controls add no complete body match. Earlier crank and
initializer bodies, their explicit callee limitations, and retained panic-data
contracts remain unchanged. The new candidate passes fresh full and focused
regressions; source, build and data evidence are retained separately from the
local instruction matches. No selected artifact is promoted.

## Buyback update context after ownership recovery

The [buyback-update ownership study](../research/fees-buyback-update-ownership/README.md)
owns the event authority and program account infos in the shared update context.
It recovers the complete 5,856-byte parser, 1,744-byte authority-update wrapper
and 1,568-byte claim-rate wrapper. All 61 direct callee bodies match; single-field
ownership controls add no complete body. No prior match is lost.

Twenty-five selected message, seed, label and owner-ID ranges also match, with a
mutation test distinguishing their identity from instruction equality. Nested
panic/format metadata, wider transitive data and exhaustive behavior still need
separate proof. Fresh full and focused regression passes; earlier sweep, crank,
initializer and panic-location contracts remain verified.

## Artifact-backed Relay worker recovery

The [shared-worker artifact packet](../repro/donation-relay/shared-worker-artifact-recovery/README.md)
independently builds the published 56-file source map with the official Linux
v1.48 SDK. The fresh baseline reproduces the prior full-Linux artifacts exactly;
the recovered build reaches 483/492, gains only worker 112, loses no normalized
or raw match and binds all 51 direct callees. A fresh 536-record / 534-unique
replay passes.

The worker packet established the 483-window checkpoint. The later
[settlement artifact recovery](../repro/donation-relay/settlement-artifact-recovery/README.md)
independently validates the combined 488-window source and exact read-only data.
The later wrapper artifact recovers original ordinals 92–95. Continue with
raw call/address values, relocations, broader behavior and transitive data.
Whole-file equality and selected-source promotion remain unachieved.

## Event contexts after isolated ownership trials

The [six ownership trials](../research/fees-event-context-ownership/README.md)
recover two bodies each for social claim, withdrawal and social-PDA creation.
Their combined source retains all six gains and every parent match. All 168
parser callees match; the three dispatch wrappers still call unmatched business
bodies. The original instruction-message bytes are checked separately.

The fee-sharing V2 trial loses two normalized bodies and one raw-local match;
its borrowed event field is retained. Admin-reset and fee-sharing-creation
trials add no complete body and are not integrated. Do not apply a blanket
conversion to every unchecked event account. Fresh combined-candidate full and
focused regressions pass, and earlier context/data contracts remain verified.

## FeeConfig initialization after prefix recovery

The [unchecked-prefix recovery](../research/fees-unchecked-prefix-recovery/README.md)
restores full-account input handling for the research decoder. It consumes the
eight-byte prefix, without checking its value in the unchecked path, and invokes
the existing payload decoder. The complete 1,144-byte helper now matches, all
11 direct callee bodies match, and the incoming initializer closure and payload
decoder remain matched. Owner constants and the decoder error-message record
are verified independently of instruction normalization.

The parent fails the added native prefix regression; the corrected source passes
35 host contract cases, including short buffers and format thresholds. The local
slice control restores the prefix but leaves 22 stack-operand differences and
does not consume the caller's descriptor. The consuming variant is retained.
The 17,331-case SBF regression passes but does not invoke `initialize_fee_config`.
These tests do not establish a successful authorized fixed-admin initializer
transaction. Older packets' discriminator-free unchecked-input limitation is
resolved for this current research candidate, not rewritten in those packets.

## Current priorities and closure criteria

The [complete review](../repro/reconstruction-status-2026-10-26/review.md)
classifies every named handler and reports unresolved text size for every build.
The following are independent requirements; completing one does not close the others.

| Priority | Remaining work | Evidence required to close it |
| --- | --- | --- |
| Current research bodies | Relay raw call/address and relocation differences; Fees' 34 windows, including the exotic-growth caller | Full original-window comparison with no lost matches, source/build hashes and relevant fresh differential coverage |
| Core source/behavior | Pump's five partial and three unaccepted handlers; AMM initializer; Mayhem initializer and opaque attribution | Concrete source, genuine successful and rejected paths, bound receipts and per-handler limitations |
| Known mismatches | Pump sell_v2 transfer-fee behavior; Mayhem diagnostics and field contracts | Authorized resumed correction where required, then targeted regressions and broader validation |
| Transitive binary identity | Calls, duplicate attribution, data, relocations, indirect calls and final ELF layout | Exact artifact comparison and explicit explanation of any allocation padding |
| Provenance and integration | Historical tools/dependencies, ATA recipe, selected-source promotion of research | Reproducible source/tool manifests, new selected artifacts and guard-approved bindings |

Body-count percentages understate large unresolved functions: Fees' residual
is 31.1% of original text; Relay's is 2.3%. Neither value measures remaining
engineering time. Preserve the documented negative experiments and stopped lanes.

## Historical immutable audit baseline

- **Whole captured-file identity:** 0/4 selected core programs; selected Relay also differs.
- **Selected public handlers:** 140/150 bounded implementations, five partial,
  five unaccepted/unrecovered. No exhaustive semantic-perfection claim.
- **Selected machine windows:** 384 have equal local body bytes, 1,408 additional
  normalized-only matches, 1,301 have no full body match and 245 remain opaque.
  This partitions 3,338 windows, not the amount of source or effort recovered.
- **Newer Fees research:** 340 unique structural pairs plus 53 call-attributed
  duplicate pairs; 94 duplicate windows still unattributed and 98 unmatched.
- **Newer Relay research:** 465/492 normalized windows, including 86 raw local
  matches, with 27 unmatched. Selected source 15 remains at 122/492.
- **Dependencies:** SPL Token is fully raw-byte equal. Token-2022's raw ELF equals
  the meaningful prefix and its separately padded allocation equals the capture.
  ATA has two exact but non-historical research recipes; its selected status is
  still unresolved. Metaplex has 1,509 differing positions.

Use the [complete handler ledger](../repro/reconstruction-audit-2026-10-26/handlers.md),
[exact-byte appendix](../repro/reconstruction-audit-2026-10-26/raw-body-matches.md)
and [full window inventory](../repro/reconstruction-audit-2026-10-26/functions.tsv)
for function-level details. “No complete match” does not prove source absence;
“raw local match” does not prove transitive semantics.

## 1. Close public-handler and behavior gaps

| Work item | Current evidence | Completion condition |
| --- | --- | --- |
| Pump `admin_update_token_incentives` | Unselected overlay; 299 bounded comparisons | New selected build, bound receipts and broader validation |
| Pump `claim_token_incentives` | Recovered overlay source; older build-bound differential | Rebind and replay the actual intended candidate |
| Pump `set_mayhem_virtual_params` | Static recovery and 84 signer-stub comparisons | Resolve genuine caller and AccountInfo ownership contracts; select/revalidate |
| Pump `buy_v3`, `sell_v3`, `buy_exact_quote_in_v3` | Partial selected handlers; overlay adds finite transfer-fee coverage | Cover remaining routes, extensions, validation ordering and complete event data |
| Pump `create_v2` | Partial selected handler; overlay adds real Mayhem CPI coverage | Broader ancestry, modes and Token-2022 interactions |
| Pump `multi_hop_curve_swap` | Finite one/two/three-hop ordinary coverage | Arbitrary supported depth, quote currencies, lifecycle, resizing and mode combinations |
| AMM `create_config` | Compiled/static structural evidence | Authentic successful fixed-admin initialization and rejection validation |
| Mayhem `initialize_mayhem_state` | Corrected overlay: 53 rejection cases ([initializer correction](../research/mayhem-initializer-validation/README.md)) and 20 real Pump-CPI cases ([retained recheck](../research/mayhem-overlay-cpi-recheck/README.md)) | Select intended source/build and cover broader initializer behavior |
| Pump `sell_v2` | Bounded accepted handler with a known quote transfer-fee minimum-output/event discrepancy | Correct and validate after explicit resumption; the corrective runtime probe remains stopped ([retained scope](COMPLETION.md)) |
| Mayhem non-initializer ABI/state | Bounded handlers, known diagnostic/error differences, five unknown GlobalParams field roles | Resolve fields and full error/data contracts |

The selected 140 count includes finite, imperfect reconstructions. It must not be
presented as 140 fully correct or byte-perfect functions. Existing stopped-lane
and signing/ownership restrictions are unchanged by this documentation audit.

## 2. Finish source and binary reconstruction

| Program / research | Concrete remaining frontier |
| --- | --- |
| Selected Pump | 507 windows without full normalized matches; calls/data and ambiguous matches also remain. The separate workspace-member build has 538 normalized windows and 497 residuals: 233 different-body, 192 no-same-size, 72 store-immediate-only heuristic rows. One of those 72 changes an error code; only 71 are reported origin-only. |
| Selected AMM | 297 unmatched original windows, 160 ambiguous normalized rows, original diagnostics, data and full call contracts |
| Fees current research | 34 unmatched windows (206,360 original body bytes), 69 additional call-attributed pairs and 78 duplicate windows still unattributed; close shareholder validators, transitive calls/data and full ELF/relocation layout |
| Selected Mayhem | Seven admitted unmatched windows and 257 source-ledger opaque windows; 12 of the opaque windows have local raw matches without semantic attribution |
| Relay current research | all 492 normalized windows now matched, with 317 raw-local matches; 18,623 meaningful-ELF positions still differ. Resolve raw linking, relocations, indirect/data semantics, privileged successes and allocator/borrow behavior |
| Metaplex | Utilize's 1,477 text differences, 30 source-coordinate differences, two relocation differences; authentic source/compiler layout |
| ATA | Historical recipe remains unknown despite exact output from explicit symbol ordering and an empty feature. Decide selection independently of historical authenticity. |
| All programs | Exact historical tool/dependency inputs, complete sections/relocations, data and indirect-call meaning; complete security and lifecycle acceptance |

The historical counts in the audit-baseline section are not the current research frontier.
The Fees and Relay research outputs are not selected production/source checkpoints.
The [audit](RECONSTRUCTION-AUDIT.md) records their full hashes, scope and exact
function-level evidence. Do not combine counts from different builds or matcher
rules into a single recovery percentage.

## 3. Integrate deliberately

The behavioral overlay and generated Relay source cannot be promoted by copying
files alone. Selection entails a new candidate, source/build manifests, exact
artifact hashes, bound differentials, current status/selection records and an
explicit guard transition. The current guard pins 37 Pump and 14 Mayhem compile
inputs; selected Relay uses its source-15 binding. This audit changes none of them.

README changes use the reviewed consolidation transition: its exact transition
hash and allowed paths live in `repro/consolidation/2026-10-26/guard.py`. Changing
a selected script set or immutable checkpoint package needs a separate reviewed
change, not a data-only reseal.

Historical SDK tests used older overlay artifacts. Repeat those flows against
any candidate actually proposed for selection. Preserve failed experiments and
finite-coverage limitations. A passing differential suite is not security sign-off.

## Evidence and reproducibility

The audit generator rechecks all selected input hashes, binary extents and body
bytes, preserves complete original partitions, and provides current candidate
bindings for every handler. Run:

```sh
python3 -B repro/reconstruction-audit-2026-10-26/audit.py --check
```

No source compilation or target-program execution is performed by that command.
This is a dated evidence snapshot, not a live PR queue or monitoring promise.
There is no defensible single overall percent complete or completion date.

## Consolidation record

| Source | Outcome |
| --- | --- |
| Primary checkout's uncommitted recovery work | Snapshotted as `1bec3365`, merged as `repro/behavioral-recovery/` |
| `codex/layered-reconstruction` | Merged: MIT `LICENSE`; its program edits went to the overlay |
| `review/reconstruction-2026-10-25` | Merged: nine A-reproduction build records |
| `codex/relay-generated-framework-20261025` @ `9f49231c` | Squashed in: all 15 evidence packages and the complete generated-framework source (its 50 Rust/Cargo inputs, byte-identical, in `repro/donation-relay/distribution-worker-source-recovery/settlement/source/`); PR #94 restored three predecessor packages its verifiers need. Only promotion to the active `programs/donation-relay` path is pending (§3) |
| Pull requests #32–#59 (except #34, closed as superseded by #38) | Merged by the parallel PR agent; included. PR #60, opened before the consolidation PR #61, merged just after it |
| Go-clone `codex/checkout-byte-preservation-transition` | Superseded by PR #32, which contains both commits plus the fix that kept the sealed attributes |
| Go-clone `research/pr8-harness-bindings-superseded` (`89634a4d`) | Not merged: self-labelled superseded, targets pass-22 bindings and edits two pinned scripts |
| Scratch worktrees `fees-edit`, `restruct-wt` | Removed after a byte-for-byte match against the banked restructure trees |
| Codex worktree `main-reconciliation` (`codex/layered-pass-36`) | Clean and contained in main; left for its owner |

## Fees configuration follow-up

The [configuration-event recovery](../research/fees-config-event-recovery/README.md)
now matches the normal/stable configuration updates and both tier upsert callers.
Removing an unnecessary event clone and reading the stored configuration admin
reproduce their original bodies. The account declarations retain `has_one = admin`.
Both duplicate-shaped upsert bodies are independently identified by their outgoing
callees; the global incoming-call refinement agrees. Fresh 17,331-case and
1,542-case exact replays pass.

The [exotic growth correction](../research/fees-exotic-growth-precedence/README.md)
now reproduces error precedence on 24 new boundary cases, with existing broad
and exact-matrix passes retained. The caller at 88552 remains unmatched despite
one same-sized trial. Continue with its account-info lifetime, source structure
and generated account/dispatch wrappers; do not equate equal byte lengths with
identity. The remaining count stays 68. Referenced data and full transitive
identity remain unproven even where caller and direct callee bodies match.

## Mayhem history follow-up

[PR #148's captured history](../research/mayhem-globalparams-field-history/README.md)
provides new value trajectories for the five unnamed fields. The independent
[wire verification](../research/mayhem-history-wire/README.md) now reproduces the
retained table from 13 raw transaction captures, including ten paired update/event
payloads and both current accounts. The original checker invokes that decoder.
This closes the retained-cohort decoding gap, not RPC authentication or complete
lifetime history. The unrelated fee-recipient log remains explicitly truncated.
Field names, units and consumer semantics still need independent attribution.
This does not resume any stopped Mayhem initializer or other execution lane.


## Mayhem shipped-library provenance

The [v1.54 sysroot object check](../research/mayhem-sysroot-object-provenance/README.md)
binds ten distinct raw capture ranges to complete functions in the official
Darwin arm64 generic-v0 libcore/compiler-builtins objects and the retained linked
Mayhem build. Eight already occur in the earlier helper audit; two conversion
bodies add matches to that bounded table. The full publisher archive digest and
all 354 retained ELF member associations rechecked locally. Sixteen symbol labels
collapse to ten ranges; 270 eligible no-hit symbols and 1,067 excluded symbols
remain recorded. This narrows shipped-library provenance, without proving a
unique historical compiler, whole-program byte identity or behavioral coverage.


## Relay donation caller construction follow-up

The [488-window cleanup controls](../repro/donation-relay/donation-close-order-controls/README.md)
show that constructing the native event after closing the temporary account
restores the missing cleanup call but leaves original windows 92/93 unmatched
(6,232 versus 6,272 bytes). A borrowed-key `DonationArgs` constructor gives the
same complete output. Windows 94/95 remain 2,552 versus 2,568 bytes. Preserve the
accepted candidate: this is evidence narrowing source hypotheses, not a new
recovered function. Compare the remaining argument/context construction and
stack use with whole-window matching still required; runtime cleanup and failure
paths need separate coverage before promoting any later candidate.


The follow-up [Result/event construction controls](../repro/donation-relay/donation-result-shape-controls/README.md)
also fail complete-window matching. The eight-byte size gap in the explicit-match
regular wrapper does not establish that only one instruction needs changing;
registers, stack slots and ordering still differ throughout the body. Further
work must explain those source/code-generation differences, preserving full
window comparison and testing runtime behavior before promotion.


The [verified Fees composition](../research/fees-composed-frontier188/README.md)
closes six more complete windows over the #188 baseline, including social-PDA
creation and two sharing dispatches. Both dispatches retain unmatched business
callees. Continue from the now-pinned 551/585 normalized candidate; do not assume
older query/log matrices were rerun against it. Whole-file and runtime acceptance
remain distinct from normalized body recovery.


## Relay normalized bodies complete; raw identity remains open

[Independent wrapper builds and replay](../repro/donation-relay/donation-wrapper-artifact-recovery/README.md)
close the four previously unmatched donation windows. Prior rejected controls and
four-window lists are historical evidence. Next compare the 18,623 meaningful-ELF
byte differences, keeping address/call relocation changes distinct from source
semantics. Do not pad the candidate with the captured allocation tail or treat
492/492 normalized coverage as byte-identical completion.


The [independent Mayhem history re-decode](../research/mayhem-globalparams-field-history/REDECODE.md)
now corroborates all 13 retained transactions and the raw old/new version chain.
The follow-up fixes package-relative paths and includes negative decoder tests.
This closes the request for another decoder implementation, while RPC provenance
and semantic field-role attribution remain separate open requirements.


## Mayhem retained Linux helper comparison

The [Linux/Darwin helper comparison](../research/mayhem-linux-helper-comparison/README.md)
applies the same 118-helper method to both retained v1.54 outputs. Linux resolves
two type-ID negatives, increasing normalized matches from 106 to 108 and raw
matches from 18 to 23 with no lost raw range. Both type-ID symbols match both
40-byte capture ranges; the unique-match count remains 66. Three intrinsic
bodies gain raw equality solely through call layout, and all 13 direct edges
reach complete raw-equal callee bodies. Ten helper negatives remain. These are
static observations of existing artifacts, not a new compiler build or evidence
of complete program identity; component causality and historical host remain
unproved. No selected artifact or stopped execution lane changes.
