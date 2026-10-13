# P2 adversarial audit — astropy__astropy-13977

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1_prepatch.lean`, `atk_2_alwaysdefer.lean`, `atk_3_negdefer.lean`, `atk_4_fatalintercept.lean`, `atk_5_dropvalue.lean`, `atk_6_partialdomain.lean`, `atk_7b_cfeffect.lean`, `atk_9_fatalswap.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 /- The two shapes a failure of the wrapped computation can take.
@@ -111,18 +111,15 @@
   ensures out = ufuncSpec call
   do
     -- impl-start
-    -- Consult the wrapped computation and branch on its OUTCOME rather than
-    -- letting every failure escape: a recoverable failure is turned into the
-    -- deferral sentinel when an alternate handler is available, else the same
-    -- failure is re-propagated; a fatal failure always propagates; a success is
-    -- returned verbatim.
+    -- Pre-image skeleton: the wrapped computation is consulted WITHOUT
+    -- interception — a successful value is returned, but ANY failure (whether
+    -- recoverable or fatal) escapes unchanged. The frozen spec requires that a
+    -- recoverable failure with an available alternate handler instead yield the
+    -- deferral sentinel, so prove_correct MUST fail on that case.
     let result : Except UfuncErr Outcome :=
       match coreUfunc call with
       | Except.ok v => Except.ok (Outcome.result v)
-      | Except.error UfuncErr.recoverable =>
-          if canDefer call then Except.ok Outcome.deferred
-          else Except.error UfuncErr.recoverable
-      | Except.error UfuncErr.fatal => Except.error UfuncErr.fatal
+      | Except.error e => Except.error e
     return result
     -- impl-end
 
```

Attack 2 — `atk_2_alwaysdefer.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 /- The two shapes a failure of the wrapped computation can take.
@@ -111,20 +111,13 @@
   ensures out = ufuncSpec call
   do
     -- impl-start
-    -- Consult the wrapped computation and branch on its OUTCOME rather than
-    -- letting every failure escape: a recoverable failure is turned into the
-    -- deferral sentinel when an alternate handler is available, else the same
-    -- failure is re-propagated; a fatal failure always propagates; a success is
-    -- returned verbatim.
     let result : Except UfuncErr Outcome :=
       match coreUfunc call with
       | Except.ok v => Except.ok (Outcome.result v)
-      | Except.error UfuncErr.recoverable =>
-          if canDefer call then Except.ok Outcome.deferred
-          else Except.error UfuncErr.recoverable
+      | Except.error UfuncErr.recoverable => Except.ok Outcome.deferred
       | Except.error UfuncErr.fatal => Except.error UfuncErr.fatal
     return result
-    -- impl-end
+        -- impl-end
 
 prove_correct dispatchUfunc by
   loom_solve
```

Attack 3 — `atk_3_negdefer.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 /- The two shapes a failure of the wrapped computation can take.
@@ -111,20 +111,15 @@
   ensures out = ufuncSpec call
   do
     -- impl-start
-    -- Consult the wrapped computation and branch on its OUTCOME rather than
-    -- letting every failure escape: a recoverable failure is turned into the
-    -- deferral sentinel when an alternate handler is available, else the same
-    -- failure is re-propagated; a fatal failure always propagates; a success is
-    -- returned verbatim.
     let result : Except UfuncErr Outcome :=
       match coreUfunc call with
       | Except.ok v => Except.ok (Outcome.result v)
       | Except.error UfuncErr.recoverable =>
-          if canDefer call then Except.ok Outcome.deferred
-          else Except.error UfuncErr.recoverable
+          if canDefer call then Except.error UfuncErr.recoverable
+          else Except.ok Outcome.deferred
       | Except.error UfuncErr.fatal => Except.error UfuncErr.fatal
     return result
-    -- impl-end
+        -- impl-end
 
 prove_correct dispatchUfunc by
   loom_solve
```

Attack 4 — `atk_4_fatalintercept.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 /- The two shapes a failure of the wrapped computation can take.
@@ -111,20 +111,14 @@
   ensures out = ufuncSpec call
   do
     -- impl-start
-    -- Consult the wrapped computation and branch on its OUTCOME rather than
-    -- letting every failure escape: a recoverable failure is turned into the
-    -- deferral sentinel when an alternate handler is available, else the same
-    -- failure is re-propagated; a fatal failure always propagates; a success is
-    -- returned verbatim.
     let result : Except UfuncErr Outcome :=
       match coreUfunc call with
       | Except.ok v => Except.ok (Outcome.result v)
