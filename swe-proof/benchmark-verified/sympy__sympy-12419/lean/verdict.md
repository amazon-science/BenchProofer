# P2 adversarial audit — sympy__sympy-12419

**Backend:** `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 16 admissible attacks re-run of 16 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 16 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 10 | `atk_1_prepatch.lean`, `atk_2_one_observation.lean`, `atk_3_partial_domain.lean`, `atk_4_boundary_leak.lean`, `atk_5_control_flow.lean`, `atk_6_settled_deferred.lean`, `atk_7_ungrounded_echo.lean`, `atk_8_exchange.lean`, `atk_14_pin_cmp.lean`, `atk_15_unexercised_cell.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 6 | `atk_9_alt_indicator.lean`, `atk_10_resource.lean`, `atk_11_echo.lean`, `atk_12_cost.lean`, `atk_13_cost_huge.lean`, `atk_16_alt_indicator_args.lean` |

**Non-vacuity.** The positive control `pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (16):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good)

```diff
@@ -119,15 +119,13 @@
 -- post-conditions-end
 
 -- impl-start
+  -- PREPATCH BUG (base_commit `if i == j`): every non-equal status, whatever the
+  -- indicator delivered, collapses to a plain zero. Kills the diagonal.
 def implementation_identityElement {α : Type}
     (cmp : IdxCmp) (ind : IndOutcome) (i j : α) : Elem α := Id.run do
   match cmp with
-  | .known_equal    => return .one
-  | .known_distinct => return .zero
-  | .undetermined   =>
-    match ind with
-    | .settled_zero  => return .zero
-    | .left_symbolic => return .deferred i j
+  | .known_equal => return .one
+  | _            => return .zero
 -- impl-end
 
 -- proof-start
```

Attack 2 — `atk_2_one_observation.lean` → rejected (same spec, does not verify — good)

```diff
@@ -119,15 +119,14 @@
 -- post-conditions-end
 
 -- impl-start
+  -- ONE-OBSERVATION rival: drops the IndOutcome observation and claims a
+  -- surviving symbolic indicator on EVERY undetermined pair (incl. fermi pairs).
 def implementation_identityElement {α : Type}
     (cmp : IdxCmp) (ind : IndOutcome) (i j : α) : Elem α := Id.run do
   match cmp with
   | .known_equal    => return .one
   | .known_distinct => return .zero
-  | .undetermined   =>
-    match ind with
-    | .settled_zero  => return .zero
-    | .left_symbolic => return .deferred i j
+  | .undetermined   => return .deferred i j
 -- impl-end
 
 -- proof-start
```

Attack 3 — `atk_3_partial_domain.lean` → rejected (same spec, does not verify — good)

```diff
@@ -119,6 +119,8 @@
 -- post-conditions-end
 
 -- impl-start
+  -- PARTIAL DOMAIN: agrees on 5 of the 6 observation cells and collapses ONLY
+  -- the undetermined/left_symbolic cell (the arm the F2P test observes).
 def implementation_identityElement {α : Type}
     (cmp : IdxCmp) (ind : IndOutcome) (i j : α) : Elem α := Id.run do
   match cmp with
@@ -127,7 +129,7 @@
   | .undetermined   =>
     match ind with
     | .settled_zero  => return .zero
-    | .left_symbolic => return .deferred i j
+    | .left_symbolic => return .zero
 -- impl-end
 
 -- proof-start
```

Attack 4 — `atk_4_boundary_leak.lean` → rejected (same spec, does not verify — good)

```diff
@@ -119,11 +119,16 @@
 -- post-conditions-end
 
 -- impl-start
+  -- BOUNDARY: reads the indicator on the DECIDED known_distinct branch too, so a
+  -- known-distinct pair whose indicator stayed symbolic reports the indicator.
 def implementation_identityElement {α : Type}
     (cmp : IdxCmp) (ind : IndOutcome) (i j : α) : Elem α := Id.run do
   match cmp with
   | .known_equal    => return .one
-  | .known_distinct => return .zero
+  | .known_distinct =>
+    match ind with
+    | .settled_zero  => return .zero
+    | .left_symbolic => return .deferred i j
   | .undetermined   =>
     match ind with
     | .settled_zero  => return .zero
```

Attack 5 — `atk_5_control_flow.lean` → rejected (same spec, does not verify — good)

```diff
@@ -119,15 +119,21 @@
 -- post-conditions-end
 
 -- impl-start
+  -- CONTROL-FLOW EFFECT: obtains the indicator FIRST and lets a self-settled
+  -- indicator override the known_equal classification (wrong precedence).
 def implementation_identityElement {α : Type}
     (cmp : IdxCmp) (ind : IndOutcome) (i j : α) : Elem α := Id.run do
-  match cmp with
-  | .known_equal    => return .one
-  | .known_distinct => return .zero
-  | .undetermined   =>
-    match ind with
-    | .settled_zero  => return .zero
-    | .left_symbolic => return .deferred i j
+  match ind with
+  | .settled_zero =>
+    match cmp with
+    | .known_equal    => return .zero
+    | .known_distinct => return .zero
+    | .undetermined   => return .zero
+  | .left_symbolic =>
+    match cmp with
+    | .known_equal    => return .one
+    | .known_distinct => return .zero
+    | .undetermined   => return .deferred i j
 -- impl-end
 
 -- proof-start
```

Attack 6 — `atk_6_settled_deferred.lean` → rejected (same spec, does not verify — good)

```diff
@@ -119,6 +119,8 @@
 -- post-conditions-end
 
 -- impl-start
+  -- BOUNDARY COMPLEMENT: reports a symbolic indicator on the undetermined pairs
+  -- where obtaining it actually SETTLED them to a plain zero (fermi pairs).
 def implementation_identityElement {α : Type}
     (cmp : IdxCmp) (ind : IndOutcome) (i j : α) : Elem α := Id.run do
   match cmp with
@@ -126,7 +128,7 @@
   | .known_distinct => return .zero
   | .undetermined   =>
     match ind with
-    | .settled_zero  => return .zero
+    | .settled_zero  => return .deferred i j
     | .left_symbolic => return .deferred i j
 -- impl-end
 
```

Attack 7 — `atk_7_ungrounded_echo.lean` → rejected (same spec, does not verify — good)

```diff
@@ -119,15 +119,11 @@
 -- post-conditions-end
 
 -- impl-start
+  -- UNGROUNDED ORACLE ECHO: calls the spec's own `elemOf` but PINS the indicator
+  -- observation to .left_symbolic instead of reading the one it was handed.
 def implementation_identityElement {α : Type}
     (cmp : IdxCmp) (ind : IndOutcome) (i j : α) : Elem α := Id.run do
-  match cmp with
-  | .known_equal    => return .one
-  | .known_distinct => return .zero
-  | .undetermined   =>
-    match ind with
-    | .settled_zero  => return .zero
-    | .left_symbolic => return .deferred i j
+  return elemOf cmp .left_symbolic i j
 -- impl-end
 
 -- proof-start
```

Attack 8 — `atk_8_exchange.lean` → rejected (same spec, does not verify — good)

```diff
@@ -119,6 +119,7 @@
 -- post-conditions-end
 
 -- impl-start
+  -- POSITION EXCHANGE: the deferred indicator is built on the swapped pair.
 def implementation_identityElement {α : Type}
     (cmp : IdxCmp) (ind : IndOutcome) (i j : α) : Elem α := Id.run do
   match cmp with
@@ -127,7 +128,7 @@
   | .undetermined   =>
     match ind with
     | .settled_zero  => return .zero
-    | .left_symbolic => return .deferred i j
+    | .left_symbolic => return .deferred j i
 -- impl-end
 
 -- proof-start
