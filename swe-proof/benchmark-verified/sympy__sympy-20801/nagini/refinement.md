# refinement.md — sympy__sympy-20801

The operation-by-operation correspondence between `model.py`'s implementation
(the `float_equals` impl region and the deep `is_*` predicates in the `pure`
region) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement), **A** (axiomatized callee — **A-consumed**, the proof uses the
axiom's `Ensures`; or **A-reference**, a deep model validated == the real callee
by axiom_check.py / G-AX), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The behavioural hunk — `Float.__eq__` (`sympy/core/numbers.py:1383`)

The gold patch relocates one two-line block. It DELETES, from immediately after
the sympify preamble (between `numbers.py:1388` and the `isinstance(other,
Boolean)` test):

```
-        if not self:
-            return not other
```

and RE-INSERTS the identical block after all the boolean/number branches, just
before the final `return False`:

```
         ompf = other._as_mpf_val(self._prec)
         return bool(mlib.mpf_eq(self._mpf_, ompf))
+        if not self:
+            return not other
         return False    # Float != non-Number
```

The dispatch order therefore changes from

  `[zero-short-circuit] → Boolean → NumberSymbol → Float → Rational → Number → return False`

to

  `Boolean → NumberSymbol → Float → Rational → Number → [zero-short-circuit] → return False`.

| # | model.py impl op (`float_equals`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A0 | (no node) | `other = _sympify(other)` / `except SympifyError: return NotImplemented` (`numbers.py:1385-1388`) | I (untouched preamble) | the sympify preamble precedes the relocated block and is unchanged by the patch; the modeled domain is "sympification succeeded" (mapping.md §2). No tested operand triggers `NotImplemented`. |
| A1 | parameters `self_is_zero, kind, other_truthy, numeric_eq` | `self` (a `Float`) and `other` (an already-sympified object) | R | `self_is_zero == (not self)`; `kind` = the operand classification by the exact `isinstance`/`is_*` facets, in dispatch order; `other_truthy == bool(other)`; `numeric_eq` = the kind-proper numeric sub-result (mapping.md §2). |
| A2 | `if kind == 0: return False` | `if isinstance(other, Boolean): return False` (`numbers.py:1391-1392`) | R + I | `kind == 0` ⟺ `isinstance(other, Boolean)`; the verdict `False` is the identical concrete result. This branch's NEW POSITION (before the zero short circuit) is the whole content of the fix. |
| A3 | `if kind == 1: return False` | `if other.is_NumberSymbol: if other.is_irrational: return False` (`numbers.py:1393-1395`) | R + I | `kind == 1` ⟺ `other.is_NumberSymbol and other.is_irrational`; verdict `False`. |
| A4 | `if kind == 2: return numeric_eq` | `other.is_NumberSymbol` (not irrational) → `return other.__eq__(self)` (`numbers.py:1396`) | R | `kind == 2` ⟺ a `NumberSymbol` not known irrational (`is_irrational` falsy); the delegated equality is the unchanged sub-result carried as `numeric_eq`. Reachable: `Catalan`, `EulerGamma` have `is_irrational is None`, so they take this branch (mapping.md §2); axiom_check.py exercises them. |
| A5 | `if kind == 3: return numeric_eq` | `if other.is_Float: return self._mpf_ == other._mpf_` (`numbers.py:1397-1400`) | R | `kind == 3` ⟺ `other.is_Float`; the exact mpf compare is the unchanged sub-result carried as `numeric_eq`. |
| A6 | `if kind == 4: return numeric_eq` | `if other.is_Rational: return other.__eq__(self)` (`numbers.py:1401-1402`) | R | `kind == 4` ⟺ `other.is_Rational`; the delegated equality carried as `numeric_eq`. |
| A7 | `if kind == 5: return numeric_eq` | `if other.is_Number: ompf = other._as_mpf_val(self._prec); return bool(mlib.mpf_eq(self._mpf_, ompf))` (`numbers.py:1403-1410`) | R | `kind == 5` ⟺ `other.is_Number` (and none of the prior); the mpf-tuple compare carried as `numeric_eq`. |
| A8 | `if self_is_zero: return not other_truthy` (the LAST conditional) | `if not self: return not other` re-inserted at `numbers.py:1411` (post-patch) | R + I | `self_is_zero` ⟺ `not self`; `not other_truthy` ⟺ `not other`. Concrete control flow and result identical to the gold block; only its POSITION (now after the dispatch) differs from pre-patch — which is the relocation the patch performs. |
| A9 | final `return False` | `return False    # Float != non-Number` (`numbers.py:1412`) | I | identical fall-through verdict. |
| A10 | `Requires(MustTerminate(1))` (termination obligation, pre-conditions region) | the whole post-patch `Float.__eq__` body: a bounded, loop-free decision that returns a verdict on every in-domain operand | R | total-correctness obligation, not a value op. Nagini verifies partial correctness by default, so without it a diverging impl (`while True: pass`) satisfies every value postcondition vacuously while its faithful real patch hangs every Float equality test (the audit's atk_7 exhibited exactly this verify-but-wrong break). The real method is straight-line (no loop, no recursion), so it discharges `MustTerminate(1)` trivially — the obligation is faithful, not spec-too-strong. |

The discriminating content of the change — deciding the truth-value case BEFORE
the zero short circuit — lives in the ORDER of A2 vs A8 in the impl region. The
postcondition `Implies(is_truth_value(kind), Result() == False)` pins it: it
must hold even when `self_is_zero` and `other` is falsy. `model_prepatch.py`
reproduces the pre-patch order (A8 moved to the FRONT of the impl, before A2),
and **fails** exactly that postcondition (for `kind == 0`, `self_is_zero ==
True`, `other_truthy == False` it returns `not False == True ≠ False`) — the
spec sensing the change (G-DIFF):

```
model_prepatch.py:74: Postcondition of float_equals might not hold.
Assertion Implies(is_truth_value(kind), (Result() == False)) might not hold.
```

For the issue's witness `S(0.0) == S.false`: `self_is_zero == True` (a zero
float), `kind == 0` (`S.false` is a `Boolean`), `other_truthy == False`. Pre-patch
the zero short circuit fires first and returns `not S.false == True` (the
reported wrong result); post-patch the `kind == 0` case fires first and returns
`False` (the desired result, matching `S.false == S(0.0)` and `S(0) == S.false`).

