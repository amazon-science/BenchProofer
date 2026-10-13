# P2 adversarial audit — django__django-15629

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -44,9 +44,9 @@
 def implementation_fkColumnParams
     (fkType : String) (fkCheck : Option String) (targetParams : ColumnParams) :
     ColumnParams := Id.run do
+  -- WRONG (prepatch A): collation never carried over from the referenced column.
   let mut params : ColumnParams :=
     { colType := fkType, checkExpr := fkCheck, collation := none }
-  params := { params with collation := targetParams.collation }
   return params
 -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -80,9 +80,10 @@
     (supportsFk oldPk newPk oldUnique newUnique : Bool)
     (oldType newType : String) (oldCollation newCollation : Option String) :
     Bool := Id.run do
+  -- WRONG (prepatch B): only fires on a type change, ignores collation change.
   let mut decision := supportsFk
   decision := decision && ((oldPk && newPk) || (oldUnique && newUnique))
-  decision := decision && ((oldType != newType) || (oldCollation != newCollation))
+  decision := decision && (oldType != newType)
   return decision
 -- impl-end
 
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -115,8 +115,7 @@
 -- impl-start
 def implementation_relatedColumnAlterKind
     (oldRelCollation relCollation : Option String) : RelAlterKind := Id.run do
-  if oldRelCollation != relCollation then
-    return RelAlterKind.collationAlter
+  -- WRONG (prepatch C): always type-aligns, never collation-aligns.
   return RelAlterKind.typeAlter
 -- impl-end
 
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -44,9 +44,12 @@
 def implementation_fkColumnParams
     (fkType : String) (fkCheck : Option String) (targetParams : ColumnParams) :
     ColumnParams := Id.run do
+  -- WRONG (partial-domain): only carries the collation when fkType is nonempty;
+  -- on fkType = "" it leaves collation = none, diverging from the spec there.
   let mut params : ColumnParams :=
     { colType := fkType, checkExpr := fkCheck, collation := none }
-  params := { params with collation := targetParams.collation }
+  if fkType != "" then
+    params := { params with collation := targetParams.collation }
   return params
 -- impl-end
 
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -80,8 +80,10 @@
     (supportsFk oldPk newPk oldUnique newUnique : Bool)
     (oldType newType : String) (oldCollation newCollation : Option String) :
     Bool := Id.run do
+  -- WRONG (control-flow-effect): the pk conjunct drops the newPk guard, so a
+  -- key that was PK only on the old side wrongly triggers a rebuild.
   let mut decision := supportsFk
-  decision := decision && ((oldPk && newPk) || (oldUnique && newUnique))
+  decision := decision && (oldPk || (oldUnique && newUnique))
   decision := decision && ((oldType != newType) || (oldCollation != newCollation))
   return decision
 -- impl-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -115,7 +115,9 @@
 -- impl-start
 def implementation_relatedColumnAlterKind
     (oldRelCollation relCollation : Option String) : RelAlterKind := Id.run do
-  if oldRelCollation != relCollation then
+  -- WRONG (boundary/inverted): uses the collation branch when the collations
+  -- are EQUAL and the type branch when they differ — inverted condition.
+  if oldRelCollation == relCollation then
     return RelAlterKind.collationAlter
   return RelAlterKind.typeAlter
 -- impl-end
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -44,10 +44,10 @@
 def implementation_fkColumnParams
     (fkType : String) (fkCheck : Option String) (targetParams : ColumnParams) :
     ColumnParams := Id.run do
-  let mut params : ColumnParams :=
-    { colType := fkType, checkExpr := fkCheck, collation := none }
-  params := { params with collation := targetParams.collation }
-  return params
+  -- ECHO (equivalent to gold, rewritten): builds the record in one shot with
+  -- the referenced column's collation. Behaviourally identical to the gold fix.
+  return { colType := fkType, checkExpr := fkCheck,
+           collation := targetParams.collation }
 -- impl-end
 
 -- proof-start
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -80,9 +80,12 @@
     (supportsFk oldPk newPk oldUnique newUnique : Bool)
     (oldType newType : String) (oldCollation newCollation : Option String) :
     Bool := Id.run do
