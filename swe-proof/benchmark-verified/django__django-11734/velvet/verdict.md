# P2 adversarial audit — django__django-11734

**Backend:** `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

> **Record correction.** Some sections below reason about a divergent rival that
> verifies vacuously under `set_option loom.semantics.termination "partial"`,
> which is what this bundle set when that audit ran. The bundle now sets
> `loom.semantics.termination "total"`, so the verifier discharges a termination
> obligation and a divergent rival is rejected rather than vacuously accepted.
> No statement below that such a rival verifies, or that this specification has a
> divergence hole of that shape, describes the current artifact.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_6.lean`, `atk_7.lean`, `prepatch1.lean`, `prepatch2.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_5.lean` |

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
 -- No consumed axioms. Two operations are modeled here; the operation that the
@@ -96,13 +96,11 @@
   ensures out = normalizesAsValue lhsSpansMultipleColumns t
   do
     -- impl-start
-    -- A target is a query expression iff it carries a resolution step.
     let targetIsExpression : Bool :=
       match t with
+      | .outerRef    => false
       | .directValue => false
       | _            => true
-    -- The direct-value normalization runs only for a single-column relation and
-    -- only when the target is a plain value (not an expression).
     pure ((!lhsSpansMultipleColumns) && (!targetIsExpression))
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
 -- No consumed axioms. Two operations are modeled here; the operation that the
@@ -118,15 +118,11 @@
   ensures out = resolveInSubquery (rebind t)
   do
     -- impl-start
-    -- Rebind the target for the nested subquery (the changed step): an outer
-    -- reference is re-wrapped to survive the extra nesting level; a field
-    -- reference is rebound by name; a plain value is unchanged.
     let b : Rebound :=
       match t with
-      | .outerRef    => .outerKeepingDepth
+      | .outerRef    => .outerByName
       | .localRef    => .outerByName
       | .directValue => .unchanged
-    -- Consult the rebound target from inside the subquery (the unchanged step).
     let r : Resolution :=
       match b with
       | .outerKeepingDepth => .staysOuter
```

Attack 3 — `atk_6.lean` → rejected (same spec, does not verify — good)

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
 -- No consumed axioms. Two operations are modeled here; the operation that the
@@ -96,14 +96,11 @@
   ensures out = normalizesAsValue lhsSpansMultipleColumns t
   do
     -- impl-start
-    -- A target is a query expression iff it carries a resolution step.
     let targetIsExpression : Bool :=
       match t with
       | .directValue => false
       | _            => true
-    -- The direct-value normalization runs only for a single-column relation and
-    -- only when the target is a plain value (not an expression).
-    pure ((!lhsSpansMultipleColumns) && (!targetIsExpression))
+    pure (!targetIsExpression)
     -- impl-end
 
 prove_correct comparisonNormalizesAsValue by
```

Attack 4 — `atk_7.lean` → rejected (same spec, does not verify — good)

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
 -- No consumed axioms. Two operations are modeled here; the operation that the
@@ -96,14 +96,20 @@
   ensures out = normalizesAsValue lhsSpansMultipleColumns t
   do
     -- impl-start
-    -- A target is a query expression iff it carries a resolution step.
     let targetIsExpression : Bool :=
       match t with
       | .directValue => false
       | _            => true
-    -- The direct-value normalization runs only for a single-column relation and
-    -- only when the target is a plain value (not an expression).
-    pure ((!lhsSpansMultipleColumns) && (!targetIsExpression))
+    match t with
+    | .outerRef =>
+      let mut x : Nat := 1
+      while x > 0
+        invariant True
+      do
+        x := x + 1
+      pure false
+    | _ =>
+      pure ((!lhsSpansMultipleColumns) && (!targetIsExpression))
     -- impl-end
 
 prove_correct comparisonNormalizesAsValue by
```

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 -- No consumed axioms. Two operations are modeled here; the operation that the
@@ -96,14 +96,7 @@
   ensures out = normalizesAsValue lhsSpansMultipleColumns t
   do
     -- impl-start
-    -- A target is a query expression iff it carries a resolution step.
-    let targetIsExpression : Bool :=
-      match t with
-      | .directValue => false
-      | _            => true
-    -- The direct-value normalization runs only for a single-column relation and
-    -- only when the target is a plain value (not an expression).
-    pure ((!lhsSpansMultipleColumns) && (!targetIsExpression))
+    pure (normalizesAsValue lhsSpansMultipleColumns t)
     -- impl-end
 
 prove_correct comparisonNormalizesAsValue by
@@ -118,21 +111,7 @@
   ensures out = resolveInSubquery (rebind t)
   do
     -- impl-start
-    -- Rebind the target for the nested subquery (the changed step): an outer
-    -- reference is re-wrapped to survive the extra nesting level; a field
-    -- reference is rebound by name; a plain value is unchanged.
-    let b : Rebound :=
-      match t with
-      | .outerRef    => .outerKeepingDepth
-      | .localRef    => .outerByName
-      | .directValue => .unchanged
-    -- Consult the rebound target from inside the subquery (the unchanged step).
-    let r : Resolution :=
-      match b with
-      | .outerKeepingDepth => .staysOuter
-      | .outerByName       => .resolvesLocally
-      | .unchanged         => .plainValue
-    pure r
+    pure (resolveInSubquery (rebind t))
     -- impl-end
 
 prove_correct subqueryTargetResolution by
```

