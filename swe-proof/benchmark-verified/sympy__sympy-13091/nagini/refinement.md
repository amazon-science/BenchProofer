# refinement.md — sympy__sympy-13091

The operation-by-operation correspondence between `model.py`'s implementation
(the `sym_eq` and `sym_ne` impl regions, with the deep model `op_eq` in the
pure region) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement), **A** (axiomatized callee — split into **A-consumed**, where the
proof uses an axiom's `Ensures`, and **A-reference**, where a deep model is
validated == the real callee by axiom_check.py / G-AX), or **I** (identical
concrete operation). The claim: *any implementation that verifies against this
frozen spec, refined per the map below, is behaviourally equal to the gold
patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

The gold patch is one delta replicated across ~30 sites in many files; there
are exactly **two distinct behavioural changes**, modeled as the two contracted
functions `sym_eq` and `sym_ne`.

## A. The equality delta — `__eq__` returns the delegation sentinel

Representative gold hunk (`sympy/core/basic.py`, `Basic.__eq__`, line 316; the
same edit recurs in `Float`/`Rational`/`NumberSymbol.__eq__` in
`sympy/core/numbers.py:1261,1722,3342`):
```
             try:
                 other = _sympify(other)
             except SympifyError:
-                return False    # sympy != other
+                return NotImplemented
```

| # | model.py impl op (`sym_eq`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `sympifiable: bool` | the `try: other = _sympify(other) except SympifyError` guard | R | `not sympifiable` ↔ `_sympify` raised `SympifyError` (the right-hand object is a foreign / incomparable peer). mapping.md §2. |
| A2 | parameter `content_equal: bool` | the downstream content comparison (`self._hashable_content() == other._hashable_content()` / `mlib.mpf_eq(...)` / `is`-checks) reached only when `_sympify` succeeded | R | `content_equal` ↔ the coerced peer's content equals `self`. mapping.md §2. |
| A3 | `if not sympifiable: return EQ_NI()` | `except SympifyError: return NotImplemented` | R + I | the value returned on the foreign-peer branch is the delegation sentinel `NotImplemented` ↔ `EQ_NI` (the int-code bijection, mapping.md §2). This is **the** change in this hunk: pre-patch returned `False` (↔ `EQ_FALSE`). |
| A4 | `if content_equal: return EQ_TRUE(); return EQ_FALSE()` | the decided branches returning `True`/`False` (`bool(mlib.mpf_eq(...))`, `self.p==other.p and ...`, etc.) | R + I | the decided replies, unchanged by the patch; `bool` ↔ `{EQ_TRUE, EQ_FALSE}`. |

