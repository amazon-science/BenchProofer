# P2 adversarial audit — django__django-15127

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1_prepatch.lean`, `atk_2_always.lean`, `atk_3_swap.lean`, `atk_4_baseonly.lean`, `atk_5_mergeswap.lean`, `atk_6_ovonly.lean`, `atk_7_diverge.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_8_echo.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good)

```diff
@@ -55,7 +55,7 @@
   ensures changedKey ≠ watchedKey → cached = cachedOld
   do
     -- impl-start
-    cached := if changedKey = watchedKey then recomputeTable base overrides else cached
+    cached := cached
     return
     -- impl-end
 
```

Attack 2 — `atk_2_always.lean` → rejected (same spec, does not verify — good)

```diff
@@ -55,7 +55,7 @@
   ensures changedKey ≠ watchedKey → cached = cachedOld
   do
     -- impl-start
-    cached := if changedKey = watchedKey then recomputeTable base overrides else cached
+    cached := recomputeTable base overrides
     return
     -- impl-end
 
```

Attack 3 — `atk_3_swap.lean` → rejected (same spec, does not verify — good)

```diff
@@ -55,7 +55,7 @@
   ensures changedKey ≠ watchedKey → cached = cachedOld
   do
     -- impl-start
-    cached := if changedKey = watchedKey then recomputeTable base overrides else cached
+    cached := if changedKey = watchedKey then cached else recomputeTable base overrides
     return
     -- impl-end
 
```

Attack 4 — `atk_4_baseonly.lean` → rejected (same spec, does not verify — good)

```diff
@@ -55,7 +55,7 @@
   ensures changedKey ≠ watchedKey → cached = cachedOld
   do
     -- impl-start
-    cached := if changedKey = watchedKey then recomputeTable base overrides else cached
+    cached := if changedKey = watchedKey then base else cached
     return
     -- impl-end
 
```

Attack 5 — `atk_5_mergeswap.lean` → rejected (same spec, does not verify — good)

```diff
@@ -55,7 +55,7 @@
   ensures changedKey ≠ watchedKey → cached = cachedOld
   do
     -- impl-start
-    cached := if changedKey = watchedKey then recomputeTable base overrides else cached
+    cached := if changedKey = watchedKey then recomputeTable overrides base else cached
     return
     -- impl-end
 
```

Attack 6 — `atk_6_ovonly.lean` → rejected (same spec, does not verify — good)

```diff
@@ -55,7 +55,7 @@
   ensures changedKey ≠ watchedKey → cached = cachedOld
   do
     -- impl-start
-    cached := if changedKey = watchedKey then recomputeTable base overrides else cached
+    cached := if changedKey = watchedKey then overrides else cached
     return
     -- impl-end
 
```

Attack 7 — `atk_7_diverge.lean` → rejected (same spec, does not verify — good)

```diff
@@ -55,7 +55,13 @@
   ensures changedKey ≠ watchedKey → cached = cachedOld
   do
     -- impl-start
-    cached := if changedKey = watchedKey then recomputeTable base overrides else cached
+    if changedKey = watchedKey then
+      let mut i : Nat := 1
+      while i > 0 do
+        i := i + 1
+      cached := recomputeTable base overrides
+    else
+      cached := cached
     return
     -- impl-end
 
```

