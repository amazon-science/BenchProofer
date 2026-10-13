# P2 adversarial audit — sympy__sympy-18211

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

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
 /- The two shapes a failure of the univariate-relation solver can take when it is
@@ -100,16 +100,10 @@
   ensures out = asSetSpec rel
   do
     -- impl-start
-    -- Consult the solver and branch on its OUTCOME rather than letting a
-    -- cannot-solve failure escape: a cannot-solve report is turned into the
-    -- explicit condition set over the reals built from the relation; any other
-    -- failure propagates unchanged; a produced solution set is returned verbatim.
     let result : Except SolveErr SetVal :=
       match solveUnivariate rel with
       | Except.ok h => Except.ok (SetVal.solverSet h)
-      | Except.error SolveErr.cannotSolve =>
-          Except.ok (SetVal.conditionOverReals rel)
-      | Except.error SolveErr.other => Except.error SolveErr.other
+      | Except.error e => Except.error e
     return result
     -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

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
 /- The two shapes a failure of the univariate-relation solver can take when it is
@@ -100,16 +100,11 @@
   ensures out = asSetSpec rel
   do
     -- impl-start
-    -- Consult the solver and branch on its OUTCOME rather than letting a
-    -- cannot-solve failure escape: a cannot-solve report is turned into the
-    -- explicit condition set over the reals built from the relation; any other
-    -- failure propagates unchanged; a produced solution set is returned verbatim.
     let result : Except SolveErr SetVal :=
       match solveUnivariate rel with
       | Except.ok h => Except.ok (SetVal.solverSet h)
-      | Except.error SolveErr.cannotSolve =>
-          Except.ok (SetVal.conditionOverReals rel)
-      | Except.error SolveErr.other => Except.error SolveErr.other
+      | Except.error SolveErr.cannotSolve => Except.error SolveErr.cannotSolve
+      | Except.error SolveErr.other => Except.ok (SetVal.conditionOverReals rel)
     return result
     -- impl-end
 
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

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
 /- The two shapes a failure of the univariate-relation solver can take when it is
@@ -100,16 +100,10 @@
   ensures out = asSetSpec rel
   do
     -- impl-start
-    -- Consult the solver and branch on its OUTCOME rather than letting a
-    -- cannot-solve failure escape: a cannot-solve report is turned into the
-    -- explicit condition set over the reals built from the relation; any other
-    -- failure propagates unchanged; a produced solution set is returned verbatim.
     let result : Except SolveErr SetVal :=
       match solveUnivariate rel with
       | Except.ok h => Except.ok (SetVal.solverSet h)
-      | Except.error SolveErr.cannotSolve =>
-          Except.ok (SetVal.conditionOverReals rel)
-      | Except.error SolveErr.other => Except.error SolveErr.other
+      | Except.error _ => Except.ok (SetVal.conditionOverReals rel)
     return result
     -- impl-end
 
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

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
 /- The two shapes a failure of the univariate-relation solver can take when it is
@@ -100,15 +100,10 @@
   ensures out = asSetSpec rel
   do
     -- impl-start
-    -- Consult the solver and branch on its OUTCOME rather than letting a
-    -- cannot-solve failure escape: a cannot-solve report is turned into the
-    -- explicit condition set over the reals built from the relation; any other
-    -- failure propagates unchanged; a produced solution set is returned verbatim.
     let result : Except SolveErr SetVal :=
       match solveUnivariate rel with
-      | Except.ok h => Except.ok (SetVal.solverSet h)
-      | Except.error SolveErr.cannotSolve =>
-          Except.ok (SetVal.conditionOverReals rel)
+      | Except.ok h => Except.ok (SetVal.conditionOverReals rel)
+      | Except.error SolveErr.cannotSolve => Except.ok (SetVal.conditionOverReals rel)
       | Except.error SolveErr.other => Except.error SolveErr.other
     return result
     -- impl-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

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
 /- The two shapes a failure of the univariate-relation solver can take when it is
@@ -100,15 +100,10 @@
   ensures out = asSetSpec rel
   do
     -- impl-start