The discriminating content — `NotImplemented` (↔ `EQ_NI`) rather than `False`
(↔ `EQ_FALSE`) on the foreign-peer branch — lives in `eq_code(False, _) ==
EQ_NI()` (model) ⇔ `return NotImplemented` (real). `model_prepatch.py`
reproduces the pre-patch `return False` (the foreign-peer branch returns
`EQ_FALSE()`) and **fails** the postcondition `Result() == eq_code(sympifiable,
content_equal)` / `Implies(not sympifiable, Result() == EQ_NI())` — exactly the
spec sensing the change (G-DIFF, prepatch #1).

## B. The inequality delta — `__ne__` complements the resolved operator

Representative gold hunk (`sympy/core/basic.py`, `Basic.__ne__`, line 332; the
same edit recurs at ~25 `__ne__`/`eq`/operator sites across the patch, e.g.
`Float.__ne__` `sympy/core/numbers.py:1278`):
```
-        return not self.__eq__(other)
+        return not self == other
```

| # | model.py impl op (`sym_ne`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | `e = sym_eq(sympifiable, content_equal)` | `self.__eq__` is what the gold form `self == other` ultimately invokes on the left | R + I | the symbolic value's own three-valued reply. |
| B2 | `op_eq(e, other_answer)` | the `==` OPERATOR `self == other` (data-model dispatch over `__eq__` and the reflected method) | A-reference | the resolved `==` operator is modeled **deeply** by the spelled-out `op_eq` in the `pure` region — there is no consumed `eq_operator` axiom. The deep model is validated **== real Python `==`** out-of-band: G-AX (axiom_check.py) builds objects whose `__eq__` returns each of `True`/`False`/`NotImplemented` and asserts `op_eq` predicts `left == right` over all 3×3 reply combinations. The gold `self == other` IS that operator dispatch (mapping.md §3.1). |
| B3 | `return not op_eq(e, other_answer)` | `return not self == other` | I | boolean complement of the resolved operator. The pre-patch form was `not self.__eq__(other)` — complement of the **raw** reply, which coerces the truthy `NotImplemented` sentinel (`not NotImplemented` is `False`). |

The discriminating content — complementing the **resolved operator** rather
than the **raw method reply** — is observable exactly when `self.__eq__`
returns the sentinel (`not sympifiable`): `model_prepatch_2.py` reproduces the
pre-patch `not self.__eq__(other)` form (impl `return e == EQ_FALSE()`: only a
definite "not equal" yields `True`, mirroring `not NotImplemented == False` and
`not True == False`) and **fails** the postcondition `Result() == (not
op_eq(eq_code(...), other_answer))` — and concretely the consequence clause
`Implies(not sympifiable and other_answer != EQ_TRUE(), Result() == True)`
(the incomparable-and-unequal peer must report `!=` as `True`, but the buggy
form gives `False`). G-DIFF, prepatch #2.

## C. The one-to-many replication and the unchanged `<,>,<=,>=` sites

The gold patch also rewrites `self.__gt__(other)` → `self > other` (and the
`<`/`<=`/`>=` analogues) at several `polyclasses`/`medium` sites, and fixes the
`NumberSymbol` reflected-operator dispatch in `Float`/`Rational.__gt__` etc.
(`other.__le__(self)` → `other.__lt__(self)`). These ordering edits are the
*same kind* of "use the operator, not the bound method" refactor as the `__ne__`
delta (B) for the equality-protocol purpose, and the `NumberSymbol` reflected
fix is exercised only by `test_NumberSymbol_comparison`, which is **NOT** in
this instance's `FAIL_TO_PASS` (`["test_equality",
"test_comparisons_with_unknown_type"]`). The two F2P tests observe exactly the
equality/inequality protocol of deltas A and B (the `Foo`/`Bar` symmetry
witnesses). The ordering hunks are PASS-preserving replications of the same
operator-dispatch idea and need no separate failing prepatch: the modeled `sym_eq`
(A) and `sym_ne` (B) already pin both independently-observable F2P behaviours.

## C2. Total correctness (termination obligation)

Both contracted functions carry `Requires(MustTerminate(...))`
(`nagini_contracts.obligations`): `sym_eq` at measure 1 and `sym_ne` at
measure 2 (leaving room for its `sym_eq` sub-call). The real
`__eq__`/`__ne__` are bounded, straight-line computations that always return
a reply to the rich-comparison protocol; an implementation that diverges
(e.g. `while True: pass` on the foreign-peer branch) satisfies the value
postconditions only vacuously and is behaviourally NOT the gold patch — in
the repo it hangs the F2P tests instead of resolving them. Nagini's
obligation leak check rejects such implementations (a loop that does not
consume the termination obligation fails verification), closing the
partial-correctness gap: *verifies ⇒ terminates with the pinned reply*.

## D. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one genuinely *changed* operation
that is not a plain int/bool refinement — the `==` operator dispatch — is
modeled **deeply** (`op_eq`, an **A-reference** validated by G-AX), not hidden
behind an axiom about a function under change. There is **no consumed axiom**:
`meta.json axioms` is empty; `op_eq` is the sole deep-model reference.

## E. verify(model) ⇒ resolved

`sym_eq` verifies only if it returns the delegation sentinel `EQ_NI` (not
`EQ_FALSE`) on the foreign-peer branch (A3) — which is `return NotImplemented`.
`sym_ne` verifies only if it equals `not (self == other)` with the resolved `==`
operator (B2/B3) — which is `return not self == other`. By R (the
bool ↔ {EQ_TRUE,EQ_FALSE} and NotImplemented ↔ EQ_NI bijection, the
sympifiable/content_equal observation of `other`) the verified functions equal
the gold `__eq__`/`__ne__`; by G-AX the deep model `op_eq` equals the real
Python `==` dispatch (A-reference). Therefore a model satisfying this spec,
refined by the map above, is the gold patch up to type refinement and the
audited operator semantics — and the gold patch resolves (G-RESOLVE). The trust
points are exactly the two of PLAN §1.1: deep-model fidelity (G-AX) and
refinement fidelity (this document, G-EQ).
