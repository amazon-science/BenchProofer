# P2 adversarial audit — django__django-11728

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
The spec problem_spec_findGroupEnd is a COMPLETE functional characterization: for `some i` it pins i to be the first (minimal) index whose (i+1)-length prefix brings depthAfter to 0, and requires i < cs.length; for `none` it requires no prefix ever reaches depth 0. This uniquely determines the output for every input, so any semantically-wrong impl violates the postcondition on a concrete input and CANNOT be proved. Confirmed differ-inputs: atk_1 (prepatch top-of-loop check) & atk_8 (depth init 0) & atk_6 (inverted +/-) & atk_2 (always none) all return None on input ")" where true=0; atk_3 (idx+1) returns 1 on ")" where true=0; atk_4 (ignore escaping) returns 1 on "\)" where true=None; atk_5 (echo some 0) returns 0 on "" where true=None; atk_7 (last crossing) returns 1 on ")x" where true=0.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -80,15 +80,13 @@
   let mut prev : Option Char := none
   let mut idx : Nat := 0
   for val in cs do
-    -- Check for unescaped `(` and `)`; they open and close nested parentheses.
+    if depth == 0 then
+      return some idx
     if val == '(' && prev != some '\\' then
       depth := depth + 1
     else if val == ')' && prev != some '\\' then
       depth := depth - 1
     prev := some val
-    -- When the depth is back to zero, the current position closes the group.
-    if depth == 0 then
-      return some idx
     idx := idx + 1
   return none
 -- impl-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -75,22 +75,7 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_findGroupEnd (cs : List Char) : Option Nat := Id.run do
-  let mut depth : Int := 1
-  let mut prev : Option Char := none
-  let mut idx : Nat := 0
-  for val in cs do
-    -- Check for unescaped `(` and `)`; they open and close nested parentheses.
-    if val == '(' && prev != some '\\' then
-      depth := depth + 1
-    else if val == ')' && prev != some '\\' then
-      depth := depth - 1
-    prev := some val
-    -- When the depth is back to zero, the current position closes the group.
-    if depth == 0 then
-      return some idx
-    idx := idx + 1
-  return none
+def implementation_findGroupEnd (cs : List Char) : Option Nat := none
 -- impl-end
 
 
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -80,15 +80,13 @@
   let mut prev : Option Char := none
   let mut idx : Nat := 0
   for val in cs do
-    -- Check for unescaped `(` and `)`; they open and close nested parentheses.
     if val == '(' && prev != some '\\' then
       depth := depth + 1
     else if val == ')' && prev != some '\\' then
       depth := depth - 1
     prev := some val
-    -- When the depth is back to zero, the current position closes the group.
     if depth == 0 then
-      return some idx
+      return some (idx + 1)
     idx := idx + 1
   return none
 -- impl-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -77,16 +77,12 @@
 -- impl-start
 def implementation_findGroupEnd (cs : List Char) : Option Nat := Id.run do
   let mut depth : Int := 1
-  let mut prev : Option Char := none
   let mut idx : Nat := 0
   for val in cs do
-    -- Check for unescaped `(` and `)`; they open and close nested parentheses.
-    if val == '(' && prev != some '\\' then
+    if val == '(' then
       depth := depth + 1
-    else if val == ')' && prev != some '\\' then
+    else if val == ')' then
       depth := depth - 1
-    prev := some val
-    -- When the depth is back to zero, the current position closes the group.
     if depth == 0 then
       return some idx
     idx := idx + 1
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -75,22 +75,7 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_findGroupEnd (cs : List Char) : Option Nat := Id.run do
-  let mut depth : Int := 1
-  let mut prev : Option Char := none
-  let mut idx : Nat := 0
-  for val in cs do
-    -- Check for unescaped `(` and `)`; they open and close nested parentheses.
-    if val == '(' && prev != some '\\' then
-      depth := depth + 1
-    else if val == ')' && prev != some '\\' then
-      depth := depth - 1
-    prev := some val
-    -- When the depth is back to zero, the current position closes the group.
-    if depth == 0 then
-      return some idx
-    idx := idx + 1
-  return none
+def implementation_findGroupEnd (cs : List Char) : Option Nat := some 0
 -- impl-end
 
 
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -80,13 +80,11 @@
   let mut prev : Option Char := none
   let mut idx : Nat := 0
   for val in cs do
-    -- Check for unescaped `(` and `)`; they open and close nested parentheses.
     if val == '(' && prev != some '\\' then
+      depth := depth - 1
+    else if val == ')' && prev != some '\\' then
       depth := depth + 1
