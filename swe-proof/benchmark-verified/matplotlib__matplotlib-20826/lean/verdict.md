# P2 adversarial audit — matplotlib__matplotlib-20826

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
None found. No same-spec wrong implementation produced a closing, clean-axiom proof, so there is no verifying-but-non-resolving counterexample. The spec problem_spec_clear is a COMPLETE extensional characterization of the result pair: it pins result.major gridKey = some (majorGridOn g w), result.minor gridKey = some (minorGridOn g w), AND (forall k != gridKey, result.major k = s.major k) plus the minor analogue. Both output maps are fixed pointwise at every key; nothing is left free. Any impl whose correct_clear closes must therefore agree with the fix at every point => behaviorally identical => resolves. verify => correct holds.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -82,8 +82,10 @@
 -- impl-start
 def implementation_clear
     (s : TickKwPair) (gridEnabled : Bool) (which : String) : TickKwPair := Id.run do
-  let mut major := s.major
-  let mut minor := s.minor
+  -- WRONG: empties both tables first (prepatch dict.clear() behaviour), dropping
+  -- every previously recorded entry.
+  let mut major : TickKw := fun _ => none
+  let mut minor : TickKw := fun _ => none
   major := Function.update major gridKey (some (majorGridOn gridEnabled which))
   minor := Function.update minor gridKey (some (minorGridOn gridEnabled which))
   return ⟨major, minor⟩
@@ -96,12 +98,11 @@
         (implementation_clear s gridEnabled which) := by
   intro s gridEnabled which
   unfold problem_spec_clear implementation_clear
-  simp only [Id.run, pure]
-  refine ⟨?_, ?_, ?_, ?_⟩
-  · rw [Function.update_self]
-  · rw [Function.update_self]
-  · intro k hk
-    rw [Function.update_of_ne hk]
-  · intro k hk
-    rw [Function.update_of_ne hk]
+  simp only [Id.run, pure, bind]
+  refine ⟨?_, ?_, ?_, ?_⟩ <;>
+    (try intro k hk) <;>
+    simp_all [Function.update, gridKey, majorGridOn, minorGridOn] <;>
+    (try rw [Function.update_self]) <;>
+    (try rw [Function.update_of_ne hk]) <;>
+    (first | rfl | decide | simp_all | omega)
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -82,10 +82,11 @@
 -- impl-start
 def implementation_clear
     (s : TickKwPair) (gridEnabled : Bool) (which : String) : TickKwPair := Id.run do
+  -- WRONG: swaps which flag goes into which table.
   let mut major := s.major
   let mut minor := s.minor
-  major := Function.update major gridKey (some (majorGridOn gridEnabled which))
-  minor := Function.update minor gridKey (some (minorGridOn gridEnabled which))
+  major := Function.update major gridKey (some (minorGridOn gridEnabled which))
+  minor := Function.update minor gridKey (some (majorGridOn gridEnabled which))
   return ⟨major, minor⟩
 -- impl-end
 
@@ -96,12 +97,11 @@
         (implementation_clear s gridEnabled which) := by
   intro s gridEnabled which
   unfold problem_spec_clear implementation_clear
-  simp only [Id.run, pure]
-  refine ⟨?_, ?_, ?_, ?_⟩
-  · rw [Function.update_self]
-  · rw [Function.update_self]
-  · intro k hk
-    rw [Function.update_of_ne hk]
-  · intro k hk
-    rw [Function.update_of_ne hk]
+  simp only [Id.run, pure, bind]
+  refine ⟨?_, ?_, ?_, ?_⟩ <;>
+    (try intro k hk) <;>
+    simp_all [Function.update, gridKey, majorGridOn, minorGridOn] <;>
+    (try rw [Function.update_self]) <;>
+    (try rw [Function.update_of_ne hk]) <;>
+    (first | rfl | decide | simp_all | omega)
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -82,10 +82,11 @@
 -- impl-start
 def implementation_clear
     (s : TickKwPair) (gridEnabled : Bool) (which : String) : TickKwPair := Id.run do
