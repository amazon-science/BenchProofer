# P2 adversarial audit — sympy__sympy-16792

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 9 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -91,7 +91,8 @@
       decreasing i
     do
       let e := requests[i - 1]!
-      result := argFor e :: result
+      let a : Arg := if e.alreadyResolved then e.prior else { bounds := [] }
+      result := a :: result
       i := i - 1
     return result
     -- impl-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -82,18 +82,7 @@
   ensures out = argList requests
   do
     -- impl-start
-    let mut result : List Arg := []
-    let mut i := requests.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ requests.length
-      invariant result = argList (requests.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let e := requests[i - 1]!
-      result := argFor e :: result
-      i := i - 1
-    return result
+    return argList requests
     -- impl-end
 
 /- The backward-fold step: dropping one fewer request exposes the request at
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -90,7 +90,7 @@
       done_with i = 0
       decreasing i
     do
-      let e := requests[i - 1]!
+      let e := requests[i]!
       result := argFor e :: result
       i := i - 1
     return result
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -93,7 +93,7 @@
       let e := requests[i - 1]!
       result := argFor e :: result
       i := i - 1
-    return result
+    return result.tail
     -- impl-end
 
 /- The backward-fold step: dropping one fewer request exposes the request at
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -82,18 +82,7 @@
   ensures out = argList requests
   do
     -- impl-start
-    let mut result : List Arg := []
-    let mut i := requests.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ requests.length
-      invariant result = argList (requests.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let e := requests[i - 1]!
-      result := argFor e :: result
-      i := i - 1
-    return result
+    return requests.map argFor
     -- impl-end
 
 /- The backward-fold step: dropping one fewer request exposes the request at
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -91,7 +91,8 @@
       decreasing i
     do
       let e := requests[i - 1]!
-      result := argFor e :: result
+      let a : Arg := if e.alreadyResolved then e.prior else { bounds := extentBounds e.extents }
+      result := a :: result
       i := i - 1
     return result
     -- impl-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -83,16 +83,16 @@
   do
     -- impl-start
     let mut result : List Arg := []
-    let mut i := requests.length
-    while i > 0
+    let mut i := 0
+    while i < requests.length
       invariant 0 ≤ i ∧ i ≤ requests.length
-      invariant result = argList (requests.drop i)
-      done_with i = 0
-      decreasing i
+      invariant result = argList (requests.drop (requests.length - i))
+      done_with i = requests.length
+      decreasing requests.length - i
     do
-      let e := requests[i - 1]!
+      let e := requests[i]!
       result := argFor e :: result
-      i := i - 1
+      i := i + 1
     return result
     -- impl-end
 
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -82,18 +82,10 @@
   ensures out = argList requests
   do
     -- impl-start
-    let mut result : List Arg := []
-    let mut i := requests.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ requests.length
-      invariant result = argList (requests.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let e := requests[i - 1]!
-      result := argFor e :: result
-      i := i - 1
-    return result
+    if requests.isEmpty then
+      return []
+    else
+      return argList requests
     -- impl-end
 
 /- The backward-fold step: dropping one fewer request exposes the request at
```

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

```diff
@@ -91,7 +91,8 @@
       decreasing i
     do
       let e := requests[i - 1]!
-      result := argFor e :: result
+      let a : Arg := if e.alreadyResolved then e.prior else { bounds := if e.arrayLike then [] else extentBounds e.extents }
+      result := a :: result
       i := i - 1
     return result
     -- impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No consumed callee contracts. The per-argument transformation is modeled
--  deeply: an already-resolved argument is carried through unchanged, and a
--  freshly-built argument's dimension metadata is the spelled-out extent map.
--  Nothing is borrowed from an opaque oracle — every observable is computed
--  from the inputs. See refinement.md / mapping.md.)
-- axioms-end

-- pure-start
/- The dimension metadata of a typed argument: for each axis it records the
   inclusive index bounds `(lower, upper)`. An empty list means the argument
   carries no dimension metadata (a plain scalar); a non-empty list means the
   argument is array-like and must be passed by reference downstream. -/
structure Arg where
  bounds : List (Int × Int)
  deriving Inhabited, DecidableEq

/- A request for one positional argument of the generated function. It records:
   - `alreadyResolved` : whether an argument with this name was already built
     while scanning the expression (in which case its prior form is reused
     verbatim — its metadata was determined there and is not recomputed here);
   - `prior` : that already-built argument (meaningful only when resolved);
   - `arrayLike` : whether the requested symbol is an array-like quantity
     (one that owns a shape), as opposed to a plain scalar;
   - `extents` : the per-axis extents of an array-like symbol (its shape). -/
structure ArgSpec where
  alreadyResolved : Bool
  prior : Arg
  arrayLike : Bool
  extents : List Int
  deriving Inhabited

/- The dimension metadata for an array-like symbol of the given extents: each
   axis `d` becomes the inclusive bound pair `(0, d - 1)`. -/
def extentBounds (extents : List Int) : List (Int × Int) :=
  extents.map (fun d => (0, d - 1))

/- The argument produced for a single request. An already-resolved request
   reuses its prior argument unchanged. A request that must be built fresh is
   array-like ⇒ it carries its extent-derived dimension metadata; otherwise it
   carries none. The behaviour the issue turns on: a freshly-built array-like
   argument must receive dimension metadata (so it is later emitted by
   reference), NOT be left with empty metadata. -/
def argFor (e : ArgSpec) : Arg :=
  if e.alreadyResolved then e.prior
  else { bounds := if e.arrayLike then extentBounds e.extents else [] }

/- The full positional argument list: each request mapped to its argument, in
   order. Front-recursive so a single unfold is available per loop step (the
   Velvet backward-fold pattern). -/
def argList : List ArgSpec → List Arg
  | []      => []
  | e :: es => argFor e :: argList es

@[grind] lemma argList_nil : argList [] = [] := rfl

@[grind] lemma argList_cons (e : ArgSpec) (es : List ArgSpec) :
    argList (e :: es) = argFor e :: argList es := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Build the generated function's positional argument list from the requested
   sequence.
   The result is exactly the per-request argument map, in the requested order:
   the count and order of the requested sequence are preserved, and each request
   yields its argument under `argFor`. `requests` is read-only (not `mut`); the
   loop constructs a fresh result and never mutates its input (directive 5). -/
method buildArgList (requests : List ArgSpec) return (out : List Arg)
  ensures out = argList requests
  do
    -- impl-start
    let mut result : List Arg := []
    let mut i := requests.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ requests.length
      invariant result = argList (requests.drop i)
      done_with i = 0
      decreasing i
    do
      let e := requests[i - 1]!
      result := argFor e :: result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer request exposes the request at
   `i-1` on the front, so `argList` peels one `argFor`. This is the single goal
   `loom_solve` leaves for the loop body. -/
lemma argList_drop_step (requests : List ArgSpec) (i : Nat)
    (hi : 0 < i) (hle : i ≤ requests.length) :
    argList (requests.drop (i - 1)) = argFor requests[i - 1]! :: argList (requests.drop i) := by
  have hlt : i - 1 < requests.length := by omega
  have hcons : requests.drop (i - 1) = requests[i - 1]! :: requests.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, argList_cons]

prove_correct buildArgList by
  loom_solve
  rw [argList_drop_step requests i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec: method buildArgList (requests : List ArgSpec) return (out : List Arg) ensures out = argList requests. The postcondition FULLY PINS the output to the frozen pure function argList (= requests.map argFor), and the prove_correct proof block (lines 99-116, OUTSIDE the impl region and thus byte-frozen along with axioms/pure/pre/post) is tailored to the exact backward-fold loop shape. same_spec=True confirmed for all 9 attacks + positive control (only the impl region edited).

ATTACK BATTERY (9 distinct same-spec wrong impls, all verified concurrently as background jobs, <=4 at a time; project root; cmd per file: `bash scripts/lean_verify.sh <path>`). Exit 0=verifies, 1=error, 3=sorry, 124=timeout:
- atk_1 (prepatch bug: fresh request ALWAYS { bounds := [] }, drops array-like extents = the exact issue bug) -> exit 1 REJECTED. This reproduces the prepatch (Solution_prepatch.lean is identical to atk_1; G-DIFF pass records prepatch verification-failed). prepatch_reproduced=true.
- atk_2 (ungrounded-oracle echo: `return argList requests`, CORRECT output) -> exit 1 REJECTED (frozen prove_correct expects the loop; 'No goals to be solved').
- atk_3 (boundary/off-by-one: index requests[i]! instead of requests[i-1]!) -> exit 1 REJECTED.
- atk_4 (control-flow-effect: build correctly then `return result.tail`, drops head) -> exit 1 REJECTED.
- atk_5 (ungrounded-oracle echo: `return requests.map argFor`, CORRECT output, alt expression) -> exit 1 REJECTED.
- atk_6 (partial-domain/wrong-branch: fresh request ALWAYS extentBounds even for scalars) -> exit 1 REJECTED.
- atk_7 (control-flow: forward loop => reversed output order) -> exit 1 REJECTED.
- atk_8 (partial-domain echo: if requests.isEmpty then [] else argList requests, CORRECT output) -> exit 1 REJECTED ('No goals to be solved').
- atk_9 (swapped arrayLike disjunct: array-like -> [], scalar -> extentBounds; identical loop shape so frozen proof still applies) -> exit 1 REJECTED on the argFor equality goal.
Positive control pos.lean (unmodified gold impl) -> exit 0 VERIFIES.

RESULT: ZERO verifying-but-wrong impls. Because no same-spec wrong impl verifies, there is NO candidate whose faithful refined patch could be materialized and run through run_resolve to exhibit verify=>NOT-resolve. patches={} accordingly (no verifying wrong impl to materialize). This is the correct, exhaustive outcome for a fully-pinning functional postcondition, not a rubber-stamp: real echoes with byte-identical output (atk_2/5/8) were attempted and are rejected by proof-fragility, and behaviourally-distinct wrongs (atk_1/3/4/6/7/9) are rejected on the postcondition.

REFINEMENT.md / A-LEG AUDIT: meta.json shows axioms=[] and deep_model_references=[]; refinement.md §C declares no consumed axioms and no A-reference callees (mapping.md §3 'Callee provenance: None'). There are NO A-legs to falsify. The one genuinely-changed op (attach extent-derived dimension metadata to a freshly-built array-like argument) is modeled DEEPLY inline (extentBounds map + argFor branch, step A4), NOT behind an axiom about the function under change. G-AX correctly skip (no axiom_check.py). Every leg is R or I, mechanically refuted by G-CONF: meta records G-CONF pass, 100012 inputs, seed=16792, 0 disagreements, driving the REAL patched CCodeGen().routine over MatrixSymbol/Symbol/IndexedBase sequences plus the F2P boundary MatrixSymbol('x',2,1). The extentBounds<->dimensions(s)=[(S.Zero,dim-1) for dim in s.shape] correspondence and the IndexedBase-.label normalization reachability claim (mapping.md §2) are both fuzz-witnessed. Correspondence holds. G-RESOLVE=pass (gold patch resolves; test_ccode_unused_array_arg renders `double *x`). No kind-3 legs.

No resolve run was required or possible for a breaking demonstration since no wrong impl verified; the mandate to materialize+resolve a faithful patch triggers only for a VERIFYING wrong impl, of which there were none. Not INCONCLUSIVE: all 9 attacks + positive control completed with definitive exit codes; no attack or needed resolve run failed to complete.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 9 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 9 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No consumed callee contracts. The per-argument transformation is modeled
--  deeply: an already-resolved argument is carried through unchanged, and a
--  freshly-built argument's dimension metadata is the spelled-out extent map.
--  Nothing is borrowed from an opaque oracle — every observable is computed
--  from the inputs. See refinement.md / mapping.md.)
-- axioms-end

-- pure-start
/- The dimension metadata of a typed argument: for each axis it records the
   inclusive index bounds `(lower, upper)`. An empty list means the argument
   carries no dimension metadata (a plain scalar); a non-empty list means the
   argument is array-like and must be passed by reference downstream. -/
structure Arg where
  bounds : List (Int × Int)
  deriving Inhabited, DecidableEq

/- A request for one positional argument of the generated function. It records:
   - `alreadyResolved` : whether an argument with this name was already built
     while scanning the expression (in which case its prior form is reused
     verbatim — its metadata was determined there and is not recomputed here);
   - `prior` : that already-built argument (meaningful only when resolved);
   - `arrayLike` : whether the requested symbol is an array-like quantity
     (one that owns a shape), as opposed to a plain scalar;
   - `extents` : the per-axis extents of an array-like symbol (its shape). -/
structure ArgSpec where
  alreadyResolved : Bool
  prior : Arg
  arrayLike : Bool
  extents : List Int
  deriving Inhabited

/- The dimension metadata for an array-like symbol of the given extents: each
   axis `d` becomes the inclusive bound pair `(0, d - 1)`. -/
def extentBounds (extents : List Int) : List (Int × Int) :=
  extents.map (fun d => (0, d - 1))

/- The argument produced for a single request. An already-resolved request
   reuses its prior argument unchanged. A request that must be built fresh is
   array-like ⇒ it carries its extent-derived dimension metadata; otherwise it
   carries none. The behaviour the issue turns on: a freshly-built array-like
   argument must receive dimension metadata (so it is later emitted by
   reference), NOT be left with empty metadata. -/
def argFor (e : ArgSpec) : Arg :=
  if e.alreadyResolved then e.prior
  else { bounds := if e.arrayLike then extentBounds e.extents else [] }

/- The full positional argument list: each request mapped to its argument, in
   order. Front-recursive so a single unfold is available per loop step (the
   Velvet backward-fold pattern). -/
def argList : List ArgSpec → List Arg
  | []      => []
  | e :: es => argFor e :: argList es

@[grind] lemma argList_nil : argList [] = [] := rfl

@[grind] lemma argList_cons (e : ArgSpec) (es : List ArgSpec) :
    argList (e :: es) = argFor e :: argList es := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Build the generated function's positional argument list from the requested
   sequence.
   The result is exactly the per-request argument map, in the requested order:
   the count and order of the requested sequence are preserved, and each request
   yields its argument under `argFor`. `requests` is read-only (not `mut`); the
   loop constructs a fresh result and never mutates its input (directive 5). -/
method buildArgList (requests : List ArgSpec) return (out : List Arg)
  ensures out = argList requests
  do
    -- impl-start
    let mut result : List Arg := []
    let mut i := requests.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ requests.length
      invariant result = argList (requests.drop i)
      done_with i = 0
      decreasing i
    do
      let e := requests[i - 1]!
      result := argFor e :: result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer request exposes the request at
   `i-1` on the front, so `argList` peels one `argFor`. This is the single goal
   `loom_solve` leaves for the loop body. -/
lemma argList_drop_step (requests : List ArgSpec) (i : Nat)
    (hi : 0 < i) (hle : i ≤ requests.length) :
    argList (requests.drop (i - 1)) = argFor requests[i - 1]! :: argList (requests.drop i) := by
  have hlt : i - 1 < requests.length := by omega
  have hcons : requests.drop (i - 1) = requests[i - 1]! :: requests.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, argList_cons]

