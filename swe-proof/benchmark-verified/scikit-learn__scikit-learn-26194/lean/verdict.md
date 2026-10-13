# P2 adversarial audit — scikit-learn__scikit-learn-26194

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1_wronghead.lean`, `atk_2_prepatch.lean`, `atk_3_partial.lean`, `atk_4_boundary.lean`, `atk_5_append.lean`, `atk_6_revtail.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7_echo.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_wronghead.lean` → rejected (same spec, does not verify — good)

```diff
@@ -51,7 +51,7 @@
 -- impl-start
 def implementation_rocCurveThresholds (ts : List ℚ) : List Thr := Id.run do
   let mut out := ts.map Thr.finite
-  out := Thr.posInf :: out
+  out := Thr.finite 999 :: out
   return out
 -- impl-end
 
@@ -62,5 +62,10 @@
         (implementation_rocCurveThresholds ts) := by
   intro ts
   unfold problem_spec_rocCurveThresholds implementation_rocCurveThresholds
-  rfl
+  first
+  | rfl
+  | (simp [Id.run, List.foldr_cons, List.foldr_nil])
+  | (induction ts with
+     | nil => rfl
+     | cons x xs ih => simp_all)
 -- proof-end
```

Attack 2 — `atk_2_prepatch.lean` → rejected (same spec, does not verify — good)

```diff
@@ -51,7 +51,7 @@
 -- impl-start
 def implementation_rocCurveThresholds (ts : List ℚ) : List Thr := Id.run do
   let mut out := ts.map Thr.finite
-  out := Thr.posInf :: out
+  out := Thr.finite (ts.headD 0 + 1) :: out
   return out
 -- impl-end
 
@@ -62,5 +62,10 @@
         (implementation_rocCurveThresholds ts) := by
   intro ts
   unfold problem_spec_rocCurveThresholds implementation_rocCurveThresholds
-  rfl
+  first
+  | rfl
+  | (simp [Id.run, List.foldr_cons, List.foldr_nil])
+  | (induction ts with
+     | nil => rfl
+     | cons x xs ih => simp_all)
 -- proof-end
```

Attack 3 — `atk_3_partial.lean` → rejected (same spec, does not verify — good)

```diff
@@ -49,10 +49,10 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_rocCurveThresholds (ts : List ℚ) : List Thr := Id.run do
-  let mut out := ts.map Thr.finite
-  out := Thr.posInf :: out
-  return out
+def implementation_rocCurveThresholds (ts : List ℚ) : List Thr :=
+  match ts with
+  | [] => []
+  | x  => Thr.posInf :: (x.map Thr.finite)
 -- impl-end
 
 -- proof-start
@@ -62,5 +62,10 @@
         (implementation_rocCurveThresholds ts) := by
   intro ts
   unfold problem_spec_rocCurveThresholds implementation_rocCurveThresholds
-  rfl
+  first
+  | rfl
+  | (simp [Id.run, List.foldr_cons, List.foldr_nil])
+  | (induction ts with
+     | nil => rfl
+     | cons x xs ih => simp_all)
 -- proof-end
```

Attack 4 — `atk_4_boundary.lean` → rejected (same spec, does not verify — good)

```diff
@@ -49,10 +49,9 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_rocCurveThresholds (ts : List ℚ) : List Thr := Id.run do
-  let mut out := ts.map Thr.finite
-  out := Thr.posInf :: out
-  return out
+def implementation_rocCurveThresholds (ts : List ℚ) : List Thr :=
+  if ts.length = 1 then Thr.posInf :: Thr.posInf :: (ts.map Thr.finite)
+  else Thr.posInf :: (ts.map Thr.finite)
 -- impl-end
 
 -- proof-start
@@ -62,5 +61,10 @@
         (implementation_rocCurveThresholds ts) := by
   intro ts
   unfold problem_spec_rocCurveThresholds implementation_rocCurveThresholds
-  rfl
+  first
+  | rfl
+  | (simp [Id.run, List.foldr_cons, List.foldr_nil])
+  | (induction ts with
+     | nil => rfl
+     | cons x xs ih => simp_all)
 -- proof-end
```

Attack 5 — `atk_5_append.lean` → rejected (same spec, does not verify — good)

```diff
@@ -51,7 +51,7 @@
 -- impl-start
 def implementation_rocCurveThresholds (ts : List ℚ) : List Thr := Id.run do
   let mut out := ts.map Thr.finite