+  -- WRONG: only the major grid entry is recomputed; the minor table is returned
+  -- untouched, so minor.gridOn is not set from the preferences.
   let mut major := s.major
-  let mut minor := s.minor
+  let minor := s.minor
   major := Function.update major gridKey (some (majorGridOn gridEnabled which))
-  minor := Function.update minor gridKey (some (minorGridOn gridEnabled which))
   return ⟨major, minor⟩
 -- impl-end
 
@@ -96,12 +97,11 @@
         (implementation_clear s gridEnabled which) := by
   intro s gridEnabled which
   unfold problem_spec_clear implementation_clear
-  simp only [Id.run, pure]
-  refine ⟨?_, ?_, ?_, ?_⟩
-  · rw [Function.update_self]
-  · rw [Function.update_self]
-  · intro k hk
-    rw [Function.update_of_ne hk]
-  · intro k hk
-    rw [Function.update_of_ne hk]
+  simp only [Id.run, pure, bind]
+  refine ⟨?_, ?_, ?_, ?_⟩ <;>
+    (try intro k hk) <;>
+    simp_all [Function.update, gridKey, majorGridOn, minorGridOn] <;>
+    (try rw [Function.update_self]) <;>
+    (try rw [Function.update_of_ne hk]) <;>
+    (first | rfl | decide | simp_all | omega)
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -82,10 +82,11 @@
 -- impl-start
 def implementation_clear
     (s : TickKwPair) (gridEnabled : Bool) (which : String) : TickKwPair := Id.run do
+  -- WRONG: grid entry hard-coded to true, ignoring the drawing preferences.
   let mut major := s.major
   let mut minor := s.minor
-  major := Function.update major gridKey (some (majorGridOn gridEnabled which))
-  minor := Function.update minor gridKey (some (minorGridOn gridEnabled which))
+  major := Function.update major gridKey (some true)
+  minor := Function.update minor gridKey (some true)
   return ⟨major, minor⟩
 -- impl-end
 
@@ -96,12 +97,11 @@
         (implementation_clear s gridEnabled which) := by
   intro s gridEnabled which
   unfold problem_spec_clear implementation_clear
-  simp only [Id.run, pure]
-  refine ⟨?_, ?_, ?_, ?_⟩
-  · rw [Function.update_self]
-  · rw [Function.update_self]
-  · intro k hk
-    rw [Function.update_of_ne hk]
-  · intro k hk
-    rw [Function.update_of_ne hk]
+  simp only [Id.run, pure, bind]
+  refine ⟨?_, ?_, ?_, ?_⟩ <;>
+    (try intro k hk) <;>
+    simp_all [Function.update, gridKey, majorGridOn, minorGridOn] <;>
+    (try rw [Function.update_self]) <;>
+    (try rw [Function.update_of_ne hk]) <;>
+    (first | rfl | decide | simp_all | omega)
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -82,9 +82,11 @@
 -- impl-start
 def implementation_clear
     (s : TickKwPair) (gridEnabled : Bool) (which : String) : TickKwPair := Id.run do
+  -- WRONG: correctly sets gridOn but ALSO wipes the "tick1On" entry of major.
   let mut major := s.major
   let mut minor := s.minor
   major := Function.update major gridKey (some (majorGridOn gridEnabled which))
+  major := Function.update major "tick1On" none
   minor := Function.update minor gridKey (some (minorGridOn gridEnabled which))
   return ⟨major, minor⟩
 -- impl-end
@@ -96,12 +98,11 @@
         (implementation_clear s gridEnabled which) := by
   intro s gridEnabled which
   unfold problem_spec_clear implementation_clear
