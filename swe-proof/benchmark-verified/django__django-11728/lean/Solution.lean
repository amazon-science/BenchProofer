import Mathlib
-- imports-end

/-!
Locating where an open parenthesis is closed inside a pattern fragment.

A fragment is a sequence of characters that begins just after a parenthesis has
already been opened. Scanning the fragment from left to right, the goal is to
find the position of the character that finally closes that initially-open
parenthesis, honouring two rules:

  * nesting — every additional unescaped `(` opens a further parenthesis that
    must be closed before the original one, and every unescaped `)` closes the
    innermost currently-open parenthesis;
  * escaping — a `(` or `)` whose immediately preceding character is a backslash
    is literal text and does NOT affect the nesting depth.

The closing position is the FIRST index at which the running nesting depth
returns to zero. It is reported wherever it occurs in the fragment, including as
the very last character (a fragment that ends exactly at its closing parenthesis
is closed at that final character, not left unclosed). If the depth never returns
to zero, the parenthesis is never closed and no position is reported.

The behaviour is stated abstractly as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged outside callee is consumed as an axiom. The fragment that is
-- scanned, and the rule for which characters count as structural parentheses,
-- are spelled out directly over the input character sequence; there is no opaque
-- callee whose property the proof must assume.
-- axioms-end

-- pure-start
/-- One scanning step over a character `c`, given the running open-parenthesis
depth `st.1` and the preceding character `st.2`. An unescaped `(` (one whose
preceding character is not a backslash) increases the depth; an unescaped `)`
decreases it; every other character — and any parenthesis escaped by a preceding
backslash — leaves the depth unchanged. The step records `c` as the new preceding
character. -/
def stepBracket (st : Int × Option Char) (c : Char) : Int × Option Char :=
  let d := st.1
  let prev := st.2
  if c == '(' && prev != some '\\' then (d + 1, some c)
  else if c == ')' && prev != some '\\' then (d - 1, some c)
  else (d, some c)

/-- The open-parenthesis depth remaining after scanning the prefix `p`, starting
from a single already-open parenthesis (depth `1`) and no previous character. -/
def depthAfter (p : List Char) : Int :=
  (p.foldl stepBracket (1, none)).1
-- pure-end

-- post-conditions-start
/-- `result` reports the position that closes the initially-open parenthesis.

  * `some i` means scanning the first `i + 1` characters brings the depth to `0`
    (the parenthesis is closed exactly at index `i`), `i` is a real index of the
    fragment, and no shorter prefix closes it (the depth stays non-zero for every
    strictly shorter prefix). The closing character may be the very last one.
  * `none` means the parenthesis is never closed: no prefix of the fragment
    brings the depth to `0`.

No output component is left free: for every fragment the reported value is fully
determined by the running depth over the fragment's own characters. -/
def problem_spec_findGroupEnd (cs : List Char) (result : Option Nat) : Prop :=
  match result with
  | some i =>
      i < cs.length ∧
      depthAfter (cs.take (i + 1)) = 0 ∧
      (∀ j, j < i → depthAfter (cs.take (j + 1)) ≠ 0)
  | none =>
      ∀ i, i < cs.length → depthAfter (cs.take (i + 1)) ≠ 0
-- post-conditions-end

-- impl-start
def implementation_findGroupEnd (cs : List Char) : Option Nat := Id.run do
  let mut depth : Int := 1
  let mut prev : Option Char := none
  let mut idx : Nat := 0
  for val in cs do
    -- Check for unescaped `(` and `)`; they open and close nested parentheses.
    if val == '(' && prev != some '\\' then
      depth := depth + 1
    else if val == ')' && prev != some '\\' then
      depth := depth - 1
    prev := some val
    -- When the depth is back to zero, the current position closes the group.
    if depth == 0 then
      return some idx
    idx := idx + 1
  return none
-- impl-end


-- proof-start
/-- The mutable loop state threaded by the `for` loop: running depth, previous
character, and current index. -/
def LoopState : Type := Int × Option Char × Nat

/-- The running open-parenthesis depth after scanning prefix `p`, starting from
an arbitrary depth `d0` and previous character `prev0`.  Generalizes
`depthAfter` (which fixes `d0 = 1`, `prev0 = none`). -/
def runDepth (d0 : Int) (prev0 : Option Char) (p : List Char) : Int :=
  (p.foldl stepBracket (d0, prev0)).1

