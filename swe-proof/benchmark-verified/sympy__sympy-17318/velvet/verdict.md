# P2 adversarial audit — sympy__sympy-17318

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 5 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 5 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 5 | `atk_2.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The frozen spec resists falsification. matchAddTerms's three postconditions form a TOTAL partition of the input space (allPosRat=true; allPosRat=false & maxDepth=0; allPosRat=false & maxDepth != 0), so EVERY verifying impl is forced to the identical Outcome function as gold. The ungrounded-oracle echo (atk_2/atk_7, which return matched on the allPosRat leg WITHOUT calling fastSplit) verifies, but its faithful refined patch is still the gold guard change (A3/A5 bind Outcome.matched on the allPosRat leg to the real split_surds decomposition per mapping.md §2). I materialized and RAN both the map-faithful patch AND an adversarial value-FABRICATION patch (allPosRat leg returns a dummy non-empty 3-list [p,0,0] WITHOUT split_surds — the strictest literal reading of the ungrounded echo). BOTH resolved=True. Even fabricated matched-branch values pass all 205 tests (F2P test_issue_12420 + 204 P2P), because the fix only alters WHICH of empty/matched is produced (the coarse Outcome model is exactly right per mapping.md §2.4). No verify⇏correct hole exists.
```

**Attacks re-run (5):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_2.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 /- No module-level consumed `axiom`. The one community callee modeled here is a
@@ -91,7 +91,7 @@
   do
     -- impl-start
     let r ← if allPosRat xs then
-        fastSplit xs
+        pure Outcome.matched
       else
         if maxDepth xs = 0 then
           pure Outcome.empty
```

Attack 2 — `atk_4.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 /- No module-level consumed `axiom`. The one community callee modeled here is a
@@ -93,10 +93,7 @@
     let r ← if allPosRat xs then
         fastSplit xs
       else
-        if maxDepth xs = 0 then
-          pure Outcome.empty
-        else
-          pure Outcome.matched
+        pure (if maxDepth xs = 0 then Outcome.empty else Outcome.matched)
     return r
     -- impl-end
 
```

Attack 3 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 /- No module-level consumed `axiom`. The one community callee modeled here is a
@@ -90,8 +90,12 @@
   ensures allPosRat xs = false → maxDepth xs ≠ 0 → out = Outcome.matched
   do
     -- impl-start
+    let _ ← if allPosRat xs then
+        fastSplit xs
+      else
+        pure Outcome.matched
     let r ← if allPosRat xs then
-        fastSplit xs
+        pure Outcome.matched
       else
         if maxDepth xs = 0 then
           pure Outcome.empty
```

Attack 4 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 /- No module-level consumed `axiom`. The one community callee modeled here is a
@@ -90,14 +90,12 @@
   ensures allPosRat xs = false → maxDepth xs ≠ 0 → out = Outcome.matched
   do
     -- impl-start
-    let r ← if allPosRat xs then
-        fastSplit xs
-      else
-        if maxDepth xs = 0 then
-          pure Outcome.empty
-        else
-          pure Outcome.matched
-    return r
+    if allPosRat xs then
+      return (← fastSplit xs)
+    else if maxDepth xs = 0 then
+      return Outcome.empty
+    else
+      return Outcome.matched
     -- impl-end
 
 prove_correct matchAddTerms by
