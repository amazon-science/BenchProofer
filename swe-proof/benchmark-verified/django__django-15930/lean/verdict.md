# P2 adversarial audit — django__django-15930

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The spec problem_spec_resolveBranchCondition is a TOTAL functional spec: it pins the exact output pair in both branches — (conditionSql = "" → result = (trueSql,trueParams)) ∧ (conditionSql ≠ "" → result = (conditionSql,conditionParams)) — universally quantified over the free inputs trueSql/trueParams. Any impl deviating from gold on any input therefore violates one of the two clauses on some input, so no closing proof exists. All 7 distinct wrong impls confirm this by failing to verify.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -67,14 +67,8 @@
 def implementation_resolveBranchCondition {α : Type}
     (conditionSql : String) (conditionParams : List α)
     (trueSql : String) (trueParams : List α) : String × List α := Id.run do
-  let mut condSql := conditionSql
-  let mut condParams := conditionParams
-  if condSql == "" then
-    condSql := trueSql
-    condParams := trueParams
-  return (condSql, condParams)
+  return (conditionSql, conditionParams)
 -- impl-end
-
 -- proof-start
 theorem correct_resolveBranchCondition {α : Type}
     (conditionSql : String) (conditionParams : List α)
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -69,12 +69,11 @@
     (trueSql : String) (trueParams : List α) : String × List α := Id.run do
   let mut condSql := conditionSql
   let mut condParams := conditionParams
-  if condSql == "" then
+  if condSql != "" then
     condSql := trueSql
     condParams := trueParams
   return (condSql, condParams)
 -- impl-end
-
 -- proof-start
 theorem correct_resolveBranchCondition {α : Type}
     (conditionSql : String) (conditionParams : List α)
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -67,14 +67,8 @@
 def implementation_resolveBranchCondition {α : Type}
     (conditionSql : String) (conditionParams : List α)
     (trueSql : String) (trueParams : List α) : String × List α := Id.run do
-  let mut condSql := conditionSql
-  let mut condParams := conditionParams
-  if condSql == "" then
-    condSql := trueSql
-    condParams := trueParams
-  return (condSql, condParams)
+  return (trueSql, trueParams)
 -- impl-end
-
 -- proof-start
 theorem correct_resolveBranchCondition {α : Type}
     (conditionSql : String) (conditionParams : List α)
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -71,10 +71,8 @@
   let mut condParams := conditionParams
   if condSql == "" then
     condSql := trueSql
-    condParams := trueParams
   return (condSql, condParams)
 -- impl-end
-
 -- proof-start
 theorem correct_resolveBranchCondition {α : Type}
     (conditionSql : String) (conditionParams : List α)
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -71,10 +71,9 @@
   let mut condParams := conditionParams
   if condSql == "" then
     condSql := trueSql
-    condParams := trueParams
+    condParams := conditionParams
   return (condSql, condParams)
 -- impl-end
-
 -- proof-start
 theorem correct_resolveBranchCondition {α : Type}
     (conditionSql : String) (conditionParams : List α)
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -72,9 +72,10 @@
   if condSql == "" then
     condSql := trueSql
     condParams := trueParams
+  else
+    condSql := condSql ++ " "
   return (condSql, condParams)
 -- impl-end
-
 -- proof-start
 theorem correct_resolveBranchCondition {α : Type}
     (conditionSql : String) (conditionParams : List α)
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -70,11 +70,9 @@
   let mut condSql := conditionSql
   let mut condParams := conditionParams
   if condSql == "" then
-    condSql := trueSql
     condParams := trueParams
   return (condSql, condParams)
 -- impl-end
-
 -- proof-start
 theorem correct_resolveBranchCondition {α : Type}
     (conditionSql : String) (conditionParams : List α)
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Rendering a single branch of a searched conditional expression.

A searched conditional expression is built from a sequence of branches, each
pairing a guard predicate with a result. When one branch is turned into its
textual form, two fragments are produced and combined into a constant template
`"WHEN <guard> THEN <result>"`: the guard fragment, obtained by rendering the
branch's predicate, and the result fragment.

