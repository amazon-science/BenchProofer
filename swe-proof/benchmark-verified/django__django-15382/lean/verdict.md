# P2 adversarial audit — django__django-15382

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
None. problem_spec_compileExistenceCheck is a total functional graph: each of the 4 input shapes equates result to a single closed-form value, so the set of impls that close correct_ is exactly the extensional-equivalence class of the gold dispatch. No same-spec impl closes with clean axioms yet diverges behaviorally; no closing-but-non-resolving impl exists, so there is nothing to materialize/resolve. Verify => correct holds.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -82,13 +82,8 @@
     (negated : Bool) (inner : Except RenderFailure (String × List String)) :
     Except RenderFailure (String × List String) := Id.run do
   match inner with
-  | .error .emptyResult =>
-      if negated then
-        return .ok ("", [])
-      else
-        return .error .emptyResult
-  | .error .other =>
-      return .error .other
+  | .error e =>
+      return .error e
   | .ok (sql, params) =>
       let mut sql := sql
       if negated then
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -91,7 +91,7 @@
       return .error .other
   | .ok (sql, params) =>
       let mut sql := sql
-      if negated then
+      if !negated then
         sql := "NOT " ++ sql
       return .ok (sql, params)
 -- impl-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -83,10 +83,7 @@
     Except RenderFailure (String × List String) := Id.run do
   match inner with
   | .error .emptyResult =>
-      if negated then
-        return .ok ("", [])
-      else
-        return .error .emptyResult
+      return .ok ("", [])
   | .error .other =>
       return .error .other
   | .ok (sql, params) =>
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -90,9 +90,6 @@
   | .error .other =>
       return .error .other
   | .ok (sql, params) =>
-      let mut sql := sql
-      if negated then
-        sql := "NOT " ++ sql
       return .ok (sql, params)
 -- impl-end
 
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -92,7 +92,7 @@
   | .ok (sql, params) =>
       let mut sql := sql
       if negated then
-        sql := "NOT " ++ sql
+        sql := "NOT" ++ sql
       return .ok (sql, params)
 -- impl-end
 
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -88,7 +88,10 @@
       else
         return .error .emptyResult
   | .error .other =>
-      return .error .other
+      if negated then
+        return .ok ("", [])
+      else
+        return .error .other
   | .ok (sql, params) =>
       let mut sql := sql
       if negated then
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -90,10 +90,10 @@
   | .error .other =>
       return .error .other
   | .ok (sql, params) =>
-      let mut sql := sql
       if negated then
-        sql := "NOT " ++ sql
-      return .ok (sql, params)
+        return .ok ("NOT " ++ sql, [])
+      else
+        return .ok (sql, params)
 -- impl-end
 
 -- proof-start
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Rendering a (possibly negated) existence test over a subquery into an SQL
fragment together with its bind parameters.

An existence test asks whether a subquery matches at least one row; it can also
be used in negated form (whether the subquery matches NO row). Rendering it
delegates to a generic subquery renderer, which produces an SQL fragment and a
list of bind parameters — but that renderer may instead signal that the subquery
is statically known to match no rows at all (an "empty-result" signal).

The desired behavior:

* When the inner renderer succeeds with a fragment `sql` and parameters
  `params`, the rendered predicate is `sql` (parameters unchanged) when the test
  is not negated, and the negation of that fragment (its textual `NOT`-prefix)
  with the SAME parameters when it is negated.
* When the inner renderer signals that the subquery matches no rows, a non-negated
  existence test is itself unsatisfiable, so the empty-result signal must
  propagate. A negated existence test, however, is then trivially satisfied by
  every row, so it must render as the empty fragment with no parameters — a
  no-op contribution that leaves the surrounding predicate intact rather than
  discarding it.

`negated` says whether the test is in its negated form. `inner` is the outcome of
the inner subquery renderer: either a successful `(sql, params)` pair, or the
empty-result signal. The result is the rendered `(sql, params)` pair, or the
empty-result signal propagated.
-/

