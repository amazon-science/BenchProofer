# P2 adversarial audit — sympy__sympy-17655

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
None found. The postcondition problem_spec_scaleByFactor factor coords result := (result = some (scaleSpec factor coords)) is a pinned definitional equality to a concrete TOTAL function. Any impl whose correct_ closes must satisfy impl factor coords = some (scaleSpec factor coords) for all inputs, i.e. it is extensionally the unique correct function. I additionally PROVED (not merely failed to prove) that a wrong impl's correctness is false: disproof_identity.lean (some coords, ignoring factor) — the theorem `¬ ∀ factor coords, problem_spec ... (impl ...)` closes at exit 0 via the witness factor=0, coords=[1] (gives [1]=[0]). So no same-spec wrong impl can verify; there is no closing-but-non-resolving alternative.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -32,10 +32,7 @@
 -- impl-start
 def implementation_scaleByFactor
     (factor : Rat) (coords : List Rat) : Option (List Rat) := Id.run do
-  let mut acc : List Rat := []
-  for x in coords do
-    acc := acc ++ [x * factor]
-  return some acc
+  return none
 -- impl-end
 
 -- proof-start
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -31,11 +31,10 @@
 
 -- impl-start
 def implementation_scaleByFactor
-    (factor : Rat) (coords : List Rat) : Option (List Rat) := Id.run do
-  let mut acc : List Rat := []
-  for x in coords do
-    acc := acc ++ [x * factor]
-  return some acc
+    (factor : Rat) (coords : List Rat) : Option (List Rat) :=
+  match coords with
+  | [] => none
+  | xs => some (xs.map (fun x => x * factor))
 -- impl-end
 
 -- proof-start
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -31,11 +31,10 @@
 
 -- impl-start
 def implementation_scaleByFactor
-    (factor : Rat) (coords : List Rat) : Option (List Rat) := Id.run do
-  let mut acc : List Rat := []
-  for x in coords do
-    acc := acc ++ [x * factor]
-  return some acc
+    (factor : Rat) (coords : List Rat) : Option (List Rat) :=
+  match coords with
+  | [] => some []
+  | x :: xs => some (x :: xs.map (fun y => y * factor))
 -- impl-end
 
 -- proof-start
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -31,11 +31,8 @@
 
 -- impl-start
 def implementation_scaleByFactor
-    (factor : Rat) (coords : List Rat) : Option (List Rat) := Id.run do
-  let mut acc : List Rat := []
-  for x in coords do
-    acc := acc ++ [x * factor]
-  return some acc
+    (factor : Rat) (coords : List Rat) : Option (List Rat) :=
+  some (coords.map (fun x => x + factor))
 -- impl-end
 
 -- proof-start
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -31,11 +31,8 @@
 
 -- impl-start
 def implementation_scaleByFactor
-    (factor : Rat) (coords : List Rat) : Option (List Rat) := Id.run do
-  let mut acc : List Rat := []
-  for x in coords do
-    acc := acc ++ [x * factor]
-  return some acc
+    (factor : Rat) (coords : List Rat) : Option (List Rat) :=
+  some coords
 -- impl-end
 
 -- proof-start
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -31,11 +31,8 @@
 
 -- impl-start
 def implementation_scaleByFactor
-    (factor : Rat) (coords : List Rat) : Option (List Rat) := Id.run do
-  let mut acc : List Rat := []
-  for x in coords do
-    acc := acc ++ [x * factor]
-  return some acc
+    (factor : Rat) (coords : List Rat) : Option (List Rat) :=
+  some (coords.map (fun x => x * (factor + 1)))
 -- impl-end
 
 -- proof-start
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -31,11 +31,8 @@
 
 -- impl-start
 def implementation_scaleByFactor
-    (factor : Rat) (coords : List Rat) : Option (List Rat) := Id.run do
-  let mut acc : List Rat := []
-  for x in coords do
-    acc := acc ++ [x * factor]
-  return some acc
+    (factor : Rat) (coords : List Rat) : Option (List Rat) :=
+  some ((coords.map (fun x => x * factor)).reverse)
 -- impl-end
 
 -- proof-start
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here: the coordinate-wise scaling
-- operation that this behavior delegates to is modeled DEEPLY (a front-recursive
-- fold over the coordinate list, below) rather than axiomatized, so its real
-- reference implementation is validated as an A-reference by G-AX. The proof
-- agent may add `_prop` axioms only if stuck.
-- axioms-end

-- pure-start
/-- Front-recursive specification fold: scale each coordinate of a point by the
given scalar factor, preserving coordinate order. This is exactly the
coordinate-wise scaling operation a point already supports when the scalar is on
the right. -/
def scaleSpec (factor : Rat) : List Rat → List Rat
  | [] => []
  | x :: xs => (x * factor) :: scaleSpec factor xs
