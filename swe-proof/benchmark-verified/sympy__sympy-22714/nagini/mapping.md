# mapping.md — sympy__sympy-22714

Binds every model.py symbol to the real repo symbol it abstracts, with the type
abstraction and the provenance (file:line at `base_commit`
`3ff4717b6aef6086e78f01cdfa06f64ae23aed7e`) of every fact the model reads.

## 1. The modeled function

| model.py | repo | location (base_commit) |
|---|---|---|
| `screen_coordinates(coord_kind, coord_verdict, coord_extra) -> bool` | the imaginary-coordinate screen inside `Point.__new__` (the `if any(...)` guard that raises `ValueError('Imaginary coordinates are not permitted.')`) | `sympy/geometry/point.py:155-156` |

Note: model.py's consumer-visible spec view uses only abstract identifiers
(`coord_kind`, `coord_verdict`, `coord_extra`, `coord_triggers`,
`any_triggering`) that name no patched path/symbol and do not narrate the
bug->fix mechanism. This mapping document (reviewer-facing, NOT part of the
spec view) is where those abstract names are bound to the real SymPy symbols.

`Point.__new__(cls, *args, **kwargs)` is defined at `sympy/geometry/point.py:109`.
The screen is the single statement the gold patch changes:

```
155  if any(a.is_number and im(a) for a in coords):                       # pre-patch
     if any(a.is_number and im(a).is_zero is False for a in coords):     # post-patch
156      raise ValueError('Imaginary coordinates are not permitted.')
```

The modeled function's boolean `Result()` is the value of the `any(...)`
generator — i.e. *whether the constructor takes the raising branch*. We model
only this decision (the operation the patch changes); everything else in
`__new__` is untouched by the patch and is irrelevant to the tested behavior.

## 2. Type abstraction

`coords` is a `Tuple` of SymPy `Expr` objects. The screen reads, per
coordinate `a`, only two decidability facts plus a truthiness:

| repo expression on coordinate `a` | type in repo | model carrier |
|---|---|---|
| `a.is_number` | `bool` (a property; always two-valued) | `coord_kind[i] : int`, 1 = True, 0 = False |
| `im(a).is_zero` | `bool` or `None` (SymPy fuzzy three-valued) | `coord_verdict[i] : int`, 1 = True (positive outcome), 0 = False (negative outcome), -1 = None (undecided) |
| `bool(im(a))` (the pre-patch generator's second conjunct used `im(a)` directly in a boolean context) | `bool` (or raises; but is only reached when `is_number` is True, where it does not raise for the tested inputs) | `coord_extra[i] : int`, 1 = truthy, 0 = falsy |

A coordinate tuple of length n maps to three parallel `List[int]` of length n,
in coordinate order. `any(P(a) for a in coords)` ↔ the existential fold
`any_triggering` (post) / the truthiness existential (pre).

Tri-state -> int encoding: SymPy's "fuzzy bool" `is_zero` returns `True`,
`False`, or `None`; `is_zero is False` is Python identity, true ONLY for the
`False` case (the negative outcome / non-zero imaginary part), not for `None`.
That is exactly `coord_verdict[i] == 0` in the model.

## 3. The changed test is modeled DEEPLY (no consumed axiom)

The operation the patch changes is the per-coordinate test itself, so it is NOT
axiomatized — it is spelled out with abstract model identifiers:
`coord_triggers(kind, verdict) == (kind == 1 and verdict == 0)` and the
existential fold `any_triggering`. The SymPy facts `a.is_number` and
`im(a).is_zero` are the *inputs* to that test (abstracted as the `int` lists,
mapping.md §2), not opaque callees the proof reasons through. Consequently there
is **no `@ContractOnly` axiom**.

The correspondence of the deep model to the real per-coordinate test
`a.is_number and im(a).is_zero is False` is an **A-reference**: validated by
`axiom_check.py` (G-AX), which runs real SymPy on representative coordinates
(real numbers under `evaluate(True)` and `evaluate(False)`, genuine imaginaries,
symbols, the issue's `sympify` repro) and asserts, for every coordinate, that

  `(a.is_number is True) and (im(a).is_zero is False)`

equals the model's `coord_triggers(enc_is_number(a), enc_imag_is_zero(a))`
(under the abstraction `coord_kind <- a.is_number`,
`coord_verdict <- im(a).is_zero` tri-state), and that the whole-tuple `any(...)`
equals `any_triggering`. (axiom_check.py's internal helper names retain the
real-operation framing — it is evidence, not the consumer-visible spec view.)

### 3.1 Why `coord_extra` is the pre-patch discriminator (provenance)

Measured with real SymPy at base_commit (`conda run -n swebench-nagini`):

| coordinate (context) | `a.is_number` | `bool(im(a))` (pre) | `im(a).is_zero` | `im(a).is_zero is False` (post) | pre raises | post raises |
|---|---|---|---|---|---|---|
| `Integer(1)`, evaluate=True | True | False (`im`=0) | True | False | no | no |
| `Integer(1)`, evaluate=False (`im(1)` unevaluated) | True | **True** | True | **False** | **YES (bug)** | no |
| `2*I` | True | True | False | True | yes | yes |
| `Symbol('x')` | False | (short-circuit) | None | False | no | no |

The pre-patch second conjunct `im(a)` is truthy for a concrete *real* number
under `evaluate(False)` (the unevaluated `im(1)` object's `__bool__` is True),
while `im(a).is_zero` is `True` there — so the post-patch `is_zero is False` is
`False`. That single row is the bug witness; in model carriers it is
`coord_extra[i] == 1` with `coord_verdict[i] == 1` and `coord_kind[i] == 1`.

## 4. F2P / P2P linkage

- F2P `test_issue_22684`: `with evaluate(False): Point(1, 2)` — exactly the
  bug-witness row; post-patch screen returns False (no raise), pre-patch returns
  True (raises). The model's spec returns `any_triggering(...) == False`
  there; the prepatch impl returns True → fails G-VERIFY.
- P2P `test_point` / `test_Point2D` / `test_issue_9214` / `test_issue_11617`
  etc.: ordinary real and symbolic points (no triggering coordinate) —
  screen returns False under both reading rules, so the post-patch preserves
  them. The fix does not over-permit: a genuinely imaginary coordinate (`2*I`,
  row 3) still has `im(a).is_zero == False` (`coord_verdict == 0`), so
  `any_triggering` is True and the raise is preserved (confirmed by running the
  patched repo).
