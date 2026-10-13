# refinement.md — sympy__sympy-17139

The operation-by-operation correspondence between `model.py`'s implementation
(the `transform_power` impl region) and `patch.diff` (the gold patch). Each step
is tagged **R** (type refinement), **A** (axiomatized callee — **A-consumed**
where the proof uses the axiom's contract, **A-reference** where a deep model is
validated == the real callee by axiom_check.py / G-AX), or **I** (identical
concrete operation). The claim: *any implementation that verifies against this
frozen spec, refined per the map below, is behaviourally equal to the gold patch
on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The single changed site — `_f(rv)` inside `_TR56` (`sympy/simplify/fu.py:496-522`)

Gold hunk:
```
         if not (rv.is_Pow and rv.base.func == f):
             return rv
+        if not rv.exp.is_real:
+            return rv
 
         if (rv.exp < 0) == True:
             return rv
```

| # | model.py impl op (`transform_power`) | patch.diff / gold `_f` op | tag | justification |
|---|---|---|---|---|
| A1 | `if not is_target: return 0` | `if not (rv.is_Pow and rv.base.func == f): return rv` (`fu.py:501-502`) | R | `is_target` ↔ `rv.is_Pow and rv.base.func == f`; `return 0` ↔ `return rv` (the "unchanged" branch). (mapping.md §2) |
| A2 | `if not exp.real: return 0` | `if not rv.exp.is_real: return rv` (the **added** lines) | R | `exp.real` ↔ `rv.exp.is_real is True`; `return 0` ↔ `return rv`. This is the fix: a power with a non-real exponent is returned unchanged **before** any ordering. (mapping.md §2) |
| A3 | `if order_lt_zero(exp) == True: return 0` | `if (rv.exp < 0) == True: return rv` (`fu.py:504`) | A-consumed | `order_lt_zero` is the weakest contract on the unchanged `Expr.__lt__` the dispatch needs: `Requires(e.real)` (its safe, non-raising domain — the real op raises `TypeError` on a non-real operand) and `Ensures(Result() == (e.value < 0))`. The proof CONSUMES the precondition: A2 must establish `exp.real` for this call to typecheck, which is exactly why the fix is required. (mapping.md §3.1; G-AX) |
| A4 | `if order_gt_max(exp, max) == True: return 0` | `if (rv.exp > max) == True: return rv` (`fu.py:506`) | A-consumed | same as A3 for `Expr.__gt__`: `Requires(e.real)`, `Ensures(Result() == (e.value > m))`. (mapping.md §3.1; G-AX) |
| A5 | `if exp.value == 1: return 0` | (no dedicated gold line) the first power falls into gold's `else` arm and is returned **unchanged**: for `pow` false `if rv.exp % 2: return rv` (1 is odd), for `pow` true `if not perfect_power(1): return rv` (`perfect_power(1)` is falsy) (`fu.py:510-519`) | R | gold has **no** special-cased `rv.exp == 1`; the model states the outcome explicitly as a faithful (redundant) restatement of what the odd/`pow` arms (A8/A10) already yield for value 1 — code 0 in every case. No behavioural claim beyond what gold produces. |
| A6 | `if exp.value == 2: return 1` | `if rv.exp == 2: return h(g(rv.base.args[0])**2)` (`fu.py:508-509`) | R | `exp.value == 2` ↔ `rv.exp == 2`; result code `1` ↔ the squared-base rewrite. The algebra of the rewrite is **unchanged** by this patch, so the rewritten expression is abstracted to a branch tag (mapping.md §2). |
| A7 | `if exp.value == 4: return 2` (inside the `else` arm) | `if rv.exp == 4: e = 2; ... return h(g(...)**2)**e` (`fu.py:513-514,522`) | R | the fourth-power magnitude is **always rewritten** (code 2), independent of `pow`; the rewrite algebra is unchanged so it is abstracted to the branch tag. (Gold has no special-cased `rv.exp == 1`; the first power is an odd magnitude handled by the `not pow` / `pow` arms below and returned unchanged — A5 states that outcome explicitly.) |
| A8 | `elif not pow: if exp.value % 2 == 1: return 0` | `elif not pow: if rv.exp % 2: return rv` (`fu.py:515-516`) | R | when every even power is admitted (`pow` false) an **odd** magnitude (≠2, ≠4) is returned **unchanged** (code 0) — `if rv.exp % 2: return rv` ↔ `return 0`. This is the F2P assertion `T(sin(x)**3, …, 4, False) == sin(x)**3`. |
| A9 | `elif not pow: ... return 2` (the even fall-through) | `elif not pow: ... e = rv.exp//2; return h(g(...)**2)**e` (`fu.py:515,517,522`) | R | an **even** magnitude (≠2, ≠4) under `pow` false is **rewritten** (code 2); the rewrite algebra is unchanged, abstracted to the branch tag. This is `T(sin(x)**6, …, 6, False) == (1-cos**2)**3`. |
| A10 | `else: if not is_perfect_power(exp.value): return 0; return 2` | `else: p = perfect_power(rv.exp); if not p: return rv; e = rv.exp//2; return h(g(...)**2)**e` (`fu.py:518-522`) | A-reference | a magnitude (≠2, ≠4) under `pow` true: **unchanged** (code 0) when it is not a perfect power (`if not p: return rv` ↔ `return 0`), else **rewritten** (code 2). This covers both parities (e.g. odd `9` is a perfect power → code 2; even `6` is not → code 0, the F2P assertion `T(sin(x)**6, …, 6, True) == sin(x)**6`). `is_perfect_power(n)` is the boolean the dispatch branches on; it is a *reference the deep model is validated against* by axiom_check.py / G-AX (`is_perfect_power(n) == bool(sympy.perfect_power(n))`, and `model_outcome == gold_outcome` over the full range), not an axiom the proof's value reasoning consumes. (mapping.md §3.2; G-AX) |

