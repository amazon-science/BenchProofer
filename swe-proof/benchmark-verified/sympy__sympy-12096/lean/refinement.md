# refinement.md — sympy__sympy-12096

Operation correspondence between `implementation_evalf` (Solution.lean, impl
region) and the gold `patch.diff` (`Function._eval_evalf` fallback branch).
Every op is tagged **R** (type refinement), **A-consumed** (proof uses an axiom's
property), **A-reference** (deep model validated == real callee by G-AX), or
**I** (identical concrete op).

The patched line is:
```
return Float(self._imp_(*[i.evalf(prec) for i in self.args]), prec)
```

| # | `implementation_evalf` op | `patch.diff` counterpart | tag | note |
|---|---|---|---|---|
| 1 | dispatch on the expression `Expr` (`num` / `atom` / `app`) | the node is a `Function` instance whose args are `self.args`; the `num`/`atom` leaves model numeric vs. symbolic operands | R | `Expr` ↔ SymPy expression tree (mapping.md). `num`/`atom`/`app` ↔ numeric leaf / free symbol / application node |
| 2 | `.num n => some n` | a numeric operand evaluates to its own `Float` value | R | numeric leaf already has a value; `evalf` is identity on it. `Int` ↔ numeric `Integer`/`Float` |
| 3 | `.atom => none` | a free symbol has no numeric value (`evalf` leaves it symbolic) | R | `none` ↔ "result is not a number" |
| 4 | `for a in args.attach do … match implementation_evalf a.1` | `[i.evalf(prec) for i in self.args]` — recursively evaluate EACH argument | R | the heart of the fix: the comprehension's recursive `i.evalf(prec)` ↔ the structural recursive call `implementation_evalf a.1` over each argument subexpression |
| 5 | `| none => return none` (early abort) | if any `i.evalf(prec)` stays symbolic, `self._imp_(*…)` raises / yields a non-numeric result and the outer `try` returns nothing | R | early-`return` ↔ the apply failing to produce a number when an argument is non-numeric (strict-in-args assumption, mapping.md) |
| 6 | `| some v => vals := vals ++ [v]` | accumulate the evaluated arguments in order to pass to `_imp_` | I | ordered accumulation of the comprehension's results |
| 7 | `return some (f vals)` | `Float(self._imp_(*evaluated_args), prec)` | R | apply the node's numeric implementation to the evaluated argument list. `f : List Int → Int` ↔ `self._imp_` (a universally-quantified model parameter, NOT an axiomatized callee); `Float(_, prec)` is the `Int`↔`Float` coercion under the bijection |

## Tag summary
- **R:** rows 1–5, 7 (type refinement: `Expr`/`Option Int`/`f` ↔ SymPy tree /
  `evalf` result / `_imp_`).
- **I:** row 6 (ordered accumulation).
- **A-consumed:** none.
- **A-reference:** none (the node implementation `f` is a model parameter,
  universally quantified in `correct_evalf`; it is not a fixed repo callee, so it
  is neither axiomatized nor G-AX-referenced — G-AX is a skip).

No changed op is left inexpressible: the recursive per-argument evaluation (the
actual fix) is modeled deeply as the structural recursion in op #4, NOT
axiomatized.

## G-CONF coverage
The impl region is R/I (not all-A), so `conf_skip = false`. `conformance_check.py`
differential-tests the R/I shadow against an independent reconstruction of the
post-patch behavior over real SymPy `implemented_function` trees (>=10^5 fuzzed
inputs, seed 12096), with the strict-in-args modeling assumption (mapping.md).
