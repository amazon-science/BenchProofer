import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- No consumed axioms. The one operation whose behaviour this change toggles —
-- extracting a single labeled component from the combined array — is modeled
-- DEEPLY by `sliceCoords` (pure region) as an A-reference: its coordinate-set
-- result is validated against the real component extractor by axiom_check.py
-- (G-AX). See mapping.md §3.
-- axioms-end

-- pure-start
/- Extracting one labeled component from a combined array yields a slice whose
   coordinate names are the shared sample coordinates, PLUS — unless the
   transient selector label is discarded during extraction — the selector label
   itself left behind as a residual scalar coordinate. `keep = false` discards
   it; `keep = true` retains it. The observable modeled here is the set of
   coordinate NAMES carried by the extracted slice (mapping.md §2, §3.1). -/
def sliceCoords (selDim : String) (sampleCoords : List String) (keep : Bool) : List String :=
  if keep then sampleCoords ++ [selDim] else sampleCoords

@[grind, simp] lemma sliceCoords_discard (selDim : String) (sampleCoords : List String) :
    sliceCoords selDim sampleCoords false = sampleCoords := rfl

/- The correct result of the whole extraction: every component, keyed by its
   label, carries exactly the shared sample coordinates and nothing transient.
   Front-recursive so a single unfold is available per loop step (the fold
   pattern). -/
def expectedComponents (sampleCoords : List String) :
    List String → List (String × List String)
  | []      => []
  | k :: ks => (k, sampleCoords) :: expectedComponents sampleCoords ks

@[grind] lemma expectedComponents_nil (sampleCoords : List String) :
    expectedComponents sampleCoords [] = [] := rfl

@[grind] lemma expectedComponents_cons (sampleCoords : List String) (k : String)
    (ks : List String) :
    expectedComponents sampleCoords (k :: ks)
      = (k, sampleCoords) :: expectedComponents sampleCoords ks := rfl

/- The labels (keys) of the extracted components are exactly the input labels,
   in order — the extraction neither drops, duplicates, nor reorders. -/
@[grind] lemma expectedComponents_keys (sampleCoords : List String) (vs : List String) :
    (expectedComponents sampleCoords vs).map Prod.fst = vs := by
  induction vs with
  | nil => rfl
  | cons k ks ih => simp [expectedComponents, ih]

/- Every extracted component carries exactly the shared sample coordinates as
   its coordinate-name set — in particular none of them carries any name absent
   from the sample coordinates. -/
@[grind] lemma expectedComponents_snd (sampleCoords : List String) (vs : List String) :
    ∀ p ∈ expectedComponents sampleCoords vs, p.2 = sampleCoords := by
  induction vs with
  | nil => intro p hp; simp [expectedComponents] at hp
  | cons k ks ih =>
    intro p hp
    rw [expectedComponents_cons] at hp
    rcases List.mem_cons.mp hp with h | h
    · subst h; rfl
    · exact ih p h
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Reassemble a combined array into its labeled components.

   `selDim` is the transient selector label used to address each component;
   `sampleCoords` are the coordinate names shared by every component; `vars`
   are the component labels to extract, in order.

   Each component is extracted by addressing it via the selector label. For the
   reassembled collection to be conflict-free, the transient selector label must
   NOT persist as a coordinate on any extracted component — otherwise distinct
   components would carry conflicting values for that same coordinate name and
   could not be combined. The result pairs each label with the coordinate names
   its extracted component carries. -/
method toComponents (selDim : String) (sampleCoords : List String) (vars : List String)
    return (out : List (String × List String))
  require selDim ∉ sampleCoords
  ensures out = expectedComponents sampleCoords vars
  ensures out.map Prod.fst = vars
  ensures ∀ p ∈ out, selDim ∉ p.2
  do
    -- impl-start
    let mut result : List (String × List String) := []
    let mut i := vars.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ vars.length
      invariant result = expectedComponents sampleCoords (vars.drop i)
      done_with i = 0
      decreasing i
    do
      let k := vars[i - 1]!
      -- Pre-image skeleton: the component is extracted WITHOUT discarding the
      -- transient selector label (keep = true), so the selector label persists
      -- as a residual scalar coordinate on every component. The frozen spec
      -- forbids that (`selDim ∉ p.2`), so prove_correct MUST fail.
      result := (k, sliceCoords selDim sampleCoords true) :: result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `expectedComponents` peels one pair. This is the
   single goal `loom_solve` leaves for the loop body. -/
lemma expectedComponents_drop_step (sampleCoords : List String) (vars : List String) (i : Nat)
    (hi : 0 < i) (hle : i ≤ vars.length) :
    expectedComponents sampleCoords (vars.drop (i - 1))
      = (vars[i - 1]!, sampleCoords) :: expectedComponents sampleCoords (vars.drop i) := by
  have hlt : i - 1 < vars.length := by omega
  have hcons : vars.drop (i - 1) = vars[i - 1]! :: vars.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, expectedComponents_cons]

prove_correct toComponents by
  loom_solve
  rw [expectedComponents_drop_step sampleCoords vars i (by omega) (by omega)]
  simp_all