-      | Except.error UfuncErr.recoverable =>
+      | Except.error _ =>
           if canDefer call then Except.ok Outcome.deferred
           else Except.error UfuncErr.recoverable
-      | Except.error UfuncErr.fatal => Except.error UfuncErr.fatal
     return result
-    -- impl-end
+        -- impl-end
 
 prove_correct dispatchUfunc by
   loom_solve
```

Attack 5 — `atk_5_dropvalue.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 /- The two shapes a failure of the wrapped computation can take.
@@ -111,20 +111,15 @@
   ensures out = ufuncSpec call
   do
     -- impl-start
-    -- Consult the wrapped computation and branch on its OUTCOME rather than
-    -- letting every failure escape: a recoverable failure is turned into the
-    -- deferral sentinel when an alternate handler is available, else the same
-    -- failure is re-propagated; a fatal failure always propagates; a success is
-    -- returned verbatim.
     let result : Except UfuncErr Outcome :=
       match coreUfunc call with
-      | Except.ok v => Except.ok (Outcome.result v)
+      | Except.ok _ => Except.ok Outcome.deferred
       | Except.error UfuncErr.recoverable =>
           if canDefer call then Except.ok Outcome.deferred
           else Except.error UfuncErr.recoverable
       | Except.error UfuncErr.fatal => Except.error UfuncErr.fatal
     return result
-    -- impl-end
+        -- impl-end
 
 prove_correct dispatchUfunc by
   loom_solve
```

Attack 6 — `atk_6_partialdomain.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 /- The two shapes a failure of the wrapped computation can take.
@@ -111,20 +111,17 @@
   ensures out = ufuncSpec call
   do
     -- impl-start
-    -- Consult the wrapped computation and branch on its OUTCOME rather than
-    -- letting every failure escape: a recoverable failure is turned into the
-    -- deferral sentinel when an alternate handler is available, else the same
-    -- failure is re-propagated; a fatal failure always propagates; a success is
-    -- returned verbatim.
     let result : Except UfuncErr Outcome :=
-      match coreUfunc call with
-      | Except.ok v => Except.ok (Outcome.result v)
-      | Except.error UfuncErr.recoverable =>
-          if canDefer call then Except.ok Outcome.deferred
-          else Except.error UfuncErr.recoverable
-      | Except.error UfuncErr.fatal => Except.error UfuncErr.fatal
+      if call = 0 then Except.ok Outcome.deferred
+      else
+        match coreUfunc call with
+        | Except.ok v => Except.ok (Outcome.result v)
+        | Except.error UfuncErr.recoverable =>
+            if canDefer call then Except.ok Outcome.deferred
+            else Except.error UfuncErr.recoverable
+        | Except.error UfuncErr.fatal => Except.error UfuncErr.fatal
     return result
-    -- impl-end
+        -- impl-end
 
 prove_correct dispatchUfunc by
   loom_solve
```

Attack 7 — `atk_7b_cfeffect.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 /- The two shapes a failure of the wrapped computation can take.
@@ -111,17 +111,14 @@
   ensures out = ufuncSpec call
   do
     -- impl-start
-    -- Consult the wrapped computation and branch on its OUTCOME rather than
-    -- letting every failure escape: a recoverable failure is turned into the
-    -- deferral sentinel when an alternate handler is available, else the same
-    -- failure is re-propagated; a fatal failure always propagates; a success is
-    -- returned verbatim.
+    let core := coreUfunc call
+    let deferDecision : Except UfuncErr Outcome :=
+      if canDefer call then Except.ok Outcome.deferred
+      else Except.ok Outcome.deferred  -- BUG: both branches defer
     let result : Except UfuncErr Outcome :=
-      match coreUfunc call with
+      match core with
       | Except.ok v => Except.ok (Outcome.result v)
-      | Except.error UfuncErr.recoverable =>
-          if canDefer call then Except.ok Outcome.deferred
-          else Except.error UfuncErr.recoverable
+      | Except.error UfuncErr.recoverable => deferDecision
       | Except.error UfuncErr.fatal => Except.error UfuncErr.fatal
     return result
     -- impl-end
```

Attack 8 — `atk_9_fatalswap.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 /- The two shapes a failure of the wrapped computation can take.
@@ -111,20 +111,15 @@
   ensures out = ufuncSpec call
   do
     -- impl-start