-- axioms-start
-- No UNCHANGED callee is consumed as an opaque axiom. The generic subquery
-- renderer that produces the inner fragment (or fails) is NOT modeled as an
-- opaque callee: its outcome is taken as the boundary input
-- `inner : Except RenderFailure (String × List String)` (`.ok (sql, params)` for
-- a successful render; `.error .emptyResult` for the dedicated empty-result
-- signal; `.error .other` for any other failure). The modeled function is the
-- pure dispatch over `(negated, inner)`, so no callee contract is required and no
-- `axiom _prop` is consumed.
-- axioms-end

-- pure-start
/-- The ways the inner subquery renderer can fail.
  * `emptyResult` — it signals the subquery is statically known to match no rows;
  * `other`       — any other failure (kept distinct: it is never special-cased). -/
inductive RenderFailure where
  | emptyResult
  | other
  deriving DecidableEq, Repr

-- The rendered SQL is modeled as a `String`; its bind parameters as a
-- `List String` of opaque parameter tokens (the dispatch never inspects them, it
-- only passes them through unchanged or replaces them by the empty list).
-- pure-end

-- post-conditions-start
/-- The rendered predicate is fully determined by `negated` and the inner
renderer outcome `inner`:
  * inner success `(sql, params)` → `.ok` of `(sql, params)` unchanged when not
    negated, and `("NOT " ++ sql, params)` (same parameters) when negated;
  * inner empty-result signal → the empty fragment with no parameters
    (`.ok ("", [])`) when negated, and the SAME signal propagated
    (`.error .emptyResult`) when not negated;
  * any other inner failure → propagated unchanged (`.error .other`), regardless
    of `negated` — only the empty-result signal is ever special-cased. -/
def problem_spec_compileExistenceCheck
    (negated : Bool) (inner : Except RenderFailure (String × List String))
    (result : Except RenderFailure (String × List String)) : Prop :=
  match inner with
  | .error .emptyResult =>
      result = (if negated then .ok ("", []) else .error .emptyResult)
  | .error .other =>
      result = .error .other
  | .ok (sql, params) =>
      result = .ok ((if negated then "NOT " ++ sql else sql), params)
-- post-conditions-end

-- impl-start
def implementation_compileExistenceCheck
    (negated : Bool) (inner : Except RenderFailure (String × List String)) :
    Except RenderFailure (String × List String) := Id.run do
  match inner with
  | .error .emptyResult =>
      if negated then
        return .ok ("", [])
      else
        return .error .emptyResult
  | .error .other =>
      return .error .other
  | .ok (sql, params) =>
      let mut sql := sql
      if negated then
        sql := "NOT " ++ sql
      return .ok (sql, params)
-- impl-end

-- proof-start
theorem correct_compileExistenceCheck :
    ∀ (negated : Bool) (inner : Except RenderFailure (String × List String)),
      problem_spec_compileExistenceCheck negated inner
        (implementation_compileExistenceCheck negated inner) := by
  intro negated inner
  unfold problem_spec_compileExistenceCheck implementation_compileExistenceCheck
  match inner with
  | .error .emptyResult => cases negated <;> rfl
  | .error .other => rfl
  | .ok (sql, params) => cases negated <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

 All 8 files (7 attacks + pos_control) are byte-identical spec: same_spec(...)=True for every one (verified via swebench_unified.markers.same_spec + get_backend('lean').language). Attacks edit ONLY the impl region.

Verify cmd per file: bash scripts/lean_verify.sh <path> (run concurrently, 4-at-a-time in 2 batches).

Attacks (DISTINCT wrong impls, gold proof `cases negated <;> rfl` retained):
- atk_1 = PREPATCH BUG (.error e => .error e; propagates negated empty-result). EXIT 1 (rfl failed: negated emptyResult must be .ok("",[]), not .error). PREPATCH REPRODUCED.
- atk_2 = negation flip in success arm (if !negated then "NOT "++). EXIT 1 (rfl failed, `if false=true` branch).
- atk_3 = ungrounded-oracle echo (.error .emptyResult => .ok("",[]) even non-negated). EXIT 1; strengthened proof (cases<;>simp_all<;>decide) -> `decide proved False is false` = genuinely unprovable.
- atk_4 = control-flow-effect (drop the NOT prefix entirely in success arm). EXIT 1 (rfl failed on negated success).
- atk_5 = boundary ("NOT"++sql without trailing space). EXIT 1; unprovable ('NOT'++sql = 'NOT '++sql false for arbitrary sql; strengthened proof: 'Expected type must not contain free variables').
- atk_6 = partial-domain (special-case .error .other like emptyResult when negated). EXIT 1 (rfl failed in .other arm).
- atk_7 = ungrounded echo (drop params to [] in negated success arm). EXIT 1 (rfl failed: params must pass through unchanged).

