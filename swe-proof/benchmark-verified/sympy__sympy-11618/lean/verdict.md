# P2 adversarial audit — sympy__sympy-11618

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_5.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -71,7 +71,7 @@
 
 -- impl-start
 def implementation_sqSeparation (sameKind : Bool) (a b : List Rat) : Rat := Id.run do
-  let n := if sameKind then min a.length b.length else max a.length b.length
+  let n := min a.length b.length
   let mut acc : Rat := 0
   for i in [0:n] do
     acc := acc + (a.getD i 0 - b.getD i 0) ^ 2
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -71,7 +71,7 @@
 
 -- impl-start
 def implementation_sqSeparation (sameKind : Bool) (a b : List Rat) : Rat := Id.run do
-  let n := if sameKind then min a.length b.length else max a.length b.length
+  let n := max a.length b.length
   let mut acc : Rat := 0
   for i in [0:n] do
     acc := acc + (a.getD i 0 - b.getD i 0) ^ 2
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -71,7 +71,7 @@
 
 -- impl-start
 def implementation_sqSeparation (sameKind : Bool) (a b : List Rat) : Rat := Id.run do
-  let n := if sameKind then min a.length b.length else max a.length b.length
+  let n := if sameKind then max a.length b.length else min a.length b.length
   let mut acc : Rat := 0
   for i in [0:n] do
     acc := acc + (a.getD i 0 - b.getD i 0) ^ 2
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -73,7 +73,7 @@
 def implementation_sqSeparation (sameKind : Bool) (a b : List Rat) : Rat := Id.run do
   let n := if sameKind then min a.length b.length else max a.length b.length
   let mut acc : Rat := 0
-  for i in [0:n] do
+  for i in [0:n-1] do
     acc := acc + (a.getD i 0 - b.getD i 0) ^ 2
   return acc
 -- impl-end
