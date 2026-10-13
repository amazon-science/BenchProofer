# P2 adversarial audit — sympy__sympy-16792

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -43,10 +43,7 @@
 def implementation_arrayArgBounds (isArrayLike : Bool) (shape : List Int) :
     List (Int × Int) := Id.run do
   let mut metadata : List (Int × Int) := []
-  if isArrayLike then
-    metadata := boundsOf shape
-  else
-    metadata := []
+  metadata := []
   return metadata
 -- impl-end
 
@@ -57,5 +54,5 @@
         (implementation_arrayArgBounds isArrayLike shape) := by
   intro isArrayLike shape
   unfold problem_spec_arrayArgBounds implementation_arrayArgBounds
-  cases isArrayLike <;> rfl
+  cases isArrayLike <;> simp [boundsOf, Id.run]
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -43,10 +43,7 @@
 def implementation_arrayArgBounds (isArrayLike : Bool) (shape : List Int) :
     List (Int × Int) := Id.run do
   let mut metadata : List (Int × Int) := []
-  if isArrayLike then
-    metadata := boundsOf shape
-  else
-    metadata := []
+  metadata := boundsOf shape
   return metadata
 -- impl-end
 
@@ -57,5 +54,5 @@
         (implementation_arrayArgBounds isArrayLike shape) := by
   intro isArrayLike shape
   unfold problem_spec_arrayArgBounds implementation_arrayArgBounds
-  cases isArrayLike <;> rfl
+  cases isArrayLike <;> simp [boundsOf, Id.run]
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -44,9 +44,9 @@
     List (Int × Int) := Id.run do
   let mut metadata : List (Int × Int) := []
   if isArrayLike then
+    metadata := []
+  else
     metadata := boundsOf shape
-  else
-    metadata := []
   return metadata
 -- impl-end
 
@@ -57,5 +57,5 @@
         (implementation_arrayArgBounds isArrayLike shape) := by
   intro isArrayLike shape
   unfold problem_spec_arrayArgBounds implementation_arrayArgBounds
-  cases isArrayLike <;> rfl
+  cases isArrayLike <;> simp [boundsOf, Id.run]
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -44,7 +44,7 @@
     List (Int × Int) := Id.run do
   let mut metadata : List (Int × Int) := []
   if isArrayLike then
-    metadata := boundsOf shape
+    metadata := shape.map (fun d => ((0 : Int), d))
   else
     metadata := []
   return metadata
@@ -57,5 +57,5 @@
         (implementation_arrayArgBounds isArrayLike shape) := by
   intro isArrayLike shape
   unfold problem_spec_arrayArgBounds implementation_arrayArgBounds
-  cases isArrayLike <;> rfl
+  cases isArrayLike <;> simp [boundsOf, Id.run]
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -44,7 +44,9 @@
     List (Int × Int) := Id.run do
   let mut metadata : List (Int × Int) := []
   if isArrayLike then
-    metadata := boundsOf shape
+    match shape with
+    | [] => metadata := [((0:Int), (0:Int))]
+    | _  => metadata := boundsOf shape
   else
     metadata := []
   return metadata
@@ -57,5 +59,5 @@
         (implementation_arrayArgBounds isArrayLike shape) := by
   intro isArrayLike shape
   unfold problem_spec_arrayArgBounds implementation_arrayArgBounds
-  cases isArrayLike <;> rfl
+  cases isArrayLike <;> cases shape <;> simp [boundsOf, Id.run]
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -44,7 +44,7 @@
     List (Int × Int) := Id.run do
   let mut metadata : List (Int × Int) := []
   if isArrayLike then
-    metadata := boundsOf shape
+    metadata := (boundsOf shape).reverse
   else
     metadata := []
   return metadata
@@ -57,5 +57,5 @@
         (implementation_arrayArgBounds isArrayLike shape) := by
   intro isArrayLike shape
   unfold problem_spec_arrayArgBounds implementation_arrayArgBounds
