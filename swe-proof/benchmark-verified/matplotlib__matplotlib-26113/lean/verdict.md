# P2 adversarial audit — matplotlib__matplotlib-26113

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec wrong impl produced a closing correct_hexbinAccum with clean axioms, so there is no faithful patch to materialize/resolve. The post-condition problem_spec_hexbinAccum cells mincnt result := (result = cells.map (cellSummary mincnt)) is a COMPLETE functional characterization pinning result to a unique value; any impl not extensionally equal to cells.map (cellSummary mincnt) makes correct_hexbinAccum a false (refutable) proposition, unprovable under the consistent axiom set [propext, Classical.choice, Quot.sound]. Machine-checked refutations at concrete witnesses (refute.lean, exit 0) confirm this for the arithmetic/order/domain families.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -57,7 +57,7 @@
     (cells : List (List Float)) (mincnt : Int) : List (Option Float) := Id.run do
   let mut accum : List (Option Float) := []
   for acc in cells do
-    if (acc.length : Int) ≥ mincnt then
+    if (acc.length : Int) > mincnt then
       accum := accum ++ [some (reduceC acc)]
     else
       accum := accum ++ [none]
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -57,7 +57,7 @@
     (cells : List (List Float)) (mincnt : Int) : List (Option Float) := Id.run do
   let mut accum : List (Option Float) := []
   for acc in cells do
-    if (acc.length : Int) ≥ mincnt then
+    if (acc.length : Int) ≥ mincnt + 1 then
       accum := accum ++ [some (reduceC acc)]
     else
       accum := accum ++ [none]
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -58,9 +58,9 @@
   let mut accum : List (Option Float) := []
   for acc in cells do
     if (acc.length : Int) ≥ mincnt then
-      accum := accum ++ [some (reduceC acc)]
+      accum := [some (reduceC acc)] ++ accum
     else
-      accum := accum ++ [none]
+      accum := [none] ++ accum
   return accum
 -- impl-end
 
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -57,10 +57,7 @@
     (cells : List (List Float)) (mincnt : Int) : List (Option Float) := Id.run do
   let mut accum : List (Option Float) := []
   for acc in cells do
-    if (acc.length : Int) ≥ mincnt then
-      accum := accum ++ [some (reduceC acc)]
-    else
-      accum := accum ++ [none]
+    accum := accum ++ [some (reduceC acc)]
   return accum
 -- impl-end
 
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -57,7 +57,7 @@
     (cells : List (List Float)) (mincnt : Int) : List (Option Float) := Id.run do
   let mut accum : List (Option Float) := []
   for acc in cells do
-    if (acc.length : Int) ≥ mincnt then
+    if (acc.length : Int) ≤ mincnt then
       accum := accum ++ [some (reduceC acc)]
     else
       accum := accum ++ [none]
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -58,7 +58,7 @@
   let mut accum : List (Option Float) := []
   for acc in cells do
     if (acc.length : Int) ≥ mincnt then
-      accum := accum ++ [some (reduceC acc)]
+      accum := accum ++ [some (reduceC acc.reverse)]
     else
       accum := accum ++ [none]
   return accum
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -58,7 +58,7 @@
   let mut accum : List (Option Float) := []
   for acc in cells do
     if (acc.length : Int) ≥ mincnt then
-      accum := accum ++ [some (reduceC acc)]
+      accum := accum ++ [some 0.0]
     else
       accum := accum ++ [none]
   return accum
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Reducing per-cell value collections to a binned grid.

A 2-D plotting routine groups input points into grid cells. When an auxiliary
value array is supplied, every grid cell accumulates the values of the points
that fall into it, and each cell is summarised to a single number by a
user-supplied reduction function. A cell that does not hold enough contributing
points is left empty (marked with the empty/absent sentinel) instead of being
summarised.

The threshold is a single count parameter shared by the whole grid. The desired
rule is:

  * a cell is summarised (its reduction value is produced) exactly when the
    number of points it holds is AT LEAST the threshold;
  * otherwise the cell is left empty.

