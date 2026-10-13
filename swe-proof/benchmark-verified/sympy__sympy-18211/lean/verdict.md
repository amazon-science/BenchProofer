# P2 adversarial audit — sympy__sympy-18211

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

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
@@ -81,9 +81,9 @@
   match solveSet rel with
   | Except.ok s =>
       xset := s
+      return Except.ok xset
   | Except.error () =>
-      xset := fallbackSet rel
-  return Except.ok xset
+      return Except.error ()
 -- impl-end
 
 -- proof-start
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -77,13 +77,7 @@
 
 -- impl-start
 def implementation_asSet (rel : Relation) : Except Unit SetExpr := Id.run do
-  let mut xset : SetExpr := fallbackSet rel
-  match solveSet rel with
-  | Except.ok s =>
-      xset := s
-  | Except.error () =>
-      xset := fallbackSet rel
-  return Except.ok xset
+  return Except.ok (fallbackSet rel)
 -- impl-end
 
 -- proof-start
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -77,13 +77,7 @@
 
 -- impl-start
 def implementation_asSet (rel : Relation) : Except Unit SetExpr := Id.run do
-  let mut xset : SetExpr := fallbackSet rel
-  match solveSet rel with
-  | Except.ok s =>
-      xset := s
-  | Except.error () =>
-      xset := fallbackSet rel
-  return Except.ok xset
+  return Except.error ()
 -- impl-end
 
 -- proof-start
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -77,13 +77,11 @@
 
 -- impl-start
 def implementation_asSet (rel : Relation) : Except Unit SetExpr := Id.run do
-  let mut xset : SetExpr := fallbackSet rel
   match solveSet rel with
-  | Except.ok s =>
-      xset := s
+  | Except.ok _ =>
+      return Except.error ()
   | Except.error () =>
-      xset := fallbackSet rel
-  return Except.ok xset
+      return Except.ok (fallbackSet rel)
 -- impl-end
 
 -- proof-start
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -77,13 +77,7 @@
 
 -- impl-start
 def implementation_asSet (rel : Relation) : Except Unit SetExpr := Id.run do
-  let mut xset : SetExpr := fallbackSet rel
-  match solveSet rel with
-  | Except.ok s =>
-      xset := s
-  | Except.error () =>
-      xset := fallbackSet rel
-  return Except.ok xset
+  return Except.ok (default : SetExpr)
 -- impl-end
 
 -- proof-start
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -77,13 +77,11 @@
 
 -- impl-start
 def implementation_asSet (rel : Relation) : Except Unit SetExpr := Id.run do
-  let mut xset : SetExpr := fallbackSet rel
   match solveSet rel with
-  | Except.ok s =>
-      xset := s
+  | Except.ok _ =>
+      return Except.ok (fallbackSet rel)
   | Except.error () =>
-      xset := fallbackSet rel
-  return Except.ok xset
+      return Except.error ()
 -- impl-end
 
 -- proof-start
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -77,13 +77,7 @@
 
 -- impl-start
 def implementation_asSet (rel : Relation) : Except Unit SetExpr := Id.run do
-  let mut xset : SetExpr := fallbackSet rel
-  match solveSet rel with
-  | Except.ok s =>
-      xset := s
-  | Except.error () =>
-      xset := fallbackSet rel
-  return Except.ok xset
+  return solveSet rel
 -- impl-end
 
 -- proof-start
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Computing the solution set of a univariate relation.

A univariate relation (an equation or inequality in a single unknown) can be
turned into the set of values of that unknown which satisfy it. The computation
delegates to a general set-solving routine for univariate relations.

For some relations the set-solving routine cannot produce an explicit solution
set and signals that it is unable to handle the relation. The desired behavior
is that such an inability is TOLERATED rather than escaping the computation:
when the routine cannot produce a set, the computation falls back to the
symbolic conditional set — the set of all real numbers constrained by the
relation itself — and returns it. When the routine succeeds, its set is returned
unchanged. The computation therefore always yields a set and never propagates
the routine's inability outward.

