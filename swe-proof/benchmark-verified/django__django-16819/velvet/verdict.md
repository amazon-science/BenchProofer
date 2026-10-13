# P2 adversarial audit — django__django-16819

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 18 admissible attacks re-run of 18 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 18 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 15 | `atk_0_prepatch.lean`, `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_7.lean`, `atk_9.lean`, `atk_10.lean`, `atk_11.lean`, `atk_12.lean`, `atk_14.lean`, `atk_15.lean`, `atk_16.lean`, `atk_17.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_6.lean`, `atk_8.lean`, `atk_13.lean` |

**Non-vacuity.** The positive control `pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (18):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_0_prepatch.lean` → rejected (same spec, does not verify — good)

```diff
@@ -65,10 +65,12 @@
   ensures out = (if removesAddedIndex addedName next then Reduction.cancel else inheritedOutcome)
   do
     -- impl-start
-    if removesAddedIndex addedName next then
-      return Reduction.cancel
-    else
-      return inheritedOutcome
+    -- Pre-image skeleton: this operation had NO special-case combination rule, so
+    -- the outcome of combining it with the following operation was ALWAYS the
+    -- ordinary inherited decision — even when the next operation removes the very
+    -- index just added. The frozen spec requires `cancel` in that case, so
+    -- prove_correct MUST fail.
+    return inheritedOutcome
     -- impl-end
 
 prove_correct reduceAddIndex by
```

Attack 2 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -65,10 +65,10 @@
   ensures out = (if removesAddedIndex addedName next then Reduction.cancel else inheritedOutcome)
   do
     -- impl-start
-    if removesAddedIndex addedName next then
-      return Reduction.cancel
-    else
-      return inheritedOutcome
+    -- ATTACK 1: name-blind: cancel against ANY index removal (drops the name-equality conjunct)
+    match next with
+    | NextOp.removesIndex _ => return Reduction.cancel
+    | NextOp.other          => return inheritedOutcome
     -- impl-end
 
 prove_correct reduceAddIndex by
```

Attack 3 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -65,7 +65,8 @@
   ensures out = (if removesAddedIndex addedName next then Reduction.cancel else inheritedOutcome)
   do
     -- impl-start
-    if removesAddedIndex addedName next then
+    -- ATTACK 2: partial domain: guard additionally demands a non-empty index name
+    if removesAddedIndex addedName next && !addedName.isEmpty then
       return Reduction.cancel
     else
       return inheritedOutcome
```

Attack 4 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -65,10 +65,11 @@
   ensures out = (if removesAddedIndex addedName next then Reduction.cancel else inheritedOutcome)
   do
     -- impl-start
+    -- ATTACK 3: inverted branches
     if removesAddedIndex addedName next then
+      return inheritedOutcome
+    else
       return Reduction.cancel
-    else
-      return inheritedOutcome
     -- impl-end
 
 prove_correct reduceAddIndex by
```

Attack 5 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -65,10 +65,14 @@
   ensures out = (if removesAddedIndex addedName next then Reduction.cancel else inheritedOutcome)
   do
     -- impl-start
-    if removesAddedIndex addedName next then
-      return Reduction.cancel
-    else
-      return inheritedOutcome
+    -- ATTACK 4: over-cancel: annihilates against a non-index-removal follower too
+    match next with
+    | NextOp.removesIndex name =>
+        if name = addedName then
+          return Reduction.cancel
+        else
+          return inheritedOutcome
+    | NextOp.other => return Reduction.cancel
     -- impl-end
 
 prove_correct reduceAddIndex by
```

Attack 6 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -65,10 +65,14 @@
   ensures out = (if removesAddedIndex addedName next then Reduction.cancel else inheritedOutcome)
   do
     -- impl-start
-    if removesAddedIndex addedName next then
-      return Reduction.cancel
-    else
-      return inheritedOutcome
+    -- ATTACK 5: boundary: prefix match instead of full name equality
+    match next with
+    | NextOp.removesIndex name =>
+        if addedName.isPrefixOf name then
+          return Reduction.cancel
+        else
+          return inheritedOutcome
+    | NextOp.other => return inheritedOutcome
     -- impl-end
 
 prove_correct reduceAddIndex by
```

Attack 7 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -65,10 +65,12 @@
   ensures out = (if removesAddedIndex addedName next then Reduction.cancel else inheritedOutcome)
   do
     -- impl-start
+    -- ATTACK 6: control-flow-effect: inherited decision bound EAGERLY before the guard
+    let inherited := inheritedOutcome
     if removesAddedIndex addedName next then
       return Reduction.cancel
     else
-      return inheritedOutcome
+      return inherited
     -- impl-end
 
 prove_correct reduceAddIndex by
```

Attack 8 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -65,10 +65,14 @@
   ensures out = (if removesAddedIndex addedName next then Reduction.cancel else inheritedOutcome)
   do
     -- impl-start
