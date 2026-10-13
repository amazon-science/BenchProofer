# P2 adversarial audit — django__django-13417

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -43,7 +43,7 @@
     return true
   if !extraOrderBy.isEmpty || !orderBy.isEmpty then
     return true
-  else if defaultOrdering && !metaOrdering.isEmpty && groupBy.isEmpty then
+  else if defaultOrdering && !metaOrdering.isEmpty then
     return true
   else
     return false
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -43,7 +43,7 @@
     return true
   if !extraOrderBy.isEmpty || !orderBy.isEmpty then
     return true
-  else if defaultOrdering && !metaOrdering.isEmpty && groupBy.isEmpty then
+  else if defaultOrdering && groupBy.isEmpty then
     return true
   else
     return false
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -43,7 +43,7 @@
     return true
   if !extraOrderBy.isEmpty || !orderBy.isEmpty then
     return true
-  else if defaultOrdering && !metaOrdering.isEmpty && groupBy.isEmpty then
+  else if defaultOrdering && !metaOrdering.isEmpty && !groupBy.isEmpty then
     return true
   else
     return false
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -43,7 +43,7 @@
     return true
   if !extraOrderBy.isEmpty || !orderBy.isEmpty then
     return true
-  else if defaultOrdering && !metaOrdering.isEmpty && groupBy.isEmpty then
+  else if (defaultOrdering || !metaOrdering.isEmpty) && groupBy.isEmpty then
     return true
   else
     return false
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -41,7 +41,7 @@
     Bool := Id.run do
   if isEmpty then
     return true
-  if !extraOrderBy.isEmpty || !orderBy.isEmpty then
+  if !orderBy.isEmpty then
     return true
   else if defaultOrdering && !metaOrdering.isEmpty && groupBy.isEmpty then
     return true
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -43,7 +43,7 @@
     return true
   if !extraOrderBy.isEmpty || !orderBy.isEmpty then
     return true
-  else if defaultOrdering && !metaOrdering.isEmpty && groupBy.isEmpty then
+  else if defaultOrdering && metaOrdering.isEmpty && groupBy.isEmpty then
     return true
   else
     return false
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -38,15 +38,9 @@
 def implementation_querysetOrdered
     (isEmpty : Bool) (extraOrderBy orderBy : List String)
     (defaultOrdering : Bool) (metaOrdering groupBy : List String) :
-    Bool := Id.run do
-  if isEmpty then
-    return true
-  if !extraOrderBy.isEmpty || !orderBy.isEmpty then
-    return true
-  else if defaultOrdering && !metaOrdering.isEmpty && groupBy.isEmpty then
-    return true
-  else
-    return false
+    Bool :=
+  isEmpty || !extraOrderBy.isEmpty || !orderBy.isEmpty ||
+    (defaultOrdering && !metaOrdering.isEmpty && groupBy.isEmpty)
 -- impl-end
 
 -- proof-start
@@ -59,12 +53,11 @@
         metaOrdering groupBy) := by
   intro isEmpty extraOrderBy orderBy defaultOrdering metaOrdering groupBy
   unfold problem_spec_querysetOrdered implementation_querysetOrdered
-  simp only [Id.run]
   cases isEmpty <;>
     cases defaultOrdering <;>
     cases he : extraOrderBy.isEmpty <;>
     cases ho : orderBy.isEmpty <;>
     cases hm : metaOrdering.isEmpty <;>
     cases hg : groupBy.isEmpty <;>
-    simp_all <;> rfl
+    simp_all
 -- proof-end
