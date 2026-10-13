# P2 adversarial audit — django__django-13343

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `positive.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -88,8 +88,7 @@
   | .useDefault => pure ()
   | .inst s => storage := s
   | .callable c =>
-      -- callable branch: retain the original callable, then evaluate it
-      storageCallable := some c
+      -- ATTACK 1 (partial/effect drop): evaluate the callable but DO NOT retain it
       storage := c.result
   return { storage := storage, storageCallable := storageCallable }
 -- impl-end
@@ -101,7 +100,11 @@
         (implementation_initStorage defaultStorage arg) := by
   intro defaultStorage arg
   cases arg <;>
-    exact ⟨rfl, rfl⟩
+    first
+      | exact ⟨rfl, rfl⟩
+      | (constructor <;> rfl)
+      | simp_all [implementation_initStorage, problem_spec_initStorage]
+      | decide
 -- proof-end
 
 -- post-conditions-start
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -123,10 +123,9 @@
     (state : FieldState) : Option DeconstructStorage := Id.run do
   let mut result : Option DeconstructStorage := none
   if state.storage ≠ defaultStorage then
-    -- getattr(self, retained-callable, resolved-instance)
-    result := some (match state.storageCallable with
-                    | some c => .callable c
-                    | none   => .inst state.storage)
+    -- ATTACK 2 (control-flow/effect drop): always echo the resolved instance,
+    -- ignoring any retained callable.
+    result := some (.inst state.storage)
   return result
 -- impl-end
 
@@ -143,5 +142,7 @@
     rfl
   · rw [if_neg h]
     simp only [Id.run, ne_eq, h, not_false_iff, if_true]
-    rfl
+    first
+      | rfl
+      | simp_all [implementation_deconstructStorage, problem_spec_deconstructStorage]
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -86,9 +86,11 @@
   let mut storageCallable : Option Callable := none
   match arg with
   | .useDefault => pure ()
-  | .inst s => storage := s
+  | .inst s =>
+      -- ATTACK 3 (boundary): a direct instance spuriously retains a callable.
+      storage := s
+      storageCallable := some { id := 0, result := s }
   | .callable c =>
-      -- callable branch: retain the original callable, then evaluate it
       storageCallable := some c
       storage := c.result
   return { storage := storage, storageCallable := storageCallable }
@@ -101,7 +103,11 @@
         (implementation_initStorage defaultStorage arg) := by
   intro defaultStorage arg
   cases arg <;>
-    exact ⟨rfl, rfl⟩
+    first
+      | exact ⟨rfl, rfl⟩
+      | (constructor <;> rfl)
+      | simp_all [implementation_initStorage, problem_spec_initStorage]
+      | decide
 -- proof-end
 
 -- post-conditions-start
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -122,11 +122,12 @@
 def implementation_deconstructStorage (defaultStorage : StorageInst)
     (state : FieldState) : Option DeconstructStorage := Id.run do
   let mut result : Option DeconstructStorage := none
+  -- ATTACK 4 (partial-domain): only emit a value when NO callable is retained;
+  -- when a callable exists, leave the key absent (`none`).
   if state.storage ≠ defaultStorage then
-    -- getattr(self, retained-callable, resolved-instance)
-    result := some (match state.storageCallable with
-                    | some c => .callable c
-                    | none   => .inst state.storage)
+    match state.storageCallable with
+    | some _ => pure ()
+    | none   => result := some (.inst state.storage)
   return result
 -- impl-end
 
@@ -139,9 +140,7 @@
   unfold problem_spec_deconstructStorage implementation_deconstructStorage
   by_cases h : state.storage = defaultStorage
   · rw [if_pos h]
-    simp only [Id.run, ne_eq, h, not_true, if_false]
-    rfl
+    simp_all [implementation_deconstructStorage, problem_spec_deconstructStorage, Id.run]
   · rw [if_neg h]
-    simp only [Id.run, ne_eq, h, not_false_iff, if_true]
-    rfl
+    simp_all [implementation_deconstructStorage, problem_spec_deconstructStorage, Id.run]
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -88,9 +88,10 @@
   | .useDefault => pure ()
   | .inst s => storage := s
   | .callable c =>
-      -- callable branch: retain the original callable, then evaluate it
+      -- ATTACK 5 (ungrounded-oracle echo): retain the callable but resolve the
+      -- runtime storage to the DEFAULT rather than the produced instance.
       storageCallable := some c
-      storage := c.result
+      storage := defaultStorage
   return { storage := storage, storageCallable := storageCallable }
 -- impl-end
 
@@ -101,7 +102,11 @@
         (implementation_initStorage defaultStorage arg) := by
   intro defaultStorage arg
   cases arg <;>
-    exact ⟨rfl, rfl⟩
+    first
+      | exact ⟨rfl, rfl⟩
+      | (constructor <;> rfl)
+      | simp_all [implementation_initStorage, problem_spec_initStorage]
+      | decide
 -- proof-end
 
 -- post-conditions-start
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -122,8 +122,9 @@
 def implementation_deconstructStorage (defaultStorage : StorageInst)
     (state : FieldState) : Option DeconstructStorage := Id.run do
   let mut result : Option DeconstructStorage := none
-  if state.storage ≠ defaultStorage then
-    -- getattr(self, retained-callable, resolved-instance)
+  -- ATTACK 6 (boundary/guard inversion): emit the value exactly when the
+  -- storage IS the default (inverting the omission condition).
+  if state.storage = defaultStorage then
     result := some (match state.storageCallable with
                     | some c => .callable c
                     | none   => .inst state.storage)
@@ -139,9 +140,7 @@
   unfold problem_spec_deconstructStorage implementation_deconstructStorage
   by_cases h : state.storage = defaultStorage
   · rw [if_pos h]
-    simp only [Id.run, ne_eq, h, not_true, if_false]
-    rfl
+    simp_all [implementation_deconstructStorage, problem_spec_deconstructStorage, Id.run]
   · rw [if_neg h]
-    simp only [Id.run, ne_eq, h, not_false_iff, if_true]
-    rfl
+    simp_all [implementation_deconstructStorage, problem_spec_deconstructStorage, Id.run]
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive.lean`

