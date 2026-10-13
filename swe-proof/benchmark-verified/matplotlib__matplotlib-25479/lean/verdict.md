# P2 adversarial audit — matplotlib__matplotlib-25479

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -65,6 +65,8 @@
 
 -- impl-start
 def implementation_colormapEq (a b : Colormap) : Bool := Id.run do
+  if a.name != b.name then
+    return false
   if a.flag != b.flag then
     return false
   return a.table == b.table
@@ -76,7 +78,10 @@
   intro a b
   unfold problem_spec_colormapEq implementation_colormapEq
   simp only [Id.run, bind, bne]
-  by_cases h : a.flag == b.flag <;> simp [pure, h]
+  first
+    | (by_cases h : a.flag == b.flag <;> simp [pure, h])
+    | simp_all
+    | decide
 -- proof-end
 
 -- post-conditions-start
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -64,10 +64,7 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_colormapEq (a b : Colormap) : Bool := Id.run do
-  if a.flag != b.flag then
-    return false
-  return a.table == b.table
+def implementation_colormapEq (a b : Colormap) : Bool := true
 -- impl-end
 
 -- proof-start
@@ -76,7 +73,10 @@
   intro a b
   unfold problem_spec_colormapEq implementation_colormapEq
   simp only [Id.run, bind, bne]
-  by_cases h : a.flag == b.flag <;> simp [pure, h]
+  first
+    | (by_cases h : a.flag == b.flag <;> simp [pure, h])
+    | simp_all
+    | decide
 -- proof-end
 
 -- post-conditions-start
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -64,10 +64,7 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_colormapEq (a b : Colormap) : Bool := Id.run do
-  if a.flag != b.flag then
-    return false
-  return a.table == b.table
+def implementation_colormapEq (a b : Colormap) : Bool := a.flag == b.flag
 -- impl-end
 
 -- proof-start
@@ -76,7 +73,10 @@
   intro a b
   unfold problem_spec_colormapEq implementation_colormapEq
   simp only [Id.run, bind, bne]
-  by_cases h : a.flag == b.flag <;> simp [pure, h]
+  first
+    | (by_cases h : a.flag == b.flag <;> simp [pure, h])
+    | simp_all
+    | decide
 -- proof-end
 
 -- post-conditions-start
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -64,10 +64,7 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_colormapEq (a b : Colormap) : Bool := Id.run do
-  if a.flag != b.flag then
-    return false
-  return a.table == b.table
+def implementation_colormapEq (a b : Colormap) : Bool := (a.flag == b.flag) || (a.table == b.table)
 -- impl-end
 
 -- proof-start
@@ -76,7 +73,10 @@
   intro a b
   unfold problem_spec_colormapEq implementation_colormapEq
   simp only [Id.run, bind, bne]
-  by_cases h : a.flag == b.flag <;> simp [pure, h]
+  first
+    | (by_cases h : a.flag == b.flag <;> simp [pure, h])
+    | simp_all
+    | decide
 -- proof-end
 
 -- post-conditions-start
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -90,14 +90,7 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_register (name : String) (cmap : Colormap) : Colormap := Id.run do
-  -- A duplicate of the colormap is what gets stored (structural copy).
-  let mut stored := cmap
-  -- The stored colormap should report the registration name, even when its own
-  -- display name differs.
-  if stored.name != name then
-    stored := { stored with name := name }
-  return stored
+def implementation_register (name : String) (cmap : Colormap) : Colormap := cmap
 -- impl-end
 
 -- proof-start
@@ -106,6 +99,8 @@
   intro name cmap
   unfold problem_spec_register implementation_register
   simp only [Id.run, bind, bne]
-  by_cases h : cmap.name == name <;> simp [pure, h]
-  exact beq_iff_eq.mp h
+  first
+    | (by_cases h : cmap.name == name <;> simp_all [pure, h])
+    | simp_all
+    | (refine ⟨?_, ?_, ?_⟩ <;> rfl)
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -90,14 +90,8 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_register (name : String) (cmap : Colormap) : Colormap := Id.run do
-  -- A duplicate of the colormap is what gets stored (structural copy).
-  let mut stored := cmap
-  -- The stored colormap should report the registration name, even when its own
-  -- display name differs.
-  if stored.name != name then
-    stored := { stored with name := name }
-  return stored
+def implementation_register (name : String) (cmap : Colormap) : Colormap :=
+  { name := name, flag := cmap.flag, table := [] }
 -- impl-end
 
 -- proof-start
