# mapping.md — sympy__sympy-24066

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 514579c655bf22e2af14f0743376ae1d7befe345`, states the type
abstraction, and gives the provenance of the one axiom (callee source + the
behaviour the axiom encodes).

Repo file under change: `sympy/physics/units/unitsystem.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `collect_argument_dimensions(arg_dims)` | the `Function` branch of `UnitSystem._collect_factor_and_dimension` — `sympy/physics/units/unitsystem.py:192-196` | the modeled changed behaviour: the per-argument dimension reporting of an applied function |
| `is_dimensionless(code)` *(axiom — A-consumed)* | `DimensionSystem.is_dimensionless` — `sympy/physics/units/dimensions.py:447`, called as `self.get_dimension_system().is_dimensionless(...)` (introduced at the patched line `unitsystem.py:195` post-patch) | unchanged community callee the patched branch consults to decide whether an argument dimension is dimensionless. **Partial**: it produces a verdict only on dimensions whose dimensional dependencies resolve; it raises `TypeError` otherwise (see §3.1). |
| `resolvable(code)` *(axiom — A-consumed, domain predicate)* | the implicit total-domain of `DimensionSystem.is_dimensionless` / `get_dimensional_dependencies` — `sympy/physics/units/dimensions.py:447`, `:433` | opaque domain predicate: the codes on which the dimensionless test returns a verdict (does not raise). Models the real callee's partiality so the proof never certifies a (false) totality. Checked by axiom_check.py raise-surface fuzzing (§3.1). |
| `CANON_ONE()` | the canonical dimensionless dimension `Dimension(1)` (`dimensions.py:150` `__new__` with `name == 1`) — the object the patch substitutes in | pure spec: the distinguished code of the canonical dimensionless dimension |
| `canon_dim(code)` *(deep model — A-reference)* | the per-argument list-comprehension element of the patched branch: `Dimension(1) if self.get_dimension_system().is_dimensionless(d[1]) else d[1]` (`unitsystem.py:195` post-patch) | pure spec: the canonicalisation of one argument dimension; the deep model of the changed reporting, validated `== the real gold Function branch` by axiom_check.py (G-AX), NOT consumed as an axiom |
| `canon_seq(s)` *(deep model — A-reference)* | the whole list comprehension `[Dimension(1) if ... else d[1] for d in fds]` (`unitsystem.py:195` post-patch) | pure spec: the canonicalisation of the whole argument-dimension list (the front-recursive fold of `canon_dim`) |

The pre-patch repo behaviour the change corrects (for the refinement audit, not
referenced from the consumer spec view): the old `Function` branch
(`unitsystem.py:192-196`) returned each argument's dimension **verbatim**
(`*(d[1] for d in fds)`), so a dimensionless-but-non-canonical argument dimension
(e.g. `Dimension(time/(capacitance*impedance))`) flowed out unchanged and later
compared structurally unequal to the canonical `Dimension(1)` in the `Add`
branch's `if dim != addend_dim` check (`unitsystem.py:178`), raising `ValueError`.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| a `Dimension` object (a sympy `Expr` whose identity for equality is its `name`) | an integer "dimension code" | each distinct `Dimension` value ↔ a distinct `int`; structural `Dimension` equality ↔ `int` equality. In particular the canonical dimensionless dimension `Dimension(1)` (whose `name == 1`) ↔ the distinguished code `CANON_ONE() == 1`; a *non-canonical dimensionless* dimension (e.g. `Dimension(time/(capacitance*impedance))`, dimensionless yet `name != 1`) ↔ some code `!= CANON_ONE()` for which `is_dimensionless` is nonetheless `True`. |
| `expr.args` of an applied `Function`, projected to the dimension component `d[1]` of each `self._collect_factor_and_dimension(arg)` | `arg_dims: List[int]` (the parallel list of argument dimension codes) | `arg_dims[k]` ↔ the code of `fds[k][1]`; `len(arg_dims)` ↔ `len(expr.args)` |
| the returned tuple's dimension components `*dims` (post-patch) / `*(d[1] for d in fds)` (pre-patch) | the returned `List[int]` | the result list ↔ the `*dims` tail of the returned tuple, element-for-element |
| the scale-factor component (`expr.func(*(f[0] for f in fds))`) and the recursion `self._collect_factor_and_dimension(arg)` that produces each `fds[k]` | omitted | the change touches ONLY the dimension components `dims`; the function-symbol/scale-factor head is unchanged by the patch and observationally irrelevant to the tested behaviour, so it is not modelled. |

`Dimension` carries no Nagini-expressible structure the tested behaviour
depends on beyond "is it dimensionless?" and "is it the canonical `Dimension(1)`?"
— both captured by the code abstraction + the `is_dimensionless` predicate.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `is_dimensionless` + `resolvable` axioms ↔ `DimensionSystem.is_dimensionless` (A-consumed)
**Callee:** `sympy/physics/units/dimensions.py:447`

```python
def is_dimensionless(self, dimension):
    if dimension.name == 1:
        return True
    return self.get_dimensional_dependencies(dimension) == {}
```