```

Attack 8 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -38,15 +38,9 @@
 def implementation_querysetOrdered
     (isEmpty : Bool) (extraOrderBy orderBy : List String)
     (defaultOrdering : Bool) (metaOrdering groupBy : List String) :
-    Bool := Id.run do
-  if isEmpty then
-    return true
-  if !extraOrderBy.isEmpty || !orderBy.isEmpty then
-    return true
-  else if defaultOrdering && !metaOrdering.isEmpty && groupBy.isEmpty then
-    return true
-  else
-    return false
+    Bool :=
+  !orderBy.isEmpty || !extraOrderBy.isEmpty || isEmpty ||
+    (groupBy.isEmpty && !metaOrdering.isEmpty && defaultOrdering)
 -- impl-end
 
 -- proof-start
@@ -59,12 +53,11 @@
         metaOrdering groupBy) := by
   intro isEmpty extraOrderBy orderBy defaultOrdering metaOrdering groupBy
   unfold problem_spec_querysetOrdered implementation_querysetOrdered
-  simp only [Id.run]
   cases isEmpty <;>
     cases defaultOrdering <;>
     cases he : extraOrderBy.isEmpty <;>
     cases ho : orderBy.isEmpty <;>
     cases hm : metaOrdering.isEmpty <;>
     cases hg : groupBy.isEmpty <;>
-    simp_all <;> rfl
+    simp_all
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature: the ordering-introspection
-- predicate inspects only the truthiness of its input carriers (an empty/EmptyQuerySet
-- flag, two explicit-ordering sequences, a default-ordering flag, the model's default
-- ordering sequence, and the grouping sequence). Every observation is reproduced
-- concretely as a boolean combination, so nothing is axiomatized. The proof agent
-- may add `_prop` axioms only if it gets stuck.
-- axioms-end

-- pure-start
-- No standalone helpers are required; the predicate is a single boolean combination.
-- pure-end

-- post-conditions-start
/-- Whether a result set will carry a meaningful row ordering.

`isEmpty` marks the trivially-ordered empty set. `extraOrderBy` and `orderBy` hold
explicitly-requested orderings; a non-empty one orders the result. Otherwise the
result is ordered only when a default ordering is in force (`defaultOrdering` set
AND the model carries a default ordering sequence `metaOrdering`) AND the result is
NOT aggregated into groups — modeled by `groupBy`, whose presence (a non-empty
grouping sequence) suppresses the default ordering. Every input is observed only by
its emptiness/flag, and the result is pinned to the full boolean combination so no
component is left free. -/
def problem_spec_querysetOrdered
    (isEmpty : Bool) (extraOrderBy orderBy : List String)
    (defaultOrdering : Bool) (metaOrdering groupBy : List String)
    (result : Bool) : Prop :=
  result =
    (isEmpty || !extraOrderBy.isEmpty || !orderBy.isEmpty ||
      (defaultOrdering && !metaOrdering.isEmpty && groupBy.isEmpty))
-- post-conditions-end

-- impl-start
def implementation_querysetOrdered
    (isEmpty : Bool) (extraOrderBy orderBy : List String)
    (defaultOrdering : Bool) (metaOrdering groupBy : List String) :
    Bool := Id.run do
  if isEmpty then
    return true
  if !extraOrderBy.isEmpty || !orderBy.isEmpty then
    return true
  else if defaultOrdering && !metaOrdering.isEmpty && groupBy.isEmpty then
    return true
  else
    return false
-- impl-end

-- proof-start
theorem correct_querysetOrdered :
    ∀ (isEmpty : Bool) (extraOrderBy orderBy : List String)
      (defaultOrdering : Bool) (metaOrdering groupBy : List String),
    problem_spec_querysetOrdered isEmpty extraOrderBy orderBy defaultOrdering
      metaOrdering groupBy
      (implementation_querysetOrdered isEmpty extraOrderBy orderBy defaultOrdering
        metaOrdering groupBy) := by
  intro isEmpty extraOrderBy orderBy defaultOrdering metaOrdering groupBy
  unfold problem_spec_querysetOrdered implementation_querysetOrdered
  simp only [Id.run]
  cases isEmpty <;>
    cases defaultOrdering <;>
    cases he : extraOrderBy.isEmpty <;>
    cases ho : orderBy.isEmpty <;>
    cases hm : metaOrdering.isEmpty <;>
    cases hg : groupBy.isEmpty <;>
    simp_all <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec is a TOTAL PINNED EQUALITY: result = (isEmpty || !extraOrderBy.isEmpty || !orderBy.isEmpty || (defaultOrdering && !metaOrdering.isEmpty && groupBy.isEmpty)). Any closing correct_ forces impl to equal gold on ALL six carriers, including discriminator (isEmpty=false, extra=[], order=[], defaultOrdering=true, meta≠[], groupBy≠[]) where gold=false. same_spec=True verified for all 8 attacks (region-identical axioms/pure/pre/post).

### RESULTS (all machine-checked via scripts/lean_verify.sh, cap 300s, from root):
- pos_control.lean: exit 0; #print axioms correct_querysetOrdered => [propext, Quot.sound] (clean, no sorryAx).
- atk_1 (prepatch bug: drop groupBy.isEmpty conjunct): exit 1 REJECTED — reproduces G-DIFF/prepatch failure.
- atk_2 (drop metaOrdering conjunct): exit 1 REJECTED.
- atk_3 (invert: !groupBy.isEmpty): exit 1 REJECTED.
- atk_4 (|| instead of && between defaultOrdering/metaOrdering — ungrounded): exit 1 REJECTED.
- atk_5 (partial-domain: omit extraOrderBy short-circuit): exit 1 REJECTED.
- atk_6 (boundary: metaOrdering.isEmpty positive): exit 1 REJECTED.
- atk_7 (ECHO: direct boolean-expression impl, proof adapted): exit 0; axioms [propext] (clean). Gold-equivalent function.
- atk_8 (ECHO: reordered/commuted disjuncts, proof adapted): exit 0; axioms [propext] (clean). Gold-equivalent function.

RESOLVE (official harness, run_resolve, swe_bench_verified docker oracle): atk_7 and atk_8 both compute the IDENTICAL gold boolean function, so their faithful refined patch is byte-identical to patch.diff (gold post-patch QuerySet.ordered adding `and not self.query.group_by`). Materialized as faithful_gold.diff and executed: RESOLVED=True, COMPLETED=True, FLAKY=False, NOTE='resolved'. Command: python -c run_resolve('django__django-13417', patch, timeout=1800, retries=1). Both echo patches resolve => no verify∧¬resolve break.

Because the spec pins result to exactly one boolean expression, there is no closing-but-non-resolving impl: closure forces gold behavior on the exact discriminator, which resolves the F2P tests (test_annotated_default_ordering / test_annotated_values_default_ordering). The 6 genuinely-wrong impls all fail to close.

A-LEG AUDIT: meta.json axioms=[], deep_model_references=[], opaque_callees=[]. refinement.md legs: rows 1-3 = R (type refinement, truthiness/emptiness observations of the six carriers), row 4 = I (identical fallthrough). NO A-consumed, NO A-reference, NO kind-3 (changed-inexpressible) legs. The changed op (row 3, added groupBy.isEmpty conjunct) is modeled deeply as a concrete boolean conjunct, NOT axiomatized — G-AX is a legitimate skip stub. R/I legs mechanically covered by G-CONF (120008 inputs, 0 disagreements, seed=13417). No A-leg correspondence to falsify. verify⇒correct holds.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature: the ordering-introspection
-- predicate inspects only the truthiness of its input carriers (an empty/EmptyQuerySet
-- flag, two explicit-ordering sequences, a default-ordering flag, the model's default
-- ordering sequence, and the grouping sequence). Every observation is reproduced
-- concretely as a boolean combination, so nothing is axiomatized. The proof agent
-- may add `_prop` axioms only if it gets stuck.
-- axioms-end

-- pure-start
-- No standalone helpers are required; the predicate is a single boolean combination.
-- pure-end

-- post-conditions-start
/-- Whether a result set will carry a meaningful row ordering.

`isEmpty` marks the trivially-ordered empty set. `extraOrderBy` and `orderBy` hold
explicitly-requested orderings; a non-empty one orders the result. Otherwise the
result is ordered only when a default ordering is in force (`defaultOrdering` set
AND the model carries a default ordering sequence `metaOrdering`) AND the result is
NOT aggregated into groups — modeled by `groupBy`, whose presence (a non-empty
grouping sequence) suppresses the default ordering. Every input is observed only by
its emptiness/flag, and the result is pinned to the full boolean combination so no
component is left free. -/
def problem_spec_querysetOrdered
    (isEmpty : Bool) (extraOrderBy orderBy : List String)
    (defaultOrdering : Bool) (metaOrdering groupBy : List String)
    (result : Bool) : Prop :=
  result =
    (isEmpty || !extraOrderBy.isEmpty || !orderBy.isEmpty ||
      (defaultOrdering && !metaOrdering.isEmpty && groupBy.isEmpty))
-- post-conditions-end

-- impl-start
def implementation_querysetOrdered
    (isEmpty : Bool) (extraOrderBy orderBy : List String)
    (defaultOrdering : Bool) (metaOrdering groupBy : List String) :
    Bool := Id.run do
  if isEmpty then
    return true
  if !extraOrderBy.isEmpty || !orderBy.isEmpty then
    return true
  else if defaultOrdering && !metaOrdering.isEmpty && groupBy.isEmpty then
    return true
  else
    return false
-- impl-end

-- proof-start
theorem correct_querysetOrdered :
    ∀ (isEmpty : Bool) (extraOrderBy orderBy : List String)
      (defaultOrdering : Bool) (metaOrdering groupBy : List String),
    problem_spec_querysetOrdered isEmpty extraOrderBy orderBy defaultOrdering
      metaOrdering groupBy
      (implementation_querysetOrdered isEmpty extraOrderBy orderBy defaultOrdering
        metaOrdering groupBy) := by
  intro isEmpty extraOrderBy orderBy defaultOrdering metaOrdering groupBy
  unfold problem_spec_querysetOrdered implementation_querysetOrdered
  simp only [Id.run]
  cases isEmpty <;>
    cases defaultOrdering <;>
    cases he : extraOrderBy.isEmpty <;>
    cases ho : orderBy.isEmpty <;>
    cases hm : metaOrdering.isEmpty <;>
    cases hg : groupBy.isEmpty <;>
    simp_all <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec is a TOTAL PINNED EQUALITY: result = (isEmpty || !extraOrderBy.isEmpty || !orderBy.isEmpty || (defaultOrdering && !metaOrdering.isEmpty && groupBy.isEmpty)). Any closing correct_ forces impl to equal gold on ALL six carriers, including discriminator (isEmpty=false, extra=[], order=[], defaultOrdering=true, meta≠[], groupBy≠[]) where gold=false. same_spec=True verified for all 8 attacks (region-identical axioms/pure/pre/post).

### RESULTS (all machine-checked via scripts/lean_verify.sh, cap 300s, from root):
- pos_control.lean: exit 0; #print axioms correct_querysetOrdered => [propext, Quot.sound] (clean, no sorryAx).
- atk_1 (prepatch bug: drop groupBy.isEmpty conjunct): exit 1 REJECTED — reproduces G-DIFF/prepatch failure.
- atk_2 (drop metaOrdering conjunct): exit 1 REJECTED.
- atk_3 (invert: !groupBy.isEmpty): exit 1 REJECTED.
- atk_4 (|| instead of && between defaultOrdering/metaOrdering — ungrounded): exit 1 REJECTED.
- atk_5 (partial-domain: omit extraOrderBy short-circuit): exit 1 REJECTED.
- atk_6 (boundary: metaOrdering.isEmpty positive): exit 1 REJECTED.
- atk_7 (ECHO: direct boolean-expression impl, proof adapted): exit 0; axioms [propext] (clean). Gold-equivalent function.
- atk_8 (ECHO: reordered/commuted disjuncts, proof adapted): exit 0; axioms [propext] (clean). Gold-equivalent function.

RESOLVE (official harness, run_resolve, swe_bench_verified docker oracle): atk_7 and atk_8 both compute the IDENTICAL gold boolean function, so their faithful refined patch is byte-identical to patch.diff (gold post-patch QuerySet.ordered adding `and not self.query.group_by`). Materialized as faithful_gold.diff and executed: RESOLVED=True, COMPLETED=True, FLAKY=False, NOTE='resolved'. Command: python -c run_resolve('django__django-13417', patch, timeout=1800, retries=1). Both echo patches resolve => no verify∧¬resolve break.

Because the spec pins result to exactly one boolean expression, there is no closing-but-non-resolving impl: closure forces gold behavior on the exact discriminator, which resolves the F2P tests (test_annotated_default_ordering / test_annotated_values_default_ordering). The 6 genuinely-wrong impls all fail to close.

A-LEG AUDIT: meta.json axioms=[], deep_model_references=[], opaque_callees=[]. refinement.md legs: rows 1-3 = R (type refinement, truthiness/emptiness observations of the six carriers), row 4 = I (identical fallthrough). NO A-consumed, NO A-reference, NO kind-3 (changed-inexpressible) legs. The changed op (row 3, added groupBy.isEmpty conjunct) is modeled deeply as a concrete boolean conjunct, NOT axiomatized — G-AX is a legitimate skip stub. R/I legs mechanically covered by G-CONF (120008 inputs, 0 disagreements, seed=13417). No A-leg correspondence to falsify. verify⇒correct holds.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for django__django-13417, modeled function QuerySet.ordered (django/db/models/query.py). 

Real callee at base_commit+patch:
  if isinstance(self, EmptyQuerySet): return True
  if self.query.extra_order_by or self.query.order_by: return True
  elif (self.query.default_ordering and self.query.get_meta().ordering and not self.query.group_by): return True
  else: return False

Spec:
  result = (isEmpty || !extraOrderBy.isEmpty || !orderBy.isEmpty || (defaultOrdering && !metaOrdering.isEmpty && groupBy.isEmpty))

The Python if/elif return-True cascade is logically the disjunction of the four guards, exactly matching the spec's biconditional — no extra constraint is imposed. Every attribute the real function reads is consumed purely by truthiness; the model abstracts each sequence carrier by List.isEmpty and the two booleans directly. This abstraction is sound AND complete for this function: the callee inspects nothing beyond these six truthiness/flag observations, so any Python state and its abstracted Lean input produce identical real results. group_by's None/True/tuple truthiness maps consistently (falsy<->empty, truthy<->non-empty). I could not construct any input where the spec disagrees with the real callee — the spec is neither too strong nor drifted.

Corroborating verification: Solution.lean compiles under lean_verify.sh (exit 0); `#print axioms correct_querysetOrdered` = [propext, Quot.sound] only (no sorryAx — proof is genuine). same_spec(Solution, Solution_prepatch, LeanBackend) = True (spec region byte-identical). G-DIFF correctly fails the prepatch, which drops the groupBy.isEmpty conjunct (the changed op).

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view verified: same_spec(Solution, Solution_prepatch)=True (post-conditions region byte-identical; impl/proof correctly elided). The load-bearing spec conjunct is `groupBy.isEmpty` inside `result = (isEmpty || !extraOrderBy.isEmpty || !orderBy.isEmpty || (defaultOrdering && !metaOrdering.isEmpty && groupBy.isEmpty))`, the modeled analogue of the gold edit `and not self.query.group_by`. This does NOT leak beyond the public problem_statement: the issue explicitly shows that `annotate(Count("pk"))` produces SQL with a GROUP BY clause and NO ORDER BY clause, while `qs.ordered` wrongly returns True and `default_ordering` is True — so 'GROUP BY suppresses the default ordering' and the desired correct behavior are both disclosed verbatim in the public statement. Carrier names (groupBy, defaultOrdering, metaOrdering, extraOrderBy, orderBy) are generic domain terms / public-API surface (`default_ordering`, `GROUP BY` appear verbatim in the statement), not diff-private identifiers or codebase-internal detail. The docstring rationale ('presence of a non-empty grouping sequence suppresses the default ordering') restates the publicly-described semantics, not solution-only vocabulary. Impl and proof regions are elided in the spec view, so no gold proof body or the specific `not self.query.group_by` diff text leaks. A spec necessarily encodes correct behavior; nothing here reveals information absent from problem_statement (hints_text not considered).

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
