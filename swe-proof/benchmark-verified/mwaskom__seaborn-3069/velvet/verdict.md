# P2 adversarial audit — mwaskom__seaborn-3069

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_4.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No axiomatized callees and no A-reference deep model. The operation under
@@ -95,8 +95,6 @@
   ensures out.hi = (decidedLimits isCategorical hasUserLimit isY nticks userLo userHi autoLo autoHi).2
   do
     -- impl-start
-    -- Start from the limits the prior (user-limit / default-margin) logic
-    -- resolves and the grid the active style chose.
     let mut lo : Rat := autoLo
     let mut hi : Rat := autoHi
     let mut grid : Bool := gridWasOn
@@ -105,15 +103,12 @@
       hi := userHi
     else
       pure ()
-    -- Categorical special-casing: suppress the grid, and (only when the
-    -- consumer did not pin limits) draw to ±1/2 of the tick range, reversed on
-    -- the vertical axis.
     if isCategorical then
       grid := false
       if hasUserLimit then
         pure ()
       else
-        let edge : Rat := (nticks : Rat) - 1 / 2
+        let edge : Rat := (nticks : Rat) + 1 / 2
         if isY then
           lo := edge
           hi := -1 / 2
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No axiomatized callees and no A-reference deep model. The operation under
@@ -95,21 +95,15 @@
   ensures out.hi = (decidedLimits isCategorical hasUserLimit isY nticks userLo userHi autoLo autoHi).2
   do
     -- impl-start
-    -- Start from the limits the prior (user-limit / default-margin) logic
-    -- resolves and the grid the active style chose.
     let mut lo : Rat := autoLo
     let mut hi : Rat := autoHi
-    let mut grid : Bool := gridWasOn
+    let grid : Bool := gridWasOn
     if hasUserLimit then
       lo := userLo
       hi := userHi
     else
       pure ()
-    -- Categorical special-casing: suppress the grid, and (only when the
-    -- consumer did not pin limits) draw to ±1/2 of the tick range, reversed on
-    -- the vertical axis.
     if isCategorical then
-      grid := false
       if hasUserLimit then
         pure ()
       else
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No axiomatized callees and no A-reference deep model. The operation under
@@ -95,8 +95,6 @@
   ensures out.hi = (decidedLimits isCategorical hasUserLimit isY nticks userLo userHi autoLo autoHi).2
   do
     -- impl-start
-    -- Start from the limits the prior (user-limit / default-margin) logic
-    -- resolves and the grid the active style chose.
     let mut lo : Rat := autoLo
     let mut hi : Rat := autoHi
     let mut grid : Bool := gridWasOn
@@ -105,21 +103,13 @@
       hi := userHi
     else
       pure ()
-    -- Categorical special-casing: suppress the grid, and (only when the
-    -- consumer did not pin limits) draw to ±1/2 of the tick range, reversed on
-    -- the vertical axis.
     if isCategorical then
       grid := false
       if hasUserLimit then
         pure ()
       else
-        let edge : Rat := (nticks : Rat) - 1 / 2
-        if isY then
-          lo := edge
-          hi := -1 / 2
-        else
-          lo := -1 / 2
-          hi := edge
+        lo := -1 / 2
+        hi := (nticks : Rat) - 1 / 2
     else
       pure ()
     return { lo := lo, hi := hi, gridVisible := grid }
```

Attack 4 — `atk_4.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No axiomatized callees and no A-reference deep model. The operation under
@@ -95,34 +95,9 @@
   ensures out.hi = (decidedLimits isCategorical hasUserLimit isY nticks userLo userHi autoLo autoHi).2
   do
     -- impl-start