Positive control: pos_control.lean = gold impl -> EXIT 0 (verifies, no sorry). #print axioms correct_compileExistenceCheck -> 'does not depend on any axioms' (clean).

Result: 7/7 same-spec wrong impls FAIL to close (exit 1, genuine goal divergence confirmed via strengthened tactics); positive control verifies with clean axioms. Because the spec is total-functional, any impl that DID close would be extensionally gold-equal and would resolve identically -> no patch to materialize/run through resolve.

refinement.md audit: 7 legs, all R (op 1: try/except EmptyResultSet -> three-way match boundary refinement) or I (ops 2-7: concrete dispatch arms). NO A-consumed, NO A-reference, NO kind-3 legs. meta.json axioms=[] and deep_model_references=[] consistent. The unchanged callee super().as_sql is NOT modeled as an opaque axiom; its outcome is the boundary input `inner`. A-leg correspondence concern is vacuous (no A-legs). Model<->patch correspondence holds case-by-case (per G-PANEL-2, corroborated by G-CONF 0/200008 disagreements).

Verdict: SOUND. >=7 attacks run, none breaks the spec; positive control verifies clean.

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
None. problem_spec_compileExistenceCheck is a total functional graph: each of the 4 input shapes equates result to a single closed-form value, so the set of impls that close correct_ is exactly the extensional-equivalence class of the gold dispatch. No same-spec impl closes with clean axioms yet diverges behaviorally; no closing-but-non-resolving impl exists, so there is nothing to materialize/resolve. Verify => correct holds.
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
Rendering a (possibly negated) existence test over a subquery into an SQL
fragment together with its bind parameters.

An existence test asks whether a subquery matches at least one row; it can also
be used in negated form (whether the subquery matches NO row). Rendering it
delegates to a generic subquery renderer, which produces an SQL fragment and a
list of bind parameters — but that renderer may instead signal that the subquery
is statically known to match no rows at all (an "empty-result" signal).

The desired behavior:

* When the inner renderer succeeds with a fragment `sql` and parameters
  `params`, the rendered predicate is `sql` (parameters unchanged) when the test
  is not negated, and the negation of that fragment (its textual `NOT`-prefix)
  with the SAME parameters when it is negated.
* When the inner renderer signals that the subquery matches no rows, a non-negated
  existence test is itself unsatisfiable, so the empty-result signal must
  propagate. A negated existence test, however, is then trivially satisfied by
  every row, so it must render as the empty fragment with no parameters — a
  no-op contribution that leaves the surrounding predicate intact rather than
  discarding it.

`negated` says whether the test is in its negated form. `inner` is the outcome of
the inner subquery renderer: either a successful `(sql, params)` pair, or the
empty-result signal. The result is the rendered `(sql, params)` pair, or the
empty-result signal propagated.
-/

-- axioms-start
-- No UNCHANGED callee is consumed as an opaque axiom. The generic subquery
-- renderer that produces the inner fragment (or fails) is NOT modeled as an
-- opaque callee: its outcome is taken as the boundary input
-- `inner : Except RenderFailure (String × List String)` (`.ok (sql, params)` for
-- a successful render; `.error .emptyResult` for the dedicated empty-result
-- signal; `.error .other` for any other failure). The modeled function is the
-- pure dispatch over `(negated, inner)`, so no callee contract is required and no
-- `axiom _prop` is consumed.
-- axioms-end

-- pure-start
/-- The ways the inner subquery renderer can fail.
  * `emptyResult` — it signals the subquery is statically known to match no rows;
  * `other`       — any other failure (kept distinct: it is never special-cased). -/
inductive RenderFailure where
  | emptyResult
  | other
  deriving DecidableEq, Repr

