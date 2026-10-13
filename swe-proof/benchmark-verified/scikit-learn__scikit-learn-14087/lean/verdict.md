# P2 adversarial audit — scikit-learn__scikit-learn-14087

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. Both post-conditions are total, deterministic functional relations. problem_spec_chooseLayout pins each of the 2 EffStrategy values to exactly one AggLayout (eff=perClass->perClassLayout, eff=joint->jointLayout). problem_spec_ratioEntry pins each of the 2 Bool values to exactly one Option (true->some ratio, false->none). Any impl deviating on even one input makes the correctness theorem literally false, hence unprovable by ANY proof (not just the carried gold script). No same-spec wrong impl can produce a closing clean-axiom proof; there is no verify-but-incorrect artifact and no faithful patch to resolve.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -72,7 +72,7 @@
 def implementation_chooseLayout
     (req : ReqStrategy) (eff : EffStrategy) : AggLayout := Id.run do
   let mut layout := AggLayout.jointLayout
-  if eff = EffStrategy.perClass then
+  if req = ReqStrategy.perClass then
     layout := AggLayout.perClassLayout
   else
     layout := AggLayout.jointLayout
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -103,10 +103,7 @@
 def implementation_ratioEntry
     (combinedPenalty : Bool) (ratio : ℚ) : Option ℚ := Id.run do
   let mut entry : Option ℚ := none
-  if combinedPenalty then
-    entry := some ratio
-  else
-    entry := none
+  entry := some ratio
   return entry
 -- impl-end
 
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -71,12 +71,7 @@
 -- impl-start
 def implementation_chooseLayout
     (req : ReqStrategy) (eff : EffStrategy) : AggLayout := Id.run do
-  let mut layout := AggLayout.jointLayout
-  if eff = EffStrategy.perClass then
-    layout := AggLayout.perClassLayout
-  else
-    layout := AggLayout.jointLayout
-  return layout
+  return AggLayout.jointLayout
 -- impl-end
 
 -- proof-start
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -71,11 +71,11 @@
 -- impl-start
 def implementation_chooseLayout
     (req : ReqStrategy) (eff : EffStrategy) : AggLayout := Id.run do
-  let mut layout := AggLayout.jointLayout
+  let mut layout := AggLayout.perClassLayout
   if eff = EffStrategy.perClass then
+    layout := AggLayout.jointLayout
+  else
     layout := AggLayout.perClassLayout
-  else
-    layout := AggLayout.jointLayout
   return layout
 -- impl-end
 
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -104,9 +104,9 @@
     (combinedPenalty : Bool) (ratio : ℚ) : Option ℚ := Id.run do
   let mut entry : Option ℚ := none
   if combinedPenalty then
+    entry := none
+  else
     entry := some ratio
-  else
-    entry := none
   return entry
 -- impl-end
 
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -102,12 +102,7 @@
 -- impl-start
 def implementation_ratioEntry
     (combinedPenalty : Bool) (ratio : ℚ) : Option ℚ := Id.run do
-  let mut entry : Option ℚ := none
-  if combinedPenalty then
-    entry := some ratio
-  else
-    entry := none
-  return entry
+  return none
 -- impl-end
 
 -- proof-start
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -71,12 +71,7 @@
 -- impl-start
 def implementation_chooseLayout
     (req : ReqStrategy) (eff : EffStrategy) : AggLayout := Id.run do
-  let mut layout := AggLayout.jointLayout
-  if eff = EffStrategy.perClass then
-    layout := AggLayout.perClassLayout
-  else
-    layout := AggLayout.jointLayout
-  return layout
+  return AggLayout.perClassLayout
 -- impl-end
 
 -- proof-start
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Mathlib
-- imports-end

/-!
A cross-validation routine selects regularization hyper-parameters by scoring
candidate settings across folds, and — in the mode where it does NOT refit a
final model on the full data — summarizes its choice into per-class output
attributes. This bundle models two independent decisions taken while building
those summaries.

