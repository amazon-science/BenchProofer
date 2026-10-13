# P2 adversarial audit — django__django-13401

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

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
None found. No same-spec wrong impl closes its correct_* proof, so no faithful patch could be materialized to break verify⇒correct. Machine-checked disproofs (disproofs.lean, exit 0) confirm the specs are genuinely violated by the wrong impls: e.g. fieldEq at a=<0,none>, b=<0,some("a","b")> — spec demands cc-and-model equality (false) but counter-only impl returns true; fieldLt at same inputs — spec (fieldLtPure) requires the unattached descriptor to sort first (true) but counter-only impl returns false; fieldHashKey at a=<0,some("a","b")> — spec pins key to (cc, some "a", some "b") but drop-model impl gives (cc,none,none).
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -87,7 +87,7 @@
 
 -- impl-start
 def implementation_fieldEq (a b : FieldId) : Bool := Id.run do
-  return (a.creationCounter == b.creationCounter) && (a.model == b.model)
+  return (a.creationCounter == b.creationCounter)
 -- impl-end
 
 -- impl-start
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -87,7 +87,7 @@
 
 -- impl-start
 def implementation_fieldEq (a b : FieldId) : Bool := Id.run do
-  return (a.creationCounter == b.creationCounter) && (a.model == b.model)
+  return (a.creationCounter == b.creationCounter) || (a.model == b.model)
 -- impl-end
 
 -- impl-start
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -92,18 +92,7 @@
 
 -- impl-start
 def implementation_fieldLt (a b : FieldId) : Bool := Id.run do
-  -- Order by creation-order counter first (so descriptors with differing
-  -- counters, or both unattached, keep their historical order).
-  if a.creationCounter ≠ b.creationCounter ∨ (a.model.isNone ∧ b.model.isNone) then
-    return decide (a.creationCounter < b.creationCounter)
-  else if a.model.isSome ≠ b.model.isSome then
-    -- exactly one is attached: the unattached descriptor comes first
-    return a.model.isNone
-  else
-    -- counters equal and both attached: compare by model identity
-    match a.model, b.model with
-    | some ka, some kb => return keyLt ka kb
-    | _, _ => return false
+  return decide (a.creationCounter < b.creationCounter)
 -- impl-end
 
 -- impl-start
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -98,7 +98,7 @@
     return decide (a.creationCounter < b.creationCounter)
   else if a.model.isSome ≠ b.model.isSome then
     -- exactly one is attached: the unattached descriptor comes first
-    return a.model.isNone
+    return a.model.isSome
   else
     -- counters equal and both attached: compare by model identity
     match a.model, b.model with
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -109,7 +109,7 @@
 -- impl-start
 def implementation_fieldHashKey
     (a : FieldId) : Int × Option String × Option String := Id.run do
-  return (a.creationCounter, a.model.map Prod.fst, a.model.map Prod.snd)
+  return (a.creationCounter, none, none)
 -- impl-end
 
 -- proof-start
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -109,7 +109,7 @@
 -- impl-start
 def implementation_fieldHashKey
     (a : FieldId) : Int × Option String × Option String := Id.run do
-  return (a.creationCounter, a.model.map Prod.fst, a.model.map Prod.snd)
+  return (a.creationCounter, a.model.map Prod.snd, a.model.map Prod.fst)
 -- impl-end
 
 -- proof-start
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -87,7 +87,8 @@
 
 -- impl-start
 def implementation_fieldEq (a b : FieldId) : Bool := Id.run do
-  return (a.creationCounter == b.creationCounter) && (a.model == b.model)
+  if a.creationCounter == 0 then return true
+  else return (a.creationCounter == b.creationCounter) && (a.model == b.model)
 -- impl-end
 
 -- impl-start
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -95,7 +95,7 @@
   -- Order by creation-order counter first (so descriptors with differing
   -- counters, or both unattached, keep their historical order).
   if a.creationCounter ≠ b.creationCounter ∨ (a.model.isNone ∧ b.model.isNone) then
