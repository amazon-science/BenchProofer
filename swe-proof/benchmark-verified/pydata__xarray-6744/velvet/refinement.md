# refinement.md — pydata__xarray-6744

The operation-by-operation correspondence between `Solution.lean`'s `impl`
regions (the `blockEnds` / `blockBegins` `do` blocks, plus the `pure`-region
deep model `endShift` / `endAt` / `beginAt`) and `patch.diff` (the gold patch).
Each step is tagged **R** (type refinement; the bijection is stated), **A**
(axiomatized callee — split into **A-consumed**, the proof uses the axiom's
`ensures`, and **A-reference**, a deep model validated == the real operation by
`axiom_check.py` / G-AX), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

The change is a single function that builds the per-position index ranges of a
one-dimensional moving-window traversal. The patch replaces how the two
half-open-range arrays (the block START and END index arrays) are computed; the
rest of the function (the underlying slicing, the per-window masking, and the
emission of each labelled window) is unchanged. The two index arrays are
modelled as two methods, `blockEnds` and `blockBegins` (SPEC_GUIDE §3: one
modeled function per site for more differential witnesses), sharing one frozen
`pure` region.

## A. The block-end array — `blockEnds` ↔ gold END index array

| # | Solution.lean impl op (`blockEnds`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `n : Nat` (`positions n` has length `n`) | the dimension size of the rolling axis (= the count of position labels) | R | a dimension size; `Nat` ↔ the integer size (mapping.md §1,§2). |
| A2 | param `w : Int` with `require w > 0` | the integer window size | R | window size; positivity is the constructor invariant (mapping.md §1). |
| A3 | param `center : Bool` | the per-axis centred flag | R | a plain boolean (mapping.md §2). |
| A4 | `endShift w center` (= `(w+1)/2` if center else `1`) | the `offset` local (post-patch: `(window0+1)//2 if center else 1`) | A-reference + I | identical integer formula; the deep model `endShift` IS the patch's offset. Validated == the real operation by `axiom_check.py` (mapping.md §3.1). |
| A5 | build `[endAt 0 .., …, endAt (n-1) ..]` (the loop, `endAt i = i + endShift`) | the END array `arange(offset, n + offset)`, so `END[i] = offset + i` | R | an ascending integer range ↔ the `List Int` `[a, a+1, …]`; element-wise equal (mapping.md §2). |

`blockEnds`' frozen postcondition `out = endsSeq w center (positions n)` (with
`endsSeq` mapping each position `i` to `endAt i w center = i + endShift w center`)
pins each end to the centre-aware shift. The pre-image END array uses shift `1`
always; `Solution_prepatch.lean` reproduces that (`p + 1`, ignoring `center`)
and **fails** `prove_correct` — the residual goal `p + 1 = endAt p w center` is
unprovable when `center` is true and `endShift = (w+1)/2 ≠ 1` (G-DIFF). The spec
senses that the centred shift `ceil(w/2)` is required.

## B. The block-start array — `blockBegins` ↔ gold START index array

| # | Solution.lean impl op (`blockBegins`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | `endShift w center` (reused) | `offset` (same local) | A-reference + I | as A4. |
| B2 | `raw := endAt p w center - w` per position (= `endAt i - w`) | the START array `END - window0` (so `START[i] = END[i] - window0`) | R + I | element-wise integer subtraction (mapping.md §2). |
| B3 | `if raw > 0 then raw else 0` (clamp to 0) | the leading slice-assign `START[: window0 - offset] = 0` | I (algebraically) | the leading slice-assign equals `max(0, ·)` on every entry: for `i ≥ window0 - offset` the value is already `≥ 0`; for `i < window0 - offset` it is `< 0` and set to `0`. So both equal `max(0, endAt i - w) = beginAt i` (mapping.md §3.2). |

`blockBegins`' frozen postcondition `out = beginsSeq w center (positions n)`
pins each start to the clamped centre-aware value. `Solution_prepatch.lean`
reproduces shift `1` (`(p + 1) - w`, ignoring `center`) and **fails**
`prove_correct` for the same reason as site A (G-DIFF).

## C. The unchanged tail (no model obligation)
The slicing of the underlying sequence by each `[start, stop)` range, the
per-window count mask, and the emission of each labelled window are **unchanged**
by the patch. They are the caller that consumes the index ranges; the model
specifies only the ranges. (The gold also renames a local and widens a return
type annotation; both are behaviour-preserving and carry no model node.)

## D. No kind-3 (unexpressible-changed-op) steps; no consumed axioms
Every step above is R, A-reference, or I. The one operation that *changed* — the
index arithmetic producing the START/END arrays — is modelled **deeply** (the
integer helpers `endShift` / `endAt` / `beginAt` and the verified backward
folds), not hidden behind an axiom. There is **no `axiom`** in this bundle (the
`axioms` region is empty): the changed operation calls no library function whose
behaviour the proof must assume. The deep model is validated **== the real
changed operation** by `axiom_check.py` / G-AX (the lone A-reference). The
fold helpers (`endsSeq` / `beginsSeq` / their `*_drop_step` lemmas /
`positions`) are verified Lean defs and lemmas, not axioms.

## E. verify(Solution) ⇒ resolved
`blockEnds` / `blockBegins` verify only if each produced index equals the
centre-aware closed form (`endAt` / `beginAt`, A4/A5/B1–B3). By R (an ascending
integer range ↔ `List Int`, subtraction / leading-zero-clamp ↔ the same integer
arithmetic) the verified arrays equal the gold patch's START/END arrays
element-by-element, and by G-AX the deep model equals the real operation on the
boundary sweep + 200 000 fuzz cases. Feeding those exact ranges to the unchanged
slicing/masking/emission tail (site C) reproduces the centre-justified manual
iteration the issue demands and the FAIL_TO_PASS `test_rolling_iter[...-True-...]`
cases assert (manual iteration == the vectorised centred mean). Therefore a
model satisfying this spec, refined by the map above, is the gold patch up to
type refinement and the audited A-reference — and the gold patch resolves
(G-RESOLVE). The trust points reduce to A-reference fidelity (G-AX) and
refinement fidelity (this document + G-CONF, G-EQ); there is no consumed axiom
to trust.
