# P2 adversarial audit — pydata__xarray-6938

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
None found. The spec conjunction uniquely pins the model output to (heap.push heap[src]!, heap.size). clause1 result.2=heap.size fixes handle; clause2 result.1.size=heap.size+1 fixes growth; clause4 frame fixes first n slots; clause3 fixes produced-slot contents = heap[src]!. With precondition src<heap.size all [...]! reads are in-bounds (no getElem!-default vacuity). No same-spec wrong impl can close its proof, hence no closing-clean-axiom impl exists to materialize a non-resolving patch from. verify⇏correct cannot be triggered.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -51,11 +51,7 @@
 -- impl-start
 def implementation_toIndexVariable
     (heap : Array VarRec) (src : Nat) : Array VarRec × Nat := Id.run do
-  let mut h := heap
-  let fresh := h[src]!        -- the contents of the source object
-  let handle := h.size        -- identity of the produced object: a new slot
-  h := h.push fresh           -- allocate the produced object as an independent slot
-  return (h, handle)
+  return (heap, src)
 -- impl-end
 
 -- proof-start
@@ -65,13 +61,16 @@
       (implementation_toIndexVariable heap src) := by
   intro heap src hsrc
   unfold problem_spec_toIndexVariable implementation_toIndexVariable
-  simp only [Id.run, pure]
-  refine ⟨trivial, ?_, ?_, ?_⟩
-  · simp [Array.size_push]
-  · simp [Array.getElem!_eq_getD]
-  · intro i hi
-    rw [Array.getElem!_eq_getD, Array.getElem!_eq_getD,
-        Array.getD_eq_getD_getElem?, Array.getD_eq_getD_getElem?,
-        Array.getElem?_push]
-    simp [Nat.ne_of_lt hi, hi]
+  simp only [Id.run, pure, bind]
+  first
+  | (refine ⟨trivial, ?_, ?_, ?_⟩
+     · simp [Array.size_push]
+     · simp [Array.getElem!_eq_getD]
+     · intro i hi
+       rw [Array.getElem!_eq_getD, Array.getElem!_eq_getD,
+           Array.getD_eq_getD_getElem?, Array.getD_eq_getD_getElem?,
+           Array.getElem?_push]
+       simp [Nat.ne_of_lt hi, hi])
+  | (refine ⟨?_, ?_, ?_, ?_⟩ <;> simp_all [Array.size_push, Array.getElem!_eq_getD, Array.getElem?_push] <;> omega)
+  | simp_all [Array.size_push, Array.getElem!_eq_getD, Array.getElem?_push]
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -52,10 +52,8 @@
 def implementation_toIndexVariable
     (heap : Array VarRec) (src : Nat) : Array VarRec × Nat := Id.run do
   let mut h := heap
-  let fresh := h[src]!        -- the contents of the source object
-  let handle := h.size        -- identity of the produced object: a new slot
-  h := h.push fresh           -- allocate the produced object as an independent slot
-  return (h, handle)
+  h := h.push (default : VarRec)
+  return (h, heap.size)
 -- impl-end
 
 -- proof-start
@@ -65,13 +63,16 @@
       (implementation_toIndexVariable heap src) := by
   intro heap src hsrc
   unfold problem_spec_toIndexVariable implementation_toIndexVariable
-  simp only [Id.run, pure]
-  refine ⟨trivial, ?_, ?_, ?_⟩
-  · simp [Array.size_push]
-  · simp [Array.getElem!_eq_getD]
-  · intro i hi
-    rw [Array.getElem!_eq_getD, Array.getElem!_eq_getD,
-        Array.getD_eq_getD_getElem?, Array.getD_eq_getD_getElem?,
-        Array.getElem?_push]
-    simp [Nat.ne_of_lt hi, hi]
+  simp only [Id.run, pure, bind]
+  first
+  | (refine ⟨trivial, ?_, ?_, ?_⟩
+     · simp [Array.size_push]
+     · simp [Array.getElem!_eq_getD]
+     · intro i hi
+       rw [Array.getElem!_eq_getD, Array.getElem!_eq_getD,
+           Array.getD_eq_getD_getElem?, Array.getD_eq_getD_getElem?,
+           Array.getElem?_push]
+       simp [Nat.ne_of_lt hi, hi])
+  | (refine ⟨?_, ?_, ?_, ?_⟩ <;> simp_all [Array.size_push, Array.getElem!_eq_getD, Array.getElem?_push] <;> omega)
+  | simp_all [Array.size_push, Array.getElem!_eq_getD, Array.getElem?_push]
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -52,10 +52,10 @@
 def implementation_toIndexVariable
     (heap : Array VarRec) (src : Nat) : Array VarRec × Nat := Id.run do
   let mut h := heap
