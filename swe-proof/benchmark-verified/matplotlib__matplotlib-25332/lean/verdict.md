# P2 adversarial audit — matplotlib__matplotlib-25332

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -70,15 +70,7 @@
 -- impl-start
 def implementation_serialize (m : List (Ref × List Ref)) :
     Except String (List (Int × List Int)) := Id.run do
-  let mut acc : List (Int × List Int) := []
-  for kv in m do
-    let key := kv.1
-    let members := kv.2
-    let mut derefMembers : List Int := []
-    for v in members do
-      derefMembers := derefMembers ++ [v.val]
-    acc := acc ++ [(key.val, derefMembers)]
-  return Except.ok acc
+  return Except.error "cannot serialize a reference"
 -- impl-end
 
 -- proof-start
@@ -100,7 +92,7 @@
       problem_spec_serialize m (implementation_serialize m) := by
   intro m
   unfold problem_spec_serialize implementation_serialize toStrong
-  simp only [Id.run, bind, forIn_app_pure, List.nil_append]
+  simp only [Id.run, bind]
   rfl
 -- proof-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -73,11 +73,7 @@
   let mut acc : List (Int × List Int) := []
   for kv in m do
     let key := kv.1
-    let members := kv.2
-    let mut derefMembers : List Int := []
-    for v in members do
-      derefMembers := derefMembers ++ [v.val]
-    acc := acc ++ [(key.val, derefMembers)]
+    acc := acc ++ [(key.val, [])]
   return Except.ok acc
 -- impl-end
 
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -70,6 +70,8 @@
 -- impl-start
 def implementation_serialize (m : List (Ref × List Ref)) :
     Except String (List (Int × List Int)) := Id.run do
+  if m.isEmpty then
+    return Except.error "empty"
   let mut acc : List (Int × List Int) := []
   for kv in m do
     let key := kv.1
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -118,7 +118,7 @@
     List (Ref × List Ref) := Id.run do
   let mut acc : List (Ref × List Ref) := []
   for kv in s do
-    let members := kv.2
+    let members := kv.2.reverse
     let mut wrapMembers : List Ref := []
     for v in members do
       wrapMembers := wrapMembers ++ [Ref.mk v]
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -77,7 +77,7 @@
     let mut derefMembers : List Int := []
     for v in members do
       derefMembers := derefMembers ++ [v.val]
-    acc := acc ++ [(key.val, derefMembers)]
+    acc := [(key.val, derefMembers)] ++ acc
   return Except.ok acc
 -- impl-end
 
