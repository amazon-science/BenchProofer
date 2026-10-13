# P2 adversarial audit — django__django-13012

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_echo1.lean`, `atk_echo2.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -66,12 +66,16 @@
 
 -- impl-start
 def implementation_wrapperGroupByCols (e : Expr) : List Col := Id.run do
-  return e.innerCols
+  if e.innerContainsAggregate then
+    return e.innerCols
+  return [e.selfCol]
 -- impl-end
 
 -- proof-start
 theorem correct_wrapperGroupByCols :
     ∀ (e : Expr), problem_spec_wrapperGroupByCols e (implementation_wrapperGroupByCols e) := by
   intro e
-  rfl
+  unfold problem_spec_wrapperGroupByCols implementation_wrapperGroupByCols
+  simp only [Id.run]
+  split <;> rfl
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -66,12 +66,16 @@
 
 -- impl-start
 def implementation_wrapperGroupByCols (e : Expr) : List Col := Id.run do
-  return e.innerCols
+  if e.innerContainsAggregate then
+    return e.innerCols
+  return []
 -- impl-end
 
 -- proof-start
 theorem correct_wrapperGroupByCols :
     ∀ (e : Expr), problem_spec_wrapperGroupByCols e (implementation_wrapperGroupByCols e) := by
   intro e
-  rfl
+  unfold problem_spec_wrapperGroupByCols implementation_wrapperGroupByCols
+  simp only [Id.run]
+  split <;> rfl
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -66,7 +66,7 @@
 
 -- impl-start
 def implementation_wrapperGroupByCols (e : Expr) : List Col := Id.run do
-  return e.innerCols
+  return e.innerCols ++ [e.selfCol]
 -- impl-end
 
 -- proof-start
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -66,7 +66,7 @@
 
 -- impl-start
 def implementation_wrapperGroupByCols (e : Expr) : List Col := Id.run do
-  return e.innerCols
+  return []
 -- impl-end
 
 -- proof-start
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -66,7 +66,7 @@
 
 -- impl-start
 def implementation_wrapperGroupByCols (e : Expr) : List Col := Id.run do
-  return e.innerCols
+  return [e.selfCol]
 -- impl-end
 
 -- proof-start
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -66,7 +66,7 @@
 
 -- impl-start
 def implementation_wrapperGroupByCols (e : Expr) : List Col := Id.run do
-  return e.innerCols
+  return e.selfCol :: e.innerCols
 -- impl-end
 
 -- proof-start
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -66,7 +66,7 @@
 
 -- impl-start
 def implementation_wrapperGroupByCols (e : Expr) : List Col := Id.run do
-  return e.innerCols
+  return e.innerCols.reverse
 -- impl-end
 
 -- proof-start
```

Attack 8 — `atk_echo1.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -65,8 +65,9 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_wrapperGroupByCols (e : Expr) : List Col := Id.run do
-  return e.innerCols
+def implementation_wrapperGroupByCols (e : Expr) : List Col :=
+  match e with
+  | ⟨_, _, c⟩ => c
 -- impl-end
 
 -- proof-start
```

Attack 9 — `atk_echo2.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -66,6 +66,8 @@
 
 -- impl-start
 def implementation_wrapperGroupByCols (e : Expr) : List Col := Id.run do
+  if e.innerContainsAggregate then
+    return e.innerCols
   return e.innerCols
 -- impl-end
 
@@ -73,5 +75,7 @@
 theorem correct_wrapperGroupByCols :
     ∀ (e : Expr), problem_spec_wrapperGroupByCols e (implementation_wrapperGroupByCols e) := by
   intro e
-  rfl
+  unfold problem_spec_wrapperGroupByCols implementation_wrapperGroupByCols
+  simp only [Id.run]
+  split <;> rfl
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Group-by columns contributed by a wrapping expression.

