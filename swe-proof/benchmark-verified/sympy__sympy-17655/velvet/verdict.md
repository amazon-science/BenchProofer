# P2 adversarial audit — sympy__sympy-17655

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 16 admissible attacks re-run of 16 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 16 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 16 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean`, `atk_10.lean`, `atk_11.lean`, `atk_12.lean`, `atk_13.lean`, `atk_14.lean`, `atk_15.lean`, `atk_16.lean` |

**Non-vacuity.** The positive control `ctrl.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. 16 same-spec, admissible wrong impls were verified; ZERO verified (all exit=1), so no attack reached the mandatory resolve stage. The spec's discriminating clause `ensures out = scaleCoords coords factor` rejected every one, and 14/16 failed at exactly that named goal (`case «ensures_2: out = scaleCoords coords factor»`).
```

**Attacks re-run (16):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -64,10 +64,9 @@
   ensures out.length = coords.length
   do
     -- impl-start
-    -- Delegate to the library's existing point-by-scalar scaling operation (the
-    -- per-coordinate product), and return its result — so left-multiplication by
-    -- a number matches right-multiplication by the same number.
-    let out :| out = scaleCoords coords factor
+    -- ATTACK 1 (prepatch bug re-encode): factor never applied; left-multiply
+    -- returns the point unscaled.
+    let out := coords
     return out
     -- impl-end
 end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -64,10 +64,9 @@
   ensures out.length = coords.length
   do
     -- impl-start
-    -- Delegate to the library's existing point-by-scalar scaling operation (the
-    -- per-coordinate product), and return its result — so left-multiplication by
-    -- a number matches right-multiplication by the same number.
-    let out :| out = scaleCoords coords factor
+    -- ATTACK 2 (partial domain): correct on dim >= 2, wrong on the
+    -- degenerate 0/1-coordinate points.
+    let out := if coords.length ≤ 1 then coords else scaleCoords coords factor
     return out
     -- impl-end
 end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -64,10 +64,9 @@
   ensures out.length = coords.length
   do
     -- impl-start
-    -- Delegate to the library's existing point-by-scalar scaling operation (the
-    -- per-coordinate product), and return its result — so left-multiplication by
-    -- a number matches right-multiplication by the same number.
-    let out :| out = scaleCoords coords factor
+    -- ATTACK 3 (boundary): correct for every factor except 0, where the
+    -- coordinates come back unscaled instead of zeroed.
+    let out := if factor = 0 then coords else scaleCoords coords factor
     return out
     -- impl-end
 end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -64,10 +64,11 @@
   ensures out.length = coords.length
   do
     -- impl-start
-    -- Delegate to the library's existing point-by-scalar scaling operation (the
-    -- per-coordinate product), and return its result — so left-multiplication by
-    -- a number matches right-multiplication by the same number.
-    let out :| out = scaleCoords coords factor
+    -- ATTACK 4 (control-flow effect): scales only the FIRST coordinate and
+    -- leaves the remaining ones untouched.
+    let out := match coords with
+      | [] => []
+      | c :: rest => (c * factor) :: rest
     return out
     -- impl-end
 end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -64,10 +64,8 @@
   ensures out.length = coords.length
   do
     -- impl-start
-    -- Delegate to the library's existing point-by-scalar scaling operation (the
-    -- per-coordinate product), and return its result — so left-multiplication by
-    -- a number matches right-multiplication by the same number.
-    let out :| out = scaleCoords coords factor
+    -- ATTACK 5 (wrong operator): additive instead of multiplicative.
+    let out := coords.map (· + factor)
     return out
     -- impl-end
 end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -64,10 +64,8 @@
   ensures out.length = coords.length
   do
     -- impl-start
-    -- Delegate to the library's existing point-by-scalar scaling operation (the
-    -- per-coordinate product), and return its result — so left-multiplication by
-    -- a number matches right-multiplication by the same number.
-    let out :| out = scaleCoords coords factor
+    -- ATTACK 6 (order): right values, reversed coordinate order.
+    let out := (scaleCoords coords factor).reverse
     return out
     -- impl-end
 end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -64,10 +64,8 @@
   ensures out.length = coords.length
   do
     -- impl-start
-    -- Delegate to the library's existing point-by-scalar scaling operation (the
-    -- per-coordinate product), and return its result — so left-multiplication by
-    -- a number matches right-multiplication by the same number.
-    let out :| out = scaleCoords coords factor
+    -- ATTACK 7 (dimension): scaled coordinates plus a spurious extra one.
+    let out := scaleCoords coords factor ++ [(0:Rat)]
     return out
     -- impl-end
 end
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -64,10 +64,9 @@
   ensures out.length = coords.length
   do
     -- impl-start
-    -- Delegate to the library's existing point-by-scalar scaling operation (the
-    -- per-coordinate product), and return its result — so left-multiplication by
-    -- a number matches right-multiplication by the same number.
-    let out :| out = scaleCoords coords factor
+    -- ATTACK 8 (ungrounded-oracle echo): the delegation is pinned only by
+    -- its DIMENSION, never by the coordinate values.
+    let out :| out.length = coords.length
     return out
     -- impl-end
 end
```

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -64,10 +64,10 @@
   ensures out.length = coords.length
   do
     -- impl-start