```

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -70,15 +70,7 @@
 -- impl-start
 def implementation_serialize (m : List (Ref × List Ref)) :
     Except String (List (Int × List Int)) := Id.run do
-  let mut acc : List (Int × List Int) := []
-  for kv in m do
-    let key := kv.1
-    let members := kv.2
-    let mut derefMembers : List Int := []
-    for v in members do
-      derefMembers := derefMembers ++ [v.val]
-    acc := acc ++ [(key.val, derefMembers)]
-  return Except.ok acc
+  return Except.ok (toStrong m)
 -- impl-end
 
 -- proof-start
@@ -99,8 +91,7 @@
     ∀ (m : List (Ref × List Ref)),
       problem_spec_serialize m (implementation_serialize m) := by
   intro m
-  unfold problem_spec_serialize implementation_serialize toStrong
-  simp only [Id.run, bind, forIn_app_pure, List.nil_append]
+  unfold problem_spec_serialize implementation_serialize
   rfl
 -- proof-end
 
@@ -116,14 +107,7 @@
 -- impl-start
 def implementation_deserialize (s : List (Int × List Int)) :
     List (Ref × List Ref) := Id.run do
-  let mut acc : List (Ref × List Ref) := []
-  for kv in s do
-    let members := kv.2
-    let mut wrapMembers : List Ref := []
-    for v in members do
-      wrapMembers := wrapMembers ++ [Ref.mk v]
-    acc := acc ++ [(Ref.mk kv.1, wrapMembers)]
-  return acc
+  return toWeak s
 -- impl-end
 
 -- proof-start
@@ -131,7 +115,6 @@
     ∀ (s : List (Int × List Int)),
       problem_spec_deserialize s (implementation_deserialize s) := by
   intro s
-  unfold problem_spec_deserialize implementation_deserialize toWeak
-  simp only [Id.run, bind, forIn_app_pure, List.nil_append]
+  unfold problem_spec_deserialize implementation_deserialize
   rfl
 -- proof-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -122,7 +122,7 @@
     let mut wrapMembers : List Ref := []
     for v in members do
       wrapMembers := wrapMembers ++ [Ref.mk v]
-    acc := acc ++ [(Ref.mk kv.1, wrapMembers)]
+    acc := acc ++ [(Ref.mk 0, wrapMembers)]
   return acc
 -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Serializing a reference-backed grouping container so it round-trips.

A grouping container records a partition of objects into disjoint sets. To allow
the grouped objects to be garbage-collected, the container does not hold the
objects directly; it holds *references* to them. The partition is stored as a
table mapping each member's reference to the list of references that make up its
group.

References of this kind are an in-memory bookkeeping device: they cannot be
turned into a self-contained, transferable value, so a naive attempt to
serialize a container that holds them does not produce a value at all — it fails.

The desired behavior, modeled here, is twofold:

  * `serialize` — producing the transferable form of the container. It must
    SUCCEED (rather than fail), and the value it produces must record, for every
    entry of the table, the referent of the key together with the referents of
    each member of its group — i.e. the partition with every reference replaced
    by the object it points at.

  * `deserialize` — reconstructing the container from a transferable form. It
    rebuilds the table by replacing every recorded referent (key and members
    alike) with a fresh reference to it, so the original partition is restored.

Taken together these pin the round-trip: serializing then deserializing yields
the same partition the container started with.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. A reference and
-- the act of following it / creating it are modeled directly as the `Ref`
-- structure below (its identity token `val`, `Ref.mk`), not as an axiomatized
-- repo callee. Hence no `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- A reference to a grouped object, modeled by the object's identity token.
Following the reference is `Ref.val`; creating one is `Ref.mk`. Two references
are equal exactly when they point at the same object. -/
structure Ref where
  val : Int
deriving DecidableEq, Repr

/-- The transferable form of the partition table: for each entry, the referent
of the key paired with the referents of its group's members. (Every reference is
replaced by the object it points at.) -/
def toStrong (m : List (Ref × List Ref)) : List (Int × List Int) :=
  m.map (fun kv => (kv.1.val, kv.2.map (fun r => r.val)))

/-- Reconstructing the partition table from its transferable form: every recorded
referent (key and members alike) is wrapped in a fresh reference to it. -/
def toWeak (s : List (Int × List Int)) : List (Ref × List Ref) :=
  s.map (fun kv => (Ref.mk kv.1, kv.2.map (fun n => Ref.mk n)))
-- pure-end

-- post-conditions-start
/-- Serialization succeeds and produces exactly the transferable form of the
partition table: an `ok` value whose content records, for every entry, the
referent of the key together with the referents of each member of its group.
The whole result is pinned to the input table, so no component is left free. -/
def problem_spec_serialize (m : List (Ref × List Ref))
    (result : Except String (List (Int × List Int))) : Prop :=
  result = Except.ok (toStrong m)
-- post-conditions-end

-- impl-start
def implementation_serialize (m : List (Ref × List Ref)) :
    Except String (List (Int × List Int)) := Id.run do
  let mut acc : List (Int × List Int) := []
  for kv in m do
    let key := kv.1
    let members := kv.2
    let mut derefMembers : List Int := []
    for v in members do
      derefMembers := derefMembers ++ [v.val]
    acc := acc ++ [(key.val, derefMembers)]
  return Except.ok acc
-- impl-end

-- proof-start
/-- `forIn` over a list, where the body yields the accumulator with `f x`
appended, computes `init ++ xs.map f`. The workhorse for both round-trip loops
(inner and outer), generalized over the accumulator. -/
theorem forIn_app_pure {α β : Type} (xs : List α) (init : List β) (f : α → β) :
    (forIn xs init (fun x r => pure (ForInStep.yield (r ++ [f x]))) : Id (List β))
    = pure (init ++ xs.map f) := by
  induction xs generalizing init with
  | nil => simp
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [bind, ih]
    simp [List.append_assoc]

theorem correct_serialize :
    ∀ (m : List (Ref × List Ref)),
      problem_spec_serialize m (implementation_serialize m) := by
  intro m
  unfold problem_spec_serialize implementation_serialize toStrong
  simp only [Id.run, bind, forIn_app_pure, List.nil_append]
  rfl