-    -- Consult the wrapped computation and branch on its OUTCOME rather than
-    -- letting every failure escape: a recoverable failure is turned into the
-    -- deferral sentinel when an alternate handler is available, else the same
-    -- failure is re-propagated; a fatal failure always propagates; a success is
-    -- returned verbatim.
     let result : Except UfuncErr Outcome :=
       match coreUfunc call with
       | Except.ok v => Except.ok (Outcome.result v)
       | Except.error UfuncErr.recoverable =>
           if canDefer call then Except.ok Outcome.deferred
           else Except.error UfuncErr.recoverable
-      | Except.error UfuncErr.fatal => Except.error UfuncErr.fatal
+      | Except.error UfuncErr.fatal => Except.error UfuncErr.recoverable
     return result
-    -- impl-end
+        -- impl-end
 
 prove_correct dispatchUfunc by
   loom_solve
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- The two shapes a failure of the wrapped computation can take.

     * `recoverable` — a failure of the kind that arises when the operands are
       incompatible with the requested operation (an operand whose value cannot
       be brought into the form the operation expects). This is the failure the
       desired behavior is allowed to turn into a deferral.
     * `fatal` — any other failure; it is never intercepted and always
       propagates out unchanged.

   The distinction is exactly the set of failure shapes the desired behavior
   distinguishes; provenance + executable soundness check: mapping.md §3 /
   axiom_check.py (G-AX). -/
inductive UfuncErr where
  | recoverable
  | fatal
  deriving DecidableEq

/- The shape of a normal (non-failing) return of the dispatch.

     * `deferred` — the distinguished sentinel meaning "this object does not
       implement the requested operation; another participant may"; returning it
       lets the operation be retried against the other operand's handler.
     * `result v` — an ordinary returned value, carried verbatim as an opaque
       handle `v` (the dispatch never inspects it). -/
inductive Outcome where
  | deferred
  | result (v : Int)
  deriving DecidableEq

/- The wrapped computation the dispatch consults (an UNCHANGED helper invoked,
   never redefined). It does NOT always succeed: on operands incompatible with
   the requested operation it fails, and the failure may be `recoverable` or
   `fatal`; otherwise it yields a value. Declared `opaque` (computable inside the
   `do` block) and given NO `ensures` — the desired behavior assumes nothing
   about WHICH value it returns, only how a success vs a failure is handled.
   Provenance + executable soundness check (that the real computation indeed
   fails recoverably on incompatible operands and succeeds on compatible ones):
   mapping.md §3.1 / axiom_check.py (G-AX). -/
opaque coreUfunc : Int → Except UfuncErr Int

/- Whether some participant in the operation advertises its own handler for it,
   so that — should the computation fail recoverably — deferring would give that
   participant a chance to perform the operation instead. An UNCHANGED predicate
   over the operands; modeled `opaque` with no asserted `ensures`. Provenance:
   mapping.md §3.2 / axiom_check.py (G-AX). -/
opaque canDefer : Int → Bool
-- axioms-end

-- pure-start
/- The intended outcome of the whole dispatch, as `Except UfuncErr Outcome`
   (`error` = a failure propagates out, `ok` = a value is returned):

     * if the wrapped computation SUCCEEDS, its value is returned verbatim;
     * if it fails RECOVERABLY, the failure is intercepted: when some other
       participant advertises a handler (`canDefer`), the dispatch returns the
       deferral sentinel instead of failing; otherwise the very same recoverable
       failure is re-propagated unchanged;
     * if it fails in any OTHER way, that failure propagates out unchanged — it
       is never intercepted.

   Only a recoverable failure with an available alternate handler is turned into
   a deferral; every other case preserves the wrapped computation's behavior
   exactly. -/
def ufuncSpec (call : Int) : Except UfuncErr Outcome :=
  match coreUfunc call with
  | Except.ok v => Except.ok (Outcome.result v)
  | Except.error UfuncErr.recoverable =>
      if canDefer call then Except.ok Outcome.deferred
      else Except.error UfuncErr.recoverable
  | Except.error UfuncErr.fatal => Except.error UfuncErr.fatal
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Dispatch an operation over operands, taking care of the operands'
   compatibility with it.

   Desired behavior: the dispatch consults a wrapped computation over the
   operands. That computation does not always succeed — on operands incompatible
   with the requested operation it fails, and a failure is either `recoverable`
   (an incompatibility that another participant might still resolve) or `fatal`.
   When it fails recoverably AND some participant advertises its own handler for
   the operation, the dispatch must RECOVER by returning the deferral sentinel
   (`Outcome.deferred`) rather than letting the failure escape — so the operation
   can be retried against that participant (the missing behavior the public
   problem statement reports). When it fails recoverably but no alternate handler
   is available, the same recoverable failure is re-propagated unchanged. A fatal
   failure always propagates unchanged. On success the computed value is returned
   verbatim.

   `call` is the read-only operation descriptor (not `mut`): the dispatch
   computes an outcome and mutates no input (directive 5). The descriptor is
   modeled as an opaque handle (`Int`); the only observations are the wrapped
   computation's outcome (`coreUfunc`) and the alternate-handler classification
   (`canDefer`) (mapping.md §2). -/