-    -- Start from the limits the prior (user-limit / default-margin) logic
-    -- resolves and the grid the active style chose.
-    let mut lo : Rat := autoLo
-    let mut hi : Rat := autoHi
-    let mut grid : Bool := gridWasOn
-    if hasUserLimit then
-      lo := userLo
-      hi := userHi
-    else
-      pure ()
-    -- Categorical special-casing: suppress the grid, and (only when the
-    -- consumer did not pin limits) draw to ±1/2 of the tick range, reversed on
-    -- the vertical axis.
-    if isCategorical then
-      grid := false
-      if hasUserLimit then
-        pure ()
-      else
-        let edge : Rat := (nticks : Rat) - 1 / 2
-        if isY then
-          lo := edge
-          hi := -1 / 2
-        else
-          lo := -1 / 2
-          hi := edge
-    else
-      pure ()
-    return { lo := lo, hi := hi, gridVisible := grid }
+    let g : Bool := decidedGrid isCategorical gridWasOn
+    let p : Rat × Rat := decidedLimits isCategorical hasUserLimit isY nticks userLo userHi autoLo autoHi
+    return { lo := p.1, hi := p.2, gridVisible := g }
     -- impl-end
 
 prove_correct finalizeAxis by
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No axiomatized callees and no A-reference deep model. The operation under
@@ -95,19 +95,14 @@
   ensures out.hi = (decidedLimits isCategorical hasUserLimit isY nticks userLo userHi autoLo autoHi).2
   do
     -- impl-start
-    -- Start from the limits the prior (user-limit / default-margin) logic
-    -- resolves and the grid the active style chose.
     let mut lo : Rat := autoLo
     let mut hi : Rat := autoHi
     let mut grid : Bool := gridWasOn
     if hasUserLimit then
-      lo := userLo
-      hi := userHi
+      lo := userHi
+      hi := userLo
     else
       pure ()
-    -- Categorical special-casing: suppress the grid, and (only when the
-    -- consumer did not pin limits) draw to ±1/2 of the tick range, reversed on
-    -- the vertical axis.
     if isCategorical then
       grid := false
       if hasUserLimit then
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No axiomatized callees and no A-reference deep model. The operation under
@@ -95,8 +95,6 @@
   ensures out.hi = (decidedLimits isCategorical hasUserLimit isY nticks userLo userHi autoLo autoHi).2
   do
     -- impl-start
-    -- Start from the limits the prior (user-limit / default-margin) logic
-    -- resolves and the grid the active style chose.
     let mut lo : Rat := autoLo
     let mut hi : Rat := autoHi
     let mut grid : Bool := gridWasOn
@@ -105,21 +103,15 @@
       hi := userHi
     else
       pure ()
-    -- Categorical special-casing: suppress the grid, and (only when the
-    -- consumer did not pin limits) draw to ±1/2 of the tick range, reversed on
-    -- the vertical axis.
     if isCategorical then
       grid := false
-      if hasUserLimit then
-        pure ()
+      let edge : Rat := (nticks : Rat) - 1 / 2
+      if isY then
+        lo := edge
+        hi := -1 / 2
       else
-        let edge : Rat := (nticks : Rat) - 1 / 2
-        if isY then
-          lo := edge
-          hi := -1 / 2
-        else
-          lo := -1 / 2
-          hi := edge
+        lo := -1 / 2
+        hi := edge
     else
       pure ()
     return { lo := lo, hi := hi, gridVisible := grid }
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No axiomatized callees and no A-reference deep model. The operation under
@@ -95,34 +95,9 @@
   ensures out.hi = (decidedLimits isCategorical hasUserLimit isY nticks userLo userHi autoLo autoHi).2
   do
     -- impl-start
-    -- Start from the limits the prior (user-limit / default-margin) logic
-    -- resolves and the grid the active style chose.
-    let mut lo : Rat := autoLo
-    let mut hi : Rat := autoHi
-    let mut grid : Bool := gridWasOn
-    if hasUserLimit then
-      lo := userLo
-      hi := userHi
-    else
-      pure ()
-    -- Categorical special-casing: suppress the grid, and (only when the
-    -- consumer did not pin limits) draw to ±1/2 of the tick range, reversed on
-    -- the vertical axis.
-    if isCategorical then
-      grid := false
-      if hasUserLimit then
-        pure ()
-      else
-        let edge : Rat := (nticks : Rat) - 1 / 2
-        if isY then
-          lo := edge
-          hi := -1 / 2
-        else
-          lo := -1 / 2
-          hi := edge
-    else
-      pure ()
-    return { lo := lo, hi := hi, gridVisible := grid }
+    let rec loop (n : Nat) : Rat := loop (n + 1)
+    let x : Rat := loop 0
+    return { lo := x, hi := x, gridVisible := true }
     -- impl-end
 
 prove_correct finalizeAxis by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees and no A-reference deep model. The operation under
