# Requirements — sympy__sympy-17630

## Introduction

In SymPy's matrix-expression subsystem, symbolic matrix expressions built with
the top-level `sympy.core.Add` constructor are routed through a
constructor post-processor (`get_postprocessor(Add)` in
`sympy/matrices/expressions/matexpr.py`). This post-processor partitions the
addends into matrix terms and scalar (non-matrix) terms and rebuilds the sum as
a `MatAdd`, which then canonicalizes itself (via `MatAdd.doit` →
`sympy/matrices/expressions/matadd.py:canonicalize`) by dropping additive-identity
terms and sorting the survivors.

There is a defect on the branch where **every** addend is a matrix expression
(no scalar terms). On that branch the post-processor prepends a scalar zero
(the empty-argument reduction of `Add`, i.e. `sympy.core.numbers.Zero`) ahead of
the matrix terms before constructing the `MatAdd`. When the matrix terms are all
additive identities — e.g. a sum of `ZeroMatrix` blocks — the canonicalization's
"remove identities" rule keeps the first survivor, which is that scalar `Zero`.
The result is therefore a shapeless scalar `Zero` instead of a shape-preserving
`ZeroMatrix`.

This corrupts downstream matrix algebra. In particular, repeated block
multiplication of a `BlockMatrix` containing `ZeroMatrix` blocks (`block_collapse`
in `sympy/matrices/expressions/blockmatrix.py`) produces intermediate blocks that
are scalar `Zero` objects; a later step reads `.cols`/`.rows` on those blocks and
raises `AttributeError: 'Zero' object has no attribute 'cols'`. So
`block_collapse(b*b)` works but `block_collapse(b*b*b)` crashes.

The goal is: an `Add` over matrix expressions only must produce a matrix result
that preserves matrix shape (a `ZeroMatrix` when the terms cancel to zero), so
that repeated block-matrix products of block matrices containing zero blocks
evaluate without error and to the mathematically correct block form — while all
previously-working matrix-sum, block-collapse, and mixed scalar/matrix behaviors
are preserved.

## Requirement 1: Adding matrix expressions yields a matrix, not a scalar

**User story:** As a user building symbolic matrix expressions, I want the sum
of matrix terms to remain a matrix quantity, so that the result keeps its shape
and can be used in further matrix operations.

**Acceptance criteria**
1. WHEN a top-level `Add` is constructed and every addend is a matrix expression
   (there are no scalar/non-matrix addends), THEN the addition post-processor in
   `sympy/matrices/expressions/matexpr.py` SHALL return a matrix expression
   (a `MatrixExpr`), never a bare scalar.
2. WHEN such a matrix-only `Add` reduces to the additive identity because every
   term is an additive-identity matrix (each term is a `ZeroMatrix`), THEN the
   result SHALL be a `ZeroMatrix` of the shared block/matrix shape, and SHALL NOT
   be a scalar `sympy.core.numbers.Zero`.
3. The system SHALL ensure the result of adding two same-shaped zero matrices is
   a zero matrix of that shape (i.e. `Add(ZeroMatrix(m, n), ZeroMatrix(m, n))`
   equals `ZeroMatrix(m, n)`).
4. WHEN the matrix-only sum has surviving (non-identity) matrix terms, THEN the
   post-processor SHALL return those terms combined as a matrix sum with identity
   (zero-matrix) terms dropped, and SHALL NOT inject a scalar zero as an
   additional term ahead of them.
5. IF a matrix-only sum reduces to a single surviving matrix term, THEN the
   result SHALL be exactly that matrix term.

## Requirement 2: Repeated block multiplication with zero blocks succeeds

**User story:** As a user working with block matrices that contain zero blocks,
I want to multiply them repeatedly, so that expressions like `b*b*b` collapse
without raising an exception.

**Acceptance criteria**
1. WHEN a square `BlockMatrix` containing one or more `ZeroMatrix` blocks is
   multiplied by itself two or more times and collapsed with `block_collapse`,
   THEN the collapse SHALL complete without raising an `AttributeError` about a
   `Zero` object lacking `.cols`.
2. WHEN a block matrix `b = BlockMatrix([[a, z], [z, z]])` (with `a` a square
   matrix symbol and `z` a same-shaped `ZeroMatrix`) is formed, THEN
   `block_collapse(b*b)` SHALL equal `BlockMatrix([[a**2, z], [z, z]])` and
   `block_collapse(b*b*b)` SHALL equal `BlockMatrix([[a**3, z], [z, z]])`.
3. WHILE performing block multiplication, the intermediate zero blocks produced
   by summing zero blocks SHALL remain shape-carrying zero matrices, so that
   subsequent access to a block's column/row counts succeeds.

## Requirement 3: Preserve mixed scalar-and-matrix addition behavior

**User story:** As an algorithm author who substitutes matrix expressions with
non-commutative scalar placeholders, I want to still be able to form
`Add(scalar, matrix)` without an exception, so that existing manipulation
strategies keep working.

**Acceptance criteria**
1. WHEN a top-level `Add` mixes scalar (non-matrix) terms with matrix terms,
   THEN the post-processor SHALL keep returning a result that combines the scalar
   part with the matrix part (a `MatAdd` seeded with the scalar terms), without
   raising an exception.
2. The system SHALL keep the behavior that an `Add` containing only scalar terms
   returns the ordinary scalar sum.
3. Because the correction is confined to the branch where every addend is a
   matrix expression, the system SHALL leave every other addition path
   unchanged — in particular, any `Add` that mixes a scalar (non-matrix) term
   with a matrix term SHALL be constructed with exactly the same behavior as
   before the fix.

## Requirement 4: Preserve existing matrix-sum and block-matrix behavior

**User story:** As a maintainer, I want the fix to be surgical, so that all
previously-correct matrix-sum canonicalization and block-matrix operations are
unchanged.

**Acceptance criteria**
1. The system SHALL keep canonicalizing a matrix sum by removing additive-identity
   (zero-matrix) terms and ordering the remaining terms by SymPy's canonical sort,
   so equal sums compare equal regardless of the order the terms were supplied.
2. The system SHALL keep merging repeated like terms in a matrix sum into scalar
   multiples (e.g. combining a term added to itself).
3. The system SHALL keep folding explicit numeric matrix addends into a single
   explicit matrix within a matrix sum.
4. WHEN a single block collapse of a block matrix is requested, THEN the existing
   results of block addition, block multiplication, block transpose, block
   distribution, and block-plus-identity SHALL be unchanged.
5. The system SHALL keep the previously-correct results for block-matrix trace,
   determinant, square-block detection, block-diagonal handling, block cutting,
   2×2 re-blocking, and de-blocking.
6. The system SHALL keep the canonical sort key, sympification, and `doit`
   behavior of matrix sums, and SHALL keep the generic zero-matrix additive
   identity of matrix addition distinct from the scalar zero.
