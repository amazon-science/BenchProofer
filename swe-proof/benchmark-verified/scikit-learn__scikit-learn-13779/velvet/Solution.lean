import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees and no consumed axioms. The two facts this validation
--  scan consults about each member — whether the member is present at all, and
--  whether a present member accepts a per-sample weighting parameter — are
--  abstracted as the boolean input fields `present`/`supports` of the member
--  record. This is a pure type refinement of the member carrier (mapping.md §2),
--  validated by conformance_check.py (G-CONF) and the bridge check
--  axiom_check.py; nothing is left as an opaque assumed contract.)
-- axioms-end

-- pure-start
/- One member of an ensemble, abstracted to exactly the three facts this
   validation step observes:
     * `name`     — the member's identity (its label), abstracted to a distinct
                    integer id (mapping.md §2); reported when validation fails;
     * `present`  — whether the member is actually supplied (an unsupplied /
                    absent member is modeled by `present = false`);
     * `supports` — whether a *present* member accepts a per-sample weighting
                    parameter. Immaterial for an absent member. -/
structure Member where
  name     : Int
  present  : Bool
  supports : Bool
  deriving Inhabited, DecidableEq

/- Validation of an ensemble when a per-sample weighting is supplied.

   Scanning the members in order: an absent member (`present = false`) imposes no
   requirement and is passed over; the FIRST present member that does not accept
   a per-sample weighting parameter makes validation fail, reporting that
   member's identity. If no present member is unsupported, validation succeeds.

   Front-recursive so a single unfold is available per loop step (the fold
   pattern, plan §5.4). The error leg carries the offending member's identity. -/
def validate : List Member → Except Int Unit
  | []      => Except.ok ()
  | m :: ms =>
      if (m.present && !m.supports) then Except.error m.name
      else validate ms

@[grind] lemma validate_nil : validate [] = Except.ok () := rfl
@[grind] lemma validate_cons (m : Member) (ms : List Member) :
    validate (m :: ms) =
      (if (m.present && !m.supports) then Except.error m.name else validate ms) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- When a per-sample weighting is supplied, every present member of an ensemble
   must accept such a weighting; absent members are exempt and impose no
   requirement. The outcome is success exactly when no present member is
   unsupported, and otherwise failure reporting the FIRST present member (in
   order) that does not accept a per-sample weighting parameter.

   `members` is consulted read-only: it is not declared `mut` (directive 5).
   The result is pinned to `validate members`, which pins both legs at once —
   the success outcome when every present member is supported (absent members
   skipped), and the exact identity reported on the failure leg. -/
method validateWeightSupport (members : List Member) return (out : Except Int Unit)
  ensures out = validate members
  do
    -- impl-start
    -- Scan the members back-to-front, keeping the earliest failure seen so far.
    -- A present member that does not accept a per-sample weighting becomes the
    -- recorded failure; an absent member contributes nothing (it is skipped);
    -- a present, supported member leaves the running outcome unchanged. Because
    -- the scan runs back-to-front, the earliest (front-most) failure is the one
    -- that survives — exactly the first offending member.
    let mut result : Except Int Unit := Except.ok ()
    let mut i := members.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ members.length
      invariant result = validate (members.drop i)
      done_with i = 0
      decreasing i
    do
      let m := members[i - 1]!
      result := if (m.present && !m.supports) then Except.error m.name else result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the member at
   `i-1` on the front, so `validate` peels one guarded step. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma validate_drop_step (members : List Member) (i : Nat)
    (hi : 0 < i) (hle : i ≤ members.length) :
    validate (members.drop (i - 1)) =
      (if (members[i - 1]!.present && !members[i - 1]!.supports)
       then Except.error members[i - 1]!.name
       else validate (members.drop i)) := by
  have hlt : i - 1 < members.length := by omega
  have hcons : members.drop (i - 1) = members[i - 1]! :: members.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, validate_cons]

prove_correct validateWeightSupport by
  loom_solve
  rw [validate_drop_step members i (by omega) (by omega)]
  simp_all
