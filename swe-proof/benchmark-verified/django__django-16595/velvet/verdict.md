# P2 adversarial audit — django__django-16595

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 9 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. No same-spec wrong impl verifies, so no faithful patch needed materializing/resolving.
```

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 /- No consumed axioms and no deep-model references. The decision the desired
@@ -73,7 +73,7 @@
   ensures out = reduceDecision op
   do
     -- impl-start
-    if (op.incomingIsAlter || op.incomingIsRemove) && op.sameField then
+    if op.incomingIsRemove && op.sameField then
       return ReduceResult.keepLater
     else
       return ReduceResult.deferToInherited
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 /- No consumed axioms and no deep-model references. The decision the desired
@@ -73,10 +73,7 @@
   ensures out = reduceDecision op
   do
     -- impl-start
-    if (op.incomingIsAlter || op.incomingIsRemove) && op.sameField then
-      return ReduceResult.keepLater
-    else
-      return ReduceResult.deferToInherited
+    return ReduceResult.deferToInherited
     -- impl-end
 
 prove_correct reduceAlterField by
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 /- No consumed axioms and no deep-model references. The decision the desired
@@ -73,10 +73,7 @@
   ensures out = reduceDecision op
   do
     -- impl-start
-    if (op.incomingIsAlter || op.incomingIsRemove) && op.sameField then
-      return ReduceResult.keepLater
-    else
-      return ReduceResult.deferToInherited
+    return ReduceResult.keepLater
     -- impl-end
 
 prove_correct reduceAlterField by
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 /- No consumed axioms and no deep-model references. The decision the desired
@@ -73,7 +73,7 @@
   ensures out = reduceDecision op
   do
     -- impl-start
-    if (op.incomingIsAlter || op.incomingIsRemove) && op.sameField then
+    if (op.incomingIsAlter || op.incomingIsRemove) then
       return ReduceResult.keepLater
     else
       return ReduceResult.deferToInherited
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 /- No consumed axioms and no deep-model references. The decision the desired
@@ -73,7 +73,7 @@
   ensures out = reduceDecision op
   do
     -- impl-start
-    if (op.incomingIsAlter || op.incomingIsRemove) && op.sameField then
+    if (op.incomingIsAlter && op.incomingIsRemove) && op.sameField then
       return ReduceResult.keepLater
     else
       return ReduceResult.deferToInherited
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 /- No consumed axioms and no deep-model references. The decision the desired
@@ -73,7 +73,7 @@
   ensures out = reduceDecision op
   do
     -- impl-start
-    if (op.incomingIsAlter || op.incomingIsRemove) && op.sameField then
+    if op.sameField then
       return ReduceResult.keepLater
     else
       return ReduceResult.deferToInherited
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 /- No consumed axioms and no deep-model references. The decision the desired
@@ -74,9 +74,9 @@
   do
     -- impl-start
     if (op.incomingIsAlter || op.incomingIsRemove) && op.sameField then
+      return ReduceResult.deferToInherited
+    else
       return ReduceResult.keepLater
-    else
-      return ReduceResult.deferToInherited
     -- impl-end
 
 prove_correct reduceAlterField by
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 /- No consumed axioms and no deep-model references. The decision the desired
@@ -73,7 +73,7 @@
   ensures out = reduceDecision op
   do
     -- impl-start
-    if (op.incomingIsAlter || op.incomingIsRemove) && op.sameField then
+    if op.incomingIsAlter && op.sameField then
       return ReduceResult.keepLater
     else
       return ReduceResult.deferToInherited
```

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 /- No consumed axioms and no deep-model references. The decision the desired
@@ -73,7 +73,7 @@
   ensures out = reduceDecision op
   do
     -- impl-start