-    if removesAddedIndex addedName next then
-      return Reduction.cancel
-    else
-      return inheritedOutcome
+    -- ATTACK 7: inlined guard, comparison operands swapped
+    match next with
+    | NextOp.removesIndex name =>
+        if addedName = name then
+          return Reduction.cancel
+        else
+          return inheritedOutcome
+    | NextOp.other => return inheritedOutcome
     -- impl-end
 
 prove_correct reduceAddIndex by
```

Attack 9 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -65,10 +65,8 @@
   ensures out = (if removesAddedIndex addedName next then Reduction.cancel else inheritedOutcome)
   do
     -- impl-start
-    if removesAddedIndex addedName next then
-      return Reduction.cancel
-    else
-      return inheritedOutcome
+    -- ATTACK 8: ungrounded-oracle echo: postcondition returned verbatim
+    return (if removesAddedIndex addedName next then Reduction.cancel else inheritedOutcome)
     -- impl-end
 
 prove_correct reduceAddIndex by
```

Attack 10 — `atk_9.lean` → rejected (same spec, does not verify — good)

```diff
@@ -65,10 +65,14 @@
   ensures out = (if removesAddedIndex addedName next then Reduction.cancel else inheritedOutcome)
   do
     -- impl-start
-    if removesAddedIndex addedName next then
-      return Reduction.cancel
-    else
-      return inheritedOutcome
+    -- ATTACK 9: ungrounded oracle on the callee: perturbs the INHERITED outcome it must pass through
+    match inheritedOutcome with
+    | Reduction.cancel => return Reduction.cancel
+    | Reduction.inherited t =>
+        if removesAddedIndex addedName next then
+          return Reduction.cancel
+        else
+          return Reduction.inherited (t + 1)
     -- impl-end
 
 prove_correct reduceAddIndex by
```

Attack 11 — `atk_10.lean` → rejected (same spec, does not verify — good)

```diff
@@ -65,7 +65,8 @@
   ensures out = (if removesAddedIndex addedName next then Reduction.cancel else inheritedOutcome)
   do
     -- impl-start
-    if removesAddedIndex addedName next then
+    -- ATTACK 10: structural equality on the projected follower instead of the pure guard
+    if next = NextOp.removesIndex addedName then
       return Reduction.cancel
     else
       return inheritedOutcome
```

Attack 12 — `atk_11.lean` → rejected (same spec, does not verify — good)

```diff
@@ -65,6 +65,12 @@
   ensures out = (if removesAddedIndex addedName next then Reduction.cancel else inheritedOutcome)
   do
     -- impl-start
+    -- ATTACK 11: divergence: correct value behind a non-terminating loop (probes total semantics)
+    let mut k := 0
+    while k = 0
+    invariant True
+    do
+      k := 0
     if removesAddedIndex addedName next then
       return Reduction.cancel
     else
```

Attack 13 — `atk_12.lean` → rejected (same spec, does not verify — good)

```diff
@@ -65,10 +65,14 @@
   ensures out = (if removesAddedIndex addedName next then Reduction.cancel else inheritedOutcome)
   do
     -- impl-start
-    if removesAddedIndex addedName next then
-      return Reduction.cancel
-    else
-      return inheritedOutcome
+    -- ATTACK 12: boundary: name LENGTH equality instead of name equality
+    match next with
+    | NextOp.removesIndex name =>
+        if name.length = addedName.length then
+          return Reduction.cancel
+        else
+          return inheritedOutcome
+    | NextOp.other => return inheritedOutcome
     -- impl-end
 
 prove_correct reduceAddIndex by
```

Attack 14 — `atk_13.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -65,10 +65,14 @@
   ensures out = (if removesAddedIndex addedName next then Reduction.cancel else inheritedOutcome)
   do
     -- impl-start
-    if removesAddedIndex addedName next then
-      return Reduction.cancel
-    else
-      return inheritedOutcome
+    -- ATTACK 13: effect-order: consults the inherited decision FIRST, even on the cancel path
+    match inheritedOutcome with
+    | Reduction.cancel => return inheritedOutcome
+    | Reduction.inherited _ =>
+        if removesAddedIndex addedName next then
+          return Reduction.cancel
+        else
+          return inheritedOutcome
     -- impl-end
 
 prove_correct reduceAddIndex by
```

Attack 15 — `atk_14.lean` → rejected (same spec, does not verify — good)

```diff
@@ -65,10 +65,11 @@
   ensures out = (if removesAddedIndex addedName next then Reduction.cancel else inheritedOutcome)
   do
     -- impl-start
+    -- ATTACK 14: ungrounded oracle: fabricates a concrete inherited outcome instead of passing it through
     if removesAddedIndex addedName next then
       return Reduction.cancel
     else
-      return inheritedOutcome
+      return (Reduction.inherited 0)
     -- impl-end
 
 prove_correct reduceAddIndex by
```

Attack 16 — `atk_15.lean` → rejected (same spec, does not verify — good)

