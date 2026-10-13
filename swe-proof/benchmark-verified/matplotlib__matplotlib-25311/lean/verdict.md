# P2 adversarial audit — matplotlib__matplotlib-25311

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

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
@@ -50,7 +50,7 @@
   let mut st : List Attr := []
   st := st ++ [Attr.serial]                            -- the dragged object reference
   st := st ++ [Attr.flag false]                        -- "drag in progress" flag
-  st := st ++ [Attr.flag (useBlit && blitSupported)]   -- effective fast-redraw flag
+  st := st ++ [Attr.flag useBlit]   -- effective fast-redraw flag
   st := st ++ [Attr.serial]                            -- connected callback identifiers
   return st
 -- impl-end
@@ -61,12 +61,11 @@
     problem_spec_initHandlerState useBlit blitSupported
       (implementation_initHandlerState useBlit blitSupported) := by
   intro useBlit blitSupported
-  have himpl : implementation_initHandlerState useBlit blitSupported
-      = [Attr.serial, Attr.flag false, Attr.flag (useBlit && blitSupported), Attr.serial] := rfl
-  refine ⟨?_, himpl⟩
-  rw [himpl]
-  intro a ha
-  fin_cases ha <;> simp
+  unfold problem_spec_initHandlerState implementation_initHandlerState stateSerializable
+  refine ⟨?_, ?_⟩ <;>
+    first
+      | (intro a ha; fin_cases ha <;> simp)
+      | (simp) | rfl | decide | (cases useBlit <;> cases blitSupported <;> simp)
 -- proof-end
 
 -- post-conditions-start
@@ -88,5 +87,6 @@
     problem_spec_accessDisplayHandle owner
       (implementation_accessDisplayHandle owner) := by
   intro owner
-  rfl
+  unfold problem_spec_accessDisplayHandle implementation_accessDisplayHandle
+  first | rfl | simp | decide
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -48,10 +48,10 @@
 def implementation_initHandlerState
     (useBlit blitSupported : Bool) : List Attr := Id.run do
   let mut st : List Attr := []
-  st := st ++ [Attr.serial]                            -- the dragged object reference
-  st := st ++ [Attr.flag false]                        -- "drag in progress" flag
-  st := st ++ [Attr.flag (useBlit && blitSupported)]   -- effective fast-redraw flag
-  st := st ++ [Attr.serial]                            -- connected callback identifiers
+  st := st ++ [Attr.flag false]                        -- WRONG: drag flag first
+  st := st ++ [Attr.serial]                            -- dragged object ref second
+  st := st ++ [Attr.flag (useBlit && blitSupported)]
+  st := st ++ [Attr.serial]
   return st
 -- impl-end
 
@@ -61,12 +61,11 @@
     problem_spec_initHandlerState useBlit blitSupported
       (implementation_initHandlerState useBlit blitSupported) := by
   intro useBlit blitSupported
-  have himpl : implementation_initHandlerState useBlit blitSupported
-      = [Attr.serial, Attr.flag false, Attr.flag (useBlit && blitSupported), Attr.serial] := rfl
-  refine ⟨?_, himpl⟩
-  rw [himpl]
-  intro a ha
-  fin_cases ha <;> simp
+  unfold problem_spec_initHandlerState implementation_initHandlerState stateSerializable
+  refine ⟨?_, ?_⟩ <;>
+    first
+      | (intro a ha; fin_cases ha <;> simp)
+      | (simp) | rfl | decide | (cases useBlit <;> cases blitSupported <;> simp)
 -- proof-end
 
 -- post-conditions-start
@@ -88,5 +87,6 @@
     problem_spec_accessDisplayHandle owner
       (implementation_accessDisplayHandle owner) := by
   intro owner
-  rfl
+  unfold problem_spec_accessDisplayHandle implementation_accessDisplayHandle
+  first | rfl | simp | decide
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -48,10 +48,11 @@
 def implementation_initHandlerState
     (useBlit blitSupported : Bool) : List Attr := Id.run do
   let mut st : List Attr := []
