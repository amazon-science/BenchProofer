# P2 adversarial audit — django__django-15499

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. The spec problem_spec_optimizeCreateThenAlterManagers is a fully-determined functional contract: it pins the result exactly in BOTH branches (sameModel=true -> result = [{model with managers := newManagers}]; sameModel=false -> result = []). No same-spec wrong implementation admits a closing proof, so there is no verifying-but-incorrect impl and thus no faithful patch that fails to resolve. verify => correct holds.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -74,8 +74,6 @@
 def implementation_optimizeCreateThenAlterManagers
     (model : ModelState) (targetName : String)
     (newManagers : List (String × String)) : List ModelState := Id.run do
-  if sameModel model.name targetName then
-    return [{ model with managers := newManagers }]
   return []
 -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -74,9 +74,7 @@
 def implementation_optimizeCreateThenAlterManagers
     (model : ModelState) (targetName : String)
     (newManagers : List (String × String)) : List ModelState := Id.run do
-  if sameModel model.name targetName then
-    return [{ model with managers := newManagers }]
-  return []
+  return [{ model with managers := newManagers }]
 -- impl-end
 
 -- proof-start
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -75,8 +75,8 @@
     (model : ModelState) (targetName : String)
     (newManagers : List (String × String)) : List ModelState := Id.run do
   if sameModel model.name targetName then
-    return [{ model with managers := newManagers }]
-  return []
+    return []
+  return [{ model with managers := newManagers }]
 -- impl-end
 
 -- proof-start
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -75,7 +75,7 @@
     (model : ModelState) (targetName : String)
     (newManagers : List (String × String)) : List ModelState := Id.run do
   if sameModel model.name targetName then
-    return [{ model with managers := newManagers }]
+    return [model]
   return []
 -- impl-end
 
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -75,7 +75,7 @@
     (model : ModelState) (targetName : String)
     (newManagers : List (String × String)) : List ModelState := Id.run do
   if sameModel model.name targetName then
-    return [{ model with managers := newManagers }]
+    return [{ model with fields := newManagers }]
   return []
 -- impl-end
 
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -74,7 +74,7 @@
 def implementation_optimizeCreateThenAlterManagers
     (model : ModelState) (targetName : String)
     (newManagers : List (String × String)) : List ModelState := Id.run do
-  if sameModel model.name targetName then
+  if model.name = targetName then
     return [{ model with managers := newManagers }]
   return []
 -- impl-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -75,7 +75,7 @@
     (model : ModelState) (targetName : String)
     (newManagers : List (String × String)) : List ModelState := Id.run do
   if sameModel model.name targetName then
-    return [{ model with managers := newManagers }]
+    return [{ model with managers := newManagers }, { model with managers := newManagers }]
   return []
 -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Collapsing a model-creation step followed by a manager-reconfiguration step
during migration optimization.

A migration is optimized by repeatedly looking at a creation step together with
the step that immediately follows it and, where possible, fusing the two into a
single step. A model-creation step records, for one model: its name, its fields,
its options, its bases, and its managers.

When the step that follows a model-creation step merely reconfigures the
**managers** of the *same* model, the two steps describe a single net effect:
create that model already carrying the reconfigured managers. In that case the
pair collapses into one creation step that is identical to the original except
that its managers are replaced by the reconfigured ones — the name, fields,
options, and bases are carried over unchanged.

