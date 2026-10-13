# P2 adversarial audit — django__django-11066

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
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `pos_return_db.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. The postcondition `ensures aliasEq out db` unfolds to `out = db` (aliasEq a b := a = b) — a fully FUNCTIONAL postcondition that pins the output to exactly the explicit alias `db`, with `routed` a free/unconstrained input. Therefore any TERMINATING impl that verifies must produce exactly `db`, i.e. is behaviorally the gold. No terminating verifying-but-wrong impl exists; all 8 value-computing attacks fail at `case «ensures_1: aliasEq out db»`. The only verifying wrong impl is a NON-TERMINATING one (atk_div), which is a universal partial-correctness artifact (see notes), not a spec weakness, and has no faithful refined patch.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

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
 -- (No axiomatized callees. The fallback routing policy's chosen target is taken
@@ -47,20 +47,13 @@
   ensures aliasEq out db
   do
     -- impl-start
-    -- The write target is `explicit or routing_policy_choice`: an explicit
-    -- (present, non-empty) handle is used directly; the routing-policy fallback
-    -- is reached only when no explicit handle is given. An explicit handle (db)
-    -- is always present here, so the resolution short-circuits to it.
-    let src : List Char := if db.length > 0 then db else routed
-    -- Copy the resolved handle into a fresh result carrier (the write commits to
-    -- the store this handle names).
+    let src : List Char := routed
     let mut result : List Char := []
     let mut i := src.length
     while i > 0
       invariant 0 ≤ i ∧ i ≤ src.length
       invariant result = src.drop i
       done_with i = 0
-      decreasing i
     do
       let c := src[i - 1]!
       result := c :: result
@@ -82,10 +75,7 @@
 
 prove_correct resolveTarget by
   loom_solve
-  · -- loop-body step: the resolution `if` reduces to the explicit handle `db`,
-    -- then the copy peels one code point off the front.
-    simp only [require_2, if_true] at *
-    rw [drop_copy_step db i (by omega) (by omega), invariant_2]
-  · -- exit: `result = db.drop 0 = db`, so `aliasEq result db` holds.
-    simp only [require_2, if_true, aliasEq] at *
+  · simp only [require_2, if_true] at *
+    rw [drop_copy_step routed i (by omega) (by omega), invariant_2]
+  · simp only [require_2, if_true, aliasEq] at *
     simp_all
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
 -- (No axiomatized callees. The fallback routing policy's chosen target is taken
@@ -47,20 +47,13 @@
   ensures aliasEq out db
   do
     -- impl-start
-    -- The write target is `explicit or routing_policy_choice`: an explicit
-    -- (present, non-empty) handle is used directly; the routing-policy fallback
-    -- is reached only when no explicit handle is given. An explicit handle (db)
-    -- is always present here, so the resolution short-circuits to it.
-    let src : List Char := if db.length > 0 then db else routed
-    -- Copy the resolved handle into a fresh result carrier (the write commits to
-    -- the store this handle names).
+    let src : List Char := if routed.length > 0 then routed else db
     let mut result : List Char := []
     let mut i := src.length
     while i > 0
       invariant 0 ≤ i ∧ i ≤ src.length
       invariant result = src.drop i
       done_with i = 0
-      decreasing i
     do
       let c := src[i - 1]!
       result := c :: result
@@ -82,10 +75,7 @@
 
 prove_correct resolveTarget by
   loom_solve
-  · -- loop-body step: the resolution `if` reduces to the explicit handle `db`,
-    -- then the copy peels one code point off the front.
-    simp only [require_2, if_true] at *
-    rw [drop_copy_step db i (by omega) (by omega), invariant_2]
-  · -- exit: `result = db.drop 0 = db`, so `aliasEq result db` holds.
-    simp only [require_2, if_true, aliasEq] at *
+  · simp only [require_2, if_true] at *
+    rw [drop_copy_step routed i (by omega) (by omega), invariant_2]
+  · simp only [require_2, if_true, aliasEq] at *
     simp_all
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
 -- (No axiomatized callees. The fallback routing policy's chosen target is taken
@@ -47,20 +47,13 @@
   ensures aliasEq out db
   do
     -- impl-start
-    -- The write target is `explicit or routing_policy_choice`: an explicit
-    -- (present, non-empty) handle is used directly; the routing-policy fallback
-    -- is reached only when no explicit handle is given. An explicit handle (db)
-    -- is always present here, so the resolution short-circuits to it.
-    let src : List Char := if db.length > 0 then db else routed
-    -- Copy the resolved handle into a fresh result carrier (the write commits to
-    -- the store this handle names).
+    let src : List Char := db ++ routed
     let mut result : List Char := []
     let mut i := src.length
     while i > 0
       invariant 0 ≤ i ∧ i ≤ src.length
       invariant result = src.drop i
       done_with i = 0
-      decreasing i
     do
       let c := src[i - 1]!
       result := c :: result
@@ -82,10 +75,7 @@
 
 prove_correct resolveTarget by
   loom_solve
-  · -- loop-body step: the resolution `if` reduces to the explicit handle `db`,
-    -- then the copy peels one code point off the front.
-    simp only [require_2, if_true] at *
-    rw [drop_copy_step db i (by omega) (by omega), invariant_2]
-  · -- exit: `result = db.drop 0 = db`, so `aliasEq result db` holds.
-    simp only [require_2, if_true, aliasEq] at *
+  · simp only [require_2, if_true] at *
+    rw [drop_copy_step (db ++ routed) i (by omega) (by omega), invariant_2]
+  · simp only [require_2, if_true, aliasEq] at *
     simp_all
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
 -- (No axiomatized callees. The fallback routing policy's chosen target is taken
@@ -47,25 +47,7 @@
   ensures aliasEq out db
   do
     -- impl-start
-    -- The write target is `explicit or routing_policy_choice`: an explicit
-    -- (present, non-empty) handle is used directly; the routing-policy fallback
-    -- is reached only when no explicit handle is given. An explicit handle (db)
-    -- is always present here, so the resolution short-circuits to it.
-    let src : List Char := if db.length > 0 then db else routed
-    -- Copy the resolved handle into a fresh result carrier (the write commits to
-    -- the store this handle names).
-    let mut result : List Char := []
-    let mut i := src.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ src.length
-      invariant result = src.drop i
-      done_with i = 0
-      decreasing i
-    do
-      let c := src[i - 1]!
-      result := c :: result
-      i := i - 1
-    return result
+    return ([] : List Char)
     -- impl-end
 
 /- The backward-copy step: dropping one fewer element exposes the element at
@@ -81,11 +63,4 @@
   rw [h, hsucc]
 
 prove_correct resolveTarget by
-  loom_solve
-  · -- loop-body step: the resolution `if` reduces to the explicit handle `db`,
-    -- then the copy peels one code point off the front.
-    simp only [require_2, if_true] at *
-    rw [drop_copy_step db i (by omega) (by omega), invariant_2]
-  · -- exit: `result = db.drop 0 = db`, so `aliasEq result db` holds.
-    simp only [require_2, if_true, aliasEq] at *
-    simp_all
+  loom_solve <;> simp_all [aliasEq]
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
 -- (No axiomatized callees. The fallback routing policy's chosen target is taken
@@ -47,25 +47,7 @@
   ensures aliasEq out db
   do
     -- impl-start
-    -- The write target is `explicit or routing_policy_choice`: an explicit
-    -- (present, non-empty) handle is used directly; the routing-policy fallback
-    -- is reached only when no explicit handle is given. An explicit handle (db)
-    -- is always present here, so the resolution short-circuits to it.
-    let src : List Char := if db.length > 0 then db else routed
-    -- Copy the resolved handle into a fresh result carrier (the write commits to
-    -- the store this handle names).
-    let mut result : List Char := []
-    let mut i := src.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ src.length
-      invariant result = src.drop i
-      done_with i = 0
-      decreasing i
-    do
-      let c := src[i - 1]!
-      result := c :: result
-      i := i - 1
-    return result
+    return db.reverse
     -- impl-end
 
 /- The backward-copy step: dropping one fewer element exposes the element at
@@ -81,11 +63,4 @@
   rw [h, hsucc]
 
 prove_correct resolveTarget by
-  loom_solve
-  · -- loop-body step: the resolution `if` reduces to the explicit handle `db`,
-    -- then the copy peels one code point off the front.
-    simp only [require_2, if_true] at *
-    rw [drop_copy_step db i (by omega) (by omega), invariant_2]
-  · -- exit: `result = db.drop 0 = db`, so `aliasEq result db` holds.
-    simp only [require_2, if_true, aliasEq] at *
-    simp_all
+  loom_solve <;> simp_all [aliasEq]
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
 -- (No axiomatized callees. The fallback routing policy's chosen target is taken
@@ -47,25 +47,7 @@
   ensures aliasEq out db
   do
     -- impl-start
-    -- The write target is `explicit or routing_policy_choice`: an explicit
-    -- (present, non-empty) handle is used directly; the routing-policy fallback
-    -- is reached only when no explicit handle is given. An explicit handle (db)
-    -- is always present here, so the resolution short-circuits to it.
-    let src : List Char := if db.length > 0 then db else routed
-    -- Copy the resolved handle into a fresh result carrier (the write commits to
-    -- the store this handle names).
-    let mut result : List Char := []
-    let mut i := src.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ src.length
-      invariant result = src.drop i
-      done_with i = 0
-      decreasing i
-    do
-      let c := src[i - 1]!
-      result := c :: result
-      i := i - 1
-    return result
+    return db.tail
     -- impl-end
 
 /- The backward-copy step: dropping one fewer element exposes the element at
@@ -81,11 +63,4 @@
   rw [h, hsucc]
 
 prove_correct resolveTarget by
-  loom_solve
-  · -- loop-body step: the resolution `if` reduces to the explicit handle `db`,
-    -- then the copy peels one code point off the front.
-    simp only [require_2, if_true] at *
-    rw [drop_copy_step db i (by omega) (by omega), invariant_2]
-  · -- exit: `result = db.drop 0 = db`, so `aliasEq result db` holds.
-    simp only [require_2, if_true, aliasEq] at *
-    simp_all
+  loom_solve <;> simp_all [aliasEq]
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
 -- (No axiomatized callees. The fallback routing policy's chosen target is taken
@@ -47,20 +47,13 @@
   ensures aliasEq out db
   do
     -- impl-start
-    -- The write target is `explicit or routing_policy_choice`: an explicit
-    -- (present, non-empty) handle is used directly; the routing-policy fallback
-    -- is reached only when no explicit handle is given. An explicit handle (db)
-    -- is always present here, so the resolution short-circuits to it.
-    let src : List Char := if db.length > 0 then db else routed
-    -- Copy the resolved handle into a fresh result carrier (the write commits to
-    -- the store this handle names).
+    let src : List Char := db.take (db.length - 1)
     let mut result : List Char := []
     let mut i := src.length
     while i > 0
       invariant 0 ≤ i ∧ i ≤ src.length
       invariant result = src.drop i
       done_with i = 0
-      decreasing i
     do
       let c := src[i - 1]!
       result := c :: result
@@ -82,10 +75,7 @@
 
 prove_correct resolveTarget by
   loom_solve
-  · -- loop-body step: the resolution `if` reduces to the explicit handle `db`,
-    -- then the copy peels one code point off the front.
-    simp only [require_2, if_true] at *
-    rw [drop_copy_step db i (by omega) (by omega), invariant_2]
-  · -- exit: `result = db.drop 0 = db`, so `aliasEq result db` holds.
-    simp only [require_2, if_true, aliasEq] at *
+  · simp only [require_2, if_true] at *
+    rw [drop_copy_step (db.take (db.length - 1)) i (by omega) (by omega), invariant_2]
+  · simp only [require_2, if_true, aliasEq] at *
     simp_all
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
 -- (No axiomatized callees. The fallback routing policy's chosen target is taken
@@ -47,25 +47,7 @@
   ensures aliasEq out db
   do
     -- impl-start
-    -- The write target is `explicit or routing_policy_choice`: an explicit
-    -- (present, non-empty) handle is used directly; the routing-policy fallback
-    -- is reached only when no explicit handle is given. An explicit handle (db)
-    -- is always present here, so the resolution short-circuits to it.
-    let src : List Char := if db.length > 0 then db else routed
-    -- Copy the resolved handle into a fresh result carrier (the write commits to
-    -- the store this handle names).
-    let mut result : List Char := []
-    let mut i := src.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ src.length
-      invariant result = src.drop i
-      done_with i = 0
-      decreasing i
-    do
-      let c := src[i - 1]!
-      result := c :: result
-      i := i - 1
-    return result
+    return routed
     -- impl-end
 
 /- The backward-copy step: dropping one fewer element exposes the element at
@@ -81,11 +63,4 @@
   rw [h, hsucc]
 
 prove_correct resolveTarget by
-  loom_solve
-  · -- loop-body step: the resolution `if` reduces to the explicit handle `db`,
-    -- then the copy peels one code point off the front.
-    simp only [require_2, if_true] at *
-    rw [drop_copy_step db i (by omega) (by omega), invariant_2]
-  · -- exit: `result = db.drop 0 = db`, so `aliasEq result db` holds.
-    simp only [require_2, if_true, aliasEq] at *
-    simp_all
+  loom_solve <;> simp_all [aliasEq]
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_return_db.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The fallback routing policy's chosen target is taken
--  as a free input alias `routed`: the operation under spec does NOT determine
--  how that policy decides, and an explicit named target supersedes it whenever
--  one is given. Its only relied-on property — the policy may name a store
--  different from the explicit one — is validated against the real routing
--  machinery by axiom_check.py (G-AX), an A-reference, not a consumed contract.)
-- axioms-end

-- pure-start
/- Two store handles denote the same data store iff their code-point sequences
   are equal. A store handle is carried as its `List Char` of code points; this
   is the alias equality the resolution must respect. -/
def aliasEq (a b : List Char) : Prop := a = b
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- A persistence step is handed two things: an explicitly named target data
   store (a handle that is always present here) and the handle a separate,
   independent write-routing policy would otherwise pick. The write must land in
   the EXPLICITLY NAMED store, so the resolved target equals the named handle no
   matter which store the routing policy would have chosen. The routing policy
   is only a fallback, reached when no explicit store is named at all.

   `db` is the explicitly named target handle and is always present (non-empty);
   `routed` is the handle the routing policy would otherwise pick — an arbitrary
   present handle, unconstrained to equal `db`. Both are read-only (neither is
   `mut`; the resolution mutates nothing — directive 5). The result is a freshly
   built handle whose code points equal the explicitly named store's, so a
   resolution cannot satisfy the postcondition by echoing `routed`. -/
method resolveTarget (db : List Char) (routed : List Char) return (out : List Char)
  require db.length > 0
  require routed.length > 0
  ensures aliasEq out db
  do
    -- impl-start
    return db
    -- impl-end

/- The backward-copy step: dropping one fewer element exposes the element at
   `i-1` on the front, so the suffix peels one code point. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma drop_copy_step (src : List Char) (i : Nat)
    (hi : 0 < i) (hle : i ≤ src.length) :
    src.drop (i - 1) = src[i - 1]! :: src.drop i := by
  have hlt : i - 1 < src.length := by omega
  have h := List.drop_eq_getElem_cons hlt
  rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
  have hsucc : i - 1 + 1 = i := by omega
  rw [h, hsucc]

prove_correct resolveTarget by
  loom_solve <;> simp_all [aliasEq]
```

