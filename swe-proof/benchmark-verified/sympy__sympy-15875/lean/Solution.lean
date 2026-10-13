import Mathlib
-- imports-end

/-!
Deciding whether a finite sum of terms is definitely zero, definitely nonzero,
or undetermined — a three-valued verdict (`some true` / `some false` / `none`).

Each term is pre-classified by where it lives:

* `realZero`     — a real term already known to be zero;
* `realNonzero`  — a real term known to be nonzero;
* `realUnknown`  — a real term whose zero-ness cannot be settled;
* `imaginary`    — a purely imaginary (nonzero) term;
* `imagOrZero`   — a term that is either purely imaginary or zero (its product
                   with the imaginary unit is real), but which is not pinned to
                   be purely imaginary;
* `indeterminate`— a term that fits none of the above categories.

The verdict must be *sound*: it may answer `none` (undetermined) whenever it
cannot be sure, but every definite zero/nonzero answer it gives must hold. The
decision also consumes one auxiliary three-valued fact —
`realSumZero`, whether the combined sum of just the definitely-nonzero real
terms is itself zero — since cancellation among those terms can still occur.

The governing principle this captures: when every term is real and zero the sum
is zero; when there is no definitely-nonzero real term to anchor the real part
(or every term is such a term), no definite verdict about the whole sum is
warranted and the answer must stay undetermined; otherwise the real anchor plus
the imaginary content jointly decide the outcome.
-/

-- axioms-start
-- No unchanged outside callee is consumed. Each term's category is supplied as
-- an input classification (`Summand`), and the three-valued zero-test of the
-- real anchor sub-sum is supplied as the input `realSumZero`, so the verdict is
-- grounded directly in the inputs and the proof needs no callee contract.
-- (G-AX is a skip stub.)
-- axioms-end

-- pure-start
/-- Category of a single summand (see module docstring). -/
inductive Summand
  | realZero
  | realNonzero
  | realUnknown
  | imaginary
  | imagOrZero
  | indeterminate
deriving DecidableEq, Repr

/-- A real term whose zero-ness cannot be decided, or a wholly unclassifiable
term: either forces the overall verdict to be undetermined. -/
def isUnclassified : Summand → Bool
  | .realUnknown => true
  | .indeterminate => true
  | _ => false

def isRealZero : Summand → Bool
  | .realZero => true
  | _ => false

def isRealNonzero : Summand → Bool
  | .realNonzero => true
  | _ => false

def isImag : Summand → Bool
  | .imaginary => true
  | _ => false

def isImagOrZero : Summand → Bool
  | .imagOrZero => true
  | _ => false

/-- The sound three-valued zero-verdict for the whole sum, as a total function
of the term categories and the real-anchor fact `realSumZero`. -/
def zeroVerdict (terms : List Summand) (realSumZero : Option Bool) : Option Bool :=
  if terms.any isUnclassified then
    none
  else
    let z := terms.countP isRealZero
    let nz := terms.countP isRealNonzero
    let n := terms.length
    let im := terms.any isImag
    let imOrZ := terms.any isImagOrZero
    if z == n then
      some true
    else if nz == 0 || nz == n then
      none
    else
      match realSumZero with
      | some true =>
          if !imOrZ && !im then some true
          else if im && !imOrZ then some false
          else none
      | some false => some false
      | none => none
-- pure-end

-- post-conditions-start
/-- The result is exactly the sound three-valued zero-verdict determined by the
term categories and the real-anchor fact. This pins every case: a sum of only
real-zero terms is zero; a sum with no definitely-nonzero real anchor (or made
up entirely of such terms) is undetermined; otherwise the anchor combined with
the imaginary content decides, and any presence of an undecidable real term or
an unclassifiable term forces `none`. -/
def problem_spec_zeroStatus
    (terms : List Summand) (realSumZero : Option Bool) (result : Option Bool) : Prop :=
  result = zeroVerdict terms realSumZero
-- post-conditions-end

-- impl-start
def implementation_zeroStatus
    (terms : List Summand) (realSumZero : Option Bool) : Option Bool := Id.run do
  let mut z := 0
  let mut nz := 0
  let mut im := false
  let mut imOrZ := false
  for a in terms do
    match a with
    | .realZero => z := z + 1
    | .realNonzero => nz := nz + 1
    | .realUnknown => return none
    | .imaginary => im := true
    | .imagOrZero => imOrZ := true
    | .indeterminate => return none
  if z == terms.length then
    return some true
  if nz == 0 || nz == terms.length then
    return none
  match realSumZero with
  | some true =>
      if !imOrZ && !im then
        return some true
      if im && !imOrZ then
        return some false
  | some false => return some false
  | none => pure ()
  return none
-- impl-end