-  let fresh := h[src]!        -- the contents of the source object
-  let handle := h.size        -- identity of the produced object: a new slot
-  h := h.push fresh           -- allocate the produced object as an independent slot
-  return (h, handle)
+  let fresh := h[src]!
+  h := h.set! src { dims := [], data := 999 }
+  h := h.push fresh
+  return (h, heap.size)
 -- impl-end
 
 -- proof-start
@@ -65,13 +65,16 @@
       (implementation_toIndexVariable heap src) := by
   intro heap src hsrc
   unfold problem_spec_toIndexVariable implementation_toIndexVariable
-  simp only [Id.run, pure]
-  refine ⟨trivial, ?_, ?_, ?_⟩
-  · simp [Array.size_push]
-  · simp [Array.getElem!_eq_getD]
-  · intro i hi
-    rw [Array.getElem!_eq_getD, Array.getElem!_eq_getD,
-        Array.getD_eq_getD_getElem?, Array.getD_eq_getD_getElem?,
-        Array.getElem?_push]
-    simp [Nat.ne_of_lt hi, hi]
+  simp only [Id.run, pure, bind]
+  first
+  | (refine ⟨trivial, ?_, ?_, ?_⟩
+     · simp [Array.size_push]
+     · simp [Array.getElem!_eq_getD]
+     · intro i hi
+       rw [Array.getElem!_eq_getD, Array.getElem!_eq_getD,
+           Array.getD_eq_getD_getElem?, Array.getD_eq_getD_getElem?,
+           Array.getElem?_push]
+       simp [Nat.ne_of_lt hi, hi])
+  | (refine ⟨?_, ?_, ?_, ?_⟩ <;> simp_all [Array.size_push, Array.getElem!_eq_getD, Array.getElem?_push] <;> omega)
+  | simp_all [Array.size_push, Array.getElem!_eq_getD, Array.getElem?_push]
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -52,10 +52,9 @@
 def implementation_toIndexVariable
     (heap : Array VarRec) (src : Nat) : Array VarRec × Nat := Id.run do
   let mut h := heap
-  let fresh := h[src]!        -- the contents of the source object
-  let handle := h.size        -- identity of the produced object: a new slot
-  h := h.push fresh           -- allocate the produced object as an independent slot
-  return (h, handle)
+  let fresh := h[src]!
+  h := h.push fresh
+  return (h, 0)
 -- impl-end
 
 -- proof-start
@@ -65,13 +64,16 @@
       (implementation_toIndexVariable heap src) := by
   intro heap src hsrc
   unfold problem_spec_toIndexVariable implementation_toIndexVariable