Prepatch bug re-encoded as an attack: `True`.

 All files same_spec=True (verified via swebench_unified.markers.same_spec, velvet). Verifier: `bash scripts/lean_verify.sh <file>` run concurrently ≤4/batch.

SPEC SHAPE: method resolveTarget (db routed : List Char) return (out) with require db.length>0, require routed.length>0, ensures aliasEq out db; aliasEq a b := a=b (so postcondition == out=db). set_option loom.semantics.termination "partial". Spec view collapses impl + prove_correct body (both editable); lemma drop_copy_step and everything else kept byte-identical.

BASELINE + POSITIVES: baseline.lean (gold) EXIT=0 (verifies). pos_return_db.lean (`return db`, correct, structurally different) EXIT=0. posvar_1.lean (reads routed as unused, `src:=db`+copy loop) EXIT=0. Non-vacuity confirmed.

8 TERMINATING WRONG IMPLS — all same_spec, ALL FAIL (exit 1) exactly at `case «ensures_1: aliasEq out db»` (genuine postcondition violations, honest best-effort proofs, not tactic plumbing):
  atk_1 prepatch bug src:=routed (loop) → residual `result_1=db` under `routed=result_1` (unprovable). PREPATCH REPRODUCED.
  atk_2 src:=if routed.length>0 then routed else db (==routed) → residual result_1=db under routed=result_1.
  atk_3 boundary: src:=db++routed → residual result_1=db under db++routed=result_1.
  atk_4 partial/empty: return [] → residual db=[] (db nonempty).
  atk_5 boundary: return db.reverse → residual db.reverse=db.
  atk_6 boundary: return db.tail → residual db.tail=db.
  atk_7 control-flow-effect: src:=db.take(db.length-1) (drop last char)+copy loop → residual take(...)db=db.
  atk_8 ungrounded-oracle echo: return routed → residual routed=db (routed free).
