# refinement.md — sympy__sympy-21612

Every operation in `implementation_printDenominatorFactor` mapped to its
`patch.diff` counterpart. Tags: **R** (type refinement), **A-consumed** (proof uses
an axiom's property), **A-reference** (deep model validated == real callee by
G-AX/G-CONF), **I** (identical concrete op).

## `implementation_printDenominatorFactor` ↔ `_print_Mul` denominator-factor bracketing (str.py:333–356)

Gold (post-patch) decision + wrap:
```python
if (len(item.args[0].args) != 1 and
        isinstance(item.base, (Mul, Pow))):    # <-- fix widens Mul to (Mul, Pow)
    pow_paren.append(item)
b.append(item.base)
...
b_str = [self.parenthesize(x, prec, strict=False) for x in b]
for item in pow_paren:
    if item.base in b:
        b_str[b.index(item.base)] = "(%s)" % b_str[b.index(item.base)]
```
Pre-patch decision (only difference):
```python
if (len(item.args[0].args) != 1 and
        isinstance(item.base, Mul)):
```

| Lean op | patch.diff op | tag |
|---|---|---|
| `let baseStr := render base` | `b_str[i] = self.parenthesize(item.base, prec, strict=False)` — render the base into its fragment | **A-reference** (renderer universally quantified; binding to real `self.parenthesize` checked by G-CONF) |
| `let needParen := baseComponentCount ≠ 1 ∧ (baseIsProduct = true ∨ baseIsPower = true)` | `len(item.args[0].args) != 1 and isinstance(item.base, (Mul, Pow))` — the bracket-needed predicate | **R** (`baseComponentCount ≠ 1` ↔ `len(item.args[0].args) != 1`; `baseIsProduct` ↔ `isinstance(item.base, Mul)`; `baseIsPower` ↔ `isinstance(item.base, Pow)`) |
| `if needParen then return "(" ++ baseStr ++ ")" else return baseStr` | the extra wrap `b_str[i] = "(%s)" % b_str[i]` applied iff `item ∈ pow_paren`, else `b_str[i]` unchanged | **I** (string template: wrap in one bracket pair, or leave the fragment as is) |

The prepatch's `needParen := baseComponentCount ≠ 1 ∧ baseIsProduct = true`
corresponds to the pre-patch `isinstance(item.base, Mul)` test, which drops the
brackets when the base is a multi-component POWER (e.g. `1/y`), producing `x/1/y`
instead of `x/(1/y)`.

## Notes
- No op is changed-inexpressible. The single behavioral change — widen the
  bracket-needed type test from "product" to "product or power" — is modeled
  directly as the extra `baseIsPower` disjunct in the bracketing predicate.
- No consumed axiom: `render` is universally quantified, so the proof uses no
  property of it (the spec holds for every base renderer). `axiom_check.py` is a
  skip stub. The R/I content (the bracketing predicate + the wrap/no-wrap template)
  is differential-tested by `conformance_check.py` (G-CONF, `conf_skip=false`).
