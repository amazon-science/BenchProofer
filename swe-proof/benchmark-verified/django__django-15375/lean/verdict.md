# P2 adversarial audit — django__django-15375

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
@@ -66,16 +66,10 @@
 -- impl-start
 def implementation_resolveAggregate
     (isTerminalAggregation hasFallback : Bool) : ResolvedExpr := Id.run do
-  -- The aggregate is marked as terminal exactly when it is resolved as a
-  -- terminal aggregation.
   let mut terminal := isTerminalAggregation
   if !hasFallback then
-    -- No fallback supplied: return the bare aggregate node.
     return { wrapped := false, terminal := terminal }
-  -- A fallback is supplied: build the coalescing wrapper (which starts out
-  -- non-terminal) and carry the aggregate's terminal marker onto it.
   let mut wrapperTerminal := false
-  wrapperTerminal := terminal
   return { wrapped := true, terminal := wrapperTerminal }
 -- impl-end
 
@@ -85,6 +79,12 @@
       problem_spec_resolveAggregate isTerminalAggregation hasFallback
         (implementation_resolveAggregate isTerminalAggregation hasFallback) := by
   intro isTerminalAggregation hasFallback
-  unfold problem_spec_resolveAggregate implementation_resolveAggregate
-  cases hasFallback <;> simp [Id.run, pure, bind]
+  first
+  | (unfold problem_spec_resolveAggregate implementation_resolveAggregate;
+     cases isTerminalAggregation <;> cases hasFallback <;> simp [Id.run, pure, bind])
+  | (cases isTerminalAggregation <;> cases hasFallback <;> decide)
+  | (cases isTerminalAggregation <;> cases hasFallback <;> native_decide)
+  | decide
+  | native_decide
+  | simp_all [problem_spec_resolveAggregate, implementation_resolveAggregate, Id.run, pure, bind]
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -65,18 +65,8 @@
 
 -- impl-start
 def implementation_resolveAggregate
-    (isTerminalAggregation hasFallback : Bool) : ResolvedExpr := Id.run do
-  -- The aggregate is marked as terminal exactly when it is resolved as a
-  -- terminal aggregation.
-  let mut terminal := isTerminalAggregation
-  if !hasFallback then
-    -- No fallback supplied: return the bare aggregate node.
-    return { wrapped := false, terminal := terminal }
-  -- A fallback is supplied: build the coalescing wrapper (which starts out
-  -- non-terminal) and carry the aggregate's terminal marker onto it.
-  let mut wrapperTerminal := false
-  wrapperTerminal := terminal
-  return { wrapped := true, terminal := wrapperTerminal }
+    (isTerminalAggregation hasFallback : Bool) : ResolvedExpr :=
+  { wrapped := hasFallback, terminal := !isTerminalAggregation }
 -- impl-end
 
 -- proof-start
@@ -85,6 +75,12 @@
       problem_spec_resolveAggregate isTerminalAggregation hasFallback
         (implementation_resolveAggregate isTerminalAggregation hasFallback) := by
   intro isTerminalAggregation hasFallback
-  unfold problem_spec_resolveAggregate implementation_resolveAggregate
-  cases hasFallback <;> simp [Id.run, pure, bind]
+  first
+  | (unfold problem_spec_resolveAggregate implementation_resolveAggregate;
+     cases isTerminalAggregation <;> cases hasFallback <;> simp [Id.run, pure, bind])
+  | (cases isTerminalAggregation <;> cases hasFallback <;> decide)
+  | (cases isTerminalAggregation <;> cases hasFallback <;> native_decide)
+  | decide
+  | native_decide
+  | simp_all [problem_spec_resolveAggregate, implementation_resolveAggregate, Id.run, pure, bind]
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -65,18 +65,8 @@
 
 -- impl-start
 def implementation_resolveAggregate
