import Mathlib
-- imports-end

/-!
Collecting the chunk sizes of a collection of array-like variables.

Each variable in the collection may be *chunked*: if so it exposes, for each of
its named dimensions, the block length along that dimension. `get_chunksizes`
walks the collection and builds a single mapping from dimension name to block
length:

* a variable that is not chunked contributes nothing;
* a chunked variable contributes one entry per dimension; if a dimension has
  already been recorded with a *different* block length the collection has
  inconsistent chunking and the whole operation is rejected;
* recording a dimension whose block length already agrees with the stored value
  leaves the mapping unchanged.

The resulting mapping lists dimensions in the order they were first encountered.

Crucially, deciding whether a variable is chunked is a question about the
variable's chunk metadata only: it must be answerable by inspecting that
metadata and must never force the variable's contents to be loaded into memory.
The outcome therefore depends solely on each variable's chunk metadata, and is
the same whether or not loading a variable's contents would succeed.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. Whether a
-- variable is chunked, and the per-dimension block lengths it then exposes, are
-- observable properties of the variable supplied directly as inputs; the
-- accumulation and the inconsistency rejection are modeled deeply over those
-- inputs. Hence no `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- The touched observable properties of one array-like variable.

* `hasChunks` — whether the variable is chunked (answerable from chunk metadata
  alone, without loading the variable's contents);
* `chunksizes` — when chunked, the per-dimension block lengths, as
  `(dimension name, block lengths)` pairs in dimension order;
* `isDuckArray` — whether the variable already holds an in-place array handle;
* `materializeRaises` — whether forcing the variable's contents into memory
  would fail (e.g. an unreachable backing store).

`isDuckArray` and `materializeRaises` describe what happens if the variable's
contents are loaded; a correct computation of the chunk-size mapping never needs
them, and the specification below is deliberately independent of both. -/
structure XVar where
  hasChunks : Bool
  chunksizes : List (String × List Nat)
  isDuckArray : Bool
  materializeRaises : Bool

/-- Record one `(dimension, block lengths)` entry into the accumulated mapping.
A new dimension is appended (preserving first-seen order); a dimension already
present with the *same* block lengths leaves the mapping unchanged; a dimension
present with *different* block lengths makes the collection inconsistent. -/
def insertChunk (acc : List (String × List Nat)) (p : String × List Nat) :
    Except Unit (List (String × List Nat)) :=
  match acc.lookup p.1 with
  | some c' => if c' = p.2 then .ok acc else .error ()
  | none    => .ok (acc ++ [p])

/-- Fold a single chunked variable's entries into the accumulator, rejecting on
the first inconsistency. -/
def mergePairs : List (String × List Nat) → List (String × List Nat) →
    Except Unit (List (String × List Nat))
  | acc, []      => .ok acc
  | acc, p :: ps =>
    match insertChunk acc p with
    | .error _ => .error ()
    | .ok acc' => mergePairs acc' ps

/-- The reference chunk-size mapping for a collection of variables, threaded
front-to-back. Non-chunked variables are skipped; chunked variables fold their
entries in, rejecting on the first inconsistency. Depends only on each
variable's chunk metadata (`hasChunks`, `chunksizes`). -/
def mergeVars : List XVar → List (String × List Nat) →
    Except Unit (List (String × List Nat))
  | [],      acc => .ok acc
  | v :: vs, acc =>
    if v.hasChunks then
      match mergePairs acc v.chunksizes with
      | .error _ => .error ()
      | .ok acc' => mergeVars vs acc'
    else mergeVars vs acc
-- pure-end

-- post-conditions-start
/-- The collected mapping is exactly the reference fold over the variables'
chunk metadata: each non-chunked variable contributes nothing, each chunked
variable contributes its per-dimension block lengths, inconsistent block lengths
for the same dimension are rejected, and dimensions appear in first-seen order.
The outcome is independent of whether loading any variable's contents would
succeed. -/
def problem_spec_getChunksizes (vars : List XVar)
    (result : Except Unit (List (String × List Nat))) : Prop :=
  result = mergeVars vars []
-- post-conditions-end

-- impl-start
def implementation_getChunksizes (vars : List XVar) :
    Except Unit (List (String × List Nat)) := Id.run do
  let mut chunks : List (String × List Nat) := []
  for v in vars do
    if v.hasChunks then
      for p in v.chunksizes do
        match chunks.lookup p.1 with
        | some c' => if c' ≠ p.2 then return .error ()
        | none    => chunks := chunks ++ [p]
  return .ok chunks
-- impl-end


-- proof-start
/-- Collapse the `for`-loop's early-return state `⟨earlyReturn?, acc⟩` back into
the `Except` result: a pending early return propagates, otherwise the loop
succeeded with its accumulator. This mirrors the impl's final `match`. -/
def loopFinish
    (r : MProd (Option (Except Unit (List (String × List Nat))))
              (List (String × List Nat))) :
    Except Unit (List (String × List Nat)) :=
  match r.fst with
  | some e => e
  | none   => .ok r.snd

/-- Pure functional counterpart of the inner `for p in v.chunksizes` loop,
mirroring its early-return-on-inconsistency semantics. -/
def innerLoop : List (String × List Nat) → List (String × List Nat) →
    Except Unit (List (String × List Nat))
  | acc, []      => .ok acc
  | acc, p :: ps =>
    match acc.lookup p.1 with
    | some c' => if c' ≠ p.2 then .error () else innerLoop acc ps
    | none    => innerLoop (acc ++ [p]) ps

/-- Pure functional counterpart of the outer `for v in vars` loop, threading the
accumulator and propagating the first inconsistency. -/
def outerLoop : List (String × List Nat) → List XVar →
    Except Unit (List (String × List Nat))
  | acc, []      => .ok acc
  | acc, v :: vs =>
    if v.hasChunks then
      match innerLoop acc v.chunksizes with
      | .error _ => .error ()
      | .ok acc' => outerLoop acc' vs
    else outerLoop acc vs

theorem inner_forIn_eq_innerLoop (acc pairs : List (String × List Nat)) :
    loopFinish
      (forIn (m := Id) pairs
        (⟨none, acc⟩ : MProd (Option (Except Unit (List (String × List Nat))))
                            (List (String × List Nat)))
        (fun p r =>
          match r.snd.lookup p.1 with
          | some c' =>
            if c' ≠ p.2 then pure (ForInStep.done ⟨some (Except.error ()), r.snd⟩)
            else pure (ForInStep.yield ⟨none, r.snd⟩)
          | none => pure (ForInStep.yield ⟨none, r.snd ++ [p]⟩))) =
      innerLoop acc pairs := by
  induction pairs generalizing acc with
  | nil => rfl
  | cons p ps ih =>
    rw [List.forIn_cons]
    dsimp only
    unfold innerLoop
    split
    · split
      · rfl
      · exact ih acc
    · exact ih (acc ++ [p])

theorem outer_forIn_eq_outerLoop (acc : List (String × List Nat)) (vars : List XVar) :
    loopFinish
      (forIn (m := Id) vars
        (⟨none, acc⟩ : MProd (Option (Except Unit (List (String × List Nat))))
                            (List (String × List Nat)))
        (fun v r =>
          if v.hasChunks = true then
            (do
              let r' ← forIn v.chunksizes
                (⟨none, r.snd⟩ : MProd (Option (Except Unit (List (String × List Nat))))
                                    (List (String × List Nat)))
                (fun p r =>
                  match r.snd.lookup p.1 with
                  | some c' =>
                    if c' ≠ p.2 then pure (ForInStep.done ⟨some (Except.error ()), r.snd⟩)
                    else pure (ForInStep.yield ⟨none, r.snd⟩)
                  | none => pure (ForInStep.yield ⟨none, r.snd ++ [p]⟩))
              match r'.fst with
              | none   => pure (ForInStep.yield ⟨none, r'.snd⟩)
              | some a => pure (ForInStep.done ⟨some a, r'.snd⟩))
          else pure (ForInStep.yield ⟨none, r.snd⟩))) =
      outerLoop acc vars := by
  have hinner : ∀ (pairs : List (String × List Nat)) (a : List (String × List Nat)),
      (match innerLoop a pairs with
       | .ok acc' =>
           (forIn (m := Id) pairs
             (⟨none, a⟩ : MProd (Option (Except Unit (List (String × List Nat))))
                               (List (String × List Nat)))
             (fun p r =>
               match r.snd.lookup p.1 with
               | some c' =>
                 if c' ≠ p.2 then pure (ForInStep.done ⟨some (Except.error ()), r.snd⟩)
                 else pure (ForInStep.yield ⟨none, r.snd⟩)
               | none => pure (ForInStep.yield ⟨none, r.snd ++ [p]⟩)))
             = ⟨none, acc'⟩
       | .error _ =>
           ∃ s, (forIn (m := Id) pairs
             (⟨none, a⟩ : MProd (Option (Except Unit (List (String × List Nat))))
                               (List (String × List Nat)))
             (fun p r =>
               match r.snd.lookup p.1 with
               | some c' =>
                 if c' ≠ p.2 then pure (ForInStep.done ⟨some (Except.error ()), r.snd⟩)
                 else pure (ForInStep.yield ⟨none, r.snd⟩)
               | none => pure (ForInStep.yield ⟨none, r.snd ++ [p]⟩)))
             = ⟨some (Except.error ()), s⟩) := by
    intro pairs
    induction pairs with
    | nil => intro a; rfl
    | cons p ps ih =>
      intro a
      rw [List.forIn_cons]
      simp only [innerLoop]
      cases hl : a.lookup p.1 with
      | none => exact ih (a ++ [p])
      | some c' =>
        by_cases hc : c' ≠ p.2
        · simp only [if_pos hc]; exact ⟨a, rfl⟩
        · simp only [if_neg hc]; exact ih a
  induction vars generalizing acc with
  | nil => rfl
  | cons v vs ih =>
    rw [List.forIn_cons]
    simp only [outerLoop]
    by_cases hv : v.hasChunks = true
    · simp only [hv, if_true]
      have := hinner v.chunksizes acc
      cases hIL : innerLoop acc v.chunksizes with
      | error e =>
        simp only [hIL] at this
        obtain ⟨s, hs⟩ := this
        rw [hs]
        rfl
      | ok acc' =>
        simp only [hIL] at this
        rw [this]
        exact ih acc'
    · simp only [Bool.not_eq_true] at hv
      simp only [hv, Bool.false_eq_true, if_false]
      exact ih acc

theorem impl_eq_outerLoop (vars : List XVar) :
    implementation_getChunksizes vars = outerLoop [] vars := by
  rw [← outer_forIn_eq_outerLoop]
  simp only [implementation_getChunksizes, Id.run, loopFinish, bind, pure]
  split <;> rename_i h <;> rw [h]

theorem innerLoop_eq_mergePairs (acc pairs : List (String × List Nat)) :
    innerLoop acc pairs = mergePairs acc pairs := by
  induction pairs generalizing acc with
  | nil => rfl
  | cons p ps ih =>
    rw [innerLoop, mergePairs, insertChunk]
    cases h : acc.lookup p.1 with
    | none => simp [ih]
    | some c' =>
      by_cases hc : c' = p.2
      · simp [hc, ih]
      · simp [hc]

theorem outerLoop_eq_mergeVars (acc : List (String × List Nat)) (vars : List XVar) :
    outerLoop acc vars = mergeVars vars acc := by
  induction vars generalizing acc with
  | nil => rfl
  | cons v vs ih =>
    unfold outerLoop mergeVars
    cases h : v.hasChunks with
    | false => simp only [Bool.false_eq_true, if_false]; exact ih acc
    | true =>
      simp only [if_true]
      rw [innerLoop_eq_mergePairs]
      cases mergePairs acc v.chunksizes with
      | error e => rfl
      | ok acc' => exact ih acc'

theorem correct_getChunksizes : ∀ vars,
    problem_spec_getChunksizes vars (implementation_getChunksizes vars) := by
  intro vars
  unfold problem_spec_getChunksizes
  rw [impl_eq_outerLoop, outerLoop_eq_mergeVars]

-- proof-end

#print axioms correct_getChunksizes