@@ -106,6 +100,8 @@
   intro name cmap
   unfold problem_spec_register implementation_register
   simp only [Id.run, bind, bne]
-  by_cases h : cmap.name == name <;> simp [pure, h]
-  exact beq_iff_eq.mp h
+  first
+    | (by_cases h : cmap.name == name <;> simp_all [pure, h])
+    | simp_all
+    | (refine ⟨?_, ?_, ?_⟩ <;> rfl)
 -- proof-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -90,14 +90,8 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_register (name : String) (cmap : Colormap) : Colormap := Id.run do
-  -- A duplicate of the colormap is what gets stored (structural copy).
-  let mut stored := cmap
-  -- The stored colormap should report the registration name, even when its own
-  -- display name differs.
-  if stored.name != name then
-    stored := { stored with name := name }
-  return stored
+def implementation_register (name : String) (cmap : Colormap) : Colormap :=
+  { name := name, flag := cmap.flag, table := cmap.table.reverse }
 -- impl-end
 
 -- proof-start
@@ -106,6 +100,8 @@
   intro name cmap
   unfold problem_spec_register implementation_register
   simp only [Id.run, bind, bne]
-  by_cases h : cmap.name == name <;> simp [pure, h]
-  exact beq_iff_eq.mp h
+  first
+    | (by_cases h : cmap.name == name <;> simp_all [pure, h])
+    | simp_all
+    | (refine ⟨?_, ?_, ?_⟩ <;> rfl)
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Colormap identity and name registration.

A colormap carries a human-readable *display name* together with the data that
determines how it maps values to colors: a small auxiliary attribute and a
lookup table. Two behaviors are modeled.

* **Equality of colormaps.** Two colormaps are considered equal exactly when
  their color-determining content matches — that is, when their auxiliary
  attribute is equal AND their lookup tables are equal, element for element. The
  display name is *not* part of this comparison: two colormaps that differ only
  in their display name are equal. (Equality is decided purely by the
  color-producing content; relabelling a colormap does not change what it is.)

* **Registering a colormap under a name.** When a colormap is stored in the
  registry under a chosen lookup name, the stored colormap must carry that very
  name as its display name, so that a later lookup by the registered name yields
  a colormap that reports the name it was registered under. All of the stored
  colormap's color-determining content (the auxiliary attribute and the lookup
  table) is that of the colormap being registered — only the display name is set
  to the registration name.

The two behaviors interact: after registering a colormap under a name different
from its original display name, the looked-up colormap both reports the
registration name and compares equal to the colormap that was registered.
-/

-- axioms-start
-- No UNCHANGED callee is invoked by the modeled behaviors. Duplicating a
-- colormap before storing it is structural (it preserves every modeled field),
-- and comparing two lookup tables is ordinary element-wise list equality; both
-- are modeled directly below rather than axiomatized. Hence no `opaque` callee
-- and no consumed `_prop` axiom.
-- axioms-end

-- pure-start
/-- A colormap, modeled by the fields that the modeled behaviors touch:
* `name`   — the display name (a string);
* `flag`   — a small comparable auxiliary attribute that participates in equality
             (modeled as an integer code; see mapping.md for the bijection);
* `table`  — the lookup table that participates in equality, compared as a
             whole (modeled as a list of rows of integer entries, so that two
             tables compare equal exactly when they have the same shape and
             agree entry-for-entry).
Other colormap fields are irrelevant to the modeled behaviors and omitted. -/
structure Colormap where
  name  : String
  flag  : Int
  table : List (List Int)
deriving Repr, DecidableEq
-- pure-end

-- post-conditions-start
/-- Equality of two colormaps: the result is `true` exactly when the
color-determining content of the two colormaps agrees — their auxiliary
attribute is equal and their lookup tables are equal element-wise. The display
name does not enter the comparison. The result is fully pinned by the inputs:
nothing about it is left unconstrained. -/
def problem_spec_colormapEq (a b : Colormap) (result : Bool) : Prop :=
  result = ((a.flag == b.flag) && (a.table == b.table))
