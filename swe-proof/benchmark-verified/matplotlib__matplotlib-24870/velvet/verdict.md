# P2 adversarial audit — matplotlib__matplotlib-24870

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -71,13 +71,7 @@
       if posGiven then
         return posArg
       else
-        if boolField then
-          if filled then
-            return (LevelArg.explicit [0, 1/2, 1])
-          else
-            return (LevelArg.explicit [1/2])
-        else
-          return (LevelArg.count 7)
+        return (LevelArg.count 7)
     -- impl-end
 
 prove_correct chooseLevelArg by
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -73,9 +73,9 @@
       else
         if boolField then
           if filled then
+            return (LevelArg.explicit [1/2])
+          else
             return (LevelArg.explicit [0, 1/2, 1])
-          else
-            return (LevelArg.explicit [1/2])
         else
           return (LevelArg.count 7)
     -- impl-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -77,7 +77,7 @@
           else
             return (LevelArg.explicit [1/2])
         else
-          return (LevelArg.count 7)
+          return (LevelArg.count 6)
     -- impl-end
 
 prove_correct chooseLevelArg by
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -65,11 +65,11 @@
     -- (no loops in this method.)
     -- invariants-end
     -- impl-start
-    if levelsKwSet then
-      return levelsKw
+    if posGiven then
+      return posArg
     else
-      if posGiven then
-        return posArg
+      if levelsKwSet then
+        return levelsKw
       else
         if boolField then
           if filled then
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -72,10 +72,7 @@
         return posArg
       else
         if boolField then
-          if filled then
-            return (LevelArg.explicit [0, 1/2, 1])
-          else
-            return (LevelArg.explicit [1/2])
+          return (LevelArg.explicit [0, 1/2, 1])
         else
           return (LevelArg.count 7)
     -- impl-end