-- proof-start
/-- The mutable state tracked by the imperative loop: the running counts of
real-zero (`z`) and real-nonzero (`nz`) terms, and the imaginary (`im`) /
imaginary-or-zero (`imOrZ`) presence flags. -/
structure LoopState where
  z : Nat
  nz : Nat
  im : Bool
  imOrZ : Bool

/-- Pure model of the loop body: updates the accumulator for a classified term,
or signals early exit (`none`) on an unclassifiable term. -/
def stepState (s : LoopState) (a : Summand) : Option LoopState :=
  match a with
  | .realZero => some { s with z := s.z + 1 }
  | .realNonzero => some { s with nz := s.nz + 1 }
  | .realUnknown => none
  | .imaginary => some { s with im := true }
  | .imagOrZero => some { s with imOrZ := true }
  | .indeterminate => none

/-- Pure model of the implementation's post-loop decision cascade. Structurally
identical to the `else`-branch of `zeroVerdict`. -/
def postDecide (s : LoopState) (n : Nat) (realSumZero : Option Bool) : Option Bool :=
  if s.z == n then some true
  else if s.nz == 0 || s.nz == n then none
  else
    match realSumZero with
    | some true =>
        if !s.imOrZ && !s.im then some true
        else if s.im && !s.imOrZ then some false
        else none
    | some false => some false
    | none => none

/-- Pure recursive model of the whole imperative computation: fold the loop body
over the list (short-circuiting to `none` on an unclassifiable term), then apply
the post-loop decision at the empty tail. -/
def loopRec (n : Nat) (realSumZero : Option Bool) : List Summand → LoopState → Option Bool
  | [], s => postDecide s n realSumZero
  | a :: l, s =>
      match stepState s a with
      | none => none
      | some s' => loopRec n realSumZero l s'
/-- The REAL elaborated loop-state type threaded by the desugared `for` loop:
the early-return slot (`Option (Option Bool)`) bundled with the `im`, `imOrZ`
flags and the `nz`, `z` counts, in the exact order Lean packs them
(`⟨slot, im, imOrZ, nz, z⟩`). -/
abbrev PS := MProd (Option (Option Bool)) (MProd Bool (MProd Bool (MProd Nat Nat)))

/-- Refinement map from the packed loop state to the model `LoopState`,
dropping the early-return slot. `PS` is `⟨slot, im, imOrZ, nz, z⟩`;
`LoopState` is `⟨z, nz, im, imOrZ⟩`. -/
def toLS (p : PS) : LoopState := ⟨p.2.2.2.2, p.2.2.2.1, p.2.1, p.2.2.1⟩

/-- Pure model of the elaborated loop body: the accumulating constructors
`yield` a slot-`none` state with one field bumped; the two unclassifiable
constructors `done` with the slot set to `some none` (early return). -/
def forInBodyPS (a : Summand) (p : PS) : ForInStep PS :=
  match a with
  | .realZero => ForInStep.yield ⟨none, p.2.1, p.2.2.1, p.2.2.2.1, p.2.2.2.2 + 1⟩
  | .realNonzero => ForInStep.yield ⟨none, p.2.1, p.2.2.1, p.2.2.2.1 + 1, p.2.2.2.2⟩
  | .realUnknown => ForInStep.done ⟨some none, p.2.1, p.2.2.1, p.2.2.2.1, p.2.2.2.2⟩
  | .imaginary => ForInStep.yield ⟨none, true, p.2.2.1, p.2.2.2.1, p.2.2.2.2⟩
  | .imagOrZero => ForInStep.yield ⟨none, p.2.1, true, p.2.2.2.1, p.2.2.2.2⟩
  | .indeterminate => ForInStep.done ⟨some none, p.2.1, p.2.2.1, p.2.2.2.1, p.2.2.2.2⟩

/-- Pure model of the elaborated post-loop projection + decision cascade:
if the early-return slot is set (`some a`) return `a`; otherwise run the same
`z==n / nz==0∨nz==n / realSumZero` cascade as `postDecide`. -/
def postLoopPS (n : Nat) (realSumZero : Option Bool) (p : PS) : Option Bool :=
  match p.1 with
  | some a => a
  | none =>
      if p.2.2.2.2 == n then some true
      else if p.2.2.2.1 == 0 || p.2.2.2.1 == n then none
      else match realSumZero with
        | some true =>
            if !p.2.2.1 && !p.2.1 then some true
            else if p.2.1 && !p.2.2.1 then some false
            else none
        | some false => some false
        | none => none

/-- The WHOLE `Option Bool`-valued computation continuing from suffix `l` and
packed state `p`: finish the `forIn` loop, then run the post-loop cascade. This
is what the generalized lemma equates to `loopRec` (NOT the bare `forIn`). -/
def runFrom (n : Nat) (realSumZero : Option Bool) (l : List Summand) (p : PS) : Option Bool :=
  Id.run (forIn l p (fun a r => pure (forInBodyPS a r)) >>= fun r => pure (postLoopPS n realSumZero r))