-  cases isArrayLike <;> rfl
+  cases isArrayLike <;> simp [boundsOf, Id.run]
 -- proof-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -44,7 +44,7 @@
     List (Int × Int) := Id.run do
   let mut metadata : List (Int × Int) := []
   if isArrayLike then
-    metadata := boundsOf shape
+    metadata := shape.map (fun d => ((1 : Int), d - 1))
   else
     metadata := []
   return metadata
@@ -57,5 +57,5 @@
         (implementation_arrayArgBounds isArrayLike shape) := by
   intro isArrayLike shape
   unfold problem_spec_arrayArgBounds implementation_arrayArgBounds
-  cases isArrayLike <;> rfl
+  cases isArrayLike <;> simp [boundsOf, Id.run]
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Computing the index-bound metadata of a procedure argument when the procedure's
argument order is pinned by the caller and the argument does not otherwise occur
in the procedure body.

A scalar argument carries no index bounds (it is a single value). An
array-valued argument — one whose value has a shape (a sequence of axis sizes) —
must instead carry, for each of its axes, the inclusive index range
`(0, size - 1)`. This index-bound metadata is what later determines whether the
argument is emitted as a pointer/array rather than a plain scalar in the
generated signature.

The behavior is stated abstractly as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract: the behavior is spelled
-- out with concrete operations (a Boolean branch and an element-wise map over a
-- shape).
-- axioms-end

-- pure-start
/-- The inclusive index range for each axis of a shape: an axis of `size` spans
indices `0 … size - 1`, modeled as the bound pair `(0, size - 1)`. -/
def boundsOf (shape : List Int) : List (Int × Int) :=
  shape.map (fun d => ((0 : Int), d - 1))
-- pure-end

-- post-conditions-start
/-- The argument's index-bound metadata is the per-dimension bound list of its
shape when the argument is array-valued, and the empty list (no bounds, i.e. a
scalar) otherwise. -/
def problem_spec_arrayArgBounds (isArrayLike : Bool) (shape : List Int)
    (result : List (Int × Int)) : Prop :=
  result = (if isArrayLike then boundsOf shape else [])
-- post-conditions-end

-- impl-start
def implementation_arrayArgBounds (isArrayLike : Bool) (shape : List Int) :
    List (Int × Int) := Id.run do
  let mut metadata : List (Int × Int) := []
  if isArrayLike then
    metadata := boundsOf shape
  else
    metadata := []
  return metadata
-- impl-end

-- proof-start
theorem correct_arrayArgBounds :
    ∀ (isArrayLike : Bool) (shape : List Int),
      problem_spec_arrayArgBounds isArrayLike shape
        (implementation_arrayArgBounds isArrayLike shape) := by
  intro isArrayLike shape
  unfold problem_spec_arrayArgBounds implementation_arrayArgBounds
  cases isArrayLike <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: total, deterministic function equality with ZERO axioms. post: problem_spec_arrayArgBounds isArrayLike shape result := result = (if isArrayLike then boundsOf shape else []); boundsOf shape = shape.map (fun d => (0, d-1)). correct_arrayArgBounds is a universally-quantified equality over all (isArrayLike, shape), so any verifying impl must be extensionally equal to the gold function on ALL inputs. There is no consumed axiom to echo (G-AX is a legitimate skip stub; the sole introduced op dimensions(s) is modeled DEEPLY as boundsOf, an A-reference validated by G-CONF: 120009 checks, 0 disagreements). This is the airtight verify=>correct case.

POSITIVE CONTROL: positive_control.lean (gold Solution.lean copy). CMD: `bash scripts/lean_verify.sh <f>` -> exit 0 (verifies). `#print axioms correct_arrayArgBounds` -> 'does not depend on any axioms' (clean, appended in pc_axioms.lean).