In particular, with a threshold of `1`, every cell that holds one or more points
is summarised; with a threshold of `0`, every cell — including empty ones — is
summarised. The threshold counts points the same way whether or not auxiliary
values are present: a cell holding exactly the threshold number of points is
summarised, not skipped.
-/

-- axioms-start
-- The per-cell reduction is an UNCHANGED, user-supplied callee: it maps a cell's
-- collection of contributing values to a single summary number. It is applied
-- identically in the specification and the implementation and the result pins no
-- output component on its own, so no property of it is asserted (no `_prop`
-- axiom); only its signature is declared so it can appear in the executable impl.
opaque reduceC : List Float → Float
-- axioms-end

-- pure-start
/-- The summary of one grid cell. `cells` lists, per grid cell, the collection of
contributing values; `mincnt` is the shared count threshold. A cell is summarised
(its reduction value, wrapped in `some`) exactly when it holds at least `mincnt`
points; otherwise it is left empty (`none`). -/
def cellSummary (mincnt : Int) (acc : List Float) : Option Float :=
  if (acc.length : Int) ≥ mincnt then some (reduceC acc) else none
-- pure-end

-- post-conditions-start
/-- The binned grid is, cell by cell, the summary of that cell's collection under
the shared threshold: every cell is summarised iff it holds at least `mincnt`
points, and the grid preserves the order and count of the input cells. -/
def problem_spec_hexbinAccum
    (cells : List (List Float)) (mincnt : Int) (result : List (Option Float)) : Prop :=
  result = cells.map (cellSummary mincnt)
-- post-conditions-end

-- impl-start
def implementation_hexbinAccum
    (cells : List (List Float)) (mincnt : Int) : List (Option Float) := Id.run do
  let mut accum : List (Option Float) := []
  for acc in cells do
    if (acc.length : Int) ≥ mincnt then
      accum := accum ++ [some (reduceC acc)]
    else
      accum := accum ++ [none]
  return accum
-- impl-end

-- proof-start
/-- Helper: the cleaned `forIn` loop, generalized over the accumulator,
computes the running list followed by the per-cell summaries (Route B). -/
private theorem hexbinAccum_forIn
    (cells : List (List Float)) (mincnt : Int) (init : List (Option Float)) :
    Id.run (forIn cells init (fun acc r =>
      (if (acc.length : Int) ≥ mincnt then
        pure (ForInStep.yield (r ++ [some (reduceC acc)]))
      else
        pure (ForInStep.yield (r ++ [none])) : Id _)))
      = init ++ cells.map (cellSummary mincnt) := by
  induction cells generalizing init with
  | nil => simp only [List.map_nil, List.append_nil]; rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind] at ih ⊢
    by_cases h : (a.length : Int) ≥ mincnt <;>
      simp only [h, if_true, if_false, ih, cellSummary, List.map_cons,
        List.append_assoc, List.cons_append, List.nil_append]

theorem correct_hexbinAccum :
    ∀ (cells : List (List Float)) (mincnt : Int),
      problem_spec_hexbinAccum cells mincnt
        (implementation_hexbinAccum cells mincnt) := by
  intro cells mincnt
  unfold problem_spec_hexbinAccum implementation_hexbinAccum
  have h2 : (Id.run do
      let r ← forIn cells ([] : List (Option Float)) fun acc r =>
            if (acc.length : Int) ≥ mincnt then do
              pure PUnit.unit
              pure (ForInStep.yield (r ++ [some (reduceC acc)]))
            else do
              pure PUnit.unit
              pure (ForInStep.yield (r ++ [none]))
      pure r)
      = Id.run (forIn cells ([] : List (Option Float)) (fun acc r =>
          (if (acc.length : Int) ≥ mincnt then
            pure (ForInStep.yield (r ++ [some (reduceC acc)]))
          else
            pure (ForInStep.yield (r ++ [none])) : Id _))) := rfl
  rw [h2, hexbinAccum_forIn]
  simp
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SAME-SPEC: all 8 files (7 attacks + pos) return same_spec=True vs Solution.lean via swebench_unified.markers.same_spec (backend lean) — impl region edited only, axioms/pure/pre/post byte-identical.