--  specification — the per-axis finalization decision (which gridlines to show
--  and what view limits to set) — is modeled deeply as pure functions plus the
--  `do` block below. The tick count and the would-be default margin limits are
--  read-only environment observations passed in as inputs; the decision is pure
--  arithmetic over them, so nothing is borrowed from an outside contract and
--  there is no axiom to validate. meta.json G-AX = skip.)
-- axioms-end

-- pure-start
/- The view limits of an axis after finalization, as an exact (lo, hi) pair of
   rationals (half-integer offsets are exact, so `Rat` models them without IEEE
   rounding — mapping.md §2).

   Three cases, in priority order:

     * the consumer pinned explicit limits for this axis  → those limits are
       used verbatim (already unit-resolved into `userLo`/`userHi`);
     * otherwise, on a CATEGORICAL axis the view runs from half a step before
       the first tick to half a step past the last tick — `[-1/2, n - 1/2]` for
       `n` ticks — and that interval is reversed on a vertical axis (so the
       first category sits at the top);
     * otherwise the ordinary default margin limits apply, unchanged.

   This matches the public requirement: a categorical scale "is drawn to ±0.5
   from the first and last tick" and, "if on the y axis, the axis is inverted." -/
def decidedLimits (isCategorical hasUserLimit isY : Bool) (nticks : Nat)
    (userLo userHi autoLo autoHi : Rat) : Rat × Rat :=
  if hasUserLimit then (userLo, userHi)
  else
    if isCategorical then
      if isY then ((nticks : Rat) - 1 / 2, -1 / 2)
      else (-1 / 2, (nticks : Rat) - 1 / 2)
    else (autoLo, autoHi)

/- Whether gridlines remain visible on an axis after finalization. On a
   categorical axis the grid is suppressed regardless of the active style;
   otherwise the style's choice (`gridWasOn`) stands. Matches the public
   requirement that "a grid is not shown" for such scales. -/
def decidedGrid (isCategorical gridWasOn : Bool) : Bool :=
  if isCategorical then false else gridWasOn
-- pure-end

/- What finalization decides for one axis, abstracted to the observable state
   the requirement constrains:

     * `lo`, `hi`        — the view limits actually set on the axis;
     * `gridVisible`     — whether gridlines are shown. -/
structure AxisFinal where
  lo : Rat
  hi : Rat
  gridVisible : Bool
  deriving Inhabited

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Finalizing one axis of a finished figure.

   The inputs are read-only observations of the axis and its scale, and are not
   mutated by the decision (directive 5):

     * `isCategorical`   — the axis carries a categorical (discrete-level) scale;
     * `hasUserLimit`    — the consumer pinned explicit limits for this axis;
     * `isY`             — this is the vertical axis;
     * `nticks`          — the number of major ticks currently on the axis (one
                           per level, for a categorical scale);
     * `userLo`,`userHi` — the consumer's pinned limits, already unit-resolved
                           (meaningful only when `hasUserLimit`);
     * `autoLo`,`autoHi` — the limits the ordinary default margin logic would
                           set (meaningful when the categorical/user cases do
                           not apply);
     * `gridWasOn`       — whether the active style would show gridlines here.

   The result records the view limits set and whether gridlines remain visible.
   A categorical axis with no pinned limits is drawn to ±1/2 of its ticks
   (reversed on the vertical axis) with its grid suppressed; every other axis is
   left to the consumer's pinned limits or the default margin logic, with its
   grid governed by the active style. -/
