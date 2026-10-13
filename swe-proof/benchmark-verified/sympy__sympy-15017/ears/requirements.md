# Requirements — `len` of rank-0 arrays

## Introduction

SymPy's N-dimensional array types (`sympy.tensor.array`, principally the dense
implementations `ImmutableDenseNDimArray` / `MutableDenseNDimArray` in
`sympy/tensor/array/dense_ndim_array.py`, with the shared `NDimArray` base in
`sympy/tensor/array/ndim_array.py`) represent a tensor by a flat list of
elements plus a `shape` tuple of dimension sizes. The number of stored elements
equals the product of the dimension sizes.

A rank-0 array is a scalar: its `shape` is the empty tuple `()`, and it holds
exactly one element. Because the element count is derived by folding
multiplication over the dimension tuple, the empty-product case (rank-0) was
computed as `0` instead of the mathematically correct `1`. As a result
`len(sympy.Array(3))` returned `0` even though iterating the array yields one
element (`len(list(sympy.Array(3))) == 1`), diverging from the analogous NumPy
behavior where a scalar array has size `1`.

The goal is to make the derived element count of the immutable dense array type
(`sympy.Array` / `ImmutableDenseNDimArray`) treat a rank-0 array as containing
exactly one element (the empty product is `1`), so that `len`, element access,
and iteration are mutually consistent for that type, while leaving the element
count of every array with at least one dimension unchanged. The corrected rank-0
element count is a property of the immutable dense array; other array types
(e.g. the mutable dense or sparse implementations) are outside the scope of this
change.

## Requirement 1: Rank-0 (scalar) array reports a length of one

**User story:** As a user creating a scalar N-dim array, I want `len` to report
one element, so that the length is consistent with iterating the array and with
NumPy's notion of a scalar's size.

**Acceptance criteria**

1. WHEN an immutable dense array (`sympy.Array` / `ImmutableDenseNDimArray`) is
   constructed with no dimensions (a rank-0 array, e.g.
   `ImmutableDenseNDimArray(x)` for a scalar `x`, whose `shape` is `()`),
   THEN calling `len(...)` on it SHALL return `1`.
2. WHEN a rank-0 immutable dense array is constructed, THEN its `shape` property
   SHALL be the empty tuple `()` and its `rank()` SHALL be `0`.
3. WHEN a rank-0 immutable dense array is iterated (e.g. `list(arr)`), THEN it
   SHALL yield exactly one element, and that element count SHALL equal the value
   returned by `len(...)`.

## Requirement 2: Scalar element is accessible by integer index and by empty tuple

**User story:** As a user of a scalar N-dim array, I want to retrieve its single
element by indexing, so that access is consistent with the array having one
element.

**Acceptance criteria**

1. WHEN a rank-0 immutable dense array holding scalar value `x` is indexed with
   the empty tuple (`arr[()]`), THEN it SHALL return `x`.
2. WHEN a rank-0 immutable dense array holding scalar value `x` is indexed with
   integer `0` (`arr[0]`), THEN it SHALL return `x` and SHALL NOT raise an error.
3. The system SHALL treat a rank-0 immutable dense array as holding exactly one
   addressable element, so that the range of valid flat integer indices is
   exactly `{0}`.

## Requirement 3: Empty-dimension and populated arrays keep their existing element counts

**User story:** As a user relying on array lengths, I want arrays that have one
or more dimensions to report the same length as before, so that the rank-0 fix
introduces no regression for other shapes.

**Acceptance criteria**

1. WHEN a dense N-dim array is constructed with a shape that contains a zero
   dimension (e.g. an empty array with `shape=(0,)`), THEN `len(...)` SHALL
   return `0` and `rank()` SHALL return the number of given dimensions (e.g. `1`
   for `shape=(0,)`).
2. WHEN a dense N-dim array is constructed with a shape whose dimensions are all
   positive, THEN `len(...)` SHALL return the product of the dimension sizes
   (e.g. `1` for a single-element array, `9` for `shape=(3, 3)`).
3. The system SHALL derive the reported element count as the product of the
   dimension sizes for every array, where the product over an empty dimension
   tuple is `1`.

## Requirement 4: Consistency of length across construction, iteration, reshaping, and arithmetic

**User story:** As a user manipulating N-dim arrays, I want length, iteration,
reshaping, and elementwise operations to remain mutually consistent, so that
existing array workflows continue to behave correctly.

**Acceptance criteria**

1. The system SHALL keep `len(arr)` equal to the number of elements produced by
   iterating `arr` for every array with one or more dimensions, and
   additionally for the rank-0 immutable dense array
   (`sympy.Array` / `ImmutableDenseNDimArray`).
2. WHEN an array is reshaped to a new shape whose dimension product equals its
   current element count, THEN the reshape SHALL succeed and the result SHALL
   report the same `len(...)`; IF the new shape's dimension product differs from
   the current element count, THEN reshaping SHALL NOT silently produce a
   mismatched array and SHALL instead raise an error.
3. The system SHALL keep unchanged the existing behavior of construction from
   nested lists, sparse arrays, elementwise arithmetic, equality, slicing,
   symbolic indexing, differentiation, `applyfunc`, and conversion helpers for
   all arrays with one or more dimensions.
