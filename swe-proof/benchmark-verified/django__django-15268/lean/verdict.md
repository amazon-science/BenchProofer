# P2 adversarial audit — django__django-15268

**Backend:** `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -68,14 +68,11 @@
 -- post-conditions-end
 
 -- impl-start
--- Extends the baseline rule with one extra allowance: the two flavours are
--- independent, so a later operation of the OTHER flavour is also permitted.
+-- Extends the baseline rule (attack variant).
 def implementation_canOptimizeAcross
     (selfKind : Kind) (selfName : String) (operation : Op) : Bool :=
-  baseCanOptimizeAcross selfName operation ||
-    (isAlterTogether operation.ty && decide (operation.ty ≠ kindTag selfKind))
+  baseCanOptimizeAcross selfName operation
 -- impl-end
-
 -- proof-start
 theorem correct_canOptimizeAcross :
     ∀ (selfKind : Kind) (selfName : String) (operation : Op),
@@ -83,8 +80,13 @@
         (implementation_canOptimizeAcross selfKind selfName operation) := by
   intro selfKind selfName operation
   unfold problem_spec_canOptimizeAcross implementation_canOptimizeAcross baseCanOptimizeAcross
-  simp only [Bool.or_eq_true, Bool.and_eq_true, decide_eq_true_eq,
-    Bool.not_eq_eq_eq_not, Bool.not_true]
+  cases selfKind <;> cases h : operation.ty <;>
+    simp_all [isAlterTogether, kindTag, Bool.or_eq_true, Bool.and_eq_true,
+      decide_eq_true_eq, Bool.not_eq_eq_eq_not, Bool.not_true] <;>
+    first
+      | rfl
+      | tauto
+      | (cases hb : affectsModel operation selfName <;> simp_all)
 -- proof-end
 
 #print axioms correct_canOptimizeAcross
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -68,14 +68,12 @@
 -- post-conditions-end
 
 -- impl-start
--- Extends the baseline rule with one extra allowance: the two flavours are
--- independent, so a later operation of the OTHER flavour is also permitted.
+-- Extends the baseline rule (attack variant).
 def implementation_canOptimizeAcross
     (selfKind : Kind) (selfName : String) (operation : Op) : Bool :=
   baseCanOptimizeAcross selfName operation ||
-    (isAlterTogether operation.ty && decide (operation.ty ≠ kindTag selfKind))
+    decide (operation.ty ≠ kindTag selfKind)
 -- impl-end
-
 -- proof-start
 theorem correct_canOptimizeAcross :
     ∀ (selfKind : Kind) (selfName : String) (operation : Op),
@@ -83,8 +81,13 @@
         (implementation_canOptimizeAcross selfKind selfName operation) := by
   intro selfKind selfName operation
   unfold problem_spec_canOptimizeAcross implementation_canOptimizeAcross baseCanOptimizeAcross
-  simp only [Bool.or_eq_true, Bool.and_eq_true, decide_eq_true_eq,
-    Bool.not_eq_eq_eq_not, Bool.not_true]
+  cases selfKind <;> cases h : operation.ty <;>
+    simp_all [isAlterTogether, kindTag, Bool.or_eq_true, Bool.and_eq_true,
+      decide_eq_true_eq, Bool.not_eq_eq_eq_not, Bool.not_true] <;>
+    first
+      | rfl
+      | tauto
+      | (cases hb : affectsModel operation selfName <;> simp_all)
 -- proof-end
 
 #print axioms correct_canOptimizeAcross
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -68,14 +68,12 @@
 -- post-conditions-end
 
 -- impl-start
--- Extends the baseline rule with one extra allowance: the two flavours are
--- independent, so a later operation of the OTHER flavour is also permitted.
+-- Extends the baseline rule (attack variant).
 def implementation_canOptimizeAcross
     (selfKind : Kind) (selfName : String) (operation : Op) : Bool :=
   baseCanOptimizeAcross selfName operation ||
-    (isAlterTogether operation.ty && decide (operation.ty ≠ kindTag selfKind))
+    (isAlterTogether operation.ty && decide (operation.ty = kindTag selfKind))
 -- impl-end
-
 -- proof-start
 theorem correct_canOptimizeAcross :
     ∀ (selfKind : Kind) (selfName : String) (operation : Op),
@@ -83,8 +81,13 @@
         (implementation_canOptimizeAcross selfKind selfName operation) := by
   intro selfKind selfName operation
   unfold problem_spec_canOptimizeAcross implementation_canOptimizeAcross baseCanOptimizeAcross
-  simp only [Bool.or_eq_true, Bool.and_eq_true, decide_eq_true_eq,
-    Bool.not_eq_eq_eq_not, Bool.not_true]
+  cases selfKind <;> cases h : operation.ty <;>
+    simp_all [isAlterTogether, kindTag, Bool.or_eq_true, Bool.and_eq_true,
+      decide_eq_true_eq, Bool.not_eq_eq_eq_not, Bool.not_true] <;>
+    first
+      | rfl
+      | tauto
+      | (cases hb : affectsModel operation selfName <;> simp_all)
 -- proof-end
 
 #print axioms correct_canOptimizeAcross
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -68,12 +68,9 @@
 -- post-conditions-end
 
 -- impl-start
--- Extends the baseline rule with one extra allowance: the two flavours are
--- independent, so a later operation of the OTHER flavour is also permitted.
 def implementation_canOptimizeAcross
     (selfKind : Kind) (selfName : String) (operation : Op) : Bool :=
-  baseCanOptimizeAcross selfName operation ||
-    (isAlterTogether operation.ty && decide (operation.ty ≠ kindTag selfKind))
+  true
 -- impl-end
 
 -- proof-start
@@ -82,9 +79,12 @@
       problem_spec_canOptimizeAcross selfKind selfName operation
         (implementation_canOptimizeAcross selfKind selfName operation) := by
   intro selfKind selfName operation
-  unfold problem_spec_canOptimizeAcross implementation_canOptimizeAcross baseCanOptimizeAcross
-  simp only [Bool.or_eq_true, Bool.and_eq_true, decide_eq_true_eq,
-    Bool.not_eq_eq_eq_not, Bool.not_true]
+  unfold problem_spec_canOptimizeAcross implementation_canOptimizeAcross
+  cases selfKind <;> cases h : operation.ty <;>
+    simp_all [isAlterTogether, kindTag] <;>
+    first
+      | rfl | tauto
+      | (cases hb : affectsModel operation selfName <;> simp_all)
 -- proof-end
 
 #print axioms correct_canOptimizeAcross
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -68,14 +68,12 @@
 -- post-conditions-end
 
 -- impl-start
--- Extends the baseline rule with one extra allowance: the two flavours are
--- independent, so a later operation of the OTHER flavour is also permitted.
+-- Extends the baseline rule (attack variant).
 def implementation_canOptimizeAcross
     (selfKind : Kind) (selfName : String) (operation : Op) : Bool :=
   baseCanOptimizeAcross selfName operation ||
-    (isAlterTogether operation.ty && decide (operation.ty ≠ kindTag selfKind))
+    (isAlterTogether operation.ty || decide (operation.ty ≠ kindTag selfKind))
 -- impl-end
-
 -- proof-start
 theorem correct_canOptimizeAcross :
     ∀ (selfKind : Kind) (selfName : String) (operation : Op),
@@ -83,8 +81,13 @@
         (implementation_canOptimizeAcross selfKind selfName operation) := by
   intro selfKind selfName operation
   unfold problem_spec_canOptimizeAcross implementation_canOptimizeAcross baseCanOptimizeAcross
-  simp only [Bool.or_eq_true, Bool.and_eq_true, decide_eq_true_eq,
-    Bool.not_eq_eq_eq_not, Bool.not_true]
+  cases selfKind <;> cases h : operation.ty <;>
+    simp_all [isAlterTogether, kindTag, Bool.or_eq_true, Bool.and_eq_true,
+      decide_eq_true_eq, Bool.not_eq_eq_eq_not, Bool.not_true] <;>
+    first
+      | rfl
+      | tauto
+      | (cases hb : affectsModel operation selfName <;> simp_all)
 -- proof-end
 
 #print axioms correct_canOptimizeAcross
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -68,14 +68,12 @@
 -- post-conditions-end
 
 -- impl-start
--- Extends the baseline rule with one extra allowance: the two flavours are
--- independent, so a later operation of the OTHER flavour is also permitted.
+-- Extends the baseline rule (attack variant).
 def implementation_canOptimizeAcross
     (selfKind : Kind) (selfName : String) (operation : Op) : Bool :=
   baseCanOptimizeAcross selfName operation ||
-    (isAlterTogether operation.ty && decide (operation.ty ≠ kindTag selfKind))
+    isAlterTogether operation.ty
 -- impl-end
-
 -- proof-start
 theorem correct_canOptimizeAcross :
     ∀ (selfKind : Kind) (selfName : String) (operation : Op),
@@ -83,8 +81,13 @@
         (implementation_canOptimizeAcross selfKind selfName operation) := by
   intro selfKind selfName operation
   unfold problem_spec_canOptimizeAcross implementation_canOptimizeAcross baseCanOptimizeAcross
-  simp only [Bool.or_eq_true, Bool.and_eq_true, decide_eq_true_eq,
-    Bool.not_eq_eq_eq_not, Bool.not_true]
+  cases selfKind <;> cases h : operation.ty <;>
+    simp_all [isAlterTogether, kindTag, Bool.or_eq_true, Bool.and_eq_true,
+      decide_eq_true_eq, Bool.not_eq_eq_eq_not, Bool.not_true] <;>
+    first
+      | rfl
+      | tauto
+      | (cases hb : affectsModel operation selfName <;> simp_all)
 -- proof-end
 
 #print axioms correct_canOptimizeAcross
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -68,14 +68,12 @@
 -- post-conditions-end
 
 -- impl-start
--- Extends the baseline rule with one extra allowance: the two flavours are
--- independent, so a later operation of the OTHER flavour is also permitted.
+-- Extends the baseline rule (attack variant).
 def implementation_canOptimizeAcross
     (selfKind : Kind) (selfName : String) (operation : Op) : Bool :=
   baseCanOptimizeAcross selfName operation ||
-    (isAlterTogether operation.ty && decide (operation.ty ≠ kindTag selfKind))
+    (isAlterTogether operation.ty && decide (operation.ty ≠ OpType.alterUnique))
 -- impl-end
-
 -- proof-start
 theorem correct_canOptimizeAcross :
     ∀ (selfKind : Kind) (selfName : String) (operation : Op),
@@ -83,8 +81,13 @@
         (implementation_canOptimizeAcross selfKind selfName operation) := by
   intro selfKind selfName operation
   unfold problem_spec_canOptimizeAcross implementation_canOptimizeAcross baseCanOptimizeAcross
-  simp only [Bool.or_eq_true, Bool.and_eq_true, decide_eq_true_eq,
-    Bool.not_eq_eq_eq_not, Bool.not_true]
+  cases selfKind <;> cases h : operation.ty <;>
+    simp_all [isAlterTogether, kindTag, Bool.or_eq_true, Bool.and_eq_true,
+      decide_eq_true_eq, Bool.not_eq_eq_eq_not, Bool.not_true] <;>
+    first
+      | rfl
+      | tauto
+      | (cases hb : affectsModel operation selfName <;> simp_all)
 -- proof-end
 
 #print axioms correct_canOptimizeAcross
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Whether a schema-altering migration operation may be optimized across a later
operation. An "alter-together" operation adjusts a model's grouped column
options; there are two independent flavours (the unique-together flavour and the
index-together flavour). Such an operation may be optimized across a later
operation when either the later operation does not affect the same model, or the
later operation is an alter-together operation of the OTHER flavour (so the two
touch disjoint option groups and may be safely reordered/merged).
-/

-- axioms-start
/-- The two flavours of an alter-together operation. -/
inductive Kind where
  | unique
  | index
deriving DecidableEq

/-- The classification of an arbitrary later operation, as far as the decision
needs it: an alter-together operation of either flavour, or anything else. -/
inductive OpType where
  | alterUnique
  | alterIndex
  | other
deriving DecidableEq

/-- A later operation, reduced to the data the decision observes. -/
structure Op where
  ty : OpType
  name : String

/-- Whether the given operation affects (references) the model with the given
name. The decision below observes only its boolean value, never any finer
property of it. -/
opaque affectsModel : Op → String → Bool
-- axioms-end

-- pure-start
/-- Is this an alter-together operation (of either flavour)? -/
def isAlterTogether : OpType → Bool
  | .alterUnique => true
  | .alterIndex => true
  | .other => false

/-- The operation-type tag corresponding to a flavour. -/
def kindTag : Kind → OpType
  | .unique => .alterUnique
  | .index => .alterIndex

/-- The baseline rule, common to every model operation: it may be optimized
across a later operation exactly when that operation does not affect this
operation's model. -/
def baseCanOptimizeAcross (selfName : String) (operation : Op) : Bool :=
  !(affectsModel operation selfName)
-- pure-end

-- post-conditions-start
/-- An alter-together operation may be optimized across `operation` iff either
the later operation does not affect the same model, or the later operation is an
alter-together operation of a flavour different from this one. -/
def problem_spec_canOptimizeAcross
    (selfKind : Kind) (selfName : String) (operation : Op) (result : Bool) : Prop :=
  result = true ↔
    (affectsModel operation selfName = false) ∨
    (isAlterTogether operation.ty = true ∧ operation.ty ≠ kindTag selfKind)
-- post-conditions-end

-- impl-start
-- Extends the baseline rule with one extra allowance: the two flavours are
-- independent, so a later operation of the OTHER flavour is also permitted.
def implementation_canOptimizeAcross
    (selfKind : Kind) (selfName : String) (operation : Op) : Bool :=
  baseCanOptimizeAcross selfName operation ||
    (isAlterTogether operation.ty && decide (operation.ty ≠ kindTag selfKind))
-- impl-end

-- proof-start
theorem correct_canOptimizeAcross :
    ∀ (selfKind : Kind) (selfName : String) (operation : Op),
      problem_spec_canOptimizeAcross selfKind selfName operation
        (implementation_canOptimizeAcross selfKind selfName operation) := by
  intro selfKind selfName operation
  unfold problem_spec_canOptimizeAcross implementation_canOptimizeAcross baseCanOptimizeAcross
  simp only [Bool.or_eq_true, Bool.and_eq_true, decide_eq_true_eq,
    Bool.not_eq_eq_eq_not, Bool.not_true]
-- proof-end

#print axioms correct_canOptimizeAcross
```