-  simp only [Id.run, pure]
-  refine ⟨?_, ?_, ?_, ?_⟩
-  · rw [Function.update_self]
-  · rw [Function.update_self]
-  · intro k hk
-    rw [Function.update_of_ne hk]
-  · intro k hk
-    rw [Function.update_of_ne hk]
+  simp only [Id.run, pure, bind]
+  refine ⟨?_, ?_, ?_, ?_⟩ <;>
+    (try intro k hk) <;>
+    simp_all [Function.update, gridKey, majorGridOn, minorGridOn] <;>
+    (try rw [Function.update_self]) <;>
+    (try rw [Function.update_of_ne hk]) <;>
+    (first | rfl | decide | simp_all | omega)
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -82,9 +82,11 @@
 -- impl-start
 def implementation_clear
     (s : TickKwPair) (gridEnabled : Bool) (which : String) : TickKwPair := Id.run do
+  -- WRONG: major grid entry = gridEnabled only, ignoring the "which" preference
+  -- (agrees with spec only when which selects major).
   let mut major := s.major
   let mut minor := s.minor
-  major := Function.update major gridKey (some (majorGridOn gridEnabled which))
+  major := Function.update major gridKey (some gridEnabled)
   minor := Function.update minor gridKey (some (minorGridOn gridEnabled which))
   return ⟨major, minor⟩
 -- impl-end
@@ -96,12 +98,11 @@
         (implementation_clear s gridEnabled which) := by
   intro s gridEnabled which
   unfold problem_spec_clear implementation_clear
-  simp only [Id.run, pure]
-  refine ⟨?_, ?_, ?_, ?_⟩
-  · rw [Function.update_self]
-  · rw [Function.update_self]
-  · intro k hk
-    rw [Function.update_of_ne hk]
-  · intro k hk
-    rw [Function.update_of_ne hk]
+  simp only [Id.run, pure, bind]
+  refine ⟨?_, ?_, ?_, ?_⟩ <;>
+    (try intro k hk) <;>
+    simp_all [Function.update, gridKey, majorGridOn, minorGridOn] <;>
+    (try rw [Function.update_self]) <;>
+    (try rw [Function.update_of_ne hk]) <;>
+    (first | rfl | decide | simp_all | omega)
 -- proof-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -82,10 +82,12 @@
 -- impl-start
 def implementation_clear
     (s : TickKwPair) (gridEnabled : Bool) (which : String) : TickKwPair := Id.run do
+  -- WRONG: writes the computed flag under the WRONG key ("gridOff"); the real
+  -- gridOn entry is left as whatever s carried.
   let mut major := s.major
   let mut minor := s.minor
-  major := Function.update major gridKey (some (majorGridOn gridEnabled which))
-  minor := Function.update minor gridKey (some (minorGridOn gridEnabled which))
+  major := Function.update major "gridOff" (some (majorGridOn gridEnabled which))
+  minor := Function.update minor "gridOff" (some (minorGridOn gridEnabled which))
   return ⟨major, minor⟩
 -- impl-end
 
@@ -96,12 +98,11 @@
         (implementation_clear s gridEnabled which) := by
   intro s gridEnabled which
   unfold problem_spec_clear implementation_clear
-  simp only [Id.run, pure]
-  refine ⟨?_, ?_, ?_, ?_⟩
-  · rw [Function.update_self]
-  · rw [Function.update_self]
-  · intro k hk
-    rw [Function.update_of_ne hk]
-  · intro k hk
-    rw [Function.update_of_ne hk]
+  simp only [Id.run, pure, bind]
+  refine ⟨?_, ?_, ?_, ?_⟩ <;>
+    (try intro k hk) <;>
+    simp_all [Function.update, gridKey, majorGridOn, minorGridOn] <;>
+    (try rw [Function.update_self]) <;>
+    (try rw [Function.update_of_ne hk]) <;>
+    (first | rfl | decide | simp_all | omega)
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Re-initialising an axis' tick configuration.

An axis carries two keyword tables that record per-tick appearance settings —
one for the major ticks and one for the minor ticks. Each table maps a setting
name (a string key such as the grid-visibility flag, or the per-side tick and
label visibility flags) to its value. These tables are populated over the life
of the axis: in particular, when two axes share a common scale, several
per-side visibility entries are written so that interior ticks and labels are
suppressed.