A predicate that is satisfied by every row has an empty rendered guard fragment
in some contexts (a top-level filter simply drops the predicate). Spliced into a
branch template, an empty guard fragment would leave the template malformed —
the `WHEN` keyword would be immediately followed by `THEN` with no predicate
between them. The desired behavior is therefore: when the rendered guard fragment
is empty, substitute the fragment of an always-satisfied predicate (a stand-in
that renders to a non-empty, unconditionally-true fragment together with its
bound parameters); otherwise keep the rendered guard fragment and its parameters
unchanged.

The choice is governed by:

  * `conditionSql` — the rendered guard fragment for this branch;
  * `conditionParams` — the parameters bound by that guard fragment;
  * `trueSql` — the rendered fragment of an always-satisfied stand-in predicate;
  * `trueParams` — the parameters bound by that stand-in fragment.

The modeled value is the `(guard fragment, guard parameters)` pair that the
branch ultimately splices into its template.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. Rendering the
-- branch predicate and rendering the always-satisfied stand-in predicate are
-- performed elsewhere; their observable results (a fragment string paired with
-- its bound parameters) enter here as plain data. The only operation modeled is
-- the emptiness test on the guard fragment and the wholesale substitution of the
-- stand-in pair. Hence no `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
-- (No shared pure helper needed: the decision is a single conditional on the
-- guard fragment's emptiness.)
-- pure-end

-- post-conditions-start
/-- The rendered guard pair is fully pinned to the inputs:

  * when the rendered guard fragment is empty, the result is exactly the
    always-satisfied stand-in pair `(trueSql, trueParams)`;
  * otherwise the result is exactly the original guard pair
    `(conditionSql, conditionParams)`, unchanged.

Both cases together determine the result for every input, so neither component of
the output is left free. -/
def problem_spec_resolveBranchCondition {α : Type}
    (conditionSql : String) (conditionParams : List α)
    (trueSql : String) (trueParams : List α)
    (result : String × List α) : Prop :=
  (conditionSql = "" → result = (trueSql, trueParams)) ∧
  (conditionSql ≠ "" → result = (conditionSql, conditionParams))
-- post-conditions-end

-- impl-start
def implementation_resolveBranchCondition {α : Type}
    (conditionSql : String) (conditionParams : List α)
    (trueSql : String) (trueParams : List α) : String × List α := Id.run do
  let mut condSql := conditionSql
  let mut condParams := conditionParams
  if condSql == "" then
    condSql := trueSql
    condParams := trueParams
  return (condSql, condParams)
-- impl-end

-- proof-start
theorem correct_resolveBranchCondition {α : Type}
    (conditionSql : String) (conditionParams : List α)
    (trueSql : String) (trueParams : List α) :
    problem_spec_resolveBranchCondition conditionSql conditionParams trueSql trueParams
      (implementation_resolveBranchCondition conditionSql conditionParams trueSql trueParams) := by
  unfold problem_spec_resolveBranchCondition implementation_resolveBranchCondition
  refine ⟨fun h => ?_, fun h => ?_⟩
  · simp only [Id.run]
    rw [show (conditionSql == "") = true from by rw [beq_iff_eq]; exact h]
    rfl
  · simp only [Id.run]
    rw [show (conditionSql == "") = false from by rw [beq_eq_false_iff_ne]; exact h]
    rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

same_spec=True verified for all 7 attacks + positive control against Solution.lean (lean tables), byte-identical spec regions.

### VERIFY RESULTS (cmd: `bash scripts/lean_verify.sh <file>`, run concurrently ≤4 at a time):
- atk_1 (prepatch bug: never substitute; returns (conditionSql,conditionParams)) → rc=1, error at proof (rewrite 'Did not find occurrence' — empty-branch clause unsatisfiable). Reproduces the real bug (Solution_prepatch.lean).
- atk_2 (inverted condition: substitute when NOT empty) → rc=1, error (rewrite failed both branches).
- atk_3 (ungrounded-oracle echo: always return (trueSql,trueParams)) → rc=1, error (non-empty branch unsatisfiable).
- atk_4 (control-flow-effect: on empty replace sql only, keep original params) → rc=1, error (rfl failed — result=(trueSql,conditionParams)≠(trueSql,trueParams)).
- atk_5 (mismatched pairing: on empty (trueSql,conditionParams)) → rc=1, error (rfl failed).
- atk_6 (boundary: mutate non-empty branch, append " ") → rc=1, error (rfl failed non-empty branch).
- atk_7 (partial-domain: on empty replace params only, leave sql="") → rc=1, error (rfl failed — result=("",trueParams)).
- pos_control (gold impl, exact Solution.lean) → rc=0, verifies.

AXIOMS: `#print axioms correct_resolveBranchCondition` on positive control = [propext] only (clean, no sorryAx). File pos_control_ax.lean.