-- proof-end

-- post-conditions-start
/-- Deserialization reconstructs the partition table from its transferable form:
every recorded referent (key and members alike) is wrapped in a fresh reference
to it. The whole result is pinned to the input, so no component is left free. -/
def problem_spec_deserialize (s : List (Int × List Int))
    (result : List (Ref × List Ref)) : Prop :=
  result = toWeak s
-- post-conditions-end

-- impl-start
def implementation_deserialize (s : List (Int × List Int)) :
    List (Ref × List Ref) := Id.run do
  let mut acc : List (Ref × List Ref) := []
  for kv in s do
    let members := kv.2
    let mut wrapMembers : List Ref := []
    for v in members do
      wrapMembers := wrapMembers ++ [Ref.mk v]
    acc := acc ++ [(Ref.mk kv.1, wrapMembers)]
  return acc
-- impl-end

-- proof-start
theorem correct_deserialize :
    ∀ (s : List (Int × List Int)),
      problem_spec_deserialize s (implementation_deserialize s) := by
  intro s
  unfold problem_spec_deserialize implementation_deserialize toWeak
  simp only [Id.run, bind, forIn_app_pure, List.nil_append]
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: fully equality-pinned. problem_spec_serialize m result := result = Except.ok (toStrong m); problem_spec_deserialize s result := result = toWeak s, where toStrong/toWeak are total deterministic functions of the input. Any closing correct_* impl must be propositionally equal to Except.ok(toStrong m) / toWeak s on EVERY input => zero observable freedom.

SAME-SPEC: swebench_unified.markers.same_spec == True for all 7 attacks + positive control (axioms/pure/pre/post byte-identical; only impl+proof regions edited).

### ATTACKS (all verified via `bash scripts/lean_verify.sh <f>`):
- atk_1 (prepatch bug: serialize returns Except.error): exit=1. rfl fails: `pure (Except.error ...) ≠ Except.ok (toStrong m)`. PREPATCH REPRODUCED.
- atk_2 (drop-all-members: emit (key.val, []) per entry): exit=1. rfl fails on `(x.1.val, []) ≠ (kv.1.val, map .val kv.2)`.
- atk_3 (partial-domain: return Except.error on empty input, else gold): exit=1. gold proof cannot discharge the `if m.isEmpty` branch.
- atk_4 (boundary: deserialize reverses each member list, kv.2.reverse): exit=1. rfl fails: map over reverse ≠ map.
- atk_5 (control-flow-effect: serialize prepends `[e] ++ acc`, reversing outer order): exit=1. rfl fails on the forIn residual.
- atk_6 (ungrounded-oracle echo: serialize := return Except.ok (toStrong m); deserialize := return toWeak s): exit=0 CLOSES. `#print axioms correct_serialize/correct_deserialize` => "does not depend on any axioms" (clean, no sorryAx). Positive control also verifies (exit=0).
- atk_7 (key-corruption: deserialize wraps key as constant Ref.mk 0): exit=1. rfl fails: `{val:=0} ≠ {val:=kv.1}`.

MANDATORY RESOLVE for the only closing impl (atk_6): atk_6 literally computes toStrong/toWeak, so it is EXTENSIONALLY IDENTICAL to gold on every input; its faithful refined patch IS the gold patch (materialized at atk_6.patch). Ran through the official harness via swebench_unified.harness.run_resolve (docker, SWE-bench_Verified, --run_id sbu-audit-atk6-dbg-25332, timeout 1800). Report at experiments/logs/run_evaluation/sbu-audit-atk6-dbg-25332/.../report.json => resolved=TRUE; FAIL_TO_PASS success=[test_pickle.py::test_complete[png]], failure=[]. So the one verifying impl RESOLVES => verify⇒correct, NOT a break. (Two prior harness invocations returned completed=False 'no report' because the eval image had not yet been built locally; after ensure_image built it, the run completed with resolved=true.)

