# P2 adversarial audit — django__django-15268

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_correct.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. All 7 same-spec wrong impls FAIL Lean verification (exit 1, 'unsolved goals' at the prove_correct sites), so no verifying wrong impl exists and there is no faithful patch to run through run_resolve. verify=>correct is not falsifiable for this bundle.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -119,7 +119,7 @@
   do
     -- impl-start
     let base ← reorderableBase selfName other
-    return base || (isTogetherOp other && !sameKind selfKind other)
+    return base
     -- impl-end
 
 prove_correct reorderableTogether by
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -100,7 +100,7 @@
   ensures result = (!affectsModel selfName other)
   do
     -- impl-start
-    return !affectsModel selfName other
+    return affectsModel selfName other
     -- impl-end
 
 prove_correct reorderableBase by
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -119,7 +119,7 @@
   do
     -- impl-start
     let base ← reorderableBase selfName other
-    return base || (isTogetherOp other && !sameKind selfKind other)
+    return base || (isTogetherOp other && sameKind selfKind other)
     -- impl-end
 
 prove_correct reorderableTogether by
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -140,8 +140,8 @@
     -- impl-start
     let canReorder ← reorderableTogether selfName selfKind other
     let r := if mergeable selfName selfKind other then OptimizeOutcome.merge
-             else (if canReorder then OptimizeOutcome.reorderable
-                   else OptimizeOutcome.blocked)
+             else (if canReorder then OptimizeOutcome.blocked
+                   else OptimizeOutcome.reorderable)
     return r
     -- impl-end
 
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -138,10 +138,9 @@
                           else OptimizeOutcome.blocked))
   do
     -- impl-start
-    let canReorder ← reorderableTogether selfName selfKind other
+    let _canReorder ← reorderableTogether selfName selfKind other
     let r := if mergeable selfName selfKind other then OptimizeOutcome.merge
-             else (if canReorder then OptimizeOutcome.reorderable
-                   else OptimizeOutcome.blocked)
+             else OptimizeOutcome.reorderable
     return r
     -- impl-end
 
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -138,7 +138,7 @@
                           else OptimizeOutcome.blocked))
   do
     -- impl-start
-    let canReorder ← reorderableTogether selfName selfKind other
+    let canReorder ← reorderableBase selfName other
     let r := if mergeable selfName selfKind other then OptimizeOutcome.merge
              else (if canReorder then OptimizeOutcome.reorderable
                    else OptimizeOutcome.blocked)
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -119,7 +119,7 @@
   do
     -- impl-start
     let base ← reorderableBase selfName other
-    return base || (isTogetherOp other && !sameKind selfKind other)
+    return base || !sameKind selfKind other
     -- impl-end
 
 prove_correct reorderableTogether by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_correct.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The only facts the modeled decision consults about a
--  non-modeled operation — "does this neighbouring operation touch my model?"
--  and "is it marked elidable?" — are UNCHANGED and are carried as FREE INPUTS
--  (`OtherOp.generic refsSelf elidable`), so the spec makes no behavioural
--  claim about them and holds for every value. Nothing requires validation
--  against a real callee, hence no G-AX.)
-- axioms-end

-- pure-start
/- The two flavours of "together" model-option an operation may target. Only the
   flavour is ever observed (whether two such operations target the SAME flavour
   or DIFFERENT flavours of the same model). -/
inductive TogetherKind where
  | unique
  | index
  deriving DecidableEq, Inhabited, BEq

/- A neighbouring migration operation, abstracted to exactly the features the
   eligibility decision observes:
   * `together name kind` — an Alter{Unique,Index}Together operation on model
     `name` of flavour `kind` (such operations are never marked elidable);
   * `deleteModel name`   — a delete-model operation on model `name` (never
     marked elidable);
   * `generic refsSelf elidable` — any other operation, carrying only the two
     (free, unchanged) answers the decision observes: "does it touch my
     model?" and "is it marked elidable?" (an elidable neighbour is one the
     optimizer may silently drop, collapsing the pair to my operation alone —
     a merge). -/
inductive OtherOp where
  | together (name : Nat) (kind : TogetherKind)
  | deleteModel (name : Nat)
  | generic (refsSelf : Bool) (elidable : Bool)
  deriving DecidableEq, Inhabited

