# P2 adversarial audit — django__django-13516

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 16 admissible attacks re-run of 16 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 16 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 15 | `atk_1_prepatch.lean`, `atk_2_unconditional.lean`, `atk_3_inverted.lean`, `atk_4_double.lean`, `atk_5_frame.lean`, `atk_6_once_only.lean`, `atk_7_lostupdate.lean`, `atk_8b_pick_count.lean`, `atk_9b_diverge.lean`, `atk_11_parity.lean`, `atk_13_capped.lean`, `atk_14_set_to_one.lean`, `atk_8_vacuous_pick.lean`, +2 more |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_12b_equiv_correct.lean` |

**Non-vacuity.** The positive control `atk_0_positive.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. No same-spec wrong implementation verifies. The only same-spec NON-frozen implementation that verified (atk_12b_equiv_correct.lean, a behaviourally-equivalent getattr-lookup form) had its faithful refined patch materialized and RUN through the official harness: run_resolve('django__django-13516', patch_12b.diff) => resolved=True, completed=True, FAIL_TO_PASS 1/1 success, PASS_TO_PASS 43/43 success, 0 failures. So verify => resolve held on the one executed resolve, and no verify-but-not-resolve witness exists.
```

**Attacks re-run (16):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good)

```diff
@@ -46,10 +46,8 @@
   ensures sinkOld.flushable = false → sink.flushes = sinkOld.flushes
   do
     -- impl-start
-    if sink.flushable then
-      sink := { sink with flushes := sink.flushes + 1 }
-    else
-      return
+    -- PREPATCH: inherited TextIOBase.flush is a generic no-op that never
+    -- reaches self._out; __getattr__ is not consulted. Nothing is forwarded.
     return
     -- impl-end
 
```

Attack 2 — `atk_2_unconditional.lean` → rejected (same spec, does not verify — good)

```diff
@@ -46,10 +46,9 @@
   ensures sinkOld.flushable = false → sink.flushes = sinkOld.flushes
   do
     -- impl-start
-    if sink.flushable then
-      sink := { sink with flushes := sink.flushes + 1 }
-    else
-      return
+    -- WRONG: forwards the flush with NO hasattr guard (partial-domain bug):
+    -- `self._out.flush()` unconditionally. Increments even when not flushable.
+    sink := { sink with flushes := sink.flushes + 1 }
     return
     -- impl-end
 
```

Attack 3 — `atk_3_inverted.lean` → rejected (same spec, does not verify — good)

```diff
@@ -46,10 +46,12 @@
   ensures sinkOld.flushable = false → sink.flushes = sinkOld.flushes
   do
     -- impl-start
+    -- WRONG: guard inverted -- forwards only when the stream CANNOT flush
+    -- (`if not hasattr(self._out, 'flush'): self._out.flush()`).
     if sink.flushable then
+      return
+    else
       sink := { sink with flushes := sink.flushes + 1 }
-    else
-      return
     return
     -- impl-end
 
```

Attack 4 — `atk_4_double.lean` → rejected (same spec, does not verify — good)

```diff
@@ -46,8 +46,10 @@
   ensures sinkOld.flushable = false → sink.flushes = sinkOld.flushes
   do
     -- impl-start
+    -- WRONG: forwards the request TWICE (`self._out.flush(); self._out.flush()`)
+    -- -- boundary error on the exact-once observable.
     if sink.flushable then
-      sink := { sink with flushes := sink.flushes + 1 }
+      sink := { sink with flushes := sink.flushes + 2 }
     else
       return
     return
```

Attack 5 — `atk_5_frame.lean` → rejected (same spec, does not verify — good)

```diff
@@ -46,10 +46,12 @@
   ensures sinkOld.flushable = false → sink.flushes = sinkOld.flushes
   do
     -- impl-start
+    -- WRONG: forwards the flush but also CLOBBERS the read-only `flushable`
+    -- aspect (e.g. rebinding self._out to a flushable surrogate).
     if sink.flushable then
-      sink := { sink with flushes := sink.flushes + 1 }
+      sink := { flushable := true, flushes := sink.flushes + 1 }
     else
-      return
+      sink := { flushable := true, flushes := sink.flushes }
     return
     -- impl-end
 
```

Attack 6 — `atk_6_once_only.lean` → rejected (same spec, does not verify — good)

```diff
@@ -46,8 +46,14 @@
   ensures sinkOld.flushable = false → sink.flushes = sinkOld.flushes
   do
     -- impl-start
+    -- WRONG (partial domain): forwards the flush only the FIRST time -- a
+    -- "already flushed once, skip it" memoization bug. Correct on flushes = 0,
+    -- silently a no-op on every later request.
     if sink.flushable then
-      sink := { sink with flushes := sink.flushes + 1 }
+      if sink.flushes = 0 then
+        sink := { sink with flushes := sink.flushes + 1 }
+      else
+        return
     else
       return
     return
```

Attack 7 — `atk_7_lostupdate.lean` → rejected (same spec, does not verify — good)

```diff
@@ -46,8 +46,11 @@
   ensures sinkOld.flushable = false → sink.flushes = sinkOld.flushes
   do
     -- impl-start
-    if sink.flushable then
-      sink := { sink with flushes := sink.flushes + 1 }
+    -- WRONG (lost update): computes the forwarded flush on a LOCAL COPY and
+    -- never writes it back -- the outward effect never reaches the wrapper.
+    let mut tmp := sink
+    if tmp.flushable then
+      tmp := { tmp with flushes := tmp.flushes + 1 }
     else
       return
     return
```

Attack 8 — `atk_8b_pick_count.lean` → rejected (same spec, does not verify — good)

```diff
@@ -46,8 +46,12 @@
   ensures sinkOld.flushable = false → sink.flushes = sinkOld.flushes
   do
     -- impl-start
+    -- ATTACK (ungrounded oracle): let an unconstrained oracle choose HOW MANY
+    -- times to forward the flush. Satisfiable predicate, so the pick itself is
+    -- grounded; verifies only if demonic choice were angelic.
     if sink.flushable then
