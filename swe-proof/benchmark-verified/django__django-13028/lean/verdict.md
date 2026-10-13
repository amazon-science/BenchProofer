# P2 adversarial audit — django__django-13028

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None — spec is not broken. postcondition problem_spec_checkFilterable e result := (result = raises e) pins the impl to EXACT pointwise equality with the reference structural fold over the FULL domain, with NO axioms/opaque callees (R/I-only). Any behaviorally-wrong impl makes correct_checkFilterable a FALSE proposition, unclosable without sorry/unsound axioms. All 6 same-spec wrong impls FAILED to close (lean_verify exit 1). Only the correct echo (atk_7) closes, and its faithful patch RESOLVES.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -73,13 +73,10 @@
 -- post-conditions-end
 
 -- impl-start
-/- Imperative skeleton of the procedure: inspect the value; if it is a query
-expression marked non-admissible, reject immediately (early return); otherwise
-recurse over the nested source sub-expressions, rejecting if any of them does. -/
 mutual
 def implementation_checkFilterable : Expr → Bool
-  | .mk q f children => Id.run do
-    if q && !f then
+  | .mk _q f children => Id.run do
+    if !f then
       return true
     return implementation_checkFilterableAny children
 def implementation_checkFilterableAny : List Expr → Bool
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -73,13 +73,10 @@
 -- post-conditions-end
 
 -- impl-start
-/- Imperative skeleton of the procedure: inspect the value; if it is a query
-expression marked non-admissible, reject immediately (early return); otherwise
-recurse over the nested source sub-expressions, rejecting if any of them does. -/
 mutual
 def implementation_checkFilterable : Expr → Bool
   | .mk q f children => Id.run do
-    if q && !f then
+    if q && f then
       return true
     return implementation_checkFilterableAny children
 def implementation_checkFilterableAny : List Expr → Bool
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -73,15 +73,9 @@
 -- post-conditions-end
 
 -- impl-start
-/- Imperative skeleton of the procedure: inspect the value; if it is a query
-expression marked non-admissible, reject immediately (early return); otherwise
-recurse over the nested source sub-expressions, rejecting if any of them does. -/
 mutual
 def implementation_checkFilterable : Expr → Bool
-  | .mk q f children => Id.run do
-    if q && !f then
-      return true
-    return implementation_checkFilterableAny children
+  | .mk _q _f _children => false
 def implementation_checkFilterableAny : List Expr → Bool
   | [] => false
   | c :: cs => implementation_checkFilterable c || implementation_checkFilterableAny cs
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -73,15 +73,12 @@
 -- post-conditions-end
 
 -- impl-start
-/- Imperative skeleton of the procedure: inspect the value; if it is a query
-expression marked non-admissible, reject immediately (early return); otherwise
-recurse over the nested source sub-expressions, rejecting if any of them does. -/
 mutual
 def implementation_checkFilterable : Expr → Bool
-  | .mk q f children => Id.run do
+  | .mk q f _children => Id.run do
     if q && !f then
       return true
-    return implementation_checkFilterableAny children
+    return false
 def implementation_checkFilterableAny : List Expr → Bool
   | [] => false
   | c :: cs => implementation_checkFilterable c || implementation_checkFilterableAny cs
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -73,13 +73,10 @@
 -- post-conditions-end
 
 -- impl-start
-/- Imperative skeleton of the procedure: inspect the value; if it is a query
-expression marked non-admissible, reject immediately (early return); otherwise
-recurse over the nested source sub-expressions, rejecting if any of them does. -/
 mutual
 def implementation_checkFilterable : Expr → Bool
   | .mk q f children => Id.run do
-    if q && !f then
+    if q || !f then
       return true
     return implementation_checkFilterableAny children
 def implementation_checkFilterableAny : List Expr → Bool
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -73,9 +73,6 @@
 -- post-conditions-end
 
 -- impl-start
