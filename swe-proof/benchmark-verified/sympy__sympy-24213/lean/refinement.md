# refinement.md — sympy__sympy-24213

Operation-by-operation correspondence between
`implementation_factorAndDimensionOfSum` (Solution.lean impl region) and
`patch.diff` (the POST-PATCH `Add` branch of `_collect_factor_and_dimension`).
Tags: **R** type refinement, **A-consumed** proof uses an axiom, **A-reference**
deep model validated == real callee, **I** identical concrete op.

| # | Lean impl op | patch.diff / post-patch Python op | tag |
|---|---|---|---|
| 1 | `let dim := head.2` | `factor, dim = self._collect_factor_and_dimension(expr.args[0])` (the `dim` half) | R |
| 2 | `let mut factor := head.1` | `factor, dim = ... (the factor half)` | R |
| 3 | `for a in addends do` | `for addend in expr.args[1:]: addend_factor, addend_dim = self._collect_factor_and_dimension(addend)` | R |
| 4 | `if dim.deps ≠ a.2.deps then return none` | `if not self.get_dimension_system().equivalent_dims(dim, addend_dim): raise ValueError(...)` | R |
| 5 | `factor := factor + a.1` | `factor += addend_factor` | R |
| 6 | `return some (factor, dim)` | `return factor, dim` | I |

## Notes

- **Every step is R or I — no A.** The changed op (the addend-compatibility
  test) is modeled DEEPLY as equality of the canonical base-dimension power maps
  `dim.deps = a.2.deps`. SPEC_GUIDE §3 forbids axiomatizing a deeply-modeled
  changed op, so the `axioms` region is empty and **G-AX skips**. Rational
  addition `+` is `Rat`'s field operation (Mathlib), not an axiomatized callee.

- **R justification.**
  - Steps 1–3: the recursive sub-calls
    `self._collect_factor_and_dimension(addend)` are *unchanged* behavior; their
    `(scale_factor, dimension)` results are taken as the modeled routine's
    *inputs* — the head pair `head : Rat × Dim` and the remaining addends
    `addends : List (Rat × Dim)` (the fix neither alters nor inspects how those
    pairs are produced). A rational scale factor refines to `Rat`; a sympy
    `Dimension` refines to `Dim` (surface `name` + canonical `deps` map;
    mapping.md bijection). `expr.args[1:]` (the list of remaining addends)
    refines to the `addends : List …` walked in order by `for a in addends`.
  - **Step 4 is the fix.** Post-patch the addend is accepted iff
    `equivalent_dims(dim, addend_dim)`, i.e.
    `get_dimensional_dependencies(dim) == get_dimensional_dependencies(addend_dim)`
    — equality of base-dimension power maps. `Dim.deps` carries exactly that map
    as a canonical (sorted, zero-free) assoc list, so `dim.deps = a.2.deps`
    reproduces `equivalent_dims` (mapping.md canonicalization invariant). On
    failure the routine `raise ValueError(...)`; the model returns `none` (the
    `Option` ↔ raised-vs-returned bijection). On success it continues.
  - Step 5: `factor += addend_factor` ↔ `factor := factor + a.1` (exact `Rat`
    addition; the fix never inspects the factor's numeric value, only sums them).
  - Step 6: `return factor, dim` — the head dimension is carried through
    unchanged (frame, SPEC_GUIDE §0.5) and paired with the summed factor; `I`.

- **The bug the spec sees.** Base-commit step 4 was `if dim != addend_dim:` —
  structural `Dimension` inequality, which compares the symbolic *surface name*
  (`Dimension.__eq__`). Two addends written with different surface names but the
  same base-dimension powers (e.g. a quantity recorded as `velocity` versus the
  product `acceleration*time`, both reducing to length·time⁻¹) compare unequal,
  so the head-vs-addend test fired and the sum was rejected with a `ValueError`.
  `Solution_prepatch.lean` models exactly this by branching on the surface
  identity `dim.name ≠ a.2.name` instead of the dependency map `dim.deps`. On any
  addend list mixing equivalent-but-differently-named dimensions, the prepatch
  returns `none` (rejects) where the spec demands `some (Σfactor, head dim)`.
  Its carried gold proof (the accumulator-generalized `deps`-keyed fold) cannot
  close against the `name`-keyed branch and fails to typecheck (G-DIFF). This is
  the only independently-observable fixed behavior, so one prepatch suffices.

- **G-CONF** mechanically refutes the R/I legs: an in-process replica of the
  POST-patch Add branch using the REAL sympy `DimensionSystem.equivalent_dims`
  (oracle) is diffed against the impl shadow (branch on the canonical dependency
  assoc list, sum factors, carry head dim) over ≥1e5 fuzzed `(head, addends)`
  inputs drawn from a catalog that deliberately includes
  equivalent-but-differently-written dimensions (velocity / length·time⁻¹ /
  acceleration·time; force / mass·acceleration; acceleration / length·time⁻²) —
  the discriminating category — plus genuinely incompatible dimensions. Zero
  disagreements required. No A legs, so nothing for G-EQ beyond this narrative.
