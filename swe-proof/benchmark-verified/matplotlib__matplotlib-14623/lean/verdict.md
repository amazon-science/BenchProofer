# P2 adversarial audit — matplotlib__matplotlib-14623

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1_noswap.lean`, `atk_2_alwaysswap.lean`, `atk_3_ge.lean`, `atk_4_swapargs.lean`, `atk_5_noclamp.lean`, `atk_6_dup.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7_echo.lean` |

**Non-vacuity.** The positive control `atk_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_noswap.lean` → rejected (same spec, does not verify — good)

```diff
@@ -69,17 +69,9 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_setLim (a b : Rat) : Rat × Rat := Id.run do
-  let swapped : Bool := decide (a > b)
+def implementation_setLim (a b : Rat) : Rat × Rat :=
   let n := normalizeRange a b
-  let c := clampToDomain n.1 n.2
-  let mut lo : Rat := c.1
-  let mut hi : Rat := c.2
-  if swapped then
-    let t := lo
-    lo := hi
-    hi := t
-  return (lo, hi)
+  clampToDomain n.1 n.2
 -- impl-end
 
 -- proof-start
```

Attack 2 — `atk_2_alwaysswap.lean` → rejected (same spec, does not verify — good)

```diff
@@ -69,17 +69,10 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_setLim (a b : Rat) : Rat × Rat := Id.run do
-  let swapped : Bool := decide (a > b)
+def implementation_setLim (a b : Rat) : Rat × Rat :=
   let n := normalizeRange a b
   let c := clampToDomain n.1 n.2
-  let mut lo : Rat := c.1
-  let mut hi : Rat := c.2
-  if swapped then
-    let t := lo
-    lo := hi
-    hi := t
-  return (lo, hi)
+  (c.2, c.1)
 -- impl-end
 
 -- proof-start
```

Attack 3 — `atk_3_ge.lean` → rejected (same spec, does not verify — good)

```diff
@@ -69,17 +69,10 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_setLim (a b : Rat) : Rat × Rat := Id.run do
-  let swapped : Bool := decide (a > b)
+def implementation_setLim (a b : Rat) : Rat × Rat :=
   let n := normalizeRange a b
   let c := clampToDomain n.1 n.2
-  let mut lo : Rat := c.1
-  let mut hi : Rat := c.2
-  if swapped then
-    let t := lo
-    lo := hi
-    hi := t
-  return (lo, hi)
+  if a >= b then (c.2, c.1) else c
 -- impl-end
 
 -- proof-start
```

Attack 4 — `atk_4_swapargs.lean` → rejected (same spec, does not verify — good)

```diff
@@ -69,17 +69,10 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_setLim (a b : Rat) : Rat × Rat := Id.run do
-  let swapped : Bool := decide (a > b)
-  let n := normalizeRange a b
+def implementation_setLim (a b : Rat) : Rat × Rat :=
+  let n := normalizeRange b a
   let c := clampToDomain n.1 n.2
-  let mut lo : Rat := c.1
-  let mut hi : Rat := c.2
-  if swapped then
-    let t := lo
-    lo := hi
-    hi := t
-  return (lo, hi)
+  if a > b then (c.2, c.1) else c
 -- impl-end
 
 -- proof-start
```

Attack 5 — `atk_5_noclamp.lean` → rejected (same spec, does not verify — good)

```diff
@@ -69,17 +69,9 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_setLim (a b : Rat) : Rat × Rat := Id.run do
-  let swapped : Bool := decide (a > b)
+def implementation_setLim (a b : Rat) : Rat × Rat :=
   let n := normalizeRange a b
-  let c := clampToDomain n.1 n.2
-  let mut lo : Rat := c.1
-  let mut hi : Rat := c.2
-  if swapped then
-    let t := lo
-    lo := hi
-    hi := t
-  return (lo, hi)
+  if a > b then (n.2, n.1) else n
 -- impl-end
 
 -- proof-start
```

Attack 6 — `atk_6_dup.lean` → rejected (same spec, does not verify — good)

```diff
@@ -69,17 +69,10 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_setLim (a b : Rat) : Rat × Rat := Id.run do
-  let swapped : Bool := decide (a > b)
+def implementation_setLim (a b : Rat) : Rat × Rat :=
   let n := normalizeRange a b
   let c := clampToDomain n.1 n.2
-  let mut lo : Rat := c.1
-  let mut hi : Rat := c.2
-  if swapped then
-    let t := lo
-    lo := hi
-    hi := t
-  return (lo, hi)
+  if a > b then (c.2, c.2) else c
 -- impl-end
 
 -- proof-start