/- The result of asking whether one operation can be combined with / advanced
   past a neighbouring one:
   * `merge`       — the two collapse into one;
   * `reorderable` — they are independent, so the first may be advanced past the
     second while the optimizer keeps looking for a merge;
   * `blocked`     — neither; a boundary the optimizer cannot cross. -/
inductive OptimizeOutcome where
  | merge
  | reorderable
  | blocked
  deriving DecidableEq, Inhabited

/- "Does the neighbouring operation touch my model `selfName`?" For an
   Alter…Together operation this is name identity (model names compared for
   equality). A delete-model operation conservatively touches EVERY model (a
   deleted model may reference any other through its relations), so it always
   answers yes. For any other operation it is the free, unchanged answer carried
   on the operation. -/
def affectsModel (selfName : Nat) : OtherOp → Bool
  | .together name _    => name == selfName
  | .deleteModel _      => true
  | .generic refsSelf _ => refsSelf

/- Is the neighbouring operation one of the together-option operations? -/
def isTogetherOp : OtherOp → Bool
  | .together _ _ => true
  | _             => false

/- Is the neighbouring operation a together-option operation of the SAME flavour
   as mine? -/
def sameKind (selfKind : TogetherKind) : OtherOp → Bool
  | .together _ kind => kind == selfKind
  | _                => false

/- Do my operation and the neighbour collapse into one? This happens exactly
   when the neighbour is a together-option operation of MY flavour on MY model,
   a delete of MY model, or any other operation marked elidable (the optimizer
   silently drops an elidable neighbour, leaving just my operation — the pair
   becomes one). Together-option and delete-model operations are never marked
   elidable, so the elidable answer is carried only on `generic`. -/
def mergeable (selfName : Nat) (selfKind : TogetherKind) : OtherOp → Bool
  | .together name kind  => kind == selfKind && name == selfName
  | .deleteModel name    => name == selfName
  | .generic _ elidable  => elidable
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The baseline independence test shared by every model operation: an operation
   may be advanced past a neighbour exactly when that neighbour does not touch
   its model. `selfName`, `other` are read-only (directive 5). -/
method reorderableBase (selfName : Nat) (other : OtherOp) return (result : Bool)
  ensures result = (!affectsModel selfName other)
  do
    -- impl-start
    return !affectsModel selfName other
    -- impl-end

prove_correct reorderableBase by
  loom_solve

/- The independence test specialised to a together-option operation. It widens
   the baseline test: such an operation is ALSO independent of a together-option
   neighbour of a DIFFERENT flavour on the same model — the two constrain
   disjoint kinds of model option, so the optimizer may advance one past the
   other (which is what later lets a remove/re-add pair on each flavour collapse
   to a single operation). `selfName`, `selfKind`, `other` are read-only. -/
method reorderableTogether (selfName : Nat) (selfKind : TogetherKind) (other : OtherOp)
    return (result : Bool)
  ensures result = ((!affectsModel selfName other) ||
                    (isTogetherOp other && !sameKind selfKind other))
  do
    -- impl-start
    let base ← reorderableBase selfName other
    return base || (isTogetherOp other && !sameKind selfKind other)
    -- impl-end

prove_correct reorderableTogether by
  loom_solve

/- The full eligibility verdict an Alter…Together operation reaches against a
   neighbour: it merges with a same-flavour together (or a delete) on its model;
   otherwise it is reorderable iff the independence test above holds; otherwise
   it is blocked. `selfName`, `selfKind`, `other` are read-only. -/
method optimizeAgainst (selfName : Nat) (selfKind : TogetherKind) (other : OtherOp)
    return (result : OptimizeOutcome)
  ensures result = (if mergeable selfName selfKind other then OptimizeOutcome.merge
                    else (if ((!affectsModel selfName other) ||
                              (isTogetherOp other && !sameKind selfKind other))
                          then OptimizeOutcome.reorderable
                          else OptimizeOutcome.blocked))
  do
    -- impl-start
    let canReorder ← reorderableTogether selfName selfKind other
    let r := if mergeable selfName selfKind other then OptimizeOutcome.merge
             else (if canReorder then OptimizeOutcome.reorderable
                   else OptimizeOutcome.blocked)
    return r
    -- impl-end

prove_correct optimizeAgainst by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

 Spec shape: three methods (reorderableBase/reorderableTogether/optimizeAgainst), each with an EXACT-equality `ensures result = <expr>` postcondition, no preconditions, under loom.semantics.termination=total + choice=demonic. That pins any verifying impl to the gold behaviour on all inputs.

