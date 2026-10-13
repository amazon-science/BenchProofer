# P2 adversarial audit — matplotlib__matplotlib-24149

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 11 admissible attacks re-run of 11 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 11 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 10 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_9.lean`, `atk_10.lean`, `atk_11.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_8.lean` |

**Non-vacuity.** The positive control `ctl_gold.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec wrong implementation verified. 11 attacks, all same_spec=True and admissible=True; 10 of 11 REJECTED (lean_verify exit 1). The single verifier (atk_8) is the ungrounded-oracle echo 'implementation := chooseRepresentative arg', which is NOT a wrong impl: theorem echo_eq_gold (wit_echo_eq_gold.lean, exit 0) proves it denotationally IDENTICAL to the gold impl on the whole CoordArg domain, and its faithful refined patch (patch_atk_8.diff, a one-place _representative() factoring of the same three-way selection including the StopIteration fall-back) RESOLVES under the official harness (resolved=True, F2P test_bar_all_nan[png] success, 0 P2P failures). So verify=>correct holds on every probe run.
```

**Attacks re-run (11):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -99,7 +99,7 @@
     for v in vs do
       if v.countsAsFinite then
         return (some v)
-    return vs.head?
+    return none
   | .unsearched vs => return vs.head?
 -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -94,7 +94,7 @@
 -- impl-start
 def implementation_safeRepresentative (arg : CoordArg) : Option CoordVal := Id.run do
   match arg with
-  | .single v => return (some v)
+  | .single v => if v.countsAsFinite then return (some v) else return none
   | .sequence vs =>
     for v in vs do
       if v.countsAsFinite then
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -97,8 +97,9 @@
   | .single v => return (some v)
   | .sequence vs =>
     for v in vs do
-      if v.countsAsFinite then
-        return (some v)
+      match v with
+      | .numeric x => if x.isFinite then return (some v)
+      | _          => pure ()
     return vs.head?
   | .unsearched vs => return vs.head?
 -- impl-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -97,8 +97,9 @@
   | .single v => return (some v)
   | .sequence vs =>
     for v in vs do
-      if v.countsAsFinite then
-        return (some v)
+      match v with
+      | .missing => return (some v)
+      | _        => if v.countsAsFinite then return (some v)
     return vs.head?
   | .unsearched vs => return vs.head?
 -- impl-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -100,7 +100,11 @@
       if v.countsAsFinite then
         return (some v)
     return vs.head?
-  | .unsearched vs => return vs.head?
+  | .unsearched vs =>
+    for v in vs do
+      if v.countsAsFinite then
+        return (some v)
+    return vs.head?
 -- impl-end
 
 -- proof-start
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -99,7 +99,7 @@
     for v in vs do
       if v.countsAsFinite then
         return (some v)
-    return vs.head?
+    return vs.getLast?
   | .unsearched vs => return vs.head?
 -- impl-end
 
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -96,7 +96,7 @@
   match arg with
   | .single v => return (some v)
   | .sequence vs =>
-    for v in vs do
+    for v in vs.take 2 do
       if v.countsAsFinite then
         return (some v)
     return vs.head?
```

Attack 8 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -92,15 +92,8 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_safeRepresentative (arg : CoordArg) : Option CoordVal := Id.run do
-  match arg with
-  | .single v => return (some v)
-  | .sequence vs =>
-    for v in vs do
-      if v.countsAsFinite then
-        return (some v)
-    return vs.head?
-  | .unsearched vs => return vs.head?
+def implementation_safeRepresentative (arg : CoordArg) : Option CoordVal :=
+  chooseRepresentative arg
 -- impl-end
 
 -- proof-start
@@ -123,13 +116,5 @@
 theorem correct_safeRepresentative : ∀ arg : CoordArg,
     problem_spec_safeRepresentative arg (implementation_safeRepresentative arg) := by
   intro arg
-  unfold problem_spec_safeRepresentative implementation_safeRepresentative chooseRepresentative
-  cases arg with
-  | single v => rfl
-  | sequence vs =>
-    simp only [Id.run, bind, forIn_firstFinite_helper]
-    cases h : vs.find? (fun v => v.countsAsFinite) with
-    | none => rfl
-    | some v => rfl
-  | unsearched vs => rfl
+  rfl
 -- proof-end
```

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -96,7 +96,7 @@
   match arg with
   | .single v => return (some v)
   | .sequence vs =>
-    for v in vs do
+    for v in vs.tail do
       if v.countsAsFinite then
         return (some v)
     return vs.head?
```

Attack 10 — `atk_10.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -100,7 +100,7 @@
       if v.countsAsFinite then
         return (some v)
     return vs.head?
-  | .unsearched vs => return vs.head?
+  | .unsearched vs => return vs.getLast?
 -- impl-end
 
 -- proof-start
```

Attack 11 — `atk_11.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -95,11 +95,7 @@
 def implementation_safeRepresentative (arg : CoordArg) : Option CoordVal := Id.run do
   match arg with
   | .single v => return (some v)
-  | .sequence vs =>
-    for v in vs do
-      if v.countsAsFinite then
-        return (some v)
-    return vs.head?
+  | .sequence vs => return vs.head?
   | .unsearched vs => return vs.head?
 -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `ctl_gold.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

**PROTOCOL.** Base worktree at af39f1edffcd828f05cfdd04f2e59506bb4a27bc: (git worktree add --detach from the upstream repository). Verify command for EVERY lean file: `bash scripts/lean_verify.sh <f>.lean` from the repo root. Same-spec/admissibility recomputed mechanically for all 11 attacks with markers.same_spec + variant_scope.unsound_evasions: all same_spec=True, admissible=True (no new axiom/sorry/native_decide, correct_safeRepresentative statement byte-identical). Attack verifications were launched concurrently in batches of 4 background jobs; resolve runs were serialized ONE AT A TIME (gold control first, then atk_8) exactly as instructed, so no ImageNotFound and the gold control is certified.