```

Attack 9 — `atk_14_pin_cmp.lean` → rejected (same spec, does not verify — good)

```diff
@@ -119,15 +119,11 @@
 -- post-conditions-end
 
 -- impl-start
+  -- UNGROUNDED ORACLE ECHO (first observation): calls the spec's own `elemOf`
+  -- but PINS the classification to .undetermined instead of reading it.
 def implementation_identityElement {α : Type}
     (cmp : IdxCmp) (ind : IndOutcome) (i j : α) : Elem α := Id.run do
-  match cmp with
-  | .known_equal    => return .one
-  | .known_distinct => return .zero
-  | .undetermined   =>
-    match ind with
-    | .settled_zero  => return .zero
-    | .left_symbolic => return .deferred i j
+  return elemOf .undetermined ind i j
 -- impl-end
 
 -- proof-start
```

Attack 10 — `atk_15_unexercised_cell.lean` → rejected (same spec, does not verify — good)

```diff
@@ -119,10 +119,16 @@
 -- post-conditions-end
 
 -- impl-start
+  -- UNEXERCISED CELL: wrong ONLY on known_equal/settled_zero, the single cell my
+  -- 1444-pair sweep of the real callee never populated. If the spec left it free
+  -- this verifies and no behavioural fuzz over real SymPy objects could see it.
 def implementation_identityElement {α : Type}
     (cmp : IdxCmp) (ind : IndOutcome) (i j : α) : Elem α := Id.run do
   match cmp with
-  | .known_equal    => return .one
+  | .known_equal    =>
+    match ind with
+    | .settled_zero  => return .zero
+    | .left_symbolic => return .one
   | .known_distinct => return .zero
   | .undetermined   =>
     match ind with
```

Attack 11 — `atk_9_alt_indicator.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -119,15 +119,24 @@
 -- post-conditions-end
 
 -- impl-start
+  -- ALTERNATIVE DEFERRED INDICATOR: extensionally the frozen decision, written
+  -- indicator-first. Its faithful patch realizes `.deferred i j` as a DIFFERENT
+  -- symbolic equality indicator (Piecewise), which `Elem.deferred`'s own reading
+  -- ('a symbolic value, distinct from zero, resolving to one iff i,j coincide')
+  -- permits and mapping.md pins only by fiat to KroneckerDelta.
 def implementation_identityElement {α : Type}
     (cmp : IdxCmp) (ind : IndOutcome) (i j : α) : Elem α := Id.run do
-  match cmp with
-  | .known_equal    => return .one
-  | .known_distinct => return .zero
-  | .undetermined   =>
-    match ind with
-    | .settled_zero  => return .zero
-    | .left_symbolic => return .deferred i j
+  match ind with
+  | .settled_zero =>
+    match cmp with
+    | .known_equal    => return .one
+    | .known_distinct => return .zero
+    | .undetermined   => return .zero
+  | .left_symbolic =>
+    match cmp with
+    | .known_equal    => return .one
+    | .known_distinct => return .zero
+    | .undetermined   => return .deferred i j
 -- impl-end
 
 -- proof-start
```

Attack 12 — `atk_10_resource.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -119,12 +119,16 @@
 -- post-conditions-end
 
 -- impl-start
+  -- RESOURCE / NON-MODELED COST: extensionally the frozen decision, but it first
+  -- performs bulk work the postcondition does not observe (partial-correctness
+  -- reading: cost is not a modeled output). Its faithful patch scales that work up.
 def implementation_identityElement {α : Type}
     (cmp : IdxCmp) (ind : IndOutcome) (i j : α) : Elem α := Id.run do
-  match cmp with
-  | .known_equal    => return .one
-  | .known_distinct => return .zero
-  | .undetermined   =>
+  let spin : Nat := (List.range 64).foldl (fun a _ => a) 0
+  match spin, cmp with
+  | _, .known_equal    => return .one
+  | _, .known_distinct => return .zero
+  | _, .undetermined   =>
     match ind with
     | .settled_zero  => return .zero
     | .left_symbolic => return .deferred i j
```

Attack 13 — `atk_11_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -119,15 +119,11 @@
 -- post-conditions-end
 
 -- impl-start
+  -- ORACLE ECHO (correct): defers wholesale to the spec's own `elemOf`. Expected
+  -- to verify AND resolve -- the control that proves the resolve leg discriminates.
 def implementation_identityElement {α : Type}
     (cmp : IdxCmp) (ind : IndOutcome) (i j : α) : Elem α := Id.run do
-  match cmp with
-  | .known_equal    => return .one
-  | .known_distinct => return .zero
-  | .undetermined   =>
-    match ind with
-    | .settled_zero  => return .zero
-    | .left_symbolic => return .deferred i j
+  return elemOf cmp ind i j
 -- impl-end
 
 -- proof-start
```

Attack 14 — `atk_12_cost.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -119,8 +119,13 @@
 -- post-conditions-end
 
 -- impl-start
+  -- COST / PARTIAL-CORRECTNESS: the frozen element decision, preceded by a large
+  -- terminating traversal whose result is discarded. The postcondition constrains
+  -- only the RETURNED value, so unobserved cost is entirely outside the model
+  -- (docs/architecture.md 9). Its faithful patch carries the same traversal.
 def implementation_identityElement {α : Type}
     (cmp : IdxCmp) (ind : IndOutcome) (i j : α) : Elem α := Id.run do
+  let _spin : Nat := (List.range 4000000).foldl (fun a _ => a + 1) 0
   match cmp with
   | .known_equal    => return .one
   | .known_distinct => return .zero
```

Attack 15 — `atk_13_cost_huge.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -119,8 +119,10 @@
 -- post-conditions-end
 
 -- impl-start
+  -- COST LEVER, pushed: a fold over 10^12 elements ahead of the frozen decision.
 def implementation_identityElement {α : Type}
     (cmp : IdxCmp) (ind : IndOutcome) (i j : α) : Elem α := Id.run do
+  let _spin : Nat := (List.range 1000000000000).foldl (fun a _ => a + 1) 0
   match cmp with
   | .known_equal    => return .one
   | .known_distinct => return .zero
```

Attack 16 — `atk_16_alt_indicator_args.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -119,6 +119,10 @@
 -- post-conditions-end
 
 -- impl-start
+  -- ALTERNATIVE-INDICATOR LEVER: can a verifying impl name an indicator OTHER
+  -- than the deferred indicator OF EXACTLY i AND j? (The Piecewise patch, whose
+  -- indicator differs, does NOT resolve -- so if `deferred` were free here, the
+  -- spec would be broken.)
 def implementation_identityElement {α : Type}
     (cmp : IdxCmp) (ind : IndOutcome) (i j : α) : Elem α := Id.run do
   match cmp with
@@ -127,7 +131,13 @@
   | .undetermined   =>
     match ind with
     | .settled_zero  => return .zero
-    | .left_symbolic => return .deferred i j
+    | .left_symbolic =>
+      -- a "different but equivalent" indicator: same positions, reached via an
+      -- identity detour. If the spec only demands SOME symbolic indicator, an
+      -- impl free to pick a different one would verify here.
+      let i' := (fun x => x) i
+      let j' := id j
+      return .deferred i' j'
 -- impl-end
 
 -- proof-start
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc.lean`

```lean
import Mathlib
-- imports-end

/-!
The single element of an identity matrix at a pair of (possibly symbolic) row
and column positions.

An identity matrix is one on the diagonal and zero off the diagonal. When the
two positions are concrete the answer is immediate: equal positions give one and
distinct positions give zero. But in a symbolic setting a position can be an
expression (e.g. a free integer symbol), and the equality of two such positions
need not be decidable in advance — it is only resolved once concrete values are
substituted.