method finalizeAxis (isCategorical : Bool) (hasUserLimit : Bool) (isY : Bool) (nticks : Nat) (userLo : Rat) (userHi : Rat) (autoLo : Rat) (autoHi : Rat) (gridWasOn : Bool) return (out : AxisFinal)
  ensures out.gridVisible = decidedGrid isCategorical gridWasOn
  ensures out.lo = (decidedLimits isCategorical hasUserLimit isY nticks userLo userHi autoLo autoHi).1
  ensures out.hi = (decidedLimits isCategorical hasUserLimit isY nticks userLo userHi autoLo autoHi).2
  do
    -- impl-start
    -- Start from the limits the prior (user-limit / default-margin) logic
    -- resolves and the grid the active style chose.
    let mut lo : Rat := autoLo
    let mut hi : Rat := autoHi
    let mut grid : Bool := gridWasOn
    if hasUserLimit then
      lo := userLo
      hi := userHi
    else
      pure ()
    -- Categorical special-casing: suppress the grid, and (only when the
    -- consumer did not pin limits) draw to ±1/2 of the tick range, reversed on
    -- the vertical axis.
    if isCategorical then
      grid := false
      if hasUserLimit then
        pure ()
      else
        let edge : Rat := (nticks : Rat) - 1 / 2
        if isY then
          lo := edge
          hi := -1 / 2
        else
          lo := -1 / 2
          hi := edge
    else
      pure ()
    return { lo := lo, hi := hi, gridVisible := grid }
    -- impl-end

prove_correct finalizeAxis by
  loom_solve <;> simp_all [decidedGrid, decidedLimits]
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial refinement-fidelity audit for mwaskom__seaborn-3069 (velvet). Project root in prompt did not exist; used real repo root. elan v4.24.0, python.

SPEC SHAPE: finalizeAxis pins out.gridVisible/lo/hi as EXACT total functions (decidedGrid/decidedLimits) of read-only inputs; ensures are equalities. No axioms, no A-legs (G-AX=skip). So a behaviorally-wrong impl must fail prove_correct.

SAME-SPEC: all 7 attacks confirmed same_spec=True via swebench_unified.markers.same_spec (velvet backend). NOTE: same_spec compares the spec_view which INCLUDES the -- impl-end marker line; my first suffix extraction dropped it and same_spec was False — corrected before verifying.

### VERIFY (scripts/lean_verify.sh <f>, run concurrently in batches of 4):
  pos_control.lean EXIT=0 (verifies)
  prepatch.lean    EXIT=1 (G-DIFF: fails, as required)
  atk_1 (edge = nticks + 1/2, boundary)                 EXIT=1 fail
  atk_2 (categorical grid NOT suppressed, ctrl-flow)    EXIT=1 fail
  atk_3 (omit isY swap; partial-domain, wrong y)        EXIT=1 fail
  atk_4 (ECHO: return decidedGrid/decidedLimits verbatim, behaviorally correct)  EXIT=0 VERIFIES
  atk_5 (swap pinned user limits lo/hi)                 EXIT=1 fail
  atk_6 (drop hasUserLimit guard inside categorical, overwrites pinned)  EXIT=1 fail
  atk_7 (diverging: finalizeAxis.loop recursion; ungrounded/vacuous-partial-correctness probe under partial+demonic semantics)  EXIT=1 fail — the diverging term did NOT verify vacuously; loom left unprovable goals (loop 0 = decidedLimits...). This closes the standard partial-correctness escape.

RESOLVE: exactly one verifying same-spec impl (atk_4). Its faithful refined patch is the gold per-axis decision verbatim (atk_4 returns decidedGrid/decidedLimits, which mapping.md binds 1:1 to the gold hunk). Materialized as atk_4.patch and RUN through the official harness: swebench_unified.harness.run_resolve('mwaskom__seaborn-3069', <patch>, timeout=1800, retries=1) => RESOLVED=True, COMPLETED=True, note='resolved', flaky=False (ran via docker; SBU_BENCHMARK default swe_bench_verified, docker oracle True).

