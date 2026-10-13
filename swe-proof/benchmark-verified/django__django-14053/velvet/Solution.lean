import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No consumed callee contracts. The per-pass producer of file events is an
--  unchanged callee whose only relevant effect is the SEQUENCE of (key, result)
--  observations it emits; that sequence is the read-only input `events` here.
--  The reporting transformation under spec is modeled deeply below — every
--  observable is computed from `events`, nothing is borrowed from an oracle.
--  See refinement.md / mapping.md.)
-- axioms-end

-- pure-start
/- One reported observation: a content key (`fst`) paired with the latest
   reported value for that key (`snd`). Keys identify the source item; values
   are the value most recently observed for it. -/
abbrev Obs := Int × Int

/- Insertion-ordered upsert: record value `v` under key `k`.
   - a key never seen before is appended at the end, keeping the order in which
     keys were first encountered;
   - a key already present keeps its original position but takes the NEW value.
   This is the exact semantics of assigning `m[k] = v` to an order-preserving
   mapping and then reading it back in key order. -/
def upsert (m : List Obs) (k v : Int) : List Obs :=
  match m with
  | []            => [(k, v)]
  | (k', v') :: r => if k' = k then (k, v) :: r else (k', v') :: upsert r k v

/- Fold one observation into the accumulating mapping. -/
def collectStep (m : List Obs) (e : Obs) : List Obs := upsert m e.1 e.2

/- The reported sequence built from a whole stream of observations: each
   observation upserts into the order-preserving mapping; the report is that
   mapping read out in key order. Net effect: every distinct key appears EXACTLY
   ONCE, in first-encounter order, carrying its LAST observed value. -/
def collect (events : List Obs) : List Obs := events.foldl collectStep []

/- Keys of an upsert: an already-present key leaves the key list unchanged; a
   fresh key is appended. -/
@[grind] lemma keys_upsert (m : List Obs) (k v : Int) :
    (upsert m k v).map Prod.fst
      = if k ∈ m.map Prod.fst then m.map Prod.fst else m.map Prod.fst ++ [k] := by
  induction m with
  | nil => simp [upsert]
  | cons hd tl ih =>
    obtain ⟨k', v'⟩ := hd
    by_cases hkk : k' = k
    · subst hkk; simp [upsert]
    · simp only [upsert, hkk, if_false, List.map_cons]
      by_cases hmem : k ∈ tl.map Prod.fst
      · simp [ih, hmem, List.mem_cons, Ne.symm hkk]
      · have : k ∉ (k', v').1 :: tl.map Prod.fst := by
          simp [List.mem_cons, Ne.symm hkk, hmem]
        simp [ih, hmem, List.mem_cons, Ne.symm hkk]

/- Upsert preserves key-uniqueness. -/
@[grind] lemma nodup_upsert (m : List Obs) (k v : Int)
    (h : (m.map Prod.fst).Nodup) : ((upsert m k v).map Prod.fst).Nodup := by
  rw [keys_upsert]
  by_cases hmem : k ∈ m.map Prod.fst
  · simp [hmem, h]
  · simp only [hmem, if_false]
    exact h.append (by simp) (by simp [hmem])

/- The accumulator's keys stay unique through any fold, starting from any
   key-unique seed. -/
lemma nodup_foldl (events : List Obs) :
    ∀ m, (m.map Prod.fst).Nodup → ((events.foldl collectStep m).map Prod.fst).Nodup := by
  induction events with
  | nil => intro m h; simpa using h
  | cons e es ih =>
    intro m h
    exact ih (collectStep m e) (by simpa [collectStep] using nodup_upsert m e.1 e.2 h)

/- The report never lists a key twice: no source item is reported more than
   once, regardless of how many observations carried that key. -/
@[grind] lemma collect_nodup (events : List Obs) :
    ((collect events).map Prod.fst).Nodup :=
  nodup_foldl events [] (by simp)

/- Forward-fold step: extending the consumed prefix by one observation upserts
   that observation into the mapping built from the shorter prefix. The single
   goal `loom_solve` leaves for the loop body. -/
lemma collect_take_step (events : List Obs) (i : Nat) (hi : i < events.length) :
    (events.take (i + 1)).foldl collectStep []
      = collectStep ((events.take i).foldl collectStep []) events[i]! := by
  have hcons : events.take (i + 1) = events.take i ++ [events[i]!] := by
    rw [List.take_succ, List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi]
    simp
  rw [hcons, List.foldl_append, List.foldl_cons, List.foldl_nil]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Build the sequence reported back to the caller from the full stream of
   per-pass observations `events`.
   The result is exactly the order-preserving, keep-last collapse of the stream:
   every distinct key appears once (no key is reported twice), in first-encounter
   order, carrying the value most recently observed for it. `events` is read-only
   (not `mut`): the loop builds a fresh result and never mutates its input. -/
method reportCollected (events : List Obs) return (out : List Obs)
  ensures out = collect events
  ensures (out.map Prod.fst).Nodup
  do
    -- impl-start
    let mut result : List Obs := []
    let mut i := 0
    while i < events.length
      invariant i ≤ events.length
      invariant result = (events.take i).foldl collectStep []
      done_with i = events.length
      decreasing events.length - i
    do
      let e := events[i]!
      result := upsert result e.1 e.2
      i := i + 1
    return result
    -- impl-end

prove_correct reportCollected by
  loom_solve
  case «invariant_2: result = (events.take i).foldl collectStep []» =>
    have hi : i < events.length := by omega
    rw [invariant_2, collect_take_step events i hi, collectStep,
        List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi]
  case «ensures_1: (out.map Prod.fst).Nodup» =>
    have h := collect_nodup events
    simp_all [collect]
  all_goals simp_all [collect]
