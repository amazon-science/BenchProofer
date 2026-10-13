# refinement.md — sympy__sympy-22714

The operation-by-operation correspondence between `model.py`'s implementation
(the `screen_coordinates` impl region + the deep model `any_triggering` /
`coord_triggers`) and `patch.diff` (the gold patch).
Each step is tagged **R** (type refinement), **A-consumed** (the proof uses an
axiom's `Ensures`), **A-reference** (a deep model validated == the real
operation by axiom_check.py / G-AX, NOT consumed), or **I** (identical concrete
operation).

The claim: *any implementation that verifies against this frozen spec, refined
per the map below, computes the same raise/no-raise decision as the gold patch
on the tested coordinate tuples, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The single changed site — `Point.__new__` imaginary screen

Gold hunk (`sympy/geometry/point.py:155`):
```
- if any(a.is_number and im(a) for a in coords):
+ if any(a.is_number and im(a).is_zero is False for a in coords):
      raise ValueError('Imaginary coordinates are not permitted.')
```

| # | model.py impl op (`screen_coordinates` / fold) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameters `coord_kind, coord_verdict, coord_extra : List[int]` | `coords` (a `Tuple` of `Expr`) iterated by `for a in coords` | R | per-coordinate facts abstracted as parallel `int` lists in coordinate order: `coord_kind[i] = (a.is_number)`, `coord_verdict[i] = (im(a).is_zero)` tri-state, `coord_extra[i] = bool(im(a))`. The 1:1 bijection (incl. the `None`->-1 / `is_zero is False`->`==0` encoding) is in mapping.md §2-3. |
| A2 | `coord_triggers(kind, verdict) == (kind == 1 and verdict == 0)` | the per-coordinate conjunct `a.is_number and im(a).is_zero is False` | A-reference | the **changed** test is modeled DEEPLY (spelled out), not behind a consumed axiom. `a.is_number` True ⇔ `coord_kind == 1`; `im(a).is_zero is False` ⇔ `coord_verdict == 0` (Python `is False` identity matches ONLY the `False` verdict, not `None`). G-AX (axiom_check.py) runs real SymPy on representative coordinates and asserts `coord_triggers(enc(a)) == (a.is_number is True and im(a).is_zero is False)`. No `@ContractOnly` axiom is consumed. |
| A3 | `any_triggering(seq_kind, seq_verdict)` — front-recursive existential over the head | `any(... for a in coords)` | A-reference + R | `any` over the generator ⇔ the existential fold; G-AX asserts `any_triggering(enc tuple) == any(a.is_number and im(a).is_zero is False for a in coords)` on every probed tuple. R for the `Tuple`->`PSeq[int]` carrier. |
| A4 | `Result()` (the bool) interpreted as "the constructor takes the raising branch" | the `if any(...)` guard controlling `raise ValueError('Imaginary coordinates are not permitted.')` | I | identical control decision: True ⇔ raise, False ⇔ fall through. The raise itself and the unchanged remainder of `__new__` are outside the modeled delta (mapping.md §1). |

The discriminating content of the change lives in step A2: the post-patch keys
the rejection off `im(a).is_zero is False` (the negative outcome,
`coord_verdict[i] == 0`), whereas the pre-patch keys it off the raw truthiness
`im(a)` (`coord_extra[i]`). `model_prepatch.py` reproduces the pre-patch
generator (`coord_kind[i] == 1 and coord_extra[i] == 1`) and **fails**
the postcondition `Result() == any_triggering(...)` on the bug-witness row
(a concrete real coordinate under `evaluate(False)`: `coord_kind=1`,
`coord_extra=1`, `coord_verdict=1`) — exactly the spec sensing the change
(G-DIFF). It is the same row as F2P `test_issue_22684`.

## B. No consumed axioms

There is no `@ContractOnly` axiom in this bundle. The changed operation — the
per-coordinate imaginary test — is modeled deeply (A2/A3, both **A-reference**),
not hidden behind an axiom about the function under change. The SymPy
attributes `a.is_number` and `im(a).is_zero` are the *inputs* to the modeled
test (abstracted to `int` lists, step A1), not opaque callees the proof
reasons through, so they are neither axioms nor A-references in their own right;
their faithful encoding is what G-AX validates as part of A2/A3.

## C. No kind-3 (unexpressible-changed-op) steps

Every step is R, A-reference, or I. The one operation that genuinely *changed* —
the rejection test — is modeled deeply (the spelled-out `coord_triggers` /
`any_triggering`), an **A-reference** validated by G-AX against real SymPy.

## D. verify(model) ⇒ resolved

`screen_coordinates` verifies only if its `Result()` equals
`any_triggering(ToSeq(coord_kind), ToSeq(coord_verdict))` — i.e. the
exact post-patch predicate "some concrete-number coordinate has an imaginary
part certified to be non-zero." By R (the coordinate-fact bijection of
mapping.md §2) and the A-reference equalities (A2/A3, G-AX), the verified
decision equals
`any(a.is_number and im(a).is_zero is False for a in coords)` on the tested
coordinate tuples — i.e. the gold patch's guard. A model satisfying this spec,
refined by the map above, is the gold patch up to type refinement and the
G-AX-validated deep model; the gold patch resolves (G-RESOLVE). The single
trust point is refinement fidelity (this document, G-EQ) backed by the G-AX
encoding check; there is no axiom-soundness trust point because no axiom is
consumed.
