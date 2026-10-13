# mapping.md — sympy__sympy-12096

## Modeled function

| Lean | Python | file:line @ base_commit `d7c3045115` |
|---|---|---|
| `implementation_evalf` / `problem_spec_evalf` / `correct_evalf` | `Function._eval_evalf(self, prec)` — numerically evaluate a function-application node when no mpmath implementation exists, by applying the node's own numeric implementation (`_imp_`) to its arguments | `sympy/core/function.py:500-512` (the `except (AttributeError, KeyError):` fallback branch; post-patch line 510 becomes `return Float(self._imp_(*[i.evalf(prec) for i in self.args]), prec)`) |

The modeled behavior is the `_imp_` fallback branch only: the function has no
mpmath counterpart, so its numeric value is obtained by evaluating each argument
numerically and then applying its registered numeric implementation. The
surrounding mpmath path (lines 514+) is unchanged and out of scope.

## Type bijection (Lean ↔ Python) — used by G-CONF + G-AX

| Python | Lean | notes |
|---|---|---|
| a SymPy expression tree of `_imp_`-carrying application nodes, numeric `Integer` leaves, and free `Symbol`s | `Expr` (`num`/`atom`/`app`) | `num n` ↔ `Integer n`; `atom` ↔ a free `Symbol` (a leaf with no numeric value); `app f args` ↔ an `implemented_function` node applied to the argument subexpressions |
| a node's numeric implementation `_imp_` | `f : List Int → Int` | the registered lambda; modeled as a strict function of the evaluated argument list (see assumption below) |
| `expr.evalf()` result | `Option Int` | numeric `Float` equal to `n` ↔ `some n`; a result that stays symbolic (`not is_number`) ↔ `none` |
| evaluating each arg then applying `_imp_` (recursive) | `args.attach.mapM evalSpec |>.map f` | the POST-patch recursion: a node has a numeric value iff every argument does |

## Modeling assumption (binding for G-CONF / G-AX)

The node implementations modeled are **strict in every argument**: the result is
numeric exactly when every argument is numeric, and there is no annihilation or
simplification that lets a symbolic argument vanish. The two implementations
demonstrated in the issue and the F2P test (`lambda x: x**2`, `lambda x: 2*x`)
are strict in this sense. G-CONF fuzzes with strict linear node implementations
(fixed nonzero coefficients + offset over the evaluated arguments) so the SymPy
oracle exhibits exactly this numeric-iff-all-numeric behavior; multiplicative
annihilation / order simplifications (which would let `0*x` or `Max(x, c)`
collapse a symbolic arg) are deliberately excluded as outside the modeled
behavior.

## Callee provenance / flag deps

- The numeric evaluation is modeled **deeply** (`evalSpec` / `implementation_evalf`):
  the per-argument recursion and the apply-implementation step are spelled out.
  There is **no** `opaque` callee and **no** consumed `_prop` axiom. The node's
  numeric implementation `f` is an abstract parameter of the model (universally
  quantified), not an axiomatized callee, so G-AX is a skip.
- The construction recurses structurally over the argument subexpressions
  (`args.attach`, well-founded by `List.sizeOf_lt_of_mem`); this is the deep model
  of "evaluate each argument before applying the implementation."

## Pre-patch behavior (the bug, for G-DIFF)

Pre-patch line 510 is `return Float(self._imp_(*self.args), prec)` — the
arguments are passed to `_imp_` **without** being numerically evaluated first.
When an argument is itself an unevaluated application (e.g. `g(2)` inside
`f(g(2))`), `_imp_` receives a symbolic argument and the apply fails / stays
symbolic, so the composition does not evaluate. `Solution_prepatch.lean` models
this: a value is taken only from arguments that are **already** concrete numbers
(`.num`), and any non-numeric argument (including a nested application) aborts to
`none`. Its carried gold proof (`impl_app`/`correct_evalf`) is therefore
unclosable — the discriminating clause is the `app` case with a nested
application argument.

**Exactness of the prepatch model (under the strict-in-args assumption).** This
is not merely a conservative bug model — under the modeling assumption above it
is *exact*. With a strict numeric `_imp_`, applying it to an un-evaluated
immediate child that is itself an application yields a SymPy expression that is
still symbolic, so `Float(symbolic, prec)` raises and the surrounding
`except (AttributeError, TypeError, ValueError): return` produces no value (the
issue's `f(g(2)) -> f(g(2))` observation). Hence "immediate child is not already
a concrete number" ⟺ "the pre-patch `_imp_` application fails to produce a
number" ⟺ `none` — exactly the prepatch's `match a with | .num v => … | _ =>
return none`. The general (non-strict `_imp_`) case — where some implementation
might tolerate or annihilate a symbolic argument — is deliberately outside the
modeled behavior (same assumption that scopes G-CONF), not a faithfulness gap.

## G-CONF fuzz seed

`conf_seed = 12096` (pinned; see conformance_check.py and meta.json).