-  simp only [Id.run, pure]
-  refine ⟨trivial, ?_, ?_, ?_⟩
-  · simp [Array.size_push]
-  · simp [Array.getElem!_eq_getD]
-  · intro i hi
-    rw [Array.getElem!_eq_getD, Array.getElem!_eq_getD,
-        Array.getD_eq_getD_getElem?, Array.getD_eq_getD_getElem?,
-        Array.getElem?_push]
-    simp [Nat.ne_of_lt hi, hi]
+  simp only [Id.run, pure, bind]
+  first
+  | (refine ⟨trivial, ?_, ?_, ?_⟩
+     · simp [Array.size_push]
+     · simp [Array.getElem!_eq_getD]
+     · intro i hi
+       rw [Array.getElem!_eq_getD, Array.getElem!_eq_getD,
+           Array.getD_eq_getD_getElem?, Array.getD_eq_getD_getElem?,
+           Array.getElem?_push]
+       simp [Nat.ne_of_lt hi, hi])
+  | (refine ⟨?_, ?_, ?_, ?_⟩ <;> simp_all [Array.size_push, Array.getElem!_eq_getD, Array.getElem?_push] <;> omega)
+  | simp_all [Array.size_push, Array.getElem!_eq_getD, Array.getElem?_push]
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -52,10 +52,9 @@
 def implementation_toIndexVariable
     (heap : Array VarRec) (src : Nat) : Array VarRec × Nat := Id.run do
   let mut h := heap
-  let fresh := h[src]!        -- the contents of the source object
-  let handle := h.size        -- identity of the produced object: a new slot
-  h := h.push fresh           -- allocate the produced object as an independent slot
-  return (h, handle)
+  let fresh := h[src]!
+  h := h.push { dims := fresh.dims, data := fresh.data + 1 }
+  return (h, heap.size)
 -- impl-end
 
 -- proof-start
@@ -65,13 +64,16 @@
       (implementation_toIndexVariable heap src) := by
   intro heap src hsrc
   unfold problem_spec_toIndexVariable implementation_toIndexVariable
-  simp only [Id.run, pure]
-  refine ⟨trivial, ?_, ?_, ?_⟩
-  · simp [Array.size_push]
-  · simp [Array.getElem!_eq_getD]
-  · intro i hi
-    rw [Array.getElem!_eq_getD, Array.getElem!_eq_getD,
-        Array.getD_eq_getD_getElem?, Array.getD_eq_getD_getElem?,
-        Array.getElem?_push]
-    simp [Nat.ne_of_lt hi, hi]
+  simp only [Id.run, pure, bind]
+  first
+  | (refine ⟨trivial, ?_, ?_, ?_⟩
+     · simp [Array.size_push]
+     · simp [Array.getElem!_eq_getD]
+     · intro i hi
+       rw [Array.getElem!_eq_getD, Array.getElem!_eq_getD,
+           Array.getD_eq_getD_getElem?, Array.getD_eq_getD_getElem?,
+           Array.getElem?_push]
+       simp [Nat.ne_of_lt hi, hi])
+  | (refine ⟨?_, ?_, ?_, ?_⟩ <;> simp_all [Array.size_push, Array.getElem!_eq_getD, Array.getElem?_push] <;> omega)
+  | simp_all [Array.size_push, Array.getElem!_eq_getD, Array.getElem?_push]
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -51,11 +51,7 @@
 -- impl-start
 def implementation_toIndexVariable
     (heap : Array VarRec) (src : Nat) : Array VarRec × Nat := Id.run do
-  let mut h := heap
-  let fresh := h[src]!        -- the contents of the source object
-  let handle := h.size        -- identity of the produced object: a new slot
-  h := h.push fresh           -- allocate the produced object as an independent slot
-  return (h, handle)
+  return (heap, heap.size)
 -- impl-end
 
 -- proof-start
@@ -65,13 +61,16 @@
       (implementation_toIndexVariable heap src) := by
   intro heap src hsrc
   unfold problem_spec_toIndexVariable implementation_toIndexVariable
