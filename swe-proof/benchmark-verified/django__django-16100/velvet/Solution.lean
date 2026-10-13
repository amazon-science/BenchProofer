import Velvet.Std
-- imports-end

-- Total correctness: the modeled save loop is a bounded pass over a finite
-- batch of queued updates that always terminates and reports its commit set,
-- so a diverging implementation must NOT satisfy the spec (partial
-- correctness would admit it vacuously).
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No consumed axioms. The all-or-nothing commit behaviour the desired
--  semantics requires is modeled DEEPLY in the `pure` region (`committedAtomic`): a batch of
--  record updates is committed only if the whole batch is processed without an
--  error, otherwise no update is committed. The unchanged commit/rollback
--  machinery this rides on is an A-reference, validated against the real
--  transaction manager by axiom_check.py (G-AX); there is no module-level
--  `axiom`. mapping.md §3.)
-- axioms-end

-- pure-start
/- One queued record update in a save batch. The only facts the desired
   behaviour distinguishes are: whether this row was actually edited (`changed`
   — an unedited row stages no write), the new value its write would persist
   (`value` — an opaque identity token; presence in the result means the write
   was committed), and whether processing this row encounters an error
   (`raises` — e.g. a downstream step signalling a failure). Everything else
   about the record is orthogonal (mapping.md §2). -/
structure Upd where
  changed : Bool
  value   : Int
  raises  : Bool
deriving Inhabited, DecidableEq

/- Does processing the batch encounter an error? An error can only arise while
   processing an edited row (an unedited row stages no work). Front-recursive so
   a single unfold is available per loop step (the fold pattern, plan §5.4). -/
def anyFail : List Upd → Bool
  | []      => false
  | u :: us => (u.changed && u.raises) || anyFail us

/- The values the edited rows would stage, in batch order — what a clean run of
   the batch commits. Front-recursive (the fold pattern). -/
def changedVals : List Upd → List Int
  | []      => []
  | u :: us => (if u.changed then [u.value] else []) ++ changedVals us

/- The set of writes actually committed after the WHOLE batch is processed under
   all-or-nothing semantics: if any error is encountered anywhere in the batch,
   nothing is committed (the batch is rolled back as a unit); otherwise every
   edited row's write is committed. This is the desired behaviour — partial
   progress is never left behind when the batch fails midway. -/
def committedAtomic (us : List Upd) : List Int :=
  if anyFail us then [] else changedVals us

@[simp] lemma anyFail_nil : anyFail [] = false := rfl
@[simp] lemma changedVals_nil : changedVals [] = [] := rfl
lemma anyFail_cons (u : Upd) (us : List Upd) :
    anyFail (u :: us) = ((u.changed && u.raises) || anyFail us) := rfl
lemma changedVals_cons (u : Upd) (us : List Upd) :
    changedVals (u :: us) = (if u.changed then [u.value] else []) ++ changedVals us := rfl

/- Exposing the element at index `i` on the front of `drop i`. -/
lemma drop_cons_eq (us : List Upd) (i : Nat) (hi : i < us.length) :
    us.drop i = us[i]! :: us.drop (i + 1) := by
  have h := List.drop_eq_getElem_cons hi
  rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi, Option.getD_some]
  exact h

/- The per-row fold step for the error scan: dropping one fewer element exposes
   row `i-1` on the front, so the scan peels its error contribution. -/
lemma anyFail_drop_step (us : List Upd) (i : Nat) (hi : 0 < i) (hle : i ≤ us.length) :
    anyFail (us.drop (i - 1)) =
      ((us[i - 1]!.changed && us[i - 1]!.raises) || anyFail (us.drop i)) := by
  have hlt : i - 1 < us.length := by omega
  have hsucc : i - 1 + 1 = i := by omega
  rw [drop_cons_eq us (i - 1) hlt, hsucc, anyFail_cons]

/- The per-row fold step for the staged values. -/
lemma changedVals_drop_step (us : List Upd) (i : Nat) (hi : 0 < i) (hle : i ≤ us.length) :
    changedVals (us.drop (i - 1)) =
      (if us[i - 1]!.changed then [us[i - 1]!.value] else []) ++ changedVals (us.drop i) := by
  have hlt : i - 1 < us.length := by omega
  have hsucc : i - 1 + 1 = i := by omega
  rw [drop_cons_eq us (i - 1) hlt, hsucc, changedVals_cons]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Process a batch of queued record updates and report which writes end up
   committed. Desired behaviour (all-or-nothing): the batch is a single unit of
   work — if processing any row raises an error, the result must commit NOTHING
   (every staged write is rolled back, so a failure midway leaves no partial
   progress); only a batch processed end-to-end without error commits its edited
   rows' writes. `updates` is read-only (not `mut`): the batch description is not
   mutated, only consulted (directive 5). -/
method processBatch (updates : List Upd) return (out : List Int)
  ensures out = committedAtomic updates
  do
    -- impl-start
    -- All staged writes accumulate in one unit of work (`staged`); `failed`
    -- records whether processing any row signalled an error escaping that unit.
    let mut staged : List Int := []
    let mut failed : Bool := false
    let mut i : Nat := updates.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ updates.length
      invariant staged = changedVals (updates.drop i)
      invariant failed = anyFail (updates.drop i)
      done_with i = 0
      decreasing i
    do
      let u := updates[i - 1]!
      -- an edited row stages its write into the unit of work; a downstream step
      -- may signal a failure of the unit while processing that row.
      staged := (if u.changed then [u.value] else []) ++ staged
      failed := (u.changed && u.raises) || failed
      i := i - 1
    -- Commit point: a clean unit commits its staged writes; a failed unit
    -- commits nothing (the whole batch is rolled back as one unit of work).
    let committed : List Int := if failed then [] else staged
    return committed
    -- impl-end

prove_correct processBatch by
  loom_solve <;>
    first
    | -- loop-entry: drop updates.length = [], both folds are nil.
      (rw [List.drop_length]; simp)
    | -- loop-body step: peel row `i-1` from the staged-values fold.
      (rw [changedVals_drop_step updates i (by omega) (by omega)]; simp_all)
    | -- loop-body step: peel row `i-1` from the error scan.
      (rw [anyFail_drop_step updates i (by omega) (by omega)]; simp_all)
    | -- exit (i = 0): `drop 0 = updates`, so the commit equals `committedAtomic`.
      (simp only [committedAtomic] at *; simp_all)