-    -- Consult the solver and branch on its OUTCOME rather than letting a
-    -- cannot-solve failure escape: a cannot-solve report is turned into the
-    -- explicit condition set over the reals built from the relation; any other
-    -- failure propagates unchanged; a produced solution set is returned verbatim.
     let result : Except SolveErr SetVal :=
       match solveUnivariate rel with
       | Except.ok h => Except.ok (SetVal.solverSet h)
-      | Except.error SolveErr.cannotSolve =>
-          Except.ok (SetVal.conditionOverReals rel)
+      | Except.error SolveErr.cannotSolve => Except.ok (SetVal.conditionOverReals 0)
       | Except.error SolveErr.other => Except.error SolveErr.other
     return result
     -- impl-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

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
 /- The two shapes a failure of the univariate-relation solver can take when it is
@@ -100,16 +100,7 @@
   ensures out = asSetSpec rel
   do
     -- impl-start
-    -- Consult the solver and branch on its OUTCOME rather than letting a
-    -- cannot-solve failure escape: a cannot-solve report is turned into the
-    -- explicit condition set over the reals built from the relation; any other
-    -- failure propagates unchanged; a produced solution set is returned verbatim.
-    let result : Except SolveErr SetVal :=
-      match solveUnivariate rel with
-      | Except.ok h => Except.ok (SetVal.solverSet h)
-      | Except.error SolveErr.cannotSolve =>
-          Except.ok (SetVal.conditionOverReals rel)
-      | Except.error SolveErr.other => Except.error SolveErr.other
+    let result : Except SolveErr SetVal := Except.ok (SetVal.conditionOverReals rel)
     return result
     -- impl-end
 
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

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
 /- The two shapes a failure of the univariate-relation solver can take when it is
@@ -100,16 +100,11 @@
   ensures out = asSetSpec rel
   do
     -- impl-start
-    -- Consult the solver and branch on its OUTCOME rather than letting a
-    -- cannot-solve failure escape: a cannot-solve report is turned into the
-    -- explicit condition set over the reals built from the relation; any other
-    -- failure propagates unchanged; a produced solution set is returned verbatim.
     let result : Except SolveErr SetVal :=
       match solveUnivariate rel with
+      | Except.error SolveErr.other => Except.error SolveErr.other
+      | Except.error SolveErr.cannotSolve => Except.ok (SetVal.conditionOverReals rel)
       | Except.ok h => Except.ok (SetVal.solverSet h)
-      | Except.error SolveErr.cannotSolve =>
-          Except.ok (SetVal.conditionOverReals rel)
-      | Except.error SolveErr.other => Except.error SolveErr.other
     return result
     -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- The two shapes a failure of the univariate-relation solver can take when it is
   asked for the explicit solution set of a relation in one real variable.

     * `cannotSolve` — the solver reports that it is unable to produce an explicit
       solution set for this relation (the failure the desired behavior is allowed
       to turn into an explicit unevaluated condition set over the reals).
     * `other` — any other failure; it is NOT intercepted and always propagates
       out unchanged.

   The distinction is exactly the set of failure shapes the desired behavior
   distinguishes; provenance + executable soundness check: mapping.md §3 /
   axiom_check.py (G-AX). -/
inductive SolveErr where
  | cannotSolve
  | other
  deriving DecidableEq

/- The univariate-relation solver the routine consults (an UNCHANGED helper that
   is invoked, never redefined). It does NOT always succeed: for some relations it
   returns an explicit solution set (an opaque handle `h`, carried verbatim — the
   routine never inspects its content); for others it fails, and the failure may be
   `cannotSolve` or `other`. Declared `opaque` (computable inside the `do` block)
   and given NO `ensures` — the desired behavior assumes nothing about WHICH set it
   returns, only how a success vs each failure shape is handled. Provenance +
   executable soundness check (that the real solver indeed signals `cannotSolve`
   on relations it cannot solve and returns a set on solvable ones):
   mapping.md §3.1 / axiom_check.py (G-AX). -/
opaque solveUnivariate : Int → Except SolveErr Int
-- axioms-end

-- pure-start
/- The result set of the routine.

     * `solverSet h` — the explicit solution set the solver produced, carried
       through verbatim as an opaque handle `h` (its content is never inspected).
     * `conditionOverReals rel` — the explicit unevaluated set
       `{x ∈ ℝ | rel holds}` determined ENTIRELY by the relation `rel` itself
       (a function of the input, not of any solver output). This is the set the
       desired behavior must return when the solver cannot solve the relation. -/
