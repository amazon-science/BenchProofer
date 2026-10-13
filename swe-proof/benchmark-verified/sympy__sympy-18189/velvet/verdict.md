# P2 adversarial audit — sympy__sympy-18189

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 9 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean` |

**Non-vacuity.** The positive control `pos_correct2.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

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
 /- The base solver consulted when the caller requests the results in a particular
@@ -64,9 +64,7 @@
   ensures out = reorderAll order (baseSolve permute)
   do
     -- impl-start
-    -- Consult the base solver with the SAME variant flag the caller requested,
-    -- then reindex each produced tuple into the requested variable order.
-    let base := baseSolve permute
+    let base := baseSolve false
     let result := reorderAll order base
     return result
     -- impl-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

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
 /- The base solver consulted when the caller requests the results in a particular
@@ -64,11 +64,7 @@
   ensures out = reorderAll order (baseSolve permute)
   do
     -- impl-start
-    -- Consult the base solver with the SAME variant flag the caller requested,
-    -- then reindex each produced tuple into the requested variable order.
-    let base := baseSolve permute
-    let result := reorderAll order base
-    return result
+    return reorderAll order (baseSolve (!permute))
     -- impl-end
 
 prove_correct reorderSolutions by
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

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
 /- The base solver consulted when the caller requests the results in a particular
@@ -64,11 +64,7 @@
   ensures out = reorderAll order (baseSolve permute)
   do
     -- impl-start
-    -- Consult the base solver with the SAME variant flag the caller requested,
-    -- then reindex each produced tuple into the requested variable order.
-    let base := baseSolve permute
-    let result := reorderAll order base
-    return result
+    return reorderAll order (baseSolve true)
     -- impl-end
 
 prove_correct reorderSolutions by
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

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
 /- The base solver consulted when the caller requests the results in a particular
@@ -64,11 +64,7 @@
   ensures out = reorderAll order (baseSolve permute)
   do
     -- impl-start
-    -- Consult the base solver with the SAME variant flag the caller requested,
-    -- then reindex each produced tuple into the requested variable order.
-    let base := baseSolve permute
-    let result := reorderAll order base
-    return result
+    return baseSolve permute
     -- impl-end
 
 prove_correct reorderSolutions by
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

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
 /- The base solver consulted when the caller requests the results in a particular
@@ -64,11 +64,7 @@
   ensures out = reorderAll order (baseSolve permute)
   do
     -- impl-start
-    -- Consult the base solver with the SAME variant flag the caller requested,
-    -- then reindex each produced tuple into the requested variable order.
-    let base := baseSolve permute
-    let result := reorderAll order base
-    return result
+    return []
     -- impl-end
 
 prove_correct reorderSolutions by
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

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
 /- The base solver consulted when the caller requests the results in a particular
@@ -64,11 +64,7 @@
   ensures out = reorderAll order (baseSolve permute)
   do
     -- impl-start
-    -- Consult the base solver with the SAME variant flag the caller requested,
-    -- then reindex each produced tuple into the requested variable order.
-    let base := baseSolve permute
-    let result := reorderAll order base
-    return result
+    return reorderAll order.reverse (baseSolve permute)
     -- impl-end
 
 prove_correct reorderSolutions by
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

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
 /- The base solver consulted when the caller requests the results in a particular
@@ -64,11 +64,7 @@
   ensures out = reorderAll order (baseSolve permute)
   do
     -- impl-start
-    -- Consult the base solver with the SAME variant flag the caller requested,
-    -- then reindex each produced tuple into the requested variable order.
-    let base := baseSolve permute
-    let result := reorderAll order base
-    return result
+    return reorderAll order (reorderAll order (baseSolve permute))
     -- impl-end
 
 prove_correct reorderSolutions by
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

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
 /- The base solver consulted when the caller requests the results in a particular
@@ -64,11 +64,7 @@
   ensures out = reorderAll order (baseSolve permute)
   do
     -- impl-start
-    -- Consult the base solver with the SAME variant flag the caller requested,
-    -- then reindex each produced tuple into the requested variable order.
-    let base := baseSolve permute
-    let result := reorderAll order base
-    return result
+    return (reorderAll order (baseSolve permute)).take 1
     -- impl-end
 
 prove_correct reorderSolutions by