-- pure-end

-- post-conditions-start
/-- Multiplying a scalar `factor` by a point (given by its coordinate list)
succeeds and yields the point whose coordinates are each scaled by `factor`,
matching the result of scaling the same point by the same scalar. The result is
`some scaled` — a well-defined point — never an undefined/error result. -/
def problem_spec_scaleByFactor
    (factor : Rat) (coords : List Rat) (result : Option (List Rat)) : Prop :=
  result = some (scaleSpec factor coords)
-- post-conditions-end

-- impl-start
def implementation_scaleByFactor
    (factor : Rat) (coords : List Rat) : Option (List Rat) := Id.run do
  let mut acc : List Rat := []
  for x in coords do
    acc := acc ++ [x * factor]
  return some acc
-- impl-end

-- proof-start
/-- The append-accumulating `forIn` over the coordinate list, generalized over
the accumulator, equals the initial accumulator followed by the spec fold. -/
theorem scale_forIn_eq (factor : Rat) (xs : List Rat) (init : List Rat) :
    (forIn xs init (fun x r =>
        (pure (ForInStep.yield (r ++ [x * factor])) : Id (ForInStep (List Rat))))
      : Id (List Rat))
      = init ++ scaleSpec factor xs := by
  induction xs generalizing init with
  | nil => simp [scaleSpec, pure]
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [bind, pure] at ih ⊢
    rw [ih]
    simp [scaleSpec, List.append_assoc]

theorem correct_scaleByFactor : ∀ (factor : Rat) (coords : List Rat),
    problem_spec_scaleByFactor factor coords
      (implementation_scaleByFactor factor coords) := by
  intro factor coords
  unfold problem_spec_scaleByFactor implementation_scaleByFactor
  simp only [Id.run, bind]
  rw [scale_forIn_eq factor coords []]
  simp [pure]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

venv python. same_spec=True for all 7 attacks (spec regions byte-identical; only impl+proof edited). Verifier: `bash scripts/lean_verify.sh <file>` (exit 0=verifies/no-sorry, 1=error, 3=sorry, 124=timeout). Runs launched concurrently in two ≤4 background batches.

### Results
- positive_control pos.lean (gold impl, forIn accumulate) -> exit 0 (VERIFIES). #print axioms is [propext, Classical.choice, Quot.sound] per bundle verdict.md; clean.
- atk_1 (prepatch bug: `return none`, ungrounded no-point) -> exit 1 (fails to close). Reproduces the prepatch G-DIFF signal: none ≠ some(scaleSpec...).
- atk_2 (partial-domain: none on empty coords, else map) -> exit 1.
- atk_3 (boundary/off-by: skip scaling head coordinate) -> exit 1.
- atk_4 (control-flow-effect: x+factor instead of x*factor) -> exit 1 (`simp made no progress`).
- atk_5 (ungrounded-oracle echo: identity `some coords`, ignores factor) -> exit 1 (`simp made no progress`).
- atk_6 (off-by-one factor: x*(factor+1)) -> exit 1.
- atk_7 (reversed coordinate order) -> exit 1.

Every attack that closes with clean axioms would trigger step-2 (materialize faithful patch + run_resolve). NONE closed, so patches={} and no resolve run is required or possible. To rule out that failures were mere proof-shape mismatches (I reused the gold forIn proof), I built disproof_identity.lean holding the spec byte-identical and PROVING the identity impl's universal correctness FALSE — it verifies at exit 0, positively confirming the spec pins the unique correct function.

REFINEMENT AUDIT (refinement.md): 5 rows, all legal kinds — row1 R (scalar↔Rat, point↔List Rat), row2/row3 I (empty-init, coordinate iteration), row4 A-reference (per-coordinate x*factor modeled DEEPLY as scaleSpec, validated == real Point.__mul__ by G-AX), row5 R (Point(...)↔some coords). No A-consumed rows (axioms region empty), no kind-3 legs. The single A-reference correspondence holds: axiom_check.py fuzzes 40k+ rational (factor,coords) probes comparing scaleSpec vs the REAL Point.__mul__ (which gold __rmul__ forwards to) with 0 mismatches (seed 17655), incl. boundary fixtures (0, negatives, unit fractions). The A-leg's real callee (`__mul__` body `[simplify(x*factor) for x in self.args]`) matches the deep model.

