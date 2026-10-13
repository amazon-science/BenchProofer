# mapping.md — sympy__sympy-17139

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 1d3327b8e90a186df6972991963a5ae87053259d`, states the type
abstraction, and gives the provenance of each axiom (callee source + the exact
behaviour the axiom encodes).

Repo file under change: `sympy/simplify/fu.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `transform_power(is_target, exp, max, pow)` | the inner transformer `_f(rv)` inside `_TR56(rv, f, g, h, max, pow)` — `sympy/simplify/fu.py:496-522` | the modeled changed function: the per-node power-rewrite dispatch run by `bottom_up` |
| `Expon` (`.real`, `.value`) | the exponent `rv.exp` of the inspected power node — a `sympy.core.expr.Expr` | minimal carrier: only the two touched attributes (`is_real`; integer magnitude) |
| `is_target` parameter | `rv.is_Pow and rv.base.func == f` (`fu.py:501`) | whether the node is a power of the designated base function `f` (`sin`/`cos`) |
| `order_lt_zero(e)` *(axiom — A-consumed)* | `(rv.exp < 0)` — `sympy.core.expr.Expr.__lt__`, `sympy/core/expr.py:398-419` (the call at `fu.py:504`) | unchanged library ordering predicate; raises `TypeError` on a non-real operand |
| `order_gt_max(e, m)` *(axiom — A-consumed)* | `(rv.exp > max)` — `sympy.core.expr.Expr.__gt__`, `sympy/core/expr.py` (the call at `fu.py:506`) | unchanged library ordering predicate; raises `TypeError` on a non-real operand |
| `is_perfect_power(n)` *(axiom — A-reference)* | `bool(perfect_power(rv.exp))` — `sympy.perfect_power` (`sympy/ntheory/factor_.py`); the call `p = perfect_power(rv.exp); if not p` at `fu.py:518-519` | unchanged library predicate the `pow`-true arm branches on (for magnitudes of either parity); the deep model is validated == this boolean by axiom_check.py |
| `pow` parameter | the `pow` kwarg of `_TR56` threaded into `_f` (`fu.py:293,348`) | selects whether the general (≠2,≠4) arm admits every even power (`pow` false: even rewritten, odd left unchanged) or only perfect powers (`pow` true: perfect power rewritten, else left unchanged) — a parameter the unchanged dispatch keys on for two *different observable outcomes* on the same magnitude |
| result code `0/1/2` of `transform_power` | the return shapes of `_f`: `return rv` (unchanged — non-target, non-real, `<0`, `>max`, an odd magnitude under `pow` false, or a non-perfect-power magnitude under `pow` true) / `return h(g(...)**2)` (exp==2) / `return h(g(...)**2)**e` (general: exp==4, an even magnitude under `pow` false, or a perfect-power magnitude under `pow` true) | which branch fires; the *unchanged-vs-rewritten* distinction is the F2P-observable, so every observably-distinct arm of the dispatch is modeled (not collapsed) |

The gold change adds, between `fu.py:502` and the first ordering at `fu.py:504`:

```
+ if not rv.exp.is_real:
+     return rv
```

i.e. a power with a non-real exponent is returned unchanged *before* any
ordering of that exponent is evaluated. There is exactly one changed hunk.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `rv` (a `Pow` node) reaching the ordering branches | the triple `(is_target, exp, …)` | `rv.is_Pow and rv.base.func == f` ↔ `is_target`; `rv.exp` ↔ `exp`. Only nodes with `is_target` true proceed past `fu.py:501`. |
| `rv.exp` (a `sympy.Expr`) | `Expon` with `real: bool`, `value: int` | `rv.exp.is_real is True` ↔ `exp.real`; for a real *integer* exponent, `int(rv.exp)` ↔ `exp.value`. The dispatch only ever reads `value` after establishing realness, so a single integer carrier suffices for the modeled cases (`<0`, `>max`, `==1`, `==2`, `==4`, parity, and the perfect-power test). |
| `max` (the `max` kwarg, ≥ 4 in every call site: `TR5`/`TR6` default 4, `_TR56` callers) | `max: int`, `Requires(max >= 4)` | identity; the bound's only role is the `exp > max` test. |
| `pow` (the `pow` kwarg threaded into `_f`) | `pow: bool` | identity; keys the even-arm dispatch between two *observably-different* outcomes (rewrite vs. unchanged), so it MUST appear in the carrier. |
| `(rv.exp < 0) == True` truth test (`fu.py:504`) | `order_lt_zero(exp) == True` | `== True` is SymPy's idiom for "the relational evaluated to the literal truth `S.true`"; modeled as the bool the axiom returns. R/I. |
| `return` shapes of `_f` | result codes `0` (unchanged) / `1` (exp==2 rewrite) / `2` (general rewrite) | the F2P/P2P observable is *whether and how* the node is rewritten; the algebraic value of a rewrite is unchanged by this patch, so it is abstracted to a branch tag — but the *unchanged-vs-rewritten* distinction is NOT abstracted (it is the F2P observable), so every dispatch arm with a distinct outcome is modeled. |

The exponent's symbolic *rewrite value* is not modeled: the patch changes only
the *guard* (non-real ⇒ leave unchanged), never the algebra of the rewrite, so
the carrier need only distinguish real-vs-non-real and (when real) the integer
magnitude the dispatch keys on. The unchanged dispatch that follows the guards,
however, selects between *unchanged* and *rewritten* depending on the magnitude
AND `pow` (via the perfect-power test); because the F2P test `test__TR56`
asserts both outcomes for the SAME magnitude (`sin(x)**6` with `pow` False vs.
True), those arms are modeled deeply (A5–A10 in refinement.md) rather than
collapsed — collapsing them would positively mandate the wrong result code on a
tested input.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `order_lt_zero` ↔ `Expr.__lt__` and `order_gt_max` ↔ `Expr.__gt__` (A-consumed)
**Callee:** `sympy.core.expr.Expr.__lt__` / `__gt__` (`sympy/core/expr.py:398`
and `:374`). Source of the raise (every comparison dunder, lines 336/359/382/406):