The behaviour modeled here is the step that re-initialises this configuration.
It must recompute exactly one designated entry — the grid-visibility flag — from
the current global drawing preferences, while leaving every other entry of each
table exactly as it already stood. The grid flag is on for the major table when
grids are globally enabled AND the global "which ticks" preference selects the
major ticks (either the dedicated major selection or the combined selection);
symmetrically for the minor table. No other key of either table is created,
removed, or altered: their values carry through unchanged.

The two tables are handled by the same rule and differ only in which "which
ticks" preference value enables their grid flag.
-/

-- axioms-start
-- No unchanged outside callee is invoked: the grid-flag value is computed from
-- the two global drawing preferences with concrete boolean logic, and the
-- preservation of the remaining entries is a pure structural property. Hence
-- there is no `opaque` callee to declare and no consumed `_prop` axiom.
-- axioms-end

-- pure-start
/-- The string key naming the grid-visibility entry of a tick-keyword table. -/
def gridKey : String := "gridOn"

/-- A tick-keyword table: each setting name maps to an optional boolean value
(`none` = the entry is absent, `some b` = present with value `b`). The setting
values relevant to the modeled behaviour are visibility flags, hence booleans
(see mapping.md for the refinement). -/
abbrev TickKw := String → Option Bool

/-- The pair of tables touched together: the major-tick table and the
minor-tick table. -/
structure TickKwPair where
  major : TickKw
  minor : TickKw

/-- Grid flag for the major table: grids globally enabled, and the global
"which ticks" preference selects the major ticks. -/
def majorGridOn (gridEnabled : Bool) (which : String) : Bool :=
  gridEnabled && (which == "both" || which == "major")

/-- Grid flag for the minor table: grids globally enabled, and the global
"which ticks" preference selects the minor ticks. -/
def minorGridOn (gridEnabled : Bool) (which : String) : Bool :=
  gridEnabled && (which == "both" || which == "minor")
-- pure-end

-- post-conditions-start
/-- Re-initialising the tick configuration. The result is pinned completely
(frame discipline):

* the grid-visibility entry of each table equals that table's freshly computed
  grid flag;
* every OTHER key of each table is unchanged from its prior value — nothing
  about the previously-recorded entries is left free.

This is what guarantees that the per-side visibility entries written for shared
axes survive the re-initialisation. -/
def problem_spec_clear
    (s : TickKwPair) (gridEnabled : Bool) (which : String)
    (result : TickKwPair) : Prop :=
  result.major gridKey = some (majorGridOn gridEnabled which) ∧
  result.minor gridKey = some (minorGridOn gridEnabled which) ∧
  (∀ k, k ≠ gridKey → result.major k = s.major k) ∧
  (∀ k, k ≠ gridKey → result.minor k = s.minor k)
-- post-conditions-end

-- impl-start
def implementation_clear
    (s : TickKwPair) (gridEnabled : Bool) (which : String) : TickKwPair := Id.run do
  let mut major := s.major
  let mut minor := s.minor
  major := Function.update major gridKey (some (majorGridOn gridEnabled which))
  minor := Function.update minor gridKey (some (minorGridOn gridEnabled which))
  return ⟨major, minor⟩
-- impl-end

-- proof-start
theorem correct_clear :
    ∀ (s : TickKwPair) (gridEnabled : Bool) (which : String),
      problem_spec_clear s gridEnabled which
        (implementation_clear s gridEnabled which) := by
  intro s gridEnabled which
  unfold problem_spec_clear implementation_clear
  simp only [Id.run, pure]
  refine ⟨?_, ?_, ?_, ?_⟩
  · rw [Function.update_self]
  · rw [Function.update_self]
  · intro k hk
    rw [Function.update_of_ne hk]
  · intro k hk
    rw [Function.update_of_ne hk]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

 Attack verifications run concurrently in two background batches of 4 (<=4 at a time).