-    else if val == ')' && prev != some '\\' then
-      depth := depth - 1
     prev := some val
-    -- When the depth is back to zero, the current position closes the group.
     if depth == 0 then
       return some idx
     idx := idx + 1
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -79,18 +79,17 @@
   let mut depth : Int := 1
   let mut prev : Option Char := none
   let mut idx : Nat := 0
+  let mut res : Option Nat := none
   for val in cs do
-    -- Check for unescaped `(` and `)`; they open and close nested parentheses.
     if val == '(' && prev != some '\\' then
       depth := depth + 1
     else if val == ')' && prev != some '\\' then
       depth := depth - 1
     prev := some val
-    -- When the depth is back to zero, the current position closes the group.
     if depth == 0 then
-      return some idx
+      res := some idx
     idx := idx + 1
-  return none
+  return res
 -- impl-end
 
 
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -76,17 +76,15 @@
 
 -- impl-start
 def implementation_findGroupEnd (cs : List Char) : Option Nat := Id.run do
-  let mut depth : Int := 1
+  let mut depth : Int := 0
   let mut prev : Option Char := none
   let mut idx : Nat := 0
   for val in cs do
-    -- Check for unescaped `(` and `)`; they open and close nested parentheses.
     if val == '(' && prev != some '\\' then
       depth := depth + 1
     else if val == ')' && prev != some '\\' then
       depth := depth - 1
     prev := some val
-    -- When the depth is back to zero, the current position closes the group.
     if depth == 0 then
       return some idx
     idx := idx + 1
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
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
```

Prepatch bug re-encoded as an attack: `True`.

Cmd per attack: `bash scripts/lean_verify.sh <path>`. same_spec(gold, atk_N)=True for all 8 attacks and pos (verified via swebench_unified.markers.same_spec with lean backend). RESULTS: pos.lean exit=0 (verifies, no sorry); `#print axioms correct_findGroupEnd` => [propext, Classical.choice, Quot.sound] only (clean). ALL 8 attacks exit=1 (error, proof does NOT close): each dies at specialize_initial's `rfl` — impl no longer definitionally equals `loopFrom cs 1 none 0`. Independently, a Python re-encoding of the true spec function vs each attack model over ~350 exhaustive small inputs {(,),x,\} confirms every attack is genuinely semantically wrong (counterexamples above), so NO proof could close any of them regardless of tactic.

Because no wrong impl has a closing clean-axiom proof, there is no materialized-patch resolve step to run for falsification (none required — nothing verified). Attack taxonomy covered: partial-domain/control-flow-effect (atk_1 prepatch top-check = THE actual bug, atk_8 wrong init, atk_6 inverted update), boundary/off-by-one (atk_3 idx+1, atk_7 last-vs-first crossing), ungrounded-oracle echo (atk_2 always-none, atk_5 always some 0), escaping-rule drop (atk_4). REFINEMENT AUDIT: all 9 legs in refinement.md are R or I (no A-consumed, no A-reference, no kind-3). Structurally confirmed: no `axiom`/`opaque` declarations in Solution.lean; meta.axioms=[], deep_model_references=[], conf_skip=false, patch_equals_gold=true; axiom_check.py is a legitimate skip stub.

Model↔patch correspondence holds: op #7 (depth-zero test AFTER the per-char update, recording end+idx+1/start+2+idx) is the behaviour-changing op; the prepatch top-of-loop control flow (atk_1) is provably spec-violating (misses trailing-character close), matching the reported bug and the F2P discriminator. Spec discriminates the real fix. Verdict SOUND: >=8 distinct same-spec wrong impls attacked, positive control verifies with clean axioms, none broke the spec.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
The spec problem_spec_findGroupEnd is a COMPLETE functional characterization: for `some i` it pins i to be the first (minimal) index whose (i+1)-length prefix brings depthAfter to 0, and requires i < cs.length; for `none` it requires no prefix ever reaches depth 0. This uniquely determines the output for every input, so any semantically-wrong impl violates the postcondition on a concrete input and CANNOT be proved. Confirmed differ-inputs: atk_1 (prepatch top-of-loop check) & atk_8 (depth init 0) & atk_6 (inverted +/-) & atk_2 (always none) all return None on input ")" where true=0; atk_3 (idx+1) returns 1 on ")" where true=0; atk_4 (ignore escaping) returns 1 on "\)" where true=None; atk_5 (echo some 0) returns 0 on "" where true=None; atk_7 (last crossing) returns 1 on ")x" where true=0.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
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
```

Prepatch bug re-encoded as an attack: `True`.

Cmd per attack: `bash scripts/lean_verify.sh <path>`. same_spec(gold, atk_N)=True for all 8 attacks and pos (verified via swebench_unified.markers.same_spec with lean backend). RESULTS: pos.lean exit=0 (verifies, no sorry); `#print axioms correct_findGroupEnd` => [propext, Classical.choice, Quot.sound] only (clean). ALL 8 attacks exit=1 (error, proof does NOT close): each dies at specialize_initial's `rfl` — impl no longer definitionally equals `loopFrom cs 1 none 0`. Independently, a Python re-encoding of the true spec function vs each attack model over ~350 exhaustive small inputs {(,),x,\} confirms every attack is genuinely semantically wrong (counterexamples above), so NO proof could close any of them regardless of tactic.