```

Attack 5 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 /- No module-level consumed `axiom`. The one community callee modeled here is a
@@ -90,14 +90,9 @@
   ensures allPosRat xs = false → maxDepth xs ≠ 0 → out = Outcome.matched
   do
     -- impl-start
-    let r ← if allPosRat xs then
-        fastSplit xs
-      else
-        if maxDepth xs = 0 then
-          pure Outcome.empty
-        else
-          pure Outcome.matched
-    return r
+    return (if allPosRat xs then Outcome.matched
+            else if maxDepth xs = 0 then Outcome.empty
+            else Outcome.matched)
     -- impl-end
 
 prove_correct matchAddTerms by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No module-level consumed `axiom`. The one community callee modeled here is a
   structural-decomposition routine, captured below as the `fastSplit` method
   stub (its contract is the WEAKEST one the dispatch needs): it is only defined
   for sums whose terms each have a positive-rational square, and on that domain
   it always succeeds in producing a decomposition. Provenance + executable
   soundness check: mapping.md §3 / axiom_check.py (G-AX). -/
-- axioms-end

-- pure-start
/- A single addend of a sum, abstracted by exactly the three observations the
   decomposition decision depends on:
     * `sqRat`  — its square is a rational number;
     * `sqPos`  — its square is a positive number;
     * `depth`  — its nesting depth of square roots (0 for a plain atom). -/
structure Addend where
  sqRat : Bool
  sqPos : Bool
  depth : Nat
deriving DecidableEq, Inhabited

/- The possible outcomes of matching a sum against the shape `a + b·√r`:
   either a decomposition is produced (`matched`) or the sum has none
   (`empty`). These mirror the function's `[a, b, r]` vs `[]` results. -/
inductive Outcome where
  | empty
  | matched
deriving DecidableEq, Inhabited

/- The domain of the fast structural split: every term of the sum must have a
   positive-rational square. Only within this domain is the gcd-based split a
   well-defined total operation. -/
def allPosRat (xs : List Addend) : Bool :=
  xs.all (fun a => a.sqRat && a.sqPos)

/- The maximal square-root nesting depth among the terms of the sum (0 when the
   sum contains no nested radical at all). -/
def maxDepth (xs : List Addend) : Nat :=
  xs.foldl (fun m a => Nat.max m a.depth) 0
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The fast structural split of a sum into the `a + b·√r` shape via the common
   gcd of the (squared) surds. It is a PARTIAL operation: it is only defined for
   sums all of whose terms have a positive-rational square (`allPosRat`); on that
   domain it always yields a decomposition. Calling it outside that domain is not
   permitted — the precondition pins the domain so no caller may invoke it on a
   sum outside it. Models an unchanged community routine (mapping.md §3,
   G-AX-checked); read-only input (directive 5). -/
method fastSplit (xs : List Addend) return (r : Outcome)
  require allPosRat xs = true
  ensures r = Outcome.matched
  do
    -- impl-start
    return Outcome.matched
    -- impl-end

prove_correct fastSplit by
  loom_solve

/- Match a sum of terms against the shape `a + b·√r`, returning whether a
   decomposition exists. The decision proceeds in two regimes:

   * When every term of the sum has a positive-rational square, the sum lies in
     the domain of the fast structural split (`fastSplit`), which always produces
     a decomposition.
   * Otherwise the sum is routed to the general depth-based procedure: it yields
     no decomposition exactly when the sum contains no nested radical (its
     maximal root-nesting depth is 0); when some term is itself a radical it
     produces a decomposition.

   The fast split is invoked ONLY within its domain; the general regime is total.
   `xs` is read-only (directive 5). -/
method matchAddTerms (xs : List Addend) return (out : Outcome)
  ensures allPosRat xs = true → out = Outcome.matched
  ensures allPosRat xs = false → maxDepth xs = 0 → out = Outcome.empty
  ensures allPosRat xs = false → maxDepth xs ≠ 0 → out = Outcome.matched
  do
    -- impl-start
    let r ← if allPosRat xs then
        fastSplit xs
      else
        if maxDepth xs = 0 then
          pure Outcome.empty
        else
          pure Outcome.matched
    return r
    -- impl-end

prove_correct matchAddTerms by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

SAME-SPEC: all 7 attacks + pos_control return same_spec=True (velvet spec_signature identical; only impl regions edited).

VERIFY (bash scripts/lean_verify.sh <f>), run concurrently ≤4/batch:
  pos_control.lean exit=0 (VERIFIES — positive control OK)
  atk_1.lean  exit=1 (PREPATCH BUG: weak guard `xs.all sqRat` -> fastSplit called out of domain; error at 103:28 'unsolved goals case require_1: allPosRat xs = true' -> `require allPosRat` undischargeable. prepatch_reproduced=TRUE)
  atk_2.lean  exit=0 VERIFIES  (ungrounded-oracle echo: allPosRat leg returns Outcome.matched via `pure`, NEVER calls fastSplit)
  atk_3.lean  exit=1 (wrong-argument callee: fastSplit on filtered sublist; loom cannot prove allPosRat(filter …) -> NOT a same-spec verifier, discarded)
  atk_4.lean  exit=0 VERIFIES  (control-flow-effect: else-branch collapsed to pure if; still calls fastSplit in-domain)
  atk_5.lean  exit=0 VERIFIES  (call-and-discard: invokes fastSplit in-domain then ignores its result, returns matched by fiat)
  atk_6.lean  exit=0 VERIFIES  (early-return restructure, monadic bind of fastSplit)
  atk_7.lean  exit=0 VERIFIES  (pure ungrounded echo: single `return (if …)`, no monadic callee at all)

5 same-spec VERIFYING wrong/variant impls: atk_2, atk_4, atk_5, atk_6, atk_7 (>= the required 4-6, spanning ungrounded-oracle echo, control-flow-effect, call-discard, boundary/restructure).

### RESOLVE (harness.run_resolve, swe_bench_verified, docker oracle live, timeout 1800):
  faithful_gold.diff (= map-faithful refined patch of ALL verifying attacks; gold guard change binding matched->real split_surds) -> resolved=True completed=True note='resolved'
  faithful_atk2_fabricate.diff (adversarial: allPosRat leg returns [p,S.Zero,S.Zero] WITHOUT split_surds — strictest literal reading of the ungrounded echo atk_2/atk_7) -> resolved=True completed=True note='resolved'
Every verifying attack's faithful refined patch RESOLVES. No `verified & ¬resolved` witness exists.

WHY SOUND: matchAddTerms postconditions are a TOTAL partition -> all verifying impls are Outcome-identical to gold. The Outcome abstraction (empty/matched via len==0) is the ONLY behavior the fix changes; the F2P (test_issue_12420: _sqrt_match(4+I)==[] with no IndexError) + 204 P2P pin exactly which of empty/matched, not the algebraic decomposition values (produced by UNCHANGED split_surds/general matcher). Confirmed empirically: even the fabricated-values patch passes all 205 tests. The ungrounded echo does NOT break the spec because its faithful refinement (A3/A5 ground matched in the real callee) IS the gold change.

REFINEMENT.MD AUDIT: legs A1(R), A2(R+I), A3(A-consumed + A-reference), A4(R+I), A5(R). All R/A/I; NO kind-3 (§C). A3 A-reference fastSplit<->split_surds validated by G-AX/axiom_check.py: S1 (on allPosRat, split_surds returns 3-tuple, never raises/[]), S2 (off-domain IndexError witnessed) -> domain neither too wide nor too narrow. §B radsimp.py hunks are docstring-only (no impl op) — correctly excluded. Correspondence holds.

Verdict SOUND: >=5 same-spec verifying attacks run, prepatch reproduced, positive control verifies, and every verifying attack's materialized faithful patch was EXECUTED through run_resolve and resolved.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 5 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 5 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 5 | `atk_2.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The frozen spec resists falsification. matchAddTerms's three postconditions form a TOTAL partition of the input space (allPosRat=true; allPosRat=false & maxDepth=0; allPosRat=false & maxDepth != 0), so EVERY verifying impl is forced to the identical Outcome function as gold. The ungrounded-oracle echo (atk_2/atk_7, which return matched on the allPosRat leg WITHOUT calling fastSplit) verifies, but its faithful refined patch is still the gold guard change (A3/A5 bind Outcome.matched on the allPosRat leg to the real split_surds decomposition per mapping.md §2). I materialized and RAN both the map-faithful patch AND an adversarial value-FABRICATION patch (allPosRat leg returns a dummy non-empty 3-list [p,0,0] WITHOUT split_surds — the strictest literal reading of the ungrounded echo). BOTH resolved=True. Even fabricated matched-branch values pass all 205 tests (F2P test_issue_12420 + 204 P2P), because the fix only alters WHICH of empty/matched is produced (the coarse Outcome model is exactly right per mapping.md §2.4). No verify⇏correct hole exists.
```

**Attacks re-run (5):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 5 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_2.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 2 — `atk_4.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 3 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 4 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 5 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No module-level consumed `axiom`. The one community callee modeled here is a
   structural-decomposition routine, captured below as the `fastSplit` method
   stub (its contract is the WEAKEST one the dispatch needs): it is only defined
   for sums whose terms each have a positive-rational square, and on that domain
   it always succeeds in producing a decomposition. Provenance + executable
   soundness check: mapping.md §3 / axiom_check.py (G-AX). -/
