import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axiom. The only foreign helper is the resolver of an ambient
   library-wide preference into a concrete boolean; it is an UNCHANGED pure
   callee modeled deeply as `resolveGlobal` below (an A-reference, validated
   `resolveGlobal == the real resolver` by axiom_check.py / G-AX), not an
   axiom the proof consumes. Provenance: mapping.md §3. -/
-- axioms-end

-- pure-start
/- The ambient, library-wide preference governing whether metadata is carried
   across a derived result when a caller does not state a per-call choice:
   * `gDefault` — defer to the operation's own fallback;
   * `gKeep`    — always carry metadata;
   * `gDrop`    — never carry metadata. -/
inductive GlobalPref where
  | gDefault
  | gKeep
  | gDrop
deriving DecidableEq, Inhabited, Repr

/- Resolve the ambient preference against an operation-supplied fallback.
   `gDefault` yields the fallback; the explicit settings override it. This is
   the deep model of the unchanged shared resolver (mapping.md §3.1). -/
def resolveGlobal (g : GlobalPref) (fallback : Bool) : Bool :=
  match g with
  | .gDefault => fallback
  | .gKeep    => true
  | .gDrop    => false

/- The effective keep-metadata decision for a single derived result. When the
   caller passes an explicit choice it is honored verbatim; when the caller
   leaves it unset, the decision falls back to the ambient preference resolved
   against the operation's own fallback (here: drop, i.e. `false`). This is the
   semantics every metadata-bearing reduction is expected to share. -/
def effectiveKeep (choice : Option Bool) (g : GlobalPref) : Bool :=
  match choice with
  | some b => b
  | none   => resolveGlobal g false

/- The metadata a derived result must carry: the source metadata when the
   effective decision keeps it, otherwise no metadata (the empty mapping).
   Metadata is modeled as an association list of key/value entries; "no
   metadata" is the empty list (mapping.md §2). -/
def keptAttrs (srcAttrs : List (String × String)) (choice : Option Bool)
    (g : GlobalPref) : List (String × String) :=
  if effectiveKeep choice g then srcAttrs else []
-- pure-end

-- pre-conditions-start
-- (No module-level preconditions; the operations are total in their inputs.)
-- pre-conditions-end

-- post-conditions-start
-- (Postconditions are the inline `ensures` clauses on each `method` below.)
-- post-conditions-end

/- Core element-wise reduction over an array's values, viewed only through the
   metadata it attaches to its derived result. The value/shape computation is
   orthogonal to this view and unchanged (mapping.md §2), so it is elided here.
   Like the other metadata-bearing reductions, this operation accepts an
   optional keep-metadata choice and must attach the source metadata exactly
   when the effective decision keeps it — honoring an explicit choice, and
   otherwise the ambient preference. The source metadata is read-only (not
   `mut`); the result is a freshly built mapping (directive 5). -/
method reduceElementAttrs (srcAttrs : List (String × String))
    (choice : Option Bool) (glob : GlobalPref)
    return (out : List (String × String))
  ensures out = keptAttrs srcAttrs choice glob
  do
    -- impl-start
    let effective : Bool :=
      match choice with
      | some b => b
      | none   => resolveGlobal glob false
    let attrs : List (String × String) := if effective then srcAttrs else []
    return attrs
    -- impl-end

prove_correct reduceElementAttrs by
  loom_solve
  simp_all [keptAttrs, effectiveKeep, resolveGlobal]

/- Container-level reduction that delegates to the element reduction for each
   member and reports the member's resulting metadata. The container must thread
   its own keep-metadata choice through to the element reduction unchanged;
   otherwise the member silently falls back to the ambient preference and the
   caller's explicit choice is lost. Modeled via callee-under-spec: the element
   reduction's contract is applied directly. -/
method reduceContainerAttrs (srcAttrs : List (String × String))
    (choice : Option Bool) (glob : GlobalPref)
    return (out : List (String × String))
  ensures out = keptAttrs srcAttrs choice glob
  do
    -- impl-start
    let r ← reduceElementAttrs srcAttrs choice glob
    return r
    -- impl-end

prove_correct reduceContainerAttrs by
  loom_solve

/- Labeled-array reduction: the user-facing wrapper. It forwards its
   keep-metadata choice to the container reduction and returns the resulting
   metadata. End to end, an explicit "keep" choice must surface the source
   metadata on the result. -/
method reduceLabeledAttrs (srcAttrs : List (String × String))
    (choice : Option Bool) (glob : GlobalPref)
    return (out : List (String × String))
  ensures out = keptAttrs srcAttrs choice glob
  do
    -- impl-start
    let r ← reduceContainerAttrs srcAttrs choice glob
    return r
    -- impl-end

prove_correct reduceLabeledAttrs by
  loom_solve
