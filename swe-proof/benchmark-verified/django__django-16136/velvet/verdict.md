# P2 adversarial audit — django__django-16136

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

> **Record correction.** Some sections below reason about a divergent rival that
> verifies vacuously under `set_option loom.semantics.termination "partial"`,
> which is what this bundle set when that audit ran. The bundle now sets
> `loom.semantics.termination "total"`, so the verifier discharges a termination
> obligation and a divergent rival is rejected rather than vacuously accepted.
> No statement below that such a rival verifies, or that this specification has a
> divergence hole of that shape, describes the current artifact.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 13 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 13 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 10 | `atk_1_prepatch.lean`, `atk_2_inverted.lean`, `atk_3_always_awaitable.lean`, `atk_4_truncate_allowed.lean`, `atk_5_reverse_allowed.lean`, `atk_6_empty_response.lean`, `atk_7_diverge_measure.lean`, `atk_8_diverge_nomeasure.lean`, `atk_10_flag_from_list.lean`, `atk_15_guarded_selfcall.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_9_oracle_echo.lean`, `atk_11_oob_read.lean`, `atk_12_oob_async_only.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec, VERIFYING impl has a faithful refined patch that fails to resolve. The first ensures clause (`out = deliverNotAllowed asynchronous allowed`) totally pins the return value as a function of both inputs over a finite two-shape carrier, and the four auxiliary clauses re-pin the wrapper (`out.isAwaitable = asynchronous`), the content (`out.response = {allowed}`) and the per-branch shape. Every wrong-VALUE terminating impl is therefore rejected (atk_1..atk_6, atk_10 all exit 1). The three impls that DO verify (atk_9 ungrounded-oracle echo, atk_11/atk_12 logically-total out-of-range reads) are all behaviourally GOLD, and each one's faithful patch was materialized and RUN: resolved=True in all three cases -- correct echoes, not spec weakness. The interesting near-miss is atk_11/atk_12: `allowed[7]!` / `allowed[allowed.length]!` is provably `= default` in the logic (`by decide` closes it) yet PANICS under `#eval`, which looked like a total-in-the-logic / aborts-at-runtime hole. Two measurements killed it: (a) Lean's panic PRINTS and CONTINUES with the Inhabited default rather than aborting (probe_panic_semantics.lean prints "EXECUTION_CONTINUED_AFTER_PANIC"), and (b) an UNUSED `let _probe := allowed[7]!` binding is dead code that never even evaluates (probe_lazy.lean prints the A-sentinel with NO panic line). So the faithful Python counterpart is a stderr line plus a default value, NOT a raised IndexError -- and that faithful patch RESOLVES (atk11_faithful, atk12_faithful: completed=True resolved=True). The over-strong IndexError-raising transliterations do NOT resolve (completed=True resolved=False), but they are UNFAITHFUL refinements of a dead binding and are reported as such rather than as a break.
```

**Attacks re-run (13):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good)

```diff
@@ -79,12 +79,10 @@
   ensures asynchronous = false → out = Delivery.immediate { allowed := allowed }
   do
     -- impl-start
-    -- Build the 405 response listing the permitted methods, then choose the
-    -- delivery wrapper by whether the view runs asynchronously: an awaitable in
-    -- the asynchronous case (so the caller may await it), the response object
-    -- itself otherwise.
+    -- PREPATCH BUG: the 405 response is handed back as the plain response object
+    -- unconditionally; the asynchronous case is not handled.
     let resp : NotAllowed := { allowed := allowed }
-    let out := if asynchronous then Delivery.awaitable resp else Delivery.immediate resp
+    let out := Delivery.immediate resp
     return out
     -- impl-end
 
```

Attack 2 — `atk_2_inverted.lean` → rejected (same spec, does not verify — good)

```diff
@@ -79,12 +79,9 @@
   ensures asynchronous = false → out = Delivery.immediate { allowed := allowed }
   do
     -- impl-start
-    -- Build the 405 response listing the permitted methods, then choose the
-    -- delivery wrapper by whether the view runs asynchronously: an awaitable in
-    -- the asynchronous case (so the caller may await it), the response object
-    -- itself otherwise.
+    -- WRONG: delivery wrapper inverted -- awaitable when SYNC, plain when ASYNC.
     let resp : NotAllowed := { allowed := allowed }
-    let out := if asynchronous then Delivery.awaitable resp else Delivery.immediate resp
+    let out := if asynchronous then Delivery.immediate resp else Delivery.awaitable resp
     return out
     -- impl-end
 
```

Attack 3 — `atk_3_always_awaitable.lean` → rejected (same spec, does not verify — good)

```diff
@@ -79,12 +79,10 @@
   ensures asynchronous = false → out = Delivery.immediate { allowed := allowed }
   do
     -- impl-start
-    -- Build the 405 response listing the permitted methods, then choose the
-    -- delivery wrapper by whether the view runs asynchronously: an awaitable in
-    -- the asynchronous case (so the caller may await it), the response object
-    -- itself otherwise.
+    -- PARTIAL DOMAIN: always an awaitable. Correct on the async row, wrong on the
+    -- sync row (a sync view would hand back a coroutine nobody awaits).
     let resp : NotAllowed := { allowed := allowed }
-    let out := if asynchronous then Delivery.awaitable resp else Delivery.immediate resp
+    let out := Delivery.awaitable resp
     return out
     -- impl-end
 
```

Attack 4 — `atk_4_truncate_allowed.lean` → rejected (same spec, does not verify — good)

```diff
@@ -79,11 +79,10 @@
   ensures asynchronous = false → out = Delivery.immediate { allowed := allowed }
   do
     -- impl-start
-    -- Build the 405 response listing the permitted methods, then choose the
-    -- delivery wrapper by whether the view runs asynchronously: an awaitable in
-    -- the asynchronous case (so the caller may await it), the response object
-    -- itself otherwise.
-    let resp : NotAllowed := { allowed := allowed }
+    -- BOUNDARY / PARTIAL DOMAIN: wrapper mapping is CORRECT and the response is
+    -- correct on every one-element method list, but a longer permitted-method
+    -- list is truncated to its first method (a malformed 405 Allow header).
+    let resp : NotAllowed := { allowed := allowed.take 1 }
     let out := if asynchronous then Delivery.awaitable resp else Delivery.immediate resp
     return out
     -- impl-end
