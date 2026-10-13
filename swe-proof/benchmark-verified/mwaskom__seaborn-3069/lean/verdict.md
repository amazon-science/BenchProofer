# P2 adversarial audit — mwaskom__seaborn-3069

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -72,15 +72,6 @@
     (isY isNominal hasLimit : Bool) (nticks : Nat) : AxisLayout := Id.run do
   let mut gridHidden := false
   let mut fixedLimit : Option (ℚ × ℚ) := none
-  if isNominal then
-    gridHidden := true
-    if !hasLimit then
-      let lo : ℚ := -1/2
-      let hi : ℚ := (nticks : ℚ) - 1/2
-      if isY then
-        fixedLimit := some (hi, lo)
-      else
-        fixedLimit := some (lo, hi)
   return ⟨gridHidden, fixedLimit⟩
 -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -77,10 +77,7 @@
     if !hasLimit then
       let lo : ℚ := -1/2
       let hi : ℚ := (nticks : ℚ) - 1/2
-      if isY then
-        fixedLimit := some (hi, lo)
-      else
-        fixedLimit := some (lo, hi)
+      fixedLimit := some (lo, hi)
   return ⟨gridHidden, fixedLimit⟩
 -- impl-end
 
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -76,7 +76,7 @@
     gridHidden := true
     if !hasLimit then
       let lo : ℚ := -1/2
-      let hi : ℚ := (nticks : ℚ) - 1/2
+      let hi : ℚ := (nticks : ℚ) + 1/2
       if isY then
         fixedLimit := some (hi, lo)
       else
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -74,13 +74,12 @@
   let mut fixedLimit : Option (ℚ × ℚ) := none
   if isNominal then
     gridHidden := true
-    if !hasLimit then
-      let lo : ℚ := -1/2
-      let hi : ℚ := (nticks : ℚ) - 1/2
-      if isY then
-        fixedLimit := some (hi, lo)
-      else
-        fixedLimit := some (lo, hi)
+    let lo : ℚ := -1/2
+    let hi : ℚ := (nticks : ℚ) - 1/2
+    if isY then
+      fixedLimit := some (hi, lo)
+    else
+      fixedLimit := some (lo, hi)
   return ⟨gridHidden, fixedLimit⟩
 -- impl-end
 
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -76,7 +76,7 @@
     gridHidden := true
     if !hasLimit then
       let lo : ℚ := -1/2
-      let hi : ℚ := (nticks : ℚ) - 1/2
+      let hi : ℚ := 5/2
       if isY then
         fixedLimit := some (hi, lo)
       else
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -70,10 +70,9 @@
 -- impl-start
 def implementation_nominalAxis
     (isY isNominal hasLimit : Bool) (nticks : Nat) : AxisLayout := Id.run do
-  let mut gridHidden := false
+  let mut gridHidden := !isNominal
   let mut fixedLimit : Option (ℚ × ℚ) := none
   if isNominal then
-    gridHidden := true
     if !hasLimit then
       let lo : ℚ := -1/2
       let hi : ℚ := (nticks : ℚ) - 1/2
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -74,13 +74,13 @@
   let mut fixedLimit : Option (ℚ × ℚ) := none
   if isNominal then
     gridHidden := true
-    if !hasLimit then
-      let lo : ℚ := -1/2
-      let hi : ℚ := (nticks : ℚ) - 1/2
-      if isY then
-        fixedLimit := some (hi, lo)
-      else
-        fixedLimit := some (lo, hi)
+  if !hasLimit then
+    let lo : ℚ := -1/2
+    let hi : ℚ := (nticks : ℚ) - 1/2
+    if isY then
+      fixedLimit := some (hi, lo)
+    else
+      fixedLimit := some (lo, hi)
   return ⟨gridHidden, fixedLimit⟩
 -- impl-end
 
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -78,9 +78,9 @@
       let lo : ℚ := -1/2
       let hi : ℚ := (nticks : ℚ) - 1/2
       if isY then
+        fixedLimit := some (lo, hi)
+      else
         fixedLimit := some (hi, lo)
-      else
-        fixedLimit := some (lo, hi)
   return ⟨gridHidden, fixedLimit⟩
 -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Drawing a categorical (nominal) plot axis the way categorical axes are drawn.