ATTACKS (all same_spec=True vs Solution.lean, verified via swebench_unified.markers.same_spec; impl region edited only, axioms/pure/pre/post byte-identical). CMD each: `bash scripts/lean_verify.sh atk_N.lean`. ALL FAILED TO CLOSE (exit 1, genuine 'unsolved goals'):
- atk_1 PREPATCH BUG: always [] (metadata:=[] unconditionally). exit 1. Residual goal `case true: pure [] = List.map (fun d => (0,d-1)) shape`. Reproduces the prepatch defect (array-like arg emitted as scalar).
- atk_2 UNGROUNDED-ORACLE ECHO: always boundsOf shape (ignores flag). exit 1. Residual `case false: pure (List.map ...) = []`.
- atk_3 CONTROL-FLOW/swapped branches: [] when array-like, bounds when scalar. exit 1. Both cases unsolved.
- atk_4 BOUNDARY/wrong upper bound: (0, d) instead of (0, d-1). exit 1. `case true: List.map (fun d => (0,d)) shape = List.map (fun d => (0,d-1)) shape`.
- atk_5 PARTIAL-DOMAIN: correct for all inputs except isArrayLike=true & shape=[] (returns [(0,0)] there). exit 1. Residual `case true.nil: False` (impossible to discharge) — spec forces [] there.
- atk_6 CONTROL-FLOW EFFECT: (boundsOf shape).reverse. exit 1. `case true: (List.map ...).reverse = List.map ...` (differs for len>=2).
- atk_7 OFF-BY-ONE lower bound: (1, d-1) instead of (0, d-1). exit 1. `case true: List.map (fun d => (1,d-1)) shape = List.map (fun d => (0,d-1)) shape`.

