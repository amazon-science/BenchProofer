# P2 adversarial audit — pydata__xarray-3151

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -80,11 +80,10 @@
             | some n => Except.error n
             | none => Except.ok ())
 -- post-conditions-end
-
 -- impl-start
 def implementation_monotonicCheck (dims : List Dim) : Except String Unit := Id.run do
   for d in dims do
-    if d.variesBetweenInputs && !d.isMonotonic then
+    if d.isCoordDim && !d.isMonotonic then
       return Except.error d.name
   return Except.ok ()
 -- impl-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -80,12 +80,8 @@
             | some n => Except.error n
             | none => Except.ok ())
 -- post-conditions-end
-
 -- impl-start
 def implementation_monotonicCheck (dims : List Dim) : Except String Unit := Id.run do
-  for d in dims do
-    if d.variesBetweenInputs && !d.isMonotonic then
-      return Except.error d.name
   return Except.ok ()
 -- impl-end
 
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -80,10 +80,9 @@
             | some n => Except.error n
             | none => Except.ok ())
 -- post-conditions-end
-
 -- impl-start
 def implementation_monotonicCheck (dims : List Dim) : Except String Unit := Id.run do
-  for d in dims do
+  for d in dims.tail do
     if d.variesBetweenInputs && !d.isMonotonic then
       return Except.error d.name
   return Except.ok ()
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -80,10 +80,9 @@
             | some n => Except.error n
             | none => Except.ok ())
 -- post-conditions-end
-
 -- impl-start
 def implementation_monotonicCheck (dims : List Dim) : Except String Unit := Id.run do
-  for d in dims do
+  for d in dims.reverse do
     if d.variesBetweenInputs && !d.isMonotonic then
       return Except.error d.name
   return Except.ok ()
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -80,11 +80,10 @@
             | some n => Except.error n
             | none => Except.ok ())
 -- post-conditions-end
-
 -- impl-start
 def implementation_monotonicCheck (dims : List Dim) : Except String Unit := Id.run do
   for d in dims do
-    if d.variesBetweenInputs && !d.isMonotonic then
+    if d.variesBetweenInputs then
       return Except.error d.name
   return Except.ok ()
 -- impl-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -80,11 +80,10 @@
             | some n => Except.error n
             | none => Except.ok ())
 -- post-conditions-end
-
 -- impl-start
 def implementation_monotonicCheck (dims : List Dim) : Except String Unit := Id.run do
   for d in dims do
-    if d.variesBetweenInputs && !d.isMonotonic then
+    if d.variesBetweenInputs && d.isMonotonic then
       return Except.error d.name
   return Except.ok ()
 -- impl-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -80,12 +80,11 @@
             | some n => Except.error n
             | none => Except.ok ())
 -- post-conditions-end
-
 -- impl-start
 def implementation_monotonicCheck (dims : List Dim) : Except String Unit := Id.run do
   for d in dims do
     if d.variesBetweenInputs && !d.isMonotonic then
-      return Except.error d.name
+      return Except.error "x"
   return Except.ok ()
 -- impl-end
 
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -80,11 +80,10 @@
             | some n => Except.error n
             | none => Except.ok ())
 -- post-conditions-end
-
 -- impl-start
 def implementation_monotonicCheck (dims : List Dim) : Except String Unit := Id.run do
   for d in dims do
-    if d.variesBetweenInputs && !d.isMonotonic then
+    if (d.variesBetweenInputs || d.isCoordDim) && !d.isMonotonic then
       return Except.error d.name
   return Except.ok ()
 -- impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Validating that a freshly combined N-dimensional object has monotonic global
indexes.

When several datasets are merged into one by aligning them along their shared
coordinates, some dimensions are *combined across* the inputs (their coordinate
values differ between datasets, so the inputs are stacked along them) while other
coordinate dimensions are mere *bystanders* — identical in every input, and so
carried through unchanged rather than concatenated.

After the combine, the result is checked: along every dimension that was combined
across the inputs, the resulting global index must be monotonic (either
increasing or decreasing throughout); otherwise the combine is rejected with an
error naming the offending dimension.

A bystander coordinate dimension — one that does not vary between the inputs — is
NOT subjected to this requirement: its values are taken verbatim from the inputs
and may legitimately be in any order, so it must never cause the combine to be
rejected. Only dimensions actually combined across the inputs are validated.

