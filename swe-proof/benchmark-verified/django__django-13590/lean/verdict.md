# P2 adversarial audit — django__django-13590

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

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -87,22 +87,17 @@
     (resolveExpr : Nat → Value) (v : Value) : Option Value := Id.run do
   match v with
   | .expr id =>
-      -- an expression is replaced by its resolved form
       return some (resolveExpr id)
   | .seq c elems =>
-      -- the elements may themselves be values, so resolve each independently;
-      -- then rebuild a sequence of the same container kind from the results
       let values := elems.map (resolveRef resolveExpr)
       match c with
       | .special =>
-          -- this kind requires its elements supplied individually; rebuild it
-          return some (.seq .special values)
+          return none
       | .plain =>
           return some (.seq .plain values)
       | .tupleLike =>
           return some (.seq .tupleLike values)
   | .scalar n =>
-      -- a plain scalar is returned unchanged
       return some (.scalar n)
 -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -87,22 +87,17 @@
     (resolveExpr : Nat → Value) (v : Value) : Option Value := Id.run do
   match v with
   | .expr id =>
-      -- an expression is replaced by its resolved form
       return some (resolveExpr id)
   | .seq c elems =>
-      -- the elements may themselves be values, so resolve each independently;
-      -- then rebuild a sequence of the same container kind from the results
       let values := elems.map (resolveRef resolveExpr)
       match c with
       | .special =>
-          -- this kind requires its elements supplied individually; rebuild it
           return some (.seq .special values)
       | .plain =>
           return some (.seq .plain values)
       | .tupleLike =>
-          return some (.seq .tupleLike values)
+          return some (.seq .plain values)
   | .scalar n =>
-      -- a plain scalar is returned unchanged
       return some (.scalar n)
 -- impl-end
 
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -87,22 +87,16 @@
     (resolveExpr : Nat → Value) (v : Value) : Option Value := Id.run do
   match v with
   | .expr id =>
-      -- an expression is replaced by its resolved form
       return some (resolveExpr id)
   | .seq c elems =>
-      -- the elements may themselves be values, so resolve each independently;
-      -- then rebuild a sequence of the same container kind from the results
-      let values := elems.map (resolveRef resolveExpr)
       match c with
       | .special =>
-          -- this kind requires its elements supplied individually; rebuild it
-          return some (.seq .special values)
+          return some (.seq .special elems)
       | .plain =>
-          return some (.seq .plain values)
+          return some (.seq .plain elems)
       | .tupleLike =>
-          return some (.seq .tupleLike values)
+          return some (.seq .tupleLike elems)
   | .scalar n =>
-      -- a plain scalar is returned unchanged
       return some (.scalar n)
 -- impl-end
 
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -87,22 +87,17 @@
     (resolveExpr : Nat → Value) (v : Value) : Option Value := Id.run do
   match v with
   | .expr id =>
-      -- an expression is replaced by its resolved form
-      return some (resolveExpr id)
+      return some (.scalar 0)
   | .seq c elems =>
-      -- the elements may themselves be values, so resolve each independently;
-      -- then rebuild a sequence of the same container kind from the results
       let values := elems.map (resolveRef resolveExpr)
       match c with
       | .special =>
-          -- this kind requires its elements supplied individually; rebuild it
           return some (.seq .special values)
       | .plain =>
           return some (.seq .plain values)
       | .tupleLike =>
           return some (.seq .tupleLike values)
   | .scalar n =>
-      -- a plain scalar is returned unchanged
       return some (.scalar n)
 -- impl-end
 
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -87,23 +87,18 @@
     (resolveExpr : Nat → Value) (v : Value) : Option Value := Id.run do
   match v with
   | .expr id =>
-      -- an expression is replaced by its resolved form
       return some (resolveExpr id)
   | .seq c elems =>
-      -- the elements may themselves be values, so resolve each independently;
-      -- then rebuild a sequence of the same container kind from the results
       let values := elems.map (resolveRef resolveExpr)
       match c with
       | .special =>
-          -- this kind requires its elements supplied individually; rebuild it
           return some (.seq .special values)
       | .plain =>
           return some (.seq .plain values)
       | .tupleLike =>
           return some (.seq .tupleLike values)
   | .scalar n =>
