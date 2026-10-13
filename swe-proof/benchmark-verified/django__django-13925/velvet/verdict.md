# P2 adversarial audit — django__django-13925

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `atk_ctrl.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -62,10 +62,7 @@
      !defaultKeyTypeConfigured && !appKeyTypeConfigured)
   do
     -- impl-start
-    -- Emit the advisory only when the primary key was auto-supplied, is NOT the
-    -- implicit key inherited from an ancestor, and no default primary-key type
-    -- has been configured project-wide or for the model's application.
-    return (pkAutoCreated && !pkInheritedFromAncestor &&
+    return (pkAutoCreated &&
             !defaultKeyTypeConfigured && !appKeyTypeConfigured)
     -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -62,11 +62,8 @@
      !defaultKeyTypeConfigured && !appKeyTypeConfigured)
   do
     -- impl-start
-    -- Emit the advisory only when the primary key was auto-supplied, is NOT the
-    -- implicit key inherited from an ancestor, and no default primary-key type
-    -- has been configured project-wide or for the model's application.
     return (pkAutoCreated && !pkInheritedFromAncestor &&
-            !defaultKeyTypeConfigured && !appKeyTypeConfigured)
+            !defaultKeyTypeConfigured)
     -- impl-end
 
 prove_correct implicitPrimaryKeyAdvisory by
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -62,11 +62,7 @@
      !defaultKeyTypeConfigured && !appKeyTypeConfigured)
   do
     -- impl-start
-    -- Emit the advisory only when the primary key was auto-supplied, is NOT the
-    -- implicit key inherited from an ancestor, and no default primary-key type
-    -- has been configured project-wide or for the model's application.
-    return (pkAutoCreated && !pkInheritedFromAncestor &&
-            !defaultKeyTypeConfigured && !appKeyTypeConfigured)
+    return true
     -- impl-end
 
 prove_correct implicitPrimaryKeyAdvisory by
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -62,11 +62,7 @@
      !defaultKeyTypeConfigured && !appKeyTypeConfigured)
   do
     -- impl-start
-    -- Emit the advisory only when the primary key was auto-supplied, is NOT the
-    -- implicit key inherited from an ancestor, and no default primary-key type
-    -- has been configured project-wide or for the model's application.
-    return (pkAutoCreated && !pkInheritedFromAncestor &&
-            !defaultKeyTypeConfigured && !appKeyTypeConfigured)
+    return false
     -- impl-end
 
 prove_correct implicitPrimaryKeyAdvisory by
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -62,11 +62,8 @@
      !defaultKeyTypeConfigured && !appKeyTypeConfigured)
   do
     -- impl-start
-    -- Emit the advisory only when the primary key was auto-supplied, is NOT the
-    -- implicit key inherited from an ancestor, and no default primary-key type
-    -- has been configured project-wide or for the model's application.
-    return (pkAutoCreated && !pkInheritedFromAncestor &&
-            !defaultKeyTypeConfigured && !appKeyTypeConfigured)
+    return (pkAutoCreated || (!pkInheritedFromAncestor &&
+            !defaultKeyTypeConfigured && !appKeyTypeConfigured))
     -- impl-end
 
 prove_correct implicitPrimaryKeyAdvisory by
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -62,10 +62,7 @@
      !defaultKeyTypeConfigured && !appKeyTypeConfigured)
   do
     -- impl-start
-    -- Emit the advisory only when the primary key was auto-supplied, is NOT the
-    -- implicit key inherited from an ancestor, and no default primary-key type
-    -- has been configured project-wide or for the model's application.
-    return (pkAutoCreated && !pkInheritedFromAncestor &&
+    return (pkAutoCreated && pkInheritedFromAncestor &&
             !defaultKeyTypeConfigured && !appKeyTypeConfigured)
     -- impl-end
 
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -62,9 +62,9 @@
      !defaultKeyTypeConfigured && !appKeyTypeConfigured)
   do
     -- impl-start
-    -- Emit the advisory only when the primary key was auto-supplied, is NOT the
-    -- implicit key inherited from an ancestor, and no default primary-key type
-    -- has been configured project-wide or for the model's application.
+    let mut i := 0
+    while true do
+      i := i + 1
     return (pkAutoCreated && !pkInheritedFromAncestor &&
             !defaultKeyTypeConfigured && !appKeyTypeConfigured)
     -- impl-end
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -62,11 +62,8 @@
      !defaultKeyTypeConfigured && !appKeyTypeConfigured)
   do
     -- impl-start
-    -- Emit the advisory only when the primary key was auto-supplied, is NOT the
-    -- implicit key inherited from an ancestor, and no default primary-key type
-    -- has been configured project-wide or for the model's application.
     return (pkAutoCreated && !pkInheritedFromAncestor &&
-            !defaultKeyTypeConfigured && !appKeyTypeConfigured)
+            !defaultKeyTypeConfigured && appKeyTypeConfigured)
     -- impl-end
 
 prove_correct implicitPrimaryKeyAdvisory by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_ctrl.lean`

