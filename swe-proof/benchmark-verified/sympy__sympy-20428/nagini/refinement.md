# refinement.md — sympy__sympy-20428

The operation-by-operation correspondence between `model.py`'s implementation
(the `coeff_truthy` impl, the `strip_constant_len` impl, and the deep `mzero`
facet of `Coeff`) and `patch.diff` (the gold patch). Each step is tagged
**R** (type refinement), **A** (axiomatized/deep callee — split into
**A-consumed**, where the proof uses a `@ContractOnly` axiom's `Ensures`, and
**A-reference**, where a deep model is validated == the real callee by
axiom_check.py / G-AX), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The changed site — `Expression.__bool__` (`expressiondomain.py:122-123`)

Gold hunk:
```
  def __bool__(f):
-     return f.ex != 0
+     return not f.ex.is_zero
```

| # | model.py impl op (`coeff_truthy`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `c: Coeff` (fields `lit0`, `mzero`) | `f` (an `ExpressionDomain.Expression` wrapping the SymPy expr `f.ex`) | R | `Coeff.lit0 == 1` ↔ `f.ex == Integer(0)` (structural); `Coeff.mzero == 1` ↔ `f.ex.is_zero is True` (mathematical). See mapping.md §2. |
| A2 | `return c.mzero == 0` | `return not f.ex.is_zero` | A-reference | the changed operation is modeled **deeply**: `mzero` is the explicit mathematical-zero facet, and `coeff_truthy(c) == (c.mzero == 0)` is exactly `not f.ex.is_zero`. There is no consumed `is_zero` axiom — the proof never depends on a `@ContractOnly`. The deep facet is validated **== the real `Expr.is_zero`** out-of-band: G-AX (axiom_check.py) builds real `EX` coefficients and asserts `bool(coeff) == (not coeff.ex.is_zero)` over bare-zero, non-zero, and denoting-zero-but-structurally-non-trivial expressions (mapping.md §3.1). |

The discriminating content of the change — truthiness keyed on the
**mathematical** value `f.ex.is_zero` rather than the **structural** inequality
`f.ex != 0` — lives in `coeff_truthy`'s postcondition
`Result() == (c.mzero == 0)` (model) ⇔ `not f.ex.is_zero` (real). The pre-patch
`f.ex != 0` is the structural test; `model_prepatch.py` reproduces it
(`return c.lit0 == 0`) and **fails** the postcondition `Result() == (c.mzero == 0)`
on the state `lit0 == 0, mzero == 1` — precisely the issue's coefficient: a
non-trivial radical form that denotes zero (G-DIFF).

## B. The observable consequence — leading-zero stripping (`densebasic.py:265`)

The `__bool__` change is consumed by `dup_strip([c])` (the `if not f or f[0]`
guard): a constant univariate polynomial's coefficient list `[c]` is kept iff
`bool(c)` is truthy, else collapses to the canonical empty list (the zero
polynomial). This is the path through which the issue manifests — the
`clear_denoms()` result whose `rep` is `DMP([EX(0)], EX, None)` instead of
`DMP([], EX, None)`, with `is_zero` wrongly `False`.

| # | model.py impl op (`strip_constant_len`) | patch.diff-induced behaviour | tag | justification |
|---|---|---|---|---|
| B1 | `if coeff_truthy(c): return 1 else: return 0` | `dup_strip([coeff])` returns `[coeff]` if `bool(coeff)` else `[]` (`densebasic.py:265`) | R + I | the strip's keep/drop branch IS the truthiness test (I, the same control structure); the carrier refinement (R) maps the stored list to its length: `len == 0` ↔ `DMP([], EX, None)` (the canonical zero poly), `len == 1` ↔ `DMP([coeff], EX, None)` (mapping.md §2). `dup_strip` is unchanged by the patch; only the `bool(coeff)` it calls changes, so the modeled effect is exactly the patch's effect. |
| B2 | postcondition `Implies(c.mzero == 1, Result() == 0)` and `Implies(c.mzero == 0, Result() == 1)` | a constant poly's stored list is empty (the zero poly) iff its single coefficient denotes zero | I | this is `dup_strip` composed with the corrected `bool`: the canonical zero-poly representation is reached exactly when the coefficient denotes zero, which is what makes `Poly(<zero expr>, x) == Poly(0, x, domain='EX')` (`f.rep == g.rep`, both `[]`) — the F2P `test_issue_20427` assertion. |

