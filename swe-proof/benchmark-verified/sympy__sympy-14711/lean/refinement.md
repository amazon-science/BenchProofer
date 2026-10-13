# refinement.md — sympy__sympy-14711

Operation-by-operation correspondence between `implementation_vectorAdd`
(Solution.lean impl region) and `patch.diff` (the POST-PATCH `Vector.__add__`).
Tags: **R** type refinement, **A-consumed** proof uses an axiom, **A-reference**
deep model validated == real callee, **I** identical concrete op.

Post-patch Python:

```python
def __add__(self, other):
    """The add operator for Vector. """
    if other == 0:
        return self
    other = _check_vector(other)
    return Vector(self.args + other.args)
```

| # | Lean impl op | patch.diff / post-patch Python op | tag |
|---|---|---|---|
| 1 | `if isAdditiveZero other then return Except.ok selfArgs` | `if other == 0: return self` (the ADDED guard) | R |
| 2 | `match other with .vector otherArgs => return Except.ok (selfArgs ++ otherArgs)` | `other = _check_vector(other); return Vector(self.args + other.args)` (the non-error path: `other` is a `Vector`, components appended) | R |
| 3 | `| _ => return Except.error ()` | `other = _check_vector(other)` raises `TypeError('A Vector must be supplied')` when `other` is not a `Vector` | R |

Notes:

- **Every step is R — no A.** The operand classification and the resulting
  component list are modeled DEEPLY and structurally over the observable shape of
  the operand (`AddOperand`); SPEC_GUIDE §3 forbids axiomatizing a deeply-modeled
  changed decision. The `axioms` region is empty; **G-AX skips**.
- **The fix itself is op #1**: the ADDED `if other == 0: return self` guard. In
  the impl this is the leading `if isAdditiveZero other then return ...`. Its
  absence in the pre-patch impl (`Solution_prepatch.lean`) makes the scalar zero
  fall through to the type-error path (op #3), exactly the original bug
  (`_check_vector` raises `TypeError` on the scalar `0`).
- **R refinement for op 1 (`other == 0`).** Python's `other == 0` is true for the
  scalar `0`. It is ALSO true (via `Vector.__eq__`) for a vector with no
  components (the zero vector, `self.args == []` against `Vector(0)`), in which
  case returning `self` (the zero vector) is equal to the append-result anyway
  (`selfArgs ++ [] == selfArgs`), so the guard is behaviour-preserving on that
  overlap. `isAdditiveZero` therefore maps both `.scalarZero` and `.vector []` to
  the identity branch; for `.vector []` the result (`selfArgs`) coincides with the
  ordinary vector-append result (`selfArgs ++ [] = selfArgs`), so the two impl
  paths agree — no discriminating disagreement is introduced by the overlap. The
  bijection (scalar `0` ↔ `.scalarZero`, a `Vector` ↔ `.vector args`, any other
  value ↔ `.nonVector`) is in mapping.md.
- **R refinement for op 2/3.** `_check_vector(other)` is the identity on a
  `Vector` and raises `TypeError` otherwise; the construction
  `Vector(self.args + other.args)` appends the two argument lists. We model the
  raise as `Except.error ()` and the produced vector by its component list
  (`Except.ok (selfArgs ++ otherArgs)`). `_check_vector` is UNCHANGED by the patch
  and its net effect (identity / raise on the operand's vector-ness) is folded
  into the `AddOperand` classification; it is not separately axiomatized.
- **G-CONF** mechanically refutes the R legs (no A legs): a Python shadow of the
  impl is diffed against an in-process replica of the POST-PATCH `__add__`
  behaviour over ≥1e5 fuzzed operands, including the discriminating scalar-zero
  case.
