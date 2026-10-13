# P2 adversarial audit — django__django-14500

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 14 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 14 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 12 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_9.lean`, `atk_10.lean`, `atk_11.lean`, `atk_12.lean`, `atk_13.lean`, `atk_14.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `pc_correct.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None — no verifying wrong impl exists. 14 same-spec attacks were run; 12 were REJECTED by the verifier (exit 1) and the 2 that verified (atk_7 oracle echo, atk_8 effect laundering) are behaviourally IDENTICAL to the gold patch on the modeled observable, and their materialized faithful patches both RESOLVE under the official harness (F2P test_migrate_marks_replacement_unapplied passes, 21/21 P2P, 0 failures). A third, deliberately more aggressive materialization of atk_8's throwaway key sequence (refining the discarded `scratch` into REAL recorder calls on the OTHER sink, recorder.record_applied — an effect the modeled record_unapplied observable cannot see) ALSO resolves: probe_aggressive.patch, resolved=True, F2P pass, 21/21 P2P. So even the projection's blind spot does not yield a non-resolving patch here.
```

**Attacks re-run (14):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -45,11 +45,16 @@
   ensures out = m.replaces ++ [(m.appLabel, m.name)]
   do
     -- impl-start
-    let mut result : List (String × String) := [(m.appLabel, m.name)]
+    -- Pre-patch control flow: own key recorded ONLY when there are no replaced
+    -- keys (the `else` branch the gold patch deletes).
+    let mut result : List (String × String) := []
+    let e : List (String × String) :=
+      if m.replaces = [] then [(m.appLabel, m.name)] else []
+    result := e
     let mut i := m.replaces.length
     while i > 0
       invariant 0 ≤ i ∧ i ≤ m.replaces.length
-      invariant result = m.replaces.drop i ++ [(m.appLabel, m.name)]
+      invariant result = m.replaces.drop i ++ e
       done_with i = 0
       decreasing i
     do
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -45,11 +45,15 @@
   ensures out = m.replaces ++ [(m.appLabel, m.name)]
   do
     -- impl-start
-    let mut result : List (String × String) := [(m.appLabel, m.name)]
+    -- Partial domain: for a squashed migration the own key is appended, but an
+    -- ORDINARY migration (empty replaced set) records nothing at all.
+    let e : List (String × String) :=
+      if m.replaces = [] then [] else [(m.appLabel, m.name)]
+    let mut result : List (String × String) := e
     let mut i := m.replaces.length
     while i > 0
       invariant 0 ≤ i ∧ i ≤ m.replaces.length
-      invariant result = m.replaces.drop i ++ [(m.appLabel, m.name)]
+      invariant result = m.replaces.drop i ++ e
       done_with i = 0
       decreasing i
     do
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -45,12 +45,14 @@
   ensures out = m.replaces ++ [(m.appLabel, m.name)]
   do
     -- impl-start
+    -- Boundary/off-by-one: the backward scan stops one short, so the FIRST
+    -- replaced key is never recorded.
     let mut result : List (String × String) := [(m.appLabel, m.name)]
     let mut i := m.replaces.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ m.replaces.length
+    while i > 1
+      invariant 0 ≤ i ∧ i ≤ m.replaces.length ∨ m.replaces = []
       invariant result = m.replaces.drop i ++ [(m.appLabel, m.name)]
-      done_with i = 0
+      done_with i ≤ 1
       decreasing i
     do
       let k := m.replaces[i - 1]!
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -45,18 +45,20 @@
   ensures out = m.replaces ++ [(m.appLabel, m.name)]
   do
     -- impl-start
-    let mut result : List (String × String) := [(m.appLabel, m.name)]
+    -- Wrong order: the own key is recorded BEFORE the replaced keys
+    -- (out = ownKey :: replaces instead of replaces ++ [ownKey]).
+    let mut result : List (String × String) := []
     let mut i := m.replaces.length
     while i > 0
       invariant 0 ≤ i ∧ i ≤ m.replaces.length
-      invariant result = m.replaces.drop i ++ [(m.appLabel, m.name)]
+      invariant result = m.replaces.drop i
       done_with i = 0
       decreasing i
     do
       let k := m.replaces[i - 1]!
       result := k :: result
       i := i - 1
-    return result
+    return (m.appLabel, m.name) :: result
     -- impl-end
 
 prove_correct recordUnappliedKeys by
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -45,11 +45,14 @@
   ensures out = m.replaces ++ [(m.appLabel, m.name)]
   do
     -- impl-start
-    let mut result : List (String × String) := [(m.appLabel, m.name)]
+    -- Over-recording: the own key is recorded twice (the pre-patch `else` branch
+    -- kept AND the new unconditional call added).
+    let mut result : List (String × String) :=
+      [(m.appLabel, m.name), (m.appLabel, m.name)]
     let mut i := m.replaces.length
     while i > 0
       invariant 0 ≤ i ∧ i ≤ m.replaces.length
-      invariant result = m.replaces.drop i ++ [(m.appLabel, m.name)]
+      invariant result = m.replaces.drop i ++ [(m.appLabel, m.name), (m.appLabel, m.name)]
       done_with i = 0
       decreasing i
     do
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -45,11 +45,16 @@
   ensures out = m.replaces ++ [(m.appLabel, m.name)]
   do
     -- impl-start
