import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- No axioms. Combining two per-key value collections with precedence and then
-- dropping every key whose effective value is the distinguished unset value is
-- the behaviour under specification; it is spelled out deeply in the `pure`
-- region and discharged by the verified loop. There is no unchanged opaque
-- callee to axiomatize.
-- axioms-end

-- pure-start
/- A per-key value collection is modelled as a `List Int` indexed by key
   position: the key universe is the index set `0 .. n-1`, shared by both inputs
   and the output, and position `k` carries the value held for key `k`. Only
   membership ("is key `k` carried, and with what value") is observed, so
   integer identity is a faithful carrier (mapping.md §2). Two distinguished
   values: `absent` means "key not carried by this collection / dropped from the
   result" (a lookup finds the key missing), and `noneVal` means "the explicit
   unset value a caller may store under a key". Any other integer is an ordinary
   value. -/
def absent  : Int := 0
def noneVal : Int := -1

/- The effective value for a key before the unset-drop: the per-request value
   wins where the per-request collection carries the key (`rv ≠ absent`),
   otherwise the standing per-session value is used. -/
def effective (sv rv : Int) : Int :=
  if rv ≠ absent then rv else sv

/- The value the combined collection holds for a key: the effective value,
   except that an effective value equal to the unset value drops the key (it
   becomes `absent`). This is the per-key behaviour the result must realise. -/
def combined (sv rv : Int) : Int :=
  if effective sv rv = noneVal then absent else effective sv rv

/- The combined collection over a shared key universe: the per-key `combined`
   value at each aligned position. Front-recursive so a single unfold is
   available per loop step (the Velvet fold pattern). Positions beyond the
   shorter input are not in the shared key universe and are dropped. -/
def combinedSeq : List Int → List Int → List Int
  | s :: ss, r :: rs => combined s r :: combinedSeq ss rs
  | _,       _       => []

@[grind] lemma combinedSeq_nil_left (rs : List Int) : combinedSeq [] rs = [] := by
  cases rs <;> rfl
@[grind] lemma combinedSeq_nil_right (ss : List Int) : combinedSeq ss [] = [] := by
  cases ss <;> rfl
@[grind] lemma combinedSeq_cons (s r : Int) (ss rs : List Int) :
    combinedSeq (s :: ss) (r :: rs) = combined s r :: combinedSeq ss rs := rfl

/- The headline guarantee, proven of the deep model: no position of the combined
   collection holds the unset value — every lookup yields a real value or finds
   the key absent. This is the clause an impl that drops a key only by
   inspecting the per-request side (leaving a session-side unset value in place)
   violates. -/
@[grind] lemma combined_ne_noneVal (sv rv : Int) : combined sv rv ≠ noneVal := by
  unfold combined
  split
  · decide
  · rename_i h; exact h

@[grind] lemma combinedSeq_mem_ne_noneVal (ss rs : List Int) :
    ∀ x ∈ combinedSeq ss rs, x ≠ noneVal := by
  induction ss generalizing rs with
  | nil => intro x hx; simp [combinedSeq_nil_left] at hx
  | cons s ss ih =>
    cases rs with
    | nil => intro x hx; simp [combinedSeq_nil_right] at hx
    | cons r rs =>
      intro x hx
      rw [combinedSeq_cons] at hx
      rcases List.mem_cons.mp hx with h | h
      · subst h; exact combined_ne_noneVal s r
      · exact ih rs x h
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method effectiveCollection (session : List Int) (request : List Int)
    return (out : List Int)
  ensures out = combinedSeq session request
  ensures ∀ x ∈ out, x ≠ noneVal
  do
    -- impl-start
    let mut result : List Int := []
    let mut i := min session.length request.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ min session.length request.length
      invariant result = combinedSeq (session.drop i) (request.drop i)
      done_with i = 0
      decreasing i
    do
      let sv := session[i - 1]!
      let rv := request[i - 1]!
      -- Precedence: the per-request value wins where the per-request collection
      -- carries the key, else the per-session value.
      let ev : Int := if rv ≠ absent then rv else sv
      -- Drop the key (absent) when its effective value is the unset value,
      -- regardless of which side contributed it; otherwise carry it through.
      let val : Int := if ev = noneVal then absent else ev
      result := val :: result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element from each aligned input
   exposes the per-key `combined` value at position `i-1` on the front, so
   `combinedSeq` peels one element. This is the single goal `loom_solve` leaves
   for the loop body. -/
lemma combinedSeq_drop_step (session request : List Int) (i : Nat)
    (hi : 0 < i) (hs : i ≤ session.length) (hr : i ≤ request.length) :
    combinedSeq (session.drop (i - 1)) (request.drop (i - 1))
      = combined session[i - 1]! request[i - 1]! :: combinedSeq (session.drop i) (request.drop i) := by
  have hslt : i - 1 < session.length := by omega
  have hrlt : i - 1 < request.length := by omega
  have hsucc : i - 1 + 1 = i := by omega
  have hsc : session.drop (i - 1) = session[i - 1]! :: session.drop i := by
    have h := List.drop_eq_getElem_cons hslt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hslt, Option.getD_some]
    rw [h, hsucc]
  have hrc : request.drop (i - 1) = request[i - 1]! :: request.drop i := by
    have h := List.drop_eq_getElem_cons hrlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hrlt, Option.getD_some]
    rw [h, hsucc]
  rw [hsc, hrc, combinedSeq_cons]

prove_correct effectiveCollection by
  loom_solve
  rw [combinedSeq_drop_step session request i (by omega) (by omega) (by omega)]
  simp only [combined, effective, invariant_2]