The check scans the dimensions in order and reports the FIRST combined dimension
whose global index fails to be monotonic; if every combined dimension is
monotonic, the combine succeeds. The result is success, or the name of that first
offending dimension.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. Whether a given
-- dimension's global index is monotonic, and whether that dimension was combined
-- across the inputs, are upstream observations carried as plain data on each
-- dimension record; the decision the specification pins — which dimensions are
-- subjected to the monotonicity requirement, and which offending one is reported
-- first — is modeled deeply over those observations, so no `opaque`/`axiom`
-- callee contract is needed.
-- axioms-end

-- pure-start
/-- One dimension of a combined object, together with the observations the
validation reads about it.

* `name` — the dimension's label (reported when the dimension is the offender);
* `isCoordDim` — the dimension carries a coordinate index;
* `variesBetweenInputs` — the dimension's coordinate values differ between the
  input datasets, i.e. the inputs were combined across this dimension (as opposed
  to a bystander dimension identical in every input);
* `isMonotonic` — the dimension's global index is monotonic (increasing OR
  decreasing) throughout. -/
structure Dim where
  name : String
  isCoordDim : Bool
  variesBetweenInputs : Bool
  isMonotonic : Bool
deriving DecidableEq, Repr

/-- The label of the first dimension, in order, that was combined across the
inputs yet whose global index is not monotonic — `none` if there is no such
dimension. Bystander dimensions (those that do not vary between the inputs) are
skipped regardless of their monotonicity. -/
def firstNonMonotonicVarying (dims : List Dim) : Option String :=
  match dims with
  | [] => none
  | d :: rest =>
      if d.variesBetweenInputs && !d.isMonotonic then
        some d.name
      else
        firstNonMonotonicVarying rest
-- pure-end

-- post-conditions-start
/-- The validation succeeds (`Except.ok ()`) iff every dimension combined across
the inputs has a monotonic global index; otherwise it fails with the name of the
first such offending dimension in iteration order. A bystander dimension that
does not vary between the inputs never affects the outcome. -/
def problem_spec_monotonicCheck
    (dims : List Dim) (result : Except String Unit) : Prop :=
  result = (match firstNonMonotonicVarying dims with
            | some n => Except.error n
            | none => Except.ok ())
-- post-conditions-end

-- impl-start
def implementation_monotonicCheck (dims : List Dim) : Except String Unit := Id.run do
  for d in dims do
    if d.variesBetweenInputs && !d.isMonotonic then
      return Except.error d.name
  return Except.ok ()
-- impl-end

-- proof-start
theorem correct_monotonicCheck :
    ∀ (dims : List Dim),
      problem_spec_monotonicCheck dims (implementation_monotonicCheck dims) := by
  intro dims
  unfold problem_spec_monotonicCheck implementation_monotonicCheck
  induction dims with
  | nil => rfl
  | cons d rest ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind] at ih ⊢
    by_cases h : (d.variesBetweenInputs && !d.isMonotonic) = true
    · simp only [h, if_true, firstNonMonotonicVarying, pure]
    · simp only [h, firstNonMonotonicVarying, ih, if_false, reduceCtorEq]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: problem_spec_monotonicCheck dims result := result = (match firstNonMonotonicVarying dims with | some n => Except.error n | none => Except.ok ()). This is a TOTAL FUNCTIONAL EQUALITY over the entire input domain (all Lists of Dim) — the output is fully pinned as a deterministic function of the input, no free component. Therefore any same-spec impl that verifies must be extensionally equal to firstNonMonotonicVarying-driven gold behavior; there is no room for a divergent verifying impl. Maximally tight spec.

SAME-SPEC: all 8 attacks + pos confirmed same_spec=True via swebench_unified.markers.same_spec (lean backend); only the impl region edited, axioms/pure/pre/post byte-identical.

### ATTACKS (all run via `bash scripts/lean_verify.sh <f>`, run concurrently ≤4/batch):
- atk_1 (PREPATCH BUG: guard isCoordDim instead of variesBetweenInputs) -> exit 1, error 'unsolved goals' at proof. Prepatch reproduced.
- atk_2 (partial-domain / always Except.ok ()) -> exit 1, unsolved goals.
- atk_3 (boundary: iterate dims.tail, skip first) -> exit 1, unsolved goals.
- atk_4 (control-flow-effect: iterate dims.reverse, reports LAST offender) -> exit 1, rewrite tactic failed.
- atk_5 (ungrounded-oracle echo: raise on first variesBetweenInputs ignoring isMonotonic) -> exit 1, unsolved goals. Also atk_5b with aggressive simp_all/aesop -> exit 1, unsolved goals.
- atk_6 (negation flip: raise on varying && isMonotonic) -> exit 1, unsolved goals.
- atk_7 (wrong payload: Except.error "x" literal) -> exit 1, unsolved goals.
- atk_8 (superset guard: (variesBetweenInputs || isCoordDim) && !isMonotonic) -> exit 1, unsolved goals.