```

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

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
 /- The base solver consulted when the caller requests the results in a particular
@@ -64,11 +64,10 @@
   ensures out = reorderAll order (baseSolve permute)
   do
     -- impl-start
-    -- Consult the base solver with the SAME variant flag the caller requested,
-    -- then reindex each produced tuple into the requested variable order.
-    let base := baseSolve permute
-    let result := reorderAll order base
-    return result
+    if permute then
+      return reorderAll order (baseSolve false)
+    else
+      return reorderAll order (baseSolve permute)
     -- impl-end
 
 prove_correct reorderSolutions by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_correct2.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- The base solver consulted when the caller requests the results in a particular
   variable ordering. It is the UNCHANGED routine that produces the full solution
   set for an equation, taking a single Boolean that selects whether the extra
   variant solutions (sign and value variants) are included alongside the base
   solution. It is invoked here, never redefined.

   Each solution it returns is a tuple of integer values, one per variable, listed
   in the routine's own canonical variable order; the whole result is the list of
   such tuples. It is modeled `opaque` with NO asserted `ensures`: the desired
   behavior assumes nothing about WHICH tuples it returns for a given flag — only
   that the flag it is given is the same one the caller asked for. Provenance +
   executable soundness check (that this is exactly the canonical solver's output
   for each flag value): mapping.md §3 / axiom_check.py (G-AX). -/
opaque baseSolve : Bool → List (List Int)
-- axioms-end

-- pure-start
/- Reindex one solution tuple into the requested variable order: `order` lists,
   for each requested position, the index of that variable within the base
   solver's canonical tuple, so the reindexed tuple gathers those components in
   the requested order. A pure positional gather over the tuple's components. -/
def reorderTuple (order : List Nat) (t : List Int) : List Int :=
  order.map (fun k => t[k]!)

/- Reindex every solution in a result set into the requested variable order,
   preserving the set of solutions and only relabeling each tuple's components. -/
def reorderAll (order : List Nat) (ts : List (List Int)) : List (List Int) :=
  ts.map (reorderTuple order)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Produce the solution set of an equation when the caller has requested the
   tuple components in a particular variable order that differs from the solver's
   canonical one.

   Desired behavior: the routine consults the base solver and then reindexes each
   returned tuple into the requested order. The Boolean `permute` selects whether
   the additional variant solutions are produced. That selection must hold
   regardless of the requested ordering: the base solver is consulted with the
   SAME `permute` the caller asked for, so requesting a non-canonical variable
   order never suppresses the variants the caller selected. The result is exactly
   the reindexing of whatever full set the base solver produces for that flag.

   `order` and `permute` are read-only (directive 5): the routine computes a set
   and mutates no input. `baseSolve` is the unchanged base solver (mapping.md §3);
   `reorderAll`/`reorderTuple` are the positional reindexing the routine applies
   (a function of `order` and the produced tuples only). -/
method reorderSolutions (order : List Nat) (permute : Bool)
    return (out : List (List Int))
  ensures out = reorderAll order (baseSolve permute)
  do
    -- impl-start
    let base := baseSolve permute
    let result := reorderAll order base
    return result
    -- impl-end

prove_correct reorderSolutions by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

SPEC IS A MAXIMALLY-TIGHT FUNCTIONAL POSTCONDITION. ensures out = reorderAll order (baseSolve permute); the impl returns exactly that RHS, so the spec pins `out` as a closed function of the inputs (order, permute) and the opaque callee baseSolve. Only A-leg surface is opaque baseSolve (no ensures).

PROTOCOL: /tmp scratch dir All attacks built by copying the frozen Solution.lean and editing ONLY the impl region (axioms/pure/pre/post byte-identical). same_spec(velvet) verified True for all 9 attacks + all 3 positive controls (via swebench_unified.markers.same_spec + get_backend('velvet').language). Verifications run concurrently in background Bash batches (<=4 at a time) via `bash scripts/lean_verify.sh <file>`.

ATTACKS (all same_spec=True, all FAIL verify exit 1 at the exact clause `out = reorderAll order (baseSolve permute)`):
- atk_1 = PREPATCH BUG: `baseSolve false` (permute dropped). exit 1, residual goal `reorderAll order (baseSolve false) = reorderAll order (baseSolve permute)` -> prepatch reproduced.
- atk_2 = negated flag `baseSolve (!permute)`. exit 1.
- atk_3 = ungrounded-oracle echo, constant `baseSolve true`. exit 1.
- atk_4 = partial-domain: return base w/o reorder (`baseSolve permute`). exit 1.
- atk_5 = boundary: return []. exit 1.
- atk_6 = control-flow permutation error: `reorderAll order.reverse (baseSolve permute)`. exit 1.
- atk_7 = double reorder. exit 1.
- atk_8 = boundary/partial: `(reorderAll order (baseSolve permute)).take 1`. exit 1.
- atk_9 = control-flow-effect: `if permute then baseSolve false else baseSolve permute` (wrong flag on the true-branch). exit 1.

Commands: `bash scripts/lean_verify.sh <file>.lean`. Observed EXIT: atk_1..atk_9 = 1 (all).

### POSITIVE CONTROLS (same_spec=True, verify exit 0):
- pos_correct2 = exact gold impl body (`let base := baseSolve permute; let result := reorderAll order base; return result`) -> exit 0.
- pos_correct3 = structurally-different `.map (reorderTuple order)` form with proof augmented `simp [reorderAll, reorderTuple]` -> exit 0.
- original frozen Solution.lean -> exit 0.
Note: a naive positive control (pos_correct = `.map (reorderTuple order)` WITH the bare `loom_solve` proof) fails ONLY because loom_solve does not auto-unfold reorderAll/reorderTuple (residual goal `List.map (reorderTuple order) (baseSolve permute) = reorderAll order (baseSolve permute)`) — a proof-engineering gap, not a behavioral one; the same body verifies once the unfold is supplied (pos_correct3). This matches verdict.md's atk_7/atk_7b note. Chosen positive_control = pos_correct2 (the unambiguous exact-gold-body verifier).

RESOLVE: The protocol requires materializing a faithful refined patch and running run_resolve ONLY for wrong impls that VERIFY. ZERO wrong impls verify, so there is no verifying-but-wrong candidate to falsify with — the verify⇏correct break cannot be exhibited. No resolve run is applicable; `patches` is empty by construction, not by omission.

REFINEMENT AUDIT (refinement.md): tags A1(R) A2(R) A3(A-reference) A4(I) A5(R) — no kind-3 (inexpressible-changed-op). The one genuinely changed op (forwarding `permute` into the recursive base solve) is captured at the type level as a Bool threaded into the opaque baseSolve (A2/A3), not behind an over-claiming axiom. baseSolve is opaque with NO asserted ensures (weakest contract; nothing to consume). A3 A-reference correspondence holds: opaque baseSolve <-> real recursive diophantine(eq, param, permute=permute) with syms=None (mapping.md §3.1), which is off the changed path and validated by G-AX (deterministic in (eq,permute); flag load-bearing, issue eq m**4+n**4-97 gives 1 sol at False vs 8 at True). R/I legs (A1,A2,A4,A5) are G-CONF's domain. Correspondence audit passes.

CONCLUSION: verify => correct holds here. All >=5 (9) required distinct attacks were fully verified; none breaks the spec; positive control verifies. Verdict: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 9 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean` |