```

Attack 5 — `atk_5_reverse_allowed.lean` → rejected (same spec, does not verify — good)

```diff
@@ -79,11 +79,9 @@
   ensures asynchronous = false → out = Delivery.immediate { allowed := allowed }
   do
     -- impl-start
-    -- Build the 405 response listing the permitted methods, then choose the
-    -- delivery wrapper by whether the view runs asynchronously: an awaitable in
-    -- the asynchronous case (so the caller may await it), the response object
-    -- itself otherwise.
-    let resp : NotAllowed := { allowed := allowed }
+    -- BOUNDARY (order): correct wrapper and correct method SET, but the permitted
+    -- method list is reversed -- a fixed point on singletons, wrong for 2+.
+    let resp : NotAllowed := { allowed := allowed.reverse }
     let out := if asynchronous then Delivery.awaitable resp else Delivery.immediate resp
     return out
     -- impl-end
```

Attack 6 — `atk_6_empty_response.lean` → rejected (same spec, does not verify — good)

```diff
@@ -79,11 +79,9 @@
   ensures asynchronous = false → out = Delivery.immediate { allowed := allowed }
   do
     -- impl-start
-    -- Build the 405 response listing the permitted methods, then choose the
-    -- delivery wrapper by whether the view runs asynchronously: an awaitable in
-    -- the asynchronous case (so the caller may await it), the response object
-    -- itself otherwise.
-    let resp : NotAllowed := { allowed := allowed }
+    -- BOUNDARY (content): correct wrapper, but the 405 is built over a FRESH EMPTY
+    -- method list instead of the one handed in.
+    let resp : NotAllowed := { allowed := [] }
     let out := if asynchronous then Delivery.awaitable resp else Delivery.immediate resp
     return out
     -- impl-end
```

Attack 7 — `atk_7_diverge_measure.lean` → rejected (same spec, does not verify — good)

```diff
@@ -79,10 +79,17 @@
   ensures asynchronous = false → out = Delivery.immediate { allowed := allowed }
   do
     -- impl-start
-    -- Build the 405 response listing the permitted methods, then choose the
-    -- delivery wrapper by whether the view runs asynchronously: an awaitable in
-    -- the asynchronous case (so the caller may await it), the response object
-    -- itself otherwise.
+    -- CONTROL-FLOW EFFECT (divergence): a non-terminating prefix carrying a
+    -- measure that does NOT descend. Under partial-correctness semantics this
+    -- would discharge every `ensures` VACUOUSLY; the question is whether the
+    -- frozen `termination "total"` / `open TotalCorrectness` scope rejects it.
+    let mut spin : Nat := 1
+    while spin > 0
+      invariant spin = 1
+      done_with spin = 0
+      decreasing spin
+    do
+      spin := spin
     let resp : NotAllowed := { allowed := allowed }
     let out := if asynchronous then Delivery.awaitable resp else Delivery.immediate resp
     return out
```

Attack 8 — `atk_8_diverge_nomeasure.lean` → rejected (same spec, does not verify — good)

```diff
@@ -79,10 +79,14 @@
   ensures asynchronous = false → out = Delivery.immediate { allowed := allowed }
   do
     -- impl-start
-    -- Build the 405 response listing the permitted methods, then choose the
-    -- delivery wrapper by whether the view runs asynchronously: an awaitable in
-    -- the asynchronous case (so the caller may await it), the response object
-    -- itself otherwise.
+    -- CONTROL-FLOW EFFECT (divergence, no measure): same diverging prefix with the
+    -- `decreasing` clause omitted entirely.
+    let mut spin : Nat := 1
+    while spin > 0
+      invariant spin = 1
+      done_with spin = 0
+    do
+      spin := spin
     let resp : NotAllowed := { allowed := allowed }
     let out := if asynchronous then Delivery.awaitable resp else Delivery.immediate resp
     return out
```

Attack 9 — `atk_9_oracle_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -79,13 +79,9 @@
   ensures asynchronous = false → out = Delivery.immediate { allowed := allowed }
   do
     -- impl-start
-    -- Build the 405 response listing the permitted methods, then choose the
-    -- delivery wrapper by whether the view runs asynchronously: an awaitable in
-    -- the asynchronous case (so the caller may await it), the response object
-    -- itself otherwise.
-    let resp : NotAllowed := { allowed := allowed }
-    let out := if asynchronous then Delivery.awaitable resp else Delivery.immediate resp
-    return out
+    -- UNGROUNDED-ORACLE ECHO: return the pure deep-model value verbatim, doing no
+    -- work of its own. Verifies by definitional unfolding; behaviourally gold.
+    return deliverNotAllowed asynchronous allowed
     -- impl-end
 
 prove_correct notAllowedResponse by
```

Attack 10 — `atk_10_flag_from_list.lean` → rejected (same spec, does not verify — good)

```diff
@@ -79,12 +79,11 @@
   ensures asynchronous = false → out = Delivery.immediate { allowed := allowed }
   do
     -- impl-start
-    -- Build the 405 response listing the permitted methods, then choose the
-    -- delivery wrapper by whether the view runs asynchronously: an awaitable in
-    -- the asynchronous case (so the caller may await it), the response object
-    -- itself otherwise.
+    -- UNGROUNDED ORACLE (wrong witness): decide the delivery from a property of the
+    -- permitted-method list instead of the asynchronicity flag. Agrees with gold
+    -- on the inputs where `allowed` happens to be non-empty AND the view is async.
     let resp : NotAllowed := { allowed := allowed }
-    let out := if asynchronous then Delivery.awaitable resp else Delivery.immediate resp
+    let out := if allowed.isEmpty then Delivery.immediate resp else Delivery.awaitable resp
     return out
     -- impl-end
 
```

Attack 11 — `atk_11_oob_read.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -79,10 +79,10 @@
   ensures asynchronous = false → out = Delivery.immediate { allowed := allowed }
   do
     -- impl-start
-    -- Build the 405 response listing the permitted methods, then choose the
-    -- delivery wrapper by whether the view runs asynchronously: an awaitable in
-    -- the asynchronous case (so the caller may await it), the response object
-    -- itself otherwise.
+    -- BOUNDARY (total-Lean op): read past the end of the permitted-method list and
+    -- discard the value. `allowed[7]!` is TOTAL in Lean (it denotes `default` when
+    -- out of range), so this cannot change the delivered value.
+    let _probe := allowed[7]!
     let resp : NotAllowed := { allowed := allowed }
     let out := if asynchronous then Delivery.awaitable resp else Delivery.immediate resp
     return out