/-- Base unfold of the full computation: an empty suffix runs only the
post-loop cascade. -/
theorem runFrom_nil (n : Nat) (realSumZero : Option Bool) (p : PS) :
    runFrom n realSumZero [] p = postLoopPS n realSumZero p := rfl

/-- One-step unfold of the full computation: run the body on the head; on
`yield` recurse on the tail, on `done` short-circuit into the post-loop
cascade. -/
theorem runFrom_cons (n : Nat) (realSumZero : Option Bool) (a : Summand)
    (l : List Summand) (p : PS) :
    runFrom n realSumZero (a :: l) p
      = (match forInBodyPS a p with
          | ForInStep.yield p' => runFrom n realSumZero l p'
          | ForInStep.done p'' => postLoopPS n realSumZero p'') := by
  cases a <;> simp only [runFrom, forInBodyPS, List.forIn_cons] <;> rfl

/-- With the early-return slot empty, the post-loop cascade coincides with
`postDecide` on the projected model state. -/
theorem postLoop_slot_none (n : Nat) (realSumZero : Option Bool) (p : PS)
    (h : p.1 = none) :
    postLoopPS n realSumZero p = postDecide (toLS p) n realSumZero := by
  unfold postLoopPS postDecide toLS
  rw [h]

/-- With the early-return slot set to `some r`, the post-loop cascade returns
`r` directly (the early return short-circuits the decision). -/
theorem postLoop_slot_some (n : Nat) (realSumZero : Option Bool) (p : PS)
    (r : Option Bool) (h : p.1 = some r) :
    postLoopPS n realSumZero p = r := by
  unfold postLoopPS
  rw [h]

/-- Per-constructor lockstep between the elaborated body and `stepState`: an
accumulating constructor (`stepState = some s'`) yields a slot-`none` state
whose projection is `s'`; an unclassifiable constructor (`stepState = none`)
emits `done` with the slot set to `some none`. -/
theorem toLS_step_agree (a : Summand) (p : PS) :
    (∀ s', stepState (toLS p) a = some s' →
        forInBodyPS a p = ForInStep.yield ⟨none, s'.im, s'.imOrZ, s'.nz, s'.z⟩) ∧
    (stepState (toLS p) a = none →
        forInBodyPS a p
          = ForInStep.done ⟨some none, p.2.1, p.2.2.1, p.2.2.2.1, p.2.2.2.2⟩) := by
  constructor
  · intro s' h
    cases a <;>
      simp only [stepState, toLS, forInBodyPS, Option.some.injEq, reduceCtorEq] at h ⊢ <;>
      subst h <;>
      rfl
  · intro h
    cases a <;>
      simp_all [stepState, toLS, forInBodyPS]

/-- The semantic core: for every suffix `l` and every packed state `p` whose
early-return slot is empty, the full computation equals the pure model
`loopRec` on the projected state. Proved by induction on `l` generalizing `p`,
casing on the head constructor so the elaborated body reduces in lockstep with
`stepState` (via `toLS_step_agree`); the slot-none invariant is preserved by
the accumulating `yield`s. -/
theorem loop_eq_loopRec_general (n : Nat) (realSumZero : Option Bool)
    (l : List Summand) (p : PS) (h : p.1 = none) :
    runFrom n realSumZero l p = loopRec n realSumZero l (toLS p) := by
  induction l generalizing p with
  | nil =>
    rw [runFrom_nil, postLoop_slot_none n realSumZero p h]
    rfl
  | cons a l' ih =>
    rw [runFrom_cons]
    have hstep := toLS_step_agree a p
    cases hs : stepState (toLS p) a with
    | none =>
      have hbody := hstep.2 hs
      rw [hbody]
      simp only []
      rw [postLoop_slot_some n realSumZero _ none rfl]
      simp only [loopRec, hs]
    | some s' =>
      have hbody := hstep.1 s' hs
      rw [hbody]
      simp only []
      have hp1 : (⟨none, s'.im, s'.imOrZ, s'.nz, s'.z⟩ : PS).1 = none := rfl
      rw [ih _ hp1]
      have htols : toLS (⟨none, s'.im, s'.imOrZ, s'.nz, s'.z⟩ : PS) = s' := by
        cases s'; rfl
      rw [htols]
      simp only [loopRec, hs]