-- post-conditions-end

-- impl-start
def implementation_colormapEq (a b : Colormap) : Bool := Id.run do
  if a.flag != b.flag then
    return false
  return a.table == b.table
-- impl-end

-- proof-start
theorem correct_colormapEq : ∀ a b : Colormap,
    problem_spec_colormapEq a b (implementation_colormapEq a b) := by
  intro a b
  unfold problem_spec_colormapEq implementation_colormapEq
  simp only [Id.run, bind, bne]
  by_cases h : a.flag == b.flag <;> simp [pure, h]
-- proof-end

-- post-conditions-start
/-- Storing a colormap under a registration name: the stored colormap reports the
registration name as its display name, while its color-determining content (the
auxiliary attribute and the lookup table) is exactly that of the colormap being
registered. Every output component is pinned to its input: the name to the
registration name, the remaining content to the registered colormap. -/
def problem_spec_register (name : String) (cmap : Colormap) (result : Colormap) : Prop :=
  result.name = name ∧ result.flag = cmap.flag ∧ result.table = cmap.table
-- post-conditions-end

-- impl-start
def implementation_register (name : String) (cmap : Colormap) : Colormap := Id.run do
  -- A duplicate of the colormap is what gets stored (structural copy).
  let mut stored := cmap
  -- The stored colormap should report the registration name, even when its own
  -- display name differs.
  if stored.name != name then
    stored := { stored with name := name }
  return stored
-- impl-end

-- proof-start
theorem correct_register : ∀ (name : String) (cmap : Colormap),
    problem_spec_register name cmap (implementation_register name cmap) := by
  intro name cmap
  unfold problem_spec_register implementation_register
  simp only [Id.run, bind, bne]
  by_cases h : cmap.name == name <;> simp [pure, h]
  exact beq_iff_eq.mp h
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Both specs are FULLY-PINNED equalities: problem_spec_colormapEq pins result = ((a.flag==b.flag) && (a.table==b.table)); problem_spec_register pins all 3 fields of the 3-field Colormap (result.name=name ∧ result.flag=cmap.flag ∧ result.table=cmap.table). Any verifying impl must therefore be functionally identical to the spec RHS. No axioms/opaque callees exist (refinement all R/I), so there are NO A-legs to attack; correspondence is vacuous.

Same-spec confirmed True for all 7 attacks + positive_control via swebench_unified.markers.same_spec (lean backend). spec_view collapses BOTH impl and proof regions, so impl+proof were edited while axioms/pure/pre/post kept byte-identical.

7 DISTINCT wrong impls, each given a genuine closing-proof ATTEMPT (gold-style + simp_all/decide/refine fallbacks). ALL fail lean_verify.sh (exit 1) with genuine unsolved-goal / simp-no-progress errors — no candidate closed, so protocol step 2 (materialize faithful patch + run_resolve) has NO candidates to run:
  atk_1 (colormapEq reintroduces a.name!=b.name guard = PREPATCH bug): exit 1, unsolved goal ¬a.name=b.name → ¬a.table=b.table.
  atk_2 (colormapEq ≡ true, degenerate/const): exit 1, simp made no progress.
  atk_3 (colormapEq drops table term, only a.flag==b.flag): exit 1, simp made no progress.
  atk_4 (colormapEq uses || instead of && — control-flow-effect): exit 1, simp made no progress.
  atk_5 (register omits name-propagation tail = PREPATCH_2 bug): exit 1, unsolved goal False under ¬cmap.name=name.
  atk_6 (register corrupts table:=[] — boundary): exit 1, unsolved goal cmap.table=[].
  atk_7 (register reverses table rows — transform/ungrounded): exit 1, unsolved goal cmap.table.reverse=cmap.table.

Commands: bash scripts/lean_verify.sh <atk>.lean (run concurrently ≤4/batch). Results: atk_1..7 all EXIT=1; positive_control EXIT=0.

Positive control = gold Solution.lean copy: verifies (exit 0). #print axioms both theorems => 'correct_colormapEq' depends on axioms: [propext]; 'correct_register' depends on axioms: [propext] — clean, no sorry/sorryAx, no Classical/Quot beyond propext (propext is standard/clean).