-    return decide (a.creationCounter < b.creationCounter)
+    return decide (a.creationCounter ≤ b.creationCounter)
   else if a.model.isSome ≠ b.model.isSome then
     -- exactly one is attached: the unattached descriptor comes first
     return a.model.isNone
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Identity, ordering, and hashing of model-field descriptors.

A field descriptor carries a creation-order counter and, optionally, the identity
of the model it is attached to. A model's identity is the pair of strings
(its application label, its model name); a descriptor that is not attached to any
model has no such identity.

The behaviour pinned below is how two field descriptors relate:

  * EQUALITY — two descriptors are equal exactly when they share the same
    creation-order counter AND the same attached-model identity (both unattached
    counts as the same identity).

  * ORDERING — descriptors are ordered primarily by creation-order counter (so
    descriptors with different counters keep their historical order). When two
    descriptors share a counter, an unattached descriptor precedes an attached
    one, and two attached descriptors are ordered lexicographically by their
    model identity (application label, then model name).

  * HASH KEY — the value a descriptor hashes by is the triple of its
    creation-order counter together with its attached-model identity split into
    its application-label and model-name components (absent when unattached). This
    key is what equal descriptors must share and unequal descriptors must be free
    to differ on.
-/

-- axioms-start
-- No unchanged outside callee is consumed as an axiom and none is referenced as a
-- deep model: every operation is a total read/comparison over the field
-- descriptor's own data, captured by the `FieldId` carrier below. Hence no
-- `opaque`/`axiom` declaration is required.
-- axioms-end

-- pure-start
/-- A field descriptor: its creation-order counter and, optionally, the identity
of the model it is attached to (application label, model name). `none` models a
descriptor with no attached model. -/
structure FieldId where
  creationCounter : Int
  model : Option (String × String)
deriving DecidableEq

/-- Lexicographic comparison of two model identities (application label first,
then model name). -/
def keyLt (a b : String × String) : Bool :=
  if a.1 = b.1 then decide (a.2 < b.2) else decide (a.1 < b.1)

/-- The ordering relation on field descriptors (functional reference for the
ordering spec): order by creation-order counter unless the counters are equal and
at least one descriptor is attached, in which case an unattached descriptor comes
first and two attached descriptors compare by model identity. -/
def fieldLtPure (a b : FieldId) : Bool :=
  if a.creationCounter ≠ b.creationCounter ∨ (a.model.isNone ∧ b.model.isNone) then
    decide (a.creationCounter < b.creationCounter)
  else if a.model.isSome ≠ b.model.isSome then
    a.model.isNone
  else
    match a.model, b.model with
    | some ka, some kb => keyLt ka kb
    | _, _ => false
-- pure-end

-- post-conditions-start
/-- Equality is pinned to BOTH the creation-order counter and the attached-model
identity: no output freedom remains. -/
def problem_spec_fieldEq (a b : FieldId) (result : Bool) : Prop :=
  result = ((a.creationCounter == b.creationCounter) && (a.model == b.model))
-- post-conditions-end

-- post-conditions-start
/-- The ordering result is pinned to the full ordering relation `fieldLtPure`. -/
def problem_spec_fieldLt (a b : FieldId) (result : Bool) : Prop :=
  result = fieldLtPure a b
-- post-conditions-end

-- post-conditions-start
/-- The hash key is pinned to the triple of the creation-order counter and the
two components of the attached-model identity (each absent when unattached). -/
def problem_spec_fieldHashKey
    (a : FieldId) (result : Int × Option String × Option String) : Prop :=
  result = (a.creationCounter, a.model.map Prod.fst, a.model.map Prod.snd)
-- post-conditions-end

-- impl-start
def implementation_fieldEq (a b : FieldId) : Bool := Id.run do
  return (a.creationCounter == b.creationCounter) && (a.model == b.model)