method dispatchUfunc (call : Int)
    return (out : Except UfuncErr Outcome)
  ensures out = ufuncSpec call
  do
    -- impl-start
    -- Consult the wrapped computation and branch on its OUTCOME rather than
    -- letting every failure escape: a recoverable failure is turned into the
    -- deferral sentinel when an alternate handler is available, else the same
    -- failure is re-propagated; a fatal failure always propagates; a success is
    -- returned verbatim.
    let result : Except UfuncErr Outcome :=
      match coreUfunc call with
      | Except.ok v => Except.ok (Outcome.result v)
      | Except.error UfuncErr.recoverable =>
          if canDefer call then Except.ok Outcome.deferred
          else Except.error UfuncErr.recoverable
      | Except.error UfuncErr.fatal => Except.error UfuncErr.fatal
    return result
    -- impl-end

prove_correct dispatchUfunc by
  loom_solve
  simp_all [ufuncSpec]
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ (velvet, refinement-fidelity / A-leg focus) for astropy__astropy-13977. VERDICT: SOUND. No verifying-but-wrong impl was found; the step-2 resolve obligation therefore applies to the empty set (no verifying patch to materialize / run_resolve), so verify-does-not-imply-correct is NOT exhibited.

PROTOCOL: all files, built by copying Solution.lean and editing ONLY the impl + prove_correct regions (axioms/pure/pre/post left byte-identical). same_spec (velvet backend) = True confirmed for every attack and both controls. Verified with `bash scripts/lean_verify.sh <f>` from project root, run concurrently in batches of <=4. Exit 0 = verifies, 1 = rejected.

### Controls
- pos_control.lean (gold Solution impl): exit 0, 0 error lines -> VERIFIES.
- atk_8b_oracleecho.lean (`return ufuncSpec call`, ungrounded-oracle echo, proof `loom_solve` only): same_spec=True, exit 0, 0 errors -> VERIFIES. This is a behaviorally-CORRECT echo (= ufuncSpec), i.e. a second non-vacuity control, NOT a wrong impl; a resolve run on its faithful patch would pass. (Note: atk_8_oracleecho.lean with the frozen 2-line proof `loom_solve; simp_all` failed only with 'No goals to be solved' at the simp_all line -- a proof-tactic artifact because loom_solve already closes the trivial goal; atk_8b uses the reduced proof and verifies.)

WRONG IMPLS (all same_spec=True, all REJECTED with exactly one 'unsolved goals' ensures-mismatch -- genuine spec-strength rejections on the discriminating leg, not parse/tactic artifacts):
- atk_1_prepatch.lean (prepatch bug: `Except.error e => Except.error e`, never defers): exit 1, unsolved goals on the recoverable+canDefer=true leg (LHS Except.error recoverable, spec Except.ok deferred). Prepatch reproduced = true.
- atk_2_alwaysdefer.lean (always-defer on recoverable, ignores canDefer): exit 1, unsolved goals on recoverable+canDefer=false.
- atk_3_negdefer.lean (negated canDefer, branches inverted): exit 1, unsolved goals.
- atk_4_fatalintercept.lean (partial-domain: collapses both error subtypes, also intercepts fatal): exit 1, unsolved goals on the fatal leg.
- atk_5_dropvalue.lean (success drops value -> deferred): exit 1, unsolved goals on the Except.ok leg.
- atk_6_partialdomain.lean (correct spec except call=0 forced to deferred): exit 1, unsolved goals.
- atk_7b_cfeffect.lean (control-flow-effect: let/intermediate-binding do-block where both if-branches defer): exit 1, unsolved goals. (An earlier atk_7 using `let mut ... := ...` in a do block failed to PARSE under WPGen -- mut assignment unsupported -- so it was replaced by atk_7b which parses cleanly and is rejected for the right reason.)
- atk_9_fatalswap.lean (boundary: fatal leg returns Except.error recoverable instead of fatal): exit 1, unsolved goals on the fatal leg.

