# Requirements: Preserve symbol assumptions in `posify`

## Introduction

`posify` (in `sympy/simplify/simplify.py`) rewrites an expression so that every
free symbol whose sign is not already known is replaced by a brand‑new dummy
symbol asserted to be positive, returning the rewritten expression together with
a mapping that can restore the original symbols via `subs`. This lets downstream
simplification (powers, logarithms, etc.) proceed on generically‑positive
symbols.

The problem: when building the positive replacement symbol, `posify` declares it
with *only* `positive=True`. As a result every other assumption the original
symbol carried — `finite`, `integer`, `rational`, `prime`, `even`, `odd`, and so
on — is silently dropped. For example, a symbol declared `finite=True` loses its
finiteness after `posify`, so `is_finite` becomes indeterminate on the
replacement.

The goal is to make `posify` **preserve all of the original symbol's declared
assumptions** on the positive replacement symbol, while keeping every other
existing behavior (which symbols get replaced, the restoration mapping, iterable
handling, name preservation) unchanged.

## Requirement 1: Preserve original assumptions on the replacement symbol

**User story:** As a user of `posify`, I want the positive dummy that replaces a
symbol to keep all the assumptions the original symbol declared, so that
downstream reasoning that relies on properties like finiteness or integrality is
not silently invalidated.

**Acceptance criteria**

1. WHEN `posify` replaces a free symbol whose sign is undetermined, THEN the
   system SHALL create the replacement dummy symbol declared with `positive=True`
   **together with** every assumption present on the original symbol.
2. WHEN the original symbol carries an assumption such as `finite`, `integer`,
   `rational`, `prime`, `even`, or `odd`, THEN the replacement symbol SHALL carry
   that same assumption (and everything it entails) after replacement.
3. WHEN a symbol declared `finite=True` is passed to `posify`, THEN the
   replacement symbol's resolved assumptions SHALL report `finite` as `True` (and
   `infinite` as `False`), in addition to reporting `positive` as `True`.
4. The replacement symbol's full set of resolved assumptions SHALL be exactly
   what a freshly declared symbol having the original symbol's declared
   assumptions plus `positive=True` would entail — i.e. the declared properties
   together with all of their logical consequences (`real`, `nonnegative`,
   `nonzero`, `hermitian`, `complex`, and the corresponding negatives), with no
   original property discarded.
5. IF adding `positive=True` to the original assumptions would contradict a
   determined sign, THEN this situation SHALL NOT arise, because a symbol is only
   replaced when its positivity is undetermined (see Requirement 2).

## Requirement 2: Replace only sign‑undetermined symbols

**User story:** As a user of `posify`, I want only symbols with an unknown sign
to be rewritten, so that symbols already known to be positive, negative, or
otherwise sign‑determined are left untouched.

**Acceptance criteria**

1. WHEN a free symbol has `is_positive` equal to `None` (its positivity is
   undetermined), THEN `posify` SHALL replace it with a positive dummy symbol.
2. IF a free symbol already has a determined positivity (for example it was
   declared positive or negative), THEN `posify` SHALL leave that symbol
   unchanged and SHALL NOT include it in the returned mapping.
3. The system SHALL preserve any other symbols in the expression (those it does
   not replace) exactly as they appear.

## Requirement 3: Preserve the restoration mapping and name

**User story:** As a user of `posify`, I want the returned mapping and dummy
names to behave as before, so that I can restore the original expression and keep
using existing code.

**Acceptance criteria**

1. WHEN `posify` returns, THEN it SHALL return a two‑element result: the rewritten
   expression and a dictionary mapping each replacement dummy symbol back to the
   original symbol it replaced.
2. WHEN the returned mapping is applied to the rewritten expression via `subs`,
   THEN the original expression SHALL be recovered.
3. WHEN a symbol is replaced, THEN its replacement dummy SHALL carry the same name
   as the original symbol.

## Requirement 4: Preserve support for iterables of expressions

**User story:** As a user of `posify`, I want to pass a list (or other iterable)
of expressions and have all shared symbols rewritten consistently, so that
existing multi‑expression workflows keep working.

**Acceptance criteria**

1. WHEN `posify` is given an iterable of expressions, THEN it SHALL return the
   iterable of rewritten expressions (of the same container type) together with a
   single restoration mapping.
2. WHEN a symbol appears in more than one expression of the iterable, THEN the
   system SHALL replace it consistently with the same dummy across all
   expressions.
3. The assumption‑preservation behavior of Requirement 1 SHALL apply equally to
   symbols replaced within an iterable of expressions.

## Requirement 5: Preserve established simplification behavior (regression guard)

**User story:** As a maintainer, I want the documented behaviors of `posify` and
of the simplification routines it interacts with to remain intact, so that
fixing the assumption loss introduces no regressions.

**Acceptance criteria**

1. The system SHALL keep the documented `posify` behaviors: rewriting only
   sign‑undetermined symbols to positive dummies, enabling expansions such as
   `log(1/x)` to expand to `-log(_x)`, and supporting round‑trip restoration
   through the returned mapping.
2. WHEN existing expressions containing already sign‑determined symbols alongside
   undetermined ones are posified, THEN only the undetermined symbols SHALL be
   rewritten and the determined ones SHALL remain.
3. The system SHALL keep all other `simplify`‑module behaviors unchanged; the
   assumption‑preservation change SHALL be confined to how `posify` builds its
   replacement symbols and SHALL NOT alter unrelated simplification results.
