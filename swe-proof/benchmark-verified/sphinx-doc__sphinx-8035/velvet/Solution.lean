import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The behaviour under specification — which members of a
   collection survive the visibility filter — is modeled DEEPLY in the `pure`
   region (`memberShown` / `shownMembers`): the keep-decision is concrete data,
   not hidden behind a module-level `axiom`. The upstream classifications that
   feed the decision (whether a member is visibility-restricted, whether it
   carries documentation, and how a caller's selection argument parses into the
   tri-state below) are produced by unchanged helpers; their faithful
   abstraction into the inputs is recorded in mapping.md and validated against
   the real helpers by axiom_check.py (G-AX). -/
-- axioms-end

-- pure-start
/- A caller's selection of which visibility-restricted members to surface, in
   the three shapes the desired behaviour distinguishes:
   * `none`  — no selection given: surface no restricted members;
   * `all`   — surface every restricted member;
   * `only names` — surface exactly the restricted members whose identifier is
     listed in `names`.
   mapping.md §3 gives the bijection to the repository's parsed option value. -/
inductive Sel where
  | none
  | all
  | only (names : List String)

/- The observable facts about one member the desired behaviour depends on: its
   identifier, whether it is visibility-restricted, and whether it carries
   documentation. Every other property of a member is orthogonal (mapping.md
   §2). -/
structure Member where
  name         : String
  isRestricted : Bool
  hasDoc       : Bool
  deriving Inhabited, DecidableEq

/- Whether a selection surfaces a restricted member of a given identifier:
   nothing when no selection is given, everything when the selection is the
   blanket one, and otherwise exactly the listed identifiers. -/
def selKeeps : Sel → String → Bool
  | .none,       _    => false
  | .all,        _    => true
  | .only names, name => names.contains name

/- The keep-decision for a single member when documenting a whole collection.
   A non-restricted member is shown when it is documented (or undocumented
   members are requested). A restricted member is shown only when it is
   additionally surfaced by the selection — so a blanket request shows all
   restricted members, a specific request shows exactly the named ones, and the
   default shows none. The selection therefore distinguishes specific restricted
   members rather than acting as a single all-or-nothing switch. -/
def memberShown (sel : Sel) (showUndocumented : Bool) (m : Member) : Bool :=
  if m.isRestricted then
    (m.hasDoc || showUndocumented) && selKeeps sel m.name
  else
    m.hasDoc || showUndocumented

/- The members of a collection that survive the filter, in input order.
   Front-recursive so a single unfold is available per loop step (the fold
   pattern, plan §5.4). -/
def shownMembers (sel : Sel) (showUndocumented : Bool) : List Member → List Member
  | []      => []
  | m :: ms =>
      (if memberShown sel showUndocumented m then [m] else [])
        ++ shownMembers sel showUndocumented ms

@[grind] lemma shownMembers_nil (sel : Sel) (su : Bool) :
    shownMembers sel su [] = [] := rfl
@[grind] lemma shownMembers_cons (sel : Sel) (su : Bool) (m : Member) (ms : List Member) :
    shownMembers sel su (m :: ms)
      = (if memberShown sel su m then [m] else []) ++ shownMembers sel su ms := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Filter the members of a collection down to those that should be surfaced,
   preserving input order.

   `members`, `sel` and `showUndocumented` are read-only inputs (none is `mut`):
   the filter consumes them and never alters them (directive 5). The result is
   exactly the per-member keep-decision applied across the input
   (`out = shownMembers sel showUndocumented members`); in particular, when the
   selection names specific restricted members, only those named are surfaced —
   a verifying implementation cannot treat a specific selection as a blanket
   "show all restricted members" switch. -/
method selectMembers (members : List Member) (sel : Sel) (showUndocumented : Bool)
    return (out : List Member)
  ensures out = shownMembers sel showUndocumented members
  do
    -- impl-start
    let mut result : List Member := []
    let mut i := members.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ members.length
      invariant result = shownMembers sel showUndocumented (members.drop i)
      done_with i = 0
      decreasing i
    do
      let m := members[i - 1]!
      result := (if memberShown sel showUndocumented m then [m] else []) ++ result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `shownMembers` peels one keep-decision. This is the
   single goal `loom_solve` leaves for the loop body. -/
lemma shownMembers_drop_step (members : List Member) (sel : Sel) (su : Bool) (i : Nat)
    (hi : 0 < i) (hle : i ≤ members.length) :
    shownMembers sel su (members.drop (i - 1))
      = (if memberShown sel su members[i - 1]! then [members[i - 1]!] else [])
        ++ shownMembers sel su (members.drop i) := by
  have hlt : i - 1 < members.length := by omega
  have hcons : members.drop (i - 1) = members[i - 1]! :: members.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, shownMembers_cons]

prove_correct selectMembers by
  loom_solve
  rw [shownMembers_drop_step members sel showUndocumented i (by omega) (by omega)]
  simp_all
