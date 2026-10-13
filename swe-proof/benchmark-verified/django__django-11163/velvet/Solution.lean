import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees: the per-candidate selection decision is a pure
--  function of the candidate's name, the optional selector, and the excl list,
--  modeled deeply over `List Int`. There is no unchanged library callee the
--  proof must axiomatize.)
-- axioms-end

-- pure-start
/- Whether a single candidate name `n` survives the selection.

   The optional selector `sel` distinguishes three situations that must be kept
   apart:
     * `none`        — no selector was supplied: every candidate is admissible;
     * `some present` — a selector list was supplied: a candidate is admissible
       only if its name is among the listed `present` ones. Crucially this is decided by the
       PRESENCE of the selector, NOT by whether it lists anything: a supplied
       selector that lists nothing keeps nothing.
   Independently, an excl list removes any candidate whose name it contains (an
   empty excl list removes nothing, since no name is a member of it). -/
def keep (sel : Option (List Int)) (excl : List Int) (n : Int) : Bool :=
  (match sel with
   | none         => true
   | some present => decide (n ∈ present))
  && decide (n ∉ excl)

/- The selection of a whole candidate list: keep each admissible name, in order.
   Front-recursive so a single unfold is available per loop step (the Velvet
   fold pattern). -/
def selectNames (sel : Option (List Int)) (excl : List Int) : List Int → List Int
  | []      => []
  | n :: ns => (if keep sel excl n then [n] else []) ++ selectNames sel excl ns

@[grind] lemma selectNames_nil (sel : Option (List Int)) (excl : List Int) :
    selectNames sel excl [] = [] := rfl
@[grind] lemma selectNames_cons (sel : Option (List Int)) (excl : List Int)
    (n : Int) (ns : List Int) :
    selectNames sel excl (n :: ns) =
      (if keep sel excl n then [n] else []) ++ selectNames sel excl ns := rfl

/- A supplied selector that lists nothing keeps nothing. -/
@[grind] lemma keep_empty_selector (excl : List Int) (n : Int) :
    keep (some []) excl n = false := by
  unfold keep; simp

/- Hence selecting against an empty supplied selector yields the empty list,
   regardless of the candidates or the excl list. This is the behaviour the
   issue demands and the single clause on which the pre-image skeleton fails. -/
@[grind] lemma selectNames_empty_selector (excl : List Int) (ns : List Int) :
    selectNames (some []) excl ns = [] := by
  induction ns with
  | nil => rfl
  | cons n ns ih => rw [selectNames_cons, keep_empty_selector]; simpa using ih

/- A selected name is always one of the candidates (nothing is invented) and is
   admissible. Proven by induction; marked `@[grind]` so the corresponding
   postconditions discharge automatically. -/
@[grind] lemma selectNames_mem (sel : Option (List Int)) (excl : List Int)
    (ns : List Int) :
    ∀ n, n ∈ selectNames sel excl ns → n ∈ ns ∧ keep sel excl n = true := by
  induction ns with
  | nil => intro n h; simp [selectNames] at h
  | cons c cs ih =>
      intro n h
      rw [selectNames_cons] at h
      by_cases hk : keep sel excl c = true
      · rw [if_pos hk] at h
        rw [List.singleton_append, List.mem_cons] at h
        rcases h with hnc | htail
        · subst hnc; exact ⟨List.mem_cons_self, hk⟩
        · obtain ⟨hmem, hkeep⟩ := ih n htail
          exact ⟨List.mem_cons_of_mem _ hmem, hkeep⟩
      · rw [if_neg hk] at h
        rw [List.nil_append] at h
        obtain ⟨hmem, hkeep⟩ := ih n h
        exact ⟨List.mem_cons_of_mem _ hmem, hkeep⟩
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- A routine collects, for a model instance, the values of a set of candidate
   fields keyed by field name. Two read-only knobs narrow that set:

   - an OPTIONAL selector of names. When absent, every candidate field is
     collected. When PRESENT, only the named candidates are collected — and a
     present selector that names nothing collects nothing. The distinction
     between "no selector" and "a selector that names nothing" is the whole
     point: requesting an empty set of fields yields an empty result, it does
     NOT fall back to collecting everything.
   - an excl list of names. Any candidate whose name appears in it is dropped;
     an excl list that names nothing drops nothing.

   The candidate names are modeled as `List Int` (each distinct field name is a
   distinct identifier); the optional selector is `Option (List Int)` so that
   "absent" and "present but empty" are genuinely different inputs; the excl
   list is `List Int`. The result is the list of collected (kept) names, in the
   candidate order.

   `candidates`, `selector` and `excl` are read-only (not `mut`); the routine
   builds a fresh result and mutates none of them (directive 5). -/
method selectModelFields (candidates : List Int) (selector : Option (List Int))
    (excl : List Int) return (out : List Int)
  ensures out = selectNames selector excl candidates
  ensures selector = some [] → out = []
  ensures ∀ n, n ∈ out → n ∈ candidates ∧ keep selector excl n = true
  do
    -- impl-start
    let mut result : List Int := []
    let mut i := candidates.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ candidates.length
      invariant result = selectNames selector excl (candidates.drop i)
      done_with i = 0
      decreasing i
    do
      let c := candidates[i - 1]!
      result := (if keep selector excl c then [c] else []) ++ result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `selectNames` peels one keep-decision. This is the
   single goal `loom_solve` leaves for the loop body. -/
lemma selectNames_drop_step (sel : Option (List Int)) (excl : List Int)
    (xs : List Int) (i : Nat) (hi : 0 < i) (hle : i ≤ xs.length) :
    selectNames sel excl (xs.drop (i - 1)) =
      (if keep sel excl xs[i - 1]! then [xs[i - 1]!] else [])
        ++ selectNames sel excl (xs.drop i) := by
  have hlt : i - 1 < xs.length := by omega
  have hcons : xs.drop (i - 1) = xs[i - 1]! :: xs.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, selectNames_cons]

prove_correct selectModelFields by
  loom_solve
  rw [selectNames_drop_step selector excl candidates i (by omega) (by omega)]
  rw [‹result = selectNames selector excl (candidates.drop i)›]