**Non-vacuity.** The positive control `pos_correct2.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

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

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_correct2.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- The base solver consulted when the caller requests the results in a particular
   variable ordering. It is the UNCHANGED routine that produces the full solution
   set for an equation, taking a single Boolean that selects whether the extra
   variant solutions (sign and value variants) are included alongside the base
   solution. It is invoked here, never redefined.

   Each solution it returns is a tuple of integer values, one per variable, listed
   in the routine's own canonical variable order; the whole result is the list of
   such tuples. It is modeled `opaque` with NO asserted `ensures`: the desired
   behavior assumes nothing about WHICH tuples it returns for a given flag — only
   that the flag it is given is the same one the caller asked for. Provenance +
   executable soundness check (that this is exactly the canonical solver's output
   for each flag value): mapping.md §3 / axiom_check.py (G-AX). -/
opaque baseSolve : Bool → List (List Int)
-- axioms-end

-- pure-start
/- Reindex one solution tuple into the requested variable order: `order` lists,
   for each requested position, the index of that variable within the base
   solver's canonical tuple, so the reindexed tuple gathers those components in
   the requested order. A pure positional gather over the tuple's components. -/
def reorderTuple (order : List Nat) (t : List Int) : List Int :=
  order.map (fun k => t[k]!)

/- Reindex every solution in a result set into the requested variable order,
   preserving the set of solutions and only relabeling each tuple's components. -/
def reorderAll (order : List Nat) (ts : List (List Int)) : List (List Int) :=
  ts.map (reorderTuple order)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Produce the solution set of an equation when the caller has requested the
   tuple components in a particular variable order that differs from the solver's
   canonical one.

   Desired behavior: the routine consults the base solver and then reindexes each
   returned tuple into the requested order. The Boolean `permute` selects whether
   the additional variant solutions are produced. That selection must hold
   regardless of the requested ordering: the base solver is consulted with the
   SAME `permute` the caller asked for, so requesting a non-canonical variable
   order never suppresses the variants the caller selected. The result is exactly
   the reindexing of whatever full set the base solver produces for that flag.

   `order` and `permute` are read-only (directive 5): the routine computes a set
   and mutates no input. `baseSolve` is the unchanged base solver (mapping.md §3);
   `reorderAll`/`reorderTuple` are the positional reindexing the routine applies
   (a function of `order` and the produced tuples only). -/
method reorderSolutions (order : List Nat) (permute : Bool)
    return (out : List (List Int))
  ensures out = reorderAll order (baseSolve permute)
  do
    -- impl-start
    let base := baseSolve permute
    let result := reorderAll order base
    return result
    -- impl-end

prove_correct reorderSolutions by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

SPEC IS A MAXIMALLY-TIGHT FUNCTIONAL POSTCONDITION. ensures out = reorderAll order (baseSolve permute); the impl returns exactly that RHS, so the spec pins `out` as a closed function of the inputs (order, permute) and the opaque callee baseSolve. Only A-leg surface is opaque baseSolve (no ensures).

PROTOCOL: /tmp scratch dir All attacks built by copying the frozen Solution.lean and editing ONLY the impl region (axioms/pure/pre/post byte-identical). same_spec(velvet) verified True for all 9 attacks + all 3 positive controls (via swebench_unified.markers.same_spec + get_backend('velvet').language). Verifications run concurrently in background Bash batches (<=4 at a time) via `bash scripts/lean_verify.sh <file>`.

ATTACKS (all same_spec=True, all FAIL verify exit 1 at the exact clause `out = reorderAll order (baseSolve permute)`):
- atk_1 = PREPATCH BUG: `baseSolve false` (permute dropped). exit 1, residual goal `reorderAll order (baseSolve false) = reorderAll order (baseSolve permute)` -> prepatch reproduced.
- atk_2 = negated flag `baseSolve (!permute)`. exit 1.
- atk_3 = ungrounded-oracle echo, constant `baseSolve true`. exit 1.
- atk_4 = partial-domain: return base w/o reorder (`baseSolve permute`). exit 1.
- atk_5 = boundary: return []. exit 1.
- atk_6 = control-flow permutation error: `reorderAll order.reverse (baseSolve permute)`. exit 1.
- atk_7 = double reorder. exit 1.
- atk_8 = boundary/partial: `(reorderAll order (baseSolve permute)).take 1`. exit 1.
- atk_9 = control-flow-effect: `if permute then baseSolve false else baseSolve permute` (wrong flag on the true-branch). exit 1.

Commands: `bash scripts/lean_verify.sh <file>.lean`. Observed EXIT: atk_1..atk_9 = 1 (all).

### POSITIVE CONTROLS (same_spec=True, verify exit 0):
- pos_correct2 = exact gold impl body (`let base := baseSolve permute; let result := reorderAll order base; return result`) -> exit 0.
- pos_correct3 = structurally-different `.map (reorderTuple order)` form with proof augmented `simp [reorderAll, reorderTuple]` -> exit 0.
- original frozen Solution.lean -> exit 0.
Note: a naive positive control (pos_correct = `.map (reorderTuple order)` WITH the bare `loom_solve` proof) fails ONLY because loom_solve does not auto-unfold reorderAll/reorderTuple (residual goal `List.map (reorderTuple order) (baseSolve permute) = reorderAll order (baseSolve permute)`) — a proof-engineering gap, not a behavioral one; the same body verifies once the unfold is supplied (pos_correct3). This matches verdict.md's atk_7/atk_7b note. Chosen positive_control = pos_correct2 (the unambiguous exact-gold-body verifier).

RESOLVE: The protocol requires materializing a faithful refined patch and running run_resolve ONLY for wrong impls that VERIFY. ZERO wrong impls verify, so there is no verifying-but-wrong candidate to falsify with — the verify⇏correct break cannot be exhibited. No resolve run is applicable; `patches` is empty by construction, not by omission.

REFINEMENT AUDIT (refinement.md): tags A1(R) A2(R) A3(A-reference) A4(I) A5(R) — no kind-3 (inexpressible-changed-op). The one genuinely changed op (forwarding `permute` into the recursive base solve) is captured at the type level as a Bool threaded into the opaque baseSolve (A2/A3), not behind an over-claiming axiom. baseSolve is opaque with NO asserted ensures (weakest contract; nothing to consume). A3 A-reference correspondence holds: opaque baseSolve <-> real recursive diophantine(eq, param, permute=permute) with syms=None (mapping.md §3.1), which is off the changed path and validated by G-AX (deterministic in (eq,permute); flag load-bearing, issue eq m**4+n**4-97 gives 1 sol at False vs 8 at True). R/I legs (A1,A2,A4,A5) are G-CONF's domain. Correspondence audit passes.

CONCLUSION: verify => correct holds here. All >=5 (9) required distinct attacks were fully verified; none breaks the spec; positive control verifies. Verdict: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec region byte-identical (swebench_unified.markers.same_spec(Solution, Solution_prepatch, Velvet.language) = True). Solution.lean verifies via lean_verify.sh (exit 0); Solution_prepatch.lean fails as required (G-DIFF). The modeled function reorderSolutions abstracts diophantine.py:182-185 (the syms-reorder branch). Its only spec clause is `out = reorderAll order (baseSolve permute)`, where baseSolve is an OPAQUE Bool->List(List Int) with NO ensures — the weakest possible contract. This is a minimal, not over-strong, model: the sole assumption is that the same `permute` the caller passes reaches the recursive base solve, which is exactly the content of the gold fix (pre-patch forwarded default False).

Empirical faithfulness checks against the real repo at base_commit (worktree, patch applied):
- reorderTuple/reorderAll transliteration (t[k]! positional gather -> [tup[k] for k in order]) matches the gold `tuple([t[dict_sym_index[i]] for i in var])` exactly on the issue equation (x**4+y**4-97, both syms orders), quadratics, and 3-variable full permutations, for permute in {False,True}.
- 3104 fuzzed in-branch (eq, syms, permute) inputs over a**deg+b**deg-N families: 0 model-vs-real disagreements (set-of-tuples comparison, the observation test_diophantine makes).
- Subset-of-syms edge case (request fewer syms than variables): real repo raises KeyError; this input is OUTSIDE the modeled branch domain (perm_and_var returns None / order-build KeyErrors), so no over-claim — the spec is not asserting behavior the repo doesn't have there.
- The set-vs-list carrier abstraction is sound because both reorderAll and the gold set-comprehension are per-tuple maps; membership/cardinality (the F2P observation) is preserved.
- G-AX independently confirms baseSolve == real diophantine(eq,param,permute=p) with syms=None, deterministic and flag load-bearing (issue eq 1->8 solutions), and that syms=None never enters the reorder branch (unchanged callee).

The modeled function agrees with the real callee on all tested in-domain inputs; no diverging input found. Spec is FAITHFUL (neither too strong nor drifting).

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec region verified byte-identical to Solution_prepatch.lean (same_spec=True). Gold edit: `diophantine(eq, param)` -> `diophantine(eq, param, permute=permute)` on the reordered-syms path (forward the caller's permute flag into the recursive base solve). The public problem_statement ALREADY fully exposes the discriminating behavior: it is titled 'diophantine: incomplete results depending on syms order with permute=True' and demonstrates syms=(m,n),permute=True -> 8 solutions vs syms=(n,m),permute=True -> 1 solution. The corrective requirement (reordering variables must not suppress the variants selected by permute) is directly derivable from that symptom. The spec view encodes exactly this correct behavior via `ensures out = reorderAll order (baseSolve permute)` plus prose ('the base solver is consulted with the SAME permute the caller asked for'). This is a spec doing its legitimate job, not a leak: it reveals nothing about the gold edit BEYOND the problem_statement. Specifically the spec view contains NO gold-patch specifics: no repo call form `diophantine(eq, param)`, no statement that the recursive call omitted permute, no pre-patch/False-default detail, no repo symbols/line numbers, no diff. The pre-patch discriminator prose ('received False unconditionally', `baseSolve false`) lives only in mapping.md and refinement.md, which are AUDIT docs — G-LEAK/leak.py screens solution_src() (the Solution.lean spec view) only, not those. `baseSolve` is opaque with no ensures, so it leaks no tuple-level behavior; reorderTuple/reorderAll describe pre-existing UNCHANGED reindexing code, not the fix. Nothing in the screened spec view reconstructs the gold edit beyond what the public problem_statement already states.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