```lean
import Velvet.Std
-- imports-end

-- Total correctness: the modeled routine is a straight-line boolean guard that
-- always terminates, so a diverging implementation must NOT satisfy the spec.
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- No consumed axioms and no axiomatized callees. Every input the decision reads
-- is a read-only boolean observation about the model and its environment
-- (modeled directly as a `Bool` parameter, mapping.md §2); none is an outside
-- routine whose return value the spec must contract. There is therefore no
-- `axiom` to validate against a real callee (meta.json G-AX skip).
-- axioms-end

-- pure-start
-- (No pure helpers needed — the decision is a single boolean expression.)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- A model self-diagnostic decides whether to emit an advisory that an
   auto-created primary key is being used while no primary-key type has been
   chosen. The advisory is appropriate ONLY for a model that genuinely lacks a
   primary key of its own: the system supplied one automatically, AND that
   automatic primary key is not merely the implicit key the model carries by
   virtue of inheriting from an ancestor model, AND no default primary-key type
   has been configured either project-wide or for the model's own application.

   Crucially, a model whose only "auto-created" primary key is the one it
   inherits from an ancestor has not failed to choose a primary-key type — the
   ancestor is the place that choice belongs, and the ancestor is diagnosed on
   its own. So when the automatic primary key is the inherited ancestor key, the
   advisory must be suppressed for this model even though its primary key is, in
   the narrow attribute sense, auto-created.

   All four observations are read-only classifications of the model and its
   settings (none is `mut`): the routine reads them and emits a single decision,
   mutating nothing (directive 5). Each is a `Bool` (mapping.md §2):
     `pkAutoCreated`            — the primary key was supplied automatically
                                   rather than declared on this model;
     `pkInheritedFromAncestor`  — that automatic primary key is the implicit key
                                   the model holds purely by inheriting from an
                                   ancestor model (not a fresh auto field);
     `defaultKeyTypeConfigured` — a project-wide default primary-key type is set;
     `appKeyTypeConfigured`     — the model's own application sets a default
                                   primary-key type.
   The advisory is emitted (`out = true`) exactly on the conjunction below. -/
method implicitPrimaryKeyAdvisory
    (pkAutoCreated : Bool) (pkInheritedFromAncestor : Bool)
    (defaultKeyTypeConfigured : Bool) (appKeyTypeConfigured : Bool)
    return (out : Bool)
  ensures out =
    (pkAutoCreated && !pkInheritedFromAncestor &&
     !defaultKeyTypeConfigured && !appKeyTypeConfigured)
  do
    -- impl-start
    if pkAutoCreated then
      if pkInheritedFromAncestor then return false
      else return !(defaultKeyTypeConfigured || appKeyTypeConfigured)
    else
      return false
    -- impl-end

prove_correct implicitPrimaryKeyAdvisory by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. The spec's postcondition is `ensures out = (pkAutoCreated && !pkInheritedFromAncestor && !defaultKeyTypeConfigured && !appKeyTypeConfigured)` — a CLOSED total boolean function of four FREE Bool inputs with NO axioms, NO deep-model references, NO opaque/oracle symbol (meta.json: axioms:[], deep_model_references:[], G-AX=skip). Any impl can verify only by computing exactly that function extensionally; there is nothing to echo and no A-leg to ground. There are therefore no A-consumed/A-reference legs — refinement.md's A1–A4 are R (bool<->Bool exact) and A5 is I (the boolean conjunction), no kind-3.

### Protocol results

same_spec check (all True) via swebench_unified.markers.same_spec with velvet backend over all 9 files.

Verify command per file: `bash scripts/lean_verify.sh <file>` (run concurrently, <=4 at a time).
- atk_ctrl (POSITIVE CONTROL: structurally-different nested-if / De Morgan `if pkAutoCreated then (if pkInheritedFromAncestor then false else !(default||app)) else false`): same_spec=True, verify EXIT 0 (verifies) — spec non-vacuous.
- atk_1 (prepatch bug: drops `!pkInheritedFromAncestor`, = Solution_prepatch): same_spec=True, verify EXIT 1. Unsolved goal `(pkAutoCreated && !default && !app) = (pkAutoCreated && !inherited && !default && !app)` — the exact missing conjunct = whole behavioral change. PREPATCH REPRODUCED.
- atk_2 (boundary: drop `!appKeyTypeConfigured`): same_spec=True, EXIT 1.
- atk_3 (ungrounded-oracle echo: `return true`): same_spec=True, EXIT 1.
- atk_4 (constant `return false`): same_spec=True, EXIT 1.
- atk_5 (wrong connective: `pkAutoCreated || (...)`): same_spec=True, EXIT 1.
- atk_6 (wrong polarity: `pkInheritedFromAncestor` un-negated): same_spec=True, EXIT 1.
- atk_7 (control-flow-effect / divergence: `while true do i:=i+1` before returning the correct value): same_spec=True, EXIT 1 — rejected with `error: Decreasing annotations are required in total correctness semantics`, confirming the `loom.semantics.termination "total"` hardening cited in refinement.md is REAL, not decorative (a diverging impl cannot vacuously verify).
- atk_8 (boundary: require `appKeyTypeConfigured` instead of `!`): same_spec=True, EXIT 1.

No wrong impl verifies => step-2 (materialize + run_resolve every VERIFYING wrong impl) is vacuously satisfied (patches:{} — no verifying wrong impl to materialize). To prove the resolve leg is LIVE and not skipped, I executed the correct-impl faithful patch (= gold guard, the behavior atk_ctrl encodes) through the official harness:
  cmd: `python3 run_resolve.py django__django-13925 gold.patch 1500` (swebench_unified.harness.run_resolve)
  result: {"resolved": true, "completed": true, "note": "resolved", "attempts": 1, "flaky": false}

Refinement.md / mapping.md audit: every leg is R (A1–A4) or I (A5); no kind-3; no A-consumed axiom, no A-reference deep model, so no A-leg correspondence to a real callee is needed (mapping.md §3 correctly justifies collapsing `isinstance(pk,OneToOneField) and pk.remote_field.parent_link` into one atomic Bool since the patch adds exactly that conjunct and F2P tests discriminate only on advisory present/absent). The single trust point (refinement fidelity) is corroborated by G-CONF (0 disagreements / 100016 inputs, seed 13925).

VERDICT: SOUND. >=5 distinct attacks (8 total) plus divergence and echo classes all run and rejected; positive control verifies and its faithful patch resolves. No verifying wrong impl exists, so verify==>correct holds for this spec.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `atk_ctrl.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

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

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_ctrl.lean`

```lean
import Velvet.Std
-- imports-end