VERDICT: SOUND. 7 distinct same-spec wrong impls (prepatch bug + partial-domain + boundary + control-flow-effect + ungrounded-oracle echo + 2 off-by/reorder) all fail to close; gold verifies; a wrong impl's correctness is provably false. verify⇒correct holds here because the postcondition is an equality to a concrete total function, admitting exactly one satisfying impl.

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
None found. The postcondition problem_spec_scaleByFactor factor coords result := (result = some (scaleSpec factor coords)) is a pinned definitional equality to a concrete TOTAL function. Any impl whose correct_ closes must satisfy impl factor coords = some (scaleSpec factor coords) for all inputs, i.e. it is extensionally the unique correct function. I additionally PROVED (not merely failed to prove) that a wrong impl's correctness is false: disproof_identity.lean (some coords, ignoring factor) — the theorem `¬ ∀ factor coords, problem_spec ... (impl ...)` closes at exit 0 via the witness factor=0, coords=[1] (gives [1]=[0]). So no same-spec wrong impl can verify; there is no closing-but-non-resolving alternative.
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

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here: the coordinate-wise scaling
-- operation that this behavior delegates to is modeled DEEPLY (a front-recursive
-- fold over the coordinate list, below) rather than axiomatized, so its real
-- reference implementation is validated as an A-reference by G-AX. The proof
-- agent may add `_prop` axioms only if stuck.
-- axioms-end

-- pure-start
/-- Front-recursive specification fold: scale each coordinate of a point by the
given scalar factor, preserving coordinate order. This is exactly the
coordinate-wise scaling operation a point already supports when the scalar is on
the right. -/
def scaleSpec (factor : Rat) : List Rat → List Rat
  | [] => []
  | x :: xs => (x * factor) :: scaleSpec factor xs
-- pure-end

-- post-conditions-start
/-- Multiplying a scalar `factor` by a point (given by its coordinate list)
succeeds and yields the point whose coordinates are each scaled by `factor`,
matching the result of scaling the same point by the same scalar. The result is
`some scaled` — a well-defined point — never an undefined/error result. -/
def problem_spec_scaleByFactor
    (factor : Rat) (coords : List Rat) (result : Option (List Rat)) : Prop :=
  result = some (scaleSpec factor coords)
-- post-conditions-end

-- impl-start
def implementation_scaleByFactor
    (factor : Rat) (coords : List Rat) : Option (List Rat) := Id.run do
  let mut acc : List Rat := []
  for x in coords do
    acc := acc ++ [x * factor]
  return some acc
-- impl-end

-- proof-start
/-- The append-accumulating `forIn` over the coordinate list, generalized over
the accumulator, equals the initial accumulator followed by the spec fold. -/
theorem scale_forIn_eq (factor : Rat) (xs : List Rat) (init : List Rat) :
    (forIn xs init (fun x r =>
        (pure (ForInStep.yield (r ++ [x * factor])) : Id (ForInStep (List Rat))))
      : Id (List Rat))
      = init ++ scaleSpec factor xs := by
  induction xs generalizing init with
  | nil => simp [scaleSpec, pure]
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [bind, pure] at ih ⊢
    rw [ih]
    simp [scaleSpec, List.append_assoc]

theorem correct_scaleByFactor : ∀ (factor : Rat) (coords : List Rat),
    problem_spec_scaleByFactor factor coords
      (implementation_scaleByFactor factor coords) := by
  intro factor coords
  unfold problem_spec_scaleByFactor implementation_scaleByFactor
  simp only [Id.run, bind]
  rw [scale_forIn_eq factor coords []]
  simp [pure]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

venv python. same_spec=True for all 7 attacks (spec regions byte-identical; only impl+proof edited). Verifier: `bash scripts/lean_verify.sh <file>` (exit 0=verifies/no-sorry, 1=error, 3=sorry, 124=timeout). Runs launched concurrently in two ≤4 background batches.

### Results
- positive_control pos.lean (gold impl, forIn accumulate) -> exit 0 (VERIFIES). #print axioms is [propext, Classical.choice, Quot.sound] per bundle verdict.md; clean.
- atk_1 (prepatch bug: `return none`, ungrounded no-point) -> exit 1 (fails to close). Reproduces the prepatch G-DIFF signal: none ≠ some(scaleSpec...).
- atk_2 (partial-domain: none on empty coords, else map) -> exit 1.
- atk_3 (boundary/off-by: skip scaling head coordinate) -> exit 1.
- atk_4 (control-flow-effect: x+factor instead of x*factor) -> exit 1 (`simp made no progress`).
- atk_5 (ungrounded-oracle echo: identity `some coords`, ignores factor) -> exit 1 (`simp made no progress`).
- atk_6 (off-by-one factor: x*(factor+1)) -> exit 1.
- atk_7 (reversed coordinate order) -> exit 1.

Every attack that closes with clean axioms would trigger step-2 (materialize faithful patch + run_resolve). NONE closed, so patches={} and no resolve run is required or possible. To rule out that failures were mere proof-shape mismatches (I reused the gold forIn proof), I built disproof_identity.lean holding the spec byte-identical and PROVING the identity impl's universal correctness FALSE — it verifies at exit 0, positively confirming the spec pins the unique correct function.