-    let mut result : List (String × String) := [(m.appLabel, m.name)]
+    -- Plausible "don't double-record" refinement: the own key is appended only if
+    -- it is not already among the replaced keys. Differs from the frozen spec
+    -- exactly on a migration that lists its own key in `replaces`.
+    let e : List (String × String) :=
+      if (m.appLabel, m.name) ∈ m.replaces then [] else [(m.appLabel, m.name)]
+    let mut result : List (String × String) := e
     let mut i := m.replaces.length
     while i > 0
       invariant 0 ≤ i ∧ i ≤ m.replaces.length
-      invariant result = m.replaces.drop i ++ [(m.appLabel, m.name)]
+      invariant result = m.replaces.drop i ++ e
       done_with i = 0
       decreasing i
     do
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -45,21 +45,10 @@
   ensures out = m.replaces ++ [(m.appLabel, m.name)]
   do
     -- impl-start
-    let mut result : List (String × String) := [(m.appLabel, m.name)]
-    let mut i := m.replaces.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ m.replaces.length
-      invariant result = m.replaces.drop i ++ [(m.appLabel, m.name)]
-      done_with i = 0
-      decreasing i
-    do
-      let k := m.replaces[i - 1]!
-      result := k :: result
-      i := i - 1
-    return result
+    -- Oracle echo: no loop at all, the postcondition's right-hand side is
+    -- returned directly. Tests whether the contract is grounded in the inputs.
+    return m.replaces ++ [(m.appLabel, m.name)]
     -- impl-end
 
 prove_correct recordUnappliedKeys by
   loom_solve
-  rw [drop_step m.replaces i (by omega) (by omega)]
-  simp_all
```

Attack 8 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -45,6 +45,10 @@
   ensures out = m.replaces ++ [(m.appLabel, m.name)]
   do
     -- impl-start
+    -- Effect laundering: the returned (observable) sequence is correct, but the
+    -- impl additionally builds a SECOND, discarded key sequence — the Velvet
+    -- analogue of issuing extra recorder calls whose result nothing consumes.
+    let mut scratch : List (String × String) := []
     let mut result : List (String × String) := [(m.appLabel, m.name)]
     let mut i := m.replaces.length
     while i > 0
@@ -54,6 +58,7 @@
       decreasing i
     do
       let k := m.replaces[i - 1]!
+      scratch := k :: (m.appLabel, m.name) :: scratch
       result := k :: result
       i := i - 1
     return result
```

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

```diff
@@ -45,21 +45,10 @@
   ensures out = m.replaces ++ [(m.appLabel, m.name)]
   do
     -- impl-start
-    let mut result : List (String × String) := [(m.appLabel, m.name)]
-    let mut i := m.replaces.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ m.replaces.length
-      invariant result = m.replaces.drop i ++ [(m.appLabel, m.name)]
-      done_with i = 0
-      decreasing i
-    do
-      let k := m.replaces[i - 1]!
-      result := k :: result
-      i := i - 1
-    return result
+    -- Vacuity probe: pick the answer nondeterministically instead of computing it.
+    let out :| out = m.replaces ++ [(m.appLabel, m.name)]
+    return out
     -- impl-end
 
 prove_correct recordUnappliedKeys by
   loom_solve
-  rw [drop_step m.replaces i (by omega) (by omega)]
-  simp_all
```

Attack 10 — `atk_10.lean` → rejected (same spec, does not verify — good)

```diff
@@ -45,21 +45,21 @@
   ensures out = m.replaces ++ [(m.appLabel, m.name)]
   do
     -- impl-start
-    let mut result : List (String × String) := [(m.appLabel, m.name)]
-    let mut i := m.replaces.length
-    while i > 0
+    -- Order corruption inside the replaced-key loop: forward scan APPENDS, so the
+    -- replaced keys come out reversed relative to `migration.replaces`.
+    let mut result : List (String × String) := []
+    let mut i := 0
+    while i < m.replaces.length
       invariant 0 ≤ i ∧ i ≤ m.replaces.length
-      invariant result = m.replaces.drop i ++ [(m.appLabel, m.name)]
-      done_with i = 0
-      decreasing i
+      invariant result = (m.replaces.take i).reverse
+      done_with i = m.replaces.length
+      decreasing m.replaces.length - i
     do
-      let k := m.replaces[i - 1]!
+      let k := m.replaces[i]!
       result := k :: result
-      i := i - 1
-    return result
+      i := i + 1
+    return result ++ [(m.appLabel, m.name)]
     -- impl-end
 
 prove_correct recordUnappliedKeys by
   loom_solve
-  rw [drop_step m.replaces i (by omega) (by omega)]
-  simp_all
```

Attack 11 — `atk_11.lean` → rejected (same spec, does not verify — good)

```diff
@@ -45,11 +45,15 @@
   ensures out = m.replaces ++ [(m.appLabel, m.name)]
   do
     -- impl-start
-    let mut result : List (String × String) := [(m.appLabel, m.name)]
+    -- Partial domain on a size boundary: the own key is appended only when the
+    -- replaced set has at most one entry; larger squashes lose it.
+    let e : List (String × String) :=
+      if m.replaces.length ≤ 1 then [(m.appLabel, m.name)] else []
+    let mut result : List (String × String) := e
     let mut i := m.replaces.length
     while i > 0
       invariant 0 ≤ i ∧ i ≤ m.replaces.length
-      invariant result = m.replaces.drop i ++ [(m.appLabel, m.name)]
+      invariant result = m.replaces.drop i ++ e
       done_with i = 0
       decreasing i
     do
```

Attack 12 — `atk_12.lean` → rejected (same spec, does not verify — good)

