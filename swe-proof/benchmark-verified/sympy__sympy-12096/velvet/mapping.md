# mapping.md — sympy__sympy-12096

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = d7c3045115693e887bcd03599b7ca4650ac5f2cb`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and gives
the provenance of each axiom.

Repo file under change: `sympy/core/function.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `evaluateArgs (prec : Nat) (args : List Term)` | the argument-sequence preparation of `Function._eval_evalf`'s `_imp_` fallback branch — `sympy/core/function.py:510` (the `Float(self._imp_(...), prec)` call) | the modeled changed operation: numeric pre-evaluation of the arguments before they are handed to the function's numerical implementation |
| `Term` *(opaque type axiom)* | `sympy.core.expr.Expr` (a SymPy expression / argument; `self.args[k]` is an `Expr`) | one argument carried into a numerical evaluation; only its numeric evaluation is observed |
| `termDefault` *(opaque constant)* | a default `Expr` (out-of-range probe sentinel; no repo counterpart in the patched line) | harmless default for the total-indexing model; never observed on a real run (indices are always in range) |
| `numEval` *(opaque axiom — A-consumed)* | `Expr.evalf` bound method — `Basic.evalf` (`sympy/core/evalf.py`), called as `i.evalf(prec)` (`function.py:510` post-patch) | UNCHANGED per-argument numerical evaluator: `arg.evalf(prec)` |
| `numEvalSeq (prec) (args : List Term)` *(deep model — A-reference)* | the list comprehension `[i.evalf(prec) for i in self.args]` (`function.py:510` post-patch) | pure spec: numerically evaluate the whole argument sequence; deep model validated `numEvalSeq == real comprehension` by axiom_check.py (G-AX), NOT a consumed equational axiom |

The pre-patch expression this change replaces (refinement audit only, not in the
consumer spec view): `self._imp_(*self.args)` (`function.py:510`) — the arguments
`self.args` were spliced into `_imp_` **verbatim**, with no per-argument
`evalf`, so a composite argument (e.g. `f(2)` inside `f(f(2))`) reached `_imp_`
unevaluated and the outer `evalf` could not numerically reduce it.

The surrounding context is UNCHANGED by the patch and out of scope of the
modeled operation: the mpmath-name lookup (`function.py:500-506`), the
`self._imp_` callable resolution and its invocation `self._imp_(*...)`, and the
`Float(..., prec)` wrapping (`function.py:510`). The patch alters ONLY the
argument list spliced into `_imp_`: `*self.args` → `*[i.evalf(prec) for i in
self.args]`.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types. A wrong entry surfaces as spurious
G-CONF disagreements (the falsifiability the plan §4 trust statement refers to).

| repo reality | Lean carrier | bijection |
|---|---|---|
| the argument sequence `self.args` (a tuple of `Expr`) | `List Term` | the `k`-th `Expr` argument ↔ the `k`-th `List` element, by position; `len(self.args)` ↔ `args.length`; empty ↔ `[]` |
| one argument `Expr` | opaque Lean `Term` | object identity / `Expr.__eq__` ↔ Lean `Eq`; only its `evalf(prec)` numeric evaluation is observed (mapping.md §3) |
| the requested working precision `prec` (a non-negative `int`) | `Nat` | Python `int prec ≥ 0` ↔ Lean `Nat`; identity |
| `i.evalf(prec)` (an `Expr`, a `Float` once numeric) | `numEval i prec : Term` | Python evaluated `Expr` ↔ the Lean opaque value returned by `numEval`; observed by `Expr.__eq__` |

The patched call site is `Float(self._imp_(*ARGS), prec)`. The patch changes only
`ARGS`: from `self.args` (pre) to `[i.evalf(prec) for i in self.args]` (post).
The downstream `self._imp_(*ARGS)` application and the `Float(..., prec)` wrapper
are unchanged by the patch (mapping.md §1) and observationally identical given
the same `ARGS`, so only the construction of `ARGS` is modeled; `_imp_` and
`Float` are identity under refinement and omitted from the carrier.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `numEvalSeq` / `numEval` deep model ↔ the post-patch comprehension (A-reference)
The changed operation is modeled **deeply** by `numEval`/`numEvalSeq` (axioms +
pure region); there is **no consumed equational axiom about the function under
change** (`_eval_evalf`). The post-patch source (`sympy/core/function.py:510`):

```python
return Float(self._imp_(*[i.evalf(prec) for i in self.args]), prec)
```

`numEval a prec` is exactly the per-element rule `i.evalf(prec)`; `numEvalSeq` is
the front-recursive map of `numEval` over the list, i.e. exactly the list
comprehension `[i.evalf(prec) for i in self.args]`. Because each argument is
evaluated independently and order is preserved, the front-recursive fold equals
the comprehension element-wise (length and order preserved — `numEvalSeq_length`).

**Soundness check (G-AX):** `axiom_check.py` builds real argument sequences from
sympy expressions (plain numbers, composite numeric expressions, and — the
issue's witness — applied implemented-functions such as `f(2)` whose `evalf`
genuinely changes the term) and asserts `numEvalSeq(prec, args) == [a.evalf(prec)
for a in args]` (A-reference) over boundary + randomized cases. Exit 0 iff sound.

### 3.2 `numEval` ↔ `Expr.evalf` (A-consumed, opaque)
**Callee:** the bound method `i.evalf(prec)` — `Basic.evalf` (`sympy/core/
evalf.py`), UNCHANGED by the patch. Modeled by an **opaque** `axiom numEval :
Term → Nat → Term` — the weakest sufficient contract is none (directive 7): the
proof only needs that the SAME evaluator is applied to each argument in order,
never any equational fact about the value it returns. Used inside the deep model
`numEvalSeq`.

**Soundness check (G-AX):** `axiom_check.py` confirms `evalf(prec)` is a total
`Expr × prec -> Expr` on every fuzzed argument, and exhibits the load-bearing
witness — there exist arguments `a` with `a.evalf(prec) != a` (e.g. `f(2)` for an
implemented `f = x**2`, which evaluates to `4.0`, or any composite numeric
expression), so the per-argument evaluation genuinely changes the result (the
bug). Imports only sympy (the same package the patch lives in).

### 3.3 `termDefault` ↔ default `Expr` (opaque sentinel)
**Value:** a default `Expr` used only as the total-indexing sentinel
(`args[i-1]!`). It has no counterpart in the patched line and is never observed
on a real run, because the loop only indexes in range (`0 < i ≤ args.length`).
Left fully opaque (directive 7). Not exercised by G-AX or G-CONF.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`12096`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates `numEval`/`numEvalSeq` (the R/I per-element-map ops) to Python and
leaves the A-tagged callee as the REAL repo callee: `numEval` → `Expr.evalf`. The
oracle is the post-patch argument list `[i.evalf(prec) for i in self.args]`
applied to a real applied-`Function` expression's `args`. Shadow and oracle share
the unchanged `_imp_`/`Float` context, so the test isolates the R/I evaluation
map of the arguments.