+  -- WRONG (inverted collation test): the collation disjunct fires when the
+  -- collations are EQUAL (== instead of !=), so a genuine collation change no
+  -- longer triggers a rebuild by itself.
   let mut decision := supportsFk
   decision := decision && ((oldPk && newPk) || (oldUnique && newUnique))
-  decision := decision && ((oldType != newType) || (oldCollation != newCollation))
+  decision := decision && ((oldType != newType) || (oldCollation == newCollation))
   return decision
 -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. The referenced column's
-- already-computed parameter mapping is taken as an INPUT (grounded data, read
-- directly from the input carrier), and the choice between the two
-- column-alteration strategies is modeled DEEPLY as a sum type below rather than
-- axiomatized. The proof agent may add `_prop` axioms only if it gets stuck.
-- axioms-end

-- pure-start
/-- The database-level parameters describing a single column: its column type
text, an optional check-constraint expression, and an optional collation. -/
structure ColumnParams where
  colType : String
  checkExpr : Option String
  collation : Option String
deriving DecidableEq, Repr

/-- Which strategy is used to re-alter a column that references a key whose
parameters are changing: align its collation, or align its type. -/
inductive RelAlterKind where
  | collationAlter
  | typeAlter
deriving DecidableEq, Repr
-- pure-end

-- post-conditions-start
/-- The parameter mapping for a column that references another column. Its type
text and check expression are its own; its collation is pinned to the collation
of the referenced column's parameter mapping, so a referencing column always
carries the same collation as the column it points at. Every component is pinned
to its input. -/
def problem_spec_fkColumnParams
    (fkType : String) (fkCheck : Option String) (targetParams : ColumnParams)
    (result : ColumnParams) : Prop :=
  result.colType = fkType ∧
  result.checkExpr = fkCheck ∧
  result.collation = targetParams.collation
-- post-conditions-end

-- impl-start
def implementation_fkColumnParams
    (fkType : String) (fkCheck : Option String) (targetParams : ColumnParams) :
    ColumnParams := Id.run do
  let mut params : ColumnParams :=
    { colType := fkType, checkExpr := fkCheck, collation := none }
  params := { params with collation := targetParams.collation }
  return params
-- impl-end

-- proof-start
theorem correct_fkColumnParams :
    ∀ (fkType : String) (fkCheck : Option String) (targetParams : ColumnParams),
    problem_spec_fkColumnParams fkType fkCheck targetParams
      (implementation_fkColumnParams fkType fkCheck targetParams) := by
  intro fkType fkCheck targetParams
  exact ⟨rfl, rfl, rfl⟩
-- proof-end

-- post-conditions-start
/-- Whether incoming references to this key must be torn down and rebuilt while
its parameters change. This is required when the backend supports such
references, the key is a stable primary/unique key on both sides, AND something
the referencing columns must mirror is changing — either the column type or the
collation. The result is determined by all inputs. -/
def problem_spec_rebuildIncomingFks
    (supportsFk oldPk newPk oldUnique newUnique : Bool)
    (oldType newType : String) (oldCollation newCollation : Option String)
    (result : Bool) : Prop :=
  result =
    (supportsFk &&
      ((oldPk && newPk) || (oldUnique && newUnique)) &&
      ((oldType != newType) || (oldCollation != newCollation)))
-- post-conditions-end

-- impl-start
def implementation_rebuildIncomingFks
    (supportsFk oldPk newPk oldUnique newUnique : Bool)
    (oldType newType : String) (oldCollation newCollation : Option String) :
    Bool := Id.run do
  let mut decision := supportsFk
  decision := decision && ((oldPk && newPk) || (oldUnique && newUnique))
  decision := decision && ((oldType != newType) || (oldCollation != newCollation))
  return decision