GENUINE-WRONGNESS WITNESS: eval.lean (exit 0) #eval shows concrete divergence vs gold expected: wrong1 [bystander y]=Except.error "y" vs gold Except.ok (); wrong4 [a,b varying non-mono]=Except.error "b" vs gold Except.error "a"; wrong5 [m varying monotonic]=Except.error "m" vs gold Except.ok (). So these are genuinely wrong impls whose proofs correctly cannot close — not merely hard-to-prove.

POSITIVE CONTROL: pos.lean = gold, exit 0. #print axioms correct_monotonicCheck => [propext, Quot.sound] only (clean; no sorryAx, no custom axioms).

NO PATCHES TO RESOLVE: since NO wrong impl's proof closed with clean axioms, there is no verifying-but-wrong impl to materialize a faithful patch for; the verify=>correct implication is not falsifiable here. patches={} accordingly.

REFINEMENT.MD AUDIT: 3 legs — op1 (for d in dims / for dim in concat_dims) = R; op2 (raise refinement, is_monotonic_* observation) = R; op3 (fallthrough) = I. Axioms region EMPTY, G-AX skips — no A-consumed / A-reference legs and NO kind-3 legs. The changed decision (WHICH dims are subjected to the monotonicity check) is modeled DEEPLY over per-dim observations, not axiomatized (SPEC_GUIDE §3 compliant). R-leg correspondence sound: iterating full `dims` guarding variesBetweenInputs is order-preservingly equivalent to iterating concat_dims = dims.filter(·.variesBetweenInputs). Unchanged callees is_monotonic_increasing/decreasing and _infer_concat_order_from_coords enter as grounded observations isMonotonic/variesBetweenInputs — correct. No A-leg correspondence to falsify.

VERDICT: SOUND. ≥8 distinct wrong impls (partial-domain, boundary, control-flow-effect, ungrounded-oracle echo, negation flip, wrong payload, superset guard, prepatch bug) attempted incl. aggressive tactics; none verifies. Spec fully pins output; verify=>correct holds.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Validating that a freshly combined N-dimensional object has monotonic global
indexes.

When several datasets are merged into one by aligning them along their shared
coordinates, some dimensions are *combined across* the inputs (their coordinate
values differ between datasets, so the inputs are stacked along them) while other
coordinate dimensions are mere *bystanders* — identical in every input, and so
carried through unchanged rather than concatenated.

After the combine, the result is checked: along every dimension that was combined
across the inputs, the resulting global index must be monotonic (either
increasing or decreasing throughout); otherwise the combine is rejected with an
error naming the offending dimension.

A bystander coordinate dimension — one that does not vary between the inputs — is
NOT subjected to this requirement: its values are taken verbatim from the inputs
and may legitimately be in any order, so it must never cause the combine to be
rejected. Only dimensions actually combined across the inputs are validated.

The check scans the dimensions in order and reports the FIRST combined dimension
whose global index fails to be monotonic; if every combined dimension is
monotonic, the combine succeeds. The result is success, or the name of that first
offending dimension.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. Whether a given
-- dimension's global index is monotonic, and whether that dimension was combined
-- across the inputs, are upstream observations carried as plain data on each
-- dimension record; the decision the specification pins — which dimensions are
-- subjected to the monotonicity requirement, and which offending one is reported
-- first — is modeled deeply over those observations, so no `opaque`/`axiom`
-- callee contract is needed.
-- axioms-end

-- pure-start
/-- One dimension of a combined object, together with the observations the
validation reads about it.

* `name` — the dimension's label (reported when the dimension is the offender);
* `isCoordDim` — the dimension carries a coordinate index;
* `variesBetweenInputs` — the dimension's coordinate values differ between the
  input datasets, i.e. the inputs were combined across this dimension (as opposed
  to a bystander dimension identical in every input);
* `isMonotonic` — the dimension's global index is monotonic (increasing OR
  decreasing) throughout. -/
structure Dim where
  name : String
  isCoordDim : Bool
  variesBetweenInputs : Bool
  isMonotonic : Bool
deriving DecidableEq, Repr

/-- The label of the first dimension, in order, that was combined across the
inputs yet whose global index is not monotonic — `none` if there is no such
dimension. Bystander dimensions (those that do not vary between the inputs) are
skipped regardless of their monotonicity. -/
def firstNonMonotonicVarying (dims : List Dim) : Option String :=
  match dims with
  | [] => none
  | d :: rest =>
      if d.variesBetweenInputs && !d.isMonotonic then
        some d.name
      else
        firstNonMonotonicVarying rest
