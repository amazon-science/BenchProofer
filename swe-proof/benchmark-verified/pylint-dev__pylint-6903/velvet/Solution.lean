import Velvet.Std
-- imports-end

/- Total correctness: the modeled operation is the straight-line post-processing
   tail of the real routine (one comparison, one conditional assignment, one
   return) and always terminates, so a diverging implementation must NOT
   satisfy this spec. Partial correctness would let a non-terminating body
   discharge every postcondition vacuously. -/
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The processor-count estimate is produced by an
--  unchanged upstream computation — reading the environment's resource limits
--  and dividing — whose result is taken here as a plain optional input. The
--  operation under spec does not change how that estimate is produced; it only
--  post-processes the estimate, so there is no library callee the proof must
--  axiomatize.)
-- axioms-end

-- pure-start
/- A processor-count estimate that may be absent (`none`, when the environment
   exposes no figure to read). Post-processing the estimate so it is fit to use:
   an estimate that resolves to exactly zero is not a usable count, so it is
   raised to the smallest usable count, one; any other resolved estimate is kept
   exactly as produced, and an absent estimate stays absent. Modeled over
   `Option Int` (the estimate is an optional signed count). -/
def clampCount : Option Int → Option Int
  | none   => none
  | some n => if n = 0 then some 1 else some n

@[grind] lemma clampCount_none : clampCount none = none := rfl
@[grind] lemma clampCount_some (n : Int) :
    clampCount (some n) = (if n = 0 then some 1 else some n) := rfl

/- The post-processed estimate is never the unusable zero. -/
@[grind] lemma clampCount_ne_some_zero (a : Option Int) : clampCount a ≠ some 0 := by
  cases a with
  | none => simp [clampCount]
  | some n =>
      rw [clampCount_some]
      by_cases h : n = 0
      · simp [h]
      · simp [h]

/- An estimate that is not the unusable zero is post-processed to itself: the
   only estimate the post-processing rewrites is the zero one. -/
@[grind] lemma clampCount_eq_self_of_ne (a : Option Int) (h : a ≠ some 0) :
    clampCount a = a := by
  cases a with
  | none => rfl
  | some n =>
      rw [clampCount_some]
      have hn : n ≠ 0 := by intro hz; exact h (by rw [hz])
      simp [hn]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- An optional processor-count estimate is post-processed before it is handed to
   the component that needs a positive count of workers. The estimate is optional
   because the surrounding environment may expose no figure at all.

   The post-processing pins the behavior the issue demands:

   - an absent estimate stays absent (nothing to post-process);
   - an estimate that resolves to exactly zero is raised to one — a count of zero
     is not a usable number of workers and must never be reported;
   - any other resolved estimate is reported exactly as produced.

   In particular the reported value is NEVER the unusable zero. `avail` is the
   estimate as produced by the unchanged upstream computation; it is read-only —
   the operation derives a fresh result and mutates nothing it was handed
   (directive 5). The estimate and the result are modeled as `Option Int`. -/
method clampedCpuCount (avail : Option Int) return (out : Option Int)
  ensures out = clampCount avail
  ensures avail = none → out = none
  ensures avail = some 0 → out = some 1
  ensures ∀ n, avail = some n → n ≠ 0 → out = some n
  ensures out ≠ some 0
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct clampedCpuCount by
  -- proof elided — supplied by the consumer