SAME-SPEC: same_spec(Solution.lean, atk_N.lean, lean) == True for pos_control and all 7 attacks (built by copying Solution.lean and editing ONLY the impl region; axioms/pure/pre/post byte-identical).

COMMANDS: `bash scripts/lean_verify.sh <file>` from project root for each.

### RESULTS (exit codes read from the echoed `exit=` value, NOT the wrapper's exit):
- pos_control.lean (gold impl: Function.update on s.major/s.minor at gridKey): exit=0 VERIFIES. Positive control good.
- atk_1 clear-first / prepatch bug (build each table from `fun _ => none` then set gridOn): exit=1. Fails on frame conjuncts (result.major k = s.major k is none vs s.major k). prepatch_reproduced=true.
- atk_2 swapped major/minor grid flags: exit=1. Fails gridKey conjunct (some (minorGridOn ..) = some (majorGridOn ..)).
- atk_3 partial: minor table returned untouched (minor.gridOn not set): exit=1. Fails minor gridKey conjunct.
- atk_4 constant-true flag (ignores preferences): exit=1. Fails gridKey conjunct when flag should be false.
- atk_5 control-flow-effect: sets gridOn correctly but ALSO wipes major "tick1On": exit=1. Fails frame conjunct at k="tick1On".
- atk_6 partial-domain: major flag = gridEnabled only, ignores which: exit=1. Fails gridKey conjunct when which='minor'.
- atk_7 ungrounded/wrong-key: writes computed flag under key "gridOff", real gridOn left as s's value: exit=1. Fails gridKey conjunct.
Every failure is a GENUINE unsolved-goal error at the closing tactic (final `omega` on a false residual equation) after an aggressive close chain (refine + simp_all[Function.update,gridKey,majorGridOn,minorGridOn] + rfl/decide/simp_all/omega) — NOT import/environment errors (confirmed by reading the error text: 'omega could not prove the goal' at the proof line, with prior tactics discharging trivial parts). No sorry.

SINCE NO WRONG IMPL CLOSES, there are no verifying attacks to materialize as faithful patches; patches={} and no resolve runs were needed by protocol.