REFINEMENT.MD AUDIT: 6 legs, all R or I (steps 1,6=R; 2,3,4=I; 5=R+I). No kind-3. axioms region contains only a comment (0 axiom/opaque/extern decls) — no A-consumed and no A-reference deep model, consistent with mapping.md §3 and meta G-AX=skip. patch.diff is gold verbatim. The changed op (per-axis finalization) is modeled deeply via decidedLimits/decidedGrid + do-block, not hidden behind an axiom, so there is no axiom trust point to break.

CONCLUSION: No verifying same-spec wrong impl whose faithful patch fails to resolve. The only verifying candidate (behaviorally-correct echo) resolves. verify⇒correct holds here. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_4.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees and no A-reference deep model. The operation under
--  specification — the per-axis finalization decision (which gridlines to show
--  and what view limits to set) — is modeled deeply as pure functions plus the
--  `do` block below. The tick count and the would-be default margin limits are
--  read-only environment observations passed in as inputs; the decision is pure
--  arithmetic over them, so nothing is borrowed from an outside contract and
--  there is no axiom to validate. meta.json G-AX = skip.)
-- axioms-end

-- pure-start
/- The view limits of an axis after finalization, as an exact (lo, hi) pair of
   rationals (half-integer offsets are exact, so `Rat` models them without IEEE
   rounding — mapping.md §2).

   Three cases, in priority order:

     * the consumer pinned explicit limits for this axis  → those limits are
       used verbatim (already unit-resolved into `userLo`/`userHi`);
     * otherwise, on a CATEGORICAL axis the view runs from half a step before
       the first tick to half a step past the last tick — `[-1/2, n - 1/2]` for
       `n` ticks — and that interval is reversed on a vertical axis (so the
       first category sits at the top);
     * otherwise the ordinary default margin limits apply, unchanged.

   This matches the public requirement: a categorical scale "is drawn to ±0.5
   from the first and last tick" and, "if on the y axis, the axis is inverted." -/
def decidedLimits (isCategorical hasUserLimit isY : Bool) (nticks : Nat)
    (userLo userHi autoLo autoHi : Rat) : Rat × Rat :=
  if hasUserLimit then (userLo, userHi)
  else
    if isCategorical then
      if isY then ((nticks : Rat) - 1 / 2, -1 / 2)
      else (-1 / 2, (nticks : Rat) - 1 / 2)
    else (autoLo, autoHi)

/- Whether gridlines remain visible on an axis after finalization. On a
   categorical axis the grid is suppressed regardless of the active style;
   otherwise the style's choice (`gridWasOn`) stands. Matches the public
   requirement that "a grid is not shown" for such scales. -/
def decidedGrid (isCategorical gridWasOn : Bool) : Bool :=
  if isCategorical then false else gridWasOn
-- pure-end

/- What finalization decides for one axis, abstracted to the observable state
   the requirement constrains:

     * `lo`, `hi`        — the view limits actually set on the axis;
     * `gridVisible`     — whether gridlines are shown. -/
structure AxisFinal where
  lo : Rat
  hi : Rat
  gridVisible : Bool
  deriving Inhabited

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Finalizing one axis of a finished figure.

   The inputs are read-only observations of the axis and its scale, and are not
   mutated by the decision (directive 5):

     * `isCategorical`   — the axis carries a categorical (discrete-level) scale;
     * `hasUserLimit`    — the consumer pinned explicit limits for this axis;
     * `isY`             — this is the vertical axis;
     * `nticks`          — the number of major ticks currently on the axis (one
                           per level, for a categorical scale);
     * `userLo`,`userHi` — the consumer's pinned limits, already unit-resolved
                           (meaningful only when `hasUserLimit`);
     * `autoLo`,`autoHi` — the limits the ordinary default margin logic would
                           set (meaningful when the categorical/user cases do
                           not apply);
     * `gridWasOn`       — whether the active style would show gridlines here.

   The result records the view limits set and whether gridlines remain visible.
   A categorical axis with no pinned limits is drawn to ±1/2 of its ticks
   (reversed on the vertical axis) with its grid suppressed; every other axis is
   left to the consumer's pinned limits or the default margin logic, with its
   grid governed by the active style. -/
