# P2 adversarial audit — django__django-15916

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `atk_6_posctrl.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

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
 -- (No axioms: this operation selects which field-building callback a form
@@ -48,7 +48,7 @@
   ensures out = configCallback
   do
     -- impl-start
-    return configCallback
+    return (declaredCallback.getD inheritedCallback)
     -- impl-end
 
 prove_correct selectFieldCallback by
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
 -- (No axioms: this operation selects which field-building callback a form
@@ -48,7 +48,7 @@
   ensures out = configCallback
   do
     -- impl-start
-    return configCallback
+    return inheritedCallback
     -- impl-end
 
 prove_correct selectFieldCallback by
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
 -- (No axioms: this operation selects which field-building callback a form
@@ -48,7 +48,7 @@
   ensures out = configCallback
   do
     -- impl-start
-    return configCallback
+    return none
     -- impl-end
 
 prove_correct selectFieldCallback by
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
 -- (No axioms: this operation selects which field-building callback a form
@@ -48,7 +48,7 @@
   ensures out = configCallback
   do
     -- impl-start
-    return configCallback
+    return (declaredCallback.getD configCallback)
     -- impl-end
 
 prove_correct selectFieldCallback by
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
 -- (No axioms: this operation selects which field-building callback a form
@@ -48,7 +48,7 @@
   ensures out = configCallback
   do
     -- impl-start
-    return configCallback
+    return (declaredCallback.bind id)
     -- impl-end
 
 prove_correct selectFieldCallback by
```

