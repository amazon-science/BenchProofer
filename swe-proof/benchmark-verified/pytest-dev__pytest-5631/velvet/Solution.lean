import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No axioms. The behaviour under specification is modeled DEEPLY in the `pure`
   region below; it calls no unchanged outside operation whose contract would
   need to be assumed. See refinement.md (every step is R or I; no A). -/
-- axioms-end

-- pure-start
/- One entry in the list being scanned. Each entry carries:
   * `isAttribute` — the entry is bound to a named attribute (such entries are
     skipped by the count);
   * `valueId` — the OPAQUE object identity of the replacement value the entry
     installs (two distinct values have distinct ids; identity is decidable and
     total);
   * `eqTotal` — whether that replacement value has a *total* equality test,
     i.e. comparing it for equality against an arbitrary object always yields a
     boolean and never aborts. Some values (problem statement: array-like
     objects) have a NON-total equality test. -/
structure ArgEntry where
  isAttribute : Bool
  valueId     : Nat
  eqTotal     : Bool
deriving Repr, Inhabited

/- The outcome of the scan: `err` is set iff the scan aborted (the problem
   statement's `ValueError`); `n` is the number of counted entries. -/
structure CountResult where
  err : Bool
  n   : Nat
deriving Repr, Inhabited

/- The two sentinel markers, as opaque object identities. An entry's replacement
   value designates a marker exactly when its identity equals one of these. -/
def markerA : Nat := 0
def markerB : Nat := 1

/- An entry is counted exactly when it is not bound to a named attribute AND its
   replacement value's identity is one of the two markers. This is decided by
   IDENTITY (`valueId == marker`), which is total — it inspects no value
   contents and so can never abort. -/
def hitsMarker (e : ArgEntry) : Bool :=
  (!e.isAttribute) && (e.valueId == markerA || e.valueId == markerB)

def contrib (e : ArgEntry) : Nat := if hitsMarker e then 1 else 0

/- The count over a whole list: the sum of per-entry contributions. Front
   recursive so a single unfold is available per loop step (the Velvet fold
   pattern). -/
def sentinelCount : List ArgEntry → Nat
  | []      => 0
  | e :: es => contrib e + sentinelCount es

@[grind] lemma sentinelCount_nil : sentinelCount [] = 0 := rfl
@[grind] lemma sentinelCount_cons (e : ArgEntry) (es : List ArgEntry) :
    sentinelCount (e :: es) = contrib e + sentinelCount es := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method countSentinelArgs (entries : List ArgEntry) return (out : CountResult)
  ensures out.err = false
  ensures out.n = sentinelCount entries
  do
    -- impl-start
    let mut cnt : Nat := 0
    let mut i := entries.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ entries.length
      invariant cnt = sentinelCount (entries.drop i)
      done_with i = 0
      decreasing i
    do
      let e := entries[i - 1]!
      if hitsMarker e then
        cnt := cnt + 1
      else
        cnt := cnt
      i := i - 1
    return ⟨false, cnt⟩
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the entry at
   `i-1` on the front, so `sentinelCount` peels one `contrib`. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma sentinelCount_drop_step (es : List ArgEntry) (i : Nat)
    (hi : 0 < i) (hle : i ≤ es.length) :
    sentinelCount (es.drop (i - 1)) = contrib es[i - 1]! + sentinelCount (es.drop i) := by
  have hlt : i - 1 < es.length := by omega
  have hcons : es.drop (i - 1) = es[i - 1]! :: es.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, sentinelCount_cons]

prove_correct countSentinelArgs by
  loom_solve
  all_goals
    rw [sentinelCount_drop_step entries i (by omega) (by omega)]
    simp only [contrib]
    split <;> simp_all <;> omega