-  simp only [Id.run, pure]
-  refine ⟨trivial, ?_, ?_, ?_⟩
-  · simp [Array.size_push]
-  · simp [Array.getElem!_eq_getD]
-  · intro i hi
-    rw [Array.getElem!_eq_getD, Array.getElem!_eq_getD,
-        Array.getD_eq_getD_getElem?, Array.getD_eq_getD_getElem?,
-        Array.getElem?_push]
-    simp [Nat.ne_of_lt hi, hi]
+  simp only [Id.run, pure, bind]
+  first
+  | (refine ⟨trivial, ?_, ?_, ?_⟩
+     · simp [Array.size_push]
+     · simp [Array.getElem!_eq_getD]
+     · intro i hi
+       rw [Array.getElem!_eq_getD, Array.getElem!_eq_getD,
+           Array.getD_eq_getD_getElem?, Array.getD_eq_getD_getElem?,
+           Array.getElem?_push]
+       simp [Nat.ne_of_lt hi, hi])
+  | (refine ⟨?_, ?_, ?_, ?_⟩ <;> simp_all [Array.size_push, Array.getElem!_eq_getD, Array.getElem?_push] <;> omega)
+  | simp_all [Array.size_push, Array.getElem!_eq_getD, Array.getElem?_push]
 -- proof-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -52,10 +52,10 @@
 def implementation_toIndexVariable
     (heap : Array VarRec) (src : Nat) : Array VarRec × Nat := Id.run do
   let mut h := heap
-  let fresh := h[src]!        -- the contents of the source object
-  let handle := h.size        -- identity of the produced object: a new slot
-  h := h.push fresh           -- allocate the produced object as an independent slot
-  return (h, handle)
+  let fresh := h[src]!
+  h := h.push fresh
+  h := h.push fresh
+  return (h, heap.size)
 -- impl-end
 
 -- proof-start
@@ -65,13 +65,16 @@
       (implementation_toIndexVariable heap src) := by
   intro heap src hsrc
   unfold problem_spec_toIndexVariable implementation_toIndexVariable
-  simp only [Id.run, pure]
-  refine ⟨trivial, ?_, ?_, ?_⟩
-  · simp [Array.size_push]
-  · simp [Array.getElem!_eq_getD]
-  · intro i hi
-    rw [Array.getElem!_eq_getD, Array.getElem!_eq_getD,
-        Array.getD_eq_getD_getElem?, Array.getD_eq_getD_getElem?,
-        Array.getElem?_push]
-    simp [Nat.ne_of_lt hi, hi]
+  simp only [Id.run, pure, bind]
+  first
+  | (refine ⟨trivial, ?_, ?_, ?_⟩
+     · simp [Array.size_push]
+     · simp [Array.getElem!_eq_getD]
+     · intro i hi
+       rw [Array.getElem!_eq_getD, Array.getElem!_eq_getD,
+           Array.getD_eq_getD_getElem?, Array.getD_eq_getD_getElem?,
+           Array.getElem?_push]
+       simp [Nat.ne_of_lt hi, hi])
+  | (refine ⟨?_, ?_, ?_, ?_⟩ <;> simp_all [Array.size_push, Array.getElem!_eq_getD, Array.getElem?_push] <;> omega)
+  | simp_all [Array.size_push, Array.getElem!_eq_getD, Array.getElem?_push]
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Converting an array-like object into its indexed form should yield an
INDEPENDENT object: the returned object must not be the same object as the
source, so that later in-place edits to the returned object cannot reach back
and alter the source. We model the universe of live objects as a heap (an
`Array` of records); an object's identity is its slot index (a handle). The
modeled operation takes a source handle and returns the updated heap together
with the handle of the produced object.
-/

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here: producing the independent
-- object is modeled DEEPLY as a fresh heap allocation duplicating the source
-- record, rather than abstracted behind an axiom. The proof agent may add
-- `_prop` axioms only if it gets stuck.
-- axioms-end

-- pure-start
/-- A live object, holding the touched fields: its axis labels (`dims`, a list
of label codes) and an opaque contents code (`data`). Two objects are equal
exactly when both fields agree. -/
structure VarRec where
  dims : List Nat
  data : Nat
deriving DecidableEq, Repr, Inhabited
-- pure-end

-- post-conditions-start
/-- The result of converting the object at handle `src` to its indexed form.

`result.1` is the resulting heap, `result.2` the handle of the produced object.

* Independence: the produced handle is a brand-new slot (`= heap.size`), hence
  distinct from every pre-existing handle — in particular from `src`. This is
  what guarantees that mutating the produced object later cannot affect `src`.