Attack 6 — `atk_7.lean` → rejected (same spec, does not verify — good)

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
 -- (No axioms: this operation selects which field-building callback a form
@@ -48,7 +48,14 @@
   ensures out = configCallback
   do
     -- impl-start
-    return configCallback
+    let mut k : Nat := 1
+    while k > 0
+      invariant True
+      done_with k = 0
+      decreasing k
+    do
+      k := k + 1
+    return inheritedCallback
     -- impl-end
 
 prove_correct selectFieldCallback by
```

Attack 7 — `atk_8.lean` → rejected (same spec, does not verify — good)

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
 -- (No axioms: this operation selects which field-building callback a form
@@ -48,7 +48,10 @@
   ensures out = configCallback
   do
     -- impl-start
-    return configCallback
+    if declaredCallback.isSome then
+      return (declaredCallback.getD none)
+    else
+      return configCallback
     -- impl-end
 
 prove_correct selectFieldCallback by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_6_posctrl.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axioms: this operation selects which field-building callback a form
--  should use, from facts already read off the form's configuration and its
--  ancestry. There is no unchanged callee whose contract the proof consumes.)
-- axioms-end

-- pure-start
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Choose the field-building callback for a model-backed form.

   A callback is an opaque function identified here by a tag (`some n`), with
   `none` meaning "no callback". A form has three callback sources that are
   observable when its fields are built:

   * `configCallback`  — the callback the form's OWN configuration resolves to
                         (its configuration block directly, or one inherited
                         through that block's ancestry); already resolved here;
   * `declaredCallback` — what, if anything, is named directly on the form class
                         body. The outer `Option` is presence (`none` = nothing
                         named there), the inner is the named value (`some none`
                         = explicitly "no callback" named on the body);
   * `inheritedCallback` — the callback a parent form offers as a default.

   The desired behavior is that the callback the form is built with is exactly
   the one its own configuration resolves to (`configCallback`), independently
   of what is named on the class body or offered by a parent. All three are
   read-only inputs (no `mut`): the result is a pure selection. -/
method selectFieldCallback
    (configCallback : Option Nat)
    (declaredCallback : Option (Option Nat))
    (inheritedCallback : Option Nat)
    return (out : Option Nat)
  ensures out = configCallback
  do
    -- impl-start
    match configCallback with
    | some n => return (some n)
    | none => return none
    -- impl-end

prove_correct selectFieldCallback by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit for django__django-15916 (velvet). Spec is a TOTAL exact equation `ensures out = configCallback` (no requires) with impl `return configCallback`, so the output is pinned uniquely and any behaviorally-different impl fails the lone clause.

SAME-SPEC: all 8 files pass swebench_unified.markers.same_spec (=True) — edited impl region only; axioms/pure/pre/post byte-identical.

### VERIFY (bash scripts/lean_verify.sh <f>):
- atk_1 return (declaredCallback.getD inheritedCallback) [prepatch bug] -> exit 1, unsolved `declaredCallback.getD inheritedCallback = configCallback`.
- atk_2 return inheritedCallback -> exit 1, `inheritedCallback = configCallback`.
- atk_3 return none [boundary/ungrounded] -> exit 1, `none = configCallback`.
- atk_4 return (declaredCallback.getD configCallback) -> exit 1, `declaredCallback.getD configCallback = configCallback`.
- atk_5 return (declaredCallback.bind id) [flatten] -> exit 1, `declaredCallback.bind id = configCallback`.
- atk_7 CONTROL-FLOW-EFFECT: divergent `while k>0 (k:=k+1)` under loom.semantics.termination=partial then `return inheritedCallback` -> exit 1. This is the key adversarial probe: the ONLY theoretical verify-but-wrong escape against a total exact-equation spec is nontermination under partial correctness. Rejected: Velvet WP still discharges the postcondition on the loop-exit continuation using invariant(True)+done_with(k=0), leaving `inheritedCallback = configCallback` unsolved. The `decreasing` annotation is (harmlessly) unchecked in partial semantics, but the exit-state post obligation is NOT waived. No escape hatch.
- atk_8 branchy partial-domain (wrong iff declaredCallback.isSome) -> exit 1, `declaredCallback.getD none = configCallback`.

POSITIVE CONTROL atk_6_posctrl: structurally-different correct `match configCallback with | some n => some n | none => none` -> exit 0 (verifies). Shipped Solution.lean -> exit 0. Solution_prepatch.lean -> exit 1 on exactly the discriminating goal `declaredCallback.getD inheritedCallback = configCallback` (prepatch reproduced, G-DIFF genuine).

RESOLVE: no wrong impl verified, so there is no verifying-wrong-impl whose faithful refined patch needs a harness resolve run (protocol step 2 obligation is vacuous — it applies only to wrong impls that VERIFY). Nothing was skipped: every attack was fully verified.

REFINEMENT AUDIT: meta.json axioms=[], deep_model_references=[], conf_skip=false, no axiom_check.py. refinement.md legs A1-A5 are all tagged R or R+I (the section-header 'A' is a section letter, not an axiom kind); no kind-3, no consumed axioms, no deep-model references. The three inputs (configCallback/declaredCallback/inheritedCallback) are the R-refinement observation functions of the input bijection (mapping.md §2), matching the tzinfo exemplar django__django-14792 — not callee contracts. Correspondence to the real selection site (ModelFormMetaclass.__new__ choosing opts.formfield_callback post-patch vs declaredCallback.getD inheritedCallback pre-patch) holds; the discriminator lives in `out = configCallback`.

VERDICT: SOUND. ≥7 distinct same-spec wrong impls (partial-domain, boundary, control-flow-effect/divergence, ungrounded-oracle echo, prepatch bug) all rejected; positive control + shipped verify; prepatch fails on the load-bearing goal. verify⇒correct is not falsified for this bundle.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `atk_6_posctrl.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_8.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_6_posctrl.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axioms: this operation selects which field-building callback a form
--  should use, from facts already read off the form's configuration and its
--  ancestry. There is no unchanged callee whose contract the proof consumes.)
-- axioms-end

