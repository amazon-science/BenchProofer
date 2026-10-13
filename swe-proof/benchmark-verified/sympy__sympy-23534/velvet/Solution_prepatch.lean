import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- The requested object class for a building request. A symbol-building call is
   parameterised by the class of object to create (the default leaf kind, or a
   `Function`/`Wild`-like alternative). We observe only the class an element
   carries, since that is the sole property the desired behaviour constrains. -/
inductive SymCls where
  | sym   -- the default symbol kind
  | func  -- the function-like kind
  | wild  -- the wildcard kind
  deriving DecidableEq, Repr

/- Building objects from a SINGLE name string under a requested class. This is
   the unchanged community routine the sequence builder defers to once per
   element; it returns the list of objects parsed from one name. Its only
   relied-upon property is that every object it produces carries exactly the
   class it was asked for. Provenance + executable soundness check:
   mapping.md / axiom_check.py (G-AX). -/
axiom buildName : String → SymCls → List SymCls

/- The weakest contract sufficient here: the per-name builder honours the
   requested class on every object it returns. (A-consumed.) -/
axiom buildName_cls : ∀ (s : String) (c : SymCls), ∀ x ∈ buildName s c, x = c
-- axioms-end

-- pure-start
/- The objects built from a SEQUENCE of names under a requested class: each
   name is expanded by the per-name builder carrying THE SAME requested class,
   and the per-name results are kept in order. Front-recursive so a single
   unfold is available per loop step (the Velvet fold pattern, plan §5.4). -/
noncomputable def expand : List String → SymCls → List (List SymCls)
  | [],      _ => []
  | n :: ns, c => buildName n c :: expand ns c

@[grind] lemma expand_nil (c : SymCls) : expand [] c = [] := rfl
@[grind] lemma expand_cons (n : String) (ns : List String) (c : SymCls) :
    expand (n :: ns) c = buildName n c :: expand ns c := rfl

/- Every object in every per-name group of a sequence expansion carries the
   requested class. This is the behavioural guarantee the desired result
   demands; it consumes `buildName_cls`. Marked `@[grind]` so `loom_solve`
   discharges the class postcondition automatically. -/
@[grind] lemma expand_cls :
    ∀ (names : List String) (c : SymCls), ∀ sub ∈ expand names c, ∀ x ∈ sub, x = c := by
  intro names
  induction names with
  | nil => intro c sub hsub; simp [expand] at hsub
  | cons n ns ih =>
    intro c sub hsub x hx
    rw [expand_cons] at hsub
    rcases List.mem_cons.mp hsub with h | h
    · subst h; exact buildName_cls n c x hx
    · exact ih c sub h x hx
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

noncomputable section
method buildSeq (names : List String) (cls : SymCls) return (out : List (List SymCls))
  ensures out = expand names cls
  ensures ∀ sub ∈ out, ∀ x ∈ sub, x = cls
  do
    -- impl-start
    -- Pre-image skeleton: the per-name builder is invoked WITHOUT propagating
    -- the requested class, so it falls back to the default leaf kind (`.sym`)
    -- regardless of `cls`. The frozen spec requires `out = expand names cls`
    -- (each element carrying the requested `cls`), so prove_correct MUST fail
    -- whenever `cls ≠ .sym`.
    let mut result : List (List SymCls) := []
    let mut i := names.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ names.length
      invariant result = expand (names.drop i) cls
      done_with i = 0
      decreasing i
    do
      let n := names[i - 1]!
      result := buildName n .sym :: result
      i := i - 1
    return result
    -- impl-end
end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `expand` peels one per-name group. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma expand_drop_step (names : List String) (cls : SymCls) (i : Nat)
    (hi : 0 < i) (hle : i ≤ names.length) :
    expand (names.drop (i - 1)) cls
      = buildName names[i - 1]! cls :: expand (names.drop i) cls := by
  have hlt : i - 1 < names.length := by omega
  have hcons : names.drop (i - 1) = names[i - 1]! :: names.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, expand_cons]

prove_correct buildSeq by
  loom_solve
  rw [expand_drop_step names cls i (by omega) (by omega)]
  simp_all
