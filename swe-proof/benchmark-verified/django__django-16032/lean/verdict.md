# P2 adversarial audit — django__django-16032

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -60,10 +60,13 @@
 -- post-conditions-end
 
 -- impl-start
+
 def implementation_prepInLookup
     (rhs : SubqueryState) (lhsTargetPrimaryKey : Bool)
     (targetField : String) : SubqueryState := Id.run do
-  if !rhs.explicitValuesApplied && !lhsTargetPrimaryKey then
+  let looksSelected := !rhs.selectCols.isEmpty
+    || rhs.hasAnnotationSelection || rhs.hasExtraSelection
+  if !looksSelected && !lhsTargetPrimaryKey then
     return restrictTo rhs [targetField]
   return rhs
 -- impl-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -60,10 +60,11 @@
 -- post-conditions-end
 
 -- impl-start
+
 def implementation_prepInLookup
     (rhs : SubqueryState) (lhsTargetPrimaryKey : Bool)
     (targetField : String) : SubqueryState := Id.run do
-  if !rhs.explicitValuesApplied && !lhsTargetPrimaryKey then
+  if !rhs.explicitValuesApplied && !lhsTargetPrimaryKey && rhs.selectCols.isEmpty then
     return restrictTo rhs [targetField]
   return rhs
 -- impl-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -60,10 +60,11 @@
 -- post-conditions-end
 
 -- impl-start
+
 def implementation_prepInLookup
     (rhs : SubqueryState) (lhsTargetPrimaryKey : Bool)
     (targetField : String) : SubqueryState := Id.run do
-  if !rhs.explicitValuesApplied && !lhsTargetPrimaryKey then
+  if !lhsTargetPrimaryKey then
     return restrictTo rhs [targetField]
   return rhs
 -- impl-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -60,11 +60,12 @@
 -- post-conditions-end
 
 -- impl-start
+
 def implementation_prepInLookup
     (rhs : SubqueryState) (lhsTargetPrimaryKey : Bool)
     (targetField : String) : SubqueryState := Id.run do
   if !rhs.explicitValuesApplied && !lhsTargetPrimaryKey then
-    return restrictTo rhs [targetField]
+    return { rhs with selectCols := [targetField], explicitValuesApplied := true }
   return rhs
 -- impl-end
 
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -60,12 +60,10 @@
 -- post-conditions-end
 
 -- impl-start
+
 def implementation_prepInLookup
     (rhs : SubqueryState) (lhsTargetPrimaryKey : Bool)
-    (targetField : String) : SubqueryState := Id.run do
-  if !rhs.explicitValuesApplied && !lhsTargetPrimaryKey then
-    return restrictTo rhs [targetField]
-  return rhs
+    (targetField : String) : SubqueryState := rhs
 -- impl-end
 
 -- proof-start
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -60,10 +60,11 @@
 -- post-conditions-end
 
 -- impl-start
+
 def implementation_prepInLookup
     (rhs : SubqueryState) (lhsTargetPrimaryKey : Bool)
     (targetField : String) : SubqueryState := Id.run do
-  if !rhs.explicitValuesApplied && !lhsTargetPrimaryKey then
+  if rhs.explicitValuesApplied && !lhsTargetPrimaryKey then
     return restrictTo rhs [targetField]
   return rhs
 -- impl-end
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -60,12 +60,14 @@
 -- post-conditions-end
 
 -- impl-start
+
 def implementation_prepInLookup
     (rhs : SubqueryState) (lhsTargetPrimaryKey : Bool)
-    (targetField : String) : SubqueryState := Id.run do
+    (targetField : String) : SubqueryState :=
   if !rhs.explicitValuesApplied && !lhsTargetPrimaryKey then
-    return restrictTo rhs [targetField]
-  return rhs
+    restrictTo rhs [targetField]
+  else
+    rhs
 -- impl-end
 
 -- proof-start
@@ -76,8 +78,7 @@
   intro rhs lhsTargetPrimaryKey targetField
   unfold problem_spec_prepInLookup implementation_prepInLookup restrictTo
   by_cases h : (!rhs.explicitValuesApplied && !lhsTargetPrimaryKey) = true
-  · simp only [Id.run, h, if_true]
-    exact ⟨rfl, rfl, rfl, rfl⟩
-  · simp only [Bool.not_eq_true] at h
-    simp only [Id.run, h, Bool.false_eq_true, if_false, bind, pure]
+  · rw [if_pos h, if_pos h]
+    refine ⟨rfl, rfl, rfl, rfl⟩
+  · rw [if_neg h, if_neg h]
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Restricting a subquery used on the right-hand side of a membership ("in")
lookup to a single comparison column.

