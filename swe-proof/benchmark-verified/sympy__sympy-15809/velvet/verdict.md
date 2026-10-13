# P2 adversarial audit — sympy__sympy-15809

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_7.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -95,15 +95,15 @@
   ensures rawArgs = [] → out = Except.ok (MinMaxResult.identityResult idv)
   do
     -- impl-start
-    -- Normalise the raw arguments (unchanged pipeline) and decide the result by
-    -- how many members survive. There is NO rejection of an empty argument list:
-    -- the empty collection's extremum is the identity element, reached through
-    -- the empty-normalisation branch below.
+    -- ATTACK: prepatch bug — reject empty argument list
     let result : Except MinMaxErr MinMaxResult :=
-      match processArgs rawArgs with
-      | []           => Except.ok (MinMaxResult.identityResult idv)
-      | [a]          => Except.ok (MinMaxResult.single a)
-      | a :: b :: rest => Except.ok (MinMaxResult.combined (a :: b :: rest))
+      if rawArgs = [] then
+        Except.error MinMaxErr.noArguments
+      else
+        match processArgs rawArgs with
+        | []           => Except.ok (MinMaxResult.identityResult idv)
+        | [a]          => Except.ok (MinMaxResult.single a)
+        | a :: b :: rest => Except.ok (MinMaxResult.combined (a :: b :: rest))
     return result
     -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -95,15 +95,15 @@
   ensures rawArgs = [] → out = Except.ok (MinMaxResult.identityResult idv)
   do
     -- impl-start
-    -- Normalise the raw arguments (unchanged pipeline) and decide the result by
-    -- how many members survive. There is NO rejection of an empty argument list:
-    -- the empty collection's extremum is the identity element, reached through
-    -- the empty-normalisation branch below.
+    -- ATTACK(boundary): special-case empty rawArgs up front, else pipeline
     let result : Except MinMaxErr MinMaxResult :=
-      match processArgs rawArgs with
-      | []           => Except.ok (MinMaxResult.identityResult idv)
-      | [a]          => Except.ok (MinMaxResult.single a)
-      | a :: b :: rest => Except.ok (MinMaxResult.combined (a :: b :: rest))
+      match rawArgs with
+      | [] => Except.ok (MinMaxResult.identityResult idv)
+      | _  =>
+        match processArgs rawArgs with
+        | []           => Except.ok (MinMaxResult.identityResult idv)
+        | [a]          => Except.ok (MinMaxResult.single a)
+        | a :: b :: rest => Except.ok (MinMaxResult.combined (a :: b :: rest))
     return result
     -- impl-end
 
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -95,14 +95,11 @@
   ensures rawArgs = [] → out = Except.ok (MinMaxResult.identityResult idv)
   do
     -- impl-start
-    -- Normalise the raw arguments (unchanged pipeline) and decide the result by
-    -- how many members survive. There is NO rejection of an empty argument list:
-    -- the empty collection's extremum is the identity element, reached through
-    -- the empty-normalisation branch below.
+    -- ATTACK(partial-domain): treat a lone survivor as a combined object
     let result : Except MinMaxErr MinMaxResult :=
       match processArgs rawArgs with
       | []           => Except.ok (MinMaxResult.identityResult idv)
-      | [a]          => Except.ok (MinMaxResult.single a)
+      | [a]          => Except.ok (MinMaxResult.combined [a])
       | a :: b :: rest => Except.ok (MinMaxResult.combined (a :: b :: rest))
     return result
     -- impl-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -95,13 +95,10 @@
   ensures rawArgs = [] → out = Except.ok (MinMaxResult.identityResult idv)
   do
     -- impl-start
-    -- Normalise the raw arguments (unchanged pipeline) and decide the result by
-    -- how many members survive. There is NO rejection of an empty argument list:
-    -- the empty collection's extremum is the identity element, reached through
-    -- the empty-normalisation branch below.
+    -- ATTACK: on empty survivor set return a bogus single value instead of identity
     let result : Except MinMaxErr MinMaxResult :=
       match processArgs rawArgs with
-      | []           => Except.ok (MinMaxResult.identityResult idv)
+      | []           => Except.ok (MinMaxResult.single 0)
       | [a]          => Except.ok (MinMaxResult.single a)
       | a :: b :: rest => Except.ok (MinMaxResult.combined (a :: b :: rest))
     return result
