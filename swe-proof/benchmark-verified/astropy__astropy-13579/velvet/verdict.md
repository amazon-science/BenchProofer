# P2 adversarial audit — astropy__astropy-13579

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 9 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean` |

**Non-vacuity.** The positive control `atk_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -74,6 +74,10 @@
   ensures out = scatter axes supplied
   do
     -- impl-start
+    -- Pre-image skeleton: an absent axis is filled with the constant 1.0 — a
+    -- fixed placeholder — instead of that axis's own reference coordinate
+    -- (a.2). The frozen spec requires `scatter`, which fills absent axes with
+    -- a.2, so prove_correct MUST fail whenever a.2 ≠ 1.0 for some absent axis.
     let mut result : List Float := []
     let mut remaining : List Float := supplied
     let mut i := 0
@@ -85,7 +89,7 @@
       decreasing axes.length - i
     do
       let a := axes[i]!
-      let v : Float := if a.1 then remaining.headD 0 else a.2
+      let v : Float := if a.1 then remaining.headD 0 else 1.0
       result := result ++ [v]
       remaining := if a.1 then remaining.tail else remaining
       i := i + 1
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -85,7 +85,7 @@
       decreasing axes.length - i
     do
       let a := axes[i]!
-      let v : Float := if a.1 then remaining.headD 0 else a.2
+      let v : Float := if a.1 then remaining.headD 0 else 0.0
       result := result ++ [v]
       remaining := if a.1 then remaining.tail else remaining
       i := i + 1
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -85,9 +85,9 @@
       decreasing axes.length - i
     do
       let a := axes[i]!
-      let v : Float := if a.1 then remaining.headD 0 else a.2
+      let v : Float := if a.1 then a.2 else remaining.headD 0
       result := result ++ [v]
-      remaining := if a.1 then remaining.tail else remaining
+      remaining := if a.1 then remaining else remaining.tail
       i := i + 1
     return result
     -- impl-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -87,7 +87,7 @@
       let a := axes[i]!
       let v : Float := if a.1 then remaining.headD 0 else a.2
       result := result ++ [v]
-      remaining := if a.1 then remaining.tail else remaining
+      remaining := remaining
       i := i + 1
     return result
     -- impl-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -74,22 +74,7 @@
   ensures out = scatter axes supplied
   do
     -- impl-start
-    let mut result : List Float := []
-    let mut remaining : List Float := supplied
-    let mut i := 0
-    while i < axes.length
-      invariant i ≤ axes.length
-      invariant result = ((axes.take i).foldl scatterStep (([] : List Float), supplied)).1
-      invariant remaining = ((axes.take i).foldl scatterStep (([] : List Float), supplied)).2
-      done_with i = axes.length
-      decreasing axes.length - i
-    do
-      let a := axes[i]!
-      let v : Float := if a.1 then remaining.headD 0 else a.2
-      result := result ++ [v]
-      remaining := if a.1 then remaining.tail else remaining
-      i := i + 1
-    return result
+    return supplied
     -- impl-end
 
 prove_correct assembleWorldVector by
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -89,7 +89,7 @@
       result := result ++ [v]
       remaining := if a.1 then remaining.tail else remaining
       i := i + 1
-    return result
+    return result.reverse
     -- impl-end
 
 prove_correct assembleWorldVector by
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -74,22 +74,7 @@
   ensures out = scatter axes supplied
   do
     -- impl-start
-    let mut result : List Float := []
-    let mut remaining : List Float := supplied
-    let mut i := 0
-    while i < axes.length
-      invariant i ≤ axes.length
-      invariant result = ((axes.take i).foldl scatterStep (([] : List Float), supplied)).1
-      invariant remaining = ((axes.take i).foldl scatterStep (([] : List Float), supplied)).2
-      done_with i = axes.length
-      decreasing axes.length - i
-    do
-      let a := axes[i]!
-      let v : Float := if a.1 then remaining.headD 0 else a.2
-      result := result ++ [v]
-      remaining := if a.1 then remaining.tail else remaining
-      i := i + 1
-    return result
+    return ([] : List Float)
     -- impl-end
 
 prove_correct assembleWorldVector by
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -87,7 +87,7 @@
       let a := axes[i]!
       let v : Float := if a.1 then remaining.headD 0 else a.2
       result := result ++ [v]
-      remaining := if a.1 then remaining.tail else remaining
+      remaining := remaining.tail
       i := i + 1
     return result
     -- impl-end
