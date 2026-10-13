# refinement.md — sympy__sympy-12096

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`evaluateArgs` `do` block, the deep `numEvalSeq`/`numEval` model, and the opaque
`numEval` / `termDefault` axioms) and `patch.diff` (the gold patch). Each step is
tagged **R** (type refinement), **A** (axiomatized callee — **A-consumed** where
the proof uses the axiom, **A-reference** where a deep model is validated == the
real callee by G-AX), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. Claim: any impl
verifying against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The `_imp_` fallback branch — `Function._eval_evalf` (`core/function.py:510`)

Gold hunk:
```
-                return Float(self._imp_(*self.args), prec)
+                return Float(self._imp_(*[i.evalf(prec) for i in self.args]), prec)
```

The only behavioural change is the argument list spliced into `self._imp_(...)`:
the bare `self.args` becomes `[i.evalf(prec) for i in self.args]`, i.e. each
argument is numerically evaluated to the working precision before being handed
to the numerical implementation. The `self._imp_(*...)` application and the
`Float(..., prec)` wrapper are byte-unchanged. The modeled operation is exactly
the construction of that per-argument-evaluated list.

| # | Solution.lean impl op (`evaluateArgs`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `args : List Term` | `self.args` (`function.py:510`) | R | the argument tuple of `Expr` objects ↔ `List Term`, by position (mapping.md §2). G-CONF builds it via `list(expr.args)`. |
| A2 | parameter `prec : Nat` | `prec` (`_eval_evalf(self, prec)`) | R | the non-negative working precision `int` ↔ `Nat` (mapping.md §2); identity. |
| A3 | `result = numEvalSeq prec args`: the per-element map `numEval _ prec`, computed by the backward `while` fold | the comprehension `[i.evalf(prec) for i in self.args]` | A-reference + I | the changed operation is modeled **deeply**: `numEvalSeq`/`numEval` (axioms + pure region) and the verified loop ARE the per-element numeric evaluation. No consumed equational axiom about the function under change. The fold ops (`numEval a prec`, `::`, the loop) are **I** (concrete, transliterated by G-CONF); the equality of that deep model to the real comprehension is the **A-reference** G-AX validates (mapping.md §3.1). |
| A4 | `numEval a prec` per element | `i.evalf(prec)` per element | A-consumed + I | the per-argument numerical evaluation. `numEval` is the OPAQUE axiom over the UNCHANGED callee `Expr.evalf` (mapping.md §3.2). The proof consumes it only as the same total evaluator applied per element; G-AX confirms `evalf(prec)` is total and that it genuinely changes composite arguments (the load-bearing witness). |
| A5 | `out` returned (`List Term`), `out.length = args.length` | the list spliced as `*[...]` into `self._imp_(...)`; downstream `_imp_`/`Float` unchanged | R | the evaluated list is the argument vector passed to the unchanged `self._imp_(*...)`; `_imp_` and `Float(..., prec)` are byte-identical pre/post (mapping.md §1, §2) and identity under refinement, so only the argument list is modeled. The length/order guarantee (`numEvalSeq_length`) pins the arity `_imp_` is called with. |

Discriminating content of the change — a **composite numeric argument** (e.g.
`f(2)` inside `f(f(2))`, which evaluates to `4.0`) is replaced by its numeric
evaluation, NOT passed through verbatim — lives in `numEval a prec` per element
(model) ⇔ the `i.evalf(prec)` step (real). The pre-patch branch spliced
`self.args` verbatim; `Solution_prepatch.lean` reproduces that (`result := a ::
result`) and **fails** `out = numEvalSeq prec args` precisely on the clause
`args[i-1]! = numEval args[i-1]! prec` (G-DIFF), which is false exactly when an
argument's numeric evaluation differs from the argument itself — the bug the F2P
test `test_issue_12092` exercises via `f(f(2)).evalf() == Float(16)`.

## B. No second site

The patch touches a single expression in a single branch of a single function;
there is no second independently-fixed behaviour. The only failing prepatch is
site A's.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, A, or I. The one operation that genuinely *changed* — the
per-argument numeric evaluation of the argument sequence — is modeled **deeply**
(the spelled-out fold `numEvalSeq`/`numEval`, step A3, an A-reference + I), not
hidden behind an axiom about the function under change (`_eval_evalf`). The only
consumed axiom, `numEval` (step A4), covers an **unchanged** callee
(`Expr.evalf`); it is opaque (weakest contract, directive 7). `termDefault` is an
opaque indexing sentinel never observed on a real run (mapping.md §3.3).

## D. verify(Solution) ⇒ resolved

`evaluateArgs` verifies only if its output equals the exact per-element numeric
evaluation `numEvalSeq` (A3): every argument numerically evaluated to the target
precision, in order, with length preserved (A4, A5). By R (`List Term` ↔
`self.args`; `prec` ↔ `Nat`; the `_imp_` application and `Float` wrap are
unchanged identities) the verified operation equals the patched argument list
`[i.evalf(prec) for i in self.args]` spliced into `self._imp_(...)` on real
implemented-function expressions; by G-AX the deep model `numEvalSeq` equals the
real comprehension (A-reference) and `Expr.evalf` meets the opaque axiom's usage
(A-consumed); by G-CONF the R/I transliteration of the fold agrees with
`patch.diff`'s behaviour on the modeled argument lists. Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement and audited callees — and the gold patch resolves (G-RESOLVE). Trust
points are exactly the two of plan §1.1: axiom soundness (G-AX) and refinement
fidelity (this doc, G-EQ + G-CONF).
