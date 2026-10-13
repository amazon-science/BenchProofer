# mapping.md — sympy__sympy-24213

## Modeled routine

The `Add`-branch of `_collect_factor_and_dimension(self, expr)`
(`sympy/physics/units/unitsystem.py`, lines 171–184 @ base_commit
`e8c22f6eac7314be8d92590bfff92ced79ee03e2`).

The full routine recursively returns, for an expression, a tuple
`(scale_factor, dimension)`. For an `Add` (a sum), it collects the head
addend's `(factor, dim)`, then walks the remaining addends; each must have a
dimension *compatible* with the head's, otherwise a `ValueError` is raised; the
returned factor is the sum of all addends' factors and the returned dimension is
the head's dimension.

The change is localized to the compatibility check inside that loop:

```
            for addend in expr.args[1:]:
                addend_factor, addend_dim = \
                    self._collect_factor_and_dimension(addend)
-               if dim != addend_dim:                                       # base_commit
+               if not self.get_dimension_system().equivalent_dims(dim, addend_dim):
                    raise ValueError( ... )
                factor += addend_factor
            return factor, dim
```

- base_commit: `dim != addend_dim` — **structural** `Dimension` inequality.
  `Dimension` is an `Expr` (`sympy/physics/units/dimensions.py:95`); its `__eq__`
  is structural over the symbolic *name*, so two dimensions are `==` iff their
  name expressions coincide. `Dimension('velocity') != Dimension('acceleration*time')`
  is `True` even though both reduce to the same base-dimension powers.
- post-patch: `equivalent_dims(dim, addend_dim)`
  (`dimensions.py:428`):
  ```
  def equivalent_dims(self, dim1, dim2):
      deps1 = self.get_dimensional_dependencies(dim1)
      deps2 = self.get_dimensional_dependencies(dim2)
      return deps1 == deps2
  ```
  i.e. two dimensions are *equivalent* iff their **dimensional-dependency maps**
  (base-dimension → integer exponent, via `get_dimensional_dependencies`,
  `dimensions.py:422`) are equal as dicts.

## Symbol binding

| Lean | Python | file:line @ base_commit |
|---|---|---|
| `implementation_factorAndDimensionOfSum` / `problem_spec_…` / `correct_…` | the `Add` branch of `_collect_factor_and_dimension` | `sympy/physics/units/unitsystem.py:171-184` |
| `head : Rat × Dim` | `(factor, dim)` from `self._collect_factor_and_dimension(expr.args[0])` | unitsystem.py:172 |
| `addends : List (Rat × Dim)` | `[self._collect_factor_and_dimension(a) for a in expr.args[1:]]` | unitsystem.py:173-175 |
| `Dim.name : String` | the `Dimension` object's structural identity (its `.name` Expr, used by `Dimension.__eq__`) | dimensions.py:95,150 |
| `Dim.deps : List (String × Int)` | `get_dimension_system().get_dimensional_dependencies(dim)` rendered as a canonical assoc list | dimensions.py:422 |
| `head.2.deps = a.2.deps` (compat test, post-patch) | `equivalent_dims(dim, addend_dim)` | dimensions.py:428 |
| `head.2.name = a.2.name` (compat test, prepatch) | `dim == addend_dim` (structural) | unitsystem.py:179 base_commit |
| `result = none` | `raise ValueError(...)` | unitsystem.py:180-183 |
| `result = some (Σfactor, head dim)` | `return factor, dim` | unitsystem.py:185 |

## Lean ↔ Python type bijection (G-CONF / G-AX)

- `Rat` ↔ a rational scale factor. The fix never inspects the factor's value;
  factors are only summed (`factor += addend_factor`). `Rat` gives exact `+`.
  In the conformance shadow these are `fractions.Fraction`.
- `Dim` ↔ a sympy `Dimension`. `Dim.name : String` ↔ `str(dim.name)`
  (the structural identity that `Dimension.__eq__` compares — distinct surface
  forms `velocity` vs `acceleration*time` get distinct names). `Dim.deps`
  ↔ the canonical sorted assoc list of
  `get_dimensional_dependencies(dim)` (keys `str`-ified, zero exponents dropped,
  sorted by key) — so `deps` equality is exactly dict equality, i.e.
  `equivalent_dims`. **Canonicalization invariant:** every `Dim.deps` produced
  by the bridge is sorted by key with no zero entries, so structural list
  equality reproduces dict equality.
- `Option (Rat × Dim)` ↔ the routine's outcome: `none` ↔ `ValueError` raised;
  `some (f, d)` ↔ `return (f, d)`.

## Callee provenance / flag deps

- `equivalent_dims` / `get_dimensional_dependencies` are **not** axiomatized:
  the changed comparison is modeled DEEPLY as `Dim.deps` equality (SPEC_GUIDE
  §3 — never axiomatize the changed op). No `opaque` callee, no `_prop` axiom.
- The recursive sub-calls `self._collect_factor_and_dimension(addend)` are
  unchanged behavior; their `(factor, dim)` results are taken as the modeled
  routine's *inputs* (the `head` / `addends` lists). No flag dependence.

## G-CONF fuzz seed

`24213` (pinned; also in `conformance_check.py` and `meta.json`).
