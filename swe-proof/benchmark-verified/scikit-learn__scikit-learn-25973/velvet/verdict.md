# P2 adversarial audit — scikit-learn__scikit-learn-25973

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 4 | `atk2_readonce.lean`, `atk5_nomat.lean`, `atk6_offbyone.lean`, `atk7_partial.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk1_echo.lean`, `atk3_forward.lean`, `atk4_matecho.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. No same-spec, Velvet-verifying wrong impl exists whose faithful refined patch fails to resolve. The postcondition `obs = List.replicate k source.splits` is a TOTAL FUNCTIONAL spec: the output is uniquely determined by the inputs and universally quantified over ALL `source` values, including the demonic single-pass case (reusable=false, consumed=false). Any impl that verifies must therefore denote 'every one of the k rounds observes the full split sequence regardless of single-pass exhaustion' — which is exactly the behavior the gold buffering fix (check_cv before the loop) provides. Every verifying attack's faithful refined patch is behaviorally the gold patch, which resolves.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk1_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -81,22 +81,7 @@
   ensures obs = List.replicate k source.splits
   do
     -- impl-start
-    let mut src := materialize source
-    let mut obs : List Splits := []
-    let mut i := k
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ k
-      invariant src.reusable = true
-      invariant src.splits = source.splits
-      invariant obs = List.replicate (k - i) source.splits
-      done_with i = 0
-      decreasing i
-    do
-      let o := readObs src
-      src := advance src
-      obs := o :: obs
-      i := i - 1
-    return obs
+    return List.replicate k source.splits
     -- impl-end
 
 /- The backward-fold step: with one fewer round remaining, the running record
@@ -110,6 +95,3 @@
 
 prove_correct runScoringRounds by
   loom_solve
-  rw [readObs_reusable src (by assumption)]
-  rw [replicate_step source.splits k i (by omega) (by omega)]
-  simp_all
```

Attack 2 — `atk3_forward.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -81,21 +81,17 @@
   ensures obs = List.replicate k source.splits
   do
     -- impl-start
-    let mut src := materialize source
+    let src := materialize source
     let mut obs : List Splits := []
-    let mut i := k
-    while i > 0
+    let mut i := 0
+    while i < k
       invariant 0 ≤ i ∧ i ≤ k
-      invariant src.reusable = true
-      invariant src.splits = source.splits
-      invariant obs = List.replicate (k - i) source.splits
-      done_with i = 0
-      decreasing i
+      invariant obs = List.replicate i source.splits
+      done_with i = k
+      decreasing k - i
     do
-      let o := readObs src
-      src := advance src
-      obs := o :: obs
-      i := i - 1
+      obs := obs ++ [readObs src]
+      i := i + 1
     return obs
     -- impl-end
 
@@ -109,7 +105,6 @@
   rw [h, List.replicate_succ]
 
 prove_correct runScoringRounds by
-  loom_solve
-  rw [readObs_reusable src (by assumption)]
-  rw [replicate_step source.splits k i (by omega) (by omega)]
-  simp_all
+  loom_solve <;>
+    simp_all [readObs, materialize, List.replicate_succ'] <;>
+    omega
```

Attack 3 — `atk4_matecho.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -81,22 +81,8 @@
   ensures obs = List.replicate k source.splits
   do
     -- impl-start
-    let mut src := materialize source
-    let mut obs : List Splits := []
-    let mut i := k
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ k
-      invariant src.reusable = true
-      invariant src.splits = source.splits
-      invariant obs = List.replicate (k - i) source.splits
-      done_with i = 0
-      decreasing i
-    do
-      let o := readObs src
-      src := advance src
-      obs := o :: obs
-      i := i - 1
-    return obs
+    let _src := materialize source
+    return List.replicate k source.splits
     -- impl-end
 
 /- The backward-fold step: with one fewer round remaining, the running record
@@ -110,6 +96,3 @@
 
 prove_correct runScoringRounds by
   loom_solve
-  rw [readObs_reusable src (by assumption)]
-  rw [replicate_step source.splits k i (by omega) (by omega)]
-  simp_all
```

Attack 4 — `atk2_readonce.lean` → rejected (same spec, does not verify — good)

