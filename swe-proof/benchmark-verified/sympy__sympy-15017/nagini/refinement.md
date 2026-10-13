# refinement.md — sympy__sympy-15017

The operation-by-operation correspondence between `model.py`'s implementation
(the `array_element_count` impl region and the deep `axis_count` fold) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A-consumed** (proof uses an axiom's `Ensures`), **A-reference** (a deep model
validated == the real callee by axiom_check.py / G-AX), or **I** (identical
concrete operation). The claim: *any implementation that verifies against this
frozen spec, refined per the map below, is behaviourally equal to the gold patch
on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## R0. Precision-independence of the carrier

The modeled value is an element COUNT — the product of integer axis lengths.
Modeling axis lengths as `int` (rather than `sympy.Integer`) is sound because
the tested behaviour (`len(...)` results: 0, 1, 81, and the rank-zero `1`)
depends only on which integers multiply and the empty-product convention, both
exactly preserved by `int`. No floating point is involved (no `--float-encoding`).

## A. The element-count site — `_new`'s `_loop_size`

Gold hunk (`sympy/tensor/array/dense_ndim_array.py:152`):
```
- self._loop_size = functools.reduce(lambda x,y: x*y, shape) if shape else 0
+ self._loop_size = functools.reduce(lambda x,y: x*y, shape, 1)
```

| # | model.py impl op (`array_element_count`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `shape: List[int]` | `shape` — the sympified `Tuple` of axis lengths | R | `sympy.Tuple`/`Integer` ↔ `List[int]` axis lengths (mapping.md §2); empty `Tuple` ↔ `[]`. |
| A1b | `Requires(MustTerminate(2))` on `array_element_count`; loop `Invariant(MustTerminate(len(shape) - i + 1))` | the real `_loop_size` computation is one bounded fold (`functools.reduce`) over the finitely many axes that always returns to its caller | R | total-correctness obligation: the real operation always ANSWERS. Nagini verifies partial correctness by default, so without the obligation a diverging same-spec impl (bare self-recursion, or an endless loop) satisfies every `Ensures` vacuously — the audited G-PANEL-1 counterexample. Measure 2 lets the impl invoke the `@Pure` helpers but forbids re-invoking `array_element_count` itself; the fold loop consumes the obligation with the strictly decreasing, bounded-below measure `len(shape) - i + 1`. |
| A2 | `acc = 1` then the loop `acc = acc * shape[i]` for `i in 0..len(shape)-1`, i.e. the result is `axis_count(ToSeq(shape), len(shape))` | `functools.reduce(lambda x,y: x*y, shape, 1)` | R | the post-patch `reduce(mul, shape, 1)` is a left fold with initial value `1`; the verified loop with `acc` initialized to `1` and folded over the axes is the same left fold. `axis_count`'s defining equation (`axis_count(s,0)==1`, `axis_count(s,k)==axis_count(s,k-1)*s[k-1]`) is exactly `reduce`'s recurrence with seed `1`. The empty-product base case `axis_count(s,0)==1` mirrors `reduce(..., 1)` returning the seed on an empty `shape`. |
| A3 | result returned as the array's element count, observed via `len(...)` | `self._loop_size = …`; `NDimArray.__len__` returns `self._loop_size` | I | `__len__` is the identity `return self._loop_size` (`ndim_array.py:164-178`); the modeled count IS what `len(...)` reports. |

The discriminating content of the change — the empty (rank-zero) shape yields
count **1**, not 0 — lives in `axis_count(s, 0) == 1` (model) ⇔ the seed `1` of
`reduce(mul, shape, 1)` (real). The pre-patch `reduce(mul, shape) if shape
else 0` returns `0` for the empty shape; `model_prepatch.py` reproduces that
(`if len(shape) == 0: return 0`) and **fails** the postcondition
`Result() == axis_count(ToSeq(shape), len(shape))` (and the spelled-out
`Implies(len(shape) == 0, Result() == 1)`), which is exactly the spec sensing
the change (G-DIFF). For any non-empty shape the pre-patch fold (seed = first
axis, fold the rest) equals the post-patch fold, so the prepatch fails ONLY on
the empty-shape clause — the single observable behaviour the fix changes.

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R or I. The one operation that genuinely *changed* — the
empty-product convention of the axis-length product — is modeled **deeply**
(the spelled-out prefix-recursive `axis_count` with base case 1, consumed by the
verified loop in `array_element_count`), not hidden behind an axiom. There is no
`@ContractOnly` callee: `functools.reduce` is the standard left fold reproduced
exactly by `axis_count`'s recurrence, so there is neither an **A-consumed** axiom
nor an **A-reference** deep model to validate against a real library callee.
(Consequently there is no `axiom_check.py`; G-AX has nothing to check.)

## C. verify(model) ⇒ resolved

`array_element_count` verifies only if it RETURNS (the `MustTerminate(2)`
obligation, A1b — no diverging impl passes vacuously) and its output equals the
running product of the axis lengths with the empty-product seed 1 (A2), i.e.
`1` for the rank-zero shape and the product otherwise. By R (`Tuple`/`Integer` ↔ `List[int]`,
`reduce(mul, shape, 1)` ↔ the verified loop) the verified count equals
`functools.reduce(lambda x,y: x*y, shape, 1)`, which is assigned to
`self._loop_size` and returned verbatim by `__len__` (A3, I). Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement — and the gold patch resolves (G-RESOLVE: F2P `test_ndim_array_initiation`
now sees `len(rank_zero_array) == 1`, and the P2P `len(...)` products are
unchanged because the seed `1` is the multiplicative identity for non-empty
shapes). The sole trust point of PLAN §1.1 that applies here is refinement
fidelity (this document, G-EQ); there are no axioms (G-AX is vacuous).
