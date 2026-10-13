# mapping.md — sympy__sympy-21612

## Symbol binding (file:line @ base_commit b4777fdcef467b7132c055f8ac2c9a5059e6a145)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_printDenominatorFactor` / `problem_spec_printDenominatorFactor` | the denominator-factor bracketing branch of `StrPrinter._print_Mul` | `sympy/printing/str.py:249` (`_print_Mul`); the bracketing decision at lines `333`–`339` |
| `render : Expr → String` | the printer's own per-factor base renderer `self.parenthesize(item.base, prec, strict=False)` (the entry that produces `b_str[i]`) | `sympy/printing/str.py` (`b_str` built at `:350`; the optional extra wrap applied at `:354`–`356`) |

### What the modeled branch is

`_print_Mul` splits a product into numerator items `a` and denominator items `b`.
For each denominator factor that is a commutative `Pow` with `exp is S.NegativeOne`
(i.e. a bare `1/base`), the code appends `item.base` to `b` and decides whether
that base's rendered fragment must be wrapped in an EXTRA pair of brackets. The
decision (str.py:333–336) is:

```python
if (len(item.args[0].args) != 1 and
        isinstance(item.base, Mul)):          # gold: (Mul, Pow)
    pow_paren.append(item)
```
and later (str.py:354–356) the collected `pow_paren` factors get their `b_str`
entry wrapped: `b_str[i] = "(%s)" % b_str[i]`.

The fix widens the type test from `isinstance(item.base, Mul)` to
`isinstance(item.base, (Mul, Pow))`, so a denominator factor whose base is itself a
multi-component POWER (e.g. `1/y`, which is `Pow(y, -1)`) is now also bracketed.
Without it, `Mul(x, Pow(1/y, -1, evaluate=False))` printed as `x/1/y` instead of
`x/(1/y)`.

The triple models exactly this per-factor bracketing decision: given the base's
component count and whether the base is a product / a power, return the base
fragment, wrapped in one pair of brackets iff the decision fires.

## Lean ↔ Python type bijection (used by G-CONF + G-AX)

| Lean | Python |
|---|---|
| `Expr : Type` (abstract) | the base of a denominator `Pow` factor (`item.base`, a sympy `Expr`) |
| `render : Expr → String` | `lambda b: StrPrinter().parenthesize(b, prec, strict=False)` — the printer's base-fragment renderer (the value stored in `b_str[i]` before any extra wrap) |
| `base : Expr` | `item.base` |
| `baseComponentCount : Nat` | `len(item.args[0].args)` — the number of components of the factor's exponent-stripped argument (`item.args[0]`); equals `len(item.base.args)` for the modeled `exp == -1` factors |
| `baseIsProduct : Bool` | `isinstance(item.base, Mul)` |
| `baseIsPower : Bool` | `isinstance(item.base, Pow)` |
| `result : String` | the final `b_str[i]` entry for this factor (after the optional extra-bracket wrap) |

`Expr` is an abstract Lean type variable and `render` is universally quantified, so
the spec/impl are parametric over EVERY base renderer. The only modeled behavior is
the bracketing predicate: `baseComponentCount ≠ 1 ∧ (baseIsProduct ∨ baseIsPower)`
(gold) vs `baseComponentCount ≠ 1 ∧ baseIsProduct` (prepatch).

Note on `len(item.args[0].args)`: for the modeled factors `item = Pow(base, -1,
evaluate=False)`, `item.args[0]` is `base`, so `baseComponentCount == len(base.args)`.
G-CONF computes `baseComponentCount` exactly as `len(item.args[0].args)` to stay
faithful to the real expression carrier.

## Callee provenance + flag deps

- `render` (the base-fragment renderer) is the UNCHANGED `self.parenthesize` /
  `self._print` dispatch. It is NOT axiomatized: it is left universally quantified,
  so it is an A-reference recorded only to document the G-CONF binding to the real
  callee.
- No flag dependency. The modeled decision is a pure structural test on `item.base`
  (`isinstance` against `Mul` / `Pow`) and the component count
  `len(item.args[0].args)`; it does not consult any printer setting.
- Branch scope: the modeled factors are exactly the commutative `Pow` factors with
  `exp is S.NegativeOne` reached via the `else` branch at str.py:330–339 (the only
  place `pow_paren` is populated). G-CONF constructs `Mul(..., Pow(B, -1,
  evaluate=False), evaluate=False)` inputs so this branch is exercised.

## Pinned G-CONF fuzz seed

`random.Random(21612)`, N = 100_000 (`conformance_check.py`).