-    (isTerminalAggregation hasFallback : Bool) : ResolvedExpr := Id.run do
-  -- The aggregate is marked as terminal exactly when it is resolved as a
-  -- terminal aggregation.
-  let mut terminal := isTerminalAggregation
-  if !hasFallback then
-    -- No fallback supplied: return the bare aggregate node.
-    return { wrapped := false, terminal := terminal }
-  -- A fallback is supplied: build the coalescing wrapper (which starts out
-  -- non-terminal) and carry the aggregate's terminal marker onto it.
-  let mut wrapperTerminal := false
-  wrapperTerminal := terminal
-  return { wrapped := true, terminal := wrapperTerminal }
+    (isTerminalAggregation hasFallback : Bool) : ResolvedExpr :=
+  { wrapped := hasFallback, terminal := isTerminalAggregation && hasFallback }
 -- impl-end
 
 -- proof-start
@@ -85,6 +75,12 @@
       problem_spec_resolveAggregate isTerminalAggregation hasFallback
         (implementation_resolveAggregate isTerminalAggregation hasFallback) := by
   intro isTerminalAggregation hasFallback
-  unfold problem_spec_resolveAggregate implementation_resolveAggregate
-  cases hasFallback <;> simp [Id.run, pure, bind]
+  first
+  | (unfold problem_spec_resolveAggregate implementation_resolveAggregate;
+     cases isTerminalAggregation <;> cases hasFallback <;> simp [Id.run, pure, bind])
+  | (cases isTerminalAggregation <;> cases hasFallback <;> decide)
+  | (cases isTerminalAggregation <;> cases hasFallback <;> native_decide)
+  | decide
+  | native_decide
+  | simp_all [problem_spec_resolveAggregate, implementation_resolveAggregate, Id.run, pure, bind]
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -66,17 +66,10 @@
 -- impl-start
 def implementation_resolveAggregate
     (isTerminalAggregation hasFallback : Bool) : ResolvedExpr := Id.run do
-  -- The aggregate is marked as terminal exactly when it is resolved as a
-  -- terminal aggregation.
-  let mut terminal := isTerminalAggregation
-  if !hasFallback then
-    -- No fallback supplied: return the bare aggregate node.
-    return { wrapped := false, terminal := terminal }
-  -- A fallback is supplied: build the coalescing wrapper (which starts out
-  -- non-terminal) and carry the aggregate's terminal marker onto it.
-  let mut wrapperTerminal := false
-  wrapperTerminal := terminal
-  return { wrapped := true, terminal := wrapperTerminal }
+  let mut wrapped := true
+  if hasFallback then
+    wrapped := true
+  return { wrapped := wrapped, terminal := isTerminalAggregation }
 -- impl-end
 
 -- proof-start
@@ -85,6 +78,12 @@
       problem_spec_resolveAggregate isTerminalAggregation hasFallback
         (implementation_resolveAggregate isTerminalAggregation hasFallback) := by
   intro isTerminalAggregation hasFallback
-  unfold problem_spec_resolveAggregate implementation_resolveAggregate
-  cases hasFallback <;> simp [Id.run, pure, bind]
+  first
+  | (unfold problem_spec_resolveAggregate implementation_resolveAggregate;
+     cases isTerminalAggregation <;> cases hasFallback <;> simp [Id.run, pure, bind])
+  | (cases isTerminalAggregation <;> cases hasFallback <;> decide)
+  | (cases isTerminalAggregation <;> cases hasFallback <;> native_decide)
+  | decide
+  | native_decide
+  | simp_all [problem_spec_resolveAggregate, implementation_resolveAggregate, Id.run, pure, bind]
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -65,18 +65,8 @@
 
 -- impl-start
 def implementation_resolveAggregate
-    (isTerminalAggregation hasFallback : Bool) : ResolvedExpr := Id.run do
-  -- The aggregate is marked as terminal exactly when it is resolved as a
-  -- terminal aggregation.
-  let mut terminal := isTerminalAggregation
-  if !hasFallback then
-    -- No fallback supplied: return the bare aggregate node.
-    return { wrapped := false, terminal := terminal }
-  -- A fallback is supplied: build the coalescing wrapper (which starts out
-  -- non-terminal) and carry the aggregate's terminal marker onto it.
-  let mut wrapperTerminal := false
-  wrapperTerminal := terminal
-  return { wrapped := true, terminal := wrapperTerminal }
+    (isTerminalAggregation hasFallback : Bool) : ResolvedExpr :=
+  { wrapped := hasFallback, terminal := hasFallback }
 -- impl-end
 
 -- proof-start