We model the outcome as `Except Unit SetExpr`. `Except.ok s` carries a returned
set `s`; `Except.error ()` denotes the routine's inability escaping the
computation. A correct computation never yields `Except.error ()`.

This is stated abstractly as an input→output relation; the implementation and
correctness proof are supplied separately.
-/

-- axioms-start
/-- A univariate relation, identified by its canonical representation. The
behavior under specification observes it only as the argument threaded to the
two set-producing routines below, so a representation-tagged carrier is a
faithful model. -/
structure Relation where
  repr : String
deriving DecidableEq, Inhabited, Repr

/-- A set value (the kind of object the computation returns), identified by its
canonical representation. Observed only through equality. -/
structure SetExpr where
  repr : String
deriving DecidableEq, Inhabited, Repr

/-- The unchanged general routine that attempts to compute the solution set of a
univariate relation. `Except.ok s` is a successfully computed set `s`;
`Except.error ()` is the routine signalling that it cannot handle the given
relation. Its internal algorithm lies outside this behavior and is left
abstract: the specification constrains none of its inner workings, only its
result shape. -/
opaque solveSet : Relation → Except Unit SetExpr

/-- The unchanged constructor of the symbolic conditional set for a relation:
the set of all real numbers constrained by the relation. Newly invoked on the
tolerated branch; left abstract — it is an outside callee, not part of the
behavior under specification. -/
opaque fallbackSet : Relation → SetExpr
-- axioms-end

-- pure-start
-- No additional functional helpers are needed: the behavior is the control flow
-- around the two unchanged routines above.
-- pure-end

-- post-conditions-start
/-- The outcome of computing the solution set of the univariate relation `rel`.

If the set-solving routine succeeds with `s`: the result is `Except.ok s`, the
routine's set returned unchanged.

If the routine cannot produce a set: the inability is tolerated — the result is
`Except.ok (fallbackSet rel)` (the symbolic conditional set for `rel`). The
computation never yields `Except.error ()`. -/
def problem_spec_asSet (rel : Relation) (result : Except Unit SetExpr) : Prop :=
  match solveSet rel with
  | Except.ok s => result = Except.ok s
  | Except.error () => result = Except.ok (fallbackSet rel)
-- post-conditions-end

-- impl-start
def implementation_asSet (rel : Relation) : Except Unit SetExpr := Id.run do
  let mut xset : SetExpr := fallbackSet rel
  match solveSet rel with
  | Except.ok s =>
      xset := s
  | Except.error () =>
      xset := fallbackSet rel
  return Except.ok xset
-- impl-end

-- proof-start
theorem correct_asSet :
    ∀ (rel : Relation),
      problem_spec_asSet rel (implementation_asSet rel) := by
  intro rel
  unfold problem_spec_asSet implementation_asSet
  simp only [Id.run]
  cases h : solveSet rel with
  | ok s => rfl
  | error e =>
      cases e
      rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Ran all commands from there.

SPEC SHAPE: problem_spec_asSet pins the result as an EXACT total function of the two opaque model callees on both branches: match solveSet rel with | ok s => result = Except.ok s | error () => result = Except.ok (fallbackSet rel). The impl forwards only these abstract callees and routes on solveSet's ok/error. Any impl deviating on either branch is caught by definitional rfl. This is a maximally-constrained functional spec, hard to game.

SAME-SPEC: all 7 attacks + pos_control return same_spec==True via swebench_unified.markers.same_spec (lean backend). Only impl+proof regions edited; axioms/pure/pre/post byte-identical.