-  st := st ++ [Attr.serial]                            -- the dragged object reference
-  st := st ++ [Attr.flag false]                        -- "drag in progress" flag
-  st := st ++ [Attr.flag (useBlit && blitSupported)]   -- effective fast-redraw flag
-  st := st ++ [Attr.serial]                            -- connected callback identifiers
+  st := st ++ [Attr.serial]
+  st := st ++ [Attr.flag false]
+  st := st ++ [Attr.liveHandle]                        -- BUG: stores live canvas handle (prepatch)
+  st := st ++ [Attr.flag (useBlit && blitSupported)]
+  st := st ++ [Attr.serial]
   return st
 -- impl-end
 
@@ -61,12 +62,11 @@
     problem_spec_initHandlerState useBlit blitSupported
       (implementation_initHandlerState useBlit blitSupported) := by
   intro useBlit blitSupported
-  have himpl : implementation_initHandlerState useBlit blitSupported
-      = [Attr.serial, Attr.flag false, Attr.flag (useBlit && blitSupported), Attr.serial] := rfl
-  refine ⟨?_, himpl⟩
-  rw [himpl]
-  intro a ha
-  fin_cases ha <;> simp
+  unfold problem_spec_initHandlerState implementation_initHandlerState stateSerializable
+  refine ⟨?_, ?_⟩ <;>
+    first
+      | (intro a ha; fin_cases ha <;> simp)
+      | (simp) | rfl | decide | (cases useBlit <;> cases blitSupported <;> simp)
 -- proof-end
 
 -- post-conditions-start
@@ -88,5 +88,6 @@
     problem_spec_accessDisplayHandle owner
       (implementation_accessDisplayHandle owner) := by
   intro owner
-  rfl
+  unfold problem_spec_accessDisplayHandle implementation_accessDisplayHandle
+  first | rfl | simp | decide
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -61,12 +61,11 @@
     problem_spec_initHandlerState useBlit blitSupported
       (implementation_initHandlerState useBlit blitSupported) := by
   intro useBlit blitSupported
-  have himpl : implementation_initHandlerState useBlit blitSupported
-      = [Attr.serial, Attr.flag false, Attr.flag (useBlit && blitSupported), Attr.serial] := rfl
-  refine ⟨?_, himpl⟩
-  rw [himpl]
-  intro a ha
-  fin_cases ha <;> simp
+  unfold problem_spec_initHandlerState implementation_initHandlerState stateSerializable
+  refine ⟨?_, ?_⟩ <;>
+    first
+      | (intro a ha; fin_cases ha <;> simp)
+      | (simp) | rfl | decide | (cases useBlit <;> cases blitSupported <;> simp)
 -- proof-end
 
 -- post-conditions-start
@@ -79,7 +78,7 @@
 
 -- impl-start
 def implementation_accessDisplayHandle (owner : Container) : Nat := Id.run do
-  return owner.displayHandle
+  return 0
 -- impl-end
 
 -- proof-start
@@ -88,5 +87,6 @@
     problem_spec_accessDisplayHandle owner
       (implementation_accessDisplayHandle owner) := by
   intro owner
-  rfl
+  unfold problem_spec_accessDisplayHandle implementation_accessDisplayHandle
+  first | rfl | simp | decide
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -49,7 +49,7 @@
     (useBlit blitSupported : Bool) : List Attr := Id.run do
   let mut st : List Attr := []
   st := st ++ [Attr.serial]                            -- the dragged object reference
-  st := st ++ [Attr.flag false]                        -- "drag in progress" flag
+  st := st ++ [Attr.flag true]                         -- WRONG polarity
   st := st ++ [Attr.flag (useBlit && blitSupported)]   -- effective fast-redraw flag
   st := st ++ [Attr.serial]                            -- connected callback identifiers
   return st
@@ -61,12 +61,11 @@
     problem_spec_initHandlerState useBlit blitSupported
       (implementation_initHandlerState useBlit blitSupported) := by
   intro useBlit blitSupported
