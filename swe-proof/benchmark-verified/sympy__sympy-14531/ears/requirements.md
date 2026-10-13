# Requirements — StrPrinter settings must reach nested subexpressions

## Introduction

SymPy's string printer, `StrPrinter` in `sympy/printing/str.py` (exposed via the
`sstr` function and the `str()`/`__str__` protocol), accepts printer settings —
notably `sympy_integers` — that control how atoms are rendered. For example,
with `sympy_integers=True` a rational one-half renders as `S(1)/2` rather than
`1/2`.

The defect: several `_print_*` methods build their output by interpolating a
subexpression through a bare `%s` / `str()` conversion instead of routing it
back through the printer (`self._print(...)`). A bare `str()` starts a brand-new
printer at default settings, so the active settings are silently dropped for
those subexpressions. As reported in the issue:

```
>>> sstr(x + S(1)/2, sympy_integers=True)
'x + S(1)/2'          # correct
>>> sstr(Eq(x, S(1)/2), sympy_integers=True)
'Eq(x, 1/2)'          # wrong — setting ignored inside Eq
>>> sstr(Limit(x, x, S(1)/2), sympy_integers=True)
'Limit(x, x, 1/2)'    # wrong — expected 'Limit(x, x, S(1)/2)'
```

The same root cause corrupts the Python code generator `python()` in
`sympy/printing/python.py` (built on `PythonPrinter`, which subclasses
`StrPrinter`). `PythonPrinter` registers the free symbols and functions of an
expression by observing which subexpressions flow through its `_print_Symbol` /
`_print_Function` hooks. When a container printer interpolates its operands with
a bare `str()`, those hooks are never invoked, so the required
`Symbol('...')` preamble lines are omitted:

```
>>> python(Eq(x, y))
'e = Eq(x, y)'        # wrong — the x, y Symbol declarations are missing
```

Goal: every `StrPrinter` method that emits a container-style expression MUST
render each of its subexpressions through the printer itself so that (a) the
active settings propagate and (b) the `PythonPrinter` symbol/function
registration side effects fire. Behavior at default settings, and the exact
textual layout of every rendering, must otherwise be unchanged.

The affected methods in `sympy/printing/str.py` include those that print
`Relational`/equality/inequality containers, `Limit`, `Lambda`,
`AppliedPredicate`, `ExprCondPair` (piecewise pairs), `MatrixElement`, the
statistics distributions `Normal` and `Uniform`, `Permutation`,
`PermutationGroup`, and the polynomial `PolyRing` / `FracField` descriptions.

## Requirement 1: Relational/equality containers honor active settings

**User story:** As a user printing an equation or inequality with custom printer
settings, I want the settings to apply to both sides, so that the whole
expression is rendered consistently.

**Acceptance criteria**

1. WHEN a relational or (in)equality expression whose operator maps to a
   function-call form (e.g. `Eq`, `Ne`, and the augmented-assignment operators)
   is printed by `StrPrinter`, THEN the printer SHALL render each side of the
   relation by recursively invoking the printer with its currently active
   settings, rather than by a default-settings string conversion.
2. WHEN `sstr` is called with `sympy_integers=True` on an equality one of whose
   sides is a non-integer rational, THEN that rational side SHALL be rendered in
   the same `S(...)` integer form it would receive as a standalone atom under
   the same setting, rather than the default `p/q` form.
3. WHEN `sstr` is called on `Eq(x, S(1)/2)` with `sympy_integers=True`, THEN the
   result SHALL be `Eq(x, 1/2)` rendered instead as `Eq(x, S(1)/2)`.
4. The system SHALL keep the existing default rendering of relational containers:
   with default settings, an equality `Eq(x, y)` SHALL still render as
   `Eq(x, y)`, and inequalities SHALL still render in their established textual
   form (function-call form for `Eq`/`Ne`, and the infix `>=`, `<=`, `>`, `<`
   operator form for the ordering relations).

## Requirement 2: Limit containers honor active settings

**User story:** As a user printing a `Limit` with custom settings, I want the
settings to apply to the limit's subexpressions, so that the point and the
expression render consistently.

**Acceptance criteria**

1. WHEN `StrPrinter` prints a `Limit`, THEN it SHALL render the limit
   expression, the limit variable, and the limit point (and, when present, the
   direction expression) by recursively invoking the printer with the active
   settings.