-      -- a plain scalar is returned unchanged
-      return some (.scalar n)
+      return some (.scalar (n + 1))
 -- impl-end
 
 -- proof-start
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -87,22 +87,17 @@
     (resolveExpr : Nat → Value) (v : Value) : Option Value := Id.run do
   match v with
   | .expr id =>
-      -- an expression is replaced by its resolved form
       return some (resolveExpr id)
   | .seq c elems =>
-      -- the elements may themselves be values, so resolve each independently;
-      -- then rebuild a sequence of the same container kind from the results
       let values := elems.map (resolveRef resolveExpr)
       match c with
       | .special =>
-          -- this kind requires its elements supplied individually; rebuild it
-          return some (.seq .special values)
+          return some (.seq .special values.reverse)
       | .plain =>
           return some (.seq .plain values)
       | .tupleLike =>
           return some (.seq .tupleLike values)
   | .scalar n =>
-      -- a plain scalar is returned unchanged
       return some (.scalar n)
 -- impl-end
 
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -84,26 +84,8 @@
 
 -- impl-start
 def implementation_resolveValue
-    (resolveExpr : Nat → Value) (v : Value) : Option Value := Id.run do
-  match v with
-  | .expr id =>
-      -- an expression is replaced by its resolved form
-      return some (resolveExpr id)
-  | .seq c elems =>
-      -- the elements may themselves be values, so resolve each independently;
-      -- then rebuild a sequence of the same container kind from the results
-      let values := elems.map (resolveRef resolveExpr)
-      match c with
-      | .special =>
-          -- this kind requires its elements supplied individually; rebuild it
-          return some (.seq .special values)
-      | .plain =>
-          return some (.seq .plain values)
-      | .tupleLike =>
-          return some (.seq .tupleLike values)
-  | .scalar n =>
-      -- a plain scalar is returned unchanged
-      return some (.scalar n)
+    (resolveExpr : Nat → Value) (v : Value) : Option Value :=
+  some (resolveRef resolveExpr v)
 -- impl-end
 
 -- proof-start
@@ -112,15 +94,5 @@
       problem_spec_resolveValue resolveExpr v
         (implementation_resolveValue resolveExpr v) := by
   intro resolveExpr v
-  cases v with
-  | scalar n =>
-      simp only [problem_spec_resolveValue, implementation_resolveValue, resolveRef, Id.run]
-      rfl
-  | expr id =>
-      simp only [problem_spec_resolveValue, implementation_resolveValue, resolveRef, Id.run]
-      rfl
-  | seq c elems =>
-      cases c <;>
-        · simp only [problem_spec_resolveValue, implementation_resolveValue, resolveRef, Id.run]
-          rfl
+  rfl
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Resolving a value that may be a scalar, a resolvable expression, or a finite
sequence.

A value has one of three shapes:

  * a plain scalar, which carries no sub-structure;
  * a resolvable expression, which is replaced by its resolved form (the
    resolution of a single expression is supplied as a given operation
    `resolveExpr`, the SAME operation for every expression);
  * a finite sequence, which additionally carries a container kind drawn from a
    small enumeration of kinds.

Resolution is defined uniformly:

  * a scalar is returned unchanged;
  * an expression is replaced by `resolveExpr` of it;
  * a sequence is rebuilt from the independently-resolved images of its
    elements, in order — the rebuilt sequence has the SAME length and the SAME
    container kind as the original, and each element is the resolution of the
    corresponding original element.

Resolution is TOTAL: it produces a result for every input, including a sequence
of every container kind. The behavior pinned below records, for every input,
exactly which value the resolution yields.
-/

-- axioms-start
-- No unchanged outside callee is consumed as a proof axiom. The resolution of a
-- single expression is modeled as an arbitrary parameter `resolveExpr : Nat →
-- Value`: the modeled behavior is solely HOW a composite value is rebuilt from
-- the resolutions of its parts, so the result is pinned for every possible
-- single-expression resolver. Hence the spec needs no `opaque`/`axiom` callee
-- contract; `resolveExpr` is universally quantified in `correct_resolveValue`.
-- axioms-end

