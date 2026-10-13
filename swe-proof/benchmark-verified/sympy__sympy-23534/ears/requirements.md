# Requirements: `symbols` honors `cls` for nested name groups

## Introduction

`sympy.core.symbol.symbols` transforms strings (or nested collections of
strings) into symbol-like objects. Its signature accepts a keyword argument
`cls` (default `Symbol`) that selects the class of object to construct, so a
caller can build instances of `Function`, `Wild`, etc. instead of plain
symbols.

When the `names` argument is a single string, `cls` is applied to every
generated object. But when `names` is a *collection* (tuple or list) of name
specifications — the form used to group the output into separate sub-tuples,
e.g. `symbols(('q:2', 'u:2'), cls=Function)` — the function processes each
element recursively. The affected behavior is in the branch of `symbols` that
iterates over a non-string `names` collection: that recursive processing must
carry the caller's requested `cls` forward. Prior to the fix it did not, so
every object in a grouped/nested result was constructed as a plain `Symbol`
regardless of `cls`, silently ignoring the caller's intent.

The goal is that `cls` is respected uniformly whether `names` is a flat string
or a nested collection of strings, while all existing parsing, grouping,
ordering, assumption-passing, and single-string behaviors are preserved.

## Requirement 1: `cls` is respected for nested/grouped name collections

**User story:** As a user of `sympy.symbols`, I want to pass a collection of
name specifications together with `cls` and receive objects of that class in
every nested group, so that I can construct grouped `Function` (or other
symbol-like) objects and deconstruct the result into separate tuples.

**Acceptance criteria**

1. WHEN `symbols` is called with `names` being a collection (e.g. a tuple or
   list) of strings AND a `cls` keyword argument, THEN `symbols` SHALL
   construct every resulting object using that `cls` rather than the default
   `Symbol` class.
2. WHEN `symbols(('q:2', 'u:2'), cls=Function)` is called (with `Function`
   being `sympy.core.function.Function`), THEN `symbols` SHALL return a
   collection of two sub-collections, and the objects contained in each
   sub-collection SHALL be instances produced by `Function` (i.e. of type
   `sympy.core.function.UndefinedFunction`), not `Symbol`.
3. WHEN `names` is a collection and `cls` is not supplied, THEN `symbols` SHALL
   construct the objects using the default `Symbol` class (unchanged default
   behavior).
4. WHEN `names` is a nested collection, THEN each element SHALL be processed
   with the same `cls` at every level of nesting, so that no group is
   constructed with a different class than any other group.

## Requirement 2: Grouping structure, ordering, and assumptions are preserved for collections

**User story:** As a user relying on the grouped form of `symbols`, I want the
returned structure, element order, and per-object assumptions to stay exactly
as before, so that adding `cls` support does not change any other behavior.

**Acceptance criteria**

1. WHEN `names` is a collection of specifications, THEN `symbols` SHALL return
   a result whose outer container type matches the type of the input
   collection, with one entry per input element in the same order.
2. WHEN an element of the `names` collection is itself a range/multi-name
   specification, THEN `symbols` SHALL expand it into a sub-collection whose
   contents and order match what the equivalent single-string call would
   produce.
3. WHEN additional keyword assumption arguments (for example `real=True`,
   `integer=True`) are supplied alongside a collection, THEN `symbols` SHALL
   apply those assumptions to every constructed object.

## Requirement 3: Single-string behavior is unchanged (regression protection)

**User story:** As an existing user of `symbols` with string arguments, I want
all current string-parsing behavior to keep working identically, so that the
`cls`-forwarding fix introduces no regression.

**Acceptance criteria**

1. The system SHALL continue to construct objects of the requested `cls` when
   `names` is a single string (e.g. `symbols('f,g,h', cls=Function)` yields
   `Function`-produced objects).
2. WHEN `names` is a single string containing comma- or space-separated names
   and range specifications (colon ranges, lettered ranges, parenthesized
   ranges, escaped separators), THEN `symbols` SHALL expand and order the names
   exactly as it did before this change.
3. WHEN a single-string call resolves to exactly one name and is not forced to
   be a sequence, THEN `symbols` SHALL return that single object rather than a
   one-element tuple, preserving the existing scalar-versus-sequence contract.
4. The system SHALL continue to apply supplied assumption keyword arguments to
   objects created from a single string.
5. The system SHALL continue to raise the existing errors for malformed input
   (for example an empty specification or a range missing its end).