```

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

```diff
@@ -85,7 +85,7 @@
       decreasing axes.length - i
     do
       let a := axes[i]!
-      let v : Float := if a.1 then remaining.headD 0 else a.2
+      let v : Float := a.2
       result := result ++ [v]
       remaining := if a.1 then remaining.tail else remaining
       i := i + 1
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No consumed callee contracts. Two callees are involved and BOTH are
--  unchanged: the routine that produces the per-axis reference
--  coordinates, and the lower-level inverse transform. The first supplies a
--  read-only per-axis value carried here as the `.2` component of each axis
--  descriptor; the second consumes the assembled vector and is downstream of
--  the modeled construction. The transformation under spec — assembling the
--  full-dimensional input vector — is modeled DEEPLY below; every observable is
--  computed from the read-only inputs, nothing is borrowed from an oracle.
--  See refinement.md / mapping.md.)
-- axioms-end

-- pure-start
/- One axis descriptor: a flag saying whether this axis is present in the
   lower-dimensional view (`.1`), paired with that axis's reference coordinate
   (`.2`). The reference coordinate is the value the axis takes at the chosen
   reference position; it is meaningful only for axes absent from the view. -/
abbrev Axis := Bool × Float

/- Fold one axis into the (assembled-vector, remaining-supplied-values) state.
   - a present axis emits the next caller-supplied value and consumes it;
   - an absent axis emits that axis's own reference coordinate and consumes
     nothing.
   This threads the supplied values as a stream so each present axis takes the
   next one in order. -/
def scatterStep (acc : List Float × List Float) (a : Axis) : List Float × List Float :=
  (acc.1 ++ [if a.1 then acc.2.headD 0 else a.2],
   if a.1 then acc.2.tail else acc.2)

/- The full-dimensional vector assembled from the axis descriptors and the
   supplied values: present axes are filled, in order, from `supplied`; absent
   axes are filled with their own reference coordinate. Front-recursive via a
   left fold so a single unfold is available per loop step (the fold pattern). -/
def scatter (axes : List Axis) (supplied : List Float) : List Float :=
  (axes.foldl scatterStep (([] : List Float), supplied)).1

/- Forward-fold step: extending the consumed prefix by one axis applies one
   `scatterStep` to the state built from the shorter prefix. The single goal the
   loop body must discharge. -/
lemma scatter_fold_step (axes : List Axis) (supplied : List Float) (i : Nat)
    (hi : i < axes.length) :
    (axes.take (i + 1)).foldl scatterStep (([] : List Float), supplied)
      = scatterStep ((axes.take i).foldl scatterStep (([] : List Float), supplied)) axes[i]! := by
  have hcons : axes.take (i + 1) = axes.take i ++ [axes[i]!] := by
    rw [List.take_succ, List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi]
    simp
  rw [hcons, List.foldl_append, List.foldl_cons, List.foldl_nil]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Assemble the full-dimensional coordinate vector consumed by the inverse
   transform. The lower-dimensional view exposes only the axes flagged present;
   the caller supplies one value per present axis, in order. The result is the
   full vector: each present axis takes the next supplied value; each absent
   axis takes its own reference coordinate (`.2`), the value that axis holds at
   the chosen reference position. `axes` and `supplied` are read-only (not
   `mut`): the loop builds a fresh result and never mutates its inputs. -/
method assembleWorldVector (axes : List Axis) (supplied : List Float)
    return (out : List Float)
  require (axes.filter (·.1)).length = supplied.length
  ensures out = scatter axes supplied
  do
    -- impl-start
    let mut result : List Float := []
    let mut remaining : List Float := supplied
    let mut i := 0
    while i < axes.length
      invariant i ≤ axes.length
      invariant result = ((axes.take i).foldl scatterStep (([] : List Float), supplied)).1
      invariant remaining = ((axes.take i).foldl scatterStep (([] : List Float), supplied)).2
      done_with i = axes.length
      decreasing axes.length - i
    do
      let a := axes[i]!
      let v : Float := if a.1 then remaining.headD 0 else a.2
      result := result ++ [v]
      remaining := if a.1 then remaining.tail else remaining
      i := i + 1
    return result
    -- impl-end