First decision: choosing how to aggregate the per-fold coefficient estimates.
There are two aggregation layouts. The choice must be driven by the *effective*
multiclass strategy actually in force — the strategy after configuration has been
resolved to a concrete one — and never by the raw, possibly-unresolved configured
request. Concretely, the per-class aggregation layout is used exactly when the
effective strategy is the per-class one, and the joint layout exactly when the
effective strategy is the joint one. The raw requested setting does not influence
this choice at all: two runs with the same effective strategy aggregate the same
way regardless of how that strategy was originally requested.

Second decision: recording the mixing-ratio summary entry. A mixing ratio between
the two penalty components is only meaningful when the model is run in the
combined-penalty regime. When it is, the recorded entry is the computed mixing
ratio. When it is not, there is no meaningful ratio and the recorded entry is
absent. The entry is fully determined by whether the combined-penalty regime is in
force: it is never the computed ratio outside that regime.
-/

-- axioms-start
-- No unchanged outside callee is CONSUMED as an axiom by either specification.
-- The effective strategy and the computed mixing ratio are produced by unchanged
-- upstream routines; they enter each modeled decision as free inputs, so the
-- decisions are proved correct for ALL of their possible values and no callee
-- property is consumed. Hence no `opaque`/`axiom` declaration is needed.
-- axioms-end

-- pure-start
/-- The effective (already-resolved) multiclass strategy in force. It is always a
concrete strategy — never an unresolved placeholder. -/
inductive EffStrategy where
  | perClass
  | joint
  deriving DecidableEq, Repr

/-- The raw requested multiclass strategy, which may still be an unresolved
placeholder (`autoStrategy`) in addition to the two concrete choices. -/
inductive ReqStrategy where
  | autoStrategy
  | perClass
  | joint
  deriving DecidableEq, Repr

/-- The coefficient-aggregation layout that is selected. -/
inductive AggLayout where
  | perClassLayout
  | jointLayout
  deriving DecidableEq, Repr
-- pure-end

-- post-conditions-start
/-- The selected aggregation layout is pinned solely to the EFFECTIVE strategy:
the per-class layout exactly when the effective strategy is per-class, and the
joint layout exactly when it is joint. The raw requested strategy is intentionally
unconstrained in the relation — the result must not depend on it. -/
def problem_spec_chooseLayout
    (req : ReqStrategy) (eff : EffStrategy) (result : AggLayout) : Prop :=
  (eff = EffStrategy.perClass → result = AggLayout.perClassLayout) ∧
  (eff = EffStrategy.joint → result = AggLayout.jointLayout)
-- post-conditions-end

-- impl-start
def implementation_chooseLayout
    (req : ReqStrategy) (eff : EffStrategy) : AggLayout := Id.run do
  let mut layout := AggLayout.jointLayout
  if eff = EffStrategy.perClass then
    layout := AggLayout.perClassLayout
  else
    layout := AggLayout.jointLayout
  return layout
-- impl-end

-- proof-start
theorem correct_chooseLayout :
    ∀ (req : ReqStrategy) (eff : EffStrategy),
      problem_spec_chooseLayout req eff (implementation_chooseLayout req eff) := by
  intro req eff
  unfold problem_spec_chooseLayout implementation_chooseLayout
  simp only [Id.run]
  refine ⟨fun he => ?_, fun he => ?_⟩ <;> subst he <;> rfl
-- proof-end

-- post-conditions-start
/-- The recorded mixing-ratio entry is pinned solely to whether the combined
penalty regime is in force: it is the computed ratio when in that regime, and
absent (`none`) otherwise. The computed ratio is irrelevant outside the regime. -/
def problem_spec_ratioEntry
    (combinedPenalty : Bool) (ratio : ℚ) (result : Option ℚ) : Prop :=
  (combinedPenalty = true → result = some ratio) ∧
  (combinedPenalty = false → result = none)
-- post-conditions-end

-- impl-start
def implementation_ratioEntry
    (combinedPenalty : Bool) (ratio : ℚ) : Option ℚ := Id.run do
  let mut entry : Option ℚ := none
  if combinedPenalty then
    entry := some ratio
  else
    entry := none
  return entry
-- impl-end