```lean
import Mathlib
-- imports-end

/-!
Two related behaviors for a file field whose storage backend may be supplied
either directly as a storage instance or as a callable that produces one.

* When the field is constructed, the storage argument is resolved to a concrete
  storage instance. If the argument is itself a callable, the resolution both
  evaluates the callable to obtain the runtime instance AND retains the original
  callable as a separate piece of the field's state. A direct instance (or an
  absent argument falling back to the project default) leaves no retained
  callable.

* When the field is serialized back into its construction arguments, the value
  recorded under the `storage` key is the original callable whenever one was
  retained, and otherwise the resolved instance. The key is omitted entirely
  when the resolved storage is the project default.

The net effect is that a callable storage argument survives a construct →
serialize round-trip as the very same callable object, so the storage backend
can still be chosen at runtime. These are stated abstractly as input→output
relations; the implementation and correctness proof for each are supplied
separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract: both modeled behaviors are
-- spelled out with concrete operations (a three-way case on the argument shape;
-- an identity comparison with an optional retained value).
-- axioms-end

-- pure-start
/-- Identity token for a storage instance (object identity in the real world). -/
abbrev StorageInst := Nat

/-- A callable storage argument: its own object identity together with the
storage instance it produces when evaluated. -/
structure Callable where
  id : Nat
  result : StorageInst
deriving DecidableEq, Repr

/-- The storage argument a field may be constructed with. -/
inductive StorageArg where
  /-- absent / falsy — falls back to the project default. -/
  | useDefault : StorageArg
  /-- a concrete storage instance. -/
  | inst : StorageInst → StorageArg
  /-- a callable producing a storage instance. -/
  | callable : Callable → StorageArg
deriving DecidableEq, Repr

/-- The field state established at construction time that serialization reads:
the resolved runtime storage instance and, optionally, a retained callable. -/
structure FieldState where
  storage : StorageInst
  storageCallable : Option Callable
deriving DecidableEq, Repr

/-- The value serialized under the `storage` key. -/
inductive DeconstructStorage where
  | inst : StorageInst → DeconstructStorage
  | callable : Callable → DeconstructStorage
deriving DecidableEq, Repr
-- pure-end

-- post-conditions-start
/-- Resolving the storage argument: an absent argument resolves to the default
and retains no callable; a direct instance resolves to itself and retains no
callable; a callable resolves to the instance it produces AND retains the
original callable. -/
def problem_spec_initStorage (defaultStorage : StorageInst) (arg : StorageArg)
    (result : FieldState) : Prop :=
  match arg with
  | .useDefault  => result.storage = defaultStorage ∧ result.storageCallable = none
  | .inst s      => result.storage = s ∧ result.storageCallable = none
  | .callable c  => result.storage = c.result ∧ result.storageCallable = some c
-- post-conditions-end

-- impl-start
def implementation_initStorage (defaultStorage : StorageInst) (arg : StorageArg) :
    FieldState := Id.run do
  -- self.storage = storage or default_storage
  let mut storage : StorageInst := defaultStorage
  let mut storageCallable : Option Callable := none
  match arg with
  | .useDefault => pure ()
  | .inst s => storage := s
  | .callable c =>
      -- callable branch: retain the original callable, then evaluate it
      storageCallable := some c
      storage := c.result
  return { storage := storage, storageCallable := storageCallable }
-- impl-end

-- proof-start
theorem correct_initStorage :
    ∀ (defaultStorage : StorageInst) (arg : StorageArg),
      problem_spec_initStorage defaultStorage arg
        (implementation_initStorage defaultStorage arg) := by
  intro defaultStorage arg
  cases arg <;>
    exact ⟨rfl, rfl⟩
-- proof-end

-- post-conditions-start
/-- Serializing the storage argument: the `storage` key is omitted when the
resolved storage is the project default; otherwise it carries the retained
callable if one exists, and the resolved instance if not. -/
def problem_spec_deconstructStorage (defaultStorage : StorageInst)
    (state : FieldState) (result : Option DeconstructStorage) : Prop :=
  if state.storage = defaultStorage then
    result = none
  else
    result = some (match state.storageCallable with
                   | some c => .callable c
                   | none   => .inst state.storage)
-- post-conditions-end

-- impl-start
def implementation_deconstructStorage (defaultStorage : StorageInst)
    (state : FieldState) : Option DeconstructStorage := Id.run do
  let mut result : Option DeconstructStorage := none
  if state.storage ≠ defaultStorage then
    -- getattr(self, retained-callable, resolved-instance)
    result := some (match state.storageCallable with
                    | some c => .callable c
                    | none   => .inst state.storage)
  return result
-- impl-end

-- proof-start
theorem correct_deconstructStorage :
    ∀ (defaultStorage : StorageInst) (state : FieldState),
      problem_spec_deconstructStorage defaultStorage state
        (implementation_deconstructStorage defaultStorage state) := by
  intro defaultStorage state
  unfold problem_spec_deconstructStorage implementation_deconstructStorage
  by_cases h : state.storage = defaultStorage
  · rw [if_pos h]
    simp only [Id.run, ne_eq, h, not_true, if_false]
    rfl
  · rw [if_neg h]
    simp only [Id.run, ne_eq, h, not_false_iff, if_true]
    rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit of django__django-13343 (lean), two modeled triples: initStorage and deconstructStorage.

SAME-SPEC: all 6 attacks + positive control confirmed same_spec=True vs Solution.lean via swebench_unified.markers.same_spec (impl regions only edited; axioms/pure/pre/post byte-identical).

ATTACKS (each: cp Solution.lean, edit ONLY impl region, best-effort proof with `first | ... | simp_all | decide`; cmd: `bash scripts/lean_verify.sh <path>`; ran concurrently ≤4 background jobs):
- atk_1 (initStorage, effect-drop): callable branch evaluates c.result but drops the retained callable (prepatch_1 shape) → exit 1 (goal `⊢ False`, some c vs none).
- atk_2 (deconstruct, control-flow drop): always echo `.inst state.storage`, ignore retained callable (prepatch_2 shape) → exit 1.
- atk_3 (initStorage, boundary): `.inst s` spuriously retains `some {id:=0,result:=s}` → exit 1 (goal `⊢ False`).
- atk_4 (deconstruct, partial-domain): emit value only when NO callable retained; leave key absent when `some c` → exit 1.
- atk_5 (initStorage, ungrounded-oracle echo): callable retains c but resolves storage:=defaultStorage instead of c.result → exit 1 (goal `⊢ defaultStorage = a.result`).
- atk_6 (deconstruct, guard inversion): emit value when storage = defaultStorage (inverted omission) → exit 1.

RESULT: ALL 6 attacks fail to verify (exit 1). No same-spec wrong impl closes with clean axioms, so there is NOTHING to materialize into a faithful patch — the verify⇒correct obligation is vacuously satisfied; `patches` is empty by construction (no closing wrong impl). This is the correct outcome for a total functional spec.

WHY SOUND (mechanized): both problem_spec_* are total functional relations. problem_spec_initStorage pins BOTH FieldState fields for every StorageArg constructor; problem_spec_deconstructStorage pins the full Option DeconstructStorage for every (storage, storageCallable). Any impl whose correct_* closes must produce exactly the gold output on every input — no observable behavioral freedom. (verdict.md records Lean functional-uniqueness lemmas initStorage_functional / deconstruct_functional that compile; consistent with all 6 attacks failing.)

POSITIVE CONTROL: positive.lean (gold impl) → exit 0. #print axioms: `correct_initStorage` does not depend on any axioms; `correct_deconstructStorage` depends on [propext, Quot.sound] only (no sorryAx) — clean.

PREPATCH: Solution_prepatch_1.lean → exit 1 (callable case storageCallable=none vs some c); Solution_prepatch_2.lean → exit 1 (result .inst vs .callable c). Both bugs genuinely reproduced.

REFINEMENT.MD AUDIT: axioms region EMPTY (byte-identical in all files); refinement.md declares/consumes NO axioms — every leg is R (type refinement) or I (identical concrete op), no A-consumed, no A-reference, no kind-3. Since there are no A-legs, there is no deep-model↔real-callee correspondence to fail; the R/I legs are covered by G-CONF (conformance_check.py present, seed 20240613, ≥1e5 draws, exercises callable-returns-default corner). No axiom soundness concern.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `positive.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive.lean`

```lean
import Mathlib
-- imports-end