```diff
@@ -45,16 +45,21 @@
   ensures out = m.replaces ++ [(m.appLabel, m.name)]
   do
     -- impl-start
+    -- Dedup of the replaced keys: a repeated key in the replaced set is recorded
+    -- only once, so the recorded sequence loses entries the gold patch emits.
     let mut result : List (String × String) := [(m.appLabel, m.name)]
     let mut i := m.replaces.length
     while i > 0
       invariant 0 ≤ i ∧ i ≤ m.replaces.length
-      invariant result = m.replaces.drop i ++ [(m.appLabel, m.name)]
+      invariant result = (m.replaces.drop i).eraseDups ++ [(m.appLabel, m.name)]
       done_with i = 0
       decreasing i
     do
       let k := m.replaces[i - 1]!
-      result := k :: result
+      if k ∈ result then
+        result := result
+      else
+        result := k :: result
       i := i - 1
     return result
     -- impl-end
```

Attack 13 — `atk_13.lean` → rejected (same spec, does not verify — good)

```diff
@@ -45,6 +45,7 @@
   ensures out = m.replaces ++ [(m.appLabel, m.name)]
   do
     -- impl-start
+    -- Truncation: only the final replaced key is recorded before the own key.
     let mut result : List (String × String) := [(m.appLabel, m.name)]
     let mut i := m.replaces.length
     while i > 0
@@ -56,7 +57,7 @@
       let k := m.replaces[i - 1]!
       result := k :: result
       i := i - 1
-    return result
+    return result.take (min 2 result.length)
     -- impl-end
 
 prove_correct recordUnappliedKeys by
```

Attack 14 — `atk_14.lean` → rejected (same spec, does not verify — good)