/-- The generalized scanning loop: exactly `implementation_findGroupEnd`'s body
but started from an arbitrary state `(d0, prev0, idx0)` instead of `(1, none, 0)`.
This is what makes the loop characterization statable over the tail's non-initial
start state. -/
def loopFrom (cs : List Char) (d0 : Int) (prev0 : Option Char) (idx0 : Nat) :
    Option Nat := Id.run do
  let mut depth : Int := d0
  let mut prev : Option Char := prev0
  let mut idx : Nat := idx0
  for val in cs do
    if val == '(' && prev != some '\\' then
      depth := depth + 1
    else if val == ')' && prev != some '\\' then
      depth := depth - 1
    prev := some val
    if depth == 0 then
      return some idx
    idx := idx + 1
  return none

/-- One iteration of the loop body's depth/prev update coincides with
`stepBracket`. -/
theorem loopStep_eq_stepBracket (depth : Int) (prev : Option Char) (val : Char) :
    (if val == '(' && prev != some '\\' then (depth + 1, some val)
     else if val == ')' && prev != some '\\' then (depth - 1, some val)
     else (depth, some val)) = stepBracket (depth, prev) val := by
  unfold stepBracket
  simp only

/-- The bridge identity between the spec's `depthAfter` and the generalized
`runDepth`: `depthAfter` is `runDepth` from the initial state `(1, none)`. -/
theorem runDepth_def (p : List Char) :
    depthAfter p = runDepth 1 none p := rfl

/-- Running depth over a scanned prefix splits off the head: after applying
`stepBracket` to the first character, the running depth over the remaining
prefix continues from the new state.  This lets `runDepth` over prefixes of
`c :: rest` be re-expressed as `runDepth` from the next state over prefixes of
`rest`. -/
theorem depth_bridge (d0 : Int) (prev0 : Option Char) (c : Char)
    (rest : List Char) (j : Nat) :
    runDepth d0 prev0 ((c :: rest).take (j + 1)) =
      runDepth (stepBracket (d0, prev0) c).1 (stepBracket (d0, prev0) c).2
        (rest.take j) := by
  simp only [runDepth, List.take_succ_cons, List.foldl_cons]

/-- Expose one iteration of the early-return loop on a nonempty list. -/
theorem forIn_unfold_step (c : Char) (rest : List Char) (d0 : Int)
    (prev0 : Option Char) (idx0 : Nat) :
    loopFrom (c :: rest) d0 prev0 idx0 =
      (let st := stepBracket (d0, prev0) c
       if st.1 = 0 then some idx0
       else loopFrom rest st.1 st.2 (idx0 + 1)) := by
  simp only [loopFrom, List.forIn_cons, stepBracket]
  split <;> simp only [beq_iff_eq] <;> split <;> first | rfl | (split <;> rfl)