-    -- Delegate to the library's existing point-by-scalar scaling operation (the
-    -- per-coordinate product), and return its result — so left-multiplication by
-    -- a number matches right-multiplication by the same number.
-    let out :| out = scaleCoords coords factor
+    -- ATTACK 9 (vacuity probe): an INFEASIBLE demonic choice. If an
+    -- unsatisfiable choice discharges the postcondition vacuously, the spec
+    -- admits an operator that can never return a value at all.
+    let out :| out = coords ∧ out = scaleCoords coords factor
     return out
     -- impl-end
 end
```

Attack 10 — `atk_10.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -64,10 +64,15 @@
   ensures out.length = coords.length
   do
     -- impl-start
-    -- Delegate to the library's existing point-by-scalar scaling operation (the
-    -- per-coordinate product), and return its result — so left-multiplication by
-    -- a number matches right-multiplication by the same number.
-    let out :| out = scaleCoords coords factor
+    -- ATTACK 10 (divergence probe under total semantics): the routine spins
+    -- forever and returns the UNSCALED coordinates. Under "total" a diverging
+    -- impl must be rejected; if it verifies, verify does not imply termination.
+    let mut out := coords
+    let mut i := (0:Nat)
+    while i = 0
+    invariant out = coords
+    do
+      i := 0
     return out
     -- impl-end
 end
```

Attack 11 — `atk_11.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -64,10 +64,15 @@
   ensures out.length = coords.length
   do
     -- impl-start
-    -- Delegate to the library's existing point-by-scalar scaling operation (the
-    -- per-coordinate product), and return its result — so left-multiplication by
-    -- a number matches right-multiplication by the same number.
-    let out :| out = scaleCoords coords factor
+    -- ATTACK 11 (termination/divergence): the returned VALUE is exactly the
+    -- scaled coordinates, but the routine first spins in a loop that never
+    -- makes progress. Probes whether "total" really forces termination.
+    let out := scaleCoords coords factor
+    let mut i := (1:Nat)
+    while i > 0
+    invariant out = scaleCoords coords factor
+    do
+      i := i + 1
     return out
     -- impl-end
 end
```

Attack 12 — `atk_12.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -64,10 +64,10 @@
   ensures out.length = coords.length
   do
     -- impl-start
-    -- Delegate to the library's existing point-by-scalar scaling operation (the
-    -- per-coordinate product), and return its result — so left-multiplication by
-    -- a number matches right-multiplication by the same number.
-    let out :| out = scaleCoords coords factor
+    -- ATTACK 12 (vacuity): the demonic choice has NO satisfying value at all.
+    -- If an unsatisfiable choice discharges the postconditions vacuously, the
+    -- spec admits an operator that can never return anything.
+    let out :| False
     return out
     -- impl-end
 end
```

Attack 13 — `atk_13.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -64,10 +64,21 @@
   ensures out.length = coords.length
   do
     -- impl-start
-    -- Delegate to the library's existing point-by-scalar scaling operation (the
-    -- per-coordinate product), and return its result — so left-multiplication by
-    -- a number matches right-multiplication by the same number.
-    let out :| out = scaleCoords coords factor
+    -- ATTACK 13 (control-flow off-by-one): scale the coordinates with an
+    -- explicit terminating loop, but stop one short — the LAST coordinate is
+    -- returned unscaled.
+    let mut out : List Rat := []
+    let mut rest := coords
+    while rest.length > 1
+    invariant rest.length ≤ coords.length
+    decreasing rest.length
+    do
+      match rest with
+      | [] => rest := []
+      | c :: tl =>
+        out := out ++ [c * factor]
+        rest := tl
+    out := out ++ rest
     return out
     -- impl-end
 end
```

Attack 14 — `atk_14.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -64,10 +64,10 @@
   ensures out.length = coords.length
   do
     -- impl-start
-    -- Delegate to the library's existing point-by-scalar scaling operation (the
-    -- per-coordinate product), and return its result — so left-multiplication by
-    -- a number matches right-multiplication by the same number.
-    let out :| out = scaleCoords coords factor
+    -- ATTACK 14 (partial domain outside the tested inputs): correct for
+    -- integer factors, returns the coordinates unscaled for every fractional
+    -- factor.
+    let out := if factor.den = 1 then scaleCoords coords factor else coords
     return out
     -- impl-end
 end
```

Attack 15 — `atk_15.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -64,10 +64,10 @@
   ensures out.length = coords.length
   do
     -- impl-start