```

Attack 12 — `atk_12_oob_async_only.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -79,12 +79,17 @@
   ensures asynchronous = false → out = Delivery.immediate { allowed := allowed }
   do
     -- impl-start
-    -- Build the 405 response listing the permitted methods, then choose the
-    -- delivery wrapper by whether the view runs asynchronously: an awaitable in
-    -- the asynchronous case (so the caller may await it), the response object
-    -- itself otherwise.
+    -- BOUNDARY (logically total, runtime-panicking) reached ONLY in the async
+    -- branch -- the exact F2P case. `allowed[allowed.length]!` is out of range for
+    -- EVERY list, and in the LOGIC it denotes the Inhabited default, so the
+    -- postconditions are untouched and the frozen proof closes.
     let resp : NotAllowed := { allowed := allowed }
-    let out := if asynchronous then Delivery.awaitable resp else Delivery.immediate resp
+    let out :=
+      if asynchronous then
+        let _probe := allowed[allowed.length]!
+        Delivery.awaitable resp
+      else
+        Delivery.immediate resp
     return out
     -- impl-end
 
```

Attack 13 — `atk_15_guarded_selfcall.lean` → rejected (same spec, does not verify — good)

```diff
@@ -79,13 +79,16 @@
   ensures asynchronous = false → out = Delivery.immediate { allowed := allowed }
   do
     -- impl-start
-    -- Build the 405 response listing the permitted methods, then choose the
-    -- delivery wrapper by whether the view runs asynchronously: an awaitable in
-    -- the asynchronous case (so the caller may await it), the response object
-    -- itself otherwise.
+    -- CONTROL-FLOW EFFECT (guarded self-call): recurse under a guard, then deliver.
+    -- If the guard is treated as infeasible the recursion is never discharged yet
+    -- the clauses still close -- and the faithful patch recurses without bound.
     let resp : NotAllowed := { allowed := allowed }
-    let out := if asynchronous then Delivery.awaitable resp else Delivery.immediate resp
-    return out
+    if allowed.length > 1000000 then
+      let inner <- notAllowedResponse asynchronous allowed
+      return inner
+    else
+      let out := if asynchronous then Delivery.awaitable resp else Delivery.immediate resp
+      return out
     -- impl-end
 
 prove_correct notAllowedResponse by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The set of HTTP methods the resource permits is
--  produced by an UNCHANGED helper; this routine merely consumes that set, so it
--  is taken as the read-only free input `allowed` and owed no contract. There is
--  no `axiom` declaration and no A-reference deep model of an outside callee:
--  the only behaviour under spec — how the 405 response is HANDED BACK — is
--  modeled deeply in the `pure`/`impl` regions. See mapping.md §3.)
-- axioms-end

-- pure-start
/- The "405 — method not allowed" response: it reports the set of HTTP methods
   the resource does permit. Its content does not depend on how it is delivered. -/
structure NotAllowed where
  allowed : List String
  deriving DecidableEq, Inhabited

/- How a produced response is handed back to the caller:
     * `immediate r` — the response object `r` itself, returned directly;
     * `awaitable r` — an awaitable object that yields the response `r` when it
                       is awaited.
   Only the outer delivery wrapper differs between the two; the underlying
   response `r` is the same. -/
inductive Delivery where
  | immediate (resp : NotAllowed)
  | awaitable (resp : NotAllowed)
  deriving DecidableEq, Inhabited

/- Whether the handed-back object is an awaitable (must be awaited to obtain the
   response) rather than the response object itself. -/
def Delivery.isAwaitable : Delivery → Bool
  | .immediate _ => false
  | .awaitable _ => true

/- The response ultimately obtained — directly, or after awaiting. -/
def Delivery.response : Delivery → NotAllowed
  | .immediate r => r
  | .awaitable r => r

/- The desired delivery of a "method not allowed" outcome: build the 405 response
   listing the permitted methods `allowed`, then hand it back as an awaitable
   exactly when the view runs asynchronously (so a caller may await it), and as
   the plain response object otherwise. The response content is identical in
   both cases — only the wrapper differs. -/
def deliverNotAllowed (asynchronous : Bool) (allowed : List String) : Delivery :=
  let resp : NotAllowed := { allowed := allowed }
  if asynchronous then Delivery.awaitable resp else Delivery.immediate resp
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Produce the response handed back when a request uses an HTTP method the view
   does not permit.

   `asynchronous` records whether the view runs asynchronously; `allowed` is the
   set of methods the resource permits (read-only — the value an unchanged helper
   reports). Both are read-only (neither `mut`): the routine reads them and
   returns a delivery, mutating nothing it is handed (directive 5).

   The 405 response listing `allowed` is delivered as an awaitable precisely when
   the view is asynchronous, and as the plain response object otherwise; either
   way the underlying response is the same 405 response listing `allowed`. -/
method notAllowedResponse (asynchronous : Bool) (allowed : List String) return (out : Delivery)
  ensures out = deliverNotAllowed asynchronous allowed
  ensures out.isAwaitable = asynchronous
  ensures out.response = { allowed := allowed }
  ensures asynchronous = true  → out = Delivery.awaitable { allowed := allowed }
  ensures asynchronous = false → out = Delivery.immediate { allowed := allowed }
  do
    -- impl-start
    -- Positive control: same behaviour, different SHAPE (match instead of if,
    -- response built per branch). Must verify -- else the spec over-constrains
    -- the impl shape rather than the observable behaviour.
    match asynchronous with
    | true  => return Delivery.awaitable { allowed := allowed }
    | false => return Delivery.immediate { allowed := allowed }
    -- impl-end

prove_correct notAllowedResponse by
  loom_solve <;>
    cases asynchronous <;>
    simp_all [deliverNotAllowed, Delivery.isAwaitable, Delivery.response]
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity attack on django__django-16136 velvet. Scratch: (worktree at base_commit 19e6efa50b under ./wt). All 14 submitted files are same_spec=True vs the frozen Solution.lean AND admissible under variant_scope.variant_problems (no new axiom/sorry/theorem, prove_correct preserved) -- confirmed programmatically.