When a membership lookup compares a column against a subquery, and the subquery
has NOT been given an explicit column selection, and the comparison's target
column is not itself the primary key, the subquery must be narrowed to the
single target column so the comparison is column-for-column. Otherwise the
subquery's existing selection is kept unchanged.
-/

-- axioms-start
-- No unchanged callee is consumed as an axiom: the single-column narrowing of
-- the subquery yields the one target column directly (modeled as a literal
-- one-element selection), so there is nothing to axiomatize.
-- axioms-end

-- pure-start
/-- The state of the subquery appearing on the right-hand side of the lookup,
restricted to the components that decide whether it must be narrowed.

* `selectCols`             — the columns the subquery currently selects.
* `hasAnnotationSelection` — whether an annotation-selection mask is present.
* `hasExtraSelection`      — whether an extra-selection mask is present.
* `explicitValuesApplied`  — whether an explicit column selection has been
  applied to the subquery (i.e. its selected columns were chosen on purpose). -/
structure SubqueryState where
  selectCols : List String
  hasAnnotationSelection : Bool
  hasExtraSelection : Bool
  explicitValuesApplied : Bool
deriving DecidableEq, Repr

/-- Narrow a subquery so it selects exactly the given columns. -/
def restrictTo (q : SubqueryState) (fields : List String) : SubqueryState :=
  { q with selectCols := fields,
           hasAnnotationSelection := false,
           hasExtraSelection := false,
           explicitValuesApplied := true }
-- pure-end

-- post-conditions-start
/-- When the subquery has no explicit column selection and the target column is
not the primary key, the result selects exactly the single target column, has
its annotation- and extra-selection cleared, and is marked as having an explicit
selection. Otherwise the subquery is left entirely unchanged. -/
def problem_spec_prepInLookup
    (rhs : SubqueryState) (lhsTargetPrimaryKey : Bool) (targetField : String)
    (result : SubqueryState) : Prop :=
  if (!rhs.explicitValuesApplied && !lhsTargetPrimaryKey) then
    result.selectCols = [targetField]
      ∧ result.hasAnnotationSelection = false
      ∧ result.hasExtraSelection = false
      ∧ result.explicitValuesApplied = true
  else
    result = rhs
-- post-conditions-end

-- impl-start
def implementation_prepInLookup
    (rhs : SubqueryState) (lhsTargetPrimaryKey : Bool)
    (targetField : String) : SubqueryState := Id.run do
  if !rhs.explicitValuesApplied && !lhsTargetPrimaryKey then
    return restrictTo rhs [targetField]
  return rhs
-- impl-end

-- proof-start
theorem correct_prepInLookup :
    ∀ (rhs : SubqueryState) (lhsTargetPrimaryKey : Bool) (targetField : String),
      problem_spec_prepInLookup rhs lhsTargetPrimaryKey targetField
        (implementation_prepInLookup rhs lhsTargetPrimaryKey targetField) := by
  intro rhs lhsTargetPrimaryKey targetField
  unfold problem_spec_prepInLookup implementation_prepInLookup restrictTo
  by_cases h : (!rhs.explicitValuesApplied && !lhsTargetPrimaryKey) = true
  · simp only [Id.run, h, if_true]
    exact ⟨rfl, rfl, rfl, rfl⟩
  · simp only [Bool.not_eq_true] at h
    simp only [Id.run, h, Bool.false_eq_true, if_false, bind, pure]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

All 7 attacks confirmed byte-identical spec (same_spec=True). Verifications run concurrently in two background batches of 4.

Commands: `bash scripts/lean_verify.sh <file>` per attack; `#print axioms correct_prepInLookup` appended for closing impls; resolve via python `swebench_unified.harness.run_resolve('django__django-16032', <patch>, timeout=3000)` (docker reachable only through `docker`, which the harness uses).