-    -- Delegate to the library's existing point-by-scalar scaling operation (the
-    -- per-coordinate product), and return its result — so left-multiplication by
-    -- a number matches right-multiplication by the same number.
-    let out :| out = scaleCoords coords factor
+    -- ATTACK 15 (grounded-but-wrong oracle): the delegation is an equality
+    -- choice (so the frozen Findable instance applies) yet it commits to the
+    -- WRONG value — the coordinates scaled by the factor PLUS the factor.
+    let out :| out = coords.map (fun c => c * factor + factor)
     return out
     -- impl-end
 end
```

Attack 16 — `atk_16.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -64,10 +64,10 @@
   ensures out.length = coords.length
   do
     -- impl-start
-    -- Delegate to the library's existing point-by-scalar scaling operation (the
-    -- per-coordinate product), and return its result — so left-multiplication by
-    -- a number matches right-multiplication by the same number.
-    let out :| out = scaleCoords coords factor
+    -- ATTACK 16 (partial domain keyed on dimension, outside F2P coverage):
+    -- exact for 2-D and 3-D points (all the hidden tests use), unscaled for any
+    -- point of dimension 4 or more.
+    let out := if coords.length ≤ 3 then scaleCoords coords factor else coords
     return out
     -- impl-end
 end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `ctrl.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial audit of sympy__sympy-17655/velvet. Attacks built by editing ONLY the impl region (lines 66-72); all 16 confirmed same_spec=True AND unsound_evasions=[] (admissible).

VERIFY COMMAND (each): timeout 400/500 bash scripts/lean_verify.sh atk_N.lean|420 . Run 4-concurrent in background batches per instruction.

RESULTS - 16/16 REJECTED (exit=1), 0 verified: 1 atk_1 prepatch-bug re-encode (factor never applied, out:=coords) -> exit 1, unsolved `ensures_2` 2 atk_2 partial domain: unscaled when length<=1 -> exit 1 3 atk_3 boundary: factor=0 returns coords unscaled -> exit 1 4 atk_4 control-flow: scales only the FIRST coordinate (match/cons) -> exit 1 5 atk_5 wrong operator: (·+factor) additive -> exit 1 6 atk_6 right values, reversed order -> exit 1 7 atk_7 dimension: scaled ++ [0] -> exit 1 (fails BOTH ensures_1 and ensures_2) 8 atk_8 ungrounded oracle `out :| out.length = coords.length` -> exit 1 (Findable not synthesizable => obligation not discharged) 9 atk_9 infeasible choice `out = coords AND out = scaleCoords ...` -> exit 1 (failed to synthesize Findable) 10 atk_10 divergence + unscaled value, no measure -> exit 1 ("Decreasing annotations are required in total correctness semantics") 11 atk_11 CORRECT value but routine DIVERGES (while i>0, i:=i+1) -> exit 1, same total-correctness rejection.

Confirms the frozen `termination "total"` is load-bearing: a right-valued but non-returning `__rmul__` would hang the F2P tests and is correctly refused. 12 atk_12 pure vacuity `out :| False` -> exit 1 (failed to synthesize Findable for typeWithName False). The frozen findableEqList instance is equality-shaped only, so it does NOT admit vacuous choices. 13 atk_13 terminating explicit loop, off-by-one: LAST coordinate unscaled -> exit 1 (fails ensures_1 AND ensures_2) 14 atk_14 partial domain keyed on factor.den=1: exact for the integer factors the F2P tests use (5), unscaled for every fractional factor -> exit 1. The postcondition is TOTAL over the modeled Rat domain, not merely test-shaped. 15 atk_15 grounded-but-wrong equality oracle `out = coords.map (c*factor+factor)` (Findable DOES apply here) -> exit 1 16 atk_16 partial domain on dimension: exact for dim<=3 (all F2P coverage), unscaled for dim>=4 -> exit 1

**POSITIVE CONTROL:** bash scripts/lean_verify.sh .../ctrl.lean -> exit 0 (byte-identical copy of the frozen Solution.lean; same_spec=True).
PREPATCH REPRODUCED: .../atk_pre.lean (bundle's Solution_prepatch.lean) -> exit 1, error is exactly `case «ensures_2: out = scaleCoords coords factor»` with goal `coords = scaleCoords coords factor` — G-DIFF discriminates at the intended clause.

ORACLE DISCRIMINATION PROVEN (not speculated). No attack verified, so the protocol's mandatory per-candidate resolve had no candidates; I nonetheless executed two real harness runs to show the oracle refutes here and that spec-rejection tracks oracle-rejection:
(a) atk_1.diff — the FAITHFUL refinement of attack 1 (a real `__rmul__` that returns the point unscaled). `git apply --check` OK at base_commit. run_resolve('sympy__sympy-17655', ...) -> completed=True resolved=False; F2P failure=['test_point','test_point3D'], all 9 P2P pass. So attack 1 is a genuine wrong impl that the spec ALSO rejects — verify and correct agree.
(b) rleg_barelist.diff — R-leg probe (A4): `__rmul__` returns the BARE scaled coordinate list instead of a re-wrapped Point. `git apply --check` OK. run_resolve -> completed=True resolved=False (same F2P failures, 9/9 P2P pass). The constructor wrapper is therefore NOT vacuous, and refinement.md A4's 'identity on the coordinate carrier' is a genuine R+I obligation the harness enforces.
Gold patch `git apply --check` at base_commit: OK. Recorded G-RESOLVE=pass, so `_oracle_cannot_refute_here` is empty — a not-resolved verdict on this instance is informative.

A-LEG AUDIT (the assignment's focus). Only ONE modeled callee: scaleCoords (A-reference) <-> the UNCHANGED Point.`__mul__` at sympy/geometry/point.py:250. Confirmed against the real base_commit worktree: body is `factor = sympify(factor); coords = [simplify(x*factor) for x in self.args]; return Point(coords, evaluate=False)` — matches mapping.md §3.1 verbatim, and it is genuinely untouched by patch.diff (the diff adds only `__rmul__`). Ran the G-AX check myself in the base_commit worktree: `PYTHONPATH=<worktree> python velvet/axiom_check.py` -> 'G-AX OK ... 7 boundary + 20000 fuzz point/factor pairs (seed=17655)'.

So the single trust point is executably validated, and the deep model is a transparent `coords.map (· * factor)` — not an opaque oracle, and NOT an axiom about the function under change (axioms region is empty; 0 axiom decls). refinement.md leg tags: A1=R, A2=R, A3=A-reference, A4=R+I. Every leg is R / A-reference / I — no kind-3, no A-consumed leg, so no unproved `ensures` is consumed anywhere. §D's G-CONF skip is legitimate and matches meta.json conf_skip=true / G-CONF=skip('no-RI-content'); the fidelity weight correctly shifts to G-AX, which passes.

I also empirically checked mapping.md §2's most load-bearing R-leg caveat in a PATCHED worktree: `5*Point`(1,1)->Point2D(5,5); `5*Point3D`(1,1,1)->Point3D(5,5,5); Fraction(1,2)*Point(3,4)->Point2D(3/2,2); but sympify(2.0)*Point(1,1)->2.0*Point2D(1,1) (still an unevaluated Mul). mapping.md documents exactly this — the Rat carrier models the Python-native-scalar case that `__rmul__` actually fires for, and it does not overclaim the SymPy-left-operand case. Honest and correct.

RECORD DEFECT FOUND (advisory, does NOT weaken the spec — flagging for the ledger, not a BROKEN verdict): the 9 attacks retained in verdict.md/meta.json for the prior G-EQ pass are STALE against the current frozen spec. Each uses `set_option loom.semantics.termination "partial"` + `open PartialCorrectness`, whereas the frozen Solution.lean uses "total" + TotalCorrectness. Those two lines sit OUTSIDE the impl region, so they are spec-signature-bearing: spec_signature(current) != spec_signature(retained atk_1) and same_spec returns False. Re-run today, all 9 would be scored 'not a counterexample (changed the spec)', yielding 0 admissible of 9 and an INCONCLUSIVE G-EQ — i.e. the recorded 'eq: 9 attacks re-run, none breaks the spec' no longer describes this artifact. My 16 fresh attacks all keep "total"/TotalCorrectness and are same_spec=True, so this submission re-establishes the falsification floor (16 admissible >> 5) on the CURRENT bytes. Worth noting the partial->total change is a spec TIGHTENING, which is why attacks 10 and 11 (divergence) are now rejected on termination grounds.

**VERDICT:** SOUND. 16 distinct same-spec admissible wrong impls (partial-domain x3, boundary, control-flow-effect x2, wrong-operator, order, dimension, ungrounded-oracle x2, vacuity x2, divergence x2, off-by-one loop) were all rejected by the frozen spec; the positive control verifies; the prepatch twin fails at the discriminating clause; the sole A-reference is executably validated against the real unchanged callee on 20007 pairs; and two faithful wrong-impl refinements were run through the official harness and both correctly failed to resolve, matching the spec's own rejections. No verifying wrong impl exists, so no verify=>correct gap was exhibited.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 16 admissible attacks re-run of 16 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 16 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 16 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean`, `atk_10.lean`, `atk_11.lean`, `atk_12.lean`, `atk_13.lean`, `atk_14.lean`, `atk_15.lean`, `atk_16.lean` |