```diff
@@ -81,22 +81,8 @@
   ensures obs = List.replicate k source.splits
   do
     -- impl-start
-    let mut src := materialize source
-    let mut obs : List Splits := []
-    let mut i := k
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ k
-      invariant src.reusable = true
-      invariant src.splits = source.splits
-      invariant obs = List.replicate (k - i) source.splits
-      done_with i = 0
-      decreasing i
-    do
-      let o := readObs src
-      src := advance src
-      obs := o :: obs
-      i := i - 1
-    return obs
+    let o := readObs source
+    return List.replicate k o
     -- impl-end
 
 /- The backward-fold step: with one fewer round remaining, the running record
@@ -110,6 +96,3 @@
 
 prove_correct runScoringRounds by
   loom_solve
-  rw [readObs_reusable src (by assumption)]
-  rw [replicate_step source.splits k i (by omega) (by omega)]
-  simp_all
```

Attack 5 — `atk5_nomat.lean` → rejected (same spec, does not verify — good)

```diff
@@ -81,14 +81,12 @@
   ensures obs = List.replicate k source.splits
   do
     -- impl-start
-    let mut src := materialize source
+    let mut src := source
     let mut obs : List Splits := []
     let mut i := k
     while i > 0
       invariant 0 ≤ i ∧ i ≤ k
-      invariant src.reusable = true
       invariant src.splits = source.splits
-      invariant obs = List.replicate (k - i) source.splits
       done_with i = 0
       decreasing i
     do
@@ -110,6 +108,3 @@
 
 prove_correct runScoringRounds by
   loom_solve
-  rw [readObs_reusable src (by assumption)]
-  rw [replicate_step source.splits k i (by omega) (by omega)]
-  simp_all
```

Attack 6 — `atk6_offbyone.lean` → rejected (same spec, does not verify — good)

```diff
@@ -81,22 +81,7 @@
   ensures obs = List.replicate k source.splits
   do
     -- impl-start
-    let mut src := materialize source
-    let mut obs : List Splits := []
-    let mut i := k
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ k
-      invariant src.reusable = true
-      invariant src.splits = source.splits
-      invariant obs = List.replicate (k - i) source.splits
-      done_with i = 0
-      decreasing i
-    do
-      let o := readObs src
-      src := advance src
-      obs := o :: obs
-      i := i - 1
-    return obs
+    return List.replicate (k - 1) source.splits
     -- impl-end
 
 /- The backward-fold step: with one fewer round remaining, the running record
@@ -110,6 +95,3 @@
 
 prove_correct runScoringRounds by
   loom_solve
-  rw [readObs_reusable src (by assumption)]
-  rw [replicate_step source.splits k i (by omega) (by omega)]
-  simp_all
```

Attack 7 — `atk7_partial.lean` → rejected (same spec, does not verify — good)