Because no wrong impl has a closing clean-axiom proof, there is no materialized-patch resolve step to run for falsification (none required — nothing verified). Attack taxonomy covered: partial-domain/control-flow-effect (atk_1 prepatch top-check = THE actual bug, atk_8 wrong init, atk_6 inverted update), boundary/off-by-one (atk_3 idx+1, atk_7 last-vs-first crossing), ungrounded-oracle echo (atk_2 always-none, atk_5 always some 0), escaping-rule drop (atk_4). REFINEMENT AUDIT: all 9 legs in refinement.md are R or I (no A-consumed, no A-reference, no kind-3). Structurally confirmed: no `axiom`/`opaque` declarations in Solution.lean; meta.axioms=[], deep_model_references=[], conf_skip=false, patch_equals_gold=true; axiom_check.py is a legitimate skip stub.

Model↔patch correspondence holds: op #7 (depth-zero test AFTER the per-char update, recording end+idx+1/start+2+idx) is the behaviour-changing op; the prepatch top-of-loop control flow (atk_1) is provably spec-violating (misses trailing-character close), matching the reported bug and the F2P discriminator. Spec discriminates the real fix. Verdict SOUND: >=8 distinct same-spec wrong impls attacked, positive control verifies with clean axioms, none broke the spec.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack: no divergence found; spec matches the real post-patch callee. Verification performed: (1) Solution.lean compiles via lean_verify.sh (exit 0); (2) #print axioms correct_findGroupEnd => [propext, Classical.choice, Quot.sound] only, no sorryAx (proof is genuine, not fake); (3) same_spec(Solution, Solution_prepatch) = True under LeanBackend.language tables — spec region is byte-identical, the fix is impl-only. FAITHFULNESS CHECK against real repo: I independently modeled the SPEC semantics (depthAfter starting at depth 1; result = first index i where depthAfter(cs[:i+1])==0, else none) — NOT reusing the bundle's impl shadow — then rebuilt both whole real functions replace_named_groups/replace_unnamed_groups using only that spec scan (plus the unchanged group-start regexes and the constant index shifts end+i+1 / start+2+i documented in mapping.md), and diffed the final output string against the REAL post-patch django functions (django 4.1.dev, gold patch present). Result: 0 mismatches over 200,000 general fuzzed patterns AND 300,000 escape/backslash/nesting-heavy adversarial patterns, plus the exact F2P patterns from tests/admin_docs/test_views.py::test_simplify_regex. Cases covered: trailing group closing at final char (the reported bug), trailing text after close, nested parens ((x|y)\w+), escaped parens \( \), literal backslashes, and never-closing fragments (depth never returns to 0 => none). The spec is neither too weak (G-DIFF confirms the buggy prepatch impl fails it) nor too strong (matches the patched callee exactly on every input tested). The Lean offset->real-index bridge is a fixed constant shift correctly applied by G-CONF. No input on which the modeled findGroupEnd disagrees with the real replace_named_groups/replace_unnamed_groups scan.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (no diff markers, no reproduced gold-patch line, no patched file/module path django/contrib/admindocs/utils.py, spec-view identifiers findGroupEnd/stepBracket/depthAfter/cs do not embed patched repo symbols replace_named_groups/replace_unnamed_groups/unmatched_open_brackets, no narration keywords). Spec view exposes only the abstract postcondition + pure helpers; impl and proof regions are elided. same_spec(Solution, Solution_prepatch)=True, so the discriminator is not encoded in the spec text. The docstring's 'closed at that final character, not left unclosed' clause specifies CORRECT behavior — which the public problem_statement already discloses ('doesn't replace trailing groups', 'fails to replace the final named group if the urlpattern is missing a trailing /'). It does not reveal the gold edit's mechanics (relocating the depth==0 check below the depth update; index bump end+idx -> end+idx+1) beyond the public statement. No leakage beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