-  have himpl : implementation_initHandlerState useBlit blitSupported
-      = [Attr.serial, Attr.flag false, Attr.flag (useBlit && blitSupported), Attr.serial] := rfl
-  refine ⟨?_, himpl⟩
-  rw [himpl]
-  intro a ha
-  fin_cases ha <;> simp
+  unfold problem_spec_initHandlerState implementation_initHandlerState stateSerializable
+  refine ⟨?_, ?_⟩ <;>
+    first
+      | (intro a ha; fin_cases ha <;> simp)
+      | (simp) | rfl | decide | (cases useBlit <;> cases blitSupported <;> simp)
 -- proof-end
 
 -- post-conditions-start
@@ -88,5 +87,6 @@
     problem_spec_accessDisplayHandle owner
       (implementation_accessDisplayHandle owner) := by
   intro owner
-  rfl
+  unfold problem_spec_accessDisplayHandle implementation_accessDisplayHandle
+  first | rfl | simp | decide
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -50,7 +50,7 @@
   let mut st : List Attr := []
   st := st ++ [Attr.serial]                            -- the dragged object reference
   st := st ++ [Attr.flag false]                        -- "drag in progress" flag
-  st := st ++ [Attr.flag (useBlit && blitSupported)]   -- effective fast-redraw flag
+  st := st ++ [Attr.flag (useBlit || blitSupported)]   -- effective fast-redraw flag
   st := st ++ [Attr.serial]                            -- connected callback identifiers
   return st
 -- impl-end
@@ -61,12 +61,11 @@
     problem_spec_initHandlerState useBlit blitSupported
       (implementation_initHandlerState useBlit blitSupported) := by
   intro useBlit blitSupported
-  have himpl : implementation_initHandlerState useBlit blitSupported
-      = [Attr.serial, Attr.flag false, Attr.flag (useBlit && blitSupported), Attr.serial] := rfl
-  refine ⟨?_, himpl⟩
-  rw [himpl]
-  intro a ha
-  fin_cases ha <;> simp
+  unfold problem_spec_initHandlerState implementation_initHandlerState stateSerializable
+  refine ⟨?_, ?_⟩ <;>
+    first
+      | (intro a ha; fin_cases ha <;> simp)
+      | (simp) | rfl | decide | (cases useBlit <;> cases blitSupported <;> simp)
 -- proof-end
 
 -- post-conditions-start
@@ -88,5 +87,6 @@
     problem_spec_accessDisplayHandle owner
       (implementation_accessDisplayHandle owner) := by
   intro owner
-  rfl
+  unfold problem_spec_accessDisplayHandle implementation_accessDisplayHandle
+  first | rfl | simp | decide
 -- proof-end
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -46,13 +46,8 @@
 
 -- impl-start
 def implementation_initHandlerState
-    (useBlit blitSupported : Bool) : List Attr := Id.run do
-  let mut st : List Attr := []
-  st := st ++ [Attr.serial]                            -- the dragged object reference
-  st := st ++ [Attr.flag false]                        -- "drag in progress" flag
-  st := st ++ [Attr.flag (useBlit && blitSupported)]   -- effective fast-redraw flag
-  st := st ++ [Attr.serial]                            -- connected callback identifiers
-  return st
+    (useBlit blitSupported : Bool) : List Attr :=
+  [Attr.serial, Attr.flag false, Attr.flag (useBlit && blitSupported), Attr.serial]
 -- impl-end
 
 -- proof-start
@@ -61,12 +56,11 @@
     problem_spec_initHandlerState useBlit blitSupported
       (implementation_initHandlerState useBlit blitSupported) := by
   intro useBlit blitSupported
-  have himpl : implementation_initHandlerState useBlit blitSupported
-      = [Attr.serial, Attr.flag false, Attr.flag (useBlit && blitSupported), Attr.serial] := rfl
-  refine ⟨?_, himpl⟩
-  rw [himpl]
-  intro a ha
-  fin_cases ha <;> simp
+  unfold problem_spec_initHandlerState implementation_initHandlerState stateSerializable
+  refine ⟨?_, ?_⟩ <;>
+    first
+      | (intro a ha; fin_cases ha <;> simp)
+      | (simp) | rfl | decide | (cases useBlit <;> cases blitSupported <;> simp)
 -- proof-end
 
 -- post-conditions-start