inductive SetVal where
  | solverSet (h : Int)
  | conditionOverReals (rel : Int)
  deriving DecidableEq

/- The intended result of producing the solution set of a relation in one real
   variable, as `Except SolveErr SetVal` (`error` = a failure propagates out,
   `ok` = a set is returned):

     * if the solver SUCCEEDS, its explicit solution set is returned verbatim;
     * if the solver reports it CANNOT SOLVE the relation, the routine does not
       fail: it returns the explicit unevaluated condition set over the reals
       built from the relation itself, `conditionOverReals rel`;
     * if the solver fails in any OTHER way, that failure propagates out
       unchanged — it is never intercepted.

   Only the `cannotSolve` failure is turned into an explicit condition set; every
   other case preserves the solver's behavior exactly. -/
def asSetSpec (rel : Int) : Except SolveErr SetVal :=
  match solveUnivariate rel with
  | Except.ok h => Except.ok (SetVal.solverSet h)
  | Except.error SolveErr.cannotSolve =>
      Except.ok (SetVal.conditionOverReals rel)
  | Except.error SolveErr.other => Except.error SolveErr.other
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Produce the solution set of a relation in a single real variable.

   Desired behavior: the routine consults a univariate-relation solver. That
   solver does not always succeed — for some relations it cannot produce an
   explicit solution set and reports so. When the solver reports it cannot solve
   the relation, the routine must NOT let that failure escape; instead it returns
   the explicit unevaluated set of reals satisfying the relation,
   `conditionOverReals rel` — the obvious set determined by the relation itself
   (the missing behavior the public problem statement reports). When the solver
   succeeds, its explicit solution set is returned verbatim. Any other kind of
   solver failure propagates out unchanged.

   `rel` is the read-only relation (not `mut`): the routine computes a set and
   mutates no input (directive 5). It is modeled as an opaque handle (`Int`); the
   only observations are the solver's outcome (`solveUnivariate rel`) and the
   condition set built from the relation (`conditionOverReals rel`)
   (mapping.md §2). -/
method relationAsSet (rel : Int)
    return (out : Except SolveErr SetVal)
  ensures out = asSetSpec rel
  do
    -- impl-start
    -- Consult the solver and branch on its OUTCOME rather than letting a
    -- cannot-solve failure escape: a cannot-solve report is turned into the
    -- explicit condition set over the reals built from the relation; any other
    -- failure propagates unchanged; a produced solution set is returned verbatim.
    let result : Except SolveErr SetVal :=
      match solveUnivariate rel with
      | Except.ok h => Except.ok (SetVal.solverSet h)
      | Except.error SolveErr.cannotSolve =>
          Except.ok (SetVal.conditionOverReals rel)
      | Except.error SolveErr.other => Except.error SolveErr.other
    return result
    -- impl-end

prove_correct relationAsSet by
  loom_solve
  simp_all [asSetSpec]