* The heap grows by exactly one slot.
* Contents: the produced object carries the same fields as the source object.
* Frame: every pre-existing object is left untouched. -/
def problem_spec_toIndexVariable
    (heap : Array VarRec) (src : Nat)
    (result : Array VarRec × Nat) : Prop :=
  result.2 = heap.size ∧
  result.1.size = heap.size + 1 ∧
  result.1[result.2]! = heap[src]! ∧
  (∀ i, i < heap.size → result.1[i]! = heap[i]!)
-- post-conditions-end

-- impl-start
def implementation_toIndexVariable
    (heap : Array VarRec) (src : Nat) : Array VarRec × Nat := Id.run do
  let mut h := heap
  let fresh := h[src]!        -- the contents of the source object
  let handle := h.size        -- identity of the produced object: a new slot
  h := h.push fresh           -- allocate the produced object as an independent slot
  return (h, handle)
-- impl-end

-- proof-start
theorem correct_toIndexVariable :
    ∀ (heap : Array VarRec) (src : Nat), src < heap.size →
    problem_spec_toIndexVariable heap src
      (implementation_toIndexVariable heap src) := by
  intro heap src hsrc
  unfold problem_spec_toIndexVariable implementation_toIndexVariable
  simp only [Id.run, pure]
  refine ⟨trivial, ?_, ?_, ?_⟩
  · simp [Array.size_push]
  · simp [Array.getElem!_eq_getD]
  · intro i hi
    rw [Array.getElem!_eq_getD, Array.getElem!_eq_getD,
        Array.getD_eq_getD_getElem?, Array.getD_eq_getD_getElem?,
        Array.getElem?_push]
    simp [Nat.ne_of_lt hi, hi]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PY=python. same_spec (lean backend) = True for all 7 attacks and pos_control. Verify cmd: `bash scripts/lean_verify.sh <file>`. Results: pos_control exit=0 (verifies); #print axioms correct_toIndexVariable => [propext, Classical.choice, Quot.sound] (clean, no sorryAx). atk_1..atk_7 all exit=1 with genuine 'error: unsolved goals' (checked out files; not parse errors), using a strong multi-branch proof-closing attempt (gold body + simp_all/omega fallbacks) so failures reflect the spec, not weak tactics.

Attack classes: atk_1 prepatch alias `return (heap,src)`; atk_2 push default record (wrong contents); atk_3 corrupt src slot via set! then push (frame/control-flow-effect); atk_4 correct heap but wrong handle 0; atk_5 push {dims,data+1} boundary near-miss; atk_6 `return (heap,heap.size)` no-growth ungrounded-oracle echo; atk_7 double push (size n+2). Verifications launched concurrently in background batches (<=4).

Since NO attack closes with a clean-axiom proof, protocol step 2 (materialize faithful patch + run_resolve) has no eligible closing impl; patches={} accordingly, and no resolve run was required. refinement.md audit: 5 legs all R (rows1-4)/I (row5); no kind-3 changed-inexpressible; axioms region empty so no A-consumed/A-reference legs — self.copy() modeled deeply (fresh slot = heap[src], new handle = heap.size) not axiomatized, exercised end-to-end by G-CONF; correspondence to real callee IndexVariable.copy (variable.py:2831 -> _replace, same dims/data, distinct object) holds. mapping.md/verdict.md consistent.

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
None found. The spec conjunction uniquely pins the model output to (heap.push heap[src]!, heap.size). clause1 result.2=heap.size fixes handle; clause2 result.1.size=heap.size+1 fixes growth; clause4 frame fixes first n slots; clause3 fixes produced-slot contents = heap[src]!. With precondition src<heap.size all [...]! reads are in-bounds (no getElem!-default vacuity). No same-spec wrong impl can close its proof, hence no closing-clean-axiom impl exists to materialize a non-resolving patch from. verify⇏correct cannot be triggered.
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
Converting an array-like object into its indexed form should yield an
INDEPENDENT object: the returned object must not be the same object as the
source, so that later in-place edits to the returned object cannot reach back
and alter the source. We model the universe of live objects as a heap (an
`Array` of records); an object's identity is its slot index (a handle). The
modeled operation takes a source handle and returns the updated heap together
with the handle of the produced object.
-/

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here: producing the independent
-- object is modeled DEEPLY as a fresh heap allocation duplicating the source
-- record, rather than abstracted behind an axiom. The proof agent may add
-- `_prop` axioms only if it gets stuck.
-- axioms-end