Same_spec check (swebench_unified.markers.same_spec, velvet lang): True for all 7 attacks + prepatch + pos_correct (axioms/pure/pre/post regions byte-identical; only impl regions edited).

Verify command: `bash scripts/lean_verify.sh <path>`. Ran concurrently, <=4 at a time.
Results:
- pos_correct.lean: EXIT 0 (verifies).
- prepatch.lean (Solution_prepatch, drops different-flavour disjunct): EXIT 1, unsolved goals @125 (prove_correct reorderableTogether) -> prepatch bug reproduced, exactly the clause refinement.md §D names.
- atk_1 (reorderableTogether: return base, drops `|| (isTogetherOp && !sameKind)` = prepatch bug re-encode): EXIT 1 @125.
- atk_2 (reorderableBase: return affectsModel, negation dropped; boundary/logic flip): EXIT 1 @106.
- atk_3 (reorderableTogether: sameKind instead of !sameKind; flavour-sense flip): EXIT 1 @125.
- atk_4 (optimizeAgainst: swap reorderable/blocked branches; control-flow-effect): EXIT 1 @148.
- atk_5 (optimizeAgainst: never blocks, always reorderable when not merge; ungrounded-oracle echo): EXIT 1 @147.
- atk_6 (optimizeAgainst: uses narrower reorderableBase instead of reorderableTogether; partial-domain, misses different-kind reorderable): EXIT 1 @148.
- atk_7 (reorderableTogether: return base || !sameKind, drops isTogetherOp guard; over-widens to non-together ops): EXIT 1 @125.
All attack failures are genuine 'unsolved goals' at prove_correct (spec-mismatch), not syntax/import errors (confirmed from .log files).

Since NO wrong impl verifies, step-2 materialize+resolve is vacuous (patches={}); no resolve run was needed or possible to break the spec.

Refinement.md/mapping.md audit (§4 A-legs focus): axioms region EMPTY; axiom_check.py status=skip; NO A-consumed, NO A-reference, NO kind-3. Every leg is R (type-refinement bijections: Nat<->lower-cased model name equality; TogetherKind<->type(self) in {AlterUniqueTogether,AlterIndexTogether}; OtherOp<->neighbouring migration Operation) or I (concrete transliterations: affectsModel=references_model incl. DeleteModel unconditional-True asymmetry, isTogetherOp=isinstance(AlterTogetherOptionOperation), !sameKind=type differs, mergeable=union of ModelOptionOperation.reduce merge branch + Operation.reduce elidable branch). The single behavioural change (B4 different-flavour disjunct) is modeled DEEPLY, not axiomatized. Unchanged callees references_model/elidable carried as FREE inputs on OtherOp.generic (refsSelf/elidable) => no behavioural claim, no G-AX needed — sound because the patch adds no discriminator on the generic branch (verified: mapping.md §2 note). Model<->patch correspondence holds.

Verdict SOUND: >=5 (7) distinct same-spec wrong impls attempted (partial-domain, boundary, control-flow-effect, ungrounded-oracle echo, flavour flips, prepatch re-encode) + prepatch reproduced; none verified, so none could break verify=>correct.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_correct.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. All 7 same-spec wrong impls FAIL Lean verification (exit 1, 'unsolved goals' at the prove_correct sites), so no verifying wrong impl exists and there is no faithful patch to run through run_resolve. verify=>correct is not falsifiable for this bundle.
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

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_correct.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The only facts the modeled decision consults about a
--  non-modeled operation — "does this neighbouring operation touch my model?"
--  and "is it marked elidable?" — are UNCHANGED and are carried as FREE INPUTS
--  (`OtherOp.generic refsSelf elidable`), so the spec makes no behavioural
--  claim about them and holds for every value. Nothing requires validation
--  against a real callee, hence no G-AX.)
-- axioms-end

-- pure-start
/- The two flavours of "together" model-option an operation may target. Only the
   flavour is ever observed (whether two such operations target the SAME flavour
   or DIFFERENT flavours of the same model). -/
inductive TogetherKind where
  | unique
  | index
  deriving DecidableEq, Inhabited, BEq