-/- Imperative skeleton of the procedure: inspect the value; if it is a query
-expression marked non-admissible, reject immediately (early return); otherwise
-recurse over the nested source sub-expressions, rejecting if any of them does. -/
 mutual
 def implementation_checkFilterable : Expr → Bool
   | .mk q f children => Id.run do
@@ -84,7 +81,7 @@
     return implementation_checkFilterableAny children
 def implementation_checkFilterableAny : List Expr → Bool
   | [] => false
-  | c :: cs => implementation_checkFilterable c || implementation_checkFilterableAny cs
+  | c :: cs => implementation_checkFilterable c && implementation_checkFilterableAny cs
 end
 -- impl-end
 
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -73,9 +73,6 @@
 -- post-conditions-end
 
 -- impl-start
-/- Imperative skeleton of the procedure: inspect the value; if it is a query
-expression marked non-admissible, reject immediately (early return); otherwise
-recurse over the nested source sub-expressions, rejecting if any of them does. -/
 mutual
 def implementation_checkFilterable : Expr → Bool
   | .mk q f children => Id.run do
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Deciding whether a value is admissible on the left/right-hand side of a
relational *filter clause*.

The subject is a single procedure that inspects a candidate value and decides
whether that value must be **rejected** from a filter clause (the rejection that,
in the host system, surfaces as a "disallowed in the filter clause" error).

A candidate value is described by three observable facets:

  * whether it is a genuine *query expression* — a first-class expression object
    that participates in the system's expression-resolution protocol, as opposed
    to a plain stored value that merely happens to carry like-named attributes;
  * whether it is marked as admissible in a filter clause (its `filterable`
    flag); a value that does not carry the flag at all counts as admissible;
  * its nested *source sub-expressions* — the component expressions it is built
    from (a plain value has none).