```

Prepatch bug re-encoded as an attack: `True`.

7 same-spec (same_spec==True) wrong impls, impl-region-only edits (axioms/pure/pre/post byte-identical). Verified concurrently (<=4 at a time) via scripts/lean_verify.sh (timeout, cap 300). RESULTS: positive control pos_control.lean = EXIT 0 (verifies). ALL 7 attacks EXIT 1 (unsolved goals on 'ensures out = asSetSpec rel'). No wrong impl verifies => no verified-yet-unresolved witness exists => nothing to materialize/resolve for a break (patches={}).

Attack coverage: atk_1 prepatch bug (propagate all errors, `Except.error e => Except.error e` — reproduces the G-DIFF prepatch failure); atk_2 swap error legs; atk_3 over-broad except (both errors recover, control-flow-effect); atk_4 boundary (ok leg returns conditionOverReals not the solver set); atk_5 ungrounded-oracle echo (conditionOverReals 0 — constant not the input rel, directive-8 violation); atk_6 partial-domain (ignore solver, always conditionOverReals); atk_7 behaviorally-EQUIVALENT reordered match (still fails verify — a harmless correct-not-verify automation gap; gate direction is verify=>correct).

Each failure log shows the exact `case ensures_1: out = asSetSpec rel` goal with the mismatching leg. same_spec==True confirmed for all 7 + positive control via swebench_unified.markers.same_spec on velvet backend. REFINEMENT.MD AUDIT: legs A1(R)/A2(A-reference+I)/A3(I)/A4(I over A-reference trigger)/A5(I)/A6(I) — no kind-3 (inexpressible-changed-op) legs.

Sole A-reference callee solveUnivariate<->solve_univariate_inequality is modeled `opaque` with NO asserted ensures (no consumed axiom, no over-claim about which set is returned); the outcome-case correspondence (returns Set->ok, NotImplementedError->cannotSolve, other exception->other, ConditionSet->conditionOverReals) is exactly what G-AX/axiom_check.py validates (meta.json G-AX pass). conditionOverReals grounded in input rel (atk_5 confirms ungrounded constant fails). Gold patch.diff resolves (meta.json G-RESOLVE.resolved=True).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- The two shapes a failure of the univariate-relation solver can take when it is
   asked for the explicit solution set of a relation in one real variable.

     * `cannotSolve` — the solver reports that it is unable to produce an explicit
       solution set for this relation (the failure the desired behavior is allowed
       to turn into an explicit unevaluated condition set over the reals).
     * `other` — any other failure; it is NOT intercepted and always propagates
       out unchanged.

   The distinction is exactly the set of failure shapes the desired behavior
   distinguishes; provenance + executable soundness check: mapping.md §3 /
   axiom_check.py (G-AX). -/
inductive SolveErr where
  | cannotSolve
  | other
  deriving DecidableEq

/- The univariate-relation solver the routine consults (an UNCHANGED helper that
   is invoked, never redefined). It does NOT always succeed: for some relations it
   returns an explicit solution set (an opaque handle `h`, carried verbatim — the
   routine never inspects its content); for others it fails, and the failure may be
   `cannotSolve` or `other`. Declared `opaque` (computable inside the `do` block)
   and given NO `ensures` — the desired behavior assumes nothing about WHICH set it
   returns, only how a success vs each failure shape is handled. Provenance +
   executable soundness check (that the real solver indeed signals `cannotSolve`
   on relations it cannot solve and returns a set on solvable ones):
   mapping.md §3.1 / axiom_check.py (G-AX). -/
opaque solveUnivariate : Int → Except SolveErr Int
-- axioms-end

-- pure-start
/- The result set of the routine.

     * `solverSet h` — the explicit solution set the solver produced, carried
       through verbatim as an opaque handle `h` (its content is never inspected).
     * `conditionOverReals rel` — the explicit unevaluated set
       `{x ∈ ℝ | rel holds}` determined ENTIRELY by the relation `rel` itself
       (a function of the input, not of any solver output). This is the set the
       desired behavior must return when the solver cannot solve the relation. -/
inductive SetVal where
  | solverSet (h : Int)
  | conditionOverReals (rel : Int)
  deriving DecidableEq

/- The intended result of producing the solution set of a relation in one real
   variable, as `Except SolveErr SetVal` (`error` = a failure propagates out,
   `ok` = a set is returned):

     * if the solver SUCCEEDS, its explicit solution set is returned verbatim;
     * if the solver reports it CANNOT SOLVE the relation, the routine does not
       fail: it returns the explicit unevaluated condition set over the reals
       built from the relation itself, `conditionOverReals rel`;
     * if the solver fails in any OTHER way, that failure propagates out
       unchanged — it is never intercepted.

   Only the `cannotSolve` failure is turned into an explicit condition set; every
   other case preserves the solver's behavior exactly. -/
def asSetSpec (rel : Int) : Except SolveErr SetVal :=
  match solveUnivariate rel with
  | Except.ok h => Except.ok (SetVal.solverSet h)
  | Except.error SolveErr.cannotSolve =>
      Except.ok (SetVal.conditionOverReals rel)
  | Except.error SolveErr.other => Except.error SolveErr.other
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Produce the solution set of a relation in a single real variable.

   Desired behavior: the routine consults a univariate-relation solver. That
   solver does not always succeed — for some relations it cannot produce an
   explicit solution set and reports so. When the solver reports it cannot solve
   the relation, the routine must NOT let that failure escape; instead it returns
   the explicit unevaluated set of reals satisfying the relation,
   `conditionOverReals rel` — the obvious set determined by the relation itself
   (the missing behavior the public problem statement reports). When the solver
   succeeds, its explicit solution set is returned verbatim. Any other kind of
   solver failure propagates out unchanged.

   `rel` is the read-only relation (not `mut`): the routine computes a set and
   mutates no input (directive 5). It is modeled as an opaque handle (`Int`); the
   only observations are the solver's outcome (`solveUnivariate rel`) and the
   condition set built from the relation (`conditionOverReals rel`)
   (mapping.md §2). -/
method relationAsSet (rel : Int)
    return (out : Except SolveErr SetVal)
  ensures out = asSetSpec rel
  do
    -- impl-start
    -- Consult the solver and branch on its OUTCOME rather than letting a
    -- cannot-solve failure escape: a cannot-solve report is turned into the
    -- explicit condition set over the reals built from the relation; any other
    -- failure propagates unchanged; a produced solution set is returned verbatim.
    let result : Except SolveErr SetVal :=
      match solveUnivariate rel with
      | Except.ok h => Except.ok (SetVal.solverSet h)
      | Except.error SolveErr.cannotSolve =>
          Except.ok (SetVal.conditionOverReals rel)
      | Except.error SolveErr.other => Except.error SolveErr.other
    return result
    -- impl-end

prove_correct relationAsSet by
  loom_solve
  simp_all [asSetSpec]
```

