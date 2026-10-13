# Requirements — ConditionSet substitution of free symbols

## Introduction

`sympy.sets.conditionset.ConditionSet` represents a set of the form
`{sym | condition(sym) for sym in base_set}`, where `sym` is a *bound* (dummy)
variable, `condition` is a boolean predicate, and `base_set` is the base set.

When a user substitutes a value for a symbol that appears *free* in a
`ConditionSet` (i.e. a symbol other than the bound variable `sym`, such as a
parameter appearing in the condition or the base set), the result must simply
propagate that substitution into the condition and the base set while leaving
the bound variable untouched. In particular the outcome must match the
behaviour already produced by `xreplace` and by `subs(..., simultaneous=True)`.

Prior to this change, `ConditionSet._eval_subs` (in
`sympy/sets/conditionset.py`) contained a special case for the free-symbol
substitution path: if the condition happened to evaluate to `True` after the
substitution, the method rebuilt the set using the *substituted value* as the
new bound variable and wrapped it in a `Contains(new, base)` condition. This
produced nonsensical results — e.g. substituting a numeric value into a
`ConditionSet` built over an `ImageSet` would replace the bound variable `x`
with that number and turn the condition into a membership test — instead of the
expected, straightforward propagation.

The goal is to make the free-symbol substitution path consistent: preserve the
bound variable and substitute only into the condition and base set, without any
special handling for a condition that becomes `True`. The affected module is
`sympy/sets/conditionset.py`; the affected behaviour is exposed through the
public `subs` method of `ConditionSet` (dispatched via `_eval_subs`). Existing
behaviour for substituting the bound variable itself, for finite base sets, and
for membership/equality queries must be preserved.

## Requirement 1: Substituting a free symbol preserves the bound variable

**User story:** As a user manipulating a `ConditionSet`, I want substituting a
value for a free symbol (a symbol other than the bound variable) to keep the
bound variable and simply update the condition and base set, so that the result
is a well-formed `ConditionSet` describing the same kind of set with the
parameter replaced.

**Acceptance criteria**

1. WHEN `subs` is called on a `ConditionSet` with an `old` argument that is not
   equal to the set's bound variable `sym` and `sym` is a symbolic expression,
   THEN the system SHALL assemble the result by re-invoking the `ConditionSet`
   constructor with the original bound variable `sym` (never the substituted
   value `new`) as the candidate bound variable, so that — whenever the outcome
   remains a `ConditionSet` — its bound variable is that original `sym`,
   unchanged; the final object is then subject to the ordinary construction
   semantics, so it MAY instead collapse to another form (for example the base
   set when the substituted condition is trivially true; see Requirements 1.3
   and 3.1), rather than being an unconditional guarantee that a `ConditionSet`
   retaining `sym` is always returned.
2. WHEN such a substitution is performed, THEN the system SHALL compute the new
   condition by substituting `old → new` in the original condition and the new
   base set by substituting `old → new` in the original base set, and SHALL
   assemble the result from the original `sym`, the new condition, and the new
   base set.
3. IF the condition of the `ConditionSet` evaluates to `True` after the
   substitution, THEN the system SHALL still return the set assembled from the
   original bound variable, the (now trivially true) condition, and the
   substituted base set, and SHALL NOT rebind the bound variable to `new` nor
   introduce a membership (`Contains`) condition based on `new`.
4. WHEN a value is substituted for a free symbol that appears inside the base
   set of a `ConditionSet` (for example a base set that is an image/mapped set
   parameterised by that free symbol), THEN the resulting set SHALL be
   equivalent to applying the same substitution directly to that base set,
   with the bound variable and set structure preserved.
5. The result of substituting a free symbol via `subs` SHALL be equal to the
   result obtained via `xreplace` of the same mapping and via `subs` with
   `simultaneous=True`, for the free-symbol substitution case.

## Requirement 2: Substituting the bound (dummy) variable is unchanged

**User story:** As a user, I want the established rules for substituting the
bound variable of a `ConditionSet` to keep working, so that renaming the dummy
symbol and targeting the base set continue to behave as documented.

**Acceptance criteria**

1. WHEN `subs` is called with `old` equal to the bound variable and `new` is
   not a symbol (e.g. a number), THEN the system SHALL leave the bound variable
   and condition unchanged and SHALL only apply the substitution to the base
   set.
2. WHEN `subs` replaces the bound variable with a symbol whose assumptions match
   the old symbol's assumptions (or a symbol carrying a single assumption with
   matching commutativity) AND the base set is unaffected by the substitution,
   THEN the system SHALL rename the bound variable to the new symbol and apply
   the substitution within the condition.
3. WHEN `subs` replaces the bound variable with an acceptable symbol BUT the
   base set is changed by the substitution, THEN the system SHALL apply the
   substitution to the base set while leaving the bound variable unchanged, so
   that a second substitution is required to also rename the bound variable.
4. IF the bound variable is asked to be replaced with a symbol whose
   assumptions differ from the bound variable's and that does not qualify under
   the single-assumption/matching-commutativity allowance (for example
   replacing a symbol with a non-commutative symbol or with an incompatibly
   assumed symbol), THEN the system SHALL raise a `ValueError`.
5. WHEN user-supplied assumptions on the bound variable cause the condition to
   evaluate during construction, THEN the constructed set SHALL reflect that
   collapse (an always-false condition yielding the empty set, an always-true
   condition yielding the base set), consistent with `ConditionSet`
   construction semantics.

## Requirement 3: Construction and finite base-set behaviour preserved

**User story:** As a user, I want `ConditionSet` construction and finite-base
filtering to keep behaving as before, so that this fix does not regress set
creation.

**Acceptance criteria**

1. WHEN a `ConditionSet` is constructed with a condition that is identically
   `False`, THEN the system SHALL return the empty set; and WHEN the condition
   is identically `True`, THEN the system SHALL return the base set.
2. WHEN a `ConditionSet` is constructed over a finite base set, THEN the system
   SHALL retain only those elements whose membership under the condition is not
   definitively known, dropping elements known to satisfy it into a separate
   finite set and combining the parts as appropriate.
3. WHEN a `ConditionSet` is constructed with a non-symbol dummy expression that
   does not appear in the condition, THEN the system SHALL raise a `ValueError`
   indicating the non-symbol dummy is not recognised in the condition.
4. WHEN a `ConditionSet` is nested inside another `ConditionSet` as its base
   set, THEN the system SHALL combine the conditions and, where the bound
   variables would clash between condition and base, SHALL choose a fresh bound
   variable so that the free symbols remain distinct from the bound variable.

## Requirement 4: Membership, equality, and free-symbol queries preserved

**User story:** As a user, I want membership tests, dummy-equality comparisons,
and free-symbol reporting on `ConditionSet` to remain correct, so that
downstream logic depending on them is unaffected.

**Acceptance criteria**

1. WHEN membership of a value in a `ConditionSet` is queried, THEN the system
   SHALL report membership as the conjunction of the value belonging to the
   base set and the condition holding for that value.
2. The `free_symbols` of a `ConditionSet` SHALL be the free symbols of the
   condition (excluding the bound variable) combined with the free symbols of
   the base set.
3. WHEN two `ConditionSet` instances are compared for equality up to renaming of
   the bound variable, THEN the system SHALL treat them as equal exactly when
   one becomes identical to the other after renaming its bound variable to the
   other's, and SHALL treat instances using the unsolved-equation (tuple) dummy
   form as not dummy-equal to symbol-dummy instances.
4. WHEN a `ConditionSet` is intersected with another set, THEN the system SHALL
   produce a result consistent with the set's membership semantics (the
   condition together with the base set restricted by the other set).