REFINEMENT.MD AUDIT: 11 legs, all tagged R or I; NO A-consumed and NO A-reference; no kind-3 leg. This is legitimate: weakref.ref deref (r()) / construction (weakref.ref(x)) are deep-modeled as the Ref structure (Ref.val / Ref.mk), not axiomatized repo callees => meta.json axioms=[], deep_model_references=[], axiom_check.py is a skip stub (G-AX skip), consistent with mapping.md. Model↔patch correspondence holds: verified via patch.diff context + a sibling matplotlib checkout that Grouper.__init__ sets ONLY self._mapping, so {**vars(self), "_mapping": ...} reduces exactly to the deref'd mapping (toStrong) and vars(self).update(state) + rebuild reduces to rewrap (toWeak). success↔Except.ok; pre-patch default pickling of weakref.ref objects raises TypeError↔Except.error (the real FAIL_TO_PASS bug). No kind-3 / ungrounded leg found.

CONCLUSION: The equality-pinned spec admits no divergent-yet-conforming impl. The only same-spec impl whose correct_* closes with clean axioms (atk_6) is behaviorally identical to gold and its faithful patch RESOLVES under the official harness (executed, resolved=true). ≥5 distinct attacks run (7 total, incl. prepatch + the required echo/oracle attack); none breaks the spec. VERDICT: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Serializing a reference-backed grouping container so it round-trips.

A grouping container records a partition of objects into disjoint sets. To allow
the grouped objects to be garbage-collected, the container does not hold the
objects directly; it holds *references* to them. The partition is stored as a
table mapping each member's reference to the list of references that make up its
group.

References of this kind are an in-memory bookkeeping device: they cannot be
turned into a self-contained, transferable value, so a naive attempt to
serialize a container that holds them does not produce a value at all — it fails.

The desired behavior, modeled here, is twofold:

  * `serialize` — producing the transferable form of the container. It must
    SUCCEED (rather than fail), and the value it produces must record, for every
    entry of the table, the referent of the key together with the referents of
    each member of its group — i.e. the partition with every reference replaced
    by the object it points at.

  * `deserialize` — reconstructing the container from a transferable form. It
    rebuilds the table by replacing every recorded referent (key and members
    alike) with a fresh reference to it, so the original partition is restored.