-  out := Thr.posInf :: out
+  out := out ++ [Thr.posInf]
   return out
 -- impl-end
 
@@ -62,5 +62,10 @@
         (implementation_rocCurveThresholds ts) := by
   intro ts
   unfold problem_spec_rocCurveThresholds implementation_rocCurveThresholds
-  rfl
+  first
+  | rfl
+  | (simp [Id.run, List.foldr_cons, List.foldr_nil])
+  | (induction ts with
+     | nil => rfl
+     | cons x xs ih => simp_all)
 -- proof-end
```

Attack 6 — `atk_6_revtail.lean` → rejected (same spec, does not verify — good)

```diff
@@ -49,10 +49,8 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_rocCurveThresholds (ts : List ℚ) : List Thr := Id.run do
-  let mut out := ts.map Thr.finite
-  out := Thr.posInf :: out
-  return out
+def implementation_rocCurveThresholds (ts : List ℚ) : List Thr :=
+  Thr.posInf :: (ts.reverse.map Thr.finite)
 -- impl-end
 
 -- proof-start
@@ -62,5 +60,10 @@
         (implementation_rocCurveThresholds ts) := by
   intro ts
   unfold problem_spec_rocCurveThresholds implementation_rocCurveThresholds
-  rfl
+  first
+  | rfl
+  | (simp [Id.run, List.foldr_cons, List.foldr_nil])
+  | (induction ts with
+     | nil => rfl
+     | cons x xs ih => simp_all)
 -- proof-end
```

Attack 7 — `atk_7_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -49,10 +49,8 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_rocCurveThresholds (ts : List ℚ) : List Thr := Id.run do
-  let mut out := ts.map Thr.finite
-  out := Thr.posInf :: out
-  return out
+def implementation_rocCurveThresholds (ts : List ℚ) : List Thr :=
+  Thr.posInf :: (ts.foldr (fun q acc => Thr.finite q :: acc) [])
 -- impl-end
 
 -- proof-start
@@ -62,5 +60,10 @@
         (implementation_rocCurveThresholds ts) := by
   intro ts
   unfold problem_spec_rocCurveThresholds implementation_rocCurveThresholds
-  rfl
+  first
+  | rfl
+  | (simp [Id.run, List.foldr_cons, List.foldr_nil])
+  | (induction ts with
+     | nil => rfl
+     | cons x xs ih => simp_all)
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Building the threshold vector returned by the receiver-operating-characteristic
routine.

The routine first computes, from the scores, a vector of decreasing distinct
score values together with the false/true-positive counts at each of them. An
extra leading position is then prepended to the threshold vector so that the
plotted curve starts at the origin `(0, 0)`: this leading position stands for the
operating point at which no instance is predicted positive.

Because that leading position corresponds to "predict nothing positive", any
finite score is strictly below it; the value placed there is therefore the
positive-infinity sentinel `+∞`. The remaining entries of the returned vector are
exactly the decreasing score thresholds, unchanged.

So the returned threshold vector is the positive-infinity sentinel followed by the
decreasing finite score thresholds.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The decreasing
-- finite score thresholds produced upstream (and any optional thinning of them)
-- enter as the grounded input `ts`; the modeled behavior is purely the
-- construction of the returned threshold vector from `ts`. No `opaque`/`axiom`
-- callee contract is needed.
-- axioms-end

-- pure-start
/-- A returned threshold value: either a finite score threshold (`finite q`) or
the positive-infinity sentinel (`posInf`) placed at the leading "predict nothing
positive" position. (Faithful refinement of a float threshold, whose only
non-finite value used here is `+∞`.) -/
inductive Thr where
  | posInf
  | finite (q : ℚ)
deriving DecidableEq, Repr
-- pure-end

-- post-conditions-start
/-- The returned threshold vector is the positive-infinity sentinel followed by
the decreasing finite score thresholds `ts`, in order. The leading entry is the
sentinel and every later entry equals the corresponding input threshold. -/
def problem_spec_rocCurveThresholds
    (ts : List ℚ) (result : List Thr) : Prop :=
  result = Thr.posInf :: ts.map Thr.finite
-- post-conditions-end

-- impl-start
def implementation_rocCurveThresholds (ts : List ℚ) : List Thr := Id.run do
  let mut out := ts.map Thr.finite
  out := Thr.posInf :: out
  return out
-- impl-end