@@ -85,6 +75,12 @@
       problem_spec_resolveAggregate isTerminalAggregation hasFallback
         (implementation_resolveAggregate isTerminalAggregation hasFallback) := by
   intro isTerminalAggregation hasFallback
-  unfold problem_spec_resolveAggregate implementation_resolveAggregate
-  cases hasFallback <;> simp [Id.run, pure, bind]
+  first
+  | (unfold problem_spec_resolveAggregate implementation_resolveAggregate;
+     cases isTerminalAggregation <;> cases hasFallback <;> simp [Id.run, pure, bind])
+  | (cases isTerminalAggregation <;> cases hasFallback <;> decide)
+  | (cases isTerminalAggregation <;> cases hasFallback <;> native_decide)
+  | decide
+  | native_decide
+  | simp_all [problem_spec_resolveAggregate, implementation_resolveAggregate, Id.run, pure, bind]
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -65,18 +65,8 @@
 
 -- impl-start
 def implementation_resolveAggregate
-    (isTerminalAggregation hasFallback : Bool) : ResolvedExpr := Id.run do
-  -- The aggregate is marked as terminal exactly when it is resolved as a
-  -- terminal aggregation.
-  let mut terminal := isTerminalAggregation
-  if !hasFallback then
-    -- No fallback supplied: return the bare aggregate node.
-    return { wrapped := false, terminal := terminal }
-  -- A fallback is supplied: build the coalescing wrapper (which starts out
-  -- non-terminal) and carry the aggregate's terminal marker onto it.
-  let mut wrapperTerminal := false
-  wrapperTerminal := terminal
-  return { wrapped := true, terminal := wrapperTerminal }
+    (isTerminalAggregation hasFallback : Bool) : ResolvedExpr :=
+  { wrapped := !hasFallback, terminal := isTerminalAggregation }
 -- impl-end
 
 -- proof-start
@@ -85,6 +75,12 @@
       problem_spec_resolveAggregate isTerminalAggregation hasFallback
         (implementation_resolveAggregate isTerminalAggregation hasFallback) := by
   intro isTerminalAggregation hasFallback
-  unfold problem_spec_resolveAggregate implementation_resolveAggregate
-  cases hasFallback <;> simp [Id.run, pure, bind]
+  first
+  | (unfold problem_spec_resolveAggregate implementation_resolveAggregate;
+     cases isTerminalAggregation <;> cases hasFallback <;> simp [Id.run, pure, bind])
+  | (cases isTerminalAggregation <;> cases hasFallback <;> decide)
+  | (cases isTerminalAggregation <;> cases hasFallback <;> native_decide)
+  | decide
+  | native_decide
+  | simp_all [problem_spec_resolveAggregate, implementation_resolveAggregate, Id.run, pure, bind]
 -- proof-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -65,18 +65,8 @@
 
 -- impl-start
 def implementation_resolveAggregate
-    (isTerminalAggregation hasFallback : Bool) : ResolvedExpr := Id.run do
-  -- The aggregate is marked as terminal exactly when it is resolved as a
-  -- terminal aggregation.
-  let mut terminal := isTerminalAggregation
-  if !hasFallback then
-    -- No fallback supplied: return the bare aggregate node.
-    return { wrapped := false, terminal := terminal }
-  -- A fallback is supplied: build the coalescing wrapper (which starts out
-  -- non-terminal) and carry the aggregate's terminal marker onto it.
-  let mut wrapperTerminal := false
-  wrapperTerminal := terminal
-  return { wrapped := true, terminal := wrapperTerminal }
+    (isTerminalAggregation hasFallback : Bool) : ResolvedExpr :=
+  { wrapped := false, terminal := false }
 -- impl-end
 
 -- proof-start
@@ -85,6 +75,12 @@
       problem_spec_resolveAggregate isTerminalAggregation hasFallback
         (implementation_resolveAggregate isTerminalAggregation hasFallback) := by
   intro isTerminalAggregation hasFallback