/-!
Two related behaviors for a file field whose storage backend may be supplied
either directly as a storage instance or as a callable that produces one.

* When the field is constructed, the storage argument is resolved to a concrete
  storage instance. If the argument is itself a callable, the resolution both
  evaluates the callable to obtain the runtime instance AND retains the original
  callable as a separate piece of the field's state. A direct instance (or an
  absent argument falling back to the project default) leaves no retained
  callable.

* When the field is serialized back into its construction arguments, the value
  recorded under the `storage` key is the original callable whenever one was
  retained, and otherwise the resolved instance. The key is omitted entirely
  when the resolved storage is the project default.

The net effect is that a callable storage argument survives a construct →
serialize round-trip as the very same callable object, so the storage backend
can still be chosen at runtime. These are stated abstractly as input→output
relations; the implementation and correctness proof for each are supplied
separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract: both modeled behaviors are
-- spelled out with concrete operations (a three-way case on the argument shape;
-- an identity comparison with an optional retained value).
-- axioms-end

-- pure-start
/-- Identity token for a storage instance (object identity in the real world). -/
abbrev StorageInst := Nat

/-- A callable storage argument: its own object identity together with the
storage instance it produces when evaluated. -/
structure Callable where
  id : Nat
  result : StorageInst
deriving DecidableEq, Repr