@@ -78,8 +72,8 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_accessDisplayHandle (owner : Container) : Nat := Id.run do
-  return owner.displayHandle
+def implementation_accessDisplayHandle (owner : Container) : Nat :=
+  owner.displayHandle
 -- impl-end
 
 -- proof-start
@@ -88,5 +82,6 @@
     problem_spec_accessDisplayHandle owner
       (implementation_accessDisplayHandle owner) := by
   intro owner
-  rfl
+  unfold problem_spec_accessDisplayHandle implementation_accessDisplayHandle
+  first | rfl | simp | decide
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. The persisted handler
-- state is modeled concretely as the ordered list of attributes it retains, and
-- the display-handle accessor is modeled concretely as a dereference of the
-- owning container. The proof agent may add `_prop` axioms only if it gets stuck.
-- axioms-end

-- pure-start
/-- A single attribute that an interactive handler may retain in its persisted
state. A value is either a boolean status flag, an ordinary serializable datum
(an object reference or a collection of callback identifiers), or a live display
handle that cannot be serialized. -/
inductive Attr where
  | flag (b : Bool)
  | serial
  | liveHandle
  deriving DecidableEq

/-- The persisted state is serializable exactly when it retains no live display
handle. -/
def stateSerializable (st : List Attr) : Prop :=
  ∀ a ∈ st, a ≠ Attr.liveHandle

/-- A container that owns a current display handle, identified abstractly. -/
structure Container where
  displayHandle : Nat
-- pure-end

-- post-conditions-start
/-- The handler's persisted state, after initialization, must be fully
serializable and must consist of exactly: the dragged object reference, the
"drag in progress" status flag (initially off), the effective fast-redraw flag
(requested only when both requested and supported), and the collection of
connected callback identifiers — in that order. Pinning the whole list frames
every component to its input; the serializability conjunct names the property
the result must have. -/
def problem_spec_initHandlerState
    (useBlit blitSupported : Bool) (result : List Attr) : Prop :=
  stateSerializable result ∧
  result = [Attr.serial, Attr.flag false,
            Attr.flag (useBlit && blitSupported), Attr.serial]
-- post-conditions-end

-- impl-start
def implementation_initHandlerState
    (useBlit blitSupported : Bool) : List Attr := Id.run do
  let mut st : List Attr := []
  st := st ++ [Attr.serial]                            -- the dragged object reference
  st := st ++ [Attr.flag false]                        -- "drag in progress" flag
  st := st ++ [Attr.flag (useBlit && blitSupported)]   -- effective fast-redraw flag
  st := st ++ [Attr.serial]                            -- connected callback identifiers
  return st
-- impl-end

-- proof-start
theorem correct_initHandlerState :
    ∀ (useBlit blitSupported : Bool),
    problem_spec_initHandlerState useBlit blitSupported
      (implementation_initHandlerState useBlit blitSupported) := by
  intro useBlit blitSupported
  have himpl : implementation_initHandlerState useBlit blitSupported
      = [Attr.serial, Attr.flag false, Attr.flag (useBlit && blitSupported), Attr.serial] := rfl
  refine ⟨?_, himpl⟩
  rw [himpl]
  intro a ha
  fin_cases ha <;> simp
-- proof-end

-- post-conditions-start
/-- The display-handle accessor yields the owning container's CURRENT display
handle (recomputed on every access rather than read from a stored snapshot). -/
def problem_spec_accessDisplayHandle
    (owner : Container) (result : Nat) : Prop :=
  result = owner.displayHandle
-- post-conditions-end

-- impl-start
def implementation_accessDisplayHandle (owner : Container) : Nat := Id.run do
  return owner.displayHandle
-- impl-end