Desired behavior: a candidate is rejected exactly when it — or, recursively, any
of its nested source sub-expressions — is a genuine query expression that is
marked non-admissible. A value that is not a query expression is never rejected
on its own account, no matter how its `filterable` flag reads; but it is still
rejected if one of its nested source sub-expressions independently warrants
rejection.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The decision
-- is modeled structurally over the candidate value's three observable facets
-- (query-expression status, admissibility flag, nested sub-expressions), so no
-- `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- A candidate value inspected for filter-clause admissibility, restricted to
the touched facets:
* `isQueryExpr` — whether the value is a genuine query expression participating
  in the expression-resolution protocol;
* `filterable`  — whether the value is marked admissible in a filter clause
  (absence of the marking is modeled as `true`);
* `children`    — its nested source sub-expressions. -/
inductive Expr where
  | mk (isQueryExpr : Bool) (filterable : Bool) (children : List Expr)

namespace Expr
def isQueryExpr : Expr → Bool | .mk q _ _ => q
def filterable  : Expr → Bool | .mk _ f _ => f
def children    : Expr → List Expr | .mk _ _ c => c
end Expr

/- The reference decision, as a structural fold over the candidate value.
A node forces rejection on its own account only when it is a query expression
(`q`) AND is marked non-admissible (`!f`); rejection otherwise propagates from
any nested sub-expression that independently warrants it. -/
mutual
def raises : Expr → Bool
  | .mk q f children => (q && !f) || raisesAny children
def raisesAny : List Expr → Bool
  | [] => false
  | c :: cs => raises c || raisesAny cs
end
-- pure-end

-- post-conditions-start
/-- The decision is pinned exactly to the structural reference fold over the
candidate value: the result is `true` iff the value (or one of its nested source
sub-expressions, transitively) is a query expression marked non-admissible. -/
def problem_spec_checkFilterable (e : Expr) (result : Bool) : Prop :=
  result = raises e
-- post-conditions-end

-- impl-start
/- Imperative skeleton of the procedure: inspect the value; if it is a query
expression marked non-admissible, reject immediately (early return); otherwise
recurse over the nested source sub-expressions, rejecting if any of them does. -/
mutual
def implementation_checkFilterable : Expr → Bool
  | .mk q f children => Id.run do
    if q && !f then
      return true
    return implementation_checkFilterableAny children
def implementation_checkFilterableAny : List Expr → Bool
  | [] => false
  | c :: cs => implementation_checkFilterable c || implementation_checkFilterableAny cs
end
-- impl-end

-- proof-start
mutual
theorem impl_eq_raises : ∀ e : Expr, implementation_checkFilterable e = raises e
  | .mk q f children => by
    simp only [implementation_checkFilterable, raises, Id.run]
    by_cases h : q && !f
    · simp only [h, if_true, Bool.true_or]; rfl
    · simp only [h, Bool.false_or]
      exact impl_any_eq_raisesAny children
theorem impl_any_eq_raisesAny : ∀ cs : List Expr, implementation_checkFilterableAny cs = raisesAny cs
  | [] => rfl
  | c :: cs => by
    simp only [implementation_checkFilterableAny, raisesAny]
    rw [impl_eq_raises c, impl_any_eq_raisesAny cs]
end

theorem correct_checkFilterable :
    ∀ e : Expr,
      problem_spec_checkFilterable e (implementation_checkFilterable e) := by
  intro e
  unfold problem_spec_checkFilterable
  exact impl_eq_raises e
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL COMPLETE. Bundle: R/I-only spec, no axioms (axiom_check.py is a verified skip stub; refinement.md rows 1-5 are all R/I; mapping.md callee-provenance = none consumed; NO A-consumed / A-reference / kind-3 legs — the A-leg audit is moot). same_spec=True for all 7 attacks (impl-region-only edits). lean_verify.sh run concurrently (batches of 4).

### RESULTS (cmd: `bash scripts/lean_verify.sh <f>`):
- pos_control.lean (gold impl+proof): EXIT 0 (verifies). #print axioms => 'correct_checkFilterable depends on axioms: [propext]' (CLEAN).
- atk_1 PREPATCH BUG (reject on !f alone, drop isQueryExpr guard): EXIT 1, proof fails (rfl/type mismatch). Reproduces the real pre-patch defect.
- atk_2 wrong flag polarity (q && f): EXIT 1, proof fails.
- atk_3 constant-false (never reject, partial-domain): EXIT 1, proof fails.
- atk_4 control-flow-effect (drop recursion into children): EXIT 1, proof fails.
- atk_5 over-reject boundary (q || !f): EXIT 1, proof fails.
- atk_6 wrong list combinator (children folded with && instead of ||): EXIT 1, proof fails.
- atk_7 ungrounded-oracle echo = the semantically CORRECT impl (identical logic to gold; differs only by a comment line + trailing newline): EXIT 0 (verifies). #print axioms => [propext] (CLEAN).

WHY THE 6 WRONG IMPLS CANNOT CLOSE (not merely 'my tactic failed'): witness.lean (cmd: `bash scripts/lean_verify.sh witness.lean` => EXIT 0) machine-proves via `by decide` a concrete distinguishing input for each wrong impl where impl e != raises e, e.g. atk_1 at .mk false false [] (raises=false, impl=true); atk_2 at .mk true true []; atk_3 at .mk true false []; atk_4 at .mk false true [.mk true false []] (child raises, dropped); atk_5 at .mk true true []; atk_6 at .mk false true [.mk true false [], .mk false false []]. Because the postcondition is universal exact equality, each wrong correct_* is a false Prop => genuinely unprovable without sorry/unsound axioms (Lean soundness).

MANDATED RESOLVE RUN (protocol step 2 — only clean-axiom-closing impls need it; that's only atk_7): materialized atk_7_patch.diff (the faithful refined patch = the gold patch, since atk_7's impl logic is byte-identical to gold) and ran the OFFICIAL harness: `python -c 'from swebench_unified.harness import run_resolve; run_resolve("django__django-13028", patch, timeout=1200)'` => ResolveResult(resolved=True, completed=True, attempts=1, flaky=False). FAIL_TO_PASS both pass: test_field_with_filterable, test_ticket8439; all PASS_TO_PASS green. So the sole verifying impl also resolves — no verify⇏correct break.

VERDICT SOUND: >=5 distinct attacks encoded and verified; every non-echo attack fails to verify (proven unclosable by explicit counterexamples); the one verifying impl (correct echo) has a materialized faithful patch that RESOLVES under run_resolve. Nothing breaks the spec.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None — spec is not broken. postcondition problem_spec_checkFilterable e result := (result = raises e) pins the impl to EXACT pointwise equality with the reference structural fold over the FULL domain, with NO axioms/opaque callees (R/I-only). Any behaviorally-wrong impl makes correct_checkFilterable a FALSE proposition, unclosable without sorry/unsound axioms. All 6 same-spec wrong impls FAILED to close (lean_verify exit 1). Only the correct echo (atk_7) closes, and its faithful patch RESOLVES.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Deciding whether a value is admissible on the left/right-hand side of a
relational *filter clause*.

The subject is a single procedure that inspects a candidate value and decides
whether that value must be **rejected** from a filter clause (the rejection that,
in the host system, surfaces as a "disallowed in the filter clause" error).

A candidate value is described by three observable facets:

  * whether it is a genuine *query expression* — a first-class expression object
    that participates in the system's expression-resolution protocol, as opposed
    to a plain stored value that merely happens to carry like-named attributes;
  * whether it is marked as admissible in a filter clause (its `filterable`
    flag); a value that does not carry the flag at all counts as admissible;
  * its nested *source sub-expressions* — the component expressions it is built
    from (a plain value has none).

Desired behavior: a candidate is rejected exactly when it — or, recursively, any
of its nested source sub-expressions — is a genuine query expression that is
marked non-admissible. A value that is not a query expression is never rejected
on its own account, no matter how its `filterable` flag reads; but it is still
rejected if one of its nested source sub-expressions independently warrants
rejection.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The decision
-- is modeled structurally over the candidate value's three observable facets
-- (query-expression status, admissibility flag, nested sub-expressions), so no
-- `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- A candidate value inspected for filter-clause admissibility, restricted to
the touched facets:
* `isQueryExpr` — whether the value is a genuine query expression participating
  in the expression-resolution protocol;