The discriminating content of the change — *a non-real exponent must short-
circuit to "unchanged" before any ordering is evaluated* — lives in step A2
(the added guard) feeding the precondition of A3/A4. `model_prepatch.py`
**omits** A2 and so calls `order_lt_zero(exp)` (A3) with `exp.real` possibly
false, violating its `Requires(e.real)`; it FAILS verification at exactly that
call (`model_prepatch.py:173: precondition of order_lt_zero ... e.real might not
hold`). That is the spec sensing the bug (G-DIFF): the model crash-domain
precondition mirrors the real `TypeError("Invalid comparison of complex I")`.

The post-guard dispatch (A5–A10) is the **unchanged** rewrite-selection logic of
`_f`. It is modeled deeply (not collapsed) because its arms have *different
observable outcomes* — code 0 (unchanged) vs. code 2 (rewritten) — which the F2P
test `test__TR56` directly observes: `T(sin(x)**6, …, 6, False) == (1-cos**2)**3`
(rewritten, code 2) vs. `T(sin(x)**6, …, 6, True) == sin(x)**6` (unchanged, code
0). The `pow` parameter the dispatch keys on to choose between those outcomes is
therefore part of the carrier (it is not optional abstraction: collapsing the
arms would positively mandate the wrong outcome on a tested input).

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-consumed, A-reference, or I. The operation that
genuinely *changed* is the **guard placement** (A2), modeled deeply as a
concrete `if not exp.real: return 0` whose effect — making the subsequent
ordering's `Requires(e.real)` satisfiable — is the verified property. The two
ordering predicates (A3/A4) are **unchanged** library callees the dispatch
*calls* but does not change; they are the only **A-consumed** axioms (the proof
relies on their `Requires`/`Ensures`). The perfect-power predicate (A10) is an
**A-reference**: the deep dispatch is validated to equal `bool(perfect_power)`
by axiom_check.py — the proof's value reasoning does not consume a contract on
it (it only branches on its deterministic boolean). There is no axiom about the
function under change `_f`.

## C. verify(model) ⇒ resolved

`transform_power` verifies only if (i) a non-real exponent short-circuits to
"unchanged" (postcondition `Implies(is_target and not exp.real, Result()==0)`,
established by A2) AND (ii) every ordering call is reached only on a real
exponent (the `Requires(e.real)` of A3/A4, satisfiable only because A2 precedes
them) AND (iii) the post-guard dispatch reports exactly the gold `_f` outcome on
every in-range real magnitude (A5–A10: the squared rewrite for value 2; the
fourth-power rewrite for value 4; under `pow` false an even magnitude is
rewritten while an odd magnitude — including the first power — is returned
unchanged; under `pow` true the magnitude is rewritten exactly when it is a
perfect power, else returned unchanged). By the type refinement R (mapping.md §2) the verified
dispatch equals the gold `_f` on every node: a non-real-exponent power is
returned unchanged without evaluating `rv.exp < 0`, so the `TypeError` of the
problem statement never fires, and `T(sin(x)**I, …) == sin(x)**I`,
`T(sin(x)**(2*I+1), …) == sin(x)**(2*I+1)` hold (the issue-17137 F2P
assertions). Real-exponent nodes follow the unchanged selection A3–A10, so the
F2P pow-sensitive assertions (`T(sin(x)**6, …, 6, False)` rewritten vs.
`T(sin(x)**6, …, 6, True)` unchanged) and the P2P trig-rewrite behaviour are
preserved. By G-AX the axiomatized `Expr.__lt__`/`__gt__` are sound on their
declared real domain (and genuinely raise off it), and the A-reference
`is_perfect_power` matches `bool(perfect_power)`. Therefore a model satisfying
this spec, refined by the map above, is the gold patch up to type refinement and
audited callees — and the gold patch resolves (G-RESOLVE). The trust points are
exactly the two of PLAN §1.1: axiom soundness (G-AX) and refinement fidelity
(this document, G-EQ).
