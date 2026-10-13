# Requirements: Evaluating powers of tensor product expressions

## Introduction

In `sympy.physics.quantum.tensorproduct`, the simplification routine
`tensor_product_simp` (with its helper `tensor_product_simp_Mul`) is intended to
pull scalar and operator factors inside `TensorProduct` objects and to combine
adjacent tensor products. Before this change it silently failed on any
expression that contained a **power** whose base is a `TensorProduct`: raising a
tensor product to an exponent, multiplying such a power by scalars or other
tensor products, or embedding it in a sum all left the expression essentially
unevaluated (e.g. a tensor product raised to a power was returned unchanged, and
the product `tp(1,1)*tp(1,1)` from the issue could not be reduced).

The goal is to make `tensor_product_simp` evaluate powers of tensor products by
distributing the exponent across each factor of the tensor product, both when a
power appears on its own, when it appears as a factor of a product together with
scalars and other tensor products, and when it appears inside a sum — while
preserving every simplification the routine already performed. The affected code
lives entirely in `sympy/physics/quantum/tensorproduct.py`; the public entry
point is `tensor_product_simp` (also exposed as
`sympy.physics.quantum.tensor_product_simp`).

Throughout this document, "distributing an exponent across a tensor product"
means: given a tensor product with factors `f1, f2, …, fk` and an exponent `e`,
producing the tensor product whose factors are `f1**e, f2**e, …, fk**e`.

## Requirement 1: Evaluate a standalone power of a tensor product

**User story:** As a user simplifying quantum-mechanical expressions, I want a
tensor product raised to a power to be evaluated by distributing the exponent
across its factors, so that `(a ⊗ b)**n` becomes `(a**n) ⊗ (b**n)` instead of
remaining an opaque power.

**Acceptance criteria**

1. WHEN `tensor_product_simp` is called on a power whose base is a
   `TensorProduct`, THEN the function SHALL return a single `TensorProduct` whose
   ordered factors are each of the original base factors raised to the original
   exponent.
2. WHEN the exponent is a symbolic quantity, THEN the function SHALL still
   distribute that exact exponent onto every factor (e.g. a tensor product with
   two factors raised to a symbol `x` yields a tensor product of those two
   factors each raised to `x`).
3. WHEN the exponent is a concrete positive integer, THEN the function SHALL
   distribute that integer exponent onto every factor.
4. The distribution SHALL preserve the number and order of the factors of the
   original tensor product.

## Requirement 2: Evaluate powers of tensor products appearing within a product

**User story:** As a user, I want products that mix scalars, powers of tensor
products, and plain tensor products to be combined into a single tensor product,
so that such an expression collapses to a scalar coefficient times one tensor
product.

**Acceptance criteria**

1. WHEN `tensor_product_simp` is called on a product whose only non-commutative
   factor is a power of a tensor product, THEN the function SHALL return the
   commutative (scalar) factors multiplied by the tensor product obtained by
   distributing the exponent across that tensor product's factors.
2. WHEN a product contains a power of a tensor product alongside one or more
   plain tensor products (and optional scalar factors), THEN the function SHALL
   first distribute each power's exponent across its factors and then combine all
   the resulting tensor products factor-by-factor into a single tensor product,
   multiplying the position-`i` factors of each in their original left-to-right
   order.
3. WHEN combining tensor products under criterion 2, THEN the scalar (commutative)
   factors SHALL be preserved as an overall multiplicative coefficient in front of
   the resulting single tensor product.
4. IF the non-commutative factors of the product do not all share the same number
   of tensor-product factors, THEN the function SHALL signal an error rather than
   produce a mismatched tensor product.
5. IF a non-commutative factor of the product is neither a tensor product nor a
   power whose base is a tensor product, THEN the function SHALL raise a
   `TypeError` rather than silently absorbing that factor into the tensor product.

## Requirement 3: Evaluate powers of tensor products appearing within a sum

**User story:** As a user, I want sums that contain powers of tensor products to
be simplified term-by-term, so that each power term is evaluated while the other
terms are left intact.

**Acceptance criteria**

1. WHEN `tensor_product_simp` is called on a sum (an `Add`), THEN the function
   SHALL apply the same simplification to each addend and return the sum of the
   simplified addends.
2. WHEN an addend is a power of a tensor product, THEN that addend SHALL be
   evaluated by distributing the exponent across the tensor product's factors,
   while addends that are plain tensor products SHALL be returned unchanged.

## Requirement 4: Leave non-tensor-product powers and other expressions unchanged

**User story:** As a user, I want the routine to only rewrite powers whose base
is a tensor product, so that unrelated expressions are not corrupted.

**Acceptance criteria**

1. IF `tensor_product_simp` is called on a power whose base is not a
   `TensorProduct`, THEN the function SHALL simplify the base and re-apply the
   original exponent, without attempting to distribute the exponent as a tensor
   product.
2. IF `tensor_product_simp` is called on an expression that is not a sum,
   product, power, commutator, or anticommutator (for example an atom or a bare
   tensor product), THEN the function SHALL return that expression unchanged.
3. The helper that distributes an exponent across a tensor product SHALL return
   its input unchanged when that input is not a power whose base is a tensor
   product.

## Requirement 5: Preserve existing tensor-product simplifications (regression protection)

**User story:** As a maintainer, I want all previously supported simplifications
to continue to work exactly as before, so that adding power support does not
regress existing behavior.

**Acceptance criteria**

1. WHEN `tensor_product_simp` is called on a product of two tensor products of
   equal length, THEN the function SHALL combine them into a single tensor
   product whose position-`i` factor is the product of the two position-`i`
   factors.
2. WHEN `tensor_product_simp` is called on a commutator or anticommutator, THEN
   the function SHALL apply the simplification to each argument and return a
   commutator or anticommutator, respectively, of the simplified arguments.
3. The system SHALL preserve the existing behavior of expanding a tensor product
   over sums via `expand(tensorproduct=True)`, so that a tensor product with a
   sum argument is expanded into a sum of tensor products.
4. The system SHALL preserve the existing distinction between commutative
   (scalar) and non-commutative arguments of a `TensorProduct`, pulling scalar
   arguments out in front of the tensor product.
5. WHEN `tensor_product_simp` is applied to a product of tensor products that has
   no power factor, THEN the function SHALL produce the same result it produced
   before this change (no regression for the power-free path).
6. The system SHALL keep the existing behavior used by density-matrix and trace
   simplifications that rely on `tensor_product_simp`, so that those computations
   continue to yield their previously correct results.