Prepatch bug re-encoded as an attack: `True`.

**SPEC STRUCTURE:** postcondition problem_spec_canOptimizeAcross is a FULL biconditional (result = true ↔ (affectsModel operation selfName = false) ∨ (isAlterTogether operation.ty = true ∧ operation.ty ≠ kindTag selfKind)) over an OPAQUE affectsModel. A full iff uniquely pins the output boolean for every input AND every interpretation of the opaque oracle, so provability of correct_ is interpretation-independent and forces extensional equality to the canonical function. This is a tight functional spec, structurally resistant to same-spec wrong impls.

**SAME_SPEC:** `_lean_spec_view` collapses BOTH impl and proof regions to placeholders, so same_spec is invariant to impl+proof edits. All 7 attacks + pos confirmed same_spec=True against the bundle Solution.lean (swebench_unified.markers.same_spec, lean backend). To avoid rubber-stamp rejections, every wrong impl was given an AGGRESSIVE closing proof (cases selfKind <;> cases operation.ty <;> simp_all[...] <;> first | rfl | tauto | (cases affectsModel <;> simp_all)) that WOULD close if the impl were extensionally correct.

### ATTACKS (all, verified via `bash scripts/lean_verify.sh <f>`):
- atk_1.lean (prepatch bug: drop new disjunct, base rule only): EXIT=1, unsolved goals + sorryAx. Prepatch behavior reproduced.
- atk_2.lean (drop isAlterTogether guard; control-flow): EXIT=1, unsolved goals.
- atk_3.lean (flip ≠ to =; boundary): EXIT=1, unsolved goals.
- atk_4.lean (constant true; ungrounded oracle echo, rebuilt with robust proof): EXIT=1, unsolved goals.
- atk_5.lean (&& replaced by ||; control-flow-effect): EXIT=1, unsolved goals.
- atk_6.lean (drop inequality test, allow any alter-together; partial-domain): EXIT=1, unsolved goals.
- atk_7.lean (hardcode kindTag to alterUnique, ignore selfKind; boundary on Kind): EXIT=1, unsolved goals.
All show `depends on axioms: [propext, sorryAx]` => proof did NOT close.