-    if (op.incomingIsAlter || op.incomingIsRemove) && op.sameField then
+    if op.sameField && (op.incomingIsRemove || op.incomingIsAlter) then
       return ReduceResult.keepLater
     else
       return ReduceResult.deferToInherited
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no deep-model references. The decision the desired
   behaviour concerns — whether one alteration of a model field is superseded by
   the step that immediately follows it — is modeled directly in the `pure`
   region (`reduceDecision`) from observable booleans about that following step.
   Every situation the modeled decision does not collapse is left to the
   pre-existing combining dispatch via the abstract tag
   `ReduceResult.deferToInherited`; that dispatch's concrete outcome is
   independent of the desired behaviour and is exercised against the real
   reducer by G-CONF (conformance_check.py). Nothing is axiomatized. -/
-- axioms-end

-- pure-start
/- What the reducer observes about the step that immediately follows this
   alteration when deciding whether the two can be combined into the later one.
   * `incomingIsAlter`  — the following step is itself an alteration of a model
                          field's definition.
   * `incomingIsRemove` — the following step removes a model field.
   * `sameField`        — the following step targets the same model field (same
                          model, same field name) as this alteration. -/
structure ReduceInput where
  incomingIsAlter  : Bool
  incomingIsRemove : Bool
  sameField        : Bool
  deriving DecidableEq, Inhabited

/- The reducer's decision for one (this-alteration, following-step) pair.
   * `keepLater`        — the two collapse: this alteration is dropped and only
                          the following step is kept.
   * `deferToInherited` — no special combination applies, so the decision is
                          left to the pre-existing combining dispatch (whose
                          concrete result is independent of the desired
                          behaviour). -/
inductive ReduceResult where
  | keepLater
  | deferToInherited
  deriving DecidableEq, Inhabited

/- The desired behaviour: when the following step acts on the SAME model field
   and is either another alteration of that field or its removal, the earlier
   alteration is redundant and the pair collapses onto the later step alone; in
   every other case the decision is left to the pre-existing combining dispatch.
   The redundancy of one alteration followed by another on the same field is the
   behaviour the desired change adds. -/
def reduceDecision (op : ReduceInput) : ReduceResult :=
  if (op.incomingIsAlter || op.incomingIsRemove) && op.sameField then
    ReduceResult.keepLater
  else
    ReduceResult.deferToInherited
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Decide how an alteration of a model field combines with the step that
   immediately follows it, given only what the reducer observes about that
   following step (`op`). `op` is read-only — the decision mutates nothing
   (directive 5). The pair collapses onto the later step precisely when that
   following step acts on the same field and is either another alteration of it
   or its removal; otherwise the pre-existing combining dispatch decides. -/
method reduceAlterField (op : ReduceInput) return (out : ReduceResult)
  ensures out = reduceDecision op
  do
    -- impl-start
    if (op.incomingIsAlter || op.incomingIsRemove) && op.sameField then
      return ReduceResult.keepLater
    else
      return ReduceResult.deferToInherited
    -- impl-end

prove_correct reduceAlterField by
  loom_solve <;> simp_all [reduceDecision]