-      sink := { sink with flushes := sink.flushes + 1 }
+      let k :| (k : Nat) ≥ 1
+      sink := { sink with flushes := sink.flushes + k }
     else
       return
     return
```

Attack 9 — `atk_9b_diverge.lean` → rejected (same spec, does not verify — good)

```diff
@@ -46,10 +46,15 @@
   ensures sinkOld.flushable = false → sink.flushes = sinkOld.flushes
   do
     -- impl-start
-    if sink.flushable then
-      sink := { sink with flushes := sink.flushes + 1 }
-    else
-      return
+    -- ATTACK (divergence): spin forever with a constant measure, never
+    -- forwarding the flush. Under partial correctness a diverging program
+    -- satisfies any postcondition; total correctness must reject it.
+    let mut n := 0
+    while 0 < 1
+      invariant n = n
+      decreasing (0 : Nat)
+    do
+      n := n + 1
     return
     -- impl-end
 
```

Attack 10 — `atk_11_parity.lean` → rejected (same spec, does not verify — good)

```diff
@@ -46,8 +46,13 @@
   ensures sinkOld.flushable = false → sink.flushes = sinkOld.flushes
   do
     -- impl-start
+    -- WRONG (partial domain): forwards the flush only when the observed count
+    -- so far is EVEN -- correct on half the domain, silently a no-op elsewhere.
     if sink.flushable then
-      sink := { sink with flushes := sink.flushes + 1 }
+      if sink.flushes % 2 = 0 then
+        sink := { sink with flushes := sink.flushes + 1 }
+      else
+        return
     else
       return
     return
```

Attack 11 — `atk_13_capped.lean` → rejected (same spec, does not verify — good)

```diff
@@ -46,8 +46,13 @@
   ensures sinkOld.flushable = false → sink.flushes = sinkOld.flushes
   do
     -- impl-start
+    -- WRONG (boundary): forwards the flush only while the observed count is
+    -- below a cap (a "throttle the flushes" bug). Correct for small counts.
     if sink.flushable then
-      sink := { sink with flushes := sink.flushes + 1 }
+      if sink.flushes < 3 then
+        sink := { sink with flushes := sink.flushes + 1 }
+      else
+        return
     else
       return
     return
```

Attack 12 — `atk_14_set_to_one.lean` → rejected (same spec, does not verify — good)

```diff
@@ -46,8 +46,12 @@
   ensures sinkOld.flushable = false → sink.flushes = sinkOld.flushes
   do
     -- impl-start
+    -- WRONG (ungrounded-oracle echo of the F2P observable): SETS the forwarded
+    -- count to 1 instead of incrementing it. Satisfies `flushes >= 1` -- which
+    -- is all the F2P test observes (`mocked_flush.called is True`) -- but is
+    -- not "forwarded exactly once per request".
     if sink.flushable then
-      sink := { sink with flushes := sink.flushes + 1 }
+      sink := { sink with flushes := 1 }
     else
       return
     return
```

Attack 13 — `atk_12b_equiv_correct.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -46,10 +46,14 @@
   ensures sinkOld.flushable = false → sink.flushes = sinkOld.flushes
   do
     -- impl-start
+    -- EQUIVALENT CORRECT impl, written differently (explicit records on both
+    -- branches, no `with`). Refines to the getattr-lookup form of the fix:
+    --   f = getattr(self._out, 'flush', None)
+    --   if f is not None: f()
     if sink.flushable then
-      sink := { sink with flushes := sink.flushes + 1 }
+      sink := { flushable := sink.flushable, flushes := sink.flushes + 1 }
     else
-      return
+      sink := { flushable := sink.flushable, flushes := sink.flushes }
     return
     -- impl-end
 
```

Attack 14 — `atk_8_vacuous_pick.lean` → rejected (same spec, does not verify — good)

```diff
@@ -46,8 +46,13 @@
   ensures sinkOld.flushable = false → sink.flushes = sinkOld.flushes
   do
     -- impl-start
-    if sink.flushable then
-      sink := { sink with flushes := sink.flushes + 1 }
+    -- ATTACK (ungrounded oracle): try to make the obligation VACUOUS by
+    -- picking a witness from an empty set, then do NOT forward the flush.
+    -- Verifies only if demonic choice is an assumption rather than an
+    -- obligation.
+    let k :| (k : Nat) < 0
+    if k = 0 then
+      return
     else
       return
     return
```

Attack 15 — `atk_9_diverge.lean` → rejected (same spec, does not verify — good)

```diff
@@ -46,10 +46,15 @@
   ensures sinkOld.flushable = false → sink.flushes = sinkOld.flushes
   do
     -- impl-start
-    if sink.flushable then
-      sink := { sink with flushes := sink.flushes + 1 }
-    else
-      return
+    -- ATTACK (divergence): spin forever, then do NOT forward the flush. Under
+    -- partial correctness a diverging program vacuously satisfies every
+    -- postcondition; total correctness must reject it.
+    let mut n := 0
+    while n < 1
+      invariant n = 0
+      decreasing 1 - n
+    do
+      n := n + 0
     return
     -- impl-end
 
```

Attack 16 — `atk_10_assert_false.lean` → rejected (same spec, does not verify — good)

```diff
@@ -46,10 +46,10 @@
   ensures sinkOld.flushable = false → sink.flushes = sinkOld.flushes
   do
     -- impl-start
-    if sink.flushable then
-      sink := { sink with flushes := sink.flushes + 1 }
-    else
-      return
+    -- ATTACK (ungrounded oracle): assume-shaped `assert False` in front of the
+    -- prepatch body. Verifies only if `assert` is an ASSUMPTION rather than a
+    -- proof obligation.
+    assert False
     return
     -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_0_positive.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- No axiomatized callees: the modeled operation is spelled out directly over
-- the observable state (see `pure` region). There is no unchanged callee whose
-- internal behavior the proof must assume.
-- axioms-end