When the scale assigned to a plot axis is a nominal/categorical scale, the axis
gets a distinctive treatment at figure-finalization time, mirroring the way the
classic categorical plots draw their category axis:

  * its grid is not shown, even when the active style would otherwise draw one;
  * its extent is pinned to run half a unit beyond the first and last category
    position — i.e. from `-1/2` to `nticks - 1/2`, where `nticks` is the number
    of category tick marks — rather than using the ordinary data-margin logic;
  * on a vertical (`y`) axis that pinned extent is reversed, so the categories
    read from top to bottom.

The pinned extent is applied ONLY when the user has not pinned an explicit limit
on that axis; an explicit limit takes precedence and the categorical extent is
left unset. The grid is hidden for every nominal axis regardless of any explicit
limit. A non-nominal axis is untouched by this step.

We model the two finalization decisions for a single axis as `AxisLayout`:
  * `gridHidden`  — whether finalization forces the grid off for this axis;
  * `fixedLimit`  — `some (lo, hi)` when finalization pins the categorical extent,
                    or `none` when it leaves the extent to the ordinary logic.
Coordinates are exact half-integers, so they are modeled as `ℚ` (rational),
whose order is transparent to the logic.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The number of
-- category tick marks (`nticks`) is taken as an input observation, and the two
-- decisions are a closed expression over the axis orientation, the nominal flag,
-- the explicit-limit flag, and that count. No `opaque`/`axiom` callee contract
-- is needed.
-- axioms-end

-- pure-start
/-- The two finalization decisions for one plot axis. `gridHidden` records
whether the grid is forced off; `fixedLimit` is `some (lo, hi)` when the extent
is pinned, `none` when it is left to the ordinary data-margin logic. -/
structure AxisLayout where
  gridHidden : Bool
  fixedLimit : Option (ℚ × ℚ)
deriving DecidableEq
-- pure-end

-- post-conditions-start
/-- The finalization decisions for a single axis. `isY` is true on a vertical
axis; `isNominal` is true when the axis carries a nominal/categorical scale;
`hasLimit` is true when the user pinned an explicit limit on the axis; `nticks`
is the number of category tick marks.

The grid is hidden exactly when the axis is nominal. The extent is pinned to
`(-1/2, nticks - 1/2)` (reversed on a vertical axis) exactly when the axis is
nominal AND no explicit limit is present; in every other case the extent is left
unset. -/
def problem_spec_nominalAxis
    (isY isNominal hasLimit : Bool) (nticks : Nat) (result : AxisLayout) : Prop :=
  (result.gridHidden = isNominal) ∧
  (isNominal = true → hasLimit = false →
      result.fixedLimit
        = some (if isY then ((nticks : ℚ) - 1/2, -1/2)
                else (-1/2, (nticks : ℚ) - 1/2))) ∧
  (isNominal = false → result.fixedLimit = none) ∧
  (hasLimit = true → result.fixedLimit = none)
-- post-conditions-end

-- impl-start
def implementation_nominalAxis
    (isY isNominal hasLimit : Bool) (nticks : Nat) : AxisLayout := Id.run do
  let mut gridHidden := false
  let mut fixedLimit : Option (ℚ × ℚ) := none
  if isNominal then
    gridHidden := true
    if !hasLimit then
      let lo : ℚ := -1/2
      let hi : ℚ := (nticks : ℚ) - 1/2
      if isY then
        fixedLimit := some (hi, lo)
      else
        fixedLimit := some (lo, hi)
  return ⟨gridHidden, fixedLimit⟩
-- impl-end

-- proof-start
theorem correct_nominalAxis :
    ∀ (isY isNominal hasLimit : Bool) (nticks : Nat),
      problem_spec_nominalAxis isY isNominal hasLimit nticks
        (implementation_nominalAxis isY isNominal hasLimit nticks) := by
  intro isY isNominal hasLimit nticks
  unfold problem_spec_nominalAxis implementation_nominalAxis
  cases isNominal <;> cases hasLimit <;> cases isY <;>
    exact ⟨rfl, by intro h; simp_all, by intro h; simp_all, by intro h; simp_all⟩
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Positive control (gold Solution.lean copy) verifies exit 0 (clean). All 8 same-spec wrong impls (same_spec=True verified for each; only impl region edited, axioms/pure/pre/post byte-identical) FAIL to verify (exit 1, genuine 'unsolved goals'/'Application type mismatch' proof-closure errors, no sorry/no timeout). NONE closed with clean axioms, so per protocol no faithful patch materialization/resolve run was required (that step is triggered only for a verifying wrong impl).