/-- The storage argument a field may be constructed with. -/
inductive StorageArg where
  /-- absent / falsy — falls back to the project default. -/
  | useDefault : StorageArg
  /-- a concrete storage instance. -/
  | inst : StorageInst → StorageArg
  /-- a callable producing a storage instance. -/
  | callable : Callable → StorageArg
deriving DecidableEq, Repr

/-- The field state established at construction time that serialization reads:
the resolved runtime storage instance and, optionally, a retained callable. -/
structure FieldState where
  storage : StorageInst
  storageCallable : Option Callable
deriving DecidableEq, Repr

/-- The value serialized under the `storage` key. -/
inductive DeconstructStorage where
  | inst : StorageInst → DeconstructStorage
  | callable : Callable → DeconstructStorage
deriving DecidableEq, Repr
-- pure-end

-- post-conditions-start
/-- Resolving the storage argument: an absent argument resolves to the default
and retains no callable; a direct instance resolves to itself and retains no
callable; a callable resolves to the instance it produces AND retains the
original callable. -/
def problem_spec_initStorage (defaultStorage : StorageInst) (arg : StorageArg)
    (result : FieldState) : Prop :=
  match arg with
  | .useDefault  => result.storage = defaultStorage ∧ result.storageCallable = none
  | .inst s      => result.storage = s ∧ result.storageCallable = none
  | .callable c  => result.storage = c.result ∧ result.storageCallable = some c
-- post-conditions-end

-- impl-start
def implementation_initStorage (defaultStorage : StorageInst) (arg : StorageArg) :
    FieldState := Id.run do
  -- self.storage = storage or default_storage
  let mut storage : StorageInst := defaultStorage
  let mut storageCallable : Option Callable := none
  match arg with
  | .useDefault => pure ()
  | .inst s => storage := s
  | .callable c =>
      -- callable branch: retain the original callable, then evaluate it
      storageCallable := some c
      storage := c.result
  return { storage := storage, storageCallable := storageCallable }