The desired behavior distinguishes THREE situations for the pair of positions:

  * their equality is known to hold  → the element is one;
  * their equality is known to fail  → the element is zero;
  * their equality is not yet determined → the element is a *deferred equality
    indicator* of the two positions: a symbolic value that evaluates to one when
    the positions later turn out equal and to zero otherwise.

The essential point is the third case: when it is not yet known whether the two
positions coincide, the element must remain the deferred indicator and must NOT
be reported as a plain zero. Reporting zero there would treat an undetermined
comparison as if the positions were definitely distinct, and downstream
aggregations (such as summing the element over a range that includes the
diagonal) would then lose the diagonal contribution.

Obtaining that deferred indicator is itself an act of comparison, and it need not
leave the comparison open. The indicator is produced by an operation carrying its
own means of settling the two positions, and that means is not the one that
classified the pair as undetermined above: on some pairs it succeeds where the
earlier classification did not, and it then delivers an outright value rather
than a symbolic one. Where it settles such a pair negatively, the value it
delivers is a plain zero, and there is no symbolic indicator left to report.

The element is therefore specified over BOTH observations: how the pair of
positions is classified, and — when that classification is undetermined — what
obtaining the indicator actually delivered. On an undetermined pair the element
is exactly the latter: the symbolic indicator on the pairs where obtaining it
left the comparison open, and a plain zero on the pairs where obtaining it
settled the comparison. So the requirement of the third case is precisely this: a
plain zero must not be reported for an undetermined pair whose indicator was left
SYMBOLIC. That is what keeps the diagonal contribution alive under aggregation,
and demanding more than it would demand a symbolic value on pairs where none
exists.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The element is
-- modeled DEEPLY over the two observations the reported value depends on: the
-- three-valued classification of the pair of positions (known-equal,
-- known-distinct, undetermined) and, on an undetermined classification, the
-- outcome of obtaining the deferred indicator. Both are upstream observations
-- carried as plain input data, and the symbolic indicator is represented
-- structurally. So no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- The three-valued status of comparing two (possibly symbolic) positions:
* `known_equal`   — the two positions are known to coincide;
* `known_distinct`— the two positions are known to differ;
* `undetermined`  — it is not (yet) known whether they coincide. -/
inductive IdxCmp where
  | known_equal
  | known_distinct
  | undetermined
deriving DecidableEq, Repr

/-- The outcome of obtaining the deferred equality indicator of the two
positions — the second observation, read only where the classification of the
pair is `undetermined`:
* `settled_zero`  — obtaining the indicator settled the two positions
  negatively, so what it delivered is a plain zero and no symbolic value
  remains;
* `left_symbolic` — obtaining the indicator left the comparison open, so what it
  delivered is a genuine symbolic indicator of the two positions. -/
inductive IndOutcome where
  | settled_zero
  | left_symbolic
deriving DecidableEq, Repr

/-- The value of a single matrix element at positions `i, j` (each of position
type `α`):
* `one`         — the constant one;
* `zero`        — the constant zero;
* `deferred i j`— the deferred equality indicator of `i` and `j` (a symbolic
  value, distinct from `zero`, that resolves to one iff `i` and `j` coincide). -/
inductive Elem (α : Type) where
  | one
  | zero
  | deferred (i j : α)
deriving Repr

/-- The element dictated by the two observations: the classification of the pair
of positions decides first, and only on an undetermined classification does the
outcome of obtaining the deferred indicator decide between the symbolic
indicator and a plain zero. -/
def elemOf {α : Type} (cmp : IdxCmp) (ind : IndOutcome) (i j : α) : Elem α :=
  match cmp with
  | .known_equal    => .one
  | .known_distinct => .zero
  | .undetermined   =>
    match ind with
    | .settled_zero  => .zero
    | .left_symbolic => .deferred i j
-- pure-end

-- post-conditions-start
/-- The reported element is exactly the one dictated by the two observations: one
when the positions are known equal, zero when they are known distinct, and — when
their equality is undetermined — exactly what obtaining the deferred indicator
delivered, which is the deferred indicator of those two positions (NOT a plain
zero) on every pair where that indicator was left symbolic. -/
def problem_spec_identityElement {α : Type}
    (cmp : IdxCmp) (ind : IndOutcome) (i j : α) (result : Elem α) : Prop :=
  result = elemOf cmp ind i j
-- post-conditions-end

-- impl-start
def implementation_identityElement {α : Type}
    (cmp : IdxCmp) (ind : IndOutcome) (i j : α) : Elem α := Id.run do
  match cmp with
  | .known_equal    => return .one
  | .known_distinct => return .zero
  | .undetermined   =>
    match ind with
    | .settled_zero  => return .zero
    | .left_symbolic => return .deferred i j
-- impl-end

-- proof-start
theorem correct_identityElement {α : Type} :
    ∀ (cmp : IdxCmp) (ind : IndOutcome) (i j : α),
      problem_spec_identityElement cmp ind i j
        (implementation_identityElement cmp ind i j) := by
  intro cmp ind i j
  cases cmp <;> cases ind <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ (A-legs / model-patch correspondence) for the lean bundle. VERDICT: SOUND. 16 same-spec attacks (all same_spec=True, all unsound_evasions=[]), 10 REJECTED by the spec, 6 verifying with clean axioms and ALL SIX faithful patches materialized and RUN through run_resolve -- every one resolved. Nothing breaks the spec.

COMMANDS: `bash scripts/lean_verify.sh <S>/<atk>.lean`; same_spec via swebench_unified.markers.same_spec + variant_scope.unsound_evasions; resolve via harness.run_resolve('sympy__sympy-12419', patch).

POSITIVE CONTROL <S>/pc.lean (byte-identical to Solution.lean, cmp confirmed): exit 0, 'correct_identityElement' does not depend on any axioms.
PREPATCH REPRODUCED: atk_1_prepatch re-encodes base_commit's two-valued `if i == j` (`| .known_equal => .one | _ => .zero`) -> exit 1, rejected on undetermined/left_symbolic. Also reproduced BEHAVIOURALLY in the worktree (<S>/wt at 479939f8c6, PYTHONPATH shim for py3.10): In[i,j]=0, all three F2P assertions False.

REJECTED (exit 1 -- the spec refuses them), with the goal each died on:
 1 atk_1_prepatch (prepatch collapse) | 2 atk_2_one_observation (drops IndOutcome; claims a live indicator on every undetermined pair -- dies on undetermined.settled_zero, i.e. the fermi cell) | 3 atk_3_partial_domain (correct on 5 of 6 cells, collapses ONLY undetermined/left_symbolic) | 4 atk_4_boundary_leak (reads the indicator on the DECIDED known_distinct branch) | 5 atk_5_control_flow (indicator consulted first, overrides known_equal -- dies on known_equal.settled_zero) | 6 atk_6_settled_deferred (symbolic indicator on pairs it actually settled) | 7 atk_7_ungrounded_echo (elemOf with `ind` PINNED to .left_symbolic) | 8 atk_8_exchange (deferred j i -- goal `pure (Elem.deferred j i) = Elem.deferred i j`) | 9 atk_14_pin_cmp (elemOf with `cmp` PINNED to .undetermined) | 10 atk_15_unexercised_cell (wrong ONLY on known_equal/settled_zero -- the single cell my 1444-pair sweep of the REAL callee never populated; the spec still pins it, so this hole is closed by construction rather than by corpus luck).