prove_correct assembleWorldVector by
  loom_solve
  all_goals
    first
      | (rw [scatter_fold_step axes supplied i (by omega)]; simp_all [scatterStep])
      | simp_all [scatter, List.take_length]
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: exact functional-equality postcondition `ensures out = scatter axes supplied` under `loom.semantics.termination "total"` (TotalCorrectness). Frozen surface (verified via same_spec, all 9 attacks + pos control = True): imports, set_options, axioms (comment-only), pure region (Axis/scatterStep/scatter/scatter_fold_step), empty pre/post, the method signature+require+ensures, and the prove_correct HEADER. Free to the attacker: the impl-region do-block AND the prove_correct tactic body. Because the postcondition pins `out` to the deterministic function `scatter axes supplied` for ALL admissible inputs, verify <=> out = scatter pointwise; NO same-spec wrong impl can verify. This is why the attack battery has 0 verifiers and 0 resolve runs are NEEDED (protocol step 2 is vacuously satisfied — a resolve run is only required for a verifying wrong impl, of which there are none).

PROTOCOL / TOOLING: cwd=, PATH prepended with. same_spec cmd: python3 markers.same_spec(Solution, atk_N, get_backend('velvet').language) -> True for atk_1..9 and atk_pos. verify cmd (each, run concurrently <=4 as background jobs): `bash scripts/lean_verify.sh atk_N.lean`.

### ATTACK RESULTS (path : exact edit to impl : verify exit : failure site):
- atk_pos.lean : correct impl = shipped Solution.lean : EXIT 0 (verifies) -> POSITIVE CONTROL, spec non-vacuous.
- atk_1.lean : PREPATCH BUG, absent axis -> constant 1.0 : EXIT 1 : unsolved goals at prove_correct 99:34, case invariant_2, goal `(if .. else 1.0) = (if .. else axes[i].2)`. Prepatch reproduced.
- atk_2.lean : absent axis -> constant 0.0 (boundary/other-constant) : EXIT 1 : unsolved goals invariant_2.
- atk_3.lean : SWAPPED branches (present->a.2, absent->supplied head; consume swapped) : EXIT 1 : unsolved goals invariant_2.
- atk_4.lean : CONTROL-FLOW-EFFECT: present axis does NOT advance cursor (`remaining := remaining`) : EXIT 1 : unsolved goals 95:34 (invariant on remaining/result unprovable).
- atk_5.lean : PARTIAL-DOMAIN: `return supplied` (drops absent axes; length+content mismatch) : EXIT 1 : unsolved goals at 80:34.
- atk_6.lean : `return result.reverse` : EXIT 1 : unsolved goals 95:34.
- atk_7.lean : `return []` (empty) : EXIT 1 : unsolved goals.
- atk_8.lean : absent axes ALSO advance cursor (`remaining := remaining.tail` unconditionally) : EXIT 1 : unsolved goals 95:34.
- atk_9.lean : UNGROUNDED-ORACLE ECHO: fill EVERY axis with a.2 (`v := a.2`, ignoring supplied) : EXIT 1 : unsolved goals 95:34, goal `axes[i].1 = true -> axes[i].2 = ...head?.getD 0` (present axis must equal next supplied, not a.2).
All 9 failures are genuine semantic `unsolved goals` at the frozen postcondition (not syntax/timeout/sorry artifacts; grep confirms `error: unsolved goals` at the prove_correct line for each).

REFINEMENT AUDIT (refinement.md / mapping.md): concentrated on A legs per mandate. patch.diff touches ONLY astropy/wcs/wcsapi/wrappers/sliced_wcs.py with exactly two changed lines: (+) `sliced_out_world_coords = self._pixel_to_world_values_all(*[0]*len(self._pixel_keep))` and the else-branch `1.` -> `sliced_out_world_coords[iworld]`. Neither callee DEFINITION (_pixel_to_world_values_all @:212, self._wcs.world_to_pixel_values @:257) is modified — confirmed by grep of the diff. So refinement.md's central claim holds: there are NO A legs (both callees unchanged, supply only read-only inputs carried as Axis.2 / consumed downstream), G-AX is a legitimate skip, and the genuinely-changed op is modeled DEEPLY by scatterStep's `else a.2` branch (A5) rather than hidden behind an axiom -> NO kind-3.

Every leg is R (type refinement: Axis=Bool*Float, List Float carriers) or I (identical concrete op). model<->patch correspondence verified: present-branch A4 (`remaining.headD 0` + `remaining.tail` <-> `world_arrays[iworld_curr]` + `iworld_curr+=1`), absent-branch A5 (`a.2` <-> `sliced_out_world_coords[iworld]`), return A6 (`scatter` <-> `world_arrays_new`, downstream unchanged consumer -> identical assembly => identical pixels). Correspondence holds.