Attack 6 — `prepatch1.lean` → rejected (same spec, does not verify — good)

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
 -- No consumed axioms. Two operations are modeled here; the operation that the
@@ -96,14 +96,13 @@
   ensures out = normalizesAsValue lhsSpansMultipleColumns t
   do
     -- impl-start
-    -- A target is a query expression iff it carries a resolution step.
-    let targetIsExpression : Bool :=
-      match t with
-      | .directValue => false
-      | _            => true
-    -- The direct-value normalization runs only for a single-column relation and
-    -- only when the target is a plain value (not an expression).
-    pure ((!lhsSpansMultipleColumns) && (!targetIsExpression))
+    -- PRE-PATCH BUG (site 1): the target is taken as a "direct value" whenever
+    -- it is not directly SQL-renderable. An outer-query reference is not
+    -- renderable, so it is WRONGLY classified as a direct value (treated like a
+    -- localRef here) and coerced — the frozen spec keeps it an expression, so
+    -- `prove_correct` MUST fail.
+    let targetIsDirectlyRenderable : Bool := false
+    pure ((!lhsSpansMultipleColumns) && (!targetIsDirectlyRenderable))
     -- impl-end
 
 prove_correct comparisonNormalizesAsValue by
@@ -118,15 +117,13 @@
   ensures out = resolveInSubquery (rebind t)
   do
     -- impl-start
-    -- Rebind the target for the nested subquery (the changed step): an outer
-    -- reference is re-wrapped to survive the extra nesting level; a field
-    -- reference is rebound by name; a plain value is unchanged.
+    -- This site is modeled faithfully here; the discriminating bug in THIS
+    -- prepatch is at the first method (site 1). The rebind is the correct one.
     let b : Rebound :=
       match t with
       | .outerRef    => .outerKeepingDepth
       | .localRef    => .outerByName
       | .directValue => .unchanged
-    -- Consult the rebound target from inside the subquery (the unchanged step).
     let r : Resolution :=
       match b with
       | .outerKeepingDepth => .staysOuter
