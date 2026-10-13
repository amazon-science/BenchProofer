# refinement.md — django__django-13794

The operation-by-operation correspondence between `model.py`'s implementation
(`forward_combine` and `reverse_combine`) and `patch.diff` (the gold patch). Each step is
tagged **R** (type refinement), **A-consumed** (proof uses an axiom's
`Ensures`), **A-reference** (a deep model validated == the real callee by
axiom_check.py / G-AX), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit`, the
real correctness oracle, G-RESOLVE).

## A. The left-operand site — `__add__` (`django/utils/functional.py:179`)

Gold hunk:
```
+        def __add__(self, other):
+            return self.__cast() + other
```

| # | model.py impl op (`forward_combine`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `realized: List[int]` | `self.__cast()` | R | `__cast()` forces the proxy and returns its realized value; the patch does not change it, so its result is the modelled read-only input. `str` ↔ `List[int]` code points (mapping.md §2, §3). |
| A2 | parameter `other: List[int]` | `other` argument | R | `str` ↔ `List[int]` code points (mapping.md §2). |
| A3 | the loop building `result` so that `ToSeq(result) == ToSeq(realized) + ToSeq(other)` (copy `realized`, then append `other`) | the `+` in `self.__cast() + other` | A-reference + R | the changed operation is the binary `+`, modelled **deeply** as `PSeq[int]` concatenation (the two-phase append loop). There is no consumed axiom. The deep model is validated **== the real method** out-of-band: axiom_check.py (G-AX) builds a live `lazy()` proxy and asserts the real `__add__` yields exactly `realized ++ other` on strings and on the integer F2P case. By R (`str` `+` ↔ `PSeq` `+`) the loop equals `self.__cast() + other`. |
| A4 | `return result` | `return ...` | I | return the produced value. |

## B. The reflected site — `__radd__` (`django/utils/functional.py:182`)

Gold hunk:
```
+        def __radd__(self, other):
+            return other + self.__cast()
```

| # | model.py impl op (`reverse_combine`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | parameter `realized: List[int]` | `self.__cast()` | R | as A1. |
| B2 | parameter `other: List[int]` | `other` argument | R | as A2. |
| B3 | the loop building `result` so that `ToSeq(result) == ToSeq(other) + ToSeq(realized)` (copy `other`, then append `realized`) | the `+` in `other + self.__cast()` | A-reference + R | the changed operation is the binary `+` with operands in **reflected order**, modelled deeply as `PSeq[int]` concatenation `other ++ realized`. Validated == the real `__radd__` by axiom_check.py (G-AX). By R the loop equals `other + self.__cast()`. |
| B4 | `return result` | `return ...` | I | return the produced value. |

The operand ORDER is the discriminating content: `__add__` puts the realized
value first, `__radd__` puts `other` first. The reflected method exists so that
`other + proxy` succeeds when `type(other).__add__` returns `NotImplemented`
(the F2P `test_add08`: `'string' + gettext_lazy('lazy') == 'stringlazy'`, and
the integer round of `test_lazy_add`: `4 + proxy_5` dispatching to
`proxy_5.__radd__`).

## C. The pre-patch image and the failing clause (G-DIFF)

Pre-patch, `__proxy__` has no `__add__`/`__radd__`; `str.__add__` /
`int.__add__` return `NotImplemented` against the proxy, the binary `+` raises
`TypeError`, and the `add` template filter's `except Exception: return ''`
collapses the result to the empty string. Both `model_prepatch.py` (reverts
`forward_combine`) and `model_prepatch_2.py` (reverts `reverse_combine`) reproduce that by
returning the empty sequence `[]`, and each **fails** its postcondition
`ToSeq(Result()) == ...` — exactly the spec sensing each independently-fixed
behaviour. Two prepatch variants, one per added method, because the two methods
fix two independently-observable behaviours (left-operand vs reflected `+`):
`test_add09` (both operands lazy → left proxy's `__add__`) and `test_add08`
(string + lazy → proxy's `__radd__`).

## D. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — the proxy's participation in `+` — is modelled **deeply** (the
spelled-out concatenation folds in the two impl regions), not hidden behind an
axiom about the function under change. There is **no consumed `@ContractOnly`
axiom**: the only callee the patched methods invoke is the unchanged `__cast()`,
whose result is the R-refined input `realized`. The deep concatenation model is
the A-reference that G-AX validates against the real `__add__`/`__radd__`.

## E. verify(model) ⇒ resolved

`forward_combine` / `reverse_combine` verify only if their output equals the exact ordered
concatenation (`realized ++ other` resp. `other ++ realized`). By R
(`str`/`int` `+` ↔ `PSeq` `+`, `__cast()` ↔ `realized`) the verified methods
equal `self.__cast() + other` resp. `other + self.__cast()` on the tested
inputs; by G-AX the deep concatenation model equals the real patched methods
(A-reference). Therefore a model satisfying this spec, refined by the map above,
is the gold patch up to type refinement — and the gold patch resolves
(G-RESOLVE). The single trust point is refinement fidelity (this document,
G-EQ) plus the executable deep-model check (G-AX); there is no axiom-soundness
trust point because there is no consumed axiom.