```

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -95,12 +95,10 @@
   ensures rawArgs = [] → out = Except.ok (MinMaxResult.identityResult idv)
   do
     -- impl-start
-    -- Normalise the raw arguments (unchanged pipeline) and decide the result by
-    -- how many members survive. There is NO rejection of an empty argument list:
-    -- the empty collection's extremum is the identity element, reached through
-    -- the empty-normalisation branch below.
+    -- ATTACK(control-flow, behaviorally-equal): dispatch on length
+    let surv := processArgs rawArgs
     let result : Except MinMaxErr MinMaxResult :=
-      match processArgs rawArgs with
+      match surv with
       | []           => Except.ok (MinMaxResult.identityResult idv)
       | [a]          => Except.ok (MinMaxResult.single a)
       | a :: b :: rest => Except.ok (MinMaxResult.combined (a :: b :: rest))
```

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -95,15 +95,8 @@
   ensures rawArgs = [] → out = Except.ok (MinMaxResult.identityResult idv)
   do
     -- impl-start
-    -- Normalise the raw arguments (unchanged pipeline) and decide the result by
-    -- how many members survive. There is NO rejection of an empty argument list:
-    -- the empty collection's extremum is the identity element, reached through
-    -- the empty-normalisation branch below.
-    let result : Except MinMaxErr MinMaxResult :=
-      match processArgs rawArgs with
-      | []           => Except.ok (MinMaxResult.identityResult idv)
-      | [a]          => Except.ok (MinMaxResult.single a)
-      | a :: b :: rest => Except.ok (MinMaxResult.combined (a :: b :: rest))
+    -- ATTACK(ungrounded-oracle echo): return the model verbatim
+    let result : Except MinMaxErr MinMaxResult := minMaxResult idv rawArgs
     return result
     -- impl-end
 
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -95,15 +95,15 @@
   ensures rawArgs = [] → out = Except.ok (MinMaxResult.identityResult idv)
   do
     -- impl-start
-    -- Normalise the raw arguments (unchanged pipeline) and decide the result by
-    -- how many members survive. There is NO rejection of an empty argument list:
-    -- the empty collection's extremum is the identity element, reached through
-    -- the empty-normalisation branch below.
+    -- ATTACK(partial-domain): a single raw argument is returned verbatim, bypassing normalisation
     let result : Except MinMaxErr MinMaxResult :=
-      match processArgs rawArgs with
-      | []           => Except.ok (MinMaxResult.identityResult idv)
-      | [a]          => Except.ok (MinMaxResult.single a)
-      | a :: b :: rest => Except.ok (MinMaxResult.combined (a :: b :: rest))
+      match rawArgs with
+      | [a] => Except.ok (MinMaxResult.single a)
+      | _   =>
+        match processArgs rawArgs with
+        | []           => Except.ok (MinMaxResult.identityResult idv)
+        | [a]          => Except.ok (MinMaxResult.single a)
+        | a :: b :: rest => Except.ok (MinMaxResult.combined (a :: b :: rest))
     return result
     -- impl-end
 
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -95,15 +95,12 @@
   ensures rawArgs = [] → out = Except.ok (MinMaxResult.identityResult idv)
   do
     -- impl-start
-    -- Normalise the raw arguments (unchanged pipeline) and decide the result by
-    -- how many members survive. There is NO rejection of an empty argument list:
-    -- the empty collection's extremum is the identity element, reached through
-    -- the empty-normalisation branch below.
+    -- ATTACK: build the combined object over the wrong survivor multiset (drop the head)
     let result : Except MinMaxErr MinMaxResult :=
       match processArgs rawArgs with
       | []           => Except.ok (MinMaxResult.identityResult idv)
       | [a]          => Except.ok (MinMaxResult.single a)
