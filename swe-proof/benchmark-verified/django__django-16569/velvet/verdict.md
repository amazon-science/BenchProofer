# P2 adversarial audit — django__django-16569

**Backend:** `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_5.lean` |

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
 /- No unchanged callee is axiomatized for this bundle. The behaviour under spec
@@ -81,18 +81,17 @@
   ensures position = none → out = Except.ok (enabled && offerOnExtra)
   do
     -- impl-start
-    -- Short-circuiting decision mirroring `enabled AND (offerOnExtra OR P)`,
-    -- where the position test P is taken only when the control is enabled and is
-    -- not already offered on surplus rows. The test guards the order comparison
-    -- against an absent position: with no position the test yields `false`, so
-    -- the decision stays a verdict instead of attempting an undefined comparison.
-    let mut decision : Bool := false
+    let mut result : Except ControlErr Bool := Except.ok false
     if enabled = true then
       if offerOnExtra = true then
-        decision := true
+        result := Except.ok true
       else
-        decision := positionWithinInitial position initialCount
-    return Except.ok decision
+        result := match position with
+          | some i => Except.ok (decide (i < initialCount))
+          | none   => Except.error ControlErr.positionComparisonUndefined
+    else
+      result := Except.ok false
+    return result
     -- impl-end
 
 prove_correct deletionFieldDecision by
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
 /- No unchanged callee is axiomatized for this bundle. The behaviour under spec
@@ -81,18 +81,7 @@
   ensures position = none → out = Except.ok (enabled && offerOnExtra)
   do
     -- impl-start
-    -- Short-circuiting decision mirroring `enabled AND (offerOnExtra OR P)`,
-    -- where the position test P is taken only when the control is enabled and is
-    -- not already offered on surplus rows. The test guards the order comparison
-    -- against an absent position: with no position the test yields `false`, so
-    -- the decision stays a verdict instead of attempting an undefined comparison.
-    let mut decision : Bool := false
-    if enabled = true then
-      if offerOnExtra = true then
-        decision := true
-      else
-        decision := positionWithinInitial position initialCount
-    return Except.ok decision
+    return Except.ok (enabled && offerOnExtra)
     -- impl-end
 
 prove_correct deletionFieldDecision by
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
 /- No unchanged callee is axiomatized for this bundle. The behaviour under spec
@@ -81,18 +81,10 @@
   ensures position = none → out = Except.ok (enabled && offerOnExtra)
   do
     -- impl-start
-    -- Short-circuiting decision mirroring `enabled AND (offerOnExtra OR P)`,
-    -- where the position test P is taken only when the control is enabled and is
-    -- not already offered on surplus rows. The test guards the order comparison
-    -- against an absent position: with no position the test yields `false`, so
-    -- the decision stays a verdict instead of attempting an undefined comparison.
-    let mut decision : Bool := false
-    if enabled = true then
-      if offerOnExtra = true then
-        decision := true
-      else
-        decision := positionWithinInitial position initialCount
-    return Except.ok decision
+    let posTest : Bool := match position with
+      | some i => decide (i <= initialCount)
+      | none   => false
+    return Except.ok (enabled && (offerOnExtra || posTest))
     -- impl-end
 
 prove_correct deletionFieldDecision by
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
 /- No unchanged callee is axiomatized for this bundle. The behaviour under spec
@@ -81,17 +81,9 @@
   ensures position = none → out = Except.ok (enabled && offerOnExtra)
   do
     -- impl-start
-    -- Short-circuiting decision mirroring `enabled AND (offerOnExtra OR P)`,
-    -- where the position test P is taken only when the control is enabled and is
-    -- not already offered on surplus rows. The test guards the order comparison
-    -- against an absent position: with no position the test yields `false`, so
-    -- the decision stays a verdict instead of attempting an undefined comparison.
     let mut decision : Bool := false
     if enabled = true then
-      if offerOnExtra = true then
-        decision := true
-      else
-        decision := positionWithinInitial position initialCount
+      decision := true
     return Except.ok decision
     -- impl-end
 