Each output archived at atk_N.out.

VERIFYING WRONG IMPL (documented, NOT submitted as a break): atk_div.lean — `let mut i:=1; while i>0 invariant i≥1 done_with i=0 do i:=i+1; return routed` — VERIFIES (exit 0; only lint warnings, loom_solve closes it). It is behaviorally wrong (diverges, never yields db) yet passes VACUOUSLY under `termination "partial"`. This is a UNIVERSAL partial-correctness artifact: the velvet framework explicitly sanctions `set_option loom.semantics.termination "partial"` "when the impl is not structurally terminating" (prompts/velvet/quickref.md) and the GOLD Solution.lean itself uses it (line 4), so a divergent impl vacuously verifies in EVERY partial-correctness velvet bundle, gold included — it is not a §4 refinement-fidelity defect specific to this spec.

Critically it has NO faithful refined patch: its `return routed` is unreachable dead code corresponding to NO leg (A1–A4) of refinement.md, so there is nothing to materialize; any patch I attached would refine nothing (a fabricated false-positive). Hence it is deliberately excluded from `attacks`/`patches` (including it would only produce a candidate-without-patch INCONCLUSIVE, misrepresenting the finding). Reported here for full transparency.

SOUND-LEG PROOF (executed resolve): faithful_gold.diff (the gold one-token change content_type.save(update_fields={'model'}) → content_type.save(using=db, update_fields={'model'})) RESOLVED=True, completed=True, note='resolved' via harness.run_resolve('django__django-11066', ...). Command: SBU_PYTHON -c run_resolve(...) under `docker`. This confirms the value-producing verifying impls (return db / gold) refine to a RESOLVING patch — verify⇒correct on the terminating class.
  Supplementary (not relied on): faithful_routed.diff (prepatch/no-fix, keeps save without using=db) → run_resolve returned completed=False note='no report at ... — harness error' after retries (harness/image flake, NOT a resolve verdict); empty-patch likewise no-report. Prepatch non-resolution is instead established by the shipped Solution_prepatch.lean G-DIFF (fails at aliasEq out db) plus G-AX.