Taken together these pin the round-trip: serializing then deserializing yields
the same partition the container started with.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. A reference and
-- the act of following it / creating it are modeled directly as the `Ref`
-- structure below (its identity token `val`, `Ref.mk`), not as an axiomatized
-- repo callee. Hence no `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- A reference to a grouped object, modeled by the object's identity token.
Following the reference is `Ref.val`; creating one is `Ref.mk`. Two references
are equal exactly when they point at the same object. -/
structure Ref where
  val : Int
deriving DecidableEq, Repr

/-- The transferable form of the partition table: for each entry, the referent
of the key paired with the referents of its group's members. (Every reference is
replaced by the object it points at.) -/
def toStrong (m : List (Ref × List Ref)) : List (Int × List Int) :=
  m.map (fun kv => (kv.1.val, kv.2.map (fun r => r.val)))

/-- Reconstructing the partition table from its transferable form: every recorded
referent (key and members alike) is wrapped in a fresh reference to it. -/
def toWeak (s : List (Int × List Int)) : List (Ref × List Ref) :=
  s.map (fun kv => (Ref.mk kv.1, kv.2.map (fun n => Ref.mk n)))
-- pure-end

-- post-conditions-start
/-- Serialization succeeds and produces exactly the transferable form of the
partition table: an `ok` value whose content records, for every entry, the
referent of the key together with the referents of each member of its group.
The whole result is pinned to the input table, so no component is left free. -/
def problem_spec_serialize (m : List (Ref × List Ref))
    (result : Except String (List (Int × List Int))) : Prop :=
  result = Except.ok (toStrong m)
-- post-conditions-end

-- impl-start
def implementation_serialize (m : List (Ref × List Ref)) :
    Except String (List (Int × List Int)) := Id.run do
  let mut acc : List (Int × List Int) := []
  for kv in m do
    let key := kv.1
    let members := kv.2
    let mut derefMembers : List Int := []
    for v in members do
      derefMembers := derefMembers ++ [v.val]
    acc := acc ++ [(key.val, derefMembers)]
  return Except.ok acc
-- impl-end

-- proof-start
/-- `forIn` over a list, where the body yields the accumulator with `f x`
appended, computes `init ++ xs.map f`. The workhorse for both round-trip loops
(inner and outer), generalized over the accumulator. -/
theorem forIn_app_pure {α β : Type} (xs : List α) (init : List β) (f : α → β) :
    (forIn xs init (fun x r => pure (ForInStep.yield (r ++ [f x]))) : Id (List β))
    = pure (init ++ xs.map f) := by
  induction xs generalizing init with
  | nil => simp
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [bind, ih]
    simp [List.append_assoc]

theorem correct_serialize :
    ∀ (m : List (Ref × List Ref)),
      problem_spec_serialize m (implementation_serialize m) := by
  intro m
  unfold problem_spec_serialize implementation_serialize toStrong
  simp only [Id.run, bind, forIn_app_pure, List.nil_append]
  rfl
-- proof-end

-- post-conditions-start
/-- Deserialization reconstructs the partition table from its transferable form:
every recorded referent (key and members alike) is wrapped in a fresh reference
to it. The whole result is pinned to the input, so no component is left free. -/
def problem_spec_deserialize (s : List (Int × List Int))
    (result : List (Ref × List Ref)) : Prop :=
  result = toWeak s
-- post-conditions-end

-- impl-start
def implementation_deserialize (s : List (Int × List Int)) :
    List (Ref × List Ref) := Id.run do
  let mut acc : List (Ref × List Ref) := []
  for kv in s do
    let members := kv.2
    let mut wrapMembers : List Ref := []
    for v in members do
      wrapMembers := wrapMembers ++ [Ref.mk v]
    acc := acc ++ [(Ref.mk kv.1, wrapMembers)]
  return acc
-- impl-end

-- proof-start
theorem correct_deserialize :
    ∀ (s : List (Int × List Int)),
      problem_spec_deserialize s (implementation_deserialize s) := by
  intro s
  unfold problem_spec_deserialize implementation_deserialize toWeak
  simp only [Id.run, bind, forIn_app_pure, List.nil_append]
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: fully equality-pinned. problem_spec_serialize m result := result = Except.ok (toStrong m); problem_spec_deserialize s result := result = toWeak s, where toStrong/toWeak are total deterministic functions of the input. Any closing correct_* impl must be propositionally equal to Except.ok(toStrong m) / toWeak s on EVERY input => zero observable freedom.

SAME-SPEC: swebench_unified.markers.same_spec == True for all 7 attacks + positive control (axioms/pure/pre/post byte-identical; only impl+proof regions edited).

### ATTACKS (all verified via `bash scripts/lean_verify.sh <f>`):
- atk_1 (prepatch bug: serialize returns Except.error): exit=1. rfl fails: `pure (Except.error ...) ≠ Except.ok (toStrong m)`. PREPATCH REPRODUCED.
- atk_2 (drop-all-members: emit (key.val, []) per entry): exit=1. rfl fails on `(x.1.val, []) ≠ (kv.1.val, map .val kv.2)`.
- atk_3 (partial-domain: return Except.error on empty input, else gold): exit=1. gold proof cannot discharge the `if m.isEmpty` branch.
- atk_4 (boundary: deserialize reverses each member list, kv.2.reverse): exit=1. rfl fails: map over reverse ≠ map.
- atk_5 (control-flow-effect: serialize prepends `[e] ++ acc`, reversing outer order): exit=1. rfl fails on the forIn residual.
- atk_6 (ungrounded-oracle echo: serialize := return Except.ok (toStrong m); deserialize := return toWeak s): exit=0 CLOSES. `#print axioms correct_serialize/correct_deserialize` => "does not depend on any axioms" (clean, no sorryAx). Positive control also verifies (exit=0).
- atk_7 (key-corruption: deserialize wraps key as constant Ref.mk 0): exit=1. rfl fails: `{val:=0} ≠ {val:=kv.1}`.

MANDATORY RESOLVE for the only closing impl (atk_6): atk_6 literally computes toStrong/toWeak, so it is EXTENSIONALLY IDENTICAL to gold on every input; its faithful refined patch IS the gold patch (materialized at atk_6.patch). Ran through the official harness via swebench_unified.harness.run_resolve (docker, SWE-bench_Verified, --run_id sbu-audit-atk6-dbg-25332, timeout 1800). Report at experiments/logs/run_evaluation/sbu-audit-atk6-dbg-25332/.../report.json => resolved=TRUE; FAIL_TO_PASS success=[test_pickle.py::test_complete[png]], failure=[]. So the one verifying impl RESOLVES => verify⇒correct, NOT a break. (Two prior harness invocations returned completed=False 'no report' because the eval image had not yet been built locally; after ensure_image built it, the run completed with resolved=true.)