-  unfold problem_spec_resolveAggregate implementation_resolveAggregate
-  cases hasFallback <;> simp [Id.run, pure, bind]
+  first
+  | (unfold problem_spec_resolveAggregate implementation_resolveAggregate;
+     cases isTerminalAggregation <;> cases hasFallback <;> simp [Id.run, pure, bind])
+  | (cases isTerminalAggregation <;> cases hasFallback <;> decide)
+  | (cases isTerminalAggregation <;> cases hasFallback <;> native_decide)
+  | decide
+  | native_decide
+  | simp_all [problem_spec_resolveAggregate, implementation_resolveAggregate, Id.run, pure, bind]
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Resolving an aggregate expression that carries a fallback value for the
empty-result case.

A terminal aggregation (one applied to the whole queryset at once) is marked as
such while it is being resolved. When the aggregate additionally carries a
fallback value to substitute when there is no row to aggregate, resolving it does
not return the bare aggregate: it returns a *wrapper* node — a coalescing node
whose first operand is the aggregate and whose second operand is the fallback —
so that the fallback is supplied at evaluation time.

The wrapper node carries its own "this is a terminal aggregation" marker. For the
resolved expression to be emitted in the correct position, that marker on the
wrapper must agree with the marker the aggregate itself was resolved with: a
wrapper produced while resolving a terminal aggregation must itself be marked as
terminal, and otherwise must not be.

So resolving an aggregate yields a node that is:
  * the coalescing wrapper exactly when a fallback value was supplied, and the
    bare aggregate otherwise; and
  * marked as a terminal aggregation exactly when the aggregate was resolved as a
    terminal aggregation — in both the wrapped and the unwrapped case.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The resolution