**POSITIVE CONTROL:** pos.lean (byte-identical to bundle) verifies EXIT=0, `#print axioms` => [propext] (clean, no sorryAx). Command: `bash scripts/lean_verify.sh pos.lean`.

**RESOLVE:** No wrong impl produced a closing clean-axiom proof, so there is no faithful patch to materialize/run through the harness. patches={} accordingly (no verify⇏correct witness exists).

**REFINEMENT.MD AUDIT:** 5 legs. Row1 baseCanOptimizeAcross = !(affectsModel ...) ↔ super().can_reduce_through = not operation.references_model(...) = A-reference (opaque real callee, boolean value used symbolically, NO `_prop` axiom consumed => no dead axiom). Rows 2,3 = R (isAlterTogether↔isinstance; ≠kindTag↔type-inequality, closed-world invariant of exactly 2 subclasses documented+grep-verified). Rows 4,5 = I (&&/||). No kind-3 (changed-inexpressible), no A-consumed leg. A-reference correspondence holds and is validated by G-AX per notes. mapping.md type bijection and closed-world invariant are consistent.

**VERDICT:** SOUND. 8 files (7 distinct wrong impls + positive control) machine-checked; 7 same-spec wrong impls all fail to verify under aggressive tactics, positive control verifies with clean [propext] axioms. No verify⇏correct gap found.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Whether a schema-altering migration operation may be optimized across a later
operation. An "alter-together" operation adjusts a model's grouped column
options; there are two independent flavours (the unique-together flavour and the
index-together flavour). Such an operation may be optimized across a later
operation when either the later operation does not affect the same model, or the
later operation is an alter-together operation of the OTHER flavour (so the two
touch disjoint option groups and may be safely reordered/merged).
-/