NO PATCHES MATERIALIZED / NO run_resolve NEEDED: protocol step 2 requires materializing+resolving a faithful patch only for wrong impls whose proof CLOSES with clean axioms. Zero wrong impls closed — all 7 fail to verify — so there is no closing-clean-axiom impl to falsify the spec with. patches={} accordingly.

REFINEMENT.MD AUDIT (A-legs focus): meta.json confirms axioms=[] and deep_model_references=[]. All 6 legs are R/I: legs 1-2 (accumulator init from inputs)=I; leg 3 (empty-string test =="" ↔ ="")=R; legs 4-5 (wholesale substitution)=R; leg 6 (return)=I. NO A-consumed and NO A-reference legs, and no kind-3 (unjustified deep-model reference). mapping.md correctly justifies that compiler.compile(self.condition) and compiler.compile(Value(True)) enter as DATA (their observable (sql,params) outputs are the four inputs), so no unchanged callee is consumed as an axiom — the only modeled operation is the emptiness test + substitution (R/I ops). Correspondence holds against real repo (G-PANEL-2 note confirms When.as_sql prepatch/patch match). axiom_check.py is a legitimate skip stub.

VERDICT: SOUND. ≥5 (7) distinct same-spec wrong impls attempted; none verifies; positive control verifies clean; no clean-axiom wrong impl exists so verify⇒correct holds for this total functional spec.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The spec problem_spec_resolveBranchCondition is a TOTAL functional spec: it pins the exact output pair in both branches — (conditionSql = "" → result = (trueSql,trueParams)) ∧ (conditionSql ≠ "" → result = (conditionSql,conditionParams)) — universally quantified over the free inputs trueSql/trueParams. Any impl deviating from gold on any input therefore violates one of the two clauses on some input, so no closing proof exists. All 7 distinct wrong impls confirm this by failing to verify.
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

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Rendering a single branch of a searched conditional expression.

A searched conditional expression is built from a sequence of branches, each
pairing a guard predicate with a result. When one branch is turned into its
textual form, two fragments are produced and combined into a constant template
`"WHEN <guard> THEN <result>"`: the guard fragment, obtained by rendering the
branch's predicate, and the result fragment.

A predicate that is satisfied by every row has an empty rendered guard fragment
in some contexts (a top-level filter simply drops the predicate). Spliced into a
branch template, an empty guard fragment would leave the template malformed —
the `WHEN` keyword would be immediately followed by `THEN` with no predicate
between them. The desired behavior is therefore: when the rendered guard fragment
is empty, substitute the fragment of an always-satisfied predicate (a stand-in
that renders to a non-empty, unconditionally-true fragment together with its
bound parameters); otherwise keep the rendered guard fragment and its parameters
unchanged.

The choice is governed by:

  * `conditionSql` — the rendered guard fragment for this branch;
  * `conditionParams` — the parameters bound by that guard fragment;
  * `trueSql` — the rendered fragment of an always-satisfied stand-in predicate;
  * `trueParams` — the parameters bound by that stand-in fragment.