REFINEMENT.MD AUDIT: 11 legs, all tagged R or I; NO A-consumed and NO A-reference; no kind-3 leg. This is legitimate: weakref.ref deref (r()) / construction (weakref.ref(x)) are deep-modeled as the Ref structure (Ref.val / Ref.mk), not axiomatized repo callees => meta.json axioms=[], deep_model_references=[], axiom_check.py is a skip stub (G-AX skip), consistent with mapping.md. Model↔patch correspondence holds: verified via patch.diff context + a sibling matplotlib checkout that Grouper.__init__ sets ONLY self._mapping, so {**vars(self), "_mapping": ...} reduces exactly to the deref'd mapping (toStrong) and vars(self).update(state) + rebuild reduces to rewrap (toWeak). success↔Except.ok; pre-patch default pickling of weakref.ref objects raises TypeError↔Except.error (the real FAIL_TO_PASS bug). No kind-3 / ungrounded leg found.

CONCLUSION: The equality-pinned spec admits no divergent-yet-conforming impl. The only same-spec impl whose correct_* closes with clean axioms (atk_6) is behaviorally identical to gold and its faithful patch RESOLVES under the official harness (executed, resolved=true). ≥5 distinct attacks run (7 total, incl. prepatch + the required echo/oracle attack); none breaks the spec. VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack failed; model matches the real Grouper.__getstate__/__setstate__ (cbook.py @ base 66ba515). Mechanical: lean_verify exit 0, #print axioms = [propext, Quot.sound] only (no sorryAx, genuine proof), same_spec(Solution,prepatch)=True, conformance_check.py re-run = checked=120007 disagreements=0 status=pass. Verified from real git source: Grouper.__init__ sets ONLY self._mapping, so {**vars(self),'_mapping':...} reduces exactly to the deref'd mapping => serialize == toStrong m (always Except.ok, never raises on a live graph); __setstate__ rewrap == toWeak s. Prepatch (no __getstate__) => default pickling raises TypeError on weakref => Except.error, faithful to the real bug/FAIL_TO_PASS. Probed the three candidate divergences and none is reachable: (1) DEAD REFS — __getstate__ does not call clean(), so a dead weakref would yield None, but Ref{val:Int} cannot represent a dead ref; every Ref derefs. Domain is explicitly scoped to a live object graph, which is the real serialization context; no representable divergence. (2) LIST-IDENTITY SHARING — real _mapping shares one group list across sibling keys and joined() reads by 'is'; both the real comprehensions and the model rebuild fresh independent lists, so identity is dropped either way but member-token CONTENT is preserved identically. joined/list-identity is outside the modeled surface (documented in mapping.md) and the modeled observable (partition content) agrees. (3) DUPLICATE KEYS — unreachable: a real dict _mapping has unique keys and the fuzzer's rng.sample respects distinctness; out of the callee's domain. No input in the real callee's domain (live graph, distinct-key dict) makes serialize/deserialize disagree with __getstate__/__setstate__. Spec is equality-pinned but faithful, not too strong within the real domain.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Lexical screen over the spec view (Solution.lean docstring + problem_spec_serialize/deserialize + toStrong/toWeak): zero occurrences of any patched symbol (__getstate__, __setstate__, Grouper, _mapping, cbook, weakref, pickle, vars(, __dict__, align, matplotlib). Spec regions are byte-identical to Solution_prepatch.lean (diff touches only impl/proof), so the spec view is stable. Public problem_statement already reveals the core: pickling fails because weakrefs are unpicklable (TypeError: cannot pickle 'weakref.ReferenceType' object) after align_labels(), and the goal is successful pickling. The spec's behavioral content — serialize must succeed and record referents (deref), deserialize rewraps to fresh references to round-trip — is the unavoidable, essentially canonical content of any behavioral spec of a fix the public traceback already points at; it does not exceed the public statement. Modeled function names serialize/deserialize are neutral behavioral names, not substrings of the patched method/class names. Borderline descriptive tokens 'grouping container'/'partition into disjoint sets'/'garbage-collected' (lines 5-11) are generic framing of the abstract container, not identifiers, and do not reveal the edit locus (added serialization hooks in cbook.py's Grouper) or the patched method names. A solver cannot recover the class/method/file from the spec view. Within bounds -> NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