POSITIVE CONTROL: pos.lean (= unchanged Solution.lean). cmd: `bash scripts/lean_verify.sh .../pos.lean` -> exit=0. Appended `#print axioms correct_hexbinAccum` (pos_ax.lean) -> 'correct_hexbinAccum depends on axioms: [propext, Classical.choice, Quot.sound]', exit=0. Clean, no sorryAx. Prepatch bug reproduced as atk_1.

ATTACKS (each: `bash scripts/lean_verify.sh .../atk_N.lean`, carrying the ORIGINAL closing proof so a genuinely-wrong impl must fail):
 - atk_1 boundary/control-flow: `> mincnt` (the PREPATCH strict-greater bug) -> exit=1 (proof does not close).
 - atk_2 boundary off-by-one: `≥ mincnt + 1` (extensionally = strict >, distinct syntax) -> exit=1.
 - atk_3 control-flow-effect: prepend instead of append (reverses output order) -> exit=1.
 - atk_4 partial-domain: always summarise, ignore threshold -> exit=1.
 - atk_5 inverted logic: `≤ mincnt` keep test -> exit=1.
 - atk_6 ungrounded-oracle: `reduceC acc.reverse` (needs unasserted reduceC(reverse)=reduceC) -> exit=1.
 - atk_7 ungrounded-oracle echo: `some 0.0` constant instead of reduceC (needs unasserted reduceC=0) -> exit=1.
 Ran concurrently as background jobs, ≤4 at a time (batch1: pos,atk_1,atk_2,atk_3; batch2: atk_4,atk_5,atk_6,atk_7).

No attack closed with clean axioms => step 2 (materialize faithful patch + run_resolve) has no eligible candidate; patches={} correctly (a resolve run is only mandated for a CLOSING clean-axiom wrong impl, of which there are none).

WHY NO CLOSER EXISTS (rigor beyond 'naive proof failed'): the spec is a complete functional characterization. I machine-proved refutations in refute.lean (`bash scripts/lean_verify.sh .../refute.lean` -> exit=0): refute_atk12 (¬spec at cells=[[1.0]],mincnt=1 for the `>` family), refute_atk3 (order at [[1.0],[]],1), refute_atk4 (always-summarise at [[]],1), refute_atk5 (`≤` at [[1.0,2.0]],1). Since these impls provably violate the frozen spec at a concrete input, no correct_ can close for them without making the (consistent) theory inconsistent. atk_6/atk_7 differ from spec on any acc where reduceC is not invariant/zero — a property the axioms region deliberately does NOT assert, so unprovable.

REFINEMENT.MD AUDIT: 5 legs. #1 R (mut/for-loop <-> list comprehension), #2 R (≥ keep test, the fix), #3 A-reference (reduceC applied IDENTICALLY in cellSummary/spec and impl; cancels in proof; NO _prop axiom asserted => G-AX skips correctly, reduceC is an arbitrary user callable not pinned by the fix), #4 R (none <-> np.nan), #5 R (accum <-> np.array). No kind-3 (assumption-only) leg. The lone A-reference leg's correspondence holds: reduceC IS the unchanged user reduce_C_function, applied identically, asserting nothing — consistent with mapping.md provenance (no consumed callee axiom). R/I legs mechanically covered by G-CONF (conformance_check.py, 120010 inputs, 0 disagreements). No opaque Float order on the proof path; the changed op (count comparison) is deeply modeled in Int/Nat.

VERDICT: SOUND — ≥7 distinct same-spec wrong impls all fail to verify, positive control verifies with clean axioms, machine-checked refutations confirm no closes-but-doesn't-resolve witness can exist, and the A-reference leg's correspondence is valid. verify⇒correct holds.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec wrong impl produced a closing correct_hexbinAccum with clean axioms, so there is no faithful patch to materialize/resolve. The post-condition problem_spec_hexbinAccum cells mincnt result := (result = cells.map (cellSummary mincnt)) is a COMPLETE functional characterization pinning result to a unique value; any impl not extensionally equal to cells.map (cellSummary mincnt) makes correct_hexbinAccum a false (refutable) proposition, unprovable under the consistent axiom set [propext, Classical.choice, Quot.sound]. Machine-checked refutations at concrete witnesses (refute.lean, exit 0) confirm this for the arithmetic/order/domain families.
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

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Reducing per-cell value collections to a binned grid.