-- axioms-end

-- pure-start
/- A single addend of a sum, abstracted by exactly the three observations the
   decomposition decision depends on:
     * `sqRat`  — its square is a rational number;
     * `sqPos`  — its square is a positive number;
     * `depth`  — its nesting depth of square roots (0 for a plain atom). -/
structure Addend where
  sqRat : Bool
  sqPos : Bool
  depth : Nat
deriving DecidableEq, Inhabited

/- The possible outcomes of matching a sum against the shape `a + b·√r`:
   either a decomposition is produced (`matched`) or the sum has none
   (`empty`). These mirror the function's `[a, b, r]` vs `[]` results. -/
inductive Outcome where
  | empty
  | matched
deriving DecidableEq, Inhabited

/- The domain of the fast structural split: every term of the sum must have a
   positive-rational square. Only within this domain is the gcd-based split a
   well-defined total operation. -/
def allPosRat (xs : List Addend) : Bool :=
  xs.all (fun a => a.sqRat && a.sqPos)

/- The maximal square-root nesting depth among the terms of the sum (0 when the
   sum contains no nested radical at all). -/
def maxDepth (xs : List Addend) : Nat :=
  xs.foldl (fun m a => Nat.max m a.depth) 0
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The fast structural split of a sum into the `a + b·√r` shape via the common
   gcd of the (squared) surds. It is a PARTIAL operation: it is only defined for
   sums all of whose terms have a positive-rational square (`allPosRat`); on that
   domain it always yields a decomposition. Calling it outside that domain is not
   permitted — the precondition pins the domain so no caller may invoke it on a
   sum outside it. Models an unchanged community routine (mapping.md §3,
   G-AX-checked); read-only input (directive 5). -/