-      | a :: b :: rest => Except.ok (MinMaxResult.combined (a :: b :: rest))
+      | a :: b :: rest => Except.ok (MinMaxResult.combined (b :: rest))
     return result
     -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- The standard argument-normalisation pipeline a lattice extremum constructor
   runs over its raw arguments before deciding a result: it sympifies, flattens
   nested same-kind extrema, drops the absorbing/identity elements, and removes
   locally-dominated members, yielding the normalised argument multiset. It is an
   UNCHANGED helper the constructor merely invokes (never redefined), so it is
   modeled `opaque` (computable inside the `do` block) and carries NO general
   `ensures` — the desired behaviour assumes nothing about which members survive
   for a non-empty input.

   The one fact the desired behaviour relies on is `processArgs_nil`: normalising
   an EMPTY argument list yields an EMPTY multiset (the pipeline introduces no
   members out of nothing). This is the WEAKEST contract sufficient for the
   empty-input result and is the only consumed axiom (A-consumed). Provenance +
   executable soundness check: mapping.md §3 / axiom_check.py (G-AX). -/
opaque processArgs : List Int → List Int

axiom processArgs_nil : processArgs [] = []
-- axioms-end

-- pure-start
/- The failure the constructor is asked about: being called with no arguments at
   all. (The public problem statement reports exactly this case — that empty
   calls currently fail.) -/
inductive MinMaxErr where
  | noArguments
  deriving DecidableEq

/- The result of constructing a lattice extremum:

     * `identityResult idv` — the lattice identity element `idv` is returned
       (the value that is the extremum of the EMPTY collection: the top element
       for a minimum, the bottom element for a maximum);
     * `single a` — exactly one member survives normalisation, returned verbatim;
     * `combined members` — two or more members survive; the extremum object over
       that normalised multiset is built. -/
inductive MinMaxResult where
  | identityResult (idv : Int)
  | single (a : Int)
  | combined (members : List Int)
  deriving DecidableEq

/- The intended outcome of constructing a lattice extremum from a raw argument
   list and the lattice identity element `idv`, as `Except MinMaxErr MinMaxResult`:

   the raw arguments are normalised (the unchanged `processArgs` pipeline), then
   the result is decided ENTIRELY by how many members survive —
     * none survive  ⇒ the identity element `idv` is returned (the extremum of the
       empty collection); in particular a call with no arguments at all yields the
       identity element rather than failing;
     * one survives  ⇒ that member is returned verbatim;
     * two or more    ⇒ the extremum object over the survivors is built.

   No input is rejected for being empty: the empty collection has a well-defined
   extremum, namely the identity element. -/
def minMaxResult (idv : Int) (rawArgs : List Int) : Except MinMaxErr MinMaxResult :=
  match processArgs rawArgs with
  | []           => Except.ok (MinMaxResult.identityResult idv)
  | [a]          => Except.ok (MinMaxResult.single a)
  | a :: b :: rest => Except.ok (MinMaxResult.combined (a :: b :: rest))
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Construct a lattice extremum (a minimum or a maximum) from a raw argument list
   and the lattice identity element `idv` (the top element for a minimum, the
   bottom element for a maximum — the extremum of the empty collection).

   Desired behaviour: the constructor normalises its raw arguments through the
   unchanged argument-normalisation pipeline and then decides the result purely by
   how many members survive — none ⇒ the identity element, one ⇒ that member,
   two or more ⇒ the extremum object. Crucially it must NOT reject an empty
   argument list: the empty collection has a well-defined extremum, the identity
   element, so a call with no arguments returns `idv` instead of failing.

   `idv` and `rawArgs` are read-only (not `mut`): the constructor computes a
   result and mutates no input (directive 5). Arguments are modeled as opaque
   handles (`Int`); the only observations are the normalisation outcome
   (`processArgs rawArgs`) and the supplied identity element (mapping.md §2). -/
method constructMinMax (idv : Int) (rawArgs : List Int)
    return (out : Except MinMaxErr MinMaxResult)
  ensures out = minMaxResult idv rawArgs
  ensures rawArgs = [] → out = Except.ok (MinMaxResult.identityResult idv)
  do
    -- impl-start
    -- Normalise the raw arguments (unchanged pipeline) and decide the result by
    -- how many members survive. There is NO rejection of an empty argument list:
    -- the empty collection's extremum is the identity element, reached through
    -- the empty-normalisation branch below.
    let result : Except MinMaxErr MinMaxResult :=
      match processArgs rawArgs with
      | []           => Except.ok (MinMaxResult.identityResult idv)
      | [a]          => Except.ok (MinMaxResult.single a)
      | a :: b :: rest => Except.ok (MinMaxResult.combined (a :: b :: rest))
    return result
    -- impl-end