-- is modeled over two boolean observables (whether the aggregate is being
-- resolved as a terminal aggregation, and whether a fallback value was supplied);
-- constructing the coalescing wrapper and propagating the terminal marker are
-- modeled directly, so no `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- The resolved aggregate expression, recording only the two observable aspects
the resolution decides:

  * `wrapped` — the returned node is the coalescing wrapper (a fallback value was
    supplied) rather than the bare aggregate; and
  * `terminal` — the returned node is marked as a terminal aggregation (one
    applied to the whole queryset at once). -/
structure ResolvedExpr where
  wrapped  : Bool
  terminal : Bool
  deriving Repr, DecidableEq
-- pure-end

-- post-conditions-start
/-- The resolved node is fully pinned to the two inputs:

  * it is the coalescing wrapper exactly when a fallback value was supplied
    (`result.wrapped = hasFallback`); and
  * it is marked as a terminal aggregation exactly when the aggregate is being
    resolved as a terminal aggregation (`result.terminal = isTerminalAggregation`)
    — this holds whether or not the node is the wrapper, so the marker is never
    left to default to non-terminal on the wrapper.

Both components are determined for every input, so no output is left free. -/
def problem_spec_resolveAggregate
    (isTerminalAggregation hasFallback : Bool) (result : ResolvedExpr) : Prop :=
  result.wrapped = hasFallback ∧ result.terminal = isTerminalAggregation
-- post-conditions-end

-- impl-start
def implementation_resolveAggregate
    (isTerminalAggregation hasFallback : Bool) : ResolvedExpr := Id.run do
  let mut terminal := isTerminalAggregation
  if !hasFallback then
    return { wrapped := false, terminal := terminal }
  let mut wrapperTerminal := false
  wrapperTerminal := terminal
  return { wrapped := true, terminal := wrapperTerminal }
-- impl-end

-- proof-start
theorem correct_resolveAggregate :
    ∀ (isTerminalAggregation hasFallback : Bool),
      problem_spec_resolveAggregate isTerminalAggregation hasFallback
        (implementation_resolveAggregate isTerminalAggregation hasFallback) := by
  intro isTerminalAggregation hasFallback
  unfold problem_spec_resolveAggregate implementation_resolveAggregate
  cases hasFallback <;> simp [Id.run, pure, bind]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Spec problem_spec_resolveAggregate isTerminalAggregation hasFallback result := (result.wrapped = hasFallback) ∧ (result.terminal = isTerminalAggregation) FULLY PINS both output fields over the entire Bool×Bool (4-point) input domain — each input has exactly one satisfying ResolvedExpr. Any behaviorally-wrong impl (differing on ≥1 point) cannot close correct_resolveAggregate.

All 8 files confirmed byte-identical spec via swebench_unified.markers.same_spec (backend lean) = True (impl region only was edited; axioms/pure/pre/post byte-identical).

 Command per file: `bash scripts/lean_verify.sh <path>`.

POSITIVE CONTROL pos_control.lean (gold impl+proof): EXIT=0 (verifies, no sorry). #print axioms correct_resolveAggregate → depends on axioms: [propext] (clean; no sorryAx, no Classical, no custom axiom). Confirmed via pos_axioms.lean EXIT=0.

7 DISTINCT wrong impls, each with a hammer proof attempt (first | unfold+cases+simp | cases+decide | cases+native_decide | decide | native_decide | simp_all) — ALL FAIL TO CLOSE:
- atk_1 (prepatch bug / control-flow drop of op#4: wrapper keeps wrapperTerminal:=false; wrong on (T,T)): EXIT=1, unsolved goal `case true.true ⊢ False`. This is byte-identical to Solution_prepatch.lean's impl → prepatch bug reproduced.
- atk_2 (terminal := !isTerminalAggregation; wrong on all 4): EXIT=1.
- atk_3 (boundary: terminal := isTerminalAggregation && hasFallback; wrong on (T,F)): EXIT=1.
- atk_4 (control-flow-effect: always wrapped=true; wrong on (*,F)): EXIT=1.
- atk_5 (ungrounded-oracle echo: terminal := hasFallback; wrong on (T,F),(F,T)): EXIT=1.
- atk_6 (wrapped := !hasFallback; wrong on all 4): EXIT=1.
- atk_7 (constant false; wrong on 3 points): EXIT=1.

No wrong impl produced a closing clean-axiom proof, therefore NO faithful refined patch needed to be materialized or run through run_resolve (protocol step 2 vacuous — nothing to resolve). patches={}.

Refinement audit: meta.json axioms=[], deep_model_references=[], conf_skip=False. refinement.md legs: #1,#2,#3,#5 = R (type-refinement), #4 (the fix, coalesce.is_summary = c.is_summary ↔ wrapperTerminal := terminal) = I. NO A-legs, NO kind-3 legs — so A-leg correspondence audit is vacuous (nothing to reference). Model is over two boolean observables (isTerminalAggregation ↔ c.is_summary/summarize; hasFallback ↔ c.default is not None), which is faithful to patch.diff's Coalesce-wrapper construction + is_summary propagation per mapping.md. R/I-only ⇒ G-CONF differential-tests, out of A-scope here.

Verdict SOUND: ≥5 (7) distinct same-spec wrong impls attempted with aggressive proof automation; none closes; positive control verifies clean. verify⇔correct holds for this fully-determined spec. No evidence of verify⇏correct.

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
Resolving an aggregate expression that carries a fallback value for the
empty-result case.

A terminal aggregation (one applied to the whole queryset at once) is marked as
such while it is being resolved. When the aggregate additionally carries a
fallback value to substitute when there is no row to aggregate, resolving it does
not return the bare aggregate: it returns a *wrapper* node — a coalescing node
whose first operand is the aggregate and whose second operand is the fallback —
so that the fallback is supplied at evaluation time.

The wrapper node carries its own "this is a terminal aggregation" marker. For the
resolved expression to be emitted in the correct position, that marker on the
wrapper must agree with the marker the aggregate itself was resolved with: a
wrapper produced while resolving a terminal aggregation must itself be marked as
terminal, and otherwise must not be.

So resolving an aggregate yields a node that is:
  * the coalescing wrapper exactly when a fallback value was supplied, and the
    bare aggregate otherwise; and
  * marked as a terminal aggregation exactly when the aggregate was resolved as a
    terminal aggregation — in both the wrapped and the unwrapped case.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The resolution
-- is modeled over two boolean observables (whether the aggregate is being
-- resolved as a terminal aggregation, and whether a fallback value was supplied);
-- constructing the coalescing wrapper and propagating the terminal marker are
-- modeled directly, so no `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- The resolved aggregate expression, recording only the two observable aspects
the resolution decides:

  * `wrapped` — the returned node is the coalescing wrapper (a fallback value was
    supplied) rather than the bare aggregate; and
  * `terminal` — the returned node is marked as a terminal aggregation (one
    applied to the whole queryset at once). -/