/- A neighbouring migration operation, abstracted to exactly the features the
   eligibility decision observes:
   * `together name kind` — an Alter{Unique,Index}Together operation on model
     `name` of flavour `kind` (such operations are never marked elidable);
   * `deleteModel name`   — a delete-model operation on model `name` (never
     marked elidable);
   * `generic refsSelf elidable` — any other operation, carrying only the two
     (free, unchanged) answers the decision observes: "does it touch my
     model?" and "is it marked elidable?" (an elidable neighbour is one the
     optimizer may silently drop, collapsing the pair to my operation alone —
     a merge). -/
inductive OtherOp where
  | together (name : Nat) (kind : TogetherKind)
  | deleteModel (name : Nat)
  | generic (refsSelf : Bool) (elidable : Bool)
  deriving DecidableEq, Inhabited

/- The result of asking whether one operation can be combined with / advanced
   past a neighbouring one:
   * `merge`       — the two collapse into one;
   * `reorderable` — they are independent, so the first may be advanced past the
     second while the optimizer keeps looking for a merge;
   * `blocked`     — neither; a boundary the optimizer cannot cross. -/
inductive OptimizeOutcome where
  | merge
  | reorderable
  | blocked
  deriving DecidableEq, Inhabited

/- "Does the neighbouring operation touch my model `selfName`?" For an
   Alter…Together operation this is name identity (model names compared for
   equality). A delete-model operation conservatively touches EVERY model (a
   deleted model may reference any other through its relations), so it always
   answers yes. For any other operation it is the free, unchanged answer carried
   on the operation. -/
def affectsModel (selfName : Nat) : OtherOp → Bool
  | .together name _    => name == selfName
  | .deleteModel _      => true
  | .generic refsSelf _ => refsSelf

/- Is the neighbouring operation one of the together-option operations? -/
def isTogetherOp : OtherOp → Bool
  | .together _ _ => true
  | _             => false

/- Is the neighbouring operation a together-option operation of the SAME flavour
   as mine? -/
def sameKind (selfKind : TogetherKind) : OtherOp → Bool
  | .together _ kind => kind == selfKind
  | _                => false

/- Do my operation and the neighbour collapse into one? This happens exactly
   when the neighbour is a together-option operation of MY flavour on MY model,
   a delete of MY model, or any other operation marked elidable (the optimizer
   silently drops an elidable neighbour, leaving just my operation — the pair
   becomes one). Together-option and delete-model operations are never marked
   elidable, so the elidable answer is carried only on `generic`. -/
def mergeable (selfName : Nat) (selfKind : TogetherKind) : OtherOp → Bool
  | .together name kind  => kind == selfKind && name == selfName
  | .deleteModel name    => name == selfName
  | .generic _ elidable  => elidable
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The baseline independence test shared by every model operation: an operation
   may be advanced past a neighbour exactly when that neighbour does not touch
   its model. `selfName`, `other` are read-only (directive 5). -/
method reorderableBase (selfName : Nat) (other : OtherOp) return (result : Bool)
  ensures result = (!affectsModel selfName other)
  do
    -- impl-start
    return !affectsModel selfName other
    -- impl-end

prove_correct reorderableBase by
  loom_solve

/- The independence test specialised to a together-option operation. It widens
   the baseline test: such an operation is ALSO independent of a together-option
   neighbour of a DIFFERENT flavour on the same model — the two constrain
   disjoint kinds of model option, so the optimizer may advance one past the
   other (which is what later lets a remove/re-add pair on each flavour collapse
   to a single operation). `selfName`, `selfKind`, `other` are read-only. -/
method reorderableTogether (selfName : Nat) (selfKind : TogetherKind) (other : OtherOp)
    return (result : Bool)
  ensures result = ((!affectsModel selfName other) ||
                    (isTogetherOp other && !sameKind selfKind other))
  do
    -- impl-start
    let base ← reorderableBase selfName other
    return base || (isTogetherOp other && !sameKind selfKind other)
    -- impl-end

prove_correct reorderableTogether by
  loom_solve

/- The full eligibility verdict an Alter…Together operation reaches against a
   neighbour: it merges with a same-flavour together (or a delete) on its model;
   otherwise it is reorderable iff the independence test above holds; otherwise
   it is blocked. `selfName`, `selfKind`, `other` are read-only. -/
