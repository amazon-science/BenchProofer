# P2 adversarial audit — django__django-14011

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_prepatch_install.lean`, `atk_prepatch_release.lean`, `atk_donewith_install.lean`, `atk_donewith_release.lean`, `atk_nonterm_install.lean`, `atk_nonterm_release.lean`, `atk_offbyone_install.lean`, `atk_partialdomain_release.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_oracle_echo.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_prepatch_install.lean` → rejected (same spec, does not verify — good)

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
 -- No consumed axioms. Both modeled operations are unchanged library callees
@@ -71,17 +71,11 @@
   ensures ∀ p, p ∈ preferred → p ∈ out
   do
     -- impl-start
-    let mut result : List (String × Int) := registry
-    let mut i := preferred.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ preferred.length
-      invariant result = preferred.drop i ++ registry
-      done_with i = 0
-      decreasing i
-    do
-      let kv := preferred[i - 1]!
-      result := kv :: result
-      i := i - 1
+    -- Pre-image skeleton: the worker does NOT install the preferred bindings;
+    -- it operates against the registry as-is. The frozen spec requires the
+    -- preferred bindings to take precedence (out = preferred ++ registry), so
+    -- prove_correct MUST fail whenever `preferred` is non-empty.
+    let result : List (String × Int) := registry
     return result
     -- impl-end
 
@@ -102,8 +96,6 @@
 
 prove_correct installPreferred by
   loom_solve
-  rw [overlay_drop_step preferred registry i (by omega) (by omega)]
-  simp_all
 
 -- pre-conditions-start
 -- pre-conditions-end
@@ -128,7 +120,6 @@
       invariant 0 ≤ i ∧ i ≤ handles.length
       invariant result = releasedSeq (handles.drop i)
       done_with i = 0
-      decreasing i
     do
       result := false :: result
       i := i - 1
```

Attack 2 — `atk_prepatch_release.lean` → rejected (same spec, does not verify — good)

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
 -- No consumed axioms. Both modeled operations are unchanged library callees
@@ -77,7 +77,6 @@
       invariant 0 ≤ i ∧ i ≤ preferred.length
       invariant result = preferred.drop i ++ registry
       done_with i = 0
-      decreasing i
     do
       let kv := preferred[i - 1]!
       result := kv :: result
@@ -122,16 +121,11 @@
   ensures ∀ b ∈ out, b = false
   do
     -- impl-start