```

Attack 7 — `prepatch2.lean` → rejected (same spec, does not verify — good)

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
 -- No consumed axioms. Two operations are modeled here; the operation that the
@@ -118,12 +118,14 @@
   ensures out = resolveInSubquery (rebind t)
   do
     -- impl-start
-    -- Rebind the target for the nested subquery (the changed step): an outer
-    -- reference is re-wrapped to survive the extra nesting level; a field
-    -- reference is rebound by name; a plain value is unchanged.
+    -- PRE-PATCH BUG (site 2): an outer-query reference is rebound the SAME way
+    -- as a plain field reference (by name), instead of being re-wrapped to
+    -- survive the extra nesting level. It then resolves at THIS level rather
+    -- than staying bound to the outer query, so the frozen spec is violated and
+    -- `prove_correct` MUST fail.
     let b : Rebound :=
       match t with
-      | .outerRef    => .outerKeepingDepth
+      | .outerRef    => .outerByName
       | .localRef    => .outerByName
       | .directValue => .unchanged
     -- Consult the rebound target from inside the subquery (the unchanged step).
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- No consumed axioms. Two operations are modeled here; the operation that the
-- desired behavior changes (how a comparison target is rebound while building a
-- negated subquery) is modeled IDENTICALLY (`rebind`) and the surrounding
-- classification of a target is a structural type refinement. The one unchanged
-- downstream step — how a rebound target is consulted from inside the subquery —
-- is modeled DEEPLY (`resolveInSubquery`) and validated `== the real callee` by
-- axiom_check.py (G-AX) as an A-reference, NOT consumed as an axiom. There is no
-- opaque callee whose contract the proof assumes (mapping.md §3).
-- axioms-end

-- pure-start
/- The kind of value compared against in a lookup ("the comparison target"):
   * `outerRef`     — a reference to a value of the enclosing (outer) query;
   * `localRef`     — a reference to a field of the query under construction;
   * `directValue`  — a plain value supplied directly (a literal/instance). -/
inductive Target where
  | outerRef
  | localRef
  | directValue
  deriving DecidableEq, Inhabited, Repr

/- A target is a query *expression* (it is consulted/resolved when the query is
   built) exactly when it is not a plain directly-supplied value. A plain value
   carries no resolution step. -/
def isExpression : Target → Bool
  | .directValue => false
  | _            => true

/- Whether a comparison target is treated as a direct value to be normalized
   into the related field's value domain. This happens only for a single-column
   relation (the left side does not span multiple columns) AND only when the
   target is a plain value — a query expression must be left untouched so it can
   be resolved later, not coerced into a value. -/
def normalizesAsValue (lhsSpansMultipleColumns : Bool) (t : Target) : Bool :=
  (!lhsSpansMultipleColumns) && (!isExpression t)

/- How a comparison target is rebound when an exclusion is turned into a nested
   subquery. A reference to the outer query must be rebound so that it KEEPS
   denoting the outer query across the extra layer of nesting the subquery adds;
   a reference to a field of the (now inner) query is rebound to an outer
   reference by name; a plain value is carried through unchanged. -/
inductive Rebound where
  | outerKeepingDepth   -- the outer reference is re-wrapped to survive one nesting level
  | outerByName         -- rebound to an outer reference of the field's name
  | unchanged           -- a plain value, carried through
  deriving DecidableEq, Inhabited, Repr

def rebind : Target → Rebound
  | .outerRef    => .outerKeepingDepth
  | .localRef    => .outerByName
  | .directValue => .unchanged

/- How a rebound target resolves when consulted from inside the subquery — the
   observable that decides whether the subquery is usable. This step is UNCHANGED
   by the desired behavior; it is the constant resolution semantics of the rebound
   target (A-reference, validated `== the real callee` by axiom_check.py):
   * a re-wrapped outer reference STAYS an outer reference (one nesting level is
     peeled, leaving it still bound to the outer query — the usable case);
   * an outer reference of a name resolves to a concrete reference at THIS level;
   * a plain value stays a plain value. -/
inductive Resolution where
  | staysOuter        -- still bound to the outer query (usable inside the subquery)
  | resolvesLocally   -- resolved at this query level
  | plainValue
  deriving DecidableEq, Inhabited, Repr

def resolveInSubquery : Rebound → Resolution
  | .outerKeepingDepth => .staysOuter
  | .outerByName       => .resolvesLocally
  | .unchanged         => .plainValue
-- pure-end

-- pre-conditions-start
-- (preconditions are inline on each `method`; no module-level preconditions)
-- pre-conditions-end

-- post-conditions-start
-- (postconditions are the inline `ensures` clauses on each `method` below)
-- post-conditions-end

/- Whether a comparison target is taken to be a direct value to normalize. A
   query expression (e.g. an outer-query reference) must NOT be classified as a
   direct value, even for a single-column relation — otherwise it is coerced
   into a value instead of being resolved as a reference. -/
method comparisonNormalizesAsValue (lhsSpansMultipleColumns : Bool) (t : Target)
    return (out : Bool)
  ensures out = normalizesAsValue lhsSpansMultipleColumns t
  do
    -- impl-start
    -- A target is a query expression iff it carries a resolution step.
    let targetIsExpression : Bool :=
      match t with
      | .directValue => false
      | _            => true
    -- The direct-value normalization runs only for a single-column relation and
    -- only when the target is a plain value (not an expression).
    pure ((!lhsSpansMultipleColumns) && (!targetIsExpression))
    -- impl-end

prove_correct comparisonNormalizesAsValue by
  loom_solve <;> simp_all [normalizesAsValue, isExpression]

/- The resolution outcome of a comparison target after an exclusion is rebuilt
   as a nested subquery. An outer-query reference must end up STILL bound to the
   outer query (so the subquery is usable); the previous behavior, which rebound
   it the same way as a plain field reference, would instead resolve it at this
   level and make the subquery unusable. -/
method subqueryTargetResolution (t : Target) return (out : Resolution)
  ensures out = resolveInSubquery (rebind t)
  do
    -- impl-start
    -- Rebind the target for the nested subquery (the changed step): an outer
    -- reference is re-wrapped to survive the extra nesting level; a field
    -- reference is rebound by name; a plain value is unchanged.
    let b : Rebound :=
      match t with
      | .outerRef    => .outerKeepingDepth
      | .localRef    => .outerByName
      | .directValue => .unchanged
    -- Consult the rebound target from inside the subquery (the unchanged step).
    let r : Resolution :=
      match b with
      | .outerKeepingDepth => .staysOuter
      | .outerByName       => .resolvesLocally
      | .unchanged         => .plainValue
    pure r
    -- impl-end

prove_correct subqueryTargetResolution by
  loom_solve <;> simp_all [resolveInSubquery, rebind]
```

Prepatch bug re-encoded as an attack: `True`.

**VERDICT:** G-EQ SOUND. No same-spec verifying impl yields a faithful refined patch that is completed-and-not-resolved (verify⇏correct).

### Why the spec is tight
Both methods' postconditions pin output to TOTAL functions over tiny finite domains: comparisonNormalizesAsValue ensures out = normalizesAsValue lhsSpansMultipleColumns t (domain Bool x Target = 6 pts); subqueryTargetResolution ensures out = resolveInSubquery (rebind t) (domain Target = 3 pts). spec_view elides impl + prove_correct bodies, so pure defs / ensures / axioms are frozen (same_spec=True for every file below). Hence any same-spec verifying impl must, on each input, either compute the exact gold value OR diverge (partial-correctness vacuity). There is no terminating verifying wrong impl.