VERIFYING (exit 0 + clean axioms) -- each patch materialized, applied (git apply --check) and RESOLVED:
 atk_9_alt_indicator (indicator-first control flow; patch reads KroneckerDelta first) -> resolved=True completed=True applied=True F2P 1/1 P2P 25/25
 atk_10_resource (64-iteration unobserved work) -> resolved=True, P2P 25/25
 atk_11_echo (`elemOf cmp ind i j`; the discriminating-power control = gold refinement) -> resolved=True
 atk_12_cost (4e6-element fold) -> resolved=True (measured cost only 0.3s: the F2P assertions make just 3 `_entry` calls)
 atk_13_cost_huge (1e12-element fold) -> FAITHFUL patch resolved=True
 atk_16_alt_indicator_args (identity-detour indicator) -> resolved=True
All six: `'correct_identityElement' does not depend on any axioms` (allowed set is propext/Classical.choice/Quot.sound; none even needed).

THE ONE NEAR-MISS, AND WHY IT IS NOT A BREAK. <S>/probe_piecewise_indicator.diff returns `Piecewise((1, Eq(i,j)), (0, True))` instead of KroneckerDelta. It DOES NOT RESOLVE: resolved=False completed=True applied=True, 3 consistent attempts, F2P test_Identity fails while P2P stays 25/25 (so it is a real wrong-result rejection, not a collection failure). Root cause measured: `Sum(Sum(PW,(i,0,n-1)),(j,0,n-1)).subs(n,3).doit()` returns an unevaluated Piecewise sum instead of 3, because KroneckerDelta's inner sum collapses to `Piecewise((1, (0<=j)&(j<=2)),(0,True))` and Piecewise's does not.

Both indicators satisfy the prose characterization of `Elem.deferred` verbatim ('a symbolic value, distinct from zero, that resolves to one iff i and j coincide' -- I confirmed both are !=0 and both subs to 1/0 correctly). So this is a genuine gap between the DOC COMMENT and the required behavior.

It is NOT a G-EQ break, because no same-spec impl whose faithful image is that patch verifies: `Elem` has exactly three constructors, so the postcondition `result = elemOf cmp ind i j` pins the undetermined/left_symbolic arm to `.deferred i j` -- the indicator OF EXACTLY i AND j -- and offers no way to name a different indicator. atk_16 probed precisely this and only verified because the `id` detour reduces to the same term; its patch resolves. atk_8/atk_9-exchange probed the adjacent freedom and were rejected. Verify=>correct therefore holds; the residue is a DOC-PRECISION observation (the prose under-determines what the inductive pins), not a spec weakness. Worth a one-line tightening of Elem.deferred's docstring to name the indicator's aggregation behavior, but it changes no obligation.

COST LEVER CLOSED PROPERLY (the partial-correctness hole named in architecture.md 9). The unexecuted-loop variant <S>/patch_atk_13_cost_huge.diff (loop actually RUN) gives resolved=False completed=False -- harness 'Test timed out after 900 seconds'. I did NOT count that as a break, because it is not a faithful image: `#eval implementation_identityElement .known_equal .left_symbolic 0 0` on atk_13 returns Elem.one in 8s, indistinguishable from the 9s baseline (<S>/atk_13_eval.lean vs atk_11_eval.lean), i.e. Lean NEVER FORCES the unused `let _spin`. Control proving the fold is genuinely expensive when forced: <S>/cost_forced.lean adds `#eval ((List.range 1000000000000).foldl ...)` and TIMES OUT at exit=124/374s. So the verified term does no such work, and the honest image binds the computation without running it -- <S>/patch_atk_13_faithful.diff -- which RESOLVES. Conclusion: the impl region cannot smuggle in cost the spec does not see, because Lean's own evaluation does not perform it either. Also note the harness routes such a case to inconclusive anyway (`_patch_not_a_faithful_refinement` / `_ungradeable_because_of_the_patch`), never to a spec verdict.