prove_correct constructMinMax by
  loom_solve <;> simp_all [minMaxResult, processArgs_nil]
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec structure: constructMinMax carries a TOTAL functional postcondition `ensures out = minMaxResult idv rawArgs` (plus the redundant empty-case `rawArgs=[] -> identityResult idv`). This pins `out` on EVERY input, so any impl that verifies against the frozen spec is provably behaviourally equal to the count-driven model minMaxResult. The prove_correct tactic block is byte-identical, so a verifying impl must actually be simp-provably equal to the model. No behavioural slack exists for a wrong-but-verifying impl.

8 same-spec attacks built (impl region only; same_spec=True for all 8; verified via swebench_unified.markers.same_spec / get_backend('velvet')). Command per attack: `bash scripts/lean_verify.sh <file>` from project root.

### Verify results
- pos_control.lean (gold impl): exit 0 VERIFIES (positive control passes).
- atk_1 (prepatch bug: reject empty args -> Except.error noArguments): exit 1 FAILS to verify — the empty-case postcondition goal `¬rawArgs=[]` is unprovable. verify correctly rejects the prepatch bug (prepatch_reproduced=true).
- atk_2 (boundary: match rawArgs [] up front else pipeline; behaviourally equal): exit 1 FAILS — fixed tactic cannot close the case-split (unsolved goals). Not a verifying impl -> does not count.
- atk_3 (partial-domain: lone survivor [a] -> combined [a] instead of single a): exit 1 FAILS. correctly rejected.
- atk_4 (empty survivor set -> single 0 instead of identityResult idv): exit 1 FAILS. correctly rejected.
- atk_5 (control-flow: bind `let surv := processArgs rawArgs` then dispatch; behaviourally EQUAL to model): exit 0 VERIFIES.
- atk_6 (ungrounded-oracle echo: `return minMaxResult idv rawArgs` verbatim; behaviourally EQUAL): exit 0 VERIFIES.
- atk_7 (partial-domain: single raw arg [a] returned verbatim bypassing normalisation): exit 1 FAILS. correctly rejected.
- atk_8 (build combined over wrong survivor multiset — drop head, b::rest): exit 1 FAILS. correctly rejected.

Both VERIFYING attacks (atk_5, atk_6) are behaviourally identical to the gold model (a `let`-binding refactor and a verbatim model echo, respectively). Their faithful refined patch is therefore the gold-behaviour patch (delete the two-line empty-args guard so the empty call falls through to `if not args: return cls.identity`), which is byte-identical to patch.diff / dataset gold.

RESOLVE (protocol step 2, EXECUTED — not speculated): materialized faithful_patch.diff and ran run_resolve('sympy__sympy-15809', patch, timeout=1800, retries=1) via swebench_unified.harness. Result: RESOLVED=True, COMPLETED=True, NOTE='resolved', ATTEMPTS=1 (FAIL_TO_PASS test_Min/test_Max + PASS_TO_PASS pass). Both atk_5 and atk_6 share this identical faithful patch, so both resolve. No verifying wrong impl exists whose faithful patch fails to resolve.

refinement.md AUDIT: legs A1/A2 = R (List Int handle / cls.identity abstraction); A3 = A-consumed (processArgs opaque, sole axiom processArgs_nil); A4/A5/A6 = I (identity/single/combined result legs). No kind-3 (inexpressible) leg — the changed op (removing the empty rejection) is modeled directly by the empty branch reachable on []. A-consumed axiom `processArgs_nil : processArgs [] = []` re-validated against the REAL unchanged base pipeline: ran _new_args_filter -> _collapse_arguments -> _find_localzeros on [] for both Max and Min at base_commit (guard restored) -> both return set() (empty). Axiom is sound and base-valid; the empty->identity leg is the patched behaviour, correctly validated by G-RESOLVE/G-CONF rather than G-AX. A-legs' correspondence to real callees holds.