2. WHEN `sstr` is called with `sympy_integers=True` on a `Limit` whose limit
   point (or any other subexpression) is a non-integer rational, THEN that
   subexpression SHALL be rendered in the `S(...)` integer form rather than the
   default `p/q` form.
3. WHEN `sstr` is called on `Limit(x, x, S(1)/2)` with `sympy_integers=True`,
   THEN the result SHALL be `Limit(x, x, S(1)/2)` (not `Limit(x, x, 1/2)`).
4. The system SHALL preserve the existing Limit output layout: when the
   direction is the default (`+`), the printed form SHALL be
   `Limit(<e>, <z>, <z0>)`; otherwise it SHALL be
   `Limit(<e>, <z>, <z0>, dir='<dir>')`, with the same argument order and
   punctuation as before.

## Requirement 3: Other container printers honor active settings

**User story:** As a user printing a variety of structured expressions with
custom settings, I want the settings to reach the operands uniformly, so that no
subexpression is silently rendered at default settings.

**Acceptance criteria**

1. The system SHALL render the subexpressions of the following `StrPrinter`
   methods by recursively invoking the printer with the active settings rather
   than by a default-settings string conversion: applied-predicate containers,
   piecewise expression/condition pairs, `Lambda` (its bound argument(s) and
   body), matrix-element indices, the `Normal` and `Uniform` distributions
   (their parameters), `Permutation` (its array form and size), the members of a
   `PermutationGroup`, and the generator/domain/order descriptions of a
   polynomial `PolyRing` and rational-function `FracField`.
2. WHEN any of these containers is printed with a non-default setting such as
   `sympy_integers=True`, THEN each rendered subexpression SHALL reflect that
   setting.
3. The system SHALL keep the outer textual template of each of these renderings
   unchanged (same surrounding function names, delimiters, keywords, and
   argument order); only the settings used for the subexpressions change.

## Requirement 4: Python code generator emits required symbol declarations

**User story:** As a user generating executable Python from a symbolic
expression, I want every free symbol to be declared, so that the emitted code
runs as-is.

**Acceptance criteria**

1. WHEN `python()` is called on an expression whose top-level node is a
   relational/equality container (e.g. `Eq(x, y)`), THEN the free symbols of
   that expression SHALL be registered and emitted as leading
   `<name> = Symbol('<name>')` declaration lines before the final assignment
   line.
2. WHEN `python(Eq(x, y))` is evaluated, THEN the result SHALL be
   `"x = Symbol('x')\ny = Symbol('y')\ne = Eq(x, y)"`.
3. WHEN `python()` is called on a relational whose sides are compound
   expressions built from free symbols, THEN every free symbol appearing
   anywhere within those compound sides SHALL be registered and emitted as a
   leading `<name> = Symbol('<name>')` declaration line before the final
   `e = ...` assignment, rather than being dropped because it is nested inside
   an operand.
4. The system SHALL keep the existing behavior for ordering-relation code
   generation: `python(Ge(x, y))`, `python(Le(x, y))`, `python(Gt(x, y))`, and
   `python(Lt(x, y))` SHALL each still emit the `x`/`y` `Symbol` declarations
   followed by the infix assignment (`e = x >= y`, `e = x <= y`, `e = x > y`,
   `e = x < y` respectively).

## Requirement 5: No regression to unaffected printing

**User story:** As a maintainer, I want the wide body of existing printing
behavior to remain intact, so that this fix changes only the mis-propagated
settings.

**Acceptance criteria**

1. The system SHALL keep all existing default-settings string output for every
   expression type unchanged; only cases where a non-default setting was
   previously dropped for a subexpression change.
2. WHEN `sstr` is called with `sympy_integers=True` on expressions that already
   rendered correctly — for instance the bare sum `x + S(1)/2` (→ `x + S(1)/2`),
   and more generally any standalone rational or any power with a rational
   exponent, whose operands already route through the printer — THEN those
   results SHALL be unchanged.
3. The system SHALL preserve the established rendering of all other structured
   expressions exercised by the printer (limits at default settings, relationals,
   matrices, sets, sums, integrals, derivatives, polynomials, permutations,
   distributions, and the full existing `python()` output for non-relational
   expressions), producing byte-for-byte the same strings as before the change
   except where a previously dropped setting now correctly propagates.
