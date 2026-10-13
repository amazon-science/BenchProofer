# P2 adversarial audit — django__django-15741

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 21 admissible attacks re-run of 21 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 21 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 21 | `atk_1_prepatch.lean`, `atk_2_no_force_content.lean`, `atk_3_force_only_eager.lean`, `atk_4_partial_domain.lean`, `atk_5_boundary_const.lean`, `atk_6_echo_name.lean`, `atk_7_always_error.lean`, `atk_8_corrupt_content.lean`, `atk_9_swapped.lean`, `atk_10_double_resolve.lean`, `atk_11_match_payload.lean`, +10 more |

**Non-vacuity.** The positive control `ctrl_correct.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (21):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -74,11 +74,12 @@
   ensures out = Except.ok (resolveName (force nm))
   do
     -- impl-start
-    -- Force the name to its resolved content before using it as a lookup name,
-    -- then resolve. Forcing handles both the already-resolved and the deferred
-    -- carriers uniformly.
-    let key := force nm
-    return Except.ok (resolveName key)
+    -- PRE-PATCH: uses the name as a lookup name without forcing it; a deferred
+    -- name cannot be used in that state.
+    if nm.isDeferred then
+      return Except.error LookupErr.unresolvedName
+    else
+      return Except.ok (resolveName nm.content)
     -- impl-end
 end
 
```

Attack 2 — `atk_2_no_force_content.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -74,10 +74,9 @@
   ensures out = Except.ok (resolveName (force nm))
   do
     -- impl-start
-    -- Force the name to its resolved content before using it as a lookup name,
-    -- then resolve. Forcing handles both the already-resolved and the deferred
-    -- carriers uniformly.
-    let key := force nm
+    -- Use the name exactly as received: read its content off the carrier with
+    -- NO forcing step at all, and resolve that.
+    let key := nm.content
     return Except.ok (resolveName key)
     -- impl-end
 end
```

Attack 3 — `atk_3_force_only_eager.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -74,11 +74,12 @@
   ensures out = Except.ok (resolveName (force nm))
   do
     -- impl-start
-    -- Force the name to its resolved content before using it as a lookup name,
-    -- then resolve. Forcing handles both the already-resolved and the deferred
-    -- carriers uniformly.
-    let key := force nm
-    return Except.ok (resolveName key)
+    -- Dispatch on the carrier: force only the already-resolved (eager) carrier;
+    -- for the deferred carrier use the name as received, unforced.
+    if nm.isDeferred then
+      return Except.ok (resolveName nm.content)
+    else
+      return Except.ok (resolveName (force nm))
     -- impl-end
 end
 
```

Attack 4 — `atk_4_partial_domain.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -74,11 +74,10 @@
   ensures out = Except.ok (resolveName (force nm))
   do
     -- impl-start
-    -- Force the name to its resolved content before using it as a lookup name,
-    -- then resolve. Forcing handles both the already-resolved and the deferred
-    -- carriers uniformly.
-    let key := force nm
-    return Except.ok (resolveName key)
+    if nm.isDeferred then
+      return Except.ok (resolveName [])
+    else
+      return Except.ok (resolveName (force nm))
     -- impl-end
 end
 
```

Attack 5 — `atk_5_boundary_const.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -74,11 +74,7 @@
   ensures out = Except.ok (resolveName (force nm))
   do
     -- impl-start
-    -- Force the name to its resolved content before using it as a lookup name,
-    -- then resolve. Forcing handles both the already-resolved and the deferred
-    -- carriers uniformly.
-    let key := force nm
-    return Except.ok (resolveName key)
+    return Except.ok []
     -- impl-end
 end
 
```

Attack 6 — `atk_6_echo_name.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -74,11 +74,8 @@
   ensures out = Except.ok (resolveName (force nm))
   do
     -- impl-start
-    -- Force the name to its resolved content before using it as a lookup name,
-    -- then resolve. Forcing handles both the already-resolved and the deferred
-    -- carriers uniformly.
     let key := force nm
-    return Except.ok (resolveName key)
+    return Except.ok key
     -- impl-end
 end
 
```

Attack 7 — `atk_7_always_error.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -74,11 +74,7 @@
   ensures out = Except.ok (resolveName (force nm))
   do
     -- impl-start
-    -- Force the name to its resolved content before using it as a lookup name,
-    -- then resolve. Forcing handles both the already-resolved and the deferred
-    -- carriers uniformly.
-    let key := force nm
-    return Except.ok (resolveName key)
+    return Except.error LookupErr.unresolvedName
     -- impl-end
 end
 
```

Attack 8 — `atk_8_corrupt_content.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -74,10 +74,7 @@
   ensures out = Except.ok (resolveName (force nm))
   do
     -- impl-start
-    -- Force the name to its resolved content before using it as a lookup name,
-    -- then resolve. Forcing handles both the already-resolved and the deferred
-    -- carriers uniformly.
-    let key := force nm
+    let key := force nm ++ ['x']
     return Except.ok (resolveName key)
     -- impl-end
 end
```

Attack 9 — `atk_9_swapped.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -74,11 +74,10 @@
   ensures out = Except.ok (resolveName (force nm))
   do
     -- impl-start
-    -- Force the name to its resolved content before using it as a lookup name,
-    -- then resolve. Forcing handles both the already-resolved and the deferred
-    -- carriers uniformly.
-    let key := force nm
-    return Except.ok (resolveName key)
+    if nm.isDeferred then
+      return Except.ok (resolveName (force nm))
+    else
+      return Except.error LookupErr.unresolvedName
     -- impl-end
 end
 
```