-- pure-end

-- post-conditions-start
/-- The validation succeeds (`Except.ok ()`) iff every dimension combined across
the inputs has a monotonic global index; otherwise it fails with the name of the
first such offending dimension in iteration order. A bystander dimension that
does not vary between the inputs never affects the outcome. -/
def problem_spec_monotonicCheck
    (dims : List Dim) (result : Except String Unit) : Prop :=
  result = (match firstNonMonotonicVarying dims with
            | some n => Except.error n
            | none => Except.ok ())
-- post-conditions-end

-- impl-start
def implementation_monotonicCheck (dims : List Dim) : Except String Unit := Id.run do
  for d in dims do
    if d.variesBetweenInputs && !d.isMonotonic then
      return Except.error d.name
  return Except.ok ()
-- impl-end

-- proof-start
theorem correct_monotonicCheck :
    ∀ (dims : List Dim),
      problem_spec_monotonicCheck dims (implementation_monotonicCheck dims) := by
  intro dims
  unfold problem_spec_monotonicCheck implementation_monotonicCheck
  induction dims with
  | nil => rfl
  | cons d rest ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind] at ih ⊢
    by_cases h : (d.variesBetweenInputs && !d.isMonotonic) = true
    · simp only [h, if_true, firstNonMonotonicVarying, pure]
    · simp only [h, firstNonMonotonicVarying, ih, if_false, reduceCtorEq]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: problem_spec_monotonicCheck dims result := result = (match firstNonMonotonicVarying dims with | some n => Except.error n | none => Except.ok ()). This is a TOTAL FUNCTIONAL EQUALITY over the entire input domain (all Lists of Dim) — the output is fully pinned as a deterministic function of the input, no free component. Therefore any same-spec impl that verifies must be extensionally equal to firstNonMonotonicVarying-driven gold behavior; there is no room for a divergent verifying impl. Maximally tight spec.

SAME-SPEC: all 8 attacks + pos confirmed same_spec=True via swebench_unified.markers.same_spec (lean backend); only the impl region edited, axioms/pure/pre/post byte-identical.

### ATTACKS (all run via `bash scripts/lean_verify.sh <f>`, run concurrently ≤4/batch):
- atk_1 (PREPATCH BUG: guard isCoordDim instead of variesBetweenInputs) -> exit 1, error 'unsolved goals' at proof. Prepatch reproduced.
- atk_2 (partial-domain / always Except.ok ()) -> exit 1, unsolved goals.
- atk_3 (boundary: iterate dims.tail, skip first) -> exit 1, unsolved goals.
- atk_4 (control-flow-effect: iterate dims.reverse, reports LAST offender) -> exit 1, rewrite tactic failed.
- atk_5 (ungrounded-oracle echo: raise on first variesBetweenInputs ignoring isMonotonic) -> exit 1, unsolved goals. Also atk_5b with aggressive simp_all/aesop -> exit 1, unsolved goals.
- atk_6 (negation flip: raise on varying && isMonotonic) -> exit 1, unsolved goals.
- atk_7 (wrong payload: Except.error "x" literal) -> exit 1, unsolved goals.
- atk_8 (superset guard: (variesBetweenInputs || isCoordDim) && !isMonotonic) -> exit 1, unsolved goals.

GENUINE-WRONGNESS WITNESS: eval.lean (exit 0) #eval shows concrete divergence vs gold expected: wrong1 [bystander y]=Except.error "y" vs gold Except.ok (); wrong4 [a,b varying non-mono]=Except.error "b" vs gold Except.error "a"; wrong5 [m varying monotonic]=Except.error "m" vs gold Except.ok (). So these are genuinely wrong impls whose proofs correctly cannot close — not merely hard-to-prove.

POSITIVE CONTROL: pos.lean = gold, exit 0. #print axioms correct_monotonicCheck => [propext, Quot.sound] only (clean; no sorryAx, no custom axioms).

NO PATCHES TO RESOLVE: since NO wrong impl's proof closed with clean axioms, there is no verifying-but-wrong impl to materialize a faithful patch for; the verify=>correct implication is not falsifiable here. patches={} accordingly.