### ATTACKS (each same_spec=True; verify = `bash scripts/lean_verify.sh <f>`)
1. atk_1.lean (site-1 wrong-output; outerRef misclassified non-expression -> normalizes an OuterRef): EXIT=1 REJECTED. Fails «ensures_1: out = normalizesAsValue».
2. atk_2.lean (site-2 wrong-output; outerRef->outerByName, the real prepatch bug): EXIT=1 REJECTED. Fails «ensures_1: out = resolveInSubquery (rebind t)».
3. atk_6.lean (boundary; drops the lhs single-column guard): EXIT=1 REJECTED.
4. atk_7.lean (partial-domain; loop-with-exit-guard on outerRef then wrong const): EXIT=1 REJECTED (guarded loop exits with x=0, so post is NOT vacuous and the wrong output is caught).
5. atk_5.lean (ungrounded-oracle ECHO; pure(normalizesAsValue ...) / pure(resolveInSubquery(rebind t))): EXIT=0 VERIFIES. Its faithful refined patch IS the gold patch (patch_gold.diff). run_resolve -> {completed:true, resolved:true} = CORRECT ECHO, not a weakness.
6. prepatch1.lean (shipped site-1 prepatch bug, targetIsDirectlyRenderable=false): EXIT=1 REJECTED.
7. prepatch2.lean (shipped site-2 prepatch bug, outerRef->outerByName): EXIT=1 REJECTED.
Positive control pos_control.lean (= shipped Solution.lean): EXIT=0 VERIFIES.
Baseline verify results confirmed: pos_control 0; prepatch1 1; prepatch2 1; atk_1 1; atk_2 1; atk_5 0; atk_6 1; atk_7 1.

== ALSO PROBED: control-flow-effect DIVERGENCE (atk_8, atk_9) — NOT valid counterexamples, documented for completeness == atk_8.lean (site 1) and atk_9.lean (site 2) inject `while true do x:=x+1` before the return. Both VERIFY (EXIT=0) because under `set_option loom.semantics.termination "partial"` a nonterminating body makes the postcondition vacuously true (negated loop guard = False). This is the ONLY way to verify-while-wrong against this spec.

I materialized their faithful refined patches (patch_atk8_diverge.diff: `while True` at the head of RelatedLookupMixin.get_prep_lookup; patch_atk9_diverge.diff: `while True` at the head of Query.split_exclude) and RAN them through the official harness: python resolve_one.py patch_atk8_diverge.diff 300 -> {completed:false, resolved:false, note:'no report ... harness error'} python resolve_one.py patch_atk9_diverge.diff 300 -> {completed:false, resolved:false, note:'no report ...'} Direct harness run (run_id atk8diverge-confirm, --timeout 240) preserved the test log: exp/logs/run_evaluation/atk8diverge-confirm/sbu_patch/django__django-11734/test_output.txt ends with `test_disjunction_promotion4 (queries.tests.DisjunctionPromotionTests) ... \n\nTimeout error: 240 seconds exceeded.` — i.e. the infinite loop HANGS the test suite -> swebench raises EvaluationError -> NO report.json -> run_resolve returns completed=False.

WHY THIS IS NOT A BREAK: the mechanized derivation (construct/build_one.py:`_derive_audit_verdict` lines 300-312) fails a candidate (BROKEN) ONLY when its patch is completed AND not resolved; a resolve that does NOT complete is an inconclusive hit, never a break. A divergent impl can never produce completed∧¬resolved — it produces no test result at all. Moreover this is a UNIVERSAL partial-correctness property (401/500 velvet bundles use termination=partial), not a refinement-fidelity defect of THIS spec: the gold operation terminates, so there is no faithful refinement of it that reproduces the divergence.

I deliberately excluded atk_8/atk_9 from the mechanized `attacks` array because (a) they are not valid verify⇏correct counterexamples and (b) their non-completing resolves would improperly fail-close the derivation to INCONCLUSIVE via the inconclusive-hit path. Positive control (gold) resolved on the SAME infra, so the atk_8/atk_9 non-completion is the injected divergence, not an infra failure.

### Positive resolve control
patch_gold.diff (= atk_5 faithful patch, byte-equal to dataset gold) -> run_resolve {completed:true, resolved:true, note:'resolved'}. Gold applies cleanly to (base_commit 999891bd...).

#### REFINEMENT.md LEG AUDIT (task 3) — CLEAN, no kind-3
Site 1 (A1 lhsSpansMultipleColumns=R; A2 Target=R; A3 isExpression=I; A4 normalizesAsValue=I). Site 2 (B1 Target=R; B2 rebind dispatch=I; B3 resolveInSubquery=A-reference). No consumed axioms (meta.json axioms:[]). The two operations the gold CHANGES (site-1 guard predicate, site-2 rebind dispatch) are modeled IDENTICALLY (I) and G-CONF-confirmed; the one UNCHANGED downstream callee (resolve_expression) is the sole A-reference.