structure ResolvedExpr where
  wrapped  : Bool
  terminal : Bool
  deriving Repr, DecidableEq
-- pure-end

-- post-conditions-start
/-- The resolved node is fully pinned to the two inputs:

  * it is the coalescing wrapper exactly when a fallback value was supplied
    (`result.wrapped = hasFallback`); and
  * it is marked as a terminal aggregation exactly when the aggregate is being
    resolved as a terminal aggregation (`result.terminal = isTerminalAggregation`)
    — this holds whether or not the node is the wrapper, so the marker is never
    left to default to non-terminal on the wrapper.

Both components are determined for every input, so no output is left free. -/
def problem_spec_resolveAggregate
    (isTerminalAggregation hasFallback : Bool) (result : ResolvedExpr) : Prop :=
  result.wrapped = hasFallback ∧ result.terminal = isTerminalAggregation
-- post-conditions-end

-- impl-start
def implementation_resolveAggregate
    (isTerminalAggregation hasFallback : Bool) : ResolvedExpr := Id.run do
  let mut terminal := isTerminalAggregation
  if !hasFallback then
    return { wrapped := false, terminal := terminal }
  let mut wrapperTerminal := false
  wrapperTerminal := terminal
  return { wrapped := true, terminal := wrapperTerminal }
-- impl-end

-- proof-start
theorem correct_resolveAggregate :
    ∀ (isTerminalAggregation hasFallback : Bool),
      problem_spec_resolveAggregate isTerminalAggregation hasFallback
        (implementation_resolveAggregate isTerminalAggregation hasFallback) := by
  intro isTerminalAggregation hasFallback
  unfold problem_spec_resolveAggregate implementation_resolveAggregate
  cases hasFallback <;> simp [Id.run, pure, bind]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Spec problem_spec_resolveAggregate isTerminalAggregation hasFallback result := (result.wrapped = hasFallback) ∧ (result.terminal = isTerminalAggregation) FULLY PINS both output fields over the entire Bool×Bool (4-point) input domain — each input has exactly one satisfying ResolvedExpr. Any behaviorally-wrong impl (differing on ≥1 point) cannot close correct_resolveAggregate.

All 8 files confirmed byte-identical spec via swebench_unified.markers.same_spec (backend lean) = True (impl region only was edited; axioms/pure/pre/post byte-identical).

 Command per file: `bash scripts/lean_verify.sh <path>`.

POSITIVE CONTROL pos_control.lean (gold impl+proof): EXIT=0 (verifies, no sorry). #print axioms correct_resolveAggregate → depends on axioms: [propext] (clean; no sorryAx, no Classical, no custom axiom). Confirmed via pos_axioms.lean EXIT=0.