prepatch_reproduced=true: the two documented prepatch bugs (atk_1 name-guard, atk_5 omitted name tail) were re-encoded and correctly REJECTED by the spec (fail to verify), confirming verify catches exactly the gold fix.

refinement.md audit: 3 legs for colormapEq (R, R, R/I) + 3 legs for register (R, I, R). Every leg is R or I — NO kind-3 (changed-inexpressible), NO A-consumed / A-reference, conf_skip=false consistent with executable impl content. __copy__ modeled as structural identity (R), np.array_equal modeled deeply as List(List Int) equality capturing shape+entries (R/I) — both faithful, not axiomatized. No axiom correspondence to audit. Refinement is faithful.

verify⇏correct NOT demonstrated: no wrong impl achieved a closing clean-axiom proof, so verify⇒correct holds for the tested attack surface. Spec is sound.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Colormap identity and name registration.

A colormap carries a human-readable *display name* together with the data that
determines how it maps values to colors: a small auxiliary attribute and a
lookup table. Two behaviors are modeled.

* **Equality of colormaps.** Two colormaps are considered equal exactly when
  their color-determining content matches — that is, when their auxiliary
  attribute is equal AND their lookup tables are equal, element for element. The
  display name is *not* part of this comparison: two colormaps that differ only
  in their display name are equal. (Equality is decided purely by the
  color-producing content; relabelling a colormap does not change what it is.)

* **Registering a colormap under a name.** When a colormap is stored in the
  registry under a chosen lookup name, the stored colormap must carry that very
  name as its display name, so that a later lookup by the registered name yields
  a colormap that reports the name it was registered under. All of the stored
  colormap's color-determining content (the auxiliary attribute and the lookup
  table) is that of the colormap being registered — only the display name is set
  to the registration name.

The two behaviors interact: after registering a colormap under a name different
from its original display name, the looked-up colormap both reports the
registration name and compares equal to the colormap that was registered.
-/

-- axioms-start
-- No UNCHANGED callee is invoked by the modeled behaviors. Duplicating a
-- colormap before storing it is structural (it preserves every modeled field),
-- and comparing two lookup tables is ordinary element-wise list equality; both
-- are modeled directly below rather than axiomatized. Hence no `opaque` callee
-- and no consumed `_prop` axiom.
-- axioms-end

-- pure-start
/-- A colormap, modeled by the fields that the modeled behaviors touch:
* `name`   — the display name (a string);
* `flag`   — a small comparable auxiliary attribute that participates in equality
             (modeled as an integer code; see mapping.md for the bijection);
* `table`  — the lookup table that participates in equality, compared as a
             whole (modeled as a list of rows of integer entries, so that two
             tables compare equal exactly when they have the same shape and
             agree entry-for-entry).
Other colormap fields are irrelevant to the modeled behaviors and omitted. -/
structure Colormap where
  name  : String
  flag  : Int
  table : List (List Int)
deriving Repr, DecidableEq
-- pure-end

-- post-conditions-start
/-- Equality of two colormaps: the result is `true` exactly when the
color-determining content of the two colormaps agrees — their auxiliary
attribute is equal and their lookup tables are equal element-wise. The display
name does not enter the comparison. The result is fully pinned by the inputs:
nothing about it is left unconstrained. -/
def problem_spec_colormapEq (a b : Colormap) (result : Bool) : Prop :=
  result = ((a.flag == b.flag) && (a.table == b.table))
-- post-conditions-end

-- impl-start
def implementation_colormapEq (a b : Colormap) : Bool := Id.run do
  if a.flag != b.flag then
    return false
  return a.table == b.table
-- impl-end

-- proof-start
theorem correct_colormapEq : ∀ a b : Colormap,
    problem_spec_colormapEq a b (implementation_colormapEq a b) := by
  intro a b
  unfold problem_spec_colormapEq implementation_colormapEq
  simp only [Id.run, bind, bne]
  by_cases h : a.flag == b.flag <;> simp [pure, h]
-- proof-end

-- post-conditions-start
/-- Storing a colormap under a registration name: the stored colormap reports the
registration name as its display name, while its color-determining content (the
auxiliary attribute and the lookup table) is exactly that of the colormap being
registered. Every output component is pinned to its input: the name to the
registration name, the remaining content to the registered colormap. -/
def problem_spec_register (name : String) (cmap : Colormap) (result : Colormap) : Prop :=
  result.name = name ∧ result.flag = cmap.flag ∧ result.table = cmap.table