```diff
@@ -65,7 +65,8 @@
   ensures out = (if removesAddedIndex addedName next then Reduction.cancel else inheritedOutcome)
   do
     -- impl-start
-    if removesAddedIndex addedName next then
+    -- ATTACK 15: over-cancel on the empty-name boundary (widens the guard)
+    if removesAddedIndex addedName next || addedName.isEmpty then
       return Reduction.cancel
     else
       return inheritedOutcome
```

Attack 17 — `atk_16.lean` → rejected (same spec, does not verify — good)

```diff
@@ -65,10 +65,14 @@
   ensures out = (if removesAddedIndex addedName next then Reduction.cancel else inheritedOutcome)
   do
     -- impl-start
-    if removesAddedIndex addedName next then
-      return Reduction.cancel
-    else
-      return inheritedOutcome
+    -- ATTACK 16: case-insensitive name comparison (plausible: migration_name_fragment lowercases)
+    match next with
+    | NextOp.removesIndex name =>
+        if name.map Char.toLower = addedName.map Char.toLower then
+          return Reduction.cancel
+        else
+          return inheritedOutcome
+    | NextOp.other => return inheritedOutcome
     -- impl-end
 
 prove_correct reduceAddIndex by
```

Attack 18 — `atk_17.lean` → rejected (same spec, does not verify — good)