prove_correct buildArgList by
  loom_solve
  rw [argList_drop_step requests i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec: method buildArgList (requests : List ArgSpec) return (out : List Arg) ensures out = argList requests. The postcondition FULLY PINS the output to the frozen pure function argList (= requests.map argFor), and the prove_correct proof block (lines 99-116, OUTSIDE the impl region and thus byte-frozen along with axioms/pure/pre/post) is tailored to the exact backward-fold loop shape. same_spec=True confirmed for all 9 attacks + positive control (only the impl region edited).

ATTACK BATTERY (9 distinct same-spec wrong impls, all verified concurrently as background jobs, <=4 at a time; project root; cmd per file: `bash scripts/lean_verify.sh <path>`). Exit 0=verifies, 1=error, 3=sorry, 124=timeout:
- atk_1 (prepatch bug: fresh request ALWAYS { bounds := [] }, drops array-like extents = the exact issue bug) -> exit 1 REJECTED. This reproduces the prepatch (Solution_prepatch.lean is identical to atk_1; G-DIFF pass records prepatch verification-failed). prepatch_reproduced=true.
- atk_2 (ungrounded-oracle echo: `return argList requests`, CORRECT output) -> exit 1 REJECTED (frozen prove_correct expects the loop; 'No goals to be solved').
- atk_3 (boundary/off-by-one: index requests[i]! instead of requests[i-1]!) -> exit 1 REJECTED.
- atk_4 (control-flow-effect: build correctly then `return result.tail`, drops head) -> exit 1 REJECTED.
- atk_5 (ungrounded-oracle echo: `return requests.map argFor`, CORRECT output, alt expression) -> exit 1 REJECTED.
- atk_6 (partial-domain/wrong-branch: fresh request ALWAYS extentBounds even for scalars) -> exit 1 REJECTED.
- atk_7 (control-flow: forward loop => reversed output order) -> exit 1 REJECTED.
- atk_8 (partial-domain echo: if requests.isEmpty then [] else argList requests, CORRECT output) -> exit 1 REJECTED ('No goals to be solved').
- atk_9 (swapped arrayLike disjunct: array-like -> [], scalar -> extentBounds; identical loop shape so frozen proof still applies) -> exit 1 REJECTED on the argFor equality goal.
Positive control pos.lean (unmodified gold impl) -> exit 0 VERIFIES.

RESULT: ZERO verifying-but-wrong impls. Because no same-spec wrong impl verifies, there is NO candidate whose faithful refined patch could be materialized and run through run_resolve to exhibit verify=>NOT-resolve. patches={} accordingly (no verifying wrong impl to materialize). This is the correct, exhaustive outcome for a fully-pinning functional postcondition, not a rubber-stamp: real echoes with byte-identical output (atk_2/5/8) were attempted and are rejected by proof-fragility, and behaviourally-distinct wrongs (atk_1/3/4/6/7/9) are rejected on the postcondition.

REFINEMENT.md / A-LEG AUDIT: meta.json shows axioms=[] and deep_model_references=[]; refinement.md §C declares no consumed axioms and no A-reference callees (mapping.md §3 'Callee provenance: None'). There are NO A-legs to falsify. The one genuinely-changed op (attach extent-derived dimension metadata to a freshly-built array-like argument) is modeled DEEPLY inline (extentBounds map + argFor branch, step A4), NOT behind an axiom about the function under change. G-AX correctly skip (no axiom_check.py). Every leg is R or I, mechanically refuted by G-CONF: meta records G-CONF pass, 100012 inputs, seed=16792, 0 disagreements, driving the REAL patched CCodeGen().routine over MatrixSymbol/Symbol/IndexedBase sequences plus the F2P boundary MatrixSymbol('x',2,1). The extentBounds<->dimensions(s)=[(S.Zero,dim-1) for dim in s.shape] correspondence and the IndexedBase-.label normalization reachability claim (mapping.md §2) are both fuzz-witnessed. Correspondence holds. G-RESOLVE=pass (gold patch resolves; test_ccode_unused_array_arg renders `double *x`). No kind-3 legs.

No resolve run was required or possible for a breaking demonstration since no wrong impl verified; the mandate to materialize+resolve a faithful patch triggers only for a VERIFYING wrong impl, of which there were none. Not INCONCLUSIVE: all 9 attacks + positive control completed with definitive exit codes; no attack or needed resolve run failed to complete.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness attack (spec-too-strong / drift from real callee): no divergence found. Modeled function is argFor/argList over List ArgSpec, mapping the real CodeGen.routine argument_sequence fall-through arm (sympy/utilities/codegen.py:738-743, patched). Checks performed:

1) Byte-identical spec region: same_spec(Solution, Solution_prepatch)=True via swebench_unified.markers; spec_view elides only impl/proof. Prepatch keeps spec byte-identical (G-DIFF satisfied) and fails verification exactly on the array-like fresh leg.