*** STALE-PRIOR-PASS CORRECTION (the most important finding) *** The recorded G-EQ verdict (meta.json: status=fail, "eq: INCONCLUSIVE -- 1 attack(s) inconclusive") rests on reasoning that does NOT describe this artifact. Every attack file rendered in verdict.md reads `set_option loom.semantics.termination "partial"` / `open PartialCorrectness`, and its whole crux paragraph argues that divergence verifies vacuously under partial semantics and can only ever hang (completed=False => inconclusive). The FROZEN Solution.lean is `"total"` / `open TotalCorrectness` (as are all 500 velvet bundles).

I re-measured the semantics with a rival rather than reading the option, per docs/architecture.md §9: atk_7 (diverging `while spin > 0` prefix carrying `decreasing spin`) is REJECTED on the measure's own goal (`case «decreasing_1: spin» ... |- False`, exit 1), and atk_8 (same loop, `decreasing` omitted) is refused even earlier by the elaborator ("Decreasing annotations are required in total correctness semantics", exit 1). Loom/MonadAlgebras/WP/Options.lean:180-186 shows the `set_option` elaborator itself calls `openScope `TotalCorrectness`, so option and open cannot disagree. The divergence lane -- the prior pass's entire basis for INCONCLUSIVE -- is CLOSED here. The bundle deserves a real verdict, and no attack of mine breaks it.

1. atk_1_prepatch.lean            -- PREPATCH BUG (always Delivery.immediate) | EXIT 1 => prepatch reproduced; this is the F2P bug (asyncio.iscoroutine must be True for AsyncView).
2. atk_2_inverted.lean            -- wrapper inverted (wrong on BOTH rows) | EXIT 1.
3. atk_3_always_awaitable.lean    -- partial-domain: always awaitable, right only on the async row | EXIT 1.
4. atk_4_truncate_allowed.lean    -- boundary: `allowed.take 1`, correct on every singleton list | EXIT 1.
5. atk_5_reverse_allowed.lean     -- boundary (order): `allowed.reverse`, a fixed point on singletons | EXIT 1.
6. atk_6_empty_response.lean      -- boundary (content): 405 over a fresh `[]` | EXIT 1.
7. atk_7_diverge_measure.lean     -- control-flow-effect: divergence w/ non-descending measure | EXIT 1 (measure goal `spin < spin`).
8. atk_8_diverge_nomeasure.lean   -- control-flow-effect: divergence, no measure | EXIT 1 (elaborator refuses).
9. atk_9_oracle_echo.lean         -- UNGROUNDED-ORACLE ECHO `return deliverNotAllowed asynchronous allowed` | EXIT 0 VERIFIES. Faithful patch = gold patch.diff VERBATIM (diff-confirmed identical). run_resolve => completed=True RESOLVED=True => correct echo, NOT a weakness.
10. atk_10_flag_from_list.lean     -- ungrounded oracle: dispatch on `allowed.isEmpty` instead of the flag | EXIT 1.
11. atk_11_oob_read.lean           -- `let _probe := allowed[7]!` then gold | EXIT 0 VERIFIES. Faithful patch (stderr panic line + default, per measurement) => completed=True RESOLVED=True. Gold-equivalent echo.
12. atk_12_oob_async_only.lean     -- same read reached ONLY on the async row (the exact F2P case) | EXIT 0 VERIFIES. Faithful patch => completed=True RESOLVED=True.
13. atk_15_guarded_selfcall.lean   -- guarded self-call (known vacuity trap; its Python counterpart is RecursionError, a COMPLETED failure unlike a hang) | EXIT 1, rejected on a genuine termination obligation ("fail to show termination for notAllowedResponse").
Positive control pos_control.lean -- structurally different (match on the flag, response built per branch), behaviourally gold | EXIT 0 VERIFIES (so the spec is not over-fitted to the gold impl SHAPE). Distinct file from every attack.

EXECUTED RESOLVE RUNS (5 total, all completed; runner `resolve_one.py` = run_resolve(instance, patch, timeout=1800, retries=1), launched concurrently as background jobs; JSON at resolve_<name>.json):
  atk9_echo        (= gold verbatim)            -> completed=True resolved=True  "resolved"
  atk11_faithful   (dead-binding-faithful)      -> completed=True resolved=True  "resolved"
  atk12_faithful   (dead-binding-faithful)      -> completed=True resolved=True  "resolved"
  atk11_oob        (UNFAITHFUL IndexError form) -> completed=True resolved=False "did not resolve in 2 attempts (consistent -- not flaky)"
  atk12_oob_async  (UNFAITHFUL IndexError form) -> completed=True resolved=False "did not resolve in 2 attempts (consistent -- not flaky)"
I report the two non-resolutions in full and explicitly DECLINE to call them a break, because the refinement they encode is wrong, not the spec: `_probe` is an UNUSED binding, and I measured (probe_lazy.lean) that Lean never evaluates it (no panic line printed), while a raised IndexError is a control-flow effect the Lean impl provably does not have. Per docs/architecture.md §5 the finding requires the attack's FAITHFUL patch to fail; the faithful one resolves. Calling the IndexError variant a break would be inventing spec weakness from a bad transliteration.

NEGATIVE RESULTS I am NOT counting as spec strength (honesty about measurement traps, docs §9): atk_13_demonic_no_wrapper.lean and atk_14_demonic_pinned.lean (demonic `let (out : Delivery) :| ...` -- an underdetermined delivery whose wrapper is unconstrained) both exit 1, but on `failed to synthesize Findable ...` -- an INSTANCE-SYNTHESIS artifact of the substrate, not a postcondition rejection. An earlier spelling failed on a bare parse error. The `:|` lane is thus UNMEASURED on this carrier; even the fully-pinned control could not be made to elaborate, so I cannot claim the lane is closed. It is also not evidence of a hole (nothing verified). Files are left in the scratch dir for a re-run.

REFINEMENT.MD AUDIT (my assigned focus -- the A legs). meta.json: axioms=[], deep_model_references=[], G-AX status=skip; Solution.lean contains ZERO `axiom` declarations (grep-confirmed), so there is no A-consumed and no A-reference leg to audit, and axiom_check.py is a legitimate skip stub rather than a hidden trust point.

All five legs A1-A5 are R or I and each correspondence checks out against the gold hunk read at base_commit: A1 `allowed : List String` <-> `self._allowed_methods()` (verified in the worktree to return `['GET','OPTIONS']` for both F2P view classes); A2 `asynchronous : Bool` <-> the `view_is_async` classproperty (base.py:60-76, an UNCHANGED all-sync-or-all-async check -- correctly a free input, and the spec holds for BOTH values so no contract is consumed); A3 `NotAllowed {allowed}` <-> `HttpResponseNotAllowed(...)`; A4 the dispatch `Delivery.awaitable resp` <-> `func()` (the `async def func(): return response` coroutine) and `Delivery.immediate resp` <-> `return response` -- matches patch.diff 1:1; A5 the return.