Why SOUND: the spec `ensures out = ufuncSpec call` is a TOTAL function pinning the exact Except UfuncErr Outcome over the three exhaustive coreUfunc outcomes (ok / error recoverable / error fatal) x the canDefer classification. There is no answer-key to echo -- the spec is a function of the SAME two opaque callees (coreUfunc, canDefer, both `opaque` with NO ensures) that any verifying impl must consult, so any verifying impl is behaviorally = ufuncSpec (ungrounded-oracle probe negative: atk_8b echo is itself correct and resolves). Every genuine divergence I could construct (partial-domain, boundary error-subtype swap, control-flow-effect, negation, drop-value, always-defer, fatal-intercept, and the prepatch) is rejected on its discriminating leg.

REFINEMENT.MD AUDIT (A-leg / correspondence focus): legs A1-A6 tagged R (A1: call descriptor <-> opaque Int handle), A-reference+I (A2: match on coreUfunc outcome = try/except; A4: recoverable leg = the except (TypeError,ValueError) recover/re-raise with canDefer <-> the not all(... in ignored_ufunc) predicate), and I (A3 success verbatim, A5 fatal propagates, A6 totality). EVERY leg is R / A-reference / I -- NO kind-3 (inexpressible changed-op). The two A-reference callees carry NO `ensures`, so there is no consumed axiom to over-claim (matches refinement.md B). Model<->patch correspondence holds: UfuncErr.recoverable <-> the (TypeError,ValueError) the clause catches; UfuncErr.fatal <-> any other raise (propagated, never caught); Outcome.deferred <-> return NotImplemented; else-branch Except.error recoverable <-> raise e (same caught error); Outcome.result v <-> a normally-escaping value. The discriminating changed op (intercept recoverable failure -> defer iff alternate handler) is modeled DIRECTLY as the match/if-canDefer control flow (I legs over A-reference callees), not hidden behind an axiom. Correspondence is faithful.

EVIDENCE: {pos_control,atk_8b_oracleecho,atk_1_prepatch,atk_2_alwaysdefer,atk_3_negdefer,atk_4_fatalintercept,atk_5_dropvalue,atk_6_partialdomain,atk_7b_cfeffect,atk_9_fatalswap}.{lean,log}. >=5 distinct wrong-impl attacks run, none verifies -> none breaks the spec; no resolve run was needed because no wrong impl verified.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1_prepatch.lean`, `atk_2_alwaysdefer.lean`, `atk_3_negdefer.lean`, `atk_4_fatalintercept.lean`, `atk_5_dropvalue.lean`, `atk_6_partialdomain.lean`, `atk_7b_cfeffect.lean`, `atk_9_fatalswap.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_alwaysdefer.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3_negdefer.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4_fatalintercept.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5_dropvalue.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6_partialdomain.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7b_cfeffect.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_9_fatalswap.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- The two shapes a failure of the wrapped computation can take.

     * `recoverable` — a failure of the kind that arises when the operands are
       incompatible with the requested operation (an operand whose value cannot
       be brought into the form the operation expects). This is the failure the
       desired behavior is allowed to turn into a deferral.
     * `fatal` — any other failure; it is never intercepted and always
       propagates out unchanged.

   The distinction is exactly the set of failure shapes the desired behavior
   distinguishes; provenance + executable soundness check: mapping.md §3 /
   axiom_check.py (G-AX). -/
inductive UfuncErr where
  | recoverable
  | fatal
  deriving DecidableEq

/- The shape of a normal (non-failing) return of the dispatch.

     * `deferred` — the distinguished sentinel meaning "this object does not
       implement the requested operation; another participant may"; returning it
       lets the operation be retried against the other operand's handler.
     * `result v` — an ordinary returned value, carried verbatim as an opaque
       handle `v` (the dispatch never inspects it). -/
inductive Outcome where
  | deferred
  | result (v : Int)
  deriving DecidableEq

/- The wrapped computation the dispatch consults (an UNCHANGED helper invoked,
   never redefined). It does NOT always succeed: on operands incompatible with
   the requested operation it fails, and the failure may be `recoverable` or
   `fatal`; otherwise it yields a value. Declared `opaque` (computable inside the
   `do` block) and given NO `ensures` — the desired behavior assumes nothing
   about WHICH value it returns, only how a success vs a failure is handled.
   Provenance + executable soundness check (that the real computation indeed
   fails recoverably on incompatible operands and succeeds on compatible ones):
   mapping.md §3.1 / axiom_check.py (G-AX). -/