Why sound: problem_spec_nominalAxis fully pins BOTH output components in EVERY input case -- gridHidden=isNominal (clause 1, all inputs); fixedLimit = some(exact half-integer extent, y-reversed) when nominal & !hasLimit (clause 2), = none when !nominal (clause 3), = none when hasLimit (clause 4). Both (isNominal,hasLimit) combos x orientation are covered => the spec is a COMPLETE function graph, so any verifying impl is extensionally equal to gold; no same-spec wrong impl can close any proof.

Attack coverage (DISTINCT failure modes): atk_1 prepatch bug (no special-casing, always default) -> reproduces discriminating-clause failure; atk_2 partial-domain (omit y-axis reversal); atk_3 boundary (nticks+1/2 offset instead of -1/2); atk_4 control-flow-effect (ignore hasLimit, pin extent whenever nominal -> violates clause 4); atk_5 ungrounded-oracle echo (hardcode F2P answer hi=5/2); atk_6 grid decision wrong (gridHidden=!isNominal); atk_7 frame violation (pin extent on non-nominal axis -> violates clause 3); atk_8 wrong-axis reversal (swap on x instead of y). All 8 fail to verify.

A-leg / refinement audit: refinement.md legs are all R/I; there is NO A-tagged content. No callee axioms are declared (axioms-start block empty of opaque/axiom; axiom_check.py is a legitimate SKIP STUB -- the two decisions are a closed arithmetic/Boolean expression over the four inputs isY/isNominal/hasLimit/nticks, no unchanged repo callee contract consumed). No kind-3 legs present. R/I correspondence to patch.diff is faithful and validated by conformance_check.py: oracle_axis replicates the post-patch block (grid off when Nominal; extent (-.5, nticks-.5) reversed to (hi,lo) on y, only when axis_key not in _limits) exactly, using Fraction for exact half-integers matching the Lean Q model; edge cross-product + >=1e5 fuzz, 0 disagreements. mapping.md input<->Python bijection (isY=axis=='y', isNominal=isinstance(...,Nominal), hasLimit=axis_key in _limits, nticks=len(get_major_ticks())) holds.

Commands: positive control + each attack run as `bash scripts/lean_verify.sh <path>`. pos_control EXIT=0; atk_1..8 EXIT=1 (verified concurrently in two <=4 batches). same_spec checked via swebench_unified.markers.same_spec on lean backend = True for all 8.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

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
Drawing a categorical (nominal) plot axis the way categorical axes are drawn.

When the scale assigned to a plot axis is a nominal/categorical scale, the axis
gets a distinctive treatment at figure-finalization time, mirroring the way the
classic categorical plots draw their category axis:

  * its grid is not shown, even when the active style would otherwise draw one;
  * its extent is pinned to run half a unit beyond the first and last category
    position — i.e. from `-1/2` to `nticks - 1/2`, where `nticks` is the number
    of category tick marks — rather than using the ordinary data-margin logic;
  * on a vertical (`y`) axis that pinned extent is reversed, so the categories
    read from top to bottom.

The pinned extent is applied ONLY when the user has not pinned an explicit limit
on that axis; an explicit limit takes precedence and the categorical extent is
left unset. The grid is hidden for every nominal axis regardless of any explicit
limit. A non-nominal axis is untouched by this step.

We model the two finalization decisions for a single axis as `AxisLayout`:
  * `gridHidden`  — whether finalization forces the grid off for this axis;
  * `fixedLimit`  — `some (lo, hi)` when finalization pins the categorical extent,
                    or `none` when it leaves the extent to the ordinary logic.
Coordinates are exact half-integers, so they are modeled as `ℚ` (rational),
whose order is transparent to the logic.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The number of
-- category tick marks (`nticks`) is taken as an input observation, and the two
-- decisions are a closed expression over the axis orientation, the nominal flag,
-- the explicit-limit flag, and that count. No `opaque`/`axiom` callee contract
-- is needed.
-- axioms-end

-- pure-start
/-- The two finalization decisions for one plot axis. `gridHidden` records
whether the grid is forced off; `fixedLimit` is `some (lo, hi)` when the extent
is pinned, `none` when it is left to the ordinary data-margin logic. -/
structure AxisLayout where
  gridHidden : Bool
  fixedLimit : Option (ℚ × ℚ)
deriving DecidableEq
-- pure-end