method optimizeAgainst (selfName : Nat) (selfKind : TogetherKind) (other : OtherOp)
    return (result : OptimizeOutcome)
  ensures result = (if mergeable selfName selfKind other then OptimizeOutcome.merge
                    else (if ((!affectsModel selfName other) ||
                              (isTogetherOp other && !sameKind selfKind other))
                          then OptimizeOutcome.reorderable
                          else OptimizeOutcome.blocked))
  do
    -- impl-start
    let canReorder ← reorderableTogether selfName selfKind other
    let r := if mergeable selfName selfKind other then OptimizeOutcome.merge
             else (if canReorder then OptimizeOutcome.reorderable
                   else OptimizeOutcome.blocked)
    return r
    -- impl-end

prove_correct optimizeAgainst by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

 Spec shape: three methods (reorderableBase/reorderableTogether/optimizeAgainst), each with an EXACT-equality `ensures result = <expr>` postcondition, no preconditions, under loom.semantics.termination=total + choice=demonic. That pins any verifying impl to the gold behaviour on all inputs.

Same_spec check (swebench_unified.markers.same_spec, velvet lang): True for all 7 attacks + prepatch + pos_correct (axioms/pure/pre/post regions byte-identical; only impl regions edited).

Verify command: `bash scripts/lean_verify.sh <path>`. Ran concurrently, <=4 at a time.
Results:
- pos_correct.lean: EXIT 0 (verifies).
- prepatch.lean (Solution_prepatch, drops different-flavour disjunct): EXIT 1, unsolved goals @125 (prove_correct reorderableTogether) -> prepatch bug reproduced, exactly the clause refinement.md §D names.
- atk_1 (reorderableTogether: return base, drops `|| (isTogetherOp && !sameKind)` = prepatch bug re-encode): EXIT 1 @125.
- atk_2 (reorderableBase: return affectsModel, negation dropped; boundary/logic flip): EXIT 1 @106.
- atk_3 (reorderableTogether: sameKind instead of !sameKind; flavour-sense flip): EXIT 1 @125.
- atk_4 (optimizeAgainst: swap reorderable/blocked branches; control-flow-effect): EXIT 1 @148.
- atk_5 (optimizeAgainst: never blocks, always reorderable when not merge; ungrounded-oracle echo): EXIT 1 @147.
- atk_6 (optimizeAgainst: uses narrower reorderableBase instead of reorderableTogether; partial-domain, misses different-kind reorderable): EXIT 1 @148.
- atk_7 (reorderableTogether: return base || !sameKind, drops isTogetherOp guard; over-widens to non-together ops): EXIT 1 @125.
All attack failures are genuine 'unsolved goals' at prove_correct (spec-mismatch), not syntax/import errors (confirmed from .log files).

Since NO wrong impl verifies, step-2 materialize+resolve is vacuous (patches={}); no resolve run was needed or possible to break the spec.

Refinement.md/mapping.md audit (§4 A-legs focus): axioms region EMPTY; axiom_check.py status=skip; NO A-consumed, NO A-reference, NO kind-3. Every leg is R (type-refinement bijections: Nat<->lower-cased model name equality; TogetherKind<->type(self) in {AlterUniqueTogether,AlterIndexTogether}; OtherOp<->neighbouring migration Operation) or I (concrete transliterations: affectsModel=references_model incl. DeleteModel unconditional-True asymmetry, isTogetherOp=isinstance(AlterTogetherOptionOperation), !sameKind=type differs, mergeable=union of ModelOptionOperation.reduce merge branch + Operation.reduce elidable branch). The single behavioural change (B4 different-flavour disjunct) is modeled DEEPLY, not axiomatized. Unchanged callees references_model/elidable carried as FREE inputs on OtherOp.generic (refsSelf/elidable) => no behavioural claim, no G-AX needed — sound because the patch adds no discriminator on the generic branch (verified: mapping.md §2 note). Model<->patch correspondence holds.

Verdict SOUND: >=5 (7) distinct same-spec wrong impls attempted (partial-domain, boundary, control-flow-effect, ungrounded-oracle echo, flavour flips, prepatch re-encode) + prepatch reproduced; none verified, so none could break verify=>correct.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack on velvet django__django-15268. Spec region byte-identical between Solution.lean and Solution_prepatch.lean (swebench_unified.markers.same_spec via VelvetBackend => True). Solution.lean verifies (lean_verify exit 0); prepatch fails on reorderableTogether ensures (unsolved goal), confirming the spec senses the behavioural change (G-DIFF holds).