/-- Complete characterization of the generalized loop's returned `Option Nat`
from an arbitrary start state, in terms of the first-zero offset over `runDepth`
prefixes.  Proved by induction on `cs` generalized over the start state. -/
theorem loop_characterization (cs : List Char) (d0 : Int) (prev0 : Option Char)
    (idx0 : Nat) :
    (∀ m, loopFrom cs d0 prev0 idx0 = some m ↔
        ∃ j, m = idx0 + j ∧ j < cs.length ∧
          runDepth d0 prev0 (cs.take (j + 1)) = 0 ∧
          (∀ k, k < j → runDepth d0 prev0 (cs.take (k + 1)) ≠ 0)) ∧
    (loopFrom cs d0 prev0 idx0 = none ↔
        ∀ j, j < cs.length → runDepth d0 prev0 (cs.take (j + 1)) ≠ 0) := by
  induction cs generalizing d0 prev0 idx0 with
  | nil =>
    refine ⟨?_, ?_⟩
    · intro m; simp [loopFrom]
    · simp [loopFrom]
  | cons c rest ih =>
    rw [forIn_unfold_step]
    have bridge : ∀ j, runDepth d0 prev0 ((c :: rest).take (j + 1))
        = runDepth (stepBracket (d0, prev0) c).1 (stepBracket (d0, prev0) c).2 (rest.take j) :=
      fun j => depth_bridge d0 prev0 c rest j
    have hstep0 : runDepth d0 prev0 ((c :: rest).take (0 + 1)) = (stepBracket (d0, prev0) c).1 := by
      rw [bridge 0]; rfl
    by_cases hz : (stepBracket (d0, prev0) c).1 = 0
    · simp only [hz, ↓reduceIte]
      refine ⟨?_, ?_⟩
      · intro m
        constructor
        · intro h
          injection h with h'
          refine ⟨0, by omega, by simp, ?_, ?_⟩
          · rw [hstep0]; exact hz
          · intro k hk; omega
        · rintro ⟨j, hm, hjlen, hjz, hjmin⟩
          have hj0 : j = 0 := by
            by_contra hne
            have h0j : 0 < j := Nat.pos_of_ne_zero hne
            have hcontra := hjmin 0 h0j
            rw [hstep0] at hcontra
            exact hcontra hz
          subst hj0
          simp only [Nat.add_zero] at hm
          rw [hm]
      · constructor
        · intro h; exact absurd h (by simp)
        · intro h; exfalso
          have hc := h 0 (by simp)
          rw [hstep0] at hc
          exact hc hz
    · simp only [hz, ↓reduceIte]
      obtain ⟨ihA, ihB⟩ := ih (stepBracket (d0, prev0) c).1 (stepBracket (d0, prev0) c).2 (idx0 + 1)
      refine ⟨?_, ?_⟩
      · intro m
        rw [ihA m]
        constructor
        · rintro ⟨j', hm, hjlen, hjz, hjmin⟩
          refine ⟨j' + 1, by omega, by simp only [List.length_cons]; omega, ?_, ?_⟩
          · rw [bridge (j' + 1)]; exact hjz
          · intro k hk
            rcases k with _ | k'
            · rw [hstep0]; exact hz
            · rw [bridge (k' + 1)]; exact hjmin k' (by omega)
        · rintro ⟨j, hm, hjlen, hjz, hjmin⟩
          have hjpos : j ≠ 0 := by
            rintro rfl
            rw [hstep0] at hjz
            exact hz hjz
          obtain ⟨j', rfl⟩ : ∃ j', j = j' + 1 := ⟨j - 1, by omega⟩
          refine ⟨j', by omega, by simp only [List.length_cons] at hjlen; omega, ?_, ?_⟩
          · rw [← bridge (j' + 1)]; exact hjz
          · intro k' hk'
            rw [← bridge (k' + 1)]; exact hjmin (k' + 1) (by omega)
      · rw [ihB]
        constructor
        · intro hyp j hj
          rcases j with _ | j'
          · rw [hstep0]; exact hz
          · rw [bridge (j' + 1)]
            exact hyp j' (by simp only [List.length_cons] at hj; omega)
        · intro hyp j' hj'
          rw [← bridge (j' + 1)]
          exact hyp (j' + 1) (by simp only [List.length_cons]; omega)

/-- The actual implementation is the generalized loop started at `(1, none, 0)`. -/
theorem specialize_initial (cs : List Char) :
    implementation_findGroupEnd cs = loopFrom cs 1 none 0 := rfl

/-- The three `some`-branch postcondition atoms, read off the specialized
characterization. -/
theorem some_branch_atoms (cs : List Char) (i : Nat)
    (h : implementation_findGroupEnd cs = some i) :
    i < cs.length ∧
    depthAfter (cs.take (i + 1)) = 0 ∧
    (∀ j, j < i → depthAfter (cs.take (j + 1)) ≠ 0) := by
  rw [specialize_initial] at h
  obtain ⟨j, hij, hjlt, hzero, hlt⟩ := ((loop_characterization cs 1 none 0).1 i).mp h
  subst hij
  simp only [Nat.zero_add] at *
  refine ⟨hjlt, ?_, ?_⟩
  · rw [runDepth_def]; exact hzero
  · intro k hk; rw [runDepth_def]; exact hlt k hk

/-- The single `none`-branch postcondition atom. -/
theorem none_branch_atom (cs : List Char)
    (h : implementation_findGroupEnd cs = none) :
    ∀ i, i < cs.length → depthAfter (cs.take (i + 1)) ≠ 0 := by
  intro i hi
  rw [runDepth_def]
  have hloop : loopFrom cs 1 none 0 = none := by
    rw [← specialize_initial]; exact h
  exact ((loop_characterization cs 1 none 0).2.mp hloop) i hi

theorem correct_findGroupEnd :
    ∀ (cs : List Char),
      problem_spec_findGroupEnd cs (implementation_findGroupEnd cs) := by
  intro cs
  unfold problem_spec_findGroupEnd
  cases h : implementation_findGroupEnd cs with
  | some i => exact some_branch_atoms cs i h
  | none => exact none_branch_atom cs h

-- proof-end