opaque coreUfunc : Int → Except UfuncErr Int

/- Whether some participant in the operation advertises its own handler for it,
   so that — should the computation fail recoverably — deferring would give that
   participant a chance to perform the operation instead. An UNCHANGED predicate
   over the operands; modeled `opaque` with no asserted `ensures`. Provenance:
   mapping.md §3.2 / axiom_check.py (G-AX). -/
opaque canDefer : Int → Bool
-- axioms-end

-- pure-start
/- The intended outcome of the whole dispatch, as `Except UfuncErr Outcome`
   (`error` = a failure propagates out, `ok` = a value is returned):

     * if the wrapped computation SUCCEEDS, its value is returned verbatim;
     * if it fails RECOVERABLY, the failure is intercepted: when some other
       participant advertises a handler (`canDefer`), the dispatch returns the
       deferral sentinel instead of failing; otherwise the very same recoverable
       failure is re-propagated unchanged;
     * if it fails in any OTHER way, that failure propagates out unchanged — it
       is never intercepted.

   Only a recoverable failure with an available alternate handler is turned into
   a deferral; every other case preserves the wrapped computation's behavior
   exactly. -/
def ufuncSpec (call : Int) : Except UfuncErr Outcome :=
  match coreUfunc call with
  | Except.ok v => Except.ok (Outcome.result v)
  | Except.error UfuncErr.recoverable =>
      if canDefer call then Except.ok Outcome.deferred
      else Except.error UfuncErr.recoverable
  | Except.error UfuncErr.fatal => Except.error UfuncErr.fatal
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Dispatch an operation over operands, taking care of the operands'
   compatibility with it.

   Desired behavior: the dispatch consults a wrapped computation over the
   operands. That computation does not always succeed — on operands incompatible
   with the requested operation it fails, and a failure is either `recoverable`
   (an incompatibility that another participant might still resolve) or `fatal`.
   When it fails recoverably AND some participant advertises its own handler for
   the operation, the dispatch must RECOVER by returning the deferral sentinel
   (`Outcome.deferred`) rather than letting the failure escape — so the operation
   can be retried against that participant (the missing behavior the public
   problem statement reports). When it fails recoverably but no alternate handler
   is available, the same recoverable failure is re-propagated unchanged. A fatal
   failure always propagates unchanged. On success the computed value is returned
   verbatim.

   `call` is the read-only operation descriptor (not `mut`): the dispatch
   computes an outcome and mutates no input (directive 5). The descriptor is
   modeled as an opaque handle (`Int`); the only observations are the wrapped
   computation's outcome (`coreUfunc`) and the alternate-handler classification
   (`canDefer`) (mapping.md §2). -/
method dispatchUfunc (call : Int)
    return (out : Except UfuncErr Outcome)
  ensures out = ufuncSpec call
  do
    -- impl-start
    -- Consult the wrapped computation and branch on its OUTCOME rather than
    -- letting every failure escape: a recoverable failure is turned into the
    -- deferral sentinel when an alternate handler is available, else the same
    -- failure is re-propagated; a fatal failure always propagates; a success is
    -- returned verbatim.
    let result : Except UfuncErr Outcome :=
      match coreUfunc call with
      | Except.ok v => Except.ok (Outcome.result v)
      | Except.error UfuncErr.recoverable =>
          if canDefer call then Except.ok Outcome.deferred
          else Except.error UfuncErr.recoverable
      | Except.error UfuncErr.fatal => Except.error UfuncErr.fatal
    return result
    -- impl-end

prove_correct dispatchUfunc by
  loom_solve
  simp_all [ufuncSpec]
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ (velvet, refinement-fidelity / A-leg focus) for astropy__astropy-13977. VERDICT: SOUND. No verifying-but-wrong impl was found; the step-2 resolve obligation therefore applies to the empty set (no verifying patch to materialize / run_resolve), so verify-does-not-imply-correct is NOT exhibited.

PROTOCOL: all files, built by copying Solution.lean and editing ONLY the impl + prove_correct regions (axioms/pure/pre/post left byte-identical). same_spec (velvet backend) = True confirmed for every attack and both controls. Verified with `bash scripts/lean_verify.sh <f>` from project root, run concurrently in batches of <=4. Exit 0 = verifies, 1 = rejected.