-- Total correctness: the modeled routine is a straight-line boolean guard that
-- always terminates, so a diverging implementation must NOT satisfy the spec.
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- No consumed axioms and no axiomatized callees. Every input the decision reads
-- is a read-only boolean observation about the model and its environment
-- (modeled directly as a `Bool` parameter, mapping.md §2); none is an outside
-- routine whose return value the spec must contract. There is therefore no
-- `axiom` to validate against a real callee (meta.json G-AX skip).
-- axioms-end

-- pure-start
-- (No pure helpers needed — the decision is a single boolean expression.)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- A model self-diagnostic decides whether to emit an advisory that an
   auto-created primary key is being used while no primary-key type has been
   chosen. The advisory is appropriate ONLY for a model that genuinely lacks a
   primary key of its own: the system supplied one automatically, AND that
   automatic primary key is not merely the implicit key the model carries by
   virtue of inheriting from an ancestor model, AND no default primary-key type
   has been configured either project-wide or for the model's own application.

   Crucially, a model whose only "auto-created" primary key is the one it
   inherits from an ancestor has not failed to choose a primary-key type — the
   ancestor is the place that choice belongs, and the ancestor is diagnosed on
   its own. So when the automatic primary key is the inherited ancestor key, the
   advisory must be suppressed for this model even though its primary key is, in
   the narrow attribute sense, auto-created.

   All four observations are read-only classifications of the model and its
   settings (none is `mut`): the routine reads them and emits a single decision,
   mutating nothing (directive 5). Each is a `Bool` (mapping.md §2):
     `pkAutoCreated`            — the primary key was supplied automatically
                                   rather than declared on this model;
     `pkInheritedFromAncestor`  — that automatic primary key is the implicit key
                                   the model holds purely by inheriting from an
                                   ancestor model (not a fresh auto field);
     `defaultKeyTypeConfigured` — a project-wide default primary-key type is set;
     `appKeyTypeConfigured`     — the model's own application sets a default
                                   primary-key type.
   The advisory is emitted (`out = true`) exactly on the conjunction below. -/