### Results
- pos_control (reference impl): lean_verify exit 0; axioms = [propext].
- atk_1 = prepatch bug (op-1 derived-rule under-narrow, `!(selectCols nonempty || annMask || extraMask)`) under the reference proof: exit 1 (proof does NOT close) => prepatch bug reproduced (matches Solution_prepatch.lean bug direction; discriminator rhs=([id,ann],ann=true,false,false),lhsPK=false,target=id yields .selectCols=[id,ann] vs spec-required [id]).
- atk_2 = partial-domain (adds spurious `rhs.selectCols.isEmpty` guard): exit 1.
- atk_3 = over-narrow/boundary (narrows whenever !lhsTargetPrimaryKey, ignores flag): exit 1.
- atk_4 = control-flow-effect (narrows selectCols+flag but leaves hasAnnotationSelection uncleared): exit 1.
- atk_5 = ungrounded identity (return rhs always): exit 1.
- atk_6 = inverted flag (narrows when explicitValuesApplied true): exit 1.
- atk_7 = equivalent echo (match on `!explicitValuesApplied && !lhsTargetPrimaryKey` -> restrictTo, else rhs; if_pos/if_neg proof): lean_verify exit 0; `#print axioms` => 'does not depend on any axioms' (clean); MATERIALIZED faithful patch = gold patch (extensionally identical branch decision + full output frame) and RAN it through official run_resolve => completed=True, resolved=True, attempts=1, flaky=False, note='resolved'.

Spec analysis: problem_spec_prepInLookup is FUNCTIONAL — it pins all four SubqueryState fields in the narrowing branch (selectCols=[t], annMask=false, extraMask=false, flag=true) and the entire frame (result=rhs) in the else branch. This leaves no slack: every divergent impl (atk_1..6) fails to close, and the only closing impl is extensionally equal to the reference and resolves. No divergent-but-closing impl exists => verify ⇒ correct holds.

Refinement/axiom audit: refinement.md legs are #1 R, #2 R/I, #3 R, #4 I, #5 R/I — all R/A-consumed/A-reference/I with NO kind-3 and, in fact, no A-legs at all. axioms-start/end region is comment-only; axioms=[], deep_model_references=[]; axiom_check.py is a principled skip stub. The reference proof's only axiom is propext (Mathlib proof mechanics, not a callee/model axiom), and the echo needs no axioms — so there is no A-leg correspondence to falsify. Refinement audit clean.

Verdict: SOUND — 7 same-spec attacks run, 6 diverge and fail to close, the 1 that closes with clean axioms resolves under the harness. No verify⇏correct break.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Restricting a subquery used on the right-hand side of a membership ("in")
lookup to a single comparison column.

When a membership lookup compares a column against a subquery, and the subquery
has NOT been given an explicit column selection, and the comparison's target
column is not itself the primary key, the subquery must be narrowed to the
single target column so the comparison is column-for-column. Otherwise the
subquery's existing selection is kept unchanged.
-/

-- axioms-start
-- No unchanged callee is consumed as an axiom: the single-column narrowing of
-- the subquery yields the one target column directly (modeled as a literal
-- one-element selection), so there is nothing to axiomatize.
-- axioms-end

-- pure-start
/-- The state of the subquery appearing on the right-hand side of the lookup,
restricted to the components that decide whether it must be narrowed.

* `selectCols`             — the columns the subquery currently selects.
* `hasAnnotationSelection` — whether an annotation-selection mask is present.
* `hasExtraSelection`      — whether an extra-selection mask is present.
* `explicitValuesApplied`  — whether an explicit column selection has been
  applied to the subquery (i.e. its selected columns were chosen on purpose). -/
structure SubqueryState where
  selectCols : List String
  hasAnnotationSelection : Bool
  hasExtraSelection : Bool
  explicitValuesApplied : Bool
deriving DecidableEq, Repr

/-- Narrow a subquery so it selects exactly the given columns. -/
def restrictTo (q : SubqueryState) (fields : List String) : SubqueryState :=
  { q with selectCols := fields,
           hasAnnotationSelection := false,
           hasExtraSelection := false,
           explicitValuesApplied := true }
-- pure-end

-- post-conditions-start
/-- When the subquery has no explicit column selection and the target column is
not the primary key, the result selects exactly the single target column, has
its annotation- and extra-selection cleared, and is marked as having an explicit
selection. Otherwise the subquery is left entirely unchanged. -/
def problem_spec_prepInLookup
    (rhs : SubqueryState) (lhsTargetPrimaryKey : Bool) (targetField : String)
    (result : SubqueryState) : Prop :=
  if (!rhs.explicitValuesApplied && !lhsTargetPrimaryKey) then
    result.selectCols = [targetField]
      ∧ result.hasAnnotationSelection = false
      ∧ result.hasExtraSelection = false
      ∧ result.explicitValuesApplied = true
  else
    result = rhs