```

Attack 7 — `atk_7_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -69,17 +69,10 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_setLim (a b : Rat) : Rat × Rat := Id.run do
-  let swapped : Bool := decide (a > b)
+def implementation_setLim (a b : Rat) : Rat × Rat :=
   let n := normalizeRange a b
   let c := clampToDomain n.1 n.2
-  let mut lo : Rat := c.1
-  let mut hi : Rat := c.2
-  if swapped then
-    let t := lo
-    lo := hi
-    hi := t
-  return (lo, hi)
+  if b < a then (c.2, c.1) else (c.1, c.2)
 -- impl-end
 
 -- proof-start
@@ -87,8 +80,5 @@
     ∀ (a b : Rat),
       problem_spec_setLim a b (implementation_setLim a b) := by
   intro a b
-  simp only [problem_spec_setLim, implementation_setLim, Id.run]
-  by_cases h : a > b
-  · simp only [h, decide_true, if_true]; rfl
-  · simp only [h, decide_false, Bool.false_eq_true, if_false]; rfl
+  simp only [problem_spec_setLim, implementation_setLim, gt_iff_lt]
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Setting the visible coordinate range of an axis from a requested pair of
endpoints.

A caller supplies two endpoint values describing the range that should become
visible. The caller may supply them in increasing order (the range runs in the
ascending direction) or in decreasing order (the range runs in the descending,
"flipped" direction). Before the range is committed, each endpoint is run
through two normalizing steps:

* a degenerate (zero-width) range is expanded so that the two endpoints are
  distinct, with the normalizer returning its two endpoints in increasing
  order; and
* the endpoints are restricted to the values permitted by the axis (some axes
  only accept endpoints from a limited domain).

The desired behavior: the *direction* the caller asked for must survive these
normalizing steps. If the caller gave the endpoints in increasing order the
committed range is ascending; if the caller gave them in decreasing order the
committed range is descending. In magnitude the committed endpoints are exactly
the two values produced by the normalizing steps; only their order may be
adjusted to match the requested direction.

The behavior is stated abstractly as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- Two unchanged dependency callees the behavior uses. Their results pass
-- through verbatim into the committed range; the modeled behavior (the
-- direction-restoring reassembly) is spelled out concretely below and consumes
-- no property of either callee, so no `_prop` axiom is declared. Each callee is
-- left as the real repo callee in the differential check (G-CONF, A-reference).

/-- The singularity-avoiding endpoint normalizer: given two endpoints it returns
a pair, expanding a degenerate range when necessary. -/
opaque normalizeRange : Rat → Rat → Rat × Rat

/-- The scale-domain limiter: restricts a pair of endpoints to the axis's
permitted domain. -/
opaque clampToDomain : Rat → Rat → Rat × Rat
-- axioms-end

-- pure-start
-- No additional pure helpers: the modeled behavior is the direction-preserving
-- reassembly of the normalized endpoints, spelled out directly below.
-- pure-end

-- post-conditions-start
/-- `result` is the committed range for requested endpoints `a`, `b`.

Let `p` be the pair obtained by normalizing `(a, b)` and then restricting it to
the axis domain. Then:

* if the caller requested ascending order (`a ≤ b`) the committed range is `p`
  unchanged (ascending); and
* if the caller requested descending order (`a > b`) the committed range is `p`
  with its two endpoints exchanged (descending).

So the committed magnitudes are exactly the two values of `p` and their order is
determined solely by the order the caller requested. -/
def problem_spec_setLim (a b : Rat) (result : Rat × Rat) : Prop :=
  let n := normalizeRange a b
  let p := clampToDomain n.1 n.2
  result = if a > b then (p.2, p.1) else p
-- post-conditions-end

-- impl-start
def implementation_setLim (a b : Rat) : Rat × Rat := Id.run do
  let swapped : Bool := decide (a > b)
  let n := normalizeRange a b
  let c := clampToDomain n.1 n.2
  let mut lo : Rat := c.1
  let mut hi : Rat := c.2
  if swapped then
    let t := lo
    lo := hi
    hi := t
  return (lo, hi)
-- impl-end

-- proof-start
theorem correct_setLim :
    ∀ (a b : Rat),
      problem_spec_setLim a b (implementation_setLim a b) := by
  intro a b
  simp only [problem_spec_setLim, implementation_setLim, Id.run]
  by_cases h : a > b
  · simp only [h, decide_true, if_true]; rfl
  · simp only [h, decide_false, Bool.false_eq_true, if_false]; rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

REFINEMENT-FIDELITY (A-leg) AUDIT of matplotlib__matplotlib-14623 lean bundle.