NO wrong impl produced a closing proof with clean axioms, therefore NO faithful refined patch needed to be materialized/resolve-run (the plan's step-2 obligation is vacuously satisfied — no verifying same-spec counterexample exists).

REFINEMENT.MD AUDIT: legs = I (metadata:=[] init), R (isArrayLike Boolean bijection), A-reference (boundsOf shape <-> dimensions(s)=[(S.Zero,dim-1) for dim in s.shape]; validated by G-CONF), R (else []), R (return/InputArgument.dimensions carrier). No kind-3 legs. The single A-reference correspondence holds byte-for-byte semantically (S.Zero->0, dim-1->d-1, per-dim map) and G-CONF passed over the full discrete matrix + 120009 random draws with 0 disagreements. G-AX skip stub is legitimate (no consumed callee axiom). Model<->patch correspondence sound.

Schedule: attacks encoded then verified concurrently in two background batches of 4 (pc+atk1-3, then atk4-7), <=4 at a time; all fully verified. VERDICT: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Computing the index-bound metadata of a procedure argument when the procedure's
argument order is pinned by the caller and the argument does not otherwise occur
in the procedure body.

A scalar argument carries no index bounds (it is a single value). An
array-valued argument — one whose value has a shape (a sequence of axis sizes) —
must instead carry, for each of its axes, the inclusive index range
`(0, size - 1)`. This index-bound metadata is what later determines whether the
argument is emitted as a pointer/array rather than a plain scalar in the
generated signature.

The behavior is stated abstractly as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract: the behavior is spelled
-- out with concrete operations (a Boolean branch and an element-wise map over a
-- shape).
-- axioms-end

-- pure-start
/-- The inclusive index range for each axis of a shape: an axis of `size` spans
indices `0 … size - 1`, modeled as the bound pair `(0, size - 1)`. -/
def boundsOf (shape : List Int) : List (Int × Int) :=
  shape.map (fun d => ((0 : Int), d - 1))
-- pure-end

-- post-conditions-start
/-- The argument's index-bound metadata is the per-dimension bound list of its
shape when the argument is array-valued, and the empty list (no bounds, i.e. a
scalar) otherwise. -/
def problem_spec_arrayArgBounds (isArrayLike : Bool) (shape : List Int)
    (result : List (Int × Int)) : Prop :=
  result = (if isArrayLike then boundsOf shape else [])
-- post-conditions-end

-- impl-start
def implementation_arrayArgBounds (isArrayLike : Bool) (shape : List Int) :
    List (Int × Int) := Id.run do
  let mut metadata : List (Int × Int) := []
  if isArrayLike then
    metadata := boundsOf shape
  else
    metadata := []
  return metadata
-- impl-end

-- proof-start
theorem correct_arrayArgBounds :
    ∀ (isArrayLike : Bool) (shape : List Int),
      problem_spec_arrayArgBounds isArrayLike shape
        (implementation_arrayArgBounds isArrayLike shape) := by
  intro isArrayLike shape
  unfold problem_spec_arrayArgBounds implementation_arrayArgBounds
  cases isArrayLike <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: total, deterministic function equality with ZERO axioms. post: problem_spec_arrayArgBounds isArrayLike shape result := result = (if isArrayLike then boundsOf shape else []); boundsOf shape = shape.map (fun d => (0, d-1)). correct_arrayArgBounds is a universally-quantified equality over all (isArrayLike, shape), so any verifying impl must be extensionally equal to the gold function on ALL inputs. There is no consumed axiom to echo (G-AX is a legitimate skip stub; the sole introduced op dimensions(s) is modeled DEEPLY as boundsOf, an A-reference validated by G-CONF: 120009 checks, 0 disagreements). This is the airtight verify=>correct case.

POSITIVE CONTROL: positive_control.lean (gold Solution.lean copy). CMD: `bash scripts/lean_verify.sh <f>` -> exit 0 (verifies). `#print axioms correct_arrayArgBounds` -> 'does not depend on any axioms' (clean, appended in pc_axioms.lean).

ATTACKS (all same_spec=True vs Solution.lean, verified via swebench_unified.markers.same_spec; impl region edited only, axioms/pure/pre/post byte-identical). CMD each: `bash scripts/lean_verify.sh atk_N.lean`. ALL FAILED TO CLOSE (exit 1, genuine 'unsolved goals'):
- atk_1 PREPATCH BUG: always [] (metadata:=[] unconditionally). exit 1. Residual goal `case true: pure [] = List.map (fun d => (0,d-1)) shape`. Reproduces the prepatch defect (array-like arg emitted as scalar).
- atk_2 UNGROUNDED-ORACLE ECHO: always boundsOf shape (ignores flag). exit 1. Residual `case false: pure (List.map ...) = []`.
- atk_3 CONTROL-FLOW/swapped branches: [] when array-like, bounds when scalar. exit 1. Both cases unsolved.
- atk_4 BOUNDARY/wrong upper bound: (0, d) instead of (0, d-1). exit 1. `case true: List.map (fun d => (0,d)) shape = List.map (fun d => (0,d-1)) shape`.
- atk_5 PARTIAL-DOMAIN: correct for all inputs except isArrayLike=true & shape=[] (returns [(0,0)] there). exit 1. Residual `case true.nil: False` (impossible to discharge) — spec forces [] there.
- atk_6 CONTROL-FLOW EFFECT: (boundsOf shape).reverse. exit 1. `case true: (List.map ...).reverse = List.map ...` (differs for len>=2).
- atk_7 OFF-BY-ONE lower bound: (1, d-1) instead of (0, d-1). exit 1. `case true: List.map (fun d => (1,d-1)) shape = List.map (fun d => (0,d-1)) shape`.

NO wrong impl produced a closing proof with clean axioms, therefore NO faithful refined patch needed to be materialized/resolve-run (the plan's step-2 obligation is vacuously satisfied — no verifying same-spec counterexample exists).

REFINEMENT.MD AUDIT: legs = I (metadata:=[] init), R (isArrayLike Boolean bijection), A-reference (boundsOf shape <-> dimensions(s)=[(S.Zero,dim-1) for dim in s.shape]; validated by G-CONF), R (else []), R (return/InputArgument.dimensions carrier). No kind-3 legs. The single A-reference correspondence holds byte-for-byte semantically (S.Zero->0, dim-1->d-1, per-dim map) and G-CONF passed over the full discrete matrix + 120009 random draws with 0 disagreements. G-AX skip stub is legitimate (no consumed callee axiom). Model<->patch correspondence sound.

Schedule: attacks encoded then verified concurrently in two background batches of 4 (pc+atk1-3, then atk4-7), <=4 at a time; all fully verified. VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack on sympy__sympy-16792 (lean). The modeled function problem_spec_arrayArgBounds(isArrayLike, shape, result) := result = (if isArrayLike then boundsOf shape else []) with boundsOf shape = shape.map (fun d => (0, d-1)) models CodeGen.routine's redundant-argument (argument_sequence KeyError) branch: array-like symbol -> [(0,d-1) for each axis], scalar -> []/None.

Checks performed:
1. same_spec(Solution.lean, Solution_prepatch.lean) = True via swebench_unified.markers with LeanBackend.language — spec region (axioms/pure/post-conditions) is byte-identical between patched and prepatch; the only difference is impl/proof (correctly outside the spec view). Spec is genuinely the same across variants.
2. Solution.lean compiles clean via lean_verify.sh (exit 0). `#print axioms correct_arrayArgBounds` => 'does not depend on any axioms' (no sorryAx; proof is real, closes by `cases isArrayLike <;> rfl`). impl sanity checks (true [3,3] -> [(0,2),(0,2)]; false -> []) pass by `decide`.
3. Differential fuzz against the REAL patched callee (gold patch present at codegen.py:741-748) using CCodeGen().routine('test', S, argument_sequence=(symbol,)) then arg.dimensions: 200,050 draws (scalar Symbol + MatrixSymbol shapes m,n in 1..15) => 0 mismatches. Spec exactly reproduces real bounds.
4. Edge/boundary inputs outside the conformance fuzz window (randint 1..12): dims 0 -> real=[(0,-1),...] == spec (both use d-1 with no clamping); (0,0),(2,0),(0,2),(1,1) all match. Symbolic shapes (n,m),(n,3) match structurally. IndexedBase on this path is replaced by its .label (plain Symbol) before the KeyError branch (codegen.py:728-734) and returns None/scalar -> consistent with mapping.md's documented abstraction (array-like case on this path is MatrixSymbol), no divergence. Scalar case ignores shape, matching real behavior.

The mapping.md/refinement.md abstraction boundaries (isinstance(symbol,(IndexedBase,MatrixSymbol)) -> isArrayLike:Bool; symbol.shape -> shape:List Int; None -> []) are accurate and I could not find any input where the modeled function disagrees with the real CodeGen.routine callee. The spec is neither too strong nor drifting. No diverging input exists.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (verified via markers.spec_view with LeanBackend.language; impl/proof correctly elided; same_spec vs prepatch = True) states only an abstract input→output relation: a scalar argument carries no index bounds ([]), an array-valued argument (one with a shape) carries per-axis inclusive index range (0, size-1) via boundsOf, and this metadata determines pointer/array-vs-scalar emission. Every element of this is already public in problem_statement, which explicitly describes: array arguments not in the wrapped expr get an incorrect scalar C signature (double x) instead of pointer/array (double *x), with a MatrixSymbol('x',2,1) as the concrete case. The (0, size-1) bound form is the codebase's pre-existing dimensions convention (the gold patch only refactors the already-present [(S.Zero, dim-1) for dim in shape] into a helper and reuses it), i.e. the natural/domain-standard formalization, not a gold-specific invention. Crucially, the spec view names NO sympy internals that would pin the gold edit: no KeyError/argument_sequence branch, no isinstance(IndexedBase, MatrixSymbol) guard, no dimensions() helper, no InputArgument, no codegen.py line references. Those gold-locating specifics live only in mapping.md and refinement.md, which are not part of the leak-screened spec view. G-LEAK recorded pass ('spec view clean'). No line reveals the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