REFINEMENT.MD AUDIT (A-leg focus): every leg R / A-reference / I, NO kind-3. Verified against REAL Django at base_commit inside the instance image (swebench/sweb.eval.x86_64.django_1776_django-11066:latest, HEAD 2a6700a2efef...): A1 (R): db ↔ `db = schema_editor.connection.alias` — CONFIRMED __init__.py:15 (always non-empty alias). str↔List Char code points. A2 (A-reference, NOT consumed axiom): routed ↔ return of router.db_for_write(...) — free input. Callee ConnectionRouter.db_for_write CONFIRMED real (django/db/utils.py:267 via _router_func). UNCHANGED by the fix; bypassed → modeling as consumed axiom would be dead, correctly an A-reference free input. A3 (I under R): src:=if db.length>0 then db else routed ↔ Python `using = using or router.db_for_write(...)` — CONFIRMED base.py:761.

Gold sets using=db (present/truthy) → short-circuits to db, matching the db-branch. A4 (R): copy src→result, ensures aliasEq out db ↔ write commits to resolved alias (=db). Caller line CONFIRMED __init__.py:27 (the exact gold-patched line). G-AX executed: axiom_check.py run IN-CONTAINER against real Django → rc=0 ("G-AX OK ... over 5 boundary + 5000 fuzz alias pairs"), validating both A-reference properties (router independent of db; resolution short-circuits to explicit using). A-legs' correspondence to real callees HOLDS.