-- proof-start
theorem correct_ratioEntry :
    ∀ (combinedPenalty : Bool) (ratio : ℚ),
      problem_spec_ratioEntry combinedPenalty ratio
        (implementation_ratioEntry combinedPenalty ratio) := by
  intro combinedPenalty ratio
  unfold problem_spec_ratioEntry implementation_ratioEntry
  refine ⟨fun hc => ?_, fun hc => ?_⟩ <;>
    simp only [hc] <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL EXECUTED same_spec(gold,atk_N)=True for all 7 (swebench_unified.markers.same_spec python; gold self-check True). Verify command for each: `bash scripts/lean_verify.sh <file>`, run concurrently in 2 batches of <=4 background jobs.

### ATTACKS (7 distinct same-spec wrong impls; axioms/pure/pre/post left byte-identical, only impl regions edited):
- atk_1 (prepatch bug 1 / control-flow): chooseLayout selects on RAW request `if req = ReqStrategy.perClass` instead of eff -> exit 1, `rfl` failed at line 89 (req=autoStrategy,eff=perClass yields jointLayout != required perClassLayout). Reproduces the issue's IndexError config.
- atk_2 (prepatch bug 2 / control-flow-effect): ratioEntry always `some ratio`, no combinedPenalty guard -> exit 1, `rfl` failed (combinedPenalty=false yields some ratio != none). Reproduces F2P l2 config.
- atk_3 (partial-domain): chooseLayout always returns jointLayout -> exit 1, `rfl` failed at line 84 (eff=perClass path violated).
- atk_4 (boundary/inversion): chooseLayout swapped mapping (perClass->joint, else->perClass) -> exit 1, `rfl` failed line 89.
- atk_5 (control-flow-effect/inversion): ratioEntry swapped (true->none, false->some ratio) -> exit 1, `rfl` failed line 121.
- atk_6 (ungrounded/partial-domain): ratioEntry always none -> exit 1, `simp made no progress` line 116 (true path violated).
- atk_7 (partial-domain, other side): chooseLayout always returns perClassLayout -> exit 1, `rfl` failed (eff=joint path violated).