-- impl-end

-- proof-start
theorem correct_rebuildIncomingFks :
    ∀ (supportsFk oldPk newPk oldUnique newUnique : Bool)
      (oldType newType : String) (oldCollation newCollation : Option String),
    problem_spec_rebuildIncomingFks supportsFk oldPk newPk oldUnique newUnique
      oldType newType oldCollation newCollation
      (implementation_rebuildIncomingFks supportsFk oldPk newPk oldUnique
        newUnique oldType newType oldCollation newCollation) := by
  intro supportsFk oldPk newPk oldUnique newUnique oldType newType oldCollation newCollation
  rfl
-- proof-end

-- post-conditions-start
/-- Which strategy re-aligns a referencing column when the referenced key's
parameters change. When the referencing column's collation differs from what it
should now be, the collation-aligning strategy is used; otherwise the
type-aligning strategy is used. The result is determined by the two collation
inputs. -/
def problem_spec_relatedColumnAlterKind
    (oldRelCollation relCollation : Option String)
    (result : RelAlterKind) : Prop :=
  result =
    (if oldRelCollation != relCollation then RelAlterKind.collationAlter
     else RelAlterKind.typeAlter)
-- post-conditions-end

-- impl-start
def implementation_relatedColumnAlterKind
    (oldRelCollation relCollation : Option String) : RelAlterKind := Id.run do
  if oldRelCollation != relCollation then
    return RelAlterKind.collationAlter
  return RelAlterKind.typeAlter
-- impl-end

-- proof-start
theorem correct_relatedColumnAlterKind :
    ∀ (oldRelCollation relCollation : Option String),
    problem_spec_relatedColumnAlterKind oldRelCollation relCollation
      (implementation_relatedColumnAlterKind oldRelCollation relCollation) := by
  intro oldRelCollation relCollation
  unfold implementation_relatedColumnAlterKind problem_spec_relatedColumnAlterKind
  by_cases h : oldRelCollation != relCollation <;> simp only [h, Id.run, if_true] <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Bundle has THREE tight, total functional postconditions, each pinning every field of its result: (A) problem_spec_fkColumnParams pins all 3 ColumnParams fields (colType=fkType, checkExpr=fkCheck, collation=targetParams.collation); (B) problem_spec_rebuildIncomingFks pins the Bool exactly to the full expression; (C) problem_spec_relatedColumnAlterKind pins the RelAlterKind exactly to the if-then-else. There are NO preconditions. Consequently any implementation whose correct_ theorem closes must compute exactly the gold function pointwise, so its faithful patch necessarily resolves. verify⇒correct holds; no verify⇏correct gap found.

Spec-region byte-identity: same_spec=True for all 8 attacks + positive control (checked via swebench_unified.markers.same_spec with the lean backend). Only impl (and proof) regions edited; axioms/pure/pre/post byte-identical.

8 same-spec wrong/echo impls run through scripts/lean_verify.sh (300s cap):
- atk_1 prepatch-A (fkColumnParams omits collation carry-over): exit 1 (FAILS to verify). Reproduces the prepatch bug for triple 1.
- atk_2 prepatch-B (rebuildIncomingFks drops collation disjunct, only old_type!=new_type): exit 1 (FAILS). Reproduces prepatch bug B.
- atk_3 prepatch-C (relatedColumnAlterKind always typeAlter): exit 1 (FAILS). Reproduces prepatch bug C.
- atk_4 partial-domain (carry collation only when fkType != ""): exit 1 (FAILS).
- atk_5 control-flow-effect (drops newPk guard: oldPk || (oldUnique&&newUnique)): exit 1 (FAILS).
- atk_6 boundary/inverted (collationAlter when collations EQUAL): exit 1 (FAILS).
- atk_8 inverted collation test (oldCollation == newCollation instead of !=): exit 1 (FAILS).
All 7 wrong impls fail — the exact functional specs reject every deviation; the rfl/by_cases proofs no longer close (goal remains open in each log).