VERDICT: SOUND. 8 distinct same-spec terminating wrong impls all fail to verify at the discriminating postcondition; positive control verifies; prepatch reproduced; the exact functional postcondition out=db admits no terminating verifying-but-wrong impl; the gold faithful patch RESOLVES (executed); refinement legs all R/A-reference/I with real-callee correspondence machine-checked (G-AX rc=0). The single verifying wrong impl is a sanctioned-semantics divergence artifact with no faithful patch, not a spec break.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `pos_return_db.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. The postcondition `ensures aliasEq out db` unfolds to `out = db` (aliasEq a b := a = b) — a fully FUNCTIONAL postcondition that pins the output to exactly the explicit alias `db`, with `routed` a free/unconstrained input. Therefore any TERMINATING impl that verifies must produce exactly `db`, i.e. is behaviorally the gold. No terminating verifying-but-wrong impl exists; all 8 value-computing attacks fail at `case «ensures_1: aliasEq out db»`. The only verifying wrong impl is a NON-TERMINATING one (atk_div), which is a universal partial-correctness artifact (see notes), not a spec weakness, and has no faithful refined patch.
```

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

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_return_db.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The fallback routing policy's chosen target is taken
--  as a free input alias `routed`: the operation under spec does NOT determine
--  how that policy decides, and an explicit named target supersedes it whenever
--  one is given. Its only relied-on property — the policy may name a store
--  different from the explicit one — is validated against the real routing
--  machinery by axiom_check.py (G-AX), an A-reference, not a consumed contract.)
-- axioms-end