Attack 10 — `atk_10_double_resolve.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -74,11 +74,8 @@
   ensures out = Except.ok (resolveName (force nm))
   do
     -- impl-start
-    -- Force the name to its resolved content before using it as a lookup name,
-    -- then resolve. Forcing handles both the already-resolved and the deferred
-    -- carriers uniformly.
     let key := force nm
-    return Except.ok (resolveName key)
+    return Except.ok (resolveName (resolveName key))
     -- impl-end
 end
 
```

Attack 11 — `atk_11_match_payload.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -74,11 +74,9 @@
   ensures out = Except.ok (resolveName (force nm))
   do
     -- impl-start
-    -- Force the name to its resolved content before using it as a lookup name,
-    -- then resolve. Forcing handles both the already-resolved and the deferred
-    -- carriers uniformly.
-    let key := force nm
-    return Except.ok (resolveName key)
+    match nm with
+    | .eager s => return Except.ok (resolveName s)
+    | .deferred s => return Except.ok (resolveName s)
     -- impl-end
 end
 
```

Attack 12 — `atk_12b_diverge.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -74,10 +74,14 @@
   ensures out = Except.ok (resolveName (force nm))
   do
     -- impl-start
-    -- Force the name to its resolved content before using it as a lookup name,
-    -- then resolve. Forcing handles both the already-resolved and the deferred
-    -- carriers uniformly.
     let key := force nm
+    let mut i : Nat := 1
+    while i > 0
+      invariant i > 0
+      done_with i = 0
+      decreasing i
+    do
+      i := i + 1
     return Except.ok (resolveName key)
     -- impl-end
 end
```

Attack 13 — `atk_13_resolve_bit.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -74,10 +74,7 @@
   ensures out = Except.ok (resolveName (force nm))
   do
     -- impl-start
-    -- Force the name to its resolved content before using it as a lookup name,
-    -- then resolve. Forcing handles both the already-resolved and the deferred
-    -- carriers uniformly.
-    let key := force nm
+    let key : List Char := if nm.isDeferred then force nm else []
     return Except.ok (resolveName key)
     -- impl-end
 end
```

Attack 14 — `atk_14_truncate.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -74,10 +74,7 @@
   ensures out = Except.ok (resolveName (force nm))
   do
     -- impl-start
-    -- Force the name to its resolved content before using it as a lookup name,
-    -- then resolve. Forcing handles both the already-resolved and the deferred
-    -- carriers uniformly.
-    let key := force nm
+    let key := (force nm).dropLast
     return Except.ok (resolveName key)
     -- impl-end
 end
```

Attack 15 — `atk_15_empty_special.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -74,11 +74,11 @@
   ensures out = Except.ok (resolveName (force nm))
   do
     -- impl-start
-    -- Force the name to its resolved content before using it as a lookup name,
-    -- then resolve. Forcing handles both the already-resolved and the deferred
-    -- carriers uniformly.
     let key := force nm
-    return Except.ok (resolveName key)
+    if key.isEmpty then
+      return Except.error LookupErr.unresolvedName
+    else
+      return Except.ok (resolveName key)
     -- impl-end
 end
 
```

Attack 16 — `atk_16_reverse.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -74,10 +74,7 @@
   ensures out = Except.ok (resolveName (force nm))
   do
     -- impl-start
-    -- Force the name to its resolved content before using it as a lookup name,
-    -- then resolve. Forcing handles both the already-resolved and the deferred
-    -- carriers uniformly.
-    let key := force nm
+    let key := (force nm).reverse
     return Except.ok (resolveName key)
     -- impl-end
 end
```

Attack 17 — `atk_17_loop_drain.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -74,10 +74,13 @@
   ensures out = Except.ok (resolveName (force nm))
   do
     -- impl-start
-    -- Force the name to its resolved content before using it as a lookup name,
-    -- then resolve. Forcing handles both the already-resolved and the deferred
-    -- carriers uniformly.
-    let key := force nm
+    let mut key := force nm
+    while key.length > 0
+      invariant True
+      done_with key.length = 0
+      decreasing key.length
+    do
+      key := key.tail
     return Except.ok (resolveName key)
     -- impl-end
 end
```

Attack 18 — `atk_18_len_boundary.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -74,11 +74,11 @@
   ensures out = Except.ok (resolveName (force nm))
   do
     -- impl-start
-    -- Force the name to its resolved content before using it as a lookup name,
-    -- then resolve. Forcing handles both the already-resolved and the deferred
-    -- carriers uniformly.
     let key := force nm
-    return Except.ok (resolveName key)
+    if key.length <= 1 then
+      return Except.ok (resolveName key)
+    else
+      return Except.ok (resolveName [key.headD 'a'])
     -- impl-end
 end
 
```

Attack 19 — `atk_19_reshape_eager_roundtrip.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -74,10 +74,7 @@
   ensures out = Except.ok (resolveName (force nm))
   do
     -- impl-start
-    -- Force the name to its resolved content before using it as a lookup name,
-    -- then resolve. Forcing handles both the already-resolved and the deferred
-    -- carriers uniformly.
-    let key := force nm
+    let key := force (Name.eager (force nm))
     return Except.ok (resolveName key)
     -- impl-end
 end
```

Attack 20 — `atk_20_reshape_deferred_roundtrip.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -74,10 +74,7 @@
   ensures out = Except.ok (resolveName (force nm))
   do
     -- impl-start
-    -- Force the name to its resolved content before using it as a lookup name,
-    -- then resolve. Forcing handles both the already-resolved and the deferred
-    -- carriers uniformly.
-    let key := force nm
+    let key := force (Name.deferred (force nm))
     return Except.ok (resolveName key)
     -- impl-end
 end
```