-- pure-start
/-- A live object, holding the touched fields: its axis labels (`dims`, a list
of label codes) and an opaque contents code (`data`). Two objects are equal
exactly when both fields agree. -/
structure VarRec where
  dims : List Nat
  data : Nat
deriving DecidableEq, Repr, Inhabited
-- pure-end

-- post-conditions-start
/-- The result of converting the object at handle `src` to its indexed form.

`result.1` is the resulting heap, `result.2` the handle of the produced object.

* Independence: the produced handle is a brand-new slot (`= heap.size`), hence
  distinct from every pre-existing handle — in particular from `src`. This is
  what guarantees that mutating the produced object later cannot affect `src`.
* The heap grows by exactly one slot.
* Contents: the produced object carries the same fields as the source object.
* Frame: every pre-existing object is left untouched. -/
def problem_spec_toIndexVariable
    (heap : Array VarRec) (src : Nat)
    (result : Array VarRec × Nat) : Prop :=
  result.2 = heap.size ∧
  result.1.size = heap.size + 1 ∧
  result.1[result.2]! = heap[src]! ∧
  (∀ i, i < heap.size → result.1[i]! = heap[i]!)
-- post-conditions-end

-- impl-start
def implementation_toIndexVariable
    (heap : Array VarRec) (src : Nat) : Array VarRec × Nat := Id.run do
  let mut h := heap
  let fresh := h[src]!        -- the contents of the source object
  let handle := h.size        -- identity of the produced object: a new slot
  h := h.push fresh           -- allocate the produced object as an independent slot
  return (h, handle)
-- impl-end

-- proof-start
theorem correct_toIndexVariable :
    ∀ (heap : Array VarRec) (src : Nat), src < heap.size →
    problem_spec_toIndexVariable heap src
      (implementation_toIndexVariable heap src) := by
  intro heap src hsrc
  unfold problem_spec_toIndexVariable implementation_toIndexVariable
  simp only [Id.run, pure]
  refine ⟨trivial, ?_, ?_, ?_⟩
  · simp [Array.size_push]
  · simp [Array.getElem!_eq_getD]
  · intro i hi
    rw [Array.getElem!_eq_getD, Array.getElem!_eq_getD,
        Array.getD_eq_getD_getElem?, Array.getD_eq_getD_getElem?,
        Array.getElem?_push]
    simp [Nat.ne_of_lt hi, hi]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PY=python. same_spec (lean backend) = True for all 7 attacks and pos_control. Verify cmd: `bash scripts/lean_verify.sh <file>`. Results: pos_control exit=0 (verifies); #print axioms correct_toIndexVariable => [propext, Classical.choice, Quot.sound] (clean, no sorryAx). atk_1..atk_7 all exit=1 with genuine 'error: unsolved goals' (checked out files; not parse errors), using a strong multi-branch proof-closing attempt (gold body + simp_all/omega fallbacks) so failures reflect the spec, not weak tactics.

Attack classes: atk_1 prepatch alias `return (heap,src)`; atk_2 push default record (wrong contents); atk_3 corrupt src slot via set! then push (frame/control-flow-effect); atk_4 correct heap but wrong handle 0; atk_5 push {dims,data+1} boundary near-miss; atk_6 `return (heap,heap.size)` no-growth ungrounded-oracle echo; atk_7 double push (size n+2). Verifications launched concurrently in background batches (<=4).

Since NO attack closes with a clean-axiom proof, protocol step 2 (materialize faithful patch + run_resolve) has no eligible closing impl; patches={} accordingly, and no resolve run was required. refinement.md audit: 5 legs all R (rows1-4)/I (row5); no kind-3 changed-inexpressible; axioms region empty so no A-consumed/A-reference legs — self.copy() modeled deeply (fresh slot = heap[src], new handle = heap.size) not axiomatized, exercised end-to-end by G-CONF; correspondence to real callee IndexVariable.copy (variable.py:2831 -> _replace, same dims/data, distinct object) holds. mapping.md/verdict.md consistent.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack found no divergence between the modeled function and the real repo callee.