-    let mut result : List Bool := []
-    let mut i := handles.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ handles.length
-      invariant result = releasedSeq (handles.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      result := false :: result
-      i := i - 1
+    -- Pre-image skeleton: the worker does NOT release its handles before being
+    -- recycled; it leaves them in whatever state they were in. The frozen spec
+    -- requires every handle to end inactive (∀ b ∈ out, b = false), so
+    -- prove_correct MUST fail whenever any input handle was active.
+    let result : List Bool := handles
     return result
     -- impl-end
 
@@ -151,5 +145,3 @@
 
 prove_correct releaseAll by
   loom_solve
-  rw [released_drop_step handles i (by omega) (by omega)]
-  simp_all
```

Attack 3 — `atk_donewith_install.lean` → rejected (same spec, does not verify — good)

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
 -- No consumed axioms. Both modeled operations are unchanged library callees
@@ -75,12 +75,8 @@
     let mut i := preferred.length
     while i > 0
       invariant 0 ≤ i ∧ i ≤ preferred.length
-      invariant result = preferred.drop i ++ registry
-      done_with i = 0
-      decreasing i
+      done_with result = preferred ++ registry
     do
-      let kv := preferred[i - 1]!
-      result := kv :: result
       i := i - 1
     return result
     -- impl-end
@@ -102,8 +98,7 @@
 
 prove_correct installPreferred by
   loom_solve
-  rw [overlay_drop_step preferred registry i (by omega) (by omega)]
-  simp_all
+  all_goals simp_all
 
 -- pre-conditions-start
 -- pre-conditions-end
@@ -128,7 +123,6 @@
       invariant 0 ≤ i ∧ i ≤ handles.length
       invariant result = releasedSeq (handles.drop i)
       done_with i = 0
-      decreasing i
     do
       result := false :: result
       i := i - 1
```

Attack 4 — `atk_donewith_release.lean` → rejected (same spec, does not verify — good)

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
 -- No consumed axioms. Both modeled operations are unchanged library callees
@@ -77,7 +77,6 @@
       invariant 0 ≤ i ∧ i ≤ preferred.length
       invariant result = preferred.drop i ++ registry
       done_with i = 0
-      decreasing i
     do
       let kv := preferred[i - 1]!
       result := kv :: result
@@ -126,11 +125,8 @@
     let mut i := handles.length
     while i > 0
       invariant 0 ≤ i ∧ i ≤ handles.length
-      invariant result = releasedSeq (handles.drop i)
-      done_with i = 0
-      decreasing i
+      done_with result = releasedSeq handles
     do
-      result := false :: result
       i := i - 1
     return result
     -- impl-end
@@ -151,5 +147,4 @@
 
 prove_correct releaseAll by
   loom_solve
-  rw [released_drop_step handles i (by omega) (by omega)]
-  simp_all
+  all_goals simp_all
```

Attack 5 — `atk_nonterm_install.lean` → rejected (same spec, does not verify — good)

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
 -- No consumed axioms. Both modeled operations are unchanged library callees
@@ -77,11 +77,8 @@
       invariant 0 ≤ i ∧ i ≤ preferred.length
       invariant result = preferred.drop i ++ registry
       done_with i = 0
-      decreasing i
     do
-      let kv := preferred[i - 1]!
-      result := kv :: result
-      i := i - 1
+      result := result
     return result
     -- impl-end
 
@@ -128,7 +125,6 @@
       invariant 0 ≤ i ∧ i ≤ handles.length
       invariant result = releasedSeq (handles.drop i)
       done_with i = 0
-      decreasing i
     do
       result := false :: result
       i := i - 1
```

Attack 6 — `atk_nonterm_release.lean` → rejected (same spec, does not verify — good)

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
 -- No consumed axioms. Both modeled operations are unchanged library callees
@@ -77,7 +77,6 @@
       invariant 0 ≤ i ∧ i ≤ preferred.length
       invariant result = preferred.drop i ++ registry
       done_with i = 0
-      decreasing i
     do
       let kv := preferred[i - 1]!
       result := kv :: result
@@ -128,10 +127,8 @@
       invariant 0 ≤ i ∧ i ≤ handles.length
       invariant result = releasedSeq (handles.drop i)
       done_with i = 0
-      decreasing i
     do
-      result := false :: result
-      i := i - 1
+      result := true :: result
     return result
     -- impl-end
 
```

Attack 7 — `atk_offbyone_install.lean` → rejected (same spec, does not verify — good)

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
 -- No consumed axioms. Both modeled operations are unchanged library callees
@@ -73,11 +73,9 @@
     -- impl-start
     let mut result : List (String × Int) := registry
     let mut i := preferred.length
-    while i > 0
+    while i > 1
       invariant 0 ≤ i ∧ i ≤ preferred.length
       invariant result = preferred.drop i ++ registry
-      done_with i = 0
-      decreasing i
     do
       let kv := preferred[i - 1]!
       result := kv :: result
@@ -128,7 +126,6 @@
       invariant 0 ≤ i ∧ i ≤ handles.length
       invariant result = releasedSeq (handles.drop i)
       done_with i = 0
-      decreasing i
     do
       result := false :: result
       i := i - 1
```

Attack 8 — `atk_partialdomain_release.lean` → rejected (same spec, does not verify — good)

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
 -- No consumed axioms. Both modeled operations are unchanged library callees
@@ -77,7 +77,6 @@
       invariant 0 ≤ i ∧ i ≤ preferred.length
       invariant result = preferred.drop i ++ registry
       done_with i = 0
-      decreasing i
     do
       let kv := preferred[i - 1]!
       result := kv :: result
@@ -122,16 +121,7 @@
   ensures ∀ b ∈ out, b = false
   do
     -- impl-start
-    let mut result : List Bool := []
-    let mut i := handles.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ handles.length
-      invariant result = releasedSeq (handles.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      result := false :: result
-      i := i - 1
+    let result : List Bool := if handles.isEmpty then [] else handles
     return result
     -- impl-end
 
@@ -151,5 +141,4 @@
 
 prove_correct releaseAll by
   loom_solve
-  rw [released_drop_step handles i (by omega) (by omega)]
-  simp_all
+  all_goals simp_all
```

Attack 9 — `atk_oracle_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 -- No consumed axioms. Both modeled operations are unchanged library callees
@@ -77,7 +77,6 @@
       invariant 0 ≤ i ∧ i ≤ preferred.length
       invariant result = preferred.drop i ++ registry
       done_with i = 0
-      decreasing i
     do
       let kv := preferred[i - 1]!
       result := kv :: result
@@ -122,16 +121,7 @@
   ensures ∀ b ∈ out, b = false
   do
     -- impl-start
-    let mut result : List Bool := []
-    let mut i := handles.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ handles.length
-      invariant result = releasedSeq (handles.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      result := false :: result
-      i := i - 1
+    let result : List Bool := releasedSeq handles
     return result
     -- impl-end
 
@@ -151,5 +141,4 @@
 
 prove_correct releaseAll by
   loom_solve
-  rw [released_drop_step handles i (by omega) (by omega)]
-  simp_all
+  all_goals simp_all
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- No consumed axioms. Both modeled operations are unchanged library callees
-- modeled DEEPLY as concrete data transforms (A-reference), validated
-- == the real callee by axiom_check.py (G-AX); see mapping.md §3.
-- axioms-end

-- pure-start
/- The "released" image of a registry of resource-handles: every handle in the
   sequence is left in the released (inactive) state, regardless of its prior
   state. Front-recursive so a single unfold is available per loop step (the
   backward-fold pattern). A handle is modeled by a `Bool` recording whether it
   is currently active. -/
def releasedSeq : List Bool → List Bool
  | []      => []
  | _ :: cs => false :: releasedSeq cs

@[grind] lemma releasedSeq_nil : releasedSeq [] = [] := rfl
@[grind] lemma releasedSeq_cons (b : Bool) (cs : List Bool) :
    releasedSeq (b :: cs) = false :: releasedSeq cs := rfl

/- After releasing, every entry is inactive. -/
@[grind] lemma releasedSeq_all_false (cs : List Bool) :
    ∀ b ∈ releasedSeq cs, b = false := by
  induction cs with
  | nil => simp [releasedSeq]
  | cons c cs ih =>
      intro b hb
      simp [releasedSeq_cons] at hb
      rcases hb with h | h
      · exact h
      · exact ih b h

@[grind] lemma releasedSeq_length (cs : List Bool) :
    (releasedSeq cs).length = cs.length := by
  induction cs with
  | nil => rfl
  | cons c cs ih => simp [releasedSeq_cons, ih]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Install a set of preferred bindings over an existing keyed registry.

   `registry` is a keyed collection (alias ↦ handle id), modeled as an
   association list with first-match lookup. `preferred` is the set of bindings
   that must take precedence: after installation, every alias present in
   `preferred` resolves to the preferred handle, and aliases absent from
   `preferred` keep their prior binding. Modeled as prepending the preferred
   bindings, so first-match lookup yields preferred precedence (mapping.md §2).

   This is the behavior an isolated worker needs: it must operate against the
   handles handed to it, not against freshly-created handles for the same
   aliases. -/
method installPreferred
    (preferred : List (String × Int)) (registry : List (String × Int))
    return (out : List (String × Int))
  ensures out = preferred ++ registry
  ensures out.length = preferred.length + registry.length
  ensures ∀ p, p ∈ preferred → p ∈ out
  do
    -- impl-start
    let mut result : List (String × Int) := registry
    let mut i := preferred.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ preferred.length
      invariant result = preferred.drop i ++ registry
      done_with i = 0
    do
      let kv := preferred[i - 1]!
      result := kv :: result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the binding at
   `i-1` on the front, and `++` distributes through the resulting cons. The one
   goal `loom_solve` leaves for the loop body. -/
lemma overlay_drop_step (preferred registry : List (String × Int)) (i : Nat)
    (hi : 0 < i) (hle : i ≤ preferred.length) :
    preferred.drop (i - 1) ++ registry
      = preferred[i - 1]! :: (preferred.drop i ++ registry) := by
  have hlt : i - 1 < preferred.length := by omega
  have hcons : preferred.drop (i - 1) = preferred[i - 1]! :: preferred.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, List.cons_append]

prove_correct installPreferred by
  loom_solve
  rw [overlay_drop_step preferred registry i (by omega) (by omega)]
  simp_all

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Release every resource-handle held by a worker before it is recycled. The
   handles are modeled by their active/inactive flags; after this operation no
   handle remains active, so a later teardown observes no still-held resources.
   This is the per-handle release the worker must perform at the end of each
   unit of work (mapping.md §2). -/
method releaseAll (handles : List Bool) return (out : List Bool)
  ensures out = releasedSeq handles
  ensures out.length = handles.length
  ensures ∀ b ∈ out, b = false
  do
    -- impl-start
    let mut result : List Bool := []
    let mut i := handles.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ handles.length
      invariant result = releasedSeq (handles.drop i)
      done_with i = 0
    do
      result := false :: result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step for release: dropping one fewer element exposes one
   more handle on the front, and `releasedSeq` peels one inactive entry (the
   prior state of that handle is irrelevant). -/
lemma released_drop_step (handles : List Bool) (i : Nat)
    (hi : 0 < i) (hle : i ≤ handles.length) :
    releasedSeq (handles.drop (i - 1)) = false :: releasedSeq (handles.drop i) := by
  have hlt : i - 1 < handles.length := by omega
  have hcons : handles.drop (i - 1) = handles[i - 1]! :: handles.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, releasedSeq_cons]

prove_correct releaseAll by
  loom_solve
  rw [released_drop_step handles i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. Frozen spec pins BOTH modeled outputs by exact functional equalities under partial-correctness semantics: installPreferred `ensures out = preferred ++ registry` (+ length + membership) and releaseAll `ensures out = releasedSeq handles` (+ `∀ b ∈ out, b = false` + length). This is a maximally tight spec shape, so no terminating wrong data-transform can verify, and I additionally probed the partial-correctness vacuity surface.

MECHANICS: velvet spec_view collapses impl regions AND elides prove_correct bodies (markers.py _lean_spec_view + _elide_prove_correct), so editing the do-block, loop invariants/done_with, and prove_correct tactics keeps same_spec=True; the helper lemmas overlay_drop_step/released_drop_step are in the spec view and were left byte-identical. All 9 attacks + positive control confirmed same_spec=True.

### ATTACKS (cmd: `bash scripts/lean_verify.sh <path>`; exit 0=verifies, 1=error, 3=sorry):
1. atk_prepatch_install (prepatch bug; `return registry`) -> EXIT 1, unsolved ensures_1/2/3 (out=preferred++registry, length, membership). REJECTED.
2. atk_prepatch_release (prepatch bug; `return handles`) -> EXIT 1, unsolved ensures_1 (∀b∈out,b=false) + ensures_3 (out=releasedSeq handles). REJECTED.
3. atk_donewith_install (control-flow-effect: body only decrements i, lying `done_with result = preferred ++ registry`) -> EXIT 1, unsolved goals. Velvet CHECKS done_with entailment; vacuity door closed.
4. atk_donewith_release (same lying-done_with attack on releaseAll) -> EXIT 1, unsolved goals. Closed.
5. atk_nonterm_install (non-terminating: never decrement i) -> EXIT 1. REJECTED.
6. atk_nonterm_release (non-terminating: body cons true, no decrement) -> EXIT 1, unknownIdentifier + unsolved invariant_2. REJECTED.
7. atk_offbyone_install (boundary: guard i>1 skips last preferred elem) -> EXIT 1, unsolved ensures_1/2/3. REJECTED.
8. atk_partialdomain_release (partial-domain: `if handles.isEmpty then [] else handles`) -> EXIT 1, unsolved ensures_1 + ensures_3. REJECTED.
9. atk_oracle_echo (ungrounded-oracle echo: releaseAll `return releasedSeq handles`, installPreferred left correct) -> EXIT 0, VERIFIES.

Positive control pos_control (= baseline Solution.lean) -> EXIT 0, verifies (spec non-vacuous, satisfiable).

PER-PROTOCOL RESOLVE OF THE ONE VERIFYING CANDIDATE: atk_oracle_echo's faithful refined patch is byte-identical to gold (diff = empty). Reason: `releasedSeq` is a fully-spelled-out pure function (definitionally `map (fun _=>false)` = universal release = connections.close_all()), so echoing it IS performing the real fix, and installPreferred stays the correct override-precedence merge. Executed run_resolve('django__django-14011', <faithful patch>, timeout=1800): RESOLVED=True, COMPLETED=True, NOTE='resolved' (see resolve_oracle_echo.log). So the only verify=>resolve leg holds; this is a legitimate resolving echo (consistent with the 2026-08-06 G-PANEL-1 echo policy), NOT a verify⇏correct break.

REFINEMENT.MD AUDIT (protocol step 3): every leg is R / A-reference / I — NO kind-3, NO consumed axioms. The two genuinely-changed data ops (override-precedence install, universal release) are modeled deeply/concretely (spelled-out ++/cons merge; releasedSeq fold). The only A-tags are A-reference deep models of UNCHANGED callees. Verified at base_commit e4430f22c8e3d29ce5d9d0263fba57121938d06d (worktree): __setitem__ = setattr(self._connections,key,value); __getitem__ returns stored attr else lazily creates -> installing override makes that alias resolve to the override object, un-overridden aliases keep their binding == preferred++registry under first-match.

(ii) close_all iterates registry, `continue` on AttributeError (never-instantiated), else connection.close() on each -> every present connection closed regardless of prior state == releasedSeq. CONFIRMED patch.diff touches ONLY basehttp.py + sqlite3/features.py — it does NOT modify django/utils/connection.py or django/db/utils.py, so both A-references are genuinely unchanged callees the patch merely calls. CONFIRMED Site-B target 'LiveServerTestCloseConnectionTest.test_closes_connections' is NOT in FAIL_TO_PASS (17 F2P entries, target absent), so refinement.md §C leaving django_test_skips unmodeled (data-free config datum, not kind-3) is accurate.

CONCLUSION: 9 attacks run (prepatch bug + both prepatch classes + control-flow-effect done_with lies + non-termination + boundary/off-by-one + partial-domain + ungrounded-oracle echo). Only the gold-equivalent echo verifies and its faithful patch RESOLVES. No verifying wrong impl whose faithful patch fails to resolve. Spec is tight; verify=>resolve holds. G-EQ SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_prepatch_install.lean`, `atk_prepatch_release.lean`, `atk_donewith_install.lean`, `atk_donewith_release.lean`, `atk_nonterm_install.lean`, `atk_nonterm_release.lean`, `atk_offbyone_install.lean`, `atk_partialdomain_release.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_oracle_echo.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 9 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_prepatch_install.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_prepatch_release.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_donewith_install.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_donewith_release.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_nonterm_install.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_nonterm_release.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_offbyone_install.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_partialdomain_release.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_oracle_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- No consumed axioms. Both modeled operations are unchanged library callees
-- modeled DEEPLY as concrete data transforms (A-reference), validated
-- == the real callee by axiom_check.py (G-AX); see mapping.md §3.
-- axioms-end

-- pure-start
/- The "released" image of a registry of resource-handles: every handle in the
   sequence is left in the released (inactive) state, regardless of its prior
   state. Front-recursive so a single unfold is available per loop step (the
   backward-fold pattern). A handle is modeled by a `Bool` recording whether it
   is currently active. -/
def releasedSeq : List Bool → List Bool
  | []      => []
  | _ :: cs => false :: releasedSeq cs

@[grind] lemma releasedSeq_nil : releasedSeq [] = [] := rfl
@[grind] lemma releasedSeq_cons (b : Bool) (cs : List Bool) :
    releasedSeq (b :: cs) = false :: releasedSeq cs := rfl

/- After releasing, every entry is inactive. -/
@[grind] lemma releasedSeq_all_false (cs : List Bool) :
    ∀ b ∈ releasedSeq cs, b = false := by
  induction cs with
  | nil => simp [releasedSeq]
  | cons c cs ih =>
      intro b hb
      simp [releasedSeq_cons] at hb
      rcases hb with h | h
      · exact h
      · exact ih b h

@[grind] lemma releasedSeq_length (cs : List Bool) :
    (releasedSeq cs).length = cs.length := by
  induction cs with
  | nil => rfl
  | cons c cs ih => simp [releasedSeq_cons, ih]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Install a set of preferred bindings over an existing keyed registry.

   `registry` is a keyed collection (alias ↦ handle id), modeled as an
   association list with first-match lookup. `preferred` is the set of bindings
   that must take precedence: after installation, every alias present in
   `preferred` resolves to the preferred handle, and aliases absent from
   `preferred` keep their prior binding. Modeled as prepending the preferred
   bindings, so first-match lookup yields preferred precedence (mapping.md §2).

   This is the behavior an isolated worker needs: it must operate against the
   handles handed to it, not against freshly-created handles for the same
   aliases. -/
method installPreferred
    (preferred : List (String × Int)) (registry : List (String × Int))
    return (out : List (String × Int))
  ensures out = preferred ++ registry
  ensures out.length = preferred.length + registry.length
  ensures ∀ p, p ∈ preferred → p ∈ out
  do
    -- impl-start
    let mut result : List (String × Int) := registry
    let mut i := preferred.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ preferred.length
      invariant result = preferred.drop i ++ registry
      done_with i = 0
    do
      let kv := preferred[i - 1]!
      result := kv :: result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the binding at
   `i-1` on the front, and `++` distributes through the resulting cons. The one
   goal `loom_solve` leaves for the loop body. -/
lemma overlay_drop_step (preferred registry : List (String × Int)) (i : Nat)
    (hi : 0 < i) (hle : i ≤ preferred.length) :
    preferred.drop (i - 1) ++ registry
      = preferred[i - 1]! :: (preferred.drop i ++ registry) := by
  have hlt : i - 1 < preferred.length := by omega
  have hcons : preferred.drop (i - 1) = preferred[i - 1]! :: preferred.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, List.cons_append]

prove_correct installPreferred by
  loom_solve
  rw [overlay_drop_step preferred registry i (by omega) (by omega)]
  simp_all

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Release every resource-handle held by a worker before it is recycled. The
   handles are modeled by their active/inactive flags; after this operation no
   handle remains active, so a later teardown observes no still-held resources.
   This is the per-handle release the worker must perform at the end of each
   unit of work (mapping.md §2). -/
method releaseAll (handles : List Bool) return (out : List Bool)
  ensures out = releasedSeq handles
  ensures out.length = handles.length
  ensures ∀ b ∈ out, b = false
  do
    -- impl-start
    let mut result : List Bool := []
    let mut i := handles.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ handles.length
      invariant result = releasedSeq (handles.drop i)
      done_with i = 0
    do
      result := false :: result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step for release: dropping one fewer element exposes one
   more handle on the front, and `releasedSeq` peels one inactive entry (the
   prior state of that handle is irrelevant). -/
lemma released_drop_step (handles : List Bool) (i : Nat)
    (hi : 0 < i) (hle : i ≤ handles.length) :
    releasedSeq (handles.drop (i - 1)) = false :: releasedSeq (handles.drop i) := by
  have hlt : i - 1 < handles.length := by omega
  have hcons : handles.drop (i - 1) = handles[i - 1]! :: handles.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, releasedSeq_cons]