-- pure-start
/- Two store handles denote the same data store iff their code-point sequences
   are equal. A store handle is carried as its `List Char` of code points; this
   is the alias equality the resolution must respect. -/
def aliasEq (a b : List Char) : Prop := a = b
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- A persistence step is handed two things: an explicitly named target data
   store (a handle that is always present here) and the handle a separate,
   independent write-routing policy would otherwise pick. The write must land in
   the EXPLICITLY NAMED store, so the resolved target equals the named handle no
   matter which store the routing policy would have chosen. The routing policy
   is only a fallback, reached when no explicit store is named at all.

   `db` is the explicitly named target handle and is always present (non-empty);
   `routed` is the handle the routing policy would otherwise pick — an arbitrary
   present handle, unconstrained to equal `db`. Both are read-only (neither is
   `mut`; the resolution mutates nothing — directive 5). The result is a freshly
   built handle whose code points equal the explicitly named store's, so a
   resolution cannot satisfy the postcondition by echoing `routed`. -/
method resolveTarget (db : List Char) (routed : List Char) return (out : List Char)
  require db.length > 0
  require routed.length > 0
  ensures aliasEq out db
  do
    -- impl-start
    return db
    -- impl-end

/- The backward-copy step: dropping one fewer element exposes the element at
   `i-1` on the front, so the suffix peels one code point. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma drop_copy_step (src : List Char) (i : Nat)
    (hi : 0 < i) (hle : i ≤ src.length) :
    src.drop (i - 1) = src[i - 1]! :: src.drop i := by
  have hlt : i - 1 < src.length := by omega
  have h := List.drop_eq_getElem_cons hlt
  rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
  have hsucc : i - 1 + 1 = i := by omega
  rw [h, hsucc]

prove_correct resolveTarget by
  loom_solve <;> simp_all [aliasEq]
