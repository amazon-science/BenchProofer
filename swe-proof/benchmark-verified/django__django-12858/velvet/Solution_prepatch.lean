import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The schema accessors a single ordering reference is
--  resolved against — "resolve this part to a field of this model", "the alias
--  field of this model", "is this part a registered transform of a field", "is
--  this part a registered lookup of a field" — are taken as FREE INPUTS
--  (`lookup`, `aliasField`, `hasTransform`, `hasLookup`). The spec makes no
--  behavioural claim about them and holds for EVERY schema, so there is nothing
--  to check against a real callee, hence no G-AX. The validity decision under
--  spec — how those accessors are threaded across the chain of parts — is
--  modeled deeply below; every observable is computed from the inputs, nothing
--  is borrowed from an oracle. See refinement.md / mapping.md.)
-- axioms-end

-- pure-start
/- A model in the schema graph, identified abstractly. -/
abbrev Model := Nat

/- The observable metadata of a resolved field: whether it is a relation (so the
   chain may continue into another model) and, if so, which model it points at. -/
structure Field where
  isRel : Bool
  relModel : Model
deriving Inhabited, DecidableEq

/- One part of a dotted ordering reference (e.g. the `parent`, then `pk`, parts
   of `parent__pk`). `isAlias` marks the part that names the primary-key alias —
   an alias that denotes a model's identity field but is not itself returned by a
   plain field resolution. -/
structure Part where
  name : Nat
  isAlias : Bool
deriving Inhabited, DecidableEq

/- The state carried while walking the chain of parts of one reference:
   - `cur`  : the model the next part is resolved against, or `none` when the
              chain has stepped off the model graph (a part resolved to a
              non-relation field, so there is no further model to descend into);
   - `last` : the most recently resolved field, or `none` before any part has
              resolved (consulted only to decide whether an unresolved part is an
              admissible registered transform/lookup of it);
   - `flag` : whether the reference has been judged invalid (an E015-style
              report has been raised for it). -/
abbrev WalkState := Option Model × Option Field × Bool

/- The seed state for a reference rooted at model `cls0`: resolution starts at
   `cls0`, no field resolved yet, not yet flagged. -/
def initState (cls0 : Model) : WalkState := (some cls0, none, false)

/- When a part fails to resolve, the reference is flagged UNLESS that part names
   a registered transform OR a registered lookup of the LAST resolved field. A
   trailing part that is a registered transform/lookup of the field resolved so
   far is an admissible suffix and must not invalidate the reference. With no
   field resolved yet (`none`), there is nothing to host such a transform/lookup,
   so the reference is flagged. -/
def flagOnUnresolved (hasTransform hasLookup : Field → Part → Bool)
    (last : Option Field) (p : Part) : Bool :=
  match last with
  | none   => true
  | some f => !(hasTransform f p) && !(hasLookup f p)

/- Advance the walk by one part `p`.

   - If there is no current model to resolve against, the part cannot resolve;
     the reference is flagged unless `p` is a registered transform/lookup of the
     last resolved field, and the chain stays off the model graph.
   - Otherwise, against current model `m`:
     * the alias part resolves to `m`'s identity field directly;
     * any other part is resolved by `lookup`; failing to resolve leaves the
       current model in place and flags the reference (modulo the
       transform/lookup escape hatch).
     After a successful resolution the chain descends into the related model when
     the field is a relation, and otherwise steps off the model graph (`none`):
     a non-relation field terminates the descent, so a following part has no
     model to resolve against. -/
def stepWalk (lookup : Model → Part → Option Field) (aliasField : Model → Field)
    (hasTransform hasLookup : Field → Part → Bool) (st : WalkState) (p : Part) : WalkState :=
  let cur  := st.1
  let last := st.2.1
  let flag := st.2.2
  match cur with
  | none   => (none, last, flag || flagOnUnresolved hasTransform hasLookup last p)
  | some m =>
      if p.isAlias then
        let f := aliasField m
        (if f.isRel then some f.relModel else none, some f, flag)
      else
        match lookup m p with
        | some f => (if f.isRel then some f.relModel else none, some f, flag)
        | none   => (some m, last, flag || flagOnUnresolved hasTransform hasLookup last p)