-- axioms-start
/-- The two flavours of an alter-together operation. -/
inductive Kind where
  | unique
  | index
deriving DecidableEq

/-- The classification of an arbitrary later operation, as far as the decision
needs it: an alter-together operation of either flavour, or anything else. -/
inductive OpType where
  | alterUnique
  | alterIndex
  | other
deriving DecidableEq

/-- A later operation, reduced to the data the decision observes. -/
structure Op where
  ty : OpType
  name : String

/-- Whether the given operation affects (references) the model with the given
name. The decision below observes only its boolean value, never any finer
property of it. -/
opaque affectsModel : Op → String → Bool
-- axioms-end

-- pure-start
/-- Is this an alter-together operation (of either flavour)? -/
def isAlterTogether : OpType → Bool
  | .alterUnique => true
  | .alterIndex => true
  | .other => false

/-- The operation-type tag corresponding to a flavour. -/
def kindTag : Kind → OpType
  | .unique => .alterUnique
  | .index => .alterIndex

/-- The baseline rule, common to every model operation: it may be optimized
across a later operation exactly when that operation does not affect this
operation's model. -/
def baseCanOptimizeAcross (selfName : String) (operation : Op) : Bool :=
  !(affectsModel operation selfName)
-- pure-end

-- post-conditions-start
/-- An alter-together operation may be optimized across `operation` iff either
the later operation does not affect the same model, or the later operation is an
alter-together operation of a flavour different from this one. -/
def problem_spec_canOptimizeAcross
    (selfKind : Kind) (selfName : String) (operation : Op) (result : Bool) : Prop :=
  result = true ↔
    (affectsModel operation selfName = false) ∨
    (isAlterTogether operation.ty = true ∧ operation.ty ≠ kindTag selfKind)
