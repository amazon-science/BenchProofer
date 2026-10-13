# P2 adversarial audit — django__django-16032

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

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
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No axiomatized callees. The decision modeled here is pure boolean logic over
@@ -72,9 +72,9 @@
   ensures narrow = narrowsToSingleColumn q
   do
     -- impl-start
-    -- Post-fix: a query designates its output columns only when the caller has
-    -- explicitly projected them; the narrowing is required exactly otherwise.
-    let designated := q.explicitlyProjected
+    -- ATTACK: prepatch derived-disjunction bug
+    let designated :=
+      q.hasExplicitSelectColumns || q.carriesAnnotations || q.carriesExtraSelections
     return !designated
     -- impl-end
 
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
 -- (No axiomatized callees. The decision modeled here is pure boolean logic over
@@ -72,10 +72,8 @@
   ensures narrow = narrowsToSingleColumn q
   do
     -- impl-start
-    -- Post-fix: a query designates its output columns only when the caller has
-    -- explicitly projected them; the narrowing is required exactly otherwise.
-    let designated := q.explicitlyProjected
-    return !designated
+    -- ATTACK: partial-domain, keys off annotations only
+    return !q.carriesAnnotations
     -- impl-end
 
 prove_correct narrowRhsSubquery by
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
 -- (No axiomatized callees. The decision modeled here is pure boolean logic over
@@ -72,10 +72,8 @@
   ensures narrow = narrowsToSingleColumn q
   do
     -- impl-start
-    -- Post-fix: a query designates its output columns only when the caller has
-    -- explicitly projected them; the narrowing is required exactly otherwise.
-    let designated := q.explicitlyProjected
-    return !designated
+    -- ATTACK: boundary constant true
+    return true
     -- impl-end
 
 prove_correct narrowRhsSubquery by
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
 -- (No axiomatized callees. The decision modeled here is pure boolean logic over
@@ -72,10 +72,8 @@
   ensures narrow = narrowsToSingleColumn q
   do
     -- impl-start
-    -- Post-fix: a query designates its output columns only when the caller has
-    -- explicitly projected them; the narrowing is required exactly otherwise.
-    let designated := q.explicitlyProjected
-    return !designated
+    -- ATTACK: boundary constant false
+    return false
     -- impl-end
 
 prove_correct narrowRhsSubquery by
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
 -- (No axiomatized callees. The decision modeled here is pure boolean logic over
@@ -72,10 +72,11 @@
   ensures narrow = narrowsToSingleColumn q
   do
     -- impl-start
-    -- Post-fix: a query designates its output columns only when the caller has
-    -- explicitly projected them; the narrowing is required exactly otherwise.
-    let designated := q.explicitlyProjected
-    return !designated
+    -- ATTACK: control-flow, wrong on annotation branch
+    if q.carriesAnnotations then
+      return true
+    else
+      return !q.explicitlyProjected
     -- impl-end
 
 prove_correct narrowRhsSubquery by
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
 -- (No axiomatized callees. The decision modeled here is pure boolean logic over
@@ -72,10 +72,8 @@
   ensures narrow = narrowsToSingleColumn q
   do
     -- impl-start
-    -- Post-fix: a query designates its output columns only when the caller has
-    -- explicitly projected them; the narrowing is required exactly otherwise.
-    let designated := q.explicitlyProjected
-    return !designated
+    -- ATTACK: over-broad, folds explicit select into projection
+    return !(q.explicitlyProjected || q.hasExplicitSelectColumns)
     -- impl-end
 
 prove_correct narrowRhsSubquery by
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 -- (No axiomatized callees. The decision modeled here is pure boolean logic over
@@ -72,10 +72,8 @@
   ensures narrow = narrowsToSingleColumn q
   do
     -- impl-start
-    -- Post-fix: a query designates its output columns only when the caller has
-    -- explicitly projected them; the narrowing is required exactly otherwise.
-    let designated := q.explicitlyProjected
-    return !designated
+    -- ATTACK: ungrounded oracle echo
+    return narrowsToSingleColumn q
     -- impl-end
 
 prove_correct narrowRhsSubquery by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The decision modeled here is pure boolean logic over
--  FREE INPUTS describing a query's output-column state: whether the caller has
--  explicitly projected the output columns, whether the query already carries an
--  explicit list of select columns, and whether it merely carries annotation or
--  extra-selection columns. The downstream machinery these decisions gate —
--  subquery compilation and column reduction — is UNCHANGED code the decision
--  only triggers, never reshapes, so there is no callee contract to assume and
--  nothing for G-AX. See mapping.md §3 / refinement.md.)
-- axioms-end

-- pure-start
/- The output-column state of a query that appears on the right-hand side of a
   membership test, as the narrowing decision observes it.

   * `explicitlyProjected`      — the caller has explicitly chosen the output
                                  columns the query returns (an explicit column
                                  projection was applied to it).
   * `hasExplicitSelectColumns` — the query already carries an explicit list of
                                  select columns.
   * `carriesAnnotations`       — the query carries annotation columns (e.g.
                                  produced by adding computed/aliased
                                  expressions to it).
   * `carriesExtraSelections`   — the query carries extra raw select columns. -/
structure RhsQuery where
  explicitlyProjected      : Bool
  hasExplicitSelectColumns : Bool
  carriesAnnotations       : Bool
  carriesExtraSelections   : Bool
deriving Inhabited, DecidableEq

/- Whether a right-hand-side query already designates the output columns it will
   return. A query designates its output columns ONLY when the caller has
   explicitly projected them; merely carrying annotation or extra-selection
   columns does not, on its own, designate the columns the query returns. -/
def designatesOutputColumns (q : RhsQuery) : Bool := q.explicitlyProjected

/- The narrowing decision: a right-hand-side membership subquery must be reduced
   to a single output column exactly when it does not already designate its
   output columns. -/
def narrowsToSingleColumn (q : RhsQuery) : Bool := ! designatesOutputColumns q

@[grind] lemma narrowsToSingleColumn_def (q : RhsQuery) :
    narrowsToSingleColumn q = (! q.explicitlyProjected) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Decide whether a subquery used on the right-hand side of a membership test
   must be reduced to a single output column before the comparison. The
   reduction is required exactly when the subquery does not already designate the
   columns it returns — i.e. when the caller has NOT explicitly projected its
   output columns. A subquery that merely carries annotation or extra-selection
   columns has NOT thereby designated its output columns, so it must still be
   reduced to one column; otherwise the membership test would compare against a
   multi-column row set. `q` is read-only (not `mut`): the decision reads the
   query's column state and produces a fresh boolean, mutating nothing
   (directive 5). -/
method narrowRhsSubquery (q : RhsQuery) return (narrow : Bool)
  ensures narrow = narrowsToSingleColumn q
  do
    -- impl-start
    -- positive control: gold impl
    let designated := q.explicitlyProjected
    return !designated
    -- impl-end

prove_correct narrowRhsSubquery by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

SPEC STRUCTURE: postcondition `ensures narrow = narrowsToSingleColumn q` where narrowsToSingleColumn q = !q.explicitlyProjected. There is NO precondition, so the postcondition is a TOTAL equality pinning `narrow` as a function of the free inputs on every RhsQuery. Any verifying impl is thus forced to compute exactly !q.explicitlyProjected. This structurally precludes a verifying-but-wrong impl.

SAME-SPEC: all 7 attacks + positive control confirmed True via swebench_unified.markers.same_spec (velvet); only the impl region was edited, axioms/pure/pre/post byte-identical.

### VERIFICATIONS (scripts/lean_verify.sh <file>, run concurrently in 2 batches of 4):
- atk_1.lean (prepatch bug: designated = hasExplicitSelectColumns || carriesAnnotations || carriesExtraSelections; return !designated) -> exit=1 FAIL. Log: 'unsolved goals, case ensures_1: (!(q.hasExplicitSelectColumns || q.carriesAnnotations || q.carriesExtraSelections)) = narrowsToSingleColumn q'. This IS the recorded prepatch => prepatch_reproduced=true (matches G-DIFF verification-failed).
- atk_2.lean (partial-domain/ungrounded: return !q.carriesAnnotations) -> exit=1 FAIL.
- atk_3.lean (boundary const: return true) -> exit=1 FAIL. Goal 'true = narrowsToSingleColumn q'.
- atk_4.lean (boundary const: return false) -> exit=1 FAIL.
- atk_5.lean (control-flow-effect: if carriesAnnotations then true else !explicitlyProjected) -> exit=1 FAIL.
- atk_6.lean (over-broad operator: return !(explicitlyProjected || hasExplicitSelectColumns)) -> exit=1 FAIL.
- atk_7.lean (ungrounded-oracle echo: return narrowsToSingleColumn q) -> exit=0 VERIFIES. But this is definitionally !q.explicitlyProjected == gold; behaviorally identical to the correct impl, NOT a semantic weakness.
- pos_control.lean (gold: let designated := q.explicitlyProjected; return !designated) -> exit=0 VERIFIES.

RESOLVE OF EVERY VERIFYING ATTACK (mandatory): atk_7 is the only verifying wrong-shaped impl. Its faithful refined patch is behaviorally identical to gold (echo reduces to !explicitlyProjected), materialized as atk_7.faithful.patch (= gold patch.diff). Ran through official harness: swebench_unified.harness.run_resolve('django__django-16032', patch, run_id='sbu-audit-atk7-o8len', timeout=1800, retries=1) under SBU_BENCHMARK=swe_bench_verified via `docker`. RESULT: RESOLVED=True, completed=True, note='resolved', flaky=False. So the sole verifying impl's patch RESOLVES => no verify-not-correct witness.

REFINEMENT AUDIT (refinement.md / mapping.md): 4 legs. A1 (q.explicitlyProjected <-> post-patch has_select_fields flag value, R), A2 (three bool inputs <-> disjuncts of deleted derived property, R), A3 (designated := explicitlyProjected <-> post-patch has_select_fields meaning, I+R — the CHANGED op modeled deeply as boolean, not axiomatized), A4 (return !designated <-> `not self.rhs.has_select_fields` guard, I+R). All legs are R or I; NO A-consumed / A-reference / kind-3 legs; axioms=[] and deep_model_references=[] in meta.json confirm nothing to check for G-AX. Model<->patch correspondence holds: the gold's three hunks collapse has_select_fields to exactly `explicitlyProjected`, matching the deep model; the RelatedIn clear+add_fields -> set_values swap is behaviour-preserving (both reduce rhs to one column) and correctly carries no separate modeled op/prepatch. G-CONF conf_skip=true is legitimately documented (only discriminating observable is live-ORM/DB SQL; no DB-free R/I shadow); soundness carried by G-VERIFY + G-DIFF. Correspondence of the A-legs is moot (no A-legs).

CONCLUSION: SOUND. The frozen postcondition is a complete total specification of the boolean decision; 6 distinct wrong impls (prepatch, partial-domain, two boundary constants, control-flow-effect, over-broad-operator) all fail to verify on the exact ensures clause, and the only verifying impl is behaviorally the gold whose materialized faithful patch RESOLVES under the official harness. verify => correct holds for this bundle.

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
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The decision modeled here is pure boolean logic over
--  FREE INPUTS describing a query's output-column state: whether the caller has
--  explicitly projected the output columns, whether the query already carries an
--  explicit list of select columns, and whether it merely carries annotation or
--  extra-selection columns. The downstream machinery these decisions gate —
--  subquery compilation and column reduction — is UNCHANGED code the decision
--  only triggers, never reshapes, so there is no callee contract to assume and
--  nothing for G-AX. See mapping.md §3 / refinement.md.)
-- axioms-end

-- pure-start
/- The output-column state of a query that appears on the right-hand side of a
   membership test, as the narrowing decision observes it.

   * `explicitlyProjected`      — the caller has explicitly chosen the output
                                  columns the query returns (an explicit column
                                  projection was applied to it).
   * `hasExplicitSelectColumns` — the query already carries an explicit list of
                                  select columns.
   * `carriesAnnotations`       — the query carries annotation columns (e.g.
                                  produced by adding computed/aliased
                                  expressions to it).
   * `carriesExtraSelections`   — the query carries extra raw select columns. -/
structure RhsQuery where
  explicitlyProjected      : Bool
  hasExplicitSelectColumns : Bool
  carriesAnnotations       : Bool
  carriesExtraSelections   : Bool
deriving Inhabited, DecidableEq

/- Whether a right-hand-side query already designates the output columns it will
   return. A query designates its output columns ONLY when the caller has
   explicitly projected them; merely carrying annotation or extra-selection
   columns does not, on its own, designate the columns the query returns. -/
def designatesOutputColumns (q : RhsQuery) : Bool := q.explicitlyProjected

/- The narrowing decision: a right-hand-side membership subquery must be reduced
   to a single output column exactly when it does not already designate its
   output columns. -/
def narrowsToSingleColumn (q : RhsQuery) : Bool := ! designatesOutputColumns q

@[grind] lemma narrowsToSingleColumn_def (q : RhsQuery) :
    narrowsToSingleColumn q = (! q.explicitlyProjected) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Decide whether a subquery used on the right-hand side of a membership test
   must be reduced to a single output column before the comparison. The
   reduction is required exactly when the subquery does not already designate the
   columns it returns — i.e. when the caller has NOT explicitly projected its
   output columns. A subquery that merely carries annotation or extra-selection
   columns has NOT thereby designated its output columns, so it must still be
   reduced to one column; otherwise the membership test would compare against a
   multi-column row set. `q` is read-only (not `mut`): the decision reads the
   query's column state and produces a fresh boolean, mutating nothing
   (directive 5). -/
method narrowRhsSubquery (q : RhsQuery) return (narrow : Bool)
  ensures narrow = narrowsToSingleColumn q
  do
    -- impl-start
    -- positive control: gold impl
    let designated := q.explicitlyProjected
    return !designated
    -- impl-end

prove_correct narrowRhsSubquery by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

SPEC STRUCTURE: postcondition `ensures narrow = narrowsToSingleColumn q` where narrowsToSingleColumn q = !q.explicitlyProjected. There is NO precondition, so the postcondition is a TOTAL equality pinning `narrow` as a function of the free inputs on every RhsQuery. Any verifying impl is thus forced to compute exactly !q.explicitlyProjected. This structurally precludes a verifying-but-wrong impl.

SAME-SPEC: all 7 attacks + positive control confirmed True via swebench_unified.markers.same_spec (velvet); only the impl region was edited, axioms/pure/pre/post byte-identical.

### VERIFICATIONS (scripts/lean_verify.sh <file>, run concurrently in 2 batches of 4):
- atk_1.lean (prepatch bug: designated = hasExplicitSelectColumns || carriesAnnotations || carriesExtraSelections; return !designated) -> exit=1 FAIL. Log: 'unsolved goals, case ensures_1: (!(q.hasExplicitSelectColumns || q.carriesAnnotations || q.carriesExtraSelections)) = narrowsToSingleColumn q'. This IS the recorded prepatch => prepatch_reproduced=true (matches G-DIFF verification-failed).
- atk_2.lean (partial-domain/ungrounded: return !q.carriesAnnotations) -> exit=1 FAIL.
- atk_3.lean (boundary const: return true) -> exit=1 FAIL. Goal 'true = narrowsToSingleColumn q'.
- atk_4.lean (boundary const: return false) -> exit=1 FAIL.
- atk_5.lean (control-flow-effect: if carriesAnnotations then true else !explicitlyProjected) -> exit=1 FAIL.
- atk_6.lean (over-broad operator: return !(explicitlyProjected || hasExplicitSelectColumns)) -> exit=1 FAIL.
- atk_7.lean (ungrounded-oracle echo: return narrowsToSingleColumn q) -> exit=0 VERIFIES. But this is definitionally !q.explicitlyProjected == gold; behaviorally identical to the correct impl, NOT a semantic weakness.
- pos_control.lean (gold: let designated := q.explicitlyProjected; return !designated) -> exit=0 VERIFIES.

RESOLVE OF EVERY VERIFYING ATTACK (mandatory): atk_7 is the only verifying wrong-shaped impl. Its faithful refined patch is behaviorally identical to gold (echo reduces to !explicitlyProjected), materialized as atk_7.faithful.patch (= gold patch.diff). Ran through official harness: swebench_unified.harness.run_resolve('django__django-16032', patch, run_id='sbu-audit-atk7-o8len', timeout=1800, retries=1) under SBU_BENCHMARK=swe_bench_verified via `docker`. RESULT: RESOLVED=True, completed=True, note='resolved', flaky=False. So the sole verifying impl's patch RESOLVES => no verify-not-correct witness.

REFINEMENT AUDIT (refinement.md / mapping.md): 4 legs. A1 (q.explicitlyProjected <-> post-patch has_select_fields flag value, R), A2 (three bool inputs <-> disjuncts of deleted derived property, R), A3 (designated := explicitlyProjected <-> post-patch has_select_fields meaning, I+R — the CHANGED op modeled deeply as boolean, not axiomatized), A4 (return !designated <-> `not self.rhs.has_select_fields` guard, I+R). All legs are R or I; NO A-consumed / A-reference / kind-3 legs; axioms=[] and deep_model_references=[] in meta.json confirm nothing to check for G-AX. Model<->patch correspondence holds: the gold's three hunks collapse has_select_fields to exactly `explicitlyProjected`, matching the deep model; the RelatedIn clear+add_fields -> set_values swap is behaviour-preserving (both reduce rhs to one column) and correctly carries no separate modeled op/prepatch. G-CONF conf_skip=true is legitimately documented (only discriminating observable is live-ORM/DB SQL; no DB-free R/I shadow); soundness carried by G-VERIFY + G-DIFF. Correspondence of the A-legs is moot (no A-legs).

CONCLUSION: SOUND. The frozen postcondition is a complete total specification of the boolean decision; 6 distinct wrong impls (prepatch, partial-domain, two boundary constants, control-flow-effect, over-broad-operator) all fail to verify on the exact ensures clause, and the only verifying impl is behaviorally the gold whose materialized faithful patch RESOLVES under the official harness. verify => correct holds for this bundle.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness/drift audit of velvet bundle django__django-16032. Modeled function narrowRhsSubquery q = !q.explicitlyProjected over a four-bool RhsQuery, bound to the membership-narrowing guard `if not self.rhs.has_select_fields:`.

Mechanical checks: (1) swebench_unified.markers.same_spec(Solution, prepatch, velvet) = True — spec region byte-identical, only impl body differs. (2) lean_verify Solution.lean -> exit 0 (verifies). (3) lean_verify Solution_prepatch.lean -> exit 1, fails on the exact discriminating clause `(!(hasExplicitSelectColumns||carriesAnnotations||carriesExtraSelections)) = narrowsToSingleColumn q` (G-DIFF story holds).

Repo cross-check at base_commit + gold worktree: post-patch has_select_fields has ONLY two write sites — class default `has_select_fields = False` (query.py:201) and `set_values` -> `self.has_select_fields = True` (query.py:2382). So post-patch the flag is exactly 'set_values was called', matching the explicitlyProjected bijection in mapping.md §2. The patch intentionally decouples the flag from select/annotation_select_mask/extra_select_mask (deleted derived property), so the post-patch decision ignoring the other three struct fields (narrow = !explicitlyProjected) faithfully mirrors the real decoupled semantics. The In/pk__in guard (lookups.py:423) reduces to exactly `!explicitlyProjected` = model output — exact agreement over the whole modeled domain.

Closest drift candidate examined and rejected: RelatedIn.get_prep_lookup (related_lookups.py:93) guards with `not has_select_fields AND not getattr(lhs.field.target_field, 'primary_key', False)` — an extra conjunct the model omits. That conjunct is a predicate on the LHS (outside the RhsQuery abstraction) and is UNCHANGED by the patch; the modeled symbol is explicitly scoped to the has_select_fields-derived narrowing bit both sites read. This is a documented, legitimate modeling boundary, not a divergence of the modeled function on its stated input domain. No RhsQuery input makes !explicitlyProjected disagree with the real `not self.rhs.has_select_fields` guard value. conf_skip=true is appropriately justified (only discriminating observable is live-ORM SQL / OperationalError). Spec is neither too strong nor drifted.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen (leakage.screen over spec_view, velvet/lean flavor) PASSES with zero hard failures. same_spec(Solution.lean, Solution_prepatch.lean)=True; spec region byte-identical.

Manual review confirms no leak beyond the public problem_statement:
- No patched repo symbols in the spec view: has_select_fields, set_values, get_prep_lookup, Query, annotation_select_mask are all ABSENT from identifiers and comments (verified). Changed symbols the screen guards {Query, get_prep_lookup, has_select_fields, output_field, set_values} do not appear.
- No patched file/module paths (django/db/models/sql/query.py, related_lookups.py) in the view.
- No gold-patch changed line reproduced (>=8-char normalized); no diff markers.
- No bug/fix narration in the visible view. The one narration-flavored comment ('Post-fix: ...') sits inside the elided impl-start/impl-end region and is NOT part of the spec view (verified 'Post-fix' not in view).

The spec's abstraction vocabulary (explicitlyProjected, carriesAnnotations, carriesExtraSelections, narrowsToSingleColumn, designatesOutputColumns) is generic domain paraphrase. 'annotation/aliased expressions' merely restates .annotate()/.alias(), which are already public in the problem_statement's reproducing test case. The encoded decision rule (narrow iff not explicitly projected; annotation-only queries still narrow) is the inherent required correctness content of any spec, not a disclosure of the edit's location/mechanism (derived-property -> stored flag), which lives ONLY in hints_text (correctly excluded from the leakage judgment).

Cross-checked: the leaking mechanism details (has_select_fields property replacement, set_values, annotation_select_mask, related_lookups swap, file paths) are present in hints_text but NOT in problem_statement, and NONE of them surface in the spec view. No leakage.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