Some expressions merely wrap another expression to attach extra context (such as
an output type) without changing what that inner expression computes. When a
query groups its rows, every selected expression contributes a (possibly empty)
set of columns to the grouping clause. Each kind of expression decides this for
itself: a constant expression contributes no columns, an aggregate contributes
the columns of its operands, a plain column contributes itself, and so on.

A wrapping expression adds no grouping column of its own. The columns it
contributes to the grouping clause are exactly the columns contributed by the
expression it wraps. In particular, wrapping a constant expression — which
contributes nothing — itself contributes nothing, rather than standing in as a
grouping column. The result is fully determined by the wrapped expression.
-/

-- axioms-start
-- The columns the wrapped (inner) expression contributes to the grouping clause
-- are observed directly as the `Expr.innerCols` field: this is the unchanged,
-- self-determined behavior of the inner expression, carried into the model as
-- input data (an A-reference — the wrapping expression forwards to it verbatim).
-- No separate property of that observation is consumed, so there is no
-- `opaque`/`axiom` callee contract here.
-- axioms-end

-- pure-start
/-- A single column expression as it may appear in a query's grouping clause.
Its identity is opaque; only equality of columns is observable. -/
structure Col where
  ref : Nat
deriving DecidableEq, Repr

/-- A wrapping expression, observed through the only features that determine the
columns it contributes to the grouping clause:

  * `selfCol`  — the wrapping expression viewed as a single grouping column (its
    own identity, were it to stand in for itself);
  * `innerContainsAggregate` — whether the expression it wraps contains an
    aggregate;
  * `innerCols` — the columns the wrapped (inner) expression contributes to the
    grouping clause. -/
structure Expr where
  /-- the wrapping expression as a single grouping column (its own identity) -/
  selfCol : Col
  /-- whether the wrapped (inner) expression contains an aggregate -/
  innerContainsAggregate : Bool
  /-- the grouping columns contributed by the wrapped (inner) expression -/
  innerCols : List Col
deriving Repr
-- pure-end

-- post-conditions-start
/-- The columns a wrapping expression `e` contributes to the grouping clause are
exactly those contributed by the expression it wraps (`e.innerCols`). The result
is pinned in full to the wrapped expression's contribution (directive 5 frame:
no component of the result is left free; directive 8: the result is grounded in
the actual input `e`, so it must be *produced by* forwarding to the wrapped
expression, not by re-introducing the wrapper itself). -/
def problem_spec_wrapperGroupByCols (e : Expr) (result : List Col) : Prop :=
  result = e.innerCols
-- post-conditions-end

-- impl-start
def implementation_wrapperGroupByCols (e : Expr) : List Col := Id.run do
  return e.innerCols
-- impl-end

-- proof-start
theorem correct_wrapperGroupByCols :
    ∀ (e : Expr), problem_spec_wrapperGroupByCols e (implementation_wrapperGroupByCols e) := by
  intro e
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC: problem_spec_wrapperGroupByCols e result := (result = e.innerCols) — a maximally tight FULL-EQUALITY postcondition pinning the entire result to the single input field e.innerCols (the A-reference modeling self.expression.get_group_by_cols). Any impl that verifies must return exactly e.innerCols on every input, i.e. be behaviorally identical to gold. This leaves no room for a divergent-but-verifying impl.

SAME-SPEC: all 10 files (7 wrong + 2 echo + pos control) confirmed byte-identical spec via markers.same_spec (LeanBackend) = True. Only impl+proof regions edited; axioms/pure/pre/post byte-identical.