CONCLUSION: >=5 distinct attacks (partial-domain atk_5/7, boundary/constant atk_2, control-flow-effect atk_4/8, swap atk_3, ungrounded-oracle echo atk_9, reverse atk_6, prepatch atk_1) all encoded, all same_spec=True, all verified concurrently, none verifies. Positive control verifies; prepatch reproduced. No verifying wrong impl exists (exact-equality total-correctness spec), so no faithful patch could fail to resolve. verify => correct holds. VERDICT: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 9 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean` |

**Non-vacuity.** The positive control `atk_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 9 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No consumed callee contracts. Two callees are involved and BOTH are
--  unchanged: the routine that produces the per-axis reference
--  coordinates, and the lower-level inverse transform. The first supplies a
--  read-only per-axis value carried here as the `.2` component of each axis
--  descriptor; the second consumes the assembled vector and is downstream of
--  the modeled construction. The transformation under spec — assembling the
--  full-dimensional input vector — is modeled DEEPLY below; every observable is
--  computed from the read-only inputs, nothing is borrowed from an oracle.
--  See refinement.md / mapping.md.)
-- axioms-end

-- pure-start
/- One axis descriptor: a flag saying whether this axis is present in the
   lower-dimensional view (`.1`), paired with that axis's reference coordinate
   (`.2`). The reference coordinate is the value the axis takes at the chosen
   reference position; it is meaningful only for axes absent from the view. -/
abbrev Axis := Bool × Float

/- Fold one axis into the (assembled-vector, remaining-supplied-values) state.
   - a present axis emits the next caller-supplied value and consumes it;
   - an absent axis emits that axis's own reference coordinate and consumes
     nothing.
   This threads the supplied values as a stream so each present axis takes the
   next one in order. -/
def scatterStep (acc : List Float × List Float) (a : Axis) : List Float × List Float :=
  (acc.1 ++ [if a.1 then acc.2.headD 0 else a.2],
   if a.1 then acc.2.tail else acc.2)

/- The full-dimensional vector assembled from the axis descriptors and the
   supplied values: present axes are filled, in order, from `supplied`; absent
   axes are filled with their own reference coordinate. Front-recursive via a
   left fold so a single unfold is available per loop step (the fold pattern). -/
def scatter (axes : List Axis) (supplied : List Float) : List Float :=
  (axes.foldl scatterStep (([] : List Float), supplied)).1

/- Forward-fold step: extending the consumed prefix by one axis applies one
   `scatterStep` to the state built from the shorter prefix. The single goal the
   loop body must discharge. -/
lemma scatter_fold_step (axes : List Axis) (supplied : List Float) (i : Nat)
    (hi : i < axes.length) :
    (axes.take (i + 1)).foldl scatterStep (([] : List Float), supplied)
      = scatterStep ((axes.take i).foldl scatterStep (([] : List Float), supplied)) axes[i]! := by
  have hcons : axes.take (i + 1) = axes.take i ++ [axes[i]!] := by
    rw [List.take_succ, List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi]
    simp
  rw [hcons, List.foldl_append, List.foldl_cons, List.foldl_nil]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Assemble the full-dimensional coordinate vector consumed by the inverse
   transform. The lower-dimensional view exposes only the axes flagged present;
   the caller supplies one value per present axis, in order. The result is the
   full vector: each present axis takes the next supplied value; each absent
   axis takes its own reference coordinate (`.2`), the value that axis holds at
   the chosen reference position. `axes` and `supplied` are read-only (not
   `mut`): the loop builds a fresh result and never mutates its inputs. -/
method assembleWorldVector (axes : List Axis) (supplied : List Float)
    return (out : List Float)
  require (axes.filter (·.1)).length = supplied.length
  ensures out = scatter axes supplied
  do
    -- impl-start
    let mut result : List Float := []
    let mut remaining : List Float := supplied
    let mut i := 0
    while i < axes.length
      invariant i ≤ axes.length
      invariant result = ((axes.take i).foldl scatterStep (([] : List Float), supplied)).1
      invariant remaining = ((axes.take i).foldl scatterStep (([] : List Float), supplied)).2
      done_with i = axes.length
      decreasing axes.length - i
    do
      let a := axes[i]!
      let v : Float := if a.1 then remaining.headD 0 else a.2
      result := result ++ [v]
      remaining := if a.1 then remaining.tail else remaining
      i := i + 1
    return result
    -- impl-end