prove_correct releaseAll by
  loom_solve
  rw [released_drop_step handles i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. Frozen spec pins BOTH modeled outputs by exact functional equalities under partial-correctness semantics: installPreferred `ensures out = preferred ++ registry` (+ length + membership) and releaseAll `ensures out = releasedSeq handles` (+ `∀ b ∈ out, b = false` + length). This is a maximally tight spec shape, so no terminating wrong data-transform can verify, and I additionally probed the partial-correctness vacuity surface.

MECHANICS: velvet spec_view collapses impl regions AND elides prove_correct bodies (markers.py _lean_spec_view + _elide_prove_correct), so editing the do-block, loop invariants/done_with, and prove_correct tactics keeps same_spec=True; the helper lemmas overlay_drop_step/released_drop_step are in the spec view and were left byte-identical. All 9 attacks + positive control confirmed same_spec=True.

### ATTACKS (cmd: `bash scripts/lean_verify.sh <path>`; exit 0=verifies, 1=error, 3=sorry):
1. atk_prepatch_install (prepatch bug; `return registry`) -> EXIT 1, unsolved ensures_1/2/3 (out=preferred++registry, length, membership). REJECTED.
2. atk_prepatch_release (prepatch bug; `return handles`) -> EXIT 1, unsolved ensures_1 (∀b∈out,b=false) + ensures_3 (out=releasedSeq handles). REJECTED.
3. atk_donewith_install (control-flow-effect: body only decrements i, lying `done_with result = preferred ++ registry`) -> EXIT 1, unsolved goals. Velvet CHECKS done_with entailment; vacuity door closed.
4. atk_donewith_release (same lying-done_with attack on releaseAll) -> EXIT 1, unsolved goals. Closed.
5. atk_nonterm_install (non-terminating: never decrement i) -> EXIT 1. REJECTED.
6. atk_nonterm_release (non-terminating: body cons true, no decrement) -> EXIT 1, unknownIdentifier + unsolved invariant_2. REJECTED.
7. atk_offbyone_install (boundary: guard i>1 skips last preferred elem) -> EXIT 1, unsolved ensures_1/2/3. REJECTED.
8. atk_partialdomain_release (partial-domain: `if handles.isEmpty then [] else handles`) -> EXIT 1, unsolved ensures_1 + ensures_3. REJECTED.
9. atk_oracle_echo (ungrounded-oracle echo: releaseAll `return releasedSeq handles`, installPreferred left correct) -> EXIT 0, VERIFIES.

Positive control pos_control (= baseline Solution.lean) -> EXIT 0, verifies (spec non-vacuous, satisfiable).

PER-PROTOCOL RESOLVE OF THE ONE VERIFYING CANDIDATE: atk_oracle_echo's faithful refined patch is byte-identical to gold (diff = empty). Reason: `releasedSeq` is a fully-spelled-out pure function (definitionally `map (fun _=>false)` = universal release = connections.close_all()), so echoing it IS performing the real fix, and installPreferred stays the correct override-precedence merge. Executed run_resolve('django__django-14011', <faithful patch>, timeout=1800): RESOLVED=True, COMPLETED=True, NOTE='resolved' (see resolve_oracle_echo.log). So the only verify=>resolve leg holds; this is a legitimate resolving echo (consistent with the 2026-08-06 G-PANEL-1 echo policy), NOT a verify⇏correct break.

REFINEMENT.MD AUDIT (protocol step 3): every leg is R / A-reference / I — NO kind-3, NO consumed axioms. The two genuinely-changed data ops (override-precedence install, universal release) are modeled deeply/concretely (spelled-out ++/cons merge; releasedSeq fold). The only A-tags are A-reference deep models of UNCHANGED callees. Verified at base_commit e4430f22c8e3d29ce5d9d0263fba57121938d06d (worktree): __setitem__ = setattr(self._connections,key,value); __getitem__ returns stored attr else lazily creates -> installing override makes that alias resolve to the override object, un-overridden aliases keep their binding == preferred++registry under first-match.

(ii) close_all iterates registry, `continue` on AttributeError (never-instantiated), else connection.close() on each -> every present connection closed regardless of prior state == releasedSeq. CONFIRMED patch.diff touches ONLY basehttp.py + sqlite3/features.py — it does NOT modify django/utils/connection.py or django/db/utils.py, so both A-references are genuinely unchanged callees the patch merely calls. CONFIRMED Site-B target 'LiveServerTestCloseConnectionTest.test_closes_connections' is NOT in FAIL_TO_PASS (17 F2P entries, target absent), so refinement.md §C leaving django_test_skips unmodeled (data-free config datum, not kind-3) is accurate.

CONCLUSION: 9 attacks run (prepatch bug + both prepatch classes + control-flow-effect done_with lies + non-termination + boundary/off-by-one + partial-domain + ungrounded-oracle echo). Only the gold-equivalent echo verifies and its faithful patch RESOLVES. No verifying wrong impl whose faithful patch fails to resolve. Spec is tight; verify=>resolve holds. G-EQ SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) attack on django__django-14011 velvet bundle. No divergence found; the modeled functions agree with the real repo callees on every input tested.