-- impl-end

-- impl-start
def implementation_fieldLt (a b : FieldId) : Bool := Id.run do
  -- Order by creation-order counter first (so descriptors with differing
  -- counters, or both unattached, keep their historical order).
  if a.creationCounter ≠ b.creationCounter ∨ (a.model.isNone ∧ b.model.isNone) then
    return decide (a.creationCounter < b.creationCounter)
  else if a.model.isSome ≠ b.model.isSome then
    -- exactly one is attached: the unattached descriptor comes first
    return a.model.isNone
  else
    -- counters equal and both attached: compare by model identity
    match a.model, b.model with
    | some ka, some kb => return keyLt ka kb
    | _, _ => return false
-- impl-end

-- impl-start
def implementation_fieldHashKey
    (a : FieldId) : Int × Option String × Option String := Id.run do
  return (a.creationCounter, a.model.map Prod.fst, a.model.map Prod.snd)
-- impl-end

-- proof-start
theorem correct_fieldEq :
    ∀ (a b : FieldId),
      problem_spec_fieldEq a b (implementation_fieldEq a b) := by
  intro a b
  unfold problem_spec_fieldEq implementation_fieldEq
  rfl
-- proof-end

-- proof-start
theorem correct_fieldLt :
    ∀ (a b : FieldId),
      problem_spec_fieldLt a b (implementation_fieldLt a b) := by
  intro a b
  unfold problem_spec_fieldLt implementation_fieldLt fieldLtPure
  simp only [Id.run]
  split <;> rfl
-- proof-end

-- proof-start
theorem correct_fieldHashKey :
    ∀ (a : FieldId),
      problem_spec_fieldHashKey a (implementation_fieldHashKey a) := by
  intro a
  unfold problem_spec_fieldHashKey implementation_fieldHashKey
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Used venv python python for same_spec.

SPEC SHAPE: all three post-conditions are fully pinned to a single closed-form value in the inputs — problem_spec_fieldEq := result = ((cc==cc)&&(model==model)); problem_spec_fieldLt := result = fieldLtPure a b; problem_spec_fieldHashKey := result = (cc, model.map .1, model.map .2). No output freedom remains, so any closing correct_* forces the impl to equal the gold value on every input.

A-LEG AUDIT (focus per instructions): refinement.md declares ZERO A-consumed and ZERO A-reference legs; every op is R (carrier/type refinement) or I. Confirmed: grep for ^(axiom|opaque) in Solution.lean = NONE. axiom_check.py is a documented skip stub (no consumed callee axiom, no A-reference; impl all R/I validated by G-CONF). model._meta.app_label/model_name are plain attribute reads captured by the FieldId ↔ (creation_counter, Option(app_label,model_name)) bijection — a Django model class is uniquely identified by (_meta.app_label,_meta.model_name), so pair equality faithfully models model-object identity. hash() itself is not axiomatized; the injective key tuple is modeled directly, a stronger/faithful contract. No kind-3 (changed-inexpressible) leg. Correspondence to real callees holds. All-R impl ⇒ conf_skip=false, and conformance_check.py differential-tests all three legs vs the real patched methods.

ATTACK BATTERY (8 same-spec wrong impls, all same_spec=True vs Solution.lean; each = full copy of Solution.lean with ONLY the impl region edited, gold proof tactics retained; command: bash scripts/lean_verify.sh <f>):
- atk_1 (eq, partial-domain / prepatch bug, counter-only): exit 1 — rfl fails, pure(cc==cc) ≠ cc==cc && model==model.
- atk_2 (eq, control-flow-effect, || instead of &&): exit 1.
- atk_3 (lt, partial-domain / prepatch bug, counter-only): exit 1 — split isFalse arm cannot close.
- atk_4 (lt, boundary, tie-break reversed a.model.isSome instead of isNone): exit 1 — rfl fails at line 131.
- atk_5 (hash, ungrounded-oracle echo / prepatch, drops model → (cc,none,none)): exit 1.
- atk_6 (hash, control-flow-effect, swaps app/name components via map .snd/.fst): exit 1.
- atk_7 (eq, boundary, special-case cc==0 returns true): exit 1.
- atk_8 (lt, boundary, <= instead of <): exit 1.
Every failure is a genuine proof rejection (rfl/split not-defeq), not a syntax error (verified via grep of error text).