```diff
@@ -65,8 +65,11 @@
   ensures out = (if removesAddedIndex addedName next then Reduction.cancel else inheritedOutcome)
   do
     -- impl-start
+    -- ATTACK 17: partial domain in the FREE input: cancels only when the inherited outcome is `inherited 0`
     if removesAddedIndex addedName next then
-      return Reduction.cancel
+      match inheritedOutcome with
+      | Reduction.inherited 0 => return Reduction.cancel
+      | _                     => return inheritedOutcome
     else
       return inheritedOutcome
     -- impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The ordinary reduction decision that applies to every
--  other pairing — the inherited, UNCHANGED behaviour delegated to the base
--  operation — is taken as a FREE INPUT `inheritedOutcome`, so the spec makes no
--  behavioural claim about it and holds for every value. Nothing here needs
--  validation against a real callee, hence no G-AX.)
-- axioms-end

-- pure-start
/- The outcome of asking whether an operation can be combined with the operation
   that immediately follows it in a plan. `cancel` denotes the empty replacement
   (the two operations annihilate and are dropped from the plan); `inherited tag`
   stands for any OTHER outcome of the ordinary, unchanged reduction decision (a
   keep / a non-empty replacement / "cannot combine"). The `tag` makes the
   non-`cancel` outcomes an open domain, so a consumer cannot conflate them with
   the empty-replacement outcome. -/
inductive Reduction where
  | cancel
  | inherited (tag : Nat)
  deriving DecidableEq, Inhabited

/- The shape of the operation that follows. `removesIndex name` is an operation
   that removes the index identified by `name`; `other` is anything else. Only
   this much of the following operation is consulted by the decision below. -/
inductive NextOp where
  | removesIndex (name : List Char)
  | other
  deriving DecidableEq, Inhabited

/- The decisive condition: the operation that follows removes the very index this
   operation adds — i.e. it is an index-removal whose target name equals the
   added index's name. -/
def removesAddedIndex (addedName : List Char) (next : NextOp) : Bool :=
  match next with
  | NextOp.removesIndex name => decide (name = addedName)
  | NextOp.other             => false
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Combine an index-addition with the operation that immediately follows it.

   Desired behaviour: when the following operation removes the very index that was
   just added (same index name), the two operations cancel and the plan keeps
   nothing in their place (`cancel`). In every other situation the result is the
   ordinary, unchanged reduction decision (`inheritedOutcome`).

   `addedName` (the added index's name), `next` (the following operation), and
   `inheritedOutcome` (the ordinary decision for every other pairing) are
   read-only inputs; nothing handed in is mutated (directive 5). -/
method reduceAddIndex (addedName : List Char) (next : NextOp) (inheritedOutcome : Reduction)
    return (out : Reduction)
  ensures out = (if removesAddedIndex addedName next then Reduction.cancel else inheritedOutcome)
  do
    -- impl-start
    if removesAddedIndex addedName next then
      return Reduction.cancel
    else
      return inheritedOutcome
    -- impl-end

prove_correct reduceAddIndex by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ (refinement fidelity) for django__django-16819/velvet. 18 same-spec attacks (same_spec=True on ALL 18, checked with swebench_unified.markers.same_spec + get_backend('velvet').language, editing ONLY the impl region). Positive control pc.lean is byte-identical to the bundle Solution.lean and verifies EXIT=0 via `bash scripts/lean_verify.sh <file>`.

PREPATCH REPRODUCED: atk_0_prepatch.lean (bundle Solution_prepatch.lean, `return inheritedOutcome` always) -> EXIT=1, unsolved goal `inheritedOutcome = if removesAddedIndex addedName next = true then Reduction.cancel else inheritedOutcome` — EXACTLY the goal refinement.md §B predicts.

REJECTED (EXIT=1, all SEMANTIC failures — unsolved `ensures_1` goals or the total-correctness termination discipline, NOT syntax/type errors; verified by reading every log):
- atk_1 name-blind: cancel vs ANY RemoveIndex (drops the name-equality conjunct)
- atk_2 partial domain: guard also demands a non-empty index name
- atk_3 inverted branches
- atk_4 over-cancel: annihilates vs a non-index-removal follower (NextOp.other)
- atk_5 boundary: `addedName.isPrefixOf name` instead of full equality
- atk_9 ungrounded oracle on the callee: perturbs the inherited outcome (`inherited (t+1)`) it must pass through
- atk_11 DIVERGENCE probe: correct value behind a non-terminating `while k = 0` loop -> rejected with "Decreasing annotations are required in total correctness semantics". The `loom.semantics.termination "total"` setting is load-bearing: a hanging refinement cannot sneak through.
- atk_12 boundary: name LENGTH equality instead of name equality
- atk_14 ungrounded oracle: fabricates a concrete `Reduction.inherited 0` instead of passing the inherited decision through
- atk_15 over-cancel on the empty-name boundary (`|| addedName.isEmpty`)
- atk_16 case-INSENSITIVE name comparison (plausible bug: migration_name_fragment lowercases the name) — correctly rejected, so the spec pins code-point equality as mapping.md §2 claims
- atk_17 partial domain in the FREE input: cancels only when inheritedOutcome = `inherited 0`
- atk_7 / atk_10 are behaviourally EQUIVALENT to gold (operands swapped; structural `next = NextOp.removesIndex addedName`) yet were rejected on unsolved goals — `loom_solve` incompleteness (it does not unfold `removesAddedIndex` under the branch hypothesis). This is a correct-but-not-verifying direction, which does NOT bear on verify=>correct, so it is not a G-EQ defect. Noted for the record.

VERIFIED (EXIT=0) — 3 candidates, ALL materialized as faithful refined patches and ALL RUN through the official harness (`swebench_unified.harness.run_resolve('django__django-16819', patch)`), NOT speculation:
- atk_6 (inherited decision bound EAGERLY before the guard; patch_atk_6.diff) -> resolved=True, completed=True, F2P test_add_remove_index PASS, 38/38 P2P pass
- atk_8 (ungrounded-oracle ECHO: postcondition returned verbatim as one ternary; patch_atk_8.diff) -> resolved=True, completed=True, F2P PASS, 38/38 P2P
- atk_13 (effect-order: consults super().reduce FIRST, even on the cancel path; patch_atk_13.diff) -> resolved=True, completed=True, F2P PASS, 38/38 P2P
All three are behaviourally gold-equivalent — `Operation.reduce` cannot return `[]` (base.py:134-139 returns `[operation]`, `[self]` or `False`, and `elidable=False` by default), so eager evaluation and the `inherited == []` pre-check are both no-ops. Correct echoes, NOT weaknesses. No verifying attack's patch failed to resolve => verify=>correct holds on this evidence.

A-LEG AUDIT (my focus; R/I legs left to G-CONF): the bundle declares NO axioms and NO A-references. Confirmed mechanically: 0 axiom/opaque/sorry declarations in Solution.lean, the axioms region is comment-only, meta.json gates['G-AX'].status='skip'. The single callee `super().reduce(operation, app_label)` is abstracted as the FREE INPUT `inheritedOutcome` with NO relied-on property (the ensures clause holds for every value it may take, which atk_9/atk_14/atk_17 confirm is genuinely universally quantified — perturbing or restricting it is rejected).

Correspondence checked against the real repo in a worktree at base_commit 0b0998dc151feb77068e2387c34cc50ef6b356ae: AddIndex.__mro__ = [AddIndex, IndexOperation, Operation, object]; IndexOperation has NO own `reduce` ('reduce' in IndexOperation.__dict__ == False); AddIndex.reduce.__qualname__ == 'Operation.reduce' at base. So `super().reduce` provably binds to Operation.reduce (base.py:128-139), UNCHANGED by patch.diff (the gold hunk touches only models.py) — mapping.md §3 is accurate. RemoveIndex.name is a plain __init__ attribute (models.py:869) and RemoveIndex is untouched, so the `isinstance` + `.name` facts the guard leans on are pre-existing unchanged repo facts, correctly modeled structurally by the NextOp carrier rather than axiomatized.

MODEL<->PATCH CORRESPONDENCE: patch.diff is byte-identical to the frozen row['patch'] (diffed against instance.json). Every refinement.md leg A1-A5 is R or I (no kind-3); the changed operation — the special-case cancellation — is modeled DEEPLY via `removesAddedIndex` over an explicit NextOp carrier plus the `if ... then cancel else inheritedOutcome` decision, not hidden behind an axiom about a function under change. A3's claim that the gold guard compares ONLY the index name (not model_name) matches models.py:865 exactly, and refinement.md states it explicitly rather than glossing it. The `Reduction.cancel` / `inherited tag` split is justified: `[]` is genuinely disjoint from everything Operation.reduce can return, so the carrier does not conflate the empty replacement with an inherited outcome, and the open `tag : Nat` domain keeps the atk_9/atk_14 perturbations detectable.

The bundle's previously recorded G-EQ 'fail' was an EVIDENCE gap ('only 0 attacks (need >= 5); prepatch bug not reproduced; no positive control' — attacks were not retained for this bundle), not a discovered spec defect. This run supplies the missing machine-checked evidence.

Verdict SOUND: 18 same-spec attacks run (>= 5 floor met), prepatch reproduced, positive control verifies, and every one of the 3 verifying candidates has an executed run_resolve showing resolved=True. No counterexample to verify=>correct found.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 18 admissible attacks re-run of 18 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 18 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 15 | `atk_0_prepatch.lean`, `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_7.lean`, `atk_9.lean`, `atk_10.lean`, `atk_11.lean`, `atk_12.lean`, `atk_14.lean`, `atk_15.lean`, `atk_16.lean`, `atk_17.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_6.lean`, `atk_8.lean`, `atk_13.lean` |

**Non-vacuity.** The positive control `pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (18):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 18 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_0_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 10 — `atk_9.lean` → rejected (same spec, does not verify — good)