-- post-conditions-end

-- impl-start
def implementation_prepInLookup
    (rhs : SubqueryState) (lhsTargetPrimaryKey : Bool)
    (targetField : String) : SubqueryState := Id.run do
  if !rhs.explicitValuesApplied && !lhsTargetPrimaryKey then
    return restrictTo rhs [targetField]
  return rhs
-- impl-end

-- proof-start
theorem correct_prepInLookup :
    ∀ (rhs : SubqueryState) (lhsTargetPrimaryKey : Bool) (targetField : String),
      problem_spec_prepInLookup rhs lhsTargetPrimaryKey targetField
        (implementation_prepInLookup rhs lhsTargetPrimaryKey targetField) := by
  intro rhs lhsTargetPrimaryKey targetField
  unfold problem_spec_prepInLookup implementation_prepInLookup restrictTo
  by_cases h : (!rhs.explicitValuesApplied && !lhsTargetPrimaryKey) = true
  · simp only [Id.run, h, if_true]
    exact ⟨rfl, rfl, rfl, rfl⟩
  · simp only [Bool.not_eq_true] at h
    simp only [Id.run, h, Bool.false_eq_true, if_false, bind, pure]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

All 7 attacks confirmed byte-identical spec (same_spec=True). Verifications run concurrently in two background batches of 4.

Commands: `bash scripts/lean_verify.sh <file>` per attack; `#print axioms correct_prepInLookup` appended for closing impls; resolve via python `swebench_unified.harness.run_resolve('django__django-16032', <patch>, timeout=3000)` (docker reachable only through `docker`, which the harness uses).

### Results
- pos_control (reference impl): lean_verify exit 0; axioms = [propext].
- atk_1 = prepatch bug (op-1 derived-rule under-narrow, `!(selectCols nonempty || annMask || extraMask)`) under the reference proof: exit 1 (proof does NOT close) => prepatch bug reproduced (matches Solution_prepatch.lean bug direction; discriminator rhs=([id,ann],ann=true,false,false),lhsPK=false,target=id yields .selectCols=[id,ann] vs spec-required [id]).
- atk_2 = partial-domain (adds spurious `rhs.selectCols.isEmpty` guard): exit 1.
- atk_3 = over-narrow/boundary (narrows whenever !lhsTargetPrimaryKey, ignores flag): exit 1.
- atk_4 = control-flow-effect (narrows selectCols+flag but leaves hasAnnotationSelection uncleared): exit 1.
- atk_5 = ungrounded identity (return rhs always): exit 1.
- atk_6 = inverted flag (narrows when explicitValuesApplied true): exit 1.
- atk_7 = equivalent echo (match on `!explicitValuesApplied && !lhsTargetPrimaryKey` -> restrictTo, else rhs; if_pos/if_neg proof): lean_verify exit 0; `#print axioms` => 'does not depend on any axioms' (clean); MATERIALIZED faithful patch = gold patch (extensionally identical branch decision + full output frame) and RAN it through official run_resolve => completed=True, resolved=True, attempts=1, flaky=False, note='resolved'.

Spec analysis: problem_spec_prepInLookup is FUNCTIONAL — it pins all four SubqueryState fields in the narrowing branch (selectCols=[t], annMask=false, extraMask=false, flag=true) and the entire frame (result=rhs) in the else branch. This leaves no slack: every divergent impl (atk_1..6) fails to close, and the only closing impl is extensionally equal to the reference and resolves. No divergent-but-closing impl exists => verify ⇒ correct holds.

Refinement/axiom audit: refinement.md legs are #1 R, #2 R/I, #3 R, #4 I, #5 R/I — all R/A-consumed/A-reference/I with NO kind-3 and, in fact, no A-legs at all. axioms-start/end region is comment-only; axioms=[], deep_model_references=[]; axiom_check.py is a principled skip stub. The reference proof's only axiom is propext (Mathlib proof mechanics, not a callee/model axiom), and the echo needs no axioms — so there is no A-leg correspondence to falsify. Refinement audit clean.