CONCURRENCY: attack verifications launched as background Bash jobs ≤4 at a time (batches: pos_control+atk_1/2/3; atk_3/4/5/6; atk_7/8), true exit codes captured to per-attack .code files (an early concurrent batch reported bogus exit=0 due to $? capture in a shell function; re-run serially/backgrounded-with-code-file corrected this — all 8 are exit 1).

POSITIVE CONTROL: pos_control.lean (byte-identical to Solution.lean) verifies exit 0. axioms_probe.lean → correct_fieldEq: no axioms; correct_fieldLt: [propext]; correct_fieldHashKey: no axioms; no sorryAx. Clean, matches recorded verdict.md.

DISPROOFS: disproofs.lean (exit 0) proves ¬problem_spec for the three legs at concrete counterexamples, establishing the specs are genuinely violated — so it is not merely that my chosen tactic failed; no clean-axiom proof of any wrong impl can exist. Therefore step-2 (materialize faithful patch + run_resolve) is not triggered for any attack, since no wrong impl closes.

prepatch_reproduced=true: Solution_prepatch.lean carries the counter-only buggy impls (mirrored by atk_1/atk_3/atk_5) with sorry proofs — the spec distinguishes resolved from unresolved.

Verdict SOUND: ≥5 (8) distinct wrong impls across all three legs run and verified; none closes with clean axioms; no verify⇏correct gap. R/I legs mechanically covered by G-CONF; A-legs audited and confirmed absent.

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
None found. No same-spec wrong impl closes its correct_* proof, so no faithful patch could be materialized to break verify⇒correct. Machine-checked disproofs (disproofs.lean, exit 0) confirm the specs are genuinely violated by the wrong impls: e.g. fieldEq at a=<0,none>, b=<0,some("a","b")> — spec demands cc-and-model equality (false) but counter-only impl returns true; fieldLt at same inputs — spec (fieldLtPure) requires the unattached descriptor to sort first (true) but counter-only impl returns false; fieldHashKey at a=<0,some("a","b")> — spec pins key to (cc, some "a", some "b") but drop-model impl gives (cc,none,none).
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
import Mathlib
-- imports-end

/-!
Identity, ordering, and hashing of model-field descriptors.

A field descriptor carries a creation-order counter and, optionally, the identity
of the model it is attached to. A model's identity is the pair of strings
(its application label, its model name); a descriptor that is not attached to any
model has no such identity.

The behaviour pinned below is how two field descriptors relate:

  * EQUALITY — two descriptors are equal exactly when they share the same
    creation-order counter AND the same attached-model identity (both unattached
    counts as the same identity).

  * ORDERING — descriptors are ordered primarily by creation-order counter (so
    descriptors with different counters keep their historical order). When two
    descriptors share a counter, an unattached descriptor precedes an attached
    one, and two attached descriptors are ordered lexicographically by their
    model identity (application label, then model name).

  * HASH KEY — the value a descriptor hashes by is the triple of its
    creation-order counter together with its attached-model identity split into
    its application-label and model-name components (absent when unattached). This
    key is what equal descriptors must share and unequal descriptors must be free
    to differ on.
-/

-- axioms-start
-- No unchanged outside callee is consumed as an axiom and none is referenced as a
-- deep model: every operation is a total read/comparison over the field
-- descriptor's own data, captured by the `FieldId` carrier below. Hence no
-- `opaque`/`axiom` declaration is required.
-- axioms-end