SPEC-REGION BYTE-IDENTITY: swebench_unified.markers.same_spec(Solution, prepatch, velvet-tables) == True for BOTH Solution_prepatch.lean and Solution_prepatch_2.lean. Spec view (axioms/pure/pre/post + signatures + contracts) is unchanged across variants; only impl regions differ. Confirmed.

LEAN DISCRIMINATION (real): Solution.lean elaborates cleanly (exit 0). Solution_prepatch.lean FAILS on `out = preferred ++ registry` (and length) — the reverted override-install; Solution_prepatch_2.lean FAILS on `∀ b ∈ out, b = false` / `out = releasedSeq handles` — the reverted release. So the two ensures clauses each carry the discriminating gold behavior and are not vacuously satisfiable.

### MODELED CALLEE FIDELITY vs REAL REPO:
- installPreferred models `ThreadedWSGIServer.process_request_thread`'s override-install loop over django.db.connections, whose real behavior is BaseConnectionHandler.__setitem__ (setattr) + __getitem__ (return stored attr else lazy-create). Modeled as `preferred ++ registry` with first-match lookup. G-CONF conformance_check.py (100,007 fuzzed inputs, seed 14011) and G-AX axiom_check.py (40,000 fuzz + boundary) run the REAL BaseConnectionHandler and agree with the model on every input. I re-ran both against a real Django 4.1a source tree (django/utils/connection.py, django/db/utils.py identical to base-commit callee bodies): both print OK, 0 disagreements.
- releaseAll models `connections.close_all()` (django/db/utils.py:207) which iterates the registry and calls conn.close() on each present connection, swallowing AttributeError for never-instantiated aliases. Modeled as releasedSeq = map every entry to false. G-AX confirms every present connection ends closed and never-instantiated aliases are not created; matches model.