A 2-D plotting routine groups input points into grid cells. When an auxiliary
value array is supplied, every grid cell accumulates the values of the points
that fall into it, and each cell is summarised to a single number by a
user-supplied reduction function. A cell that does not hold enough contributing
points is left empty (marked with the empty/absent sentinel) instead of being
summarised.

The threshold is a single count parameter shared by the whole grid. The desired
rule is:

  * a cell is summarised (its reduction value is produced) exactly when the
    number of points it holds is AT LEAST the threshold;
  * otherwise the cell is left empty.

In particular, with a threshold of `1`, every cell that holds one or more points
is summarised; with a threshold of `0`, every cell — including empty ones — is
summarised. The threshold counts points the same way whether or not auxiliary
values are present: a cell holding exactly the threshold number of points is
summarised, not skipped.
-/

-- axioms-start
-- The per-cell reduction is an UNCHANGED, user-supplied callee: it maps a cell's
-- collection of contributing values to a single summary number. It is applied
-- identically in the specification and the implementation and the result pins no
-- output component on its own, so no property of it is asserted (no `_prop`
-- axiom); only its signature is declared so it can appear in the executable impl.
opaque reduceC : List Float → Float
-- axioms-end

-- pure-start
/-- The summary of one grid cell. `cells` lists, per grid cell, the collection of
contributing values; `mincnt` is the shared count threshold. A cell is summarised
(its reduction value, wrapped in `some`) exactly when it holds at least `mincnt`
points; otherwise it is left empty (`none`). -/
def cellSummary (mincnt : Int) (acc : List Float) : Option Float :=
  if (acc.length : Int) ≥ mincnt then some (reduceC acc) else none
-- pure-end

-- post-conditions-start
/-- The binned grid is, cell by cell, the summary of that cell's collection under
the shared threshold: every cell is summarised iff it holds at least `mincnt`
points, and the grid preserves the order and count of the input cells. -/
def problem_spec_hexbinAccum
    (cells : List (List Float)) (mincnt : Int) (result : List (Option Float)) : Prop :=
  result = cells.map (cellSummary mincnt)
-- post-conditions-end

-- impl-start
def implementation_hexbinAccum
    (cells : List (List Float)) (mincnt : Int) : List (Option Float) := Id.run do
  let mut accum : List (Option Float) := []
  for acc in cells do
    if (acc.length : Int) ≥ mincnt then
      accum := accum ++ [some (reduceC acc)]
    else
      accum := accum ++ [none]
  return accum
-- impl-end

-- proof-start
/-- Helper: the cleaned `forIn` loop, generalized over the accumulator,
computes the running list followed by the per-cell summaries (Route B). -/
private theorem hexbinAccum_forIn
    (cells : List (List Float)) (mincnt : Int) (init : List (Option Float)) :
    Id.run (forIn cells init (fun acc r =>
      (if (acc.length : Int) ≥ mincnt then
        pure (ForInStep.yield (r ++ [some (reduceC acc)]))
      else
        pure (ForInStep.yield (r ++ [none])) : Id _)))
      = init ++ cells.map (cellSummary mincnt) := by
  induction cells generalizing init with
  | nil => simp only [List.map_nil, List.append_nil]; rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind] at ih ⊢
    by_cases h : (a.length : Int) ≥ mincnt <;>
      simp only [h, if_true, if_false, ih, cellSummary, List.map_cons,
        List.append_assoc, List.cons_append, List.nil_append]

