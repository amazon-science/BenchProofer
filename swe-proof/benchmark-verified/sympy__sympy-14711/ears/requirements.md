## Introduction

In `sympy.physics.vector`, a `Vector` (defined in
`sympy/physics/vector/vector.py`) represents a physical vector as a list of
basis-weighted components. Vector addition is implemented by the `Vector`
class's addition operator (`__add__`, which is also bound as the reflected
addition operator `__radd__`).

Adding the integer `0` to a `Vector` currently fails: the addition operator
routes every operand through a strict "must be a Vector" check and raises
`TypeError` when the operand is the scalar `0`. This breaks natural, idiomatic
code such as summing a list of vectors with the built-in `sum(...)`, because
`sum` begins accumulation from the integer `0`, so the very first addition adds
`0` to a `Vector` and raises.

The goal is to make the scalar additive identity `0` a valid operand of vector
addition: adding `0` to a vector (in either operand order) must succeed and
yield the original vector unchanged, while all other addition behavior is
preserved.

## Requirement 1: Adding the scalar zero to a vector returns the vector unchanged

**User story:** As a user of `sympy.physics.vector`, I want to add the integer
`0` to a `Vector` without an error, so that idioms like `sum([...])` over
vectors work and `0` behaves as the additive identity.

**Acceptance criteria**

1. WHEN the addition operator of a `Vector` is invoked with the integer `0` as
   the other operand, THEN the operator SHALL return a vector equal to the
   original vector and SHALL NOT raise an exception.
2. WHEN a `Vector` `v` is added to the integer `0` (as in `v + 0`), THEN the
   result SHALL compare equal to `v`.
3. WHEN the integer `0` is added to a `Vector` `v` with `0` on the left (as in
   `0 + v`, exercising reflected addition), THEN the result SHALL compare equal
   to `v`.
4. WHEN the built-in `sum` is applied to a list of `Vector` objects (which
   begins accumulation from the integer `0`), THEN the operation SHALL complete
   without raising and SHALL yield the sum of those vectors.
5. IF the other operand of vector addition equals `0`, THEN the operator SHALL
   yield the original vector's components unchanged, rather than treating the
   operand as an invalid addend.

## Requirement 2: Adding another vector still concatenates their components

**User story:** As a user relying on existing vector arithmetic, I want ordinary
vector-to-vector addition to keep working exactly as before, so that adding
`0` support introduces no regression.

**Acceptance criteria**

1. WHEN two `Vector` objects are added, THEN the operator SHALL return a
   `Vector` whose component representation is the combination of both operands'
   components.
2. WHEN a component and its negation are both present across the added vectors,
   THEN the resulting vector SHALL reflect the correct algebraic sum (e.g.
   canceling components produce the zero vector).
3. The system SHALL preserve equality, negation, scalar multiplication, dot
   product, and difference (`-`) behavior of vectors unchanged by this change.

## Requirement 3: Non-zero, non-vector operands remain rejected

**User story:** As a maintainer, I want addition to still reject invalid
operands, so that the relaxation for `0` does not silently accept meaningless
additions.

**Acceptance criteria**

1. IF the other operand of vector addition is neither a `Vector` nor equal to
   the scalar `0`, THEN the operator SHALL raise `TypeError`.
2. WHEN vector addition rejects an invalid operand, THEN the raised error SHALL
   indicate that a `Vector` must be supplied.
