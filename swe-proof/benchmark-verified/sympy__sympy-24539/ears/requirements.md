# Requirements: `PolyElement.as_expr()` must honor caller-supplied symbols

## Introduction

In `sympy/polys/rings.py`, the `PolyElement.as_expr()` method is meant to
convert a multivariate polynomial ring element into a symbolic SymPy
expression, optionally letting the caller choose which symbols (generators)
the resulting expression is written in terms of. As implemented, the method is
broken: when the caller passes a list of symbols of the correct length, the
method ignores them and always uses the ring's own symbols; and when a list of
the wrong length is passed it raises an error with a misleading message.

The goal is to make `PolyElement.as_expr()` behave as documented: use the
caller's symbols when a correctly-sized set is supplied, fall back to the
ring's own symbols only when none are supplied, and reject a wrong-sized set
with a clear error — while preserving the no-argument behavior that existing
callers rely on. The conversion of term data into an expression (via
`as_expr_dict` and the underlying `expr_from_dict` helper in
`sympy/polys/polyutils.py`) is unchanged; only *which* symbols are handed to it
is affected.

## Requirement 1: Honor a correctly-sized set of caller-supplied symbols

**User story:** As a user of SymPy's sparse polynomial rings, I want
`PolyElement.as_expr(*symbols)` to build the expression using the symbols I
pass, so that I can render a polynomial in terms of names of my choosing rather
than the ring's original generator names.

**Acceptance criteria**
1. WHEN `as_expr` is called on a polynomial ring element with a number of
   positional symbol arguments equal to the number of generators of its ring
   (`self.ring.ngens`), THEN `as_expr` SHALL return a symbolic expression built
   using exactly the caller-supplied symbols, in the order given.
2. WHEN `as_expr` is called with a correctly-sized set of symbols that differ
   from the ring's own symbols, THEN the returned expression SHALL contain the
   caller-supplied symbols and SHALL NOT contain the ring's own symbols.
3. WHEN `as_expr` is called with a correctly-sized set of symbols, THEN the
   monomial-exponent-to-symbol correspondence and the coefficients of the
   returned expression SHALL be identical to those produced with the ring's own
   symbols, differing only in the symbol names substituted position-for-position.

## Requirement 2: Fall back to the ring's own symbols when none are supplied

**User story:** As an existing caller of `as_expr`, I want the no-argument form
to keep working exactly as before, so that code that relies on the ring's own
generator names is not broken.

**Acceptance criteria**
1. WHEN `as_expr` is called with no positional symbol arguments, THEN `as_expr`
   SHALL return the symbolic expression built using the ring's own symbols
   (`self.ring.symbols`).
2. The system SHALL keep the no-argument result of `as_expr` unchanged from its
   prior behavior for every polynomial ring element.

## Requirement 3: Reject a wrong-sized set of caller-supplied symbols

**User story:** As a user who passes the wrong number of symbols, I want a
clear, immediate error, so that I can correct my call instead of getting a
silently wrong expression.

**Acceptance criteria**
1. IF `as_expr` is called with a non-empty set of positional symbol arguments
   whose count is not equal to the number of generators of the ring
   (`self.ring.ngens`), THEN `as_expr` SHALL raise a `ValueError` and SHALL NOT
   return an expression.
2. WHEN such a `ValueError` is raised, THEN its message SHALL report both the
   expected number of symbols (the ring's generator count) and the number of
   symbols actually supplied.