-- proof-start
theorem correct_rocCurveThresholds :
    ∀ (ts : List ℚ),
      problem_spec_rocCurveThresholds ts
        (implementation_rocCurveThresholds ts) := by
  intro ts
  unfold problem_spec_rocCurveThresholds implementation_rocCurveThresholds
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Spec: problem_spec_rocCurveThresholds ts result := result = Thr.posInf :: ts.map Thr.finite. This is a single EXACT extensional equality over a TOTAL domain (no ts != [] precondition in the frozen correct_; verdict.md's claim of one is STALE). It pins result uniquely as a function of ts, so any impl whose correct_ closes must be extensionally identical to post-patch (np.r_[np.inf, thresholds]) on every input — zero divergence freedom.

### Protocol executed
1. same_spec: True for all 7 attacks (swebench_unified.markers.same_spec, lean backend).
2. lean_verify (bash scripts/lean_verify.sh <f>), concurrent <=4/batch:
   - pos_control (Solution.lean): exit 0; #print axioms correct_ = [propext] (clean, no sorryAx).
   - atk_1_wronghead (Thr.finite 999 head, ungrounded): exit 1, unsolved goals.
   - atk_2_prepatch (Thr.finite (ts.headD 0 + 1) — exact transliteration of buggy thresholds[0]+1): exit 1, unsolved goals => PREPATCH REPRODUCED (unprovable on discriminating head clause).
   - atk_3_partial ([] on empty ts, correct on nonempty): exit 1, rfl failed.
   - atk_4_boundary (double posInf head when ts.length=1): exit 1, unsolved goals.
   - atk_5_append (sentinel appended at TAIL, control-flow-effect): exit 1, unsolved goals.
   - atk_6_revtail (reversed tail, diverges len>=2): exit 1, unsolved goals.
   - atk_7_echo (Thr.posInf :: ts.foldr (fun q acc => Thr.finite q :: acc) [], ungrounded-oracle echo): exit 0; #print axioms = [propext] (clean).
   All 6 divergent failures are GENUINE unsolved-goal/rfl failures, not syntax errors (proof block used a robust `first | rfl | simp[Id.run,...] | induction` so a close is genuine and a valid alt-construction is not spuriously rejected).
3. atk_7 is the ONLY closing clean-axiom impl. Its foldr construction is PROVABLY equal to ts.map Thr.finite (echo_eq.lean, induction, lean_verify exit 0), i.e. extensionally IDENTICAL to post-patch. Its faithful refined patch = the gold post-patch np.r_[np.inf, thresholds]. MATERIALIZED and RUN through official harness: run_resolve('scikit-learn__scikit-learn-26194', patch, timeout=1800, retries=0) => resolved=True, completed=True, note='resolved', attempts=1. Echo RESOLVES => no break.

REFINEMENT.MD AUDIT (A-legs / correspondence): op1 R (upstream _binary_clf_curve output + optional drop_intermediate thinning, UNCHANGED by patch, carried as grounded input ts:List Q — order/value-preserving float<->Thr.finite bijection per mapping.md), op2 R (the fix: np.r_[np.inf, thresholds] modeled DEEPLY as constructor Thr.posInf vs arithmetic max+1), op3 I (return threshold component). NO kind-3 legs. Axioms region contains NO opaque/axiom declarations (grep confirmed) => G-AX skips, NO A-legs to audit. A-leg correspondence trivially holds (none exist). R/I legs mechanically covered by G-CONF (conformance_check.py, seed 26194, N=120000, oracle=[INF]+ts vs shadow of impl).

CONCLUSION: SOUND. The exact-equality total post-condition admits no closing-but-divergent implementation; the sole closing echo resolves. verify => correct holds for this bundle. >=5 distinct wrong impls attacked (7 total incl. prepatch), all divergent ones fail to close, and the only closing (echo) impl's faithful patch was executed through run_resolve and RESOLVED.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1_wronghead.lean`, `atk_2_prepatch.lean`, `atk_3_partial.lean`, `atk_4_boundary.lean`, `atk_5_append.lean`, `atk_6_revtail.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7_echo.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1_wronghead.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3_partial.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4_boundary.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5_append.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6_revtail.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Building the threshold vector returned by the receiver-operating-characteristic
routine.

The routine first computes, from the scores, a vector of decreasing distinct
score values together with the false/true-positive counts at each of them. An
extra leading position is then prepended to the threshold vector so that the
plotted curve starts at the origin `(0, 0)`: this leading position stands for the
operating point at which no instance is predicted positive.

Because that leading position corresponds to "predict nothing positive", any
finite score is strictly below it; the value placed there is therefore the
positive-infinity sentinel `+∞`. The remaining entries of the returned vector are
exactly the decreasing score thresholds, unchanged.

So the returned threshold vector is the positive-infinity sentinel followed by the
decreasing finite score thresholds.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The decreasing
-- finite score thresholds produced upstream (and any optional thinning of them)
-- enter as the grounded input `ts`; the modeled behavior is purely the
-- construction of the returned threshold vector from `ts`. No `opaque`/`axiom`
-- callee contract is needed.
-- axioms-end

-- pure-start
/-- A returned threshold value: either a finite score threshold (`finite q`) or
the positive-infinity sentinel (`posInf`) placed at the leading "predict nothing
positive" position. (Faithful refinement of a float threshold, whose only
non-finite value used here is `+∞`.) -/
inductive Thr where
  | posInf
  | finite (q : ℚ)