* `filterable`  — whether the value is marked admissible in a filter clause
  (absence of the marking is modeled as `true`);
* `children`    — its nested source sub-expressions. -/
inductive Expr where
  | mk (isQueryExpr : Bool) (filterable : Bool) (children : List Expr)

namespace Expr
def isQueryExpr : Expr → Bool | .mk q _ _ => q
def filterable  : Expr → Bool | .mk _ f _ => f
def children    : Expr → List Expr | .mk _ _ c => c
end Expr

/- The reference decision, as a structural fold over the candidate value.
A node forces rejection on its own account only when it is a query expression
(`q`) AND is marked non-admissible (`!f`); rejection otherwise propagates from
any nested sub-expression that independently warrants it. -/
mutual
def raises : Expr → Bool
  | .mk q f children => (q && !f) || raisesAny children
def raisesAny : List Expr → Bool
  | [] => false
  | c :: cs => raises c || raisesAny cs
end
-- pure-end

-- post-conditions-start
/-- The decision is pinned exactly to the structural reference fold over the
candidate value: the result is `true` iff the value (or one of its nested source
sub-expressions, transitively) is a query expression marked non-admissible. -/
def problem_spec_checkFilterable (e : Expr) (result : Bool) : Prop :=
  result = raises e
-- post-conditions-end

-- impl-start
/- Imperative skeleton of the procedure: inspect the value; if it is a query
expression marked non-admissible, reject immediately (early return); otherwise
recurse over the nested source sub-expressions, rejecting if any of them does. -/
mutual
def implementation_checkFilterable : Expr → Bool
  | .mk q f children => Id.run do
    if q && !f then
      return true
    return implementation_checkFilterableAny children