NO kind-3 (inexpressible-changed-op) leg: the one genuinely CHANGED operation (wrap in an awaitable iff async) is modeled DEEPLY by the `Delivery` sum + `deliverNotAllowed`, not hidden behind an axiom about the function under change. Independently confirmed the same async-def-wrap idiom already exists verbatim in the UNCHANGED `options()` handler (base.py:153-166), which is what the P2P test_options_handler_responds_correctly pins -- consistent with refinement.md's "strict, content-preserving addition" claim.

One modeling gap I note as advisory (NOT a break): the model says nothing about the `logger.warning(... status_code 405 ...)` call the real handler makes first; I searched the tests and no F2P or P2P test observes that log (the tested surface is only tests/async/tests.py -- 2 F2P + 7 P2P), so it is unobservable at the oracle and correctly outside the modeling boundary.

FLOOR: 13 distinct same-spec attacks (>= 5) spanning prepatch, wrong-value, partial-domain, boundary/content/order, control-flow-effect (divergence x2, guarded self-call), and ungrounded-oracle echo; prepatch bug reproduced (atk_1 exit 1); positive control verifies (exit 0) and is a distinct file. Every verifying attack has a materialized faithful patch that was RUN through the official harness, and all three resolved. VERDICT: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 13 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 13 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 10 | `atk_1_prepatch.lean`, `atk_2_inverted.lean`, `atk_3_always_awaitable.lean`, `atk_4_truncate_allowed.lean`, `atk_5_reverse_allowed.lean`, `atk_6_empty_response.lean`, `atk_7_diverge_measure.lean`, `atk_8_diverge_nomeasure.lean`, `atk_10_flag_from_list.lean`, `atk_15_guarded_selfcall.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_9_oracle_echo.lean`, `atk_11_oob_read.lean`, `atk_12_oob_async_only.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec, VERIFYING impl has a faithful refined patch that fails to resolve. The first ensures clause (`out = deliverNotAllowed asynchronous allowed`) totally pins the return value as a function of both inputs over a finite two-shape carrier, and the four auxiliary clauses re-pin the wrapper (`out.isAwaitable = asynchronous`), the content (`out.response = {allowed}`) and the per-branch shape. Every wrong-VALUE terminating impl is therefore rejected (atk_1..atk_6, atk_10 all exit 1). The three impls that DO verify (atk_9 ungrounded-oracle echo, atk_11/atk_12 logically-total out-of-range reads) are all behaviourally GOLD, and each one's faithful patch was materialized and RUN: resolved=True in all three cases -- correct echoes, not spec weakness. The interesting near-miss is atk_11/atk_12: `allowed[7]!` / `allowed[allowed.length]!` is provably `= default` in the logic (`by decide` closes it) yet PANICS under `#eval`, which looked like a total-in-the-logic / aborts-at-runtime hole. Two measurements killed it: (a) Lean's panic PRINTS and CONTINUES with the Inhabited default rather than aborting (probe_panic_semantics.lean prints "EXECUTION_CONTINUED_AFTER_PANIC"), and (b) an UNUSED `let _probe := allowed[7]!` binding is dead code that never even evaluates (probe_lazy.lean prints the A-sentinel with NO panic line). So the faithful Python counterpart is a stderr line plus a default value, NOT a raised IndexError -- and that faithful patch RESOLVES (atk11_faithful, atk12_faithful: completed=True resolved=True). The over-strong IndexError-raising transliterations do NOT resolve (completed=True resolved=False), but they are UNFAITHFUL refinements of a dead binding and are reported as such rather than as a break.
```

**Attacks re-run (13):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 13 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_inverted.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3_always_awaitable.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4_truncate_allowed.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5_reverse_allowed.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6_empty_response.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7_diverge_measure.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8_diverge_nomeasure.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9_oracle_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 10 — `atk_10_flag_from_list.lean` → rejected (same spec, does not verify — good)

Attack 11 — `atk_11_oob_read.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 12 — `atk_12_oob_async_only.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 13 — `atk_15_guarded_selfcall.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The set of HTTP methods the resource permits is
--  produced by an UNCHANGED helper; this routine merely consumes that set, so it
--  is taken as the read-only free input `allowed` and owed no contract. There is
--  no `axiom` declaration and no A-reference deep model of an outside callee:
--  the only behaviour under spec — how the 405 response is HANDED BACK — is
--  modeled deeply in the `pure`/`impl` regions. See mapping.md §3.)
-- axioms-end

-- pure-start
/- The "405 — method not allowed" response: it reports the set of HTTP methods
   the resource does permit. Its content does not depend on how it is delivered. -/
structure NotAllowed where
  allowed : List String
  deriving DecidableEq, Inhabited

/- How a produced response is handed back to the caller:
     * `immediate r` — the response object `r` itself, returned directly;
     * `awaitable r` — an awaitable object that yields the response `r` when it
                       is awaited.
   Only the outer delivery wrapper differs between the two; the underlying
   response `r` is the same. -/
inductive Delivery where
  | immediate (resp : NotAllowed)
  | awaitable (resp : NotAllowed)
  deriving DecidableEq, Inhabited

/- Whether the handed-back object is an awaitable (must be awaited to obtain the
   response) rather than the response object itself. -/
def Delivery.isAwaitable : Delivery → Bool
  | .immediate _ => false
  | .awaitable _ => true

/- The response ultimately obtained — directly, or after awaiting. -/
def Delivery.response : Delivery → NotAllowed
  | .immediate r => r
  | .awaitable r => r

/- The desired delivery of a "method not allowed" outcome: build the 405 response
   listing the permitted methods `allowed`, then hand it back as an awaitable
   exactly when the view runs asynchronously (so a caller may await it), and as
   the plain response object otherwise. The response content is identical in
   both cases — only the wrapper differs. -/