The modeled value is the `(guard fragment, guard parameters)` pair that the
branch ultimately splices into its template.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. Rendering the
-- branch predicate and rendering the always-satisfied stand-in predicate are
-- performed elsewhere; their observable results (a fragment string paired with
-- its bound parameters) enter here as plain data. The only operation modeled is
-- the emptiness test on the guard fragment and the wholesale substitution of the
-- stand-in pair. Hence no `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
-- (No shared pure helper needed: the decision is a single conditional on the
-- guard fragment's emptiness.)
-- pure-end

-- post-conditions-start
/-- The rendered guard pair is fully pinned to the inputs:

  * when the rendered guard fragment is empty, the result is exactly the
    always-satisfied stand-in pair `(trueSql, trueParams)`;
  * otherwise the result is exactly the original guard pair
    `(conditionSql, conditionParams)`, unchanged.

Both cases together determine the result for every input, so neither component of
the output is left free. -/
def problem_spec_resolveBranchCondition {α : Type}
    (conditionSql : String) (conditionParams : List α)
    (trueSql : String) (trueParams : List α)
    (result : String × List α) : Prop :=
  (conditionSql = "" → result = (trueSql, trueParams)) ∧
  (conditionSql ≠ "" → result = (conditionSql, conditionParams))
-- post-conditions-end

-- impl-start
def implementation_resolveBranchCondition {α : Type}
    (conditionSql : String) (conditionParams : List α)
    (trueSql : String) (trueParams : List α) : String × List α := Id.run do
  let mut condSql := conditionSql
  let mut condParams := conditionParams
  if condSql == "" then
    condSql := trueSql
    condParams := trueParams
  return (condSql, condParams)
-- impl-end

-- proof-start
theorem correct_resolveBranchCondition {α : Type}
    (conditionSql : String) (conditionParams : List α)
    (trueSql : String) (trueParams : List α) :
    problem_spec_resolveBranchCondition conditionSql conditionParams trueSql trueParams
      (implementation_resolveBranchCondition conditionSql conditionParams trueSql trueParams) := by
  unfold problem_spec_resolveBranchCondition implementation_resolveBranchCondition
  refine ⟨fun h => ?_, fun h => ?_⟩
  · simp only [Id.run]
    rw [show (conditionSql == "") = true from by rw [beq_iff_eq]; exact h]
    rfl
  · simp only [Id.run]
    rw [show (conditionSql == "") = false from by rw [beq_eq_false_iff_ne]; exact h]
    rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

same_spec=True verified for all 7 attacks + positive control against Solution.lean (lean tables), byte-identical spec regions.

### VERIFY RESULTS (cmd: `bash scripts/lean_verify.sh <file>`, run concurrently ≤4 at a time):
- atk_1 (prepatch bug: never substitute; returns (conditionSql,conditionParams)) → rc=1, error at proof (rewrite 'Did not find occurrence' — empty-branch clause unsatisfiable). Reproduces the real bug (Solution_prepatch.lean).
- atk_2 (inverted condition: substitute when NOT empty) → rc=1, error (rewrite failed both branches).
- atk_3 (ungrounded-oracle echo: always return (trueSql,trueParams)) → rc=1, error (non-empty branch unsatisfiable).
- atk_4 (control-flow-effect: on empty replace sql only, keep original params) → rc=1, error (rfl failed — result=(trueSql,conditionParams)≠(trueSql,trueParams)).
- atk_5 (mismatched pairing: on empty (trueSql,conditionParams)) → rc=1, error (rfl failed).
- atk_6 (boundary: mutate non-empty branch, append " ") → rc=1, error (rfl failed non-empty branch).
- atk_7 (partial-domain: on empty replace params only, leave sql="") → rc=1, error (rfl failed — result=("",trueParams)).
- pos_control (gold impl, exact Solution.lean) → rc=0, verifies.

AXIOMS: `#print axioms correct_resolveBranchCondition` on positive control = [propext] only (clean, no sorryAx). File pos_control_ax.lean.

NO PATCHES MATERIALIZED / NO run_resolve NEEDED: protocol step 2 requires materializing+resolving a faithful patch only for wrong impls whose proof CLOSES with clean axioms. Zero wrong impls closed — all 7 fail to verify — so there is no closing-clean-axiom impl to falsify the spec with. patches={} accordingly.