-- pure-start
/- The observable state of a thin output stream wrapper, restricted to the two
   aspects a flush request can touch:

   * `flushable` — whether the underlying stream the wrapper forwards to is one
     that supports flushing (it exposes a flush operation of its own);
   * `flushes`   — how many times a flush has actually been driven through to
     that underlying stream (the outward observable effect of forwarding).

   Other wrapper state (text content already written, the line ending, styling)
   is untouched by a flush request and is therefore not part of this carrier
   (mapping.md §2). -/
structure OutputSink where
  flushable : Bool
  flushes : Nat
  deriving Inhabited
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- A flush request on the wrapper. The required behavior: when the underlying
   stream supports flushing, the request must be carried through to it exactly
   once; when it does not, the request is a no-op. The `flushable` aspect is a
   read-only property of the wrapper and is never altered by a flush. -/
method propagateFlush (mut sink : OutputSink) return (u : Unit)
  ensures sink.flushable = sinkOld.flushable
  ensures sinkOld.flushable = true  → sink.flushes = sinkOld.flushes + 1
  ensures sinkOld.flushable = false → sink.flushes = sinkOld.flushes
  do
    -- impl-start
    if sink.flushable then
      sink := { sink with flushes := sink.flushes + 1 }
    else
      return
    return
    -- impl-end

prove_correct propagateFlush by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial audit, django__django-13516 (velvet). All 17 files confirmed same_spec=True AND unsound_evasions=[] (no new axiom/sorry/admit/native_decide, prove_correct propagateFlush retained) via swebench_unified.markers.same_spec + variant_scope.unsound_evasions against the frozen Solution.lean. Attack files differ from frozen ONLY inside the impl region.

WHY THIS SPEC IS HARD TO BREAK (structural analysis): the three postconditions pin BOTH carrier fields as total functions of the old state -- `sink.flushable = sinkOld.flushable` (frame, read-only aspect), `flushable=true -> flushes = flushesOld+1` (exact-once forward), `flushable=false -> flushes = flushesOld` (no-op). Over the 2-field carrier OutputSink{flushable:Bool, flushes:Nat} that is a COMPLETE functional characterization: the post-state is uniquely determined on the entire domain, and the precondition is empty (no partial domain to hide in). So a behaviourally-divergent verifying impl is impossible unless the verifier admits an ESCAPE (vacuity / divergence / unearned assumption). I therefore attacked the escapes directly rather than only mutating the arithmetic.

ESCAPE ANALYSIS (the real threat, read from the Loom sources under lean_shared/.lake/packages): under `set_option loom.semantics.termination "total"` + `choice "demonic"` the file opens TotalCorrectness.DemonicChoice, where NonDetT/Basic.lean gives wp_assume = (as) INF post and wp_pickSuchThat = (EXISTS h, p h) INF (INF a, p a -> post a) -- CONJUNCTIVE, i.e. a nondeterministic choice is an OBLIGATION (must prove the witness set nonempty AND the post for EVERY witness), not an assumption. WPGen.assert (WP/Gen.lean:262) is likewise h INF (h -> post), so `assert False` cannot discharge anything. And `decreasing` is mandatory under total semantics (CaseStudies/Macro.lean throws "Decreasing annotations are required in total correctness semantics"). All three escape doors are closed, which the attacks below confirm empirically.

COMMANDS. Same-spec: python -c "from swebench_unified.markers import same_spec; from swebench_unified.backends import get_backend; b=get_backend('velvet'); print(same_spec(open('<frozen>').read(), open('<atk>').read(), b.language))" -> True for all. Verify: bash scripts/lean_verify.sh <file>.lean (run as concurrent background batches of <=4).

### RESULTS (exit 0 = verifies, 1 = rejected):
- atk_0_positive.lean (frozen gold impl) -> EXIT 0 VERIFIES. Positive control good; the harness is live, so the rejections below are real.
- atk_1_prepatch.lean -> EXIT 1. PREPATCH BUG REPRODUCED. Bare `return`: inherited TextIOBase.flush is a generic no-op that never reaches self._out (__getattr__ not consulted, attribute resolves on the base class). Unsolved goal exactly `sinkOld.flushable = true -> sinkOld.flushes = sinkOld.flushes + 1`.
- atk_2_unconditional.lean -> EXIT 1. Drops the hasattr guard (partial-domain). Goal: `flushable=false -> flushesOld+1 = flushesOld`.
- atk_3_inverted.lean -> EXIT 1. Guard inverted (control-flow-effect); BOTH ensures_1 and ensures_2 unsolved.
- atk_4_double.lean -> EXIT 1. Forwards twice (boundary). Goal: `flushesOld+2 = flushesOld+1`.
- atk_5_frame.lean -> EXIT 1. FRAME violation: clobbers read-only `flushable`. Goal: `true = sinkOld.flushable`. Confirms the mut-frame clause has teeth.
- atk_6_once_only.lean -> EXIT 1. Memoized "already flushed once, skip" (partial domain); rejected on the flushes!=0 branch.
- atk_7_lostupdate.lean -> EXIT 1. Lost update: mutates a local copy, never writes back, so the outward effect never lands.
- atk_11_parity.lean -> EXIT 1. Forwards only when count is even -- correct on HALF the domain, still rejected.
- atk_13_capped.lean -> EXIT 1. Throttle/cap bug: forwards only while flushes<3; rejected on the >=3 branch.
- atk_14_set_to_one.lean -> EXIT 1. SHARPEST attack (ungrounded-oracle echo of the F2P observable): SETS flushes:=1 instead of incrementing. This satisfies `flushes >= 1`, which is ALL the F2P test observes (`mocked_flush.called is True`), yet the spec rejects it -- goal `1 = sinkOld.flushes + 1`. Proves the spec is STRICTLY STRONGER than the hidden test's observable, i.e. it did not merely transcribe the oracle.
- atk_8b_pick_count.lean -> EXIT 1. Ungrounded oracle via demonic `let k :| k >= 1` choosing the forward count. Rejected with TWO goals: `EXISTS h, h >= 1` (witness-nonemptiness) and `flushesOld + i = flushesOld + 1` for the universally-quantified witness. Empirically confirms demonic choice is conjunctive -- an oracle cannot pick a convenient count.
- atk_9b_diverge.lean -> EXIT 1. Divergence escape: `while 0 < 1` with constant measure, never forwarding. Rejected on the decrease obligation `0 < 0`. Confirms "total" semantics rejects nontermination, so a diverging program cannot vacuously satisfy the post.
- atk_8_vacuous_pick.lean / atk_9_diverge.lean / atk_10_assert_false.lean -> EXIT 1, but on ELABORATION/tactic errors ("do element is unreachable", HSub synthesis failure, "Failed to parse an assertion without names: False"), NOT on spec strength. I am reporting these transparently as WEAK evidence and they are NOT counted toward the >=5; that is exactly why I re-encoded them as the repaired atk_8b / atk_9b above, which fail on genuine unsolved postcondition/measure goals. atk_12_equiv_correct.lean likewise died on a Velvet `match`-in-impl tooling limit and was re-encoded as atk_12b.