### SETUP CHECKS (all pass):
- lean_verify.sh Solution.lean => exit 0 (compiles, no sorry).
- #print axioms correct_toIndexVariable = [propext, Classical.choice, Quot.sound] — clean, NO sorryAx (proof is genuine).
- swebench_unified.markers.same_spec(Solution, Solution_prepatch, lean) = True; spec view contains only docstring/empty-axioms/VarRec/problem_spec_toIndexVariable/signatures — no impl, no patch content leaked.

### REAL CALLEE (fetched base_commit c4e40d991c28be51de9ac560ce895ac7f9b14924 into worktree):
- Base (buggy): IndexVariable.to_index_variable (variable.py:2882) => `return self` (aliasing).
- Patched: `return self.copy()`. IndexVariable.copy (2831) does `data = self._data.copy(deep=deep)` then `self._replace(data=data)`. _replace (976) with default dims sets `dims = copy.copy(self._dims)` and constructs `type(self)(dims, data, attrs, encoding, fastpath=True)` — a NEW IndexVariable with SAME dims/data (index _data is an immutable pandas Index, so copy is value-identical per the copy docstring). Source object never mutated.

FAITHFULNESS ARGUMENT: The model is a heap (Array VarRec) with object identity = slot handle. Projecting the patched callee onto the modeled observables (dims, data, identity, frame):
  1. distinct/fresh object  <-> result.2 = heap.size (>= 1 by precondition src<heap.size, so != src)
  2. universe grows by one   <-> result.1.size = heap.size + 1
  3. produced fields = source <-> result.1[heap.size]! = heap[src]! (copy preserves dims; immutable index data value-identical)
  4. source untouched (frame) <-> forall i<heap.size, result.1[i]! = heap[i]!
The modeled implementation_toIndexVariable (push a duplicate of heap[src], return handle heap.size) reproduces exactly this on EVERY input. Since to_index_variable is only defined on IndexVariable, self._data is always an immutable pandas Index and copy() always yields a distinct, value-identical object — no input class breaks the correspondence.

The spec is NOT too strong: it asserts nothing false about the abstracted-away fields (attrs/encoding), and the F2P test test_to_index_variable_copy observes only identity (`a is not b`) and dims — both faithfully modeled. No diverging input exists.

Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Gold edit: IndexVariable.to_index_variable returns self.copy() instead of self (produce an independent object so later in-place edits don't reach back to the source). Public problem_statement already states the expected behavior explicitly: '.swap_dims() can modify original object' / 'I expected it not to modify the original object.' The consumer spec view (Solution.lean projection) formalizes exactly this public expectation as a postcondition — independence (produced handle = heap.size, distinct from src), heap grows by one, contents copied, frame preserved. Checked the full spec view: no diff markers, no patched file path (dataset.py/variable.py), no reproduction of any gold-patch changed line, and no patched repo symbol echoed. Modeled identifiers are generic domain terms (VarRec, heap, src, dims, data, problem_spec_toIndexVariable/implementation_toIndexVariable); the mechanical screen (leakage.screen) returns passed=True with zero hard failures, and toIndexVariable does NOT trigger the symbol-collision check (no patched def/class name >=4 chars beyond the problem statement is embedded). The narration in the /-! ... -/ block ('INDEPENDENT object', 'cannot reach back and alter the source') restates only the publicly-stated expected behavior, not the specific edit (no mention of copy(), to_index_variable, or the return-self bug site). Encoding correct behavior is the inherent function of a spec and does not exceed problem_statement. mapping.md/refinement.md DO name to_index_variable/self.copy(), but those are auditor-facing correspondence artifacts, not part of the G-LEAK-screened consumer spec view. Nothing in the spec view reconstructs the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