deriving DecidableEq, Repr
-- pure-end

-- post-conditions-start
/-- The returned threshold vector is the positive-infinity sentinel followed by
the decreasing finite score thresholds `ts`, in order. The leading entry is the
sentinel and every later entry equals the corresponding input threshold. -/
def problem_spec_rocCurveThresholds
    (ts : List ℚ) (result : List Thr) : Prop :=
  result = Thr.posInf :: ts.map Thr.finite
-- post-conditions-end

-- impl-start
def implementation_rocCurveThresholds (ts : List ℚ) : List Thr := Id.run do
  let mut out := ts.map Thr.finite
  out := Thr.posInf :: out
  return out
-- impl-end

-- proof-start
theorem correct_rocCurveThresholds :
    ∀ (ts : List ℚ),
      problem_spec_rocCurveThresholds ts
        (implementation_rocCurveThresholds ts) := by
  intro ts
  unfold problem_spec_rocCurveThresholds implementation_rocCurveThresholds
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Spec: problem_spec_rocCurveThresholds ts result := result = Thr.posInf :: ts.map Thr.finite. This is a single EXACT extensional equality over a TOTAL domain (no ts != [] precondition in the frozen correct_; verdict.md's claim of one is STALE). It pins result uniquely as a function of ts, so any impl whose correct_ closes must be extensionally identical to post-patch (np.r_[np.inf, thresholds]) on every input — zero divergence freedom.

### Protocol executed
1. same_spec: True for all 7 attacks (swebench_unified.markers.same_spec, lean backend).
2. lean_verify (bash scripts/lean_verify.sh <f>), concurrent <=4/batch:
   - pos_control (Solution.lean): exit 0; #print axioms correct_ = [propext] (clean, no sorryAx).
   - atk_1_wronghead (Thr.finite 999 head, ungrounded): exit 1, unsolved goals.
   - atk_2_prepatch (Thr.finite (ts.headD 0 + 1) — exact transliteration of buggy thresholds[0]+1): exit 1, unsolved goals => PREPATCH REPRODUCED (unprovable on discriminating head clause).
   - atk_3_partial ([] on empty ts, correct on nonempty): exit 1, rfl failed.
   - atk_4_boundary (double posInf head when ts.length=1): exit 1, unsolved goals.
   - atk_5_append (sentinel appended at TAIL, control-flow-effect): exit 1, unsolved goals.
   - atk_6_revtail (reversed tail, diverges len>=2): exit 1, unsolved goals.
   - atk_7_echo (Thr.posInf :: ts.foldr (fun q acc => Thr.finite q :: acc) [], ungrounded-oracle echo): exit 0; #print axioms = [propext] (clean).
   All 6 divergent failures are GENUINE unsolved-goal/rfl failures, not syntax errors (proof block used a robust `first | rfl | simp[Id.run,...] | induction` so a close is genuine and a valid alt-construction is not spuriously rejected).
3. atk_7 is the ONLY closing clean-axiom impl. Its foldr construction is PROVABLY equal to ts.map Thr.finite (echo_eq.lean, induction, lean_verify exit 0), i.e. extensionally IDENTICAL to post-patch. Its faithful refined patch = the gold post-patch np.r_[np.inf, thresholds]. MATERIALIZED and RUN through official harness: run_resolve('scikit-learn__scikit-learn-26194', patch, timeout=1800, retries=0) => resolved=True, completed=True, note='resolved', attempts=1. Echo RESOLVES => no break.

REFINEMENT.MD AUDIT (A-legs / correspondence): op1 R (upstream _binary_clf_curve output + optional drop_intermediate thinning, UNCHANGED by patch, carried as grounded input ts:List Q — order/value-preserving float<->Thr.finite bijection per mapping.md), op2 R (the fix: np.r_[np.inf, thresholds] modeled DEEPLY as constructor Thr.posInf vs arithmetic max+1), op3 I (return threshold component). NO kind-3 legs. Axioms region contains NO opaque/axiom declarations (grep confirmed) => G-AX skips, NO A-legs to audit. A-leg correspondence trivially holds (none exist). R/I legs mechanically covered by G-CONF (conformance_check.py, seed 26194, N=120000, oracle=[INF]+ts vs shadow of impl).

CONCLUSION: SOUND. The exact-equality total post-condition admits no closing-but-divergent implementation; the sole closing echo resolves. verify => correct holds for this bundle. >=5 distinct wrong impls attacked (7 total incl. prepatch), all divergent ones fail to close, and the only closing (echo) impl's faithful patch was executed through run_resolve and RESOLVED.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong/drift) attack: no divergence found. Spec: problem_spec_rocCurveThresholds ts result := result = Thr.posInf :: ts.map Thr.finite. Real callee (post-patch roc_curve, sklearn/metrics/_ranking.py:1091, base_commit 2864505+patch): `thresholds = np.r_[np.inf, thresholds]`, returned unchanged as the threshold component of `return fpr, tpr, thresholds`. Modeling boundary: the decreasing finite thresholds from _binary_clf_curve (optionally drop_intermediate-thinned) enter as grounded input `ts`; the modeled behavior is exactly the leading-position prepend. On every input the modeled function equals the real callee: (1) leading entry is always +inf post-patch (never finite) -> Thr.posInf; (2) tail passes through np.r_ concatenation unchanged -> ts.map Thr.finite (order/equality preserved by float->Q refinement, and the construction does no float arithmetic, so exact rationals introduce no divergence); (3) drop_intermediate thinning is orthogonal and already folded into `ts`, never touching the sentinel; (4) totality over `ts` including [] matches the real total prepend (np.r_[np.inf, []] == [inf] == Thr.posInf::[]) so the total theorem demands no behavior the callee lacks — it is a (non-)weakening, not an over-strengthening. Verification evidence: same_spec(Solution, Solution_prepatch, lean tables)=True (spec region byte-identical); lean_verify.sh exit 0; #print axioms correct_rocCurveThresholds = [propext] (no sorryAx — proof is genuine); G-CONF conformance_check.py checked=120008 disagreements=0 status=pass; G-AX legitimately skips (deeply-modeled changed op, no consumed callee axiom). Spec pins the full returned vector to exactly the real post-patch output on all inputs. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `conformance_check.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Independently verified. same_spec(Solution, Solution_prepatch, LeanBackend.language)=True, so the gold discriminator lives only in the elided impl/proof regions; the spec view is identical between patch and prepatch. Gold edit under audit: sklearn/metrics/_ranking.py:1086, np.r_[thresholds[0] + 1, thresholds] -> np.r_[np.inf, thresholds] (leading threshold sentinel max(y_score)+1 -> np.inf). Scanned the full spec view (docstring + axioms + pure + post-conditions) for repo/edit-reconstructing tokens: np.inf, np.r_, roc_curve, _binary_clf_curve, _ranking, sklearn, 1086, y_score, thresholds[0], max(...), '+1', isinf, drop_intermediate, diff markers, patched path -- ALL absent. No bug/fix narration words present. The spec is expressed abstractly: inductive Thr (posInf | finite q:Q) and result = Thr.posInf :: ts.map Thr.finite, with a mathematical docstring calling the leading 'predict nothing positive' position the +infinity sentinel. That is the correct post-patch behavior any faithful spec must encode (as mathematics, not the literal np.inf code), not edit-localization -> not leakage. Decisively, the PUBLIC problem_statement is strictly MORE revealing than the spec: it cites line 1086, names the literal max(y_score)+1 / '+1' rule as the cause, and even proposes a fix (clip thresholds <= 1); the spec view names no file, line, numpy call, or diff fragment and does not literally mention np.inf. File:line/diff specifics live only in mapping.md/refinement.md, which are NOT part of the spec view. Not a relaxed bundle (relaxed_leakage=None, no RELAXED_LEAKAGE.md). No spec-view line reconstructs the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