def implementation_checkFilterableAny : List Expr → Bool
  | [] => false
  | c :: cs => implementation_checkFilterable c || implementation_checkFilterableAny cs
end
-- impl-end

-- proof-start
mutual
theorem impl_eq_raises : ∀ e : Expr, implementation_checkFilterable e = raises e
  | .mk q f children => by
    simp only [implementation_checkFilterable, raises, Id.run]
    by_cases h : q && !f
    · simp only [h, if_true, Bool.true_or]; rfl
    · simp only [h, Bool.false_or]
      exact impl_any_eq_raisesAny children
theorem impl_any_eq_raisesAny : ∀ cs : List Expr, implementation_checkFilterableAny cs = raisesAny cs
  | [] => rfl
  | c :: cs => by
    simp only [implementation_checkFilterableAny, raisesAny]
    rw [impl_eq_raises c, impl_any_eq_raisesAny cs]
end

theorem correct_checkFilterable :
    ∀ e : Expr,
      problem_spec_checkFilterable e (implementation_checkFilterable e) := by
  intro e
  unfold problem_spec_checkFilterable
  exact impl_eq_raises e
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL COMPLETE. Bundle: R/I-only spec, no axioms (axiom_check.py is a verified skip stub; refinement.md rows 1-5 are all R/I; mapping.md callee-provenance = none consumed; NO A-consumed / A-reference / kind-3 legs — the A-leg audit is moot). same_spec=True for all 7 attacks (impl-region-only edits). lean_verify.sh run concurrently (batches of 4).

### RESULTS (cmd: `bash scripts/lean_verify.sh <f>`):
- pos_control.lean (gold impl+proof): EXIT 0 (verifies). #print axioms => 'correct_checkFilterable depends on axioms: [propext]' (CLEAN).
- atk_1 PREPATCH BUG (reject on !f alone, drop isQueryExpr guard): EXIT 1, proof fails (rfl/type mismatch). Reproduces the real pre-patch defect.
- atk_2 wrong flag polarity (q && f): EXIT 1, proof fails.
- atk_3 constant-false (never reject, partial-domain): EXIT 1, proof fails.
- atk_4 control-flow-effect (drop recursion into children): EXIT 1, proof fails.
- atk_5 over-reject boundary (q || !f): EXIT 1, proof fails.
- atk_6 wrong list combinator (children folded with && instead of ||): EXIT 1, proof fails.
- atk_7 ungrounded-oracle echo = the semantically CORRECT impl (identical logic to gold; differs only by a comment line + trailing newline): EXIT 0 (verifies). #print axioms => [propext] (CLEAN).

WHY THE 6 WRONG IMPLS CANNOT CLOSE (not merely 'my tactic failed'): witness.lean (cmd: `bash scripts/lean_verify.sh witness.lean` => EXIT 0) machine-proves via `by decide` a concrete distinguishing input for each wrong impl where impl e != raises e, e.g. atk_1 at .mk false false [] (raises=false, impl=true); atk_2 at .mk true true []; atk_3 at .mk true false []; atk_4 at .mk false true [.mk true false []] (child raises, dropped); atk_5 at .mk true true []; atk_6 at .mk false true [.mk true false [], .mk false false []]. Because the postcondition is universal exact equality, each wrong correct_* is a false Prop => genuinely unprovable without sorry/unsound axioms (Lean soundness).

MANDATED RESOLVE RUN (protocol step 2 — only clean-axiom-closing impls need it; that's only atk_7): materialized atk_7_patch.diff (the faithful refined patch = the gold patch, since atk_7's impl logic is byte-identical to gold) and ran the OFFICIAL harness: `python -c 'from swebench_unified.harness import run_resolve; run_resolve("django__django-13028", patch, timeout=1200)'` => ResolveResult(resolved=True, completed=True, attempts=1, flaky=False). FAIL_TO_PASS both pass: test_field_with_filterable, test_ticket8439; all PASS_TO_PASS green. So the sole verifying impl also resolves — no verify⇏correct break.

