# refinement.md — pydata__xarray-6721

The operation-by-operation correspondence between `model.py`'s implementation
(the `get_chunksizes` impl region together with the payload-view callees
`inspect_underlying` / `inspect_materialised`) and `patch.diff` (the gold
patch). Each step is tagged **R** (type refinement), **A** (axiomatized callee —
**A-consumed** = the proof uses the axiom's `Ensures`; **A-reference** = a deep
model validated == the real callee/semantics by `axiom_check.py` / G-AX), or
**I** (identical concrete operation). Claim: *any implementation that verifies
against this frozen spec, refined per the map below, is behaviourally equal to
the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (one line; applies cleanly at
`base_commit`; it is the real correctness oracle, G-RESOLVE).

## The change

Gold hunk (`xarray/core/common.py`, inside `get_chunksizes`):
```
     for v in variables:
-        if hasattr(v.data, "chunks"):
+        if hasattr(v._data, "chunks"):
             for dim, c in v.chunksizes.items():
                 ...
```
The fix inspects the variable's UNDERLYING store (`v._data`) for a block
(`chunks`) structure instead of its MATERIALISED payload (`v.data`). Reading
`v._data` never pulls the payload into memory; reading `v.data` does for a
lazily-backed, non-duck array (`Variable.data` falls through to
`Variable.values` → `np.asarray`).

## Callee modelling and the capability token

The two payload-view reads are unchanged library operations Nagini cannot
express, so they are modelled as `@ContractOnly` callees whose contracts the
proof consumes (**A-consumed**, SPEC_GUIDE §2 "unchanged library/utility callee
→ @ContractOnly axiom"; §3). Their runtime-observable contracts (block status +
forced-load count) are validated against the real `xarray` `Variable` machinery
by `axiom_check.py` (G-AX).

The regression is a SIDE EFFECT (forced materialisation), not a value: on the
F2P regime (`block_backed=False, forces_load=True`) both views answer the same
block status, so there is no value-level discriminator. The discriminator is
therefore carried by an UNFORGEABLE, CONSUMABLE capability predicate
`payload_intact(e)` — an abstract `@ContractOnly @Predicate` (no body; Nagini
rejects any `Fold`, so it can never be fabricated or regained once consumed):

- `inspect_underlying` (the `v._data` view) **requires and returns**
  `payload_intact(e)` — it reads in place, so the entry stays intact.
- `inspect_materialised` (the `v.data` view) **requires but does NOT return**
  `payload_intact(e)` — obtaining the materialised payload pulls it into memory,
  consuming intactness.
- `block_lengths_by_axis` requires `payload_intact` for every entry on entry and
  **re-establishes it for every entry in its postcondition**.

Hence any verifying implementation must keep every entry intact end-to-end,
which is possible only if it never materialises any entry. An implementation
that calls `inspect_materialised` on any entry — even one that ALSO reads the
underlying store for the correct value and writes a literal `0` into the
trailing load slot — permanently loses that entry's token and cannot discharge
the postcondition (machine-confirmed: both call orderings fail). This is what
pins the no-materialisation regression; the trailing `== 0` slot alone is an
echoable constant and does not carry it.

## Operation correspondence

