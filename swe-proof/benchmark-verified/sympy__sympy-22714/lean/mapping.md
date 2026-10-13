# mapping.md — sympy__sympy-22714

## Symbol binding (file:line @ base_commit 3ff4717b6a)

| Lean symbol | Python | location |
|---|---|---|
| `implementation_imaginaryCheck` / `problem_spec_imaginaryCheck` / `correct_imaginaryCheck` | the imaginary-coordinate validation guard inside the point constructor: `any(a.is_number and im(a).is_zero is False for a in coords)` (post-patch) | `sympy/geometry/point.py:155` @ base_commit (`Point.__new__`, the `raise ValueError('Imaginary coordinates are not permitted.')` guard) |
| `Coord.imagPartDetZero = some false` (the discriminating clause) | `im(a).is_zero is False` (post-patch) | gold patch, `point.py:155` (pre-patch: bare `im(a)`, i.e. `bool(im(a))`) |

The modeled function is the per-coordinate guard that decides whether the
constructor raises `ValueError('Imaginary coordinates are not permitted.')`.
For a tuple of sympified coordinates `coords`, the guard returns a single
boolean — *should this construction be rejected as imaginary?* — computed by

```python
# POST-PATCH (gold):
any(a.is_number and im(a).is_zero is False for a in coords)
# PRE-PATCH (buggy):
any(a.is_number and im(a)                 for a in coords)
```

The pre-patch form tests the raw truthiness of the imaginary-part object
`im(a)`. When the global `evaluate` flag is off, `im(1)` (and similar) stays an
*unevaluated* object whose `bool(...)` is `True`, so a genuinely real coordinate
is wrongly classified as imaginary and the construction is rejected. The
post-patch form consults the three-valued `is_zero` of the imaginary part and
rejects only when that imaginary part is *determined* non-zero (`is_zero` is
exactly `False`, i.e. neither `True`/determined-zero nor `None`/undetermined).

## Modeled branch / configuration

The guard runs after dimension/morph handling, on the already-sympified
`coords` tuple, independent of the `evaluate` flag value. We model exactly the
`any(...)` boolean decision (raise vs. accept). The earlier `ValueError`/
`TypeError` guards (sequence, dimension, nonzero-removal, `Expr`-ness) are
unchanged, upstream of the edited line, and out of scope; the subsequent
`Point2D`/`Point3D` dispatch is downstream of the decision and unchanged.

## Lean ↔ Python type bijection (used by G-CONF + G-AX)

Each coordinate `a` is bridged to a `Coord` record of three observations taken
from the real sympy object:

| Python observation on coordinate `a` | Lean field | bijection |
|---|---|---|
| `bool(a.is_number)` | `Coord.isNumber : Bool` | `True ↦ true`, `False ↦ false` |
| `bool(im(a))` (raw truthiness of the imaginary-part object — the pre-patch observation) | `Coord.imagPartTruthy : Bool` | `True ↦ true`, `False ↦ false` |
| `im(a).is_zero` (three-valued determined-zero query on the imaginary part) | `Coord.imagPartDetZero : Option Bool` | `True ↦ some true`, `False ↦ some false`, `None ↦ none` |

| Python | Lean | bijection |
|---|---|---|
| the coordinate tuple `coords` | `coords : List Coord` | one `Coord` record per coordinate, in order |
| the `any(...)` boolean (raise iff `True`) | `result : Bool` | `True ↦ true` (reject), `False ↦ false` (accept) |

Sanity points (computed on real sympy objects):
- `a = Integer(1)` (evaluate on): `is_number=True`, `im(1)=0` → `imagPartTruthy=false`, `is_zero=True` → `some true` ⇒ accept.
- `a = Integer(1)` under `evaluate(False)`: `is_number=True`, `im(1)` unevaluated → `imagPartTruthy=true`, `is_zero=True` → `some true` ⇒ accept (post) / reject (pre — the bug).
- `a = I`: `is_number=True`, `im(I)=1` → `imagPartTruthy=true`, `is_zero=False` → `some false` ⇒ reject (both).
- `a = Symbol('x')`: `is_number=False` ⇒ accept (`im(x).is_zero=None` → `none`).

## Callee provenance + flag dependencies

- No callee axiom is consumed. The observations `is_number`, `im`, `is_zero` are
  unchanged callees; they are read as input observations and bridged into the
  `Coord` record (A-reference, validated == real callees by G-CONF). The changed
  operation — switching the imaginary classification from raw truthiness to the
  three-valued determined-non-zero test — is modeled DEEPLY in the spec
  (`imagPartDetZero = some false`), never axiomatized (§0.7).
- Flag dependency: the reported failure manifests when the global `evaluate`
  flag is off (an unevaluated imaginary-part object reads as truthy while its
  determined-zero status is still `True`). G-CONF fuzzes both `evaluate` settings
  so the divergence between the raw-truthiness and determined-zero observations
  is exercised.

## G-CONF fuzz seed

`SEED = 20240627` (pinned in `conformance_check.py`).