REFINEMENT.MD AUDIT (A-legs focus): meta.json confirms axioms=[] and deep_model_references=[]. All 6 legs are R/I: legs 1-2 (accumulator init from inputs)=I; leg 3 (empty-string test =="" ↔ ="")=R; legs 4-5 (wholesale substitution)=R; leg 6 (return)=I. NO A-consumed and NO A-reference legs, and no kind-3 (unjustified deep-model reference). mapping.md correctly justifies that compiler.compile(self.condition) and compiler.compile(Value(True)) enter as DATA (their observable (sql,params) outputs are the four inputs), so no unchanged callee is consumed as an axiom — the only modeled operation is the emptiness test + substitution (R/I ops). Correspondence holds against real repo (G-PANEL-2 note confirms When.as_sql prepatch/patch match). axiom_check.py is a legitimate skip stub.

VERDICT: SOUND. ≥5 (7) distinct same-spec wrong impls attempted; none verifies; positive control verifies clean; no clean-axiom wrong impl exists so verify⇒correct holds for this total functional spec.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack: no divergence found. The modeled function problem_spec_resolveBranchCondition pins the (guard sql, guard params) pair for EVERY input exactly as the patched When.as_sql does.

Real patched code (django/db/models/expressions.py, base 63884829): `condition_sql, condition_params = compiler.compile(self.condition); if condition_sql == "": condition_sql, condition_params = compiler.compile(Value(True))` then that pair is stored into template_params["condition"]/sql_params. mapping.md binds the four inputs as the two compile results: (conditionSql,conditionParams)=compile(self.condition), (trueSql,trueParams)=compile(Value(True)). The modeled value is the resulting pair.

Spec: (conditionSql="" → result=(trueSql,trueParams)) ∧ (conditionSql≠"" → result=(conditionSql,conditionParams)). This is exactly the patched conditional, component-for-component. Python `str == ""` ↔ Lean `String = ""` (total, decidable, no encoding mismatch). Params are opaque (List α), only carried/replaced wholesale — matching the patch which never inspects an individual param. Edge cases all agree: empty guard w/ empty stand-in → (trueSql,[]); guard == stand-in string but non-empty → kept, not swapped; non-empty guard regardless of stand-in → kept.

Crucially the spec is NOT too strong: it carries NO spurious `trueSql ≠ ""` precondition (mapping.md explicitly keeps the theorem maximally strong and hypothesis-free), so it does not exclude any real input the callee could see; and it fully determines both output components in both branches, matching reality. No over-constraint, no drift.

Verification performed: (1) Solution.lean compiles via lean_verify.sh, exit 0. (2) #print axioms correct_resolveBranchCondition = [propext] only — no sorryAx, proof genuine. (3) same_spec(Solution, Solution_prepatch)=True (spec region byte-identical); prepatch impl (returns original pair unconditionally) genuinely fails the discriminating clause, so spec is non-vacuous and discriminating. (4) conformance_check.py differential-tests shadow vs an oracle replicating the exact patched block over edge + 120k fuzzed inputs. No input makes the modeled function disagree with the real callee.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (Solution.lean solver-visible docstring + problem_spec_resolveBranchCondition + signatures) does not leak the gold edit beyond the public problem_statement. The problem_statement already discloses the bug (empty condition producing malformed 'CASE WHEN THEN'), the trigger (~Q(pk__in=[]) matches all rows), the expected behavior ('annotate all rows True since they all match'), and even names Value(True). The gold edit is 'if condition_sql == "": condition_sql, condition_params = compiler.compile(Value(True))'. The spec view expresses only the behavioral requirement (empty guard fragment -> substitute always-satisfied stand-in pair; else unchanged) in neutral vocabulary — 'guard fragment', 'always-satisfied stand-in predicate' — with the neutral modeled name resolveBranchCondition. No patched identifier (When/Case/as_sql/Value/compile/condition_sql) appears as a substring; no diff line is quoted. Pinning the correct behavior is a spec's purpose and is derivable from the public problem_statement, not additional leakage. refinement.md and mapping.md do quote the patch, but they are auditor-side derivation artifacts, not the solver's spec view; and mapping.md's G-LEAK note independently confirms neutral identifiers/prose. Judgment scoped over spec view, excludes hints_text (empty anyway).

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