-- post-conditions-end

-- impl-start
def implementation_register (name : String) (cmap : Colormap) : Colormap := Id.run do
  -- A duplicate of the colormap is what gets stored (structural copy).
  let mut stored := cmap
  -- The stored colormap should report the registration name, even when its own
  -- display name differs.
  if stored.name != name then
    stored := { stored with name := name }
  return stored
-- impl-end

-- proof-start
theorem correct_register : ∀ (name : String) (cmap : Colormap),
    problem_spec_register name cmap (implementation_register name cmap) := by
  intro name cmap
  unfold problem_spec_register implementation_register
  simp only [Id.run, bind, bne]
  by_cases h : cmap.name == name <;> simp [pure, h]
  exact beq_iff_eq.mp h
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Both specs are FULLY-PINNED equalities: problem_spec_colormapEq pins result = ((a.flag==b.flag) && (a.table==b.table)); problem_spec_register pins all 3 fields of the 3-field Colormap (result.name=name ∧ result.flag=cmap.flag ∧ result.table=cmap.table). Any verifying impl must therefore be functionally identical to the spec RHS. No axioms/opaque callees exist (refinement all R/I), so there are NO A-legs to attack; correspondence is vacuous.

Same-spec confirmed True for all 7 attacks + positive_control via swebench_unified.markers.same_spec (lean backend). spec_view collapses BOTH impl and proof regions, so impl+proof were edited while axioms/pure/pre/post kept byte-identical.

7 DISTINCT wrong impls, each given a genuine closing-proof ATTEMPT (gold-style + simp_all/decide/refine fallbacks). ALL fail lean_verify.sh (exit 1) with genuine unsolved-goal / simp-no-progress errors — no candidate closed, so protocol step 2 (materialize faithful patch + run_resolve) has NO candidates to run:
  atk_1 (colormapEq reintroduces a.name!=b.name guard = PREPATCH bug): exit 1, unsolved goal ¬a.name=b.name → ¬a.table=b.table.
  atk_2 (colormapEq ≡ true, degenerate/const): exit 1, simp made no progress.
  atk_3 (colormapEq drops table term, only a.flag==b.flag): exit 1, simp made no progress.
  atk_4 (colormapEq uses || instead of && — control-flow-effect): exit 1, simp made no progress.
  atk_5 (register omits name-propagation tail = PREPATCH_2 bug): exit 1, unsolved goal False under ¬cmap.name=name.
  atk_6 (register corrupts table:=[] — boundary): exit 1, unsolved goal cmap.table=[].
  atk_7 (register reverses table rows — transform/ungrounded): exit 1, unsolved goal cmap.table.reverse=cmap.table.

Commands: bash scripts/lean_verify.sh <atk>.lean (run concurrently ≤4/batch). Results: atk_1..7 all EXIT=1; positive_control EXIT=0.

Positive control = gold Solution.lean copy: verifies (exit 0). #print axioms both theorems => 'correct_colormapEq' depends on axioms: [propext]; 'correct_register' depends on axioms: [propext] — clean, no sorry/sorryAx, no Classical/Quot beyond propext (propext is standard/clean).

prepatch_reproduced=true: the two documented prepatch bugs (atk_1 name-guard, atk_5 omitted name tail) were re-encoded and correctly REJECTED by the spec (fail to verify), confirming verify catches exactly the gold fix.

refinement.md audit: 3 legs for colormapEq (R, R, R/I) + 3 legs for register (R, I, R). Every leg is R or I — NO kind-3 (changed-inexpressible), NO A-consumed / A-reference, conf_skip=false consistent with executable impl content. __copy__ modeled as structural identity (R), np.array_equal modeled deeply as List(List Int) equality capturing shape+entries (R/I) — both faithful, not axiomatized. No axiom correspondence to audit. Refinement is faithful.

verify⇏correct NOT demonstrated: no wrong impl achieved a closing clean-axiom proof, so verify⇒correct holds for the tested attack surface. Spec is sound.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack on matplotlib__matplotlib-25479 (lean). Verified against exact base_commit 7fdf772201e4c9bafbc16dfac23b5472d6a53fa2 sources (fetched lib/matplotlib/colors.py and cm.py from GitHub raw at that commit).