```

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -70,12 +70,8 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_sqSeparation (sameKind : Bool) (a b : List Rat) : Rat := Id.run do
-  let n := if sameKind then min a.length b.length else max a.length b.length
-  let mut acc : Rat := 0
-  for i in [0:n] do
-    acc := acc + (a.getD i 0 - b.getD i 0) ^ 2
-  return acc
+def implementation_sqSeparation (sameKind : Bool) (a b : List Rat) : Rat :=
+  sqSep sameKind a b
 -- impl-end
 
 -- proof-start
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -74,7 +74,7 @@
   let n := if sameKind then min a.length b.length else max a.length b.length
   let mut acc : Rat := 0
   for i in [0:n] do
-    acc := acc + (a.getD i 0 - b.getD i 0) ^ 2
+    acc := acc + (a.getD i 0 - b.getD i 0)
   return acc
 -- impl-end
 
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -70,12 +70,7 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_sqSeparation (sameKind : Bool) (a b : List Rat) : Rat := Id.run do
-  let n := if sameKind then min a.length b.length else max a.length b.length
-  let mut acc : Rat := 0
-  for i in [0:n] do
-    acc := acc + (a.getD i 0 - b.getD i 0) ^ 2
-  return acc
+def implementation_sqSeparation (sameKind : Bool) (a b : List Rat) : Rat := 0
 -- impl-end
 
 -- proof-start
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
The squared Euclidean separation between two points given by their finite
sequences of numeric coordinates.

A point in `n`-dimensional space is described by its ordered list of
coordinates. The Euclidean separation between two points is obtained from the
sum of the squared differences of their coordinates, taken coordinate by
coordinate. The actual distance is the square root of that sum; the square root
is a constant, order-preserving outer wrapper, so the quantity that fully
determines the distance is this sum of squared coordinate differences — the
radicand — and that is what is specified here.

The two sequences may have DIFFERENT dimensions, and the dimension the
comparison is carried out in depends on whether the two points are of the SAME
kind (`sameKind = true`) or of DIFFERENT kinds (`sameKind = false`):

* When the two points are of the same kind, the comparison runs in the SMALLER
  of the two dimensions: positions present in only the longer sequence are
  dropped (the plain coordinate-by-coordinate pairing truncates to the shorter
  sequence).
* When the two points are of different kinds, the comparison runs in the LARGER
  of the two dimensions: the shorter sequence is embedded at the origin of the
  larger ambient space, so a position present in only one sequence still
  contributes the square of that sequence's coordinate (the missing trailing
  coordinates of the shorter sequence read as zero), and must NOT be dropped.

Thus a position beyond the compared dimension contributes nothing, and a
position within it where one sequence is too short reads that sequence's
coordinate as `0`.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The quantity
-- is modeled DEEPLY and structurally over the two coordinate sequences (summing
-- squared coordinate differences across the compared dimension, with missing
-- coordinates within that dimension read as zero). The square-root outer wrapper
-- is constant and order-preserving, hence modeled away. So no `opaque`/`axiom`
-- callee contract is needed.
-- axioms-end

-- pure-start
/-- The ambient dimension the two coordinate sequences are compared in. When the
two points are of the same kind (`sameKind = true`) the comparison runs in the
SMALLER dimension (the truncating coordinate pairing); when they are of
different kinds it runs in the LARGER dimension (the shorter sequence is
zero-embedded into the larger ambient space). -/
def commonLen (sameKind : Bool) (a b : List Rat) : Nat :=
  if sameKind then min a.length b.length else max a.length b.length

/-- The squared separation of two coordinate sequences `a` and `b` with kind
discriminator `sameKind`: the sum, over every position `i` below the compared
dimension `commonLen sameKind a b`, of the squared difference of the coordinates
at `i`, where a sequence too short to have a coordinate at position `i` reads as
`0` there. Front-aligned accumulator fold over the positions
`0, 1, …, commonLen sameKind a b - 1`. -/
def sqSep (sameKind : Bool) (a b : List Rat) : Rat :=
  (List.range (commonLen sameKind a b)).foldl
    (fun acc i => acc + (a.getD i 0 - b.getD i 0) ^ 2) 0
-- pure-end

-- post-conditions-start
/-- The reported squared separation is exactly the sum of squared coordinate
differences over every position up to the compared dimension (missing
coordinates counting as zero): `result = sqSep sameKind a b`. -/
def problem_spec_sqSeparation (sameKind : Bool) (a b : List Rat) (result : Rat) : Prop :=
  result = sqSep sameKind a b
-- post-conditions-end

-- impl-start
def implementation_sqSeparation (sameKind : Bool) (a b : List Rat) : Rat := Id.run do
  let n := if sameKind then min a.length b.length else max a.length b.length
  let mut acc : Rat := 0
  for i in [0:n] do
    acc := acc + (a.getD i 0 - b.getD i 0) ^ 2
  return acc
-- impl-end

-- proof-start
theorem correct_sqSeparation : ∀ (sameKind : Bool) (a b : List Rat),
    problem_spec_sqSeparation sameKind a b (implementation_sqSeparation sameKind a b) := by
  intro sameKind a b
  unfold problem_spec_sqSeparation implementation_sqSeparation sqSep commonLen
  simp [List.range_eq_range']
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Spec postcondition is a tight functional equality: result = sqSep sameKind a b, with commonLen = if sameKind then min else max. No axioms (axioms region empty; G-AX skips). All refinement.md legs are R (A1-A3, A7) or I (A4-A6) — no A-consumed/A-reference, no kind-3. The deeply-modeled changed op (kind-keyed min/max compared dimension + zero-embedding via getD) is structural, matching the gold post-patch distance radicand.

same_spec=True for all 7 attacks + positive_control (axioms/pure/pre/post byte-identical; only impl region edited).

Commands: bash scripts/lean_verify.sh <path>, run concurrently (batches of 4).
Results:
- atk_1 prepatch bug (n:=min a.length b.length unconditionally): exit 1 (proof unclosable). Reproduces the base_commit truncation bug -> prepatch_reproduced=True.
- atk_2 partial-domain (n:=max unconditionally; wrong for sameKind=true unequal lengths): exit 1.
- atk_3 control-flow-effect (branches swapped: if sameKind then max else min): exit 1.
- atk_4 boundary/off-by-one (loop [0:n-1], drops last coord): exit 1.
- atk_5 ungrounded-oracle echo (return sqSep sameKind a b): exit 0 (VERIFIES). #print axioms correct_sqSeparation => [propext, Classical.choice, Quot.sound] (clean); no sorry. This impl is behaviorally identical to the deep model = the gold post-patch radicand.
- atk_6 no-square ((a-b) not squared): exit 1.
- atk_7 ungrounded constant (return 0): exit 1.
- pos_control (gold impl, identical to Solution.lean): exit 0, clean axioms, no sorry.

MANDATORY resolve of every clean-axiom-verifying impl: only atk_5 closes. Its faithful refined patch (atk_5 computes exactly the post-patch radicand sqSep = gold behavior) IS the gold patch. Executed official harness: from PYTHONPATH=src, swebench_unified.harness.run_resolve('sympy__sympy-11618', gold_patch, run_id='sbu-audit-atk5-echo') => resolved=True, note='resolved'. So the sole verifying impl RESOLVES. No verify-but-not-resolve counterexample exists.

Because the postcondition pins result to sqSep exactly (universally quantified over sameKind,a,b), any impl whose correct_sqSeparation closes is forced pointwise-equal to sqSep, i.e. behaviorally the gold radicand; all 6 behaviorally-wrong impls fail to close (exit 1). Refinement audit passes: R/I legs, no kind-3, A-legs correspond to real callees (self.args/p.args/type-discriminator/sqrt outer wrapper). verify => resolve holds. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_5.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
The squared Euclidean separation between two points given by their finite
sequences of numeric coordinates.

A point in `n`-dimensional space is described by its ordered list of
coordinates. The Euclidean separation between two points is obtained from the
sum of the squared differences of their coordinates, taken coordinate by
coordinate. The actual distance is the square root of that sum; the square root
is a constant, order-preserving outer wrapper, so the quantity that fully
determines the distance is this sum of squared coordinate differences — the
radicand — and that is what is specified here.

The two sequences may have DIFFERENT dimensions, and the dimension the
comparison is carried out in depends on whether the two points are of the SAME
kind (`sameKind = true`) or of DIFFERENT kinds (`sameKind = false`):

* When the two points are of the same kind, the comparison runs in the SMALLER
  of the two dimensions: positions present in only the longer sequence are
  dropped (the plain coordinate-by-coordinate pairing truncates to the shorter
  sequence).
* When the two points are of different kinds, the comparison runs in the LARGER
  of the two dimensions: the shorter sequence is embedded at the origin of the
  larger ambient space, so a position present in only one sequence still
  contributes the square of that sequence's coordinate (the missing trailing
  coordinates of the shorter sequence read as zero), and must NOT be dropped.

Thus a position beyond the compared dimension contributes nothing, and a
position within it where one sequence is too short reads that sequence's
coordinate as `0`.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The quantity
-- is modeled DEEPLY and structurally over the two coordinate sequences (summing
-- squared coordinate differences across the compared dimension, with missing
-- coordinates within that dimension read as zero). The square-root outer wrapper
-- is constant and order-preserving, hence modeled away. So no `opaque`/`axiom`
-- callee contract is needed.
-- axioms-end

-- pure-start
/-- The ambient dimension the two coordinate sequences are compared in. When the
two points are of the same kind (`sameKind = true`) the comparison runs in the
SMALLER dimension (the truncating coordinate pairing); when they are of
different kinds it runs in the LARGER dimension (the shorter sequence is
zero-embedded into the larger ambient space). -/
def commonLen (sameKind : Bool) (a b : List Rat) : Nat :=
  if sameKind then min a.length b.length else max a.length b.length

/-- The squared separation of two coordinate sequences `a` and `b` with kind
discriminator `sameKind`: the sum, over every position `i` below the compared
dimension `commonLen sameKind a b`, of the squared difference of the coordinates
at `i`, where a sequence too short to have a coordinate at position `i` reads as
`0` there. Front-aligned accumulator fold over the positions
`0, 1, …, commonLen sameKind a b - 1`. -/
def sqSep (sameKind : Bool) (a b : List Rat) : Rat :=
  (List.range (commonLen sameKind a b)).foldl
    (fun acc i => acc + (a.getD i 0 - b.getD i 0) ^ 2) 0
-- pure-end

-- post-conditions-start
/-- The reported squared separation is exactly the sum of squared coordinate
differences over every position up to the compared dimension (missing
coordinates counting as zero): `result = sqSep sameKind a b`. -/
def problem_spec_sqSeparation (sameKind : Bool) (a b : List Rat) (result : Rat) : Prop :=
  result = sqSep sameKind a b
-- post-conditions-end

-- impl-start
def implementation_sqSeparation (sameKind : Bool) (a b : List Rat) : Rat := Id.run do
  let n := if sameKind then min a.length b.length else max a.length b.length
  let mut acc : Rat := 0
  for i in [0:n] do
    acc := acc + (a.getD i 0 - b.getD i 0) ^ 2
  return acc
-- impl-end

-- proof-start
theorem correct_sqSeparation : ∀ (sameKind : Bool) (a b : List Rat),
    problem_spec_sqSeparation sameKind a b (implementation_sqSeparation sameKind a b) := by
  intro sameKind a b
  unfold problem_spec_sqSeparation implementation_sqSeparation sqSep commonLen
  simp [List.range_eq_range']
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Spec postcondition is a tight functional equality: result = sqSep sameKind a b, with commonLen = if sameKind then min else max. No axioms (axioms region empty; G-AX skips). All refinement.md legs are R (A1-A3, A7) or I (A4-A6) — no A-consumed/A-reference, no kind-3. The deeply-modeled changed op (kind-keyed min/max compared dimension + zero-embedding via getD) is structural, matching the gold post-patch distance radicand.

same_spec=True for all 7 attacks + positive_control (axioms/pure/pre/post byte-identical; only impl region edited).

Commands: bash scripts/lean_verify.sh <path>, run concurrently (batches of 4).
Results:
- atk_1 prepatch bug (n:=min a.length b.length unconditionally): exit 1 (proof unclosable). Reproduces the base_commit truncation bug -> prepatch_reproduced=True.
- atk_2 partial-domain (n:=max unconditionally; wrong for sameKind=true unequal lengths): exit 1.
- atk_3 control-flow-effect (branches swapped: if sameKind then max else min): exit 1.
- atk_4 boundary/off-by-one (loop [0:n-1], drops last coord): exit 1.
- atk_5 ungrounded-oracle echo (return sqSep sameKind a b): exit 0 (VERIFIES). #print axioms correct_sqSeparation => [propext, Classical.choice, Quot.sound] (clean); no sorry. This impl is behaviorally identical to the deep model = the gold post-patch radicand.
- atk_6 no-square ((a-b) not squared): exit 1.
- atk_7 ungrounded constant (return 0): exit 1.
- pos_control (gold impl, identical to Solution.lean): exit 0, clean axioms, no sorry.

MANDATORY resolve of every clean-axiom-verifying impl: only atk_5 closes. Its faithful refined patch (atk_5 computes exactly the post-patch radicand sqSep = gold behavior) IS the gold patch. Executed official harness: from PYTHONPATH=src, swebench_unified.harness.run_resolve('sympy__sympy-11618', gold_patch, run_id='sbu-audit-atk5-echo') => resolved=True, note='resolved'. So the sole verifying impl RESOLVES. No verify-but-not-resolve counterexample exists.

Because the postcondition pins result to sqSep exactly (universally quantified over sameKind,a,b), any impl whose correct_sqSeparation closes is forced pointwise-equal to sqSep, i.e. behaviorally the gold radicand; all 6 behaviorally-wrong impls fail to close (exit 1). Refinement audit passes: R/I legs, no kind-3, A-legs correspond to real callees (self.args/p.args/type-discriminator/sqrt outer wrapper). verify => resolve holds. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) attack on sympy__sympy-11618 lean bundle. The modeled function is Point.distance(self,p) post-patch; the modeled quantity is the RADICAND of sqrt(...) (sq. distance), since sqrt is a constant order-preserving outer wrapper. Spec: problem_spec_sqSeparation sameKind a b result := result = sqSep sameKind a b, where commonLen = if sameKind then min else max and sqSep = sum over i in [0:commonLen) of (a.getD i 0 - b.getD i 0)^2. sameKind models `type(p) is type(self)`.

METHODOLOGY: The provided was at the wrong commit (33b47e4bd6, a later version whose distance uses _normalize_dimension). I created a fresh worktree at the actual base_commit 360290c4c401e386db60723ddb0109ed499c9f6e, applied patch.diff (gold, verbatim), confirmed the post-patch branch matches refinement.md/mapping.md, and ran the REAL Point.distance (py3.8 + mpmath) differentially against the spec model, deriving sameKind from real Python `type(p) is type(self)` (note: Point of dim 1->Point, 2->Point2D, 3->Point3D, 4+->Point, so class transitions are exercised).

RESULTS: 0 disagreements across 13,000+ random inputs (3000 integer, 4000 rational dims1-6, 6000 rational dims1-9) + 25-case exhaustive dims 1x1..5x5 + targeted diff-kind unequal (dims 2vs3,3vs2,1vs2,etc all match: e.g. Point3D(1,0,2) vs Point2D(2,0) real_sq=5, model=5 — the F2P case) + same-kind differing-dim truncation (e.g. bare Point[1,2,3,4] vs Point[5,6,7,8,9] both same class -> min-dim truncation, real_sq=64=model). The load-bearing correction (max only on different-kind path; min/truncate on same-kind differing-dim path) is exactly reproduced by commonLen. No spec-too-strong case found: the spec pins result to a value the real callee always attains; no input rejects a gold-consistent result.

VERIFICATION: scripts/lean_verify.sh exit 0; #print axioms correct_sqSeparation => [propext, Classical.choice, Quot.sound] only (no sorryAx — genuine proof). same_spec(Solution.lean, Solution_prepatch.lean, lean tables) = True (spec region byte-identical; prepatch differs only in impl/proof using unconditional min). Spec is FAITHFUL to the post-patch repo behavior.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (Solution.lean regions only; impl/proof elided by spec_view projection) does not leak the gold edit beyond the public problem_statement. The problem_statement already names distance as buggy, states extra dimensions are dropped by zip, and gives Point(2,0).distance(Point(1,0,2))==1 should be sqrt(5). Mechanical G-LEAK screen PASSES (verified): no diff markers, no >=8-char gold-patch line reproduced (no `zip`, `p1=[0]*max(...)`, `type(p) is not type(self)`, `sqrt(sum(...))`), no patched file path (sympy/geometry/point.py) or module path, no narration terms (bug/fix/wrong/broken) in spec-view comments, and the only distinctive patched symbol is `distance` — which is already public in the problem_statement (screen skips it). The spec models the quantity abstractly over `List Rat` / `sameKind : Bool` (commonLen, sqSep, problem_spec_sqSeparation) — the intended behavior a specification must encode, not a reconstruction of the Python edit's mechanical form or localization. The sameKind (same-kind=>min/truncate vs different-kind=>max/zero-pad) discriminator is the correctness spec, expressed over Lean data, by design for this spec-driven benchmark — not gold-diff leakage. NOTE: the gold-patch-quoting/narration prose in mapping.md and refinement.md (e.g. 'buggy', verbatim patch fragments) is NOT part of the spec view — leak.py screens only solution_src(), so it does not bear on the solver-visible spec. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