MANDATORY RESOLVE RUN (protocol step 2). Exactly one same-spec non-frozen impl VERIFIED: atk_12b_equiv_correct.lean (EXIT 0) -- explicit records on both branches, refining to the getattr-lookup form of the fix. Per protocol I materialized its faithful refined patch (patch_12b.diff; `git apply --check` at base_commit b7da588e -> PATCH_12B_APPLIES_CLEAN) and RAN it through the official harness: python -c "from swebench_unified.harness import run_resolve; run_resolve('django__django-13516', patch_12b, timeout=1800, retries=1)". OBSERVED RESULT: resolved=True, completed=True, note='resolved', attempts=1, FAIL_TO_PASS success=['test_outputwrapper_flush (user_commands.tests.CommandTests)'] failure=[], PASS_TO_PASS success=43 failure=0, PASS_TO_FAIL=0, FAIL_TO_FAIL=0. Saved: resolve_12b.json / resolve_12b.log. So the one verifying rival RESOLVES -- no verify-but-not-resolve witness. No non-resolving verifying patch exists to report, hence not BROKEN.

REFINEMENT.MD AUDIT (protocol step 3). Legs A1 (R: OutputWrapper restricted to flush-relevant state <-> OutputSink), A2 (R+I: boolean guard <-> hasattr(self._out,'flush')), A3 (I: guarded flushes increment <-> self._out.flush()), A4 (R+I: no-op fallthrough <-> implicit None return). Every leg is R or I; NO kind-3 leg, and no leg is left unclassified. The claim of ZERO A-legs is CORRECT and verified against the artifacts, not just the prose: Solution.lean's axioms region contains only comments (grep for axiom/sorry/admit/native_decide finds nothing but the region markers), meta.json declares axioms=[] and deep_model_references=[], and there is no axiom_check.py.