If the following step reconfigures the managers of a *different* model, the two
steps are independent and no such collapse is produced.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The reduction
-- performs only a case-insensitive comparison of the two model identifiers and
-- the construction of a fresh creation step that copies four components and
-- substitutes the managers. Both are modeled directly (`String.toLower` and a
-- structure update), so no `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- A model-creation step, observed through the five components an optimization
of it reads or rewrites: the model identifier, its fields, its options, its
bases, and its managers. Fields/options/bases/managers are carried as opaque
`(name, repr)` token lists — the optimization only ever copies them. -/
structure ModelState where
  name : String
  fields : List (String × String)
  options : List (String × String)
  bases : List String
  managers : List (String × String)
deriving DecidableEq, Repr

/-- Two model identifiers name the same model when they agree case-insensitively
(the optimizer compares lower-cased names). -/
def sameModel (a b : String) : Bool := a.toLower = b.toLower
-- pure-end

-- post-conditions-start
/-- The outcome of pairing a model-creation step `model` with a following step
that reconfigures managers (`newManagers`) of the model identified by
`targetName`:

  * when the two refer to the same model, the pair collapses into exactly one
    creation step equal to `model` in name, fields, options, and bases, but with
    its managers replaced by `newManagers` (every carried-over component pinned
    to its input — directive 5 frame);
  * otherwise no collapsed creation step is produced (the empty result).

The two cases are exhaustive and mutually exclusive, so the result is fully
determined for every input. -/
def problem_spec_optimizeCreateThenAlterManagers
    (model : ModelState) (targetName : String)
    (newManagers : List (String × String))
    (result : List ModelState) : Prop :=
  (sameModel model.name targetName = true →
      result = [{ model with managers := newManagers }]) ∧
  (sameModel model.name targetName = false →
      result = [])
-- post-conditions-end

-- impl-start
def implementation_optimizeCreateThenAlterManagers
    (model : ModelState) (targetName : String)
    (newManagers : List (String × String)) : List ModelState := Id.run do
  if sameModel model.name targetName then
    return [{ model with managers := newManagers }]
  return []
-- impl-end

-- proof-start
theorem correct_optimizeCreateThenAlterManagers :
    ∀ (model : ModelState) (targetName : String)
      (newManagers : List (String × String)),
      problem_spec_optimizeCreateThenAlterManagers model targetName newManagers
        (implementation_optimizeCreateThenAlterManagers model targetName newManagers) := by
  intro model targetName newManagers
  unfold problem_spec_optimizeCreateThenAlterManagers
    implementation_optimizeCreateThenAlterManagers
  by_cases h : sameModel model.name targetName = true
  · refine ⟨fun _ => ?_, fun h' => ?_⟩
    · simp only [Id.run, h, if_true, pure]
    · rw [h] at h'; exact absurd h' (by decide)
  · simp only [Bool.not_eq_true] at h
    refine ⟨fun h' => ?_, fun _ => ?_⟩
    · rw [h] at h'; exact absurd h' (by decide)
    · simp only [Id.run, h, Bool.false_eq_true, if_false, pure, bind]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL: same_spec (lean backend) = True for all 7 attacks (verified with python -m ... markers.same_spec, spec regions byte-identical: only impl-region edited).

COMMANDS: for each file X.lean: `bash scripts/lean_verify.sh X.lean`. Attack verifications launched concurrently in two background batches (atk_1-4, then atk_5-7), <=4 at a time.

### Results
- pos_control.lean (exact Solution.lean impl): EXIT=0 (verifies, no sorry). #print axioms correct_optimizeCreateThenAlterManagers => depends on axioms: [propext] (axcheck.lean EXIT=0) — CLEAN.
- atk_1 (prepatch bug: unconditional `return []`): EXIT=1, unsolved goals. Reproduces the prepatch behavior (Solution_prepatch.lean impl is byte-identical `return []`). prepatch_reproduced=true.
- atk_2 (control-flow-effect: no name guard, always merge `return [{model with managers:=newManagers}]`): EXIT=1, unsolved goals (fails sameModel=false branch: [merged] != []).
- atk_3 (boundary: swapped guard — merge only when models DIFFER): EXIT=1, unsolved goals. Brute-force proof attempt (simp_all/split/aesop) also EXIT=1, leaves `⊢ False` with h:¬toLower=toLower.
- atk_4 (no-update: `return [model]` on match, keeps old managers): EXIT=1, unsolved goals (model != {model with managers:=newManagers} unless newManagers=model.managers).
- atk_5 (wrong-slot / ungrounded-oracle echo: substitutes newManagers into `fields` slot): EXIT=1, unsolved goals.
- atk_6 (case-sensitivity boundary: exact `model.name = targetName` instead of sameModel/toLower): EXIT=1, unsolved goals at both branches. Brute-force attempt EXIT=1, leaves `⊢ False` with h:¬model.name=targetName — witness: name="Foo", targetName="foo" makes sameModel=true (spec demands [merged]) but impl returns [].
- atk_7 (wrong cardinality: duplicated singleton -> 2-element list): EXIT=1, unsolved goals.

All 7 same-spec wrong impls REJECTED (exit 1, unsolved goals). NO wrong impl closes with clean axioms => NO faithful patch to materialize => run_resolve not applicable (correctly, per protocol step 2: only triggered if a wrong impl's proof closes cleanly). patches={}.

REFINEMENT.MD AUDIT: 3 legs, all R or R/I (leg1 R name-guard; leg2 R/I record-copy+managers substitution; leg3 R empty-result/no-reduction). No A-consumed, no A-reference, no kind-3. meta.json axioms=[] and deep_model_references=[] are JUSTIFIED: the modeled reduction is pure structural work — a case-insensitive name compare (self.name_lower==operation.name_lower modeled deeply as String.toLower) and construction of a fresh CreateModel copying name/fields/options/bases and substituting managers (modeled deeply as `{model with managers:=…}`). No unchanged-callee contract consumed; CreateModel.__init__ sanity checks are not part of the modeled reduction value. axiom_check.py is a legitimate skip stub. Correspondence to the real patched `elif isinstance(operation, AlterModelManagers) and self.name_lower==operation.name_lower` arm in django/db/migrations/operations/models.py holds (mapping.md file:line bindings check out). R/I legs covered by conformance_check.py (present, conf_skip=false, seed 15499).

CONCLUSION: verify => correct is upheld. SOUND. (Consistent with prior nagini pass at box6g70v which also found SOUND with 7 rejected attacks.)

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. The spec problem_spec_optimizeCreateThenAlterManagers is a fully-determined functional contract: it pins the result exactly in BOTH branches (sameModel=true -> result = [{model with managers := newManagers}]; sameModel=false -> result = []). No same-spec wrong implementation admits a closing proof, so there is no verifying-but-incorrect impl and thus no faithful patch that fails to resolve. verify => correct holds.
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

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Collapsing a model-creation step followed by a manager-reconfiguration step
during migration optimization.

A migration is optimized by repeatedly looking at a creation step together with
the step that immediately follows it and, where possible, fusing the two into a
single step. A model-creation step records, for one model: its name, its fields,
its options, its bases, and its managers.

When the step that follows a model-creation step merely reconfigures the
**managers** of the *same* model, the two steps describe a single net effect:
create that model already carrying the reconfigured managers. In that case the
pair collapses into one creation step that is identical to the original except
that its managers are replaced by the reconfigured ones — the name, fields,
options, and bases are carried over unchanged.

If the following step reconfigures the managers of a *different* model, the two
steps are independent and no such collapse is produced.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The reduction
-- performs only a case-insensitive comparison of the two model identifiers and
-- the construction of a fresh creation step that copies four components and
-- substitutes the managers. Both are modeled directly (`String.toLower` and a
-- structure update), so no `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- A model-creation step, observed through the five components an optimization
of it reads or rewrites: the model identifier, its fields, its options, its
bases, and its managers. Fields/options/bases/managers are carried as opaque
`(name, repr)` token lists — the optimization only ever copies them. -/
structure ModelState where
  name : String
  fields : List (String × String)
  options : List (String × String)
  bases : List String
  managers : List (String × String)
