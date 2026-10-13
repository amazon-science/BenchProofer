# P2 adversarial audit — scikit-learn__scikit-learn-15100

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 admissible attacks re-run of 8 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_7.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found — the spec is not broken. Postcondition `out = markFreeSeq (canonicalDecompose s)` is exact functional equality, universally quantified, under EMPTY preconditions, over two genuinely FREE opaque callees (no asserted ensures ⇒ no A-consumed axiom to echo or exploit). 8 same-spec wrong impls (partial-domain, boundary, control-flow-effect, inverted-guard, no-filter, double-decompose A-leg probe, prepatch guard bug, ungrounded-oracle echo) were verified: 7 REJECTED (exit 1, each with a genuine unsolved goal on the real ensures clause), and the only verifier is the literal echo `return markFreeSeq (canonicalDecompose s)`, which IS the gold behaviour. Its materialized faithful refined patch RESOLVES under the official harness (F2P + all P2P pass), so verify⇒correct holds on the one available leg.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -65,7 +65,7 @@
       let c := (canonicalDecompose s)[i - 1]!
       result := (if isCombiningMark c then [] else [c]) ++ result
       i := i - 1
-    return result
+    return if canonicalDecompose s = s then s else result
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the code point at
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -56,10 +56,10 @@
     -- impl-start
     let mut result : List Char := []
     let mut i := (canonicalDecompose s).length
-    while i > 0
+    while i > 1
       invariant 0 ≤ i ∧ i ≤ (canonicalDecompose s).length
       invariant result = markFreeSeq ((canonicalDecompose s).drop i)
-      done_with i = 0
+      done_with i ≤ 1
       decreasing i
     do
       let c := (canonicalDecompose s)[i - 1]!
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -54,18 +54,7 @@
   ensures out = markFreeSeq (canonicalDecompose s)
   do
     -- impl-start