| # | model.py impl op | patch.diff op | tag | justification |
|---|---|---|---|---|
| 1 | parameter `entries: List[Entry]` | `variables: Iterable[Variable]` | R | one `Entry` ↔ one `Variable`; the touched fields are abstracted (mapping.md §"Type abstraction"). |
| 2 | `while i < len(entries): e = entries[i]; ... ; i = i+1` | `for v in variables:` | R | bounded index loop ↔ iterator over the collection, same order, one pass. |
| 3 | `probe = inspect_underlying(e)` | `hasattr(v._data, "chunks")` | A-consumed | the **new** (post-fix) payload view. The callee's `Ensures` give the block status from the underlying store (`e.block_backed`), force `0` loads, and thread the `payload_intact` token through unchanged — exactly as `hasattr(v._data, "chunks")` reads `v._data` in place without materialising. `axiom_check.py` validates the block-status + zero-load contract against the real `Variable._data`/`hasattr` semantics (G-AX). |
| 3' | (`inspect_materialised`, called only by `model_prepatch`) | `hasattr(v.data, "chunks")` (the **pre-fix** line) | A-consumed | the pre-fix view: the callee forces `block_load_cost(e)` loads, reports `e.block_backed and not e.forces_load`, and CONSUMES the `payload_intact` token, mirroring `Variable.data` → `Variable.values` → `np.asarray` materialising a non-duck store (which then advertises no `chunks`). Validated == real semantics by `axiom_check.py`. Present in both files (shared spec); the prepatch calls it, the model does not. |
| 4 | the `payload_intact` token: required in `block_lengths_by_axis`'s pre, threaded by `inspect_underlying`, consumed by `inspect_materialised`, re-required in the post | the regression property: inspecting `chunks` must not load any variable's data | A-consumed | the consumable token makes the materialisation side effect unforgeable; step 3 preserves it, step 3' destroys it. This is the clause the F2P test `test_chunks_does_not_load_data` exercises. (The `loads` integer tally + `Result()[2*len(entries)]==0` is a redundant secondary witness, not the binding regression sensor.) |
| 5 | `if probe[0]: result += [e.axis, e.length] else: result += [-1, -1]` | `if hasattr(...): for dim, c in v.chunksizes.items(): chunks[dim] = c` (skip otherwise) | R | a chunked entry contributes its `(axis, length)` (its `chunksizes` entry, read from the underlying store); a non-chunked entry contributes the empty marker `(-1,-1)`, i.e. nothing — the `dict`/`Frozen` aggregation ↔ the flat pair list (mapping.md). |
| 6 | `return result` (pairs + trailing loads tally) | `return Frozen(chunks)` | R | `Frozen` is identity on content; the trailing tally is a secondary observability instrument, not repo state. |

The `ValueError` on inconsistent chunks (`common.py:2028-2032`) is orthogonal to
the tested regression and to the single-line change; the model carries one axis
per entry and does not re-model the cross-entry inconsistency raise. This does
not weaken the discriminating clause (the load side effect), which is what both
the F2P test and the gold diff turn on.

## No kind-3 steps

Every step is R, A-consumed, or I. The one operation that genuinely changed —
which payload view is inspected — is modelled on both sides as A-consumed
`@ContractOnly` callees (`inspect_underlying` for `v._data`,
`inspect_materialised` for `v.data`), with the distinguishing side effect (a
forced materialisation/load) made explicit and unforgeable in the spec via the
consumable `payload_intact` capability token. `axiom_check.py` (G-AX) validates
their runtime-observable contracts == the real `Variable` payload semantics; the
token is a proof-only construct with no runtime footprint.

## verify(model) ⇒ resolved

`get_chunksizes` verifies only if every entry remains intact end-to-end — no
variable is materialised — and each entry's contribution is read from the
UNDERLYING block status `e.block_backed`. The token obligation makes the
underlying view MANDATORY: the only way to re-establish `payload_intact` for
every entry in the postcondition is to never call `inspect_materialised`. By the
refinement above, the verified impl equals `hasattr(v._data, "chunks") →
aggregate v.chunksizes` over the collection, i.e. the gold patch, up to type
refinement and the A-consumed payload-view callees that G-AX validates against
real `xarray` semantics. The pre-patch skeleton (`inspect_materialised`, the
`v.data` line) consumes the token (and forces a load), so `model_prepatch` fails
verification (G-DIFF). The gold patch resolves (G-RESOLVE). The trust points are
precisely the two of PLAN §1.1: A-consumed axiom soundness (G-AX) and refinement
fidelity (this document, G-EQ).