Conclusion: verify DOES imply correct here — the total functional postcondition leaves no behavioural gap. >=5 attacks run (8), the sole verifying-impl class has an executed resolving faithful patch, and the A-leg axiom is sound. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_7.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- The standard argument-normalisation pipeline a lattice extremum constructor
   runs over its raw arguments before deciding a result: it sympifies, flattens
   nested same-kind extrema, drops the absorbing/identity elements, and removes
   locally-dominated members, yielding the normalised argument multiset. It is an
   UNCHANGED helper the constructor merely invokes (never redefined), so it is
   modeled `opaque` (computable inside the `do` block) and carries NO general
   `ensures` — the desired behaviour assumes nothing about which members survive
   for a non-empty input.

   The one fact the desired behaviour relies on is `processArgs_nil`: normalising
   an EMPTY argument list yields an EMPTY multiset (the pipeline introduces no
   members out of nothing). This is the WEAKEST contract sufficient for the
   empty-input result and is the only consumed axiom (A-consumed). Provenance +
   executable soundness check: mapping.md §3 / axiom_check.py (G-AX). -/
opaque processArgs : List Int → List Int

axiom processArgs_nil : processArgs [] = []
-- axioms-end

-- pure-start
/- The failure the constructor is asked about: being called with no arguments at
   all. (The public problem statement reports exactly this case — that empty
   calls currently fail.) -/
inductive MinMaxErr where
  | noArguments
  deriving DecidableEq

/- The result of constructing a lattice extremum:

     * `identityResult idv` — the lattice identity element `idv` is returned
       (the value that is the extremum of the EMPTY collection: the top element
       for a minimum, the bottom element for a maximum);
     * `single a` — exactly one member survives normalisation, returned verbatim;
     * `combined members` — two or more members survive; the extremum object over
       that normalised multiset is built. -/
inductive MinMaxResult where
  | identityResult (idv : Int)
  | single (a : Int)
  | combined (members : List Int)
  deriving DecidableEq

/- The intended outcome of constructing a lattice extremum from a raw argument
   list and the lattice identity element `idv`, as `Except MinMaxErr MinMaxResult`:

   the raw arguments are normalised (the unchanged `processArgs` pipeline), then
   the result is decided ENTIRELY by how many members survive —
     * none survive  ⇒ the identity element `idv` is returned (the extremum of the
       empty collection); in particular a call with no arguments at all yields the
       identity element rather than failing;
     * one survives  ⇒ that member is returned verbatim;
     * two or more    ⇒ the extremum object over the survivors is built.

   No input is rejected for being empty: the empty collection has a well-defined
   extremum, namely the identity element. -/
def minMaxResult (idv : Int) (rawArgs : List Int) : Except MinMaxErr MinMaxResult :=
  match processArgs rawArgs with
  | []           => Except.ok (MinMaxResult.identityResult idv)
  | [a]          => Except.ok (MinMaxResult.single a)
  | a :: b :: rest => Except.ok (MinMaxResult.combined (a :: b :: rest))
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Construct a lattice extremum (a minimum or a maximum) from a raw argument list
   and the lattice identity element `idv` (the top element for a minimum, the
   bottom element for a maximum — the extremum of the empty collection).

   Desired behaviour: the constructor normalises its raw arguments through the
   unchanged argument-normalisation pipeline and then decides the result purely by
   how many members survive — none ⇒ the identity element, one ⇒ that member,
   two or more ⇒ the extremum object. Crucially it must NOT reject an empty
   argument list: the empty collection has a well-defined extremum, the identity
   element, so a call with no arguments returns `idv` instead of failing.

   `idv` and `rawArgs` are read-only (not `mut`): the constructor computes a
   result and mutates no input (directive 5). Arguments are modeled as opaque
   handles (`Int`); the only observations are the normalisation outcome
   (`processArgs rawArgs`) and the supplied identity element (mapping.md §2). -/
method constructMinMax (idv : Int) (rawArgs : List Int)
    return (out : Except MinMaxErr MinMaxResult)
  ensures out = minMaxResult idv rawArgs
  ensures rawArgs = [] → out = Except.ok (MinMaxResult.identityResult idv)
  do
    -- impl-start
    -- Normalise the raw arguments (unchanged pipeline) and decide the result by
    -- how many members survive. There is NO rejection of an empty argument list:
    -- the empty collection's extremum is the identity element, reached through
    -- the empty-normalisation branch below.
    let result : Except MinMaxErr MinMaxResult :=
      match processArgs rawArgs with
      | []           => Except.ok (MinMaxResult.identityResult idv)
      | [a]          => Except.ok (MinMaxResult.single a)
      | a :: b :: rest => Except.ok (MinMaxResult.combined (a :: b :: rest))
    return result
    -- impl-end