2) Independent G-CONF: created fresh worktree at base_commit 09786a17, applied the gold patch cleanly, ran conformance_check.py myself -> 'agrees on 100012 inputs, 0 disagreements'. Not trusting the recorded gate.

3) Probed the legs the fuzzer does NOT exercise against the oracle (fuzz uses expr=1.0, only the fresh leg): 
   - IndexedBase normalization claim verified: IndexedBase('A',shape=(3,)).label is genuinely shapeless (hasattr(.label,'shape')==False). IB request absent from expr -> dimensions=None (scalar/fresh leg, arrayLike=false); IB present in expr -> resolved with prior bounds [(0,2)] (alreadyResolved/prior leg). Both match the model.
   - Resolved MatrixSymbol (present in expr) -> reused verbatim with bounds [(0,1),(0,0)] = extentBounds; matches alreadyResolved/prior.
   - Order preservation: non-sorted request (z_matrix, a_scalar) -> real preserves requested order z,a, model preserves via argList. Match.
   - Mixed resolved+fresh and 1x1 boundary all match argFor/argList.

4) Type abstraction (mapping.md 2): dimensions(s)=[(0,d-1) for d in shape] <-> extentBounds; None/empty <-> []; verified exactly against real Argument.dimensions. Lean Int carries integer bounds exactly (sympy uses S.Zero/Integer). No overclaim: 'prior' is a free carrier for the reuse-verbatim leg, matching real reuse behavior; termination is total, and the real fall-through loop is a bounded for-loop that terminates.