### VERIFY (bash scripts/lean_verify.sh <f>):
  atk_1 (prepatch bug: [e.selfCol] when !innerContainsAggregate) EXIT=1 — genuine proof failure `[e.selfCol] = e.innerCols` in isFalse branch (prepatch reproduced).
  atk_2 (partial-domain: correct only aggregate branch, else []) EXIT=1.
  atk_3 (e.innerCols ++ [e.selfCol]) EXIT=1.
  atk_4 (control-flow effect: always []) EXIT=1.
  atk_5 (ungrounded oracle echo: always [e.selfCol]) EXIT=1.
  atk_6 (prepend: e.selfCol :: e.innerCols) EXIT=1.
  atk_7 (boundary/order: e.innerCols.reverse) EXIT=1.
  atk_echo1 (match-extract innerCols) EXIT=0, `#print axioms` = does not depend on any axioms (CLEAN).
  atk_echo2 (redundant conditional, BOTH branches delegate) EXIT=0, axioms CLEAN.
  pos_control (gold: return e.innerCols) EXIT=0, axioms CLEAN.

RESOLVE (harness.run_resolve, django__django-13012) for the two clean-axiom verifying attacks:
  patch_echo1 (byte-identical to gold patch): first attempt returned completed=False (transient harness/image error under host contention); re-run attempts=1 -> resolved=True completed=True.
  patch_echo2 (faithful to echo2's redundant-branch control flow): resolved=True completed=True.
Both verifying same-spec attacks have materialized faithful patches that RESOLVE under the official harness. No verified impl fails to resolve => verify⇏correct NOT demonstrated => spec is SOUND.

REFINEMENT.MD AUDIT: single leg, tagged A-reference (op: return e.innerCols ↔ return self.expression.get_group_by_cols(alias=alias)). Correct: the inner callee get_group_by_cols is UNCHANGED by the patch and forwarded verbatim; its result is modeled deeply as input field e.innerCols; no property consumed by proof (no A-consumed leg), no R/I transform, NO kind-3 (changed-inexpressible) leg. Correspondence to real callee confirmed @22a59c01c0: BaseExpression.get_group_by_cols (line 350) returns [self] when !contains_aggregate (the bug), Value.get_group_by_cols returns []; patched ExpressionWrapper.get_group_by_cols delegates unconditionally to self.expression.get_group_by_cols(alias=alias) == e.innerCols. Model matches.

VERDICT: SOUND. 7 distinct wrong impls (partial-domain, boundary/order, control-flow-effect, ungrounded-oracle-echo, prepatch) all fail to verify; 2 behaviorally-gold echoes verify with clean axioms and both resolve. The full-equality spec admits only gold-equivalent behavior.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_echo1.lean`, `atk_echo2.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 9 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_echo1.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 9 — `atk_echo2.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Group-by columns contributed by a wrapping expression.

Some expressions merely wrap another expression to attach extra context (such as
an output type) without changing what that inner expression computes. When a
query groups its rows, every selected expression contributes a (possibly empty)
set of columns to the grouping clause. Each kind of expression decides this for
itself: a constant expression contributes no columns, an aggregate contributes
the columns of its operands, a plain column contributes itself, and so on.

A wrapping expression adds no grouping column of its own. The columns it
contributes to the grouping clause are exactly the columns contributed by the
expression it wraps. In particular, wrapping a constant expression — which
contributes nothing — itself contributes nothing, rather than standing in as a
grouping column. The result is fully determined by the wrapped expression.
-/

-- axioms-start
-- The columns the wrapped (inner) expression contributes to the grouping clause
-- are observed directly as the `Expr.innerCols` field: this is the unchanged,
-- self-determined behavior of the inner expression, carried into the model as
-- input data (an A-reference — the wrapping expression forwards to it verbatim).
-- No separate property of that observation is consumed, so there is no
-- `opaque`/`axiom` callee contract here.
-- axioms-end

-- pure-start
/-- A single column expression as it may appear in a query's grouping clause.
Its identity is opaque; only equality of columns is observable. -/
structure Col where
  ref : Nat
deriving DecidableEq, Repr

/-- A wrapping expression, observed through the only features that determine the
columns it contributes to the grouping clause:

  * `selfCol`  — the wrapping expression viewed as a single grouping column (its
    own identity, were it to stand in for itself);
  * `innerContainsAggregate` — whether the expression it wraps contains an
    aggregate;
  * `innerCols` — the columns the wrapped (inner) expression contributes to the
    grouping clause. -/
structure Expr where
  /-- the wrapping expression as a single grouping column (its own identity) -/
  selfCol : Col
  /-- whether the wrapped (inner) expression contains an aggregate -/
  innerContainsAggregate : Bool
  /-- the grouping columns contributed by the wrapped (inner) expression -/
  innerCols : List Col
deriving Repr
-- pure-end

-- post-conditions-start
/-- The columns a wrapping expression `e` contributes to the grouping clause are
exactly those contributed by the expression it wraps (`e.innerCols`). The result
is pinned in full to the wrapped expression's contribution (directive 5 frame:
no component of the result is left free; directive 8: the result is grounded in
the actual input `e`, so it must be *produced by* forwarding to the wrapped
expression, not by re-introducing the wrapper itself). -/
def problem_spec_wrapperGroupByCols (e : Expr) (result : List Col) : Prop :=
  result = e.innerCols
-- post-conditions-end

-- impl-start
def implementation_wrapperGroupByCols (e : Expr) : List Col := Id.run do
  return e.innerCols
-- impl-end

-- proof-start
theorem correct_wrapperGroupByCols :
    ∀ (e : Expr), problem_spec_wrapperGroupByCols e (implementation_wrapperGroupByCols e) := by
  intro e
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC: problem_spec_wrapperGroupByCols e result := (result = e.innerCols) — a maximally tight FULL-EQUALITY postcondition pinning the entire result to the single input field e.innerCols (the A-reference modeling self.expression.get_group_by_cols). Any impl that verifies must return exactly e.innerCols on every input, i.e. be behaviorally identical to gold. This leaves no room for a divergent-but-verifying impl.

SAME-SPEC: all 10 files (7 wrong + 2 echo + pos control) confirmed byte-identical spec via markers.same_spec (LeanBackend) = True. Only impl+proof regions edited; axioms/pure/pre/post byte-identical.

### VERIFY (bash scripts/lean_verify.sh <f>):
  atk_1 (prepatch bug: [e.selfCol] when !innerContainsAggregate) EXIT=1 — genuine proof failure `[e.selfCol] = e.innerCols` in isFalse branch (prepatch reproduced).
  atk_2 (partial-domain: correct only aggregate branch, else []) EXIT=1.
  atk_3 (e.innerCols ++ [e.selfCol]) EXIT=1.
  atk_4 (control-flow effect: always []) EXIT=1.
  atk_5 (ungrounded oracle echo: always [e.selfCol]) EXIT=1.
  atk_6 (prepend: e.selfCol :: e.innerCols) EXIT=1.
  atk_7 (boundary/order: e.innerCols.reverse) EXIT=1.
  atk_echo1 (match-extract innerCols) EXIT=0, `#print axioms` = does not depend on any axioms (CLEAN).
  atk_echo2 (redundant conditional, BOTH branches delegate) EXIT=0, axioms CLEAN.
  pos_control (gold: return e.innerCols) EXIT=0, axioms CLEAN.

RESOLVE (harness.run_resolve, django__django-13012) for the two clean-axiom verifying attacks:
  patch_echo1 (byte-identical to gold patch): first attempt returned completed=False (transient harness/image error under host contention); re-run attempts=1 -> resolved=True completed=True.
  patch_echo2 (faithful to echo2's redundant-branch control flow): resolved=True completed=True.
Both verifying same-spec attacks have materialized faithful patches that RESOLVE under the official harness. No verified impl fails to resolve => verify⇏correct NOT demonstrated => spec is SOUND.

REFINEMENT.MD AUDIT: single leg, tagged A-reference (op: return e.innerCols ↔ return self.expression.get_group_by_cols(alias=alias)). Correct: the inner callee get_group_by_cols is UNCHANGED by the patch and forwarded verbatim; its result is modeled deeply as input field e.innerCols; no property consumed by proof (no A-consumed leg), no R/I transform, NO kind-3 (changed-inexpressible) leg. Correspondence to real callee confirmed @22a59c01c0: BaseExpression.get_group_by_cols (line 350) returns [self] when !contains_aggregate (the bug), Value.get_group_by_cols returns []; patched ExpressionWrapper.get_group_by_cols delegates unconditionally to self.expression.get_group_by_cols(alias=alias) == e.innerCols. Model matches.

VERDICT: SOUND. 7 distinct wrong impls (partial-domain, boundary/order, control-flow-effect, ungrounded-oracle-echo, prepatch) all fail to verify; 2 behaviorally-gold echoes verify with clean axioms and both resolve. The full-equality spec admits only gold-equivalent behavior.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) audit of django__django-13012 lean.

Modeled function: `wrapperGroupByCols` = the `get_group_by_cols` method the gold patch newly adds to `ExpressionWrapper`. Spec: `problem_spec_wrapperGroupByCols (e : Expr) (result : List Col) : Prop := result = e.innerCols`.

Checks performed:
(1) scripts/lean_verify.sh on Solution.lean -> EXIT 0 (compiles, no sorry).
(2) `#print axioms correct_wrapperGroupByCols` -> 'does not depend on any axioms' (no sorryAx; the `rfl` proof is genuine, not fake).
(3) markers.same_spec(Solution.lean, Solution_prepatch.lean, LeanBackend.language) = True and spec_view identical -> spec region byte-identical between patched/prepatch; impl+proof edits confined to elided regions.
 Real repo at base_commit 22a59c01c0: ExpressionWrapper has NO get_group_by_cols at base (inherits BaseExpression.get_group_by_cols at expressions.py:350 -> returns [self] when not contains_aggregate). patch.diff adds verbatim: `def get_group_by_cols(self, alias=None): return self.expression.get_group_by_cols(alias=alias)` — an unconditional, side-condition-free delegation to the wrapped expression's own get_group_by_cols.

Faithfulness reasoning: e.innerCols is the A-reference deep-modeling exactly `self.expression.get_group_by_cols(alias=alias)` (per mapping.md / refinement.md / meta.json deep_model_references). The patched method's ENTIRE body returns that value, so result = e.innerCols is precisely what the real patched callee returns on every input. No local transformation is dropped or added; the `alias` kwarg is threaded straight through to the callee and its effect is fully absorbed into the single observed value e.innerCols. There is no domain restriction, no extra proof obligation, and no over-constraint. The spec is a total functional pin that matches the gold delegation verbatim — not too strong, not drifting.

No diverging input exists between the modeled function and the real patched callee. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (Solution.lean minus impl+proof) verified via markers.spec_view(lean backend); same_spec(patched, prepatch)=True so the spec region is byte-identical and the fix lives only in the elided impl/proof. The spec view discloses only the abstract behavioral contract: a wrapping expression contributes exactly the columns of the expression it wraps, so a wrapped constant contributes nothing; postcondition `result = e.innerCols`. The public problem_statement already names ExpressionWrapper, the GROUP BY clause, constant expressions (Value(3)), the symptom (wrapped constant wrongly forced into GROUP BY) and the correct contrast (an unwrapped constant is correctly omitted). Lexical screen over the spec view: the gold-diff line `return self.expression.get_group_by_cols(alias=alias)` is ABSENT; no diff markers/@@; no patched file path (django/db/models/expressions.py); no patched symbol `get_group_by_cols`; no `BaseExpression`/`[self]` default mechanism. Spec identifiers (wrapperGroupByCols, Expr, Col, innerCols) name behavior, not the edit. The postcondition states the correct I/O relation, which is what a spec legitimately does and is derivable from the public problem_statement; it does not reveal the delegation mechanism (the impl). No line leaks the gold edit beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