```

Prepatch bug re-encoded as an attack: `True`.

 All files same_spec=True (verified via swebench_unified.markers.same_spec, velvet). Verifier: `bash scripts/lean_verify.sh <file>` run concurrently ≤4/batch.

SPEC SHAPE: method resolveTarget (db routed : List Char) return (out) with require db.length>0, require routed.length>0, ensures aliasEq out db; aliasEq a b := a=b (so postcondition == out=db). set_option loom.semantics.termination "partial". Spec view collapses impl + prove_correct body (both editable); lemma drop_copy_step and everything else kept byte-identical.

BASELINE + POSITIVES: baseline.lean (gold) EXIT=0 (verifies). pos_return_db.lean (`return db`, correct, structurally different) EXIT=0. posvar_1.lean (reads routed as unused, `src:=db`+copy loop) EXIT=0. Non-vacuity confirmed.

8 TERMINATING WRONG IMPLS — all same_spec, ALL FAIL (exit 1) exactly at `case «ensures_1: aliasEq out db»` (genuine postcondition violations, honest best-effort proofs, not tactic plumbing):
  atk_1 prepatch bug src:=routed (loop) → residual `result_1=db` under `routed=result_1` (unprovable). PREPATCH REPRODUCED.
  atk_2 src:=if routed.length>0 then routed else db (==routed) → residual result_1=db under routed=result_1.
  atk_3 boundary: src:=db++routed → residual result_1=db under db++routed=result_1.
  atk_4 partial/empty: return [] → residual db=[] (db nonempty).
  atk_5 boundary: return db.reverse → residual db.reverse=db.
  atk_6 boundary: return db.tail → residual db.tail=db.
  atk_7 control-flow-effect: src:=db.take(db.length-1) (drop last char)+copy loop → residual take(...)db=db.
  atk_8 ungrounded-oracle echo: return routed → residual routed=db (routed free).
Each output archived at atk_N.out.

VERIFYING WRONG IMPL (documented, NOT submitted as a break): atk_div.lean — `let mut i:=1; while i>0 invariant i≥1 done_with i=0 do i:=i+1; return routed` — VERIFIES (exit 0; only lint warnings, loom_solve closes it). It is behaviorally wrong (diverges, never yields db) yet passes VACUOUSLY under `termination "partial"`. This is a UNIVERSAL partial-correctness artifact: the velvet framework explicitly sanctions `set_option loom.semantics.termination "partial"` "when the impl is not structurally terminating" (prompts/velvet/quickref.md) and the GOLD Solution.lean itself uses it (line 4), so a divergent impl vacuously verifies in EVERY partial-correctness velvet bundle, gold included — it is not a §4 refinement-fidelity defect specific to this spec.

Critically it has NO faithful refined patch: its `return routed` is unreachable dead code corresponding to NO leg (A1–A4) of refinement.md, so there is nothing to materialize; any patch I attached would refine nothing (a fabricated false-positive). Hence it is deliberately excluded from `attacks`/`patches` (including it would only produce a candidate-without-patch INCONCLUSIVE, misrepresenting the finding). Reported here for full transparency.

SOUND-LEG PROOF (executed resolve): faithful_gold.diff (the gold one-token change content_type.save(update_fields={'model'}) → content_type.save(using=db, update_fields={'model'})) RESOLVED=True, completed=True, note='resolved' via harness.run_resolve('django__django-11066', ...). Command: SBU_PYTHON -c run_resolve(...) under `docker`. This confirms the value-producing verifying impls (return db / gold) refine to a RESOLVING patch — verify⇒correct on the terminating class.
  Supplementary (not relied on): faithful_routed.diff (prepatch/no-fix, keeps save without using=db) → run_resolve returned completed=False note='no report at ... — harness error' after retries (harness/image flake, NOT a resolve verdict); empty-patch likewise no-report. Prepatch non-resolution is instead established by the shipped Solution_prepatch.lean G-DIFF (fails at aliasEq out db) plus G-AX.

REFINEMENT.MD AUDIT (A-leg focus): every leg R / A-reference / I, NO kind-3. Verified against REAL Django at base_commit inside the instance image (swebench/sweb.eval.x86_64.django_1776_django-11066:latest, HEAD 2a6700a2efef...): A1 (R): db ↔ `db = schema_editor.connection.alias` — CONFIRMED __init__.py:15 (always non-empty alias). str↔List Char code points. A2 (A-reference, NOT consumed axiom): routed ↔ return of router.db_for_write(...) — free input. Callee ConnectionRouter.db_for_write CONFIRMED real (django/db/utils.py:267 via _router_func). UNCHANGED by the fix; bypassed → modeling as consumed axiom would be dead, correctly an A-reference free input. A3 (I under R): src:=if db.length>0 then db else routed ↔ Python `using = using or router.db_for_write(...)` — CONFIRMED base.py:761.

Gold sets using=db (present/truthy) → short-circuits to db, matching the db-branch. A4 (R): copy src→result, ensures aliasEq out db ↔ write commits to resolved alias (=db). Caller line CONFIRMED __init__.py:27 (the exact gold-patched line). G-AX executed: axiom_check.py run IN-CONTAINER against real Django → rc=0 ("G-AX OK ... over 5 boundary + 5000 fuzz alias pairs"), validating both A-reference properties (router independent of db; resolution short-circuits to explicit using). A-legs' correspondence to real callees HOLDS.

VERDICT: SOUND. 8 distinct same-spec terminating wrong impls all fail to verify at the discriminating postcondition; positive control verifies; prepatch reproduced; the exact functional postcondition out=db admits no terminating verifying-but-wrong impl; the gold faithful patch RESOLVES (executed); refinement legs all R/A-reference/I with real-callee correspondence machine-checked (G-AX rc=0). The single verifying wrong impl is a sanctioned-semantics divergence artifact with no faithful patch, not a spec break.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** same_spec(Solution.lean, Solution_prepatch.lean) = True under the velvet backend (spec regions byte-identical; only impl/proof regions differ). Solution.lean elaborates cleanly under lean_verify.sh (exit 0).

Faithfulness assessment vs. real repo at base_commit 4b45b6c8: The gold patch adds `using=db` to `content_type.save(update_fields={'model'})` in RenameContentType._rename. The real write-target resolution is `using = using or router.db_for_write(...)` (django/db/models/base.py:761). The modeled function resolveTarget(db, routed) with require db.length>0, require routed.length>0, ensures aliasEq out db captures precisely this: db is a connection alias string (schema_editor.connection.alias), always a non-empty/truthy value, so post-patch the Python `or` short-circuits to `db` for EVERY router choice `routed`. This matches ensures out=db for all valid inputs.

Checked for spec-too-strong / drift:
- No input violates faithfulness. For any nonempty db and any nonempty routed, real post-patch resolution = db (short-circuit), exactly the postcondition. The impl models `if db.length>0 then db else routed`, and since the precondition guarantees db.length>0, the branch is always db — consistent with the real always-present alias.
- The abstraction (alias str <-> List Char; str-eq <-> list-eq; present-alias truthiness <-> db.length>0) is a sound bijection over the tested domain.
- routed.length>0 is faithful: router.db_for_write never returns an empty alias (empty router falls through to DEFAULT_DB_ALIAS='default'); confirmed by axiom_check.py.
- The prepatch (src=routed) correctly FAILS the postcondition (routed is an unconstrained free input, need not equal db) — the intended G-DIFF differential, matching the real pre-patch `using=None` -> router-chosen alias. This confirms the spec discriminates the actual behavioral change rather than being vacuously satisfiable.
- No consumed axiom; the only callee (router.db_for_write) is unchanged and bypassed, correctly modeled as free input `routed` and validated by axiom_check.py (G-AX) against real Django routing machinery.

No diverging input found: the modeled function agrees with the real post-patch callee on every input in the specified domain. Spec is neither too strong nor drifting.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-AX `pass` (the axiom battery). The account names `Solution.lean`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Leakage/gold-reconstruction check for velvet django__django-11066. Gold edit: add `using=db` to `content_type.save(update_fields={'model'})` in django/contrib/contenttypes/management/__init__.py (RenameContentType._rename). 

Method: generated the actual spec view via markers.spec_view (velvet flavor) and ran leakage.screen against the frozen row's gold patch + problem_statement. Also verified same_spec(Solution, Solution_prepatch)=True, so the frozen spec is shared and no impl/proof content leaks through the projection.

Mechanical screen: PASSES with zero hard failures — no diff markers, no verbatim gold-patch line (>=8 chars normalized) reproduced, no patched file path/module path in the view, and no spec-view identifier or comment naming the sole distinctive patched symbol ('rename').

Semantic judgment (leakage beyond problem_statement): the public problem_statement already discloses the ENTIRE fix verbatim — it states that `content_type.save(update_fields={'model'})` 'should be' `content_type.save(using=db, update_fields={'model'})`, and explains that without the explicit alias the write is routed to the wrong (default) database. The spec view is a faithful ABSTRACTION of this: it speaks only of opaque 'store handles' (List Char), an explicitly-named target `db` vs a routing-policy choice `routed`, and the requirement that the resolved target equal the explicitly named handle (aliasEq out db) regardless of routing. It names no Python symbols (save/using/content_type), no file path, no diff, no bug/fix narration. Every fact it conveys (explicit alias supersedes router fallback; write must land in the named store) is already fully public in the problem_statement. No spec-view line reveals the gold edit beyond what the task text discloses.

Conclusion: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).