Attack 11 — `atk_10.lean` → rejected (same spec, does not verify — good)

Attack 12 — `atk_11.lean` → rejected (same spec, does not verify — good)

Attack 13 — `atk_12.lean` → rejected (same spec, does not verify — good)

Attack 14 — `atk_13.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 15 — `atk_14.lean` → rejected (same spec, does not verify — good)

Attack 16 — `atk_15.lean` → rejected (same spec, does not verify — good)

Attack 17 — `atk_16.lean` → rejected (same spec, does not verify — good)

Attack 18 — `atk_17.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The ordinary reduction decision that applies to every
--  other pairing — the inherited, UNCHANGED behaviour delegated to the base
--  operation — is taken as a FREE INPUT `inheritedOutcome`, so the spec makes no
--  behavioural claim about it and holds for every value. Nothing here needs
--  validation against a real callee, hence no G-AX.)
-- axioms-end

-- pure-start
/- The outcome of asking whether an operation can be combined with the operation
   that immediately follows it in a plan. `cancel` denotes the empty replacement
   (the two operations annihilate and are dropped from the plan); `inherited tag`
   stands for any OTHER outcome of the ordinary, unchanged reduction decision (a
   keep / a non-empty replacement / "cannot combine"). The `tag` makes the
   non-`cancel` outcomes an open domain, so a consumer cannot conflate them with
   the empty-replacement outcome. -/
inductive Reduction where
  | cancel
  | inherited (tag : Nat)
  deriving DecidableEq, Inhabited

/- The shape of the operation that follows. `removesIndex name` is an operation
   that removes the index identified by `name`; `other` is anything else. Only
   this much of the following operation is consulted by the decision below. -/
inductive NextOp where
  | removesIndex (name : List Char)
  | other
  deriving DecidableEq, Inhabited

/- The decisive condition: the operation that follows removes the very index this
   operation adds — i.e. it is an index-removal whose target name equals the
   added index's name. -/
