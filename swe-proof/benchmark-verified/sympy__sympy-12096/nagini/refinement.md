# refinement.md — sympy__sympy-12096

The operation-by-operation correspondence between `model.py`'s implementation
(the `eval_implemented` impl region, the deep fold `eval_seq`, and the concrete
implementation `imp`) and `patch.diff` (the gold patch). Each step is tagged
**R** (type refinement), **A-consumed** (the proof uses an axiom's `Ensures`),
**A-reference** (a deep model validated == the real callee by axiom_check.py /
G-AX, NOT consumed), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The site — `Function._eval_evalf` (`sympy/core/function.py:507`)

Gold hunk (the `_imp_` branch, taken when the function has no mpmath
counterpart but carries a user implementation):
```
- return Float(self._imp_(*self.args), prec)
+ return Float(self._imp_(*[i.evalf(prec) for i in self.args]), prec)
```

The behavioural change: each argument is **evaluated to a number first**
(`i.evalf(prec)`) before the implementation is applied. When an argument is
itself an implemented-function application, this recurses (`i.evalf` re-enters
`_eval_evalf` on the inner application). The pre-patch passed `self.args`
directly, so an argument that was an unevaluated application stayed symbolic;
`self._imp_(<symbolic>)` is not a number, `Float(...)` raises
`TypeError`/`ValueError`, and the `except` clause `return`s `None` — the object
is left unevaluated.

### Type / structure abstraction (mapping.md §2)
A nested chain of `_imp_` applications over a numeric leaf is abstracted by
`(leaf: int, layers: List[int])`: `leaf` is the innermost numeric argument, and
`len(layers)` is the nesting depth (one element per surrounding application;
element values are irrelevant — only the count carries the structure). A number
is modelled as `int`; "unevaluated / `None`" is modelled as `Optional[int]`'s
`None`.

### Contract domain (exact-float window)
The real patched callee returns a `Float` rounded to ~15 significant digits, so
the exact-integer A-reference `eval_seq` agrees with it bit-for-bit only while
the reduced value is exactly representable. The contract therefore declares its
domain explicitly: `Requires(leaf >= 0)` and
`Requires(eval_seq(leaf, ToSeq(layers)) < 1e14)` (a non-negative leaf whose
inside-out reduction stays inside the exact-representation window). This is the
intended scope of the type abstraction "number ↔ exact `int`": it holds exactly
where the modelled `int` reduction equals the real `Float` reduction. The
out-of-band check `axiom_check.py` (G-AX) mirrors this precondition EXACTLY
(`within_precision(leaf, n) == (leaf >= 0 and eval_seq(leaf, n) < 1e14)`), so
the A-reference is validated on precisely the declared domain — neither broader
(which would falsely over-claim, e.g. `leaf=11, layers len 4`) nor narrower. The
tested composition `f(f(2))` (`eval_seq=16`) and all deeper in-window
compositions remain in-domain, so the discriminator is preserved.

| # | model.py impl op (`eval_implemented`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameters `leaf: int`, `layers: List[int]` | the receiver `self` (a nested chain of `Function` applications over a numeric leaf), reduced by `_eval_evalf` | R | a depth-`n` chain of unary `_imp_` applications over a numeric leaf ↔ `(leaf, layers)` with `len(layers)==n` (mapping.md §2). |
| A2 | `imp(x) == x * x` (the `pure` region) | `self._imp_` — the user implementation (the worked example's `lambda x: x**2`) | A-reference | `_imp_` is the unchanged user callee the code *invokes* but does not change. It is modelled deeply by the concrete representative `imp(x)=x*x` (the example's squaring map); axiom_check.py (G-AX) confirms the real `_eval_evalf` recursion produces this map's iterate on the worked example. The discriminating behaviour (whether a deep composition evaluates at all) is independent of which concrete `_imp_` is chosen, so the representative is faithful. There is NO consumed value axiom about `_imp_`. |
| A3 | result is `eval_seq(leaf, ToSeq(layers))`, the inside-out fold applying `imp` once per layer, computed by the verified backward loop; and `Result() is not None` for every layer count *within the declared exact-float domain* | `Float(self._imp_(*[i.evalf(prec) for i in self.args]), prec)` — recursively evalf the args, then apply `_imp_`, then wrap as a `Float` | A-reference + I | the changed operation — recursively evaluating each argument before applying `_imp_` — is modelled **deeply**: `eval_seq` is the front-recursive fold `eval_seq(leaf, layers) = imp(eval_seq(leaf, layers.drop(1)))`, and the verified loop computes it. Inside-out reduction over the layer sequence == `i.evalf(prec)` recursing through the nested applications before the outer `_imp_` (mapping.md §3). `Float(..., prec)` and the always-present result correspond to `Result() is not None`: with the fix the reduction always yields a number, so `Float` never falls through to the `return None`. The exact-`int` value-equality holds on the declared domain only (a non-negative leaf with `eval_seq(leaf, layers) < 1e14`), where the real `Float` reduction is exactly representable — outside that window the real callee rounds, so the contract does not claim it (see "Contract domain" above; G-AX mirrors this domain exactly). |

The discriminating content of the change lives in `eval_seq` evaluating ALL
layers (so `eval_implemented` returns a present number for `len(layers) >= 2`)
versus the pre-patch only evaluating the outermost application against an
un-reduced argument (a number only for `len(layers) <= 1`). `model_prepatch.py`
reproduces the bug (`return None` when `len(layers) >= 2`) and **fails** the
postconditions `Result() is not None` and `Result() == eval_seq(...)`, which is
exactly the spec sensing the change (G-DIFF).

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — recursively evaluating the arguments before applying the
implementation — is modelled **deeply** (the spelled-out inside-out fold
`eval_seq` consumed in `eval_implemented`, step A3, an **A-reference**), not
hidden behind an axiom about the function under change. The user implementation
`_imp_` (also an **A-reference**, A2) is an unchanged callee invoked by the
code, modelled by a concrete representative whose recursion shape G-AX validates
against the real `_eval_evalf`. There are **no consumed (`A-consumed`) axioms**:
the `axioms` region is empty by design.

## C. verify(model) ⇒ resolved

`eval_implemented` verifies only if its output is a PRESENT number equal to the
full inside-out reduction `eval_seq(leaf, layers)` for every layer count (A3),
including a composition (`len(layers) >= 2`). By R (chain ↔ `(leaf, layers)`,
number ↔ `int`, unevaluated ↔ `None`) the verified reduction equals
`Float(self._imp_(*[i.evalf(prec) for i in self.args]), prec)` on the tested
composition `f(f(2))`: the inner `f(2)` is reduced to `4.0` before the outer
`_imp_` squares it to `16.0`, matching `eval_seq(2, [_, _]) = imp(imp(2)) = 16`
(the F2P `test_issue_12092`: `f(f(2)).evalf() == Float(16)`). By G-AX the deep
model `eval_seq` over `imp` equals the real recursive `_eval_evalf` on the
worked example (A-reference). Therefore a model satisfying this spec, refined by
the map above, is the gold patch up to type refinement and the audited
A-reference — and the gold patch resolves (G-RESOLVE). The trust point is
exactly refinement fidelity (this document, G-EQ) plus the single A-reference
G-AX validates; there are no consumed axioms.