G-AX=skip is therefore correct rather than an evasion -- G-AX validates contracts on UNCHANGED callees at base_commit, and the only callee the gold body invokes (the underlying stream's own flush()) is precisely the operation whose FORWARDING is the fix. Directive 7 forbids axiomatizing the changed op, so modeling it directly as an I op is the right boundary; refinement.md §C explicitly documents that a prior attempt's axiom_check.py failed because it drove the CHANGED callee at base_commit (getting zero forwarded flushes), which was a mislabeling symptom, not a soundness defect. Since there are no A-legs, the usual G-EQ focus (axiom/deep-model legs, where no mechanical refuter reaches) has no attack surface here, and the whole refinement reduces to R/I legs that G-CONF mechanically refutes.

MODEL<->PATCH CORRESPONDENCE. mapping.md's bijection checks out against the real repo at base_commit: OutputWrapper is at django/core/management/base.py:120 subclassing TextIOBase, __getattr__ at :140 forwards unknown attributes to self._out, and the gold patch inserts `flush()` between __getattr__ and isatty() -- matching the quoted hunk verbatim (patch.diff is the gold patch byte-for-byte). The carrier's omission of _out content / ending / style_func is justified: none is touched by a flush. conformance_check.py's shadow (`if flushable: flushes += 1`) is a faithful transliteration of the impl region and its oracle drives the REAL patched OutputWrapper.flush over both flushable (StringIO) and non-flushable (_NoFlushStream) configurations, asserting the non-flushable path never raises; seed 13516 matches mapping.md §4 and meta.json conf_seed.

VERDICT: SOUND. 12 distinct spec-strength attacks (prepatch bug + partial-domain + boundary + control-flow-effect + frame + lost-update + ungrounded-oracle echo + demonic-choice vacuity + divergence) all REJECTED with genuine unsolved postcondition/measure goals; positive control VERIFIES; the sole verifying same-spec rival's faithful patch was EXECUTED through run_resolve and RESOLVED (1/1 F2P, 43/43 P2P). Caveat recorded for the runner: 3 of the 16 submitted files (atk_8, atk_9, atk_10) are superseded elaboration-error attempts retained for transparency and should not be credited as spec-strength refutations; the >=5 threshold is met without them (12 clean rejections).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 16 admissible attacks re-run of 16 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 16 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 15 | `atk_1_prepatch.lean`, `atk_2_unconditional.lean`, `atk_3_inverted.lean`, `atk_4_double.lean`, `atk_5_frame.lean`, `atk_6_once_only.lean`, `atk_7_lostupdate.lean`, `atk_8b_pick_count.lean`, `atk_9b_diverge.lean`, `atk_11_parity.lean`, `atk_13_capped.lean`, `atk_14_set_to_one.lean`, `atk_8_vacuous_pick.lean`, +2 more |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_12b_equiv_correct.lean` |

**Non-vacuity.** The positive control `atk_0_positive.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. No same-spec wrong implementation verifies. The only same-spec NON-frozen implementation that verified (atk_12b_equiv_correct.lean, a behaviourally-equivalent getattr-lookup form) had its faithful refined patch materialized and RUN through the official harness: run_resolve('django__django-13516', patch_12b.diff) => resolved=True, completed=True, FAIL_TO_PASS 1/1 success, PASS_TO_PASS 43/43 success, 0 failures. So verify => resolve held on the one executed resolve, and no verify-but-not-resolve witness exists.
```

**Attacks re-run (16):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 16 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_unconditional.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3_inverted.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4_double.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5_frame.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6_once_only.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7_lostupdate.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8b_pick_count.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9b_diverge.lean` → rejected (same spec, does not verify — good)

Attack 10 — `atk_11_parity.lean` → rejected (same spec, does not verify — good)

Attack 11 — `atk_13_capped.lean` → rejected (same spec, does not verify — good)

Attack 12 — `atk_14_set_to_one.lean` → rejected (same spec, does not verify — good)

Attack 13 — `atk_12b_equiv_correct.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 14 — `atk_8_vacuous_pick.lean` → rejected (same spec, does not verify — good)

Attack 15 — `atk_9_diverge.lean` → rejected (same spec, does not verify — good)

Attack 16 — `atk_10_assert_false.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_0_positive.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- No axiomatized callees: the modeled operation is spelled out directly over
-- the observable state (see `pure` region). There is no unchanged callee whose
-- internal behavior the proof must assume.
-- axioms-end

-- pure-start
/- The observable state of a thin output stream wrapper, restricted to the two
   aspects a flush request can touch:

   * `flushable` — whether the underlying stream the wrapper forwards to is one
     that supports flushing (it exposes a flush operation of its own);
   * `flushes`   — how many times a flush has actually been driven through to
     that underlying stream (the outward observable effect of forwarding).

   Other wrapper state (text content already written, the line ending, styling)
   is untouched by a flush request and is therefore not part of this carrier
   (mapping.md §2). -/
structure OutputSink where
  flushable : Bool
  flushes : Nat
  deriving Inhabited
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- A flush request on the wrapper. The required behavior: when the underlying
   stream supports flushing, the request must be carried through to it exactly
   once; when it does not, the request is a no-op. The `flushable` aspect is a
   read-only property of the wrapper and is never altered by a flush. -/
method propagateFlush (mut sink : OutputSink) return (u : Unit)
  ensures sink.flushable = sinkOld.flushable
  ensures sinkOld.flushable = true  → sink.flushes = sinkOld.flushes + 1
  ensures sinkOld.flushable = false → sink.flushes = sinkOld.flushes
  do
    -- impl-start
    if sink.flushable then
      sink := { sink with flushes := sink.flushes + 1 }
    else
      return
    return
    -- impl-end

prove_correct propagateFlush by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial audit, django__django-13516 (velvet). All 17 files confirmed same_spec=True AND unsound_evasions=[] (no new axiom/sorry/admit/native_decide, prove_correct propagateFlush retained) via swebench_unified.markers.same_spec + variant_scope.unsound_evasions against the frozen Solution.lean. Attack files differ from frozen ONLY inside the impl region.

WHY THIS SPEC IS HARD TO BREAK (structural analysis): the three postconditions pin BOTH carrier fields as total functions of the old state -- `sink.flushable = sinkOld.flushable` (frame, read-only aspect), `flushable=true -> flushes = flushesOld+1` (exact-once forward), `flushable=false -> flushes = flushesOld` (no-op). Over the 2-field carrier OutputSink{flushable:Bool, flushes:Nat} that is a COMPLETE functional characterization: the post-state is uniquely determined on the entire domain, and the precondition is empty (no partial domain to hide in). So a behaviourally-divergent verifying impl is impossible unless the verifier admits an ESCAPE (vacuity / divergence / unearned assumption). I therefore attacked the escapes directly rather than only mutating the arithmetic.

ESCAPE ANALYSIS (the real threat, read from the Loom sources under lean_shared/.lake/packages): under `set_option loom.semantics.termination "total"` + `choice "demonic"` the file opens TotalCorrectness.DemonicChoice, where NonDetT/Basic.lean gives wp_assume = (as) INF post and wp_pickSuchThat = (EXISTS h, p h) INF (INF a, p a -> post a) -- CONJUNCTIVE, i.e. a nondeterministic choice is an OBLIGATION (must prove the witness set nonempty AND the post for EVERY witness), not an assumption. WPGen.assert (WP/Gen.lean:262) is likewise h INF (h -> post), so `assert False` cannot discharge anything. And `decreasing` is mandatory under total semantics (CaseStudies/Macro.lean throws "Decreasing annotations are required in total correctness semantics"). All three escape doors are closed, which the attacks below confirm empirically.

COMMANDS. Same-spec: python -c "from swebench_unified.markers import same_spec; from swebench_unified.backends import get_backend; b=get_backend('velvet'); print(same_spec(open('<frozen>').read(), open('<atk>').read(), b.language))" -> True for all. Verify: bash scripts/lean_verify.sh <file>.lean (run as concurrent background batches of <=4).

### RESULTS (exit 0 = verifies, 1 = rejected):
- atk_0_positive.lean (frozen gold impl) -> EXIT 0 VERIFIES. Positive control good; the harness is live, so the rejections below are real.
- atk_1_prepatch.lean -> EXIT 1. PREPATCH BUG REPRODUCED. Bare `return`: inherited TextIOBase.flush is a generic no-op that never reaches self._out (__getattr__ not consulted, attribute resolves on the base class). Unsolved goal exactly `sinkOld.flushable = true -> sinkOld.flushes = sinkOld.flushes + 1`.
- atk_2_unconditional.lean -> EXIT 1. Drops the hasattr guard (partial-domain). Goal: `flushable=false -> flushesOld+1 = flushesOld`.
- atk_3_inverted.lean -> EXIT 1. Guard inverted (control-flow-effect); BOTH ensures_1 and ensures_2 unsolved.
- atk_4_double.lean -> EXIT 1. Forwards twice (boundary). Goal: `flushesOld+2 = flushesOld+1`.
- atk_5_frame.lean -> EXIT 1. FRAME violation: clobbers read-only `flushable`. Goal: `true = sinkOld.flushable`. Confirms the mut-frame clause has teeth.
- atk_6_once_only.lean -> EXIT 1. Memoized "already flushed once, skip" (partial domain); rejected on the flushes!=0 branch.
- atk_7_lostupdate.lean -> EXIT 1. Lost update: mutates a local copy, never writes back, so the outward effect never lands.
- atk_11_parity.lean -> EXIT 1. Forwards only when count is even -- correct on HALF the domain, still rejected.
- atk_13_capped.lean -> EXIT 1. Throttle/cap bug: forwards only while flushes<3; rejected on the >=3 branch.
- atk_14_set_to_one.lean -> EXIT 1. SHARPEST attack (ungrounded-oracle echo of the F2P observable): SETS flushes:=1 instead of incrementing. This satisfies `flushes >= 1`, which is ALL the F2P test observes (`mocked_flush.called is True`), yet the spec rejects it -- goal `1 = sinkOld.flushes + 1`. Proves the spec is STRICTLY STRONGER than the hidden test's observable, i.e. it did not merely transcribe the oracle.
- atk_8b_pick_count.lean -> EXIT 1. Ungrounded oracle via demonic `let k :| k >= 1` choosing the forward count. Rejected with TWO goals: `EXISTS h, h >= 1` (witness-nonemptiness) and `flushesOld + i = flushesOld + 1` for the universally-quantified witness. Empirically confirms demonic choice is conjunctive -- an oracle cannot pick a convenient count.
- atk_9b_diverge.lean -> EXIT 1. Divergence escape: `while 0 < 1` with constant measure, never forwarding. Rejected on the decrease obligation `0 < 0`. Confirms "total" semantics rejects nontermination, so a diverging program cannot vacuously satisfy the post.
- atk_8_vacuous_pick.lean / atk_9_diverge.lean / atk_10_assert_false.lean -> EXIT 1, but on ELABORATION/tactic errors ("do element is unreachable", HSub synthesis failure, "Failed to parse an assertion without names: False"), NOT on spec strength. I am reporting these transparently as WEAK evidence and they are NOT counted toward the >=5; that is exactly why I re-encoded them as the repaired atk_8b / atk_9b above, which fail on genuine unsolved postcondition/measure goals. atk_12_equiv_correct.lean likewise died on a Velvet `match`-in-impl tooling limit and was re-encoded as atk_12b.

MANDATORY RESOLVE RUN (protocol step 2). Exactly one same-spec non-frozen impl VERIFIED: atk_12b_equiv_correct.lean (EXIT 0) -- explicit records on both branches, refining to the getattr-lookup form of the fix. Per protocol I materialized its faithful refined patch (patch_12b.diff; `git apply --check` at base_commit b7da588e -> PATCH_12B_APPLIES_CLEAN) and RAN it through the official harness: python -c "from swebench_unified.harness import run_resolve; run_resolve('django__django-13516', patch_12b, timeout=1800, retries=1)". OBSERVED RESULT: resolved=True, completed=True, note='resolved', attempts=1, FAIL_TO_PASS success=['test_outputwrapper_flush (user_commands.tests.CommandTests)'] failure=[], PASS_TO_PASS success=43 failure=0, PASS_TO_FAIL=0, FAIL_TO_FAIL=0. Saved: resolve_12b.json / resolve_12b.log. So the one verifying rival RESOLVES -- no verify-but-not-resolve witness. No non-resolving verifying patch exists to report, hence not BROKEN.

REFINEMENT.MD AUDIT (protocol step 3). Legs A1 (R: OutputWrapper restricted to flush-relevant state <-> OutputSink), A2 (R+I: boolean guard <-> hasattr(self._out,'flush')), A3 (I: guarded flushes increment <-> self._out.flush()), A4 (R+I: no-op fallthrough <-> implicit None return). Every leg is R or I; NO kind-3 leg, and no leg is left unclassified. The claim of ZERO A-legs is CORRECT and verified against the artifacts, not just the prose: Solution.lean's axioms region contains only comments (grep for axiom/sorry/admit/native_decide finds nothing but the region markers), meta.json declares axioms=[] and deep_model_references=[], and there is no axiom_check.py.

G-AX=skip is therefore correct rather than an evasion -- G-AX validates contracts on UNCHANGED callees at base_commit, and the only callee the gold body invokes (the underlying stream's own flush()) is precisely the operation whose FORWARDING is the fix. Directive 7 forbids axiomatizing the changed op, so modeling it directly as an I op is the right boundary; refinement.md §C explicitly documents that a prior attempt's axiom_check.py failed because it drove the CHANGED callee at base_commit (getting zero forwarded flushes), which was a mislabeling symptom, not a soundness defect. Since there are no A-legs, the usual G-EQ focus (axiom/deep-model legs, where no mechanical refuter reaches) has no attack surface here, and the whole refinement reduces to R/I legs that G-CONF mechanically refutes.

MODEL<->PATCH CORRESPONDENCE. mapping.md's bijection checks out against the real repo at base_commit: OutputWrapper is at django/core/management/base.py:120 subclassing TextIOBase, __getattr__ at :140 forwards unknown attributes to self._out, and the gold patch inserts `flush()` between __getattr__ and isatty() -- matching the quoted hunk verbatim (patch.diff is the gold patch byte-for-byte). The carrier's omission of _out content / ending / style_func is justified: none is touched by a flush. conformance_check.py's shadow (`if flushable: flushes += 1`) is a faithful transliteration of the impl region and its oracle drives the REAL patched OutputWrapper.flush over both flushable (StringIO) and non-flushable (_NoFlushStream) configurations, asserting the non-flushable path never raises; seed 13516 matches mapping.md §4 and meta.json conf_seed.

VERDICT: SOUND. 12 distinct spec-strength attacks (prepatch bug + partial-domain + boundary + control-flow-effect + frame + lost-update + ungrounded-oracle echo + demonic-choice vacuity + divergence) all REJECTED with genuine unsolved postcondition/measure goals; positive control VERIFIES; the sole verifying same-spec rival's faithful patch was EXECUTED through run_resolve and RESOLVED (1/1 F2P, 43/43 P2P). Caveat recorded for the runner: 3 of the 16 submitted files (atk_8, atk_9, atk_10) are superseded elaboration-error attempts retained for transparency and should not be credited as spec-strength refutations; the >=5 threshold is met without them (12 clean rejections).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** FAITHFULNESS-BREAK ATTACK on django__django-13516 / velvet `propagateFlush`. Verdict FAITHFUL: no in-vocabulary input found where the modeled function disagrees with the real patched callee. I could not produce a required diverging_input, so I do not claim a defect.

SETUP (reference discipline observed). Fresh worktree at base_commit b7da588e88 with patch.diff APPLIED as the reference for the modeled function (`OutputWrapper.flush`, django/core/management/base.py:143-145). Base commit used only for the prepatch narrative claim. Confirmed the patched body is exactly `if hasattr(self._out,'flush'): self._out.flush()`.

ADMISSIBILITY / CONTROLS.
- Frozen Solution.lean verifies: lean_verify.sh exit 0.
- Spec region byte-identical: markers.same_spec(Solution, Solution_prepatch, velvet) = True; printed spec_signature to confirm the three `ensures` + carrier are what I reasoned about.
- Negative control discriminates: Solution_prepatch.lean exit 1, `unsolved goals` at the `flushes + 1` clause. Positive control: prepatch bug reproduced on the REAL base-commit callee (1 flush request -> 0 forwarded flushes, because OutputWrapper inherits TextIOBase.flush and __getattr__ is bypassed). F2P test_outputwrapper_flush PASSES on the patched worktree.
- G-CONF reproduced INDEPENDENTLY in my own worktree: exit 0, 100007 inputs, 0 disagreements.

MAIN ATTACK — differential fuzz, real patched callee vs the three ensures, over the carrier vocabulary (flushable, n_requests) -> forwarded count. 6000 randomized inputs x 6 stream kinds (Rec, __slots__ stream, StringIO, TextIOWrapper(BytesIO), no-flush object, no-flush with strict __getattr__), nreq 0..6, instrumented by DELEGATION (a probe wrapper) rather than attribute mutation. Result: 0 divergences. Exactly-once confirmed monotonically: requests 1..5 -> forwarded 1..5, matching `flushes = flushesOld + 1` per request. Non-flushable arm: 0 forwarded, never raises.

SELF-CORRECTION (reported because it nearly became a false UNFAITHFUL). My FIRST fuzz harness reported 519/4000 'divergences'. Those were entirely MY OWN BUG: I mutated `out.flush` in a loop with a leaked closure over `orig`, so counters accumulated across iterations and __slots__ streams silently failed instrumentation. The tell was arithmetically impossible output — nreq=0 yielding fwd=1, i.e. the real callee forwarding a flush that was never requested. Rewritten with per-call isolation, the divergence count went to 0. I did not submit that artifact as a finding.

### Candidate divergences investigated and rejected
1. Exception propagation (strongest candidate). On a flushable stream whose underlying flush raises, the real callee propagates the exception, while the spec is `termination "total"` with an unconditional normal return. Realistic trigger, not contrived: `manage.py migrate | head` (BrokenPipeError) and a closed file — I reproduced both. REJECTED as a faithfulness defect because it is NOT a disagreement on the MODELED observable: I measured `flushes` in exactly the raising cases and the forward still HAPPENED before the throw, so flushes = flushesOld + 1 holds (old=0 new=1) on healthy, closed-file, and broken-pipe alike. The carrier {flushable:Bool, flushes:Nat} has no vocabulary for an exception outcome, so this is a modeling-scope boundary declared in mapping.md 2, not a value-level divergence. It is also identical pre- and post-patch (an uncaught underlying flush error is out of scope of the fix) and unobservable to the F2P test, which asserts only mocked_flush.called.
2. Frame clause `sink.flushable = sinkOld.flushable`. I built a pathological stream whose flush() deletes its own flush attribute, breaking the frame (before=True after=False). REJECTED: an artificial self-mutating fixture, not any stream Django wraps. Checked every realistic target — StringIO, TextIOWrapper, sys.__stdout__, sys.__stderr__, /dev/null, nested OutputWrapper — flushability stable in all six. The patched body writes no attribute at all, so it cannot itself change the guard.
3. hasattr guard corner cases. flush=None / flush=5 -> guard true then TypeError; a flush property raising non-AttributeError -> hasattr itself raises. Same class as (1): exception-domain only, no int-valued disagreement, and unreachable for real streams.

SPEC-TOO-STRONG CHECK (the faithfulness lane's other half). Three same-spec E-lane rivals (same_spec=True each) built to see whether the spec over-fits the frozen term shape: dependent-if `if h : sink.flushable = true`, delta form `let d := if flushable then 1 else 0; flushes + d`, and `cond flushable (flushes+1) flushes`. The delta and cond reshapes both VERIFY (exit 0) — the spec admits genuinely different correct phrasings and is not over-fit to `+ 1`. The dependent-if fails only on a WPGen parse limit (`Failed to parse an assertion without names`), a backend expressiveness issue, not spec strength; I do not count it as a finding (consistent with the port's own E1/E5 dispositions).

CONCLUSION. The three ensures agree with the real patched callee on every input expressible in the carrier; the only divergences I could construct live strictly outside the modeled vocabulary (exception outcomes) or require self-mutating fixtures no Django stream exhibits. Spec is not too strong and does not drift from repo behavior. FAITHFUL, no diverging input.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** MECHANICAL CHECKS (all run, all clean):
- markers.same_spec(Solution.lean, Solution_prepatch.lean) = True; spec_signature identical -> spec region byte-identical as required.
- scripts/lean_verify.sh Solution.lean -> EXIT=0 (spec+impl genuinely verifies; not a vacuous pass).
- leakage.screen() on BOTH Solution.lean and Solution_prepatch.lean: passed=True, zero hard failures, zero warnings.
- No diff markers ('@@', 'diff --git', '+++ ', 'index ') in the spec view.
- No gold changed line reproduced. Gold changed lines are ['def flush(self):', "if hasattr(self._out, 'flush'):", 'self._out.flush()']; none appear normalized in the view.
- Patched file path / dotted module path absent from the view.
- Explicit absence check for repo+test symbols in the spec view, all False: OutputWrapper, _out, hasattr, TextIOBase, __getattr__, io., StringIO, mock, mocked_flush, test_outputwrapper, user_commands, call_command, stdout, stderr, isatty, style_func, django, base.py.
- Narration vocabulary screen clean (no bug/fix/patched/broken/previously/incorrectly/wrong...).

WHY THE ONE PATCHED SYMBOL IS NOT A LEAK: _patch_changed_symbols(gold) = {'flush'} only. 'flush' is PUBLIC via the problem_statement's first line ("flush() on self.stdout/stderr management commands doesn't work"), so the spec-view identifiers propagateFlush / flushable / flushes, which all embed 'flush', are screened-legitimate. Judged against problem_statement ONLY; hints_text is empty here anyway, so there was no hints-only term available to echo.

DIAGNOSIS IS CORRECTLY ELIDED (the decisive point): the bug->fix MECHANISM narration exists in the bundle but only inside non-shipped locations. Solution_prepatch.lean's impl region contains the real diagnosis ("the flush request resolves to the generic base-class handler, which never reaches the underlying stream ... prove_correct MUST fail"), and I confirmed it is elided from the prepatch spec view (checked 'Pre-image', 'base-class', 'generic', 'skeleton', 'MUST fail', 'never reaches' -> all False). mapping.md/refinement.md DO name base.py, hasattr(self._out,'flush'), TextIOBase and mocked_flush, but these are audit-only artifacts: I grepped eval/prompts.py and eval/dataset.py and neither ships mapping.md, refinement.md, patch.diff, conformance_check.py, properties.py, or the prepatch file to a consumer. Only markers.spec_view(Solution.lean) reaches the solver, guarded by adapter.spec_view()'s refuse-to-expose assertions. mapping.md even self-labels the diagnosis "refinement audit only, not in the consumer spec view".

BORDERLINE ITEM CONSIDERED AND REJECTED AS A LEAK: the pure-region docstring says other wrapper state ("text content already written, the line ending, styling") is untouched by a flush. These are English paraphrases of the real attributes ending / style_func / _out, and those words are not in the problem_statement. I judged this NOT leakage because (a) they are UNCHANGED attributes, not patched symbols, so they localize no edit; (b) they are paraphrased, not the identifiers; (c) it is legitimate frame prose stating what the fix must NOT touch -- disclosure that the fix does not do something cannot reconstruct the gold hunk. Non-reconstructive, so not chargeable.

SECOND BORDERLINE ITEM, OUT OF LANE: the flushable guard itself is behavior not present in the problem_statement. I judged this NOT leakage because it is the abstract required BEHAVIOR (must forward exactly once when supported, must not raise otherwise), expressed over an abstract carrier OutputSink{flushable:Bool, flushes:Nat} rather than as the edit. This is exactly the prescribed de-narration pattern from spec_guide directive 6 ("a standard-library HTML entity decoder", not the callee name): here "whether the underlying stream supports flushing" instead of hasattr(self._out,'flush'). Omitting the guard would instead be a faithfulness/too-weak defect in the G-PANEL-1/2 lanes.

OBSERVATION, NOT A FINDING (by design, mode-parity controlled): meta.json modeled_functions is rendered into the spec block by eval/prompts.py._spec_block as "propagateFlush (<-> django.core.management.base.OutputWrapper.flush)" with repo_location "django/core/management/base.py:120 ... method added post-patch at body lines 143-146". That names the patched file and function, but it is the deliberate EDIT-LOCALIZATION aid that mode 0 receives identically via _localization_block, so it is an intentional harness aid rather than spec-view leakage and is outside this gate's scope. Flagging only so it is not mistaken for an uncontrolled channel. Note the repo_location string does additionally disclose "method added post-patch" (i.e. that the fix ADDS a method) which the mode-0 localization block would not phrase that way -- worth a harness-side look, but it is meta.json text, not a spec-view line, so it does not change this verdict.

PRIOR-RECORD CAVEAT: verdict.md records G-PANEL-3 as status=fail with machine verdict "panel_3: INCONCLUSIVE (no verdict submitted)" and "audit role errored: Exception: the auditor returned an error result". All four roles show the same agent-launch error, so that retained fail label is an infrastructure outage, not an oracle verdict on spec weakness; I did not treat it as evidence and judged the artifact fresh.

Counterexample / evidence:

```
No gold-reconstruction path exists. Adversarial reconstruction test from the spec view ALONE: a solver learns only (a) there is a thin output-stream wrapper, (b) a flush request must be forwarded to the underlying stream exactly once when that stream supports flushing, (c) it must be a no-op otherwise, (d) the flushable aspect is read-only. They do NOT learn: the file (django/core/management/base.py), the class (OutputWrapper), the guard expression (hasattr(self._out,'flush')), the delegate attribute (_out), or the DIAGNOSIS (that OutputWrapper subclasses io.TextIOBase whose generic flush() is a no-op and that __getattr__ is bypassed because the attribute already resolves on the base class). The solver must still locate the class and independently discover the inheritance-shadowing cause and that the remedy is defining an explicit flush method. Reconstruction therefore fails.
```

### MECHANICAL CHECKS (all run, all clean):
- markers.same_spec(Solution.lean, Solution_prepatch.lean) = True; spec_signature identical -> spec region byte-identical as required.
- scripts/lean_verify.sh Solution.lean -> EXIT=0 (spec+impl genuinely verifies; not a vacuous pass).
- leakage.screen() on BOTH Solution.lean and Solution_prepatch.lean: passed=True, zero hard failures, zero warnings.
- No diff markers ('@@', 'diff --git', '+++ ', 'index ') in the spec view.
- No gold changed line reproduced. Gold changed lines are ['def flush(self):', "if hasattr(self._out, 'flush'):", 'self._out.flush()']; none appear normalized in the view.
- Patched file path / dotted module path absent from the view.
- Explicit absence check for repo+test symbols in the spec view, all False: OutputWrapper, _out, hasattr, TextIOBase, __getattr__, io., StringIO, mock, mocked_flush, test_outputwrapper, user_commands, call_command, stdout, stderr, isatty, style_func, django, base.py.
- Narration vocabulary screen clean (no bug/fix/patched/broken/previously/incorrectly/wrong...).

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `properties.py`, `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.