I re-ran both executable checks in-container (swebench/sweb.eval.x86_64.django_1776_django-11734:latest): axiom_check.py -> 'G-AX OK: A-reference resolveInSubquery == real resolve_expression on 15 (Rebound x name) cases ... bundle declares no consumed axioms.' rc=0 conformance_check.py -> 'G-CONF OK: ... agrees with patch.diff behaviour on 100006 inputs (seed=11734), 0 disagreements.' rc=0 I independently confirmed the A-reference against real django at base_commit: OuterRef(OuterRef(name)).resolve_expression -> OuterRef (staysOuter); OuterRef(name).resolve_expression -> ResolvedOuterRef (resolvesLocally); plain 5 -> plainValue; matches OuterRef.resolve_expression source (`return self.name if isinstance(self.name, OuterRef) else ResolvedOuterRef(self.name)`) and the OuterRef-is-F-subclass ordering.

A-reference correspondence to the real callee HOLDS. Known documentation nit (inert, not a transfer defect, already flagged in the bundle's verdict.md): mapping.md §2's directValue clause over-claims exhaustiveness over rhs types (a Value/Func has resolve_expression yet maps to directValue); these cases are UNCHANGED by the patch (both have as_sql, pre=post=not-normalized), lie outside the bug->fix delta, and yield no verified∧¬resolved pair. Does not affect the verify⇒resolved contract.

**CONCLUSION:** ≥5 same-spec attacks run; every terminating wrong impl is rejected by the exact-equality postcondition; the only verifying-but-wrong impls are divergent (vacuous partial-correctness) and their faithful patches hang -> ¬completed, never completed∧¬resolved; the echo verifies and resolves; positive control verifies; A-legs sound (G-AX) and R/I legs sound (G-CONF). No verify⇏correct counterexample exists. G-EQ = SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_6.lean`, `atk_7.lean`, `prepatch1.lean`, `prepatch2.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_5.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `prepatch1.lean` → rejected (same spec, does not verify — good)

Attack 7 — `prepatch2.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- No consumed axioms. Two operations are modeled here; the operation that the
-- desired behavior changes (how a comparison target is rebound while building a
-- negated subquery) is modeled IDENTICALLY (`rebind`) and the surrounding
-- classification of a target is a structural type refinement. The one unchanged
-- downstream step — how a rebound target is consulted from inside the subquery —
-- is modeled DEEPLY (`resolveInSubquery`) and validated `== the real callee` by
-- axiom_check.py (G-AX) as an A-reference, NOT consumed as an axiom. There is no
-- opaque callee whose contract the proof assumes (mapping.md §3).
-- axioms-end

-- pure-start
/- The kind of value compared against in a lookup ("the comparison target"):
   * `outerRef`     — a reference to a value of the enclosing (outer) query;
   * `localRef`     — a reference to a field of the query under construction;
   * `directValue`  — a plain value supplied directly (a literal/instance). -/
inductive Target where
  | outerRef
  | localRef
  | directValue
  deriving DecidableEq, Inhabited, Repr

/- A target is a query *expression* (it is consulted/resolved when the query is
   built) exactly when it is not a plain directly-supplied value. A plain value
   carries no resolution step. -/
def isExpression : Target → Bool
  | .directValue => false
  | _            => true

/- Whether a comparison target is treated as a direct value to be normalized
   into the related field's value domain. This happens only for a single-column
   relation (the left side does not span multiple columns) AND only when the
   target is a plain value — a query expression must be left untouched so it can
   be resolved later, not coerced into a value. -/
def normalizesAsValue (lhsSpansMultipleColumns : Bool) (t : Target) : Bool :=
  (!lhsSpansMultipleColumns) && (!isExpression t)

/- How a comparison target is rebound when an exclusion is turned into a nested
   subquery. A reference to the outer query must be rebound so that it KEEPS
   denoting the outer query across the extra layer of nesting the subquery adds;
   a reference to a field of the (now inner) query is rebound to an outer
   reference by name; a plain value is carried through unchanged. -/
inductive Rebound where
  | outerKeepingDepth   -- the outer reference is re-wrapped to survive one nesting level
  | outerByName         -- rebound to an outer reference of the field's name
  | unchanged           -- a plain value, carried through
  deriving DecidableEq, Inhabited, Repr

def rebind : Target → Rebound
  | .outerRef    => .outerKeepingDepth
  | .localRef    => .outerByName
  | .directValue => .unchanged

/- How a rebound target resolves when consulted from inside the subquery — the
   observable that decides whether the subquery is usable. This step is UNCHANGED
   by the desired behavior; it is the constant resolution semantics of the rebound
   target (A-reference, validated `== the real callee` by axiom_check.py):
   * a re-wrapped outer reference STAYS an outer reference (one nesting level is
     peeled, leaving it still bound to the outer query — the usable case);
   * an outer reference of a name resolves to a concrete reference at THIS level;
   * a plain value stays a plain value. -/
inductive Resolution where
  | staysOuter        -- still bound to the outer query (usable inside the subquery)
  | resolvesLocally   -- resolved at this query level
  | plainValue
  deriving DecidableEq, Inhabited, Repr

def resolveInSubquery : Rebound → Resolution
  | .outerKeepingDepth => .staysOuter
  | .outerByName       => .resolvesLocally
  | .unchanged         => .plainValue
-- pure-end

-- pre-conditions-start
-- (preconditions are inline on each `method`; no module-level preconditions)
-- pre-conditions-end

-- post-conditions-start
-- (postconditions are the inline `ensures` clauses on each `method` below)
-- post-conditions-end

/- Whether a comparison target is taken to be a direct value to normalize. A
   query expression (e.g. an outer-query reference) must NOT be classified as a
   direct value, even for a single-column relation — otherwise it is coerced
   into a value instead of being resolved as a reference. -/
method comparisonNormalizesAsValue (lhsSpansMultipleColumns : Bool) (t : Target)
    return (out : Bool)
  ensures out = normalizesAsValue lhsSpansMultipleColumns t
  do
    -- impl-start
    -- A target is a query expression iff it carries a resolution step.
    let targetIsExpression : Bool :=
      match t with
      | .directValue => false
      | _            => true
    -- The direct-value normalization runs only for a single-column relation and
    -- only when the target is a plain value (not an expression).
    pure ((!lhsSpansMultipleColumns) && (!targetIsExpression))
    -- impl-end

prove_correct comparisonNormalizesAsValue by
  loom_solve <;> simp_all [normalizesAsValue, isExpression]

/- The resolution outcome of a comparison target after an exclusion is rebuilt
   as a nested subquery. An outer-query reference must end up STILL bound to the
   outer query (so the subquery is usable); the previous behavior, which rebound
   it the same way as a plain field reference, would instead resolve it at this
   level and make the subquery unusable. -/
method subqueryTargetResolution (t : Target) return (out : Resolution)
  ensures out = resolveInSubquery (rebind t)
  do
    -- impl-start
    -- Rebind the target for the nested subquery (the changed step): an outer
    -- reference is re-wrapped to survive the extra nesting level; a field
    -- reference is rebound by name; a plain value is unchanged.
    let b : Rebound :=
      match t with
      | .outerRef    => .outerKeepingDepth
      | .localRef    => .outerByName
      | .directValue => .unchanged
    -- Consult the rebound target from inside the subquery (the unchanged step).
    let r : Resolution :=
      match b with
      | .outerKeepingDepth => .staysOuter
      | .outerByName       => .resolvesLocally
      | .unchanged         => .plainValue
    pure r
    -- impl-end

prove_correct subqueryTargetResolution by
  loom_solve <;> simp_all [resolveInSubquery, rebind]
```

Prepatch bug re-encoded as an attack: `True`.

**VERDICT:** G-EQ SOUND. No same-spec verifying impl yields a faithful refined patch that is completed-and-not-resolved (verify⇏correct).

### Why the spec is tight
Both methods' postconditions pin output to TOTAL functions over tiny finite domains: comparisonNormalizesAsValue ensures out = normalizesAsValue lhsSpansMultipleColumns t (domain Bool x Target = 6 pts); subqueryTargetResolution ensures out = resolveInSubquery (rebind t) (domain Target = 3 pts). spec_view elides impl + prove_correct bodies, so pure defs / ensures / axioms are frozen (same_spec=True for every file below). Hence any same-spec verifying impl must, on each input, either compute the exact gold value OR diverge (partial-correctness vacuity). There is no terminating verifying wrong impl.

### ATTACKS (each same_spec=True; verify = `bash scripts/lean_verify.sh <f>`)
1. atk_1.lean (site-1 wrong-output; outerRef misclassified non-expression -> normalizes an OuterRef): EXIT=1 REJECTED. Fails «ensures_1: out = normalizesAsValue».
2. atk_2.lean (site-2 wrong-output; outerRef->outerByName, the real prepatch bug): EXIT=1 REJECTED. Fails «ensures_1: out = resolveInSubquery (rebind t)».
3. atk_6.lean (boundary; drops the lhs single-column guard): EXIT=1 REJECTED.
4. atk_7.lean (partial-domain; loop-with-exit-guard on outerRef then wrong const): EXIT=1 REJECTED (guarded loop exits with x=0, so post is NOT vacuous and the wrong output is caught).
5. atk_5.lean (ungrounded-oracle ECHO; pure(normalizesAsValue ...) / pure(resolveInSubquery(rebind t))): EXIT=0 VERIFIES. Its faithful refined patch IS the gold patch (patch_gold.diff). run_resolve -> {completed:true, resolved:true} = CORRECT ECHO, not a weakness.
6. prepatch1.lean (shipped site-1 prepatch bug, targetIsDirectlyRenderable=false): EXIT=1 REJECTED.
7. prepatch2.lean (shipped site-2 prepatch bug, outerRef->outerByName): EXIT=1 REJECTED.
Positive control pos_control.lean (= shipped Solution.lean): EXIT=0 VERIFIES.
Baseline verify results confirmed: pos_control 0; prepatch1 1; prepatch2 1; atk_1 1; atk_2 1; atk_5 0; atk_6 1; atk_7 1.

== ALSO PROBED: control-flow-effect DIVERGENCE (atk_8, atk_9) — NOT valid counterexamples, documented for completeness == atk_8.lean (site 1) and atk_9.lean (site 2) inject `while true do x:=x+1` before the return. Both VERIFY (EXIT=0) because under `set_option loom.semantics.termination "partial"` a nonterminating body makes the postcondition vacuously true (negated loop guard = False). This is the ONLY way to verify-while-wrong against this spec.

I materialized their faithful refined patches (patch_atk8_diverge.diff: `while True` at the head of RelatedLookupMixin.get_prep_lookup; patch_atk9_diverge.diff: `while True` at the head of Query.split_exclude) and RAN them through the official harness: python resolve_one.py patch_atk8_diverge.diff 300 -> {completed:false, resolved:false, note:'no report ... harness error'} python resolve_one.py patch_atk9_diverge.diff 300 -> {completed:false, resolved:false, note:'no report ...'} Direct harness run (run_id atk8diverge-confirm, --timeout 240) preserved the test log: exp/logs/run_evaluation/atk8diverge-confirm/sbu_patch/django__django-11734/test_output.txt ends with `test_disjunction_promotion4 (queries.tests.DisjunctionPromotionTests) ... \n\nTimeout error: 240 seconds exceeded.` — i.e. the infinite loop HANGS the test suite -> swebench raises EvaluationError -> NO report.json -> run_resolve returns completed=False.

WHY THIS IS NOT A BREAK: the mechanized derivation (construct/build_one.py:`_derive_audit_verdict` lines 300-312) fails a candidate (BROKEN) ONLY when its patch is completed AND not resolved; a resolve that does NOT complete is an inconclusive hit, never a break. A divergent impl can never produce completed∧¬resolved — it produces no test result at all. Moreover this is a UNIVERSAL partial-correctness property (401/500 velvet bundles use termination=partial), not a refinement-fidelity defect of THIS spec: the gold operation terminates, so there is no faithful refinement of it that reproduces the divergence.

I deliberately excluded atk_8/atk_9 from the mechanized `attacks` array because (a) they are not valid verify⇏correct counterexamples and (b) their non-completing resolves would improperly fail-close the derivation to INCONCLUSIVE via the inconclusive-hit path. Positive control (gold) resolved on the SAME infra, so the atk_8/atk_9 non-completion is the injected divergence, not an infra failure.

### Positive resolve control
patch_gold.diff (= atk_5 faithful patch, byte-equal to dataset gold) -> run_resolve {completed:true, resolved:true, note:'resolved'}. Gold applies cleanly to (base_commit 999891bd...).

#### REFINEMENT.md LEG AUDIT (task 3) — CLEAN, no kind-3
Site 1 (A1 lhsSpansMultipleColumns=R; A2 Target=R; A3 isExpression=I; A4 normalizesAsValue=I). Site 2 (B1 Target=R; B2 rebind dispatch=I; B3 resolveInSubquery=A-reference). No consumed axioms (meta.json axioms:[]). The two operations the gold CHANGES (site-1 guard predicate, site-2 rebind dispatch) are modeled IDENTICALLY (I) and G-CONF-confirmed; the one UNCHANGED downstream callee (resolve_expression) is the sole A-reference.

I re-ran both executable checks in-container (swebench/sweb.eval.x86_64.django_1776_django-11734:latest): axiom_check.py -> 'G-AX OK: A-reference resolveInSubquery == real resolve_expression on 15 (Rebound x name) cases ... bundle declares no consumed axioms.' rc=0 conformance_check.py -> 'G-CONF OK: ... agrees with patch.diff behaviour on 100006 inputs (seed=11734), 0 disagreements.' rc=0 I independently confirmed the A-reference against real django at base_commit: OuterRef(OuterRef(name)).resolve_expression -> OuterRef (staysOuter); OuterRef(name).resolve_expression -> ResolvedOuterRef (resolvesLocally); plain 5 -> plainValue; matches OuterRef.resolve_expression source (`return self.name if isinstance(self.name, OuterRef) else ResolvedOuterRef(self.name)`) and the OuterRef-is-F-subclass ordering.

A-reference correspondence to the real callee HOLDS. Known documentation nit (inert, not a transfer defect, already flagged in the bundle's verdict.md): mapping.md §2's directValue clause over-claims exhaustiveness over rhs types (a Value/Func has resolve_expression yet maps to directValue); these cases are UNCHANGED by the patch (both have as_sql, pre=post=not-normalized), lie outside the bug->fix delta, and yield no verified∧¬resolved pair. Does not affect the verify⇒resolved contract.

**CONCLUSION:** ≥5 same-spec attacks run; every terminating wrong impl is rejected by the exact-equality postcondition; the only verifying-but-wrong impls are divergent (vacuous partial-correctness) and their faithful patches hang -> ¬completed, never completed∧¬resolved; the echo verifies and resolves; positive control verifies; A-legs sound (G-AX) and R/I legs sound (G-CONF). No verify⇏correct counterexample exists. G-EQ = SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for django__django-11734 velvet. Spec region byte-identity CONFIRMED: swebench_unified.markers.same_spec(Solution.lean, Solution_prepatch*.lean, VelvetBackend.language) == True for both prepatch files. Solution.lean compiles (lean_verify exit 0); both prepatch files fail verification, so the spec is non-vacuous and pins the fix.

Modeled sites validated against the REAL repo callees at base_commit 999891bd (worktree):

Site 1 — comparisonNormalizesAsValue / isExpression models post-patch `not hasattr(self.rhs,'resolve_expression')` in RelatedLookupMixin.get_prep_lookup. Real hasattr on every Target class: OuterRef->True (model isExpression=true), F->True (true), plain int/str->False (false). normalizesAsValue = (!lhsSpansMultipleColumns) && !isExpression matches the whole post-patch guard `not isinstance(lhs,MultiColSource) and not hasattr(rhs,'resolve_expression')`. Agrees on all inputs.

Site 2 — subqueryTargetResolution = resolveInSubquery(rebind t) models post-patch split_exclude rebind + the unchanged resolve_expression. Verified by constructing real objects and calling the real resolve_expression: outerRef -> OuterRef(OuterRef(name)) -> resolves to OuterRef => staysOuter; localRef -> OuterRef(name) -> ResolvedOuterRef => resolvesLocally; directValue -> carried through, no resolve_expression => plainValue. All three match model exactly.

Abstraction-coverage note (NOT a divergence): a Value(5) has resolve_expression but is neither OuterRef nor F; the mapping.md bijection defines directValue as precisely 'no resolve_expression', so Value lies OUTSIDE the modeled Target domain rather than being a class where the model contradicts the callee. OuterRef is confirmed a subclass of F (issubclass True), which is exactly why the pre-patch F-branch mis-caught OuterRef and the fix's OuterRef branch precedes it — the model reproduces this. No input in the modeled domain makes the spec disagree with the real repo behavior; the spec is not too strong and does not drift. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Independently verified. (1) Spec region byte-identical: same_spec(Solution, prepatch)=True and same_spec(Solution, prepatch_2)=True under the velvet backend (markers.same_spec over axioms/pure/pre/post regions). Impl (`do`/impl-start..impl-end) and `prove_correct` bodies are ELIDED in spec_view — confirmed by rendering spec_view directly. (2) Mechanical G-LEAK screen (leakage.screen) PASSES with zero hard failures over the frozen row's gold patch + problem_statement. Bundle is NOT relaxed (relaxed_leakage=None, no RELAXED_LEAKAGE.md), so the strict lexical result stands. (3) Semantic review of the spec view against the PUBLIC problem_statement only (never hints_text): the problem_statement already discloses OuterRef used in exclude()/~Q(), that the outer-query reference is mis-resolved against the wrong (inner) query, and the exact ValueError 'may only be used in a subquery'. The spec-view narrative ('a reference to the outer query must continue to refer to the outer query', 'staysOuter/usable inside the subquery', 'must NOT be classified as a direct value... otherwise coerced into a value instead of resolved') restates precisely this publicly-known symptom and the correctness condition it implies — nothing more. (4) No gold-edit localization leaks: none of the patched repo file paths (related_lookups.py/query.py/fields/`__init__`.py), diff markers, patched-symbol names (get_prep_lookup, split_exclude, RelatedLookupMixin, rhs_is_direct_value, resolve_expression, get_prep_value, AutoField, MultiColSource), or any gold-diff line text appear in the spec view — verbatim or embedded in an identifier/comment. The Lean modeling names (Target/outerRef/isExpression/normalizesAsValue/rebind/resolveInSubquery) are abstractions derivable from the public 'outer query'/'subquery' vocabulary and do not name the edit. (5) The 'previous behavior' phrasing in the subqueryTargetResolution docstring describes the publicly-documented failure mode (the ValueError), not the concrete gold hunk (no mention of the F-branch fall-through, the OuterRef(filter_rhs) rewrap, or the get_prep_value deletion). It evades the lexical narration list without disclosing the edit. Conclusion: spec view leaks nothing about the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).