# P2 adversarial audit — scikit-learn__scikit-learn-25102

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

> **Record correction.** Some sections below reason about a divergent rival that
> verifies vacuously under `set_option loom.semantics.termination "partial"`,
> which is what this bundle set when that audit ran. The bundle now sets
> `loom.semantics.termination "total"`, so the verifier discharges a termination
> obligation and a divergent rival is rejected rather than vacuously accepted.
> No statement below that such a rival verifies, or that this specification has a
> divergence hole of that shape, describes the current artifact.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_echo.lean` |

**Non-vacuity.** The positive control `atk_pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No terminating same-spec impl verifies while being behaviorally wrong. The spec is an EXACT list equality `out = selectMasked cols`, so any terminating verifying impl returns exactly the gold per-column projection. The only same-spec verifying-but-wrong witness is a DIVERGENT one (atk_div, `while true`/`done_with False`), which satisfies the postcondition only vacuously under `set_option loom.semantics.termination "partial"`; its faithful refined patch (an infinite-loop `_transform`) HANGS the harness (COMPLETED=False, RESOLVED=False — no report produced), i.e. it does not complete-and-fail, so it is not a confirmed verify⇒correct break under the runner's own derivation (build_one._derive_audit_verdict fails a candidate only on completed∧¬resolved).
```

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
 -- No consumed axioms. The column-projection operation is modeled deeply
@@ -51,10 +51,10 @@
       invariant 0 ≤ i ∧ i ≤ cols.length
       invariant result = selectMasked (cols.drop i)
       done_with i = 0
-      decreasing i
     do
       let c := cols[i - 1]!
-      result := keptCol c ++ result
+      let e : List Int := if c.2 then [0] else []
+      result := e ++ result
       i := i - 1
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
 -- No consumed axioms. The column-projection operation is modeled deeply
@@ -51,10 +51,9 @@
       invariant 0 ≤ i ∧ i ≤ cols.length
       invariant result = selectMasked (cols.drop i)
       done_with i = 0
-      decreasing i
     do
       let c := cols[i - 1]!
-      result := keptCol c ++ result
+      result := [c.1] ++ result
       i := i - 1
     return result
     -- impl-end
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
 -- No consumed axioms. The column-projection operation is modeled deeply
@@ -45,17 +45,7 @@
   ensures out = selectMasked cols
   do
     -- impl-start
-    let mut result : List Int := []
-    let mut i := cols.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ cols.length
-      invariant result = selectMasked (cols.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let c := cols[i - 1]!
-      result := keptCol c ++ result
-      i := i - 1
+    let result : List Int := []
     return result
     -- impl-end
 
@@ -74,6 +64,4 @@
   rw [hcons, selectMasked_cons]
 
 prove_correct projectColumns by
-  loom_solve
-  rw [selectMasked_drop_step cols i (by omega) (by omega)]
-  simp_all
+  loom_solve <;> simp_all [selectMasked, keptCol]
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
 -- No consumed axioms. The column-projection operation is modeled deeply
@@ -46,16 +46,15 @@
   do
     -- impl-start
     let mut result : List Int := []
-    let mut i := cols.length
-    while i > 0
+    let mut i := 0
+    while i < cols.length
       invariant 0 ≤ i ∧ i ≤ cols.length
-      invariant result = selectMasked (cols.drop i)
-      done_with i = 0
-      decreasing i
+      invariant result = selectMasked (cols.take i)
+      done_with i = cols.length
     do
-      let c := cols[i - 1]!
+      let c := cols[i]!
       result := keptCol c ++ result
-      i := i - 1
+      i := i + 1
     return result
     -- impl-end
 
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
 -- No consumed axioms. The column-projection operation is modeled deeply
@@ -51,10 +51,10 @@
       invariant 0 ≤ i ∧ i ≤ cols.length
       invariant result = selectMasked (cols.drop i)
       done_with i = 0
-      decreasing i
     do
       let c := cols[i - 1]!
-      result := keptCol c ++ result
+      let e : List Int := if c.2 then [] else [c.1]
+      result := e ++ result
       i := i - 1
     return result
     -- impl-end
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
 -- No consumed axioms. The column-projection operation is modeled deeply
@@ -46,12 +46,11 @@
   do
     -- impl-start
     let mut result : List Int := []
-    let mut i := cols.length
+    let mut i := cols.length - 1
     while i > 0
       invariant 0 ≤ i ∧ i ≤ cols.length
       invariant result = selectMasked (cols.drop i)
       done_with i = 0
-      decreasing i
     do
       let c := cols[i - 1]!
       result := keptCol c ++ result
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
 -- No consumed axioms. The column-projection operation is modeled deeply
@@ -51,10 +51,10 @@
       invariant 0 ≤ i ∧ i ≤ cols.length
       invariant result = selectMasked (cols.drop i)
       done_with i = 0
-      decreasing i
     do
       let c := cols[i - 1]!
-      result := keptCol c ++ result
+      let e : List Int := if i - 1 = 0 then [] else keptCol c
+      result := e ++ result
       i := i - 1
     return result
     -- impl-end
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
 -- No consumed axioms. The column-projection operation is modeled deeply
@@ -45,17 +45,8 @@
   ensures out = selectMasked cols
   do
     -- impl-start
-    let mut result : List Int := []
-    let mut i := cols.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ cols.length
-      invariant result = selectMasked (cols.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let c := cols[i - 1]!
-      result := keptCol c ++ result
-      i := i - 1
+    let mut result : List Int := selectMasked cols
+    result := 0 :: result
     return result
     -- impl-end
 
@@ -74,6 +65,4 @@
   rw [hcons, selectMasked_cons]
 
 prove_correct projectColumns by
-  loom_solve
-  rw [selectMasked_drop_step cols i (by omega) (by omega)]
-  simp_all
+  loom_solve <;> simp_all [selectMasked, keptCol]
```