```python
def __lt__(self, other):
    ...
    for me in (self, other):
        if me.is_complex and me.is_extended_real is False:
            raise TypeError("Invalid comparison of complex %s" % me)
        ...
```

So `exp < 0` (and `exp > max`) is **well-defined (non-raising) only when the
exponent is real**; on a genuinely complex exponent (`I`, `2*I + 1`, `2 + 3*I`)
it raises `TypeError("Invalid comparison of complex ...")` — exactly the
traceback in the problem statement (`fu.py:504` → `expr.py:406`).

The model encodes this as the axioms' precondition `Requires(e.real)`: the
operation may only be invoked on a real exponent. The axioms' `Ensures`
(`Result() == (e.value < 0)` / `(e.value > m)`) state the value the real
ordering yields on a real integer exponent. These are the **weakest** contracts
the dispatch needs: it tests only the sign and the magnitude-vs-`max` of a real
exponent. We do NOT axiomatize the function under change (`_f`), nor claim any
value on the non-real domain the real callee refuses.

**Flag/representation dependency:** the predicate `is_real` here is SymPy's
three-valued assumption; the model treats `exp.real == True` as "definitely
real" (the only case the dispatch proceeds on) and `not exp.real` as the union
of "definitely non-real" and "unknown" — both of which the gold guard
`if not rv.exp.is_real: return rv` returns unchanged. (`rv.exp.is_real` is
falsy — `False` or `None` — for the F2P complex inputs.)

**Soundness check (G-AX):** `axiom_check.py` imports only `sympy` (the library
the patch lives in) and:
  - runs the REAL `(exp < 0) == True` / `(exp > max) == True` on the eight
    non-real exponents (`I`, `2*I+1`, `3*I`, `2+3*I`, `1-I`, `-I`, `I/2`,
    `5*I-7`) and asserts each RAISES `TypeError` — confirming the `Requires(
    e.real)` domain is both sound (the model never claims a value there) and
    necessary (the operation is genuinely undefined there);
  - runs the REAL ordering on 42 boundary + 20 000 fuzz real integer exponents
    against integer bounds `{4,6,10}` (and random) and asserts agreement with
    `value < 0` / `value > m` — the axioms' Ensures.
Exit 0 iff every observation matches.

### 3.2 `is_perfect_power(n)` ↔ `bool(perfect_power(n))` (A-reference)
**Callee:** `sympy.perfect_power` (`sympy/ntheory/factor_.py`); gold `_f` calls
`p = perfect_power(rv.exp); if not p: return rv` at `fu.py:518-519` (on the
`pow`-true arm, for a magnitude of either parity). The model's deep dispatch
branches on the boolean `is_perfect_power(exp.value)`; the model claims no value
beyond that boolean.

This is an **A-reference** (not A-consumed): the proof does not consume a value
contract on it (the `@Pure @ContractOnly` callee gives only determinism, which
the dispatch needs to branch). Its correspondence to the real predicate is what
G-AX validates. The dispatch consults it on real Pow exponents that have passed
every guard — positive, `≠1`, `≠2`, `≠4` — and, under `pow` true, of EITHER
parity (gold's `pow` arm does not pre-filter on parity), so the smallest
reachable magnitude is `3` (e.g. `sin(x)**3` with `pow` true → `perfect_power(3)`
falsy → unchanged). A `Pow` with `exp==0` does not exist (`x**0` simplifies to
`1`, so `rv.is_Pow` is false there), and `exp==1` is short-circuited before the
dispatch reaches the callee.

**Domain note (version-sensitive):** in sympy 1.5 (the pinned eval container)
`perfect_power(n)` raises `ValueError('expecting positive n')` for `n == 0`; the
A-reference domain is therefore the positive magnitudes the dispatch actually
consults (`n ≥ 1`), matching the model's `Requires(n >= 0)` together with the
dispatch's own guards (which never reach it with `n == 0`).

**Soundness check (G-AX):** `axiom_check.py` asserts
`is_perfect_power(n) == bool(perfect_power(n))` on 23 boundary magnitudes
(including the F2P-relevant `6` → unchanged-under-pow, `8` → rewritten-under-pow,
and perfect/non-perfect powers `9,16,25,27,32,36,49,64,128`) plus 20 000 fuzz
magnitudes in `[1,200]`, and a FAITHFULNESS cross-check that the modeled dispatch
outcome (`model_outcome`) equals the REAL gold inner-transformer outcome
(`gold_outcome`, transcribed branch-for-branch from `_f`) over the whole modeled
exponent range (`value ∈ [1,m]`, `m ∈ {4,6,10,20,30}`, both `pow` values), and on
every F2P-test exponent shape (`sin(x)**3` False⇒unchanged, `sin(x)**6`
False⇒rewrite / True⇒unchanged, `sin(x)**8` True⇒rewrite, `sin(x)**10` over-max
⇒unchanged). The cross-check compares against the live dispatch, NOT a hardcoded
answer key.

Imports only `sympy`. Exit 0 iff every observation matches. (Runs in-container
against the eval interpreter for G-AX; confirmed RC=0 in the pinned sympy-1.5
image.)