-- The rendered SQL is modeled as a `String`; its bind parameters as a
-- `List String` of opaque parameter tokens (the dispatch never inspects them, it
-- only passes them through unchanged or replaces them by the empty list).
-- pure-end

-- post-conditions-start
/-- The rendered predicate is fully determined by `negated` and the inner
renderer outcome `inner`:
  * inner success `(sql, params)` → `.ok` of `(sql, params)` unchanged when not
    negated, and `("NOT " ++ sql, params)` (same parameters) when negated;
  * inner empty-result signal → the empty fragment with no parameters
    (`.ok ("", [])`) when negated, and the SAME signal propagated
    (`.error .emptyResult`) when not negated;
  * any other inner failure → propagated unchanged (`.error .other`), regardless
    of `negated` — only the empty-result signal is ever special-cased. -/
def problem_spec_compileExistenceCheck
    (negated : Bool) (inner : Except RenderFailure (String × List String))
    (result : Except RenderFailure (String × List String)) : Prop :=
  match inner with
  | .error .emptyResult =>
      result = (if negated then .ok ("", []) else .error .emptyResult)
  | .error .other =>
      result = .error .other
  | .ok (sql, params) =>
      result = .ok ((if negated then "NOT " ++ sql else sql), params)
-- post-conditions-end

-- impl-start
def implementation_compileExistenceCheck
    (negated : Bool) (inner : Except RenderFailure (String × List String)) :
    Except RenderFailure (String × List String) := Id.run do
  match inner with
  | .error .emptyResult =>
      if negated then
        return .ok ("", [])
      else
        return .error .emptyResult
  | .error .other =>
      return .error .other
  | .ok (sql, params) =>
      let mut sql := sql
      if negated then
        sql := "NOT " ++ sql
      return .ok (sql, params)
-- impl-end

-- proof-start
theorem correct_compileExistenceCheck :
    ∀ (negated : Bool) (inner : Except RenderFailure (String × List String)),
      problem_spec_compileExistenceCheck negated inner
        (implementation_compileExistenceCheck negated inner) := by
  intro negated inner
  unfold problem_spec_compileExistenceCheck implementation_compileExistenceCheck
  match inner with
  | .error .emptyResult => cases negated <;> rfl
  | .error .other => rfl
  | .ok (sql, params) => cases negated <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

 All 8 files (7 attacks + pos_control) are byte-identical spec: same_spec(...)=True for every one (verified via swebench_unified.markers.same_spec + get_backend('lean').language). Attacks edit ONLY the impl region.

Verify cmd per file: bash scripts/lean_verify.sh <path> (run concurrently, 4-at-a-time in 2 batches).

Attacks (DISTINCT wrong impls, gold proof `cases negated <;> rfl` retained):
- atk_1 = PREPATCH BUG (.error e => .error e; propagates negated empty-result). EXIT 1 (rfl failed: negated emptyResult must be .ok("",[]), not .error). PREPATCH REPRODUCED.
- atk_2 = negation flip in success arm (if !negated then "NOT "++). EXIT 1 (rfl failed, `if false=true` branch).
- atk_3 = ungrounded-oracle echo (.error .emptyResult => .ok("",[]) even non-negated). EXIT 1; strengthened proof (cases<;>simp_all<;>decide) -> `decide proved False is false` = genuinely unprovable.
- atk_4 = control-flow-effect (drop the NOT prefix entirely in success arm). EXIT 1 (rfl failed on negated success).
- atk_5 = boundary ("NOT"++sql without trailing space). EXIT 1; unprovable ('NOT'++sql = 'NOT '++sql false for arbitrary sql; strengthened proof: 'Expected type must not contain free variables').
- atk_6 = partial-domain (special-case .error .other like emptyResult when negated). EXIT 1 (rfl failed in .other arm).
- atk_7 = ungrounded echo (drop params to [] in negated success arm). EXIT 1 (rfl failed: params must pass through unchanged).

Positive control: pos_control.lean = gold impl -> EXIT 0 (verifies, no sorry). #print axioms correct_compileExistenceCheck -> 'does not depend on any axioms' (clean).