The modeled function agrees with the real repo callee on every input tested across both branches (fresh array-like, fresh scalar, resolved, IndexedBase-normalized-to-scalar). No diverging input exists; the spec is not too strong.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Leakage judged against the public problem_statement only (hints_text is empty). Byte-identity confirmed: same_spec(Solution.lean, Solution_prepatch.lean)=True; lexical G-LEAK screen passes (no diff markers, no patched file path sympy/utilities/codegen.py, no gold-patch lines reproduced, no patched repo symbols dimensions/routine in spec-view identifiers or comments, no narration keywords).

Semantic assessment of the consumer spec view (buildArgList / argFor / argList / extentBounds + method signature and ensures out = argList requests):
- The problem_statement is already very explicit: it names the bug (array args absent from expr get wrong C signature), the correct behavior ('x should be double *, not double' — i.e. passed by reference), the counterexample MatrixSymbol('x',2,1) with expr=1.0, and localizes to codegen. So the public task itself discloses that array-like arguments must carry dimension/by-reference metadata.
- The spec view models exactly this corrected behavior at an abstract level: a freshly-built array-like argument gets extent-derived bounds (later emitted by reference), a scalar gets none, a resolved argument is reused. This is the behavioral contract any faithful spec must state, and it reveals nothing about the EDIT beyond the problem statement.
- The discriminating gold-edit specifics are NOT surfaced: no mention of the isinstance(symbol,(IndexedBase,MatrixSymbol)) guard, no except-KeyError location, no dimensions(s) helper-extraction refactor, no repo symbol names. The (0, d-1) bound form is generic sympy dimension representation, not edit-localizing content.
- Comments describe behavior ('the behaviour the issue turns on', 'must receive dimension metadata, NOT be left with empty metadata') abstractly; none trip the narration lexicon and none quote gold-diff specifics.
- Gold-quoting docs (refinement.md quoting the patch hunk, mapping.md citing codegen.py line numbers) are auditor-side artifacts, not part of the consumer spec view.

The spec view leaks nothing about the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