-    let mut result : List Char := []
-    let mut i := (canonicalDecompose s).length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ (canonicalDecompose s).length
-      invariant result = markFreeSeq ((canonicalDecompose s).drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let c := (canonicalDecompose s)[i - 1]!
-      result := (if isCombiningMark c then [] else [c]) ++ result
-      i := i - 1
-    return result
+    return canonicalDecompose s
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the code point at
@@ -85,5 +74,3 @@
 
 prove_correct stripDiacritics by
   loom_solve
-  rw [markFreeSeq_drop_step (canonicalDecompose s) i (by omega) (by omega)]
-  simp_all
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -63,7 +63,7 @@
       decreasing i
     do
       let c := (canonicalDecompose s)[i - 1]!
-      result := (if isCombiningMark c then [] else [c]) ++ result
+      result := (if isCombiningMark c then [c] else []) ++ result
       i := i - 1
     return result
     -- impl-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -65,7 +65,7 @@
       let c := (canonicalDecompose s)[i - 1]!
       result := (if isCombiningMark c then [] else [c]) ++ result
       i := i - 1
-    return result
+    return []
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the code point at
```

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -54,18 +54,7 @@
   ensures out = markFreeSeq (canonicalDecompose s)
   do
     -- impl-start
-    let mut result : List Char := []
-    let mut i := (canonicalDecompose s).length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ (canonicalDecompose s).length
-      invariant result = markFreeSeq ((canonicalDecompose s).drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let c := (canonicalDecompose s)[i - 1]!
-      result := (if isCombiningMark c then [] else [c]) ++ result
-      i := i - 1
-    return result
+    return markFreeSeq (canonicalDecompose s)
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the code point at
@@ -85,5 +74,3 @@
 
 prove_correct stripDiacritics by
   loom_solve
-  rw [markFreeSeq_drop_step (canonicalDecompose s) i (by omega) (by omega)]
-  simp_all
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -65,7 +65,7 @@
       let c := (canonicalDecompose s)[i - 1]!
       result := (if isCombiningMark c then [] else [c]) ++ result
       i := i - 1
-    return result
+    return if result = [] then canonicalDecompose s else result
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the code point at
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -54,18 +54,7 @@
   ensures out = markFreeSeq (canonicalDecompose s)
   do
     -- impl-start
-    let mut result : List Char := []
-    let mut i := (canonicalDecompose s).length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ (canonicalDecompose s).length
-      invariant result = markFreeSeq ((canonicalDecompose s).drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let c := (canonicalDecompose s)[i - 1]!
-      result := (if isCombiningMark c then [] else [c]) ++ result
-      i := i - 1
-    return result
+    return markFreeSeq (canonicalDecompose (canonicalDecompose s))
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the code point at
@@ -85,5 +74,3 @@
 
 prove_correct stripDiacritics by
   loom_solve
-  rw [markFreeSeq_drop_step (canonicalDecompose s) i (by omega) (by omega)]
-  simp_all
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

**SCRATCH:**  (all work confined there; base_commit worktree at .../repo, af8a6e592a1a15d92d77011856d5aa0ec4db4c6c, restored clean after each patch materialization).

**SAME-SPEC:** all 8 attacks + positive_control return same_spec=True vs bundle Solution.lean (checked with swebench_unified.markers.same_spec + get_backend('velvet').language). Edits confined to the impl region; axioms/pure/pre/post byte-identical; the helper lemma markFreeSeq_drop_step left byte-identical (atk_3/atk_6/atk_8 also shorten the prove_correct body, which the velvet spec_view elides).

VERIFY (cmd for each: `bash scripts/lean_verify.sh <f>.lean`, run from repo root; launched as concurrent background jobs, <=4 at a time, 3 batches):
- positive_control.lean -> exit 0 VERIFIES (gold-faithful backward while-fold; non-vacuous, discharges via markFreeSeq_drop_step).
- atk_1.lean PREPATCH BUG re-encode (`return if canonicalDecompose s = s then s else result`, the removed `if normalized == s: return s` early-out) -> exit 1 REJECTED. Residual goal: `(if canonicalDecompose s = s then s else result_1) = markFreeSeq (canonicalDecompose s)`. prepatch_reproduced=true (matches Solution_prepatch.lean / G-DIFF).
- atk_2.lean BOUNDARY off-by-one (`while i > 1`, `done_with i ≤ 1` ⇒ drops the first code point) -> exit 1 REJECTED. Goal: `result_1 = markFreeSeq (canonicalDecompose s)` with done_1 : i ≤ 1.
- atk_3.lean NO-FILTER identity (`return canonicalDecompose s`) -> exit 1 REJECTED. Goal: `canonicalDecompose s = markFreeSeq (canonicalDecompose s)`.
- atk_4.lean INVERTED keep/drop guard (`if isCombiningMark c then [c] else []`) -> exit 1 REJECTED on the loop invariant itself.
- atk_5.lean CONTROL-FLOW-EFFECT (runs the full fold, then `return []`) -> exit 1 REJECTED. Goal: `[] = markFreeSeq (canonicalDecompose s)`.
- atk_6.lean UNGROUNDED-ORACLE ECHO (`return markFreeSeq (canonicalDecompose s)`) -> exit 0 VERIFIES.
- atk_7.lean PARTIAL-DOMAIN (`return if result = [] then canonicalDecompose s else result` — wrong exactly on the F2P 'combining marks by themselves' case) -> exit 1 REJECTED. Goal: `(if result_1 = [] then canonicalDecompose s else result_1) = markFreeSeq (canonicalDecompose s)`.
- atk_8.lean A-LEG PROBE, double-applies the opaque decompose (`markFreeSeq (canonicalDecompose (canonicalDecompose s))`) -> exit 1 REJECTED. Goal: `markFreeSeq (canonicalDecompose (canonicalDecompose s)) = markFreeSeq (canonicalDecompose s)`. This is the sharpest A-leg result: because canonicalDecompose is FREE (no idempotence axiom asserted), the spec cannot even prove NFKD idempotence — confirming the spec asserts nothing about the callee's values, i.e. it is not over-strong on the A legs.

### MANDATORY RESOLVE OF THE VERIFYING WRONG IMPL (atk_6):
- Faithful refined patch materialized at atk_6_faithful.diff — the maintainer-endorsed minimal fix per refinement.md §B (drop the buggy `if normalized == s: return s` guard; apply decompose-and-filter unconditionally). Generated via `git diff` in the base_commit worktree so hunk counts are exact (avoiding the malformed-diff false negative the prior pass hit).
- `cd  && git apply --check ../atk_6_faithful.diff` -> APPLY_CHECK_OK. (Gold patch.diff also re-checked: GOLD_APPLY_OK.)
- **EXECUTED:** `swebench_unified.harness.run_resolve('scikit-learn__scikit-learn-15100', patch, timeout=1800, retries=1)` -> RESOLVED=True, COMPLETED=True. Report: patch_successfully_applied=True; FAIL_TO_PASS test_strip_accents SUCCESS with failure list []; all PASS_TO_PASS SUCCESS. => the verifying wrong impl's faithful patch RESOLVES, so this leg does NOT break the spec.

EXTRA A-LEG RESOLVE PROBE (mapping.md §3.1 'NFKD' pin): since canonicalDecompose is opaque/free, an NFD-based refinement is not excluded by the Lean spec. Materialized probe_nfd.diff (NFD + unconditional strip), git apply --check OK, run_resolve -> RESOLVED=True, COMPLETED=True. So the NFKD/NFD choice is not test-discriminating at this instance: the A2 mapping is under-constrained by the frozen spec but every admissible reading still resolves. Recorded as a fidelity observation, NOT a break (no verifying wrong impl has a non-resolving faithful patch).

### REFINEMENT.MD AUDIT (A legs + model↔patch correspondence):
- A1 (R): `s : List Char` ↔ `str` arg. Sound; mapping.md §2 bijection `ch ↔ Char.ofNat (ord ch)` is exact on the BMP and the op is strictly per-code-point.
- A2 (A-reference, opaque FREE): canonicalDecompose ↔ unicodedata.normalize('NFKD',·). No asserted ensures ⇒ NOT A-consumed ⇒ nothing for G-AX; confirmed by grep (no `axiom` decl, no callee `ensures`) and by atk_8, which shows even idempotence is unprovable. Callee/line provenance (text.py:132 pre / 140 post) matches the real repo file at base_commit (verified against the worktree). Sound.
- A3 (A-reference, opaque FREE): isCombiningMark ↔ `unicodedata.combining(·) != 0`. Keep predicate = (class == 0) exactly matches `not unicodedata.combining(c)`. Sound.
- A4 (I): markFreeSeq + the verified backward loop ARE the comprehension, modeled CONCRETELY (not axiomatized). The genuinely-changed op — unconditional application — lives in the postcondition holding for ALL s. Correct; G-CONF transliterates it against the real callees (pass, 100010 inputs, seed 15100, 0 disagreements).
- A5 (R/I): `''.join` of single-char fragments ↔ List `++` of `[c]`/`[]`. Sound.
- §C no kind-3 legs: confirmed. Every leg is R, A-reference, or I; no A-consumed legs exist at all, so there is no axiom-soundness trust point (G-AX skip legitimate).
- §B ASCII fast-path claim INDEPENDENTLY RE-DERIVED, not taken on trust: (i) EXHAUSTIVE over all 0x110000 code points minus surrogates, gold(ASCII try/except) vs model(unconditional strip) -> 0 divergences; (ii) exhaustively, no ASCII cp<128 has a nontrivial NFKD decomposition or nonzero combining class (empty list) — which is exactly what makes the fast-path behaviour-preserving; (iii) 400k random multi-char strings over an accent/combining-mark-weighted alphabet -> 0 divergences; (iv) all F2P/P2P strip_accents cases pass under both gold and model, while the PREPATCH function fails 3 of them ('ö', standalone marks '̀́̂̃', 'ȫ') — the discriminating content is real and lives in the spec clause.

**WHY THIS SPEC RESISTS ATTACK:** the postcondition is exact functional equality over empty preconditions, and both callees are free opaque functions. There is no consumed axiom to echo and no partial domain to hide in, so the only way to close the universally-quantified obligation is to compute (or literally name) markFreeSeq ∘ canonicalDecompose — which is the gold behaviour. Every domain/boundary/order/effect/guard deviation leaves an unsolved goal.

**CONCLUSION:** 8 distinct same-spec wrong impls encoded and verified (>=5 required, incl. prepatch bug + partial-domain + boundary + control-flow-effect + ungrounded-oracle echo + an A-leg probe). Positive control verifies. Exactly one wrong impl verifies (the echo) and its materialized faithful patch RESOLVES under the official harness (executed, not speculated). No verifying wrong impl has a non-resolving faithful patch. verify⇒correct holds. Verdict: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 admissible attacks re-run of 8 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_7.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found — the spec is not broken. Postcondition `out = markFreeSeq (canonicalDecompose s)` is exact functional equality, universally quantified, under EMPTY preconditions, over two genuinely FREE opaque callees (no asserted ensures ⇒ no A-consumed axiom to echo or exploit). 8 same-spec wrong impls (partial-domain, boundary, control-flow-effect, inverted-guard, no-filter, double-decompose A-leg probe, prepatch guard bug, ungrounded-oracle echo) were verified: 7 REJECTED (exit 1, each with a genuine unsolved goal on the real ensures clause), and the only verifier is the literal echo `return markFreeSeq (canonicalDecompose s)`, which IS the gold behaviour. Its materialized faithful refined patch RESOLVES under the official harness (F2P + all P2P pass), so verify⇒correct holds on the one available leg.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

**SCRATCH:**  (all work confined there; base_commit worktree at .../repo, af8a6e592a1a15d92d77011856d5aa0ec4db4c6c, restored clean after each patch materialization).

**SAME-SPEC:** all 8 attacks + positive_control return same_spec=True vs bundle Solution.lean (checked with swebench_unified.markers.same_spec + get_backend('velvet').language). Edits confined to the impl region; axioms/pure/pre/post byte-identical; the helper lemma markFreeSeq_drop_step left byte-identical (atk_3/atk_6/atk_8 also shorten the prove_correct body, which the velvet spec_view elides).

VERIFY (cmd for each: `bash scripts/lean_verify.sh <f>.lean`, run from repo root; launched as concurrent background jobs, <=4 at a time, 3 batches):
- positive_control.lean -> exit 0 VERIFIES (gold-faithful backward while-fold; non-vacuous, discharges via markFreeSeq_drop_step).
- atk_1.lean PREPATCH BUG re-encode (`return if canonicalDecompose s = s then s else result`, the removed `if normalized == s: return s` early-out) -> exit 1 REJECTED. Residual goal: `(if canonicalDecompose s = s then s else result_1) = markFreeSeq (canonicalDecompose s)`. prepatch_reproduced=true (matches Solution_prepatch.lean / G-DIFF).
- atk_2.lean BOUNDARY off-by-one (`while i > 1`, `done_with i ≤ 1` ⇒ drops the first code point) -> exit 1 REJECTED. Goal: `result_1 = markFreeSeq (canonicalDecompose s)` with done_1 : i ≤ 1.
- atk_3.lean NO-FILTER identity (`return canonicalDecompose s`) -> exit 1 REJECTED. Goal: `canonicalDecompose s = markFreeSeq (canonicalDecompose s)`.
- atk_4.lean INVERTED keep/drop guard (`if isCombiningMark c then [c] else []`) -> exit 1 REJECTED on the loop invariant itself.
- atk_5.lean CONTROL-FLOW-EFFECT (runs the full fold, then `return []`) -> exit 1 REJECTED. Goal: `[] = markFreeSeq (canonicalDecompose s)`.
- atk_6.lean UNGROUNDED-ORACLE ECHO (`return markFreeSeq (canonicalDecompose s)`) -> exit 0 VERIFIES.
- atk_7.lean PARTIAL-DOMAIN (`return if result = [] then canonicalDecompose s else result` — wrong exactly on the F2P 'combining marks by themselves' case) -> exit 1 REJECTED. Goal: `(if result_1 = [] then canonicalDecompose s else result_1) = markFreeSeq (canonicalDecompose s)`.
- atk_8.lean A-LEG PROBE, double-applies the opaque decompose (`markFreeSeq (canonicalDecompose (canonicalDecompose s))`) -> exit 1 REJECTED. Goal: `markFreeSeq (canonicalDecompose (canonicalDecompose s)) = markFreeSeq (canonicalDecompose s)`. This is the sharpest A-leg result: because canonicalDecompose is FREE (no idempotence axiom asserted), the spec cannot even prove NFKD idempotence — confirming the spec asserts nothing about the callee's values, i.e. it is not over-strong on the A legs.

### MANDATORY RESOLVE OF THE VERIFYING WRONG IMPL (atk_6):
- Faithful refined patch materialized at atk_6_faithful.diff — the maintainer-endorsed minimal fix per refinement.md §B (drop the buggy `if normalized == s: return s` guard; apply decompose-and-filter unconditionally). Generated via `git diff` in the base_commit worktree so hunk counts are exact (avoiding the malformed-diff false negative the prior pass hit).
- `cd  && git apply --check ../atk_6_faithful.diff` -> APPLY_CHECK_OK. (Gold patch.diff also re-checked: GOLD_APPLY_OK.)
- **EXECUTED:** `swebench_unified.harness.run_resolve('scikit-learn__scikit-learn-15100', patch, timeout=1800, retries=1)` -> RESOLVED=True, COMPLETED=True. Report: patch_successfully_applied=True; FAIL_TO_PASS test_strip_accents SUCCESS with failure list []; all PASS_TO_PASS SUCCESS. => the verifying wrong impl's faithful patch RESOLVES, so this leg does NOT break the spec.

EXTRA A-LEG RESOLVE PROBE (mapping.md §3.1 'NFKD' pin): since canonicalDecompose is opaque/free, an NFD-based refinement is not excluded by the Lean spec. Materialized probe_nfd.diff (NFD + unconditional strip), git apply --check OK, run_resolve -> RESOLVED=True, COMPLETED=True. So the NFKD/NFD choice is not test-discriminating at this instance: the A2 mapping is under-constrained by the frozen spec but every admissible reading still resolves. Recorded as a fidelity observation, NOT a break (no verifying wrong impl has a non-resolving faithful patch).

### REFINEMENT.MD AUDIT (A legs + model↔patch correspondence):
- A1 (R): `s : List Char` ↔ `str` arg. Sound; mapping.md §2 bijection `ch ↔ Char.ofNat (ord ch)` is exact on the BMP and the op is strictly per-code-point.
- A2 (A-reference, opaque FREE): canonicalDecompose ↔ unicodedata.normalize('NFKD',·). No asserted ensures ⇒ NOT A-consumed ⇒ nothing for G-AX; confirmed by grep (no `axiom` decl, no callee `ensures`) and by atk_8, which shows even idempotence is unprovable. Callee/line provenance (text.py:132 pre / 140 post) matches the real repo file at base_commit (verified against the worktree). Sound.
- A3 (A-reference, opaque FREE): isCombiningMark ↔ `unicodedata.combining(·) != 0`. Keep predicate = (class == 0) exactly matches `not unicodedata.combining(c)`. Sound.
- A4 (I): markFreeSeq + the verified backward loop ARE the comprehension, modeled CONCRETELY (not axiomatized). The genuinely-changed op — unconditional application — lives in the postcondition holding for ALL s. Correct; G-CONF transliterates it against the real callees (pass, 100010 inputs, seed 15100, 0 disagreements).
- A5 (R/I): `''.join` of single-char fragments ↔ List `++` of `[c]`/`[]`. Sound.
- §C no kind-3 legs: confirmed. Every leg is R, A-reference, or I; no A-consumed legs exist at all, so there is no axiom-soundness trust point (G-AX skip legitimate).
- §B ASCII fast-path claim INDEPENDENTLY RE-DERIVED, not taken on trust: (i) EXHAUSTIVE over all 0x110000 code points minus surrogates, gold(ASCII try/except) vs model(unconditional strip) -> 0 divergences; (ii) exhaustively, no ASCII cp<128 has a nontrivial NFKD decomposition or nonzero combining class (empty list) — which is exactly what makes the fast-path behaviour-preserving; (iii) 400k random multi-char strings over an accent/combining-mark-weighted alphabet -> 0 divergences; (iv) all F2P/P2P strip_accents cases pass under both gold and model, while the PREPATCH function fails 3 of them ('ö', standalone marks '̀́̂̃', 'ȫ') — the discriminating content is real and lives in the spec clause.

**WHY THIS SPEC RESISTS ATTACK:** the postcondition is exact functional equality over empty preconditions, and both callees are free opaque functions. There is no consumed axiom to echo and no partial domain to hide in, so the only way to close the universally-quantified obligation is to compute (or literally name) markFreeSeq ∘ canonicalDecompose — which is the gold behaviour. Every domain/boundary/order/effect/guard deviation leaves an unsolved goal.

**CONCLUSION:** 8 distinct same-spec wrong impls encoded and verified (>=5 required, incl. prepatch bug + partial-domain + boundary + control-flow-effect + ungrounded-oracle echo + an A-leg probe). Positive control verifies. Exactly one wrong impl verifies (the echo) and its materialized faithful patch RESOLVES under the official harness (executed, not speculated). No verifying wrong impl has a non-resolving faithful patch. verify⇒correct holds. Verdict: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

**Attack:** faithfulness-break (is the spec too strong / does the modeled function disagree with the real callee on some input?). Reference used correctly: worktree at base_commit af8a6e592a1a15d92d77011856d5aa0ec4db4c6c with patch.diff APPLIED (post-patch is the reference for the changed function; base only for untouched callees). Result: no diverging input found; no defect.

**SPEC UNDER TEST.** Single ensures clause, total/demonic: `out = markFreeSeq (canonicalDecompose s)` for EVERY s, with no preconditions (pre-conditions region empty). So the spec demands the strip be applied unconditionally. Two callees are opaque FREE functions with no asserted ensures (canonicalDecompose, isCombiningMark) - the weakest possible contract, so they cannot over-constrain; markFreeSeq is a concrete deep model of the comprehension.

**THE ONE REAL ATTACK SURFACE.** The gold patch does NOT compute the comprehension unconditionally: it has an ASCII fast-path (`s.encode("ASCII", strict); return s`) that returns the input verbatim. The spec models the unconditional strip. If any ASCII-encodable s had markFreeSeq(NFKD(s)) != s, the spec would be strictly stronger than the real patched function and this would be UNFAITHFUL. refinement.md §B asserts this fast-path is behaviour-preserving; I did not take that on trust and tested it directly.

EVIDENCE (model transliterated exactly per mapping.md §2/§3: canonicalDecompose=NFKD, isCombiningMark c = combining(c)!=0; compared against the REAL patched strip_accents_unicode extracted from the patched worktree file):
1. EXHAUSTIVE all 128 ASCII code points: zero where NFKD(c)!=c or combining(c)!=0 -> the fast-path premise holds at the code-point level.
2. Fast-path soundness on longer strings: 300k random pure-ASCII strings (len 0-20); markFreeSeq(NFKD(s))==s in ALL cases. Zero counterexamples, so `return s` is observationally identical to the unconditional strip. This is the claim that would have broken the spec, and it holds.
3. EXHAUSTIVE single code point over the ENTIRE Unicode scalar range (0x0-0x10FFFF, surrogates excluded): 0 divergences model vs real.
4. EXHAUSTIVE all 2-char strings over a focused 105-char alphabet (11,025 cases, ASCII + combining marks + precomposed + compat forms like ﬁ/ḛ/İ/ß): 0 divergences.
5. EXHAUSTIVE all 3-char strings over a 14-char adversarial alphabet (2,744 cases): 0 divergences.
6. Random fuzz N=400,000 (seed 15100, alphabet weighted to accented Latin, standalone combining marks U+0300..U+036F, already-decomposed sequences, NUL/tab/newline/ZWSP/astral): 0 divergences.
7. Full-Unicode random fuzz N=500,000 (1-4 chars drawn uniformly from the whole scalar range): 0 divergences. Plus Hangul syllables, CJK compat ideographs, and enclosed-alphanumeric blocks: 0 divergences.
8. Empty string: both ''. Lone surrogates U+D800/DC00/DFFF agree (and are outside the List Char refinement domain anyway).

**CROSS-CHECKS.** Spec region byte-identity confirmed with swebench_unified.markers.same_spec using the velvet LanguageTables: same_spec(Solution.lean, Solution_prepatch.lean) == True, so the spec really is frozen across the diff pair and the prepatch rival is refuted by the impl/proof, not by a weakened contract. scripts/lean_verify.sh on Solution.lean exits 0 (no sorry/error). The postcondition is not vacuous: no preconditions, and it pins the output as an equality to a concrete computable model rather than an existential or a tautology. The spec is also not too WEAK in the direction that matters here - it forbids the pre-patch `if normalized == s: return s` early-out, which is exactly the bug the F2P test (test_strip_accents) targets.

**DIRECTION-OF-DRIFT NOTE.** The only asymmetry between spec and gold is that the gold short-circuits on ASCII; that is a pure performance refinement, invisible to the observable function, and I confirmed it empirically rather than accepting the prose argument. No input distinguishes markFreeSeq(canonicalDecompose s) from the patched strip_accents_unicode(s) anywhere in the tested domain, which includes an exhaustive sweep of the full Unicode range at length 1 and exhaustive sweeps at lengths 2-3 over the adversarial alphabets.

**CLAIMED VERDICT:** FAITHFUL. No diverging input exists to cite; asserting UNFAITHFUL here would require comparing against the BASE version, which would only re-discover the delta the patch intentionally introduces and would condemn a correct spec.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

**NO RELAXATION IN THIS BUNDLE.** Verified there is no `relaxed_leakage` key in meta.json (dumped top-level keys: additional_change_sites, axioms, base_commit, changed_files, conf_skip, deep_model_references, gates, instance_id, modeled_functions, pbt_audit, region_hashes, repo, schema_version, spec_provenance, string_modeling, version) and no RELAXED_LEAKAGE.md on disk (full `ls -la` of the bundle). meta G-LEAK status is `pass`, not `relaxed`. So there is no unavoidability argument to inherit or re-derive; this is judged as an ordinary clean-spec leakage review.

### WHAT I MEASURED (not asserted):
1. Spec-view scope. Confirmed the consumer receives ONLY markers.spec_view, not mapping.md/refinement.md: prompts/velvet/eval_mode_1.md hands the agent a "FORMAL SPECIFICATION ... shown below"; eval/dataset.py:285 sets task.spec_view = adapter.spec_view(model), and adapter.py:304-319 refuses to expose an unelided view. So the leak surface is the spec_view alone. This matters because mapping.md §1 and refinement.md §A/§B DO discuss the removed `if normalized == s: return s` guard and the gold ASCII try/except — but neither file is consumer-visible, so neither is in scope.
2. Region integrity. Ran markers.region_hashes(Solution.lean, VelvetBackend.language): spec_view=59d06bf93f29c7d87f7de8a1d61694ae7ce36f05364d1301743e50aa6961dd10, axioms=77553c98..., pure=9339d0f4..., impl=3899109b... — all four byte-identical to meta.json region_hashes. markers.same_spec(Solution.lean, Solution_prepatch.lean, velvet) = True, so the frozen spec is shared between the two.
3. Mechanical screen, re-run by me. leakage.screen(Solution.lean, VelvetBackend.language, patch, problem_statement, test_patch) → passed=True, hard_failures=[]. Independent grep -niE over Solution.lean for ascii|encode|UnicodeEncodeError|try:|except|normalized == s|strip_accents|text\.py|feature_extraction returned exactly ONE hit, line 50 "encoded differently (precomposed vs. already decomposed)" — a substring-of-'encode' false positive in prose, not the gold's `s.encode("ASCII")`. No patched file path, no patched symbol (spec renames to the abstract `stripDiacritics`), no diff markers.
4. Gold-edit non-reconstruction (the substantive judgment). The gold patch's actual edit is: replace `normalized = NFKD(s); if normalized == s: return s; else: <strip>` with `try: s.encode("ASCII", strict); return s; except UnicodeEncodeError: <strip>`. The spec view models NONE of this mechanism — no ASCII test, no try/except, no encoding concept, and it does not even name the removed `if normalized == s` early-out. All the spec view reveals is the postcondition `out = markFreeSeq (canonicalDecompose s)` holding for EVERY s, i.e. the strip applied unconditionally.
5. That postcondition is derivable from the PUBLIC problem_statement alone (I re-read instance.json problem_statement, not hints_text). The PS gives s1=chr(241) (precomposed) and s2=chr(110)+chr(771) (already-decomposed), states under Expected Results that "s1 and s2 should both be normalized to the same string, \"n\"", and diagnoses under Actual Results that the function "does nothing if the string is already in NFKD form". It names NFKD and COMBINING TILDE explicitly. So "decompose to NFKD, drop combining marks, unconditionally" is the direct formalization of publicly-stated expected behaviour — legitimate spec content (the required post-state), not a disclosure of the gold implementation. Ran the model `''.join(c for c in NFKD(s) if not combining(c))` on the PS pair and all three F2P cases ("ö"→"o", "̀́̂̃"→"", "ȫ"→"o"): all match, so the PS-derived reading and the spec coincide. The spec also does not encode the ASCII optimization, so it is strictly WEAKER in mechanism than the gold.
6. Load-bearing / non-vacuity. scripts/lean_verify.sh Solution.lean → exit 0 (real exit code captured separately from the pipe). scripts/lean_verify.sh Solution_prepatch.lean → exit 1, with the unsolved goal being purely the postcondition: `(if canonicalDecompose s = s then s else result_1) = markFreeSeq (canonicalDecompose s)`. So the postcondition alone — with no narration — is what rejects the pre-patch guard; the comments are not load-bearing and could be deleted without weakening the spec, confirming no narration is smuggling the edit.
7. Core gates the reading leans on. Independently reproduced the ASCII-fast-path-is-behaviour-preserving claim rather than taking refinement.md §B on faith: no code point <128 has a nontrivial NFKD decomposition or nonzero combining class (enumerated all 128, empty counterexample set), and gold-vs-model fuzz over 200k weighted (ASCII/Latin-1/Latin-Extended/U+0300-U+036F) plus 200k full-range-including-astral inputs gave 0 disagreements. So the omitted fast-path is genuinely invisible in behaviour, and its absence from the spec view is not a concealed leak nor a faithfulness hole.
8. No bundle file addresses me. grep for panel-3/reviewer-directed language (dear reviewer|attacker|do not submit/report/flag|please record|the correct/honest/right verdict|treat this as|instruct|NO-LEAKAGE) across verdict.md, meta.json, refinement.md, mapping.md, Solution.lean, Solution_prepatch.lean, conformance_check.py found only the retained prior-run records (verdict.md:1602 'Role 4 — G-PANEL-3 (leakage): pass', meta.json G-PANEL-3.agent_verdict) — i.e. a stamped earlier verdict, not an instruction to me. leakage.reviewer_directed() returned [] on refinement.md, mapping.md and Solution.lean. Nothing in the bundle tries to tell me what to record; my verdict above is my own measurement.

**CONCLUSION:** the spec view discloses only the publicly-stated required behaviour (unconditional NFKD-decompose-and-strip-combining-marks) and no part of the gold's implementation mechanism. NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