Why `strip_constant_len` is in the model rather than only `coeff_truthy`: it ties
the abstract truthiness change to the *observable* poly-level behaviour the F2P
test checks (`f == Poly(0, x, domain='EX')`, i.e. equal `DMP` reps, i.e. both
stripped to `[]`). It consumes `coeff_truthy` under spec (not as an axiom — the
two modeled functions are both implemented), so its prepatch image fails through
the shared `coeff_truthy` defect.

## B2. Total correctness — the MustTerminate obligation

Both modeled functions carry `Requires(MustTerminate(...))` (measures: `Coeff`
constructor 1, `coeff_truthy` 2, `strip_constant_len` 3, so nested calls
strictly decrease). This is not an extra behaviour of the gold patch — it is
the *totality* of the real operations, made explicit so the value
postconditions cannot be satisfied vacuously by a diverging implementation:

* the real `__bool__` body (`return not f.ex.is_zero`) is a straight-line
  attribute read plus negation — it terminates and returns its verdict to the
  caller (`dup_strip`'s guard);
* the real `dup_strip` on a constant list `[c]` is a bounded scan of a
  length-≤1 list — it terminates and returns the stripped representation.

Without the obligation the spec was too weak on exactly this axis: the
G-PANEL-1 auditor's atk_8 rival inserted an infinite spin
(`while (1 if (f.ex.is_zero is True) else 0) >= 0: pass`) before the correct
return; the same-spec model image verified (all value Ensures hold vacuously
on the diverging trace), while the faithful real patch HANGS the F2P suite
(recorded harness run: "sympy__sympy-20428: Test timed out after 240 seconds"
— it does not resolve). Under `MustTerminate` a measureless loop leaks the
caller's obligation and Nagini rejects it ("Obligation leak check failed");
the PBT cases `nonterm-ct-spin` / `nonterm-sl-spin` pin this rejection, and
the positive controls confirm the obligation does not over-constrain honest
straight-line implementations.

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — routing truthiness through the mathematical zero predicate
`Expr.is_zero` instead of the structural `!= 0` — is modeled **deeply** (the
explicit `mzero` facet consumed by `coeff_truthy`, step A2, an **A-reference**),
not hidden behind an axiom about the function under change. There is **no
consumed `@ContractOnly` axiom** in this bundle: the changed function
(`__bool__`) is the function under spec, and its `is_zero` callee is modeled as
the `mzero` field, validated against the real `Expr.is_zero` by G-AX.

## D. verify(model) ⇒ resolved

`coeff_truthy` verifies only if its result equals "the coefficient does not
denote zero" (`c.mzero == 0`, A2); `strip_constant_len` verifies only if the
stored constant-poly list is empty exactly when the coefficient denotes zero
(B2). By R (`Coeff` ↔ `EX` coefficient, list-length ↔ `DMP.rep`) the verified
truthiness equals `not f.ex.is_zero` and the verified strip equals `dup_strip`'s
collapse of `[EX(0_denoting)]` to `[]`; by G-AX the deep facet `mzero` equals the
real `Expr.is_zero` (A-reference) on bare-zero, non-zero, and the issue's
denoting-zero radical coefficient. Therefore a model satisfying this spec,
refined by the map above, is the gold patch (`return not f.ex.is_zero`) up to
type refinement and the audited deep facet — and the gold patch resolves
(`Poly(<zero expr>, x) == Poly(0, x, domain='EX')`, G-RESOLVE). The trust points
are exactly the two of PLAN §1.1: deep-model/axiom soundness (G-AX, here the
`mzero == Expr.is_zero` reference) and refinement fidelity (this document, G-EQ).