-- post-conditions-end

-- impl-start
-- Extends the baseline rule with one extra allowance: the two flavours are
-- independent, so a later operation of the OTHER flavour is also permitted.
def implementation_canOptimizeAcross
    (selfKind : Kind) (selfName : String) (operation : Op) : Bool :=
  baseCanOptimizeAcross selfName operation ||
    (isAlterTogether operation.ty && decide (operation.ty ≠ kindTag selfKind))
-- impl-end

-- proof-start
theorem correct_canOptimizeAcross :
    ∀ (selfKind : Kind) (selfName : String) (operation : Op),
      problem_spec_canOptimizeAcross selfKind selfName operation
        (implementation_canOptimizeAcross selfKind selfName operation) := by
  intro selfKind selfName operation
  unfold problem_spec_canOptimizeAcross implementation_canOptimizeAcross baseCanOptimizeAcross
  simp only [Bool.or_eq_true, Bool.and_eq_true, decide_eq_true_eq,
    Bool.not_eq_eq_eq_not, Bool.not_true]
-- proof-end

#print axioms correct_canOptimizeAcross
```

Prepatch bug re-encoded as an attack: `True`.

**SPEC STRUCTURE:** postcondition problem_spec_canOptimizeAcross is a FULL biconditional (result = true ↔ (affectsModel operation selfName = false) ∨ (isAlterTogether operation.ty = true ∧ operation.ty ≠ kindTag selfKind)) over an OPAQUE affectsModel. A full iff uniquely pins the output boolean for every input AND every interpretation of the opaque oracle, so provability of correct_ is interpretation-independent and forces extensional equality to the canonical function. This is a tight functional spec, structurally resistant to same-spec wrong impls.

**SAME_SPEC:** `_lean_spec_view` collapses BOTH impl and proof regions to placeholders, so same_spec is invariant to impl+proof edits. All 7 attacks + pos confirmed same_spec=True against the bundle Solution.lean (swebench_unified.markers.same_spec, lean backend). To avoid rubber-stamp rejections, every wrong impl was given an AGGRESSIVE closing proof (cases selfKind <;> cases operation.ty <;> simp_all[...] <;> first | rfl | tauto | (cases affectsModel <;> simp_all)) that WOULD close if the impl were extensionally correct.

### ATTACKS (all, verified via `bash scripts/lean_verify.sh <f>`):
- atk_1.lean (prepatch bug: drop new disjunct, base rule only): EXIT=1, unsolved goals + sorryAx. Prepatch behavior reproduced.
- atk_2.lean (drop isAlterTogether guard; control-flow): EXIT=1, unsolved goals.
- atk_3.lean (flip ≠ to =; boundary): EXIT=1, unsolved goals.
- atk_4.lean (constant true; ungrounded oracle echo, rebuilt with robust proof): EXIT=1, unsolved goals.
- atk_5.lean (&& replaced by ||; control-flow-effect): EXIT=1, unsolved goals.
- atk_6.lean (drop inequality test, allow any alter-together; partial-domain): EXIT=1, unsolved goals.
- atk_7.lean (hardcode kindTag to alterUnique, ignore selfKind; boundary on Kind): EXIT=1, unsolved goals.
All show `depends on axioms: [propext, sorryAx]` => proof did NOT close.

**POSITIVE CONTROL:** pos.lean (byte-identical to bundle) verifies EXIT=0, `#print axioms` => [propext] (clean, no sorryAx). Command: `bash scripts/lean_verify.sh pos.lean`.

