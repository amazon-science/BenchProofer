import Velvet.Std
-- imports-end

-- Total correctness: the modeled reduction is a bounded fold over a finite
-- stamp list that always terminates and returns, so a diverging implementation
-- must NOT satisfy the spec (partial correctness would admit it vacuously).
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees: the reported value is the greatest of the collected
--  per-entry stamps, modeled deeply as a running maximum over `List Int`. There
--  is no unchanged library callee the proof must axiomatize.)
-- axioms-end

-- pure-start
/- The latest stamp reported across a collection of comparable per-entry stamps.
   With no entries the collection is empty and there is no stamp to report, so
   the result is the absent marker `none` (reporting a latest stamp over an empty
   collection must NOT fail). With one or more entries the result is the greatest
   stamp. Front-recursive so a single unfold is available per loop step (the
   Velvet fold pattern). -/
def latestStamp : List Int → Option Int
  | []      => none
  | c :: cs =>
      some (match latestStamp cs with
            | none   => c
            | some m => max c m)

@[grind] lemma latestStamp_nil : latestStamp [] = none := rfl
@[grind] lemma latestStamp_cons (c : Int) (cs : List Int) :
    latestStamp (c :: cs) =
      some (match latestStamp cs with | none => c | some m => max c m) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- A section that exposes a per-entry modification stamp reports the most recent
   stamp across its entries. The per-entry stamp function applied across the
   enumerated entries yields a collection of comparable values, modeled as
   `List Int`; the reported value is `Option Int`.

   Two guarantees pin the behavior the issue demands:

   - when the section enumerates NO entries, the collection is empty and the
     reported value is the absent marker `none` — computing a latest stamp over
     an empty section must NOT fail;
   - when the section enumerates one or more entries, the reported value is the
     greatest stamp in the collection: it is one of the collected stamps and is
     greater than or equal to every collected stamp.

   `stamps` is read-only (not `mut`); the reduction builds a fresh result and
   mutates nothing (directive 5). -/
method latestLastmod (stamps : List Int) return (out : Option Int)
  ensures out = latestStamp stamps
  ensures stamps.length = 0 → out = none
  ensures stamps.length > 0 → ∃ v, out = some v
  ensures ∀ k, k < stamps.length →
    ∃ v, out = some v ∧ stamps[k]! ≤ v
  ensures ∀ v, out = some v →
    ∃ k, k < stamps.length ∧ stamps[k]! = v
  do
    -- impl-start
    let mut result : Option Int := none
    let mut i := stamps.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ stamps.length
      invariant result = latestStamp (stamps.drop i)
      done_with i = 0
      decreasing i
    do
      let c := stamps[i - 1]!
      result := some (match result with | none => c | some m => max c m)
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `latestStamp` peels one running-maximum step. This is
   the single goal `loom_solve` leaves for the loop body. -/
lemma latestStamp_drop_step (stamps : List Int) (i : Nat)
    (hi : 0 < i) (hle : i ≤ stamps.length) :
    latestStamp (stamps.drop (i - 1)) =
      some (match latestStamp (stamps.drop i) with
            | none => stamps[i - 1]! | some m => max stamps[i - 1]! m) := by
  have hlt : i - 1 < stamps.length := by omega
  have hcons : stamps.drop (i - 1) = stamps[i - 1]! :: stamps.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, latestStamp_cons]

/- `latestStamp` is `none` exactly on the empty collection. -/
@[grind] lemma latestStamp_eq_none_iff (xs : List Int) :
    latestStamp xs = none ↔ xs = [] := by
  cases xs with
  | nil => simp [latestStamp]
  | cons c cs => simp [latestStamp]

/- Every reported stamp dominates each collected stamp. -/
@[grind] lemma latestStamp_dominates (xs : List Int) :
    ∀ k, k < xs.length → ∃ v, latestStamp xs = some v ∧ xs[k]! ≤ v := by
  induction xs with
  | nil => intro k h; simp at h
  | cons c cs ih =>
      intro k h
      cases hcs : latestStamp cs with
      | none =>
          have hcsempty : cs = [] := (latestStamp_eq_none_iff cs).mp hcs
          subst hcsempty
          have hk0 : k = 0 := by simp at h; omega
          subst hk0
          exact ⟨c, by simp [latestStamp], by simp⟩
      | some m =>
          have hgoal : latestStamp (c :: cs) = some (max c m) := by
            rw [latestStamp_cons, hcs]
          rcases k with _ | k
          · exact ⟨max c m, hgoal, by simpa using le_max_left c m⟩
          · refine ⟨max c m, hgoal, ?_⟩
            have h' : k < cs.length := by simpa using h
            obtain ⟨v, hv, hle⟩ := ih k h'
            rw [hcs] at hv
            have hvm : m = v := by simpa using hv
            have hidx : (c :: cs)[k+1]! = cs[k]! := by
              simp [List.getElem!_eq_getElem?_getD]
            rw [hidx, hvm]
            exact le_trans hle (le_max_right c v)

/- Every reported stamp is one of the collected stamps. -/
@[grind] lemma latestStamp_member (xs : List Int) :
    ∀ v, latestStamp xs = some v → ∃ k, k < xs.length ∧ xs[k]! = v := by
  induction xs with
  | nil => intro v h; simp [latestStamp] at h
  | cons c cs ih =>
      intro v h
      rw [latestStamp_cons] at h
      cases hcs : latestStamp cs with
      | none =>
          rw [hcs] at h
          have hvc : v = c := by simp at h; exact h.symm
          subst hvc
          exact ⟨0, by simp, by simp⟩
      | some m =>
          rw [hcs] at h
          have hv : v = max c m := by simp at h; exact h.symm
          subst hv
          rcases max_choice c m with hmc | hmc
          · rw [hmc]; exact ⟨0, by simp, by simp⟩
          · rw [hmc]
            obtain ⟨k, hk, hkm⟩ := ih m (by rw [hcs])
            refine ⟨k+1, by simpa using hk, ?_⟩
            have hidx : (c :: cs)[k+1]! = cs[k]! := by
              simp [List.getElem!_eq_getElem?_getD]
            rw [hidx]; exact hkm

prove_correct latestLastmod by
  loom_solve
  rw [latestStamp_drop_step stamps i (by omega) (by omega)]
  rw [‹result = latestStamp (stamps.drop i)›]