method fastSplit (xs : List Addend) return (r : Outcome)
  require allPosRat xs = true
  ensures r = Outcome.matched
  do
    -- impl-start
    return Outcome.matched
    -- impl-end

prove_correct fastSplit by
  loom_solve

/- Match a sum of terms against the shape `a + b·√r`, returning whether a
   decomposition exists. The decision proceeds in two regimes:

   * When every term of the sum has a positive-rational square, the sum lies in
     the domain of the fast structural split (`fastSplit`), which always produces
     a decomposition.
   * Otherwise the sum is routed to the general depth-based procedure: it yields
     no decomposition exactly when the sum contains no nested radical (its
     maximal root-nesting depth is 0); when some term is itself a radical it
     produces a decomposition.

   The fast split is invoked ONLY within its domain; the general regime is total.
   `xs` is read-only (directive 5). -/
method matchAddTerms (xs : List Addend) return (out : Outcome)
  ensures allPosRat xs = true → out = Outcome.matched
  ensures allPosRat xs = false → maxDepth xs = 0 → out = Outcome.empty
  ensures allPosRat xs = false → maxDepth xs ≠ 0 → out = Outcome.matched
  do
    -- impl-start
    let r ← if allPosRat xs then
        fastSplit xs
      else
        if maxDepth xs = 0 then
          pure Outcome.empty
        else
          pure Outcome.matched
    return r
    -- impl-end

prove_correct matchAddTerms by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

SAME-SPEC: all 7 attacks + pos_control return same_spec=True (velvet spec_signature identical; only impl regions edited).

VERIFY (bash scripts/lean_verify.sh <f>), run concurrently ≤4/batch:
  pos_control.lean exit=0 (VERIFIES — positive control OK)
  atk_1.lean  exit=1 (PREPATCH BUG: weak guard `xs.all sqRat` -> fastSplit called out of domain; error at 103:28 'unsolved goals case require_1: allPosRat xs = true' -> `require allPosRat` undischargeable. prepatch_reproduced=TRUE)
  atk_2.lean  exit=0 VERIFIES  (ungrounded-oracle echo: allPosRat leg returns Outcome.matched via `pure`, NEVER calls fastSplit)
  atk_3.lean  exit=1 (wrong-argument callee: fastSplit on filtered sublist; loom cannot prove allPosRat(filter …) -> NOT a same-spec verifier, discarded)
  atk_4.lean  exit=0 VERIFIES  (control-flow-effect: else-branch collapsed to pure if; still calls fastSplit in-domain)
  atk_5.lean  exit=0 VERIFIES  (call-and-discard: invokes fastSplit in-domain then ignores its result, returns matched by fiat)
  atk_6.lean  exit=0 VERIFIES  (early-return restructure, monadic bind of fastSplit)
  atk_7.lean  exit=0 VERIFIES  (pure ungrounded echo: single `return (if …)`, no monadic callee at all)

5 same-spec VERIFYING wrong/variant impls: atk_2, atk_4, atk_5, atk_6, atk_7 (>= the required 4-6, spanning ungrounded-oracle echo, control-flow-effect, call-discard, boundary/restructure).

### RESOLVE (harness.run_resolve, swe_bench_verified, docker oracle live, timeout 1800):
  faithful_gold.diff (= map-faithful refined patch of ALL verifying attacks; gold guard change binding matched->real split_surds) -> resolved=True completed=True note='resolved'
  faithful_atk2_fabricate.diff (adversarial: allPosRat leg returns [p,S.Zero,S.Zero] WITHOUT split_surds — strictest literal reading of the ungrounded echo atk_2/atk_7) -> resolved=True completed=True note='resolved'
