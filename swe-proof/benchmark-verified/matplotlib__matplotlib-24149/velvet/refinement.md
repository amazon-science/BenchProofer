# refinement.md — matplotlib__matplotlib-24149

Maps every operation of `Solution.lean`'s `impl` `do` block (method
`selectReference`) to its `patch.diff` counterpart inside `Axes._convert_dx`,
under the type bijection of mapping.md §2. Tags: **R** (type refinement),
**A-consumed** (proof uses an axiom's `ensures`), **A-reference** (deep model
validated == real callee by G-AX), **I** (identical concrete op).

The patch edits the element-extraction block (lines 2170-2189 @ base_commit).
The two extraction sites (`x0` and `xconv`) are the SAME pattern; the model
captures one site (`selectReference`), and the patch's two added `except
StopIteration:` arms are two instances of it. The discriminating change the
patch introduces is identical at both: *on the all-non-finite path, recover via
the unconditional first element instead of letting `StopIteration` escape.*

| # | Solution.lean op (impl) | patch.diff / repo counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `let found := firstFinite xs` | `x0 = cbook._safe_first_finite(x0)` (default `skip_nonfinite=True`), under the `try:` that may raise `StopIteration` | **A-reference** | `firstFinite xs = xs.find? isFiniteVal` is the deep model of `_safe_first_finite`'s `else`-branch `next(val for val in obj if safe_isfinite(val))`: `some v` ⇔ a first finite element exists; `none` ⇔ all non-finite (⇔ the real call raises `StopIteration`). Validated == real callee by `axiom_check.py`. |
| 2 | `found.getD (firstElement xs)` | the `except StopIteration:` arm added by the patch: `x0 = cbook.safe_first_element(x0)` | **A-reference** | `firstElement xs = xs.headD 0` is the deep model of `safe_first_element` (= `_safe_first_finite(obj, skip_nonfinite=False)` = `next(iter(obj))`, the first element unconditionally). `Option.getD` selects the finite element when present (the no-raise path) and the unconditional first element when absent (the `except StopIteration` recovery). Validated == real callee by `axiom_check.py`. |
| 3 | `return Except.ok result` | the extraction binds `x0` (resp. `x`) to a scalar and execution continues (no exception escapes `_convert_dx`) | **R** | `Except.ok` ↔ "the block produced a representative scalar and did not raise". The refinement: `Except.ok v` ⇔ a value `v` was bound; an escaping exception ⇔ `Except.error`. The patch guarantees the `ok` leg on every non-empty input (`require xs ≠ []`, established by the preceding `if xconv.size == 0: return` guard — mapping.md §2). |

No **A-consumed** rows: both callees are modeled deeply, so they are
A-references (G-AX-validated), not consumed axioms — there are no dead axioms.
No **kind-3** rows (no changed op inexpressible in Velvet); the entire changed
behavior is the `getD`-fallback, expressed directly.

**Prepatch correspondence (G-DIFF).** `Solution_prepatch.lean` replaces op 2+3
with `match found with | some v => ok v | none => error noFiniteFound` — i.e. no
fallback, the failure propagates outward. This is the pre-patch source: only the
inner `except (TypeError, IndexError, KeyError):` arms exist, so the
`StopIteration` from the all-non-finite path is uncaught and escapes
`_convert_dx` (the crash in the bug report). The prepatch fails `prove_correct`
exactly on the `none` leg, which cannot equal `Except.ok ((firstFinite
xs).getD (firstElement xs))`.