Mechanical checks all pass:
- same_spec (lean LanguageTables): spec regions byte-identical across Solution.lean vs Solution_prepatch.lean AND Solution_prepatch_2.lean = True.
- lean_verify.sh Solution.lean = exit 0 (compiles, no sorry).
- #print axioms correct_colormapEq -> [propext]; #print axioms correct_register -> [propext]. No sorryAx; proofs genuine.

Faithfulness analysis of the two modeled triples:

(1) colormapEq <-> post-patch Colormap.__eq__ (colors.py:775-789). Real post-patch: returns False if not isinstance OR self.colorbar_extend != other.colorbar_extend, else np.array_equal(self._lut, other._lut) after _init(). The name disjunct is REMOVED by the gold patch, so the result depends only on colorbar_extend and the lut. Model: problem_spec_colormapEq result = ((a.flag==b.flag) && (a.table==b.table)). flag:Int is an injective code for colorbar_extend (bool) and only ==/!= is observed -> faithful. np.array_equal is shape-then-elementwise; List (List Int) == captures both 2D shape (row count + each row width) and entries, so a.table==b.table <-> np.array_equal (the differently-shaped -> False case, exercised by PASS_TO_PASS test_colormap_equals cm_copy._lut[:10,:], is preserved). No diverging input on the modeled bool result.

(2) register <-> post-patch ColormapRegistry.register store+name tail (cm.py:143-151). Real post-patch: self._cmaps[name] = cmap.copy(); if self._cmaps[name].name != name: self._cmaps[name].name = name. __copy__ does __dict__.update + np.copy(_lut), preserving name/colorbar_extend/_lut i.e. identity on modeled fields. Model pins result.name=name, result.flag=cmap.flag, result.table=cmap.table. Faithful on the modeled (explicit-name, successful-store) path.

Abstraction boundaries considered as candidate break inputs and rejected (explicitly declared out of scope in mapping.md/refinement.md, not in-scope drift):
- register with name=None or name="": real computes name = name or cmap.name; the model takes the RESOLVED registration name as its String binder, so name-resolution is out of the modeled scope, not a disagreement within it.
- ValueError / force / builtin-override paths: state-dependent raises, explicitly unmodeled; the model abstracts the success path (targeted FAIL_TO_PASS test_set_cmap_mismatched_name registers under an explicit differing name -> exactly the modeled path).
None of these lie within the modeled behavior, so there is no input on which the modeled function disagrees with the real callee for the behavior it claims to model. Spec is a faithful (and not-too-strong) abstraction.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Leakage judged over the spec view (spec_view projection: prologue docstring + axioms/pure/post-conditions regions; impl and proof regions are elided to placeholders), against the public problem_statement ONLY (not hints_text).

Mechanical screen: leakage.screen() PASSES with zero hard failures. No diff markers, no reproduced gold-patch line (>=8 chars), no patched file path (lib/matplotlib/{cm,colors}.py) or dotted module, no narration tokens (bug/fix/previously/removed/...). Distinctive patched symbols are {copy, register}: neither appears verbatim in a spec-view identifier or comment, and 'register' is in any case already public in the problem_statement. Both prepatch variants are same_spec==True (byte-identical spec view), so the discrimination lives entirely in the elided impl/proof, not the spec.

Semantic gold-reconstruction check:
- Gold part 1 (__eq__ drops the self.name!=other.name disjunct so equality ignores display name): the spec states the forward contract 'the display name is not part of this comparison; two colormaps differing only in display name are equal'. This is the intended behavior stated at the model level (structure Colormap with name/flag/table). It never names __eq__, colorbar_extend, _lut, does not present the behavior as a change/delta, and does not reveal it was an edit or where. Stating a modeled function's contract is a spec's proper job; a solver still must author the Lean impl + proof.
- Gold part 2 (register propagates the registration name onto the stored copy): this behavior is ALREADY PUBLIC in problem_statement, which describes registering a cmap under a name different from its own .name and expecting lookup by the registered name. The spec's abstract restatement adds no edit-localization beyond the public task.

The spec describes target behavior abstractly, not the gold patch. No spec-view line reconstructs the gold edit beyond the public problem_statement. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
