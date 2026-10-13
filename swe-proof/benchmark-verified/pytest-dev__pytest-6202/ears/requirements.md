# Requirements: Faithful module-relative dotted path for test items

## Introduction

When pytest describes a collected test item — in the failure headline of a
report, in test-discovery output, and elsewhere — it identifies the item by a
dotted path relative to the item's containing module. That path is produced by
the `getmodpath` method of the Python-item base class in
`src/_pytest/python.py` (the `PyobjMixin.getmodpath` helper, consumed via
`reportinfo` in the same module and, ultimately, by report-headline
construction in `src/_pytest/reports.py`).

`getmodpath` assembles the path from the chain of enclosing scope names — the
module name, class names, the function name, and, for a parametrized test, the
parametrization identifier — collected by walking the node's ancestor chain.

There is a defect: after joining the scope names into a dotted string,
`getmodpath` applies a final textual rewrite that replaces the two-character
sequence `.[` with `[` anywhere in the assembled string. This rewrite is not
scoped to any structural boundary, so it also mutates the *contents* of a
parametrization identifier that happens to contain a `.` immediately followed
by a `[`. For example, a test whose parametrization id is `..[` is reported as
`...[.[]` — one character of the id is silently dropped — instead of the
correct `...[..[]`. The same corruption is what breaks external test-discovery
consumers.

The goal is to make `getmodpath` produce the path as an exact join of the
enclosing scope names with `.` as the separator, preserving every name's
characters verbatim, so that parametrization identifiers containing brackets
and dots survive unchanged. The affected module is `src/_pytest/python.py`; the
behavior is observed through `getmodpath` directly and through the item name of
a collected item.

## Requirement 1: Dotted path is an exact join of scope names

**User story:** As a pytest user reading a report headline or discovery output,
I want a test item's module-relative path to be exactly the join of its
enclosing scope names, so that the reported identifier matches the test's real
identity.

**Acceptance criteria**

1. WHEN `getmodpath` is called for a collected item, THEN it SHALL return the
   sequence of enclosing scope names, ordered from outermost to innermost,
   joined into a single string using a single `.` between consecutive names.
2. The returned string SHALL contain each contributing scope name verbatim,
   with no characters added, removed, or rewritten beyond the `.` separators
   inserted between names.
3. IF the assembled path contains the substring `.[` as a natural consequence
   of joining a name that ends before a bracketed name, or as part of a scope
   name's own characters, THEN `getmodpath` SHALL leave that substring
   unchanged (it SHALL NOT replace `.[` with `[`).
4. WHEN there is exactly one contributing scope name, THEN `getmodpath` SHALL
   return that name unchanged with no separators.

## Requirement 2: Parametrization identifiers are preserved literally

**User story:** As a user parametrizing a test with an id that contains
punctuation, I want that id reported exactly as-is, so that discovery tools and
report headlines can round-trip the item's identity.

**Acceptance criteria**

1. WHEN a collected item is parametrized, THEN its item name SHALL be the
   function name immediately followed by the parametrization identifier
   enclosed in square brackets, with the identifier's characters preserved
   verbatim.
2. WHEN `getmodpath` is called for a parametrized item, THEN the innermost
   segment of the returned path SHALL be that same bracketed function-plus-id
   token, preserved verbatim.
3. IF a parametrization identifier contains a `.` immediately followed by a `[`
   (for example an id such as `.[` or `..[`), THEN both the item name and the
   `getmodpath` result SHALL retain that `.` character rather than dropping it.

## Requirement 3: Scope selection and module boundary

**User story:** As a user, I want the dotted path to reflect the item's real
enclosing scopes (classes and function) without spurious internal wrapper
nodes, so that the path reads as `Class.method` and, by default, is relative to
the module.

**Acceptance criteria**

1. WHEN building the path, THEN `getmodpath` SHALL include the names of the
   item's enclosing class scope(s) and its function scope.
2. WHEN walking the ancestor chain, THEN `getmodpath` SHALL skip internal
   instance wrapper nodes so their names do not appear in the path (a class
   method is reported as `<ClassName>.<methodName>`, not with an intervening
   wrapper segment).
3. WHILE `stopatmodule` is true and `includemodule` is false (the defaults),
   `getmodpath` SHALL stop at the containing module and SHALL NOT include the
   module name in the returned path.
4. WHEN `getmodpath` is called with `stopatmodule` false, THEN the returned
   path SHALL include the module name as its outermost segment, so the result
   ends with `<module>.<...>.<item>`.
5. WHEN a test method is defined in a base class but collected through a
   subclass, THEN the class segment of its path SHALL be the subclass through
   which it was collected.

## Requirement 4: Preserve existing collection and reporting behavior

**User story:** As a maintainer, I want the correction to change only the
erroneous path rewrite, so that unrelated collection and reporting behavior
keeps working.

**Acceptance criteria**

1. The system SHALL keep producing correct dotted paths for ordinary,
   non-parametrized items whose names contain no `.[` sequence (for example a
   top-level function reported as its bare name, and a class method reported as
   `<ClassName>.<methodName>`).
2. WHEN a module collects several items, THEN each item's item name and
   `getmodpath` result SHALL be computed independently and reflect that item's
   own enclosing scopes.
3. The system SHALL continue to collect the expected set of items from a module
   (top-level functions, methods of test classes, and methods inherited into
   subclasses) without dropping or duplicating items as a result of this
   change.
4. The system SHALL continue to expose the module-relative path through the
   item's report information so that report headlines and discovery output use
   the corrected path.
