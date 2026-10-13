# P2 adversarial audit — django__django-13786

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_8.lean`, `atk_9.lean` |

**Non-vacuity.** The positive control `atk_7.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

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
 -- (No axiomatized callees and no consumed axiom. The combined-settings operation
@@ -78,17 +78,7 @@
   ensures out = pruneFold newMap trackedKeys (mergeMaps baseMap newMap)
   do
     -- impl-start
-    let mut result : SettingMap := mergeMaps baseMap newMap
-    let mut i := trackedKeys.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ trackedKeys.length
-      invariant result = pruneFold newMap (trackedKeys.drop i) (mergeMaps baseMap newMap)
-      done_with i = 0
-      decreasing i
-    do
-      let c := trackedKeys[i - 1]!
-      result := if keyPresent c newMap then result else eraseKey c result
-      i := i - 1
+    let result : SettingMap := mergeMaps baseMap newMap
     return result
     -- impl-end
 
@@ -110,5 +100,4 @@
 
 prove_correct combineTrackedSettings by
   loom_solve
-  rw [pruneFold_drop_step newMap trackedKeys (mergeMaps baseMap newMap) i (by omega) (by omega)]
-  simp_all
+  simp_all [mergeMaps, pruneFold, eraseKey, keyPresent]
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
 -- (No axiomatized callees and no consumed axiom. The combined-settings operation
@@ -78,18 +78,7 @@
   ensures out = pruneFold newMap trackedKeys (mergeMaps baseMap newMap)
   do
     -- impl-start
-    let mut result : SettingMap := mergeMaps baseMap newMap
-    let mut i := trackedKeys.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ trackedKeys.length
-      invariant result = pruneFold newMap (trackedKeys.drop i) (mergeMaps baseMap newMap)
-      done_with i = 0
-      decreasing i
-    do
-      let c := trackedKeys[i - 1]!
-      result := if keyPresent c newMap then result else eraseKey c result
-      i := i - 1
-    return result
+    return baseMap
     -- impl-end
 
 /- The backward-fold step: dropping one fewer managed key exposes the key at
@@ -110,5 +99,4 @@
 
 prove_correct combineTrackedSettings by
   loom_solve
-  rw [pruneFold_drop_step newMap trackedKeys (mergeMaps baseMap newMap) i (by omega) (by omega)]
-  simp_all
+  simp_all [mergeMaps, pruneFold, eraseKey, keyPresent]
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
 -- (No axiomatized callees and no consumed axiom. The combined-settings operation
@@ -82,12 +82,10 @@
     let mut i := trackedKeys.length
     while i > 0
       invariant 0 ≤ i ∧ i ≤ trackedKeys.length
-      invariant result = pruneFold newMap (trackedKeys.drop i) (mergeMaps baseMap newMap)
       done_with i = 0
-      decreasing i
     do
       let c := trackedKeys[i - 1]!
-      result := if keyPresent c newMap then result else eraseKey c result
+      result := eraseKey c result
       i := i - 1
     return result
     -- impl-end
@@ -110,5 +108,4 @@
 
 prove_correct combineTrackedSettings by
   loom_solve
-  rw [pruneFold_drop_step newMap trackedKeys (mergeMaps baseMap newMap) i (by omega) (by omega)]
-  simp_all
+  simp_all [mergeMaps, pruneFold, eraseKey, keyPresent]
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
 -- (No axiomatized callees and no consumed axiom. The combined-settings operation
@@ -82,12 +82,10 @@
     let mut i := trackedKeys.length
     while i > 0
       invariant 0 ≤ i ∧ i ≤ trackedKeys.length
-      invariant result = pruneFold newMap (trackedKeys.drop i) (mergeMaps baseMap newMap)
       done_with i = 0
-      decreasing i
     do
       let c := trackedKeys[i - 1]!
-      result := if keyPresent c newMap then result else eraseKey c result
+      result := if keyPresent c newMap then eraseKey c result else result
       i := i - 1
     return result
     -- impl-end
@@ -110,5 +108,4 @@
 
 prove_correct combineTrackedSettings by
   loom_solve
-  rw [pruneFold_drop_step newMap trackedKeys (mergeMaps baseMap newMap) i (by omega) (by omega)]
-  simp_all
+  simp_all [mergeMaps, pruneFold, eraseKey, keyPresent]
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
 -- (No axiomatized callees and no consumed axiom. The combined-settings operation
@@ -78,17 +78,7 @@
   ensures out = pruneFold newMap trackedKeys (mergeMaps baseMap newMap)
   do
     -- impl-start
-    let mut result : SettingMap := mergeMaps baseMap newMap
-    let mut i := trackedKeys.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ trackedKeys.length
-      invariant result = pruneFold newMap (trackedKeys.drop i) (mergeMaps baseMap newMap)
-      done_with i = 0
-      decreasing i
-    do
-      let c := trackedKeys[i - 1]!
-      result := if keyPresent c newMap then result else eraseKey c result
-      i := i - 1
+    let result : SettingMap := mergeMaps newMap baseMap
     return result
     -- impl-end
 
@@ -110,5 +100,4 @@
 
 prove_correct combineTrackedSettings by
   loom_solve
-  rw [pruneFold_drop_step newMap trackedKeys (mergeMaps baseMap newMap) i (by omega) (by omega)]
-  simp_all
+  simp_all [mergeMaps, pruneFold, eraseKey, keyPresent]
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
 -- (No axiomatized callees and no consumed axiom. The combined-settings operation
@@ -78,18 +78,7 @@
   ensures out = pruneFold newMap trackedKeys (mergeMaps baseMap newMap)
   do
     -- impl-start
-    let mut result : SettingMap := mergeMaps baseMap newMap
-    let mut i := trackedKeys.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ trackedKeys.length
-      invariant result = pruneFold newMap (trackedKeys.drop i) (mergeMaps baseMap newMap)
-      done_with i = 0
-      decreasing i
-    do
-      let c := trackedKeys[i - 1]!
-      result := if keyPresent c newMap then result else eraseKey c result
-      i := i - 1
-    return result
+    return newMap
     -- impl-end
 
 /- The backward-fold step: dropping one fewer managed key exposes the key at
@@ -110,5 +99,4 @@
 
 prove_correct combineTrackedSettings by
   loom_solve
-  rw [pruneFold_drop_step newMap trackedKeys (mergeMaps baseMap newMap) i (by omega) (by omega)]
-  simp_all
+  simp_all [mergeMaps, pruneFold, eraseKey, keyPresent]
```

Attack 7 — `atk_8.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees and no consumed axiom. The combined-settings operation
@@ -78,18 +78,9 @@
   ensures out = pruneFold newMap trackedKeys (mergeMaps baseMap newMap)
   do
     -- impl-start
-    let mut result : SettingMap := mergeMaps baseMap newMap
-    let mut i := trackedKeys.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ trackedKeys.length
-      invariant result = pruneFold newMap (trackedKeys.drop i) (mergeMaps baseMap newMap)
-      done_with i = 0
-      decreasing i
-    do
-      let c := trackedKeys[i - 1]!
-      result := if keyPresent c newMap then result else eraseKey c result
-      i := i - 1
-    return result
+    match trackedKeys with
+    | [] => return mergeMaps baseMap newMap
+    | _  => return mergeMaps baseMap newMap
     -- impl-end
 
 /- The backward-fold step: dropping one fewer managed key exposes the key at
@@ -110,5 +101,4 @@
 
 prove_correct combineTrackedSettings by
   loom_solve
-  rw [pruneFold_drop_step newMap trackedKeys (mergeMaps baseMap newMap) i (by omega) (by omega)]
-  simp_all
+  simp_all [mergeMaps, pruneFold, eraseKey, keyPresent]
```

Attack 8 — `atk_9.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees and no consumed axiom. The combined-settings operation
@@ -79,12 +79,10 @@
   do
     -- impl-start
     let mut result : SettingMap := mergeMaps baseMap newMap
-    let mut i := trackedKeys.length
+    let mut i := trackedKeys.length - 1
     while i > 0
       invariant 0 ≤ i ∧ i ≤ trackedKeys.length
-      invariant result = pruneFold newMap (trackedKeys.drop i) (mergeMaps baseMap newMap)
       done_with i = 0
-      decreasing i
     do
       let c := trackedKeys[i - 1]!
       result := if keyPresent c newMap then result else eraseKey c result
@@ -110,5 +108,4 @@
 
 prove_correct combineTrackedSettings by
   loom_solve
-  rw [pruneFold_drop_step newMap trackedKeys (mergeMaps baseMap newMap) i (by omega) (by omega)]
-  simp_all
+  simp_all [mergeMaps, pruneFold, eraseKey, keyPresent]
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_7.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees and no consumed axiom. The combined-settings operation
--  is modeled DEEPLY by `mergeMaps`/`pruneFold` below; map union and key removal
--  are language builtins (the analogue of `List.++`), not repo callees. The only
--  repository datum the spec refers to — the prescribed list of managed setting keys
--  bound to the free input `trackedKeys` — is an A-reference validated against the
--  real constant by axiom_check.py (G-AX), NOT a contract the proof consumes.)
-- axioms-end

-- pure-start
/- A settings map is carried as an association list of key→value string pairs (a
   dict of options). Two maps denote the same options iff they have the same set
   of key→value pairs; the operations below preserve that reading. -/
abbrev SettingMap := List (String × String)

/- Whether a key occurs in a settings map. -/
def keyPresent (k : String) (m : SettingMap) : Bool :=
  m.any (fun p => p.1 = k)

/- Drop every entry carrying key `k` from a settings map (a map has at most one
   such entry, so this removes that key's binding entirely). -/
def eraseKey (k : String) (m : SettingMap) : SettingMap :=
  m.filter (fun p => p.1 ≠ k)

/- The override-merge of two settings maps: every binding of the overriding map
   `b`, together with each binding of the base map `a` whose key the overriding
   map does not rebind. On a shared key the overriding value wins. -/
def mergeMaps (a b : SettingMap) : SettingMap :=
  b ++ a.filter (fun p => !(keyPresent p.1 b))

/- Restrict a settings map so that a prescribed set of managed keys reflects ONLY the
   overriding map `newMap`: for each managed key in `keys`, if the overriding map
   does not mention it, clear it from the map. Front-recursive (one unfold per
   loop step — the backward-fold pattern, plan §5.4). -/
def pruneFold (newMap : SettingMap) : List String → SettingMap → SettingMap
  | [],      m => m
  | k :: ks, m =>
      let rest := pruneFold newMap ks m
      if keyPresent k newMap then rest else eraseKey k rest

@[grind] lemma pruneFold_nil (newMap : SettingMap) (m : SettingMap) :
    pruneFold newMap [] m = m := rfl

@[grind] lemma pruneFold_cons (newMap : SettingMap) (k : String)
    (ks : List String) (m : SettingMap) :
    pruneFold newMap (k :: ks) m
      = (if keyPresent k newMap then pruneFold newMap ks m
         else eraseKey k (pruneFold newMap ks m)) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Combining two settings maps under a managed-key discipline.

   `baseMap` is the existing settings map; `newMap` is an overriding map; both are
   read-only inputs (neither is `mut` — the combination mutates neither, directive
   5). `trackedKeys` is the prescribed set of *managed* setting keys.

   The result is the override-merge `mergeMaps baseMap newMap` further restricted
   so that every managed key NOT mentioned by the overriding map is cleared. Thus
   a managed setting the overriding map omits does not silently persist from the
   base map: it is unset, exactly as the overriding map dictates. The result is a
   freshly built map equal to the deep computation on the inputs, so a combination
   cannot satisfy the postcondition by echoing the plain merge. -/
method combineTrackedSettings (baseMap : SettingMap) (newMap : SettingMap) (trackedKeys : List String) return (out : SettingMap)
  ensures out = pruneFold newMap trackedKeys (mergeMaps baseMap newMap)
  do
    -- impl-start
    let mut result : SettingMap := mergeMaps baseMap newMap
    let mut i := trackedKeys.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ trackedKeys.length
      invariant result = pruneFold newMap (trackedKeys.drop i) (mergeMaps baseMap newMap)
      done_with i = 0
    do
      let c := trackedKeys[i - 1]!
      result := if keyPresent c newMap then result else eraseKey c result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer managed key exposes the key at
   `i-1` on the front, so `pruneFold` peels one prune step. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma pruneFold_drop_step (newMap : SettingMap) (keys : List String)
    (m : SettingMap) (i : Nat) (hi : 0 < i) (hle : i ≤ keys.length) :
    pruneFold newMap (keys.drop (i - 1)) m
      = (if keyPresent keys[i - 1]! newMap then pruneFold newMap (keys.drop i) m
         else eraseKey keys[i - 1]! (pruneFold newMap (keys.drop i) m)) := by
  have hlt : i - 1 < keys.length := by omega
  have hcons : keys.drop (i - 1) = keys[i - 1]! :: keys.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, pruneFold_cons]

prove_correct combineTrackedSettings by
  loom_solve
  rw [pruneFold_drop_step newMap trackedKeys (mergeMaps baseMap newMap) i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ SOUND / spec-strength TIGHT for django__django-13786 (velvet). Spec is a concrete full functional equation with NO axiom/opaque oracle: `ensures out = pruneFold newMap trackedKeys (mergeMaps baseMap newMap)`, where mergeMaps/pruneFold/eraseKey/keyPresent are all concretely-defined pure functions of the three free inputs (baseMap, newMap, trackedKeys). Nothing to echo; the ungrounded-oracle attack surface is empty by construction.

PROTOCOL: every attack edits ONLY the impl region (axioms/pure/pre/post byte-identical). same_spec confirmed True for atk_1..10 via swebench_unified.markers.same_spec (velvet backend). Verified with `bash scripts/lean_verify.sh <file>` from project root. Attack verifications run concurrently in two batches of ≤4.

ATTACKS (all same_spec=True, all REJECTED with genuine `error: unsolved goals` postcondition VC failure — not proof-shape/syntax artifacts):
- atk_1 plain merge, no prune (= prepatch bug): exit 1, unsolved goals @101.
- atk_2 return baseMap: exit 1, unsolved goals @100.
- atk_3 unconditional prune-ALL tracked keys (over-erase, keeps loop/control-flow): exit 1.
- atk_4 inverted condition (erase when key PRESENT in newMap): exit 1, unsolved goals @109.
- atk_5 reversed merge precedence (mergeMaps newMap baseMap, base wins): exit 1, unsolved goals @101.
- atk_6 return newMap: exit 1, unsolved goals @100.
- atk_8 partial-domain (match on trackedKeys but returns plain merge in both arms): exit 1, unsolved goals @102.
- atk_9 boundary/off-by-one (loop starts at length-1, skips last tracked key): exit 1, unsolved goals @109.
(Exact command each: `bash scripts/lean_verify.sh atk_N.lean`.)

Because NO wrong impl verifies, there is no verifying-wrong-impl whose faithful refined patch could fail to resolve — the patches map is empty and no run_resolve was required (verify⇒correct holds for every attack tried). This is the correct disposition, not a skipped resolve.

POSITIVE CONTROLS (same_spec=True, both VERIFY exit 0): atk_7 = original while-loop impl (exit 0); atk_10 = structurally DISTINCT correct impl using `trackedKeys.foldr (fun k acc => if keyPresent k newMap then acc else eraseKey k acc) (mergeMaps baseMap newMap)` with an induction-based proof (exit 0). Spec is non-vacuous and satisfied only by the correct prune-after-merge behavior.

PREPATCH: Solution_prepatch.lean (returns bare mergeMaps) fails verification, exit 1, `simp_all made no progress` at line 112 — the residual goal is exactly `mergeMaps baseMap newMap = pruneFold newMap trackedKeys (mergeMaps baseMap newMap)`, false whenever a managed key is in baseMap but absent from newMap. Fails for the RIGHT reason (the discriminating prune clause A5), G-DIFF holds.

REFINEMENT AUDIT (refinement.md + mapping.md + axiom_check.py): every leg is R / A-reference / I — NO kind-3 (inexpressible-changed-op). A1/A2 = R (dict[str,Any] ↔ List (String×String), set-of-pairs equality). A3 = A-reference: trackedKeys ↔ AlterModelOptions.ALTER_OPTION_KEYS, validated byte-equal in order by axiom_check.py (11-key pinned list matches real constant; constant untouched by the fix, so sound on both base and patched trees). A4 (merge seed) / A5 (per-key prune fold) = I. A6 = R+I (emitted options dict). The changed operation (managed-key restriction) is modeled DEEPLY via pruneFold, not hidden behind an axiom about the function under change. The A-reference correspondence to the real callee holds; there is no A-consumed axiom (G-AX VACUOUS). G-CONF/G-RESOLVE are out of this leg's scope (R/I mechanically covered by G-CONF).

VERDICT: SOUND — 8 distinct same-spec wrong impls (partial-domain, boundary/off-by-one, control-flow, inverted-condition, precedence, identity-echo variants) all verify-REJECT; 2 correct controls verify; prepatch reproduces the bug for the right reason; refinement legs are all R/A-reference/I with a sound A-reference. verify⇒correct holds; no break found.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_8.lean`, `atk_9.lean` |

**Non-vacuity.** The positive control `atk_7.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_8.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_9.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_7.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees and no consumed axiom. The combined-settings operation
--  is modeled DEEPLY by `mergeMaps`/`pruneFold` below; map union and key removal
--  are language builtins (the analogue of `List.++`), not repo callees. The only
--  repository datum the spec refers to — the prescribed list of managed setting keys
--  bound to the free input `trackedKeys` — is an A-reference validated against the
--  real constant by axiom_check.py (G-AX), NOT a contract the proof consumes.)
-- axioms-end

-- pure-start
/- A settings map is carried as an association list of key→value string pairs (a
   dict of options). Two maps denote the same options iff they have the same set
   of key→value pairs; the operations below preserve that reading. -/
abbrev SettingMap := List (String × String)

/- Whether a key occurs in a settings map. -/
def keyPresent (k : String) (m : SettingMap) : Bool :=
  m.any (fun p => p.1 = k)

/- Drop every entry carrying key `k` from a settings map (a map has at most one
   such entry, so this removes that key's binding entirely). -/
def eraseKey (k : String) (m : SettingMap) : SettingMap :=
  m.filter (fun p => p.1 ≠ k)

/- The override-merge of two settings maps: every binding of the overriding map
   `b`, together with each binding of the base map `a` whose key the overriding
   map does not rebind. On a shared key the overriding value wins. -/
def mergeMaps (a b : SettingMap) : SettingMap :=
  b ++ a.filter (fun p => !(keyPresent p.1 b))

/- Restrict a settings map so that a prescribed set of managed keys reflects ONLY the
   overriding map `newMap`: for each managed key in `keys`, if the overriding map
   does not mention it, clear it from the map. Front-recursive (one unfold per
   loop step — the backward-fold pattern, plan §5.4). -/
def pruneFold (newMap : SettingMap) : List String → SettingMap → SettingMap
  | [],      m => m
  | k :: ks, m =>
      let rest := pruneFold newMap ks m
      if keyPresent k newMap then rest else eraseKey k rest

@[grind] lemma pruneFold_nil (newMap : SettingMap) (m : SettingMap) :
    pruneFold newMap [] m = m := rfl

@[grind] lemma pruneFold_cons (newMap : SettingMap) (k : String)
    (ks : List String) (m : SettingMap) :
    pruneFold newMap (k :: ks) m
      = (if keyPresent k newMap then pruneFold newMap ks m
         else eraseKey k (pruneFold newMap ks m)) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Combining two settings maps under a managed-key discipline.

   `baseMap` is the existing settings map; `newMap` is an overriding map; both are
   read-only inputs (neither is `mut` — the combination mutates neither, directive
   5). `trackedKeys` is the prescribed set of *managed* setting keys.

   The result is the override-merge `mergeMaps baseMap newMap` further restricted
   so that every managed key NOT mentioned by the overriding map is cleared. Thus
   a managed setting the overriding map omits does not silently persist from the
   base map: it is unset, exactly as the overriding map dictates. The result is a
   freshly built map equal to the deep computation on the inputs, so a combination
   cannot satisfy the postcondition by echoing the plain merge. -/
method combineTrackedSettings (baseMap : SettingMap) (newMap : SettingMap) (trackedKeys : List String) return (out : SettingMap)
  ensures out = pruneFold newMap trackedKeys (mergeMaps baseMap newMap)
  do
    -- impl-start
    let mut result : SettingMap := mergeMaps baseMap newMap
    let mut i := trackedKeys.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ trackedKeys.length
      invariant result = pruneFold newMap (trackedKeys.drop i) (mergeMaps baseMap newMap)
      done_with i = 0
    do
      let c := trackedKeys[i - 1]!
      result := if keyPresent c newMap then result else eraseKey c result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer managed key exposes the key at
   `i-1` on the front, so `pruneFold` peels one prune step. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma pruneFold_drop_step (newMap : SettingMap) (keys : List String)
    (m : SettingMap) (i : Nat) (hi : 0 < i) (hle : i ≤ keys.length) :
    pruneFold newMap (keys.drop (i - 1)) m
      = (if keyPresent keys[i - 1]! newMap then pruneFold newMap (keys.drop i) m
         else eraseKey keys[i - 1]! (pruneFold newMap (keys.drop i) m)) := by
  have hlt : i - 1 < keys.length := by omega
  have hcons : keys.drop (i - 1) = keys[i - 1]! :: keys.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, pruneFold_cons]

prove_correct combineTrackedSettings by
  loom_solve
  rw [pruneFold_drop_step newMap trackedKeys (mergeMaps baseMap newMap) i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ SOUND / spec-strength TIGHT for django__django-13786 (velvet). Spec is a concrete full functional equation with NO axiom/opaque oracle: `ensures out = pruneFold newMap trackedKeys (mergeMaps baseMap newMap)`, where mergeMaps/pruneFold/eraseKey/keyPresent are all concretely-defined pure functions of the three free inputs (baseMap, newMap, trackedKeys). Nothing to echo; the ungrounded-oracle attack surface is empty by construction.

PROTOCOL: every attack edits ONLY the impl region (axioms/pure/pre/post byte-identical). same_spec confirmed True for atk_1..10 via swebench_unified.markers.same_spec (velvet backend). Verified with `bash scripts/lean_verify.sh <file>` from project root. Attack verifications run concurrently in two batches of ≤4.

ATTACKS (all same_spec=True, all REJECTED with genuine `error: unsolved goals` postcondition VC failure — not proof-shape/syntax artifacts):
- atk_1 plain merge, no prune (= prepatch bug): exit 1, unsolved goals @101.
- atk_2 return baseMap: exit 1, unsolved goals @100.
- atk_3 unconditional prune-ALL tracked keys (over-erase, keeps loop/control-flow): exit 1.
- atk_4 inverted condition (erase when key PRESENT in newMap): exit 1, unsolved goals @109.
- atk_5 reversed merge precedence (mergeMaps newMap baseMap, base wins): exit 1, unsolved goals @101.
- atk_6 return newMap: exit 1, unsolved goals @100.
- atk_8 partial-domain (match on trackedKeys but returns plain merge in both arms): exit 1, unsolved goals @102.
- atk_9 boundary/off-by-one (loop starts at length-1, skips last tracked key): exit 1, unsolved goals @109.
(Exact command each: `bash scripts/lean_verify.sh atk_N.lean`.)

Because NO wrong impl verifies, there is no verifying-wrong-impl whose faithful refined patch could fail to resolve — the patches map is empty and no run_resolve was required (verify⇒correct holds for every attack tried). This is the correct disposition, not a skipped resolve.

POSITIVE CONTROLS (same_spec=True, both VERIFY exit 0): atk_7 = original while-loop impl (exit 0); atk_10 = structurally DISTINCT correct impl using `trackedKeys.foldr (fun k acc => if keyPresent k newMap then acc else eraseKey k acc) (mergeMaps baseMap newMap)` with an induction-based proof (exit 0). Spec is non-vacuous and satisfied only by the correct prune-after-merge behavior.

PREPATCH: Solution_prepatch.lean (returns bare mergeMaps) fails verification, exit 1, `simp_all made no progress` at line 112 — the residual goal is exactly `mergeMaps baseMap newMap = pruneFold newMap trackedKeys (mergeMaps baseMap newMap)`, false whenever a managed key is in baseMap but absent from newMap. Fails for the RIGHT reason (the discriminating prune clause A5), G-DIFF holds.

REFINEMENT AUDIT (refinement.md + mapping.md + axiom_check.py): every leg is R / A-reference / I — NO kind-3 (inexpressible-changed-op). A1/A2 = R (dict[str,Any] ↔ List (String×String), set-of-pairs equality). A3 = A-reference: trackedKeys ↔ AlterModelOptions.ALTER_OPTION_KEYS, validated byte-equal in order by axiom_check.py (11-key pinned list matches real constant; constant untouched by the fix, so sound on both base and patched trees). A4 (merge seed) / A5 (per-key prune fold) = I. A6 = R+I (emitted options dict). The changed operation (managed-key restriction) is modeled DEEPLY via pruneFold, not hidden behind an axiom about the function under change. The A-reference correspondence to the real callee holds; there is no A-consumed axiom (G-AX VACUOUS). G-CONF/G-RESOLVE are out of this leg's scope (R/I mechanically covered by G-CONF).

VERDICT: SOUND — 8 distinct same-spec wrong impls (partial-domain, boundary/off-by-one, control-flow, inverted-condition, precedence, identity-echo variants) all verify-REJECT; 2 correct controls verify; prepatch reproduces the bug for the right reason; refinement legs are all R/A-reference/I with a sound A-reference. verify⇒correct holds; no break found.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / model-drifts-from-real-callee) attack found NO divergence.

Modeled function: combineTrackedSettings, postcondition `out = pruneFold newMap trackedKeys (mergeMaps baseMap newMap)`. This models the changed op in CreateModel.reduce's `elif isinstance(operation, AlterModelOptions)` branch (django/db/migrations/operations/models.py). mergeMaps = {**self.options, **operation.options}; pruneFold = the gold patch's `for key in operation.ALTER_OPTION_KEYS: if key not in operation.options: options.pop(key, None)`. The Lean model is a faithful transliteration of the gold hunk (commit 8d582bf510, #32262), verified verbatim against base_commit source.

Differential evidence:
1. Reimplemented the model in Python and ran it against the REAL patched django callee (CreateModel.reduce(AlterModelOptions(...))), materialized cleanly from base_commit bb64b99 + the gold hunk. 200,000 random (base,override) map pairs over the 11 tracked keys + non-tracked keys with distinct string values: 0 disagreements.
2. G-CONF already ran the recorded shadow vs. the patched real reduce over 100,009 inputs (seed 13786): 0 disagreements.
3. same_spec(Solution, Solution_prepatch, velvet) = True — spec region byte-identical between gold and prepatch skeletons (only impl differs).
4. Solution.lean elaborates cleanly (lean_verify.sh exit 0). Solution_prepatch.lean (plain mergeMaps, no prune) fails verification (G-DIFF) exactly on the managed-key-cleared case, confirming the spec is not vacuous / not too weak.

Abstraction fidelity: dict values (Any) modeled as String; mapping.md correctly restricts the observable to the key set + value-provenance, and set-of-pairs equality (matching Python dict.__eq__ order-insensitivity) is the comparison. keyPresent↔`in`, eraseKey↔`pop(k,None)` (no-op on absent key, matching). trackedKeys A-reference is byte-equal to real ALTER_OPTION_KEYS (G-AX, re-confirmed against base source). No input found where the modeled function disagrees with the real repo callee. The spec faithfully captures gold behavior — neither too strong nor drifting.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec-view leakage screen for django__django-13786 (velvet). Verified same_spec(Solution.lean, Solution_prepatch.lean)=True (spec region byte-identical) and leakage.screen()=PASS (no hard failures).

Leakage judged against the public problem_statement ONLY (not hints_text). The problem statement already discloses the FULL gold edit: it names the merge form `options={**self.options, **operation.options}` and states there is 'no logic to remove options not found in operation.options as is found in AlterModelOptions.state_forwards()'. So both the override-merge AND the corrective behavior (clear managed keys the override omits) are public.

The spec view models exactly this disclosed behavior — `mergeMaps` (override merge) plus `pruneFold` over a free `trackedKeys` input that clears each managed key absent from `newMap`. A faithful spec encoding correct behavior is expected; it reveals nothing beyond the public statement.

Checks:
- No diff markers, no patched file path (django/db/migrations/operations/models.py) or dotted module path in the view.
- Changed patch symbol is `reduce` (len>=4, distinctive); it does NOT appear in any spec-view identifier or comment.
- The concrete managed-key list (ALTER_OPTION_KEYS values, e.g. verbose_name) is NOT in the spec view — abstracted as free input `trackedKeys`; the actual constant lives only in mapping.md / axiom_check.py (auditor-facing), not the consumer spec view.
- No narration terms (bug/fix/patch/etc.) in view comments. Comments reference only bundle artifact/gate names (axiom_check.py, G-AX, plan §5.4), not repo edit specifics.

Conclusion: the spec view does not leak the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.