SPEC SHAPE: problem_spec_setLim pins `result` by EXACT EQUALITY to `if a > b then (p.2,p.1) else p` where p = clampToDomain (normalizeRange a b). Because the postcondition asserts no property of the two opaque callees, there is NO A-consumed leg; both callees are A-reference pass-throughs validated by G-CONF against the real callees (nonsingular / limit_range_for_scale). No kind-3 leg. An exact-equality spec over the callees is maximally tight: any impl not extensionally equal to the gold reassembly is unprovable.

SAME_SPEC: all 7 attacks + positive control return True via swebench_unified.markers.same_spec (byte-identical axioms/pure/pre/post; only impl region edited).

COMMANDS (from project root): `bash scripts/lean_verify.sh <file>` (exit 0=verifies, 1=error, 3=sorry, 124=timeout); axioms via appended `#print axioms correct_setLim`.

POSITIVE CONTROL atk_pos.lean (= gold): exit 0; #print axioms => [propext] (clean).

### WRONG IMPLS (each tried with BOTH the gold proof AND an aggressive auto-proof simp_all/omega/decide/tauto with by_cases splits):
 - atk_1_noswap  (never swap; == PREPATCH BUG): gold=1, agg=1  (unprovable)
 - atk_2_alwaysswap (always (c.2,c.1)): gold=1, agg=1
 - atk_3_ge (boundary: swap on a>=b): gold=1, agg=1
 - atk_4_swapargs (ungrounded: normalizeRange b a): gold=1, agg=1
 - atk_5_noclamp (partial-domain: drop clampToDomain): gold=1, agg=1
 - atk_6_dup (control-flow-effect: (c.2,c.2) in swapped branch): gold=1, agg=1
All six same-spec WRONG impls FAIL to close (exit 1). None produced a clean-axiom closing proof, so none required a resolve run.

ECHO CONTROL atk_7_echo.lean (`if b < a then (c.2,c.1) else (c.1,c.2)` — behaviorally IDENTICAL to gold since b<a ≡ a>b): CLOSES exit 0, #print axioms => [propext] (clean). Per protocol its faithful refined patch was MATERIALIZED (= the gold patch, since semantically identical) and RUN through the official harness: run_resolve('matplotlib__matplotlib-14623', patch, timeout=1500) => RESOLVED: True. This is a RESOLVING echo (source-repo adversary `weakness` protocol / 2026-08-06 G-PANEL-1 policy): a same-spec verifying impl whose refined patch RESOLVES is NOT a weakness. Hence verify⇒correct holds for the only closing wrong-shaped candidate.

PREPATCH REPRODUCED: Solution_prepatch.lean (never-swap impl) with the gold proof body => exit 1 (does not close), confirming the bug is caught by the spec.

RESULT: The only same-spec impl that closes with clean axioms is behaviorally identical to gold and its faithful patch RESOLVES. Every genuinely-wrong impl (6 distinct classes incl. the prepatch bug) fails to verify even under aggressive tactics. No materialized faithful patch of a closing clean-axiom impl fails to resolve => verify does NOT admit an incorrect impl. VERDICT: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1_noswap.lean`, `atk_2_alwaysswap.lean`, `atk_3_ge.lean`, `atk_4_swapargs.lean`, `atk_5_noclamp.lean`, `atk_6_dup.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7_echo.lean` |

**Non-vacuity.** The positive control `atk_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1_noswap.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_alwaysswap.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3_ge.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4_swapargs.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5_noclamp.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6_dup.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Setting the visible coordinate range of an axis from a requested pair of
endpoints.

A caller supplies two endpoint values describing the range that should become
visible. The caller may supply them in increasing order (the range runs in the
ascending direction) or in decreasing order (the range runs in the descending,
"flipped" direction). Before the range is committed, each endpoint is run
through two normalizing steps:

* a degenerate (zero-width) range is expanded so that the two endpoints are
  distinct, with the normalizer returning its two endpoints in increasing
  order; and
* the endpoints are restricted to the values permitted by the axis (some axes
  only accept endpoints from a limited domain).

The desired behavior: the *direction* the caller asked for must survive these
normalizing steps. If the caller gave the endpoints in increasing order the
committed range is ascending; if the caller gave them in decreasing order the
committed range is descending. In magnitude the committed endpoints are exactly
the two values produced by the normalizing steps; only their order may be
adjusted to match the requested direction.

The behavior is stated abstractly as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- Two unchanged dependency callees the behavior uses. Their results pass
-- through verbatim into the committed range; the modeled behavior (the
-- direction-restoring reassembly) is spelled out concretely below and consumes
-- no property of either callee, so no `_prop` axiom is declared. Each callee is
-- left as the real repo callee in the differential check (G-CONF, A-reference).