-- proof-start
theorem correct_accessDisplayHandle :
    ∀ (owner : Container),
    problem_spec_accessDisplayHandle owner
      (implementation_accessDisplayHandle owner) := by
  intro owner
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec shape: BOTH postconditions are exact-value equalities over the FULL result (problem_spec_initHandlerState: stateSerializable result AND result = [Attr.serial, Attr.flag false, Attr.flag (useBlit && blitSupported), Attr.serial]; problem_spec_accessDisplayHandle: result = owner.displayHandle). Axioms region EMPTY (comment only) => no A-consumed/A-reference legs; G-AX is a legitimate skip stub (mapping.md confirms). refinement.md audit: all legs R (bool->Attr.flag, objref/cids->Attr.serial, and->&&) or I (empty start; deleted `self.canvas=...` op == absent liveHandle == the bug). No kind-3 (inexpressible) leg. A-leg correspondence N/A (none). Same_spec True for all 7 attacks + pos_control (verified via markers.same_spec, lean backend).

Protocol run Cmd per file: `bash scripts/lean_verify.sh <file>`. Results: pos_control EXIT=0 (verifies). atk_1 partial-domain (flag=useBlit only, drops blitSupported) EXIT=1. atk_2 boundary (swap first two list elements) EXIT=1. atk_3 control-flow-effect = PREPATCH BUG (appends Attr.liveHandle, non-serializable) EXIT=1 (prepatch reproduced; matches Solution_prepatch.lean sorry). atk_4 ungrounded-oracle echo (accessDisplayHandle returns constant 0) EXIT=1 (goal 0 = owner.displayHandle unprovable). atk_5 flag polarity (drag-in-progress = true) EXIT=1. atk_6 operator swap (useBlit || blitSupported) EXIT=1. atk_7 gold-EQUIVALENT echo (impl rewritten as direct literal list + owner.displayHandle, same output) EXIT=0. 6/7 value-domain wrong impls fail to close (exact-value spec rejects any deviation); only the gold-equivalent echo closes.

#print axioms (files atk_7_ax.lean, pos_control_ax.lean, EXIT=0): both correct_initHandlerState depend ONLY on [propext]; both correct_accessDisplayHandle depend on NO axioms. Clean (propext is standard for List DecidableEq; matches gold pos_control byte-identically).

atk_7 is the only closing wrong-impl; per echo-attack policy its faithful refined patch MUST resolve. Materialized atk_7.patch (== gold behavior) and EXECUTED via swebench_unified.harness.run_resolve('matplotlib__matplotlib-25311', patch, timeout=1200): RESOLVED=True, note='resolved', patch_successfully_applied=True. FAIL_TO_PASS test_pickle.py::test_complete[png] PASS; all 191 PASS_TO_PASS PASS; 0 failures. A resolving echo is NOT a weakness.

No impl with a closing clean-axiom proof has a non-resolving faithful patch. verify => correct holds for this bundle. Verdict SOUND.

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
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. The persisted handler
-- state is modeled concretely as the ordered list of attributes it retains, and
-- the display-handle accessor is modeled concretely as a dereference of the
-- owning container. The proof agent may add `_prop` axioms only if it gets stuck.
-- axioms-end

-- pure-start
/-- A single attribute that an interactive handler may retain in its persisted
state. A value is either a boolean status flag, an ordinary serializable datum
(an object reference or a collection of callback identifiers), or a live display
handle that cannot be serialized. -/
inductive Attr where
  | flag (b : Bool)
  | serial
  | liveHandle
  deriving DecidableEq

/-- The persisted state is serializable exactly when it retains no live display
handle. -/
def stateSerializable (st : List Attr) : Prop :=
  ∀ a ∈ st, a ≠ Attr.liveHandle

/-- A container that owns a current display handle, identified abstractly. -/
structure Container where
  displayHandle : Nat
-- pure-end

