# refinement.md — operation correspondence (sympy__sympy-17655)

Maps every op in `implementation_scaleByFactor` to its `patch.diff` counterpart.
Tags: **R** type refinement · **A-consumed** proof uses axiom property ·
**A-reference** deep model validated == real callee (G-AX) · **I** identical op.

The patch adds a left scalar-multiply behavior that delegates to the existing
right scalar-multiply: post-patch the operation builds the coordinate list
`[simplify(x*factor) for x in self.args]` and returns the resulting point. We
model the point as its coordinate list (`List Rat`) and the result as
`Option (List Rat)` (`some` = a well-defined point; `none` = the pre-patch
undefined/error result).

| # | Lean impl op | patch.diff counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `factor : Rat`, `coords : List Rat` | the scalar `factor` and the point's `self.args` | R | scalar ↔ Rat, point ↔ coordinate `List Rat` bijection (mapping.md). Exact `Rat` faithfully captures `simplify(x*factor)` for the numeric coordinates exercised. |
| 2 | `let mut acc := []` | the empty list the comprehension `[… for x in self.args]` builds into | I | concrete empty-output init |
| 3 | `for x in coords do` | the comprehension iterates `self.args` coordinate-wise | I | per-coordinate iteration, order preserved |
| 4 | `acc := acc ++ [x * factor]` | `simplify(x*factor)` per coordinate | A-reference | the per-coordinate scaling op; validated == the real `Point.__mul__` body `simplify(x*factor)` by G-AX. NOT axiomatized. |
| 5 | `return some acc` | `return Point(coords, evaluate=False)` (a well-defined point) | R | `Point(...)` ↔ `some <coords>`; the result is a real point, never an error |

No A-consumed rows: the proof discharges `scaleSpec` directly; no UNCHANGED
callee property is assumed.

The discriminating clause is the result inhabitation: post-patch the operation
yields `some (scaleSpec factor coords)` — a well-defined point — for every input.
The prepatch impl yields `none` (the operation was undefined on the left, raising
rather than returning a point), so its `correct_scaleByFactor` cannot close
against the frozen `problem_spec_scaleByFactor` (which pins `some (...)`). That is
the G-DIFF signal, and it mirrors the real bug: `5 * Point(1,1)` raised at
`base_commit` and returns `Point(5,5)` post-patch.