Verdict: SOUND — 7 same-spec attacks run, 6 diverge and fail to close, the 1 that closes with clean axioms resolves under the harness. No verify⇏correct break.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack found NO divergence between the modeled function and the real callee. Checks performed: (1) spec regions byte-identical Solution vs Solution_prepatch via swebench_unified.markers.same_spec -> True; (2) Solution.lean compiles with no sorry and #print axioms correct_prepInLookup -> [propext] only (genuine proof); (3) traced the real post-patch callee RelatedIn.get_prep_lookup @ base_commit 0c3981eb + Query.set_values in query.py. The spec pivots on the post-patch explicit flag has_select_fields (=explicitValuesApplied), matching `elif not getattr(self.rhs,'has_select_fields',True) and not target_field.primary_key`. Narrowing branch models set_values([target]): sets has_select_fields=True, clear_select_fields() empties select+values_select, set_annotation_mask([])/set_extra_mask([]) clear both masks => ([target],False,False,True) == restrictTo; else branch = full-frame preservation (result=rhs) == the 'no set_values call' path. (4) Ran the bundle conformance_check.py against the gold repo: 120000 inputs, 0 disagreements. (5) Ran an INDEPENDENT differential test with an expanded input domain (kinds: fresh, annotated, aliased_annotated, values, values_empty, extra, extra+annotate, only/defer, raw add_fields; both lhs_pk values; all concrete targets id/name/size) driving a real gold Query -> 0 divergences; e.g. masked-preserve case aliased_annotated+pk=True yields ([],True,False,False) preserved identically by oracle and spec, confirming the full-frame else branch is not too-strong. The spec is functional (pins the entire SubqueryState in both branches) and agrees with the real callee on every reachable input. Note: verdict.md references a G-CONF fail, but that is stale — meta.json records G-CONF=pass and it reproduces. No spec-too-strong / faithfulness defect.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (consumer projection via markers.spec_view) is byte-identical between Solution.lean and Solution_prepatch.lean (same_spec=True); impl and proof regions are elided. Mechanical G-LEAK screen PASSES (rep.passed=True, zero hard failures). Manual review confirms no leak beyond the public problem_statement:
- L1: no diff markers, no verbatim gold-patch line reproduced. The discriminating gold strings (`set_values([target_field])`, `clear_select_clause()`, `has_select_fields = False`, the `@property has_select_fields` deletion) do NOT appear in the spec view.
- L2: no patched file path (`related_lookups.py`, `query.py`) or module path in the spec view.
- L2/L5: none of the distinctive patched repo symbols {Query, get_prep_lookup, has_select_fields, output_field, set_values} are embedded in any spec-view identifier. The model uses backend-abstract names (SubqueryState, selectCols, hasAnnotationSelection, hasExtraSelection, explicitValuesApplied, restrictTo, problem_spec_prepInLookup) that localize no repo edit.
- L3: no bug/fix/patch narration in any spec-view comment or docstring; the docstrings describe intended behavior abstractly.

The post-condition keys the narrow-to-single-column decision on `!explicitValuesApplied`, which is a faithful formalization of the publicly-desired correct behavior already disclosed by problem_statement (the RHS subquery must be narrowed to one column; the observable failure is 'sub-select returns N columns - expected 1'). It does NOT disclose the gold edit or its localization: the actual fix (converting a derived `has_select_fields` property into an explicit class-attribute flag set by `set_values`, plus routing RelatedIn through set_values) is not recoverable from the spec view. The buggy 'derived from select/annotation/extra masks' rule lives ONLY in the elided prepatch impl region, never in the spec view. The repo-symbol names and file paths that would leak localization appear only in mapping.md/refinement.md, which are auditor-facing artifacts and are NOT part of the solver-visible spec view. hints_text (which names has_select_fields/set_values/get_prep_lookup) is not referenced by the spec view. No RELAXED_LEAKAGE.md and relaxed_leakage flag is unset, so no deferral is needed. Note: the G-PANEL fail on this cell is G-PANEL-2 (spec drift), unrelated to leakage.

- L1: no diff markers, no verbatim gold-patch line reproduced. The discriminating gold strings (`set_values([target_field])`, `clear_select_clause()`, `has_select_fields = False`, the `@property has_select_fields` deletion) do NOT appear in the spec view.
- L2: no patched file path (`related_lookups.py`, `query.py`) or module path in the spec view.
- L2/L5: none of the distinctive patched repo symbols {Query, get_prep_lookup, has_select_fields, output_field, set_values} are embedded in any spec-view identifier. The model uses backend-abstract names (SubqueryState, selectCols, hasAnnotationSelection, hasExtraSelection, explicitValuesApplied, restrictTo, problem_spec_prepInLookup) that localize no repo edit.
- L3: no bug/fix/patch narration in any spec-view comment or docstring; the docstrings describe intended behavior abstractly.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