```

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 /- No unchanged callee is axiomatized for this bundle. The behaviour under spec
@@ -81,18 +81,7 @@
   ensures position = none → out = Except.ok (enabled && offerOnExtra)
   do
     -- impl-start
-    -- Short-circuiting decision mirroring `enabled AND (offerOnExtra OR P)`,
-    -- where the position test P is taken only when the control is enabled and is
-    -- not already offered on surplus rows. The test guards the order comparison
-    -- against an absent position: with no position the test yields `false`, so
-    -- the decision stays a verdict instead of attempting an undefined comparison.
-    let mut decision : Bool := false
-    if enabled = true then
-      if offerOnExtra = true then
-        decision := true
-      else
-        decision := positionWithinInitial position initialCount
-    return Except.ok decision
+    return shouldOfferDeletion enabled offerOnExtra position initialCount
     -- impl-end
 
 prove_correct deletionFieldDecision by
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
 /- No unchanged callee is axiomatized for this bundle. The behaviour under spec
@@ -81,18 +81,8 @@
   ensures position = none → out = Except.ok (enabled && offerOnExtra)
   do
     -- impl-start
-    -- Short-circuiting decision mirroring `enabled AND (offerOnExtra OR P)`,
-    -- where the position test P is taken only when the control is enabled and is
-    -- not already offered on surplus rows. The test guards the order comparison
-    -- against an absent position: with no position the test yields `false`, so
-    -- the decision stays a verdict instead of attempting an undefined comparison.
-    let mut decision : Bool := false
-    if enabled = true then
-      if offerOnExtra = true then
-        decision := true
-      else
-        decision := positionWithinInitial position initialCount
-    return Except.ok decision
+    let posTest : Bool := positionWithinInitial position initialCount
+    return Except.ok ((enabled && offerOnExtra) || (enabled && posTest))
     -- impl-end
 
 prove_correct deletionFieldDecision by
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
 /- No unchanged callee is axiomatized for this bundle. The behaviour under spec
@@ -81,18 +81,10 @@
   ensures position = none → out = Except.ok (enabled && offerOnExtra)
   do
     -- impl-start
-    -- Short-circuiting decision mirroring `enabled AND (offerOnExtra OR P)`,
-    -- where the position test P is taken only when the control is enabled and is
-    -- not already offered on surplus rows. The test guards the order comparison
-    -- against an absent position: with no position the test yields `false`, so
-    -- the decision stays a verdict instead of attempting an undefined comparison.
-    let mut decision : Bool := false
-    if enabled = true then
-      if offerOnExtra = true then
-        decision := true
-      else
-        decision := positionWithinInitial position initialCount
-    return Except.ok decision
+    let posTest : Bool := match position with
+      | some i => decide (i < initialCount)
+      | none   => true
+    return Except.ok (enabled && (offerOnExtra || posTest))
     -- impl-end
 
 prove_correct deletionFieldDecision by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No unchanged callee is axiomatized for this bundle. The behaviour under spec
   is a pure decision over four scalar inputs: whether a per-row removal control
   is enabled at all, whether it is also offered on surplus rows, the optional
   ordinal position of the row, and how many rows are pre-populated. The widget
   that is ultimately attached once the decision is positive is a shared
   continuation that does not influence the decision, so nothing about it is
   assumed: no consumed axiom and no deep-model reference to a foreign callee. -/
-- axioms-end

-- pure-start
/- The outcome shape of the decision. A well-formed decision always yields a
   verdict (`Except.ok`). The single error constructor records the one outcome a
   correct decision must NEVER produce: the order comparison being attempted
   without an ordinal position to compare, which is undefined and must instead be
   treated as "no position precedes the threshold". A correct result is always a
   verdict, never this error. -/
inductive ControlErr where
  | positionComparisonUndefined
  deriving DecidableEq

/- The contribution of the position test: a present position counts only when it
   lies strictly below the pre-populated count; an absent position contributes
   nothing (it does not enable the control, and — crucially — it is NOT a reason
   to abandon the decision). This is the guarded form of the ordinal comparison
   (mapping.md §3; refinement.md §A). -/
def positionWithinInitial (position : Option Nat) (initialCount : Nat) : Bool :=
  match position with
  | some i => decide (i < initialCount)
  | none   => false

/- The desired decision: the removal control is offered exactly when it is
   enabled AND (it is offered on surplus rows OR the position lies within the
   pre-populated rows). With an absent position the inner test contributes
   nothing, so the decision reduces to "enabled AND offered-on-surplus". Every
   input yields a verdict (`Except.ok`); the decision never fails. -/
def shouldOfferDeletion (enabled offerOnExtra : Bool)
    (position : Option Nat) (initialCount : Nat) : Except ControlErr Bool :=
  Except.ok (enabled && (offerOnExtra || positionWithinInitial position initialCount))

@[grind] lemma shouldOfferDeletion_none (enabled offerOnExtra : Bool) (initialCount : Nat) :
    shouldOfferDeletion enabled offerOnExtra none initialCount
      = Except.ok (enabled && offerOnExtra) := by
  simp [shouldOfferDeletion, positionWithinInitial]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Decide whether a per-row removal control should be offered on one row of a
   collection of repeated rows. All four inputs are read-only and unchanged by
   the decision (none is `mut`):
     * `enabled`      — whether the removal control is enabled for the collection;
     * `offerOnExtra` — whether it is also offered on surplus (non-prepopulated) rows;
     * `position`     — the row's ordinal position, or absent when the row has no
                        position (e.g. a standalone blank template row);
     * `initialCount` — how many rows are pre-populated.

   Desired behaviour: the control is offered exactly when it is enabled and
   either it is offered on surplus rows or the position lies strictly within the
   pre-populated rows. When the position is absent the order test contributes
   nothing and the decision must still produce a verdict — it reduces to
   "enabled and offered-on-surplus" — rather than being left undefined. The
   decision fully determines whether the control is subsequently attached. -/
method deletionFieldDecision (enabled : Bool) (offerOnExtra : Bool)
    (position : Option Nat) (initialCount : Nat)
    return (out : Except ControlErr Bool)
  ensures out = shouldOfferDeletion enabled offerOnExtra position initialCount
  ensures ∃ b, out = Except.ok b
  ensures position = none → out = Except.ok (enabled && offerOnExtra)
  do
    -- impl-start
    -- Short-circuiting decision mirroring `enabled AND (offerOnExtra OR P)`,
    -- where the position test P is taken only when the control is enabled and is
    -- not already offered on surplus rows. The test guards the order comparison
    -- against an absent position: with no position the test yields `false`, so
    -- the decision stays a verdict instead of attempting an undefined comparison.
    let mut decision : Bool := false
    if enabled = true then
      if offerOnExtra = true then
        decision := true
      else
        decision := positionWithinInitial position initialCount
    return Except.ok decision
    -- impl-end

prove_correct deletionFieldDecision by
  loom_solve <;>
    simp_all [shouldOfferDeletion, positionWithinInitial]
```

