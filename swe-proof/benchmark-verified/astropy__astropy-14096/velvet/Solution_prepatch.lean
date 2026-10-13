import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The genuine attribute-resolution routine this slice
--  delegates to on a miss is UNCHANGED, and its outcome is observed only through
--  the free input `genuineOutcome : Except AttrErr Value`. The spec makes no
--  behavioural claim about that routine and holds for EVERY value it could take,
--  so there is nothing to check against a real callee, hence no G-AX. The
--  behaviour under spec — which outcome the miss path hands back — is modeled
--  deeply in the `pure`/`impl` regions, no outside contract consumed. See
--  mapping.md §3 / refinement.md.)
-- axioms-end

-- pure-start
/- An attribute name, identified abstractly: the desired behaviour observes only
   WHICH attribute an outcome refers to (its identity), never its concrete
   spelling, so a single opaque carrier suffices. -/
abbrev Name := Nat

/- A successfully resolved attribute value, identified abstractly: only the fact
   that a value was produced is observed here, never its content. -/
abbrev Value := Nat

/- A failed attribute access. Its single observable is the `subject`: the
   attribute the failure actually refers to — i.e. the attribute named in the
   reported message. Two failures are the same exactly when they name the same
   attribute. -/
structure AttrErr where
  subject : Name
  deriving DecidableEq

/- The desired outcome of an attribute access that the object's own directly
   held state did not satisfy.

   Such an access is first offered to an unchanged resolution prefix
   (`frameOutcome`): if that prefix produces a value, that value is the result.
   Otherwise the access is a genuine miss, and the result must be EXACTLY the
   outcome of the genuine attribute-resolution routine (`genuineOutcome`) — the
   value it would yield, or the failure it would report, propagated verbatim. In
   particular, when resolving the requested attribute itself triggers a derived
   accessor that fails on some OTHER attribute, the failure handed back is the
   genuine one (about that other attribute), never a freshly minted failure
   renamed to the originally-requested attribute. The requested name is not
   consulted on the miss path at all. -/
def attrFallbackSpec (requested : Name) (frameOutcome : Option Value)
    (genuineOutcome : Except AttrErr Value) : Except AttrErr Value :=
  match frameOutcome with
  | some v => Except.ok v
  | none   => genuineOutcome
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Resolve an attribute access that the object's own directly held state did not
   satisfy.

   `requested` is the attribute that was asked for. `frameOutcome` is the outcome
   of the UNCHANGED resolution prefix that runs first — `some v` if that prefix
   itself produced a value, `none` if it declined and the access is a genuine
   miss. `genuineOutcome` is a read-only free input: the outcome the UNCHANGED
   genuine attribute-resolution routine would yield for this access (a value, or
   a failure naming the attribute it actually refers to).

   The result is `attrFallbackSpec`: a prefix-produced value is returned; on a
   genuine miss the genuine routine's outcome is handed back verbatim — never a
   failure freshly renamed to `requested`.

   `requested`, `frameOutcome`, `genuineOutcome` are all read-only (none `mut`):
   the routine reads them and returns a result, mutating nothing it is handed
   (directive 5). -/
method lookupMissingAttribute (requested : Name) (frameOutcome : Option Value) (genuineOutcome : Except AttrErr Value) return (out : Except AttrErr Value)
  ensures out = attrFallbackSpec requested frameOutcome genuineOutcome
  do
    -- impl-start
    -- Pre-image (buggy) skeleton: on a genuine miss the routine does NOT delegate
    -- to the genuine attribute-resolution routine. Instead it FABRICATES a fresh
    -- failure naming the ORIGINALLY-REQUESTED attribute (`requested`), discarding
    -- whatever the genuine routine would have reported. When the requested
    -- attribute's own resolution fails on some OTHER attribute, the frozen spec
    -- demands the genuine outcome (about that other attribute) be propagated, so
    -- prove_correct MUST fail on exactly the miss-path clause: this hands back
    -- `Except.error { subject := requested }` instead of `genuineOutcome`.
    let out := match frameOutcome with
      | some v => Except.ok v
      | none   => Except.error { subject := requested }
    return out
    -- impl-end

prove_correct lookupMissingAttribute by
  loom_solve <;> simp_all [attrFallbackSpec]