SEAM PROBED (overlapping aliases): the real-world call overrides the `default` alias that already exists in `connections`, so preferred and registry share a key. The Lean carrier `preferred ++ registry` then has a duplicate key and length = preferred.length + registry.length (e.g. 3), while the real dict registry has fewer distinct keys (e.g. 2). This is NOT a drift: the declared abstraction (mapping.md §2) is an assoc-list under FIRST-MATCH lookup that explicitly tolerates duplicate keys, and only per-alias lookup identity (conn.connection is-not-None / object identity) is observable by the tests — not registry cardinality. Manual check: real __getitem__ lookups on the overlap case == model first-match lookups exactly (default→1 override wins, replica→88 preserved). The `out.length = preferred.length + registry.length` postcondition is a true structural fact of the prepend representation, not a claim about a real repo observable, so it does not over-constrain any repo behavior. No FAIL_TO_PASS test observes registry length.

Site B (django_test_skips) is a declarative test-skip datum (not FAIL_TO_PASS), reproduced verbatim in patch.diff, correctly unmodeled.

Conclusion: spec is neither too strong nor drifted. Every ensures clause is grounded in real callee behavior and validated by executable G-CONF/G-AX over 1.4e5 total inputs against the real callees. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Independently re-verified the RELAXED_LEAKAGE disposition; not a rubber-stamp.

