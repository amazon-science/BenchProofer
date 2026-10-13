# refinement.md — sympy__sympy-22714

Operation correspondence between `implementation_imaginaryCheck` and the gold
`patch.diff`. Tags: **R** (type refinement), **A-consumed** (proof uses an
axiom's property), **A-reference** (deep model validated == real callee by
G-AX/G-CONF), **I** (identical concrete op).

No axioms are declared or consumed: the changed operation (the imaginary
classification of a coordinate) is modeled DEEPLY as the three-valued
determined-non-zero test on the per-coordinate observations. Every row is **R**,
**A-reference**, or **I**. The R/I/A-reference legs are differential-tested by
G-CONF; G-AX is a skip stub (no consumed callee axiom).

## `implementation_imaginaryCheck` ↔ the imaginary-coordinate guard

The gold patch turns

```python
if any(a.is_number and im(a)                 for a in coords):   # PRE-PATCH
    raise ValueError('Imaginary coordinates are not permitted.')
```

into

```python
if any(a.is_number and im(a).is_zero is False for a in coords):  # POST-PATCH
    raise ValueError('Imaginary coordinates are not permitted.')
```

with everything around the guard unchanged. We model the boolean the `any(...)`
computes (raise iff `True`).

| Lean op | patch.diff / source counterpart | tag | note |
|---|---|---|---|
| `coords : List Coord` (each `Coord` = `⟨isNumber, imagPartTruthy, imagPartDetZero⟩`) | the sympified `coords` tuple; per coordinate `a`: `bool(a.is_number)`, `bool(im(a))`, `im(a).is_zero` | R | rich SymPy expressions projected to the three observations the guard reads (mapping.md bijection); `is_number`/`im`/`is_zero` are unchanged callees read as inputs |
| `for c in coords do … return true / return false` | `any(<predicate> for a in coords)` | I | existential short-circuit over the tuple ↦ early-`return true` loop |
| `c.isNumber && (c.imagPartDetZero == some false)` (the per-element predicate) | `a.is_number and im(a).is_zero is False` (post-patch) | A-reference | the EDITED op: reject iff the coordinate is a number whose imaginary part is *determined* non-zero (`is_zero` exactly `False`). Modeled deeply as `imagPartDetZero = some false`; validated == real guard by G-CONF |
| `return false` (fall-through) | `any(...)` is `False` ⇒ no raise | I | accept |

The pre-patch predicate `a.is_number and im(a)` reads the *form-level* truthiness
of the imaginary-part object (`imagPartTruthy`). Under `evaluate(False)` the
imaginary part of a real number stays an unevaluated object that reads truthy
while its determined-zero status is still `True`, so a real coordinate is wrongly
rejected — the reported crash. The post-patch predicate consults the three-valued
`is_zero` and rejects only on a *determined* non-zero imaginary part.

## Independently-observable behavior (G-DIFF)

- `Solution_prepatch.lean`: the per-element predicate uses `c.imagPartTruthy`
  (the form-level reading) instead of `c.imagPartDetZero == some false`. The
  carried gold proof of `correct_imaginaryCheck` fails to close: on any
  coordinate with `imagPartTruthy = true` but `imagPartDetZero = some true`
  (e.g. a real number whose imaginary part is an unevaluated-but-zero object),
  the buggy impl returns `true` while the spec demands `false`. This is the single
  fixed behavior. (FAIL_TO_PASS: `test_issue_22684`.)