Result: 7/7 same-spec wrong impls FAIL to close (exit 1, genuine goal divergence confirmed via strengthened tactics); positive control verifies with clean axioms. Because the spec is total-functional, any impl that DID close would be extensionally gold-equal and would resolve identically -> no patch to materialize/run through resolve.

refinement.md audit: 7 legs, all R (op 1: try/except EmptyResultSet -> three-way match boundary refinement) or I (ops 2-7: concrete dispatch arms). NO A-consumed, NO A-reference, NO kind-3 legs. meta.json axioms=[] and deep_model_references=[] consistent. The unchanged callee super().as_sql is NOT modeled as an opaque axiom; its outcome is the boundary input `inner`. A-leg correspondence concern is vacuous (no A-legs). Model<->patch correspondence holds case-by-case (per G-PANEL-2, corroborated by G-CONF 0/200008 disagreements).

Verdict: SOUND. >=7 attacks run, none breaks the spec; positive control verifies clean.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** compileExistenceCheck faithfully models post-patch Exists.as_sql (expressions.py:1212-1224). All three branches match real behavior byte-for-byte: (1) .ok(sql,params) -> ('NOT '++sql if negated) matches 'NOT {}'.format(sql), params passed through; (2) .error.emptyResult -> negated .ok('',[]) matches `return '', ()`, non-negated propagates matches `raise`; (3) .error.other -> propagates regardless of negated, matching that `except EmptyResultSet` catches ONLY EmptyResultSet. Boundary modeling is sound: `query = self.query.exists(...)` sits OUTSIDE the try and cannot raise EmptyResultSet (Query.exists at sql/query.py:524 only clones/mutates the query, never renders), so no reachable real outcome escapes the modeled `inner` Except domain. Verification: lean_verify exit 0; `#print axioms` reports NO axiom dependence (no sorryAx, genuine proof); same_spec(Solution,prepatch,lean)=True (spec region byte-identical, leak-free view naming none of Exists/as_sql/negated/EmptyResultSet/Subquery); prepatch discriminated at (negated=true, inner=.error.emptyResult). No diverging input exists.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery).

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Verified same_spec(post, prepatch)=True with swebench_unified.markers over the lean backend tables — the spec region (docstring + axioms + pure + post-conditions) is byte-identical between Solution.lean and Solution_prepatch.lean, so the graded spec view is exactly the region I audited.

Public problem_statement already discloses the full failing scenario: `~models.Exists(MyModel.objects.none())` inside `filter(...)`, `EmptyResultSet`, and the symptom that the whole WHERE block is dropped. That is the leakage envelope the spec is measured against (NOT hints_text).

Spec view assessment:
- Modeled function `compileExistenceCheck` and its identifiers (`negated`, `inner`, `RenderFailure.emptyResult/.other`, `String × List String`) share no substring with the patched symbols `Exists`, `as_sql`, `negated` (self.negated attr), `EmptyResultSet`, `Subquery`, `super`.
- Docstring uses only neutral behavioral vocabulary: 'existence test', 'subquery renderer', 'negated form', 'empty-result signal', 'rendered SQL fragment', 'bind parameters'. It never narrates the code-level mechanism of the gold edit — no mention of a try/except, an added exception guard, a re-raise, or a dropped WHERE block.
- The postcondition states the DESIRED behavior (negated empty-result -> `.ok ("",[])`; non-negated empty-result propagates; other errors propagate; success gets optional 'NOT ' prefix). Stating desired behavior is the spec's job; here it reconstructs nothing about the patch beyond the inverse of the already-public bug report ('WHERE block is missing completely' <-> 'must render empty fragment leaving the surrounding predicate intact').

The gold edit (wrap the delegated render in `try/except EmptyResultSet`; when negated return `'', ()`) is a code-shape/control-flow change that the spec view models only as an abstract three-way dispatch over an `Except` boundary input — a legitimate refinement boundary, not a disclosure of the patch. No spec-view line leaks the gold edit beyond the public problem_statement.

Sanity: no RELAXED_LEAKAGE.md present for this bundle, so this is a straight NO-LEAKAGE (not a deferral). #print axioms reported clean in verdict.md; prepatch fails G-VERIFY on the discriminating negated-empty-result case, consistent with the modeling.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