**Non-vacuity.** The positive control `ctrl.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. 16 same-spec, admissible wrong impls were verified; ZERO verified (all exit=1), so no attack reached the mandatory resolve stage. The spec's discriminating clause `ensures out = scaleCoords coords factor` rejected every one, and 14/16 failed at exactly that named goal (`case «ensures_2: out = scaleCoords coords factor»`).
```

**Attacks re-run (16):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 16 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10.lean` → rejected (same spec, does not verify — good)

Attack 11 — `atk_11.lean` → rejected (same spec, does not verify — good)

Attack 12 — `atk_12.lean` → rejected (same spec, does not verify — good)

Attack 13 — `atk_13.lean` → rejected (same spec, does not verify — good)

Attack 14 — `atk_14.lean` → rejected (same spec, does not verify — good)

Attack 15 — `atk_15.lean` → rejected (same spec, does not verify — good)

Attack 16 — `atk_16.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `ctrl.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial audit of sympy__sympy-17655/velvet. Attacks built by editing ONLY the impl region (lines 66-72); all 16 confirmed same_spec=True AND unsound_evasions=[] (admissible).

VERIFY COMMAND (each): timeout 400/500 bash scripts/lean_verify.sh atk_N.lean|420 . Run 4-concurrent in background batches per instruction.

RESULTS - 16/16 REJECTED (exit=1), 0 verified: 1 atk_1 prepatch-bug re-encode (factor never applied, out:=coords) -> exit 1, unsolved `ensures_2` 2 atk_2 partial domain: unscaled when length<=1 -> exit 1 3 atk_3 boundary: factor=0 returns coords unscaled -> exit 1 4 atk_4 control-flow: scales only the FIRST coordinate (match/cons) -> exit 1 5 atk_5 wrong operator: (·+factor) additive -> exit 1 6 atk_6 right values, reversed order -> exit 1 7 atk_7 dimension: scaled ++ [0] -> exit 1 (fails BOTH ensures_1 and ensures_2) 8 atk_8 ungrounded oracle `out :| out.length = coords.length` -> exit 1 (Findable not synthesizable => obligation not discharged) 9 atk_9 infeasible choice `out = coords AND out = scaleCoords ...` -> exit 1 (failed to synthesize Findable) 10 atk_10 divergence + unscaled value, no measure -> exit 1 ("Decreasing annotations are required in total correctness semantics") 11 atk_11 CORRECT value but routine DIVERGES (while i>0, i:=i+1) -> exit 1, same total-correctness rejection.

Confirms the frozen `termination "total"` is load-bearing: a right-valued but non-returning `__rmul__` would hang the F2P tests and is correctly refused. 12 atk_12 pure vacuity `out :| False` -> exit 1 (failed to synthesize Findable for typeWithName False). The frozen findableEqList instance is equality-shaped only, so it does NOT admit vacuous choices. 13 atk_13 terminating explicit loop, off-by-one: LAST coordinate unscaled -> exit 1 (fails ensures_1 AND ensures_2) 14 atk_14 partial domain keyed on factor.den=1: exact for the integer factors the F2P tests use (5), unscaled for every fractional factor -> exit 1. The postcondition is TOTAL over the modeled Rat domain, not merely test-shaped. 15 atk_15 grounded-but-wrong equality oracle `out = coords.map (c*factor+factor)` (Findable DOES apply here) -> exit 1 16 atk_16 partial domain on dimension: exact for dim<=3 (all F2P coverage), unscaled for dim>=4 -> exit 1

**POSITIVE CONTROL:** bash scripts/lean_verify.sh .../ctrl.lean -> exit 0 (byte-identical copy of the frozen Solution.lean; same_spec=True).
PREPATCH REPRODUCED: .../atk_pre.lean (bundle's Solution_prepatch.lean) -> exit 1, error is exactly `case «ensures_2: out = scaleCoords coords factor»` with goal `coords = scaleCoords coords factor` — G-DIFF discriminates at the intended clause.

ORACLE DISCRIMINATION PROVEN (not speculated). No attack verified, so the protocol's mandatory per-candidate resolve had no candidates; I nonetheless executed two real harness runs to show the oracle refutes here and that spec-rejection tracks oracle-rejection:
(a) atk_1.diff — the FAITHFUL refinement of attack 1 (a real `__rmul__` that returns the point unscaled). `git apply --check` OK at base_commit. run_resolve('sympy__sympy-17655', ...) -> completed=True resolved=False; F2P failure=['test_point','test_point3D'], all 9 P2P pass. So attack 1 is a genuine wrong impl that the spec ALSO rejects — verify and correct agree.
(b) rleg_barelist.diff — R-leg probe (A4): `__rmul__` returns the BARE scaled coordinate list instead of a re-wrapped Point. `git apply --check` OK. run_resolve -> completed=True resolved=False (same F2P failures, 9/9 P2P pass). The constructor wrapper is therefore NOT vacuous, and refinement.md A4's 'identity on the coordinate carrier' is a genuine R+I obligation the harness enforces.
Gold patch `git apply --check` at base_commit: OK. Recorded G-RESOLVE=pass, so `_oracle_cannot_refute_here` is empty — a not-resolved verdict on this instance is informative.

A-LEG AUDIT (the assignment's focus). Only ONE modeled callee: scaleCoords (A-reference) <-> the UNCHANGED Point.`__mul__` at sympy/geometry/point.py:250. Confirmed against the real base_commit worktree: body is `factor = sympify(factor); coords = [simplify(x*factor) for x in self.args]; return Point(coords, evaluate=False)` — matches mapping.md §3.1 verbatim, and it is genuinely untouched by patch.diff (the diff adds only `__rmul__`). Ran the G-AX check myself in the base_commit worktree: `PYTHONPATH=<worktree> python velvet/axiom_check.py` -> 'G-AX OK ... 7 boundary + 20000 fuzz point/factor pairs (seed=17655)'.

So the single trust point is executably validated, and the deep model is a transparent `coords.map (· * factor)` — not an opaque oracle, and NOT an axiom about the function under change (axioms region is empty; 0 axiom decls). refinement.md leg tags: A1=R, A2=R, A3=A-reference, A4=R+I. Every leg is R / A-reference / I — no kind-3, no A-consumed leg, so no unproved `ensures` is consumed anywhere. §D's G-CONF skip is legitimate and matches meta.json conf_skip=true / G-CONF=skip('no-RI-content'); the fidelity weight correctly shifts to G-AX, which passes.

I also empirically checked mapping.md §2's most load-bearing R-leg caveat in a PATCHED worktree: `5*Point`(1,1)->Point2D(5,5); `5*Point3D`(1,1,1)->Point3D(5,5,5); Fraction(1,2)*Point(3,4)->Point2D(3/2,2); but sympify(2.0)*Point(1,1)->2.0*Point2D(1,1) (still an unevaluated Mul). mapping.md documents exactly this — the Rat carrier models the Python-native-scalar case that `__rmul__` actually fires for, and it does not overclaim the SymPy-left-operand case. Honest and correct.

RECORD DEFECT FOUND (advisory, does NOT weaken the spec — flagging for the ledger, not a BROKEN verdict): the 9 attacks retained in verdict.md/meta.json for the prior G-EQ pass are STALE against the current frozen spec. Each uses `set_option loom.semantics.termination "partial"` + `open PartialCorrectness`, whereas the frozen Solution.lean uses "total" + TotalCorrectness. Those two lines sit OUTSIDE the impl region, so they are spec-signature-bearing: spec_signature(current) != spec_signature(retained atk_1) and same_spec returns False. Re-run today, all 9 would be scored 'not a counterexample (changed the spec)', yielding 0 admissible of 9 and an INCONCLUSIVE G-EQ — i.e. the recorded 'eq: 9 attacks re-run, none breaks the spec' no longer describes this artifact. My 16 fresh attacks all keep "total"/TotalCorrectness and are same_spec=True, so this submission re-establishes the falsification floor (16 admissible >> 5) on the CURRENT bytes. Worth noting the partial->total change is a spec TIGHTENING, which is why attacks 10 and 11 (divergence) are now rejected on termination grounds.

**VERDICT:** SOUND. 16 distinct same-spec admissible wrong impls (partial-domain x3, boundary, control-flow-effect x2, wrong-operator, order, dimension, ungrounded-oracle x2, vacuity x2, divergence x2, off-by-one loop) were all rejected by the frozen spec; the positive control verifies; the prepatch twin fails at the discriminating clause; the sole A-reference is executably validated against the real unchanged callee on 20007 pairs; and two faithful wrong-impl refinements were run through the official harness and both correctly failed to resolve, matching the spec's own rejections. No verifying wrong impl exists, so no verify=>correct gap was exhibited.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

Faithfulness-break audit of sympy__sympy-17655/velvet (attacker 2). No diverging input found inside the documented input domain.

(0) SPEC REGION FROZEN. swebench_unified.markers.same_spec(Solution.lean, Solution_prepatch.lean, get_backend('velvet')) == True; spec_signature identical for both files. spec_view confirms the two obligations: `ensures out = scaleCoords coords factor` and `ensures out.length = coords.length`, with `scaleCoords coords factor = coords.map (· * factor)` in the pure region. Solution.lean elaborates via scripts/lean_verify.sh -> EXIT=0 (spec well-posed, not vacuous).

(1) REFERENCE SET CORRECTLY. Modeled function `scalePoint` == the NEW `Point.__rmul__` added by patch.diff at sympy/geometry/point.py:281. Per the task rule I compared against the worktree WITH patch.diff APPLIED (, base f5e965947af2410ded92cfad987aaf45262ea434 + patch), not the base repo. Base-commit worktree () used only for the axiom/deep-model callee `Point.__mul__` (point.py:250), which the patch does not touch. Confirmed base: `5*Point(1,1)` -> TypeError; patched: -> Point2D(5,5).

(2) DEEP-MODEL LEG (A-reference) HOLDS ON THE REAL REPO. Ran the bundle's axiom_check.py in-tree at base_commit: EXIT=0, 'scaleCoords deep model == real UNCHANGED Point.`__mul__` sound and dimension-preserving on 7 boundary + 20000 fuzz pairs (seed=17655)'. Independently stress-tested the sole soundness claim behind it -- that `simplify(x*factor) == x*factor` for exact rationals -- over pathological pairs (0, ±1, 10^50/3, 1/10^50, 2^64/3^40, near-coprime large primes): 0 non-identities.

(3) THE PATCHED FUNCTION ITSELF, DIRECTLY EXERCISED. Independently fuzzed the actual reflected-multiply path `factor * Point(...)` on the PATCHED repo against the model coords.map(·*factor), exact SymPy comparison:
  - F2P boundary: `5*Point`(1,1)==Point(5,5) True; `5*Point3D`(1,1,1)==Point3D(5,5,5) True; `p4*5`==Point(5,5) True.
  - ~3000 exact-rational pairs (dims 2-4) + 8000 pairs (dims 2-6) with numerators/denominators up to 10^12, plus magnitude sweep dims 2..8 with factors {0, ±1, 5, ±10^30, 1/10^30, -7/3} and tiny/huge coordinate sets: 0 mismatches, 0 unexpected exceptions.
  - evaluate=True construction (the real F2P style, not just evaluate=False): 4000 pairs, dims 2-6, 0 mismatches.
  - Constructor-identity leg (mapping.md A4): no reorder, no drop, no zero-pad; `out.length == coords.length` held on every case, incl. all-zero and trailing-zero coordinate tuples. (The length clause is additionally a Lean tautology via scaleCoords_length, so it cannot diverge.)
  - Result is a Point (never an unevaluated Mul) for every documented preimage: int 5/0/-7, Fraction(3,5), Fraction(-22,7), 10^25 -> Point2D.

(4) DOMAIN-BOUNDARY PROBES -- all out of the documented bijection, none a break. mapping.md §2 pins the left-operand preimage of `Rat` as a Python-NATIVE exact scalar (`int`/`Fraction`), because `__rmul__` is Python's reflected hook and only fires for those. Verified each excluded class is genuinely a different operation on the real patched repo, so excluding it removes no behavior the postcondition claims: SymPy `Rational(3,5)`/`Integer(5)` -> AttributeError inside sympy.core.mul (Mul path, never reaches `__rmul__`); `sympify(2.0)` -> Mul `2.0*Point2D(1,3)` and the issue's `p1 + sympify(2.0)*p2` STILL raises GeometryError post-patch (i.e. the gold patch does not fix the SymPy-Float case at all, so it is correctly outside the modeled behavior); bool -> TypeError BooleanAtom; complex 2j -> ValueError imaginary coords. Symbolic/irrational coordinates (x,y / sqrt(3),pi) are outside the coord bijection ('exact SymPy number') yet happen to AGREE with the model anyway. Lean `List Rat` of length 0/1 is unreachable as `self.args` (Point requires >=2 coords) -- a domain widening, not an over-strong claim, and the postcondition holds trivially there.

(5) STRONGEST CANDIDATE BREAK, EXAMINED AND REJECTED. mapping.md §2 carries a parenthetical 'Floats are exact-order-modeled as Rat too'. If a Python float were admitted as the `Rat` preimage the model would be too strong: 0.1 * Point(1,3) really returns Point2D(0.1000..., 0.3000...) whose second coordinate is exactly 1351079888211149/4503599627370496, while the model predicts Fraction(0.1)*3 = 10808639105689191/36028797018963968 -- a 1-ulp gap, and SymPy `==` on that coordinate is False (Point equality False).

I do NOT report this as UNFAITHFUL: (a) the bijection's operative row is int/Fraction, and every Rat value has such a preimage, on which real == model with 0 divergences across all runs above; (b) the parenthetical explicitly pins 'only the exact scaling relation', which is the sanctioned exact/Real float abstraction of velvet spec_guide.md:154 -- legitimate precisely because precision is NOT the behavior under change here (the bug is 'left-multiply raises instead of scaling', and `__mul__`'s own docstring already documents float->Float coercion as pre-existing, unchanged behavior); (c) the discriminating content of the patch, the F2P assertions, and G-RESOLVE all live in the exact-rational class, so the exact-rational carrier neither excludes the reviewer-relevant class nor destroys the instance. Recorded as a documentation nit on that one parenthetical, not a spec defect: no input in the domain the postcondition actually claims produces disagreement.

**CONCLUSION:** the spec is not too strong and does not drift from real repo behavior. Model and real patched `Point.__rmul__` agree on every one of ~15,000+ probed inputs spanning the documented domain, all dimensions 2-8, all magnitudes, and every boundary case; the unchanged-callee deep model is confirmed sound by a live G-AX run at base_commit. Verdict FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-AX `pass` (the axiom battery). The account names `Solution.lean`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

Leakage / gold-reconstruction audit of sympy__sympy-17655/velvet (measurements, not inherited dispositions).

**WHAT I RAN.**

(1) Spec-region identity: sys.path=src; swebench_unified.markers.same_spec(Solution.lean, Solution_prepatch.lean, VelvetBackend.language) == True, and spec_view(Solution) == spec_view(Solution_prepatch) byte-for-byte, so the spec view carries no post-patch-only text.

(2) Recomputed sha256 of spec_view = 5e66e2fafbc505066af12802b5bb39d6bc915149a8354618e2b5d078407ba528, which matches meta.json G-HYGIENE region_hashes.spec_view exactly (the audited view is the shipped view; not a stale hash).

(3) scripts/lean_verify.sh Solution.lean -> exit 0 (spec well-posed, gold-faithful impl verifies).

(4) scripts/lean_verify.sh Solution_prepatch.lean -> exit 1, 'Solution_prepatch.lean:75:25: error: unsolved goals' -- the discriminating clause `out = scaleCoords coords factor` really rejects the pre-patch 'factor never applied' behaviour (`let out := coords`), so the spec view is discriminating without naming the mechanism.

(5) Token scan of the projected spec view for gold-edit vocabulary: no '`__rmul__`', no '`__mul__`', no 'point.py', no 'geometry', no 'evaluate=False', no 'simplify', no 'sympify', no 'NotImplemented', no 'reflected', no 'hook', no 'delegat', no ':280', no 'Point('. The only hit for 'Mul' is the substring in the English words 'Multiplying'/'multiplied' in the method docstring, not the SymPy Mul class.

BASELINE COMPARISON (public problem_statement only; hints_text deliberately excluded). The statement shows `point1 + point2 * sympify(2.0)` working, `point1 + sympify(2.0) * point2` raising, the traceback text 'Don't know how to add 2.0*Point2D(1, 1) and a Point object' (i.e. the left form yields an unevaluated product rather than a point), and closes with 'The expected behaviour is, that both lines give the same result'.

Every semantic commitment in the spec view is inside that envelope: the docstring's 'when a numeric factor is multiplied on the LEFT of a point, the result is the same scaled point you get by multiplying the point by that factor on the right' is a restatement of 'both lines give the same result'; 'produces a point, not an unevaluated product' restates the public traceback's Mul-vs-Point failure; the postconditions `out = scaleCoords coords factor` (= coords.map (· * factor)) and `out.length = coords.length` are the per-coordinate scaling the statement's working right-multiplication line already demonstrates. Nothing in the view discloses the gold edit's mechanism -- that the fix is a new dunder `__rmul__` on Point delegating `return self.__mul__(factor)` at sympy/geometry/point.py:280.

That mechanism appears only in the elided impl region (line 67 comment 'Delegate to the library's existing point-by-scalar scaling operation'), which spec_view replaces with the elision placeholder, and in mapping.md/refinement.md, which are audit-provenance docs and not part of the consumer view. Notably the one true mechanism giveaway in the dataset -- hints_text's 'this would be a matter of defining `__rmul__` for Point' -- is absent from the spec view even though it would have been the easy phrasing.

**RELAXATION CLAIM:** none exists here. meta.json has no `relaxed_leakage` key (keys checked directly) and there is no RELAXED_LEAKAGE.md in the bundle, so this is an unrelaxed NO-LEAKAGE on the ordinary standard, not a judged-relaxation pass. No facet-carve-out was needed or relied on.

**BUNDLE-ADDRESSES-THE-PANEL CHECK:** I grepped the whole bundle (*.lean, *.md, *.py, meta.json) for text aimed at a reviewer -- 'attacker', 'as an auditor/reviewer', 'the honest verdict', 'please record/submit/return', 'do not flag/report', 'override', verdict strings NO-LEAKAGE/LEAKAGE outside the gate-owned ledgers. Clean: no file instructs the panel how to record or which verdict to reach. The only NO-LEAKAGE/LEAKAGE strings live in verdict.md's Role-4 section, which is the prior run's recorded ledger entry, not an instruction; I re-derived the conclusion independently above rather than adopting it (and my derivation adds the two lean_verify runs and the spec_view/G-HYGIENE hash match, which that entry did not report).

**RESIDUAL:** the spec view does state the modeling choice of exact rationals (Rat) for factor and coordinates, which narrows the domain relative to the statement's `sympify(2.0)` float example. That is a faithfulness/altitude question about the carrier (and is in G-PANEL-2's lane, where it was examined), not a disclosure of the gold edit -- it tells a solver nothing about `__rmul__`/`__mul__` and would not shortcut reconstruction.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