## B. No second prepatch needed

There is a single independently-fixed behaviour (the position of the zero short
circuit relative to the truth-value/number dispatch); one `model_prepatch.py`
exercises it. The numeric sub-decisions and the sympify preamble are not
changed, so they are not separately modeled as fixed behaviours.

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R or I. There is no axiomatized callee: the relocated block
calls nothing Nagini cannot express, and the surrounding numeric comparisons are
UNCHANGED sub-results carried opaquely (R, not A — the proof consumes no axiom
`Ensures`). The one operation that genuinely *changed* — the dispatch ORDER — is
modeled **deeply** (the explicit ordered conditionals in the impl region and the
ordered `is_*` predicates in the `pure` region), and the deep model is validated
== the real `Float.__eq__` by axiom_check.py / G-AX (an **A-reference**, not a
consumed axiom).

## D. verify(model) ⇒ resolved

`float_equals` verifies only if a truth-value operand yields `False` regardless
of the float being zero (A2 before A8), the irrational-constant operand yields
`False` (A3), each numeric kind yields its numeric-equality decision (A4–A7),
an otherwise-uncategorised operand matches only a zero float, by negating
its truth value (A8), else `False` (A9), and the decision TERMINATES on every
in-domain input (A10 — `Requires(MustTerminate(1))`, ruling out diverging
implementations that would satisfy the value clauses vacuously). By R (`self_is_zero ↔ not self`,
`kind ↔` the `is_*` dispatch, `other_truthy ↔ bool(other)`, `numeric_eq ↔` the
kind-proper unchanged sub-result) the verified function equals the gold
`Float.__eq__` on the tested operands; by G-AX the deep dispatch model equals
the real `Float.__eq__` over the operand battery (A-reference). Therefore a
model satisfying this spec, refined by the map above, is the gold patch up to
type refinement — and the gold patch resolves (G-RESOLVE). The only trust point
is refinement fidelity (this document, G-EQ); there is no axiom trust point.
