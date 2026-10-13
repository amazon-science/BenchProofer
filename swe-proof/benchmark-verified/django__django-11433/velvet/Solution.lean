import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No unchanged callee needs an axiom here. Whether the constructing loop hands
   a field's cleaned value to that field's write step is decided entirely by
   booleans observable at the field — whether the field is one the form may
   assign at all, whether the model declares a fallback for it, whether the
   submitted payload carried an incoming value for it, and whether the cleaned
   value is itself empty. All of that is modeled directly in the `pure` region
   below; nothing is axiomatized. The write step itself is an unchanged callee
   outside the modeled boundary. Cross-language soundness of those refinements
   is checked mechanically by G-CONF (conformance_check.py). -/
-- axioms-end

-- pure-start
/- One model field, as the value-assignment step observes it.
   * `eligible`          — the field is one the form may assign from cleaned
                           data at all: it accepts assignment, is not an
                           auto-generated key, has an entry in cleaned data, and
                           is permitted by the form's field selection. (The
                           gating conditions that are unaffected by the desired
                           change, bundled.)
   * `modelHasDefault`   — the model declares a fallback value for this field.
   * `noIncomingValue`   — the submitted payload carried no incoming value for
                           this field (so, absent any other reason, the model
                           fallback would stand).
   * `cleanedValueEmpty` — the cleaned value for this field is itself an empty
                           value. -/
structure Field where
  eligible          : Bool
  modelHasDefault   : Bool
  noIncomingValue   : Bool
  cleanedValueEmpty : Bool
deriving Inhabited, DecidableEq

/- Whether the constructing loop hands a single field's cleaned value to that
   field's write step, as opposed to skipping the field so the model's fallback
   stands. (What the write step then does with the handed value is the write
   step's own behavior, outside this decision.)

   An ineligible field is never handed off. An eligible field is handed its
   cleaned value UNLESS the model's fallback should stand in its place, which
   happens exactly when all three hold together: the model declares a fallback,
   the submitted payload carried no incoming value for the field, AND the
   cleaned value is itself empty. When the cleaned value is non-empty it is
   handed to the write step even though the payload omitted the field. -/
def applies (f : Field) : Bool :=
  f.eligible && !(f.modelHasDefault && f.noIncomingValue && f.cleanedValueEmpty)

/- The per-field assignment decisions across the whole field list.
   Front-recursive so a single unfold is available per loop step (the fold
   pattern, plan §5.4). -/
def applyPlan : List Field → List Bool
  | []      => []
  | f :: fs => applies f :: applyPlan fs

@[grind] lemma applyPlan_nil : applyPlan [] = [] := rfl
@[grind] lemma applyPlan_cons (f : Field) (fs : List Field) :
    applyPlan (f :: fs) = applies f :: applyPlan fs := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method assignCleanedValues (fields : List Field) return (out : List Bool)
  ensures out = applyPlan fields
  do
    -- impl-start
    let mut result : List Bool := []
    let mut i := fields.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ fields.length
      invariant result = applyPlan (fields.drop i)
      done_with i = 0
      decreasing i
    do
      let f := fields[i - 1]!
      result := applies f :: result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the field at
   `i-1` on the front, so `applyPlan` peels one `applies`. The single goal
   `loom_solve` leaves for the loop body. -/
lemma applyPlan_drop_step (fields : List Field) (i : Nat)
    (hi : 0 < i) (hle : i ≤ fields.length) :
    applyPlan (fields.drop (i - 1)) = applies fields[i - 1]! :: applyPlan (fields.drop i) := by
  have hlt : i - 1 < fields.length := by omega
  have hcons : fields.drop (i - 1) = fields[i - 1]! :: fields.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, applyPlan_cons]

prove_correct assignCleanedValues by
  loom_solve
  rw [applyPlan_drop_step fields i (by omega) (by omega)]
  simp_all
