# Requirements: Correct relational-lookup permission checking in the admin change list

## Introduction

Django's admin change list decides whether a requested filter (a "lookup") is
permitted before applying it. This decision lives in
`ModelAdmin.lookup_allowed(self, lookup, value)` in
`django/contrib/admin/options.py`.

A lookup is a `__`-separated chain of components (for example
`restaurant__place__country`) that is walked left-to-right across the model
graph. As it walks, the method accumulates the subset of components that name a
genuine relational *hop* — the "relation parts" — and finally checks whether the
accumulated relation parts (with or without the trailing component) correspond to
one of the filters the admin has declared in `list_filter` (plus
`date_hierarchy`). Components are deliberately dropped from the relation parts
when the value they name would already be reachable from the previous model's own
local column, so that two syntactically different chains that reach the *same*
stored value are treated as equivalent.

The affected behavior is the rule that decides whether a component is counted as
a fresh relational hop or is folded into the local model. The previous rule
dropped a component whenever the resolved field was one of the previous
relation's target fields. This is wrong when a model's **primary key is itself a
foreign key** (for example a `OneToOneField(..., primary_key=True)`): such a
model has no separate synthesised auto primary key, and its primary-key relation
is a genuine hop to another model, not a value already carried locally. Treating
it as local shortened the chain to a form that cannot be declared in
`list_filter`, so a legitimately declared filter such as
`restaurant__place__country` was incorrectly rejected with
`DisallowedModelAdminLookup`.

The goal is to make `lookup_allowed` count such a primary-key foreign-key
component as a real relational hop, so that filters declared on chains passing
through a foreign-key-as-primary-key model are permitted, while preserving the
existing collapsing behavior for concrete-inheritance parent links and for
components whose value is genuinely local to a model that does have its own
synthesised primary key.

## Requirement 1: Count a foreign-key-as-primary-key hop as a real relation part

**User story:** As an admin developer who declares a `list_filter` entry that
traverses a model whose primary key is a foreign key, I want that filter to be
permitted, so that the change list works instead of raising
`DisallowedModelAdminLookup`.

**Acceptance criteria**

1. WHEN `lookup_allowed` walks a lookup chain and reaches a component that
   resolves to a relational field on a model that has **no** synthesised
   automatic primary key (its primary key is itself a relation, e.g. a
   `OneToOneField(..., primary_key=True)`), THEN `lookup_allowed` SHALL count
   that component as a relation part rather than folding it into the previous
   model.
2. WHEN a declared `list_filter` chain passes through such a
   foreign-key-as-primary-key model (for example a chain of the shape
   parent-relation → primary-key-relation → further-relation), THEN
   `lookup_allowed` SHALL return `True` for that exact declared chain.
3. WHEN the requested lookup is the declared chain extended by a trailing
   component or transform on its final field (for example the declared relational
   chain followed by an id/exact-style suffix, or followed by a further declared
   field), THEN `lookup_allowed` SHALL return `True`.
4. The system SHALL, for a chain that traverses a foreign-key-as-primary-key
   model, accumulate every traversed relational component as a distinct relation
   part so that the accumulated relation parts reproduce the full declared chain
   rather than a shortened one.

## Requirement 2: Preserve collapsing for concrete-inheritance parent links

**User story:** As a maintainer relying on existing admin filter behavior, I want
components that merely re-name a value already carried locally through concrete
inheritance to keep being folded away, so that equivalent chains stay equivalent.

**Acceptance criteria**

1. WHEN the component resolves to the link field that realises concrete model
   inheritance (the field is one of the current model's parent links), THEN
   `lookup_allowed` SHALL NOT count that component as a fresh relation part.
2. WHEN the component resolves to the current model's own synthesised automatic
   primary key, THEN `lookup_allowed` SHALL NOT count that component as a fresh
   relation part.
3. IF the current model has a synthesised automatic primary key AND the component
   names one of the previous relation's declared target columns, THEN
   `lookup_allowed` SHALL NOT count that component as a fresh relation part.
4. The system SHALL count a component as a fresh relation part only when it is not
   a parent link, not the model's synthesised automatic primary key, and not (for
   a model that has such a synthesised primary key) one of the previous
   relation's target columns.

## Requirement 3: Preserve the existing walk, matching, and early-allowance behavior

**User story:** As a maintainer, I want the surrounding decision logic to remain
unchanged, so that only the relation-part rule is corrected and no existing admin
filtering behavior regresses.

**Acceptance criteria**

1. The system SHALL walk the lookup's components left-to-right, resolving each
   against the current model and advancing the current model along the relation
   at each hop.
2. WHEN a component does not resolve to a field on the current model, THEN
   `lookup_allowed` SHALL stop walking and treat the remainder of the chain as
   ignorable (a lookup on a nonexistent field is allowed).
3. WHEN a resolved field does not continue to a further model (it is
   non-relational), THEN `lookup_allowed` SHALL stop walking after processing that
   component.
4. WHEN the accumulated relation parts number at most one, THEN `lookup_allowed`
   SHALL return `True` (a purely local filter, or no relational field at all).
5. WHEN there is more than one relation part, THEN `lookup_allowed` SHALL return
   `True` if and only if either the accumulated relation parts joined into a
   chain, or that chain extended by the final processed component, equals one of
   the allowed filters declared via `date_hierarchy` or `list_filter`; otherwise
   it SHALL return `False`.
6. WHEN the requested `(lookup, value)` pair matches an allowance derived from a
   related foreign-key raw-id popup (`limit_choices_to`), THEN `lookup_allowed`
   SHALL return `True` before evaluating the chain walk.
7. The system SHALL keep returning `True` for a permitted chain that traverses a
   one-to-one relation used as a hop when that chain is declared in `list_filter`,
   without regressing previously passing relational-lookup permission checks.