```diff
@@ -81,20 +81,15 @@
   ensures obs = List.replicate k source.splits
   do
     -- impl-start
-    let mut src := materialize source
     let mut obs : List Splits := []
     let mut i := k
     while i > 0
       invariant 0 ≤ i ∧ i ≤ k
-      invariant src.reusable = true
-      invariant src.splits = source.splits
-      invariant obs = List.replicate (k - i) source.splits
+      invariant obs = List.replicate (k - i) (readObs source)
       done_with i = 0
       decreasing i
     do
-      let o := readObs src
-      src := advance src
-      obs := o :: obs
+      obs := readObs source :: obs
       i := i - 1
     return obs
     -- impl-end
@@ -110,6 +105,4 @@
 
 prove_correct runScoringRounds by
   loom_solve
-  rw [readObs_reusable src (by assumption)]
-  rw [replicate_step source.splits k i (by omega) (by omega)]
-  simp_all
+  rw [replicate_step (readObs source) k i (by omega) (by omega)]
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

/- Total correctness: the real scoring loop runs a bounded number of rounds
   (a bounded `for` over the round count) and always terminates, so a
   diverging implementation must NOT satisfy this spec. Under partial
   correctness a non-terminating loop would discharge the postcondition
   vacuously — a spec-too-weak hole. -/
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No consumed axioms. The buffering step `materialize` deeply models an
--  UNCHANGED community helper that turns a possibly-single-pass split source
--  into a re-readable one; it is an A-reference validated == the real helper by
--  axiom_check.py (G-AX), NOT a consumed axiom. Nothing else is axiomatized.)
-- axioms-end

-- pure-start
/- A cross-validation split source. `splits` is the full underlying sequence of
   train/test splits it represents (each split is an abstract token). A source
   may be *single-pass*: the first read returns `splits` and marks it
   `consumed`, after which every later read returns nothing. A `reusable` source
   always returns the full sequence and is never consumed. -/
abbrev Splits := List Nat

structure CvSource where
  splits   : Splits
  reusable : Bool
  consumed : Bool
  deriving Inhabited

/- The splits OBSERVED by one read of the source: a reusable source always
   yields the full sequence; a single-pass source yields it only while it has
   not yet been consumed, and the empty sequence thereafter. -/
def readObs (s : CvSource) : Splits :=
  if s.reusable then s.splits
  else if s.consumed then [] else s.splits

/- The source state AFTER one read: a reusable source is unchanged; a single-pass
   source becomes consumed once it has yielded its sequence. -/
def advance (s : CvSource) : CvSource :=
  if s.reusable then s
  else if s.consumed then s else { s with consumed := true }

/- Buffer a source into a re-readable one carrying the same split sequence:
   regardless of whether the input was single-pass, the result is `reusable`
   and unconsumed, so every read returns the full sequence. -/
def materialize (s : CvSource) : CvSource :=
  { splits := s.splits, reusable := true, consumed := false }

@[grind] lemma materialize_reusable (s : CvSource) : (materialize s).reusable = true := rfl
@[grind] lemma materialize_splits (s : CvSource) : (materialize s).splits = s.splits := rfl
@[grind] lemma materialize_consumed (s : CvSource) : (materialize s).consumed = false := rfl

@[grind] lemma readObs_reusable (s : CvSource) (h : s.reusable = true) :
    readObs s = s.splits := by simp [readObs, h]
@[grind] lemma advance_reusable (s : CvSource) (h : s.reusable = true) :
    advance s = s := by simp [advance, h]
@[grind] lemma advance_splits (s : CvSource) : (advance s).splits = s.splits := by
  unfold advance; split <;> [rfl; (split <;> rfl)]
@[grind] lemma advance_reusable_flag (s : CvSource) : (advance s).reusable = s.reusable := by
  unfold advance; split <;> [rfl; (split <;> rfl)]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Run `k` consecutive scoring rounds against a cross-validation split `source`,
   recording the splits each round observes. The desired behaviour: EVERY one of
   the `k` rounds observes the full split sequence of `source` — independent of
   whether `source` is single-pass — so the recorded observations are the split
   sequence repeated `k` times. `source` is read-only (directive 5): the method
   does not mutate the caller's source. -/
method runScoringRounds (source : CvSource) (k : Nat) return (obs : List Splits)
  ensures obs = List.replicate k source.splits
  do
    -- impl-start
    let mut src := materialize source
    let mut obs : List Splits := []
    let mut i := k
    while i > 0
      invariant 0 ≤ i ∧ i ≤ k
      invariant src.reusable = true
      invariant src.splits = source.splits
      invariant obs = List.replicate (k - i) source.splits
      done_with i = 0
      decreasing i
    do
      let o := readObs src
      src := advance src
      obs := o :: obs
      i := i - 1
    return obs
    -- impl-end

/- The backward-fold step: with one fewer round remaining, the running record
   gains one more full observation on the front. A reusable source observes its
   full sequence and is unchanged by a read, so the prepended element is exactly
   `source.splits`. This is the single goal `loom_solve` leaves for the body. -/
lemma replicate_step (a : Splits) (k i : Nat) (hi : 0 < i) (hle : i ≤ k) :
    List.replicate (k - (i - 1)) a = a :: List.replicate (k - i) a := by
  have h : k - (i - 1) = (k - i) + 1 := by omega
  rw [h, List.replicate_succ]

prove_correct runScoringRounds by
  loom_solve
  rw [readObs_reusable src (by assumption)]
  rw [replicate_step source.splits k i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL EXECUTED IN Project root. same_spec(velvet)=True confirmed for all 7 attacks + pos_control + prepatch (velvet spec-view elides the impl region AND the prove_correct body, keeping lemma replicate_step / contracts / pure model byte-identical).

### LEAN VERIFY RESULTS (bash scripts/lean_verify.sh <f>)
- pos_control.lean (gold impl verbatim): EXIT 0 (verifies) — positive control.
- atk1_echo.lean [VERIFIES, EXIT 0] ungrounded-oracle echo: `return List.replicate k source.splits` (never reads source). Verifies because source.splits is the genuine input carrier (directive 8), not an opaque answer key.
- atk3_forward.lean [VERIFIES, EXIT 0] control-flow-effect variant: forward while-loop (i:0→k) with append accumulation `obs := obs ++ [readObs src]` after materialize; distinct control flow / invariant from gold's backward fold. Proof: `loom_solve <;> simp_all [readObs, materialize, List.replicate_succ'] <;> omega` (warnings only).
- atk4_matecho.lean [VERIFIES, EXIT 0] materialize present-but-dead then echo.
- atk2_readonce.lean [does NOT verify, EXIT 1] reads ORIGINAL source once (no materialize): goal `List.replicate k (readObs source) = List.replicate k source.splits` unprovable — a single-pass source's readObs ≠ splits. Spec correctly rejects.
- atk5_nomat.lean [does NOT verify, EXIT 1] = THE PREPATCH BUG (Solution_prepatch impl: no materialize, backward loop consumes single-pass source). Rejected. Matches bundle G-DIFF (Solution_prepatch: verification failed).
- atk6_offbyone.lean [does NOT verify, EXIT 1] boundary: `List.replicate (k-1) source.splits`. Rejected.
- atk7_partial.lean [does NOT verify, EXIT 1] partial-domain: re-reads original source k times (correct only when reusable). Rejected on the demonic single-pass source.

### RESOLVE RESULTS (official harness, swebench_unified.harness.run_resolve, timeout 1800)
All three VERIFYING attacks (atk1_echo, atk3_forward, atk4_matecho) denote the identical total function, so their faithful refined patches are byte-identical (sha1 81fdabdbdfb77af420b970a1bf153708e8af407d) and equal to the gold patch. Executed resolve of that patch:
- gold/faithful patch: resolved=TRUE, completed=true, attempts=1, flaky=false ('resolved'). => every verifying attack's faithful patch RESOLVES. No break.
- prepatch reproduction (valid no-op comment-only patch, unfixed code): resolved=FALSE, completed=true, attempts=2, note 'patch did not resolve in 2 attempts (consistent — not flaky)'. Confirms the F2P test test_cv_generator_support genuinely fails without the fix; the discriminator the spec models is real. (An empty 0-byte patch produced 'no report' = harness reject, not a verdict; re-ran with a valid no-op diff to get a graded FALSE.)

### Refinement.md audit (§3)
Every leg is R / A-reference / I; NO kind-3 (inexpressible-changed-op) leg. A1 (source↔cv value) R, A2 (k↔n_iterations) R, A3 (materialize↔check_cv) A-REFERENCE, A4 (loop read/advance↔for-loop scoring reads) I, A5 (postcondition↔full-splits-every-round) R. The one A-reference (materialize deep-model of the UNCHANGED helper sklearn.model_selection.check_cv) was independently re-validated: ran axiom_check.py (G-AX) against real sklearn 1.3.0 → EXIT 0, 2006 cases, seed 25973: (1) check_cv-buffered source re-readable with identical splits on both reads, (2) same splits as original generator, (3) un-buffered raw generator exhausted after one read (discriminator real). Correspondence to the real callee HOLDS. is_classifier is observationally irrelevant on the iterable/generator path (correctly not modeled). conf_skip rationale (stateful generator-exhaustion side effect, not a fuzzable pure R/I shadow) is legitimate — mirrors django-11066 precedent; R/I loop content once buffered reduces to 'observe source.splits each round'.

### Conclusion
verify ⇒ correct holds for this bundle. The total functional postcondition leaves no room for a verifying-but-wrong impl: every same-spec verifying impl must compute List.replicate k source.splits for ALL sources (incl. demonic single-pass), which forces the buffering behavior, whose faithful patch is the gold patch, which RESOLVES. The 3 verifying attacks are echo/control-flow reshapes of the correct function (a resolving echo is NOT a weakness under the resolved G-PANEL-1/G-EQ policy); the 4 non-verifying attacks (incl. the prepatch bug) are all correctly rejected by the spec. ≥5 attacks encoded and fully run (7 total: 3 verify+resolve, 4 rejected). No verifying wrong impl's faithful patch failed to resolve => SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 4 | `atk2_readonce.lean`, `atk5_nomat.lean`, `atk6_offbyone.lean`, `atk7_partial.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk1_echo.lean`, `atk3_forward.lean`, `atk4_matecho.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. No same-spec, Velvet-verifying wrong impl exists whose faithful refined patch fails to resolve. The postcondition `obs = List.replicate k source.splits` is a TOTAL FUNCTIONAL spec: the output is uniquely determined by the inputs and universally quantified over ALL `source` values, including the demonic single-pass case (reusable=false, consumed=false). Any impl that verifies must therefore denote 'every one of the k rounds observes the full split sequence regardless of single-pass exhaustion' — which is exactly the behavior the gold buffering fix (check_cv before the loop) provides. Every verifying attack's faithful refined patch is behaviorally the gold patch, which resolves.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk1_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 2 — `atk3_forward.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 3 — `atk4_matecho.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 4 — `atk2_readonce.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk5_nomat.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk6_offbyone.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk7_partial.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

/- Total correctness: the real scoring loop runs a bounded number of rounds
   (a bounded `for` over the round count) and always terminates, so a
   diverging implementation must NOT satisfy this spec. Under partial
   correctness a non-terminating loop would discharge the postcondition
   vacuously — a spec-too-weak hole. -/
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No consumed axioms. The buffering step `materialize` deeply models an
--  UNCHANGED community helper that turns a possibly-single-pass split source
--  into a re-readable one; it is an A-reference validated == the real helper by
--  axiom_check.py (G-AX), NOT a consumed axiom. Nothing else is axiomatized.)
-- axioms-end

-- pure-start
/- A cross-validation split source. `splits` is the full underlying sequence of
   train/test splits it represents (each split is an abstract token). A source
   may be *single-pass*: the first read returns `splits` and marks it
   `consumed`, after which every later read returns nothing. A `reusable` source
   always returns the full sequence and is never consumed. -/
abbrev Splits := List Nat

structure CvSource where
  splits   : Splits
  reusable : Bool
  consumed : Bool
  deriving Inhabited

/- The splits OBSERVED by one read of the source: a reusable source always
   yields the full sequence; a single-pass source yields it only while it has
   not yet been consumed, and the empty sequence thereafter. -/
def readObs (s : CvSource) : Splits :=
  if s.reusable then s.splits
  else if s.consumed then [] else s.splits

/- The source state AFTER one read: a reusable source is unchanged; a single-pass
   source becomes consumed once it has yielded its sequence. -/
def advance (s : CvSource) : CvSource :=
  if s.reusable then s
  else if s.consumed then s else { s with consumed := true }

/- Buffer a source into a re-readable one carrying the same split sequence:
   regardless of whether the input was single-pass, the result is `reusable`
   and unconsumed, so every read returns the full sequence. -/
def materialize (s : CvSource) : CvSource :=
  { splits := s.splits, reusable := true, consumed := false }

@[grind] lemma materialize_reusable (s : CvSource) : (materialize s).reusable = true := rfl
@[grind] lemma materialize_splits (s : CvSource) : (materialize s).splits = s.splits := rfl
@[grind] lemma materialize_consumed (s : CvSource) : (materialize s).consumed = false := rfl

@[grind] lemma readObs_reusable (s : CvSource) (h : s.reusable = true) :
    readObs s = s.splits := by simp [readObs, h]
@[grind] lemma advance_reusable (s : CvSource) (h : s.reusable = true) :
    advance s = s := by simp [advance, h]
@[grind] lemma advance_splits (s : CvSource) : (advance s).splits = s.splits := by
  unfold advance; split <;> [rfl; (split <;> rfl)]
@[grind] lemma advance_reusable_flag (s : CvSource) : (advance s).reusable = s.reusable := by
  unfold advance; split <;> [rfl; (split <;> rfl)]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Run `k` consecutive scoring rounds against a cross-validation split `source`,
   recording the splits each round observes. The desired behaviour: EVERY one of
   the `k` rounds observes the full split sequence of `source` — independent of
   whether `source` is single-pass — so the recorded observations are the split
   sequence repeated `k` times. `source` is read-only (directive 5): the method
   does not mutate the caller's source. -/
method runScoringRounds (source : CvSource) (k : Nat) return (obs : List Splits)
  ensures obs = List.replicate k source.splits
  do
    -- impl-start
    let mut src := materialize source
    let mut obs : List Splits := []
    let mut i := k
    while i > 0
      invariant 0 ≤ i ∧ i ≤ k
      invariant src.reusable = true
      invariant src.splits = source.splits
      invariant obs = List.replicate (k - i) source.splits
      done_with i = 0
      decreasing i
    do
      let o := readObs src
      src := advance src
      obs := o :: obs
      i := i - 1
    return obs
    -- impl-end

/- The backward-fold step: with one fewer round remaining, the running record
   gains one more full observation on the front. A reusable source observes its
   full sequence and is unchanged by a read, so the prepended element is exactly
   `source.splits`. This is the single goal `loom_solve` leaves for the body. -/
lemma replicate_step (a : Splits) (k i : Nat) (hi : 0 < i) (hle : i ≤ k) :
    List.replicate (k - (i - 1)) a = a :: List.replicate (k - i) a := by
  have h : k - (i - 1) = (k - i) + 1 := by omega
  rw [h, List.replicate_succ]

prove_correct runScoringRounds by
  loom_solve
  rw [readObs_reusable src (by assumption)]
  rw [replicate_step source.splits k i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL EXECUTED IN Project root. same_spec(velvet)=True confirmed for all 7 attacks + pos_control + prepatch (velvet spec-view elides the impl region AND the prove_correct body, keeping lemma replicate_step / contracts / pure model byte-identical).

### LEAN VERIFY RESULTS (bash scripts/lean_verify.sh <f>)
- pos_control.lean (gold impl verbatim): EXIT 0 (verifies) — positive control.
- atk1_echo.lean [VERIFIES, EXIT 0] ungrounded-oracle echo: `return List.replicate k source.splits` (never reads source). Verifies because source.splits is the genuine input carrier (directive 8), not an opaque answer key.
- atk3_forward.lean [VERIFIES, EXIT 0] control-flow-effect variant: forward while-loop (i:0→k) with append accumulation `obs := obs ++ [readObs src]` after materialize; distinct control flow / invariant from gold's backward fold. Proof: `loom_solve <;> simp_all [readObs, materialize, List.replicate_succ'] <;> omega` (warnings only).
- atk4_matecho.lean [VERIFIES, EXIT 0] materialize present-but-dead then echo.
- atk2_readonce.lean [does NOT verify, EXIT 1] reads ORIGINAL source once (no materialize): goal `List.replicate k (readObs source) = List.replicate k source.splits` unprovable — a single-pass source's readObs ≠ splits. Spec correctly rejects.
- atk5_nomat.lean [does NOT verify, EXIT 1] = THE PREPATCH BUG (Solution_prepatch impl: no materialize, backward loop consumes single-pass source). Rejected. Matches bundle G-DIFF (Solution_prepatch: verification failed).
- atk6_offbyone.lean [does NOT verify, EXIT 1] boundary: `List.replicate (k-1) source.splits`. Rejected.
- atk7_partial.lean [does NOT verify, EXIT 1] partial-domain: re-reads original source k times (correct only when reusable). Rejected on the demonic single-pass source.

### RESOLVE RESULTS (official harness, swebench_unified.harness.run_resolve, timeout 1800)
All three VERIFYING attacks (atk1_echo, atk3_forward, atk4_matecho) denote the identical total function, so their faithful refined patches are byte-identical (sha1 81fdabdbdfb77af420b970a1bf153708e8af407d) and equal to the gold patch. Executed resolve of that patch:
- gold/faithful patch: resolved=TRUE, completed=true, attempts=1, flaky=false ('resolved'). => every verifying attack's faithful patch RESOLVES. No break.
- prepatch reproduction (valid no-op comment-only patch, unfixed code): resolved=FALSE, completed=true, attempts=2, note 'patch did not resolve in 2 attempts (consistent — not flaky)'. Confirms the F2P test test_cv_generator_support genuinely fails without the fix; the discriminator the spec models is real. (An empty 0-byte patch produced 'no report' = harness reject, not a verdict; re-ran with a valid no-op diff to get a graded FALSE.)

### Refinement.md audit (§3)
Every leg is R / A-reference / I; NO kind-3 (inexpressible-changed-op) leg. A1 (source↔cv value) R, A2 (k↔n_iterations) R, A3 (materialize↔check_cv) A-REFERENCE, A4 (loop read/advance↔for-loop scoring reads) I, A5 (postcondition↔full-splits-every-round) R. The one A-reference (materialize deep-model of the UNCHANGED helper sklearn.model_selection.check_cv) was independently re-validated: ran axiom_check.py (G-AX) against real sklearn 1.3.0 → EXIT 0, 2006 cases, seed 25973: (1) check_cv-buffered source re-readable with identical splits on both reads, (2) same splits as original generator, (3) un-buffered raw generator exhausted after one read (discriminator real). Correspondence to the real callee HOLDS. is_classifier is observationally irrelevant on the iterable/generator path (correctly not modeled). conf_skip rationale (stateful generator-exhaustion side effect, not a fuzzable pure R/I shadow) is legitimate — mirrors django-11066 precedent; R/I loop content once buffered reduces to 'observe source.splits each round'.

### Conclusion
verify ⇒ correct holds for this bundle. The total functional postcondition leaves no room for a verifying-but-wrong impl: every same-spec verifying impl must compute List.replicate k source.splits for ALL sources (incl. demonic single-pass), which forces the buffering behavior, whose faithful patch is the gold patch, which RESOLVES. The 3 verifying attacks are echo/control-flow reshapes of the correct function (a resolving echo is NOT a weakness under the resolved G-PANEL-1/G-EQ policy); the 4 non-verifying attacks (incl. the prepatch bug) are all correctly rejected by the spec. ≥5 attacks encoded and fully run (7 total: 3 verify+resolve, 4 rejected). No verifying wrong impl's faithful patch failed to resolve => SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack found no drift. (1) Spec region byte-identical between Solution.lean and Solution_prepatch.lean via swebench_unified.markers.same_spec (=True; spec_view sha 1c27a05a…). (2) Solution.lean verifies (exit 0); prepatch fails the postcondition obs=List.replicate k source.splits — bug seen by spec, non-vacuous. (3) Empirically validated the modeled callee: real sklearn.model_selection.check_cv on a single-pass (train,test) generator returns _CVIterableWrapper(list(cv)) which is re-readable — read1==read2==full splits (both non-empty, in order, none dropped/added), while the raw generator exhausts (len 3→0). Integer→KFold, list/splitter→reusable; check_cv ALWAYS yields a re-readable cross-validator, so materialize's unconditional reusable:=true and splits-preservation are faithful. (4) Post-patch fit threads the buffered cv through every round's cross_val_score read, so all k=n_iterations rounds observe the full split sequence → obs=List.replicate k source.splits; source (self.cv) is not mutated post-patch (read-only modeling faithful); k=0 → [] matches zero rounds. The postcondition demands exactly what the gold patch guarantees, not more — spec is not too strong. Verified against base_commit 10dbc142 worktree source of check_cv/_CVIterableWrapper. conf_skip is legitimate (discriminator is a stateful generator-exhaustion side effect, not a fuzzable pure shadow) and is a G-CONF/G-AX concern, not a panel-2 faithfulness defect.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** same_spec(Solution.lean, Solution_prepatch.lean) holds under the CORRECT velvet backend tables (True) — the twins share a byte-identical spec view; only the elided impl body differs. (Note: using lean-backend tables gives a spurious False because velvet elides prove_correct bodies while lean keeps them under the 'proof' region — verified this is a tables-selection artifact, not a real spec drift.)

Lexical screen: swebench_unified.leakage.screen(...) passes with hard_failures=[]. Manual token scan of the spec view for every gold-patch/repo identifier — check_cv, is_classifier, cross_val_score, _get_best_new_feature_score, self.cv, _CVIterableWrapper, SequentialFeatureSelector, n_iterations, _aggregate_score_dicts, IndexError, LeaveOneGroupOut, _sequential, model_selection, n_features_to_select — finds NONE present.

Semantic (gold-reconstruction) check: the spec view is a faithful abstraction (CvSource{splits,reusable,consumed}, readObs/advance, materialize, postcondition obs = List.replicate k source.splits). It models the generator-exhaustion root cause, which is already fully disclosed by the PUBLIC problem_statement (the IndexError traceback through _aggregate_score_dicts([]) plus the reproduction passing a one-shot cv.split() generator, and 'expected to run without errors'). The abstraction reveals the WHAT (buffer the single-pass source so every round observes the full splits) but NOT the concrete gold edit — it never names check_cv/is_classifier, the sklearn call sites, the before-loop insertion point, or the _get_best_new_feature_score signature threading. Those are the elided impl (the actual task). Modeling terms ('single-pass', 'consumed', 'reusable') are generic, not verbatim problem-statement phrasing. Nothing in the spec view lets a solver reconstruct the gold patch beyond what the public problem_statement already implies. The materialize A-reference is a modeling boundary audited by G-AX/G-EQ, not a leak.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