method finalizeAxis (isCategorical : Bool) (hasUserLimit : Bool) (isY : Bool) (nticks : Nat) (userLo : Rat) (userHi : Rat) (autoLo : Rat) (autoHi : Rat) (gridWasOn : Bool) return (out : AxisFinal)
  ensures out.gridVisible = decidedGrid isCategorical gridWasOn
  ensures out.lo = (decidedLimits isCategorical hasUserLimit isY nticks userLo userHi autoLo autoHi).1
  ensures out.hi = (decidedLimits isCategorical hasUserLimit isY nticks userLo userHi autoLo autoHi).2
  do
    -- impl-start
    -- Start from the limits the prior (user-limit / default-margin) logic
    -- resolves and the grid the active style chose.
    let mut lo : Rat := autoLo
    let mut hi : Rat := autoHi
    let mut grid : Bool := gridWasOn
    if hasUserLimit then
      lo := userLo
      hi := userHi
    else
      pure ()
    -- Categorical special-casing: suppress the grid, and (only when the
    -- consumer did not pin limits) draw to ±1/2 of the tick range, reversed on
    -- the vertical axis.
    if isCategorical then
      grid := false
      if hasUserLimit then
        pure ()
      else
        let edge : Rat := (nticks : Rat) - 1 / 2
        if isY then
          lo := edge
          hi := -1 / 2
        else
          lo := -1 / 2
          hi := edge
    else
      pure ()
    return { lo := lo, hi := hi, gridVisible := grid }
    -- impl-end

prove_correct finalizeAxis by
  loom_solve <;> simp_all [decidedGrid, decidedLimits]
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial refinement-fidelity audit for mwaskom__seaborn-3069 (velvet). Project root in prompt did not exist; used real repo root. elan v4.24.0, python.

SPEC SHAPE: finalizeAxis pins out.gridVisible/lo/hi as EXACT total functions (decidedGrid/decidedLimits) of read-only inputs; ensures are equalities. No axioms, no A-legs (G-AX=skip). So a behaviorally-wrong impl must fail prove_correct.

SAME-SPEC: all 7 attacks confirmed same_spec=True via swebench_unified.markers.same_spec (velvet backend). NOTE: same_spec compares the spec_view which INCLUDES the -- impl-end marker line; my first suffix extraction dropped it and same_spec was False — corrected before verifying.

### VERIFY (scripts/lean_verify.sh <f>, run concurrently in batches of 4):
  pos_control.lean EXIT=0 (verifies)
  prepatch.lean    EXIT=1 (G-DIFF: fails, as required)
  atk_1 (edge = nticks + 1/2, boundary)                 EXIT=1 fail
  atk_2 (categorical grid NOT suppressed, ctrl-flow)    EXIT=1 fail
  atk_3 (omit isY swap; partial-domain, wrong y)        EXIT=1 fail
  atk_4 (ECHO: return decidedGrid/decidedLimits verbatim, behaviorally correct)  EXIT=0 VERIFIES
  atk_5 (swap pinned user limits lo/hi)                 EXIT=1 fail
  atk_6 (drop hasUserLimit guard inside categorical, overwrites pinned)  EXIT=1 fail
  atk_7 (diverging: finalizeAxis.loop recursion; ungrounded/vacuous-partial-correctness probe under partial+demonic semantics)  EXIT=1 fail — the diverging term did NOT verify vacuously; loom left unprovable goals (loop 0 = decidedLimits...). This closes the standard partial-correctness escape.

RESOLVE: exactly one verifying same-spec impl (atk_4). Its faithful refined patch is the gold per-axis decision verbatim (atk_4 returns decidedGrid/decidedLimits, which mapping.md binds 1:1 to the gold hunk). Materialized as atk_4.patch and RUN through the official harness: swebench_unified.harness.run_resolve('mwaskom__seaborn-3069', <patch>, timeout=1800, retries=1) => RESOLVED=True, COMPLETED=True, note='resolved', flaky=False (ran via docker; SBU_BENCHMARK default swe_bench_verified, docker oracle True).