theorem correct_hexbinAccum :
    ∀ (cells : List (List Float)) (mincnt : Int),
      problem_spec_hexbinAccum cells mincnt
        (implementation_hexbinAccum cells mincnt) := by
  intro cells mincnt
  unfold problem_spec_hexbinAccum implementation_hexbinAccum
  have h2 : (Id.run do
      let r ← forIn cells ([] : List (Option Float)) fun acc r =>
            if (acc.length : Int) ≥ mincnt then do
              pure PUnit.unit
              pure (ForInStep.yield (r ++ [some (reduceC acc)]))
            else do
              pure PUnit.unit
              pure (ForInStep.yield (r ++ [none]))
      pure r)
      = Id.run (forIn cells ([] : List (Option Float)) (fun acc r =>
          (if (acc.length : Int) ≥ mincnt then
            pure (ForInStep.yield (r ++ [some (reduceC acc)]))
          else
            pure (ForInStep.yield (r ++ [none])) : Id _))) := rfl
  rw [h2, hexbinAccum_forIn]
  simp
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SAME-SPEC: all 8 files (7 attacks + pos) return same_spec=True vs Solution.lean via swebench_unified.markers.same_spec (backend lean) — impl region edited only, axioms/pure/pre/post byte-identical.

POSITIVE CONTROL: pos.lean (= unchanged Solution.lean). cmd: `bash scripts/lean_verify.sh .../pos.lean` -> exit=0. Appended `#print axioms correct_hexbinAccum` (pos_ax.lean) -> 'correct_hexbinAccum depends on axioms: [propext, Classical.choice, Quot.sound]', exit=0. Clean, no sorryAx. Prepatch bug reproduced as atk_1.

ATTACKS (each: `bash scripts/lean_verify.sh .../atk_N.lean`, carrying the ORIGINAL closing proof so a genuinely-wrong impl must fail):
 - atk_1 boundary/control-flow: `> mincnt` (the PREPATCH strict-greater bug) -> exit=1 (proof does not close).
 - atk_2 boundary off-by-one: `≥ mincnt + 1` (extensionally = strict >, distinct syntax) -> exit=1.
 - atk_3 control-flow-effect: prepend instead of append (reverses output order) -> exit=1.
 - atk_4 partial-domain: always summarise, ignore threshold -> exit=1.
 - atk_5 inverted logic: `≤ mincnt` keep test -> exit=1.
 - atk_6 ungrounded-oracle: `reduceC acc.reverse` (needs unasserted reduceC(reverse)=reduceC) -> exit=1.
 - atk_7 ungrounded-oracle echo: `some 0.0` constant instead of reduceC (needs unasserted reduceC=0) -> exit=1.
 Ran concurrently as background jobs, ≤4 at a time (batch1: pos,atk_1,atk_2,atk_3; batch2: atk_4,atk_5,atk_6,atk_7).

No attack closed with clean axioms => step 2 (materialize faithful patch + run_resolve) has no eligible candidate; patches={} correctly (a resolve run is only mandated for a CLOSING clean-axiom wrong impl, of which there are none).

WHY NO CLOSER EXISTS (rigor beyond 'naive proof failed'): the spec is a complete functional characterization. I machine-proved refutations in refute.lean (`bash scripts/lean_verify.sh .../refute.lean` -> exit=0): refute_atk12 (¬spec at cells=[[1.0]],mincnt=1 for the `>` family), refute_atk3 (order at [[1.0],[]],1), refute_atk4 (always-summarise at [[]],1), refute_atk5 (`≤` at [[1.0,2.0]],1). Since these impls provably violate the frozen spec at a concrete input, no correct_ can close for them without making the (consistent) theory inconsistent. atk_6/atk_7 differ from spec on any acc where reduceC is not invariant/zero — a property the axioms region deliberately does NOT assert, so unprovable.

REFINEMENT.MD AUDIT: 5 legs. #1 R (mut/for-loop <-> list comprehension), #2 R (≥ keep test, the fix), #3 A-reference (reduceC applied IDENTICALLY in cellSummary/spec and impl; cancels in proof; NO _prop axiom asserted => G-AX skips correctly, reduceC is an arbitrary user callable not pinned by the fix), #4 R (none <-> np.nan), #5 R (accum <-> np.array). No kind-3 (assumption-only) leg. The lone A-reference leg's correspondence holds: reduceC IS the unchanged user reduce_C_function, applied identically, asserting nothing — consistent with mapping.md provenance (no consumed callee axiom). R/I legs mechanically covered by G-CONF (conformance_check.py, 120010 inputs, 0 disagreements). No opaque Float order on the proof path; the changed op (count comparison) is deeply modeled in Int/Nat.