### Controls
- pos_control.lean (gold Solution impl): exit 0, 0 error lines -> VERIFIES.
- atk_8b_oracleecho.lean (`return ufuncSpec call`, ungrounded-oracle echo, proof `loom_solve` only): same_spec=True, exit 0, 0 errors -> VERIFIES. This is a behaviorally-CORRECT echo (= ufuncSpec), i.e. a second non-vacuity control, NOT a wrong impl; a resolve run on its faithful patch would pass. (Note: atk_8_oracleecho.lean with the frozen 2-line proof `loom_solve; simp_all` failed only with 'No goals to be solved' at the simp_all line -- a proof-tactic artifact because loom_solve already closes the trivial goal; atk_8b uses the reduced proof and verifies.)

WRONG IMPLS (all same_spec=True, all REJECTED with exactly one 'unsolved goals' ensures-mismatch -- genuine spec-strength rejections on the discriminating leg, not parse/tactic artifacts):
- atk_1_prepatch.lean (prepatch bug: `Except.error e => Except.error e`, never defers): exit 1, unsolved goals on the recoverable+canDefer=true leg (LHS Except.error recoverable, spec Except.ok deferred). Prepatch reproduced = true.
- atk_2_alwaysdefer.lean (always-defer on recoverable, ignores canDefer): exit 1, unsolved goals on recoverable+canDefer=false.
- atk_3_negdefer.lean (negated canDefer, branches inverted): exit 1, unsolved goals.
- atk_4_fatalintercept.lean (partial-domain: collapses both error subtypes, also intercepts fatal): exit 1, unsolved goals on the fatal leg.
- atk_5_dropvalue.lean (success drops value -> deferred): exit 1, unsolved goals on the Except.ok leg.
- atk_6_partialdomain.lean (correct spec except call=0 forced to deferred): exit 1, unsolved goals.
- atk_7b_cfeffect.lean (control-flow-effect: let/intermediate-binding do-block where both if-branches defer): exit 1, unsolved goals. (An earlier atk_7 using `let mut ... := ...` in a do block failed to PARSE under WPGen -- mut assignment unsupported -- so it was replaced by atk_7b which parses cleanly and is rejected for the right reason.)
- atk_9_fatalswap.lean (boundary: fatal leg returns Except.error recoverable instead of fatal): exit 1, unsolved goals on the fatal leg.

Why SOUND: the spec `ensures out = ufuncSpec call` is a TOTAL function pinning the exact Except UfuncErr Outcome over the three exhaustive coreUfunc outcomes (ok / error recoverable / error fatal) x the canDefer classification. There is no answer-key to echo -- the spec is a function of the SAME two opaque callees (coreUfunc, canDefer, both `opaque` with NO ensures) that any verifying impl must consult, so any verifying impl is behaviorally = ufuncSpec (ungrounded-oracle probe negative: atk_8b echo is itself correct and resolves). Every genuine divergence I could construct (partial-domain, boundary error-subtype swap, control-flow-effect, negation, drop-value, always-defer, fatal-intercept, and the prepatch) is rejected on its discriminating leg.

REFINEMENT.MD AUDIT (A-leg / correspondence focus): legs A1-A6 tagged R (A1: call descriptor <-> opaque Int handle), A-reference+I (A2: match on coreUfunc outcome = try/except; A4: recoverable leg = the except (TypeError,ValueError) recover/re-raise with canDefer <-> the not all(... in ignored_ufunc) predicate), and I (A3 success verbatim, A5 fatal propagates, A6 totality). EVERY leg is R / A-reference / I -- NO kind-3 (inexpressible changed-op). The two A-reference callees carry NO `ensures`, so there is no consumed axiom to over-claim (matches refinement.md B). Model<->patch correspondence holds: UfuncErr.recoverable <-> the (TypeError,ValueError) the clause catches; UfuncErr.fatal <-> any other raise (propagated, never caught); Outcome.deferred <-> return NotImplemented; else-branch Except.error recoverable <-> raise e (same caught error); Outcome.result v <-> a normally-escaping value. The discriminating changed op (intercept recoverable failure -> defer iff alternate handler) is modeled DIRECTLY as the match/if-canDefer control flow (I legs over A-reference callees), not hidden behind an axiom. Correspondence is faithful.

EVIDENCE: {pos_control,atk_8b_oracleecho,atk_1_prepatch,atk_2_alwaysdefer,atk_3_negdefer,atk_4_fatalintercept,atk_5_dropvalue,atk_6_partialdomain,atk_7b_cfeffect,atk_9_fatalswap}.{lean,log}. >=5 distinct wrong-impl attacks run, none verifies -> none breaks the spec; no resolve run was needed because no wrong impl verified.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack found NO diverging input; the spec is faithful, not over-strong.