-- post-conditions-start
/-- The handler's persisted state, after initialization, must be fully
serializable and must consist of exactly: the dragged object reference, the
"drag in progress" status flag (initially off), the effective fast-redraw flag
(requested only when both requested and supported), and the collection of
connected callback identifiers — in that order. Pinning the whole list frames
every component to its input; the serializability conjunct names the property
the result must have. -/
def problem_spec_initHandlerState
    (useBlit blitSupported : Bool) (result : List Attr) : Prop :=
  stateSerializable result ∧
  result = [Attr.serial, Attr.flag false,
            Attr.flag (useBlit && blitSupported), Attr.serial]
-- post-conditions-end

-- impl-start
def implementation_initHandlerState
    (useBlit blitSupported : Bool) : List Attr := Id.run do
  let mut st : List Attr := []
  st := st ++ [Attr.serial]                            -- the dragged object reference
  st := st ++ [Attr.flag false]                        -- "drag in progress" flag
  st := st ++ [Attr.flag (useBlit && blitSupported)]   -- effective fast-redraw flag
  st := st ++ [Attr.serial]                            -- connected callback identifiers
  return st
-- impl-end

-- proof-start
theorem correct_initHandlerState :
    ∀ (useBlit blitSupported : Bool),
    problem_spec_initHandlerState useBlit blitSupported
      (implementation_initHandlerState useBlit blitSupported) := by
  intro useBlit blitSupported
  have himpl : implementation_initHandlerState useBlit blitSupported
      = [Attr.serial, Attr.flag false, Attr.flag (useBlit && blitSupported), Attr.serial] := rfl
  refine ⟨?_, himpl⟩
  rw [himpl]
  intro a ha
  fin_cases ha <;> simp
-- proof-end

-- post-conditions-start
/-- The display-handle accessor yields the owning container's CURRENT display
handle (recomputed on every access rather than read from a stored snapshot). -/
def problem_spec_accessDisplayHandle
    (owner : Container) (result : Nat) : Prop :=
  result = owner.displayHandle
-- post-conditions-end

-- impl-start
def implementation_accessDisplayHandle (owner : Container) : Nat := Id.run do
  return owner.displayHandle
-- impl-end

-- proof-start
theorem correct_accessDisplayHandle :
    ∀ (owner : Container),
    problem_spec_accessDisplayHandle owner
      (implementation_accessDisplayHandle owner) := by
  intro owner
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec shape: BOTH postconditions are exact-value equalities over the FULL result (problem_spec_initHandlerState: stateSerializable result AND result = [Attr.serial, Attr.flag false, Attr.flag (useBlit && blitSupported), Attr.serial]; problem_spec_accessDisplayHandle: result = owner.displayHandle). Axioms region EMPTY (comment only) => no A-consumed/A-reference legs; G-AX is a legitimate skip stub (mapping.md confirms). refinement.md audit: all legs R (bool->Attr.flag, objref/cids->Attr.serial, and->&&) or I (empty start; deleted `self.canvas=...` op == absent liveHandle == the bug). No kind-3 (inexpressible) leg. A-leg correspondence N/A (none). Same_spec True for all 7 attacks + pos_control (verified via markers.same_spec, lean backend).

Protocol run Cmd per file: `bash scripts/lean_verify.sh <file>`. Results: pos_control EXIT=0 (verifies). atk_1 partial-domain (flag=useBlit only, drops blitSupported) EXIT=1. atk_2 boundary (swap first two list elements) EXIT=1. atk_3 control-flow-effect = PREPATCH BUG (appends Attr.liveHandle, non-serializable) EXIT=1 (prepatch reproduced; matches Solution_prepatch.lean sorry). atk_4 ungrounded-oracle echo (accessDisplayHandle returns constant 0) EXIT=1 (goal 0 = owner.displayHandle unprovable). atk_5 flag polarity (drag-in-progress = true) EXIT=1. atk_6 operator swap (useBlit || blitSupported) EXIT=1. atk_7 gold-EQUIVALENT echo (impl rewritten as direct literal list + owner.displayHandle, same output) EXIT=0. 6/7 value-domain wrong impls fail to close (exact-value spec rejects any deviation); only the gold-equivalent echo closes.