def deliverNotAllowed (asynchronous : Bool) (allowed : List String) : Delivery :=
  let resp : NotAllowed := { allowed := allowed }
  if asynchronous then Delivery.awaitable resp else Delivery.immediate resp
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Produce the response handed back when a request uses an HTTP method the view
   does not permit.

   `asynchronous` records whether the view runs asynchronously; `allowed` is the
   set of methods the resource permits (read-only — the value an unchanged helper
   reports). Both are read-only (neither `mut`): the routine reads them and
   returns a delivery, mutating nothing it is handed (directive 5).

   The 405 response listing `allowed` is delivered as an awaitable precisely when
   the view is asynchronous, and as the plain response object otherwise; either
   way the underlying response is the same 405 response listing `allowed`. -/
method notAllowedResponse (asynchronous : Bool) (allowed : List String) return (out : Delivery)
  ensures out = deliverNotAllowed asynchronous allowed
  ensures out.isAwaitable = asynchronous
  ensures out.response = { allowed := allowed }
  ensures asynchronous = true  → out = Delivery.awaitable { allowed := allowed }
  ensures asynchronous = false → out = Delivery.immediate { allowed := allowed }
  do
    -- impl-start
    -- Positive control: same behaviour, different SHAPE (match instead of if,
    -- response built per branch). Must verify -- else the spec over-constrains
    -- the impl shape rather than the observable behaviour.
    match asynchronous with
    | true  => return Delivery.awaitable { allowed := allowed }
    | false => return Delivery.immediate { allowed := allowed }
    -- impl-end

prove_correct notAllowedResponse by
  loom_solve <;>
    cases asynchronous <;>
    simp_all [deliverNotAllowed, Delivery.isAwaitable, Delivery.response]
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity attack on django__django-16136 velvet. Scratch: (worktree at base_commit 19e6efa50b under ./wt). All 14 submitted files are same_spec=True vs the frozen Solution.lean AND admissible under variant_scope.variant_problems (no new axiom/sorry/theorem, prove_correct preserved) -- confirmed programmatically.

*** STALE-PRIOR-PASS CORRECTION (the most important finding) *** The recorded G-EQ verdict (meta.json: status=fail, "eq: INCONCLUSIVE -- 1 attack(s) inconclusive") rests on reasoning that does NOT describe this artifact. Every attack file rendered in verdict.md reads `set_option loom.semantics.termination "partial"` / `open PartialCorrectness`, and its whole crux paragraph argues that divergence verifies vacuously under partial semantics and can only ever hang (completed=False => inconclusive). The FROZEN Solution.lean is `"total"` / `open TotalCorrectness` (as are all 500 velvet bundles).

I re-measured the semantics with a rival rather than reading the option, per docs/architecture.md §9: atk_7 (diverging `while spin > 0` prefix carrying `decreasing spin`) is REJECTED on the measure's own goal (`case «decreasing_1: spin» ... |- False`, exit 1), and atk_8 (same loop, `decreasing` omitted) is refused even earlier by the elaborator ("Decreasing annotations are required in total correctness semantics", exit 1). Loom/MonadAlgebras/WP/Options.lean:180-186 shows the `set_option` elaborator itself calls `openScope `TotalCorrectness`, so option and open cannot disagree. The divergence lane -- the prior pass's entire basis for INCONCLUSIVE -- is CLOSED here. The bundle deserves a real verdict, and no attack of mine breaks it.

1. atk_1_prepatch.lean            -- PREPATCH BUG (always Delivery.immediate) | EXIT 1 => prepatch reproduced; this is the F2P bug (asyncio.iscoroutine must be True for AsyncView).
2. atk_2_inverted.lean            -- wrapper inverted (wrong on BOTH rows) | EXIT 1.
3. atk_3_always_awaitable.lean    -- partial-domain: always awaitable, right only on the async row | EXIT 1.
4. atk_4_truncate_allowed.lean    -- boundary: `allowed.take 1`, correct on every singleton list | EXIT 1.
5. atk_5_reverse_allowed.lean     -- boundary (order): `allowed.reverse`, a fixed point on singletons | EXIT 1.
6. atk_6_empty_response.lean      -- boundary (content): 405 over a fresh `[]` | EXIT 1.
7. atk_7_diverge_measure.lean     -- control-flow-effect: divergence w/ non-descending measure | EXIT 1 (measure goal `spin < spin`).
8. atk_8_diverge_nomeasure.lean   -- control-flow-effect: divergence, no measure | EXIT 1 (elaborator refuses).
9. atk_9_oracle_echo.lean         -- UNGROUNDED-ORACLE ECHO `return deliverNotAllowed asynchronous allowed` | EXIT 0 VERIFIES. Faithful patch = gold patch.diff VERBATIM (diff-confirmed identical). run_resolve => completed=True RESOLVED=True => correct echo, NOT a weakness.
10. atk_10_flag_from_list.lean     -- ungrounded oracle: dispatch on `allowed.isEmpty` instead of the flag | EXIT 1.
11. atk_11_oob_read.lean           -- `let _probe := allowed[7]!` then gold | EXIT 0 VERIFIES. Faithful patch (stderr panic line + default, per measurement) => completed=True RESOLVED=True. Gold-equivalent echo.
12. atk_12_oob_async_only.lean     -- same read reached ONLY on the async row (the exact F2P case) | EXIT 0 VERIFIES. Faithful patch => completed=True RESOLVED=True.
13. atk_15_guarded_selfcall.lean   -- guarded self-call (known vacuity trap; its Python counterpart is RecursionError, a COMPLETED failure unlike a hang) | EXIT 1, rejected on a genuine termination obligation ("fail to show termination for notAllowedResponse").
Positive control pos_control.lean -- structurally different (match on the flag, response built per branch), behaviourally gold | EXIT 0 VERIFIES (so the spec is not over-fitted to the gold impl SHAPE). Distinct file from every attack.

EXECUTED RESOLVE RUNS (5 total, all completed; runner `resolve_one.py` = run_resolve(instance, patch, timeout=1800, retries=1), launched concurrently as background jobs; JSON at resolve_<name>.json):
  atk9_echo        (= gold verbatim)            -> completed=True resolved=True  "resolved"
  atk11_faithful   (dead-binding-faithful)      -> completed=True resolved=True  "resolved"
  atk12_faithful   (dead-binding-faithful)      -> completed=True resolved=True  "resolved"
  atk11_oob        (UNFAITHFUL IndexError form) -> completed=True resolved=False "did not resolve in 2 attempts (consistent -- not flaky)"
  atk12_oob_async  (UNFAITHFUL IndexError form) -> completed=True resolved=False "did not resolve in 2 attempts (consistent -- not flaky)"