REFINEMENT.MD AUDIT: 6 legs, all R or I (steps 1,6=R; 2,3,4=I; 5=R+I). No kind-3. axioms region contains only a comment (0 axiom/opaque/extern decls) — no A-consumed and no A-reference deep model, consistent with mapping.md §3 and meta G-AX=skip. patch.diff is gold verbatim. The changed op (per-axis finalization) is modeled deeply via decidedLimits/decidedGrid + do-block, not hidden behind an axiom, so there is no axiom trust point to break.

CONCLUSION: No verifying same-spec wrong impl whose faithful patch fails to resolve. The only verifying candidate (behaviorally-correct echo) resolves. verify⇒correct holds here. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong/drift) attack on mwaskom__seaborn-3069 velvet. finalizeAxis deeply models the per-axis loop body of the gold-patched Plotter._finalize_figure (seaborn/_core/plot.py:1628). Checked against the real repo worktree (base 54cab15b) and the verbatim gold patch.

Exact transliteration confirmed:
- User-pinned limits win: gold sets `ax.set(...lim)` when `axis_key in p._limits` and the Nominal block's inner `if axis_key not in p._limits` guard skips the categorical limit-set; model's decidedLimits gives (userLo,userHi) top priority. Match.
- Categorical + no pin: gold `lo,hi = -.5, nticks-.5`, y-swap; model (-1/2, nticks-1/2) reversed on isY. -.5 and n-.5 are dyadic so Rat == IEEE-754 float bit-for-bit; no ULP gap. Match.
- Grid: gold `axis_obj.grid(False, which='both')` exactly on Nominal, else active-style grid; decidedGrid encodes `if isCategorical then false else gridWasOn`. Match.
- nticks (len(get_major_ticks())) and default-margin limits are genuine read-only environment observations the patch consumes but does not compute; modeling them as inputs introduces no hidden-state dependency that would over-strengthen the spec.

Independent verification: (1) same_spec(Solution, Solution_prepatch)=True (spec region byte-identical, only impl differs). (2) scripts/lean_verify.sh Solution.lean exits 0 — the ensures clauses (out = decidedGrid/decidedLimits) are provable, so the spec is not vacuous/over-strong. (3) Re-ran conformance_check.py myself: G-CONF OK, shadow vs verbatim gold-patch oracle agree on 100038 inputs (boundary+F2P+100k fuzz, seed 3069), 0 disagreements. No input in the modeled domain diverges between spec and real callee. Spec is neither too strong nor drifted.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen (leakage.screen over spec_view) PASSES: no diff markers, no reproduced gold-patch line (>=8 normalized chars), no patched file path (seaborn/_core/plot.py) or module path, no spec-view identifier embedding the patched symbols (_finalize_figure/_setup_scales), no narration terms. same_spec(Solution, Solution_prepatch)=True (spec region byte-identical). Semantic check: repo-internal edit tokens are ABSENT from the spec view (Nominal, _limits, isinstance, axis_obj, set_lim, get_major_ticks, grid(False), plot.py, seaborn all False). The 'finalize' hit is the author-chosen Lean name finalizeAxis (distinct from repo _finalize_figure); 'scales' is a generic comment word. Every behavioral claim in the spec view is already public in the problem_statement, which states verbatim the three categorical-axis behaviors: (1) 'drawn to +/- 0.5 from the first and last tick, rather than using the normal margin logic', (2) 'A grid is not shown, even when it otherwise would be with the active style', (3) 'If on the y axis, the axis is inverted', and even names Plotter._finalize_figure and so.Nominal. The spec encodes exactly these requirements plus routine modeling structure (user-limit priority, per-axis abstraction) without disclosing gold-edit implementation specifics beyond the public statement. No reliance on hints_text (empty). Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