-- impl-end

-- proof-start
theorem correct_initStorage :
    ∀ (defaultStorage : StorageInst) (arg : StorageArg),
      problem_spec_initStorage defaultStorage arg
        (implementation_initStorage defaultStorage arg) := by
  intro defaultStorage arg
  cases arg <;>
    exact ⟨rfl, rfl⟩
-- proof-end

-- post-conditions-start
/-- Serializing the storage argument: the `storage` key is omitted when the
resolved storage is the project default; otherwise it carries the retained
callable if one exists, and the resolved instance if not. -/
def problem_spec_deconstructStorage (defaultStorage : StorageInst)
    (state : FieldState) (result : Option DeconstructStorage) : Prop :=
  if state.storage = defaultStorage then
    result = none
  else
    result = some (match state.storageCallable with
                   | some c => .callable c
                   | none   => .inst state.storage)
-- post-conditions-end

-- impl-start
def implementation_deconstructStorage (defaultStorage : StorageInst)
    (state : FieldState) : Option DeconstructStorage := Id.run do
  let mut result : Option DeconstructStorage := none
  if state.storage ≠ defaultStorage then
    -- getattr(self, retained-callable, resolved-instance)
    result := some (match state.storageCallable with
                    | some c => .callable c
                    | none   => .inst state.storage)
  return result
-- impl-end

-- proof-start
theorem correct_deconstructStorage :
    ∀ (defaultStorage : StorageInst) (state : FieldState),
      problem_spec_deconstructStorage defaultStorage state
        (implementation_deconstructStorage defaultStorage state) := by
  intro defaultStorage state
  unfold problem_spec_deconstructStorage implementation_deconstructStorage
  by_cases h : state.storage = defaultStorage
  · rw [if_pos h]
    simp only [Id.run, ne_eq, h, not_true, if_false]
    rfl
  · rw [if_neg h]
    simp only [Id.run, ne_eq, h, not_false_iff, if_true]
    rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit of django__django-13343 (lean), two modeled triples: initStorage and deconstructStorage.

SAME-SPEC: all 6 attacks + positive control confirmed same_spec=True vs Solution.lean via swebench_unified.markers.same_spec (impl regions only edited; axioms/pure/pre/post byte-identical).

ATTACKS (each: cp Solution.lean, edit ONLY impl region, best-effort proof with `first | ... | simp_all | decide`; cmd: `bash scripts/lean_verify.sh <path>`; ran concurrently ≤4 background jobs):
- atk_1 (initStorage, effect-drop): callable branch evaluates c.result but drops the retained callable (prepatch_1 shape) → exit 1 (goal `⊢ False`, some c vs none).
- atk_2 (deconstruct, control-flow drop): always echo `.inst state.storage`, ignore retained callable (prepatch_2 shape) → exit 1.
- atk_3 (initStorage, boundary): `.inst s` spuriously retains `some {id:=0,result:=s}` → exit 1 (goal `⊢ False`).
- atk_4 (deconstruct, partial-domain): emit value only when NO callable retained; leave key absent when `some c` → exit 1.
- atk_5 (initStorage, ungrounded-oracle echo): callable retains c but resolves storage:=defaultStorage instead of c.result → exit 1 (goal `⊢ defaultStorage = a.result`).
- atk_6 (deconstruct, guard inversion): emit value when storage = defaultStorage (inverted omission) → exit 1.

RESULT: ALL 6 attacks fail to verify (exit 1). No same-spec wrong impl closes with clean axioms, so there is NOTHING to materialize into a faithful patch — the verify⇒correct obligation is vacuously satisfied; `patches` is empty by construction (no closing wrong impl). This is the correct outcome for a total functional spec.

WHY SOUND (mechanized): both problem_spec_* are total functional relations. problem_spec_initStorage pins BOTH FieldState fields for every StorageArg constructor; problem_spec_deconstructStorage pins the full Option DeconstructStorage for every (storage, storageCallable). Any impl whose correct_* closes must produce exactly the gold output on every input — no observable behavioral freedom. (verdict.md records Lean functional-uniqueness lemmas initStorage_functional / deconstruct_functional that compile; consistent with all 6 attacks failing.)

POSITIVE CONTROL: positive.lean (gold impl) → exit 0. #print axioms: `correct_initStorage` does not depend on any axioms; `correct_deconstructStorage` depends on [propext, Quot.sound] only (no sorryAx) — clean.

