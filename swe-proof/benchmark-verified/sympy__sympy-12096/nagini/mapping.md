# mapping.md — sympy__sympy-12096

Binds every `model.py` symbol to the real repo symbol it abstracts, at
`base_commit` `d7c3045115693e887bcd03599b7ca4650ac5f2cb`. All line numbers are
at that commit.

## 1. Symbol binding

| model.py | repo symbol | file:line (base_commit) |
|---|---|---|
| `eval_implemented(leaf, layers)` | the `_imp_` branch of `Function._eval_evalf(self, prec)` (the `except (AttributeError, KeyError)` clause that returns `Float(self._imp_(...), prec)`) | `sympy/core/function.py:500` (function), `:510` (the changed `return`) |
| `imp(x)` | `self._imp_` — the user implementation attached by `implemented_function` (the worked example `lambda x: x ** 2`) | `sympy/utilities/lambdify.py:653` (`implemented_function`), `:698` (`symfunc._imp_ = staticmethod(implementation)`) |
| `eval_seq(leaf, layers)` | the inside-out recursive numeric reduction the patched line performs: `self._imp_(*[i.evalf(prec) for i in self.args])`, where each `i.evalf(prec)` re-enters `_eval_evalf` on a nested application | `sympy/core/function.py:510` (patched expression); recursion driver `Expr.evalf` at `sympy/core/expr.py:1687` |

## 2. Type / structure abstraction

The receiver `self` is a nested chain of unary implemented-function
applications over a numeric leaf (e.g. `f(f(2))`). It is abstracted by
`(leaf: int, layers: List[int])`:

- `leaf` — the innermost numeric argument (the `Integer`/`Float` at the bottom
  of the nesting). Modelled as `int` (the worked example's leaf `2` and all the
  squaring iterates are exact integers).
- `layers` — one element per surrounding application; `len(layers)` is the
  nesting depth. The element *values* are irrelevant: only the count carries
  the structure (each layer is "apply `_imp_` once more"). Carried into the
  specification as `PSeq[int]` via `ToSeq`. Read-only ⇒ `Acc(list_pred, 1/2)`,
  Required and Ensured (directive 5).
- result — a number, or "left unevaluated" when `_eval_evalf`'s `except` clause
  `return`s `None`. Modelled as `Optional[int]`: a present `int` for a
  successful numeric reduction, `None` for unevaluated.

`f(f(2))` ↔ `leaf=2, layers=[_, _]` (depth 2); `f(2)` ↔ `leaf=2, layers=[_]`
(depth 1); a bare `2` ↔ `leaf=2, layers=[]` (depth 0).

## 3. Callee provenance (A-reference, not consumed axioms)

There are **no consumed (`@ContractOnly`) axioms** in this bundle — the
`axioms` region is empty. Two A-references (deep models validated by G-AX):

### 3.1 `imp` ↔ `self._imp_`
`_imp_` is the user implementation attached by `implemented_function`
(`sympy/utilities/lambdify.py:698`, `symfunc._imp_ = staticmethod(implementation)`).
The gold patch does NOT change `_imp_`; it changes how its arguments are
computed. It is modelled by the concrete representative `imp(x) = x * x` (the
worked example `lambda x: x ** 2`). The discriminating behaviour — whether a
deep composition reduces to a number at all — is independent of which concrete
implementation is chosen, so the representative is faithful. G-AX
(axiom_check.py) confirms the real `_eval_evalf` recursion reproduces this map's
iterate on the worked example.

### 3.2 `eval_seq` ↔ the recursive `i.evalf(prec)` reduction
The patched expression `self._imp_(*[i.evalf(prec) for i in self.args])`
evaluates each argument numerically *before* applying `_imp_`. For a nested
chain, `i.evalf(prec)` recurses (re-entering `_eval_evalf` on the inner
application), giving an inside-out reduction: innermost leaf first, then `_imp_`
once per surrounding layer. `eval_seq(leaf, layers)` is the front-recursive fold
modelling exactly this. axiom_check.py runs the REAL recursion (boundary +
fuzz, in-container) and asserts the reduction equals `eval_seq` over `imp` on
the worked example, including the discriminator `f(f(2)).evalf() == Float(16)`.

**Exact-float domain (A-reference soundness).** The real callee returns a
`Float` rounded to ~15 significant digits; the exact-`int` `eval_seq` matches it
bit-for-bit only while the reduced value is exactly representable. The contract
declares this domain in its preconditions — `leaf >= 0` and
`eval_seq(leaf, ToSeq(layers)) < 1e14` — and axiom_check.py's `within_precision`
filter MIRRORS that precondition exactly (`leaf >= 0 and eval_seq(leaf, n) <
1e14`), so the validation domain is neither broader nor narrower than the
declared domain. Inputs outside the window (e.g. `leaf=11` over 4 layers →
`11**16 ≈ 4.59e16`) are out-of-domain: the contract does not assert exact
equality there, and the check does not exercise them.

## 4. Flag / configuration dependencies

None. The reduction uses default `prec` (sympy's `evalf` default). No
`--float-encoding` flag is needed: numbers are modelled as exact `int` over the
declared exact-float domain (a non-negative leaf whose inside-out reduction
stays `< 1e14`, where the real `Float` reduction is exactly representable). The
tested leaf and all in-window squaring iterates are integers; the F2P test
compares `f(f(2)).evalf() == Float(16)`, an exact integer value. The behaviour
under test is whether a deep composition evaluates at all — within that domain,
an integer-exact property. The domain is declared as preconditions in `model.py`
(`leaf >= 0`, `eval_seq(leaf, ToSeq(layers)) < 1e14`) and mirrored exactly by
axiom_check.py (G-AX), so the exact-`int` A-reference is never asserted where the
real callee would round (the spec-too-strong-vs-reality fix, SPEC_GUIDE
directive 7).