def removesAddedIndex (addedName : List Char) (next : NextOp) : Bool :=
  match next with
  | NextOp.removesIndex name => decide (name = addedName)
  | NextOp.other             => false
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Combine an index-addition with the operation that immediately follows it.

   Desired behaviour: when the following operation removes the very index that was
   just added (same index name), the two operations cancel and the plan keeps
   nothing in their place (`cancel`). In every other situation the result is the
   ordinary, unchanged reduction decision (`inheritedOutcome`).

   `addedName` (the added index's name), `next` (the following operation), and
   `inheritedOutcome` (the ordinary decision for every other pairing) are
   read-only inputs; nothing handed in is mutated (directive 5). -/
method reduceAddIndex (addedName : List Char) (next : NextOp) (inheritedOutcome : Reduction)
    return (out : Reduction)
  ensures out = (if removesAddedIndex addedName next then Reduction.cancel else inheritedOutcome)
  do
    -- impl-start
    if removesAddedIndex addedName next then
      return Reduction.cancel
    else
      return inheritedOutcome
    -- impl-end

prove_correct reduceAddIndex by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ (refinement fidelity) for django__django-16819/velvet. 18 same-spec attacks (same_spec=True on ALL 18, checked with swebench_unified.markers.same_spec + get_backend('velvet').language, editing ONLY the impl region). Positive control pc.lean is byte-identical to the bundle Solution.lean and verifies EXIT=0 via `bash scripts/lean_verify.sh <file>`.

PREPATCH REPRODUCED: atk_0_prepatch.lean (bundle Solution_prepatch.lean, `return inheritedOutcome` always) -> EXIT=1, unsolved goal `inheritedOutcome = if removesAddedIndex addedName next = true then Reduction.cancel else inheritedOutcome` — EXACTLY the goal refinement.md §B predicts.

REJECTED (EXIT=1, all SEMANTIC failures — unsolved `ensures_1` goals or the total-correctness termination discipline, NOT syntax/type errors; verified by reading every log):
- atk_1 name-blind: cancel vs ANY RemoveIndex (drops the name-equality conjunct)
- atk_2 partial domain: guard also demands a non-empty index name
- atk_3 inverted branches
- atk_4 over-cancel: annihilates vs a non-index-removal follower (NextOp.other)
- atk_5 boundary: `addedName.isPrefixOf name` instead of full equality
- atk_9 ungrounded oracle on the callee: perturbs the inherited outcome (`inherited (t+1)`) it must pass through
- atk_11 DIVERGENCE probe: correct value behind a non-terminating `while k = 0` loop -> rejected with "Decreasing annotations are required in total correctness semantics". The `loom.semantics.termination "total"` setting is load-bearing: a hanging refinement cannot sneak through.
- atk_12 boundary: name LENGTH equality instead of name equality
- atk_14 ungrounded oracle: fabricates a concrete `Reduction.inherited 0` instead of passing the inherited decision through
- atk_15 over-cancel on the empty-name boundary (`|| addedName.isEmpty`)
- atk_16 case-INSENSITIVE name comparison (plausible bug: migration_name_fragment lowercases the name) — correctly rejected, so the spec pins code-point equality as mapping.md §2 claims
- atk_17 partial domain in the FREE input: cancels only when inheritedOutcome = `inherited 0`
- atk_7 / atk_10 are behaviourally EQUIVALENT to gold (operands swapped; structural `next = NextOp.removesIndex addedName`) yet were rejected on unsolved goals — `loom_solve` incompleteness (it does not unfold `removesAddedIndex` under the branch hypothesis). This is a correct-but-not-verifying direction, which does NOT bear on verify=>correct, so it is not a G-EQ defect. Noted for the record.

VERIFIED (EXIT=0) — 3 candidates, ALL materialized as faithful refined patches and ALL RUN through the official harness (`swebench_unified.harness.run_resolve('django__django-16819', patch)`), NOT speculation:
- atk_6 (inherited decision bound EAGERLY before the guard; patch_atk_6.diff) -> resolved=True, completed=True, F2P test_add_remove_index PASS, 38/38 P2P pass
- atk_8 (ungrounded-oracle ECHO: postcondition returned verbatim as one ternary; patch_atk_8.diff) -> resolved=True, completed=True, F2P PASS, 38/38 P2P
- atk_13 (effect-order: consults super().reduce FIRST, even on the cancel path; patch_atk_13.diff) -> resolved=True, completed=True, F2P PASS, 38/38 P2P
All three are behaviourally gold-equivalent — `Operation.reduce` cannot return `[]` (base.py:134-139 returns `[operation]`, `[self]` or `False`, and `elidable=False` by default), so eager evaluation and the `inherited == []` pre-check are both no-ops. Correct echoes, NOT weaknesses. No verifying attack's patch failed to resolve => verify=>correct holds on this evidence.

A-LEG AUDIT (my focus; R/I legs left to G-CONF): the bundle declares NO axioms and NO A-references. Confirmed mechanically: 0 axiom/opaque/sorry declarations in Solution.lean, the axioms region is comment-only, meta.json gates['G-AX'].status='skip'. The single callee `super().reduce(operation, app_label)` is abstracted as the FREE INPUT `inheritedOutcome` with NO relied-on property (the ensures clause holds for every value it may take, which atk_9/atk_14/atk_17 confirm is genuinely universally quantified — perturbing or restricting it is rejected).

Correspondence checked against the real repo in a worktree at base_commit 0b0998dc151feb77068e2387c34cc50ef6b356ae: AddIndex.__mro__ = [AddIndex, IndexOperation, Operation, object]; IndexOperation has NO own `reduce` ('reduce' in IndexOperation.__dict__ == False); AddIndex.reduce.__qualname__ == 'Operation.reduce' at base. So `super().reduce` provably binds to Operation.reduce (base.py:128-139), UNCHANGED by patch.diff (the gold hunk touches only models.py) — mapping.md §3 is accurate. RemoveIndex.name is a plain __init__ attribute (models.py:869) and RemoveIndex is untouched, so the `isinstance` + `.name` facts the guard leans on are pre-existing unchanged repo facts, correctly modeled structurally by the NextOp carrier rather than axiomatized.

MODEL<->PATCH CORRESPONDENCE: patch.diff is byte-identical to the frozen row['patch'] (diffed against instance.json). Every refinement.md leg A1-A5 is R or I (no kind-3); the changed operation — the special-case cancellation — is modeled DEEPLY via `removesAddedIndex` over an explicit NextOp carrier plus the `if ... then cancel else inheritedOutcome` decision, not hidden behind an axiom about a function under change. A3's claim that the gold guard compares ONLY the index name (not model_name) matches models.py:865 exactly, and refinement.md states it explicitly rather than glossing it. The `Reduction.cancel` / `inherited tag` split is justified: `[]` is genuinely disjoint from everything Operation.reduce can return, so the carrier does not conflate the empty replacement with an inherited outcome, and the open `tag : Nat` domain keeps the atk_9/atk_14 perturbations detectable.

The bundle's previously recorded G-EQ 'fail' was an EVIDENCE gap ('only 0 attacks (need >= 5); prepatch bug not reproduced; no positive control' — attacks were not retained for this bundle), not a discovered spec defect. This run supplies the missing machine-checked evidence.

Verdict SOUND: 18 same-spec attacks run (>= 5 floor met), prepatch reproduced, positive control verifies, and every one of the 3 verifying candidates has an executed run_resolve showing resolved=True. No counterexample to verify=>correct found.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** No divergence found between the modeled function and the real callee. Reference used correctly: base_commit worktree (0b0998dc15) with patch.diff APPLIED for the modeled function AddIndex.reduce; base commit only for the untouched callee Operation.reduce.

### Spec region integrity
- markers.same_spec(Solution.lean, Solution_prepatch.lean, velvet tables) = True (byte-identical spec signature).
- region_hashes recomputed and match meta.json G-HYGIENE exactly (axioms/pure/impl/spec_view all True).

### What the spec claims
ensures out = (if removesAddedIndex addedName next then Reduction.cancel else inheritedOutcome).
The real patched method is: if isinstance(operation, RemoveIndex) and self.index.name == operation.name: return []; else return super().reduce(operation, app_label).

### FAITHFULNESS EVIDENCE (all agreeing)
1. Differential model-vs-real on the patched worktree: 12 hand-built edge cases + 60,000 fuzzed pairings -> 0 disagreements. Edge cases specifically aimed at over-strength: model-name mismatch with name match (correctly cancels -- gold guard ignores model name, and the spec faithfully ignores it too); RemoveIndex with name=None; non-RemoveIndex op that nonetheless has a .name equal to the index name; RenameIndex with old_name == added name; RemoveConstraint with the same name; unicode index name; case-differing names; RemoveIndex SUBCLASS (stand-in for contrib.postgres RemoveIndexConcurrently, a real RemoveIndex subclass) both matching and non-matching; elidable RemoveIndex; elidable AddIndex self; lazy (gettext) strings on either side of the comparison.
2. Shipped conformance_check.py re-run against the real patched repo: 100,005 inputs, 0 disagreements (reproduces the recorded G-CONF).
3. STRONGEST TEST -- substituted a reduce() derived SOLELY from the frozen Lean spec (via mapping.md's str<->List Char / NextOp / []<->cancel bijection) into the real repo: full migrations suite = 716 tests OK (skipped=2), including the F2P test_add_remove_index. Negative control through the identical injection path (a deliberately wrong guard that also requires a model-name match) FAILED 1 test, proving the injection was live and the positive result is not vacuous.
4. F2P test_add_remove_index passes on the patched worktree.
5. Prepatch control fails on exactly the intended goal: |- inheritedOutcome = if removesAddedIndex addedName next = true then Reduction.cancel else inheritedOutcome. Solution.lean verifies (lean_verify exit 0).

ABSTRACTIONS CHECKED, NOT ASSUMED
- super().reduce: MRO is AddIndex -> IndexOperation -> Operation -> object; IndexOperation does not define reduce, so super().reduce resolves exactly to the UNCHANGED Operation.reduce (base.py:129-139). Modeling it as the free input inheritedOutcome is a weakening (spec holds for every value), so it cannot be a source of over-strength, and it needs no G-AX.
- The []<->cancel bijection is sound because Operation.reduce provably can NEVER return []: it returns [operation], [self] (both single-element), or False. So the disjointness of Reduction.cancel from every 'inherited tag' matches reality; had super() been able to return [], the Nat-tagged inherited carrier would have been unfaithful. Verified by reading the source.
- app_label is dropped from the model; Operation.reduce ignores it entirely, so the projection is lossless.
- No precondition region is needed: the method is total on its domain. AddIndex.__init__ rejects an unnamed index (models.py:816-820), so self.index.name is always present, and RemoveIndex always carries .name.

### Attack surfaces that did not pan out
- 'Guard should also compare model_name' -- refuted: the gold guard compares only the index name, and refinement.md A3 / mapping.md flag this explicitly; the model matches gold, and the model-name-comparing variant is what my negative control used (it breaks the suite).
- 'NextOp collapses name mismatches into other' -- refuted: mapping.md §2 explicitly keeps a differently-named RemoveIndex as removesIndex name with name != addedName; the transliteration and real behavior agree on such inputs.
- 'RemoveIndex subclasses escape the isinstance test' -- refuted by direct subclass probe; isinstance is subclass-inclusive on both sides.

UNRELATED OBSERVATION (not a faithfulness defect, flagged for the panel): meta.json records G-EQ status='fail' with detail 'INCONCLUSIVE -- only 0 attacks (need >= 5); prepatch bug not reproduced; no positive control'. That is a missing-audit-coverage record for a different gate, not evidence of spec weakness or over-strength; per prior guidance an inconclusive/outage-shaped gate record must not be re-judged as a spec defect. My own run above supplies the prepatch reproduction and the positive control that G-EQ record says were absent, and both came out in the spec's favor.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Judged the projected consumer spec view (markers.spec_view, velvet flavor) for django__django-16819 against the SOLVER-VISIBLE problem_statement only (hints_text is empty here anyway).

PUBLIC BASELINE. problem_statement = "Reduce Add/RemoveIndex migration operations. ... We should reduce AddIndex/RemoveIndex operations when optimizing migration operations." This publicly supplies the words "reduce", "AddIndex", "RemoveIndex", "optimizing", and the pairing itself.

GOLD EDIT. models.py:864 adds AddIndex.reduce: `if isinstance(operation, RemoveIndex) and self.index.name == operation.name: return []` / `return super().reduce(operation, app_label)`.

### EVIDENCE (all run, not assumed):
1. same_spec byte-identity: markers.same_spec(Solution.lean, Solution_prepatch.lean, velvet) = True, and spec_signature(...).encode() byte-equal. Impl AND prove_correct bodies both elided; ELISION_IMPL/ELISION_PROOF present; the discriminating token `Reduction.cancel` does NOT appear inside the elided impl region.
2. leakage.screen(strict) = PASSED, 0 hard failures, 0 warnings — matches the recorded G-LEAK pass (mode=strict).
3. No gold line reproduced, incl. near-miss: computed normalized containment AND difflib ratio of every one of the 4 gold changed lines against every view line. No containment; best ratios only 0.43/0.51/0.41/0.52 (all against unrelated prose/`return (out : Reduction)`). `return[]` (normalized, len 8, above the >=8 threshold) absent.
4. No edit localization: "django", "migration", "models.py", "864", "861" -> 0 hits each. Patched file path and dotted module path absent. `isinstance`, `super`, `app_label`, and verbatim `RemoveIndex` all absent.
5. Patched symbols = {reduce, describe}. `describe` absent entirely. `reduce` survives ONLY because it is public in problem_statement — I confirmed the dependency empirically: re-running screen() with problem_statement blanked yields exactly one failure, "L2/L5: spec-view identifier 'reduceAddIndex' embeds patched repo symbol 'reduce'". With the real public text it is licensed, so not leakage beyond problem_statement.
6. No bug->fix narration: all 22 lean comment blocks scanned with _NARRATION_RE -> 0 hits. The diagnostic prose that DOES exist ("The bug: pre-patch ... had no reduce override", "redundant add/remove pair") lives only in refinement.md, which is auditor-only and not part of the consumer view; verified those phrases are absent from the view.
7. No hidden-test identity: idx_pony_weight_pink, Pony, weight, pink, test_add_remove_index, assertOptimizesTo, elidable -> all absent.

CLOSEST CANDIDATES, RESOLVED AGAINST THE REAL REPO (worktree @ 0b0998dc15):
- Axiom-comment line 11, "the inherited, UNCHANGED behaviour delegated to the base operation". Names no symbol (`super`/`Operation.reduce` absent) and, decisively, delegation-to-base is a PRE-EXISTING repo-wide idiom, not gold-specific knowledge: at base_commit there are already 5 other `reduce` overrides (models.py:32, 136, 445, 464, 1044) whose shape is exactly `if <guard>: return [...]` then `return super().reduce(operation, app_label)`, and base.py:129-139 documents the list-or-bool return. A solver reading the file sees this pattern with or without the patch, so the comment localizes nothing. It justifies why inheritedOutcome is a free input rather than narrating a mechanism.
- `cancel` <-> empty replacement / "the two operations annihilate and are dropped from the plan". This is abstract behavioral content, which a spec exists to state, and the public statement already says these operations should be reduced. It quotes no edit, no path, no symbol, no diagnosis.
- Name-only comparison (the gold guard checks index name but not model name). The view states this abstractly ("an index-removal whose target name equals the added index's name") without naming `self.index.name`/`operation.name` and without flagging the missing model check; the explicit remark about it is confined to auditor-only refinement.md. Specifying behavior at the abstract level is directive-6 compliant ("state the abstract desired behavior; never the edit or the diagnosis").

SCOPE NOTE (not a finding): the repo_symbol/repo_location localization (AddIndex.reduce, models.py:864) reaches the consumer through meta.json modeled_functions in the prompt's spec block. That is the harness's deliberate mode-1/2 localization aid, outside the spec view this gate judges, so it is not scored here.

CONCLUSION: the spec view reveals nothing about the gold edit beyond what problem_statement already makes public. NO-LEAKAGE. (Unrelated to this gate: meta.json records G-EQ and G-PANEL-1 as fail/INCONCLUSIVE with 0 attacks, so the bundle is not clean overall.)

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `refinement.md`, all of which ship in this bundle, so a reader can start there.