Attack 21 — `atk_21_force_discarded.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -74,10 +74,8 @@
   ensures out = Except.ok (resolveName (force nm))
   do
     -- impl-start
-    -- Force the name to its resolved content before using it as a lookup name,
-    -- then resolve. Forcing handles both the already-resolved and the deferred
-    -- carriers uniformly.
-    let key := force nm
+    let _unused := force nm
+    let key := nm.content
     return Except.ok (resolveName key)
     -- impl-end
 end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `ctrl_correct.lean` (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -74,11 +74,14 @@
   ensures out = Except.ok (resolveName (force nm))
   do
     -- impl-start
-    -- Force the name to its resolved content before using it as a lookup name,
-    -- then resolve. Forcing handles both the already-resolved and the deferred
-    -- carriers uniformly.
-    let key := force nm
-    return Except.ok (resolveName key)
+    -- Correct, but restructured: dispatch on the carrier and force in BOTH
+    -- branches before resolving.
+    if nm.isDeferred then
+      let key := force nm
+      return Except.ok (resolveName key)
+    else
+      let key := force nm
+      return Except.ok (resolveName key)
     -- impl-end
 end
 
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity (A-leg focused) audit, django__django-15741 (velvet).

SPEC SHAPE (why the A-leg cannot be smuggled). Postcondition is the EXACT pinned equation `out = Except.ok (resolveName (force nm))`. `resolveName` is an opaque A-consumed axiom (no body, no equations, pins NO value), so the ONLY provable return term is literally `resolveName (force nm)`. There is no constant, no answer-key, and no echo an impl can produce that `loom_solve` can equate to it. The single axiom covers UNCHANGED downstream machinery; the operation the patch ADDS (the `str()` coercion) is modeled as the total R-function `force`, not behind an axiom -- so the A-leg has no way to carry the fix.

**SAME_SPEC:** all 22 files (21 attacks + positive control) were built by copying Solution.lean and editing ONLY the impl region; axioms/pure/pre/post left byte-identical. Command: `PYTHONPATH=src python3 -c "from swebench_unified.markers import same_spec; from swebench_unified.backends import get_backend; b=get_backend('velvet'); ..."` -> True for EVERY file (verified twice, incl. a final sweep after all builds, so no /tmp clobber).
ADMISSIBILITY: `swebench_unified.variant_scope.unsound_evasions(frozen, attack, velvet.language)` -> ADMISSIBLE (empty evasion list) for all 22. No new axiom, no sorry/admit/native_decide, `prove_correct lookupValue` retained in every file.

VERIFY (command per file: `bash scripts/lean_verify.sh <abs path> 300`, run CONCURRENTLY in background batches of 4; exit 0=verifies, 1=error, 3=sorry, 124=timeout). No timeouts, no infra errors -- every result is a real measurement.
- ctrl_correct.lean exit=0, EMPTY output -> positive control VERIFIES (spec satisfiable + non-vacuous). It is structurally different from the shipped impl (branches on `nm.isDeferred`, forces in BOTH branches), so the pass is not a copy of the frozen body.
- atk_1_prepatch (PREPATCH BUG: deferred->error, eager->ok, name used unforced) exit=1; goal `Except.error LookupErr.unresolvedName = Except.ok (resolveName (force nm))` under `nm.isDeferred = true` -> PREPATCH REPRODUCED, and it fails for exactly the right reason (the TypeError-on-lazy branch).
- atk_2_no_force_content (skip forcing entirely: `let key := nm.content`) exit=1; goal `Except.ok (resolveName nm.content) = Except.ok (resolveName (force nm))`. NOTABLE: `force nm` is *definitionally* `nm.content`, and the frozen spec view exports `Name.content`, so this was my strongest a-priori vector -- an impl that never coerces at all. loom_solve does NOT unfold `force`, so the spec rejects it. The bit the issue turns on is genuinely load-bearing.
- atk_3_force_only_eager (coerce only where it is useless; deferred carrier left unforced) exit=1, same residual goal on the `isDeferred=true` branch.
- atk_21_force_discarded (compute `force nm`, DISCARD it, resolve `nm.content` -- pre-patch semantics dressed as a coercion) exit=1.
- atk_11_match_payload (pattern-match the payload out of both constructors, never call force) exit=1; residual goals for both `nm = Name.eager i` and `nm = Name.deferred i`.
- atk_4_partial_domain (deferred -> `resolveName []`, eager correct) exit=1.  atk_18_len_boundary (correct for len<=1, resolves only the head otherwise -- covers the real 'DATE_FORMAT' case) exit=1.  atk_15_empty_special (correct except errors on the empty name) exit=1.
- atk_5_boundary_const (`Except.ok []`) exit=1.  atk_7_always_error exit=1.  atk_9_swapped (eager->error, deferred->ok) exit=1.
- atk_6_echo_name (ungrounded echo `Except.ok (force nm)`) exit=1.  atk_13_resolve_bit (key chosen off the isDeferred BIT: `if nm.isDeferred then force nm else []`) exit=1.
- atk_8_corrupt_content (`force nm ++ ['x']`) exit=1.  atk_14_truncate (`.dropLast`) exit=1.  atk_16_reverse (`.reverse` -- agrees on palindromes/empty, wrong in general) exit=1.  atk_10_double_resolve (`resolveName (resolveName key)`) exit=1 (opaque axiom will not collapse).
- atk_12b_diverge (CONTROL-FLOW EFFECT: forces and resolves CORRECTLY but the loop `while i > 0 ... i := i + 1` never terminates) exit=1; residual `decreasing_1` goal `i + 1 < i` -> the `termination "total"` setting really does reject divergence, so a non-terminating rival cannot pass on the correct return value alone.
- atk_17_loop_drain (loop drains the forced key to [], resolves the drained key) exit=1.
- EQUAL-VALUE RESHAPES (the sharpest remaining G-EQ class: a term whose faithful refinement is a DIFFERENT Python op) atk_19_reshape_eager_roundtrip (`force (Name.eager (force nm))`) exit=1 and atk_20_reshape_deferred_roundtrip (`force (Name.deferred (force nm))`) exit=1 -- loom_solve does not even discharge these value-equal roundtrips, so the spec is tighter than the refinement map needs.
Every one of the 21 rejections carries an `unsolved goals` residual (verified by grepping all logs), i.e. the SPEC rejected it -- none died of a syntax/elaboration error. One earlier draft, atk_12_diverge.lean, DID die of `failed to synthesize OfNat (Option Nat)`; that is a malformed attack and NOT evidence, so it is deliberately EXCLUDED from the submitted list and replaced by the well-typed atk_12b_diverge.

PROTOCOL STEP 2: ZERO wrong impls verify, so the 'materialize the faithful refined patch and run it through run_resolve' obligation has no candidates and is vacuously satisfied; patches={}. Rather than stop at a vacuous pass, I spent two REAL harness runs proving the resolve oracle actually discriminates on the leg refinement.md declares load-bearing (A2, the coercion). Commands (concurrent, under `docker`, PYTHONPATH=src, harness.run_resolve):
- GOLD, patch_gold.diff (byte copy of the instance patch.diff): {completed: true, resolved: TRUE, note: 'resolved'}.
- NON-COERCING, patch_nocoerce.diff = the faithful refined patch of the atk_1/atk_2/atk_21 class: identical to gold EXCEPT the added line is a comment instead of `format_type = str(format_type)`, i.e. exactly the impl that reads the name without forcing it: {completed: true, resolved: FALSE, note: 'patch did not resolve in 3 attempts (consistent -- not flaky)'}.
So the class of impls the spec REJECTS is precisely the class the harness scores as NOT resolved, and the class it accepts is the class that resolves. verify=>correct is corroborated positively, not merely by absence of a counterexample. F2P lane confirms the correspondence: `test_get_format_lazy_format` (`get_format(gettext_lazy("DATE_FORMAT")) == "N j, Y"`) and `test_date_lazy` (`{{ t|date:_("H:i") }}`) -- both feed a LAZY format_type, exactly the `Name.deferred` carrier.

REFINEMENT.MD AUDIT (A legs + correspondence; R/I legs are mechanically G-CONF's job and are legitimately conf_skip=true here). 4 legs, all typed: A1=R (Name eager/deferred <-> concrete str / lazy proxy), A2=R (`let key := force nm` <-> the added `format_type = str(format_type)`), A3=A-consumed (`resolveName` <-> the UNCHANGED downstream resolution), A4=R (`Except.ok` <-> normal return). NO kind-3 leg. meta.json agrees and is internally consistent: axioms=[{resolveName, A-consumed}], deep_model_references=[], additional_change_sites=[], conf_skip=true -- so there are no A-reference legs to check and no second change site to miss.

A3 CORRESPONDENCE CHECKED AGAINST THE REAL CALLEE at base_commit 8c0886b (worktree, django/utils/formats.py:100-145): the code refinement.md cites as the callee (cache_key tuple, `_format_cache` hit/miss, `getattr(module, format_type, None)` over the format modules, the `FORMAT_SETTINGS`/`getattr(settings, format_type)` fallback) is byte-for-byte unchanged by patch.diff -- the diff inserts ONE line strictly ABOVE `cache_key = (format_type, lang)` and touches nothing else. So the axiom does model an unchanged callee, and the consumed property (resolution is a function of the resolved content alone) is the weakest one the postcondition needs. The `additional_change_sites=[]` claim also holds: the diff has exactly one hunk in one file.

Verified independently that patch.diff is the gold patch verbatim (G-RESOLVE re-run above). A-leg cannot smuggle the fix: the discriminating behavior (a deferred name must be forced, and forcing always succeeds) sits in the R-function `force`, whose totality is a Lean fact (`force (deferred s) = s`), not an assumption -- and mapping.md 3.1 is explicit that G-AX runs at base_commit on CONCRETE strings only and never feeds a lazy proxy through the CHANGED function, so the axiom probe cannot launder the patched behavior. That is the correct boundary.

ADVISORY (not a G-EQ break, no verdict weight, routed for information only): `resolveName : List Char -> List Char` types the downstream result as a character list, whereas the real `get_format` can return a list/tuple on the `ISO_INPUT_FORMATS` branch and can return the format_type itself when it is not in FORMAT_SETTINGS. Because the postcondition pins NO value (directive 7, weakest contract) this cannot create a verifying-but-wrong impl -- the return-type abstraction is quantified away -- so it is a modeling-boundary observation for G-PANEL-2 (faithfulness), not a spec-strength hole.

**VERDICT:** SOUND (advisory; runner re-runs). 21 distinct, admissible, same-spec wrong impls spanning partial-domain, boundary, control-flow-effect (incl. genuine non-termination), ungrounded-oracle echo, content corruption/permutation/truncation, carrier swap, double-transform, no-coercion-at-all, and equal-value reshape -- ALL rejected with real residual goals; positive control verifies clean; prepatch bug reproduced and fails on exactly its buggy branch; oracle discrimination confirmed by two completed harness runs (gold resolves, non-coercing does not). No verifying wrong impl exists to break verify=>correct, so no faithful refined patch needed materializing.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 21 admissible attacks re-run of 21 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 21 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 21 | `atk_1_prepatch.lean`, `atk_2_no_force_content.lean`, `atk_3_force_only_eager.lean`, `atk_4_partial_domain.lean`, `atk_5_boundary_const.lean`, `atk_6_echo_name.lean`, `atk_7_always_error.lean`, `atk_8_corrupt_content.lean`, `atk_9_swapped.lean`, `atk_10_double_resolve.lean`, `atk_11_match_payload.lean`, +10 more |

**Non-vacuity.** The positive control `ctrl_correct.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (21):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 21 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_no_force_content.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3_force_only_eager.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4_partial_domain.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5_boundary_const.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6_echo_name.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7_always_error.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8_corrupt_content.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9_swapped.lean` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10_double_resolve.lean` → rejected (same spec, does not verify — good)