/-- The container kind of a finite sequence. The kinds are distinguished because
the rebuilt sequence must preserve the original kind exactly; one of the kinds
(`special`) additionally requires its elements to be supplied individually to its
constructor rather than as a single bundle. -/
inductive Container where
  | plain
  | tupleLike
  | special
deriving DecidableEq

/-- A value to be resolved: a scalar, a single resolvable expression (identified
abstractly by a `Nat`), or a finite sequence carrying a container kind. -/
inductive Value where
  | scalar (n : Int)
  | expr (id : Nat)
  | seq (c : Container) (elems : List Value)

-- pure-start
/-- Reference resolution of a value. Scalars are unchanged; an expression is
replaced by `resolveExpr` of its identifier; a sequence is rebuilt from the
element-wise resolutions, preserving length and the container kind. This is a
structural recursion over the input value. -/
def resolveRef (resolveExpr : Nat → Value) : Value → Value
  | .scalar n => .scalar n
  | .expr id => resolveExpr id
  | .seq c elems => .seq c (elems.map (resolveRef resolveExpr))
-- pure-end

-- post-conditions-start
/-- The resolution result is fully pinned to the input value and the
single-expression resolver:

  * resolution always succeeds (`result = some _`);
  * the resolved value equals the structural, element-wise resolution of the
    input — a scalar maps to itself, an expression to its resolved form, and a
    sequence to a sequence of the SAME container kind and the SAME length whose
    elements are the resolutions of the originals.

No output component is left free: both the container kind and every element of
the result are determined for every input. -/
def problem_spec_resolveValue
    (resolveExpr : Nat → Value) (v : Value) (result : Option Value) : Prop :=
  result = some (resolveRef resolveExpr v)
-- post-conditions-end

-- impl-start
def implementation_resolveValue
    (resolveExpr : Nat → Value) (v : Value) : Option Value := Id.run do
  match v with
  | .expr id =>
      -- an expression is replaced by its resolved form
      return some (resolveExpr id)
  | .seq c elems =>
      -- the elements may themselves be values, so resolve each independently;
      -- then rebuild a sequence of the same container kind from the results
      let values := elems.map (resolveRef resolveExpr)
      match c with
      | .special =>
          -- this kind requires its elements supplied individually; rebuild it
          return some (.seq .special values)
      | .plain =>
          return some (.seq .plain values)
      | .tupleLike =>
          return some (.seq .tupleLike values)
  | .scalar n =>
      -- a plain scalar is returned unchanged
      return some (.scalar n)
-- impl-end

-- proof-start
theorem correct_resolveValue :
    ∀ (resolveExpr : Nat → Value) (v : Value),
      problem_spec_resolveValue resolveExpr v
        (implementation_resolveValue resolveExpr v) := by
  intro resolveExpr v
  cases v with
  | scalar n =>
      simp only [problem_spec_resolveValue, implementation_resolveValue, resolveRef, Id.run]
      rfl
  | expr id =>
      simp only [problem_spec_resolveValue, implementation_resolveValue, resolveRef, Id.run]
      rfl
  | seq c elems =>
      cases c <;>
        · simp only [problem_spec_resolveValue, implementation_resolveValue, resolveRef, Id.run]
          rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Spec problem_spec_resolveValue = `result = some (resolveRef resolveExpr v)` is a TOTAL extensional equality pinning the output uniquely for every v and every universally-quantified resolveExpr — zero behavioral freedom. Encoded 7 same-spec attacks (all same_spec=True, only impl region edited): atk_1 prepatch bug (.special->none, partial-domain / prepatch reproduction), atk_2 container swap .tupleLike->.seq.plain (boundary/type-confusion), atk_3 no-recursion elements unresolved (control-flow-effect), atk_4 ungrounded-oracle echo .expr->some(.scalar 0), atk_5 scalar off-by-one n+1 (boundary), atk_6 reverse elems in .special (control-flow-effect), atk_7 echo of spec RHS `some (resolveRef resolveExpr v)` (= gold behavior).