method implicitPrimaryKeyAdvisory
    (pkAutoCreated : Bool) (pkInheritedFromAncestor : Bool)
    (defaultKeyTypeConfigured : Bool) (appKeyTypeConfigured : Bool)
    return (out : Bool)
  ensures out =
    (pkAutoCreated && !pkInheritedFromAncestor &&
     !defaultKeyTypeConfigured && !appKeyTypeConfigured)
  do
    -- impl-start
    if pkAutoCreated then
      if pkInheritedFromAncestor then return false
      else return !(defaultKeyTypeConfigured || appKeyTypeConfigured)
    else
      return false
    -- impl-end

prove_correct implicitPrimaryKeyAdvisory by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. The spec's postcondition is `ensures out = (pkAutoCreated && !pkInheritedFromAncestor && !defaultKeyTypeConfigured && !appKeyTypeConfigured)` — a CLOSED total boolean function of four FREE Bool inputs with NO axioms, NO deep-model references, NO opaque/oracle symbol (meta.json: axioms:[], deep_model_references:[], G-AX=skip). Any impl can verify only by computing exactly that function extensionally; there is nothing to echo and no A-leg to ground. There are therefore no A-consumed/A-reference legs — refinement.md's A1–A4 are R (bool<->Bool exact) and A5 is I (the boolean conjunction), no kind-3.

### Protocol results

same_spec check (all True) via swebench_unified.markers.same_spec with velvet backend over all 9 files.

Verify command per file: `bash scripts/lean_verify.sh <file>` (run concurrently, <=4 at a time).
- atk_ctrl (POSITIVE CONTROL: structurally-different nested-if / De Morgan `if pkAutoCreated then (if pkInheritedFromAncestor then false else !(default||app)) else false`): same_spec=True, verify EXIT 0 (verifies) — spec non-vacuous.
- atk_1 (prepatch bug: drops `!pkInheritedFromAncestor`, = Solution_prepatch): same_spec=True, verify EXIT 1. Unsolved goal `(pkAutoCreated && !default && !app) = (pkAutoCreated && !inherited && !default && !app)` — the exact missing conjunct = whole behavioral change. PREPATCH REPRODUCED.
- atk_2 (boundary: drop `!appKeyTypeConfigured`): same_spec=True, EXIT 1.
- atk_3 (ungrounded-oracle echo: `return true`): same_spec=True, EXIT 1.
- atk_4 (constant `return false`): same_spec=True, EXIT 1.
- atk_5 (wrong connective: `pkAutoCreated || (...)`): same_spec=True, EXIT 1.
- atk_6 (wrong polarity: `pkInheritedFromAncestor` un-negated): same_spec=True, EXIT 1.
- atk_7 (control-flow-effect / divergence: `while true do i:=i+1` before returning the correct value): same_spec=True, EXIT 1 — rejected with `error: Decreasing annotations are required in total correctness semantics`, confirming the `loom.semantics.termination "total"` hardening cited in refinement.md is REAL, not decorative (a diverging impl cannot vacuously verify).
- atk_8 (boundary: require `appKeyTypeConfigured` instead of `!`): same_spec=True, EXIT 1.

No wrong impl verifies => step-2 (materialize + run_resolve every VERIFYING wrong impl) is vacuously satisfied (patches:{} — no verifying wrong impl to materialize). To prove the resolve leg is LIVE and not skipped, I executed the correct-impl faithful patch (= gold guard, the behavior atk_ctrl encodes) through the official harness:
  cmd: `python3 run_resolve.py django__django-13925 gold.patch 1500` (swebench_unified.harness.run_resolve)
  result: {"resolved": true, "completed": true, "note": "resolved", "attempts": 1, "flaky": false}