```

Prepatch bug re-encoded as an attack: `True`.

Spec structure: postcondition is `ensures out = reduceDecision op` with `reduceDecision` a TOTAL, fully-concrete frozen pure function and an EMPTY pre-conditions region. Under same_spec (axioms/pure/pre/post byte-identical) any verifying impl must be extensionally equal to reduceDecision across the entire ReduceInput domain — no partial-domain/boundary/oracle escape exists. This is the structural reason verify⇒behavioral-correctness here.

Protocol run. same_spec confirmed True for all 10 files via swebench_unified.markers.same_spec (velvet). Verification cmd per file: `bash scripts/lean_verify.sh <file>`; run concurrently in batches of 4.

Results:
- pos_control.lean (gold impl): exit 0 = VERIFIES (positive control OK).
- atk_1.lean prepatch bug, RemoveField-only first branch: exit 1 (fails on incomingIsAlter∧sameField∧¬incomingIsRemove goal — bug reproduced).
- atk_2.lean always deferToInherited: exit 1.
- atk_3.lean always keepLater: exit 1.
- atk_4.lean drop sameField guard: exit 1.
- atk_5.lean AND kinds instead of OR: exit 1.
- atk_6.lean sameField only (ignore kinds): exit 1.
- atk_7.lean swapped branches (control-flow-effect): exit 1.
- atk_8.lean alter-only, drops remove (partial-domain): exit 1.
- atk_9.lean ungrounded-oracle echo, reordered conjuncts (semantically EQUAL to gold): exit 1 — fails only on prove_correct proof-script brittleness; it is actually a CORRECT impl, so even had it verified it would not be a verify⇏correct witness.

prepatch.lean (Solution_prepatch.lean, copied): exit 1 — reproduces the gold bug at the same-field-alteration case (F2P test_alter_alter_field).

No wrong impl verified. The protocol's resolve obligation (materialize + run_resolve faithful patch) is conditional on a verifying wrong impl; none exists, so patches={} and no resolve run was required or possible. Not INCONCLUSIVE: all ≥5 attacks completed with definite verify verdicts and the positive control verifies.

Axiom/refinement audit: no `axiom`/`sorry`/`admit`/`opaque` anywhere in Solution.lean (axioms region is prose-only, declaring no consumed axioms and no deep-model references). refinement.md legs A1–A6 are all R/I; no A-consumed, no A-reference, no kind-3. The single changed op (isinstance kind-tuple widening RemoveField -> (AlterField,RemoveField)) is modeled IDENTICALLY as the incomingIsAlter disjunct of reduceDecision, not hidden behind an axiom. Correspondence to real callees holds: incomingIsAlter↔isinstance(operation,AlterField), incomingIsRemove↔isinstance(operation,RemoveField), sameField↔self.is_same_field_operation(operation), keepLater↔return [operation], deferToInherited↔every other return. mapping.md §2 bijection is consistent and G-CONF-falsifiable.

Conclusion: SOUND — verify⇒correct holds for this bundle; no falsification found across 9 distinct wrong/echo impls.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 9 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. No same-spec wrong impl verifies, so no faithful patch needed materializing/resolving.
```

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 9 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no deep-model references. The decision the desired
   behaviour concerns — whether one alteration of a model field is superseded by
   the step that immediately follows it — is modeled directly in the `pure`
   region (`reduceDecision`) from observable booleans about that following step.
   Every situation the modeled decision does not collapse is left to the
   pre-existing combining dispatch via the abstract tag
   `ReduceResult.deferToInherited`; that dispatch's concrete outcome is
   independent of the desired behaviour and is exercised against the real
   reducer by G-CONF (conformance_check.py). Nothing is axiomatized. -/
-- axioms-end

-- pure-start
/- What the reducer observes about the step that immediately follows this
   alteration when deciding whether the two can be combined into the later one.
   * `incomingIsAlter`  — the following step is itself an alteration of a model
                          field's definition.
   * `incomingIsRemove` — the following step removes a model field.
   * `sameField`        — the following step targets the same model field (same
                          model, same field name) as this alteration. -/
structure ReduceInput where
  incomingIsAlter  : Bool
  incomingIsRemove : Bool
  sameField        : Bool
  deriving DecidableEq, Inhabited

/- The reducer's decision for one (this-alteration, following-step) pair.
   * `keepLater`        — the two collapse: this alteration is dropped and only
                          the following step is kept.
   * `deferToInherited` — no special combination applies, so the decision is
                          left to the pre-existing combining dispatch (whose
                          concrete result is independent of the desired
                          behaviour). -/
inductive ReduceResult where
  | keepLater
  | deferToInherited
  deriving DecidableEq, Inhabited

/- The desired behaviour: when the following step acts on the SAME model field
   and is either another alteration of that field or its removal, the earlier
   alteration is redundant and the pair collapses onto the later step alone; in
   every other case the decision is left to the pre-existing combining dispatch.
   The redundancy of one alteration followed by another on the same field is the
   behaviour the desired change adds. -/