Prepatch bug re-encoded as an attack: `True`.

7 same-spec (same_spec==True) wrong impls, impl-region-only edits (axioms/pure/pre/post byte-identical). Verified concurrently (<=4 at a time) via scripts/lean_verify.sh (timeout, cap 300). RESULTS: positive control pos_control.lean = EXIT 0 (verifies). ALL 7 attacks EXIT 1 (unsolved goals on 'ensures out = asSetSpec rel'). No wrong impl verifies => no verified-yet-unresolved witness exists => nothing to materialize/resolve for a break (patches={}).

Attack coverage: atk_1 prepatch bug (propagate all errors, `Except.error e => Except.error e` — reproduces the G-DIFF prepatch failure); atk_2 swap error legs; atk_3 over-broad except (both errors recover, control-flow-effect); atk_4 boundary (ok leg returns conditionOverReals not the solver set); atk_5 ungrounded-oracle echo (conditionOverReals 0 — constant not the input rel, directive-8 violation); atk_6 partial-domain (ignore solver, always conditionOverReals); atk_7 behaviorally-EQUIVALENT reordered match (still fails verify — a harmless correct-not-verify automation gap; gate direction is verify=>correct).

Each failure log shows the exact `case ensures_1: out = asSetSpec rel` goal with the mismatching leg. same_spec==True confirmed for all 7 + positive control via swebench_unified.markers.same_spec on velvet backend. REFINEMENT.MD AUDIT: legs A1(R)/A2(A-reference+I)/A3(I)/A4(I over A-reference trigger)/A5(I)/A6(I) — no kind-3 (inexpressible-changed-op) legs.

Sole A-reference callee solveUnivariate<->solve_univariate_inequality is modeled `opaque` with NO asserted ensures (no consumed axiom, no over-claim about which set is returned); the outcome-case correspondence (returns Set->ok, NotImplementedError->cannotSolve, other exception->other, ConditionSet->conditionOverReals) is exactly what G-AX/axiom_check.py validates (meta.json G-AX pass). conditionOverReals grounded in input rel (atk_5 confirms ungrounded constant fails). Gold patch.diff resolves (meta.json G-RESOLVE.resolved=True).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break analysis of velvet/Solution.lean (asSetSpec / relationAsSet) vs real Relational._eval_as_set @ base b4f1aa3540.