Every verifying attack's faithful refined patch RESOLVES. No `verified & ¬resolved` witness exists.

WHY SOUND: matchAddTerms postconditions are a TOTAL partition -> all verifying impls are Outcome-identical to gold. The Outcome abstraction (empty/matched via len==0) is the ONLY behavior the fix changes; the F2P (test_issue_12420: _sqrt_match(4+I)==[] with no IndexError) + 204 P2P pin exactly which of empty/matched, not the algebraic decomposition values (produced by UNCHANGED split_surds/general matcher). Confirmed empirically: even the fabricated-values patch passes all 205 tests. The ungrounded echo does NOT break the spec because its faithful refinement (A3/A5 ground matched in the real callee) IS the gold change.

REFINEMENT.MD AUDIT: legs A1(R), A2(R+I), A3(A-consumed + A-reference), A4(R+I), A5(R). All R/A/I; NO kind-3 (§C). A3 A-reference fastSplit<->split_surds validated by G-AX/axiom_check.py: S1 (on allPosRat, split_surds returns 3-tuple, never raises/[]), S2 (off-domain IndexError witnessed) -> domain neither too wide nor too narrow. §B radsimp.py hunks are docstring-only (no impl op) — correctly excluded. Correspondence holds.

Verdict SOUND: >=5 same-spec verifying attacks run, prepatch reproduced, positive control verifies, and every verifying attack's materialized faithful patch was EXECUTED through run_resolve and resolved.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong/drift) audit for sympy__sympy-17318 velvet. Spec region byte-identical (same_spec Solution vs prepatch = True); Solution.lean verifies (lean_verify exit 0). matchAddTerms models the post-patch p.is_Add branch of _sqrt_match via allPosRat/maxDepth with three ensures legs. Tested against the real repo at base_commit 33b47e4bd6 (post-patch _sqrt_match): ~190k random Add inputs + 40k broad adversarial fuzz (rationals, sqrt of rationals, imaginary I, symbols, transcendentals, nested radicals, negatives) -> 0 spec/repo mismatches. 56k allPosRat inputs: real function never returned [] and never raised, confirming the 'allPosRat=true -> matched' leg is not too strong (split_surds is total & non-empty on-domain). Verified the subtle equivalence nmax[0]==0 <=> maxDepth==0 (default_sort_key orders the (depth,x,i) tuples by depth first) holds under fuzzing, so the maxDepth abstraction of nmax[0] is faithful. Issue discriminator 4+I: real repo returns [4,1,-1] (matched) since sqrt_depth(I)=1; spec gives allPosRat=false, maxDepth=1 != 0 -> matched — agrees. No diverging input found; the modeled function agrees with the real callee everywhere tested. NOTE (documentation only, NOT a spec defect): refinement.md §2 asserts '_sqrt_match(4 + I) == []', which is factually wrong against the actual post-patch repo (it returns [4, 1, -1] = matched). The Lean spec itself correctly predicts matched for 4+I, so this is an erroneous prose narration, not a spec/repo divergence. G-CONF (100000 inputs, 0 disagreements) and G-AX (domain stub sound) corroborate.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Attacker role 3 (leakage / gold-reconstruction). Mechanical leakage.screen() PASSES: no diff markers, no reproduced gold-patch lines, no patched file/module paths, no spec-view identifier embedding a patched symbol (patched distinctive symbols = {handle, denom_expand, sqrt_match}; none appear or are embedded), no patched symbol in comments, no narration terms. same_spec(Solution, Solution_prepatch)=True (spec region frozen; prepatch differs only in impl/proof). Token scan confirms none of _sqrt_match/split_surds/radsimp/sqrtdenest/rad_rationalize/is_positive/is_rational/IndexError/pargs/_split_gcd appear in the spec view. Semantic check: gold edit strengthens the is_Add dispatch guard to also require is_positive. The public problem_statement gives only the IndexError traceback and 'return unchanged if it cannot be denested'; the 'positive' requirement lives in hints_text (out of scope). The spec view models correct behavior abstractly via Addend.sqPos / allPosRat = sqRat && sqPos and the matchAddTerms ensures clauses. This is a spec describing correct behavior in abstract carrier types — it names no repo symbol, file, line, or diff, and does not narrate a bug/fix. Describing the correct dispatch condition is the legitimate purpose of a spec, not reconstruction of the gold patch beyond the public problem_statement. No leak.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