SPEC-VIEW STABILITY: spec_view computed via swebench_unified.markers over VelvetBackend; same_spec(Solution.lean, Solution_prepatch.lean)=True and same_spec(Solution.lean, Solution_prepatch_2.lean)=True. Spec region byte-identical across variants.

CORE SOUNDNESS (grounds unavoidability): lean_verify.sh on Solution.lean -> exit 0 (verifies). Solution_prepatch.lean (install reverted) -> exit 1, unsolved goals on all three install ensures (out = preferred ++ registry, length, membership). Solution_prepatch_2.lean (release reverted) -> exit 1, unsolved goals on release ensures (out = releasedSeq handles, forall b in out b=false). Thus the install-precedence contract is genuinely load-bearing; dropping it would let non-resolving impls satisfy the spec.

LEAK IS THE DISPOSITIONED FACET: the installPreferred contract (ensures out = preferred ++ registry; ...) plus its docstring ('must operate against the handles handed to it, not against freshly-created handles for the same aliases') disclose the parent->worker connection-handoff-with-precedence, i.e. the gold's connections_override mechanism. This is exactly the facet documented in RELAXED_LEAKAGE.md.

UNAVOIDABILITY RE-DERIVED (problem_statement only, hints_text excluded): token counts in problem_statement are ALL 0 for connections_override, override, preferred, precedence, parent, handed, fresh, worker thread, alias, install, binding, share, resolv, suppl. The PS only describes the close-after-request race (#22414) and proposes the OPPOSITE remedy (revert to non-threaded WSGIServer). A PS-only spec could model only releaseAll; a faithful spec must pin the install handoff (else Solution_prepatch verifies and G-DIFF cannot fire). Faithful + non-leaking is therefore provably impossible -> genuine problem_statement<->gold mismatch.

NO NEW LEAK BEYOND THE DISPOSITIONED FACET: releaseAll side is fully public (PS title 'ThreadedWSGIServer doesn't close database connections after each thread'), leaks nothing. Site B (django_test_skips datum) is not modeled and not in the spec view. No spec-view line leaks the gold beyond the already-dispositioned install-handoff facet, and the disposition machinery is valid (meta relaxed_leakage=true, RELAXED_LEAKAGE.md present, G-LEAK status='relaxed', gates/leak.py honors it; panel-layer recording convention = pass/NO-LEAKAGE per gates/_audit.py). Disposition re-confirmed; no undisclosed leak found.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere. This cell separately records G-LEAK as `relaxed`, which is a disclosure a reviewer accepted rather than the absence of one.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `relaxed` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `RELAXED_LEAKAGE.md`, all of which ship in this bundle, so a reader can start there.