/- A whole reference is judged invalid iff, after walking every part from the
   seed state, its flag is set. -/
def orderingRefInvalid (lookup : Model → Part → Option Field) (aliasField : Model → Field)
    (hasTransform hasLookup : Field → Part → Bool) (cls0 : Model) (parts : List Part) : Bool :=
  (parts.foldl (stepWalk lookup aliasField hasTransform hasLookup) (initState cls0)).2.2

/- Forward-fold step: extending the consumed prefix by one part advances the
   walk built from the shorter prefix by exactly that part. The single goal
   `loom_solve` leaves for the loop body. -/
lemma walk_take_step
    (lookup : Model → Part → Option Field) (aliasField : Model → Field)
    (hasTransform hasLookup : Field → Part → Bool) (cls0 : Model) (parts : List Part)
    (i : Nat) (hi : i < parts.length) :
    (parts.take (i + 1)).foldl (stepWalk lookup aliasField hasTransform hasLookup) (initState cls0)
      = stepWalk lookup aliasField hasTransform hasLookup
          ((parts.take i).foldl (stepWalk lookup aliasField hasTransform hasLookup) (initState cls0))
          parts[i]! := by
  have hcons : parts.take (i + 1) = parts.take i ++ [parts[i]!] := by
    rw [List.take_succ, List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi]
    simp
  rw [hcons, List.foldl_append, List.foldl_cons, List.foldl_nil]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Decide whether a single dotted ordering reference is invalid (would raise an
   E015-style report). The reference is the list of `parts` resolved left to
   right against the schema, rooted at the model `cls0`. The schema accessors
   `lookup` / `aliasField` / `hasTransform` / `hasLookup` and the inputs `cls0` /
   `parts` are read-only (not `mut`): the walk threads a fresh accumulator state
   and never mutates anything it is handed (directive 5). -/
method checkOrderingRef
    (lookup : Model → Part → Option Field) (aliasField : Model → Field)
    (hasTransform : Field → Part → Bool) (hasLookup : Field → Part → Bool)
    (cls0 : Model) (parts : List Part)
    return (out : Bool)
  ensures out = orderingRefInvalid lookup aliasField hasTransform hasLookup cls0 parts
  do
    -- impl-start
    let mut st : WalkState := initState cls0
    let mut i := 0
    while i < parts.length
      invariant i ≤ parts.length
      invariant st = (parts.take i).foldl (stepWalk lookup aliasField hasTransform hasLookup) (initState cls0)
      done_with i = parts.length
      decreasing parts.length - i
    do
      let p := parts[i]!
      -- Pre-image skeleton: a part that fails to resolve is flagged unless it is
      -- a registered TRANSFORM of the last resolved field — with NO escape hatch
      -- for a part that is only a registered LOOKUP. The frozen spec admits the
      -- registered-lookup suffix as well (`flagOnUnresolved` also clears on
      -- `hasLookup`), so for a lookup-but-not-transform suffix the two diverge
      -- and prove_correct MUST fail.
      let newSt : WalkState :=
        let cur  := st.1
        let last := st.2.1
        let flag := st.2.2
        let flagOnUnresolvedBuggy : Bool :=
          match last with
          | none   => true
          | some f => !(hasTransform f p)
        match cur with
        | none   => (none, last, flag || flagOnUnresolvedBuggy)
        | some m =>
            if p.isAlias then
              let f := aliasField m
              (if f.isRel then some f.relModel else none, some f, flag)
            else
              match lookup m p with
              | some f => (if f.isRel then some f.relModel else none, some f, flag)
              | none   => (some m, last, flag || flagOnUnresolvedBuggy)
      st := newSt
      i := i + 1
    return st.2.2
    -- impl-end

prove_correct checkOrderingRef by
  loom_solve
  case «invariant_2: st = (parts.take i).foldl (stepWalk lookup aliasField hasTransform hasLookup) (initState cls0)» =>
    have hi : i < parts.length := by omega
    rw [invariant_2, walk_take_step lookup aliasField hasTransform hasLookup cls0 parts i hi,
        List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi]
  all_goals simp_all [orderingRefInvalid]