prove_correct assembleWorldVector by
  loom_solve
  all_goals
    first
      | (rw [scatter_fold_step axes supplied i (by omega)]; simp_all [scatterStep])
      | simp_all [scatter, List.take_length]
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: exact functional-equality postcondition `ensures out = scatter axes supplied` under `loom.semantics.termination "total"` (TotalCorrectness). Frozen surface (verified via same_spec, all 9 attacks + pos control = True): imports, set_options, axioms (comment-only), pure region (Axis/scatterStep/scatter/scatter_fold_step), empty pre/post, the method signature+require+ensures, and the prove_correct HEADER. Free to the attacker: the impl-region do-block AND the prove_correct tactic body. Because the postcondition pins `out` to the deterministic function `scatter axes supplied` for ALL admissible inputs, verify <=> out = scatter pointwise; NO same-spec wrong impl can verify. This is why the attack battery has 0 verifiers and 0 resolve runs are NEEDED (protocol step 2 is vacuously satisfied — a resolve run is only required for a verifying wrong impl, of which there are none).

PROTOCOL / TOOLING: cwd=, PATH prepended with. same_spec cmd: python3 markers.same_spec(Solution, atk_N, get_backend('velvet').language) -> True for atk_1..9 and atk_pos. verify cmd (each, run concurrently <=4 as background jobs): `bash scripts/lean_verify.sh atk_N.lean`.

### ATTACK RESULTS (path : exact edit to impl : verify exit : failure site):
- atk_pos.lean : correct impl = shipped Solution.lean : EXIT 0 (verifies) -> POSITIVE CONTROL, spec non-vacuous.
- atk_1.lean : PREPATCH BUG, absent axis -> constant 1.0 : EXIT 1 : unsolved goals at prove_correct 99:34, case invariant_2, goal `(if .. else 1.0) = (if .. else axes[i].2)`. Prepatch reproduced.
- atk_2.lean : absent axis -> constant 0.0 (boundary/other-constant) : EXIT 1 : unsolved goals invariant_2.
- atk_3.lean : SWAPPED branches (present->a.2, absent->supplied head; consume swapped) : EXIT 1 : unsolved goals invariant_2.
- atk_4.lean : CONTROL-FLOW-EFFECT: present axis does NOT advance cursor (`remaining := remaining`) : EXIT 1 : unsolved goals 95:34 (invariant on remaining/result unprovable).
- atk_5.lean : PARTIAL-DOMAIN: `return supplied` (drops absent axes; length+content mismatch) : EXIT 1 : unsolved goals at 80:34.
- atk_6.lean : `return result.reverse` : EXIT 1 : unsolved goals 95:34.
- atk_7.lean : `return []` (empty) : EXIT 1 : unsolved goals.
- atk_8.lean : absent axes ALSO advance cursor (`remaining := remaining.tail` unconditionally) : EXIT 1 : unsolved goals 95:34.
- atk_9.lean : UNGROUNDED-ORACLE ECHO: fill EVERY axis with a.2 (`v := a.2`, ignoring supplied) : EXIT 1 : unsolved goals 95:34, goal `axes[i].1 = true -> axes[i].2 = ...head?.getD 0` (present axis must equal next supplied, not a.2).
All 9 failures are genuine semantic `unsolved goals` at the frozen postcondition (not syntax/timeout/sorry artifacts; grep confirms `error: unsolved goals` at the prove_correct line for each).

REFINEMENT AUDIT (refinement.md / mapping.md): concentrated on A legs per mandate. patch.diff touches ONLY astropy/wcs/wcsapi/wrappers/sliced_wcs.py with exactly two changed lines: (+) `sliced_out_world_coords = self._pixel_to_world_values_all(*[0]*len(self._pixel_keep))` and the else-branch `1.` -> `sliced_out_world_coords[iworld]`. Neither callee DEFINITION (_pixel_to_world_values_all @:212, self._wcs.world_to_pixel_values @:257) is modified — confirmed by grep of the diff. So refinement.md's central claim holds: there are NO A legs (both callees unchanged, supply only read-only inputs carried as Axis.2 / consumed downstream), G-AX is a legitimate skip, and the genuinely-changed op is modeled DEEPLY by scatterStep's `else a.2` branch (A5) rather than hidden behind an axiom -> NO kind-3.

