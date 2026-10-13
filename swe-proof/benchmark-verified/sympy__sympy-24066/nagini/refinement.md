# refinement.md — sympy__sympy-24066

The operation-by-operation correspondence between `model.py`'s implementation
(the `collect_argument_dimensions` impl region, the deep `canon_dim` / `canon_seq`
model, and the live `is_dimensionless` axiom) and `patch.diff` (the gold patch).
Each step is tagged **R** (type refinement), **A** (axiomatized callee — split
into **A-consumed**, where the proof uses the axiom's contract, and
**A-reference**, where a deep model is validated == the real callee by
axiom_check.py / G-AX), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The changed site — the `Function` branch of `_collect_factor_and_dimension`

Gold hunk (`sympy/physics/units/unitsystem.py:192-196`):
```
 elif isinstance(expr, Function):
-    fds = [self._collect_factor_and_dimension(
-        arg) for arg in expr.args]
-    return (expr.func(*(f[0] for f in fds)),
-            *(d[1] for d in fds))
+    fds = [self._collect_factor_and_dimension(arg) for arg in expr.args]
+    dims = [Dimension(1) if self.get_dimension_system().is_dimensionless(d[1]) else d[1] for d in fds]
+    return (expr.func(*(f[0] for f in fds)), *dims)
```

| # | model.py impl op (`collect_argument_dimensions`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `arg_dims: List[int]` | the dimension components `d[1]` of `fds = [self._collect_factor_and_dimension(arg) for arg in expr.args]` | R | each `Dimension` ↔ an integer code (mapping.md §2); `arg_dims[k]` ↔ code of `fds[k][1]`. The recursive sub-collection that *produces* `fds` is unchanged by the patch and is the input to the modeled branch, so it is taken as given (the same list on both sides). |
| A2 | per-element test `is_dimensionless(c)` (guarded by `resolvable(c)`) | `self.get_dimension_system().is_dimensionless(d[1])` | A-consumed | the unchanged community callee `DimensionSystem.is_dimensionless` (mapping.md §3.1); modeled by the opaque `@Pure @ContractOnly is_dimensionless` axiom, which is **partial**: it commits to a bool only on the `resolvable(code)` sub-domain (the real callee raises `TypeError` off it). The proof consumes only its purity (same code → same verdict) and feeds it only resolvable codes (the caller requires all argument codes resolvable — the modeled domain where the real branch's call is total). G-AX confirms it is a bool on the resolvable domain AND raises off it (the model's `resolvable` excludes exactly the raising inputs), per directive 7's raise-surface fuzz. |
| A3 | when dimensionless, `result = [CANON_ONE()] + result` (canonical dimensionless code) | `Dimension(1)` in the list-comprehension element | R + A-reference | `CANON_ONE() == 1` ↔ the canonical dimensionless dimension `Dimension(1)` (`name == 1`), the R-bijection of mapping.md §2. The *decision* to substitute it for a dimensionless argument is the deep model `canon_dim`; G-AX validates `canon_dim == the gold Function-branch element` (mapping.md §3.2), so this is an A-reference, not a consumed axiom. |
| A4 | when not dimensionless, `result = [c] + result` (the code unchanged) | `else d[1]` in the list comprehension | I + R | the argument dimension is reported verbatim; `c` ↔ `d[1]` under the code bijection. |
| A5 | the whole-list result `ToSeq(Result()) == canon_seq(ToSeq(arg_dims))` | the list comprehension `dims = [...]` and the `*dims` splat into the returned tuple | R + A-reference | the result list ↔ the `*dims` tail of the returned tuple element-for-element (mapping.md §2). `canon_seq` is the front-recursive fold of `canon_dim` over the argument list — the deep model of the comprehension, validated == the real callee by G-AX (A-reference). |
| A6 | (not modeled) | `expr.func(*(f[0] for f in fds))` — the function-symbol head with the scale factors | R (omitted) | the head/scale-factor component is **unchanged** between the two hunks (`expr.func(*(f[0] for f in fds))` in both) and is observationally irrelevant to the tested dimension behaviour; not modeled (mapping.md §2). |

The discriminating content of the change — a **dimensionless-but-non-canonical**
argument dimension is reported as the canonical `Dimension(1)` rather than
verbatim — lives in `canon_dim(c) == CANON_ONE()` when `is_dimensionless(c)`
(model) ⇔ the `Dimension(1) if ... is_dimensionless(d[1]) else d[1]` element
(real). The pre-patch branch returned `d[1]` verbatim; `model_prepatch.py`
reproduces that (`result = [c] + result` unconditionally) and **fails** the loop
invariant / postcondition `ToSeq(result) == canon_seq(ToSeq(arg_dims))`, which is
exactly the spec sensing the change (G-DIFF).

## B. Why the canonicalisation is what the F2P test observes

The F2P test `test_issue_24062` builds `exp(T/(R*C))` whose single argument has
dimension `time/(capacitance*impedance)` — dimensionless (G-AX confirms
`is_dimensionless` is `True`) yet structurally `!= Dimension(1)`. It then
collects `1 + exp(expr)` (an `Add`). The `Add` branch (`unitsystem.py:173-184`,
unchanged) requires every addend's dimension to be structurally equal; the
literal `1` carries `Dimension(1)`. Pre-patch, `exp(expr)`'s dimension is the
non-canonical `Dimension(time/(capacitance*impedance))`, so `dim != addend_dim`
is `True` and a `ValueError` is raised. Post-patch, the `Function` branch
canonicalises it to `Dimension(1)`, so the comparison succeeds and the collect
returns `(1 + E, Dimension(1))`. This is precisely the model's discriminating
behaviour `canon_dim(dimensionless) == CANON_ONE()` (the canonical code that
compares equal), tied to the structural-equality semantics by the R-bijection
`code-equality ↔ Dimension-equality` (mapping.md §2).

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-consumed, A-reference, or I. The operation that
genuinely *changed* — substituting the canonical dimensionless dimension for a
dimensionless argument — is modeled **deeply** (`canon_dim` / `canon_seq` in the
`pure` region, consumed by `collect_argument_dimensions`, an **A-reference**),
not hidden behind an axiom about the function under change. The only consumed
axiom, `is_dimensionless` (**A-consumed**, step A2), covers an **unchanged**
callee (`DimensionSystem.is_dimensionless`) the new code invokes; the changed
reporting appears only as the **A-reference** that G-AX validates the deep model
against.

## D. verify(model) ⇒ resolved

`collect_argument_dimensions` verifies only if its output equals the exact
per-argument canonicalisation `canon_seq` — i.e. a dimensionless argument is
reported as `CANON_ONE()` (A3/A5) and a non-dimensionless one verbatim (A4). By
R (Dimension ↔ int code, `Dimension(1)` ↔ `CANON_ONE()`, code-equality ↔
Dimension-equality) the verified branch equals the gold `Function` branch on the
tested inputs; by G-AX the deep model `canon_dim`/`canon_seq` equals the real
gold branch (A-reference) and the real `is_dimensionless` meets the opaque
predicate contract it stands in for (A-consumed). Therefore a model satisfying
this spec, refined by the map above, is the gold patch up to type refinement and
the audited callee — and the gold patch resolves (G-RESOLVE). The trust points
are exactly the two of PLAN §1.1: axiom soundness (G-AX) and refinement fidelity
(this document, G-EQ).
