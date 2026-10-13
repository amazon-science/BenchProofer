# P2 adversarial audit — django__django-13033

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE — no same-spec wrong impl verifies, so there is no candidate counterexample and no refined patch to run through the harness. The postcondition is an exact equality `out = appendRelatedDefaultOrdering fieldIsRelation modelHasDefaultOrdering fieldAttr segments lookup`, pinning out to a total boolean spec function over the whole domain (segments ≠ []). Any verifying impl must be extensionally equal to the gold decision, so verify ⇒ behaviorally gold. All 8 same-spec wrong impls (incl. the prepatch whole-path-comparison bug) fail verification; only the correct positive control verifies.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

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
 -- (No axiomatized callees. The decision modeled here is a pure boolean function
@@ -58,7 +58,7 @@
       fieldAttr segments lookup
   do
     -- impl-start
-    let endsAtStoredAttr := fieldAttr != some (terminalSegment segments)
+    let endsAtStoredAttr := fieldAttr != some lookup
     let notPkShortcut := lookup != "pk".toList
     return fieldIsRelation && modelHasDefaultOrdering &&
       endsAtStoredAttr && notPkShortcut
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
 -- (No axiomatized callees. The decision modeled here is a pure boolean function
@@ -58,7 +58,7 @@
       fieldAttr segments lookup
   do
     -- impl-start
-    let endsAtStoredAttr := fieldAttr != some (terminalSegment segments)
+    let endsAtStoredAttr := fieldAttr != some segments.head!
     let notPkShortcut := lookup != "pk".toList
     return fieldIsRelation && modelHasDefaultOrdering &&
       endsAtStoredAttr && notPkShortcut
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
 -- (No axiomatized callees. The decision modeled here is a pure boolean function
@@ -58,10 +58,7 @@
       fieldAttr segments lookup
   do
     -- impl-start
-    let endsAtStoredAttr := fieldAttr != some (terminalSegment segments)
-    let notPkShortcut := lookup != "pk".toList
-    return fieldIsRelation && modelHasDefaultOrdering &&
-      endsAtStoredAttr && notPkShortcut
+    return false
     -- impl-end
 
 prove_correct orderingExpansionDecision by
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
 -- (No axiomatized callees. The decision modeled here is a pure boolean function
@@ -59,9 +59,7 @@
   do
     -- impl-start
     let endsAtStoredAttr := fieldAttr != some (terminalSegment segments)
-    let notPkShortcut := lookup != "pk".toList
-    return fieldIsRelation && modelHasDefaultOrdering &&
-      endsAtStoredAttr && notPkShortcut
+    return fieldIsRelation && modelHasDefaultOrdering && endsAtStoredAttr
     -- impl-end
 
 prove_correct orderingExpansionDecision by
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
 -- (No axiomatized callees. The decision modeled here is a pure boolean function
@@ -58,10 +58,8 @@
       fieldAttr segments lookup
   do
     -- impl-start
-    let endsAtStoredAttr := fieldAttr != some (terminalSegment segments)
-    let notPkShortcut := lookup != "pk".toList
-    return fieldIsRelation && modelHasDefaultOrdering &&
-      endsAtStoredAttr && notPkShortcut
+    return appendRelatedDefaultOrdering fieldIsRelation modelHasDefaultOrdering
+      fieldAttr segments lookup
     -- impl-end
 
 prove_correct orderingExpansionDecision by
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
 -- (No axiomatized callees. The decision modeled here is a pure boolean function
@@ -58,7 +58,7 @@
       fieldAttr segments lookup
   do
     -- impl-start
-    let endsAtStoredAttr := fieldAttr != some (terminalSegment segments)
+    let endsAtStoredAttr := fieldAttr == some (terminalSegment segments)
     let notPkShortcut := lookup != "pk".toList
     return fieldIsRelation && modelHasDefaultOrdering &&
       endsAtStoredAttr && notPkShortcut
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
 -- (No axiomatized callees. The decision modeled here is a pure boolean function
@@ -58,7 +58,8 @@
       fieldAttr segments lookup
   do
     -- impl-start
-    let endsAtStoredAttr := fieldAttr != some (terminalSegment segments)
+    let term := (segments.reverse).head!
+    let endsAtStoredAttr := fieldAttr != some term
     let notPkShortcut := lookup != "pk".toList
     return fieldIsRelation && modelHasDefaultOrdering &&
       endsAtStoredAttr && notPkShortcut
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
 -- (No axiomatized callees. The decision modeled here is a pure boolean function
@@ -60,8 +60,7 @@
     -- impl-start
     let endsAtStoredAttr := fieldAttr != some (terminalSegment segments)
     let notPkShortcut := lookup != "pk".toList
-    return fieldIsRelation && modelHasDefaultOrdering &&
-      endsAtStoredAttr && notPkShortcut
+    return modelHasDefaultOrdering && endsAtStoredAttr && notPkShortcut
     -- impl-end
 
 prove_correct orderingExpansionDecision by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The decision modeled here is a pure boolean function
--  of the resolved field metadata and the lookup path; the machinery that
--  resolves that metadata is unchanged and shared by both branches, so it is
--  not consumed as an outside contract. There is no `axiom` declaration and no
--  A-reference deep model of an outside callee.)
-- axioms-end

-- pure-start
/- A relation lookup is written as a path of segments joined by a separator
   (e.g. `a__b__c` is the three segments `a`, `b`, `c`). The *terminal segment*
   is the last one — the concrete attribute actually named at the end of the
   path. -/
def terminalSegment (segments : List (List Char)) : List Char :=
  segments.getLast!

/- Whether to append a related model's own default ordering for an ordering
   lookup. The default ordering of the pointed-to model is appended only when

     * the resolved field is a relation, AND
     * that model declares a default ordering, AND
     * the field's stored attribute name is NOT the attribute named by the
       TERMINAL segment of the lookup path (when the path ends at the field's
       own stored attribute, the column is ordered directly rather than
       expanding the related model's default ordering), AND
     * the lookup is not the primary-key shortcut `pk`.

   The terminal-segment comparison is what distinguishes a lookup that ends at
   a relation's stored attribute (order directly by that column) from one that
   ends at the relation itself (expand the related model's default ordering). -/
def appendRelatedDefaultOrdering
    (fieldIsRelation modelHasDefaultOrdering : Bool)
    (fieldAttr : Option (List Char))
    (segments : List (List Char)) (lookup : List Char) : Bool :=
  fieldIsRelation && modelHasDefaultOrdering &&
    (fieldAttr != some (terminalSegment segments)) &&
    (lookup != "pk".toList)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method orderingExpansionDecision (fieldIsRelation : Bool) (modelHasDefaultOrdering : Bool) (fieldAttr : Option (List Char)) (segments : List (List Char)) (lookup : List Char) return (out : Bool)
  require segments ≠ []
  ensures out =
    appendRelatedDefaultOrdering fieldIsRelation modelHasDefaultOrdering
      fieldAttr segments lookup
  do
    -- impl-start
    let endsAtStoredAttr := fieldAttr != some (terminalSegment segments)
    let notPkShortcut := lookup != "pk".toList
    return fieldIsRelation && modelHasDefaultOrdering &&
      endsAtStoredAttr && notPkShortcut
    -- impl-end

prove_correct orderingExpansionDecision by
  loom_solve
  simp [appendRelatedDefaultOrdering]
```

Prepatch bug re-encoded as an attack: `True`.

SAME-SPEC: confirmed True for all 8 attacks + positive control via swebench_unified.markers.same_spec with get_backend('velvet').language. Command: python -c "from swebench_unified.markers import same_spec; from swebench_unified.backends import get_backend; b=get_backend('velvet'); print(same_spec(open(SRC).read(), open(ATK).read(), b.language))" — impl region only differs; axioms/pure/pre/post byte-identical.

VERIFY: `bash scripts/lean_verify.sh <f>.lean`, run concurrently ≤4/batch (batch1: pos_control,atk_1,atk_2,atk_3; batch2: atk_4..atk_7; batch3: atk_8). Results (exit codes): pos_control=0 (VERIFIES), atk_1=1, atk_2=1, atk_3=1, atk_4=1, atk_5=1, atk_6=1, atk_7=1, atk_8=1. All wrong impls REJECTED; positive control verifies.

### ATTACK CLASSES (all same-spec, all rejected):
- atk_1 prepatch bug: `fieldAttr != some lookup` (whole joined path) instead of terminal segment. Fails ensures with residual goal `... fieldAttr != some lookup ... = ... fieldAttr != some (terminalSegment segments) ...`. This is the exact gold prepatch guard; PREPATCH REPRODUCED and refuted by the spec (G-DIFF holds).
- atk_2 boundary: compares against `segments.head!` (first segment) not last.
- atk_3 control-flow-effect: `return false` (drops the whole decision) — residual goal `fieldIsRelation=true -> modelHasDefaultOrdering=true -> ¬fieldAttr=some(terminalSegment segments) -> lookup=['p','k']`, unprovable.
- atk_4 partial-domain: drops the `lookup != pk` conjunct.
- atk_5 ungrounded-oracle echo: `return appendRelatedDefaultOrdering ...` directly. Does NOT verify — the bundle's proof script (loom_solve; simp [appendRelatedDefaultOrdering]) closes the goal for the concrete `&&` form; the direct echo leaves `error: No goals to be solved`. (Even had it verified it would be gold-equivalent, hence not a weakness.)
- atk_6 negated discriminator: `==` instead of `!=` on the attr conjunct.
- atk_7 boundary: `segments.reverse.head!` — semantically equal to getLast! but NOT definitionally reducible by the pinned proof script, so it fails to verify (unsolved goals). Confirms the spec's proof does not admit off-form variants.
- atk_8: drops the `fieldIsRelation` conjunct.

run_resolve: NOT invoked — protocol step 2 requires a materialized+resolved patch ONLY for a same-spec impl that VERIFIES. Zero such impls exist, so there is no verify⇏correct exhibit to run. (≥5 distinct verifying-wrong-impl requirement is vacuously moot because the exact-equality postcondition admits no verifying wrong impl; 8 distinct attacks were still authored, same-spec-checked, and machine-verified as rejected.)

REFINEMENT AUDIT: meta.json axioms=[], deep_model_references=[], additional_change_sites=[]. refinement.md legs are all I (A2,A3,A5,A6) or R (A1) with the changed conjunct A4 modeled deeply (terminalSegment/appendRelatedDefaultOrdering) — no consumed axiom, no A-reference deep model, no kind-3. Sole callee _setup_joins is unchanged and shared by both branches (context, not consumed contract) — correspondence to mapping.md §3 holds. G-CONF legitimately skipped (conf_skip=true): operands resolved only against a live ORM graph, no DB-free R/I shadow; soundness carried by G-VERIFY (positive control) + G-DIFF (atk_1 prepatch refuted).

CONCLUSION: SOUND. The spec is an exact functional equality; verify ⇒ gold behavior. No falsification found across 8 diverse distinct wrong impls (partial-domain, boundary, control-flow-effect, ungrounded-oracle echo, negated-discriminator, prepatch).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE — no same-spec wrong impl verifies, so there is no candidate counterexample and no refined patch to run through the harness. The postcondition is an exact equality `out = appendRelatedDefaultOrdering fieldIsRelation modelHasDefaultOrdering fieldAttr segments lookup`, pinning out to a total boolean spec function over the whole domain (segments ≠ []). Any verifying impl must be extensionally equal to the gold decision, so verify ⇒ behaviorally gold. All 8 same-spec wrong impls (incl. the prepatch whole-path-comparison bug) fail verification; only the correct positive control verifies.
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

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The decision modeled here is a pure boolean function
--  of the resolved field metadata and the lookup path; the machinery that
--  resolves that metadata is unchanged and shared by both branches, so it is
--  not consumed as an outside contract. There is no `axiom` declaration and no
--  A-reference deep model of an outside callee.)
-- axioms-end

-- pure-start
/- A relation lookup is written as a path of segments joined by a separator
   (e.g. `a__b__c` is the three segments `a`, `b`, `c`). The *terminal segment*
   is the last one — the concrete attribute actually named at the end of the
   path. -/
def terminalSegment (segments : List (List Char)) : List Char :=
  segments.getLast!

/- Whether to append a related model's own default ordering for an ordering
   lookup. The default ordering of the pointed-to model is appended only when

     * the resolved field is a relation, AND
     * that model declares a default ordering, AND
     * the field's stored attribute name is NOT the attribute named by the
       TERMINAL segment of the lookup path (when the path ends at the field's
       own stored attribute, the column is ordered directly rather than
       expanding the related model's default ordering), AND
     * the lookup is not the primary-key shortcut `pk`.

   The terminal-segment comparison is what distinguishes a lookup that ends at
   a relation's stored attribute (order directly by that column) from one that
   ends at the relation itself (expand the related model's default ordering). -/
def appendRelatedDefaultOrdering
    (fieldIsRelation modelHasDefaultOrdering : Bool)
    (fieldAttr : Option (List Char))
    (segments : List (List Char)) (lookup : List Char) : Bool :=
  fieldIsRelation && modelHasDefaultOrdering &&
    (fieldAttr != some (terminalSegment segments)) &&
    (lookup != "pk".toList)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method orderingExpansionDecision (fieldIsRelation : Bool) (modelHasDefaultOrdering : Bool) (fieldAttr : Option (List Char)) (segments : List (List Char)) (lookup : List Char) return (out : Bool)
  require segments ≠ []
  ensures out =
    appendRelatedDefaultOrdering fieldIsRelation modelHasDefaultOrdering
      fieldAttr segments lookup
  do
    -- impl-start
    let endsAtStoredAttr := fieldAttr != some (terminalSegment segments)
    let notPkShortcut := lookup != "pk".toList
    return fieldIsRelation && modelHasDefaultOrdering &&
      endsAtStoredAttr && notPkShortcut
    -- impl-end

prove_correct orderingExpansionDecision by
  loom_solve
  simp [appendRelatedDefaultOrdering]
```

Prepatch bug re-encoded as an attack: `True`.

SAME-SPEC: confirmed True for all 8 attacks + positive control via swebench_unified.markers.same_spec with get_backend('velvet').language. Command: python -c "from swebench_unified.markers import same_spec; from swebench_unified.backends import get_backend; b=get_backend('velvet'); print(same_spec(open(SRC).read(), open(ATK).read(), b.language))" — impl region only differs; axioms/pure/pre/post byte-identical.

VERIFY: `bash scripts/lean_verify.sh <f>.lean`, run concurrently ≤4/batch (batch1: pos_control,atk_1,atk_2,atk_3; batch2: atk_4..atk_7; batch3: atk_8). Results (exit codes): pos_control=0 (VERIFIES), atk_1=1, atk_2=1, atk_3=1, atk_4=1, atk_5=1, atk_6=1, atk_7=1, atk_8=1. All wrong impls REJECTED; positive control verifies.

### ATTACK CLASSES (all same-spec, all rejected):
- atk_1 prepatch bug: `fieldAttr != some lookup` (whole joined path) instead of terminal segment. Fails ensures with residual goal `... fieldAttr != some lookup ... = ... fieldAttr != some (terminalSegment segments) ...`. This is the exact gold prepatch guard; PREPATCH REPRODUCED and refuted by the spec (G-DIFF holds).
- atk_2 boundary: compares against `segments.head!` (first segment) not last.
- atk_3 control-flow-effect: `return false` (drops the whole decision) — residual goal `fieldIsRelation=true -> modelHasDefaultOrdering=true -> ¬fieldAttr=some(terminalSegment segments) -> lookup=['p','k']`, unprovable.
- atk_4 partial-domain: drops the `lookup != pk` conjunct.
- atk_5 ungrounded-oracle echo: `return appendRelatedDefaultOrdering ...` directly. Does NOT verify — the bundle's proof script (loom_solve; simp [appendRelatedDefaultOrdering]) closes the goal for the concrete `&&` form; the direct echo leaves `error: No goals to be solved`. (Even had it verified it would be gold-equivalent, hence not a weakness.)
- atk_6 negated discriminator: `==` instead of `!=` on the attr conjunct.
- atk_7 boundary: `segments.reverse.head!` — semantically equal to getLast! but NOT definitionally reducible by the pinned proof script, so it fails to verify (unsolved goals). Confirms the spec's proof does not admit off-form variants.
- atk_8: drops the `fieldIsRelation` conjunct.

run_resolve: NOT invoked — protocol step 2 requires a materialized+resolved patch ONLY for a same-spec impl that VERIFIES. Zero such impls exist, so there is no verify⇏correct exhibit to run. (≥5 distinct verifying-wrong-impl requirement is vacuously moot because the exact-equality postcondition admits no verifying wrong impl; 8 distinct attacks were still authored, same-spec-checked, and machine-verified as rejected.)

REFINEMENT AUDIT: meta.json axioms=[], deep_model_references=[], additional_change_sites=[]. refinement.md legs are all I (A2,A3,A5,A6) or R (A1) with the changed conjunct A4 modeled deeply (terminalSegment/appendRelatedDefaultOrdering) — no consumed axiom, no A-reference deep model, no kind-3. Sole callee _setup_joins is unchanged and shared by both branches (context, not consumed contract) — correspondence to mapping.md §3 holds. G-CONF legitimately skipped (conf_skip=true): operands resolved only against a live ORM graph, no DB-free R/I shadow; soundness carried by G-VERIFY (positive control) + G-DIFF (atk_1 prepatch refuted).

CONCLUSION: SOUND. The spec is an exact functional equality; verify ⇒ gold behavior. No falsification found across 8 diverse distinct wrong impls (partial-domain, boundary, control-flow-effect, ungrounded-oracle echo, negated-discriminator, prepatch).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) assessment for django__django-13033 velvet bundle.

SPEC REGION IDENTITY: swebench_unified.markers.same_spec(Solution.lean, Solution_prepatch.lean, VelvetBackend) = True. The spec view (pure defs terminalSegment/appendRelatedDefaultOrdering + method signature + require/ensures) is byte-identical between the two files; only the impl block differs (prepatch: `fieldAttr != some lookup` = whole path; postpatch: `fieldAttr != some (terminalSegment segments)` = terminal segment). Solution.lean elaborates cleanly under lean_verify.sh (exit 0), so the modeled impl proves correct against the pinned spec.

REAL CALLEE (base_commit a59de6e8...): SQLCompiler.find_ordering_name guard, django/db/models/sql/compiler.py. Base: `field.is_relation and opts.ordering and getattr(field,'attname',None) != name and name != 'pk'`. GOLD PATCH changes `!= name` to `!= pieces[-1]` (pieces = name.split(LOOKUP_SEP)). The Solution models the POST-PATCH (fixed) guard, which is correct for a spec.

FAITHFULNESS OF appendRelatedDefaultOrdering vs the post-patch guard boolean:
- fieldIsRelation <-> field.is_relation (Bool, identity).
- modelHasDefaultOrdering <-> truthiness of opts.ordering. The guard consumes only truthiness inside an `if`, so Bool abstraction is exact — no realizable input where the outcome differs.
- fieldAttr != some (terminalSegment segments) <-> getattr(field,'attname',None) != pieces[-1]. terminalSegment = List.getLast! <-> pieces[-1]; precondition segments != [] mirrors split() always yielding >=1 element (so it excludes NO real input — not over-strong). Option modeling is faithful: None != <str> (True) <-> none != some _ (True); present attr str s <-> some s.toList with == on List Char <-> str equality.
- lookup != "pk".toList <-> name != 'pk'.
- Python `and` chain evaluated for a boolean branch reduces to conjunction of operand truthiness = the Lean && chain of Bools; observationally identical.

OVER-STRICTNESS CHECK: The only structural liberty is that the Lean model takes `lookup` and `segments` as independent parameters whereas in the repo pieces = name.split('__') (so segments is derived from lookup). This WIDENS the domain of the modeled function relative to reality; it can never make the modeled function REJECT/disagree on a realizable (name, pieces) pair. Hence no spec drift and no diverging realizable input. Precondition is exactly as weak as the real invariant (split >= 1 element). I searched for an input where model != real callee on the modeled decision and found none.

G-CONF is legitimately skipped (conf_skip=true): the discriminating operands are resolved via _setup_joins against a live ORM model graph, with no DB-free R/I shadow; soundness carried by G-VERIFY + G-DIFF (prepatch fails postcondition exactly on a multi-segment lookup ending at the field's stored attribute), django__django-13315 precedent. This is a modeling boundary, not a faithfulness defect.

VERDICT: FAITHFUL — the modeled function agrees with the real post-patch callee on every realizable input; the spec is neither too strong nor drifted.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (rep.passed=True, no hard failures) and markers.same_spec(Solution, Solution_prepatch)=True (spec region byte-identical). Spec view contains only an abstract boolean predicate: method orderingExpansionDecision / appendRelatedDefaultOrdering / terminalSegment over abstract params (fieldIsRelation, modelHasDefaultOrdering, fieldAttr, segments, lookup). No leakage of the gold edit beyond the public problem_statement:
- No repo file path (django/db/models/sql/compiler.py), no repo function name (find_ordering_name), no patched repo symbols (pieces, attname, opts.ordering, is_relation as identifiers embedding the change). Symbol-collision check clean.
- No gold-patch line reproduced; no diff markers (@@, +++, diff --git, index).
- Comments describe intended semantics (terminal-segment vs whole-path comparison, expand-default-ordering guard) without any bug/fix/before-after narration; _NARRATION_RE finds nothing.
- The discriminating behavior (order_by ending at the FK's stored '_id' attribute must order that column directly rather than expanding the related model's default ordering, vs ordering by the relation itself which expands it) is ALREADY public in the problem_statement, which explicitly contrasts order_by('record__root_id'), order_by('record__root__id'), and order_by('record__root') and their differing SQL. The spec merely encodes the correct predicate abstractly, as any faithful spec must, without revealing localization or the concrete edit (pieces[-1] vs name). A solver still must locate find_ordering_name and derive the terminal-segment change themselves.
Conclusion: spec view reveals no edit information beyond the public problem_statement.

- No repo file path (django/db/models/sql/compiler.py), no repo function name (find_ordering_name), no patched repo symbols (pieces, attname, opts.ordering, is_relation as identifiers embedding the change). Symbol-collision check clean.
- No gold-patch line reproduced; no diff markers (@@, +++, diff --git, index).
- Comments describe intended semantics (terminal-segment vs whole-path comparison, expand-default-ordering guard) without any bug/fix/before-after narration; _NARRATION_RE finds nothing.
- The discriminating behavior (order_by ending at the FK's stored '_id' attribute must order that column directly rather than expanding the related model's default ordering, vs ordering by the relation itself which expands it) is ALREADY public in the problem_statement, which explicitly contrasts order_by('record__root_id'), order_by('record__root__id'), and order_by('record__root') and their differing SQL. The spec merely encodes the correct predicate abstractly, as any faithful spec must, without revealing localization or the concrete edit (pieces[-1] vs name). A solver still must locate find_ordering_name and derive the terminal-segment change themselves.
Conclusion: spec view reveals no edit information beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