PREPATCH: Solution_prepatch_1.lean → exit 1 (callable case storageCallable=none vs some c); Solution_prepatch_2.lean → exit 1 (result .inst vs .callable c). Both bugs genuinely reproduced.

REFINEMENT.MD AUDIT: axioms region EMPTY (byte-identical in all files); refinement.md declares/consumes NO axioms — every leg is R (type refinement) or I (identical concrete op), no A-consumed, no A-reference, no kind-3. Since there are no A-legs, there is no deep-model↔real-callee correspondence to fail; the R/I legs are covered by G-CONF (conformance_check.py present, seed 20240613, ≥1e5 draws, exercises callable-returns-default corner). No axiom soundness concern.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-vs-real-callee drift) audit for django__django-13343, lean backend. Two modeled triples: initStorage (FileField.__init__ storage resolution) and deconstructStorage (FileField.deconstruct storage kwarg).

### PREFLIGHT (all clean):
- lean_verify.sh Solution.lean: exit 0 (compiles, no sorry).
- #print axioms correct_initStorage -> does not depend on any axioms. correct_deconstructStorage -> [propext, Quot.sound] only. No sorryAx; proofs are real.
- same_spec(Solution, prepatch_1)=True and same_spec(Solution, prepatch_2)=True (spec regions byte-identical / frozen).
- Real source at base_commit ece18207 inspected: __init__ and deconstruct match the gold patch verbatim (self._storage_callable = self.storage; getattr(self,'_storage_callable',self.storage)).

### FAITHFULNESS CHECK (modeled fn vs real callee, per input):
initStorage bijection matches on every constructor:
  .useDefault -> {storage=defaultStorage, storageCallable=none}  == `storage or default_storage` falsy arm, branch skipped.
  .inst s     -> {storage=s, storageCallable=none}                == non-callable instance; callable(...) False so no retain.
  .callable c -> {storage=c.result, storageCallable=some c}       == retain original callable then evaluate.
deconstructStorage matches:
  storage=defaultStorage -> none (key omitted)                    == `if self.storage is not default_storage`.
  else some c retained -> .callable c; else .inst storage         == getattr(self,'_storage_callable',self.storage).
The `if state.storage = defaultStorage` is checked FIRST, exactly mirroring the real code's outer identity guard; a state with storageCallable=some c but storage=default correctly yields none (real code omits the key because self.storage IS default). Verified corner case: callable returning default_storage -> _storage_callable set, self.storage becomes default -> key omitted; spec agrees.

EMPIRICAL: Ran conformance_check.py (the composed Python shadow of both impls) against the REAL patched callee: full discrete matrix + 120000 randomized draws = 120010 checks, 0 disagreements, exit 0.

DOMAIN FRAMING (not drift): the isinstance/TypeError guard for a callable returning a non-Storage is UNCHANGED by the patch and modeled as out-of-frame (Callable.result : StorageInst is always a valid instance). This is a legitimate documented success-path narrowing declared in mapping.md/refinement.md, not a spec-vs-callee divergence on any in-frame input.

Verified callable() on real Storage instances returns False (so a plain instance never takes the callable branch), confirming the .inst vs .callable discriminator faithfully mirrors callable(self.storage).

No diverging input found. Spec agrees with the real callee on every modeled input. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (rep.passed=True, zero hard failures) on the rendered lean spec view; spec region byte-identical across Solution.lean and both prepatch candidates (same_spec=True). Manual semantic review confirms no leak beyond the PUBLIC problem_statement: (1) No patched file path (django/db/models/fields/files.py), no patched attribute name (_storage_callable), no gold-diff lines, no diff markers, no getattr call, and no bug/fix narration appear in the spec view — the impl/proof regions (which contain the 'getattr(self, retained-callable, resolved-instance)' comment and the '# self.storage = storage or default_storage' comment) are ELIDED in the projected spec view. (2) The only distinctive changed symbol is 'deconstruct', which is already public in the problem_statement ('does not deconstruct properly'), so the *deconstructStorage identifiers are legitimate. (3) The spec's abstract input->output prose ('return the original callable whenever one was retained', round-trip preserves the same callable) restates the correct behavior that the problem_statement itself dictates verbatim ('The correct behavior should be to return a reference to the original callable during deconstruction'). The spec reveals the intended behavior — which is its purpose and is fully public — not the gold edit's localization or diff-level mechanics. No reliance on hints_text (which is empty here). Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