VERDICT: SOUND — ≥7 distinct same-spec wrong impls all fail to verify, positive control verifies with clean axioms, machine-checked refutations confirm no closes-but-doesn't-resolve witness can exist, and the A-reference leg's correspondence is valid. verify⇒correct holds.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack found NO drift between the modeled function and the real post-patch callee.

Setup verified: base_commit 5ca694b38d861c0e24cd8743753427dda839b90b matches the worktree. Gold patch (benchmark-verified/.../patch.diff) is exactly `len(acc) > mincnt` -> `len(acc) >= mincnt` at lib/matplotlib/axes/_axes.py:5017 (the `accum` list-comprehension in Axes.hexbin's `C is not None` branch, lines 5016-5020). Modeled boundary = that comprehension (mapping.md/meta modeled_functions agree).

Lean integrity: Solution.lean compiles under scripts/lean_verify.sh (exit 0, no sorry). `#print axioms correct_hexbinAccum` = [propext, Classical.choice, Quot.sound] only -- NO sorryAx, proof is genuine. same_spec(Solution, Solution_prepatch, LeanBackend) = True: spec view is byte-identical, so the prepatch (`> mincnt`) is a real spec-preserving discriminator (G-DIFF/G-GOLD consistent).

Faithfulness dimensions (spec `cellSummary mincnt acc = if (acc.length:Int) >= mincnt then some (reduceC acc) else none`, result = cells.map(cellSummary mincnt)):
- Operator: spec `>=` matches real `>=` exactly, including negative mincnt (Int models Python's unbounded int; mincnt=-1 keeps all cells in both).
- Order/count: real flattens [Cs_at_i1, Cs_at_i2] in iteration order; List.map preserves order+length. `cells` is the legitimate abstraction boundary (post-[1:] flattened per-cell value lists).
- reduce_C_function: applied only on kept cells in real (conditional short-circuit); spec calls reduceC only in the `then` branch, `none` else. Dropped cells never evaluate it in either -> no divergence even if reduce would nan/raise on such input. Modeled identically in spec and impl (opaque reduceC, no _prop axiom) so it cancels and cannot introduce drift.
- Sentinel: np.nan <-> none, reduced value v <-> some v; downstream ~np.isnan filtering is outside the modeled slice.

Differential check: in-process replica of the POST-PATCH comprehension vs the spec model agree on all discriminating inputs (size==mincnt, size mincnt-1, empty cells, empty grid, negative threshold). G-CONF (conformance_check.py, SEED 26113, 120k fuzzed inputs + hand-picked edges, reduceC:=sum, nan:=None) reports disagreements=0, status=pass.

Conclusion: the spec is exactly as strong as the real post-patch callee -- it fully pins order, length, the keep/drop decision, and the kept-cell value, and matches the real behavior on every input in the modeled domain. No too-strong clause and no diverging input exists. Spec is FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view confirmed via swebench_unified.markers.spec_view with LeanBackend.language; same_spec(Solution.lean, Solution_prepatch.lean) == True, so the solver-facing spec (imports/docstring/axioms/pure/post-conditions) is byte-identical between post- and pre-patch and impl+proof are elided. The gold edit is the keep-test flip `len(acc) > mincnt` -> `len(acc) >= mincnt` (keep a cell holding exactly mincnt points). The public problem_statement ALREADY discloses this exact fix in its Resolution section: 'I'd prefer to see the behavior of C is None being applied also when C isn't None (i.e. len(vals) >= mincnt, rather than the current len(vals) > mincnt)'. The spec view encodes the same desired 'AT LEAST'/'exactly the threshold ... summarised, not skipped' behavior but at a strictly higher abstraction (generic '2-D plotting routine', 'grid cells', 'reduction function'; no hexbin/C/reduce_C_function names, no file:line, no list-comprehension structure). Encoding the post-patch behavior is inherent to any spec-based task and is not leakage; nothing in the spec view exceeds what problem_statement already states. Gold-patch specifics (>vs>= mapping, patch.diff line refs) live only in the auditor artifacts mapping.md/refinement.md/patch.diff, which are not part of the solver spec view. No gold-only implementation detail (op sequence, accumulator strategy, proof route) is exposed. Not a relaxed bundle.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