Attack 11 — `atk_11_match_payload.lean` → rejected (same spec, does not verify — good)

Attack 12 — `atk_12b_diverge.lean` → rejected (same spec, does not verify — good)

Attack 13 — `atk_13_resolve_bit.lean` → rejected (same spec, does not verify — good)

Attack 14 — `atk_14_truncate.lean` → rejected (same spec, does not verify — good)

Attack 15 — `atk_15_empty_special.lean` → rejected (same spec, does not verify — good)

Attack 16 — `atk_16_reverse.lean` → rejected (same spec, does not verify — good)

Attack 17 — `atk_17_loop_drain.lean` → rejected (same spec, does not verify — good)

Attack 18 — `atk_18_len_boundary.lean` → rejected (same spec, does not verify — good)

Attack 19 — `atk_19_reshape_eager_roundtrip.lean` → rejected (same spec, does not verify — good)

Attack 20 — `atk_20_reshape_deferred_roundtrip.lean` → rejected (same spec, does not verify — good)

Attack 21 — `atk_21_force_discarded.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `ctrl_correct.lean` (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -74,11 +74,14 @@
   ensures out = Except.ok (resolveName (force nm))
   do
     -- impl-start
-    -- Force the name to its resolved content before using it as a lookup name,
-    -- then resolve. Forcing handles both the already-resolved and the deferred
-    -- carriers uniformly.
-    let key := force nm
-    return Except.ok (resolveName key)
+    -- Correct, but restructured: dispatch on the carrier and force in BOTH
+    -- branches before resolving.
+    if nm.isDeferred then
+      let key := force nm
+      return Except.ok (resolveName key)
+    else
+      let key := force nm
+      return Except.ok (resolveName key)
     -- impl-end
 end
 
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity (A-leg focused) audit, django__django-15741 (velvet).

SPEC SHAPE (why the A-leg cannot be smuggled). Postcondition is the EXACT pinned equation `out = Except.ok (resolveName (force nm))`. `resolveName` is an opaque A-consumed axiom (no body, no equations, pins NO value), so the ONLY provable return term is literally `resolveName (force nm)`. There is no constant, no answer-key, and no echo an impl can produce that `loom_solve` can equate to it. The single axiom covers UNCHANGED downstream machinery; the operation the patch ADDS (the `str()` coercion) is modeled as the total R-function `force`, not behind an axiom -- so the A-leg has no way to carry the fix.

**SAME_SPEC:** all 22 files (21 attacks + positive control) were built by copying Solution.lean and editing ONLY the impl region; axioms/pure/pre/post left byte-identical. Command: `PYTHONPATH=src python3 -c "from swebench_unified.markers import same_spec; from swebench_unified.backends import get_backend; b=get_backend('velvet'); ..."` -> True for EVERY file (verified twice, incl. a final sweep after all builds, so no /tmp clobber).
ADMISSIBILITY: `swebench_unified.variant_scope.unsound_evasions(frozen, attack, velvet.language)` -> ADMISSIBLE (empty evasion list) for all 22. No new axiom, no sorry/admit/native_decide, `prove_correct lookupValue` retained in every file.

VERIFY (command per file: `bash scripts/lean_verify.sh <abs path> 300`, run CONCURRENTLY in background batches of 4; exit 0=verifies, 1=error, 3=sorry, 124=timeout). No timeouts, no infra errors -- every result is a real measurement.
- ctrl_correct.lean exit=0, EMPTY output -> positive control VERIFIES (spec satisfiable + non-vacuous). It is structurally different from the shipped impl (branches on `nm.isDeferred`, forces in BOTH branches), so the pass is not a copy of the frozen body.
- atk_1_prepatch (PREPATCH BUG: deferred->error, eager->ok, name used unforced) exit=1; goal `Except.error LookupErr.unresolvedName = Except.ok (resolveName (force nm))` under `nm.isDeferred = true` -> PREPATCH REPRODUCED, and it fails for exactly the right reason (the TypeError-on-lazy branch).
- atk_2_no_force_content (skip forcing entirely: `let key := nm.content`) exit=1; goal `Except.ok (resolveName nm.content) = Except.ok (resolveName (force nm))`. NOTABLE: `force nm` is *definitionally* `nm.content`, and the frozen spec view exports `Name.content`, so this was my strongest a-priori vector -- an impl that never coerces at all. loom_solve does NOT unfold `force`, so the spec rejects it. The bit the issue turns on is genuinely load-bearing.
- atk_3_force_only_eager (coerce only where it is useless; deferred carrier left unforced) exit=1, same residual goal on the `isDeferred=true` branch.
- atk_21_force_discarded (compute `force nm`, DISCARD it, resolve `nm.content` -- pre-patch semantics dressed as a coercion) exit=1.
- atk_11_match_payload (pattern-match the payload out of both constructors, never call force) exit=1; residual goals for both `nm = Name.eager i` and `nm = Name.deferred i`.
- atk_4_partial_domain (deferred -> `resolveName []`, eager correct) exit=1.  atk_18_len_boundary (correct for len<=1, resolves only the head otherwise -- covers the real 'DATE_FORMAT' case) exit=1.  atk_15_empty_special (correct except errors on the empty name) exit=1.
- atk_5_boundary_const (`Except.ok []`) exit=1.  atk_7_always_error exit=1.  atk_9_swapped (eager->error, deferred->ok) exit=1.
- atk_6_echo_name (ungrounded echo `Except.ok (force nm)`) exit=1.  atk_13_resolve_bit (key chosen off the isDeferred BIT: `if nm.isDeferred then force nm else []`) exit=1.
- atk_8_corrupt_content (`force nm ++ ['x']`) exit=1.  atk_14_truncate (`.dropLast`) exit=1.  atk_16_reverse (`.reverse` -- agrees on palindromes/empty, wrong in general) exit=1.  atk_10_double_resolve (`resolveName (resolveName key)`) exit=1 (opaque axiom will not collapse).
- atk_12b_diverge (CONTROL-FLOW EFFECT: forces and resolves CORRECTLY but the loop `while i > 0 ... i := i + 1` never terminates) exit=1; residual `decreasing_1` goal `i + 1 < i` -> the `termination "total"` setting really does reject divergence, so a non-terminating rival cannot pass on the correct return value alone.
- atk_17_loop_drain (loop drains the forced key to [], resolves the drained key) exit=1.
- EQUAL-VALUE RESHAPES (the sharpest remaining G-EQ class: a term whose faithful refinement is a DIFFERENT Python op) atk_19_reshape_eager_roundtrip (`force (Name.eager (force nm))`) exit=1 and atk_20_reshape_deferred_roundtrip (`force (Name.deferred (force nm))`) exit=1 -- loom_solve does not even discharge these value-equal roundtrips, so the spec is tighter than the refinement map needs.
Every one of the 21 rejections carries an `unsolved goals` residual (verified by grepping all logs), i.e. the SPEC rejected it -- none died of a syntax/elaboration error. One earlier draft, atk_12_diverge.lean, DID die of `failed to synthesize OfNat (Option Nat)`; that is a malformed attack and NOT evidence, so it is deliberately EXCLUDED from the submitted list and replaced by the well-typed atk_12b_diverge.

PROTOCOL STEP 2: ZERO wrong impls verify, so the 'materialize the faithful refined patch and run it through run_resolve' obligation has no candidates and is vacuously satisfied; patches={}. Rather than stop at a vacuous pass, I spent two REAL harness runs proving the resolve oracle actually discriminates on the leg refinement.md declares load-bearing (A2, the coercion). Commands (concurrent, under `docker`, PYTHONPATH=src, harness.run_resolve):
- GOLD, patch_gold.diff (byte copy of the instance patch.diff): {completed: true, resolved: TRUE, note: 'resolved'}.
- NON-COERCING, patch_nocoerce.diff = the faithful refined patch of the atk_1/atk_2/atk_21 class: identical to gold EXCEPT the added line is a comment instead of `format_type = str(format_type)`, i.e. exactly the impl that reads the name without forcing it: {completed: true, resolved: FALSE, note: 'patch did not resolve in 3 attempts (consistent -- not flaky)'}.
So the class of impls the spec REJECTS is precisely the class the harness scores as NOT resolved, and the class it accepts is the class that resolves. verify=>correct is corroborated positively, not merely by absence of a counterexample. F2P lane confirms the correspondence: `test_get_format_lazy_format` (`get_format(gettext_lazy("DATE_FORMAT")) == "N j, Y"`) and `test_date_lazy` (`{{ t|date:_("H:i") }}`) -- both feed a LAZY format_type, exactly the `Name.deferred` carrier.

REFINEMENT.MD AUDIT (A legs + correspondence; R/I legs are mechanically G-CONF's job and are legitimately conf_skip=true here). 4 legs, all typed: A1=R (Name eager/deferred <-> concrete str / lazy proxy), A2=R (`let key := force nm` <-> the added `format_type = str(format_type)`), A3=A-consumed (`resolveName` <-> the UNCHANGED downstream resolution), A4=R (`Except.ok` <-> normal return). NO kind-3 leg. meta.json agrees and is internally consistent: axioms=[{resolveName, A-consumed}], deep_model_references=[], additional_change_sites=[], conf_skip=true -- so there are no A-reference legs to check and no second change site to miss.

A3 CORRESPONDENCE CHECKED AGAINST THE REAL CALLEE at base_commit 8c0886b (worktree, django/utils/formats.py:100-145): the code refinement.md cites as the callee (cache_key tuple, `_format_cache` hit/miss, `getattr(module, format_type, None)` over the format modules, the `FORMAT_SETTINGS`/`getattr(settings, format_type)` fallback) is byte-for-byte unchanged by patch.diff -- the diff inserts ONE line strictly ABOVE `cache_key = (format_type, lang)` and touches nothing else. So the axiom does model an unchanged callee, and the consumed property (resolution is a function of the resolved content alone) is the weakest one the postcondition needs. The `additional_change_sites=[]` claim also holds: the diff has exactly one hunk in one file.

Verified independently that patch.diff is the gold patch verbatim (G-RESOLVE re-run above). A-leg cannot smuggle the fix: the discriminating behavior (a deferred name must be forced, and forcing always succeeds) sits in the R-function `force`, whose totality is a Lean fact (`force (deferred s) = s`), not an assumption -- and mapping.md 3.1 is explicit that G-AX runs at base_commit on CONCRETE strings only and never feeds a lazy proxy through the CHANGED function, so the axiom probe cannot launder the patched behavior. That is the correct boundary.

ADVISORY (not a G-EQ break, no verdict weight, routed for information only): `resolveName : List Char -> List Char` types the downstream result as a character list, whereas the real `get_format` can return a list/tuple on the `ISO_INPUT_FORMATS` branch and can return the format_type itself when it is not in FORMAT_SETTINGS. Because the postcondition pins NO value (directive 7, weakest contract) this cannot create a verifying-but-wrong impl -- the return-type abstraction is quantified away -- so it is a modeling-boundary observation for G-PANEL-2 (faithfulness), not a spec-strength hole.

**VERDICT:** SOUND (advisory; runner re-runs). 21 distinct, admissible, same-spec wrong impls spanning partial-domain, boundary, control-flow-effect (incl. genuine non-termination), ungrounded-oracle echo, content corruption/permutation/truncation, carrier swap, double-transform, no-coercion-at-all, and equal-value reshape -- ALL rejected with real residual goals; positive control verifies clean; prepatch bug reproduced and fails on exactly its buggy branch; oracle discrimination confirmed by two completed harness runs (gold resolves, non-coercing does not). No verifying wrong impl exists to break verify=>correct, so no faithful refined patch needed materializing.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

**REFERENCE DISCIPLINE:** modeled function `lookupValue` compared against base_commit 8c0886b068 WITH patch.diff APPLIED (fresh worktree; asserted 'format_type = str(format_type)' present at formats.py:116 and django.utils.formats.`__file__` resolved into that worktree). A stale PYTHONPATH () initially made my first probe import a foreign django and report 6 fake divergences on ''/'NOPE'/'`__doc__`'/'a b'/'\x00'/'é' -- that was the base-version trap; discarded and re-run with the path pinned. Base commit used only for the A-consumed callee (G-AX).

**SPEC INTEGRITY:** swebench_unified.markers.same_spec(Solution.lean, Solution_prepatch.lean, lean tables) = True; spec_signature sha256 dff14304ccc8f84e identical for both, so the spec view does not vary with the impl. scripts/lean_verify.sh Solution.lean -> exit 0.

SPEC IS DISCRIMINATING (not vacuous): Solution_prepatch.lean FAILS verification with unsolved goal `Except.error LookupErr.unresolvedName = Except.ok (resolveName (force nm))` under `if_pos : nm.isDeferred = true` -- i.e. the postcondition bites on exactly the deferred clause the patch repairs. Control confirmed the ensures is load-bearing.

**STRUCTURAL FAITHFULNESS:** inspected post-patch get_format source -- there is NO use of `format_type` before the coercion line (only the docstring mentions it). So the patched body is literally a function of `str(format_type)`, `lang`, `use_l10n`, which is exactly the spec's shape `resolveName (force nm)` with force = the coercion. The ensures's three claims each hold on the modeled domain:
(1) result depends only on forced content -- 0 divergences over ~24,000 probes: every FORMAT_SETTINGS entry + 23 boundary names (empty, 'NOPE', dunders '`__doc__`'/'`__class__`'/'`__name__`', 'a b', '\x00', 'é', whitespace, settings names) + 2000 seeded fuzz names, crossed over lang in {en,de,fr,None} x use_l10n in {True,False,None} x two proxy constructors (gettext_lazy and lazy(id,str)), comparing eager vs lazy only where str(proxy)==name.
(2) forcing always succeeds / lookup never errors -- 0 raises across that same sweep; also non-str inputs (int, None, list, object with `__str__`, lazy int) all return normally post-patch.
(3) Except.ok always -- confirmed; the pre-patch TypeError('getattr(): attribute name must be string') is what the deferred branch models.

F2P/G-DIFF CONFIRMATION (test_patch applied to both worktrees): patched -> test_get_format_lazy_format + test_date_lazy both OK; base -> both ERROR with TypeError: getattr(): attribute name must be string. Full i18n.tests.FormattingTests (21 tests) OK on patched. axiom_check.py run against the UNPATCHED base worktree exits G-AX OK (resolveName well-defined on distinct concrete strs with equal content; force total/content-preserving), matching mapping.md §3.1's stated protocol of never feeding a lazy proxy through the changed function.

ATTACKS ATTEMPTED THAT DID NOT YIELD A DEFECT (each is out of the mapping.md §2 bijection domain, or is the patch's own delta, so none is a legitimate UNFAITHFUL citation):
- str subclass with a lying `__str__` (class Liar(str) whose `__str__` returns 'TIME_FORMAT'): post-patch returns 'P' where eager content 'DATE_FORMAT' would give 'N j, Y', so force(eager s) != s. NOT reportable: mapping.md §2 binds `Name.eager s` to a *concrete str* s (where str(s)==s); more decisively, this behavior change IS the patch's delta (pre-patch getattr uses the subclass object directly), so citing it would condemn the correct spec for the very line under specification. SafeString/mark_safe (an honest subclass) matches eager exactly.
- lazy over a raising callable (lazy(lambda: 1/0 ... , str)) propagates ValueError, apparently contradicting 'force is total'. NOT reportable: that is a proxy over a diverging computation, not a name-denoting proxy; gettext_lazy/str proxies never raise, and this is identical pre- and post-patch (unchanged machinery).
- proxy with unstable content (generator-backed lazy yielding a different name per force): spec models a Name as carrying fixed content; out of domain and pre/post identical.
- cache aliasing: get_format returns the *same mutable list object* from `_format_cache`, so a caller mutating it perturbs later calls. Real, but unchanged by the patch and it does NOT break the spec's claim -- eager vs lazy still compared equal after I appended a sentinel to the cached DATE_INPUT_FORMATS list.
- value-domain coarseness: get_format returns int (FIRST_DAY_OF_WEEK=0, NUMBER_GROUPING=3), list, and even a module class, while the spec types the value as List Char. This is type abstraction, not over-strength: resolveName is an opaque axiom pinning no specific value (directive 7), so the ensures makes no claim the real values violate.
- elision of lang/use_l10n from the signature: mapping.md §3.1 pins them fixed for the lookup, and I confirmed determinism across all lang x use_l10n combinations; no in-call variation exists.

**CONCLUSION:** I found no input in the modeled domain (Name.eager s <-> concrete str s; Name.deferred s <-> lazy proxy denoting s) on which `Except.ok (resolveName (force nm))` disagrees with the patched get_format. The spec is neither too strong nor drifted; it is exactly as strong as the patch's added coercion, and its one axiom covers only unchanged downstream resolution. No diverging_input to cite.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-AX `pass` (the axiom battery). The account names `Solution.lean`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

### MEASUREMENTS I RAN (not inherited from the bundle record).

1. Frozen-spec / impl-invariance. swebench_unified.markers.same_spec(Solution.lean, Solution_prepatch.lean, VelvetBackend.language) = True; stronger, the raw spec_view strings are byte-identical (sha256 841d1c784f902ff0 both). So the consumer view does not vary with the impl and cannot carry a gold-vs-prepatch tell by construction. scripts/lean_verify.sh Solution.lean -> exit 0 (positive control that the view I judged is the shipped, verifying artifact).

2. Consumer surface. I derived the actual solver-visible text with markers.spec_view + eval.adapter.EvalAdapter.spec_view (which hard-refuses an unelided view): impl region -> 'implementation elided', prove_correct body -> 'proof elided'. Everything I judged is that projection only. mapping.md / refinement.md / meta.json / verdict.md are NOT in the consumer surface (eval.dataset builds task.spec_view from the model source alone), so the concrete disclosures that do exist in those audit docs -- `str(format_type)`, `django/utils/formats.py:116`, the cache_key/getattr(module, format_type)/getattr(settings, format_type) chain, formats.py:117-145 -- never reach the solver. The two 'mapping.md §2' cross-refs inside spec-view comments are dangling pointers to a doc the solver does not receive; they name no repo symbol or mechanism, so they disclose nothing.

3. Mechanical screen, run by me. leakage.screen(Solution.lean, velvet tables, gold patch, problem_statement, test_patch) -> passed=True, hard_failures=[], warnings=[] (same for Solution_prepatch.lean). Note this screen judges against problem_statement only, never hints_text (hints_text is empty here anyway, len 0). I separately grepped the spec view for the gold-edit vocabulary: no 'str(', 'format_type', 'get_format', 'formats.py', 'django/', 'getattr', 'TypeError', 'lazy', 'gettext', 'cache_key', 'coercion', no diff markers, no bug/fix/pre-patch/regression narration. The only 'diff' substring hit is the English word 'differ' in a carrier comment (line 31) -- a substring artifact, not a marker.

4. Semantic test: is the view derivable from the public problem_statement alone? Yes, fully. The public statement is 'django.utils.formats.get_format should allow lazy parameter' + 'fails with TypeError: getattr(): attribute name must be string' on `some_date|date:_('Y-m-d')`. It therefore already discloses publicly: (a) the argument may arrive lazy or concrete -- the spec's Name.eager/Name.deferred carriers; (b) the lazy form must stop failing -- the spec's total `force` and the always-Except.ok postcondition; (c) the lazy form must behave as the equivalent concrete name -- the spec's 'depends ONLY on the resolved content' via `resolveName (force nm)`. The single modeled error constructor LookupErr.unresolvedName is the abstract counterpart of the publicly-quoted TypeError. What the view withholds is precisely the gold mechanism and its location: it never names the coercion `str(...)`, never says the edit is one added line, never says where in the function it goes, and abstracts all downstream resolution into an uninterpreted axiom pinning no value. A solver reading only the view learns 'accept a deferred name, force it, resolve on content, never error' -- the public objective restated in Lean -- not `format_type = str(format_type)`.

5. Localization is not smuggled by the view. The repo symbol django.utils.formats.get_format reaches the solver through the harness's own prompt policy (eval.prompts.`_spec_block` emitting meta.json modeled_functions), and that symbol is already named verbatim in the problem_statement. Nothing about that is a spec-view leak.

6. **RELAXATION:** NONE CLAIMED, AND NONE NEEDED. meta.json has no relaxed_leakage key (keys: additional_change_sites, axioms, base_commit, changed_files, conf_skip, deep_model_references, gates, instance_id, modeled_functions, pbt_audit, repo, schema_version, spec_provenance, string_modeling, version) and there is no RELAXED_LEAKAGE.md anywhere under the instance directory (find -iname '*RELAX*' empty). So I judged this as an ordinary cell with no inherited disposition, and no unavoidability argument was required: the problem_statement and the gold edit agree here (statement asks for lazy support; patch adds lazy support), so the discriminator the view names -- deferred-vs-eager arrival and forcing -- is a problem_statement-derivable facet rather than an unavoidable disclosure.

7. Bundle-steering check. leakage.reviewer_directed() over every bundle document (mapping.md, refinement.md, meta.json, verdict.md, properties.py, axiom_check.py, conformance_check.py, Solution.lean, Solution_prepatch.lean) returned [] for all nine, and a manual grep for attacker/panel/'which verdict'/'do not flag' language found nothing outside the pre-existing G-PANEL gate records. No file in this bundle addresses or instructs this role. The prior G-PANEL-3 record does assert NO-LEAKAGE with similar reasoning, but I did not inherit it -- the verdict above rests on the same_spec/spec_view byte comparison, the leakage.screen run, the lean_verify exit 0, and the problem_statement-derivability analysis I performed above.

**Conclusion:** the spec view discloses nothing about the gold edit beyond the public problem_statement. NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `properties.py`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.