I report the two non-resolutions in full and explicitly DECLINE to call them a break, because the refinement they encode is wrong, not the spec: `_probe` is an UNUSED binding, and I measured (probe_lazy.lean) that Lean never evaluates it (no panic line printed), while a raised IndexError is a control-flow effect the Lean impl provably does not have. Per docs/architecture.md §5 the finding requires the attack's FAITHFUL patch to fail; the faithful one resolves. Calling the IndexError variant a break would be inventing spec weakness from a bad transliteration.

NEGATIVE RESULTS I am NOT counting as spec strength (honesty about measurement traps, docs §9): atk_13_demonic_no_wrapper.lean and atk_14_demonic_pinned.lean (demonic `let (out : Delivery) :| ...` -- an underdetermined delivery whose wrapper is unconstrained) both exit 1, but on `failed to synthesize Findable ...` -- an INSTANCE-SYNTHESIS artifact of the substrate, not a postcondition rejection. An earlier spelling failed on a bare parse error. The `:|` lane is thus UNMEASURED on this carrier; even the fully-pinned control could not be made to elaborate, so I cannot claim the lane is closed. It is also not evidence of a hole (nothing verified). Files are left in the scratch dir for a re-run.

REFINEMENT.MD AUDIT (my assigned focus -- the A legs). meta.json: axioms=[], deep_model_references=[], G-AX status=skip; Solution.lean contains ZERO `axiom` declarations (grep-confirmed), so there is no A-consumed and no A-reference leg to audit, and axiom_check.py is a legitimate skip stub rather than a hidden trust point.

All five legs A1-A5 are R or I and each correspondence checks out against the gold hunk read at base_commit: A1 `allowed : List String` <-> `self._allowed_methods()` (verified in the worktree to return `['GET','OPTIONS']` for both F2P view classes); A2 `asynchronous : Bool` <-> the `view_is_async` classproperty (base.py:60-76, an UNCHANGED all-sync-or-all-async check -- correctly a free input, and the spec holds for BOTH values so no contract is consumed); A3 `NotAllowed {allowed}` <-> `HttpResponseNotAllowed(...)`; A4 the dispatch `Delivery.awaitable resp` <-> `func()` (the `async def func(): return response` coroutine) and `Delivery.immediate resp` <-> `return response` -- matches patch.diff 1:1; A5 the return.

NO kind-3 (inexpressible-changed-op) leg: the one genuinely CHANGED operation (wrap in an awaitable iff async) is modeled DEEPLY by the `Delivery` sum + `deliverNotAllowed`, not hidden behind an axiom about the function under change. Independently confirmed the same async-def-wrap idiom already exists verbatim in the UNCHANGED `options()` handler (base.py:153-166), which is what the P2P test_options_handler_responds_correctly pins -- consistent with refinement.md's "strict, content-preserving addition" claim.

One modeling gap I note as advisory (NOT a break): the model says nothing about the `logger.warning(... status_code 405 ...)` call the real handler makes first; I searched the tests and no F2P or P2P test observes that log (the tested surface is only tests/async/tests.py -- 2 F2P + 7 P2P), so it is unobservable at the oracle and correctly outside the modeling boundary.

FLOOR: 13 distinct same-spec attacks (>= 5) spanning prepatch, wrong-value, partial-domain, boundary/content/order, control-flow-effect (divergence x2, guarded self-call), and ungrounded-oracle echo; prepatch bug reproduced (atk_1 exit 1); positive control verifies (exit 0) and is a distinct file. Every verifying attack has a materialized faithful patch that was RUN through the official harness, and all three resolved. VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** ATTACK OUTCOME: no diverging input found. I could not break faithfulness; the modeled function agrees with the real post-patch callee on every input I could reach.

### Mandated checks
1. same_spec byte-identity: PASS. markers.same_spec(Solution.lean, Solution_prepatch.lean, velvet.language) = True. Verified per-region too: axioms / pure / pre-conditions / post-conditions all byte-identical (spec_view identical, 3701 bytes); impl regions differ (required). So the discriminating power below is not an artifact of a weakened spec.
2. Solution.lean verifies: lean_verify.sh exit 0, no sorry/admit.
3. G-DIFF sanity (spec has teeth): Solution_prepatch.lean FAILS with unsolved goals on exactly the three discriminating clauses — ensures_5 (out = deliverNotAllowed ...), ensures_4 (out.isAwaitable = asynchronous), ensures_2 (asynchronous = true -> Delivery.awaitable ...). Not vacuous, not rubber-stampable.