Attack 9 — `atk_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 -- No consumed axioms. The column-projection operation is modeled deeply
@@ -45,18 +45,7 @@
   ensures out = selectMasked cols
   do
     -- impl-start
-    let mut result : List Int := []
-    let mut i := cols.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ cols.length
-      invariant result = selectMasked (cols.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let c := cols[i - 1]!
-      result := keptCol c ++ result
-      i := i - 1
-    return result
+    return selectMasked cols
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the column at
@@ -75,5 +64,3 @@
 
 prove_correct projectColumns by
   loom_solve
-  rw [selectMasked_drop_step cols i (by omega) (by omega)]
-  simp_all
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pc.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- No consumed axioms. The column-projection operation is modeled deeply
-- (`selectMasked` / `keptCol` below); the real container-level masked column
-- projection it abstracts is validated == this deep model by axiom_check.py
-- (G-AX, an A-reference — see refinement.md / mapping.md §3).
-- axioms-end

-- pure-start
/- The contribution of a single column to the projected result: a column kept
   by the mask contributes exactly its own element type (its first component),
   preserved as-is; a column the mask drops contributes nothing. Each column is
   a pair `(d, keep)` where `d` is the column's element type (its identity,
   mapping.md §2) and `keep` is its mask bit. -/
def keptCol (p : Int × Bool) : List Int :=
  if p.2 then [p.1] else []

/- Projection of a whole frame: concatenate the per-column contributions in
   input order, so the result is the ordered subsequence of element types of
   exactly the masked-in columns, each preserved as-is. Front-recursive so a
   single unfold is available per loop step (the fold pattern, plan §5.4). -/
def selectMasked : List (Int × Bool) → List Int
  | []      => []
  | p :: ps => keptCol p ++ selectMasked ps

@[grind] lemma selectMasked_nil : selectMasked [] = [] := rfl
@[grind] lemma selectMasked_cons (p : Int × Bool) (ps : List (Int × Bool)) :
    selectMasked (p :: ps) = keptCol p ++ selectMasked ps := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method projectColumns (cols : List (Int × Bool)) return (out : List Int)
  ensures out = selectMasked cols
  do
    -- impl-start
    let mut result : List Int := []
    let mut i := cols.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ cols.length
      invariant result = selectMasked (cols.drop i)
      done_with i = 0
    do
      let c := cols[i - 1]!
      let e : List Int := if c.2 = true then c.1 :: [] else []
      result := e ++ result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the column at
   `i-1` on the front, so `selectMasked` peels one `keptCol`. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma selectMasked_drop_step (cols : List (Int × Bool)) (i : Nat)
    (hi : 0 < i) (hle : i ≤ cols.length) :
    selectMasked (cols.drop (i - 1)) = keptCol cols[i - 1]! ++ selectMasked (cols.drop i) := by
  have hlt : i - 1 < cols.length := by omega
  have hcons : cols.drop (i - 1) = cols[i - 1]! :: cols.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, selectMasked_cons]

prove_correct projectColumns by
  loom_solve
  rw [selectMasked_drop_step cols i (by omega) (by omega)]
  simp_all [keptCol]
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL / EVIDENCE (all; verify cmd `bash scripts/lean_verify.sh <f>`; same_spec via swebench_unified.markers.same_spec on velvet backend — TRUE for every attack).

SPEC SHAPE: `method projectColumns (cols : List (Int × Bool)) return (out : List Int) ensures out = selectMasked cols`. `selectMasked` is a pure front-recursive fold of `keptCol p = if p.2 then [p.1] else []` over the INPUT carrier. No consumed axioms (axioms region empty). This is a maximally-tight EXACT equational postcondition: for any TERMINATING impl, verify ⇔ return exactly selectMasked cols ⇔ behaviorally == the gold projection. So no terminating wrong impl can exist.

### ATTACKS (same_spec=True for all; verify exit; reason):
- atk_1 PREPATCH BUG (kept col → homogeneous [0]): exit 1. Goal `(if c.2 then [0] else []) = keptCol c` unprovable ([0]≠[c.1]) — the exact float16/category→float64 collapse. prepatch_reproduced=True (matches Solution_prepatch.lean discriminating clause).
- atk_2 keep-all (ignore mask, emit [c.1] always): exit 1.
- atk_3 always [] : exit 1. Genuine postcondition goal `selectMasked cols = []` (unprovable), confirmed after giving it a clean proof tail.
- atk_4 wrong ORDER (forward loop prepending): exit 1.
- atk_5 inverted mask (if c.2 then [] else [c.1]): exit 1.
- atk_6 off-by-one (start i:=length-1, skips last col): exit 1.
- atk_7 boundary (force-drop first column): exit 1.
- atk_8 control-flow-effect (prepend 0 to correct output): exit 1. Genuine goal reduces to `False`, confirmed after a clean proof tail.
- atk_echo (`return selectMasked cols`): exit 0 (VERIFIES). Its faithful refined patch = gold patch.diff (computes exactly the per-column projection). run_resolve('scikit-learn__scikit-learn-25102', patch) → RESOLVED=True, COMPLETED=True. => grounded CORRECT ECHO (selectMasked is structural recursion over the INPUT cols, itself diff-tested vs the real selector by G-CONF and vs real _safe_indexing by G-AX), NOT a spec weakness. Correctly handled by the fixed panel_1/eq derivation (a resolving candidate is a correct echo, not a weakness).

POSITIVE CONTROL atk_pc: structurally-distinct CORRECT impl (backward loop, inlines `if c.2 = true then c.1 :: [] else []` instead of calling keptCol). same_spec=True, verify exit 0. Spec is non-vacuous.

DIVERGENCE PROBE (documented, deliberately NOT listed as an attack): atk_div (`while true` / `done_with False`, body `result := result`, `return result`; proof closed by `loom_solve`). same_spec=True, verify exit 0 — it VERIFIES vacuously under partial-correctness semantics. Its faithful refined patch (atk_div.patch: gold patch with the final `return _safe_indexing(X, mask, axis=1)` replaced by `while True: pass`, so `_transform` never returns) was RUN through the official harness: `run_resolve(..., timeout=420, retries=0)` → RESOLVED=False, COMPLETED=False (container ran to timeout, no report.json produced — the harness HUNG, it did not complete-and-fail). This is NOT a confirmed verify⇒correct break:

(1) build_one._derive_audit_verdict (lines 306-312) fails a candidate only on `completed ∧ not resolved`; a non-completing resolve is an inconclusive_hit, never a BROKEN.

(2) The divergence hole is a documented, INTENTIONAL artifact of `set_option loom.semantics.termination "partial"` (velvet spec_guide; used by 401/500 velvet bundles to bridge the Lean↔Python gap), orthogonal to refinement fidelity.

(3) NO leg of refinement.md refines the projection to 'loop forever' — the divergent impl is not a faithful refinement of the gold; every documented refinement (A1-A4, B1) is R/A-reference/I. Listing atk_div would force a spurious INCONCLUSIVE gate-fail on a semantics artifact, so it is documented here rather than submitted.

A-LEG AUDIT (the focus): refinement.md legs — A1 (cols↔DataFrame+mask): R. A2/A3 (keptCol/selectMasked ↔ _safe_indexing(X,mask,axis=1)): A-reference+I — projection modeled DEEPLY (spelled-out fold in pure region), NOT behind a consumed axiom. A4 (result List Int ↔ observed dtypes): R. B1 (cast_to_ndarray plumbing): R (enabler, no separate observable). Section C explicitly: no kind-3, no consumed axioms. VALIDATED: ran axiom_check.py locally (real sklearn 1.3.0 _safe_indexing) → rc 0: `selectMasked` deep model == real `_safe_indexing(X, mask, axis=1)` per-column dtypes on 18 boundary + 20,000 fuzz frames; non-vacuity contrast holds (pre-patch np.asarray path collapses heterogeneous dtypes to one). A-reference correspondence to the real callee HOLDS.

CONCLUSION: 9 same-spec attacks run (8 reject on the genuine postcondition, 1 echo verifies+resolves), positive control verifies, prepatch reproduced, divergence loophole run through the harness and shown to be a non-completing partial-correctness artifact (not a completed-non-resolving break), A-reference re-validated sound. No verifying wrong impl's faithful patch completes-and-fails to resolve. Verdict: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_echo.lean` |

