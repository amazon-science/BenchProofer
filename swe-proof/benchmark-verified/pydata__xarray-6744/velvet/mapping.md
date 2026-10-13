# mapping.md — pydata__xarray-6744

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 7cc6cc991e586a6158bb656b8001234ccda25407`, states the type
abstraction, and records the provenance of the deep model.

Repo file under change: `xarray/core/rolling.py`.
Changed function: the one-dimensional moving-window traversal of a
`DataArray`-backed rolling object (`xarray/core/rolling.py`, the iteration that
builds the per-position START/END index arrays).

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file @ base_commit) | role |
|---|---|---|
| `blockEnds n w center` | the END index array built by the traversal | the per-position window END indices (one site of the changed function) |
| `blockBegins n w center` | the START index array built by the traversal | the per-position window START indices (the other site of the changed function) |
| `endShift w center` | the `offset` local of the patched traversal (`(window0+1)//2 if center else 1`) | pure spec: forward shift of every block end |
| `endAt i w center` | `END[i]` of the patched traversal (`END = arange(offset, n + offset)`, so `END[i] = offset + i`) | pure spec: end index of position i |
| `beginAt i w center` | `START[i]` of the patched traversal (`START = END - window0` then leading clamp, i.e. `max(0, offset + i - window0)`) | pure spec: start index of position i |
| `endsSeq / beginsSeq` | (proof scaffolding) the in-order sequence of the above over a list of positions | front-recursive folds materializing the index arrays for the loop invariant |
| `positions n` | the position labels `0 .. n-1` of the rolling axis | the ordered positions the traversal walks |

Inputs of the modeled functions ↔ repo quantities inside the traversal:
- `n` ↔ the size of the rolling dimension (the count of position labels; equal
  pre- and post-patch).
- `w` ↔ the integer 1-d window size (the constructor enforces `w > 0`).
- `center` ↔ the per-dimension centred flag for this 1-d rolling (a `Bool`).

The values `start_i, stop_i` produced by the model are precisely the bounds of
the half-open slice `[start, stop)` the traversal hands to the underlying
sequence slicing. That slicing, the per-window count masking, and the emission
of each labelled window are the UNCHANGED tail of the function: the patch alters
only how the START/END arrays are computed, so the model specifies exactly those
two arrays and treats the rest as the unchanged caller.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| the integer index arrays (START, END) | `List Int` of the same integer values in the same order | `arr[i]` ↔ `out[i]`; `len(arr)` ↔ `out.length`; integer subtraction / leading-zero-clamp ↔ the same integer arithmetic on `Int` |
| `offset` (an integer) | `Int` | identity |
| the integer window size | `Int` `w` with `w > 0` | identity (window positivity is a constructor invariant) |
| the centred flag | `Bool` `center` | identity |
| the dimension size | `Nat` `n` | identity (a count `≥ 0`) |

No string or float modeling is involved: the changed operation is integer index
arithmetic, modeled exactly. An ascending integer range `[a, a+1, …, a+n-1]` is
the `List Int` `(List.range n).map (a + ·)`; the gold patch's
`END = arange(offset, n + offset)` therefore has `END[i] = offset + i = endAt i`.
`START = END - window0` then the leading clamp yields
`START[i] = max(0, offset + i - window0) = beginAt i` (see §3 for the clamp
algebra).

## 3. Provenance of the deep model (A-reference — checked by G-AX / axiom_check.py)

There are **no axiomatized library callees** (the `axioms` region is empty): the
operation the patch changes is the index computation itself, modeled deeply. The
deep model is validated **== the real changed operation** (the patch's
START/END arrays) by `axiom_check.py` (G-AX), as an A-reference.

### 3.1 `endShift` ↔ the patch's `offset`
The patched traversal computes `offset = (window0 + 1)//2 if center else 1`,
then `END = arange(offset, n + offset)`, `START = END - window0`, with a leading
clamp of the first `window0 - offset` entries to `0`. `endShift w center`
returns `(w + 1)/2` when centred and `1` otherwise — byte-for-byte the patch's
`offset`. `(w + 1)/2 == ceil(w/2)` for `w > 0`; for `w = 1` it is `1`, collapsing
centred to non-centred, matching the patch.

### 3.2 the clamp algebra `beginAt i == max(0, endAt i - w)`
The patch sets `START = END - window0` then clamps `START[: window0 - offset]`
to `0`. For `i ≥ window0 - offset`: `START[i] = offset + i - window0 ≥ 0`, so the
clamp leaves it unchanged. For `i < window0 - offset`: `offset + i - window0 < 0`,
and the slice assigns `0`. Hence `START[i] = max(0, offset + i - window0) =
max(0, endAt i - w) = beginAt i`. The pre-image code clamps the first `window0`
entries (not `window0 - offset`) but with `offset == 1` always, so both its shift
and its leading clamp differ from the centred case.

### 3.3 the soundness witness (the FAIL_TO_PASS discriminator)
For the issue's example `n = 9, w = 3, center = True`: `offset = 2`,
`endAt 1 = 3`, `beginAt 1 = 0`, so position 1's block is `[0, 3)` (values
1,2,3, mean 2.0) — the centre-justified result `[nan, 2, 3, …]`. The pre-image
rule (`offset = 1` always) gives position 1's block `[0, 2)` (values 1,2, masked
by `min_periods`), the buggy `[nan, nan, 2, …]`. `axiom_check.py` reproduces the
gold patch's `arange`/subtract/slice-assign arithmetic with plain ints and
asserts `endAt`/`beginAt` equal it on the boundary sweep (sizes 0..21,
windows 1..21, both centred flags) plus 200 000 randomized `(n, w, center)` fuzz
cases, plus the worked example. `conformance_check.py` additionally runs the real
patched traversal on constructed sequences and recovers each window's
`[start, stop)` range, comparing it to the model's `(beginAt, endAt)`. Exit 0 iff
sound.

## 4. Flag dependencies & fuzz seeds
None. The computation depends only on `w > 0`, `n ≥ 0`, and the `center`
boolean; there is no library call whose default flags matter. The deterministic
fuzz seeds are `axiom_check.py` 20220702 and `conformance_check.py` 6744.

## 5. Mathlib imports
Only `Velvet.Std` (the front door) plus the `List` lemmas it re-exports
(`List.drop_eq_getElem_cons`, `List.length_map`, `List.length_range`,
`List.getElem!_eq_getElem?_getD`, `List.getElem?_eq_getElem`). No extra
`Mathlib.*` subdirectory is required.