### EMPIRICAL CONFORMANCE vs THE REAL REPO (worktree at base_commit 19e6efa50b, gold patch applied)
- EXHAUSTIVE over the real reachable domain: all 256 subsets of View.http_method_names x {sync, async} = 512 real View classes, each built with genuine (async) def handlers, calling the UNPATCHED real _allowed_methods() and the real view_is_async classproperty — no monkeypatching. Abstraction map alpha: iscoroutine -> Delivery.awaitable / else immediate, asyncio.run to await. Result: 0 disagreements with deliverNotAllowed, out.isAwaitable = asynchronous, and out.response = {allowed}. Also checked isinstance HttpResponseNotAllowed and status_code == 405 in all 512.
- 400-case randomized fuzz (bundle's pinned seed 16136) with adversarial allowed lists (empty, duplicates, embedded commas 'A,B', empty strings, unicode, lowercase): 0 mismatches.
- Invariance: delivery is independent of request/args/kwargs — 18 (request, args, kwargs) combos per async value collapse to a single delivery, so (asynchronous, allowed) really is the complete input basis. No hidden dependency the model omits.
- Content identity across delivery modes confirmed (same class, 405, same Allow header) — matches ensures out.response = {allowed} in both branches.
- allowed is neither mutated nor aliased by the real handler (Allow header is a snapshot), consistent with the read-only (non-mut) parameters.
- Real test loop closed: with gold patch, async.tests.ViewTests 5/5 OK. With only the source hunk reverted (test patch retained), test_http_method_not_allowed_responds_correctly FAILS on AsyncView (iscoroutine False is not True) — the exact bug the spec's isAwaitable clause encodes.

OVER-STRENGTH / CARRIER-EXACTNESS PROBES (attempted breaks, all rejected as defects)
- Bool carrier exactness: view_is_async returns a genuine Python bool for every non-mixed reachable class (type set = {'bool'}). Not a tri-state, so Bool is exact.
- MixedView partiality: for a mixed sync/async class, view_is_async raises ImproperlyConfigured and hence the real handler raises, while the Lean method is total. NOT a divergence: (a) the raise originates in view_is_async — the PRODUCER of the free input — not in the modeled handler body, so in that state no Bool value for `asynchronous` exists and there is no input to the modeled function; (b) the state is unreachable via routing (as_view() raises first, so no request can reach the handler); (c) the partiality is unchanged by the patch (identical pre- and post-patch) and test_mixed_views_raise_error passes at base. Correctly scoped out by mapping.md §3 as an unchanged free input.
- Coroutine single-use: the real func() coroutine can be awaited only once (second asyncio.run -> RuntimeError 'cannot reuse already awaited coroutine'), whereas Delivery.response is a pure reusable projection. Also not an over-strength defect: Delivery.response is an OBSERVATION of the yielded value, not an awaitable-consumption operation, and the spec never asserts repeated awaiting succeeds. This is abstraction lossiness (an under-specification direction), and it cannot admit a wrong impl here — it does not cause the spec to reject the gold patch, which is what this gate tests.
- Allow-header injectivity: over all 256 reachable _allowed_methods() values the ', '.join is injective and no method name contains ',' or ' ', so modeling the response content as the List String carries no collapse.

NO-AXIOM CLAIM AUDITED: confirmed there is no `axiom` declaration and no deep-model reference; the changed behaviour (awaitable-iff-async dispatch) is modeled deeply in the pure/impl regions rather than assumed, so the discriminating content is proved, not axiomatized. mapping.md §3 and refinement.md §B,§C accurately describe the real repo (_allowed_methods and view_is_async are genuinely untouched by patch.diff).

Bundle's own conformance_check.py independently reports 100010 inputs, 0 disagreements — consistent with my independent probes, which used the real Django objects rather than a transliteration.

CONCLUSION: FAITHFUL. The spec is neither too strong nor drifted: it accepts the gold patch on all 512 exhaustive reachable inputs plus 400 fuzz cases, rejects the pre-patch behaviour on precisely the bug clauses, and its two abstraction boundaries (mixed-view partiality, single-await coroutines) are correctly outside the modeled region.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** ROLE: leakage / gold-reconstruction for django__django-16136 velvet. Verdict NO-LEAKAGE.

BASELINE ESTABLISHED. Leakage judged against instance.json problem_statement ONLY; hints_text explicitly excluded. Note the hints are far more disclosive than the statement (they name http_method_not_allowed() and say to mirror options()) and NONE of that vocabulary reaches the spec view -- checked directly, not assumed. Public statement gives: title 'object HttpResponseNotAllowed can't be used in await expression'; 'Method Not Allowed (GET)'; a View subclass whose only handler is an async post; the traceback showing the returned 405 object being awaited under asgiref. So the statement itself discloses (a) the method-not-allowed path, (b) that its response is an HttpResponseNotAllowed, (c) that in an async view something must await it.

SPEC VIEW ACTUALLY COMPUTED (not eyeballed): markers.spec_view(Solution.lean, velvet) -- impl region collapsed to the elision placeholder and the prove_correct body elided; consumers see nothing else (eval/prompts.py _spec_block ships only spec_view; mapping.md and refinement.md are NOT consumer-visible, so their explicit gold hunk, file:line bindings and pre-patch body are out of scope for this role).

MECHANICAL SCREEN: leakage.screen() over the computed view = 0 hard failures, 0 warnings, mode strict. No gold-patch line reproduced, no diff markers, no patched file/module path.

TOKEN-LEVEL CHECK of the gold edit's own vocabulary, word-boundary regex on the view: func, view_is_async, http_method_not_allowed, _allowed_methods, HttpResponseNotAllowed, coroutine, 'async def', asyncio, iscoroutine, base.py, generic, views -- ALL ABSENT. Gold changed symbols per _patch_changed_symbols = {http_method_not_allowed, func}; neither appears in any identifier or comment. The view uses neutral carriers throughout (notAllowedResponse, Delivery.immediate/awaitable, deliverNotAllowed, asynchronous, allowed). No bug->fix narration (no fix/bug/regression/previously/wrong).

THE ONE CLAUSE WORTH ARGUING, and why it is not a leak. `ensures out.isAwaitable = asynchronous` (plus the two branch clauses) pins the discriminating behavior of the fix: awaitable exactly iff the view is async. I considered calling this gold-reconstruction and rejected it on three independent grounds.

(1) It is the statement's own demand: the crash is the 405 object being awaited in an async view, and sync views must keep working (PASS_TO_PASS), so 'awaitable iff async' is forced by public information -- a solver derives it without the patch.

(2) Stating required behavior is a spec's function; leakage is disclosure of the EDIT (location/mechanism/diff text) beyond baseline, and none of that survives here. A spec stripped of this clause would be dead -- I confirmed it is load-bearing rather than decorative: Solution.lean verifies (lean_verify.sh exit 0) and the prepatch twin, which returns Delivery.immediate unconditionally, FAILS exactly on this clause ('ensures_5 ... true |- False'), reproducing the F2P bug.

(3) REPO-VISIBLE ANYWAY: at base_commit 19e6efa5, django/views/generic/base.py View.options -- the sibling method ~10 lines below the function under change -- ALREADY contains the identical idiom verbatim (`if self.view_is_async: async def func(): return response; return func() else: return response`). The gold patch is a copy of a pattern the solver can read in the same class. A spec view that abstractly states 'awaitable iff async' therefore discloses strictly less than the untouched checkout does.

'405' appears in the view and not literally in the statement; not a leak: 'Method Not Allowed' IS public verbatim, 405 is its universal HTTP status code, it occurs in the patch only as CONTEXT (the unchanged extra={'status_code': 405} logging line), and it localizes nothing about the edit, which is the awaitable wrapping.

NO TEST LEAK: the companion F2P test_mixed_views_raise_error exercises view_is_async's all-sync-or-all-async ImproperlyConfigured check; the spec view says nothing about mixed handlers or raising -- correctly silent.

SPEC IDENTITY: same_spec(Solution.lean, Solution_prepatch.lean, velvet) = True -- byte-identical spec signature, so the leak judgment covers the twin too. patch.diff == instance.json patch (verbatim gold).

No writes to the bundle, no writing git commands. (velvet/meta.json shows modified in git status -- pre-existing driver gate record, mtime precedes this audit; not touched by me.)

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