Every leg is R (type refinement: Axis=Bool*Float, List Float carriers) or I (identical concrete op). model<->patch correspondence verified: present-branch A4 (`remaining.headD 0` + `remaining.tail` <-> `world_arrays[iworld_curr]` + `iworld_curr+=1`), absent-branch A5 (`a.2` <-> `sliced_out_world_coords[iworld]`), return A6 (`scatter` <-> `world_arrays_new`, downstream unchanged consumer -> identical assembly => identical pixels). Correspondence holds.

CONCLUSION: >=5 distinct attacks (partial-domain atk_5/7, boundary/constant atk_2, control-flow-effect atk_4/8, swap atk_3, ungrounded-oracle echo atk_9, reverse atk_6, prepatch atk_1) all encoded, all same_spec=True, all verified concurrently, none verifies. Positive control verifies; prepatch reproduced. No verifying wrong impl exists (exact-equality total-correctness spec), so no faithful patch could fail to resolve. verify => correct holds. VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec region byte-identical (swebench_unified.markers.same_spec(Solution, Solution_prepatch, VelvetBackend.language) = True); only the impl `else` branch differs (a.2 vs 1.0). Solution.lean verifies (lean_verify.sh exit 0); prepatch fails at the discriminating clause (G-DIFF pass). Modeled function assembleWorldVector (spec out = scatter axes supplied) faithfully matches the real repo SlicedLowLevelWCS.world_to_pixel_values assembly of world_arrays_new (sliced_wcs.py:245, base worktree @ 0df94ff7, gold patch verbatim): present axis -> next supplied value with cursor advance == scatterStep present branch (headD/tail); absent axis -> sliced_out_world_coords[iworld] == a.2. The require precondition ((axes.filter (·.1)).length = supplied.length) matches the real function's implicit domain (equal count of kept axes and supplied values; fewer would IndexError, and the model's headD never fires spuriously under the precondition). List Float is a faithful carrier for the scalar F2P case (np.broadcast_arrays is identity on scalars). G-CONF corroborates: transliterated scatter shadow vs the REAL patched callee agree on 100006 inputs, 0 disagreements; I re-read conformance_check.py and confirmed the oracle instantiates and drives the real repo callee (not a re-derivation). No in-domain input found where the spec disagrees with real repo behavior. Spec is neither too strong nor drifted.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Computed the actual consumer spec_view via swebench_unified.markers.spec_view (impl + proof regions elided) and screened it against the leakage standard, judging ONLY against the public problem_statement (not hints_text).

Gold edit: in world_to_pixel_values, an absent (dropped) axis must be filled with its reference world coordinate `sliced_out_world_coords[iworld]` instead of the constant `1.`.

Findings:
- same_spec(Solution.lean, Solution_prepatch.lean) = True (spec region byte-identical); mechanical G-LEAK screen PASSES with 0 hard failures; no relaxation invoked (relaxed_leakage flag None, no RELAXED_LEAKAGE.md).
- No gold-diff line reproduced: gold Python `world_arrays_new.append(sliced_out_world_coords[iworld])` vs type-refined Lean (Axis = Bool × Float, scatter/scatterStep, `a.2`) — no byte collision (normalized-code check clean).
- No diff markers, no patched file path (sliced_wcs.py absent), no patched module path.
- Patched repo symbols are world_to_pixel_values / pixel_to_world_values; spec-view identifiers (assembleWorldVector, scatter, scatterStep, Axis) embed neither, and neither symbol appears in any spec-view comment.
- No bug/fix narration (bug/fix/incorrect/wrong/off-by-one/… scan clean). Crucially, the buggy constant `1.` is NEVER named in the spec view — it appears only in the elided impl and in Solution_prepatch.lean, neither of which is consumer-visible.
- The spec comment "an absent axis emits that axis's own reference coordinate" is an ABSTRACT behavioral specification of correct behavior, inherent to any faithful spec — it localizes no edit, quotes no diff text, and does not name the file/symbol/constant that changed. It does not go beyond the problem_statement in an edit-revealing way: the problem_statement already reports the sliced world_to_pixel returns an erroneous (near-infinite) result; the spec merely states the correct assembled-vector semantics in fully abstracted, type-refined terms.

Conclusion: the spec view does not leak the gold edit beyond the public problem_statement. NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.