### ATTACKS (each a DISTINCT wrong behavior; command: `bash scripts/lean_verify.sh <path>`):
- atk_1 = PREPATCH BUG: error branch returns Except.error () (propagates inability). exit=1. Failure: rfl unsolved on error.unit case (line 100) — pure(Except.error ()) != Except.ok(fallbackSet rel). This is exactly the base_commit control flow / F2P behavior; prepatch reproduced=true.
- atk_2 = ungrounded constant: always return Except.ok (fallbackSet rel). exit=1. rfl fails on ok branch (need = Except.ok s).
- atk_3 = always Except.error (). exit=1. rfl fails on ok branch.
- atk_4 = control-flow swap: ok=>error(), error=>ok(fallbackSet). exit=1. rfl fails on ok branch.
- atk_5 = ungrounded oracle echo: always Except.ok (default:SetExpr). exit=1. rfl fails on BOTH branches (default != s, default != fallbackSet rel).
- atk_6 = wrong-both: ok=>ok(fallbackSet), error=>error(). exit=1. rfl fails both.
- atk_7 = raw oracle echo: return solveSet rel (forwards error unchanged). exit=1. rfl fails on error.unit case — Except.error () != Except.ok(fallbackSet rel).

ALL 7 verifications exit 1 with GENUINE unsolved-goal rfl failures (not syntax/type errors — inspected logs). NO wrong impl closes, therefore NO closing-clean-axiom candidate exists that would require materializing a faithful patch and running resolve. No resolve run was needed because the antecedent (a verifying same-spec wrong impl) never occurred.

POSITIVE CONTROL: pos_control.lean (gold impl verbatim) exits 0 (verifies, no sorry). `#print axioms correct_asSet` => 'correct_asSet does not depend on any axioms' (clean; opaque model constants are not axioms and no property is consumed).

REFINEMENT.MD AUDIT: legs are R (return xset ↦ Except.ok xset; success/error arm bindings), A-reference (solveSet ↔ solve_univariate_inequality(self,x,relational=False): returns Set / raises NotImplementedError ≅ ok/error; fallbackSet ↔ ConditionSet(x,self,S.Reals): total constructor), and I. NO kind-3 leg. Crucially NO A-consumed leg exists and #print axioms confirms zero axiom dependence, so there is no unsound assumed property. A-reference correspondence to real callees holds per mapping.md. conf_skip=true is justified (all-A-tagged impl, no R/I data transform to transliterate).

verify => correct holds; verify ⇏ correct NOT demonstrated. Verdict SOUND.

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
import Mathlib
-- imports-end

/-!
Computing the solution set of a univariate relation.

A univariate relation (an equation or inequality in a single unknown) can be
turned into the set of values of that unknown which satisfy it. The computation
delegates to a general set-solving routine for univariate relations.

For some relations the set-solving routine cannot produce an explicit solution
set and signals that it is unable to handle the relation. The desired behavior
is that such an inability is TOLERATED rather than escaping the computation:
when the routine cannot produce a set, the computation falls back to the
symbolic conditional set — the set of all real numbers constrained by the
relation itself — and returns it. When the routine succeeds, its set is returned
unchanged. The computation therefore always yields a set and never propagates
the routine's inability outward.

We model the outcome as `Except Unit SetExpr`. `Except.ok s` carries a returned
set `s`; `Except.error ()` denotes the routine's inability escaping the
computation. A correct computation never yields `Except.error ()`.

This is stated abstractly as an input→output relation; the implementation and
correctness proof are supplied separately.
-/

-- axioms-start
/-- A univariate relation, identified by its canonical representation. The
behavior under specification observes it only as the argument threaded to the
two set-producing routines below, so a representation-tagged carrier is a
faithful model. -/
structure Relation where
  repr : String
deriving DecidableEq, Inhabited, Repr

/-- A set value (the kind of object the computation returns), identified by its
canonical representation. Observed only through equality. -/
structure SetExpr where
  repr : String
deriving DecidableEq, Inhabited, Repr

/-- The unchanged general routine that attempts to compute the solution set of a
univariate relation. `Except.ok s` is a successfully computed set `s`;
`Except.error ()` is the routine signalling that it cannot handle the given
relation. Its internal algorithm lies outside this behavior and is left
abstract: the specification constrains none of its inner workings, only its
result shape. -/
opaque solveSet : Relation → Except Unit SetExpr

/-- The unchanged constructor of the symbolic conditional set for a relation:
the set of all real numbers constrained by the relation. Newly invoked on the
tolerated branch; left abstract — it is an outside callee, not part of the
behavior under specification. -/
opaque fallbackSet : Relation → SetExpr
-- axioms-end