-- post-conditions-start
/-- The finalization decisions for a single axis. `isY` is true on a vertical
axis; `isNominal` is true when the axis carries a nominal/categorical scale;
`hasLimit` is true when the user pinned an explicit limit on the axis; `nticks`
is the number of category tick marks.

The grid is hidden exactly when the axis is nominal. The extent is pinned to
`(-1/2, nticks - 1/2)` (reversed on a vertical axis) exactly when the axis is
nominal AND no explicit limit is present; in every other case the extent is left
unset. -/
def problem_spec_nominalAxis
    (isY isNominal hasLimit : Bool) (nticks : Nat) (result : AxisLayout) : Prop :=
  (result.gridHidden = isNominal) ∧
  (isNominal = true → hasLimit = false →
      result.fixedLimit
        = some (if isY then ((nticks : ℚ) - 1/2, -1/2)
                else (-1/2, (nticks : ℚ) - 1/2))) ∧
  (isNominal = false → result.fixedLimit = none) ∧
  (hasLimit = true → result.fixedLimit = none)
-- post-conditions-end

-- impl-start
def implementation_nominalAxis
    (isY isNominal hasLimit : Bool) (nticks : Nat) : AxisLayout := Id.run do
  let mut gridHidden := false
  let mut fixedLimit : Option (ℚ × ℚ) := none
  if isNominal then
    gridHidden := true
    if !hasLimit then
      let lo : ℚ := -1/2
      let hi : ℚ := (nticks : ℚ) - 1/2
      if isY then
        fixedLimit := some (hi, lo)
      else
        fixedLimit := some (lo, hi)
  return ⟨gridHidden, fixedLimit⟩
-- impl-end

-- proof-start
theorem correct_nominalAxis :
    ∀ (isY isNominal hasLimit : Bool) (nticks : Nat),
      problem_spec_nominalAxis isY isNominal hasLimit nticks
        (implementation_nominalAxis isY isNominal hasLimit nticks) := by
  intro isY isNominal hasLimit nticks
  unfold problem_spec_nominalAxis implementation_nominalAxis
  cases isNominal <;> cases hasLimit <;> cases isY <;>
    exact ⟨rfl, by intro h; simp_all, by intro h; simp_all, by intro h; simp_all⟩
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Positive control (gold Solution.lean copy) verifies exit 0 (clean). All 8 same-spec wrong impls (same_spec=True verified for each; only impl region edited, axioms/pure/pre/post byte-identical) FAIL to verify (exit 1, genuine 'unsolved goals'/'Application type mismatch' proof-closure errors, no sorry/no timeout). NONE closed with clean axioms, so per protocol no faithful patch materialization/resolve run was required (that step is triggered only for a verifying wrong impl).

Why sound: problem_spec_nominalAxis fully pins BOTH output components in EVERY input case -- gridHidden=isNominal (clause 1, all inputs); fixedLimit = some(exact half-integer extent, y-reversed) when nominal & !hasLimit (clause 2), = none when !nominal (clause 3), = none when hasLimit (clause 4). Both (isNominal,hasLimit) combos x orientation are covered => the spec is a COMPLETE function graph, so any verifying impl is extensionally equal to gold; no same-spec wrong impl can close any proof.

Attack coverage (DISTINCT failure modes): atk_1 prepatch bug (no special-casing, always default) -> reproduces discriminating-clause failure; atk_2 partial-domain (omit y-axis reversal); atk_3 boundary (nticks+1/2 offset instead of -1/2); atk_4 control-flow-effect (ignore hasLimit, pin extent whenever nominal -> violates clause 4); atk_5 ungrounded-oracle echo (hardcode F2P answer hi=5/2); atk_6 grid decision wrong (gridHidden=!isNominal); atk_7 frame violation (pin extent on non-nominal axis -> violates clause 3); atk_8 wrong-axis reversal (swap on x instead of y). All 8 fail to verify.

A-leg / refinement audit: refinement.md legs are all R/I; there is NO A-tagged content. No callee axioms are declared (axioms-start block empty of opaque/axiom; axiom_check.py is a legitimate SKIP STUB -- the two decisions are a closed arithmetic/Boolean expression over the four inputs isY/isNominal/hasLimit/nticks, no unchanged repo callee contract consumed). No kind-3 legs present. R/I correspondence to patch.diff is faithful and validated by conformance_check.py: oracle_axis replicates the post-patch block (grid off when Nominal; extent (-.5, nticks-.5) reversed to (hi,lo) on y, only when axis_key not in _limits) exactly, using Fraction for exact half-integers matching the Lean Q model; edge cross-product + >=1e5 fuzz, 0 disagreements. mapping.md input<->Python bijection (isY=axis=='y', isNominal=isinstance(...,Nominal), hasLimit=axis_key in _limits, nticks=len(get_major_ticks())) holds.