POSITIVE CONTROL: positive_control.lean is a byte-identical copy of gold Solution.lean -> `lean_verify.sh` exit 0 (only benign unused-variable `req` linter warning). `#print axioms` (pc_axioms.lean copy with #print appended): correct_chooseLayout depends on NO axioms; correct_ratioEntry depends on [propext] only. Clean (no sorry, no sorryAx, no custom/native_decide axioms).

PATCHES: empty {} because zero attacks produced a closing clean-axiom proof, so step-2 (materialize faithful patch + run_resolve) has no eligible artifact. No resolve run was needed or possible; this is not INCONCLUSIVE because every attack was fully verified (exit codes captured above) and the positive control + axioms all check out.

REFINEMENT AUDIT (refinement.md): decision 1 (chooseLayout) legs: #1 I, #2 R, #3 R, #4 R, #5 I. decision 2 (ratioEntry) legs: #1 I, #2 R, #3 R, #4 R, #5 I. All legs are R or I -- NO A-consumed, NO A-reference, NO kind-3. axiom_check.py is a consistent skip stub (no consumed callee axiom, no opaque callee) matching the R/I-only refinement; #print axioms on the positive control confirms no hidden axiom dependency beyond propext. The A-leg attack surface (axioms / deep-model references) is therefore EMPTY for this bundle, consistent with the stated pure-decision-logic modeling. R/I legs are covered by G-CONF per plan. Model<->patch correspondence in mapping.md (logistic.py:2173 effective multi_class branch; :2181-2184 elasticnet guard) is coherent with the total/deterministic specs.

VERDICT: SOUND -- >=5 (7) distinct same-spec wrong impls attempted; none closes with a clean-axiom proof; positive control verifies clean; prepatch bugs reproduced as attacks atk_1/atk_2. verify => correct holds for this spec.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. Both post-conditions are total, deterministic functional relations. problem_spec_chooseLayout pins each of the 2 EffStrategy values to exactly one AggLayout (eff=perClass->perClassLayout, eff=joint->jointLayout). problem_spec_ratioEntry pins each of the 2 Bool values to exactly one Option (true->some ratio, false->none). Any impl deviating on even one input makes the correctness theorem literally false, hence unprovable by ANY proof (not just the carried gold script). No same-spec wrong impl can produce a closing clean-axiom proof; there is no verify-but-incorrect artifact and no faithful patch to resolve.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Mathlib
-- imports-end

/-!
A cross-validation routine selects regularization hyper-parameters by scoring
candidate settings across folds, and — in the mode where it does NOT refit a
final model on the full data — summarizes its choice into per-class output
attributes. This bundle models two independent decisions taken while building
those summaries.

First decision: choosing how to aggregate the per-fold coefficient estimates.
There are two aggregation layouts. The choice must be driven by the *effective*
multiclass strategy actually in force — the strategy after configuration has been
resolved to a concrete one — and never by the raw, possibly-unresolved configured
request. Concretely, the per-class aggregation layout is used exactly when the
effective strategy is the per-class one, and the joint layout exactly when the
effective strategy is the joint one. The raw requested setting does not influence
this choice at all: two runs with the same effective strategy aggregate the same
way regardless of how that strategy was originally requested.

Second decision: recording the mixing-ratio summary entry. A mixing ratio between
the two penalty components is only meaningful when the model is run in the
combined-penalty regime. When it is, the recorded entry is the computed mixing
ratio. When it is not, there is no meaningful ratio and the recorded entry is
absent. The entry is fully determined by whether the combined-penalty regime is in
force: it is never the computed ratio outside that regime.
-/

-- axioms-start
-- No unchanged outside callee is CONSUMED as an axiom by either specification.
-- The effective strategy and the computed mixing ratio are produced by unchanged
-- upstream routines; they enter each modeled decision as free inputs, so the
-- decisions are proved correct for ALL of their possible values and no callee
-- property is consumed. Hence no `opaque`/`axiom` declaration is needed.
-- axioms-end

-- pure-start
/-- The effective (already-resolved) multiclass strategy in force. It is always a
concrete strategy — never an unresolved placeholder. -/
inductive EffStrategy where
  | perClass
  | joint
  deriving DecidableEq, Repr

/-- The raw requested multiclass strategy, which may still be an unresolved
placeholder (`autoStrategy`) in addition to the two concrete choices. -/
inductive ReqStrategy where
  | autoStrategy
  | perClass
  | joint
  deriving DecidableEq, Repr

/-- The coefficient-aggregation layout that is selected. -/
inductive AggLayout where
  | perClassLayout
  | jointLayout
  deriving DecidableEq, Repr
-- pure-end

-- post-conditions-start
/-- The selected aggregation layout is pinned solely to the EFFECTIVE strategy:
the per-class layout exactly when the effective strategy is per-class, and the
joint layout exactly when it is joint. The raw requested strategy is intentionally
unconstrained in the relation — the result must not depend on it. -/
def problem_spec_chooseLayout
    (req : ReqStrategy) (eff : EffStrategy) (result : AggLayout) : Prop :=
  (eff = EffStrategy.perClass → result = AggLayout.perClassLayout) ∧
  (eff = EffStrategy.joint → result = AggLayout.jointLayout)
-- post-conditions-end

-- impl-start
def implementation_chooseLayout
    (req : ReqStrategy) (eff : EffStrategy) : AggLayout := Id.run do
  let mut layout := AggLayout.jointLayout
  if eff = EffStrategy.perClass then
    layout := AggLayout.perClassLayout
  else
    layout := AggLayout.jointLayout
  return layout
-- impl-end

-- proof-start
theorem correct_chooseLayout :
    ∀ (req : ReqStrategy) (eff : EffStrategy),
      problem_spec_chooseLayout req eff (implementation_chooseLayout req eff) := by
  intro req eff
  unfold problem_spec_chooseLayout implementation_chooseLayout
  simp only [Id.run]
  refine ⟨fun he => ?_, fun he => ?_⟩ <;> subst he <;> rfl
-- proof-end

-- post-conditions-start
/-- The recorded mixing-ratio entry is pinned solely to whether the combined
penalty regime is in force: it is the computed ratio when in that regime, and
absent (`none`) otherwise. The computed ratio is irrelevant outside the regime. -/
def problem_spec_ratioEntry
    (combinedPenalty : Bool) (ratio : ℚ) (result : Option ℚ) : Prop :=
  (combinedPenalty = true → result = some ratio) ∧
  (combinedPenalty = false → result = none)
-- post-conditions-end

-- impl-start
def implementation_ratioEntry
    (combinedPenalty : Bool) (ratio : ℚ) : Option ℚ := Id.run do
  let mut entry : Option ℚ := none
  if combinedPenalty then
    entry := some ratio
  else
    entry := none
  return entry
-- impl-end

-- proof-start
theorem correct_ratioEntry :
    ∀ (combinedPenalty : Bool) (ratio : ℚ),
      problem_spec_ratioEntry combinedPenalty ratio
        (implementation_ratioEntry combinedPenalty ratio) := by
  intro combinedPenalty ratio
  unfold problem_spec_ratioEntry implementation_ratioEntry
  refine ⟨fun hc => ?_, fun hc => ?_⟩ <;>
    simp only [hc] <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL EXECUTED same_spec(gold,atk_N)=True for all 7 (swebench_unified.markers.same_spec python; gold self-check True). Verify command for each: `bash scripts/lean_verify.sh <file>`, run concurrently in 2 batches of <=4 background jobs.

### ATTACKS (7 distinct same-spec wrong impls; axioms/pure/pre/post left byte-identical, only impl regions edited):
- atk_1 (prepatch bug 1 / control-flow): chooseLayout selects on RAW request `if req = ReqStrategy.perClass` instead of eff -> exit 1, `rfl` failed at line 89 (req=autoStrategy,eff=perClass yields jointLayout != required perClassLayout). Reproduces the issue's IndexError config.
- atk_2 (prepatch bug 2 / control-flow-effect): ratioEntry always `some ratio`, no combinedPenalty guard -> exit 1, `rfl` failed (combinedPenalty=false yields some ratio != none). Reproduces F2P l2 config.
- atk_3 (partial-domain): chooseLayout always returns jointLayout -> exit 1, `rfl` failed at line 84 (eff=perClass path violated).
- atk_4 (boundary/inversion): chooseLayout swapped mapping (perClass->joint, else->perClass) -> exit 1, `rfl` failed line 89.
- atk_5 (control-flow-effect/inversion): ratioEntry swapped (true->none, false->some ratio) -> exit 1, `rfl` failed line 121.
- atk_6 (ungrounded/partial-domain): ratioEntry always none -> exit 1, `simp made no progress` line 116 (true path violated).
- atk_7 (partial-domain, other side): chooseLayout always returns perClassLayout -> exit 1, `rfl` failed (eff=joint path violated).

POSITIVE CONTROL: positive_control.lean is a byte-identical copy of gold Solution.lean -> `lean_verify.sh` exit 0 (only benign unused-variable `req` linter warning). `#print axioms` (pc_axioms.lean copy with #print appended): correct_chooseLayout depends on NO axioms; correct_ratioEntry depends on [propext] only. Clean (no sorry, no sorryAx, no custom/native_decide axioms).

PATCHES: empty {} because zero attacks produced a closing clean-axiom proof, so step-2 (materialize faithful patch + run_resolve) has no eligible artifact. No resolve run was needed or possible; this is not INCONCLUSIVE because every attack was fully verified (exit codes captured above) and the positive control + axioms all check out.

REFINEMENT AUDIT (refinement.md): decision 1 (chooseLayout) legs: #1 I, #2 R, #3 R, #4 R, #5 I. decision 2 (ratioEntry) legs: #1 I, #2 R, #3 R, #4 R, #5 I. All legs are R or I -- NO A-consumed, NO A-reference, NO kind-3. axiom_check.py is a consistent skip stub (no consumed callee axiom, no opaque callee) matching the R/I-only refinement; #print axioms on the positive control confirms no hidden axiom dependency beyond propext. The A-leg attack surface (axioms / deep-model references) is therefore EMPTY for this bundle, consistent with the stated pure-decision-logic modeling. R/I legs are covered by G-CONF per plan. Model<->patch correspondence in mapping.md (logistic.py:2173 effective multi_class branch; :2181-2184 elasticnet guard) is coherent with the total/deterministic specs.

VERDICT: SOUND -- >=5 (7) distinct same-spec wrong impls attempted; none closes with a clean-axiom proof; positive control verifies clean; prepatch bugs reproduced as attacks atk_1/atk_2. verify => correct holds for this spec.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack found NO diverging input; spec is faithful and not too strong.

### Verification performed
1. Compile+axioms: lean_verify.sh exit 0 (clean, no sorry). `#print axioms`: correct_chooseLayout depends on NO axioms; correct_ratioEntry depends only on [propext] (standard, NOT sorryAx). Proofs are genuine.
2. Spec-region byte-identity: swebench_unified.markers.same_spec(Solution, prepatch_1)=True and same_spec(Solution, prepatch_2)=True with the Lean LanguageTables — spec view preserved across prepatches.
3. Real repo at base_commit a5743ed36 confirmed 

DECISION 1 (chooseLayout) vs real patched callee (logistic.py:2173): patch changes guard to `if multi_class == 'ovr'` (EFFECTIVE strategy from _check_multi_class) selecting 3-D per-class layout, else 4-D joint. _check_multi_class provably returns only concrete 'ovr'/'multinomial' (never 'auto'). Spec problem_spec_chooseLayout pins result to `eff`: eff=perClass→perClassLayout, eff=joint→jointLayout. EffStrategy's two constructors exhaustively cover the real effective domain; else-branch (multinomial) → joint/4-D matches. `req` correctly excluded from the relation (the fix's whole point is dependence on effective, not raw, strategy). No divergence on any (req,eff).

DECISION 2 (ratioEntry) vs real patched callee (logistic.py:2181-2185): patch guards `if self.penalty == 'elasticnet': append(mean) else: append(None)`. Spec problem_spec_ratioEntry: combinedPenalty=true→some ratio, false→none. Bool domain exactly matches the penalty==elasticnet predicate. `ratio` is legitimately an abstract free ℚ — the patch decides only presence/absence, never the numeric mean value (unchanged argmax/floor-div/mean arithmetic), so pinning presence/absence and carrying the mean as a free input is exactly faithful, not too strong. No divergence on any (combinedPenalty,ratio).

No consumed callee axiom / no A-reference; axiom_check.py skip stub is justified — both impls are pure R/I control-flow predicates proved ∀ free inputs. The R legs are further grounded by G-CONF against the real patched fit over {l2,elasticnet}×{ovr,multinomial,auto}. Spec neither drifts from nor over-constrains real repo behavior.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `axiom_check.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Leakage judged against the public problem_statement (IndexError traceback for LogisticRegressionCV+refit=False) only; hints_text excluded. Mechanical G-LEAK screen passes with zero hard failures (verified via leakage.screen on the lean backend). Spec view was materialized via markers.spec_view: impl and proof regions are both elided to placeholders, so neither gold hunk (self.multi_class->multi_class; the `if self.penalty=='elasticnet'` guard) appears. same_spec confirms the spec region is byte-identical across Solution.lean and both prepatches.

Semantic assessment: the spec view (module docstring + pure inductives + two post-condition relations) uses only invented abstract Lean vocabulary (EffStrategy/ReqStrategy/AggLayout/combinedPenalty/ratio); no repo literals ('ovr','elasticnet',self.multi_class,l1_ratios_,coefs_paths,penalty), no diff markers, no patched file/module path, no reproduced gold-diff line, and no fix/bug/wrong-style narration. The changed-symbol set is empty (edits live inside `fit`, <4 chars after underscore-strip), so a symbol-collision leak is impossible. The post-conditions state required correct behavior (result pinned to the effective strategy not the raw request; entry = ratio in combined-penalty regime else absent) — this is a faithful behavioral contract, not a description of the edit, and does not reconstruct either hunk. Decision-2 behavior is absent from the public bug report but stating it abstractly specifies the required behavior rather than leaking the gold edit. No spec-view line reveals the gold edit beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