/-- Expose the impl's outer `Id.run` as `runFrom` started from the real initial
packed state (slot empty, all counters/flags zero). -/
theorem impl_eq_runFrom_init (terms : List Summand) (realSumZero : Option Bool) :
    implementation_zeroStatus terms realSumZero
      = runFrom terms.length realSumZero terms ⟨none, false, false, 0, 0⟩ := by
  simp only [implementation_zeroStatus, runFrom, postLoopPS, forInBodyPS, pure_bind]
  congr 1
  congr 1
  funext r
  rcases hr : r.fst with _ | _ <;> rfl

/-- Reify the imperative `for` loop (with early `return none`) as the pure
recursion `loopRec`, started from the zero state. -/
theorem forIn_unfold (terms : List Summand) (realSumZero : Option Bool) :
    implementation_zeroStatus terms realSumZero
      = loopRec terms.length realSumZero terms ⟨0, 0, false, false⟩ := by
  rw [impl_eq_runFrom_init,
      loop_eq_loopRec_general terms.length realSumZero terms ⟨none, false, false, 0, 0⟩ rfl]
  rfl

/-- The loop returns `none` whenever some term is unclassifiable, matching the
outer guard of `zeroVerdict`. -/
theorem shortcircuit_iff (terms : List Summand) (realSumZero : Option Bool)
    (h : terms.any isUnclassified = true) :
    implementation_zeroStatus terms realSumZero = none := by
  rw [forIn_unfold]
  suffices H : ∀ (l : List Summand) (s : LoopState),
      l.any isUnclassified = true →
      loopRec terms.length realSumZero l s = none by
    exact H terms _ h
  intro l
  induction l with
  | nil => intro s hl; simp [List.any_nil] at hl
  | cons a l ih =>
    intro s hl
    rw [List.any_cons] at hl
    cases a <;>
      simp only [isUnclassified, Bool.false_or, Bool.true_or, loopRec, stepState] at hl ⊢ <;>
      first
        | rfl
        | exact ih _ hl

/-- When no term is unclassifiable, running the loop from the zero state drives
the four counters/flags to exactly the four `zeroVerdict` aggregates, and reaches
the post-loop decision with those values. -/
theorem final_state_aggregates (terms : List Summand) (realSumZero : Option Bool)
    (h : terms.any isUnclassified = false) :
    loopRec terms.length realSumZero terms ⟨0, 0, false, false⟩
      = postDecide ⟨terms.countP isRealZero, terms.countP isRealNonzero,
          terms.any isImag, terms.any isImagOrZero⟩ terms.length realSumZero := by
  suffices key : ∀ (l : List Summand) (s : LoopState),
      l.any isUnclassified = false →
      loopRec terms.length realSumZero l s
        = postDecide ⟨s.z + l.countP isRealZero, s.nz + l.countP isRealNonzero,
            s.im || l.any isImag, s.imOrZ || l.any isImagOrZero⟩ terms.length realSumZero by
    have := key terms ⟨0, 0, false, false⟩ h
    simpa using this
  intro l
  induction l with
  | nil => intro s _; simp [loopRec]
  | cons a t ih =>
    intro s hany
    cases a <;>
      simp only [loopRec, stepState, isUnclassified, isRealZero, isRealNonzero,
        isImag, isImagOrZero, List.countP_cons, List.any_cons, Bool.or_eq_false_iff,
        Bool.false_eq_true, false_and, true_and, cond_true, cond_false] at hany ⊢
    case realUnknown => exact absurd hany.1 (by decide)
    case indeterminate => exact absurd hany.1 (by decide)
    all_goals
      (rw [ih _ hany]; congr 1 <;> simp [Bool.or_assoc, Nat.add_comm, Nat.add_left_comm,
        Nat.add_assoc, Nat.add_right_comm])

/-- In the classified case, the post-loop decision applied to the aggregates
equals the `else`-branch of `zeroVerdict` (the two cascades are identical). -/
theorem decision_cascade_agree (terms : List Summand) (realSumZero : Option Bool)
    (h : terms.any isUnclassified = false) :
    postDecide ⟨terms.countP isRealZero, terms.countP isRealNonzero,
        terms.any isImag, terms.any isImagOrZero⟩ terms.length realSumZero
      = zeroVerdict terms realSumZero := by
  simp only [zeroVerdict, h, Bool.false_eq_true, if_false, postDecide]

theorem correct_zeroStatus :
    ∀ (terms : List Summand) (realSumZero : Option Bool),
      problem_spec_zeroStatus terms realSumZero
        (implementation_zeroStatus terms realSumZero) := by
  intro terms realSumZero
  unfold problem_spec_zeroStatus
  by_cases h : terms.any isUnclassified = true
  · rw [shortcircuit_iff terms realSumZero h]
    simp only [zeroVerdict, h, if_true]
  · have h' : terms.any isUnclassified = false := by
      simpa using h
    rw [forIn_unfold terms realSumZero,
        final_state_aggregates terms realSumZero h',
        decision_cascade_agree terms realSumZero h']

-- proof-end