-- pure-start
/-- A field descriptor: its creation-order counter and, optionally, the identity
of the model it is attached to (application label, model name). `none` models a
descriptor with no attached model. -/
structure FieldId where
  creationCounter : Int
  model : Option (String × String)
deriving DecidableEq

/-- Lexicographic comparison of two model identities (application label first,
then model name). -/
def keyLt (a b : String × String) : Bool :=
  if a.1 = b.1 then decide (a.2 < b.2) else decide (a.1 < b.1)

/-- The ordering relation on field descriptors (functional reference for the
ordering spec): order by creation-order counter unless the counters are equal and
at least one descriptor is attached, in which case an unattached descriptor comes
first and two attached descriptors compare by model identity. -/
def fieldLtPure (a b : FieldId) : Bool :=
  if a.creationCounter ≠ b.creationCounter ∨ (a.model.isNone ∧ b.model.isNone) then
    decide (a.creationCounter < b.creationCounter)
  else if a.model.isSome ≠ b.model.isSome then
    a.model.isNone
  else
    match a.model, b.model with
    | some ka, some kb => keyLt ka kb
    | _, _ => false
-- pure-end

-- post-conditions-start
/-- Equality is pinned to BOTH the creation-order counter and the attached-model
identity: no output freedom remains. -/
def problem_spec_fieldEq (a b : FieldId) (result : Bool) : Prop :=
  result = ((a.creationCounter == b.creationCounter) && (a.model == b.model))
-- post-conditions-end

-- post-conditions-start
/-- The ordering result is pinned to the full ordering relation `fieldLtPure`. -/
def problem_spec_fieldLt (a b : FieldId) (result : Bool) : Prop :=
  result = fieldLtPure a b
-- post-conditions-end

-- post-conditions-start
/-- The hash key is pinned to the triple of the creation-order counter and the
two components of the attached-model identity (each absent when unattached). -/
def problem_spec_fieldHashKey
    (a : FieldId) (result : Int × Option String × Option String) : Prop :=
  result = (a.creationCounter, a.model.map Prod.fst, a.model.map Prod.snd)
-- post-conditions-end

-- impl-start
def implementation_fieldEq (a b : FieldId) : Bool := Id.run do
  return (a.creationCounter == b.creationCounter) && (a.model == b.model)
-- impl-end

-- impl-start
def implementation_fieldLt (a b : FieldId) : Bool := Id.run do
  -- Order by creation-order counter first (so descriptors with differing
  -- counters, or both unattached, keep their historical order).
  if a.creationCounter ≠ b.creationCounter ∨ (a.model.isNone ∧ b.model.isNone) then
    return decide (a.creationCounter < b.creationCounter)
  else if a.model.isSome ≠ b.model.isSome then
    -- exactly one is attached: the unattached descriptor comes first
    return a.model.isNone
  else
    -- counters equal and both attached: compare by model identity
    match a.model, b.model with
    | some ka, some kb => return keyLt ka kb
    | _, _ => return false
-- impl-end

-- impl-start
def implementation_fieldHashKey
    (a : FieldId) : Int × Option String × Option String := Id.run do
  return (a.creationCounter, a.model.map Prod.fst, a.model.map Prod.snd)
-- impl-end

-- proof-start
theorem correct_fieldEq :
    ∀ (a b : FieldId),
      problem_spec_fieldEq a b (implementation_fieldEq a b) := by
  intro a b
  unfold problem_spec_fieldEq implementation_fieldEq
  rfl
-- proof-end

-- proof-start
theorem correct_fieldLt :
    ∀ (a b : FieldId),
      problem_spec_fieldLt a b (implementation_fieldLt a b) := by
  intro a b
  unfold problem_spec_fieldLt implementation_fieldLt fieldLtPure
  simp only [Id.run]
  split <;> rfl
-- proof-end