REFINEMENT AUDIT (refinement.md): 5 rows, all legal kinds — row1 R (scalar↔Rat, point↔List Rat), row2/row3 I (empty-init, coordinate iteration), row4 A-reference (per-coordinate x*factor modeled DEEPLY as scaleSpec, validated == real Point.__mul__ by G-AX), row5 R (Point(...)↔some coords). No A-consumed rows (axioms region empty), no kind-3 legs. The single A-reference correspondence holds: axiom_check.py fuzzes 40k+ rational (factor,coords) probes comparing scaleSpec vs the REAL Point.__mul__ (which gold __rmul__ forwards to) with 0 mismatches (seed 17655), incl. boundary fixtures (0, negatives, unit fractions). The A-leg's real callee (`__mul__` body `[simplify(x*factor) for x in self.args]`) matches the deep model.

VERDICT: SOUND. 7 distinct same-spec wrong impls (prepatch bug + partial-domain + boundary + control-flow-effect + ungrounded-oracle echo + 2 off-by/reorder) all fail to close; gold verifies; a wrong impl's correctness is provably false. verify⇒correct holds here because the postcondition is an equality to a concrete total function, admitting exactly one satisfying impl.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for sympy__sympy-17655 lean bundle. Modeled function: Point.__rmul__ (post-patch left scalar-by-point multiply, forwarding to __mul__ = [simplify(x*factor) for x in self.args]).

Evidence the spec agrees with the real repo callee on all realizable inputs:
1. same_spec(Solution.lean, Solution_prepatch.lean) = True via swebench_unified.markers with the lean backend — spec region (axioms/pure/post-conditions) is byte-identical; only impl+proof differ, so G-DIFF is real.
2. Lean compiles under lean_verify.sh (exit 0, no sorry) and `#print axioms correct_scaleByFactor` = [propext, Classical.choice, Quot.sound] only — no sorryAx, proof is genuine.
3. G-AX (axiom_check.py) against the REAL post-patch repo (v1.8.dev, has __rmul__): scaleSpec == Point.__mul__ coordinate-wise, 40k+ probes, 0 mismatches.
4. G-CONF (conformance_check.py) against real sympy: 120,006 fuzzed (factor, coords) inputs, 0 disagreements vs gold __rmul__.
5. Independent adversarial in-domain probes (large ints ~1e9, negatives, mixed rationals like 123456789/987654321 * [999999/7, 1/999999], 2D/3D): model == real callee exactly. simplify(x*factor) on exact rationals is exact rational arithmetic — the mapping.md note that Rat captures it faithfully (no Float-order subtlety) holds.

The spec pins result = some (scaleSpec factor coords), which is EXACTLY the post-patch behavior (a well-defined point for every point input), and scaleSpec is a faithful front-recursive coordinate-scaling fold. This is not too strong: the pre-patch code raised (no left multiply), which is why prepatch's correct_scaleByFactor cannot close against the frozen `some (...)` spec — the intended G-DIFF signal, mirroring the real bug (5*Point(1,1) raised at base_commit, returns Point(5,5) post-patch).

Only nuance: the Lean spec is total over List Rat, so it also assigns a result for coords of length <2, whereas real Point raises ValueError for <2 coords. This is a benign total-extension over an UNREALIZABLE region — mapping.md restricts the domain to len(args)>=2 (a real Point cannot have <2 coordinates), and both G-AX and G-CONF only sample len 2..4. On the entire realizable domain the modeled function and the real callee agree pointwise; no diverging realizable input exists. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Leakage judged against the public problem_statement ONLY (not hints_text). Gold edit: add Point.__rmul__ delegating to __mul__, scaling each coordinate by factor. The public problem_statement already discloses: left scalar*point raises at base_commit, right point*scalar works, and 'both lines [should] give the same result'. The spec view (post-conditions problem_spec_scaleByFactor = some (scaleSpec factor coords), scaleSpec: x*factor per coord) encodes exactly that publicly-stated expected behavior — left-multiply succeeds and equals coordinate-wise scaling matching the right multiply. It does NOT reveal the gold mechanism: the changed symbol 'rmul'/'__rmul__'/'__mul__' does not appear anywhere in the spec view, and the delegation-to-__mul__ implementation approach is not reconstructable from the spec. Mechanical screen: leakage.screen passed (no hard_failures) — no diff markers, no reproduced gold-patch line, no patched file/module path, no patched-symbol identifier collision, no bug/fix narration. The pure-region comment 'a point already supports when the scalar is on the right' only restates the right-multiply behavior the problem_statement itself demonstrates works, not the edit. Verified same_spec(post, prepatch)=True and same_spec projection is byte-identical across regions. Spec view is a faithful behavioral projection derivable from the public task; no leakage beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