Checks performed:
1. Spec-region byte-identity: same_spec(Solution.lean, Solution_prepatch.lean) via swebench_unified.markers with the VelvetBackend LanguageTables = True. Axioms/pure/pre/post + method signature & `ensures` are byte-identical between gold and prepatch. G-HYGIENE region hashes recorded.
2. Gold verifies: scripts/lean_verify.sh Solution.lean -> exit 0. Prepatch fails (G-DIFF pass) precisely on the recoverable-with-canDefer leg, as expected.

Faithfulness reasoning (is ufuncSpec too strong / does it drift from the real callee?):
- ufuncSpec is a 1:1 transliteration of the gold patch control flow: try<body> success -> return value verbatim (Outcome.result v); except (TypeError,ValueError) -> if deferral predicate holds return NotImplemented (Outcome.deferred) else re-raise the SAME caught error (Except.error recoverable); any other exception propagates unchanged (Except.error fatal).
- The two callees are modeled `opaque` with NO asserted `ensures`: coreUfunc (unchanged __array_ufunc__ body outcome) and canDefer (the added `not all(getattr(type(io),'__array_ufunc__',None) in ignored_ufunc ...)` predicate). A spec that assumes nothing about WHICH value the callees produce cannot be too strong; it only pins the outcome-dispatch control flow the patch actually adds. There is no over-claim to break.
- Every leg matches the real patched dispatch (patch.diff verbatim, base_commit 5250b2442501...). No input maps a real behavior to a Lean value that ufuncSpec forbids.
- Only modeling nuance: a body-returned NotImplemented maps to Outcome.result while the recover-branch NotImplemented maps to Outcome.deferred — a conformance abstraction choice, not a spec over-claim, and covered by the opaque, ensures-free callees.
- Corroborating in-bundle evidence: G-CONF R/I shadow vs patch.diff agreed on 100013 fuzzed calls (seed 13977), 0 disagreements; G-AX confirmed the body raises exactly TypeError/ValueError on 7 boundary + 1511 fuzz operands and canDefer matches the real classification (True for a duck operand with its own __array_ufunc__, False for a plain dict).

Attempted attacks and why they fail to diverge: (a) claiming ufuncSpec forces deferral when the real code would re-raise — refuted, both gated on the identical canDefer predicate; (b) claiming success values are constrained — refuted, Outcome.result carries an opaque Int, never inspected; (c) claiming fatal exceptions could be intercepted — refuted, the fatal leg propagates unchanged, matching the narrow `except (TypeError,ValueError)`. No diverging input exists.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Verified same_spec(Solution.lean, Solution_prepatch.lean, velvet)=True via swebench_unified.markers — the spec view (imports/axioms/pure/pre/post + method signature & ensures + docstrings) is byte-identical between the gold and prepatch twins; the gold edit lives ONLY in the elided impl region, so the spec view cannot carry it by construction. Leakage screen against the public problem_statement (NOT hints_text):

- The public statement already states 'Should Quantity.__array_ufunc__() return NotImplemented instead of raising ValueError if the inputs are incompatible?' and 'it would allow for __radd__ to be called', and its own DuckArray MWE literally defines a custom __array_ufunc__. So the three abstract notions in the spec — (a) a recoverable/incompatible-operand failure, (b) some participant advertising its own handler, (c) a deferral sentinel return — are all derivable from public text.
- The spec view abstracts, never quotes, the gold specifics: UfuncErr.recoverable/fatal carry NO TypeError/ValueError literal; Outcome.deferred carries NO NotImplemented literal; canDefer is described as 'some participant advertises its own handler' with NO getattr(..., '__array_ufunc__') / ignored_ufunc / isinstance(io,(Quantity,ndarray,Column)) machinery; there is NO try/except control-flow structure anywhere in the view.
- The gold-implementation mechanics that are NOT in the public statement (the try/except wrapper and the recognized-handler getattr/isinstance check) appear ONLY in hints_text, which is excluded from this screen — and they do NOT appear in the spec view. The 're-raise when no alternate handler' leg is mere preservation of existing pre-patch behavior, not a leaked gold specific.

Helpers coreUfunc and canDefer are opaque with no asserted ensures, so no callee behavior is over-claimed in the view. No spec-view line reveals the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