7 DISTINCT wrong impls, each with a hammer proof attempt (first | unfold+cases+simp | cases+decide | cases+native_decide | decide | native_decide | simp_all) — ALL FAIL TO CLOSE:
- atk_1 (prepatch bug / control-flow drop of op#4: wrapper keeps wrapperTerminal:=false; wrong on (T,T)): EXIT=1, unsolved goal `case true.true ⊢ False`. This is byte-identical to Solution_prepatch.lean's impl → prepatch bug reproduced.
- atk_2 (terminal := !isTerminalAggregation; wrong on all 4): EXIT=1.
- atk_3 (boundary: terminal := isTerminalAggregation && hasFallback; wrong on (T,F)): EXIT=1.
- atk_4 (control-flow-effect: always wrapped=true; wrong on (*,F)): EXIT=1.
- atk_5 (ungrounded-oracle echo: terminal := hasFallback; wrong on (T,F),(F,T)): EXIT=1.
- atk_6 (wrapped := !hasFallback; wrong on all 4): EXIT=1.
- atk_7 (constant false; wrong on 3 points): EXIT=1.

No wrong impl produced a closing clean-axiom proof, therefore NO faithful refined patch needed to be materialized or run through run_resolve (protocol step 2 vacuous — nothing to resolve). patches={}.

Refinement audit: meta.json axioms=[], deep_model_references=[], conf_skip=False. refinement.md legs: #1,#2,#3,#5 = R (type-refinement), #4 (the fix, coalesce.is_summary = c.is_summary ↔ wrapperTerminal := terminal) = I. NO A-legs, NO kind-3 legs — so A-leg correspondence audit is vacuous (nothing to reference). Model is over two boolean observables (isTerminalAggregation ↔ c.is_summary/summarize; hasFallback ↔ c.default is not None), which is faithful to patch.diff's Coalesce-wrapper construction + is_summary propagation per mapping.md. R/I-only ⇒ G-CONF differential-tests, out of A-scope here.

Verdict SOUND: ≥5 (7) distinct same-spec wrong impls attempted with aggressive proof automation; none closes; positive control verifies clean. verify⇔correct holds for this fully-determined spec. No evidence of verify⇏correct.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) audit of the tail of Aggregate.resolve_expression (django/db/models/aggregates.py:63-68, default-wrapping arm). Modeled domain is exactly Bool x Bool = (isTerminalAggregation=summarize, hasFallback=default is not None); spec is `result.wrapped = hasFallback ∧ result.terminal = isTerminalAggregation`.

Empirically executed the REAL gold-patched callee (coalesce.is_summary = c.is_summary) over all 4 input combinations in the worktree (settings.configure + resolve_expression on Sum(Value, default=...)):
  (F,F)->wrapped=F,terminal=F  (F,T)->T,F  (T,F)->F,T  (T,T)->T,T.
All four points agree exactly with the spec. No input rejects a value the real callee produces (not too strong) and no output is left free (fully pinned). Abstraction is sound: the FieldError branch and default.resolve_expression / c.default=None plumbing do not affect the two modeled observables (node-identity wrapper vs bare, and is_summary marker).

Cross-check on drift toward the buggy repo: the UNPATCHED base worktree gives (T,T)->terminal=F, which correctly DISAGREES with the spec — confirming the spec encodes the fix, not the bug (matches recorded G-DIFF prepatch-fail).

Structural: Solution.lean compiles (exit 0, no sorry); #print axioms correct_resolveAggregate = [propext] only (no sorryAx, genuine proof); spec region byte-identical to Solution_prepatch.lean via swebench_unified.markers.same_spec (True). No diverging input exists across the modeled domain.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Rigorous check complete. (1) same_spec(Solution.lean, Solution_prepatch.lean, lean_tables) = True — the solver-visible spec view (imports+doc+axioms+pure+post-conditions) is byte-identical between patched and prepatch; only impl/proof differ, so the spec view analyzed is the true one. (2) Mechanical leakage.screen over the spec view: 0 hard failures. Gold changed symbol = {resolve_expression} — absent from spec view; changed file django/db/models/aggregates.py and dotted module django.db.models.aggregates — absent; all gold-diff lines (coalesce.is_summary = c.is_summary, Coalesce(c, default, output_field=c._output_field_or_none), return coalesce) — none reproduced; no diff markers; no narration tokens (bug/fix/patched/previously/etc.). (3) Manual gold-reconstruction: the spec abstracts to two booleans (wrapped, terminal) on a ResolvedExpr and never names is_summary, summarize, the Coalesce class, or resolve_expression. It describes correct behavior abstractly (a coalescing wrapper produced when a fallback is supplied, carrying the aggregate's terminal marker so the resolved node is emitted in the correct position). (4) Beyond problem_statement? The public problem_statement already discloses aggregate()/annotate()/default/Coalesce/Sum and the mis-placed-column 'SELECT FROM (...)' crash. The 'coalescing wrapper'/'fallback' vocabulary is thus already public; the terminal-marker-propagation requirement is the spec of correct behavior, not disclosure of the Python edit. A solver cannot reconstruct the gold patch (file/method/is_summary assignment) from the spec view. The is_summary / resolve_expression / summarize identifiers appear ONLY in mapping.md and refinement.md, which are auditor artifacts and NOT part of the solver-visible spec view. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