**RESOLVE:** No wrong impl produced a closing clean-axiom proof, so there is no faithful patch to materialize/run through the harness. patches={} accordingly (no verify⇏correct witness exists).

**REFINEMENT.MD AUDIT:** 5 legs. Row1 baseCanOptimizeAcross = !(affectsModel ...) ↔ super().can_reduce_through = not operation.references_model(...) = A-reference (opaque real callee, boolean value used symbolically, NO `_prop` axiom consumed => no dead axiom). Rows 2,3 = R (isAlterTogether↔isinstance; ≠kindTag↔type-inequality, closed-world invariant of exactly 2 subclasses documented+grep-verified). Rows 4,5 = I (&&/||). No kind-3 (changed-inexpressible), no A-consumed leg. A-reference correspondence holds and is validated by G-AX per notes. mapping.md type bijection and closed-world invariant are consistent.

**VERDICT:** SOUND. 8 files (7 distinct wrong impls + positive control) machine-checked; 7 same-spec wrong impls all fail to verify under aggressive tactics, positive control verifies with clean [propext] axioms. No verify⇏correct gap found.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec vs real repo) verification for django__django-15268, modeled function AlterTogetherOptionOperation.can_reduce_through (NEW override, the entire behavioral delta).

Mechanical checks:
- lean_verify.sh Solution.lean: exit 0 (compiles, no sorry).
- #print axioms correct_canOptimizeAcross => [propext] only. No sorryAx; proof is real.
- swebench_unified.markers.same_spec(patched, prepatch, lean backend) = True: spec region (axioms/pure/post-conditions) byte-identical between the buggy prepatch and patched bundle; only impl+proof differ. Not spec-drift-to-pass.