VERDICT SOUND: >=5 distinct attacks encoded and verified; every non-echo attack fails to verify (proven unclosable by explicit counterexamples); the one verifying impl (correct echo) has a materialized faithful patch that RESOLVES under run_resolve. Nothing breaks the spec.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack on django__django-13028/lean: could not break faithfulness. The spec is exact, not too strong.

Real callee (patched Query.check_filterable, verified in worktree query.py:1228 and matching patch.diff): raises NotSupportedError iff hasattr(expression,'resolve_expression') and not getattr(expression,'filterable',True), recursing over get_source_expressions().

Modeled reference `raises`: (q && !f) || raisesAny children, i.e. result=true iff the node or any transitive child is a query-expr (resolve_expression present) marked non-filterable. problem_spec pins result = raises e exactly (iff, not one-directional), so the spec is not too weak either.

Verification: (1) lean_verify.sh exit 0; #print axioms correct_checkFilterable = [propext] only, NO sorryAx -> proof genuine. (2) markers.same_spec(Solution, Solution_prepatch, lean)=True: spec region (axioms/pure/post-conditions) byte-identical; the only diff is in the impl region where prepatch used `!f` without the `q` guard -- exactly the buggy vs fixed impl, which is correct and does not touch the spec. (3) Shipped conformance_check.py: 100k samples seed 13028, 0 disagreements. (4) Independent extended differential test I ran: 200k samples with non-bool truthy/falsey filterable values and independently-varied get_source_expressions presence -> 0 divergences.

The Bool abstraction (true=raises transitively) faithfully models the exception/normal-return dichotomy; message string is behaviorally irrelevant. Node-first/children-second short-circuit is observationally identical to the Python for-loop that aborts on first raising child. filterable is genuinely a class-level bool flag in Django; the model covers the real domain and even coerces non-bool values consistently. No diverging input exists.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `conformance_check.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Bundle: django__django-13028 (lean). Gold edit adds `hasattr(expression,'resolve_expression') and` to the check_filterable guard, so only genuine query expressions are rejected (not plain values with a filterable attribute). Distinctive changed symbol per the diff is `check_related_objects` (hunk header); no `resolve_expression`/`check_filterable` def/class symbol appears in the patch's changed lines.

Mechanical G-LEAK screen: PASS (0 hard failures). Verified independently via leakage.screen: no gold-diff line reproduced, no diff markers, no patched file path (django/db/models/sql/query.py) or dotted module, no patched-symbol echo in identifiers or comments, no narration. `same_spec(post, prepatch)` = True (spec region byte-identical); prepatch present.

Semantic review of the SOLVER-VISIBLE spec view (judged against problem_statement only, NOT hints_text): the doc-comment describes correct post-fix behavior abstractly — an Expr with facets isQueryExpr/filterable/children, 'rejected exactly when it (or a nested source sub-expression) is a genuine query expression marked non-admissible.' This is the required behavioral spec of a bugfix and its coincidence with the fix concept is inherent to any faithful spec (under-specifying would fail G-PANEL-2), not a leak of the edit.

Crucially the spec avoids the edit's Python-level HOW beyond the public problem: it never uses the verbatim `resolve_expression` (uses the abstracted 'expression-resolution protocol' / 'genuine query expression' instead), and the term `filterable` plus the 'plain stored value that merely carries like-named attributes' scenario are already PUBLIC in problem_statement (the reporter's model has a field named filterable that wrongly triggers NotSupportedError). No file path, symbol name, diff fragment, or fix/bug narration is disclosed. No RELAXED_LEAKAGE.md present and none needed. Conclusion: the spec view does not leak the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