deriving DecidableEq, Repr

/-- Two model identifiers name the same model when they agree case-insensitively
(the optimizer compares lower-cased names). -/
def sameModel (a b : String) : Bool := a.toLower = b.toLower
-- pure-end

-- post-conditions-start
/-- The outcome of pairing a model-creation step `model` with a following step
that reconfigures managers (`newManagers`) of the model identified by
`targetName`:

  * when the two refer to the same model, the pair collapses into exactly one
    creation step equal to `model` in name, fields, options, and bases, but with
    its managers replaced by `newManagers` (every carried-over component pinned
    to its input — directive 5 frame);
  * otherwise no collapsed creation step is produced (the empty result).

The two cases are exhaustive and mutually exclusive, so the result is fully
determined for every input. -/
def problem_spec_optimizeCreateThenAlterManagers
    (model : ModelState) (targetName : String)
    (newManagers : List (String × String))
    (result : List ModelState) : Prop :=
  (sameModel model.name targetName = true →
      result = [{ model with managers := newManagers }]) ∧
  (sameModel model.name targetName = false →
      result = [])
-- post-conditions-end

-- impl-start
def implementation_optimizeCreateThenAlterManagers
    (model : ModelState) (targetName : String)
    (newManagers : List (String × String)) : List ModelState := Id.run do
  if sameModel model.name targetName then
    return [{ model with managers := newManagers }]
  return []