#print axioms (files atk_7_ax.lean, pos_control_ax.lean, EXIT=0): both correct_initHandlerState depend ONLY on [propext]; both correct_accessDisplayHandle depend on NO axioms. Clean (propext is standard for List DecidableEq; matches gold pos_control byte-identically).

atk_7 is the only closing wrong-impl; per echo-attack policy its faithful refined patch MUST resolve. Materialized atk_7.patch (== gold behavior) and EXECUTED via swebench_unified.harness.run_resolve('matplotlib__matplotlib-25311', patch, timeout=1200): RESOLVED=True, note='resolved', patch_successfully_applied=True. FAIL_TO_PASS test_pickle.py::test_complete[png] PASS; all 191 PASS_TO_PASS PASS; 0 failures. A resolving echo is NOT a weakness.

No impl with a closing clean-axiom proof has a non-resolving faithful patch. verify => correct holds for this bundle. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (panel_2 drift) check for matplotlib__matplotlib-25311 lean bundle. (1) Spec-region byte-identity: swebench_unified.markers.same_spec(Solution, Solution_prepatch, LeanBackend) = True; only impl/proof regions differ (prepatch inserts Attr.liveHandle and sorry). (2) Solution.lean compiles via scripts/lean_verify.sh (exit 0, no sorry); #print axioms => correct_initHandlerState depends only on [propext], correct_accessDisplayHandle depends on none — no sorryAx, proofs genuine. (3) Real repo (base 430fb1db, gold patch removes `self.canvas = self.ref_artist.figure.canvas` from DraggableBase.__init__ and adds `canvas = property(lambda self: self.ref_artist.figure.canvas)`). Fn1 initHandlerState: post-patch persisted __dict__ in insertion order = ref_artist, got_artist=False, _use_blit=(use_blit and canvas.supports_blit) [a bool], cids; canvas no longer stored. Lean model [Attr.serial, Attr.flag false, Attr.flag (useBlit && blitSupported), Attr.serial] matches for all 4 (use_blit, supports_blit) bool combos (Python `and` over bools == Lean &&), got_artist always False, no liveHandle => stateSerializable holds. Fn2 accessDisplayHandle: property recomputes ref_artist.figure.canvas each access; model returns owner.displayHandle and pins result=owner.displayHandle (identity abstraction, recomputed-per-access). No input diverges from real behavior. (4) conformance_check.py: 240004 fuzzed inputs (seed 25311), 0 disagreements. The spec is not too strong and does not drift — it is a documented, appropriately-scoped abstraction (picklability contribution, not object identity) that exactly reproduces post-patch behavior across the entire modeled input domain. No diverging input exists.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Gold edit: remove `self.canvas = self.ref_artist.figure.canvas` from DraggableBase.__init__ and add class-level `canvas = property(lambda self: self.ref_artist.figure.canvas)` in lib/matplotlib/offsetbox.py. Public problem_statement reports only the symptom (cannot pickle draggable-legend figure / 'cannot pickle FigureCanvasQTAgg'; expected pickling successful). Spec view analysis: (1) Mechanical leakage.screen PASSED — no hard failures, _patch_changed_symbols is EMPTY (diff touches only __init__/canvas, both filtered as non-distinctive/short). (2) No patched file path (offsetbox.py absent), no module path, no diff markers (@@, diff --git, +++), no repo symbols (offsetbox/DraggableBase/use_blit/got_artist/supports_blit/cids/ref_artist/figure all absent from view). (3) No bug/fix narration in comments (checked vs _NARRATION set). Only 'property' hit is the English word in a docstring ('the property the result must have'), not the Python idiom. (4) same_spec(Solution.lean, Solution_prepatch.lean)=True — spec region byte-identical, so consumer's spec view is independent of pre/post; the discriminating impl/proof are elided. The spec encodes correctness (serializable state = no liveHandle + exact result list; display handle recomputed per access), which is directly implied by the public problem statement (unpicklable canvas -> don't retain it; 'pickling successful' = serializability). Specifying correct behavior is not leaking the gold edit; no localization (file/symbol/line/edit narration) is exposed beyond the public task. G-LEAK meta status = pass; not a relaxed bundle.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