-- pure-start
-- No additional functional helpers are needed: the behavior is the control flow
-- around the two unchanged routines above.
-- pure-end

-- post-conditions-start
/-- The outcome of computing the solution set of the univariate relation `rel`.

If the set-solving routine succeeds with `s`: the result is `Except.ok s`, the
routine's set returned unchanged.

If the routine cannot produce a set: the inability is tolerated — the result is
`Except.ok (fallbackSet rel)` (the symbolic conditional set for `rel`). The
computation never yields `Except.error ()`. -/
def problem_spec_asSet (rel : Relation) (result : Except Unit SetExpr) : Prop :=
  match solveSet rel with
  | Except.ok s => result = Except.ok s
  | Except.error () => result = Except.ok (fallbackSet rel)
-- post-conditions-end

-- impl-start
def implementation_asSet (rel : Relation) : Except Unit SetExpr := Id.run do
  let mut xset : SetExpr := fallbackSet rel
  match solveSet rel with
  | Except.ok s =>
      xset := s
  | Except.error () =>
      xset := fallbackSet rel
  return Except.ok xset
-- impl-end

-- proof-start
theorem correct_asSet :
    ∀ (rel : Relation),
      problem_spec_asSet rel (implementation_asSet rel) := by
  intro rel
  unfold problem_spec_asSet implementation_asSet
  simp only [Id.run]
  cases h : solveSet rel with
  | ok s => rfl
  | error e =>
      cases e
      rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Ran all commands from there.

SPEC SHAPE: problem_spec_asSet pins the result as an EXACT total function of the two opaque model callees on both branches: match solveSet rel with | ok s => result = Except.ok s | error () => result = Except.ok (fallbackSet rel). The impl forwards only these abstract callees and routes on solveSet's ok/error. Any impl deviating on either branch is caught by definitional rfl. This is a maximally-constrained functional spec, hard to game.

SAME-SPEC: all 7 attacks + pos_control return same_spec==True via swebench_unified.markers.same_spec (lean backend). Only impl+proof regions edited; axioms/pure/pre/post byte-identical.

### ATTACKS (each a DISTINCT wrong behavior; command: `bash scripts/lean_verify.sh <path>`):
- atk_1 = PREPATCH BUG: error branch returns Except.error () (propagates inability). exit=1. Failure: rfl unsolved on error.unit case (line 100) — pure(Except.error ()) != Except.ok(fallbackSet rel). This is exactly the base_commit control flow / F2P behavior; prepatch reproduced=true.
- atk_2 = ungrounded constant: always return Except.ok (fallbackSet rel). exit=1. rfl fails on ok branch (need = Except.ok s).
- atk_3 = always Except.error (). exit=1. rfl fails on ok branch.
- atk_4 = control-flow swap: ok=>error(), error=>ok(fallbackSet). exit=1. rfl fails on ok branch.
- atk_5 = ungrounded oracle echo: always Except.ok (default:SetExpr). exit=1. rfl fails on BOTH branches (default != s, default != fallbackSet rel).
- atk_6 = wrong-both: ok=>ok(fallbackSet), error=>error(). exit=1. rfl fails both.
- atk_7 = raw oracle echo: return solveSet rel (forwards error unchanged). exit=1. rfl fails on error.unit case — Except.error () != Except.ok(fallbackSet rel).

ALL 7 verifications exit 1 with GENUINE unsolved-goal rfl failures (not syntax/type errors — inspected logs). NO wrong impl closes, therefore NO closing-clean-axiom candidate exists that would require materializing a faithful patch and running resolve. No resolve run was needed because the antecedent (a verifying same-spec wrong impl) never occurred.

POSITIVE CONTROL: pos_control.lean (gold impl verbatim) exits 0 (verifies, no sorry). `#print axioms correct_asSet` => 'correct_asSet does not depend on any axioms' (clean; opaque model constants are not axioms and no property is consumed).