Attack 8 — `atk_8_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -55,7 +55,7 @@
   ensures changedKey ≠ watchedKey → cached = cachedOld
   do
     -- impl-start
-    cached := if changedKey = watchedKey then recomputeTable base overrides else cached
+    cached := if changedKey ≠ watchedKey then cached else recomputeTable base overrides
     return
     -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

-- Total-correctness semantics: the change-notification handler must COMPLETE
-- (the real receiver is straight-line code that always terminates), so the
-- spec must also rule out diverging implementations — under partial
-- correctness a non-terminating body would vacuously satisfy every ensures.
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No consumed axioms: the only callee this operation invokes — the table
--  recompute — is modeled DEEPLY as `recomputeTable` in the `pure` region and
--  validated against the real callee by G-AX, an A-reference, not a consumed
--  axiom. See mapping.md §3 / refinement.md.)
-- axioms-end

-- pure-start
/- Lookup the value bound to `key` in an association list (first binding wins;
   the carriers come from real dictionaries, whose keys are unique). -/
def lookupEntry : List (Int × String) → Int → Option String
  | [],            _   => none
  | (k, v) :: rest, key => if k = key then some v else lookupEntry rest key

/- The recomputed lookup table: the override entries, overlaid on the base
   entries (an entry of `base` survives only when its key is not overridden).
   As a key→value mapping this is exactly "base defaults updated by overrides"
   (overrides win). Deep model of the unchanged community callee that derives
   the table; validated equal to that callee by G-AX (A-reference, mapping.md
   §3.1), so no axiom about it is consumed by the proof. -/
def recomputeTable (base overrides : List (Int × String)) : List (Int × String) :=
  overrides ++ base.filter (fun kv => (lookupEntry overrides kv.1).isNone)
-- pure-end

-- pre-conditions-start
-- (refreshCachedTable takes no `require`: it is total on every changed key.)
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- A change-notification handler that keeps a cached lookup table in sync with
   configuration. The handler watches one configuration key (`watchedKey`).
   When the key that just changed (`changedKey`) is the watched one, the cached
   table is recomputed from its base entries overlaid with the current override
   entries; for any other key, the cached table is left exactly as it was. -/
method refreshCachedTable
    (mut cached : List (Int × String))
    (changedKey : String) (watchedKey : String)
    (base : List (Int × String)) (overrides : List (Int × String))
    return (u : Unit)
  ensures changedKey = watchedKey → cached = recomputeTable base overrides
  ensures changedKey ≠ watchedKey → cached = cachedOld
  do
    -- impl-start
    cached := if changedKey = watchedKey then recomputeTable base overrides else cached
    return
    -- impl-end

prove_correct refreshCachedTable by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

ADVERSARIAL G-EQ (refinement fidelity) audit of velvet twin for django__django-15127. Working benchmark: swe_bench_verified (default). All 8 attacks pass same_spec==True (swebench_unified.markers.same_spec, velvet language) against the frozen Solution.lean; only the impl region (lines 58-59) was edited, axioms/pure/pre/post byte-identical.

SPEC SHAPE: refreshCachedTable has two ensures clauses that FULLY pin the post-state in both branches under total-correctness: (changedKey=watchedKey -> cached = recomputeTable base overrides) and (changedKey!=watchedKey -> cached = cachedOld). This is a functional, total spec covering all inputs; no consumed axioms (meta axioms:[]).

### VERIFICATION (bash scripts/lean_verify.sh <f>):
- pos_control.lean (gold impl)                 EXIT 0  VERIFIES (positive control)
- atk_1_prepatch.lean  (cached:=cached, no-op)  EXIT 1  fails ensures-1 (PREPATCH bug reproduced)
- atk_2_always.lean    (drop guard, recompute)  EXIT 1  fails ensures-2 frame (control-flow-effect)
- atk_3_swap.lean      (recompute on other keys)EXIT 1  fails
- atk_4_baseonly.lean  (recompute to base only) EXIT 1  fails (boundary/partial-domain)
- atk_5_mergeswap.lean (base wins vs overrides) EXIT 1  fails (wrong-merge / ungrounded-oracle echo)
- atk_6_ovonly.lean    (overrides only)         EXIT 1  fails (partial-domain)
- atk_7_diverge.lean   (while i>0 loop then recompute) EXIT 1 fails: 'Decreasing annotations are required in total correctness semantics' -> confirms the B2 termination-semantics repair genuinely rejects divergence
- atk_8_echo.lean      (changedKey != watchedKey then cached else recompute; behaviourally == gold) EXIT 0 VERIFIES

ONLY atk_8_echo (a behaviourally-identical rewrite of the gold conditional) verifies. Per protocol I materialized its faithful refined patch and ran it through the official harness (swebench_unified.harness.run_resolve on swe_bench_verified, image swebench/sweb.eval.x86_64.django_1776_django-15127:latest).

### RESOLVE RUNS (run_resolve, timeout 1800, retries 1, via docker):
- GOLD patch (harness positive control), run_id sbu-audit-eq-gold-15127 -> RESOLVED=True COMPLETED=True note='resolved'. Confirms harness works for this instance.
- atk_8_echo faithful patch, run_id sbu-audit-eq-echo2-15127 -> RESOLVED=True COMPLETED=True note='resolved'.
  IMPORTANT: my FIRST hand-written echo patch (run_id sbu-audit-eq-echo-15127) reported 'patch did not resolve in 2 attempts'. Root-caused as a PATCH-APPLICATION ARTIFACT: the hand-written hunk header was '@@ -1,7 +1,18 @@' but the `if setting != 'MESSAGE_TAGS': return` body is one line longer than gold's, so the correct count is +1,19. The corrected, git-generated patch (byte-diffed against apps.py at base_commit 9a6e2df3a8f01ea761529bec48e5a8dc0ea9575b, checked out) applies cleanly and RESOLVES. Not a spec break.

CONCLUSION on verify=>correct: The single verifying wrong-impl is a resolving ECHO of the gold (same observable behaviour), whose faithful patch RESOLVES under G-RESOLVE. Under the 2026-08-06 G-PANEL-1/G-EQ policy a resolving echo is NOT a weakness. No verifying impl produces a faithful patch that fails to resolve; every genuinely divergent impl (wrong branch/merge/domain/divergence) is rejected by lean verification. verify does NOT imply incorrect here.

REFINEMENT.MD LEG AUDIT: every leg is R / A-reference / I -- NO kind-3 (inexpressible-changed-op) and NO consumed axioms (matches meta axioms:[]). A-legs and their correspondence to real callees hold:
  * A4 recomputeTable (deep model, A-reference) == django.contrib.messages.utils.get_level_tags(): recomputeTable base overrides = overrides ++ base.filter(key not in overrides), which as a unique-keyed key->value mapping (first-binding-wins) is exactly {**DEFAULT_TAGS, **MESSAGE_TAGS} (overrides win). Validated by axiom_check.py (G-AX) over 7 boundary + 1e5 fuzz configs vs the REAL callee, seed 15127. Correspondence sound.
  * B1 / mapping §3.2 signal registration (A-reference plumbing): unchanged setting_changed.connect dispatch machinery, no consumed axiom, observable effect (receiver fires on setting change) exercised end-to-end by the F2P test 'test_override_settings_level_tags' under G-RESOLVE (gold resolves -> receiver is invoked). Correspondence sound.
  * A5 mut-frame (else cached, pinned by ensures-2 = cachedOld) faithfully models the receiver leaving base.LEVEL_TAGS untouched for non-MESSAGE_TAGS settings.

Verdict SOUND: >=5 (here 8) same-spec attacks encoded and verified; prepatch bug reproduced (atk_1 fails); a prior-pass-style divergence counterexample re-encoded (atk_7) and correctly rejected under total-correctness; the sole verifying wrong-impl's faithful patch was materialized and RESOLVES under the official harness. verify=>correct not falsified.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1_prepatch.lean`, `atk_2_always.lean`, `atk_3_swap.lean`, `atk_4_baseonly.lean`, `atk_5_mergeswap.lean`, `atk_6_ovonly.lean`, `atk_7_diverge.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_8_echo.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_always.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3_swap.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4_baseonly.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5_mergeswap.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6_ovonly.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7_diverge.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

-- Total-correctness semantics: the change-notification handler must COMPLETE
-- (the real receiver is straight-line code that always terminates), so the
-- spec must also rule out diverging implementations — under partial
-- correctness a non-terminating body would vacuously satisfy every ensures.
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No consumed axioms: the only callee this operation invokes — the table
--  recompute — is modeled DEEPLY as `recomputeTable` in the `pure` region and
--  validated against the real callee by G-AX, an A-reference, not a consumed
--  axiom. See mapping.md §3 / refinement.md.)
-- axioms-end

-- pure-start
/- Lookup the value bound to `key` in an association list (first binding wins;
   the carriers come from real dictionaries, whose keys are unique). -/
def lookupEntry : List (Int × String) → Int → Option String
  | [],            _   => none
  | (k, v) :: rest, key => if k = key then some v else lookupEntry rest key

/- The recomputed lookup table: the override entries, overlaid on the base
   entries (an entry of `base` survives only when its key is not overridden).
   As a key→value mapping this is exactly "base defaults updated by overrides"
   (overrides win). Deep model of the unchanged community callee that derives
   the table; validated equal to that callee by G-AX (A-reference, mapping.md
   §3.1), so no axiom about it is consumed by the proof. -/
def recomputeTable (base overrides : List (Int × String)) : List (Int × String) :=
  overrides ++ base.filter (fun kv => (lookupEntry overrides kv.1).isNone)
-- pure-end

-- pre-conditions-start
-- (refreshCachedTable takes no `require`: it is total on every changed key.)
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- A change-notification handler that keeps a cached lookup table in sync with
   configuration. The handler watches one configuration key (`watchedKey`).
   When the key that just changed (`changedKey`) is the watched one, the cached
   table is recomputed from its base entries overlaid with the current override
   entries; for any other key, the cached table is left exactly as it was. -/
method refreshCachedTable
    (mut cached : List (Int × String))
    (changedKey : String) (watchedKey : String)
    (base : List (Int × String)) (overrides : List (Int × String))
    return (u : Unit)
  ensures changedKey = watchedKey → cached = recomputeTable base overrides
  ensures changedKey ≠ watchedKey → cached = cachedOld
  do
    -- impl-start
    cached := if changedKey = watchedKey then recomputeTable base overrides else cached
    return
    -- impl-end

prove_correct refreshCachedTable by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

ADVERSARIAL G-EQ (refinement fidelity) audit of velvet twin for django__django-15127. Working benchmark: swe_bench_verified (default). All 8 attacks pass same_spec==True (swebench_unified.markers.same_spec, velvet language) against the frozen Solution.lean; only the impl region (lines 58-59) was edited, axioms/pure/pre/post byte-identical.

SPEC SHAPE: refreshCachedTable has two ensures clauses that FULLY pin the post-state in both branches under total-correctness: (changedKey=watchedKey -> cached = recomputeTable base overrides) and (changedKey!=watchedKey -> cached = cachedOld). This is a functional, total spec covering all inputs; no consumed axioms (meta axioms:[]).

### VERIFICATION (bash scripts/lean_verify.sh <f>):
- pos_control.lean (gold impl)                 EXIT 0  VERIFIES (positive control)
- atk_1_prepatch.lean  (cached:=cached, no-op)  EXIT 1  fails ensures-1 (PREPATCH bug reproduced)
- atk_2_always.lean    (drop guard, recompute)  EXIT 1  fails ensures-2 frame (control-flow-effect)
- atk_3_swap.lean      (recompute on other keys)EXIT 1  fails
- atk_4_baseonly.lean  (recompute to base only) EXIT 1  fails (boundary/partial-domain)
- atk_5_mergeswap.lean (base wins vs overrides) EXIT 1  fails (wrong-merge / ungrounded-oracle echo)
- atk_6_ovonly.lean    (overrides only)         EXIT 1  fails (partial-domain)
- atk_7_diverge.lean   (while i>0 loop then recompute) EXIT 1 fails: 'Decreasing annotations are required in total correctness semantics' -> confirms the B2 termination-semantics repair genuinely rejects divergence
- atk_8_echo.lean      (changedKey != watchedKey then cached else recompute; behaviourally == gold) EXIT 0 VERIFIES

ONLY atk_8_echo (a behaviourally-identical rewrite of the gold conditional) verifies. Per protocol I materialized its faithful refined patch and ran it through the official harness (swebench_unified.harness.run_resolve on swe_bench_verified, image swebench/sweb.eval.x86_64.django_1776_django-15127:latest).

### RESOLVE RUNS (run_resolve, timeout 1800, retries 1, via docker):
- GOLD patch (harness positive control), run_id sbu-audit-eq-gold-15127 -> RESOLVED=True COMPLETED=True note='resolved'. Confirms harness works for this instance.
- atk_8_echo faithful patch, run_id sbu-audit-eq-echo2-15127 -> RESOLVED=True COMPLETED=True note='resolved'.
  IMPORTANT: my FIRST hand-written echo patch (run_id sbu-audit-eq-echo-15127) reported 'patch did not resolve in 2 attempts'. Root-caused as a PATCH-APPLICATION ARTIFACT: the hand-written hunk header was '@@ -1,7 +1,18 @@' but the `if setting != 'MESSAGE_TAGS': return` body is one line longer than gold's, so the correct count is +1,19. The corrected, git-generated patch (byte-diffed against apps.py at base_commit 9a6e2df3a8f01ea761529bec48e5a8dc0ea9575b, checked out) applies cleanly and RESOLVES. Not a spec break.

CONCLUSION on verify=>correct: The single verifying wrong-impl is a resolving ECHO of the gold (same observable behaviour), whose faithful patch RESOLVES under G-RESOLVE. Under the 2026-08-06 G-PANEL-1/G-EQ policy a resolving echo is NOT a weakness. No verifying impl produces a faithful patch that fails to resolve; every genuinely divergent impl (wrong branch/merge/domain/divergence) is rejected by lean verification. verify does NOT imply incorrect here.

REFINEMENT.MD LEG AUDIT: every leg is R / A-reference / I -- NO kind-3 (inexpressible-changed-op) and NO consumed axioms (matches meta axioms:[]). A-legs and their correspondence to real callees hold:
  * A4 recomputeTable (deep model, A-reference) == django.contrib.messages.utils.get_level_tags(): recomputeTable base overrides = overrides ++ base.filter(key not in overrides), which as a unique-keyed key->value mapping (first-binding-wins) is exactly {**DEFAULT_TAGS, **MESSAGE_TAGS} (overrides win). Validated by axiom_check.py (G-AX) over 7 boundary + 1e5 fuzz configs vs the REAL callee, seed 15127. Correspondence sound.
  * B1 / mapping §3.2 signal registration (A-reference plumbing): unchanged setting_changed.connect dispatch machinery, no consumed axiom, observable effect (receiver fires on setting change) exercised end-to-end by the F2P test 'test_override_settings_level_tags' under G-RESOLVE (gold resolves -> receiver is invoked). Correspondence sound.
  * A5 mut-frame (else cached, pinned by ensures-2 = cachedOld) faithfully models the receiver leaving base.LEVEL_TAGS untouched for non-MESSAGE_TAGS settings.

Verdict SOUND: >=5 (here 8) same-spec attacks encoded and verified; prepatch bug reproduced (atk_1 fails); a prior-pass-style divergence counterexample re-encoded (atk_7) and correctly rejected under total-correctness; the sole verifying wrong-impl's faithful patch was materialized and RESOLVES under the official harness. verify=>correct not falsified.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) audit for django__django-15127 (velvet). Modeled function `refreshCachedTable` vs real receiver `update_level_tags(setting)` (apps.py, added by gold) which reads unchanged callee `get_level_tags()` (utils.py:5 @ base 9a6e2df3a8).

### Checks
1) same_spec(Solution.lean, Solution_prepatch.lean, velvet) == True (verified via swebench_unified.markers.same_spec with velvet backend). Spec region byte-identical between twins; only impl/proof regions differ.
2) Solution.lean verifies: scripts/lean_verify.sh exit 0. Prepatch (no-op skeleton) FAILS on the discriminating clause `changedKey = watchedKey -> cached = recomputeTable base overrides` (exit 1, unsolved goal cachedOld = recomputeTable...). Spec is discriminating, not vacuous.
3) Gold patch matches model exactly: real body sets base.LEVEL_TAGS = get_level_tags() iff setting=='MESSAGE_TAGS', else no mutation. Two ensures clauses (recompute on watched key; frame `cached = cachedOld` otherwise) capture this precisely — no branch is over-constrained.
4) Deep-model faithfulness (the only substantive drift surface): recomputeTable base overrides = overrides ++ base.filter(key not overridden), read as key->value mapping, must equal real get_level_tags() = {**DEFAULT_TAGS, **MESSAGE_TAGS} (overrides win). Empirically fuzzed 200,000 configs (seed 15127; empty dict, single/all-key remaps, extra non-default keys like 12/0/-5/100, empty-string values, value collisions) comparing dict(recomputeTable(DEFAULT_TAGS, MESSAGE_TAGS)) vs real merge => 0 mismatches. Overrides-first ordering + first-binding-wins lookupEntry correctly models later-** -spread-wins.
5) No `require` preconditions to narrow the input domain; total-correctness semantics is faithful (real receiver is straight-line, always terminates) and does not exclude any real behavior.

No input found where the modeled function disagrees with the real callee. Spec is neither too strong nor drifted. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (leakage.screen: hard_failures=[]); same_spec(Solution, Solution_prepatch)=True confirmed via swebench_unified.markers. Independent semantic review of the velvet spec view against the PUBLIC problem_statement (not hints_text):

(1) No patched repo symbol appears. Spec uses abstracted names refreshCachedTable/cached/changedKey/watchedKey/base/overrides instead of gold's update_level_tags/LEVEL_TAGS/setting/MESSAGE_TAGS/DEFAULT_TAGS/get_level_tags. No spec-view identifier embeds a patched def/class name.
(2) No patched file path (django/contrib/messages/apps.py) or dotted module path in the view.
(3) No verbatim gold-patch line; the discriminating line `base.LEVEL_TAGS = get_level_tags()` is not reproduced.
(4) No narration terms (bug/fix/patch/regression/...); comments describe abstract behavior only.

Behavioral content disclosed by the two `ensures` clauses (recompute the cached table when the watched key changes; leave it unchanged otherwise) is already public in the problem_statement, which states LEVEL_TAGS is not updated when MESSAGE_TAGS is changed via @override_settings and that Message.level_tag then returns an empty string. That is the specification of WHAT must hold — inherently allowed and required for any faithful spec. The dict-merge detail (overrides overlaid on base defaults) is expressed abstractly and names no repo symbol; the word 'override' is itself already public via '@override_settings' in the problem_statement.

Crucially, the gold-specific MECHANISM that is the fix's non-obvious insight — registering a setting_changed receiver via setting_changed.connect in MessagesConfig.ready — is the content that only hints_text reveals, and it is ENTIRELY ABSENT from the spec view (site B / the registration is deliberately not modeled in the spec regions; refinement.md §B). The spec discloses only the behavioral WHAT already public in the problem statement, not the hints-only HOW. Therefore the spec view leaks nothing beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `refinement.md`, which ships in this bundle, so a reader can start there.