/-- The singularity-avoiding endpoint normalizer: given two endpoints it returns
a pair, expanding a degenerate range when necessary. -/
opaque normalizeRange : Rat → Rat → Rat × Rat

/-- The scale-domain limiter: restricts a pair of endpoints to the axis's
permitted domain. -/
opaque clampToDomain : Rat → Rat → Rat × Rat
-- axioms-end

-- pure-start
-- No additional pure helpers: the modeled behavior is the direction-preserving
-- reassembly of the normalized endpoints, spelled out directly below.
-- pure-end

-- post-conditions-start
/-- `result` is the committed range for requested endpoints `a`, `b`.

Let `p` be the pair obtained by normalizing `(a, b)` and then restricting it to
the axis domain. Then:

* if the caller requested ascending order (`a ≤ b`) the committed range is `p`
  unchanged (ascending); and
* if the caller requested descending order (`a > b`) the committed range is `p`
  with its two endpoints exchanged (descending).

So the committed magnitudes are exactly the two values of `p` and their order is
determined solely by the order the caller requested. -/
def problem_spec_setLim (a b : Rat) (result : Rat × Rat) : Prop :=
  let n := normalizeRange a b
  let p := clampToDomain n.1 n.2
  result = if a > b then (p.2, p.1) else p
-- post-conditions-end

-- impl-start
def implementation_setLim (a b : Rat) : Rat × Rat := Id.run do
  let swapped : Bool := decide (a > b)
  let n := normalizeRange a b
  let c := clampToDomain n.1 n.2
  let mut lo : Rat := c.1
  let mut hi : Rat := c.2
  if swapped then
    let t := lo
    lo := hi
    hi := t
  return (lo, hi)
-- impl-end

-- proof-start
theorem correct_setLim :
    ∀ (a b : Rat),
      problem_spec_setLim a b (implementation_setLim a b) := by
  intro a b
  simp only [problem_spec_setLim, implementation_setLim, Id.run]
  by_cases h : a > b
  · simp only [h, decide_true, if_true]; rfl
  · simp only [h, decide_false, Bool.false_eq_true, if_false]; rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

REFINEMENT-FIDELITY (A-leg) AUDIT of matplotlib__matplotlib-14623 lean bundle.

SPEC SHAPE: problem_spec_setLim pins `result` by EXACT EQUALITY to `if a > b then (p.2,p.1) else p` where p = clampToDomain (normalizeRange a b). Because the postcondition asserts no property of the two opaque callees, there is NO A-consumed leg; both callees are A-reference pass-throughs validated by G-CONF against the real callees (nonsingular / limit_range_for_scale). No kind-3 leg. An exact-equality spec over the callees is maximally tight: any impl not extensionally equal to the gold reassembly is unprovable.

SAME_SPEC: all 7 attacks + positive control return True via swebench_unified.markers.same_spec (byte-identical axioms/pure/pre/post; only impl region edited).

COMMANDS (from project root): `bash scripts/lean_verify.sh <file>` (exit 0=verifies, 1=error, 3=sorry, 124=timeout); axioms via appended `#print axioms correct_setLim`.

POSITIVE CONTROL atk_pos.lean (= gold): exit 0; #print axioms => [propext] (clean).

### WRONG IMPLS (each tried with BOTH the gold proof AND an aggressive auto-proof simp_all/omega/decide/tauto with by_cases splits):
 - atk_1_noswap  (never swap; == PREPATCH BUG): gold=1, agg=1  (unprovable)
 - atk_2_alwaysswap (always (c.2,c.1)): gold=1, agg=1
 - atk_3_ge (boundary: swap on a>=b): gold=1, agg=1
 - atk_4_swapargs (ungrounded: normalizeRange b a): gold=1, agg=1
 - atk_5_noclamp (partial-domain: drop clampToDomain): gold=1, agg=1
 - atk_6_dup (control-flow-effect: (c.2,c.2) in swapped branch): gold=1, agg=1
All six same-spec WRONG impls FAIL to close (exit 1). None produced a clean-axiom closing proof, so none required a resolve run.

ECHO CONTROL atk_7_echo.lean (`if b < a then (c.2,c.1) else (c.1,c.2)` — behaviorally IDENTICAL to gold since b<a ≡ a>b): CLOSES exit 0, #print axioms => [propext] (clean). Per protocol its faithful refined patch was MATERIALIZED (= the gold patch, since semantically identical) and RUN through the official harness: run_resolve('matplotlib__matplotlib-14623', patch, timeout=1500) => RESOLVED: True. This is a RESOLVING echo (source-repo adversary `weakness` protocol / 2026-08-06 G-PANEL-1 policy): a same-spec verifying impl whose refined patch RESOLVES is NOT a weakness. Hence verify⇒correct holds for the only closing wrong-shaped candidate.