Exhaustive case-analysis of the three modeled methods against the REAL post-patch reduce MRO (ModelOptionOperation.reduce @ models.py:411 -> ModelOperation.reduce+can_reduce_through -> AlterTogetherOptionOperation.can_reduce_through override -> Operation.reduce @ base.py:123), verified against the worktree source:
  self = AlterFooTogether(name=m, kind=k), map list->merge, True->reorderable, False->blocked.
  1. together same-kind same-name: real [operation]=>merge; model mergeable=(kind==k && name==m)=T=>merge. MATCH
  2. together same-kind diff-name: merge-branch name mismatch fails; can_reduce_through = not refs(=name==m=F)=T=>reorderable; model !affectsModel(name==m=F)=T=>reorderable. MATCH
  3. together diff-kind same-name: merge fails (kind!=k); super().can_reduce_through=not refs(m==m)=F, OR (isinstance AlterTogether=T and type diff=T)=T=>reorderable; model isTogetherOp && !sameKind=T=>reorderable. MATCH (this is the discriminating input)
  4. together diff-kind diff-name: not refs=T=>reorderable; model !affects=T=>reorderable. MATCH
  5. deleteModel same-name: isinstance(other,(self.__class__,DeleteModel)) & name match => [operation]=>merge; model mergeable .deleteModel name==m=T=>merge. MATCH
  6. deleteModel diff-name: DeleteModel.references_model returns True unconditionally (models.py:276-278) => not True=F; not a together op => can_reduce_through=F=>blocked; model affectsModel(.deleteModel _)=true so !affects=F, isTogetherOp=F => blocked. MATCH (the asymmetry the note credits G-CONF/M1 with catching — correctly modeled).
  7. generic elidable: Operation.reduce elif operation.elidable: return [self] => merge; model mergeable .generic _ elidable = elidable=T=>merge. MATCH (self.elidable always False since AlterTogether classes leave base.py:32 default; only RunSQL/RunPython take elidable=kwarg — the dead-first-branch reasoning is correct).
  8. generic non-elidable, refsSelf=True: not refs=F, no together disjunct=>blocked; model affects=refsSelf=T=>blocked. MATCH
  9. generic non-elidable, refsSelf=False: not refs=T=>reorderable; model !affects=T=>reorderable. MATCH

Unchanged callees are correctly abstracted: references_model for generic ops and the elidable attribute are carried as FREE INPUTS on OtherOp.generic (spec makes no claim, holds for every value), which cannot over-strengthen. together/deleteModel neighbours are never elidable (class default), so restricting the elidable bit to .generic loses nothing. Nat<->name-equality and TogetherKind<->type bijections are faithful (only equality/isinstance/type observed). No axioms.

No input found on which the modeled optimizeAgainst / reorderableTogether / reorderableBase disagrees with the real repo callee. Spec is neither too strong nor drifting. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec region is byte-identical between Solution.lean and Solution_prepatch.lean (same_spec => True via swebench_unified.markers; the only diff is inside the elided impl region, line 122: `return base` vs `return base || (isTogetherOp other && !sameKind selfKind other)`). Mechanical G-LEAK screen PASSES: no diff markers, patched file path `django/db/migrations/operations/models.py` / module path absent from spec view, no patched repo symbols (`can_reduce_through`, `references_model`, `describe`) appearing as spec-view identifiers or in comments, no bug/fix narration terms. Semantic gold-reconstruction judged against problem_statement ONLY (not hints_text — hints empty here): the discriminating spec clause in `reorderableTogether`'s ensures (reorderable also when `isTogetherOp other && !sameKind selfKind other`) formalizes exactly the publicly-stated requirement — that different-flavour AlterUnique/IndexTogether ops on the same model should be optimizable, collapsing the issue's worked 4->2 example. That is the spec doing its job (encoding required behavior stated in the public issue), not leaking the gold edit. Comments describe behavior at the abstract model level (kinds, merge/reorder/block outcomes) and never name the edited method, file, MRO/super mechanics, or the `can_reduce_through` extraction. Abstracted carrier types (TogetherKind/OtherOp/OptimizeOutcome) and the pre-existing deleteModel/elidable scaffold localize no edit. The spec reveals nothing about the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