**POSITIVE CONTROL.** ctl_gold.lean = Solution.lean byte-for-byte: exit 0. Axiom probe (a separate copy probe_ctl_gold.lean with a trailing `#print axioms correct_safeRepresentative`, which is deliberately NOT an attack because appending outside the regions makes same_spec False): exit 0, 'correct_safeRepresentative depends on axioms: [propext, Quot.sound]' -- CLEAN (no sorryAx, no Classical.choice, no declared callee axiom; the bundle declares none).

PREPATCH REPRODUCED = true. atk_1.lean is the prepatch bug re-encoded (the searched-sequence non-empty fall-back is dropped: `return none` in place of `return vs.head?`), matching Solution_prepatch.lean's impl region exactly. exit 1 with a genuine `Tactic rfl failed` on the sequence/none case (`match Option.map some none ... is not definitionally equal to ... match none with | some v => some v | none => vs.head?`), i.e. the G-DIFF signal is live and it is a real spec rejection, not a tactic accident.

THE 11 ATTACKS (path, exit code, kind). All, all same_spec=True + admissible=True.
1. atk_1.lean  exit 1  PREPATCH BUG: searched-sequence non-empty fall-back dropped (`return none`).
2. atk_2.lean  exit 1  weak-single-filtered / the HOISTED relocation: the LONE coordinate is passed through the finiteness test (`if v.countsAsFinite then some v else none`). This is the mis-placement refinement.md rows 2/6 exist to pin.
3. atk_3.lean  exit 1  UNGROUNDED-ORACLE-ADJACENT / bare-arithmetic substitution: matches on the regime and only weighs `.numeric`, so an `.unweighable` value is SKIPPED (i.e. np.isfinite substituted for the real safe_isfinite). This is the substitution the refinement.md 'three regimes' section claims is pinned.
4. atk_4.lean  exit 1  converse mis-ruling: a `.missing` value is COUNTED as finite.
5. atk_5.lean  exit 1  CONTROL-FLOW-EFFECT: the `.unsearched` sequence (the np.flatiter branch, which is read at position 0 unfiltered) gets the finiteness SEARCH run over it anyway.
6. atk_6.lean  exit 1  BOUNDARY: the exhausted-search fall-back returns `vs.getLast?` instead of `vs.head?`.
7. atk_7.lean  exit 1  PARTIAL DOMAIN: the search covers only a bounded prefix (`vs.take 2`), so it is correct on short sequences and wrong beyond.
8. atk_8.lean  exit 0  UNGROUNDED-ORACLE ECHO: `implementation := chooseRepresentative arg`, proof is `intro arg; rfl`. VERIFIES -- see the resolve leg below.
9. atk_9.lean  exit 1  OFF-BY-ONE: the search skips the leading element (`for v in vs.tail`).
10. atk_10.lean exit 1  targets the LEAST-DOCUMENTED arm: `.unsearched vs => vs.getLast?` (collapses the third shape's leading-position read onto the trailing element).
11. atk_11.lean exit 1  the search is DROPPED entirely on `.sequence` (the fall-back hoisted to run unconditionally), so the leading element always wins.

EVERY REJECTION IS A GENUINE SPEC REJECTION, NOT A TACTIC ACCIDENT. For each of the 10 rejected attacks I built a WITNESS file wit_atk_N.lean carrying that attack's impl region VERBATIM and, in place of the proof region, a kernel-checked divergence: `implementation_safeRepresentative <arg> = <lhs>` by rfl, `chooseRepresentative <arg> = <rhs>` by rfl, and `NOT problem_spec_safeRepresentative <arg> (implementation_safeRepresentative <arg>)`. ALL TEN close at exit 0 (wit_atk_1, wit_atk_2, wit_atk_3, wit_atk_4, wit_atk_5, wit_atk_6, wit_atk_7, wit_atk_9, wit_atk_10, wit_atk_11), so for each attack there provably EXISTS an input where the impl contradicts the frozen postcondition -- no proof of correct_safeRepresentative could exist.

The witnesses are deliberately FLOAT-FREE (they use `.missing`, which never counts, and `.unweighable`, which always counts, both definitionally) so nothing rests on opaque kernel Float order; the sole exception is wit_atk_6, where the getLast? fall-back needs two DISTINCT non-counting values and therefore one non-finite numeric, so it is parameterized on the hypothesis `(c : Float) (hc : c.isFinite = false)` -- discharged in reality by nan.

Divergence inputs used: atk_1 sequence[missing] (none vs some missing); atk_2 single missing; atk_3/atk_4 sequence[missing, unweighable 7]; atk_5 unsearched[missing, unweighable 7]; atk_6 sequence[missing, numeric c]; atk_7 sequence[missing, missing, unweighable 7]; atk_9 sequence[unweighable 1, unweighable 2]; atk_10 unsearched[unweighable 1, unweighable 2]; atk_11 sequence[missing, unweighable 7].

THE ONE VERIFIER, AND ITS MANDATORY RESOLVE. atk_8 is the oracle echo and it is the only attack that verifies. Axioms probe (probe_atk_8.lean): exit 0, 'correct_safeRepresentative does not depend on any axioms' -- CLEAN. Per protocol I materialized its FAITHFUL refined patch and RAN it. Faithfulness argument is machine-checked, not asserted: wit_echo_eq_gold.lean declares both impls side by side and proves `theorem echo_eq_gold : forall arg, implementation_safeRepresentative_echo arg = implementation_safeRepresentative arg` -- exit 0. So the echo is not a distinct behavior at all; it is the gold selection written as one applied function where the gold source inlines it twice. Its faithful realization therefore factors the real three-way selection into a single helper and applies it to both x0 and xconv: patch_atk_8.diff introduces `def _representative(obj)` inside `_convert_dx` with `try: return cbook._safe_first_finite(obj) / except (TypeError, IndexError, KeyError): return obj / except StopIteration: return cbook.safe_first_element(obj)` and then `x0 = _representative(x0); x = _representative(xconv)`. It carries the StopIteration fall-back that IS the fix.
### RESOLVE RESULTS (serialized, one at a time, same instance):
  (a) GOLD CONTROL first -- patch_gold.diff (the instance.json gold hunk re-materialized from the worktree): run_resolve('matplotlib__matplotlib-24149', patch) => resolved=True. Control certified, so the attack's resolve result is meaningful.
  (b) ATTACK -- patch_atk_8.diff: run_resolve => resolved=True, completed=True, note='resolved', attempts=1, flaky=False; report: patch_successfully_applied=True, FAIL_TO_PASS success=['lib/matplotlib/tests/test_axes.py::test_bar_all_nan[png]'] failure=[], PASS_TO_PASS failure=[] (all 767 pass).
Both diffs were checked with `git apply --check` at base_commit: both APPLY OK.
So the ONE impl with a closing clean-axiom proof has a materialized faithful patch that DOES resolve. Nothing breaks verify=>correct, hence SOUND rather than BROKEN.

A-LEG AUDIT (my assigned focus; R/I legs left to G-CONF). refinement.md declares 7 rows: 1 R, 2 A-reference, 3 A-reference, 4 A-reference, 4b R, 5 I, 6 A-reference. NO kind-3 (changed-inexpressible) row and NO A-consumed row, consistent with the axioms region declaring nothing and with the clean `#print axioms` above -- the proof discharges chooseRepresentative directly, so there is no assumed callee property that could paper over a divergence. The axioms region is a prose-only justification block, which is the right shape here. I validated the three A-reference legs against the REAL callees rather than against the prose.

`cbook._safe_first_finite` / `safe_first_element` are UNCHANGED by the patch, so I reconstructed them verbatim`__init__`.py at base_commit, rebuilt the exact post-patch selection (the gold hunk's two try/except ladders), and compared it against a transcription of chooseRepresentative over 31 inputs spanning all three CoordArg shapes and all three CoordVal regimes: 0/31 MISMATCHES.

Coverage: lone 1.0/nan/inf/np.float64/datetime/timedelta/Decimal/0-d ndarray/None (row 2 -- confirmed the TypeError route applies NO finiteness test, so a lone nan and a lone datetime are each their own representative); sequences [nan,2.0], [nan], [nan,inf,-inf], [datetime,datetime], [datetime,2.0], [timedelta,datetime], [Decimal,2.0], ['a',2.0], [None,2.0], [None,nan], [None], [None,None,datetime], [[1,2],3.0], [asarray(nan),2.0], tuple, ndarray, all-nan ndarray (rows 3/4/6 -- confirmed safe_isfinite is a THREE-way ruling and not np.isfinite: it COUNTS unweighables, REFUSES None, and [None,nan] selects None as the head fall-back); empty list and empty ndarray (both -> none); and three np.flatiter cases.

The mapping.md claim that safe_isfinite has three regimes and that bar()/barh() pass x0 verbatim so a list of datetimes reaches the scan un-coerced is CORRECT as measured, and it is what makes attacks 3 and 4 rejectable rather than admissible -- the A-reference legs are load-bearing and they hold.

ONE DOCUMENTATION GAP, REPORTED AS ADVISORY (not a spec break, does not move the verdict). The spec's third constructor `CoordArg.unsearched` has NO row in refinement.md's operation table -- the table's 7 rows cover `.single` (row 2) and `.sequence` (rows 3/5/6) but never name `.unsearched`, and the impl op `| .unsearched vs => return vs.head?` is consequently unmapped. mapping.md does cover it, but only obliquely and in a way that UNDERSTATES it: the 'Flag dependency' section calls np.flatiter 'OUT of the declared domain'.

I measured that this is not quite right. bar() passes x0 = x VERBATIM, so `ax.bar(np.array([nan,2.0]).flat, [1.0,1.0])` really does deliver a flatiter into the modeled selection (it ran without error), and the real callee's flatiter branch returns `obj[0]` UNFILTERED -- which is exactly `.unsearched vs => vs.head?`. So the constructor is REACHABLE and its modeling is CORRECT (my 31-case probe includes three flatiter rows, all OK); the defects are that refinement.md omits the row entirely and that mapping.md's 'out of the declared domain' framing contradicts the model actually carrying the arm.

Since the arm is modeled correctly and pins real behavior, this weakens no obligation -- and I confirmed the spec still rejects impls that get that arm wrong (atk_5 and atk_10 both target it and both reject with closing witnesses at exit 0). Recommend adding an A-reference row for `.unsearched` <-> the np.flatiter branch of `_safe_first_finite` and softening the 'out of domain' sentence; this is a refinement.md/mapping.md prose fix, not a Solution.lean change, so it would not disturb spec_signature or any retained attack.

**VERDICT:** SOUND. 11 same-spec admissible attacks were built and fully verified (well above the >=5 floor), spanning the prepatch bug, the named prior counterexamples (weak-single-filtered, the bare-arithmetic/unweighable-skipped substitution, weak-missing-counted), plus partial-domain, boundary, control-flow-effect, off-by-one, search-dropped and least-documented-arm families, and an ungrounded-oracle echo. 10 of 11 were rejected, each rejection corroborated by an independently closing divergence witness. The single verifier is provably equivalent to gold (echo_eq_gold, exit 0) and its faithful patch RESOLVES (resolved=True) against a certified gold control (resolved=True). No implementation with a closing clean-axiom proof has a faithful patch that fails to resolve, so verify=>correct is not broken on any probe I could construct.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 11 admissible attacks re-run of 11 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 11 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 10 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_9.lean`, `atk_10.lean`, `atk_11.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_8.lean` |

**Non-vacuity.** The positive control `ctl_gold.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec wrong implementation verified. 11 attacks, all same_spec=True and admissible=True; 10 of 11 REJECTED (lean_verify exit 1). The single verifier (atk_8) is the ungrounded-oracle echo 'implementation := chooseRepresentative arg', which is NOT a wrong impl: theorem echo_eq_gold (wit_echo_eq_gold.lean, exit 0) proves it denotationally IDENTICAL to the gold impl on the whole CoordArg domain, and its faithful refined patch (patch_atk_8.diff, a one-place _representative() factoring of the same three-way selection including the StopIteration fall-back) RESOLVES under the official harness (resolved=True, F2P test_bar_all_nan[png] success, 0 P2P failures). So verify=>correct holds on every probe run.
```

**Attacks re-run (11):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 11 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10.lean` → rejected (same spec, does not verify — good)

Attack 11 — `atk_11.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `ctl_gold.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

**PROTOCOL.** Base worktree at af39f1edffcd828f05cfdd04f2e59506bb4a27bc: (git worktree add --detach from the upstream repository). Verify command for EVERY lean file: `bash scripts/lean_verify.sh <f>.lean` from the repo root. Same-spec/admissibility recomputed mechanically for all 11 attacks with markers.same_spec + variant_scope.unsound_evasions: all same_spec=True, admissible=True (no new axiom/sorry/native_decide, correct_safeRepresentative statement byte-identical). Attack verifications were launched concurrently in batches of 4 background jobs; resolve runs were serialized ONE AT A TIME (gold control first, then atk_8) exactly as instructed, so no ImageNotFound and the gold control is certified.

**POSITIVE CONTROL.** ctl_gold.lean = Solution.lean byte-for-byte: exit 0. Axiom probe (a separate copy probe_ctl_gold.lean with a trailing `#print axioms correct_safeRepresentative`, which is deliberately NOT an attack because appending outside the regions makes same_spec False): exit 0, 'correct_safeRepresentative depends on axioms: [propext, Quot.sound]' -- CLEAN (no sorryAx, no Classical.choice, no declared callee axiom; the bundle declares none).

PREPATCH REPRODUCED = true. atk_1.lean is the prepatch bug re-encoded (the searched-sequence non-empty fall-back is dropped: `return none` in place of `return vs.head?`), matching Solution_prepatch.lean's impl region exactly. exit 1 with a genuine `Tactic rfl failed` on the sequence/none case (`match Option.map some none ... is not definitionally equal to ... match none with | some v => some v | none => vs.head?`), i.e. the G-DIFF signal is live and it is a real spec rejection, not a tactic accident.

THE 11 ATTACKS (path, exit code, kind). All, all same_spec=True + admissible=True.
1. atk_1.lean  exit 1  PREPATCH BUG: searched-sequence non-empty fall-back dropped (`return none`).
2. atk_2.lean  exit 1  weak-single-filtered / the HOISTED relocation: the LONE coordinate is passed through the finiteness test (`if v.countsAsFinite then some v else none`). This is the mis-placement refinement.md rows 2/6 exist to pin.
3. atk_3.lean  exit 1  UNGROUNDED-ORACLE-ADJACENT / bare-arithmetic substitution: matches on the regime and only weighs `.numeric`, so an `.unweighable` value is SKIPPED (i.e. np.isfinite substituted for the real safe_isfinite). This is the substitution the refinement.md 'three regimes' section claims is pinned.
4. atk_4.lean  exit 1  converse mis-ruling: a `.missing` value is COUNTED as finite.
5. atk_5.lean  exit 1  CONTROL-FLOW-EFFECT: the `.unsearched` sequence (the np.flatiter branch, which is read at position 0 unfiltered) gets the finiteness SEARCH run over it anyway.
6. atk_6.lean  exit 1  BOUNDARY: the exhausted-search fall-back returns `vs.getLast?` instead of `vs.head?`.
7. atk_7.lean  exit 1  PARTIAL DOMAIN: the search covers only a bounded prefix (`vs.take 2`), so it is correct on short sequences and wrong beyond.
8. atk_8.lean  exit 0  UNGROUNDED-ORACLE ECHO: `implementation := chooseRepresentative arg`, proof is `intro arg; rfl`. VERIFIES -- see the resolve leg below.
9. atk_9.lean  exit 1  OFF-BY-ONE: the search skips the leading element (`for v in vs.tail`).
10. atk_10.lean exit 1  targets the LEAST-DOCUMENTED arm: `.unsearched vs => vs.getLast?` (collapses the third shape's leading-position read onto the trailing element).
11. atk_11.lean exit 1  the search is DROPPED entirely on `.sequence` (the fall-back hoisted to run unconditionally), so the leading element always wins.

EVERY REJECTION IS A GENUINE SPEC REJECTION, NOT A TACTIC ACCIDENT. For each of the 10 rejected attacks I built a WITNESS file wit_atk_N.lean carrying that attack's impl region VERBATIM and, in place of the proof region, a kernel-checked divergence: `implementation_safeRepresentative <arg> = <lhs>` by rfl, `chooseRepresentative <arg> = <rhs>` by rfl, and `NOT problem_spec_safeRepresentative <arg> (implementation_safeRepresentative <arg>)`. ALL TEN close at exit 0 (wit_atk_1, wit_atk_2, wit_atk_3, wit_atk_4, wit_atk_5, wit_atk_6, wit_atk_7, wit_atk_9, wit_atk_10, wit_atk_11), so for each attack there provably EXISTS an input where the impl contradicts the frozen postcondition -- no proof of correct_safeRepresentative could exist.

The witnesses are deliberately FLOAT-FREE (they use `.missing`, which never counts, and `.unweighable`, which always counts, both definitionally) so nothing rests on opaque kernel Float order; the sole exception is wit_atk_6, where the getLast? fall-back needs two DISTINCT non-counting values and therefore one non-finite numeric, so it is parameterized on the hypothesis `(c : Float) (hc : c.isFinite = false)` -- discharged in reality by nan.

Divergence inputs used: atk_1 sequence[missing] (none vs some missing); atk_2 single missing; atk_3/atk_4 sequence[missing, unweighable 7]; atk_5 unsearched[missing, unweighable 7]; atk_6 sequence[missing, numeric c]; atk_7 sequence[missing, missing, unweighable 7]; atk_9 sequence[unweighable 1, unweighable 2]; atk_10 unsearched[unweighable 1, unweighable 2]; atk_11 sequence[missing, unweighable 7].

THE ONE VERIFIER, AND ITS MANDATORY RESOLVE. atk_8 is the oracle echo and it is the only attack that verifies. Axioms probe (probe_atk_8.lean): exit 0, 'correct_safeRepresentative does not depend on any axioms' -- CLEAN. Per protocol I materialized its FAITHFUL refined patch and RAN it. Faithfulness argument is machine-checked, not asserted: wit_echo_eq_gold.lean declares both impls side by side and proves `theorem echo_eq_gold : forall arg, implementation_safeRepresentative_echo arg = implementation_safeRepresentative arg` -- exit 0. So the echo is not a distinct behavior at all; it is the gold selection written as one applied function where the gold source inlines it twice. Its faithful realization therefore factors the real three-way selection into a single helper and applies it to both x0 and xconv: patch_atk_8.diff introduces `def _representative(obj)` inside `_convert_dx` with `try: return cbook._safe_first_finite(obj) / except (TypeError, IndexError, KeyError): return obj / except StopIteration: return cbook.safe_first_element(obj)` and then `x0 = _representative(x0); x = _representative(xconv)`. It carries the StopIteration fall-back that IS the fix.
### RESOLVE RESULTS (serialized, one at a time, same instance):
  (a) GOLD CONTROL first -- patch_gold.diff (the instance.json gold hunk re-materialized from the worktree): run_resolve('matplotlib__matplotlib-24149', patch) => resolved=True. Control certified, so the attack's resolve result is meaningful.
  (b) ATTACK -- patch_atk_8.diff: run_resolve => resolved=True, completed=True, note='resolved', attempts=1, flaky=False; report: patch_successfully_applied=True, FAIL_TO_PASS success=['lib/matplotlib/tests/test_axes.py::test_bar_all_nan[png]'] failure=[], PASS_TO_PASS failure=[] (all 767 pass).
Both diffs were checked with `git apply --check` at base_commit: both APPLY OK.
So the ONE impl with a closing clean-axiom proof has a materialized faithful patch that DOES resolve. Nothing breaks verify=>correct, hence SOUND rather than BROKEN.

A-LEG AUDIT (my assigned focus; R/I legs left to G-CONF). refinement.md declares 7 rows: 1 R, 2 A-reference, 3 A-reference, 4 A-reference, 4b R, 5 I, 6 A-reference. NO kind-3 (changed-inexpressible) row and NO A-consumed row, consistent with the axioms region declaring nothing and with the clean `#print axioms` above -- the proof discharges chooseRepresentative directly, so there is no assumed callee property that could paper over a divergence. The axioms region is a prose-only justification block, which is the right shape here. I validated the three A-reference legs against the REAL callees rather than against the prose.

`cbook._safe_first_finite` / `safe_first_element` are UNCHANGED by the patch, so I reconstructed them verbatim`__init__`.py at base_commit, rebuilt the exact post-patch selection (the gold hunk's two try/except ladders), and compared it against a transcription of chooseRepresentative over 31 inputs spanning all three CoordArg shapes and all three CoordVal regimes: 0/31 MISMATCHES.

Coverage: lone 1.0/nan/inf/np.float64/datetime/timedelta/Decimal/0-d ndarray/None (row 2 -- confirmed the TypeError route applies NO finiteness test, so a lone nan and a lone datetime are each their own representative); sequences [nan,2.0], [nan], [nan,inf,-inf], [datetime,datetime], [datetime,2.0], [timedelta,datetime], [Decimal,2.0], ['a',2.0], [None,2.0], [None,nan], [None], [None,None,datetime], [[1,2],3.0], [asarray(nan),2.0], tuple, ndarray, all-nan ndarray (rows 3/4/6 -- confirmed safe_isfinite is a THREE-way ruling and not np.isfinite: it COUNTS unweighables, REFUSES None, and [None,nan] selects None as the head fall-back); empty list and empty ndarray (both -> none); and three np.flatiter cases.

The mapping.md claim that safe_isfinite has three regimes and that bar()/barh() pass x0 verbatim so a list of datetimes reaches the scan un-coerced is CORRECT as measured, and it is what makes attacks 3 and 4 rejectable rather than admissible -- the A-reference legs are load-bearing and they hold.

ONE DOCUMENTATION GAP, REPORTED AS ADVISORY (not a spec break, does not move the verdict). The spec's third constructor `CoordArg.unsearched` has NO row in refinement.md's operation table -- the table's 7 rows cover `.single` (row 2) and `.sequence` (rows 3/5/6) but never name `.unsearched`, and the impl op `| .unsearched vs => return vs.head?` is consequently unmapped. mapping.md does cover it, but only obliquely and in a way that UNDERSTATES it: the 'Flag dependency' section calls np.flatiter 'OUT of the declared domain'.

I measured that this is not quite right. bar() passes x0 = x VERBATIM, so `ax.bar(np.array([nan,2.0]).flat, [1.0,1.0])` really does deliver a flatiter into the modeled selection (it ran without error), and the real callee's flatiter branch returns `obj[0]` UNFILTERED -- which is exactly `.unsearched vs => vs.head?`. So the constructor is REACHABLE and its modeling is CORRECT (my 31-case probe includes three flatiter rows, all OK); the defects are that refinement.md omits the row entirely and that mapping.md's 'out of the declared domain' framing contradicts the model actually carrying the arm.

Since the arm is modeled correctly and pins real behavior, this weakens no obligation -- and I confirmed the spec still rejects impls that get that arm wrong (atk_5 and atk_10 both target it and both reject with closing witnesses at exit 0). Recommend adding an A-reference row for `.unsearched` <-> the np.flatiter branch of `_safe_first_finite` and softening the 'out of domain' sentence; this is a refinement.md/mapping.md prose fix, not a Solution.lean change, so it would not disturb spec_signature or any retained attack.

**VERDICT:** SOUND. 11 same-spec admissible attacks were built and fully verified (well above the >=5 floor), spanning the prepatch bug, the named prior counterexamples (weak-single-filtered, the bare-arithmetic/unweighable-skipped substitution, weak-missing-counted), plus partial-domain, boundary, control-flow-effect, off-by-one, search-dropped and least-documented-arm families, and an ungrounded-oracle echo. 10 of 11 were rejected, each rejection corroborated by an independently closing divergence witness. The single verifier is provably equivalent to gold (echo_eq_gold, exit 0) and its faithful patch RESOLVES (resolved=True) against a certified gold control (resolved=True). No implementation with a closing clean-axiom proof has a faithful patch that fails to resolve, so verify=>correct is not broken on any probe I could construct.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

FAITHFULNESS-BREAK ATTACK on matplotlib__matplotlib-24149/lean. No divergence found between problem_spec_safeRepresentative/chooseRepresentative and the real post-patch callee. Reference = base worktree af39f1e with patch.diff APPLIED (per instructions).

### Setup
- Fresh worktree at af39f1e, `git apply patch.diff` -> PATCH_OK (lib/matplotlib/axes/`_axes`.py, +8).
- The worktree matplotlib is not built (`_c_internal_utils` missing), so instead of TRANSCRIBING the callees I EXTRACTED `safe_first_element` and `_safe_first_finite` (incl. the inner `safe_isfinite` closure) VERBATIM by regex out of $WT/lib/matplotlib/cbook/`__init__`.py into an importable module. Zero transcription risk on the callee side. `cbook` is untouched by the patch, so base == post-patch for it (correct per the base-commit-is-reference-for-untouched-callees rule).
- Oracle = the patched selection block copied verbatim from the applied worktree: try `_safe_first_finite` / except (TypeError,IndexError,KeyError) -> arg unchanged / except StopIteration -> safe_first_element.

### Verifier
- scripts/lean_verify.sh Solution.lean -> EXIT=0 (only unusedVariable/unusedSimpArg lints).
- #print axioms correct_safeRepresentative -> [propext, Quot.sound]. NO sorryAx. problem_spec/chooseRepresentative depend on no axioms. Proof is real, not fake.
- markers.same_spec(Solution.lean, Solution_prepatch.lean, lean backend) = True: spec region byte-identical, so the discriminator is the impl, not a moved spec.
- Computed spec_view sha256 = dd39bfac46f8ad63... == meta.json gates.G-HYGIENE.data.region_hashes.spec_view. (NOTE, not a finding in this lane: meta.json TOP-LEVEL region_hashes.spec_view = 48dbf7d986e4... disagrees with both the live file and the G-HYGIENE record. Bookkeeping/integrity concern for the owning gate, no bearing on faithfulness.)

### DIFFERENTIAL FUZZ (77,580 inputs, seed 24149)
Encoding follows mapping.md's declared bijection: shape by KIND (flatiter -> .unsearched, 0-d ndarray/non-iterable -> .single, iterable -> .sequence), element by REGIME (None -> .missing; scalar np.isfinite can weigh -> .numeric; else -> .unweighable). Compared by SELECTED POSITION, not by value, so the check is independent of which Float represents a .numeric. Coverage: all lone coordinates; exhaustive ALPHA x ALPHA (55^2) 2-element lists; 60k random lists len 0-5; 6k float ndarrays; 4k object ndarrays; 3k datetime64[D] arrays (incl. NaT); 1.5k fresh flatiters; plus a hand-built exotic-container sweep (dict, set, frozenset, range, bytes, memoryview, np.matrix, np.ma masked/all-masked, 2-D arrays, nested lists, str).

ALPHA deliberately targeted the places a three-regime model usually breaks: nan/+-inf, np.float64/32 nan, 0-d nan arrays, datetime/date/timedelta, Decimal('NaN')/('Infinity'), Fraction, str/'nan'/'', nested seqs, np.datetime64('NaT'), np.timedelta64('NaT'), complex(nan,0)/complex(inf,1), np.longdouble('1e400'), `10**400`, np.ma.masked, n-d array as an ELEMENT, bare object(). RESULT: exactly TWO divergence classes, both EMPTY-SEQUENCE only (real raises/returns-arg-unchanged vs model `none`). Every non-empty input agreed, including all four regime traps I expected to bite:
  - np.datetime64('NaT') / np.timedelta64('NaT'): np.isscalar True and np.isfinite False, so these are .numeric-NOT-counting, NOT .unweighable. Real skips them; model skips them. AGREE.
  - complex(nan,0): weighed, does not count. AGREE. complex(1,2): counts. AGREE.
  - Decimal('NaN'): np.isfinite RAISES TypeError -> real ruling True (.unweighable COUNTS). Model counts it. AGREE - this is the arm a bare-arithmetic model gets backwards.
  - `10**400`: np.isfinite TypeError -> counts; no double image, correctly .unweighable, not .numeric. AGREE.
Early-run 'divergences' on flatiter and datetime64 were MY harness bugs (list(p) consuming the flatiter before real_select saw it; numpy scalars not identity-stable so position lookup failed). Both fixed and re-run; they vanished. I did not report either as spec defects.

### WHY THE EMPTY CASE IS NOT A DEFECT (checked, not assumed)
I probed the upstream guard `if xconv.size == 0: return convert(dx)` directly: for [], (), np.array([]), np.array([],dtype=object), range(0), [[]], and an empty flatiter, np.asarray(x0).size == 0, so the guard fires and the selection is NEVER reached. Empty is therefore genuinely unreachable for every array-like the real callers (bar/barh via x0=x verbatim, broken_barh via xr[0]) can deliver. `none` is also the only total completion available to an Option-valued Lean function, and mapping.md line ~54 and refinement.md row 6 both declare it explicitly ('guarded unreachable upstream, modeled as none'). Declared + unreachable + canonical totalization = modeling, not drift.

Honest residue: an empty NON-array container (set(), {}, frozenset(), '') has np.asarray(...).size == 1, so the guard does NOT fire and the real code raises StopIteration OUT of `_convert_dx` (the fallback's own next(iter(obj)) raises inside the except handler, and StopIteration is not caught by the outer except (ValueError,TypeError,AttributeError)). Model says `none`. This is a real behavioural gap on a pathological argument, but it is an unfixed upstream matplotlib edge case rather than spec over-strength, it is outside the declared domain, and no spec clause forces a correct impl to crash there - so it does not condemn the spec. Recorded for transparency.

### STRENGTH CHECKS (attacker's opposite direction - did the model claim MORE than the repo does?)
- The .single arm's 'no finiteness test applied' clause: measured lone nan, lone inf, lone None, lone datetime, lone 0-d nan array -> real leaves x0 bound to the argument itself in every case. Spec's `some v` matches. Clause is earned, not decorative.
- The .unsearched arm: fresh flatiters, incl. flat of a 2-D array whose leading element is nan -> real returns obj[0] UNFILTERED (np.flatiter branch, TODO in source). Spec's unconditional vs.head? matches. Not over-strong.
- Lean Float.isFinite semantics confirmed by #eval: nan/+-inf/1e400 -> false, 1.0/0.0/-0.0/1e308 -> true. Matches np.isfinite on doubles.
- Numeric carrier round-trip: only np.longdouble('1e400') has no finiteness-preserving DOUBLE image (real counts it, float() gives inf). This is a carrier-granularity question about which Float represents a .numeric, not a behavioural divergence - the selection never inspects a .numeric beyond countsAsFinite, and the bundle's own conformance_check.py encoder rules on the live Python value rather than via float(), so it is finiteness-preserving. Confirmed not a divergence.
- Generators are excluded from CoordArg entirely; mapping.md declares them out of domain (real: RuntimeError). Domain restriction, consistently declared.
- G-DIFF sanity: the discriminating clause is the .sequence all-non-counting fall-back (.sequence [.numeric nan] -> some, not none), which mirrors F2P test_bar_all_nan; the .single and three-regime clauses are identical pre/post-patch and strengthen on axes ORTHOGONAL to the delta. I confirmed I was not measuring the base version against the model at any point - the oracle imports the patched block.

**CONCLUSION:** FAITHFUL. No diverging input on any reachable, in-domain argument across 77,580 differential inputs against verbatim-extracted real callees. Spec is not too strong and does not drift from repo behavior.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

LEAKAGE ROLE (3) — matplotlib__matplotlib-24149 / lean. Judged from scratch on the current bytes (Solution.lean sha256 e6cc7967386ad046...). verdict.md's prior Role-4/G-PANEL-3 sections were opened ONLY to run the bundle-addresses-reviewer check, not for their disposition.

NO DOCUMENTED RELAXATION — checked, not assumed. `[k for k in meta.json if 'relax' in k.lower()]` == [] (top keys: axioms, conf_skip, deep_model_references, gates, modeled_functions, opaque_callees, patch_equals_gold, pbt_audit, prepatch_variants, region_hashes, schema_version, spec_provenance, verifier_pins), and `find <instance_dir> -iname '*RELAX*'` returns nothing. So there is no unavoidability argument to re-derive and no relaxed disposition on offer — this is a plain leakage judgement, and the verdict below is a leakage measurement, not an inherited one.

### What I ran
1. spec_view recomputed myself via markers.spec_view(src, backends.get_backend('lean')). Consumer-visible regions are exactly: imports, axioms, pure, post-conditions; impl and proof are both replaced by the standard ELISION_IMPL/ELISION_PROOF placeholders. The gold implementation body (`return vs.head?`) is NOT in the spec view.
2. markers.same_spec(Solution.lean, Solution_prepatch.lean, lean) == True — the spec region is byte-identical across the pre/post pair, so the spec was not tuned around the fix.
3. scripts/lean_verify.sh Solution.lean -> exit 0, no sorry (only unusedVariables / unusedSimpArgs style warnings). `#print axioms correct_safeRepresentative` -> [propext, Quot.sound]: clean, no sorryAx, so the proof is real.
4. leakage.screen(src, lean, instance['patch'], instance['problem_statement'], instance['test_patch']) -> hard_failures=[], warnings=[]. Judged against problem_statement only; I did NOT let hints_text count as public (hints_text here literally contains the gold diff verbatim, so treating it as public would have laundered a real leak).
5. Hand token sweep of the spec view for the edit's whole vocabulary: StopIteration, safe_first_element, `_safe_first_finite`, safe_isfinite, cbook, `_convert_dx`, x0, xconv, delist, np.iterable, `_axes`.py, matplotlib, bar(, seaborn, 3.6, flatiter, and narration words (fix/fixed/bug/patch/previously/was/no longer/instead of/regression/exception/raise/except/handler/fall back) — ZERO hits. The single word-fragment hit is 'change' inside 'No UNCHANGED callee needs an opaque signature here', which is scaffold prose about axiom hygiene, not the delta.
6. G-DIFF re-derived independently rather than inherited: I substituted only the prepatch fallback (`return vs.head?` -> `return none` in the .sequence arm) into Solution.lean while KEEPING the gold proof body verbatim, and verified. It fails with a genuine `Tactic rfl failed` at `case sequence.none` (LHS `match Option.map some none ...` vs RHS `match none with | some v => some v | none => vs.head?`) — a real semantic non-closure, not a tactic accident. So the removed clause is load-bearing and the spec genuinely discriminates gold from prepatch.
7. Bundle-addresses-reviewer check: leakage.reviewer_directed() == [] over EVERY file in the instance dir (recursive: lean/, nagini/, ears/, velvet/, instance.json, patch.diff). Hand-grep for attacker/reviewer/panel/auditor/'the honest verdict'/'you should submit'/'record ... verdict' found hits only inside verdict.md's own historical role transcripts and meta.json's gate keys — i.e. the record of past audits, which is what those files are for. No file instructs me how to record or which verdict is honest. The one imperative anywhere in the spec view ('The proof agent may add `_prop` axioms only if genuinely stuck') addresses the proof agent about axiom hygiene, says nothing to a reviewer, and is not a statement about the gold edit.

### Why NO-LEAKAGE
The spec view states the target behavior in a wholly abstract vocabulary it invents (CoordArg / CoordVal / countsAsFinite / chooseRepresentative). It names no patched file, no patched symbol, no exception type, and no handler placement — nothing that says WHERE or HOW to edit. The discriminating clause is the one in `chooseRepresentative`: for a searched sequence, the first value that counts as finite, else — when nothing counts but the sequence is non-empty — the first value unconditionally.

That clause is derivable from the public problem_statement ALONE, so it clears the bar independently of any relaxation argument:
- The traceback in problem_statement bottoms out verbatim at `return next(val for val in obj if safe_isfinite(val))` raising `StopIteration` inside `_safe_first_finite`, called from `_convert_dx` at `x0 = cbook._safe_first_finite(x0)`. Mechanism, callee, and call site are all public.
- 'Expected outcome: On 3.6.0 this returns a BarCollection with one Rectangle, having nan for x and height' IS the discriminator restated in user terms: the all-nan single-element sequence must yield nan as the representative rather than crash.
- 'Further debugging: ax.bar([np.nan],[0]) # Raises / ax.bar([0],[np.nan]) # Works ... So it's about the x position specifically' narrows it to the x0/xconv coordinate route.
A solver with only problem_statement reaches 'when the finite search finds nothing, use the first element' unaided. The spec view therefore discloses nothing beyond it.

The other three modeled axes are orthogonal STRENGTHENING, not leakage, and I checked each is pre/post-identical: the `.single` lone-coordinate arm, the three-regime `countsAsFinite` (.numeric/.unweighable/.missing modeling the UNCHANGED `safe_isfinite` closure), and the `.unsearched` third shape. All three model callees the patch does not touch, so they cannot encode the delta; per meta.prepatch_variants and my own step 6, the discriminator remains the `sequence.none` fallback with all three present.

### GATES I LEAN ON (re-derived or freshness-checked against current bytes)
G-DIFF, G-GOLD, G-LEAK, G-HYGIENE, G-AX, G-CONF, G-MUT (10/10), G-PBT, G-INTEGRITY, G-VERIFY all pass with sources.Solution.lean == the current e6cc7967 hash. I re-derived G-DIFF and G-LEAK myself and re-ran verify + #print axioms rather than trusting the stamps.

OUT OF SCOPE, FLAGGED, NOT RELIED ON (re-audit items for other roles, not leakage findings)

(a) G-PANEL-2 (faithfulness) is recorded FAIL — an over-strength/domain-carve-out finding about the np.flatiter regime. That is the faithfulness role's business; an over-strong spec is the opposite failure mode from leakage and does not make the spec view disclose the edit. G-PANEL is a rollup, not a gate, so its fail echoes that sub-role.

(b) G-EQ / G-PANEL-1/2/3 stamps carry a STALE source hash (f08dc932b3178663 vs current e6cc7967386ad046) — those records predate the last prose revision, so they are undigested, not evidence for or against me. My verdict rests on my own step 1-7 measurements on the current bytes.

(c) meta.json['region_hashes'] does not reproduce under markers.region_hashes on the current bytes (e.g. spec_view 48dbf7d9... recorded vs dd39bfac... recomputed; 'pure' and 'proof' also differ, and I could not reproduce the recorded values under raw/strip/no-blank-line normalizations). This is a fleet-wide record-convention/staleness condition, not local tampering: sweeping all 470 lean bundles gives 340 MATCH / 130 MISMATCH / 30 no-meta. The authoritative in-bundle spec-identity check, markers.same_spec, passes (step 2), so this does not touch my verdict — recording it as a ledger-hygiene item.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
