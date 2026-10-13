# mapping.md — sympy__sympy-20801

## Symbol binding (file:line @ base_commit e11d3fed782146eebbffdc9ced0364b223b84b6c)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_floatEq` / `problem_spec_floatEq` / `correct_floatEq` | `Float.__eq__` (the equality dispatch a float performs against a sympified operand) | `sympy/core/numbers.py:1383-1410` |
| `EqInput` (pure helper) | the observations of `self` and the already-sympified `other` that the dispatch reads | the locals/probes `not self`, `isinstance(other, Boolean)`, `other.is_NumberSymbol`, `other.is_irrational`, `other.is_Float`, `other.is_Rational`, `other.is_Number`, the comparison sub-results, and `not other` | `numbers.py:1388-1409` |
| `floatEqResult` (pure helper) | the body computing the returned boolean | `numbers.py:1388-1409` |

## Lean ↔ Python type bijection (used by G-CONF; G-AX skips)

The modeled value is the boolean returned by `Float.__eq__` **after** the
operand has been successfully sympified (the `SympifyError → NotImplemented`
guard is a precondition: it is out of the modeled domain). Every branch reached
after sympification returns a Python `bool`, so `result : Bool`.

| Lean field (`EqInput`) | Python expression | meaning |
|---|---|---|
| `selfIsZero : Bool` | `not self` | the float value is zero (mpf is `fzero`) |
| `otherIsBoolean : Bool` | `isinstance(other, Boolean)` | operand is a logic Boolean (`S.true`/`S.false`) |
| `otherIsNumberSymbol : Bool` | `other.is_NumberSymbol` | operand is a named numeric constant |
| `otherIsIrrational : Bool` | `other.is_irrational` | that constant is irrational |
| `numberSymbolEq : Bool` | `other.__eq__(self)` (rational NumberSymbol branch) | delegated equality result |
| `otherIsFloat : Bool` | `other.is_Float` | operand is itself a float |
| `mpfEq : Bool` | `self._mpf_ == other._mpf_` | exact mpf-tuple equality |
| `otherIsRational : Bool` | `other.is_Rational` | operand is a rational |
| `rationalEq : Bool` | `other.__eq__(self)` (rational branch) | delegated equality result |
| `otherIsNumber : Bool` | `other.is_Number` | operand is some other Number |
| `numberMpfEq : Bool` | `bool(mlib.mpf_eq(self._mpf_, ompf))` | equality at shared precision |
| `otherIsFalsy : Bool` | `not other` | the operand is "falsy" (e.g. `not S.false` is `True`) |

The carried sub-results (`numberSymbolEq`, `rationalEq`, `numberMpfEq`) are the
outcomes of UNCHANGED upstream comparisons (delegations to the operand's own
`__eq__` / the mpf-equality primitive). They enter as plain data fields (the
*carried-observation* refinement, all R) — the patch does not touch them; it
only reorders the zero-operand clause relative to the type dispatch.

## What the function does (base_commit)

After sympifying `other`, the base-commit dispatch is, in order:

```python
if not self:                      # <-- the clause the patch RELOCATES
    return not other
if isinstance(other, Boolean):
    return False
if other.is_NumberSymbol:
    if other.is_irrational:
        return False
    return other.__eq__(self)
if other.is_Float:
    return self._mpf_ == other._mpf_
if other.is_Rational:
    return other.__eq__(self)
if other.is_Number:
    ompf = other._as_mpf_val(self._prec)
    return bool(mlib.mpf_eq(self._mpf_, ompf))
return False                      # Float != non-Number
```

The leading `if not self: return not other` short-circuits **before** the type
dispatch. When the float is zero and the operand is a logic Boolean, `not other`
is `True` for `S.false`, so a zero float compared to `S.false` returns `True` —
while the operand's own dispatch returns `False`, giving an order-dependent,
asymmetric equality. The patch moves that zero-operand clause to **after** the
whole type dispatch (just before the terminal `return False`), so a Boolean
operand is caught by `isinstance(other, Boolean): return False` first.

The behaviour the patch changes and the FAIL_TO_PASS test observes:
`test_zero_not_false` asserts `(S(0.0) == S.false) is False` (and the symmetric
/ integer forms). The relocated clause still fires for genuine non-Number
operands (`return not other` only reached when the operand is none of
Boolean/NumberSymbol/Float/Rational/Number).

## Callee provenance + flag deps

No unchanged callee contract is consumed: the dispatch is modeled DEEPLY over
the observable boolean flags + carried comparison results. `axioms` region
empty; **G-AX skips**. No flag-configuration dependence beyond the per-field
observables listed above.

## G-CONF fuzz seed

Pinned seed: **20801** (also in `conformance_check.py`).