PREPATCH REPRODUCED: Solution_prepatch.lean (never-swap impl) with the gold proof body => exit 1 (does not close), confirming the bug is caught by the spec.

RESULT: The only same-spec impl that closes with clean axioms is behaviorally identical to gold and its faithful patch RESOLVES. Every genuinely-wrong impl (6 distinct classes incl. the prepatch bug) fails to verify even under aggressive tactics. No materialized faithful patch of a closing clean-axiom impl fails to resolve => verify does NOT admit an incorrect impl. VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack on Lean bundle matplotlib__matplotlib-14623. Mechanical preflight all green: lean_verify.sh Solution.lean -> exit 0 (compiles, no sorry); reconstructed proof gives `#print axioms correct_setLim` = [propext] only (no sorryAx, real proof); same_spec(Solution, Solution_prepatch, LeanBackend.language) = True (spec region byte-identical/frozen).

Spec: problem_spec_setLim a b result := let n := normalizeRange a b; let p := clampToDomain n.1 n.2; result = if a > b then (p.2,p.1) else p. normalizeRange and clampToDomain are OPAQUE (left as the REAL repo callees `<locator>.nonsingular` and `limit_range_for_scale` in the differential G-CONF), so the spec asserts NO over-strong property about either callee -- it is a pure exact-equality functional spec pinned solely to the direction-swap logic that the gold patch adds.

Compared against the real gold patch across all five sites (representative set_ylim): `swapped = bottom>top; bottom,top = nonsingular(bottom,top); bottom,top = limit_range_for_scale(bottom,top); if swapped: bottom,top = top,bottom`. This is a line-for-line transcription of the spec's reassembly. Probed for spec-too-strong divergence: (a==b) real swapped=False -> result=p, spec else-branch -> p, MATCH; (a>b) real -> (hi,lo), spec (p.2,p.1), MATCH; (a<b) both -> p, MATCH. Direction is decided solely by the a>b comparison in both model and repo; no additional reorder step exists between the callee pipeline and the commit to viewLim. Rat-vs-float carrier only affects magnitudes, which flow opaquely through the REAL callees in G-CONF; the swap boolean is the same numeric order comparison, so no order divergence is possible (order-only fix). Out-of-model inputs (None/NaN endpoints, singular-warning emission) are scope reductions, not faithfulness breaks of the modeled direction-preservation behavior.

Independent corroboration: G-CONF status=pass over 120,392 (a,b) pairs, linear+log, shadow committed range == real set_ylim outcome, direction preserved. No input found where the modeled function disagrees with the real callee. The spec is exactly as strong as the real code -- no drift, no over-abstraction.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec-region byte-identity confirmed: same_spec(Solution.lean, Solution_prepatch.lean) via LeanBackend.language = True. Spec view = prose /-! block + opaque signatures (normalizeRange, clampToDomain) + problem_spec_setLim; impl and proof are elided.

Leakage check vs PUBLIC problem_statement (hints_text excluded by policy):
- The public problem_statement already states the expected outcome verbatim: 'I would expect the yaxis to be inverted for both the linear and the log scale' — i.e. the requested endpoint direction must be preserved. The spec prose ('the direction the caller asked for must survive these normalizing steps') is a restatement of that public expectation, not new information.
- The spec view uses ONLY abstract naming (normalizeRange, clampToDomain, a, b, result). It does NOT lexically quote any gold-patch specifics: no 'swapped', no left/right/bottom/top, no nonsingular, no limit_range_for_scale, no increasing=False. The gold EDIT mechanism (capture swapped=a>b BEFORE normalization, re-swap AFTER) appears only inside the ELIDED impl region, not the spec view.
- The postcondition (result = if a > b then (p.2,p.1) else p) pins the correct OUTCOME by exact equality — as any sound functional spec here must — but does not disclose the gold edit strategy; a solver could satisfy it via multiple independent implementations (branch on b<a, reorder by min/max, etc.). The 'capture-before-normalize' insight that is the crux of the gold fix is not revealed.
- The pipeline description (normalize then domain-restrict; normalizer returns increasing order) is generic public callee structure required to state any functional spec, not a patch disclosure.

No spec-view line leaks the gold edit beyond the public problem_statement. Consistent with recorded verdict.md Role-4 (NO-LEAKAGE).

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