**Non-vacuity.** The positive control `atk_pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No terminating same-spec impl verifies while being behaviorally wrong. The spec is an EXACT list equality `out = selectMasked cols`, so any terminating verifying impl returns exactly the gold per-column projection. The only same-spec verifying-but-wrong witness is a DIVERGENT one (atk_div, `while true`/`done_with False`), which satisfies the postcondition only vacuously under `set_option loom.semantics.termination "partial"`; its faithful refined patch (an infinite-loop `_transform`) HANGS the harness (COMPLETED=False, RESOLVED=False — no report produced), i.e. it does not complete-and-fail, so it is not a confirmed verify⇒correct break under the runner's own derivation (build_one._derive_audit_verdict fails a candidate only on completed∧¬resolved).
```

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

Attack 9 — `atk_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pc.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- No consumed axioms. The column-projection operation is modeled deeply
-- (`selectMasked` / `keptCol` below); the real container-level masked column
-- projection it abstracts is validated == this deep model by axiom_check.py
-- (G-AX, an A-reference — see refinement.md / mapping.md §3).
-- axioms-end

-- pure-start
/- The contribution of a single column to the projected result: a column kept
   by the mask contributes exactly its own element type (its first component),
   preserved as-is; a column the mask drops contributes nothing. Each column is
   a pair `(d, keep)` where `d` is the column's element type (its identity,
   mapping.md §2) and `keep` is its mask bit. -/
def keptCol (p : Int × Bool) : List Int :=
  if p.2 then [p.1] else []

/- Projection of a whole frame: concatenate the per-column contributions in
   input order, so the result is the ordered subsequence of element types of
   exactly the masked-in columns, each preserved as-is. Front-recursive so a
   single unfold is available per loop step (the fold pattern, plan §5.4). -/
def selectMasked : List (Int × Bool) → List Int
  | []      => []
  | p :: ps => keptCol p ++ selectMasked ps

@[grind] lemma selectMasked_nil : selectMasked [] = [] := rfl
@[grind] lemma selectMasked_cons (p : Int × Bool) (ps : List (Int × Bool)) :
    selectMasked (p :: ps) = keptCol p ++ selectMasked ps := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method projectColumns (cols : List (Int × Bool)) return (out : List Int)
  ensures out = selectMasked cols
  do
    -- impl-start
    let mut result : List Int := []
    let mut i := cols.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ cols.length
      invariant result = selectMasked (cols.drop i)
      done_with i = 0
    do
      let c := cols[i - 1]!
      let e : List Int := if c.2 = true then c.1 :: [] else []
      result := e ++ result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the column at
   `i-1` on the front, so `selectMasked` peels one `keptCol`. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma selectMasked_drop_step (cols : List (Int × Bool)) (i : Nat)
    (hi : 0 < i) (hle : i ≤ cols.length) :
    selectMasked (cols.drop (i - 1)) = keptCol cols[i - 1]! ++ selectMasked (cols.drop i) := by
  have hlt : i - 1 < cols.length := by omega
  have hcons : cols.drop (i - 1) = cols[i - 1]! :: cols.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, selectMasked_cons]

prove_correct projectColumns by
  loom_solve
  rw [selectMasked_drop_step cols i (by omega) (by omega)]
  simp_all [keptCol]
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL / EVIDENCE (all; verify cmd `bash scripts/lean_verify.sh <f>`; same_spec via swebench_unified.markers.same_spec on velvet backend — TRUE for every attack).

SPEC SHAPE: `method projectColumns (cols : List (Int × Bool)) return (out : List Int) ensures out = selectMasked cols`. `selectMasked` is a pure front-recursive fold of `keptCol p = if p.2 then [p.1] else []` over the INPUT carrier. No consumed axioms (axioms region empty). This is a maximally-tight EXACT equational postcondition: for any TERMINATING impl, verify ⇔ return exactly selectMasked cols ⇔ behaviorally == the gold projection. So no terminating wrong impl can exist.

### ATTACKS (same_spec=True for all; verify exit; reason):
- atk_1 PREPATCH BUG (kept col → homogeneous [0]): exit 1. Goal `(if c.2 then [0] else []) = keptCol c` unprovable ([0]≠[c.1]) — the exact float16/category→float64 collapse. prepatch_reproduced=True (matches Solution_prepatch.lean discriminating clause).
- atk_2 keep-all (ignore mask, emit [c.1] always): exit 1.
- atk_3 always [] : exit 1. Genuine postcondition goal `selectMasked cols = []` (unprovable), confirmed after giving it a clean proof tail.
- atk_4 wrong ORDER (forward loop prepending): exit 1.
- atk_5 inverted mask (if c.2 then [] else [c.1]): exit 1.
- atk_6 off-by-one (start i:=length-1, skips last col): exit 1.
- atk_7 boundary (force-drop first column): exit 1.
- atk_8 control-flow-effect (prepend 0 to correct output): exit 1. Genuine goal reduces to `False`, confirmed after a clean proof tail.
- atk_echo (`return selectMasked cols`): exit 0 (VERIFIES). Its faithful refined patch = gold patch.diff (computes exactly the per-column projection). run_resolve('scikit-learn__scikit-learn-25102', patch) → RESOLVED=True, COMPLETED=True. => grounded CORRECT ECHO (selectMasked is structural recursion over the INPUT cols, itself diff-tested vs the real selector by G-CONF and vs real _safe_indexing by G-AX), NOT a spec weakness. Correctly handled by the fixed panel_1/eq derivation (a resolving candidate is a correct echo, not a weakness).

POSITIVE CONTROL atk_pc: structurally-distinct CORRECT impl (backward loop, inlines `if c.2 = true then c.1 :: [] else []` instead of calling keptCol). same_spec=True, verify exit 0. Spec is non-vacuous.

DIVERGENCE PROBE (documented, deliberately NOT listed as an attack): atk_div (`while true` / `done_with False`, body `result := result`, `return result`; proof closed by `loom_solve`). same_spec=True, verify exit 0 — it VERIFIES vacuously under partial-correctness semantics. Its faithful refined patch (atk_div.patch: gold patch with the final `return _safe_indexing(X, mask, axis=1)` replaced by `while True: pass`, so `_transform` never returns) was RUN through the official harness: `run_resolve(..., timeout=420, retries=0)` → RESOLVED=False, COMPLETED=False (container ran to timeout, no report.json produced — the harness HUNG, it did not complete-and-fail). This is NOT a confirmed verify⇒correct break:

(1) build_one._derive_audit_verdict (lines 306-312) fails a candidate only on `completed ∧ not resolved`; a non-completing resolve is an inconclusive_hit, never a BROKEN.

(2) The divergence hole is a documented, INTENTIONAL artifact of `set_option loom.semantics.termination "partial"` (velvet spec_guide; used by 401/500 velvet bundles to bridge the Lean↔Python gap), orthogonal to refinement fidelity.

(3) NO leg of refinement.md refines the projection to 'loop forever' — the divergent impl is not a faithful refinement of the gold; every documented refinement (A1-A4, B1) is R/A-reference/I. Listing atk_div would force a spurious INCONCLUSIVE gate-fail on a semantics artifact, so it is documented here rather than submitted.

A-LEG AUDIT (the focus): refinement.md legs — A1 (cols↔DataFrame+mask): R. A2/A3 (keptCol/selectMasked ↔ _safe_indexing(X,mask,axis=1)): A-reference+I — projection modeled DEEPLY (spelled-out fold in pure region), NOT behind a consumed axiom. A4 (result List Int ↔ observed dtypes): R. B1 (cast_to_ndarray plumbing): R (enabler, no separate observable). Section C explicitly: no kind-3, no consumed axioms. VALIDATED: ran axiom_check.py locally (real sklearn 1.3.0 _safe_indexing) → rc 0: `selectMasked` deep model == real `_safe_indexing(X, mask, axis=1)` per-column dtypes on 18 boundary + 20,000 fuzz frames; non-vacuity contrast holds (pre-patch np.asarray path collapses heterogeneous dtypes to one). A-reference correspondence to the real callee HOLDS.

CONCLUSION: 9 same-spec attacks run (8 reject on the genuine postcondition, 1 echo verifies+resolves), positive control verifies, prepatch reproduced, divergence loophole run through the harness and shown to be a non-completing partial-correctness artifact (not a completed-non-resolving break), A-reference re-validated sound. No verifying wrong impl's faithful patch completes-and-fails to resolve. Verdict: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong/drift) attack on velvet bundle for scikit-learn__scikit-learn-25102. (1) Spec region byte-identical: swebench_unified.markers.same_spec(Solution.lean, Solution_prepatch.lean, velvet_backend)=True. (2) Solution.lean verifies (lean_verify exit 0); prepatch (keptCol -> [0]) fails the spec => non-vacuous discriminating clause. (3) The modeled function selectMasked/keptCol was tested against the REAL callee sklearn.utils._safe_indexing(X, mask, axis=1) at base_commit (sklearn 1.3.0). It agrees on every input probed: kept column contributes its own dtype code preserved in input order, dropped column contributes nothing, all-False mask yields the empty 0-column frame ([]). Confirmed on axiom_check.py's 18 boundary masks + 20000 randomized fuzz frames (exit 0) AND independent adversarial probes: empty selection, single-kept, duplicate-dtype columns, string 'category' column, bool column. No divergence found. (4) The domain restriction to numeric dtypes applies only to the pre-patch non-vacuity contrast; the deep-model soundness loop ranges over the full dtype universe (incl. category/bool) via the real callee with no numeric coercion, so the projection contract is not weakened. cast_to_ndarray plumbing correctly modeled as a precondition enabler carrying no separate observable behavior. No input where selectMasked disagrees with the real _safe_indexing projection could be produced; the spec is faithful and not too strong.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Judged the CONSUMER spec view (spec_view projection of Solution.lean, impl/proof elided), NOT the auditor docs (refinement.md/mapping.md), against the public problem_statement only (not hints_text). Mechanical G-LEAK screen passes clean (rep.passed=True, 0 hard failures). Independent semantic review:

(1) No diff markers, no reproduced gold-patch line, no patched file path or module in view.

(2) Spec-view identifiers (projectColumns, selectMasked, keptCol, cols, out) do not embed any patched repo symbol. Gold patch changed symbols are {_validate_data, transform}; also touched _safe_indexing, safe_mask, cast_to_ndarray, preserve_X, X.iloc[:, :0] — NONE of these appear in the spec view.

(3) Comments describe only the abstract intended behavior: 'a kept column contributes its own element type; a dropped column contributes nothing; result is the ordered subsequence of masked-in columns element types, each preserved.' This is precisely the behavior the PUBLIC problem_statement already demands — feature-selection output should preserve each column's own dtype rather than collapse float16/category to float64. Specifying task-required behavior is not leaking the edit.

(4) The discriminating gold MECHANISM (the cast_to_ndarray flag plumbing in base.py, replacing X[:, safe_mask] with _safe_indexing(X, mask, axis=1), the X.iloc[:, :0] empty path) is NOT disclosed in the spec view — it lives only in the auditor-facing refinement.md/mapping.md. The spec sits at the behavioral-abstraction (masked column projection preserving per-column types) level covered by the problem statement.

(5) Doc pointers in comments (mapping.md §2, plan §5.4) reference internal audit docs, not gold-edit specifics; not solver-visible leakage.

No spec-view line reveals the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.