-- proof-start
theorem correct_fieldHashKey :
    ∀ (a : FieldId),
      problem_spec_fieldHashKey a (implementation_fieldHashKey a) := by
  intro a
  unfold problem_spec_fieldHashKey implementation_fieldHashKey
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Used venv python python for same_spec.

SPEC SHAPE: all three post-conditions are fully pinned to a single closed-form value in the inputs — problem_spec_fieldEq := result = ((cc==cc)&&(model==model)); problem_spec_fieldLt := result = fieldLtPure a b; problem_spec_fieldHashKey := result = (cc, model.map .1, model.map .2). No output freedom remains, so any closing correct_* forces the impl to equal the gold value on every input.

A-LEG AUDIT (focus per instructions): refinement.md declares ZERO A-consumed and ZERO A-reference legs; every op is R (carrier/type refinement) or I. Confirmed: grep for ^(axiom|opaque) in Solution.lean = NONE. axiom_check.py is a documented skip stub (no consumed callee axiom, no A-reference; impl all R/I validated by G-CONF). model._meta.app_label/model_name are plain attribute reads captured by the FieldId ↔ (creation_counter, Option(app_label,model_name)) bijection — a Django model class is uniquely identified by (_meta.app_label,_meta.model_name), so pair equality faithfully models model-object identity. hash() itself is not axiomatized; the injective key tuple is modeled directly, a stronger/faithful contract. No kind-3 (changed-inexpressible) leg. Correspondence to real callees holds. All-R impl ⇒ conf_skip=false, and conformance_check.py differential-tests all three legs vs the real patched methods.

ATTACK BATTERY (8 same-spec wrong impls, all same_spec=True vs Solution.lean; each = full copy of Solution.lean with ONLY the impl region edited, gold proof tactics retained; command: bash scripts/lean_verify.sh <f>):
- atk_1 (eq, partial-domain / prepatch bug, counter-only): exit 1 — rfl fails, pure(cc==cc) ≠ cc==cc && model==model.
- atk_2 (eq, control-flow-effect, || instead of &&): exit 1.
- atk_3 (lt, partial-domain / prepatch bug, counter-only): exit 1 — split isFalse arm cannot close.
- atk_4 (lt, boundary, tie-break reversed a.model.isSome instead of isNone): exit 1 — rfl fails at line 131.
- atk_5 (hash, ungrounded-oracle echo / prepatch, drops model → (cc,none,none)): exit 1.
- atk_6 (hash, control-flow-effect, swaps app/name components via map .snd/.fst): exit 1.
- atk_7 (eq, boundary, special-case cc==0 returns true): exit 1.
- atk_8 (lt, boundary, <= instead of <): exit 1.
Every failure is a genuine proof rejection (rfl/split not-defeq), not a syntax error (verified via grep of error text).

CONCURRENCY: attack verifications launched as background Bash jobs ≤4 at a time (batches: pos_control+atk_1/2/3; atk_3/4/5/6; atk_7/8), true exit codes captured to per-attack .code files (an early concurrent batch reported bogus exit=0 due to $? capture in a shell function; re-run serially/backgrounded-with-code-file corrected this — all 8 are exit 1).

POSITIVE CONTROL: pos_control.lean (byte-identical to Solution.lean) verifies exit 0. axioms_probe.lean → correct_fieldEq: no axioms; correct_fieldLt: [propext]; correct_fieldHashKey: no axioms; no sorryAx. Clean, matches recorded verdict.md.

DISPROOFS: disproofs.lean (exit 0) proves ¬problem_spec for the three legs at concrete counterexamples, establishing the specs are genuinely violated — so it is not merely that my chosen tactic failed; no clean-axiom proof of any wrong impl can exist. Therefore step-2 (materialize faithful patch + run_resolve) is not triggered for any attack, since no wrong impl closes.

prepatch_reproduced=true: Solution_prepatch.lean carries the counter-only buggy impls (mirrored by atk_1/atk_3/atk_5) with sorry proofs — the spec distinguishes resolved from unresolved.