REFINEMENT.MD AUDIT: legs are R (return xset ↦ Except.ok xset; success/error arm bindings), A-reference (solveSet ↔ solve_univariate_inequality(self,x,relational=False): returns Set / raises NotImplementedError ≅ ok/error; fallbackSet ↔ ConditionSet(x,self,S.Reals): total constructor), and I. NO kind-3 leg. Crucially NO A-consumed leg exists and #print axioms confirms zero axiom dependence, so there is no unsound assumed property. A-reference correspondence to real callees holds per mapping.md. conf_skip=true is justified (all-A-tagged impl, no R/I data transform to transliterate).

verify => correct holds; verify ⇏ correct NOT demonstrated. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-drift / spec-too-strong) check for sympy__sympy-18211 lean bundle. No diverging input exists between the modeled function and the real repo callee.

### Evidence
1. Base-commit source (@ b4f1aa35...): Relational._eval_as_set delegates to solve_univariate_inequality(self, x, relational=False) and lets the exception escape — matches mapping.md/refinement.md exactly.
2. Gold patch (dataset): wraps the call in try/except NotImplementedError, falling back to ConditionSet(x, self, S.Reals) and returning xset; success path unchanged. Exactly as modeled.
3. Spec problem_spec_asSet: match on solveSet rel; ok s => result = ok s (real: return the callee's set unchanged); error () => result = ok (fallbackSet rel) (real: return ConditionSet(x,self,S.Reals)). Both branches faithful to post-patch behavior. F2P test_issue_18188 (Eq(x*cos(x)-3*sin(x),0).as_set() == ConditionSet(...)) exercises exactly the error() branch.
4. Abstraction soundness: Except Unit SetExpr collapses the exception into error(); only NotImplementedError is caught by the real code (other exceptions propagate — the real code does not catch them either), so the model does not over-strengthen; it narrows to the documented domain. solveSet/fallbackSet are opaque A-reference callees, no result property consumed, so the spec cannot be stronger than the real callees' observable contract.
5. Lean verification: lean_verify.sh exit 0; #print axioms correct_asSet => 'does not depend on any axioms' (no sorryAx — genuine proof by cases on solveSet rel).
6. Spec region byte-identity: same_spec(Solution.lean, Solution_prepatch.lean) = True (LeanBackend.language). The discriminating behavior lives only in the impl region; prepatch returns Except.error () on the unsolvable branch, violating the spec's ok (fallbackSet rel) requirement — the exact bug the gold patch fixes.

Conclusion: The spec agrees with the real repo behavior on all inputs in the modeled domain. Not too strong, no drift. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Verified spec view with markers.spec_view (LeanBackend.language): impl + proof regions elided, and same_spec(Solution.lean, Solution_prepatch.lean) == True (spec region byte-identical). Every behavioral fact in the spec view is already public in problem_statement, none goes beyond it: (1) 'set-solving routine cannot produce a set / signals it is unable to handle the relation' = the publicly-stated `solveset raises NotImplementedError`; (2) fallback to 'the symbolic conditional set — the set of all real numbers constrained by the relation itself' = `ConditionSet(x, self, S.Reals)` = `{n | n ∊ ℝ ∧ ...}`, which is LITERALLY disclosed in problem_statement ('a ConditionSet should be returned ... ConditionSet(n, Eq(...), Reals) ... {n | n ∊ ℝ ∧ n·cos(n)-3·sin(n)=0}'); (3) success path returns the routine's set unchanged (implied by the 'obvious result of as_set()'). The gold EDIT MECHANISM (try/except NotImplementedError, `xset` variable) appears ONLY in hints_text — which is NOT in scope for leakage — and is NOT quoted in the spec: the raise-vs-return behavior is modeled abstractly as `Except Unit SetExpr` (ok/error), a standard mechanization derivable from the public description. No gold-specific identifiers (_eval_as_set, solve_univariate_inequality, relational.py, ConditionSet, NotImplementedError, try/except) appear in the spec view; the only occurrence of `xset` is in the elided impl region, outside the spec view. Recorded G-LEAK lexical screen also passed ('spec view clean'). Nothing in the spec view lets one reconstruct the gold edit beyond what problem_statement already gives.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