Verified concurrently (background bash, <=4 at a time) via scripts/lean_verify.sh with from project root. RESULTS: atk_1..atk_6 all EXIT=1, each failing on `rfl` with 'left-hand side is not definitionally equal to the right-hand side' — the spec forces the unique output so no divergent impl closes. atk_7 EXIT=0 (verifies, no sorry); `#print axioms correct_resolveValue` = [propext, Classical.choice, Quot.sound] (clean, NO sorryAx). Positive control pos_control.lean (copy of gold Solution.lean) EXIT=0. PROTOCOL step 2: atk_7 is behaviorally gold-equivalent (returns exactly the spec RHS = structural resolveRef, rebuilding .special by unpacking), so its faithful refined patch IS the gold patch.

Materialized as atk_7_faithful_patch.diff and RAN through official harness via swebench_unified.harness.run_resolve('django__django-13590', ...) with SBU_BENCHMARK=swe_bench_verified: COMPLETED=True RESOLVED=True ATTEMPTS=1 FLAKY=False NOTE='resolved'. Thus the ONLY verifying same-spec impl's faithful patch RESOLVES — no verify-without-correct gap.

A-leg audit: meta.json axioms=[], no axiom/opaque/unsafe in Solution.lean (grep NONE); refinement.md legs are R (op#2 element map), A-reference (op#1 resolveExpr universally quantified; op#3 rebuild bound to real patched Query.resolve_lookup_value via G-CONF, 100000 inputs 0 disagreements), I (op#4 scalar passthrough) — no kind-3 leg; G-AX skip stub is legitimate (no consumed callee axiom). deep_model_references correspond to the real callees (resolve_lookup_value rebuild + resolve_expression). Commands: same_spec via swebench_unified.markers.same_spec (all 7 True); verify `bash scripts/lean_verify.sh <atk>.lean`; resolve via run_resolve. Verdict SOUND: >=5 (7) distinct attacks run, only the gold-equivalent echo closes and its faithful patch resolves.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

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
Resolving a value that may be a scalar, a resolvable expression, or a finite
sequence.

A value has one of three shapes:

  * a plain scalar, which carries no sub-structure;
  * a resolvable expression, which is replaced by its resolved form (the
    resolution of a single expression is supplied as a given operation
    `resolveExpr`, the SAME operation for every expression);
  * a finite sequence, which additionally carries a container kind drawn from a
    small enumeration of kinds.

Resolution is defined uniformly:

  * a scalar is returned unchanged;
  * an expression is replaced by `resolveExpr` of it;
  * a sequence is rebuilt from the independently-resolved images of its
    elements, in order — the rebuilt sequence has the SAME length and the SAME
    container kind as the original, and each element is the resolution of the
    corresponding original element.

Resolution is TOTAL: it produces a result for every input, including a sequence
of every container kind. The behavior pinned below records, for every input,
exactly which value the resolution yields.
-/

-- axioms-start
-- No unchanged outside callee is consumed as a proof axiom. The resolution of a
-- single expression is modeled as an arbitrary parameter `resolveExpr : Nat →
-- Value`: the modeled behavior is solely HOW a composite value is rebuilt from
-- the resolutions of its parts, so the result is pinned for every possible
-- single-expression resolver. Hence the spec needs no `opaque`/`axiom` callee
-- contract; `resolveExpr` is universally quantified in `correct_resolveValue`.
-- axioms-end

/-- The container kind of a finite sequence. The kinds are distinguished because
the rebuilt sequence must preserve the original kind exactly; one of the kinds
(`special`) additionally requires its elements to be supplied individually to its
constructor rather than as a single bundle. -/
inductive Container where
  | plain
  | tupleLike
  | special
deriving DecidableEq

/-- A value to be resolved: a scalar, a single resolvable expression (identified
abstractly by a `Nat`), or a finite sequence carrying a container kind. -/
inductive Value where
  | scalar (n : Int)
  | expr (id : Nat)
  | seq (c : Container) (elems : List Value)

-- pure-start
/-- Reference resolution of a value. Scalars are unchanged; an expression is
replaced by `resolveExpr` of its identifier; a sequence is rebuilt from the
element-wise resolutions, preserving length and the container kind. This is a
structural recursion over the input value. -/
def resolveRef (resolveExpr : Nat → Value) : Value → Value
  | .scalar n => .scalar n
  | .expr id => resolveExpr id
  | .seq c elems => .seq c (elems.map (resolveRef resolveExpr))
-- pure-end

-- post-conditions-start
/-- The resolution result is fully pinned to the input value and the
single-expression resolver:

  * resolution always succeeds (`result = some _`);
  * the resolved value equals the structural, element-wise resolution of the
    input — a scalar maps to itself, an expression to its resolved form, and a
    sequence to a sequence of the SAME container kind and the SAME length whose
    elements are the resolutions of the originals.

No output component is left free: both the container kind and every element of
the result are determined for every input. -/
def problem_spec_resolveValue
    (resolveExpr : Nat → Value) (v : Value) (result : Option Value) : Prop :=
  result = some (resolveRef resolveExpr v)
-- post-conditions-end

-- impl-start
def implementation_resolveValue
    (resolveExpr : Nat → Value) (v : Value) : Option Value := Id.run do
  match v with
  | .expr id =>
      -- an expression is replaced by its resolved form
      return some (resolveExpr id)
  | .seq c elems =>
      -- the elements may themselves be values, so resolve each independently;
      -- then rebuild a sequence of the same container kind from the results
      let values := elems.map (resolveRef resolveExpr)
      match c with
      | .special =>
          -- this kind requires its elements supplied individually; rebuild it
          return some (.seq .special values)
      | .plain =>
          return some (.seq .plain values)
      | .tupleLike =>
          return some (.seq .tupleLike values)
  | .scalar n =>
      -- a plain scalar is returned unchanged
      return some (.scalar n)
-- impl-end

-- proof-start
theorem correct_resolveValue :
    ∀ (resolveExpr : Nat → Value) (v : Value),
      problem_spec_resolveValue resolveExpr v
        (implementation_resolveValue resolveExpr v) := by
  intro resolveExpr v
  cases v with
  | scalar n =>
      simp only [problem_spec_resolveValue, implementation_resolveValue, resolveRef, Id.run]
      rfl
  | expr id =>
      simp only [problem_spec_resolveValue, implementation_resolveValue, resolveRef, Id.run]
      rfl
  | seq c elems =>
      cases c <;>
        · simp only [problem_spec_resolveValue, implementation_resolveValue, resolveRef, Id.run]
          rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Spec problem_spec_resolveValue = `result = some (resolveRef resolveExpr v)` is a TOTAL extensional equality pinning the output uniquely for every v and every universally-quantified resolveExpr — zero behavioral freedom. Encoded 7 same-spec attacks (all same_spec=True, only impl region edited): atk_1 prepatch bug (.special->none, partial-domain / prepatch reproduction), atk_2 container swap .tupleLike->.seq.plain (boundary/type-confusion), atk_3 no-recursion elements unresolved (control-flow-effect), atk_4 ungrounded-oracle echo .expr->some(.scalar 0), atk_5 scalar off-by-one n+1 (boundary), atk_6 reverse elems in .special (control-flow-effect), atk_7 echo of spec RHS `some (resolveRef resolveExpr v)` (= gold behavior).

Verified concurrently (background bash, <=4 at a time) via scripts/lean_verify.sh with from project root. RESULTS: atk_1..atk_6 all EXIT=1, each failing on `rfl` with 'left-hand side is not definitionally equal to the right-hand side' — the spec forces the unique output so no divergent impl closes. atk_7 EXIT=0 (verifies, no sorry); `#print axioms correct_resolveValue` = [propext, Classical.choice, Quot.sound] (clean, NO sorryAx). Positive control pos_control.lean (copy of gold Solution.lean) EXIT=0. PROTOCOL step 2: atk_7 is behaviorally gold-equivalent (returns exactly the spec RHS = structural resolveRef, rebuilding .special by unpacking), so its faithful refined patch IS the gold patch.

Materialized as atk_7_faithful_patch.diff and RAN through official harness via swebench_unified.harness.run_resolve('django__django-13590', ...) with SBU_BENCHMARK=swe_bench_verified: COMPLETED=True RESOLVED=True ATTEMPTS=1 FLAKY=False NOTE='resolved'. Thus the ONLY verifying same-spec impl's faithful patch RESOLVES — no verify-without-correct gap.

A-leg audit: meta.json axioms=[], no axiom/opaque/unsafe in Solution.lean (grep NONE); refinement.md legs are R (op#2 element map), A-reference (op#1 resolveExpr universally quantified; op#3 rebuild bound to real patched Query.resolve_lookup_value via G-CONF, 100000 inputs 0 disagreements), I (op#4 scalar passthrough) — no kind-3 leg; G-AX skip stub is legitimate (no consumed callee axiom). deep_model_references correspond to the real callees (resolve_lookup_value rebuild + resolve_expression). Commands: same_spec via swebench_unified.markers.same_spec (all 7 True); verify `bash scripts/lean_verify.sh <atk>.lean`; resolve via run_resolve. Verdict SOUND: >=5 (7) distinct attacks run, only the gold-equivalent echo closes and its faithful patch resolves.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-drift / too-strong) audit of lean/django__django-13590. Spec: problem_spec_resolveValue pins result = some (resolveRef resolveExpr v) for Query.resolve_lookup_value (django/db/models/sql/query.py:1071). Verification performed: (1) Spec region byte-identical — swebench_unified.markers.same_spec(post,prepatch)=True and recomputed spec_view hash 891f159cf231c3b6da5003eeed99b17aaa7c4108194fc05295c8b0e19467fe5e == meta.json region_hashes.spec_view. (2) Solution.lean compiles under scripts/lean_verify.sh (exit 0); #print axioms correct_resolveValue = [propext, Classical.choice, Quot.sound] — no sorryAx, proof is genuine. Independent differential test: applied the gold patch to a clean copy of the base_commit repo (@ 755dbf39fc) and compared resolveRef against the REAL patched resolve_lookup_value over 200,000 fuzzed values (fresh seed 999) drawn from scalars/exprs/lists/plain-tuples/namedtuples of arbitrary nesting, comparing EXACT output container kind and catching any exception — 0 disagreements. The bundle's own conformance_check.py (100k inputs, seed 13590) likewise passed. (4) Too-strong checks: totality (always `some`) is faithful because the patched callee never raises in the modeled domain (namedtuple rebuild succeeds via type_(*values)); the expr branch does NOT recurse into the resolved result, matching `value = value.resolve_expression(...); return value`; resolveExpr is universally quantified (∀ resolveExpr : Nat→Value), so the model does not over-constrain the per-expression resolver; empty namedtuples, nested list-of-namedtuple, and container-kind preservation all agree. No diverging input exists; the spec neither drifts from nor is stronger than the real repo behavior.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Judged the consumer spec view (spec_view of Solution.lean: imports, docstring, axioms note, Container/Value inductives, resolveRef, problem_spec_resolveValue) against the PUBLIC problem_statement only (hints_text is empty; excluded per policy). impl and proof regions are elided in the spec view.

Mechanical screen (leakage.screen, lean flavor) PASSES with zero hard failures: no diff markers, no gold-patch line reproduced, no patched file path ('django/db/models/sql/query.py') or dotted module path, no spec-view identifier or comment echoing the patched symbol ('resolve_lookup_value'), no bug/fix narration terms. same_spec(Solution.lean, Solution_prepatch.lean) = True (spec region byte-identical), and prepatch is a genuinely different impl/proof.

Semantic assessment: the problem_statement ALREADY publicly discloses the full gold edit — that resolve_lookup_value reconstitutes list/tuple elements, that a namedtuple's constructor errors when handed a single iterator (TypeError: __new__() missing 1 required positional argument), and verbatim 'The fix is to * expand the contents of the iterator into the constructor.' The only fix-relevant content in the spec view — the three-way Container kind where 'special' 'requires its elements to be supplied individually to its constructor rather than as a single bundle', and that resolution is TOTAL (always `some _`) — is entirely within the scope of what the problem_statement states. It reveals nothing about the gold edit beyond the public task. The discriminating pre/post behavior (prepatch returns none for the .special branch) lives in the elided impl/proof, not the consumer view. No line leaks the gold edit beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