```diff
@@ -45,11 +45,15 @@
   ensures out = m.replaces ++ [(m.appLabel, m.name)]
   do
     -- impl-start
-    let mut result : List (String × String) := [(m.appLabel, m.name)]
+    -- Partial domain keyed on field CONTENT: the own key is recorded only when its
+    -- application label is non-empty, silently dropping it otherwise.
+    let e : List (String × String) :=
+      if m.appLabel = "" then [] else [(m.appLabel, m.name)]
+    let mut result : List (String × String) := e
     let mut i := m.replaces.length
     while i > 0
       invariant 0 ≤ i ∧ i ≤ m.replaces.length
-      invariant result = m.replaces.drop i ++ [(m.appLabel, m.name)]
+      invariant result = m.replaces.drop i ++ e
       done_with i = 0
       decreasing i
     do
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc_correct.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- axioms-end

-- pure-start
/- A migration's identity for recording purposes. Only the fields the recording
   step observes are modeled: the application label and migration name form the
   migration's own key, and `replaces` is the list of older migration keys a
   squashed migration stands in for (empty for an ordinary migration). -/
structure Migration where
  replaces : List (String × String)
  appLabel : String
  name     : String

/- Backward-scan step: dropping one fewer element of a list exposes the element
   at that index on the front. The single rewrite each loop iteration needs. -/
lemma drop_step {α : Type} [Inhabited α] (xs : List α) (i : Nat)
    (hi : 0 < i) (hle : i ≤ xs.length) :
    xs.drop (i - 1) = xs[i - 1]! :: xs.drop i := by
  have hlt : i - 1 < xs.length := by omega
  have h := List.drop_eq_getElem_cons hlt
  rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
  have hsucc : i - 1 + 1 = i := by omega
  rw [h, hsucc]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The keys recorded as unapplied when reversing a migration: every key the
   migration replaces, in order, followed by the migration's own key. For an
   ordinary migration (no replaced keys) this is just its own key. -/
method recordUnappliedKeys (m : Migration)
    return (out : List (String × String))
  ensures out = m.replaces ++ [(m.appLabel, m.name)]
  do
    -- impl-start
    let mut result : List (String × String) := [(m.appLabel, m.name)]
    let mut i := m.replaces.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ m.replaces.length
      invariant result = m.replaces.drop i ++ [(m.appLabel, m.name)]
      done_with i = 0
      decreasing i
    do
      let k := m.replaces[i - 1]!
      result := k :: result
      i := i - 1
    return result
    -- impl-end

prove_correct recordUnappliedKeys by
  loom_solve
  rw [drop_step m.replaces i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial audit of django__django-14500 velvet bundle. VERDICT: SOUND.

Setup: all files, each built by copying the frozen bundle Solution.lean and editing ONLY the impl region + the (elided) prove_correct tactic body. same_spec(bundle, attack, VelvetBackend.language) = True for ALL 15 files (14 attacks + positive control), verified individually. Repo cloned at base_commit 8c3bd0b708b488a1f6e8bd8cc6b96569904605be into .../repo; the recording block at django/db/migrations/executor.py:253-258 was read directly to build the refined patches.

Spec under attack: method recordUnappliedKeys (m : Migration) ensures out = m.replaces ++ [(m.appLabel, m.name)]. Frozen regions (axioms EMPTY, pure = Migration structure + generic drop_step lemma, pre/post empty) left byte-identical.

### VERIFY COMMAND (each, run 3-4 concurrently as background jobs):
  bash scripts/lean_verify.sh <file>.lean

### ATTACK RESULTS (exit 0 = verifies, 1 = rejected):
- atk_1.lean  PREPATCH BUG (own key recorded ONLY in the no-replaces `else` branch, i.e. the branch the gold patch deletes) -> exit 1 REJECTED. Error: unsolved `ensures_1: out = m.replaces ++ [(m.appLabel, m.name)]` with invariant_2 carrying `if m.replaces = [] then [ownKey] else []`. PREPATCH BUG REPRODUCED.
- atk_2.lean  PARTIAL DOMAIN (own key appended only when replaces is NON-empty; ordinary migration records nothing) -> exit 1 REJECTED.
- atk_3.lean  BOUNDARY off-by-one (`while i > 1`, first replaced key never recorded) -> exit 1 REJECTED (omega + unsolved ensures).
- atk_4.lean  ORDER (own key recorded FIRST: ownKey :: replaces) -> exit 1 REJECTED.
- atk_5.lean  OVER-RECORDING (own key emitted twice: old else-branch kept AND new unconditional call) -> exit 1 REJECTED.
- atk_6.lean  SELF-REFERENTIAL DEDUP (skip own key if already in replaces — a plausible 'don't double-record' refinement) -> exit 1 REJECTED.
- atk_7.lean  UNGROUNDED-ORACLE ECHO (no loop; `return m.replaces ++ [(m.appLabel, m.name)]`) -> exit 0 VERIFIES. Resolve-checked, see below.
- atk_8.lean  CONTROL-FLOW-EFFECT LAUNDERING (correct returned sequence + a SECOND discarded key sequence built in a throwaway local — the Velvet analogue of extra recorder calls nothing consumes) -> exit 0 VERIFIES. Resolve-checked, see below.
- atk_9.lean  VACUITY PROBE (`let out :| out = m.replaces ++ [ownKey]` — demonic nondeterministic choice of the answer) -> exit 1 REJECTED: 'failed to synthesize' (no Findable instance in the frozen pure region) + 'Failed to parse an assertion without names: WPGen sorry'. The frozen spec region supplies NO choice witness, so the `:|` escape hatch is unavailable.
- atk_10.lean REVERSED replaced-key order (forward scan prepending) -> exit 1 REJECTED.
- atk_11.lean LENGTH-CONDITIONAL partial domain (own key only when replaces.length <= 1) -> exit 1 REJECTED.
- atk_12.lean DEDUP of replaced keys (repeated key recorded once) -> exit 1 REJECTED.
- atk_13.lean TRUNCATION (`.take (min 2 ...)`, only last replaced key survives) -> exit 1 REJECTED.
- atk_14.lean CONTENT-KEYED partial domain (own key dropped when appLabel = "") -> exit 1 REJECTED.

POSITIVE CONTROL: pc_correct.lean (gold skeleton, backward while-fold seeded with the own key) -> exit 0 VERIFIES.
G-DIFF cross-check: the SHIPPED Solution_prepatch.lean, copied to shipped_prepatch.lean, -> exit 1 (unsolved ensures) as required.

MANDATORY RESOLVE RUNS for the 2 verifying attacks (run_resolve('django__django-14500', <patch>) via swebench_unified.harness, launched concurrently as detached background jobs):
- atk_7.patch -> completed=True, RESOLVED=True, patch_successfully_applied=True, F2P success=['test_migrate_marks_replacement_unapplied (migrations.test_executor.ExecutorTests)'] failure=[], P2P 21 success / 0 failure, note='resolved'.
- atk_8.patch -> completed=True, RESOLVED=True, applied=True, F2P success=[test_migrate_marks_replacement_unapplied] failure=[], P2P 21/0, note='resolved on attempt 2/3 (flaky: earlier attempt failed or did not complete)' — the harness's own retry logic; the recorded verdict is resolved.
- probe_aggressive.patch (EXTRA, my own hardest reading of atk_8: the throwaway key sequence refined into real recorder.record_applied calls, an effect OUTSIDE the modeled observable) -> completed=True, RESOLVED=True, applied=True, F2P pass, P2P 21/0.
Both verifying attacks are therefore CORRECT ECHOES of the gold patch, not spec weaknesses. No verifying wrong impl exists => verify DOES imply correct here.

REFINEMENT.MD AUDIT (protocol step 3): PASSES.
- Legs: A1 = R (rich `migration` object <-> structure with exactly the three touched fields replaces/app_label/name; bijection stated in mapping.md §2). A2 = I (the `for app_label, name in migration.replaces: record_unapplied(...)` loop <-> the backward while-fold prepending m.replaces[i-1]!, order-preserving; the `if migration.replaces:` guard is legitimately subsumed since an empty replaced set contributes an empty prefix — I confirmed this against the real code: the guard is behaviourally dead, `for x in []` is a no-op). A3 = I (the UNCONDITIONAL record_unapplied(migration.app_label, migration.name) <-> the own key appended last). NO kind-3 (inexpressible-changed-op) step: the operation that actually changed — dropping the `else` so the own key is recorded unconditionally — is expressed DIRECTLY in the do block as the fold seed, not hidden behind an axiom. Confirmed by atk_1: the pre-patch control flow fails the postcondition, so the discriminator is genuinely load-bearing.
- A-LEGS: there are NONE to over-claim, and I verified this mechanically rather than taking the doc's word: the axioms region is EMPTY (region_text(...,'axioms') == ''), the only two occurrences of the string 'axiom' in Solution.lean are the two region marker lines 9-10, and 0 sorry/admit. So the refinement.md §B claim 'no axioms consumed, no A-reference deep model, G-AX legitimately skips' is accurate — nothing is trusted about a callee. The single callee at the change site, recorder.record_unapplied (django/db/migrations/recorder.py:89-92, `self.ensure_schema(); self.migration_qs.filter(app=app, name=name).delete()`), is UNCHANGED by the gold patch (which touches only executor.py lines 250-261, one hunk, confirmed from patch.diff) and is modeled as a concrete list append — a legitimate I-op whose sole observable for this effect is the key it was called with, in order. An axiom about it would indeed be dead.
- PROJECTION: the model drops progress_callback (248-249, 260-261) and the `if not fake:` schema_editor/state prelude (250-252). All are outside the single gold hunk, so the projection cannot conceal patched behavior. I attacked this blind spot directly rather than accepting the argument: atk_8 (in-model laundering) and probe_aggressive (out-of-model recorder.record_applied side effect) both resolve, so no non-resolving faithful patch is reachable through the projection.

Why the spec resists: the postcondition is a total structural equation on the input carrier (out = m.replaces ++ [ownKey]) with no precondition restricting the domain, so it pins the ENTIRE input space — every partial-domain, boundary, order, cardinality and content-keyed deviation is caught (12/12 rejected), and the postcondition is grounded in the inputs rather than in an opaque oracle, so the only 'echo' available (atk_7) is exactly the correct computation spelled differently. The one residual soft spot, an impl op with no footprint on the returned value, is real in principle but not exploitable here: the F2P test observes precisely the recorded-key set, so any extra effect I could smuggle in still resolves.

Evidence retained: atk_*.lean (attacks), pc_correct.lean, shipped_prepatch.lean, atk_*.out (full verifier logs), atk_7.patch / atk_8.patch / probe_aggressive.patch, atk_*.resolve.json + probe_aggressive.resolve.json (full harness reports), mk.py/mk2.py/mk3.py/mk4.py (attack builders), mkpatch.py/mkprobe.py (patch materializers), res.py (resolve driver), repo/ (base_commit clone).

FLOOR CHECK: 14 attacks (>= 5), prepatch bug reproduced (atk_1, and the shipped prepatch independently fails), positive control verifies and is a distinct file from every attack, 0 inconclusive (every verify and every needed resolve completed).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 14 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 14 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 12 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_9.lean`, `atk_10.lean`, `atk_11.lean`, `atk_12.lean`, `atk_13.lean`, `atk_14.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `pc_correct.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None — no verifying wrong impl exists. 14 same-spec attacks were run; 12 were REJECTED by the verifier (exit 1) and the 2 that verified (atk_7 oracle echo, atk_8 effect laundering) are behaviourally IDENTICAL to the gold patch on the modeled observable, and their materialized faithful patches both RESOLVE under the official harness (F2P test_migrate_marks_replacement_unapplied passes, 21/21 P2P, 0 failures). A third, deliberately more aggressive materialization of atk_8's throwaway key sequence (refining the discarded `scratch` into REAL recorder calls on the OTHER sink, recorder.record_applied — an effect the modeled record_unapplied observable cannot see) ALSO resolves: probe_aggressive.patch, resolved=True, F2P pass, 21/21 P2P. So even the projection's blind spot does not yield a non-resolving patch here.
```

**Attacks re-run (14):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 14 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10.lean` → rejected (same spec, does not verify — good)