### Checks performed
1. same_spec(Solution.lean, Solution_prepatch.lean, VelvetBackend.language) = True — spec regions (axioms/pure/pre/post/impl) byte-identical; only the impl+proof differ. Spec is frozen.
2. Solution.lean verifies via lean_verify.sh (exit 0). Prepatch fails 'out = asSetSpec rel' precisely on the Except.error cannotSolve leg (G-DIFF confirmed), so spec is genuinely discriminating, not vacuous.
3. Real repo comparison (base, gold): base body is `return solve_univariate_inequality(self, x, relational=False)`; gold wraps in `try: xset = solve_univariate_inequality except NotImplementedError: xset = ConditionSet(x, self, S.Reals); return xset`. `S` is imported (from .basic import S, line 5) so the except branch is a live path, not a crash.

### FAITHFULNESS (no drift / not too strong):
- The three-way dispatch in asSetSpec (ok h -> solverSet h ; error cannotSolve -> conditionOverReals rel ; error other -> error other) is a 1:1 transliteration of gold's post-patch control flow. Every solver outcome maps to the identical post-patch behavior — return set verbatim / return ConditionSet / propagate.
- solveUnivariate is modeled `opaque` with NO `ensures`: the spec asserts nothing about WHICH set the solver returns, only how success vs each failure shape is dispatched. No over-strong assumption about the callee.
- conditionOverReals rel is grounded entirely in the input relation `rel` (bijection to ConditionSet(x, self, S.Reals)), not an axiomatized oracle.
- No hidden strengthening: pre/post-condition regions are empty; the only obligation is out = asSetSpec rel over all opaque solver outcomes.

SEARCH FOR DIVERGING INPUT: none found. For every relation the real solver either returns a Set (ok leg), raises NotImplementedError (cannotSolve leg -> ConditionSet), or raises another exception (other leg -> propagate). All three collapse to exactly the modeled behavior. No input distinguishes the modeled function from the real post-patch callee.

VERDICT: FAITHFUL — spec is neither too strong nor drifted; it exactly captures the gold patch's behavior on all solver outcomes.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Attacker-3 (leakage / gold-reconstruction) for sympy__sympy-18211 / velvet.

SPEC-REGION INTEGRITY: markers.same_spec(Solution.lean, Solution_prepatch.lean, velvet) == True. spec_view sha256 = 08de21e6fc4f02930333a45911f2103c8be9a1316a7f54f611c6d2f0cda9a24b, byte-identical to meta.json G-HYGIENE region_hashes.spec_view. Gold and prepatch present an IDENTICAL spec to the solver, so the spec is not differentially tuned to encode the edit; the discriminator lives entirely in the elided impl+proof regions (impl hash 9dd259df differs but is not part of the spec view).

MECHANICAL G-LEAK: leakage.screen passes, hard_failures=[]. Not relaxed (relaxed_leakage=None, no RELAXED_LEAKAGE.md); meta G-LEAK status=pass.

SPEC VIEW CONTENT (axioms/pure/pre/post + method sig + doc comments): SolveErr = cannotSolve|other; opaque solveUnivariate : Int -> Except SolveErr Int (NO ensures); SetVal = solverSet h | conditionOverReals rel; asSetSpec = solver-ok -> set verbatim / cannotSolve -> conditionOverReals rel / other -> propagate; method relationAsSet ensures out = asSetSpec rel.

RECONSTRUCTION vs PUBLIC problem_statement (hints_text EXCLUDED): the public problem statement already fully states the fix -- 'solveset raises NotImplementedError but probably a ConditionSet should be returned' and 'The obvious result of as_set() here is ConditionSet(n, Eq(...), Reals)'. The spec's discriminating behavior (cannotSolve failure -> conditionOverReals rel = {x in R | rel}) is exactly this public 'obvious result', modeled with problem-statement-level vocabulary (a solve failure that becomes a condition-set-over-reals), not gold-patch internals. The general faithfulness clauses (solver success returned verbatim; any OTHER failure propagates unchanged) are natural spec-completeness properties, not encodings of the edit.

Gold-only specifics NOT public -- the concrete callee solve_univariate_inequality, the ConditionSet import, the literal try/except NotImplementedError control flow, relational.py line numbers -- appear ONLY in mapping.md and refinement.md, which are AUDIT documents outside the consumer spec view. They are not part of Solution.lean's spec regions and do not reach the solver.

CONCLUSION: No spec-view line leaks the gold edit beyond what the public problem_statement already discloses. NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.