Prepatch bug re-encoded as an attack: `True`.

### ADVERSARIAL G-EQ (refinement-fidelity, A/R/I legs + model↔patch correspondence).

**SPEC SHAPE:** deletionFieldDecision has an EXACT functional-equality postcondition `out = shouldOfferDeletion enabled offerOnExtra position initialCount` (plus `∃ b, out=Except.ok b` and `position=none → out=Except.ok (enabled&&offerOnExtra)`). Output is fully pinned, so only behaviourally-identical impls can verify.

**SAME-SPEC:** all 8 files (7 attacks + positive control) confirmed same_spec=True via swebench_unified.markers.same_spec (impl-region-only edits; axioms/pure/pre/post byte-identical).

### VERIFY RESULTS (scripts/lean_verify.sh <f>, run concurrently ≤4/batch):
  pos_control (=Solution.lean)                       -> exit 0  VERIFIES (positive control, spec non-vacuous)
  atk_1 prepatch: unguarded, none⇒Except.error       -> exit 1  rejected (PREPATCH BUG REPRODUCED; fails clause3+clause1/2 on enabled=true∧offerOnExtra=false∧none)
  atk_2 partial-domain: enabled&&offerOnExtra         -> exit 1  rejected (drops position test; wrong on enabled∧¬extra∧some i<c)
  atk_3 boundary: i<=initialCount (off-by-one)        -> exit 1  rejected (wrong at i=initialCount)
  atk_4 control-flow-effect: enabled⇒always offer     -> exit 1  rejected (drops or/gate)
  atk_5 ungrounded-oracle echo: return shouldOffer... -> exit 0  VERIFIES
  atk_6 boolean restructure (enabled&&off)||(enabled&&P)-> exit 1  rejected (behaviourally equal but prove_correct automation didn't close — NOT a spec weakness, a proof-obligation artifact; still fails-closed, harmless)
  atk_7 none⇒true (wrong absent-position constant)    -> exit 1  rejected (wrong on none: yields enabled instead of enabled&&extra)

**MANDATORY RESOLVE ON EVERY VERIFYING WRONG IMPL:** only atk_5 verifies. Its faithful refined patch (R/I transliteration of the echoed decision = the guarded `index is not None and index < initial_form_count`) is BYTE-IDENTICAL to the gold patch.diff (confirmed by diff). Materialized at patch_atk5.diff and RUN through the official harness (swebench_unified.harness.run_resolve, benchmark swe_bench_verified, docker oracle).
  First run returned COMPLETED=False 'no report — harness error' due to CONTENTION with a live board-wide resolve concurrent runs (sbu-resolve-dbbaf06aa-* containers) — an INFRA non-completion, not a genuine non-resolve.
  Re-ran isolated (run_id atk5diag-16569, timeout 1800): report.json produced, resolved=True, patch_successfully_applied=True, FAIL_TO_PASS success=['test_disable_delete_extra_formset_forms' x2 (Forms + Jinja2)], F2P failure=[], PASS_TO_PASS failure=0. => atk_5's faithful patch RESOLVES. verify⇒correct holds for the sole verifying candidate; spec is NOT broken.

REFINEMENT.MD AUDIT (A/R/I legs, no kind-3): §A table rows A1–A8 are each tagged R (A1–A4,A8: bool↔Bool, int|None↔Option Nat, int(≥0)↔Nat, verdict↔field-added) or I (A5–A7: identical short-circuit boolean ops incl. the guarded comparison). §B/§C: NO consumed axioms and NO deep-model reference to any foreign callee — verified against Solution.lean (axioms-start/end region EMPTY, 0 `axiom` decls, 0 sorry/native_decide, G-AX skips legitimately). `initial_form_count()` is R-abstracted as scalar input A4 (evaluated before the decision, only its value enters), correctly an input not a callee-under-contract.

The single genuinely-changed op (adding the `index is not None` guard) is modeled DEEPLY as positionWithinInitial's `none⇒false` branch (I-op over R-refined carrier) — NO kind-3 (inexpressible-changed-op) leg. All A-legs' correspondence to the real callees holds (vacuously, since there are no axiomatized callees; the R/I legs bind to the concrete post-gold expression `self.can_delete and (self.can_delete_extra or (index is not None and index < initial_form_count))` per mapping.md §1). G-CONF (conformance_check.py, seed 16569) independently refutes-tests the R/I shadow against the REAL patched add_fields on 192-config boundary product + 100k fuzz (meta: 0 disagreements).

**VERDICT:** SOUND. ≥5 distinct wrong impls attacked (7 total: prepatch, partial-domain, boundary, control-flow-effect, ungrounded-oracle echo, boolean-restructure, wrong-none-constant); positive control verifies; prepatch reproduced; the ONLY verifying wrong impl (echo) has a faithful patch that RESOLVES under the official harness. No verifying-wrong-impl-with-non-resolving-patch exists. verify⇒correct is not falsified.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_5.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No unchanged callee is axiomatized for this bundle. The behaviour under spec
   is a pure decision over four scalar inputs: whether a per-row removal control
   is enabled at all, whether it is also offered on surplus rows, the optional
   ordinal position of the row, and how many rows are pre-populated. The widget
   that is ultimately attached once the decision is positive is a shared
   continuation that does not influence the decision, so nothing about it is
   assumed: no consumed axiom and no deep-model reference to a foreign callee. -/
-- axioms-end

-- pure-start
/- The outcome shape of the decision. A well-formed decision always yields a
   verdict (`Except.ok`). The single error constructor records the one outcome a
   correct decision must NEVER produce: the order comparison being attempted
   without an ordinal position to compare, which is undefined and must instead be
   treated as "no position precedes the threshold". A correct result is always a
   verdict, never this error. -/
inductive ControlErr where
  | positionComparisonUndefined
  deriving DecidableEq

/- The contribution of the position test: a present position counts only when it
   lies strictly below the pre-populated count; an absent position contributes
   nothing (it does not enable the control, and — crucially — it is NOT a reason
   to abandon the decision). This is the guarded form of the ordinal comparison
   (mapping.md §3; refinement.md §A). -/
def positionWithinInitial (position : Option Nat) (initialCount : Nat) : Bool :=
  match position with
  | some i => decide (i < initialCount)
  | none   => false

/- The desired decision: the removal control is offered exactly when it is
   enabled AND (it is offered on surplus rows OR the position lies within the
   pre-populated rows). With an absent position the inner test contributes
   nothing, so the decision reduces to "enabled AND offered-on-surplus". Every
   input yields a verdict (`Except.ok`); the decision never fails. -/
def shouldOfferDeletion (enabled offerOnExtra : Bool)
    (position : Option Nat) (initialCount : Nat) : Except ControlErr Bool :=
  Except.ok (enabled && (offerOnExtra || positionWithinInitial position initialCount))

@[grind] lemma shouldOfferDeletion_none (enabled offerOnExtra : Bool) (initialCount : Nat) :
    shouldOfferDeletion enabled offerOnExtra none initialCount
      = Except.ok (enabled && offerOnExtra) := by
  simp [shouldOfferDeletion, positionWithinInitial]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Decide whether a per-row removal control should be offered on one row of a
   collection of repeated rows. All four inputs are read-only and unchanged by
   the decision (none is `mut`):
     * `enabled`      — whether the removal control is enabled for the collection;
     * `offerOnExtra` — whether it is also offered on surplus (non-prepopulated) rows;
     * `position`     — the row's ordinal position, or absent when the row has no
                        position (e.g. a standalone blank template row);
     * `initialCount` — how many rows are pre-populated.

   Desired behaviour: the control is offered exactly when it is enabled and
   either it is offered on surplus rows or the position lies strictly within the
   pre-populated rows. When the position is absent the order test contributes
   nothing and the decision must still produce a verdict — it reduces to
   "enabled and offered-on-surplus" — rather than being left undefined. The
   decision fully determines whether the control is subsequently attached. -/
method deletionFieldDecision (enabled : Bool) (offerOnExtra : Bool)
    (position : Option Nat) (initialCount : Nat)
    return (out : Except ControlErr Bool)
  ensures out = shouldOfferDeletion enabled offerOnExtra position initialCount
  ensures ∃ b, out = Except.ok b
  ensures position = none → out = Except.ok (enabled && offerOnExtra)
  do
    -- impl-start
    -- Short-circuiting decision mirroring `enabled AND (offerOnExtra OR P)`,
    -- where the position test P is taken only when the control is enabled and is
    -- not already offered on surplus rows. The test guards the order comparison
    -- against an absent position: with no position the test yields `false`, so
    -- the decision stays a verdict instead of attempting an undefined comparison.
    let mut decision : Bool := false
    if enabled = true then
      if offerOnExtra = true then
        decision := true
      else
        decision := positionWithinInitial position initialCount
    return Except.ok decision
    -- impl-end

prove_correct deletionFieldDecision by
  loom_solve <;>
    simp_all [shouldOfferDeletion, positionWithinInitial]
```

Prepatch bug re-encoded as an attack: `True`.

### ADVERSARIAL G-EQ (refinement-fidelity, A/R/I legs + model↔patch correspondence).

**SPEC SHAPE:** deletionFieldDecision has an EXACT functional-equality postcondition `out = shouldOfferDeletion enabled offerOnExtra position initialCount` (plus `∃ b, out=Except.ok b` and `position=none → out=Except.ok (enabled&&offerOnExtra)`). Output is fully pinned, so only behaviourally-identical impls can verify.

**SAME-SPEC:** all 8 files (7 attacks + positive control) confirmed same_spec=True via swebench_unified.markers.same_spec (impl-region-only edits; axioms/pure/pre/post byte-identical).

### VERIFY RESULTS (scripts/lean_verify.sh <f>, run concurrently ≤4/batch):
  pos_control (=Solution.lean)                       -> exit 0  VERIFIES (positive control, spec non-vacuous)
  atk_1 prepatch: unguarded, none⇒Except.error       -> exit 1  rejected (PREPATCH BUG REPRODUCED; fails clause3+clause1/2 on enabled=true∧offerOnExtra=false∧none)
  atk_2 partial-domain: enabled&&offerOnExtra         -> exit 1  rejected (drops position test; wrong on enabled∧¬extra∧some i<c)
  atk_3 boundary: i<=initialCount (off-by-one)        -> exit 1  rejected (wrong at i=initialCount)
  atk_4 control-flow-effect: enabled⇒always offer     -> exit 1  rejected (drops or/gate)
  atk_5 ungrounded-oracle echo: return shouldOffer... -> exit 0  VERIFIES
  atk_6 boolean restructure (enabled&&off)||(enabled&&P)-> exit 1  rejected (behaviourally equal but prove_correct automation didn't close — NOT a spec weakness, a proof-obligation artifact; still fails-closed, harmless)
  atk_7 none⇒true (wrong absent-position constant)    -> exit 1  rejected (wrong on none: yields enabled instead of enabled&&extra)

**MANDATORY RESOLVE ON EVERY VERIFYING WRONG IMPL:** only atk_5 verifies. Its faithful refined patch (R/I transliteration of the echoed decision = the guarded `index is not None and index < initial_form_count`) is BYTE-IDENTICAL to the gold patch.diff (confirmed by diff). Materialized at patch_atk5.diff and RUN through the official harness (swebench_unified.harness.run_resolve, benchmark swe_bench_verified, docker oracle).
  First run returned COMPLETED=False 'no report — harness error' due to CONTENTION with a live board-wide resolve concurrent runs (sbu-resolve-dbbaf06aa-* containers) — an INFRA non-completion, not a genuine non-resolve.
  Re-ran isolated (run_id atk5diag-16569, timeout 1800): report.json produced, resolved=True, patch_successfully_applied=True, FAIL_TO_PASS success=['test_disable_delete_extra_formset_forms' x2 (Forms + Jinja2)], F2P failure=[], PASS_TO_PASS failure=0. => atk_5's faithful patch RESOLVES. verify⇒correct holds for the sole verifying candidate; spec is NOT broken.

REFINEMENT.MD AUDIT (A/R/I legs, no kind-3): §A table rows A1–A8 are each tagged R (A1–A4,A8: bool↔Bool, int|None↔Option Nat, int(≥0)↔Nat, verdict↔field-added) or I (A5–A7: identical short-circuit boolean ops incl. the guarded comparison). §B/§C: NO consumed axioms and NO deep-model reference to any foreign callee — verified against Solution.lean (axioms-start/end region EMPTY, 0 `axiom` decls, 0 sorry/native_decide, G-AX skips legitimately). `initial_form_count()` is R-abstracted as scalar input A4 (evaluated before the decision, only its value enters), correctly an input not a callee-under-contract.

The single genuinely-changed op (adding the `index is not None` guard) is modeled DEEPLY as positionWithinInitial's `none⇒false` branch (I-op over R-refined carrier) — NO kind-3 (inexpressible-changed-op) leg. All A-legs' correspondence to the real callees holds (vacuously, since there are no axiomatized callees; the R/I legs bind to the concrete post-gold expression `self.can_delete and (self.can_delete_extra or (index is not None and index < initial_form_count))` per mapping.md §1). G-CONF (conformance_check.py, seed 16569) independently refutes-tests the R/I shadow against the REAL patched add_fields on 192-config boundary product + 100k fuzz (meta: 0 disagreements).

**VERDICT:** SOUND. ≥5 distinct wrong impls attacked (7 total: prepatch, partial-domain, boundary, control-flow-effect, ungrounded-oracle echo, boolean-restructure, wrong-none-constant); positive control verifies; prepatch reproduced; the ONLY verifying wrong impl (echo) has a faithful patch that RESOLVES under the official harness. No verifying-wrong-impl-with-non-resolving-patch exists. verify⇒correct is not falsified.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-drift / spec-too-strong) analysis for django__django-16569 velvet.

**SPEC REGION:** same_spec(Solution.lean, Solution_prepatch.lean, VelvetBackend.language) = True. The four SPEC_REGIONS (axioms/pure/pre/post), the method signature of deletionFieldDecision, and its three `ensures` clauses are byte-identical between patched and prepatch; only the impl region differs (patched: guarded positionWithinInitial; prepatch: unguarded match yielding Except.error on none). Spec is legitimately frozen.

**MODELED FUNCTION vs REAL CALLEE:** The gold patch (formsets.py:493) makes the decision `self.can_delete and (self.can_delete_extra or (index is not None and index < initial_form_count))`. The spec models this as shouldOfferDeletion = enabled && (offerOnExtra || positionWithinInitial position initialCount), positionWithinInitial = (some i => decide(i<initialCount) | none => false). Transliterated the modeled function and the verbatim gold-patched decision to Python and compared over the FULL grid enabled×offerOnExtra×position({None}∪0..59)×initialCount(0..59): 0 disagreements. So the spec agrees with the real (post-patch) callee on every input — not too strong, not too weak.

**BASE vs SPEC:** the spec differs from the BASE(prepatch) repo only on exactly the 60 inputs (enabled=True, offerOnExtra=False, position=None, any initialCount) where the base raises TypeError — i.e. precisely the bug the gold patch fixes. This is the intended R/I discriminator, correctly captured by the none⇒false branch, and reproduced-as-failing by Solution_prepatch.lean.

**CARRIER FIDELITY:** index is only ever None or a non-negative enumerate() index at the sole call site (empty_form passes None; enumerate(self.forms) passes 0..len-1), so Option Nat is a faithful carrier; the only distinctions the behavior reacts to (present-vs-absent, and `<`) are exact on Nat. initial_form_count()≥0 → Nat faithful.

**LEAN:** scripts/lean_verify.sh on Solution.lean exits 0 (spec well-formed, impl proves).

No diverging input between modeled function and real gold-patched callee. Verdict FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Leakage judged against the PUBLIC problem_statement (hints_text is empty). The problem_statement for django__django-16569 is maximally disclosing: it reproduces the gold fix verbatim — 'if self.can_delete and (self.can_delete_extra or (index is not None and index < initial_form_count)):' — names the exact pre-patch TypeError, the root cause (index None compared with int), and the reproduction. Everything the velvet spec view encodes is a faithful Lean model of that already-public behavior: positionWithinInitial's guarded comparison (some i => i<initialCount, none => false) mirrors the public 'index is not None and index < initial_form_count' guard; shouldOfferDeletion mirrors the public boolean; the postcondition 'position = none → Except.ok (enabled && offerOnExtra)' restates the public reduction. No spec-view line discloses anything beyond the problem_statement. same_spec(Solution.lean, Solution_prepatch.lean)=True, so the spec region is byte-identical and leakage cannot hide in a divergent prepatch spec. The impl and proof regions are elided in the consumer spec view (verified via markers.spec_view). Conclusion: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.