prove_correct constructMinMax by
  loom_solve <;> simp_all [minMaxResult, processArgs_nil]
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec structure: constructMinMax carries a TOTAL functional postcondition `ensures out = minMaxResult idv rawArgs` (plus the redundant empty-case `rawArgs=[] -> identityResult idv`). This pins `out` on EVERY input, so any impl that verifies against the frozen spec is provably behaviourally equal to the count-driven model minMaxResult. The prove_correct tactic block is byte-identical, so a verifying impl must actually be simp-provably equal to the model. No behavioural slack exists for a wrong-but-verifying impl.

8 same-spec attacks built (impl region only; same_spec=True for all 8; verified via swebench_unified.markers.same_spec / get_backend('velvet')). Command per attack: `bash scripts/lean_verify.sh <file>` from project root.

### Verify results
- pos_control.lean (gold impl): exit 0 VERIFIES (positive control passes).
- atk_1 (prepatch bug: reject empty args -> Except.error noArguments): exit 1 FAILS to verify — the empty-case postcondition goal `¬rawArgs=[]` is unprovable. verify correctly rejects the prepatch bug (prepatch_reproduced=true).
- atk_2 (boundary: match rawArgs [] up front else pipeline; behaviourally equal): exit 1 FAILS — fixed tactic cannot close the case-split (unsolved goals). Not a verifying impl -> does not count.
- atk_3 (partial-domain: lone survivor [a] -> combined [a] instead of single a): exit 1 FAILS. correctly rejected.
- atk_4 (empty survivor set -> single 0 instead of identityResult idv): exit 1 FAILS. correctly rejected.
- atk_5 (control-flow: bind `let surv := processArgs rawArgs` then dispatch; behaviourally EQUAL to model): exit 0 VERIFIES.
- atk_6 (ungrounded-oracle echo: `return minMaxResult idv rawArgs` verbatim; behaviourally EQUAL): exit 0 VERIFIES.
- atk_7 (partial-domain: single raw arg [a] returned verbatim bypassing normalisation): exit 1 FAILS. correctly rejected.
- atk_8 (build combined over wrong survivor multiset — drop head, b::rest): exit 1 FAILS. correctly rejected.

Both VERIFYING attacks (atk_5, atk_6) are behaviourally identical to the gold model (a `let`-binding refactor and a verbatim model echo, respectively). Their faithful refined patch is therefore the gold-behaviour patch (delete the two-line empty-args guard so the empty call falls through to `if not args: return cls.identity`), which is byte-identical to patch.diff / dataset gold.

RESOLVE (protocol step 2, EXECUTED — not speculated): materialized faithful_patch.diff and ran run_resolve('sympy__sympy-15809', patch, timeout=1800, retries=1) via swebench_unified.harness. Result: RESOLVED=True, COMPLETED=True, NOTE='resolved', ATTEMPTS=1 (FAIL_TO_PASS test_Min/test_Max + PASS_TO_PASS pass). Both atk_5 and atk_6 share this identical faithful patch, so both resolve. No verifying wrong impl exists whose faithful patch fails to resolve.

refinement.md AUDIT: legs A1/A2 = R (List Int handle / cls.identity abstraction); A3 = A-consumed (processArgs opaque, sole axiom processArgs_nil); A4/A5/A6 = I (identity/single/combined result legs). No kind-3 (inexpressible) leg — the changed op (removing the empty rejection) is modeled directly by the empty branch reachable on []. A-consumed axiom `processArgs_nil : processArgs [] = []` re-validated against the REAL unchanged base pipeline: ran _new_args_filter -> _collapse_arguments -> _find_localzeros on [] for both Max and Min at base_commit (guard restored) -> both return set() (empty). Axiom is sound and base-valid; the empty->identity leg is the patched behaviour, correctly validated by G-RESOLVE/G-CONF rather than G-AX. A-legs' correspondence to real callees holds.

