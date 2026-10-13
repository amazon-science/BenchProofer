# P2 adversarial audit — django__django-12406

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None — no verifying-but-wrong impl exists. Both postconditions are TOTAL functional equations over the methods' own Bool inputs with EMPTY preconditions and ZERO axiom/opaque/oracle symbols (axioms + pure regions empty): relationBlankFlag ensures out = modelAllowsBlank; blankChoiceOffered ensures out = !((required && initialPresent) || (widgetIsRadio && !blank)). Any impl that verifies must compute exactly the gold boolean function on the entire domain, so verify => correct; answer-key echo is structurally impossible. All 8 distinct wrong impls were rejected with genuine 'unsolved goals' at prove_correct.
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
 -- (No axiomatized callees. Both modeled functions are changed functions whose
@@ -66,7 +66,7 @@
   ensures out = !((required && initialPresent) || (widgetIsRadio && !blank))
   do
     -- impl-start
-    return !((required && initialPresent) || (widgetIsRadio && !blank))
+    return !(required && initialPresent)
     -- impl-end
 
 prove_correct blankChoiceOffered by
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
 -- (No axiomatized callees. Both modeled functions are changed functions whose
@@ -34,7 +34,7 @@
   ensures out = modelAllowsBlank
   do
     -- impl-start
-    return modelAllowsBlank
+    return false
     -- impl-end
 
 prove_correct relationBlankFlag by
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
 -- (No axiomatized callees. Both modeled functions are changed functions whose
@@ -66,7 +66,7 @@
   ensures out = !((required && initialPresent) || (widgetIsRadio && !blank))
   do
     -- impl-start
-    return !((required && initialPresent) || (widgetIsRadio && !blank))
+    return !(widgetIsRadio && !blank)
     -- impl-end
 
 prove_correct blankChoiceOffered by
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
 -- (No axiomatized callees. Both modeled functions are changed functions whose
@@ -66,7 +66,7 @@
   ensures out = !((required && initialPresent) || (widgetIsRadio && !blank))
   do
     -- impl-start
-    return !((required && initialPresent) || (widgetIsRadio && !blank))
+    return true
     -- impl-end
 
 prove_correct blankChoiceOffered by
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
 -- (No axiomatized callees. Both modeled functions are changed functions whose
@@ -66,7 +66,7 @@
   ensures out = !((required && initialPresent) || (widgetIsRadio && !blank))
   do
     -- impl-start
-    return !((required && initialPresent) || (widgetIsRadio && !blank))
+    return !((required || initialPresent) || (widgetIsRadio && !blank))
     -- impl-end
 
 prove_correct blankChoiceOffered by
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
 -- (No axiomatized callees. Both modeled functions are changed functions whose
@@ -34,7 +34,7 @@
   ensures out = modelAllowsBlank
   do
     -- impl-start
-    return modelAllowsBlank
+    return !modelAllowsBlank
     -- impl-end
 
 prove_correct relationBlankFlag by
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
 -- (No axiomatized callees. Both modeled functions are changed functions whose
@@ -66,7 +66,7 @@
   ensures out = !((required && initialPresent) || (widgetIsRadio && !blank))
   do
     -- impl-start
-    return !((required && initialPresent) || (widgetIsRadio && !blank))
+    return ((required && initialPresent) || (widgetIsRadio && !blank))
     -- impl-end
 
 prove_correct blankChoiceOffered by
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
 -- (No axiomatized callees. Both modeled functions are changed functions whose
@@ -66,7 +66,7 @@
   ensures out = !((required && initialPresent) || (widgetIsRadio && !blank))
   do
     -- impl-start
-    return !((required && initialPresent) || (widgetIsRadio && !blank))
+    return !((required && initialPresent) || (widgetIsRadio && blank))
     -- impl-end
 
 prove_correct blankChoiceOffered by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. Both modeled functions are changed functions whose
--  new logic is a pure boolean combination of their inputs, modeled deeply.
--  The widget-kind test and the initial-value-present test are observed only
--  through their boolean results, which are the inputs here.)
-- axioms-end

-- pure-start
-- (No pure helpers needed: each decision is a closed boolean expression.)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- When a model relation builds the choice field used to pick a related object,
   it must hand that field the model's own "a blank selection is permitted"
   flag, so the field can decide downstream whether to present an unfilled
   option. The forwarded flag is exactly the model's declared blank-allowed
   flag — nothing more, nothing less. The model's flag is read-only (not
   `mut`); this query computes a single boolean and mutates nothing
   (directive 5). Input and result are modeled as `Bool`. -/
method relationBlankFlag (modelAllowsBlank : Bool) return (out : Bool)
  ensures out = modelAllowsBlank
  do
    -- impl-start
    return modelAllowsBlank
    -- impl-end

prove_correct relationBlankFlag by
  loom_solve

/- A choice field for picking one related object decides whether to present a
   leading, unfilled "blank" option. That option is presented unless the field
   determines it would be misleading. It is withheld in either of two
   situations:

     * the field is required AND already carries an initial value (a blank
       option would invite clearing a value that must be supplied); or
     * the field renders with a radio widget AND a blank selection is not
       permitted (a radio widget has an inherent unfilled state, so an extra
       blank radio would look like a valid choice when it is not).

   Otherwise the blank option is presented. The result is `true` exactly when
   the blank option is offered.

   Four boolean inputs are observed: whether the field is required, whether an
   initial value is present, whether the widget is a radio widget, and whether a
   blank selection is permitted. All are read-only (not `mut`); the decision
   mutates nothing (directive 5). The radio-widget kind and the
   blank-permitted flag are observed as DISTINCT inputs because the second
   withholding rule must DISCRIMINATE between a radio field that permits blank
   (option kept) and one that does not (option withheld). All inputs and the
   result are `Bool`. -/
method blankChoiceOffered (required : Bool) (initialPresent : Bool) (widgetIsRadio : Bool) (blank : Bool) return (out : Bool)
  ensures out = !((required && initialPresent) || (widgetIsRadio && !blank))
  do
    -- impl-start
    return !((required && initialPresent) || (widgetIsRadio && !blank))
    -- impl-end

prove_correct blankChoiceOffered by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

Protocol executed. same_spec(velvet) = True for all 8 attacks + both positive controls. Verification via `bash scripts/lean_verify.sh <f>` run concurrently in background batches (<=4 at a time) from project root.

### RESULTS (sort of results.log):
  positive_control exit=0 (gold Solution.lean, byte-identical spec)
  pos2             exit=0 (structurally-different CORRECT: De-Morgan'd site A `(!(required && initialPresent)) && (!(widgetIsRadio && !blank))` + site B `(modelAllowsBlank || false)` — proves spec non-vacuous, admits genuine alternative impls)
  atk_1 exit=1  siteA `!(required && initialPresent)` — partial-domain, prepatch site-A bug (radio rule dropped)
  atk_2 exit=1  siteB `false` — prepatch site-B bug (blank flag not forwarded)
  atk_3 exit=1  siteA `!(widgetIsRadio && !blank)` — partial-domain (first conjunct dropped)
  atk_4 exit=1  siteA `true` — ungrounded constant
  atk_5 exit=1  siteA `!((required || initialPresent) || (widgetIsRadio && !blank))` — operator-swap (&& -> ||)
  atk_6 exit=1  siteB `!modelAllowsBlank` — site-B flag inverted (boundary)
  atk_7 exit=1  siteA `((required && initialPresent) || (widgetIsRadio && !blank))` — missing outer negation, offered<->withheld swap (control-flow-effect)
  atk_8 exit=1  siteA `!((required && initialPresent) || (widgetIsRadio && blank))` — boundary polarity (blank instead of !blank)

All exit=1 confirmed as real spec-verification failures: `error: unsolved goals` at line 72:33 (site A) for atk_1/3/4/5/7/8 and line 40:32 (site B) for atk_2/6 — the prove_correct/loom_solve obligations, NOT syntax errors from the edits. Every attack edits ONLY the impl region(s); axioms/pure/pre/post byte-identical (same_spec True).

STEP 2 (materialize faithful refined patch + run_resolve): NO triggering candidate — zero wrong impls verified, so there is no verifying-but-wrong impl whose faithful patch could fail to resolve. Requirement vacuously satisfied; nothing to run through run_resolve.

PREPATCH: both leg bugs reproduced. Solution_prepatch.lean (site A radio rule absent, `return !(required && initialPresent)`) == my atk_1 shape, fails site-A spec; Solution_prepatch_2.lean (site B `return false`) == my atk_2 shape, fails site-B spec. G-DIFF genuine — identical frozen spec rejects both buggy impls.

REFINEMENT AUDIT (step 3): refinement.md legs A1(R)/A2(I) for site B and B1(R)/B2(I)/B3(I)/B4(I+R) for site A — all R/I, NO A-consumed, NO A-reference, NO kind-3. mapping.md §3 confirms NO axiomatized callees (axioms region empty; isinstance/is-not-None reduced to boolean inputs at the bridge; Field.__init__ abstracted-away not axiomatized; ModelChoiceIterator.__iter__ is the observation bridge `empty_label is not None <-> out`, unchanged by patch). So there are no A-legs to break — the A-leg focus is vacuous here by construction. patch.diff verified against refinement.md hunks: site B adds `'blank': self.blank` (identity forward = A2/site-B model); site A rewrites the empty_label guard to `(required and initial is not None) or (isinstance(self.widget, RadioSelect) and not blank)` observed as `empty_label is not None` (= negated disjunction = site-A model). Correspondence holds exactly.

CONCLUSION: SOUND. Spec is TIGHT (strongest possible shape: closed total boolean equations, no oracle to echo). >=5 (8) distinct verifying-attack attempts run and none verified; verify => correct holds; no BROKEN condition, no INCONCLUSIVE gap (all needed verifications completed, no resolve run was needed).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None — no verifying-but-wrong impl exists. Both postconditions are TOTAL functional equations over the methods' own Bool inputs with EMPTY preconditions and ZERO axiom/opaque/oracle symbols (axioms + pure regions empty): relationBlankFlag ensures out = modelAllowsBlank; blankChoiceOffered ensures out = !((required && initialPresent) || (widgetIsRadio && !blank)). Any impl that verifies must compute exactly the gold boolean function on the entire domain, so verify => correct; answer-key echo is structurally impossible. All 8 distinct wrong impls were rejected with genuine 'unsolved goals' at prove_correct.
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

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. Both modeled functions are changed functions whose
--  new logic is a pure boolean combination of their inputs, modeled deeply.
--  The widget-kind test and the initial-value-present test are observed only
--  through their boolean results, which are the inputs here.)
-- axioms-end

-- pure-start
-- (No pure helpers needed: each decision is a closed boolean expression.)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- When a model relation builds the choice field used to pick a related object,
   it must hand that field the model's own "a blank selection is permitted"
   flag, so the field can decide downstream whether to present an unfilled
   option. The forwarded flag is exactly the model's declared blank-allowed
   flag — nothing more, nothing less. The model's flag is read-only (not
   `mut`); this query computes a single boolean and mutates nothing
   (directive 5). Input and result are modeled as `Bool`. -/
method relationBlankFlag (modelAllowsBlank : Bool) return (out : Bool)
  ensures out = modelAllowsBlank
  do
    -- impl-start
    return modelAllowsBlank
    -- impl-end

prove_correct relationBlankFlag by
  loom_solve

/- A choice field for picking one related object decides whether to present a
   leading, unfilled "blank" option. That option is presented unless the field
   determines it would be misleading. It is withheld in either of two
   situations:

     * the field is required AND already carries an initial value (a blank
       option would invite clearing a value that must be supplied); or
     * the field renders with a radio widget AND a blank selection is not
       permitted (a radio widget has an inherent unfilled state, so an extra
       blank radio would look like a valid choice when it is not).

   Otherwise the blank option is presented. The result is `true` exactly when
   the blank option is offered.

   Four boolean inputs are observed: whether the field is required, whether an
   initial value is present, whether the widget is a radio widget, and whether a
   blank selection is permitted. All are read-only (not `mut`); the decision
   mutates nothing (directive 5). The radio-widget kind and the
   blank-permitted flag are observed as DISTINCT inputs because the second
   withholding rule must DISCRIMINATE between a radio field that permits blank
   (option kept) and one that does not (option withheld). All inputs and the
   result are `Bool`. -/
method blankChoiceOffered (required : Bool) (initialPresent : Bool) (widgetIsRadio : Bool) (blank : Bool) return (out : Bool)
  ensures out = !((required && initialPresent) || (widgetIsRadio && !blank))
  do
    -- impl-start
    return !((required && initialPresent) || (widgetIsRadio && !blank))
    -- impl-end

prove_correct blankChoiceOffered by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

Protocol executed. same_spec(velvet) = True for all 8 attacks + both positive controls. Verification via `bash scripts/lean_verify.sh <f>` run concurrently in background batches (<=4 at a time) from project root.

### RESULTS (sort of results.log):
  positive_control exit=0 (gold Solution.lean, byte-identical spec)
  pos2             exit=0 (structurally-different CORRECT: De-Morgan'd site A `(!(required && initialPresent)) && (!(widgetIsRadio && !blank))` + site B `(modelAllowsBlank || false)` — proves spec non-vacuous, admits genuine alternative impls)
  atk_1 exit=1  siteA `!(required && initialPresent)` — partial-domain, prepatch site-A bug (radio rule dropped)
  atk_2 exit=1  siteB `false` — prepatch site-B bug (blank flag not forwarded)
  atk_3 exit=1  siteA `!(widgetIsRadio && !blank)` — partial-domain (first conjunct dropped)
  atk_4 exit=1  siteA `true` — ungrounded constant
  atk_5 exit=1  siteA `!((required || initialPresent) || (widgetIsRadio && !blank))` — operator-swap (&& -> ||)
  atk_6 exit=1  siteB `!modelAllowsBlank` — site-B flag inverted (boundary)
  atk_7 exit=1  siteA `((required && initialPresent) || (widgetIsRadio && !blank))` — missing outer negation, offered<->withheld swap (control-flow-effect)
  atk_8 exit=1  siteA `!((required && initialPresent) || (widgetIsRadio && blank))` — boundary polarity (blank instead of !blank)

All exit=1 confirmed as real spec-verification failures: `error: unsolved goals` at line 72:33 (site A) for atk_1/3/4/5/7/8 and line 40:32 (site B) for atk_2/6 — the prove_correct/loom_solve obligations, NOT syntax errors from the edits. Every attack edits ONLY the impl region(s); axioms/pure/pre/post byte-identical (same_spec True).

STEP 2 (materialize faithful refined patch + run_resolve): NO triggering candidate — zero wrong impls verified, so there is no verifying-but-wrong impl whose faithful patch could fail to resolve. Requirement vacuously satisfied; nothing to run through run_resolve.

PREPATCH: both leg bugs reproduced. Solution_prepatch.lean (site A radio rule absent, `return !(required && initialPresent)`) == my atk_1 shape, fails site-A spec; Solution_prepatch_2.lean (site B `return false`) == my atk_2 shape, fails site-B spec. G-DIFF genuine — identical frozen spec rejects both buggy impls.

REFINEMENT AUDIT (step 3): refinement.md legs A1(R)/A2(I) for site B and B1(R)/B2(I)/B3(I)/B4(I+R) for site A — all R/I, NO A-consumed, NO A-reference, NO kind-3. mapping.md §3 confirms NO axiomatized callees (axioms region empty; isinstance/is-not-None reduced to boolean inputs at the bridge; Field.__init__ abstracted-away not axiomatized; ModelChoiceIterator.__iter__ is the observation bridge `empty_label is not None <-> out`, unchanged by patch). So there are no A-legs to break — the A-leg focus is vacuous here by construction. patch.diff verified against refinement.md hunks: site B adds `'blank': self.blank` (identity forward = A2/site-B model); site A rewrites the empty_label guard to `(required and initial is not None) or (isinstance(self.widget, RadioSelect) and not blank)` observed as `empty_label is not None` (= negated disjunction = site-A model). Correspondence holds exactly.

CONCLUSION: SOUND. Spec is TIGHT (strongest possible shape: closed total boolean equations, no oracle to echo). >=5 (8) distinct verifying-attack attempts run and none verified; verify => correct holds; no BROKEN condition, no INCONCLUSIVE gap (all needed verifications completed, no resolve run was needed).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) audit for django__django-12406 velvet bundle. same_spec confirmed byte-identical spec view between Solution.lean and both Solution_prepatch.lean and Solution_prepatch_2.lean. Solution.lean verifies (lean_verify.sh exit 0). Two modeled sites, both CHANGED functions modeled deeply (no axioms). Site B relationBlankFlag: ensures out=modelAllowsBlank; gold patch adds 'blank': self.blank to forwarded kwargs — pure identity forwarding, exact match, no divergence possible. Site A blankChoiceOffered: ensures out=!((required&&initialPresent)||(widgetIsRadio&&!blank)) modeling empty_label is not None. Empirically validated by cloning at base_commit 335c9c94, applying the gold patch, and instantiating the REAL patched ModelChoiceField over all 16 boolean combinations of (required, initial-present, radio-widget, blank), comparing field.empty_label is not None to the modeled formula: FULL AGREEMENT on all 16 combos, zero mismatches. Bijections match the observer ModelChoiceIterator.__iter__ (yields leading blank iff empty_label is not None). Abstraction boundaries (isinstance RadioSelect test, initial is not None test) reduced to booleans faithfully since the decision reads only their truth values. No input found where the modeled function disagrees with the real callee. Spec is neither too strong nor drifting.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (velvet Solution.lean, computed via markers.spec_view) contains two methods: relationBlankFlag (ensures out = modelAllowsBlank) and blankChoiceOffered (ensures out = !((required && initialPresent) || (widgetIsRadio && !blank))). Judged against the SOLVER-VISIBLE problem_statement ONLY (not hints_text).

Mechanical G-LEAK screen: PASS (rep.passed=True, no hard_failures). No diff markers, no reproduced gold-patch lines, no patched file path (related.py/models.py) or dotted module path, no spec-view identifier or docstring naming a patched repo symbol (formfield, empty_label, ModelChoiceField, ForeignKey, RadioSelect all absent from spec view), no bug/fix/pre-patch narration.

Semantic gold-reconstruction check: the DISCRIMINATING gold edit — 'radio widget + blank not permitted => withhold the blank option' — is ALREADY public in the problem_statement title/body ('RadioSelect widget for foreign keys should not present a blank option if blank=False on the model'; 'radioselect has an inherent unfilled state'). The spec's radio disjunct (widgetIsRadio && !blank) and the model-blank-flag forwarding (relationBlankFlag) therefore reveal nothing beyond the public task. The required&&initialPresent disjunct is NOT in problem_statement but is PRE-EXISTING/unchanged behavior carried into the spec (the pre-patch already withheld on required and initial is not None), not the gold edit, so it does not leak edit localization.

Auditor-only files refinement.md and mapping.md quote the gold hunks, changed file paths, and pre-patch behavior verbatim, but these are NOT part of the consumer spec view (only Solution.lean's projected spec view is consumer-visible) and are correctly out of scope for G-LEAK/G-PANEL-3.

same_spec: Solution.lean spec regions are byte-identical to both Solution_prepatch.lean and Solution_prepatch_2.lean (verified True/True), so the prepatch differentials differ only in impl, not spec — no leak channel there. Conclusion: the spec fully specifies correct behavior (as any faithful spec must) without disclosing the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