def reduceDecision (op : ReduceInput) : ReduceResult :=
  if (op.incomingIsAlter || op.incomingIsRemove) && op.sameField then
    ReduceResult.keepLater
  else
    ReduceResult.deferToInherited
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Decide how an alteration of a model field combines with the step that
   immediately follows it, given only what the reducer observes about that
   following step (`op`). `op` is read-only — the decision mutates nothing
   (directive 5). The pair collapses onto the later step precisely when that
   following step acts on the same field and is either another alteration of it
   or its removal; otherwise the pre-existing combining dispatch decides. -/
method reduceAlterField (op : ReduceInput) return (out : ReduceResult)
  ensures out = reduceDecision op
  do
    -- impl-start
    if (op.incomingIsAlter || op.incomingIsRemove) && op.sameField then
      return ReduceResult.keepLater
    else
      return ReduceResult.deferToInherited
    -- impl-end

prove_correct reduceAlterField by
  loom_solve <;> simp_all [reduceDecision]
```

Prepatch bug re-encoded as an attack: `True`.

Spec structure: postcondition is `ensures out = reduceDecision op` with `reduceDecision` a TOTAL, fully-concrete frozen pure function and an EMPTY pre-conditions region. Under same_spec (axioms/pure/pre/post byte-identical) any verifying impl must be extensionally equal to reduceDecision across the entire ReduceInput domain — no partial-domain/boundary/oracle escape exists. This is the structural reason verify⇒behavioral-correctness here.

Protocol run. same_spec confirmed True for all 10 files via swebench_unified.markers.same_spec (velvet). Verification cmd per file: `bash scripts/lean_verify.sh <file>`; run concurrently in batches of 4.

Results:
- pos_control.lean (gold impl): exit 0 = VERIFIES (positive control OK).
- atk_1.lean prepatch bug, RemoveField-only first branch: exit 1 (fails on incomingIsAlter∧sameField∧¬incomingIsRemove goal — bug reproduced).
- atk_2.lean always deferToInherited: exit 1.
- atk_3.lean always keepLater: exit 1.
- atk_4.lean drop sameField guard: exit 1.
- atk_5.lean AND kinds instead of OR: exit 1.
- atk_6.lean sameField only (ignore kinds): exit 1.
- atk_7.lean swapped branches (control-flow-effect): exit 1.
- atk_8.lean alter-only, drops remove (partial-domain): exit 1.
- atk_9.lean ungrounded-oracle echo, reordered conjuncts (semantically EQUAL to gold): exit 1 — fails only on prove_correct proof-script brittleness; it is actually a CORRECT impl, so even had it verified it would not be a verify⇏correct witness.

prepatch.lean (Solution_prepatch.lean, copied): exit 1 — reproduces the gold bug at the same-field-alteration case (F2P test_alter_alter_field).

No wrong impl verified. The protocol's resolve obligation (materialize + run_resolve faithful patch) is conditional on a verifying wrong impl; none exists, so patches={} and no resolve run was required or possible. Not INCONCLUSIVE: all ≥5 attacks completed with definite verify verdicts and the positive control verifies.

Axiom/refinement audit: no `axiom`/`sorry`/`admit`/`opaque` anywhere in Solution.lean (axioms region is prose-only, declaring no consumed axioms and no deep-model references). refinement.md legs A1–A6 are all R/I; no A-consumed, no A-reference, no kind-3. The single changed op (isinstance kind-tuple widening RemoveField -> (AlterField,RemoveField)) is modeled IDENTICALLY as the incomingIsAlter disjunct of reduceDecision, not hidden behind an axiom. Correspondence to real callees holds: incomingIsAlter↔isinstance(operation,AlterField), incomingIsRemove↔isinstance(operation,RemoveField), sameField↔self.is_same_field_operation(operation), keepLater↔return [operation], deferToInherited↔every other return. mapping.md §2 bijection is consistent and G-CONF-falsifiable.

Conclusion: SOUND — verify⇒correct holds for this bundle; no falsification found across 9 distinct wrong/echo impls.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) attack on django__django-16595 velvet bundle. FINDINGS: (1) Spec region is byte-identical between Solution.lean and Solution_prepatch.lean per swebench_unified.markers.same_spec with VelvetBackend.language => True. Frozen SPEC = the ReduceInput/ReduceResult types, reduceDecision, and the method signature `reduceAlterField (op) return (out) ensures out = reduceDecision op`. (2) Solution.lean elaborates and proves clean: scripts/lean_verify.sh exits 0. (3) The modeled function reduceDecision op = if (incomingIsAlter ∨ incomingIsRemove) ∧ sameField then keepLater else deferToInherited is EXACTLY the post-patch first branch `isinstance(operation, (AlterField, RemoveField)) and self.is_same_field_operation(operation): return [operation]`, with the keepLater observable defined as 'reduce returns exactly [operation]' and everything else = deferToInherited.

DIRECT DIFFERENTIAL TEST against the REAL repo (worktree at base_commit f9fe062, gold patch applied): ran conformance_check.py with using the real patched AlterField.reduce => 'G-CONF OK ... 0 disagreements' over 120,008 inputs (seed 16595). Additionally ran an independent exhaustive probe over {AlterField,RemoveField,RenameField,AddField} × {same/diff model 'Book'/'book'/'Author'} × {same/diff field 'title'/'TITLE'/'name'} = 36 realizable operation objects directly against the real reducer: 0 disagreements.

OVER-STRENGTH / DRIFT ANALYSIS: The spec does not over-constrain. The only fall-through path by which the real reducer could return [operation] outside the first branch is super().reduce when self.elidable or operation.elidable; verified Operation.elidable class default is False and AlterField exposes no elidable constructor param, so AlterField instances are never elidable — that path cannot produce a spurious keepLater. RenameField same-field returns a 2-element list (deferToInherited, matches); db_column-set self path returns False (deferToInherited, matches); CreateModel/AddField => deferToInherited (matches). The abstract deferToInherited tag asserts nothing about the unchanged dispatch, so the ensures clause is not stronger than the real behavior anywhere. The prepatch model (removal-only first branch) correctly FAILS `out = reduceDecision op` exactly at incomingIsAlter ∧ sameField ∧ ¬incomingIsRemove (the F2P test_alter_alter_field), confirming the spec is falsifiable and correctly discriminating. No diverging input exists between the modeled function and the real callee. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view built via markers.spec_view (velvet flavor): impl region elided to 'implementation elided', prove_correct body elided to 'proof elided'. same_spec(Solution.lean, Solution_prepatch.lean)=True (spec region byte-identical). Mechanical leakage.screen passes (hard_failures=[]).

Semantic review of what the spec view exposes vs. the PUBLIC problem_statement (not hints_text):
- Gold edit (patch.diff): AlterField.reduce first-branch kind test widened from `RemoveField` to `(AlterField, RemoveField)`, so a following same-field AlterField collapses onto the later op (return [operation]).
- The problem_statement ALREADY discloses the entire edit: it names the migration optimizer + AlterField, states plainly 'the AlterField.reduce does not consider the case where operation is also an AlterField', and literally prints the proposed fix `if isinstance(operation, AlterField) and self.is_same_field_operation(operation): return [operation]`.
- The spec view's discriminating content (reduceDecision: collapse when (incomingIsAlter || incomingIsRemove) && sameField) models exactly this and adds nothing beyond the public statement. The 'incomingIsRemove'/removal element is unchanged pre-existing Django behaviour, not the discriminating change; the alter-follows-alter same-field collapse — the actual gold delta — is already fully spelled out in problem_statement.
- No gold-patch-specific artifact (the `(AlterField, RemoveField)` tuple spelling, `is_same_field_operation` call site, patch hunk structure) is present in the spec view beyond what the public statement gives. Comments are abstract ('following step', 'collapses onto the later step'). No leak of the gold discriminator beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