```

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -67,17 +67,13 @@
     -- impl-start
     if levelsKwSet then
       return levelsKw
+    else if posGiven then
+      return posArg
     else
-      if posGiven then
-        return posArg
-      else
-        if boolField then
-          if filled then
-            return (LevelArg.explicit [0, 1/2, 1])
-          else
-            return (LevelArg.explicit [1/2])
-        else
-          return (LevelArg.count 7)
+      match boolField, filled with
+      | true,  true  => return (LevelArg.explicit [0, 1/2, 1])
+      | true,  false => return (LevelArg.explicit [1/2])
+      | false, _     => return (LevelArg.count 7)
     -- impl-end
 
 prove_correct chooseLevelArg by
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -73,9 +73,9 @@
       else
         if boolField then
           if filled then
-            return (LevelArg.explicit [0, 1/2, 1])
+            return (LevelArg.explicit [0/1, 1/2, 2/2])
           else
-            return (LevelArg.explicit [1/2])
+            return (LevelArg.explicit [2/4])
         else
           return (LevelArg.count 7)
     -- impl-end
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -71,11 +71,8 @@
       if posGiven then
         return posArg
       else
-        if boolField then
-          if filled then
-            return (LevelArg.explicit [0, 1/2, 1])
-          else
-            return (LevelArg.explicit [1/2])
+        if boolField && filled then
+          return (LevelArg.explicit [0, 1/2, 1])
         else
           return (LevelArg.count 7)
     -- impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (no axioms: the modeled change is a pure selection over already-available
--  flags; there is no unchanged callee whose contract the proof consumes.)
-- axioms-end

-- pure-start
/- A chosen level specification. Either an automatic level *count* (a small
   integer the data-range expander later turns into that many evenly-spaced
   positions) or an *explicit* sequence of level positions (modeled as exact
   rationals so equality is decidable and order-faithful). This is the value
   the level-selection step yields before the downstream count→positions /
   positions→array processing (which the change leaves untouched). -/
inductive LevelArg where
  | count    (n : Nat)
  | explicit (levels : List Rat)
  deriving DecidableEq, Inhabited
-- pure-end

-- pre-conditions-start
-- (no preconditions: every flag combination is admissible input.)
-- pre-conditions-end

-- post-conditions-start
-- (post-conditions are stated inline on the method below.)
-- post-conditions-end

/- Select the level specification for a 2-D field plot when the caller did not
   pass an explicit `levels` keyword.

   Inputs (all already computed by the surrounding routine):
   * `levelsKwSet`  — whether a `levels` keyword was supplied (its value is
                      `levelsKw`);
   * `posGiven`     — whether a positional level argument was supplied (its
                      value is `posArg`);
   * `boolField`    — whether the field being plotted is a boolean field;
   * `filled`       — whether the plot fills regions between levels (vs. drawing
                      boundary lines only).

   The guarantee: an explicit keyword wins; otherwise a positional argument
   wins; otherwise a boolean field gets a constant boundary specification that
   depends only on `filled`; otherwise the hard-wired automatic count. -/
method chooseLevelArg
    (levelsKwSet : Bool) (levelsKw : LevelArg)
    (posGiven : Bool)    (posArg : LevelArg)
    (boolField : Bool)   (filled : Bool)
    return (out : LevelArg)
  ensures (levelsKwSet = true)  → out = levelsKw
  ensures (levelsKwSet = false) → (posGiven = true)  → out = posArg
  ensures (levelsKwSet = false) → (posGiven = false) → (boolField = true)  → (filled = true)  →
            out = LevelArg.explicit [0, 1/2, 1]
  ensures (levelsKwSet = false) → (posGiven = false) → (boolField = true)  → (filled = false) →
            out = LevelArg.explicit [1/2]
  ensures (levelsKwSet = false) → (posGiven = false) → (boolField = false) →
            out = LevelArg.count 7
  do
    -- invariants-start
    -- (no loops in this method.)
    -- invariants-end
    -- impl-start
    if levelsKwSet then
      return levelsKw
    else
      if posGiven then
        return posArg
      else
        if boolField then
          if filled then
            return (LevelArg.explicit [0, 1/2, 1])
          else
            return (LevelArg.explicit [1/2])
        else
          return (LevelArg.count 7)
    -- impl-end

prove_correct chooseLevelArg by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

Spec chooseLevelArg is a TOTAL specification: all five ensures clauses pin `out` for every point of the full (levelsKwSet, posGiven, boolField, filled) Boolean cube with fixed levelsKw/posArg, so any verifying impl is observationally unique on the modeled domain. Attack results (all same_spec=True vs frozen Solution.lean; verified via `bash scripts/lean_verify.sh <f>`):
- atk_1 (prepatch bug: always count 7, no bool-field branch): lean_verify EXIT=1 (proof obligation LevelArg.count 7 = LevelArg.explicit [0,1/2,1] unmet) — prepatch reproduced.
- atk_2 (swap the two bool-field lists [1/2]<->[0,1/2,1]): EXIT=1 (unmet).
- atk_3 (boundary: count 6 not 7): EXIT=1 (LevelArg.count 6 = LevelArg.count 7 unmet).
- atk_4 (control-flow-effect: positional checked before keyword): EXIT=1 (posArg = levelsKw unmet).
- atk_5 (partial-domain: ignore `filled`, always [0,1/2,1] for bool field): EXIT=1 (unmet on filled=false).
- atk_8 (control-flow-effect: `boolField && filled` collapses, drops [1/2] case to count 7): EXIT=1 (unmet).
- atk_6 (ungrounded-oracle ECHO: gold behaviour via `match boolField, filled`): lean_verify EXIT=0 VERIFIES.
- atk_7 (ECHO: equal Rat literals [0/1,1/2,2/2] and [2/4], = gold): EXIT=0 VERIFIES.
Both verifying impls (atk_6, atk_7) compute the exact gold selection, so their faithful refined patch IS the gold patch.diff (sha1 00b963f4cb5076...; byte-identical to benchmark-verified/.../patch.diff). Materialized as patch_atk_6.diff / patch_atk_7.diff and RUN through the official harness via swebench_unified.harness.run_resolve('matplotlib__matplotlib-24870', ...): atk_6 -> RESOLVED=True COMPLETED=True FLAKY=False (log resolve_atk_6.log); atk_7 -> RESOLVED=True COMPLETED=True FLAKY=False (log resolve_atk_7.log). Positive control pos.lean (unedited gold impl) verifies EXIT=0. Recorded meta.json gates.G-RESOLVE.data.resolved=True corroborates. refinement.md audit: axioms region is EMPTY (no axiom/opaque/sorry); impl uses only its own params + pure LevelArg constructors; §C 'all R/I, no A-leg, no kind-3' claim is HONEST — the genuinely-changed op (bool-field branch + two fixed level lists) is modeled directly in the do block (A3), not hidden behind an axiom, so there is no ungrounded-oracle surface. No verifying wrong-impl produced a non-resolving faithful patch: verify does not diverge from correct on this spec. VERDICT: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (no axioms: the modeled change is a pure selection over already-available
--  flags; there is no unchanged callee whose contract the proof consumes.)
-- axioms-end

-- pure-start
/- A chosen level specification. Either an automatic level *count* (a small
   integer the data-range expander later turns into that many evenly-spaced
   positions) or an *explicit* sequence of level positions (modeled as exact
   rationals so equality is decidable and order-faithful). This is the value
   the level-selection step yields before the downstream count→positions /
   positions→array processing (which the change leaves untouched). -/
inductive LevelArg where
  | count    (n : Nat)
  | explicit (levels : List Rat)
  deriving DecidableEq, Inhabited
-- pure-end

-- pre-conditions-start
-- (no preconditions: every flag combination is admissible input.)
-- pre-conditions-end

-- post-conditions-start
-- (post-conditions are stated inline on the method below.)
-- post-conditions-end

/- Select the level specification for a 2-D field plot when the caller did not
   pass an explicit `levels` keyword.

   Inputs (all already computed by the surrounding routine):
   * `levelsKwSet`  — whether a `levels` keyword was supplied (its value is
                      `levelsKw`);
   * `posGiven`     — whether a positional level argument was supplied (its
                      value is `posArg`);
   * `boolField`    — whether the field being plotted is a boolean field;
   * `filled`       — whether the plot fills regions between levels (vs. drawing
                      boundary lines only).

   The guarantee: an explicit keyword wins; otherwise a positional argument
   wins; otherwise a boolean field gets a constant boundary specification that
   depends only on `filled`; otherwise the hard-wired automatic count. -/
method chooseLevelArg
    (levelsKwSet : Bool) (levelsKw : LevelArg)
    (posGiven : Bool)    (posArg : LevelArg)
    (boolField : Bool)   (filled : Bool)
    return (out : LevelArg)
  ensures (levelsKwSet = true)  → out = levelsKw
  ensures (levelsKwSet = false) → (posGiven = true)  → out = posArg
  ensures (levelsKwSet = false) → (posGiven = false) → (boolField = true)  → (filled = true)  →
            out = LevelArg.explicit [0, 1/2, 1]
  ensures (levelsKwSet = false) → (posGiven = false) → (boolField = true)  → (filled = false) →
            out = LevelArg.explicit [1/2]
  ensures (levelsKwSet = false) → (posGiven = false) → (boolField = false) →
            out = LevelArg.count 7
  do
    -- invariants-start
    -- (no loops in this method.)
    -- invariants-end
    -- impl-start
    if levelsKwSet then
      return levelsKw
    else
      if posGiven then
        return posArg
      else
        if boolField then
          if filled then
            return (LevelArg.explicit [0, 1/2, 1])
          else
            return (LevelArg.explicit [1/2])
        else
          return (LevelArg.count 7)
    -- impl-end

prove_correct chooseLevelArg by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

Spec chooseLevelArg is a TOTAL specification: all five ensures clauses pin `out` for every point of the full (levelsKwSet, posGiven, boolField, filled) Boolean cube with fixed levelsKw/posArg, so any verifying impl is observationally unique on the modeled domain. Attack results (all same_spec=True vs frozen Solution.lean; verified via `bash scripts/lean_verify.sh <f>`):
- atk_1 (prepatch bug: always count 7, no bool-field branch): lean_verify EXIT=1 (proof obligation LevelArg.count 7 = LevelArg.explicit [0,1/2,1] unmet) — prepatch reproduced.
- atk_2 (swap the two bool-field lists [1/2]<->[0,1/2,1]): EXIT=1 (unmet).
- atk_3 (boundary: count 6 not 7): EXIT=1 (LevelArg.count 6 = LevelArg.count 7 unmet).
- atk_4 (control-flow-effect: positional checked before keyword): EXIT=1 (posArg = levelsKw unmet).
- atk_5 (partial-domain: ignore `filled`, always [0,1/2,1] for bool field): EXIT=1 (unmet on filled=false).
- atk_8 (control-flow-effect: `boolField && filled` collapses, drops [1/2] case to count 7): EXIT=1 (unmet).
- atk_6 (ungrounded-oracle ECHO: gold behaviour via `match boolField, filled`): lean_verify EXIT=0 VERIFIES.
- atk_7 (ECHO: equal Rat literals [0/1,1/2,2/2] and [2/4], = gold): EXIT=0 VERIFIES.
Both verifying impls (atk_6, atk_7) compute the exact gold selection, so their faithful refined patch IS the gold patch.diff (sha1 00b963f4cb5076...; byte-identical to benchmark-verified/.../patch.diff). Materialized as patch_atk_6.diff / patch_atk_7.diff and RUN through the official harness via swebench_unified.harness.run_resolve('matplotlib__matplotlib-24870', ...): atk_6 -> RESOLVED=True COMPLETED=True FLAKY=False (log resolve_atk_6.log); atk_7 -> RESOLVED=True COMPLETED=True FLAKY=False (log resolve_atk_7.log). Positive control pos.lean (unedited gold impl) verifies EXIT=0. Recorded meta.json gates.G-RESOLVE.data.resolved=True corroborates. refinement.md audit: axioms region is EMPTY (no axiom/opaque/sorry); impl uses only its own params + pure LevelArg constructors; §C 'all R/I, no A-leg, no kind-3' claim is HONEST — the genuinely-changed op (bool-field branch + two fixed level lists) is modeled directly in the do block (A3), not hidden behind an axiom, so there is no ungrounded-oracle surface. No verifying wrong-impl produced a non-resolving faithful patch: verify does not diverge from correct on this spec. VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break audit of velvet chooseLevelArg vs real repo callee ContourSet._process_contour_level_args (lib/matplotlib/contour.py:1119, base_commit 6091437be9776139d3672cde28a19cbe6c09dcd5). Solution.lean verifies clean (lean_verify.sh exit 0, no sorry/error). Spec region byte-identical between Solution.lean and Solution_prepatch.lean (swebench_unified.markers.same_spec via VelvetBackend.language = True); prepatch fails prove_correct as intended (both boolField=true postconditions unreachable from the count-7-always prepatch impl -> valid G-DIFF, not a leak). All 5 postconditions map exactly onto the real patched selection logic and are order-faithful to the nested if/elif/else (keyword > positional > bool-field > default count 7): (kw true->self.levels), (else args->args[0]), (else bool+filled->[0,.5,1]), (else bool+!filled->[.5]), (else->7). Constants 0,1/2,1 are dyadic and exact in both Rat and IEEE-754 float, so the LevelArg bijection (count n <-> int, explicit [Rat] <-> list) is lossless. Modeling boundary is levels_arg pre-isinstance-dispatch, exactly what G-CONF compares; the dtype-plumbing hunks (drop float64 coercion, pass z.dtype) only establish the boolField binding and change no selection logic. Both call sites (contour.py:1470, tri/_tricontour.py:78) route through the same function. Searched the full (levelsKwSet,posGiven,boolField,filled) cube with representative count/explicit posArg/levelsKw values: no input where the modeled function disagrees with the real callee. Spec is not too strong and does not drift. No diverging input found.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Relaxed-leakage bundle, independently re-verified (not rubber-stamped). (1) same_spec(Solution.lean, Solution_prepatch.lean)=True via swebench_unified.markers with the velvet backend LanguageTables — spec region byte-identical/frozen. (2) Disposition properly recorded: meta.relaxed_leakage=True, RELAXED_LEAKAGE.md present, G-LEAK status 'relaxed', G-PANEL-3 pass. (3) Mechanical lexical G-LEAK screen re-run (leakage.screen): passed=True, hard_failures=[] — leak is semantic, not lexical; spec view names no patched symbol / np.issubdtype / z_dtype plumbing / file. (4) The single dispositioned facet is the filled boolean default line `out = LevelArg.explicit [0, 1/2, 1]`. PS token scan (verified against test.jsonl problem_statement) confirms contourf / filled / '[0, .5, 1]' / '0, .5, 1' are ALL ABSENT from problem_statement; they live only in hints_text (which is NOT public spec) and the hidden test_patch, and the F2P test test_bool_autolevel pins the [0,.5,1] value. Unavoidability holds: a faithful spec must pin the filled facet (else a wrong impl verifying against the spec fails the contourf/tricontourf assertions — verify⇏correct), and it is not derivable from problem_statement alone. (5) No NEW leak beyond the dispositioned facet: the LINE facet [1/2] is PS-derivable ('default levels to [0.5]', levels=[.5]); non-bool default count 7 is PS-derivable ('the default 8 levels'); keyword>positional>default ordering is generic argument handling. (6) Core soundness intact per meta (G-VERIFY/G-DIFF/G-EQ/G-CONF/G-RESOLVE/G-MUT pass; G-AX vacuous), so the disposition is not broken. Honest recording per RELAXED_LEAKAGE panel convention: NO-LEAKAGE — dispositioned filled facet re-confirmed, no leak beyond it and no PS-only derivation of the filled default found.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere. This cell separately records G-LEAK as `relaxed`, which is a disclosure a reviewer accepted rather than the absence of one.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `relaxed` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `RELAXED_LEAKAGE.md`, all of which ship in this bundle, so a reader can start there.