- atk_7 ungrounded-oracle ECHO: rewrites triple 1's impl to build ColumnParams in one shot with targetParams.collation — behaviourally identical to gold, byte-identical to gold for triples 2 & 3. lean_verify exit 0 (VERIFIES). Clean axioms: correct_fkColumnParams / correct_rebuildIncomingFks depend on NO axioms; correct_relatedColumnAlterKind depends on [propext] only (standard, from by_cases/simp; identical in gold; no sorryAx/native_decide). Per protocol its faithful refined patch (= gold patch.diff, since impl behaviour is identical) was materialized (atk_7_faithful.patch) and RUN through the official harness: run_resolve('django__django-15629', ...) => RESOLVED: True, COMPLETED: True, FLAKY: False. So the one verifying same-spec impl DOES resolve -> no break.

positive_control (gold impl verbatim): lean_verify exit 0; clean axioms (same propext-only profile). prepatch_reproduced=true (atk_1/atk_2/atk_3 are the three prepatch variants and each correctly FAILS to verify against the postpatch spec).

Exact commands:
  bash scripts/lean_verify.sh <file>   (exit codes above)
  #print axioms appended -> pos_control_ax.lean & atk_7_ax.lean both verify with propext-only.
  python -c 'from swebench_unified.harness import run_resolve; ...'  for atk_7_faithful.patch => RESOLVED True.
Attack verifications launched concurrently as background Bash jobs (<=4 at a time).