Commands: positive control + each attack run as `bash scripts/lean_verify.sh <path>`. pos_control EXIT=0; atk_1..8 EXIT=1 (verified concurrently in two <=4 batches). same_spec checked via swebench_unified.markers.same_spec on lean backend = True for all 8.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack: no diverging input found; spec is NOT too strong / does not drift from the real post-patch behavior.

Mechanical checks:
- Solution.lean compiles under scripts/lean_verify.sh (exit 0).
- `#print axioms correct_nominalAxis` => [propext, Classical.choice, Quot.sound]; NO sorryAx, proof is genuine.
- swebench_unified.markers.same_spec(Solution.lean, Solution_prepatch.lean, lean) == True: spec region byte-identical/stable.

Modeled function: nominalAxis = the per-axis categorical special-casing block added to Plotter._finalize_figure (verified against post-patch code in patch.diff and base worktree). Post-patch real code per axis:
  if isinstance(self._scales.get(axis_key), Nominal):
      axis_obj.grid(False, which='both')
      if axis_key not in p._limits:
          nticks = len(axis_obj.get_major_ticks())
          lo, hi = -.5, nticks - .5
          if axis == 'y': lo, hi = hi, lo
          set_{axis}lim(lo, hi, auto=None)

Exhaustive comparison of the 4 spec clauses to the real decision over the entire input domain (isY, isNominal, hasLimit, nticks):
1. gridHidden = isNominal: real code forces grid off iff Nominal; non-nominal never forced off. Matches both boolean cases.
2. isNominal & !hasLimit -> fixedLimit = some(y:(nticks-1/2,-1/2) | x:(-1/2,nticks-1/2)): exactly the -.5 / nticks-.5 pair with the y-swap; half-integers exact in Q. Matches.
3. !isNominal -> fixedLimit=none: nominal block skipped, no categorical pin. Matches.
4. hasLimit -> fixedLimit=none: `if axis_key not in p._limits` guard blocks the categorical set_lim(...,auto=None) call. The earlier explicit-limit block uses a different call (ax.set) and is outside the modeled decision boundary; fixedLimit tracks only the categorical auto=None pin. Consistent boundary, matches.

Spec pins both output components in every input case (no over-constraint, no under-constraint): isNominal&hasLimit -> (gridHidden=true, fixedLimit=none) correct; nticks=0 -> degenerate but faithful (-1/2,-1/2); non-nominal untouched. No input on which the spec asserts an output the real per-axis categorical decision does not produce. The 8-combo boolean cross-product x boundary nticks plus >=1e5 fuzz in conformance_check.py corroborates 0 disagreements between the R/I shadow and an in-process replica of the real decision.

No weakness of type 'spec too strong / drift' found. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (leakage.screen: 0 hard failures, 0 warnings). same_spec(patched, prepatch) = True; spec region byte-identical. Spec view contains no patched file path (seaborn/_core/plot.py), no diff-touched repo symbols (Nominal, _scales, _limits, _finalize_figure, get_major_ticks, set_xlim, axis_obj), no diff markers, no reproduced gold-patch line, and no bug/fix narration. Semantic check vs the PUBLIC problem_statement only (not hints): every behavioral fact the spec asserts is already disclosed in problem_statement — bullet 1 'scale drawn to +/- 0.5 from first and last tick rather than normal margin logic' = the (-1/2, nticks-1/2) extent; bullet 2 'grid not shown even when active style would draw one' = gridHidden ⇔ nominal; bullet 3 'if on the y axis, the axis is inverted' = the y reversal of the extent. The only extra modeling detail (extent applies only when no explicit user limit is pinned) is a natural specification consequence of the pre-existing explicit-limit logic, not a disclosure of the gold edit's location or identifiers. The spec view is expressed in fully abstracted terms (isY/isNominal/hasLimit/nticks, AxisLayout.gridHidden/fixedLimit) and is if anything less edit-revealing than problem_statement itself (which names Plotter._finalize_figure and suggests approaches). No line leaks the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