REFINEMENT.MD AUDIT (leg taxonomy, spec_guide 1.3). All 6 rows are tagged R; there are ZERO A-consumed and ZERO A-reference legs, the axioms region is empty, and no kind-3 (changed-inexpressible) leg is present -- the changed decision is modeled deeply over two carried observations and the returned value structurally, which is what 3 requires instead of axiomatizing it. So G-AX correctly skips (axiom_check.py is an honest skip stub) and there is no callee contract for me to validate; the A-leg surface is empty BY CONSTRUCTION, not by omission. I re-derived the R legs against the real repo anyway, since that is where the correspondence claim lives:
 - Rows 1-3 vs post-patch `_entry` (matexpr.py:478-482): `Eq(i,j)` + `is S.true`/`is S.false` -> IdxCmp trichotomy. Confirmed verbatim against patch.diff.
 - Rows 4-6 vs `KroneckerDelta.eval` (tensor_functions.py:158-174): I READ the real source. The fuzzy `diff.is_zero` test AND the two fermi-level branches are present exactly as mapping.md:61-69 quotes them, including the `default_sort_key` argument-order canonicalization at line 173-174 that mapping.md records as a residue. The claim that this settling is strictly RICHER than Eq's holds.
 - Correspondence re-measured INDEPENDENTLY (<S>/correspondence.py, my own pool, model transliterated through mapping.md's bijection vs the REAL patched `Identity._entry`): 1444 pairs, 0 disagreements. The 28 reported deltas are all `TypeError('Invalid NaN comparison')` raised by the real callee on nan operands -- outside the total model's domain, not model/callee divergence. mapping.md's witness re-measured exactly: Eq(p,q)=Eq(p,q), `_entry`(p,q)=0, cmp=undetermined ind=settled_zero. One-observation regression control CAUGHT at (p,q): model ('deferred',p,q) vs real ('zero',) -- so the second observation is genuinely load-bearing, as claimed.
 - IndOutcome ARITY claim (mapping.md:101-103: no pair has Eq undetermined AND indicator resolving to a plain ONE, hence 2 constructors not 3) independently re-tested over 33124 pairs (<S>/indoutcome_arity.py, 60+ symbol/expression pool incl. fermi, even/odd, sign, zero, transcendental): 0 such cases. Cells found: known_distinct/Zero 6370, known_equal/One 218, undetermined/Zero 16, undetermined/symbolic 26520. Claim holds.
 - The position-EXCHANGE residue claim (mapping.md: 'rejected by the Lean spec but resolves on the real carrier, so deliberately not shipped as a reject case') is CONFIRMED on both halves: atk_8_exchange exit=1 (spec rejects) and <S>/probe_exchange_indicator.diff (returns KroneckerDelta(j,i)) resolved=True. The artifact's own documented residue is accurate.

**COVERAGE NOTE:** my sweep of the real callee never populated known_equal/settled_zero (1444 pairs) -- consistent with mapping.md's own count of only 3 such pairs in 6970. That cell is spec-pinned regardless (atk_15 proves it), so the gap is in the CORPUS, not the spec. Prior scratch dirs as152phn/or73q69z target the VELVET bundle (MatEntry/Option Bool carrier), not this lean spec; 52_7ane0 covered this spec and its counterexamples (prepatch, one-observation, partial-domain, boundary, control-flow, echo, exchange) are all re-encoded above and re-rejected.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 16 admissible attacks re-run of 16 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 16 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 10 | `atk_1_prepatch.lean`, `atk_2_one_observation.lean`, `atk_3_partial_domain.lean`, `atk_4_boundary_leak.lean`, `atk_5_control_flow.lean`, `atk_6_settled_deferred.lean`, `atk_7_ungrounded_echo.lean`, `atk_8_exchange.lean`, `atk_14_pin_cmp.lean`, `atk_15_unexercised_cell.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 6 | `atk_9_alt_indicator.lean`, `atk_10_resource.lean`, `atk_11_echo.lean`, `atk_12_cost.lean`, `atk_13_cost_huge.lean`, `atk_16_alt_indicator_args.lean` |

**Non-vacuity.** The positive control `pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (16):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 16 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_one_observation.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3_partial_domain.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4_boundary_leak.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5_control_flow.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6_settled_deferred.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7_ungrounded_echo.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8_exchange.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_14_pin_cmp.lean` → rejected (same spec, does not verify — good)

Attack 10 — `atk_15_unexercised_cell.lean` → rejected (same spec, does not verify — good)

Attack 11 — `atk_9_alt_indicator.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 12 — `atk_10_resource.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 13 — `atk_11_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 14 — `atk_12_cost.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 15 — `atk_13_cost_huge.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 16 — `atk_16_alt_indicator_args.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc.lean`

```lean
import Mathlib
-- imports-end

/-!
The single element of an identity matrix at a pair of (possibly symbolic) row
and column positions.

An identity matrix is one on the diagonal and zero off the diagonal. When the
two positions are concrete the answer is immediate: equal positions give one and
distinct positions give zero. But in a symbolic setting a position can be an
expression (e.g. a free integer symbol), and the equality of two such positions
need not be decidable in advance — it is only resolved once concrete values are
substituted.

The desired behavior distinguishes THREE situations for the pair of positions:

  * their equality is known to hold  → the element is one;
  * their equality is known to fail  → the element is zero;
  * their equality is not yet determined → the element is a *deferred equality
    indicator* of the two positions: a symbolic value that evaluates to one when
    the positions later turn out equal and to zero otherwise.

The essential point is the third case: when it is not yet known whether the two
positions coincide, the element must remain the deferred indicator and must NOT
be reported as a plain zero. Reporting zero there would treat an undetermined
comparison as if the positions were definitely distinct, and downstream
aggregations (such as summing the element over a range that includes the
diagonal) would then lose the diagonal contribution.

Obtaining that deferred indicator is itself an act of comparison, and it need not
leave the comparison open. The indicator is produced by an operation carrying its
own means of settling the two positions, and that means is not the one that
classified the pair as undetermined above: on some pairs it succeeds where the
earlier classification did not, and it then delivers an outright value rather
than a symbolic one. Where it settles such a pair negatively, the value it
delivers is a plain zero, and there is no symbolic indicator left to report.

The element is therefore specified over BOTH observations: how the pair of
positions is classified, and — when that classification is undetermined — what
obtaining the indicator actually delivered. On an undetermined pair the element
is exactly the latter: the symbolic indicator on the pairs where obtaining it
left the comparison open, and a plain zero on the pairs where obtaining it
settled the comparison. So the requirement of the third case is precisely this: a
plain zero must not be reported for an undetermined pair whose indicator was left
SYMBOLIC. That is what keeps the diagonal contribution alive under aggregation,
and demanding more than it would demand a symbolic value on pairs where none
exists.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The element is
-- modeled DEEPLY over the two observations the reported value depends on: the
-- three-valued classification of the pair of positions (known-equal,
-- known-distinct, undetermined) and, on an undetermined classification, the
-- outcome of obtaining the deferred indicator. Both are upstream observations
-- carried as plain input data, and the symbolic indicator is represented
-- structurally. So no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- The three-valued status of comparing two (possibly symbolic) positions:
* `known_equal`   — the two positions are known to coincide;
* `known_distinct`— the two positions are known to differ;
* `undetermined`  — it is not (yet) known whether they coincide. -/
inductive IdxCmp where
  | known_equal
  | known_distinct
  | undetermined
deriving DecidableEq, Repr

/-- The outcome of obtaining the deferred equality indicator of the two
positions — the second observation, read only where the classification of the
pair is `undetermined`:
* `settled_zero`  — obtaining the indicator settled the two positions
  negatively, so what it delivered is a plain zero and no symbolic value
  remains;
* `left_symbolic` — obtaining the indicator left the comparison open, so what it
  delivered is a genuine symbolic indicator of the two positions. -/
inductive IndOutcome where
  | settled_zero
  | left_symbolic
deriving DecidableEq, Repr

/-- The value of a single matrix element at positions `i, j` (each of position
type `α`):
* `one`         — the constant one;
* `zero`        — the constant zero;
* `deferred i j`— the deferred equality indicator of `i` and `j` (a symbolic
  value, distinct from `zero`, that resolves to one iff `i` and `j` coincide). -/
inductive Elem (α : Type) where
  | one
  | zero
  | deferred (i j : α)
deriving Repr

/-- The element dictated by the two observations: the classification of the pair
of positions decides first, and only on an undetermined classification does the
outcome of obtaining the deferred indicator decide between the symbolic
indicator and a plain zero. -/
def elemOf {α : Type} (cmp : IdxCmp) (ind : IndOutcome) (i j : α) : Elem α :=
  match cmp with
  | .known_equal    => .one
  | .known_distinct => .zero
  | .undetermined   =>
    match ind with
    | .settled_zero  => .zero
    | .left_symbolic => .deferred i j
-- pure-end

-- post-conditions-start
/-- The reported element is exactly the one dictated by the two observations: one
when the positions are known equal, zero when they are known distinct, and — when
their equality is undetermined — exactly what obtaining the deferred indicator
delivered, which is the deferred indicator of those two positions (NOT a plain
zero) on every pair where that indicator was left symbolic. -/
def problem_spec_identityElement {α : Type}
    (cmp : IdxCmp) (ind : IndOutcome) (i j : α) (result : Elem α) : Prop :=
  result = elemOf cmp ind i j
-- post-conditions-end

-- impl-start
def implementation_identityElement {α : Type}
    (cmp : IdxCmp) (ind : IndOutcome) (i j : α) : Elem α := Id.run do
  match cmp with
  | .known_equal    => return .one
  | .known_distinct => return .zero
  | .undetermined   =>
    match ind with
    | .settled_zero  => return .zero
    | .left_symbolic => return .deferred i j
-- impl-end

-- proof-start
theorem correct_identityElement {α : Type} :
    ∀ (cmp : IdxCmp) (ind : IndOutcome) (i j : α),
      problem_spec_identityElement cmp ind i j
        (implementation_identityElement cmp ind i j) := by
  intro cmp ind i j
  cases cmp <;> cases ind <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ (A-legs / model-patch correspondence) for the lean bundle. VERDICT: SOUND. 16 same-spec attacks (all same_spec=True, all unsound_evasions=[]), 10 REJECTED by the spec, 6 verifying with clean axioms and ALL SIX faithful patches materialized and RUN through run_resolve -- every one resolved. Nothing breaks the spec.

COMMANDS: `bash scripts/lean_verify.sh <S>/<atk>.lean`; same_spec via swebench_unified.markers.same_spec + variant_scope.unsound_evasions; resolve via harness.run_resolve('sympy__sympy-12419', patch).

POSITIVE CONTROL <S>/pc.lean (byte-identical to Solution.lean, cmp confirmed): exit 0, 'correct_identityElement' does not depend on any axioms.
PREPATCH REPRODUCED: atk_1_prepatch re-encodes base_commit's two-valued `if i == j` (`| .known_equal => .one | _ => .zero`) -> exit 1, rejected on undetermined/left_symbolic. Also reproduced BEHAVIOURALLY in the worktree (<S>/wt at 479939f8c6, PYTHONPATH shim for py3.10): In[i,j]=0, all three F2P assertions False.

REJECTED (exit 1 -- the spec refuses them), with the goal each died on:
 1 atk_1_prepatch (prepatch collapse) | 2 atk_2_one_observation (drops IndOutcome; claims a live indicator on every undetermined pair -- dies on undetermined.settled_zero, i.e. the fermi cell) | 3 atk_3_partial_domain (correct on 5 of 6 cells, collapses ONLY undetermined/left_symbolic) | 4 atk_4_boundary_leak (reads the indicator on the DECIDED known_distinct branch) | 5 atk_5_control_flow (indicator consulted first, overrides known_equal -- dies on known_equal.settled_zero) | 6 atk_6_settled_deferred (symbolic indicator on pairs it actually settled) | 7 atk_7_ungrounded_echo (elemOf with `ind` PINNED to .left_symbolic) | 8 atk_8_exchange (deferred j i -- goal `pure (Elem.deferred j i) = Elem.deferred i j`) | 9 atk_14_pin_cmp (elemOf with `cmp` PINNED to .undetermined) | 10 atk_15_unexercised_cell (wrong ONLY on known_equal/settled_zero -- the single cell my 1444-pair sweep of the REAL callee never populated; the spec still pins it, so this hole is closed by construction rather than by corpus luck).

VERIFYING (exit 0 + clean axioms) -- each patch materialized, applied (git apply --check) and RESOLVED:
 atk_9_alt_indicator (indicator-first control flow; patch reads KroneckerDelta first) -> resolved=True completed=True applied=True F2P 1/1 P2P 25/25
 atk_10_resource (64-iteration unobserved work) -> resolved=True, P2P 25/25
 atk_11_echo (`elemOf cmp ind i j`; the discriminating-power control = gold refinement) -> resolved=True
 atk_12_cost (4e6-element fold) -> resolved=True (measured cost only 0.3s: the F2P assertions make just 3 `_entry` calls)
 atk_13_cost_huge (1e12-element fold) -> FAITHFUL patch resolved=True
 atk_16_alt_indicator_args (identity-detour indicator) -> resolved=True
All six: `'correct_identityElement' does not depend on any axioms` (allowed set is propext/Classical.choice/Quot.sound; none even needed).

THE ONE NEAR-MISS, AND WHY IT IS NOT A BREAK. <S>/probe_piecewise_indicator.diff returns `Piecewise((1, Eq(i,j)), (0, True))` instead of KroneckerDelta. It DOES NOT RESOLVE: resolved=False completed=True applied=True, 3 consistent attempts, F2P test_Identity fails while P2P stays 25/25 (so it is a real wrong-result rejection, not a collection failure). Root cause measured: `Sum(Sum(PW,(i,0,n-1)),(j,0,n-1)).subs(n,3).doit()` returns an unevaluated Piecewise sum instead of 3, because KroneckerDelta's inner sum collapses to `Piecewise((1, (0<=j)&(j<=2)),(0,True))` and Piecewise's does not.

Both indicators satisfy the prose characterization of `Elem.deferred` verbatim ('a symbolic value, distinct from zero, that resolves to one iff i and j coincide' -- I confirmed both are !=0 and both subs to 1/0 correctly). So this is a genuine gap between the DOC COMMENT and the required behavior.

It is NOT a G-EQ break, because no same-spec impl whose faithful image is that patch verifies: `Elem` has exactly three constructors, so the postcondition `result = elemOf cmp ind i j` pins the undetermined/left_symbolic arm to `.deferred i j` -- the indicator OF EXACTLY i AND j -- and offers no way to name a different indicator. atk_16 probed precisely this and only verified because the `id` detour reduces to the same term; its patch resolves. atk_8/atk_9-exchange probed the adjacent freedom and were rejected. Verify=>correct therefore holds; the residue is a DOC-PRECISION observation (the prose under-determines what the inductive pins), not a spec weakness. Worth a one-line tightening of Elem.deferred's docstring to name the indicator's aggregation behavior, but it changes no obligation.

COST LEVER CLOSED PROPERLY (the partial-correctness hole named in architecture.md 9). The unexecuted-loop variant <S>/patch_atk_13_cost_huge.diff (loop actually RUN) gives resolved=False completed=False -- harness 'Test timed out after 900 seconds'. I did NOT count that as a break, because it is not a faithful image: `#eval implementation_identityElement .known_equal .left_symbolic 0 0` on atk_13 returns Elem.one in 8s, indistinguishable from the 9s baseline (<S>/atk_13_eval.lean vs atk_11_eval.lean), i.e. Lean NEVER FORCES the unused `let _spin`. Control proving the fold is genuinely expensive when forced: <S>/cost_forced.lean adds `#eval ((List.range 1000000000000).foldl ...)` and TIMES OUT at exit=124/374s. So the verified term does no such work, and the honest image binds the computation without running it -- <S>/patch_atk_13_faithful.diff -- which RESOLVES. Conclusion: the impl region cannot smuggle in cost the spec does not see, because Lean's own evaluation does not perform it either. Also note the harness routes such a case to inconclusive anyway (`_patch_not_a_faithful_refinement` / `_ungradeable_because_of_the_patch`), never to a spec verdict.

REFINEMENT.MD AUDIT (leg taxonomy, spec_guide 1.3). All 6 rows are tagged R; there are ZERO A-consumed and ZERO A-reference legs, the axioms region is empty, and no kind-3 (changed-inexpressible) leg is present -- the changed decision is modeled deeply over two carried observations and the returned value structurally, which is what 3 requires instead of axiomatizing it. So G-AX correctly skips (axiom_check.py is an honest skip stub) and there is no callee contract for me to validate; the A-leg surface is empty BY CONSTRUCTION, not by omission. I re-derived the R legs against the real repo anyway, since that is where the correspondence claim lives:
 - Rows 1-3 vs post-patch `_entry` (matexpr.py:478-482): `Eq(i,j)` + `is S.true`/`is S.false` -> IdxCmp trichotomy. Confirmed verbatim against patch.diff.
 - Rows 4-6 vs `KroneckerDelta.eval` (tensor_functions.py:158-174): I READ the real source. The fuzzy `diff.is_zero` test AND the two fermi-level branches are present exactly as mapping.md:61-69 quotes them, including the `default_sort_key` argument-order canonicalization at line 173-174 that mapping.md records as a residue. The claim that this settling is strictly RICHER than Eq's holds.
 - Correspondence re-measured INDEPENDENTLY (<S>/correspondence.py, my own pool, model transliterated through mapping.md's bijection vs the REAL patched `Identity._entry`): 1444 pairs, 0 disagreements. The 28 reported deltas are all `TypeError('Invalid NaN comparison')` raised by the real callee on nan operands -- outside the total model's domain, not model/callee divergence. mapping.md's witness re-measured exactly: Eq(p,q)=Eq(p,q), `_entry`(p,q)=0, cmp=undetermined ind=settled_zero. One-observation regression control CAUGHT at (p,q): model ('deferred',p,q) vs real ('zero',) -- so the second observation is genuinely load-bearing, as claimed.
 - IndOutcome ARITY claim (mapping.md:101-103: no pair has Eq undetermined AND indicator resolving to a plain ONE, hence 2 constructors not 3) independently re-tested over 33124 pairs (<S>/indoutcome_arity.py, 60+ symbol/expression pool incl. fermi, even/odd, sign, zero, transcendental): 0 such cases. Cells found: known_distinct/Zero 6370, known_equal/One 218, undetermined/Zero 16, undetermined/symbolic 26520. Claim holds.
 - The position-EXCHANGE residue claim (mapping.md: 'rejected by the Lean spec but resolves on the real carrier, so deliberately not shipped as a reject case') is CONFIRMED on both halves: atk_8_exchange exit=1 (spec rejects) and <S>/probe_exchange_indicator.diff (returns KroneckerDelta(j,i)) resolved=True. The artifact's own documented residue is accurate.

**COVERAGE NOTE:** my sweep of the real callee never populated known_equal/settled_zero (1444 pairs) -- consistent with mapping.md's own count of only 3 such pairs in 6970. That cell is spec-pinned regardless (atk_15 proves it), so the gap is in the CORPUS, not the spec. Prior scratch dirs as152phn/or73q69z target the VELVET bundle (MatEntry/Option Bool carrier), not this lean spec; 52_7ane0 covered this spec and its counterexamples (prepatch, one-observation, partial-domain, boundary, control-flow, echo, exchange) are all re-encoded above and re-rejected.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** SETUP. Fresh worktrees from the upstream repository at base_commit 479939f8c65c8c2908bbedc959549a257a7c0b0b:  with patch.diff APPLIED (reference for the modeled function Identity.`_entry`) and .../base unpatched (reference for the axiom-modeled callees Eq / KroneckerDelta.eval, which the patch does not touch — it only adds two imports). Confirmed post-patch `_entry` body at matexpr.py:478-483 is the three-way Eq(i,j) is S.true / is S.false / KroneckerDelta(i,j) chain. I did NOT compare against the base `_entry`; that would manufacture the patch delta as a false divergence.

**SPEC REGION IDENTITY.** swebench_unified.markers.same_spec(Solution.lean, Solution_prepatch.lean, lean backend) => True. The spec view is byte-identical across the gold and prepatch impls, so the spec I audited is the shipped one.

**LEAN.** scripts/lean_verify.sh Solution.lean => exit 0 (elaborates, no sorry). #print axioms correct_identityElement => 'does not depend on any axioms' (no sorryAx; the axioms region is legitimately empty — the changed decision is modeled deeply/structurally, nothing is axiomatized). Non-vacuity control: the refutation of the prepatch collapse, ¬ problem_spec_identityElement .undetermined .left_symbolic 0 1 .zero, elaborates — the spec really does forbid a plain zero on the surviving-indicator arm, so it is not trivially satisfiable.

ATTACK 1 — the (undetermined, KD→One) hole, the only way this spec could be TOO STRONG. If a pair existed where Eq(i,j) is unevaluated but KroneckerDelta(i,j) auto-evaluates to S.One, the model would sit in .undetermined and (since ind ≠ settled_zero) demand .deferred i j, while the real `_entry` returns S.One — a genuine divergence, and precisely what IndOutcome having only two constructors bets against. REFUTED both ways. Structurally: Equality.`__new__` (core/relational.py:306-350) reaches `dif = lhs - rhs; z = dif.is_zero; if z: return S.true` on the same difference and the same is_zero predicate that KroneckerDelta.eval (tensor_functions.py:159-162) tests first for its S.One return.

Every earlier Eq exit (structural ==, BooleanAtom, finiteness, ratio) returns a singleton, i.e. NOT undetermined. So `undetermined` already entails `(i-j).is_zero is not True`, which is exactly the guard KD needs to return S.One — the cell is unreachable, not merely unobserved. Empirically: 0 hits over 31,870 undetermined pairs (hunt2.py) including hand-built pairs where the difference is mathematically zero but structurally distinct (sin²+cos² vs 1, exp(log(x)) vs x, sqrt(x²) vs Abs(x), Abs(x)² vs x·conj(x), x-x, f(x)-f(x), zero-assumption symbols, x/x, 2x vs x+x, Rational(1,3)*3), plus CRootOf / Piecewise / Function / Dummy / GoldenRatio / non-commutative / imaginary atoms. Also 0 pairs where KD returned any fourth shape (non-One, non-Zero, non-KroneckerDelta).

ATTACK 2 — full differential sweep (hunt.py, seed 12419, independent of the bundle's own conformance_check.py corpus): 60,000 pairs over a 24-assumption symbol pool crossed in both orders plus randomized arithmetic and constants (oo, -oo, zoo, nan, pi, I, E, Float, Rational, FiniteSet, Interval, Tuple, booleans, non-commutative symbols). Model tag vs real `_entry` tag: DISAGREE = 0. Every modeled cell populated: KE/LS=589 KE/SZ=27 KD/LS=10024 KD/SZ=11038 UN/LS=33364 UN/SZ=4958. The two cells that could hide an over-strong claim both behave as specified: UN/SZ (4,958 pairs, incl. the below_fermi/above_fermi witness — Eq(p,q) unevaluated, `_entry`(p,q) = plain 0) is pinned to .zero not .deferred, and KE/SZ (27 pairs, where Eq wins with S.true while KD would have settled to zero) is pinned to .one — the model reads `ind` only under .undetermined, correctly mirroring the real method's short-circuit, so it does not over-read the second observation on the decided branches.

ATTACK 3 — the argument-ORDER residue, disclosed in mapping.md. The real KroneckerDelta constructor canonicalizes operand order via default_sort_key, which Elem.deferred does not model, so the model returns .deferred i j on both (i,j) and (j,i) while the repo returns one canonically-sorted term. This is NOT a divergence under the stated bijection (mapping.md §2: deferred i j ↦ KroneckerDelta(i,j)): verified KroneckerDelta(a,b) == KroneckerDelta(b,a), their difference is 0, and both KroneckerDelta(a,b) == `_entry`(a,b) and KroneckerDelta(b,a) == `_entry`(b,a) hold. The interpretation map is well-defined and lands on the real return value; 16,712 raw string-order mismatches are all this symmetry, none a semantic disagreement. Honestly disclosed rather than hidden, and deliberately not shipped as a reject case.

DOMAIN NOTE (not a faithfulness defect). On inputs where KroneckerDelta raises TypeError (4,214 seen — Tuple, S.true/S.false, nan mixed with numerics) the real `_entry` either raises too or the IndOutcome observation simply does not exist, so no (cmp, ind) instantiation of the spec can be formed and the spec asserts nothing false there. Likewise 1 pair where `_entry` itself raised (Tuple(1,2) vs Tuple(1,3)). The Elem/IdxCmp/IndOutcome model is total over its own inputs and makes no claim on raising carriers; that is a coverage limit belonging to G-PANEL-1, not a spec-too-strong divergence.

**CONCLUSION.** The spec is exactly as strong as the post-patch repo: it pins result = elemOf cmp ind i j across all six (cmp, ind) combinations and every one matches the real callee, with the soundness-critical UN/left_symbolic arm forced to a value structurally distinct from zero. The two carried observations are both load-bearing and measured; a one-observation model is refuted at the fermi-level pairs, and the third IndOutcome constructor the model omits is provably unreachable rather than merely unsampled. No diverging input exists. Verdict FAITHFUL.

**SETUP.** Fresh worktrees from the upstream repository at base_commit 479939f8c65c8c2908bbedc959549a257a7c0b0b:  with patch.diff APPLIED (reference for the modeled function Identity.`_entry`) and .../base unpatched (reference for the axiom-modeled callees Eq / KroneckerDelta.eval, which the patch does not touch — it only adds two imports). Confirmed post-patch `_entry` body at matexpr.py:478-483 is the three-way Eq(i,j) is S.true / is S.false / KroneckerDelta(i,j) chain. I did NOT compare against the base `_entry`; that would manufacture the patch delta as a false divergence.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** SCOPE/DISPOSITION: No relaxation is in play. meta.json has NO `relaxed_leakage` key (checked: 'relaxed_leakage' absent from json.dumps(meta)) and there is NO RELAXED_LEAKAGE.md anywhere in the bundle or instance dir. So I judged this as an ordinary strict leakage review, not an inherited relaxation. I also grepped every bundle file (lean/*.md, *.py, *.lean) for reviewer-directed text (auditor|reviewer|panel|honest verdict|NO-LEAKAGE|should submit|rubber): the only hits are verdict.md's role headings, which merely restate prior machine statuses and do not instruct me how to record. Nothing in the bundle addresses this panel or tells me what to submit.

**SPEC REGION IDENTITY:** markers.same_spec(Solution.lean, Solution_prepatch.lean, lean tables) = True, so the prepatch variant attacks the identical contract. Computed markers.region_hashes on the live Solution.lean: spec_view=5423a1fc1ab4fc24..., byte-matching the G-HYGIENE stamp's recorded region_hashes exactly (all 6 regions identical). NOTE (non-leak, recorded for the record): meta.json's TOP-LEVEL region_hashes block is STALE relative to the live file (spec_view=368cefaec8ff07ca... vs live 5423a1fc1ab4fc24...); the authoritative G-HYGIENE gate data matches the live artifact, and I confirmed this staleness is a harness-wide pattern (9 of 40 lean bundles sampled show the same top-level/hygiene divergence), so it is not evidence of tampering with this cell.

ARTIFACT VERIFIED MYSELF (not trusting stamps): scripts/lean_verify.sh Solution.lean -> exit 0. Injected `#print axioms correct_identityElement` before proof-end and re-verified -> "'correct_identityElement' does not depend on any axioms" (no sorryAx; proof is real, and the axioms region is genuinely empty / G-AX legitimately skips). Solution_prepatch.lean -> elaborates but 'declaration uses sorry' => G-DIFF is sound, the prepatch is really rejected.

LEXICAL LEAK SCREEN (mine, independent of the stamp): re-ran leakage.screen on the live source -> passed=True, hard_failures=[], warnings=[]. Then manually, against the computed spec_view: (a) EVERY gold changed line normalized and searched for verbatim/whitespace-insensitive reproduction -- all 10 changed lines ABSENT ('eq = Eq(i, j)', 'if eq is S.true:', 'elif eq is S.false:', 'return KroneckerDelta(i, j)', 'if i == j:', the two import lines, etc.); (b) patched file path absent (no 'matexpr', no 'sympy/matrices/...'); (c) diff markers ['@@','diff --git','+++ ','\nindex '] all absent; (d) patched repo symbols absent -- literal fixed-string counts of 'KroneckerDelta'=0, 'Kronecker'=0, 'S.Zero'=0, 'S.One'=0, 'Eq('=0, '`_entry`'=0, 'below_fermi'=0, 'above_fermi'=0, 'assumptions0'=0, 'fuzzy_not'=0, 'tensor_functions'=0, 'MatrixSymbol'=0, 'refine'=0, 'orthogonal'=0.

My first pass showed apparent S.Zero/S.One/Symbol hits; these were REGEX FALSE POSITIVES ('.' wildcard matching 'is one on th'; the 19 'Symbol' hits are all the English word 'symbolic'/'SYMBOLIC'). (e) Narration vocabulary bug|buggy|fix|fixed|patch|patched|regression|previously|incorrectly|wrong|broken = 0 occurrences. The spec view names the returned value only abstractly ('deferred equality indicator', 'symbolic value ... resolves to one iff i and j coincide') and never as KroneckerDelta.

THE ONE REAL QUESTION -- is the second observation (IndOutcome) gratuitous edit-narration? This is the most leak-adjacent content, since it describes a mechanism (a second, richer comparison that can self-settle to zero) that is NOT derivable from the problem_statement ('kroneckerdelta', 'eq(', 'deferred', 'undetermined' all absent from problem_statement; KroneckerDelta appears only in hints_text, which is correctly out of scope). I tested it two ways rather than accepting refinement.md's claim.

  (1) LOAD-BEARING FOR BUG-REJECTION? No -- and this matters. I authored a ONE-observation spec (IdxCmp only, undetermined -> deferred i j) with the prepatch two-valued collapse impl and ran lean_verify: it FAILS ('j is not definitionally equal to impl_prepatch IdxCmp.undetermined i j', case undetermined). So IndOutcome is NOT what rejects the bug; the trichotomy alone already does. IndOutcome is therefore a FAITHFULNESS obligation, not a discriminator smuggled in to make the prepatch fail.

(2) IS THAT FAITHFULNESS CLAIM REAL? Yes -- measured against the real repo, not the bundle's assertion. Built a worktree at base_commit 479939f8c65c8c2908bbedc959549a257a7c0b0b, applied patch.diff (confirmed the post-patch `_entry` body), and ran the fermi witness under python:3.9-slim (the tree needs <=3.9; py3.12 dies on 'from collections import Mapping'): p=Symbol('p',below_fermi=True), q=Symbol('q',above_fermi=True) gives Eq(p,q)=Eq(p,q) with `is S.true`=False AND `is S.false`=False (genuinely UNDETERMINED), yet KroneckerDelta(p,q) is S.Zero=True and Identity(n).`_entry`(p,q) = 0 -- a PLAIN zero. A one-observation spec would mandate a non-zero indicator there and be UNFAITHFUL to the real patched code.

I also re-ran conformance_check.py against that real patched tree: checked=120000 disagreements=0, every modeled cell populated including undetermined/settled_zero=11109 -- and confirmed by reading the script that its oracle is the REAL Identity.`_entry` (ident.`_entry`(u,v)), not an in-process replica of the model. So the second observation is compelled by faithfulness to behavior the solver must reproduce anyway. Crucially, the spec view discloses this at the level of BEHAVIOR the fix must exhibit, not of the edit: it says an undetermined pair whose indicator was left symbolic must not report plain zero, and that obtaining the indicator may itself settle the pair. It never names KroneckerDelta, Eq, the import, the file, or the if/elif chain -- a solver still must discover WHICH SymPy construct is the deferred indicator and where to change it.

**CORE GATES THE DISPOSITION LEANS ON:** G-VERIFY pass (re-verified by me, axioms clean), G-DIFF pass (re-verified: prepatch sorry), G-HYGIENE pass (region hashes match live file), G-LEAK pass (re-ran screen), G-CONF pass (re-ran, 120000/0 against the real callee), G-MUT killed 16/16, G-PBT SOUND, G-INTEGRITY pass, G-RESOLVE pass. The recorded G-EQ / G-PANEL-1/2/3 fails are all 'the audit role did not run; 0 admissible attacks of 0 submitted' -- an agent-launch/infrastructure outage recorded as a spec verdict, NOT a measured spec weakness, so I did not treat them as evidence of a defect in this cell.

**CONSUMER SURFACE:** confirmed eval/prompts.py ships only task.spec_view to the solver. mapping.md and refinement.md DO name KroneckerDelta, Eq, tensor_functions.py:159-176 and the fermi branch explicitly, but they are audit-only artifacts outside the spec view, so that is not consumer leakage.

**VERDICT:** NO-LEAKAGE. The spec view reproduces no gold line, names no patched file/function/symbol, carries no bug->fix narration, and its one mechanism-adjacent clause (the second comparison observation) is a faithfulness requirement I independently confirmed against the real patched callee and independently showed is NOT needed to reject the prepatch.

**SCOPE/DISPOSITION:** No relaxation is in play. meta.json has NO `relaxed_leakage` key (checked: 'relaxed_leakage' absent from json.dumps(meta)) and there is NO RELAXED_LEAKAGE.md anywhere in the bundle or instance dir. So I judged this as an ordinary strict leakage review, not an inherited relaxation. I also grepped every bundle file (lean/*.md, *.py, *.lean) for reviewer-directed text (auditor|reviewer|panel|honest verdict|NO-LEAKAGE|should submit|rubber): the only hits are verdict.md's role headings, which merely restate prior machine statuses and do not instruct me how to record. Nothing in the bundle addresses this panel or tells me what to submit.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
