# Requirements: `srepr` of `dict` and `set` containers

## Introduction

The `srepr` function (defined in `sympy/printing/repr.py`, backed by the
`ReprPrinter` class) produces the SymPy "representation" string for an object:
a string that, when evaluated in an appropriate namespace, reconstructs the
object. `ReprPrinter` already handles Python `list` and `tuple` containers by
recursively applying `srepr` to each element (e.g. `srepr([x, y])` yields
`[Symbol('x'), Symbol('y')]`).

However, when given a Python `dict` or a Python `set`, `ReprPrinter` falls
through to its generic fallback and emits the plain `str`/`repr` of the
container, so its SymPy elements are printed with their short form rather than
their `srepr` form. For example `srepr({x: y})` returns `{x: y}` and
`srepr({x, y})` returns `{x, y}`, neither of which is a valid `srepr` string.

The goal is to make `ReprPrinter` (and therefore `srepr`) render `dict` and
`set` containers the same way it renders `list` and `tuple`: as a container
whose elements are themselves rendered by `srepr`, while preserving all
existing behavior for the container types and objects already supported.

## Requirement 1: `srepr` of a Python `dict`

**User story:** As a user calling `srepr` on a Python dictionary of SymPy
objects, I want each key and value rendered in `srepr` form inside dictionary
syntax, so that the result is a valid, round-trippable representation of the
dictionary.

**Acceptance criteria**

1. WHEN `srepr` is called on a non-empty Python `dict`, THEN the system SHALL
   return a string that begins with `{` and ends with `}`.
2. WHEN `srepr` is called on a non-empty Python `dict`, THEN for each entry the
   system SHALL render `<key-repr>: <value-repr>` where `<key-repr>` and
   `<value-repr>` are exactly the strings `srepr` produces for that key object
   and that value object respectively.
3. WHEN `srepr` is called on a `dict` with more than one entry, THEN the system
   SHALL join the rendered entries with `, ` (comma followed by a single space).
4. WHEN `srepr` is called on an empty `dict`, THEN the system SHALL return the
   string `{}`.
5. WHEN a `dict` value (or key) is itself a Python `dict`, THEN the system
   SHALL render that nested container by the same rules, so that nesting is
   handled recursively (e.g. a dict mapping a symbol to another single-entry
   dict renders as `{Symbol('x'): {Symbol('y'): Symbol('z')}}`).
6. WHEN `srepr` is called on a `dict` whose keys/values are SymPy `Symbol`
   objects, THEN each such symbol SHALL be rendered as `Symbol('<name>')`
   (its existing `srepr` form), not as its bare name.
7. WHEN `srepr` is called on a `dict` with more than one entry, THEN the system
   SHALL preserve the dictionary's own iteration order of entries in the output
   (the requirement does not impose any re-ordering of entries).

## Requirement 2: `srepr` of a Python `set`

**User story:** As a user calling `srepr` on a Python set of SymPy objects, I
want each element rendered in `srepr` form inside set syntax, so that the
result is a valid representation of the set.

**Acceptance criteria**

1. WHEN `srepr` is called on a non-empty Python `set`, THEN the system SHALL
   return a string that begins with `{` and ends with `}`.
2. WHEN `srepr` is called on a non-empty Python `set`, THEN the system SHALL
   render each element as exactly the string `srepr` produces for that element
   object, and SHALL join the rendered elements with `, ` (comma followed by a
   single space).
3. WHEN `srepr` is called on an empty `set`, THEN the system SHALL return the
   string `set()` (and SHALL NOT return `{}`, which denotes an empty dict).
4. WHEN `srepr` is called on a `set` of SymPy `Symbol` objects, THEN each
   element SHALL be rendered as `Symbol('<name>')` (its existing `srepr` form),
   not as its bare name.
5. WHILE the order in which a `set`'s elements are iterated is not defined, the
   system SHALL render every element of the set exactly once, so that the
   output is a valid rendering for any element ordering the set produces.

## Requirement 3: Preserve existing `srepr` behavior (regression protection)

**User story:** As a maintainer, I want the existing `srepr` behavior for all
already-supported inputs to remain unchanged, so that adding `dict`/`set`
support introduces no regressions.

**Acceptance criteria**

1. WHEN `srepr` is called on a Python `list`, THEN the system SHALL keep
   rendering it as `[` + `srepr`-rendered elements joined by `, ` + `]`
   (e.g. `srepr([x, y])` remains `[Symbol('x'), Symbol('y')]`).
2. WHEN `srepr` is called on a Python `tuple`, THEN the system SHALL keep
   rendering it in its existing tuple form with `srepr`-rendered elements.
3. The system SHALL keep producing the existing `srepr` output for SymPy
   scalar objects such as `Integer`, `Rational`, `Float`, `Symbol`, `Dummy`,
   and `Wild`.
4. The system SHALL keep producing the existing `srepr` output for SymPy
   expression and structured objects, including `Function`/`WildFunction`
   applications, `Matrix` (including empty matrices), matrix expressions,
   geometry objects, permutations and cycles, polynomial/field/domain objects,
   algebraic numbers, boolean atoms, the integer/natural/real set singletons,
   and named singletons.
5. The system SHALL continue to honor the printer's configuration settings
   (such as element ordering options) for the objects that already respect
   them, and SHALL keep the custom-print-method mechanism working for objects
   that define their own representation hook.
6. WHEN `srepr` is called on any input type it already supported before this
   change, THEN the system SHALL produce byte-for-byte the same output as
   before.