Refinement.md / mapping.md audit: every leg is R (A1–A4) or I (A5); no kind-3; no A-consumed axiom, no A-reference deep model, so no A-leg correspondence to a real callee is needed (mapping.md §3 correctly justifies collapsing `isinstance(pk,OneToOneField) and pk.remote_field.parent_link` into one atomic Bool since the patch adds exactly that conjunct and F2P tests discriminate only on advisory present/absent). The single trust point (refinement fidelity) is corroborated by G-CONF (0 disagreements / 100016 inputs, seed 13925).

VERDICT: SOUND. >=5 distinct attacks (8 total) plus divergence and echo classes all run and rejected; positive control verifies and its faithful patch resolves. No verifying wrong impl exists, so verify==>correct holds for this spec.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-drift / spec-too-strong) check for django__django-13925 velvet bundle. same_spec(Solution, Solution_prepatch) = True under VelvetBackend (spec view byte-identical). Solution.lean verifies (lean_verify exit 0); Solution_prepatch.lean (guard missing the !pkInheritedFromAncestor conjunct) correctly FAILS at the inherited-PK case, confirming discrimination. The modeled ensures `out = (pkAutoCreated && !pkInheritedFromAncestor && !defaultKeyTypeConfigured && !appKeyTypeConfigured)` is truth-table identical to the real post-patch guard of Model._check_default_pk at base_commit 0c42cdf0 (django/db/models/base.py:1299): `pk.auto_created and not(isinstance(pk,OneToOneField) and pk.remote_field.parent_link) and not is_overridden('DEFAULT_AUTO_FIELD') and not app_config._is_default_auto_field_overridden`, returning [W042] iff the guard holds else []. Each operand is read purely as a boolean in the real code (all under and/not); pkInheritedFromAncestor faithfully abstracts the whole `isinstance(...) and parent_link` sub-expression as one Bool (short-circuit-safe, only used under not(...)). Over all 16 boolean combinations the modeled conjunction equals the real guard's truth value; output list-shape [W042]<->true, []<->false is the only observable the F2P tests assert. No diverging input exists — the spec is exactly the patched guard, not too strong and not too weak. G-AX skip is justified (no contracted callee; every operand is a direct boolean metadata read).

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec region is byte-identical (swebench_unified.markers.same_spec(Solution.lean, Solution_prepatch.lean, lean) == True). Mechanical G-LEAK screen passes with zero hard failures. Semantic review of the spec view (imports, set_option lines, empty axiom/pure/pre/post regions, the method docstring, signature, and `ensures` clause) confirms no leakage beyond the public problem_statement:

1. No repo/edit localization is revealed. The patched file path `django/db/models/base.py`, the changed routine `_check_default_pk`, the added-conjunct symbols `OneToOneField` / `remote_field.parent_link`, and the warning id `models.W042` appear NOWHERE in the spec view. The model uses only abstract carrier names (implicitPrimaryKeyAdvisory, pkAutoCreated, pkInheritedFromAncestor, defaultKeyTypeConfigured, appKeyTypeConfigured). No diff markers, no reproduced gold-patch line, no bug/fix narration.

2. Every behavioral fact the ensures clause encodes is already public in problem_statement (NOT hints_text): the reporter explicitly states the bug is W042 'raised on inherited ... primary key', that 'models which inherit from other models ... should inherit the primary key' and 'should not use auto-created primary keys! I already defined the primary key in the ancestor' — i.e. the suppress-advisory-for-inherited-ancestor-PK discriminator (pkInheritedFromAncestor conjunct) is publicly given. The two config conjuncts (defaultKeyTypeConfigured / appKeyTypeConfigured) are named in the public W042 HINT text: 'Configure the DEFAULT_AUTO_FIELD setting or the ...Config.default_auto_field attribute'. And pkAutoCreated ('Auto-created primary key used') is the warning message itself.

3. A spec is expected to encode target behavior; here it encodes nothing beyond what the problem_statement makes public, and does so via a same-spec-frozen, symbol-free boolean abstraction. The added conjunct is modeled as one opaque Bool input, not the isinstance/parent_link mechanics. No gold reconstruction beyond public information.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