It is a **PARTIAL boolean predicate** on a dimension. On dimensions whose
dimensional dependencies can be computed, it returns: `True` for the canonical
`Dimension(1)` (the `name == 1` short-circuit) and for any dimension whose net
dependencies cancel (e.g. `time/(capacitance*impedance)`); `False` otherwise
(e.g. `length`, `mass`, even `Dimension(length**mass)` / `Dimension(time**length)`,
which resolve to a non-empty dependency dict). But it **raises `TypeError`** on
dimensions whose dependencies cannot be resolved — `get_dimensional_dependencies`
propagates the error from `_get_dimensional_dependencies_for_name` /
`Dimension.__new__`. Reproducibly in the pinned 1.12 eval container:

| dimension | `is_dimensionless` |
|---|---|
| `Dimension(1)`, `time/(capacitance*impedance)` | `True` |
| `length`, `mass`, `Dimension(length**mass)`, `Dimension(time**length)` | `False` |
| `Dimension(length+mass)`, `Dimension(length-mass)`, `Dimension(1/(length+mass))` | raises `TypeError` ("Only equivalent dimensions can be added or subtracted") |
| `Dimension(sin(length))`, `Dimension(exp(length))` | raises `TypeError` ("input … must be dimensionless …") |

**Why two axioms.** In Nagini a `@ContractOnly` predicate with no `Exsures` is a
commitment to terminate normally on every input — i.e. *totality*. Modeling the
real (partial) callee that way would over-claim it (directive 7's #1 trap). So
the model splits it:
- `resolvable(code)` — an OPAQUE domain predicate marking the codes on which
  the dimensionless test returns a verdict (does not raise);
- `is_dimensionless(code)` carries `Requires(resolvable(code))`, committing to a
  bool **only** on that sub-domain. Off it the model claims nothing (the caller
  is never proven total there) — matching the real partiality.

Both are the **weakest** contracts sufficient for the proof: `is_dimensionless`
asserts **no fixed verdict** (the proof relies only on purity — the SAME code
yields the SAME verdict at the two sites the branch consults it); `resolvable`
asserts only domain membership. The caller `collect_argument_dimensions`
requires every argument code resolvable — the modeled domain is exactly where
the real branch's call is total (the F2P/P2P inputs are all resolvable). The
patched branch calls the real callee with the default invocation
`self.get_dimension_system().is_dimensionless(d[1])` (no flags / kwargs).

**Soundness (raise-surface fuzz, directive 7):** `axiom_check.py` runs the REAL
`is_dimensionless` in-container and asserts (a) it returns a bool on every
resolvable probe dimension (canonical / non-canonical dimensionless / genuine),
and (b) it RAISES `TypeError` on the non-resolvable witnesses above — i.e. the
model's `resolvable` excludes exactly the inputs on which the real predicate has
no verdict. An axiom claiming totality over all codes would fail this fuzz.

### 3.2 `canon_dim` / `canon_seq` deep model ↔ the gold Function branch (A-reference)
**Callee:** the changed `Function` branch of `_collect_factor_and_dimension`,
`sympy/physics/units/unitsystem.py:192-196` (post-patch):

```python
elif isinstance(expr, Function):
    fds = [self._collect_factor_and_dimension(arg) for arg in expr.args]
    dims = [Dimension(1) if self.get_dimension_system().is_dimensionless(d[1]) else d[1] for d in fds]
    return (expr.func(*(f[0] for f in fds)), *dims)
```

The changed reporting is modelled **deeply** by the `@Pure` functions
`canon_dim` (one argument) and `canon_seq` (the fold over the list) in the
`pure` region; there is **no consumed axiom about the changed operation**. The
deep model is instead validated equal to the real callee out-of-band by
axiom_check.py (G-AX): for a battery of dimensions covering the three regimes
(canonical dimensionless, non-canonical dimensionless, genuinely dimensional),
`canon_dim(d)` equals `Dimension(1)` exactly when `is_dimensionless(d)` and `d`
otherwise — which is precisely the list-comprehension element. It additionally
runs the real gold `_collect_factor_and_dimension` on `exp(second/(ohm*farad))`
and on the F2P scenario `1 + exp(second/(ohm*farad))`, asserting the dimension
reported for the dimensionless argument is the canonical `Dimension(1)` and the
end-to-end result is `(1 + E, Dimension(1))`. Docs / source: the units module
docstrings; `dimensions.py` / `unitsystem.py` as cited.

**Soundness check (G-AX):** `axiom_check.py` runs the real
`SI.get_dimension_system().is_dimensionless` and the real
`SI._collect_factor_and_dimension` in-container (apply_gold=True for the
A-reference half). The `is_dimensionless` A-consumed obligation holds on both
the base and the gold tree (unchanged callee); the `canon_dim` A-reference
matches the real Function branch only on the gold tree (on the base/buggy tree
it correctly fails, returning the non-canonical dimension). It imports only
`sympy` (the repository under test) and the standard library. Exit 0 iff sound.