Conclusion: verify DOES imply correct here — the total functional postcondition leaves no behavioural gap. >=5 attacks run (8), the sole verifying-impl class has an executed resolving faithful patch, and the A-leg axiom is sound. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Verdict FAITHFUL. Evidence: (1) same_spec(Solution.lean, Solution_prepatch.lean, velvet)=True — spec-view (axioms/pure/pre/post + signature) is byte-identical; only impl+proof differ, so the spec region is legitimately frozen. (2) The modeled change is the empty-args fix: patch.diff deletes the 2-line ValueError guard so Min()/Max() fall through to `if not args: return cls.identity`. Real repo confirms Min()==oo, Max()==-oo; the model pins this load-bearingly via `ensures rawArgs=[] -> out=ok(identityResult idv)` and via minMaxResult's empty branch (which depends on axiom processArgs_nil). Solution_prepatch.lean reproduces the guard and fails exactly this clause (G-DIFF). processArgs_nil is base-valid: I ran the real _new_args_filter/_collapse_arguments/_find_localzeros chain — empty input yields empty survivors for both Max and Min. (3) The non-comparable ValueError divergence is (a) in behavior UNCHANGED by the patch (the raise at :521 exists pre- and post-patch), (b) explicitly disclosed in mapping.md §3.1 and refinement.md §3.1 ("raises ValueError on non-comparable args such as I … none of that is changed by the patch and none of it is load-bearing"), and (c) inside the benchmark's accepted opaque-callee abstraction (directive 7): only the COUNT of surviving members and the empty/non-empty distinction are observed, so processArgs is deliberately unconstrained on non-empty inputs. The executable faithfulness gate conformance_check.py builds its SHADOW on the REAL pipeline (so non-comparable behavior matches the oracle by construction) and fuzzes only comparable syms/ints, so this path never surfaces as a disagreement; within the modeled (comparable) domain the model matches reality on empty/single/two-or-more and the discriminating empty->identity case. This is a disclosed, non-load-bearing abstraction boundary on unchanged callee behavior — the spec is NOT too strong: it neither rejects a resolving impl nor admits a non-resolving one on the modeled domain. Spec is faithful.

Counterexample / evidence:

```
SHADOW/model on rawArgs=[I] => Except.ok (single ...); ORACLE (real repo, post-patch) Max(I) => raises ValueError. Also probed: ShortCircuit/absorbing case Max(x, oo)=oo, Min(x,-oo)=-oo returns cls.zero before the count-dispatch — this is observationally reconcilable because processArgs is opaque/unconstrained on non-empty inputs and the returned value is one of the args, so it is NOT a divergence.
```

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec region byte-identical between Solution.lean and Solution_prepatch.lean (swebench_unified.markers.same_spec = True). Mechanical G-LEAK screen (leakage.screen) passes with zero hard failures.

Gold edit: removes the `if not args: raise ValueError("The Max/Min functions must have arguments.")` guard in MinMaxBase.__new__, so empty Min()/Max() return the identity element (oo/-oo) instead of raising.

This desired behavior is fully PUBLIC in problem_statement: 'Right now Min() and Max() with no arguments raise ValueError... It might be mathematically more convenient to have them return oo and -oo, respectively.' The spec's discriminating requirement — empty argument list yields the identity element rather than failing (`ensures rawArgs = [] -> out = Except.ok (identityResult idv)`) — is exactly this stated behavior, so it cannot leak beyond the problem statement.

Leakage checks, all clean:
- No gold-diff string reproduced (no 'ValueError', no 'The Max/Min functions must have arguments', no diff markers).
- No patched file path/module (miscellaneous.py) in view.
- No patched repo symbol leaked: gold hunk touches only __new__ (non-distinctive); constructMinMax/minMaxResult/processArgs are model-invented names, not repo symbols.
- processArgs normalization prose describes the UNCHANGED helper (sympify/flatten/drop-identity/dominated), modeling context, not the edit.
- No bug/fix narration; MinMaxErr.noArguments comment cites the public problem statement.

The spec is a faithful formalization of a fully-public desired behavior; nothing localizes the gold edit beyond the solver-visible problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