refinement.md A-leg audit: axioms region is EMPTY. Every leg is R (type-only refinement) or I (identical concrete op) across all three triples; there are NO A-consumed and NO A-reference legs, hence NO kind-3 (ungrounded axiom/deep-model) leg to attack. axiom_check.py correctly returns status=skip (nothing to check). The grounded-data treatment of targetParams (the referenced column's already-computed db_parameters, read from the input carrier per directive 8) and the sum-type abstraction of the _alter_column_{collation,type}_sql choice (only the branch selection is observed, not the SQL bodies) are both legitimate model-vs-callee correspondences. A-leg / model-patch correspondence audit passes vacuously (no A-legs) and R/I legs match the gold hunks in patch.diff (base_commit 694cf458).

Conclusion: >=5 distinct wrong impls (7 total) all fail to verify; the sole verifying same-spec impl (echo) resolves under the harness; no impl with a closing clean-axiom proof has a non-resolving faithful patch. verify => correct is upheld. VERDICT: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. The referenced column's
-- already-computed parameter mapping is taken as an INPUT (grounded data, read
-- directly from the input carrier), and the choice between the two
-- column-alteration strategies is modeled DEEPLY as a sum type below rather than
-- axiomatized. The proof agent may add `_prop` axioms only if it gets stuck.
-- axioms-end

-- pure-start
/-- The database-level parameters describing a single column: its column type
text, an optional check-constraint expression, and an optional collation. -/
structure ColumnParams where
  colType : String
  checkExpr : Option String
  collation : Option String
deriving DecidableEq, Repr

/-- Which strategy is used to re-alter a column that references a key whose
parameters are changing: align its collation, or align its type. -/
inductive RelAlterKind where
  | collationAlter
  | typeAlter
deriving DecidableEq, Repr
-- pure-end

-- post-conditions-start
/-- The parameter mapping for a column that references another column. Its type
text and check expression are its own; its collation is pinned to the collation
of the referenced column's parameter mapping, so a referencing column always
carries the same collation as the column it points at. Every component is pinned
to its input. -/
def problem_spec_fkColumnParams
    (fkType : String) (fkCheck : Option String) (targetParams : ColumnParams)
    (result : ColumnParams) : Prop :=
  result.colType = fkType ∧
  result.checkExpr = fkCheck ∧
  result.collation = targetParams.collation
-- post-conditions-end

-- impl-start
def implementation_fkColumnParams
    (fkType : String) (fkCheck : Option String) (targetParams : ColumnParams) :
    ColumnParams := Id.run do
  let mut params : ColumnParams :=
    { colType := fkType, checkExpr := fkCheck, collation := none }
  params := { params with collation := targetParams.collation }
  return params
-- impl-end

-- proof-start
theorem correct_fkColumnParams :
    ∀ (fkType : String) (fkCheck : Option String) (targetParams : ColumnParams),
    problem_spec_fkColumnParams fkType fkCheck targetParams
      (implementation_fkColumnParams fkType fkCheck targetParams) := by
  intro fkType fkCheck targetParams
  exact ⟨rfl, rfl, rfl⟩
-- proof-end

-- post-conditions-start
/-- Whether incoming references to this key must be torn down and rebuilt while
its parameters change. This is required when the backend supports such
references, the key is a stable primary/unique key on both sides, AND something
the referencing columns must mirror is changing — either the column type or the
collation. The result is determined by all inputs. -/
def problem_spec_rebuildIncomingFks
    (supportsFk oldPk newPk oldUnique newUnique : Bool)
    (oldType newType : String) (oldCollation newCollation : Option String)
    (result : Bool) : Prop :=
  result =
    (supportsFk &&
      ((oldPk && newPk) || (oldUnique && newUnique)) &&
      ((oldType != newType) || (oldCollation != newCollation)))
-- post-conditions-end

-- impl-start
def implementation_rebuildIncomingFks
    (supportsFk oldPk newPk oldUnique newUnique : Bool)
    (oldType newType : String) (oldCollation newCollation : Option String) :
    Bool := Id.run do
  let mut decision := supportsFk
  decision := decision && ((oldPk && newPk) || (oldUnique && newUnique))
  decision := decision && ((oldType != newType) || (oldCollation != newCollation))
  return decision
-- impl-end

-- proof-start
theorem correct_rebuildIncomingFks :
    ∀ (supportsFk oldPk newPk oldUnique newUnique : Bool)
      (oldType newType : String) (oldCollation newCollation : Option String),
    problem_spec_rebuildIncomingFks supportsFk oldPk newPk oldUnique newUnique
      oldType newType oldCollation newCollation
      (implementation_rebuildIncomingFks supportsFk oldPk newPk oldUnique
        newUnique oldType newType oldCollation newCollation) := by
  intro supportsFk oldPk newPk oldUnique newUnique oldType newType oldCollation newCollation
  rfl
-- proof-end

-- post-conditions-start
/-- Which strategy re-aligns a referencing column when the referenced key's
parameters change. When the referencing column's collation differs from what it
should now be, the collation-aligning strategy is used; otherwise the
type-aligning strategy is used. The result is determined by the two collation
inputs. -/
def problem_spec_relatedColumnAlterKind
    (oldRelCollation relCollation : Option String)
    (result : RelAlterKind) : Prop :=
  result =
    (if oldRelCollation != relCollation then RelAlterKind.collationAlter
     else RelAlterKind.typeAlter)
-- post-conditions-end

-- impl-start
def implementation_relatedColumnAlterKind
    (oldRelCollation relCollation : Option String) : RelAlterKind := Id.run do
  if oldRelCollation != relCollation then
    return RelAlterKind.collationAlter
  return RelAlterKind.typeAlter
-- impl-end

-- proof-start
theorem correct_relatedColumnAlterKind :
    ∀ (oldRelCollation relCollation : Option String),
    problem_spec_relatedColumnAlterKind oldRelCollation relCollation
      (implementation_relatedColumnAlterKind oldRelCollation relCollation) := by
  intro oldRelCollation relCollation
  unfold implementation_relatedColumnAlterKind problem_spec_relatedColumnAlterKind
  by_cases h : oldRelCollation != relCollation <;> simp only [h, Id.run, if_true] <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Bundle has THREE tight, total functional postconditions, each pinning every field of its result: (A) problem_spec_fkColumnParams pins all 3 ColumnParams fields (colType=fkType, checkExpr=fkCheck, collation=targetParams.collation); (B) problem_spec_rebuildIncomingFks pins the Bool exactly to the full expression; (C) problem_spec_relatedColumnAlterKind pins the RelAlterKind exactly to the if-then-else. There are NO preconditions. Consequently any implementation whose correct_ theorem closes must compute exactly the gold function pointwise, so its faithful patch necessarily resolves. verify⇒correct holds; no verify⇏correct gap found.

Spec-region byte-identity: same_spec=True for all 8 attacks + positive control (checked via swebench_unified.markers.same_spec with the lean backend). Only impl (and proof) regions edited; axioms/pure/pre/post byte-identical.

8 same-spec wrong/echo impls run through scripts/lean_verify.sh (300s cap):
- atk_1 prepatch-A (fkColumnParams omits collation carry-over): exit 1 (FAILS to verify). Reproduces the prepatch bug for triple 1.
- atk_2 prepatch-B (rebuildIncomingFks drops collation disjunct, only old_type!=new_type): exit 1 (FAILS). Reproduces prepatch bug B.
- atk_3 prepatch-C (relatedColumnAlterKind always typeAlter): exit 1 (FAILS). Reproduces prepatch bug C.
- atk_4 partial-domain (carry collation only when fkType != ""): exit 1 (FAILS).
- atk_5 control-flow-effect (drops newPk guard: oldPk || (oldUnique&&newUnique)): exit 1 (FAILS).
- atk_6 boundary/inverted (collationAlter when collations EQUAL): exit 1 (FAILS).
- atk_8 inverted collation test (oldCollation == newCollation instead of !=): exit 1 (FAILS).
All 7 wrong impls fail — the exact functional specs reject every deviation; the rfl/by_cases proofs no longer close (goal remains open in each log).

- atk_7 ungrounded-oracle ECHO: rewrites triple 1's impl to build ColumnParams in one shot with targetParams.collation — behaviourally identical to gold, byte-identical to gold for triples 2 & 3. lean_verify exit 0 (VERIFIES). Clean axioms: correct_fkColumnParams / correct_rebuildIncomingFks depend on NO axioms; correct_relatedColumnAlterKind depends on [propext] only (standard, from by_cases/simp; identical in gold; no sorryAx/native_decide). Per protocol its faithful refined patch (= gold patch.diff, since impl behaviour is identical) was materialized (atk_7_faithful.patch) and RUN through the official harness: run_resolve('django__django-15629', ...) => RESOLVED: True, COMPLETED: True, FLAKY: False. So the one verifying same-spec impl DOES resolve -> no break.

positive_control (gold impl verbatim): lean_verify exit 0; clean axioms (same propext-only profile). prepatch_reproduced=true (atk_1/atk_2/atk_3 are the three prepatch variants and each correctly FAILS to verify against the postpatch spec).

Exact commands:
  bash scripts/lean_verify.sh <file>   (exit codes above)
  #print axioms appended -> pos_control_ax.lean & atk_7_ax.lean both verify with propext-only.
  python -c 'from swebench_unified.harness import run_resolve; ...'  for atk_7_faithful.patch => RESOLVED True.
Attack verifications launched concurrently as background Bash jobs (<=4 at a time).

refinement.md A-leg audit: axioms region is EMPTY. Every leg is R (type-only refinement) or I (identical concrete op) across all three triples; there are NO A-consumed and NO A-reference legs, hence NO kind-3 (ungrounded axiom/deep-model) leg to attack. axiom_check.py correctly returns status=skip (nothing to check). The grounded-data treatment of targetParams (the referenced column's already-computed db_parameters, read from the input carrier per directive 8) and the sum-type abstraction of the _alter_column_{collation,type}_sql choice (only the branch selection is observed, not the SQL bodies) are both legitimate model-vs-callee correspondences. A-leg / model-patch correspondence audit passes vacuously (no A-legs) and R/I legs match the gold hunks in patch.diff (base_commit 694cf458).

Conclusion: >=5 distinct wrong impls (7 total) all fail to verify; the sole verifying same-spec impl (echo) resolves under the harness; no impl with a closing clean-axiom proof has a non-resolving faithful patch. verify => correct is upheld. VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack found no divergence. Verified against the real post-patch callee (base_commit 694cf458... worktree with gold patch.diff applied). Three modeled decisions all match the real repo exactly:

A) problem_spec_fkColumnParams ↔ ForeignKey.db_parameters (related.py:1182-1187 post-patch): returns {type: db_type, check: db_check, collation: target_db_parameters.get('collation')}. Spec pins result.colType=fkType, result.checkExpr=fkCheck, result.collation=targetParams.collation. target_field.db_parameters is faithfully taken as an INPUT carrier (grounded data); dict.get('collation') absent→None ↔ Option.none. Exact.

B) problem_spec_rebuildIncomingFks ↔ drop_foreign_keys predicate (base/schema.py:828-835 post-patch): supports_foreign_keys and ((old_pk and new_pk) or (old_unique and new_unique)) and ((old_type != new_type) or (old_collation != new_collation)). Spec is the byte-for-byte boolean with and/or↔&&/|| and !=↔!=. Bool attribute reads modeled as Bool inputs, str/str|None comparisons via Lean BEq (structural, matches Python == on str and Option; '' vs None kept distinct). Exact.