-- pure-start
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Choose the field-building callback for a model-backed form.

   A callback is an opaque function identified here by a tag (`some n`), with
   `none` meaning "no callback". A form has three callback sources that are
   observable when its fields are built:

   * `configCallback`  — the callback the form's OWN configuration resolves to
                         (its configuration block directly, or one inherited
                         through that block's ancestry); already resolved here;
   * `declaredCallback` — what, if anything, is named directly on the form class
                         body. The outer `Option` is presence (`none` = nothing
                         named there), the inner is the named value (`some none`
                         = explicitly "no callback" named on the body);
   * `inheritedCallback` — the callback a parent form offers as a default.

   The desired behavior is that the callback the form is built with is exactly
   the one its own configuration resolves to (`configCallback`), independently
   of what is named on the class body or offered by a parent. All three are
   read-only inputs (no `mut`): the result is a pure selection. -/
method selectFieldCallback
    (configCallback : Option Nat)
    (declaredCallback : Option (Option Nat))
    (inheritedCallback : Option Nat)
    return (out : Option Nat)
  ensures out = configCallback
  do
    -- impl-start
    match configCallback with
    | some n => return (some n)
    | none => return none
    -- impl-end

prove_correct selectFieldCallback by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit for django__django-15916 (velvet). Spec is a TOTAL exact equation `ensures out = configCallback` (no requires) with impl `return configCallback`, so the output is pinned uniquely and any behaviorally-different impl fails the lone clause.

SAME-SPEC: all 8 files pass swebench_unified.markers.same_spec (=True) — edited impl region only; axioms/pure/pre/post byte-identical.

### VERIFY (bash scripts/lean_verify.sh <f>):
- atk_1 return (declaredCallback.getD inheritedCallback) [prepatch bug] -> exit 1, unsolved `declaredCallback.getD inheritedCallback = configCallback`.
- atk_2 return inheritedCallback -> exit 1, `inheritedCallback = configCallback`.
- atk_3 return none [boundary/ungrounded] -> exit 1, `none = configCallback`.
- atk_4 return (declaredCallback.getD configCallback) -> exit 1, `declaredCallback.getD configCallback = configCallback`.
- atk_5 return (declaredCallback.bind id) [flatten] -> exit 1, `declaredCallback.bind id = configCallback`.
- atk_7 CONTROL-FLOW-EFFECT: divergent `while k>0 (k:=k+1)` under loom.semantics.termination=partial then `return inheritedCallback` -> exit 1. This is the key adversarial probe: the ONLY theoretical verify-but-wrong escape against a total exact-equation spec is nontermination under partial correctness. Rejected: Velvet WP still discharges the postcondition on the loop-exit continuation using invariant(True)+done_with(k=0), leaving `inheritedCallback = configCallback` unsolved. The `decreasing` annotation is (harmlessly) unchecked in partial semantics, but the exit-state post obligation is NOT waived. No escape hatch.
- atk_8 branchy partial-domain (wrong iff declaredCallback.isSome) -> exit 1, `declaredCallback.getD none = configCallback`.

POSITIVE CONTROL atk_6_posctrl: structurally-different correct `match configCallback with | some n => some n | none => none` -> exit 0 (verifies). Shipped Solution.lean -> exit 0. Solution_prepatch.lean -> exit 1 on exactly the discriminating goal `declaredCallback.getD inheritedCallback = configCallback` (prepatch reproduced, G-DIFF genuine).

RESOLVE: no wrong impl verified, so there is no verifying-wrong-impl whose faithful refined patch needs a harness resolve run (protocol step 2 obligation is vacuous — it applies only to wrong impls that VERIFY). Nothing was skipped: every attack was fully verified.

REFINEMENT AUDIT: meta.json axioms=[], deep_model_references=[], conf_skip=false, no axiom_check.py. refinement.md legs A1-A5 are all tagged R or R+I (the section-header 'A' is a section letter, not an axiom kind); no kind-3, no consumed axioms, no deep-model references. The three inputs (configCallback/declaredCallback/inheritedCallback) are the R-refinement observation functions of the input bijection (mapping.md §2), matching the tzinfo exemplar django__django-14792 — not callee contracts. Correspondence to the real selection site (ModelFormMetaclass.__new__ choosing opts.formfield_callback post-patch vs declaredCallback.getD inheritedCallback pre-patch) holds; the discriminator lives in `out = configCallback`.

VERDICT: SOUND. ≥7 distinct same-spec wrong impls (partial-domain, boundary, control-flow-effect/divergence, ungrounded-oracle echo, prepatch bug) all rejected; positive control + shipped verify; prepatch fails on the load-bearing goal. verify⇒correct is not falsified for this bundle.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec: `ensures out = configCallback` over selectFieldCallback(configCallback : Option Nat, declaredCallback : Option (Option Nat), inheritedCallback : Option Nat), impl `return configCallback`. Real callee: post-patch ModelFormMetaclass.__new__ (django/forms/models.py) passes opts.formfield_callback to fields_for_model, where opts.formfield_callback = getattr(new_class.Meta,'formfield_callback',None) — the form's own Meta-resolved callback (direct on its Meta, else inherited via the Meta MRO). mapping.md §2 binds configCallback exactly to opts.formfield_callback, so the identity spec IS the post-patch selection; the pre-patch declaredCallback.getD inheritedCallback (class-body-if-present-else-base-scan) is correctly dropped.

Independent verification (did NOT trust recorded audits):
- same_spec(Solution.lean, Solution_prepatch.lean, velvet backend) = True; spec view clean (no repo mechanism leaked).
- lean_verify.sh Solution.lean -> exit 0.
- Applied gold patch (patch.diff) to a fresh copy of the base_commit worktree; confirmed post-patch metaclass passes opts.formfield_callback and drops the base-scan + attrs.pop.
- Independent probe driving the REAL patched metaclass (not the bundle shadow), reading the actual callback off base_fields['name'].widget.__class__: full 80-cell source-combination matrix (own-Meta × base-Meta × class-body-presence × class-body-value) -> total=80 bad=0. Every cell equals out=configCallback.
- Multi-base MRO cases (two base forms, own Meta inherits from first base's Meta) -> all faithful.
- Subtle edge NOT distinguished by conformance_check.py: own Meta EXPLICITLY sets formfield_callback=None over a base cb=1 -> real oracle returns None and getattr(Meta,'formfield_callback',None)=None -> faithful (spec is an identity on the getattr-bound value; the conformance's _config_callback_tag would have modeled base=1, but the mapping binds configCallback to getattr(Meta,...) which is None, matching the real callee).

No input found where the modeled function disagrees with the real post-patch callee. The spec is neither too strong nor drifted from real repo behavior. Corroborates meta.json G-CONF (100082 configs, 0 disagreements, seed 15916).

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen over the velvet spec view passes with zero hard failures (verified by running leakage.screen on the projected spec_view). Detailed checks:

- No diff markers, no reproduced gold-patch line (>=8 normalized chars), no patched file path ('django/forms/models.py') or dotted module path in the spec view.
- The only distinctive changed def-name the patch touches is 'modelform_factory', which is already public in the problem_statement (verbatim: 'the function django.forms.modelform_factory ...'), so it is exempt.
- Spec-view identifiers are all abstracted Lean names (selectFieldCallback, configCallback, declaredCallback, inheritedCallback, out) — none echo the actual patched repo symbols (opts.formfield_callback, ModelFormOptions, base_formfield_callback, attrs.pop, form_class_attrs, ModelFormMetaclass.__new__). None of the edit-localizing symbols leak.
- No narration keywords (bug/fix/patch/regression/...) in the docstring/comments.

Semantic judgment: the spec view discloses only the DESIRED behavior — 'the callback the form is built with is the one its own configuration resolves to (configCallback), independently of the class body or parent', encoded as `ensures out = configCallback`. This is precisely the feature already stated publicly in the problem_statement ('the FactoryForm uses the formfield_callback specified in the Meta attribute ... independently of base/factory default'). Specifying correct target behavior is the legitimate function of a spec; it does not reveal the gold patch's mechanics (capturing on ModelFormOptions.formfield_callback, deleting the base-scan loop and attrs.pop, dropping formfield_callback from form_class_attrs). Those mechanics appear only in refinement.md/mapping.md (auditor artifacts, not the consumer spec view). same_spec(Solution, Solution_prepatch) is True, so the prepatch skeleton shares the identical frozen spec view — no additional leakage surface.

The spec view does not leak the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