A-LEG AUDIT (refinement.md + axiom_check.py + Solution.lean): NO A-legs exist. axioms block is empty; grep of Solution.lean finds no `opaque`, no `axiom`, no `_prop`, no `noncomputable`, no sorry. All refinement legs are R (Python dict -> total String->Option Bool map; value-space restricted to boolean visibility flags) or I (majorGridOn/minorGridOn == `g and w in ('both','major'/'minor')`; Function.update at gridKey == single-key in-place dict assignment; base map is s.major/s.minor = prior contents, matching the gold's removal of the preceding .clear()). No kind-3 legs. G-AX is a principled skip (axiom_check.py status=skip, exit 0) and the model<->real-callee correspondence is exercised mechanically by conformance_check.py / G-CONF (per verdict.md: checked=100006 disagreements=0 status=pass over the real patched Axis.clear). The A-legs' correspondence claim ('no unchanged external callee; concrete boolean logic + structural frame') is correct: the patch only inlines two boolean assignments and drops the .clear() calls — no opaque callee is invoked in the modeled step.

CONCLUSION: The spec fully pins both result maps pointwise, leaving nothing free; no axiom surface exists to exploit. 7 distinct genuinely-wrong same-spec impls (partial-domain, boundary, control-flow-effect, ungrounded-oracle wrong-key, prepatch bug, swap) ALL fail to close; positive control verifies. verify => correct. VERDICT: SOUND.

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
None found. No same-spec wrong implementation produced a closing, clean-axiom proof, so there is no verifying-but-non-resolving counterexample. The spec problem_spec_clear is a COMPLETE extensional characterization of the result pair: it pins result.major gridKey = some (majorGridOn g w), result.minor gridKey = some (minorGridOn g w), AND (forall k != gridKey, result.major k = s.major k) plus the minor analogue. Both output maps are fixed pointwise at every key; nothing is left free. Any impl whose correct_clear closes must therefore agree with the fix at every point => behaviorally identical => resolves. verify => correct holds.
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
Re-initialising an axis' tick configuration.

An axis carries two keyword tables that record per-tick appearance settings —
one for the major ticks and one for the minor ticks. Each table maps a setting
name (a string key such as the grid-visibility flag, or the per-side tick and
label visibility flags) to its value. These tables are populated over the life
of the axis: in particular, when two axes share a common scale, several
per-side visibility entries are written so that interior ticks and labels are
suppressed.

The behaviour modeled here is the step that re-initialises this configuration.
It must recompute exactly one designated entry — the grid-visibility flag — from
the current global drawing preferences, while leaving every other entry of each
table exactly as it already stood. The grid flag is on for the major table when
grids are globally enabled AND the global "which ticks" preference selects the
major ticks (either the dedicated major selection or the combined selection);
symmetrically for the minor table. No other key of either table is created,
removed, or altered: their values carry through unchanged.

The two tables are handled by the same rule and differ only in which "which
ticks" preference value enables their grid flag.
-/

-- axioms-start
-- No unchanged outside callee is invoked: the grid-flag value is computed from
-- the two global drawing preferences with concrete boolean logic, and the
-- preservation of the remaining entries is a pure structural property. Hence
-- there is no `opaque` callee to declare and no consumed `_prop` axiom.
-- axioms-end

-- pure-start
/-- The string key naming the grid-visibility entry of a tick-keyword table. -/
def gridKey : String := "gridOn"

/-- A tick-keyword table: each setting name maps to an optional boolean value
(`none` = the entry is absent, `some b` = present with value `b`). The setting
values relevant to the modeled behaviour are visibility flags, hence booleans
(see mapping.md for the refinement). -/
abbrev TickKw := String → Option Bool

/-- The pair of tables touched together: the major-tick table and the
minor-tick table. -/
structure TickKwPair where
  major : TickKw
  minor : TickKw

/-- Grid flag for the major table: grids globally enabled, and the global
"which ticks" preference selects the major ticks. -/
def majorGridOn (gridEnabled : Bool) (which : String) : Bool :=
  gridEnabled && (which == "both" || which == "major")

/-- Grid flag for the minor table: grids globally enabled, and the global
"which ticks" preference selects the minor ticks. -/
def minorGridOn (gridEnabled : Bool) (which : String) : Bool :=
  gridEnabled && (which == "both" || which == "minor")
-- pure-end

-- post-conditions-start
/-- Re-initialising the tick configuration. The result is pinned completely
(frame discipline):

* the grid-visibility entry of each table equals that table's freshly computed
  grid flag;
* every OTHER key of each table is unchanged from its prior value — nothing
  about the previously-recorded entries is left free.

This is what guarantees that the per-side visibility entries written for shared
axes survive the re-initialisation. -/
def problem_spec_clear
    (s : TickKwPair) (gridEnabled : Bool) (which : String)
    (result : TickKwPair) : Prop :=
  result.major gridKey = some (majorGridOn gridEnabled which) ∧
  result.minor gridKey = some (minorGridOn gridEnabled which) ∧
  (∀ k, k ≠ gridKey → result.major k = s.major k) ∧
  (∀ k, k ≠ gridKey → result.minor k = s.minor k)
-- post-conditions-end

-- impl-start
def implementation_clear
    (s : TickKwPair) (gridEnabled : Bool) (which : String) : TickKwPair := Id.run do
  let mut major := s.major
  let mut minor := s.minor
  major := Function.update major gridKey (some (majorGridOn gridEnabled which))
  minor := Function.update minor gridKey (some (minorGridOn gridEnabled which))
  return ⟨major, minor⟩
-- impl-end

-- proof-start
theorem correct_clear :
    ∀ (s : TickKwPair) (gridEnabled : Bool) (which : String),
      problem_spec_clear s gridEnabled which
        (implementation_clear s gridEnabled which) := by
  intro s gridEnabled which
  unfold problem_spec_clear implementation_clear
  simp only [Id.run, pure]
  refine ⟨?_, ?_, ?_, ?_⟩
  · rw [Function.update_self]
  · rw [Function.update_self]
  · intro k hk
    rw [Function.update_of_ne hk]
  · intro k hk
    rw [Function.update_of_ne hk]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

 Attack verifications run concurrently in two background batches of 4 (<=4 at a time).

SAME-SPEC: same_spec(Solution.lean, atk_N.lean, lean) == True for pos_control and all 7 attacks (built by copying Solution.lean and editing ONLY the impl region; axioms/pure/pre/post byte-identical).

COMMANDS: `bash scripts/lean_verify.sh <file>` from project root for each.

### RESULTS (exit codes read from the echoed `exit=` value, NOT the wrapper's exit):
- pos_control.lean (gold impl: Function.update on s.major/s.minor at gridKey): exit=0 VERIFIES. Positive control good.
- atk_1 clear-first / prepatch bug (build each table from `fun _ => none` then set gridOn): exit=1. Fails on frame conjuncts (result.major k = s.major k is none vs s.major k). prepatch_reproduced=true.
- atk_2 swapped major/minor grid flags: exit=1. Fails gridKey conjunct (some (minorGridOn ..) = some (majorGridOn ..)).
- atk_3 partial: minor table returned untouched (minor.gridOn not set): exit=1. Fails minor gridKey conjunct.
- atk_4 constant-true flag (ignores preferences): exit=1. Fails gridKey conjunct when flag should be false.
- atk_5 control-flow-effect: sets gridOn correctly but ALSO wipes major "tick1On": exit=1. Fails frame conjunct at k="tick1On".
- atk_6 partial-domain: major flag = gridEnabled only, ignores which: exit=1. Fails gridKey conjunct when which='minor'.
- atk_7 ungrounded/wrong-key: writes computed flag under key "gridOff", real gridOn left as s's value: exit=1. Fails gridKey conjunct.
Every failure is a GENUINE unsolved-goal error at the closing tactic (final `omega` on a false residual equation) after an aggressive close chain (refine + simp_all[Function.update,gridKey,majorGridOn,minorGridOn] + rfl/decide/simp_all/omega) — NOT import/environment errors (confirmed by reading the error text: 'omega could not prove the goal' at the proof line, with prior tactics discharging trivial parts). No sorry.

SINCE NO WRONG IMPL CLOSES, there are no verifying attacks to materialize as faithful patches; patches={} and no resolve runs were needed by protocol.

A-LEG AUDIT (refinement.md + axiom_check.py + Solution.lean): NO A-legs exist. axioms block is empty; grep of Solution.lean finds no `opaque`, no `axiom`, no `_prop`, no `noncomputable`, no sorry. All refinement legs are R (Python dict -> total String->Option Bool map; value-space restricted to boolean visibility flags) or I (majorGridOn/minorGridOn == `g and w in ('both','major'/'minor')`; Function.update at gridKey == single-key in-place dict assignment; base map is s.major/s.minor = prior contents, matching the gold's removal of the preceding .clear()). No kind-3 legs. G-AX is a principled skip (axiom_check.py status=skip, exit 0) and the model<->real-callee correspondence is exercised mechanically by conformance_check.py / G-CONF (per verdict.md: checked=100006 disagreements=0 status=pass over the real patched Axis.clear). The A-legs' correspondence claim ('no unchanged external callee; concrete boolean logic + structural frame') is correct: the patch only inlines two boolean assignments and drops the .clear() calls — no opaque callee is invoked in the modeled step.

CONCLUSION: The spec fully pins both result maps pointwise, leaving nothing free; no axiom surface exists to exploit. 7 distinct genuinely-wrong same-spec impls (partial-domain, boundary, control-flow-effect, ungrounded-oracle wrong-key, prepatch bug, swap) ALL fail to close; positive control verifies. verify => correct. VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-drift) check for matplotlib__matplotlib-20826, modeling the tick-keyword re-init step of Axis.clear (post-patch, lib/matplotlib/axis.py). RESULT: FAITHFUL — no diverging input found; the modeled function agrees with the real callee on the entire realizable input space.

Evidence:
1. same_spec(Solution.lean, Solution_prepatch.lean)=True via swebench_unified.markers with LeanBackend.language — spec regions (axioms/pure/pre/post) are byte-identical; discrimination is spec-driven.
2. lean_verify.sh Solution.lean -> exit 0 (compiles, no sorry). `#print axioms correct_clear` -> 'does not depend on any axioms' (no sorryAx; proof is real, not fake).
3. Real callee: verified Axis.clear at base_commit a0d2e39 (via git object DB) and installed mpl 3.6.3 both. Post-patch clear sets `_major/minor_tick_kw['gridOn'] = mpl.rcParams['axes.grid'] and mpl.rcParams['axes.grid.which'] in ('both','major'/'minor')`, then reset_ticks() — which does NOT mutate the kw dicts (verified source). So real behavior = overwrite gridOn, preserve every other key. This matches problem_spec_clear's four conjuncts exactly.
4. Spec is not too STRONG: it demands only what the real code guarantees. majorGridOn/minorGridOn boolean logic reproduces `in ('both','major'/'minor')` on the full realizable domain. rcParams validators confirmed: axes.grid.which rejects anything but {major,minor,both}; axes.grid coerces to bool. Unrealizable which-strings can't occur, so the spec returning false there is not a divergence.
5. Spec is not too WEAK: the frame conjuncts (every non-gridOn key preserved from input s) are exactly the dropped-`.clear()` guarantee the F2P test test_shared_axes_clear observes; a clear-first impl fails the third/fourth conjunct.
6. conformance_check.py run against the REAL patched Axis.clear: checked=100006, disagreements=0, status=pass (6 edge cases + 100k fuzzed inputs incl. non-boolean sentinel entries confirming value-agnostic preservation).

No input where the modeled function disagrees with the real repo behavior was found.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** same_spec(Solution.lean, Solution_prepatch.lean, LeanBackend) = True (verified) — spec region byte-identical; the spec view is the projected docstring + gridKey/TickKw/TickKwPair/majorGridOn/minorGridOn + problem_spec_clear (impl/proof elided).

Public problem_statement (excl. hints_text): symptom-level bug report — 'ax.clear() adds extra ticks, un-hides shared-axis tick labels'; names ax.clear() and the symptom (shared-axis visibility settings reset by clear). Does NOT mention gridOn, tick-keyword dicts, rcParams, axes.grid(.which), _reset_*_tick_kw, or axis.py.

Gold edit (patch.diff): inside Axis.clear, delete the two self._reset_major/minor_tick_kw() calls (each did dict.clear() then set gridOn) and replace with two in-place assignments setting ONLY _major/minor_tick_kw['gridOn'], preserving all other entries.

Judgment: the spec view does NOT disclose the edit mechanism — no Python, no axis.py/Axis.clear, no _reset_*_tick_kw, no .clear() call, no 'delete the reset helpers', no file/line refs. It states the correct target behavior abstractly (recompute the single grid entry, preserve every other entry), which is the natural specification directly implied by the public symptom ('clear un-hides labels that should stay hidden' => 'clear must preserve those visibility entries'). Stating correct behavior is the spec's job, not leakage of the fix.

Scrutinized: the only gold-derived detail beyond problem_statement is the gridOn boolean formula (gridEnabled && which in {both,major/minor}). But this is NOT the edit's delta — it existed verbatim in the pre-patch _reset_*_tick_kw helpers and is carried through unchanged by the fix (constant across pre/post). The spec-identical Solution_prepatch.lean uses the same gridOn value yet still fails correct_clear on the frame conjuncts, confirming the spec discriminates on the frame-preservation clause, not the gridOn value; hence disclosing the formula reveals nothing about the gold EDIT. It is structural, needed only to pin what gridKey maps to. No spec-view line leaks the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