-- impl-end

-- proof-start
theorem correct_optimizeCreateThenAlterManagers :
    ∀ (model : ModelState) (targetName : String)
      (newManagers : List (String × String)),
      problem_spec_optimizeCreateThenAlterManagers model targetName newManagers
        (implementation_optimizeCreateThenAlterManagers model targetName newManagers) := by
  intro model targetName newManagers
  unfold problem_spec_optimizeCreateThenAlterManagers
    implementation_optimizeCreateThenAlterManagers
  by_cases h : sameModel model.name targetName = true
  · refine ⟨fun _ => ?_, fun h' => ?_⟩
    · simp only [Id.run, h, if_true, pure]
    · rw [h] at h'; exact absurd h' (by decide)
  · simp only [Bool.not_eq_true] at h
    refine ⟨fun h' => ?_, fun _ => ?_⟩
    · rw [h] at h'; exact absurd h' (by decide)
    · simp only [Id.run, h, Bool.false_eq_true, if_false, pure, bind]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL: same_spec (lean backend) = True for all 7 attacks (verified with python -m ... markers.same_spec, spec regions byte-identical: only impl-region edited).

COMMANDS: for each file X.lean: `bash scripts/lean_verify.sh X.lean`. Attack verifications launched concurrently in two background batches (atk_1-4, then atk_5-7), <=4 at a time.

### Results
- pos_control.lean (exact Solution.lean impl): EXIT=0 (verifies, no sorry). #print axioms correct_optimizeCreateThenAlterManagers => depends on axioms: [propext] (axcheck.lean EXIT=0) — CLEAN.
- atk_1 (prepatch bug: unconditional `return []`): EXIT=1, unsolved goals. Reproduces the prepatch behavior (Solution_prepatch.lean impl is byte-identical `return []`). prepatch_reproduced=true.
- atk_2 (control-flow-effect: no name guard, always merge `return [{model with managers:=newManagers}]`): EXIT=1, unsolved goals (fails sameModel=false branch: [merged] != []).
- atk_3 (boundary: swapped guard — merge only when models DIFFER): EXIT=1, unsolved goals. Brute-force proof attempt (simp_all/split/aesop) also EXIT=1, leaves `⊢ False` with h:¬toLower=toLower.
- atk_4 (no-update: `return [model]` on match, keeps old managers): EXIT=1, unsolved goals (model != {model with managers:=newManagers} unless newManagers=model.managers).
- atk_5 (wrong-slot / ungrounded-oracle echo: substitutes newManagers into `fields` slot): EXIT=1, unsolved goals.
- atk_6 (case-sensitivity boundary: exact `model.name = targetName` instead of sameModel/toLower): EXIT=1, unsolved goals at both branches. Brute-force attempt EXIT=1, leaves `⊢ False` with h:¬model.name=targetName — witness: name="Foo", targetName="foo" makes sameModel=true (spec demands [merged]) but impl returns [].
- atk_7 (wrong cardinality: duplicated singleton -> 2-element list): EXIT=1, unsolved goals.

