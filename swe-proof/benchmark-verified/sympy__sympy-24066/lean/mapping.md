# mapping.md — sympy__sympy-24066

## Symbol binding (file:line @ base_commit 514579c655bf22e2af14f0743376ae1d7befe345)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_collectFunction` / `problem_spec_collectFunction` / `correct_collectFunction` | the `isinstance(expr, Function)` branch of `UnitSystem._collect_factor_and_dimension` | `sympy/physics/units/unitsystem.py:192-196` |
| `FunctionResult` (pure helper) | the tuple `(scale_factor, *dims)` the branch returns | — |
| `FunctionResult.factor` | `expr.func(*(f[0] for f in fds))` | unitsystem.py:195 (post-patch) |
| `FunctionResult.dims` | the trailing dimension components `*dims` | unitsystem.py:194-195 (post-patch) |
| `canonDim` (pure helper) | `Dimension(1) if self.get_dimension_system().is_dimensionless(d[1]) else d[1]` | unitsystem.py:194 (the added comprehension) |
| `isDimensionless` (opaque callee) | `self.get_dimension_system().is_dimensionless(...)` | `sympy/physics/units/dimensions.py` `DimensionSystem.is_dimensionless` |
| `applyFunc` (opaque callee) | `expr.func(*(...))` reconstruction | core `Function.func` |
| `dimOne` (opaque) | `Dimension(1)` | `sympy/physics/units/dimensions.py` `Dimension` |
| `fds` (input) | `fds = [self._collect_factor_and_dimension(arg) for arg in expr.args]` | unitsystem.py:193 |

## The modeled behavior

Post-patch `Function` branch (unitsystem.py:192-196):

```python
elif isinstance(expr, Function):
    fds = [self._collect_factor_and_dimension(arg) for arg in expr.args]
    dims = [Dimension(1) if self.get_dimension_system().is_dimensionless(d[1]) else d[1] for d in fds]
    return (expr.func(*(f[0] for f in fds)), *dims)
```

Each `arg` of the function application is recursively collected into a
`(scale_factor, dimension)` pair `fds[i] = (f, d)`. The branch returns a tuple
whose first component is the function rebuilt on the arguments' scale factors,
`expr.func(*(f[0] ...))`, and whose remaining components are the arguments'
dimensions — **each normalised to `Dimension(1)` when the dimension system
reports it dimensionless**, otherwise left unchanged.

### The defect

Pre-patch (unitsystem.py:193-196):

```python
elif isinstance(expr, Function):
    fds = [self._collect_factor_and_dimension(arg) for arg in expr.args]
    return (expr.func(*(f[0] for f in fds)),
            *(d[1] for d in fds))
```

The branch returned each argument's dimension `d[1]` verbatim. When an argument
is dimensionless but its dimension is written in a non-canonical symbolic form
(e.g. `time/(capacitance*impedance)`, which reduces to no net dimension but is
not literally `Dimension(1)`), the dimension propagated up was that
non-canonical expression. A subsequent `Add` branch comparison (`if dim !=
addend_dim`) then saw `Dimension(time/(capacitance*impedance))` ≠
`Dimension(1)` and raised `ValueError`, even though both are dimensionless.
Normalising every dimensionless argument dimension to the single unit dimension
fixes the comparison. This is exactly the `1 + exp(second/(ohm*farad))` F2P
scenario.

### Lean modeling

The touched region is modeled deeply as a total function of the observable it
operates on — the list of recursively-collected `(factor, dimension)` pairs:

- `func : Func`                — the function head (`expr.func`); abstracted to
  an opaque tag since only its identity in the reconstruction matters;
- `fds : List (Factor × Dim)`  — the per-argument `(scale_factor, dimension)`
  pairs, produced by the *unchanged* recursive collection and carried as grounded
  inputs (directive 7: the function under spec is recursive, so its own results
  are not axiomatised);
- result `FunctionResult` with `factor : Factor` and `dims : List Dim`.

`Dim`/`Factor`/`Func` are modeled as `Nat` tags — the modeled behavior is purely
structural (a per-element conditional rewrite keyed on a dimensionless predicate
plus an unchanged reconstruction), so the carrier need only support equality and
the `isDimensionless` query. The query and the function reconstruction are the
two UNCHANGED callees, carried opaquely (`isDimensionless`, `applyFunc`), and
appear identically in spec and impl.

Post-patch decision (modeled op-for-op):

```
factor = applyFunc func (fds.map fst)
dims   = fds.map (fun (f,d) => if isDimensionless d then dimOne else d)
```

Pre-patch (the bug):

```
factor = applyFunc func (fds.map fst)
dims   = fds.map (fun (f,d) => d)          # raw dimension, no canonicalisation
```

## Lean ↔ Python type bijection (used by G-CONF / G-AX)

| Python | Lean | bijection |
|---|---|---|
| a dimension expression | `Dim` (`Nat` tag) | identity on the equivalence class observed via `is_dimensionless` |
| `Dimension(1)` | `dimOne : Dim` | identity |
| a scale-factor expression | `Factor` (`Nat` tag) | identity (only carried, never inspected) |
| `expr.func` | `Func` (`Nat` tag) | identity (only carried into `applyFunc`) |
| `self.get_dimension_system().is_dimensionless(d)` | `isDimensionless d : Bool` | identity |
| `expr.func(*(f[0] for f in fds))` | `applyFunc func (fds.map fst)` | identity |
| `fds` | `fds : List (Factor × Dim)` | element-wise pair bijection |
| `(scale_factor, *dims)` | `FunctionResult` (`factor`, `dims`) | the head is `factor`; the trailing tuple components are `dims` (in order) |

## Callee provenance + flag dependencies

- **No consumed callee axiom; no A-reference.** The operation the patch changes
  — the per-argument canonicalisation of dimensionless dimensions to the unit
  dimension — is modeled DEEPLY and structurally over the observable `fds`. Per
  SPEC_GUIDE §3 a deeply-modeled changed decision is NOT axiomatized; the
  `axioms` region carries only opaque SIGNATURES (no `_prop`), so **G-AX skips**.
- `isDimensionless` is the unchanged `DimensionSystem.is_dimensionless` query.
  It is read identically by the post-patch branch and the impl, and appears
  identically in the spec (`canonDim`) and the impl, so it cancels in the
  differential test; no property of it is consumed.
- `applyFunc` is the unchanged `expr.func(...)` reconstruction. The patch does
  not touch the scale-factor component; it is carried opaquely so the spec pins
  `result.factor` to its inputs (directive 5 frame) without inspecting the head.
- `self._collect_factor_and_dimension(arg)` (the recursive call producing `fds`)
  is the function under spec; per directive 7 its already-computed results are
  carried as the grounded input `fds`, not axiomatized.
- No flag dependency: the branch behavior does not vary with any configuration.

## G-CONF fuzz seed

Pinned LCG seed: **24066** (see `conformance_check.py` `SEED`). Corpus:
randomized `fds` lists of `(factor, dim)` pairs where each `dim` is drawn so the
`is_dimensionless` predicate crosses both outcomes, with hand-picked edge cases:
a dimensionless-but-non-unit dimension (the F2P case — must canonicalise to the
unit dimension), an already-unit dimension, a genuinely dimensioned argument
(left unchanged), the empty argument list, and mixed lists. The R/I shadow of
`implementation_collectFunction` is diffed against an in-process replica of the
POST-PATCH branch over ≥1e5 inputs.
