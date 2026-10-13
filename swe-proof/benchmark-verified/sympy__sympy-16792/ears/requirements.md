# Requirements: correct code generation for array arguments absent from the expression

## Introduction

`sympy.utilities.codegen` turns a symbolic expression and a list of arguments
into source code for a callable routine (for example the C code produced by
`CCodeGen`, and consumed downstream by `sympy.utilities.autowrap`). The public
entry point `codegen` and the underlying `CodeGen.routine` build a `Routine`
whose input arguments are described by metadata; an argument that represents an
array (a `MatrixSymbol`, or an `IndexedBase`/its label) must carry
per-dimension index-bound metadata so it is emitted as a pointer/array in the
generated signature, whereas a plain scalar argument carries none and is
emitted by value.

A defect appears when the caller pins the argument order explicitly (via the
`argument_sequence` parameter of `codegen` / `CodeGen.routine`) and one of the
requested arguments is a matrix-valued argument (a `MatrixSymbol`) but does
**not** occur anywhere in the expression being generated. In that situation the
argument is created without any dimension metadata and is therefore emitted as
a scalar (e.g. `double x` instead of `double *x` in C). This produces an
incorrect signature and makes the compiled function reject array inputs, even
though such padding arguments are legitimate when a fixed signature must be
presented to external code.

The goal is to make an explicitly-sequenced `MatrixSymbol` argument that is
absent from the expression carry the same index-bound metadata — and thus the
same pointer/array emission — as an array-valued argument that does occur in the
expression, while leaving every other code-generation behavior unchanged.

## Requirement 1: Array arguments absent from the expression are emitted as arrays

**User story:** As a user generating code with a fixed, caller-defined argument
order, I want an array argument that is required by the signature but unused in
the expression to still be treated as an array, so that the generated function
accepts array inputs and matches the intended interface.

**Acceptance criteria**

1. WHEN a routine is built with an explicit argument sequence and that sequence
   contains a `MatrixSymbol` argument that does not appear anywhere in the
   expression, THEN `CodeGen.routine` SHALL include that argument in the
   resulting routine's input arguments carrying per-dimension index-bound
   metadata derived from the argument's shape.
2. WHEN such a `MatrixSymbol` argument has shape sizes `d_1, …, d_k`, THEN the
   argument's index-bound metadata SHALL be, for each axis in order, the
   inclusive range from `0` to that axis size minus one.
3. WHEN C source is generated for a routine that has a `MatrixSymbol` argument
   absent from the expression, THEN the generated function signature SHALL
   declare that argument as a pointer to the element type (for example
   `double *x`) rather than as a by-value scalar (for example `double x`).
4. IF an argument required by the explicit argument sequence is absent from the
   expression and is a plain scalar (not array-valued), THEN the routine SHALL
   include it with no index-bound metadata and it SHALL be emitted as a by-value
   scalar.

## Requirement 2: Correctness of the routine body and returned value are preserved

**User story:** As a user, I want the padding of an unused array argument to
change only the argument's declared shape, so that the computed result is
unaffected.

**Acceptance criteria**

1. WHEN an expression that is a constant (does not reference any of the supplied
   arguments) is generated with an explicit argument sequence, THEN the routine
   SHALL still return that constant value as its result and SHALL declare each
   requested argument in the requested order.
2. The system SHALL keep the ordering of the routine's arguments identical to
   the order given in the explicit argument sequence.
3. WHEN generating the routine, THEN the presence or shape of an argument that
   is unused in the expression SHALL NOT alter the body statements or the
   returned/result value computed from the expression.

## Requirement 3: Existing code-generation behavior is unchanged (regression protection)

**User story:** As a maintainer, I want all previously-correct code generation
to keep working, so that the fix introduces no regressions.

**Acceptance criteria**

1. WHEN an array-valued argument does occur in the expression, THEN it SHALL
   continue to be emitted with per-dimension index-bound metadata (as a
   pointer/array), exactly as before.
2. WHEN a scalar argument occurs in the expression, THEN it SHALL continue to be
   emitted as a by-value scalar.
3. WHEN no explicit argument sequence is supplied, THEN argument metadata and
   ordering SHALL be determined as before from the expression's symbols, with
   array-valued symbols carrying index-bound metadata and scalar symbols
   carrying none.
4. WHEN an explicit argument sequence requests an argument that is not part of
   the routine at all, THEN `CodeGen.routine` SHALL raise the existing
   argument-list error identifying the missing argument.
5. The system SHALL preserve the existing handling of output and in/out
   arguments, matrix and matrix-slice results, indexed/loop expressions, and
   the generation of both C and Fortran source, unchanged.
6. WHEN a routine's arguments include a mix of scalar and array-valued
   arguments, THEN each argument that occurs in the expression SHALL receive
   index-bound metadata if and only if it is array-valued; and among arguments
   requested by the explicit sequence that do not occur in the expression, a
   `MatrixSymbol` SHALL receive per-dimension index-bound metadata while a plain
   scalar SHALL receive none.