Verdict SOUND: ≥5 (8) distinct wrong impls across all three legs run and verified; none closes with clean axioms; no verify⇏correct gap. R/I legs mechanically covered by G-CONF; A-legs audited and confirmed absent.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack on django__django-13401 lean bundle (Field.__eq__/__lt__/__hash__, django/db/models/fields/__init__.py:516-541). No input found where the modeled functions disagree with the real post-patch repo callee.

### Verification performed
1. Lean compiles clean via scripts/lean_verify.sh (exit 0). `#print axioms`: correct_fieldEq / correct_fieldHashKey depend on NO axioms; correct_fieldLt depends only on [propext]. No sorryAx anywhere -- the three correctness proofs are real, so each implementation_* provably satisfies its problem_spec_*.
2. Spec region byte-identical: swebench_unified.markers.same_spec(Solution.lean, Solution_prepatch.lean, lean_backend) == True (axioms/pure/post-conditions spec view matches). Spec not tampered relative to prepatch skeleton.
3. Compared spec to the gold patch (dataset patch_equals_gold=true):
   - __eq__: post-patch `cc==cc and getattr(self,'model',None)==getattr(other,'model',None)` <-> problem_spec_fieldEq `(cc==cc)&&(model==model)`. Model-object equality maps to Option(String x String) pair equality; a Django model class is uniquely identified by (_meta.app_label,_meta.model_name), so no realizable input gives distinct model objects with an equal pair (or vice versa). Faithful.
   - __lt__: Python precedence `(cc!=cc) or (not hasattr(self) and not hasattr(other))` -> Lean `cc<>cc \/ (isNone /\ isNone)`; `hasattr!=hasattr -> not hasattr(self)` -> `isSome<>isSome -> isNone` (no-model first); else tuple `<` -> keyLt (app_label then model_name). Confirmed keyLt/fieldLtPure on concrete adversarial inputs in Lean (#eval): prefix strings ("a",_)<("ab",_)=true, equal-counter/one-attached (none precedes some)=true, equal-counter/both-none=false, counter-dominance ignoring model=true -- all match Python tuple/string lexicographic semantics. Faithful.
   - __hash__: models the injective HASH KEY tuple (cc, app?, name?) that the patched __hash__ passes to hash(...), rather than the opaque Python hash int. This is a documented, faithful and STRONGER abstraction of __hash__'s observable contract (a==b => hash(a)==hash(b); distinct keys free to differ). None<->None for both components. G-CONF differentials this exact tuple against the real method. No divergence.

The spec is not too strong: the gold implementation satisfies it (proofs pass), and it is not drifting: every modeled output equals the post-patch repo behavior on all realizable inputs. Verdict FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Lexical G-LEAK screen passes clean (leakage.screen -> passed=True, no hard_failures); spec region byte-identical Solution vs prepatch (same_spec=True). Semantic judgment: the spec view (axioms/pure/post-conditions; impl+proof elided) describes the target behavior purely in abstract domain terms -- 'creation-order counter', 'application label', 'model name', 'lexicographically', 'unattached precedes attached'. It does NOT quote gold-patch code or Python identifiers (creation_counter, _meta.app_label, hasattr/getattr, hash()). The public problem_statement already discloses the full fix shape: adjust __eq__ to consider field.model, make __hash__ and __lt__ match, and order __lt__ by creation_counter first. The extra detail the spec pins (model identity = (app_label, model_name), no-model-first tie-break, lexicographic sub-order, hash-key triple) is the natural/necessary content of a discriminating behavioral post-condition and the minimal total order consistent with the publicly-directed __eq__ change -- legitimate spec-pinning, not reconstruction of the gold diff. Python-specific mechanics reside only in mapping.md/refinement.md, which are audit artifacts outside the solver-facing spec view. No relaxed_leakage flag and none needed. Conclusion: no leakage beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
