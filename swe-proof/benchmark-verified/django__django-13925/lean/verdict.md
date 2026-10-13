# P2 adversarial audit — django__django-13925

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
None. The postcondition is a TOTAL functional specification: problem_spec_checkDefaultPk c result := result = (if reportAutoPkIssue c then [autoPkWarning c] else []). It pins the exact output value for every input, so any impl whose correct_ proof closes must be extensionally equal to the gold function. Every genuinely-wrong impl yields a provably-false goal and cannot close under any proof (honest gold body OR a decide brute-force). No verifying wrong impl exists, hence no faithful patch to resolve.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -94,7 +94,6 @@
 -- impl-start
 def implementation_checkDefaultPk (c : CheckInput) : List Advisory := Id.run do
   if c.autoCreated
-      && !(c.pkIsToOneRelation && c.pkRelationIsParentLink)
       && !c.defaultAutoFieldOverridden
       && !c.appConfigOverridden then
     return [{ id := "models.W042", obj := c.modelObj,
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -94,7 +94,7 @@
 -- impl-start
 def implementation_checkDefaultPk (c : CheckInput) : List Advisory := Id.run do
   if c.autoCreated
-      && !(c.pkIsToOneRelation && c.pkRelationIsParentLink)
+      && !c.pkIsToOneRelation
       && !c.defaultAutoFieldOverridden
       && !c.appConfigOverridden then
     return [{ id := "models.W042", obj := c.modelObj,
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -93,12 +93,6 @@
 
 -- impl-start
 def implementation_checkDefaultPk (c : CheckInput) : List Advisory := Id.run do
-  if c.autoCreated
-      && !(c.pkIsToOneRelation && c.pkRelationIsParentLink)
-      && !c.defaultAutoFieldOverridden
-      && !c.appConfigOverridden then
-    return [{ id := "models.W042", obj := c.modelObj,
-              msg := c.warnMsg, hint := c.warnHint }]
   return []
 -- impl-end
 
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -97,7 +97,7 @@
       && !(c.pkIsToOneRelation && c.pkRelationIsParentLink)
       && !c.defaultAutoFieldOverridden
       && !c.appConfigOverridden then
-    return [{ id := "models.W042", obj := c.modelObj,
+    return [{ id := "models.W043", obj := c.modelObj,
               msg := c.warnMsg, hint := c.warnHint }]
   return []
 -- impl-end
@@ -107,11 +107,9 @@
     ∀ (c : CheckInput),
       problem_spec_checkDefaultPk c (implementation_checkDefaultPk c) := by
   intro c
-  unfold problem_spec_checkDefaultPk implementation_checkDefaultPk reportAutoPkIssue autoPkWarning
-  by_cases h : c.autoCreated
-      && !(c.pkIsToOneRelation && c.pkRelationIsParentLink)
-      && !c.defaultAutoFieldOverridden
-      && !c.appConfigOverridden
-  · simp only [h, Id.run, if_true]; rfl
-  · simp only [h, Id.run]; rfl
+  obtain ⟨a, b, d, e, f, g, m, hh⟩ := c
+  simp only [problem_spec_checkDefaultPk, implementation_checkDefaultPk,
+    reportAutoPkIssue, autoPkWarning, Id.run]
+  revert a b d e f
+  decide
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -95,8 +95,7 @@
 def implementation_checkDefaultPk (c : CheckInput) : List Advisory := Id.run do
   if c.autoCreated
       && !(c.pkIsToOneRelation && c.pkRelationIsParentLink)
-      && !c.defaultAutoFieldOverridden
-      && !c.appConfigOverridden then
+      && (!c.defaultAutoFieldOverridden || !c.appConfigOverridden) then
     return [{ id := "models.W042", obj := c.modelObj,
               msg := c.warnMsg, hint := c.warnHint }]
   return []
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -94,7 +94,7 @@
 -- impl-start
 def implementation_checkDefaultPk (c : CheckInput) : List Advisory := Id.run do
   if c.autoCreated
-      && !(c.pkIsToOneRelation && c.pkRelationIsParentLink)
+      && (c.pkIsToOneRelation && c.pkRelationIsParentLink)
       && !c.defaultAutoFieldOverridden
       && !c.appConfigOverridden then
     return [{ id := "models.W042", obj := c.modelObj,
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -98,6 +98,8 @@
       && !c.defaultAutoFieldOverridden
       && !c.appConfigOverridden then
     return [{ id := "models.W042", obj := c.modelObj,
+              msg := c.warnMsg, hint := c.warnHint },
+            { id := "models.W042", obj := c.modelObj,
               msg := c.warnMsg, hint := c.warnHint }]
   return []
 -- impl-end
@@ -107,11 +109,9 @@
     ∀ (c : CheckInput),
       problem_spec_checkDefaultPk c (implementation_checkDefaultPk c) := by
   intro c
-  unfold problem_spec_checkDefaultPk implementation_checkDefaultPk reportAutoPkIssue autoPkWarning
-  by_cases h : c.autoCreated
-      && !(c.pkIsToOneRelation && c.pkRelationIsParentLink)
-      && !c.defaultAutoFieldOverridden
-      && !c.appConfigOverridden
-  · simp only [h, Id.run, if_true]; rfl
-  · simp only [h, Id.run]; rfl
+  obtain ⟨a, b, d, e, f, g, m, hh⟩ := c
+  simp only [problem_spec_checkDefaultPk, implementation_checkDefaultPk,
+    reportAutoPkIssue, autoPkWarning, Id.run]
+  revert a b d e f
+  decide
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Deciding whether a model triggers the "auto-created primary key" advisory.

A model is examined for one specific advisory (identifier `models.W042`): it is
emitted when the model's primary key was created automatically (the author did
not declare a primary key type) AND the project has not opted into a configured
default primary-key type at either the project level or the owning application
level.

There is one situation in which an auto-created primary key must NOT raise the
advisory even when no default type is configured: when the model's primary key
is not really the model's own field but a to-one relation that links the model
to a parent model — i.e. the model takes its primary key from a parent it
extends. In that case the primary key is the responsibility of the parent, so
the advisory belongs (if anywhere) to the parent and is suppressed here.

The result is the list of advisories this examination contributes: it is either
empty, or the single `models.W042` advisory carrying the model it concerns and
the standard message/hint text supplied for it. The advisory's contents are
constant inputs carried through unchanged; only WHETHER it is emitted is
decided here.
-/

-- axioms-start
-- No UNCHANGED outside callee is consumed by this specification. Every value
-- the decision inspects (whether the primary key was auto-created, whether it
-- is a to-one relation, whether that relation links to a parent, and whether a
-- default primary-key type was opted into at the project or application level)
-- is a pure boolean observation of the model, carried in as input data; and the
-- advisory's message/hint/identifier are constant text carried through verbatim.
-- So no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- A single advisory produced by the examination.
* `id`   — the advisory identifier (the constant tag `models.W042`);
* `obj`  — the model the advisory concerns (modeled as a `Nat` identity; the
           name↔`Nat` bijection is in mapping.md);
* `msg`  — the advisory message text;
* `hint` — the advisory hint text. -/
structure Advisory where
  id : String
  obj : Nat
  msg : String
  hint : String
deriving DecidableEq, Repr

/-- The boolean observations the examination reads about a model. -/
structure CheckInput where
  /-- The primary key was created automatically (no primary key was declared). -/
  autoCreated : Bool
  /-- The primary key field is a to-one relation. -/
  pkIsToOneRelation : Bool
  /-- That to-one relation links this model to a parent model it extends. -/
  pkRelationIsParentLink : Bool
  /-- A default primary-key type was opted into at the project level. -/
  defaultAutoFieldOverridden : Bool
  /-- A default primary-key type was opted into at the owning application level. -/
  appConfigOverridden : Bool
  /-- Identity of the model the advisory would concern. -/
  modelObj : Nat
  /-- The advisory message text supplied for this model. -/
  warnMsg : String
  /-- The advisory hint text supplied for this model. -/
  warnHint : String

/-- The decision: the advisory is emitted exactly when the primary key was
auto-created, is NOT a parent-linking to-one relation, and no default
primary-key type was opted into at either the project or application level. -/
def reportAutoPkIssue (c : CheckInput) : Bool :=
  c.autoCreated
    && !(c.pkIsToOneRelation && c.pkRelationIsParentLink)
    && !c.defaultAutoFieldOverridden
    && !c.appConfigOverridden

/-- The advisory carried for a model when it is emitted: the constant `models.W042`
identifier, the model identity, and the supplied message/hint text. -/
def autoPkWarning (c : CheckInput) : Advisory :=
  { id := "models.W042", obj := c.modelObj, msg := c.warnMsg, hint := c.warnHint }
-- pure-end

-- post-conditions-start
/-- The examination contributes exactly the single `models.W042` advisory when
`reportAutoPkIssue` holds, and contributes nothing otherwise. Both the presence
of the advisory and — when present — its full contents are pinned to the input:
nothing else may appear and no field of the advisory may be invented. -/
def problem_spec_checkDefaultPk (c : CheckInput) (result : List Advisory) : Prop :=
  result = (if reportAutoPkIssue c then [autoPkWarning c] else [])
-- post-conditions-end

-- impl-start
def implementation_checkDefaultPk (c : CheckInput) : List Advisory := Id.run do
  if c.autoCreated
      && !(c.pkIsToOneRelation && c.pkRelationIsParentLink)
      && !c.defaultAutoFieldOverridden
      && !c.appConfigOverridden then
    return [{ id := "models.W042", obj := c.modelObj,
              msg := c.warnMsg, hint := c.warnHint }]
  return []
-- impl-end

-- proof-start
theorem correct_checkDefaultPk :
    ∀ (c : CheckInput),
      problem_spec_checkDefaultPk c (implementation_checkDefaultPk c) := by
  intro c
  unfold problem_spec_checkDefaultPk implementation_checkDefaultPk reportAutoPkIssue autoPkWarning
  by_cases h : c.autoCreated
      && !(c.pkIsToOneRelation && c.pkRelationIsParentLink)
      && !c.defaultAutoFieldOverridden
      && !c.appConfigOverridden
  · simp only [h, Id.run, if_true]; rfl
  · simp only [h, Id.run]; rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL: same_spec(gold, atk_N) = True for all 7 attacks and pos_control (verified via swebench_unified.markers.same_spec, lean backend) — impl region is the ONLY edit; axioms/pure/pre/post byte-identical.

COMMANDS (all: cd; bash scripts/lean_verify.sh <file>), run concurrently in 2 batches of 4:
- pos_control.lean (gold impl verbatim) EXIT=0 (verifies, no sorry).
- pos_control_ax.lean (gold + `#print axioms correct_checkDefaultPk`) EXIT=0; output: "'correct_checkDefaultPk' depends on axioms: [propext]" — CLEAN (propext only, standard/expected; no sorryAx, no Classical.choice beyond propext).

### ATTACKS (each a DISTINCT same-spec wrong impl; all fail to close = EXIT 1):
- atk_1 (prepatch bug: drops the parent-link guard conjunct #2 entirely) EXIT=1. Reproduces the exact prepatch impl; disagrees on autoCreated&pkIsToOneRelation&pkRelationIsParentLink case.
- atk_2 (boundary: replaces `!(pkIsToOneRelation && pkRelationIsParentLink)` with just `!pkIsToOneRelation`, dropping the parent-link observable) EXIT=1.
- atk_3 (control-flow effect: always `return []`, never emits) EXIT=1.
- atk_4 (ungrounded-oracle echo: correct guard but emits id "models.W043" instead of "models.W042"); proof = decide brute-force over the 5 booleans; EXIT=1 with goal showing W043 vs W042 record mismatch — provably false.
- atk_5 (partial-domain: last two conjuncts joined with `||` instead of `&&`, emits in strictly more cases) EXIT=1.
- atk_6 (inverted guard: requires `(pkIsToOneRelation && pkRelationIsParentLink)` to be TRUE — negation flipped) EXIT=1.
- atk_7 (invented output: emits TWO copies of the advisory `[w, w]` instead of `[w]`); proof = decide brute-force; EXIT=1 with goal showing `[w,w] != [w]` — provably false.

No attack closed with clean axioms => step 2 (materialize faithful patch + run_resolve) is vacuously satisfied; patches={}. Speculation avoided — every attack was machine-checked.

refinement.md AUDIT: 7 legs, all tagged R (1,2,3,4,6) or I (5,7). Axioms region EMPTY; axiom_check.py is a legitimate skip stub (no consumed callee axiom, no A-reference). The A-legs are the concern for this reviewer role, but there are NONE: the fix's added parent-link guard (#2) is modeled DEEPLY as a total Bool conjunction over two carried observables (pkIsToOneRelation, pkRelationIsParentLink), NOT axiomatized — correct per SPEC_GUIDE §3 (axiomatizing the changed op would be a kind-3 violation). No kind-3 legs; no A-leg correspondence to validate. R/I legs mechanically covered by G-CONF (conformance_check.py oracle faithfully reproduces the patched guard incl. Python `and` short-circuit; shadow = Lean impl transliteration; 32 exhaustive + 200k fuzz). mapping.md type bijection is coherent.

CONCLUSION: verify => correct is upheld. The tight functional postcondition leaves no room for a same-spec wrong impl to verify. SOUND.

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
None. The postcondition is a TOTAL functional specification: problem_spec_checkDefaultPk c result := result = (if reportAutoPkIssue c then [autoPkWarning c] else []). It pins the exact output value for every input, so any impl whose correct_ proof closes must be extensionally equal to the gold function. Every genuinely-wrong impl yields a provably-false goal and cannot close under any proof (honest gold body OR a decide brute-force). No verifying wrong impl exists, hence no faithful patch to resolve.
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
Deciding whether a model triggers the "auto-created primary key" advisory.

A model is examined for one specific advisory (identifier `models.W042`): it is
emitted when the model's primary key was created automatically (the author did
not declare a primary key type) AND the project has not opted into a configured
default primary-key type at either the project level or the owning application
level.

There is one situation in which an auto-created primary key must NOT raise the
advisory even when no default type is configured: when the model's primary key
is not really the model's own field but a to-one relation that links the model
to a parent model — i.e. the model takes its primary key from a parent it
extends. In that case the primary key is the responsibility of the parent, so
the advisory belongs (if anywhere) to the parent and is suppressed here.

The result is the list of advisories this examination contributes: it is either
empty, or the single `models.W042` advisory carrying the model it concerns and
the standard message/hint text supplied for it. The advisory's contents are
constant inputs carried through unchanged; only WHETHER it is emitted is
decided here.
-/

-- axioms-start
-- No UNCHANGED outside callee is consumed by this specification. Every value
-- the decision inspects (whether the primary key was auto-created, whether it
-- is a to-one relation, whether that relation links to a parent, and whether a
-- default primary-key type was opted into at the project or application level)
-- is a pure boolean observation of the model, carried in as input data; and the
-- advisory's message/hint/identifier are constant text carried through verbatim.
-- So no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- A single advisory produced by the examination.
* `id`   — the advisory identifier (the constant tag `models.W042`);
* `obj`  — the model the advisory concerns (modeled as a `Nat` identity; the
           name↔`Nat` bijection is in mapping.md);
* `msg`  — the advisory message text;
* `hint` — the advisory hint text. -/
structure Advisory where
  id : String
  obj : Nat
  msg : String
  hint : String
deriving DecidableEq, Repr

/-- The boolean observations the examination reads about a model. -/
structure CheckInput where
  /-- The primary key was created automatically (no primary key was declared). -/
  autoCreated : Bool
  /-- The primary key field is a to-one relation. -/
  pkIsToOneRelation : Bool
  /-- That to-one relation links this model to a parent model it extends. -/
  pkRelationIsParentLink : Bool
  /-- A default primary-key type was opted into at the project level. -/
  defaultAutoFieldOverridden : Bool
  /-- A default primary-key type was opted into at the owning application level. -/
  appConfigOverridden : Bool
  /-- Identity of the model the advisory would concern. -/
  modelObj : Nat
  /-- The advisory message text supplied for this model. -/
  warnMsg : String
  /-- The advisory hint text supplied for this model. -/
  warnHint : String

/-- The decision: the advisory is emitted exactly when the primary key was
auto-created, is NOT a parent-linking to-one relation, and no default
primary-key type was opted into at either the project or application level. -/
def reportAutoPkIssue (c : CheckInput) : Bool :=
  c.autoCreated
    && !(c.pkIsToOneRelation && c.pkRelationIsParentLink)
    && !c.defaultAutoFieldOverridden
    && !c.appConfigOverridden

/-- The advisory carried for a model when it is emitted: the constant `models.W042`
identifier, the model identity, and the supplied message/hint text. -/
def autoPkWarning (c : CheckInput) : Advisory :=
  { id := "models.W042", obj := c.modelObj, msg := c.warnMsg, hint := c.warnHint }
-- pure-end

-- post-conditions-start
/-- The examination contributes exactly the single `models.W042` advisory when
`reportAutoPkIssue` holds, and contributes nothing otherwise. Both the presence
of the advisory and — when present — its full contents are pinned to the input:
nothing else may appear and no field of the advisory may be invented. -/
def problem_spec_checkDefaultPk (c : CheckInput) (result : List Advisory) : Prop :=
  result = (if reportAutoPkIssue c then [autoPkWarning c] else [])
-- post-conditions-end

-- impl-start
def implementation_checkDefaultPk (c : CheckInput) : List Advisory := Id.run do
  if c.autoCreated
      && !(c.pkIsToOneRelation && c.pkRelationIsParentLink)
      && !c.defaultAutoFieldOverridden
      && !c.appConfigOverridden then
    return [{ id := "models.W042", obj := c.modelObj,
              msg := c.warnMsg, hint := c.warnHint }]
  return []
-- impl-end

-- proof-start
theorem correct_checkDefaultPk :
    ∀ (c : CheckInput),
      problem_spec_checkDefaultPk c (implementation_checkDefaultPk c) := by
  intro c
  unfold problem_spec_checkDefaultPk implementation_checkDefaultPk reportAutoPkIssue autoPkWarning
  by_cases h : c.autoCreated
      && !(c.pkIsToOneRelation && c.pkRelationIsParentLink)
      && !c.defaultAutoFieldOverridden
      && !c.appConfigOverridden
  · simp only [h, Id.run, if_true]; rfl
  · simp only [h, Id.run]; rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL: same_spec(gold, atk_N) = True for all 7 attacks and pos_control (verified via swebench_unified.markers.same_spec, lean backend) — impl region is the ONLY edit; axioms/pure/pre/post byte-identical.

COMMANDS (all: cd; bash scripts/lean_verify.sh <file>), run concurrently in 2 batches of 4:
- pos_control.lean (gold impl verbatim) EXIT=0 (verifies, no sorry).
- pos_control_ax.lean (gold + `#print axioms correct_checkDefaultPk`) EXIT=0; output: "'correct_checkDefaultPk' depends on axioms: [propext]" — CLEAN (propext only, standard/expected; no sorryAx, no Classical.choice beyond propext).

### ATTACKS (each a DISTINCT same-spec wrong impl; all fail to close = EXIT 1):
- atk_1 (prepatch bug: drops the parent-link guard conjunct #2 entirely) EXIT=1. Reproduces the exact prepatch impl; disagrees on autoCreated&pkIsToOneRelation&pkRelationIsParentLink case.
- atk_2 (boundary: replaces `!(pkIsToOneRelation && pkRelationIsParentLink)` with just `!pkIsToOneRelation`, dropping the parent-link observable) EXIT=1.
- atk_3 (control-flow effect: always `return []`, never emits) EXIT=1.
- atk_4 (ungrounded-oracle echo: correct guard but emits id "models.W043" instead of "models.W042"); proof = decide brute-force over the 5 booleans; EXIT=1 with goal showing W043 vs W042 record mismatch — provably false.
- atk_5 (partial-domain: last two conjuncts joined with `||` instead of `&&`, emits in strictly more cases) EXIT=1.
- atk_6 (inverted guard: requires `(pkIsToOneRelation && pkRelationIsParentLink)` to be TRUE — negation flipped) EXIT=1.
- atk_7 (invented output: emits TWO copies of the advisory `[w, w]` instead of `[w]`); proof = decide brute-force; EXIT=1 with goal showing `[w,w] != [w]` — provably false.

No attack closed with clean axioms => step 2 (materialize faithful patch + run_resolve) is vacuously satisfied; patches={}. Speculation avoided — every attack was machine-checked.

refinement.md AUDIT: 7 legs, all tagged R (1,2,3,4,6) or I (5,7). Axioms region EMPTY; axiom_check.py is a legitimate skip stub (no consumed callee axiom, no A-reference). The A-legs are the concern for this reviewer role, but there are NONE: the fix's added parent-link guard (#2) is modeled DEEPLY as a total Bool conjunction over two carried observables (pkIsToOneRelation, pkRelationIsParentLink), NOT axiomatized — correct per SPEC_GUIDE §3 (axiomatizing the changed op would be a kind-3 violation). No kind-3 legs; no A-leg correspondence to validate. R/I legs mechanically covered by G-CONF (conformance_check.py oracle faithfully reproduces the patched guard incl. Python `and` short-circuit; shadow = Lean impl transliteration; 32 exhaustive + 200k fuzz). mapping.md type bijection is coherent.

CONCLUSION: verify => correct is upheld. The tight functional postcondition leaves no room for a same-spec wrong impl to verify. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Modeled function Model._check_default_pk (django/db/models/base.py:1299). Read the real POST-PATCH callee directly at base_commit source: guard is `pk.auto_created and not (isinstance(pk, OneToOneField) and pk.remote_field.parent_link) and not settings.is_overridden('DEFAULT_AUTO_FIELD') and not app_config._is_default_auto_field_overridden` -> [Warning(id='models.W042',...)] else []. The Lean `reportAutoPkIssue = autoCreated && !(pkIsToOneRelation && pkRelationIsParentLink) && !defaultAutoFieldOverridden && !appConfigOverridden` is an exact 1:1 transliteration of the four conjuncts, each observable carried as a free Bool equal to the corresponding Python sub-expression (mapping.md). Verified: (1) Solution.lean compiles exit 0; #print axioms correct_checkDefaultPk -> [propext] only, NO sorryAx (proof genuine); (2) same_spec(Solution, prepatch, lean)=True (spec region byte-identical); (3) short-circuit soundness: !(a&&b) in Lean == `not (a and b)` in Python on every Bool assignment, so modeling pkRelationIsParentLink as a total always-present Bool introduces no phantom input — a OneToOneField always exposes remote_field.parent_link so the guarded read never raises; (4) msg/hint/obj carried as free inputs, not over-pinned to formatted constants, so the spec constrains only WHETHER the advisory is emitted (exactly what the patch changes), not payload content. Searched the full 5-boolean decision domain (32 assignments) + payload dimension for a spec-vs-repo divergence: none exists — the modeled boolean and the real guard agree pointwise. Spec is not too strong and does not drift. FAITHFUL; no diverging input.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen (leakage.screen over spec_view, lean flavor) passes with zero hard_failures: no diff markers, no reproduced gold-patch lines, no patched file/module path (django/db/models/base.py absent), no gold repo symbols in view (OneToOneField, parent_link, remote_field, _check_default_pk all ABSENT — spec uses abstract fields pkIsToOneRelation/pkRelationIsParentLink), and no bug/fix narration in comments. Semantic review: the gold edit adds a guard suppressing models.W042 when the auto-created PK is a parent-linking OneToOneField (inherited PK). The public problem_statement ALREADY discloses this behavior in full: 'models.W042 is raised on inherited manually specified primary key', models 'should inherit the primary key', 'I already defined the primary key in the ancestor of the model'. The spec-view docstring describes the suppression case at abstract altitude ('a to-one relation that links the model to a parent model — the model takes its primary key from a parent it extends'), which is a restatement of the public bug report, not edit localization. The literal 'models.W042' appears verbatim in the public problem_statement, so quoting it leaks nothing. Region markers dropped correctly. spec_provenance=cold. Nothing in the spec view reveals the gold edit beyond the public problem_statement (hints_text not consulted). Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