C) problem_spec_relatedColumnAlterKind ↔ rels_to_update loop (base/schema.py:1044-1057 post-patch): if old_rel_collation != rel_collation -> _alter_column_collation_sql branch else _alter_column_type_sql branch. Spec: if oldRelCollation != relCollation then collationAlter else typeAlter. The which-branch decision is exactly modeled; the two SQL-helper callees are correctly NOT modeled internally (not the observed decision) and abstracted to the RelAlterKind sum. Exact.

Evidence: lean_verify exit 0 (no sorry); #print axioms clean (only propext, no sorryAx); same_spec(Solution, prepatch_{A,B,C}) all True (spec region byte-identical); conformance_check.py 120k fuzzed inputs 0 disagreements. No input exists where the modeled function disagrees with the real callee; spec is not too strong and does not drift.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `conformance_check.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Rendered the consumer spec view via markers.spec_view (lean backend): impl+proof regions elided; only the axioms comment, pure types (ColumnParams, RelAlterKind), and three problem_spec_* post-conditions with docstrings pass through. Mechanical leakage.screen() PASSES (no diff markers, no reproduced gold-patch line >=8 chars, no patched file/module path, no spec-view identifier or comment echoing a patched repo symbol, no bug/fix narration). same_spec(Solution, prepatch_{A,B,C}) all True — spec region is stable/parses. Semantic check: (1) post_spec_fkColumnParams (fk collation pinned to referenced column's collation) is EXPLICITLY disclosed by the public problem_statement ('the collation of the pk must match the collation of the fk otherwise an error will occur', plus the shown COLLATE additions on the account_id MODIFY statements). (2) rebuildIncomingFks (rebuild on type-OR-collation change) and (3) relatedColumnAlterKind (collation-align vs type-align branch) are abstracted DB-schema-level correctness constraints that formalize WHAT correct behavior is — inherent to any spec, not a disclosure of the gold code edit. Crucially, no Django/solution identifiers (db_parameters, target_field, drop_foreign_keys, supports_foreign_keys, _alter_column_collation_sql, _alter_column_type_sql) and no file paths/diff content appear anywhere in the spec view; those repo specifics live only in mapping.md/refinement.md, which are audit artifacts NOT part of the leak-screened consumer spec view (leak.py screens solution_src's spec_view only, per SPEC_GUIDE). No relaxed_leakage flag / RELAXED_LEAKAGE.md, so strict judgment applies. The spec view reveals nothing about the gold edit's location, approach, or symbols beyond what solving the publicly-stated problem inherently requires.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