All 7 same-spec wrong impls REJECTED (exit 1, unsolved goals). NO wrong impl closes with clean axioms => NO faithful patch to materialize => run_resolve not applicable (correctly, per protocol step 2: only triggered if a wrong impl's proof closes cleanly). patches={}.

REFINEMENT.MD AUDIT: 3 legs, all R or R/I (leg1 R name-guard; leg2 R/I record-copy+managers substitution; leg3 R empty-result/no-reduction). No A-consumed, no A-reference, no kind-3. meta.json axioms=[] and deep_model_references=[] are JUSTIFIED: the modeled reduction is pure structural work — a case-insensitive name compare (self.name_lower==operation.name_lower modeled deeply as String.toLower) and construction of a fresh CreateModel copying name/fields/options/bases and substituting managers (modeled deeply as `{model with managers:=…}`). No unchanged-callee contract consumed; CreateModel.__init__ sanity checks are not part of the modeled reduction value. axiom_check.py is a legitimate skip stub. Correspondence to the real patched `elif isinstance(operation, AlterModelManagers) and self.name_lower==operation.name_lower` arm in django/db/migrations/operations/models.py holds (mapping.md file:line bindings check out). R/I legs covered by conformance_check.py (present, conf_skip=false, seed 15499).

CONCLUSION: verify => correct is upheld. SOUND. (Consistent with prior nagini pass at box6g70v which also found SOUND with 7 rejected attacks.)

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Proof verified REAL: scripts/lean_verify.sh exits 0 (compiles, no sorry) and `#print axioms correct_optimizeCreateThenAlterManagers` => [propext] only (no sorryAx). Central modeling is faithful over the declared ASCII/well-formed domain: same-model (case-insensitive) collapse copies name/fields/options/bases and substitutes managers; different-model / no-arm-fires yields a bool which is soundly modeled as []. Confirmed base Operation.reduce can only return [operation]/[self]/False and neither op is elidable in this pairing, so no non-empty list can arise on the false branch — [] is faithful. mapping.md and refinement.md correctly disclose the ASCII-only toLower bijection and the excluded duplicate-name/malformed-input cases. The spec is neither too strong nor drifting on the real modeled behavior; the only disagreements are on inputs the mapping legitimately places out of scope. Verdict: FAITHFUL.

Counterexample / evidence:

```
Real-repo confirmation at base d90e34c61b: CreateModel('Foo',fields=[],managers=[('objects','m')]).reduce(AlterModelManagers('foo',managers=[('things','t'),('published','p')]),'app') => [<CreateModel 'Foo' ... managers=[('things','t'),('published','p')]>] (matches spec [{model with managers:=newManagers}]); .reduce(AlterModelManagers('Bar',...),'app') => True (a bool, no CreateModel; matches spec []). Divergence witnesses: str.lower('Σ')='σ' vs Lean "Σ".toLower="Σ"; AlterModelManagers('Foo',[('objects','x'),('objects','y')]) reduce RAISES ValueError.
```

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (Solution.lean lean flavor) does not leak the gold edit beyond the public problem_statement. Public problem_statement already states the full target behavior: 'Optimize CreateModel + AlterModelManagers to CreateModel ... CreateModel + AlterModelManagers can become just CreateModel.' The spec-view prose and postcondition problem_spec_optimizeCreateThenAlterManagers describe exactly this behavior (collapse a creation step + same-model manager-reconfig into one creation step carrying the new managers; different model -> no collapse), which is within the publicly disclosed behavior, not beyond it.

Evidence:
- Mechanical screen (swebench_unified.leakage.screen against frozen row): PASSED, zero hard failures, zero warnings.
- No Lean/PY diff markers in view; no gold-patch changed-line reproduced; no patched file path (models.py) or dotted module in view.
- Only distinctive patched symbol is 'reduce'; it does NOT appear in any spec-view identifier or comment. 'createmodel', 'altermodelmanagers', 'name_lower', 'models.py' all absent from the view.
- Modeled-function name optimizeCreateThenAlterManagers names the behavior and shares no substring with patched symbols (patched method reduce, class CreateModel, operand AlterModelManagers).
- The five carried components (name/fields/options/bases/managers) are the public CreateModel shape / general Django domain vocabulary, not gold-edit specifics; the case-insensitive same-model guard (sameModel/String.toLower) is a behavioral condition, not the repo's elif/name_lower mechanism.
- No bug/fix narration in spec-view comments.
- same_spec(Solution_prepatch.lean, Solution.lean) = True (spec region byte-identical between pre/post).
Conclusion: spec view reveals nothing about the gold edit's location or mechanism beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