Attack 11 — `atk_11.lean` → rejected (same spec, does not verify — good)

Attack 12 — `atk_12.lean` → rejected (same spec, does not verify — good)

Attack 13 — `atk_13.lean` → rejected (same spec, does not verify — good)

Attack 14 — `atk_14.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc_correct.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- axioms-end

-- pure-start
/- A migration's identity for recording purposes. Only the fields the recording
   step observes are modeled: the application label and migration name form the
   migration's own key, and `replaces` is the list of older migration keys a
   squashed migration stands in for (empty for an ordinary migration). -/
structure Migration where
  replaces : List (String × String)
  appLabel : String
  name     : String

/- Backward-scan step: dropping one fewer element of a list exposes the element
   at that index on the front. The single rewrite each loop iteration needs. -/
lemma drop_step {α : Type} [Inhabited α] (xs : List α) (i : Nat)
    (hi : 0 < i) (hle : i ≤ xs.length) :
    xs.drop (i - 1) = xs[i - 1]! :: xs.drop i := by
  have hlt : i - 1 < xs.length := by omega
  have h := List.drop_eq_getElem_cons hlt
  rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
  have hsucc : i - 1 + 1 = i := by omega
  rw [h, hsucc]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The keys recorded as unapplied when reversing a migration: every key the
   migration replaces, in order, followed by the migration's own key. For an
   ordinary migration (no replaced keys) this is just its own key. -/
method recordUnappliedKeys (m : Migration)
    return (out : List (String × String))
  ensures out = m.replaces ++ [(m.appLabel, m.name)]
  do
    -- impl-start
    let mut result : List (String × String) := [(m.appLabel, m.name)]
    let mut i := m.replaces.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ m.replaces.length
      invariant result = m.replaces.drop i ++ [(m.appLabel, m.name)]
      done_with i = 0
      decreasing i
    do
      let k := m.replaces[i - 1]!
      result := k :: result
      i := i - 1
    return result
    -- impl-end

prove_correct recordUnappliedKeys by
  loom_solve
  rw [drop_step m.replaces i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial audit of django__django-14500 velvet bundle. VERDICT: SOUND.

Setup: all files, each built by copying the frozen bundle Solution.lean and editing ONLY the impl region + the (elided) prove_correct tactic body. same_spec(bundle, attack, VelvetBackend.language) = True for ALL 15 files (14 attacks + positive control), verified individually. Repo cloned at base_commit 8c3bd0b708b488a1f6e8bd8cc6b96569904605be into .../repo; the recording block at django/db/migrations/executor.py:253-258 was read directly to build the refined patches.

Spec under attack: method recordUnappliedKeys (m : Migration) ensures out = m.replaces ++ [(m.appLabel, m.name)]. Frozen regions (axioms EMPTY, pure = Migration structure + generic drop_step lemma, pre/post empty) left byte-identical.

### VERIFY COMMAND (each, run 3-4 concurrently as background jobs):
  bash scripts/lean_verify.sh <file>.lean

### ATTACK RESULTS (exit 0 = verifies, 1 = rejected):
- atk_1.lean  PREPATCH BUG (own key recorded ONLY in the no-replaces `else` branch, i.e. the branch the gold patch deletes) -> exit 1 REJECTED. Error: unsolved `ensures_1: out = m.replaces ++ [(m.appLabel, m.name)]` with invariant_2 carrying `if m.replaces = [] then [ownKey] else []`. PREPATCH BUG REPRODUCED.
- atk_2.lean  PARTIAL DOMAIN (own key appended only when replaces is NON-empty; ordinary migration records nothing) -> exit 1 REJECTED.
- atk_3.lean  BOUNDARY off-by-one (`while i > 1`, first replaced key never recorded) -> exit 1 REJECTED (omega + unsolved ensures).
- atk_4.lean  ORDER (own key recorded FIRST: ownKey :: replaces) -> exit 1 REJECTED.
- atk_5.lean  OVER-RECORDING (own key emitted twice: old else-branch kept AND new unconditional call) -> exit 1 REJECTED.
- atk_6.lean  SELF-REFERENTIAL DEDUP (skip own key if already in replaces — a plausible 'don't double-record' refinement) -> exit 1 REJECTED.
- atk_7.lean  UNGROUNDED-ORACLE ECHO (no loop; `return m.replaces ++ [(m.appLabel, m.name)]`) -> exit 0 VERIFIES. Resolve-checked, see below.
- atk_8.lean  CONTROL-FLOW-EFFECT LAUNDERING (correct returned sequence + a SECOND discarded key sequence built in a throwaway local — the Velvet analogue of extra recorder calls nothing consumes) -> exit 0 VERIFIES. Resolve-checked, see below.
- atk_9.lean  VACUITY PROBE (`let out :| out = m.replaces ++ [ownKey]` — demonic nondeterministic choice of the answer) -> exit 1 REJECTED: 'failed to synthesize' (no Findable instance in the frozen pure region) + 'Failed to parse an assertion without names: WPGen sorry'. The frozen spec region supplies NO choice witness, so the `:|` escape hatch is unavailable.
- atk_10.lean REVERSED replaced-key order (forward scan prepending) -> exit 1 REJECTED.
- atk_11.lean LENGTH-CONDITIONAL partial domain (own key only when replaces.length <= 1) -> exit 1 REJECTED.
- atk_12.lean DEDUP of replaced keys (repeated key recorded once) -> exit 1 REJECTED.
- atk_13.lean TRUNCATION (`.take (min 2 ...)`, only last replaced key survives) -> exit 1 REJECTED.
- atk_14.lean CONTENT-KEYED partial domain (own key dropped when appLabel = "") -> exit 1 REJECTED.

POSITIVE CONTROL: pc_correct.lean (gold skeleton, backward while-fold seeded with the own key) -> exit 0 VERIFIES.
G-DIFF cross-check: the SHIPPED Solution_prepatch.lean, copied to shipped_prepatch.lean, -> exit 1 (unsolved ensures) as required.

MANDATORY RESOLVE RUNS for the 2 verifying attacks (run_resolve('django__django-14500', <patch>) via swebench_unified.harness, launched concurrently as detached background jobs):
- atk_7.patch -> completed=True, RESOLVED=True, patch_successfully_applied=True, F2P success=['test_migrate_marks_replacement_unapplied (migrations.test_executor.ExecutorTests)'] failure=[], P2P 21 success / 0 failure, note='resolved'.
- atk_8.patch -> completed=True, RESOLVED=True, applied=True, F2P success=[test_migrate_marks_replacement_unapplied] failure=[], P2P 21/0, note='resolved on attempt 2/3 (flaky: earlier attempt failed or did not complete)' — the harness's own retry logic; the recorded verdict is resolved.
- probe_aggressive.patch (EXTRA, my own hardest reading of atk_8: the throwaway key sequence refined into real recorder.record_applied calls, an effect OUTSIDE the modeled observable) -> completed=True, RESOLVED=True, applied=True, F2P pass, P2P 21/0.
Both verifying attacks are therefore CORRECT ECHOES of the gold patch, not spec weaknesses. No verifying wrong impl exists => verify DOES imply correct here.

REFINEMENT.MD AUDIT (protocol step 3): PASSES.
- Legs: A1 = R (rich `migration` object <-> structure with exactly the three touched fields replaces/app_label/name; bijection stated in mapping.md §2). A2 = I (the `for app_label, name in migration.replaces: record_unapplied(...)` loop <-> the backward while-fold prepending m.replaces[i-1]!, order-preserving; the `if migration.replaces:` guard is legitimately subsumed since an empty replaced set contributes an empty prefix — I confirmed this against the real code: the guard is behaviourally dead, `for x in []` is a no-op). A3 = I (the UNCONDITIONAL record_unapplied(migration.app_label, migration.name) <-> the own key appended last). NO kind-3 (inexpressible-changed-op) step: the operation that actually changed — dropping the `else` so the own key is recorded unconditionally — is expressed DIRECTLY in the do block as the fold seed, not hidden behind an axiom. Confirmed by atk_1: the pre-patch control flow fails the postcondition, so the discriminator is genuinely load-bearing.
- A-LEGS: there are NONE to over-claim, and I verified this mechanically rather than taking the doc's word: the axioms region is EMPTY (region_text(...,'axioms') == ''), the only two occurrences of the string 'axiom' in Solution.lean are the two region marker lines 9-10, and 0 sorry/admit. So the refinement.md §B claim 'no axioms consumed, no A-reference deep model, G-AX legitimately skips' is accurate — nothing is trusted about a callee. The single callee at the change site, recorder.record_unapplied (django/db/migrations/recorder.py:89-92, `self.ensure_schema(); self.migration_qs.filter(app=app, name=name).delete()`), is UNCHANGED by the gold patch (which touches only executor.py lines 250-261, one hunk, confirmed from patch.diff) and is modeled as a concrete list append — a legitimate I-op whose sole observable for this effect is the key it was called with, in order. An axiom about it would indeed be dead.
- PROJECTION: the model drops progress_callback (248-249, 260-261) and the `if not fake:` schema_editor/state prelude (250-252). All are outside the single gold hunk, so the projection cannot conceal patched behavior. I attacked this blind spot directly rather than accepting the argument: atk_8 (in-model laundering) and probe_aggressive (out-of-model recorder.record_applied side effect) both resolve, so no non-resolving faithful patch is reachable through the projection.

Why the spec resists: the postcondition is a total structural equation on the input carrier (out = m.replaces ++ [ownKey]) with no precondition restricting the domain, so it pins the ENTIRE input space — every partial-domain, boundary, order, cardinality and content-keyed deviation is caught (12/12 rejected), and the postcondition is grounded in the inputs rather than in an opaque oracle, so the only 'echo' available (atk_7) is exactly the correct computation spelled differently. The one residual soft spot, an impl op with no footprint on the returned value, is real in principle but not exploitable here: the F2P test observes precisely the recorded-key set, so any extra effect I could smuggle in still resolves.

Evidence retained: atk_*.lean (attacks), pc_correct.lean, shipped_prepatch.lean, atk_*.out (full verifier logs), atk_7.patch / atk_8.patch / probe_aggressive.patch, atk_*.resolve.json + probe_aggressive.resolve.json (full harness reports), mk.py/mk2.py/mk3.py/mk4.py (attack builders), mkpatch.py/mkprobe.py (patch materializers), res.py (resolve driver), repo/ (base_commit clone).

FLOOR CHECK: 14 attacks (>= 5), prepatch bug reproduced (atk_1, and the shipped prepatch independently fails), positive control verifies and is a distinct file from every attack, 0 inconclusive (every verify and every needed resolve completed).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** ATTACK SCOPE: tried to show the modeled function `recordUnappliedKeys` is stronger than / drifts from the real callee `MigrationExecutor.unapply_migration` (django/db/migrations/executor.py:246) at base_commit 8c3bd0b708b488a1f6e8bd8cc6b96569904605be + gold patch. Found NO diverging input.

### What I verified

1. Spec-region freeze (byte-identical): using swebench_unified.markers with the real VelvetBackend LanguageTables (flavor='lean'), same_spec(Solution.lean, Solution_prepatch.lean) = True. Per-region SHA comparison: axioms, pre-conditions, post-conditions all empty (e3b0c44298fc) and identical; `pure` identical (bbb4af61e2b2). The discriminating `ensures out = m.replaces ++ [(m.appLabel, m.name)]` is present in the frozen spec_view of BOTH files, so the postcondition is genuinely frozen, not weakened in the prepatch pre-image.

2. Solution.lean verifies: scripts/lean_verify.sh -> EXIT=0, no sorry/error.

3. G-DIFF discriminating power confirmed (not rubber-stamped): Solution_prepatch.lean FAILS with `unsolved goals` on exactly the discriminating goal, with the invariant carrying the pre-patch branch `if m.replaces = [] then [(m.appLabel, m.name)] else []` and residual goal `result_1 = m.replaces ++ [(m.appLabel, m.name)]`. So the spec is strictly stronger than pre-patch behavior — it is the change, not a tautology.

4. Real-repo callee read directly from git (not trusted from refinement.md): pre-patch records own key ONLY in the `else` branch; post-patch records `record_unapplied(migration.app_label, migration.name)` UNCONDITIONALLY after the replaces loop. patch.diff is byte-identical to instance.json['patch']. grep confirms only ONE call site pair in django/ (executor.py:256,257) — no second recording path the projection could be missing.

5. INDEPENDENT differential fuzz (my own harness, NOT the bundle's): I rebuilt the oracle using the REAL `django.db.migrations.Migration` class rather than the bundle's `_StubMigration`, with a different RNG seed (987654321, vs bundle's pinned 14500). ~30,000 random inputs plus hostile boundaries: empty replaces; F2P squash scenario; own key present inside replaces; empty strings; NUL byte, accented/astral unicode, embedded newline, 500-char labels, '.', '..', dotted 'app.name'; triplicate duplicate keys; a 500-element replaces; and a TUPLE (not list) replaces. Result: 0 disagreements. Also confirmed real Migration's default class-level `replaces` is `[]` (falsy), so the `if migration.replaces:` guard is correctly subsumed by an empty prefix as refinement.md A2 claims.

6. Bundled conformance_check.py re-run in a fresh worktree at base_commit + gold patch: 'G-CONF OK ... 100006 inputs, 0 disagreements'.

7. F2P test actually passes against the patched worktree I built: migrations.test_executor.ExecutorTests.test_migrate_marks_replacement_unapplied -> OK. So the projected observable really is what the F2P test pins down.

RESIDUAL OBSERVATION (examined, judged NOT a faithfulness defect): the Lean method is total and unconditionally returns `replaces ++ [own]`, whereas the real method records NOTHING if `fake=False` and `migration.unapply(...)` raises (it propagates before reaching the recording block) — I confirmed this empirically. This is not a spec-vs-repo divergence because (a) the `Migration` carrier models only `replaces`/`appLabel`/`name` and has no representation of `unapply`/`atomic`/`connection`, so no input in the Lean domain corresponds to 'unapply raises'; the mapping.md §2 bijection holds that machinery fixed (fake=True, progress_callback=None); and (b) the pre-patch code has identical behavior on that path, so the projection cannot hide any PATCHED behavior — the patch touches only lines 253-258, which is exactly what the projection retains. The projection is therefore conservative in the direction that matters for this gate.

CONCLUSION: the modeled function agrees with the real patched callee on every input in the modeled domain; I could not construct a diverging input. The spec is neither too strong nor drifted. Verdict FAITHFUL. Cleaned up my worktree (git worktree remove --force).

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** G-PANEL-3 (leakage / gold-reconstruction) for django__django-14500 velvet. VERDICT: NO-LEAKAGE.

### Preconditions verified
- same_spec(Solution.lean, Solution_prepatch.lean, velvet) = True; spec_view BYTE-IDENTICAL, sha256 94645005e9115f81509bc9c5146f569e1e78e388c50e0457bfeb4b580d8b07e5 for BOTH files (matches meta.json G-HYGIENE region_hashes.spec_view). spec_view is idempotent (spec_view(spec_view(x))==spec_view(x)).
- scripts/lean_verify.sh Solution.lean => EXIT=0 (elaborates, no sorry/error), so the view judged is the real shipped artifact, not a phantom.
- Mechanical screen (leakage.screen, lean flavor) on BOTH Solution.lean and Solution_prepatch.lean: 0 hard failures, 0 warnings.

### What the consumer actually sees
Only: the `Migration` structure (replaces/appLabel/name), the generic `drop_step` list lemma, the `recordUnappliedKeys` signature, the postcondition `out = m.replaces ++ [(m.appLabel, m.name)]`, empty axioms/pre/post regions, and 3 authored doc-comments. impl region and prove_correct body are elided.

### Adversarial checks beyond the mechanical screen
1. Gold-diff quotation: none. The 5 changed lines (`# For replacement migrations...`, `else:`, the two `self.recorder.record_unapplied(migration.app_label, migration.name)`) appear nowhere, normalized or otherwise.
2. Diff markers / paths: no @@, diff --git, +++, index; no 'executor.py', no dotted 'django.db.migrations'.
3. Patched-function name: `unapply_migration` ABSENT. `MigrationExecutor` absent from the view (and is public in problem_statement anyway).
4. hints_text-only terms (the rule's sharp edge - judged against problem_statement ONLY): '#24800', 'PR 5280', 'work in progress', 'checkin queue', 'patch needs improvement' - ALL ABSENT. No hints-only leakage.
5. Hidden-test identity: 'test_migrate_marks_replacement_unapplied', '0001_squashed_0002', 'test_migrations_squashed', 'MIGRATION_MODULES', 'override_settings', 'applied_migrations', 'ExecutorTests' - ALL ABSENT.
6. Bug->fix narration (_NARRATION set): no bug/fix/patch/prepatch/regression/previously/incorrectly/wrong/broken in any spec-view comment. The doc-comments state abstract desired behavior ('every key the migration replaces, in order, followed by the migration's own key') WITHOUT diagnosing the pre-patch mechanism - no mention of a branch, an else, or a conditional.
7. Prepatch narration containment (checked explicitly): Solution_prepatch.lean's impl comment DOES narrate the mechanism ('Pre-image skeleton', 'own key recorded ONLY in the complementary branch', 'prove_correct MUST fail'). That text is INSIDE the impl region and is fully elided; both spec views hash identically, so none of it reaches the consumer. Correctly contained.
8. Unchanged-callee echo (the M1 html.unescape pattern, and a REAL mechanical-screen blind spot - see below): the method name `recordUnappliedKeys` echoes the unchanged callee `record_unapplied` (django/db/migrations/recorder.py:89, called at executor.py:256-257). Judged NOT leaking: problem_statement publicly contains both morphemes ('is not marked as unapplied', 'mark the squash migration as unapplied'), 'record' is a generic verb, and the name identifies a public MigrationRecorder API, NOT the patched function (`unapply_migration`), so it confers no edit-localization beyond the issue text.
9. Gold-reconstruction from the postcondition: the postcondition does state post-fix behavior (own key appended unconditionally) - but that is the irreducible job of a spec, and it is exactly what the public issue asks for ('mark the squash migration as unapplied, too, not only the replaced migrations'). It does not reveal the EDIT (which line was deleted / that an `else` was removed); that discriminator lives only in the elided impl. The extra ordering detail (replaces before own key) is a forced artifact of typing the observable as a List, not an edit disclosure.

### Mechanical-screen gap worth recording (not a verdict change)
leakage._patch_changed_symbols only harvests `def`/`class` names from changed lines and hunk section headers. At this change site the touched callee `record_unapplied` appears only as a CALL, so it never enters the screened symbol set - the L2/L5 identifier and comment checks could not have caught item 8 even had it been leaky. G-LEAK passing here is therefore partly vacuous on the callee-echo axis; the NO-LEAKAGE verdict on that axis rests on the manual problem_statement-morpheme argument above, not on the automated screen.

No LEAKAGE finding; no leaking_line to report.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