REFINEMENT.MD AUDIT: 3 legs — op1 (for d in dims / for dim in concat_dims) = R; op2 (raise refinement, is_monotonic_* observation) = R; op3 (fallthrough) = I. Axioms region EMPTY, G-AX skips — no A-consumed / A-reference legs and NO kind-3 legs. The changed decision (WHICH dims are subjected to the monotonicity check) is modeled DEEPLY over per-dim observations, not axiomatized (SPEC_GUIDE §3 compliant). R-leg correspondence sound: iterating full `dims` guarding variesBetweenInputs is order-preservingly equivalent to iterating concat_dims = dims.filter(·.variesBetweenInputs). Unchanged callees is_monotonic_increasing/decreasing and _infer_concat_order_from_coords enter as grounded observations isMonotonic/variesBetweenInputs — correct. No A-leg correspondence to falsify.

VERDICT: SOUND. ≥8 distinct wrong impls (partial-domain, boundary, control-flow-effect, ungrounded-oracle echo, negation flip, wrong payload, superset guard, prepatch bug) attempted incl. aggressive tactics; none verifies. Spec fully pins output; verify=>correct holds.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack: no divergence found between the modeled function and the real post-patch callee.

What the spec models: the post-concatenation monotonicity-validation loop in combine_by_coords (xarray/core/combine.py:503-511 @ base 118f4d99). Post-patch it iterates `concat_dims` and raises ValueError on the first dimension whose global index is neither monotonic-increasing nor -decreasing. Model: `implementation_monotonicCheck` scans full `dims` list, guard `variesBetweenInputs && !isMonotonic`, early-returns first offender's name; `problem_spec_monotonicCheck` pins result to `firstNonMonotonicVarying dims`.

Checks performed:
- Solution.lean compiles under lean_verify.sh, EXIT=0 (no sorry/error).
- #print axioms correct_monotonicCheck => [propext, Quot.sound]; NO sorryAx — proof is real.
- same_spec(Solution, Solution_prepatch, lean tables) = True: spec region (pure/post-conditions/axioms) byte-identical; only impl+proof differ (guard `variesBetweenInputs` post vs `isCoordDim` pre), so the buggy variant is measured against the identical spec (G-DIFF confirms prepatch fails).
- conformance_check.py runs 120,008 inputs (8 edge + 120k fuzz, seed 3151), disagreements=0.

Faithfulness crux (guard + ordering), verified against the real repo worktree:
1. Guard identity: real loop iterates `concat_dims`; `concat_dims` is exactly the coord dims that vary between inputs (built in _infer_concat_order_from_coords, combine.py:51-112, appended only when `not all(index.equals(...))`). Model's `variesBetweenInputs` <=> `dim in concat_dims` by construction. Filtered carrier = identical set.
2. Ordering (the real risk): _infer_concat_order_from_coords iterates `ds0.dims`, and Dataset.dims (dataset.py:497-506) returns Frozen(SortedKeysDict(self._dims)), whose __iter__ yields iter(sorted(...)) — alphabetical. The model's carrier `concatenated.dims` is ALSO SortedKeysDict-sorted, so `dims.filter(variesBetweenInputs)` == `concat_dims` in the SAME order. Hence the reported first-offending dimension name matches on every reachable input.
3. `concatenated.indexes.get(dim)` is always non-None for a concat_dim (every combined dim carries an index post-concat), so the dropped `if dim in concatenated` guard subsumes no live None-branch — no AttributeError path is elided.
4. `isMonotonic` = is_monotonic_increasing or is_monotonic_decreasing — grounded observation, identity map.

Spec strength: the model is neither too strong nor too weak. It is a total spec over all `List Dim` (holds for every input incl. unreachable flag combinations like variesBetweenInputs && !isCoordDim). On the real-callee-reachable domain, model output == real output for every input, including the discriminating F2P case (non-monotonic bystander coordinate must succeed — test_combine_leaving_bystander_dimensions). No diverging input exists.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes clean (no diff markers, no patched file path xarray/core/combine.py, no patched symbol combine_by_coords echoed in identifiers/comments, no narration words). Spec region is byte-identical between Solution.lean and Solution_prepatch.lean (same_spec=True), so the spec is not tuned to the gold. Semantic review: the spec view encodes only the correct behavioral contract — dimensions that vary between inputs are subjected to the monotonicity check, bystander (non-varying) coordinate dimensions are exempt — which is a direct paraphrase of the PUBLIC problem_statement ('...as will any coordinate dimensions which do not vary between each dataset', and the expectation that combine should succeed). The gold edit itself (concatenated.dims + `if dim in concatenated` guard -> `concat_dims`, deletion of the membership guard) is elided with the impl/proof and appears nowhere. Note the shared `Dim` struct carries an `isCoordDim` field, but the post-condition never references it, so the pre-patch guard is not disclosed. Judged against problem_statement only, not hints_text. No leakage beyond the public problem statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