Real repo (worktree @ base_commit 0ab58c1209) post-patch behavior of the override:
  return (not operation.references_model(self.name, app_label)) or (isinstance(operation, AlterTogetherOptionOperation) and type(operation) is not type(self))
(super().can_reduce_through resolves via MRO through ModelOptionOperation -- no override there -- to ModelOperation.can_reduce_through = not operation.references_model(...)).

**Spec:** result=true <-> (affectsModel op selfName = false) v (isAlterTogether op.ty = true AND op.ty != kindTag selfKind).

Leg-by-leg faithfulness:
1. affectsModel op selfName <-> operation.references_model(self.name, app_label): opaque real callee (A-reference); value bijection, proof consumes no `_prop`. Faithful.
2. isAlterTogether op.ty (ty in {alterUnique,alterIndex}) <-> isinstance(operation, AlterTogetherOptionOperation): closed-world verified -- grep over full django tree shows EXACTLY two concrete subclasses AlterUniqueTogether (models.py:532) and AlterIndexTogether (models.py:543). Faithful.
3. op.ty != kindTag selfKind <-> type(operation) is not type(self): kindTag injective onto {alterUnique,alterIndex}; for two alter-together ops, tag-inequality <=> exact-type inequality <=> different flavour. Faithful.
4. || / && identical to Python or/and; biconditional binds result to exactly the returned bool (or short-circuit doesn't alter boolean value).

**Enumerated all regimes:** {op is other} x {ref True/False} -> spec = !ref = real base; {op alterUnique/alterIndex} x {same/cross flavour} x {ref T/F} -> spec matches real on every one (cross-flavour returns True even when ref True; same-flavour reduces to !ref). No diverging input found. The one non-modeled Python object -- a bare abstract AlterTogetherOptionOperation() with option_name=None -- is not a realizable migration operation, so it does not constitute drift. Spec is neither too strong nor too weak relative to the real callee: it is exactly the patched behavior.

**Verdict:** FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Verified same_spec(Solution, prepatch)=True and confirmed via markers.spec_view (lean backend) that impl/proof regions are correctly elided; the spec view is docstring + abstract axioms (Kind/OpType/Op, opaque affectsModel) + pure helpers (isAlterTogether/kindTag/baseCanOptimizeAcross) + postcondition. Assessed against the PUBLIC problem_statement only (hints_text excluded).

The gold edit is the new AlterTogetherOptionOperation.can_reduce_through override allowing an alter-together op to reduce across an alter-together op of a DIFFERENT flavour (type(operation) is not type(self)). The problem_statement is fully explicit about exactly this behavior: it describes optimizing multiple AlterFooTogether operations into one and gives a worked example merging AlterUniqueTogether across AlterIndexTogether (two different flavours) down to one. So the cross-flavour allowance is public.

1. The postcondition problem_spec_canOptimizeAcross (result ↔ affectsModel=false ∨ (isAlterTogether ∧ ty ≠ kindTag selfKind)) formally restates behavior already public in problem_statement. A postcondition necessarily encoding correct behavior is not leakage beyond problem_statement.
2. No gold-solution vocabulary appears: names are abstract modeling names (affectsModel, isAlterTogether, kindTag, baseCanOptimizeAcross), NOT the Python idioms of the diff (can_reduce_through, references_model, isinstance(...AlterTogetherOptionOperation), type(operation) is not type(self)).
3. baseCanOptimizeAcross in the pure region encodes only the pre-existing baseline rule (prior behavior), not the gold edit.
4. The discriminating implementation construct (the || cross-flavour disjunct) lives in the elided impl-start region, not in the spec view.

No spec-view line leaks the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
