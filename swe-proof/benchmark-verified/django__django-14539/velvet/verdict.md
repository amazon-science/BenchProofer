# P2 adversarial audit — django__django-14539

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 10 admissible attacks re-run of 10 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 10 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1_prepatch.lean`, `atk_4_partialdomain.lean`, `atk_5_offbyone.lean`, `atk_6_encodedcount.lean`, `atk_7_swap.lean`, `atk_8_lostail.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 4 | `atk_2_guardless.lean`, `atk_3_twoifs.lean`, `atk_9_wrongorder.lean`, `atk_10_takewhile.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (10):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -58,6 +58,11 @@
   ensures res.tail = token.drop (token.length - trailingPunctCount token) ++ tail
   do
     -- impl-start
+    -- Pre-fix skeleton: the suffix moved into `tail` is sliced at the DECODED
+    -- length index (`stripped.length`) rather than measured from the end of the
+    -- encoded token. For tokens whose encoded and decoded lengths coincide this
+    -- agrees with the spec; otherwise the wrong number of characters is peeled,
+    -- so `prove_correct` MUST fail on the `tail` postcondition.
     let decoded := entityDecode token
     let stripped := stripTrailingPunct decoded
     let punctuationCount := decoded.length - stripped.length
@@ -65,21 +70,22 @@
     let mut newTail := tail
     if decoded ≠ stripped then
       core := token.take (token.length - punctuationCount)
-      newTail := token.drop (token.length - punctuationCount) ++ tail
+      newTail := token.drop stripped.length ++ tail
     return { core := core, tail := newTail }
     -- impl-end
 
 prove_correct peelTrailingPunctuation by
   loom_solve
-  · -- if-true, tail clause: the inlined count equals `trailingPunctCount`
+  · -- if-true, tail clause: DISCRIMINATOR — the buggy decoded-length index
+    -- `drop stripped.length` does NOT equal `drop (token.length - count)`
+    -- whenever the token contains entities (decoded.length < token.length).
+    -- This goal is UNCLOSABLE: it is exactly the issue's `&lt</a>lt!` bug.
     simp only [trailingPunctCount]
-  · -- if-true, core clause
+  · -- if-true, core clause (unchanged by the bug)
     simp only [trailingPunctCount]
-  · -- if-false, tail clause: decoded = stripped ⇒ count 0 ⇒ nothing peeled
-    rw [not_not] at if_neg
+  · rw [not_not] at if_neg
     simp only [trailingPunctCount, ← if_neg, Nat.sub_self, Nat.sub_zero,
       List.drop_length, List.nil_append]
-  · -- if-false, core clause: count 0 ⇒ whole token kept
-    rw [not_not] at if_neg
+  · rw [not_not] at if_neg
     simp only [trailingPunctCount, ← if_neg, Nat.sub_self, Nat.sub_zero,
       List.take_length]
```

Attack 2 — `atk_2_guardless.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -61,25 +61,10 @@
     let decoded := entityDecode token
     let stripped := stripTrailingPunct decoded
     let punctuationCount := decoded.length - stripped.length
-    let mut core := token
-    let mut newTail := tail
-    if decoded ≠ stripped then
-      core := token.take (token.length - punctuationCount)
-      newTail := token.drop (token.length - punctuationCount) ++ tail
+    let core := token.take (token.length - punctuationCount)
+    let newTail := token.drop (token.length - punctuationCount) ++ tail
     return { core := core, tail := newTail }
     -- impl-end
 
 prove_correct peelTrailingPunctuation by
-  loom_solve
-  · -- if-true, tail clause: the inlined count equals `trailingPunctCount`
-    simp only [trailingPunctCount]
-  · -- if-true, core clause
-    simp only [trailingPunctCount]
-  · -- if-false, tail clause: decoded = stripped ⇒ count 0 ⇒ nothing peeled
-    rw [not_not] at if_neg
-    simp only [trailingPunctCount, ← if_neg, Nat.sub_self, Nat.sub_zero,
-      List.drop_length, List.nil_append]
-  · -- if-false, core clause: count 0 ⇒ whole token kept
-    rw [not_not] at if_neg
-    simp only [trailingPunctCount, ← if_neg, Nat.sub_self, Nat.sub_zero,
-      List.take_length]
+  loom_solve <;> simp only [trailingPunctCount]
```

Attack 3 — `atk_3_twoifs.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -66,20 +66,16 @@
     if decoded ≠ stripped then
       core := token.take (token.length - punctuationCount)
       newTail := token.drop (token.length - punctuationCount) ++ tail
+    if decoded = stripped then
+      core := token.take (token.length - punctuationCount)
+      newTail := token.drop (token.length - punctuationCount) ++ tail
     return { core := core, tail := newTail }
     -- impl-end
 
 prove_correct peelTrailingPunctuation by
-  loom_solve
-  · -- if-true, tail clause: the inlined count equals `trailingPunctCount`
-    simp only [trailingPunctCount]
-  · -- if-true, core clause
-    simp only [trailingPunctCount]
-  · -- if-false, tail clause: decoded = stripped ⇒ count 0 ⇒ nothing peeled
-    rw [not_not] at if_neg
-    simp only [trailingPunctCount, ← if_neg, Nat.sub_self, Nat.sub_zero,
-      List.drop_length, List.nil_append]
-  · -- if-false, core clause: count 0 ⇒ whole token kept
-    rw [not_not] at if_neg
-    simp only [trailingPunctCount, ← if_neg, Nat.sub_self, Nat.sub_zero,
-      List.take_length]
+  loom_solve <;>
+    first
+      | (simp only [trailingPunctCount])
+      | (rw [not_not] at if_neg
+         simp only [trailingPunctCount, ← if_neg, Nat.sub_self, Nat.sub_zero,
+           List.take_length, List.drop_length, List.nil_append])
```

Attack 4 — `atk_4_partialdomain.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -63,23 +63,12 @@
     let punctuationCount := decoded.length - stripped.length
     let mut core := token
     let mut newTail := tail
-    if decoded ≠ stripped then
+    if decoded ≠ stripped ∧ token.length = decoded.length then
       core := token.take (token.length - punctuationCount)
       newTail := token.drop (token.length - punctuationCount) ++ tail
     return { core := core, tail := newTail }
     -- impl-end
 
 prove_correct peelTrailingPunctuation by
-  loom_solve
-  · -- if-true, tail clause: the inlined count equals `trailingPunctCount`
-    simp only [trailingPunctCount]
-  · -- if-true, core clause
-    simp only [trailingPunctCount]
-  · -- if-false, tail clause: decoded = stripped ⇒ count 0 ⇒ nothing peeled
-    rw [not_not] at if_neg
-    simp only [trailingPunctCount, ← if_neg, Nat.sub_self, Nat.sub_zero,
-      List.drop_length, List.nil_append]
-  · -- if-false, core clause: count 0 ⇒ whole token kept
-    rw [not_not] at if_neg
-    simp only [trailingPunctCount, ← if_neg, Nat.sub_self, Nat.sub_zero,
-      List.take_length]
+  loom_solve <;> simp_all only [trailingPunctCount, Nat.sub_self, Nat.sub_zero,
+    List.take_length, List.drop_length, List.nil_append, not_not]
```

Attack 5 — `atk_5_offbyone.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -64,8 +64,8 @@
     let mut core := token
     let mut newTail := tail
     if decoded ≠ stripped then
-      core := token.take (token.length - punctuationCount)
-      newTail := token.drop (token.length - punctuationCount) ++ tail
+      core := token.take (token.length - punctuationCount - 1)
+      newTail := token.drop (token.length - punctuationCount - 1) ++ tail
     return { core := core, tail := newTail }
     -- impl-end
 
```

Attack 6 — `atk_6_encodedcount.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -58,12 +58,11 @@
   ensures res.tail = token.drop (token.length - trailingPunctCount token) ++ tail
   do
     -- impl-start
-    let decoded := entityDecode token
-    let stripped := stripTrailingPunct decoded
-    let punctuationCount := decoded.length - stripped.length
+    let strippedEnc := stripTrailingPunct token
+    let punctuationCount := token.length - strippedEnc.length
     let mut core := token
     let mut newTail := tail
-    if decoded ≠ stripped then
+    if token ≠ strippedEnc then
       core := token.take (token.length - punctuationCount)
       newTail := token.drop (token.length - punctuationCount) ++ tail
     return { core := core, tail := newTail }
```

Attack 7 — `atk_7_swap.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -64,8 +64,8 @@
     let mut core := token
     let mut newTail := tail
     if decoded ≠ stripped then
-      core := token.take (token.length - punctuationCount)
-      newTail := token.drop (token.length - punctuationCount) ++ tail
+      core := token.drop (token.length - punctuationCount)
+      newTail := token.take (token.length - punctuationCount) ++ tail
     return { core := core, tail := newTail }
     -- impl-end
 
```

Attack 8 — `atk_8_lostail.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -65,7 +65,7 @@
     let mut newTail := tail
     if decoded ≠ stripped then
       core := token.take (token.length - punctuationCount)
-      newTail := token.drop (token.length - punctuationCount) ++ tail
+      newTail := token.drop (token.length - punctuationCount)
     return { core := core, tail := newTail }
     -- impl-end
 
```

Attack 9 — `atk_9_wrongorder.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -64,6 +64,10 @@
     let mut core := token
     let mut newTail := tail
     if decoded ≠ stripped then
+      -- NOTE: `core` is written FIRST here (refinement.md's own A6-then-A7
+      -- table order), which is the REVERSE of patch.diff's statement order
+      -- (`trail` first, then `middle`). Lean is order-insensitive because
+      -- `token` is immutable; Python is NOT, because `middle` is reassigned.
       core := token.take (token.length - punctuationCount)
       newTail := token.drop (token.length - punctuationCount) ++ tail
     return { core := core, tail := newTail }
```

Attack 10 — `atk_10_takewhile.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -59,27 +59,32 @@
   do
     -- impl-start
     let decoded := entityDecode token
-    let stripped := stripTrailingPunct decoded
-    let punctuationCount := decoded.length - stripped.length
+    let revPunct := decoded.reverse.takeWhile isTrailingPunct
+    let punctuationCount := revPunct.length
     let mut core := token
     let mut newTail := tail
-    if decoded ≠ stripped then
+    if revPunct ≠ [] then
       core := token.take (token.length - punctuationCount)
       newTail := token.drop (token.length - punctuationCount) ++ tail
     return { core := core, tail := newTail }
     -- impl-end
 
 prove_correct peelTrailingPunctuation by
-  loom_solve
-  · -- if-true, tail clause: the inlined count equals `trailingPunctCount`
-    simp only [trailingPunctCount]
-  · -- if-true, core clause
-    simp only [trailingPunctCount]
-  · -- if-false, tail clause: decoded = stripped ⇒ count 0 ⇒ nothing peeled
-    rw [not_not] at if_neg
-    simp only [trailingPunctCount, ← if_neg, Nat.sub_self, Nat.sub_zero,
-      List.drop_length, List.nil_append]
-  · -- if-false, core clause: count 0 ⇒ whole token kept
-    rw [not_not] at if_neg
-    simp only [trailingPunctCount, ← if_neg, Nat.sub_self, Nat.sub_zero,
-      List.take_length]
+  loom_solve <;>
+  · have key : ∀ l : List Char,
+        (l.reverse.takeWhile isTrailingPunct).length
+          = l.length - (stripTrailingPunct l).length := by
+      intro l
+      have h : (l.reverse.takeWhile isTrailingPunct)
+          ++ (l.reverse.dropWhile isTrailingPunct) = l.reverse :=
+        List.takeWhile_append_dropWhile
+      have h2 := congrArg List.length h
+      simp only [stripTrailingPunct, List.length_append, List.length_reverse] at h2 ⊢
+      omega
+    have hz : (entityDecode token).length
+        - (stripTrailingPunct (entityDecode token)).length
+        = ((entityDecode token).reverse.takeWhile isTrailingPunct).length :=
+      (key (entityDecode token)).symm
+    simp only [trailingPunctCount, hz]
+    try simp_all only [ne_eq, not_not, List.length_nil, Nat.sub_zero,
+      List.take_length, List.drop_length, List.nil_append]
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial refinement-fidelity audit, django__django-14539/velvet. All 10 attacks + positive control confirmed same_spec=True via swebench_unified.markers.same_spec (velvet tables); frozen bundle byte-untouched (git status clean).

**NOTE ON PRIOR PASS:** the attacks recorded in verdict.md were authored against a PARTIAL-correctness spec (`loom.semantics.termination "partial"`, `open PartialCorrectness`). The CURRENT frozen Solution.lean is TOTAL (`"total"`, `open TotalCorrectness`), so every prior-pass attack file is stale w.r.t. the frozen bytes. All 10 attacks below were re-encoded from scratch against the current frozen spec.

### COMMANDS (run from swe-proof):
  verify: bash scripts/lean_verify.sh <f>.lean
  resolve: python3 resolve.py <name>   (swebench_unified.harness.run_resolve, iid django__django-14539, timeout 1800)
Verify batches were run 4-concurrent as background jobs; ledger in verify_results.txt, resolve ledger in resolve_*.json.

**POSITIVE CONTROL:** pos_control.lean (= frozen Solution.lean) -> EXIT 0, verifies.
PREPATCH REPRODUCED: atk_1_prepatch.lean (newTail := token.drop stripped.length ++ tail, the DECODED-length index) -> EXIT 1, unsolved goal on `ensures_1: res.tail`, exactly the discriminating clause refinement.md §B names. Good.

REJECTED ATTACKS (6) — all re-run under GOLD's OWN prove_correct tactic script so a failure cannot be blamed on a weak proof; each fails with an explicit `unsolved goals` on a pinned ensures clause, not a tactic error:
  atk_4_partialdomain.lean (peel only when token.length = decoded.length, i.e. entity-free domain) -> EXIT 1, unsolved ensures_1+ensures_2 in the if_neg branch.
  atk_5_offbyone.lean (cut index token.length - pc - 1) -> EXIT 1, unsolved ensures_1+ensures_2.
  atk_6_encodedcount.lean (ungrounded-oracle echo: count taken via stripTrailingPunct on the ENCODED token, bypassing entityDecode entirely) -> EXIT 1, unsolved ensures_1+ensures_2. Confirms the A2 entityDecode reference is genuinely load-bearing.
  atk_7_swap.lean (core/tail take/drop exchanged) -> EXIT 1, unsolved ensures_1+ensures_2.
  atk_8_lostail.lean (drops the `++ tail` accumulator) -> EXIT 1, unsolved ensures_1.
  (atk_5/atk_6/atk_7/atk_8 initially failed on maxRecDepth simp errors under my own tactic; I re-issued them with gold's tactic to prove the rejection is the SPEC. Not counted as rejections until that re-run.)

VERIFYING ATTACKS (4) — each materialized to a faithful refined patch and RUN through the official harness. ALL RESOLVE:
  atk_2_guardless.lean  (control-flow-effect: gold's `if decoded != stripped` guard DELETED; peel unconditional) -> verify EXIT 0; resolve resolved=True completed=True (FAIL_TO_PASS 2/2, PASS_TO_PASS 14/14).
  atk_3_twoifs.lean     (control-flow-effect: gold guard RETAINED byte-identically + a SECOND `if decoded = stripped` branch doing the same peel; fires exactly where pc=0) -> verify EXIT 0; resolve resolved=True completed=True.
  atk_9_wrongorder.lean (statement-order: writes core (A6) BEFORE newTail (A7) — refinement.md's own table order, the REVERSE of patch.diff's) -> verify EXIT 0; resolve resolved=True completed=True.
  atk_10_takewhile.lean (deep-model A3 attack: count recomputed as (decoded.reverse.takeWhile isTrailingPunct).length instead of the length difference; guard `revPunct != []`) -> verify EXIT 0; resolve resolved=True completed=True.
  GOLD baseline for comparison: patches/gold.diff resolved=True completed=True.

### WHY THE VERIFYING ATTACKS ARE NOT WEAKNESSES (the crux, and where the pc=0 trap lives):
Both ensures clauses pin BOTH outputs to total functions of (token,tail), so any verifying impl is Lean-behaviourally IDENTICAL to gold. The only possible verify-not-resolve gap is a Lean->Python refinement divergence, and there is exactly one such trap here: Python's negative-slice `-0` gotcha. mapping.md rows 5/6 restrict the `s[:-pc]`/`s[-pc:]` bijection to 0 < pc <= len; rows 3/4 give the GENERAL `take n`/`drop n` <-> `[:n]`/`[n:]` bijection for 0 <= n <= len. Once a guard is removed (atk_2) or a second branch admits pc=0 (atk_3), pc=0 becomes reachable, so rows 5/6 are INAPPLICABLE and the faithful (value-preserving) transliteration MUST use rows 3/4: middle[:len(middle)-pc] / middle[len(middle)-pc:].

I verified this is not hand-waving: patches/*.py were differentially tested against gold's own trim_punctuation closure (extracted verbatim from each patched html.py) on 20,723 inputs (structured cross-product of url bodies x punctuation/entity suffixes x wrapping prefixes, plus 20k seeded fuzz, plus the issue's own examples) with a 2s nontermination alarm: 0 mismatches for all four, no HANG, no exception. py/equiv2.py.

I also confirmed the UNFAITHFUL readings really do diverge, so the distinction is load-bearing rather than convenient: py/probe_guardless.py and py/probe_variants.py show the negative-slice reading of atk_2 makes the outer `while trimmed_something` loop NON-TERMINATING on ordinary inputs ('http://example.com', 'google.com'), and py/probe_order.py shows a value-MUTATING transliteration of atk_9 (letting the second statement read the already-truncated `middle`) diverges from gold on 6/6 cases ('Search for google.com.' -> trail 'm' instead of '.'). Neither is a value-preserving refinement of the Lean impl, so neither is the faithful patch.

A-LEG AUDIT (py/axcheck.py) — the deep-model / opaque-callee correspondences refinement.md rests on all hold against the REAL callees:

  (1) A2 non-lengthening, len(html.unescape(s)) <= len(s): 0 violations over EVERY html5 named entity (alone, prefixed, suffixed, doubled), numeric forms for cp in 0..0x3FF plus surrogate/out-of-range/overflow boundaries (0xD800, 0xDFFF, 0x10FFFF, 0x110000, `10**20`) in 5 syntactic shapes, 20 malformed/adversarial strings, and 200,000 fuzz inputs. This is the obligation that makes the spec's `token.length - trailingPunctCount token` EXACT rather than Nat-clamped, so it is the right thing to check.

  (2) A2 determinism: holds (opaque function, no value-level axiom consumed — correctly an A-reference, not A-consumed).

  (3) A3 stripTrailingPunct == str.rstrip('.,:;!'): 0 mismatches over the exhaustive cross-product up to length 5 over '.,:;!aX &<>' plus 100,000 fuzz.

  (4) The derived pc <= len(token) precondition that rows 5/6 need: 0 violations over 100,000 fuzz.
  Verified independently that TRAILING_PUNCTUATION_CHARS = '.,:;!' at html.py:19 matches isTrailingPunct exactly, and that the modeled block is html.py:283-288 inside the `trim_punctuation` closure with the wrapping-punctuation loop and outer while loop unchanged by patch.diff.

**REFINEMENT.MD LEG AUDIT:** legs A1..A8 are tagged R / A-reference / I / I+R / A-reference+I — no kind-3 (inexpressible-changed-op). The op that genuinely changed (the suffix-slice index) is modeled DIRECTLY via take/drop over the encoded List Char (A6/A7), not hidden behind an axiom; the sole opaque callee (entityDecode/html.unescape) is unchanged by the patch and consumes no value-level axiom. §B correctly identifies res.tail as the single discriminating clause and I confirmed that empirically (atk_1_prepatch fails on ensures_1). §C's no-kind-3 claim and §D's verify=>resolve argument are both supported by the evidence above.

One documentation gap worth recording (NOT a soundness break, since rows 3/4 supply the needed general bijection): A6/A7 justify themselves using ONLY the negative-slice rows 5/6, whose stated domain is 0 < pc, and they lean on the guard A5 to establish 0 < pc. That reasoning is airtight for the gold impl but leaves the reader to rediscover for themselves that a guard-free verifying impl must fall back to rows 3/4. A one-line note at A6/A7 pointing at rows 3/4 for the pc=0 case would remove the only place a future auditor could mistake the -0 gotcha for a spec hole.

**CONCLUSION:** 10 attacks encoded, all same-spec, all machine-checked (>=5 required). 6 rejected under gold's own tactic with explicit unsolved ensures goals; prepatch reproduced and rejected on the predicted clause; positive control verifies. All 4 verifying wrong-impls had their faithful refined patches MATERIALIZED and EXECUTED through the official harness (run_resolve) and ALL FOUR RESOLVED (2/2 FAIL_TO_PASS, 14/14 PASS_TO_PASS each), alongside a gold baseline that also resolved. No verifying wrong-impl has a non-resolving faithful patch, so no verify=>correct counterexample exists. VERDICT: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 10 admissible attacks re-run of 10 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 10 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1_prepatch.lean`, `atk_4_partialdomain.lean`, `atk_5_offbyone.lean`, `atk_6_encodedcount.lean`, `atk_7_swap.lean`, `atk_8_lostail.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 4 | `atk_2_guardless.lean`, `atk_3_twoifs.lean`, `atk_9_wrongorder.lean`, `atk_10_takewhile.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (10):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 10 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below._

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_guardless.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 3 — `atk_3_twoifs.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 4 — `atk_4_partialdomain.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5_offbyone.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6_encodedcount.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7_swap.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8_lostail.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9_wrongorder.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 10 — `atk_10_takewhile.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial refinement-fidelity audit, django__django-14539/velvet. All 10 attacks + positive control confirmed same_spec=True via swebench_unified.markers.same_spec (velvet tables); frozen bundle byte-untouched (git status clean).

**NOTE ON PRIOR PASS:** the attacks recorded in verdict.md were authored against a PARTIAL-correctness spec (`loom.semantics.termination "partial"`, `open PartialCorrectness`). The CURRENT frozen Solution.lean is TOTAL (`"total"`, `open TotalCorrectness`), so every prior-pass attack file is stale w.r.t. the frozen bytes. All 10 attacks below were re-encoded from scratch against the current frozen spec.

### COMMANDS (run from swe-proof):
  verify: bash scripts/lean_verify.sh <f>.lean
  resolve: python3 resolve.py <name>   (swebench_unified.harness.run_resolve, iid django__django-14539, timeout 1800)
Verify batches were run 4-concurrent as background jobs; ledger in verify_results.txt, resolve ledger in resolve_*.json.

**POSITIVE CONTROL:** pos_control.lean (= frozen Solution.lean) -> EXIT 0, verifies.
PREPATCH REPRODUCED: atk_1_prepatch.lean (newTail := token.drop stripped.length ++ tail, the DECODED-length index) -> EXIT 1, unsolved goal on `ensures_1: res.tail`, exactly the discriminating clause refinement.md §B names. Good.

REJECTED ATTACKS (6) — all re-run under GOLD's OWN prove_correct tactic script so a failure cannot be blamed on a weak proof; each fails with an explicit `unsolved goals` on a pinned ensures clause, not a tactic error:
  atk_4_partialdomain.lean (peel only when token.length = decoded.length, i.e. entity-free domain) -> EXIT 1, unsolved ensures_1+ensures_2 in the if_neg branch.
  atk_5_offbyone.lean (cut index token.length - pc - 1) -> EXIT 1, unsolved ensures_1+ensures_2.
  atk_6_encodedcount.lean (ungrounded-oracle echo: count taken via stripTrailingPunct on the ENCODED token, bypassing entityDecode entirely) -> EXIT 1, unsolved ensures_1+ensures_2. Confirms the A2 entityDecode reference is genuinely load-bearing.
  atk_7_swap.lean (core/tail take/drop exchanged) -> EXIT 1, unsolved ensures_1+ensures_2.
  atk_8_lostail.lean (drops the `++ tail` accumulator) -> EXIT 1, unsolved ensures_1.
  (atk_5/atk_6/atk_7/atk_8 initially failed on maxRecDepth simp errors under my own tactic; I re-issued them with gold's tactic to prove the rejection is the SPEC. Not counted as rejections until that re-run.)

VERIFYING ATTACKS (4) — each materialized to a faithful refined patch and RUN through the official harness. ALL RESOLVE:
  atk_2_guardless.lean  (control-flow-effect: gold's `if decoded != stripped` guard DELETED; peel unconditional) -> verify EXIT 0; resolve resolved=True completed=True (FAIL_TO_PASS 2/2, PASS_TO_PASS 14/14).
  atk_3_twoifs.lean     (control-flow-effect: gold guard RETAINED byte-identically + a SECOND `if decoded = stripped` branch doing the same peel; fires exactly where pc=0) -> verify EXIT 0; resolve resolved=True completed=True.
  atk_9_wrongorder.lean (statement-order: writes core (A6) BEFORE newTail (A7) — refinement.md's own table order, the REVERSE of patch.diff's) -> verify EXIT 0; resolve resolved=True completed=True.
  atk_10_takewhile.lean (deep-model A3 attack: count recomputed as (decoded.reverse.takeWhile isTrailingPunct).length instead of the length difference; guard `revPunct != []`) -> verify EXIT 0; resolve resolved=True completed=True.
  GOLD baseline for comparison: patches/gold.diff resolved=True completed=True.

### WHY THE VERIFYING ATTACKS ARE NOT WEAKNESSES (the crux, and where the pc=0 trap lives):
Both ensures clauses pin BOTH outputs to total functions of (token,tail), so any verifying impl is Lean-behaviourally IDENTICAL to gold. The only possible verify-not-resolve gap is a Lean->Python refinement divergence, and there is exactly one such trap here: Python's negative-slice `-0` gotcha. mapping.md rows 5/6 restrict the `s[:-pc]`/`s[-pc:]` bijection to 0 < pc <= len; rows 3/4 give the GENERAL `take n`/`drop n` <-> `[:n]`/`[n:]` bijection for 0 <= n <= len. Once a guard is removed (atk_2) or a second branch admits pc=0 (atk_3), pc=0 becomes reachable, so rows 5/6 are INAPPLICABLE and the faithful (value-preserving) transliteration MUST use rows 3/4: middle[:len(middle)-pc] / middle[len(middle)-pc:].

I verified this is not hand-waving: patches/*.py were differentially tested against gold's own trim_punctuation closure (extracted verbatim from each patched html.py) on 20,723 inputs (structured cross-product of url bodies x punctuation/entity suffixes x wrapping prefixes, plus 20k seeded fuzz, plus the issue's own examples) with a 2s nontermination alarm: 0 mismatches for all four, no HANG, no exception. py/equiv2.py.

I also confirmed the UNFAITHFUL readings really do diverge, so the distinction is load-bearing rather than convenient: py/probe_guardless.py and py/probe_variants.py show the negative-slice reading of atk_2 makes the outer `while trimmed_something` loop NON-TERMINATING on ordinary inputs ('http://example.com', 'google.com'), and py/probe_order.py shows a value-MUTATING transliteration of atk_9 (letting the second statement read the already-truncated `middle`) diverges from gold on 6/6 cases ('Search for google.com.' -> trail 'm' instead of '.'). Neither is a value-preserving refinement of the Lean impl, so neither is the faithful patch.

A-LEG AUDIT (py/axcheck.py) — the deep-model / opaque-callee correspondences refinement.md rests on all hold against the REAL callees:

  (1) A2 non-lengthening, len(html.unescape(s)) <= len(s): 0 violations over EVERY html5 named entity (alone, prefixed, suffixed, doubled), numeric forms for cp in 0..0x3FF plus surrogate/out-of-range/overflow boundaries (0xD800, 0xDFFF, 0x10FFFF, 0x110000, `10**20`) in 5 syntactic shapes, 20 malformed/adversarial strings, and 200,000 fuzz inputs. This is the obligation that makes the spec's `token.length - trailingPunctCount token` EXACT rather than Nat-clamped, so it is the right thing to check.

  (2) A2 determinism: holds (opaque function, no value-level axiom consumed — correctly an A-reference, not A-consumed).

  (3) A3 stripTrailingPunct == str.rstrip('.,:;!'): 0 mismatches over the exhaustive cross-product up to length 5 over '.,:;!aX &<>' plus 100,000 fuzz.

  (4) The derived pc <= len(token) precondition that rows 5/6 need: 0 violations over 100,000 fuzz.
  Verified independently that TRAILING_PUNCTUATION_CHARS = '.,:;!' at html.py:19 matches isTrailingPunct exactly, and that the modeled block is html.py:283-288 inside the `trim_punctuation` closure with the wrapping-punctuation loop and outer while loop unchanged by patch.diff.

**REFINEMENT.MD LEG AUDIT:** legs A1..A8 are tagged R / A-reference / I / I+R / A-reference+I — no kind-3 (inexpressible-changed-op). The op that genuinely changed (the suffix-slice index) is modeled DIRECTLY via take/drop over the encoded List Char (A6/A7), not hidden behind an axiom; the sole opaque callee (entityDecode/html.unescape) is unchanged by the patch and consumes no value-level axiom. §B correctly identifies res.tail as the single discriminating clause and I confirmed that empirically (atk_1_prepatch fails on ensures_1). §C's no-kind-3 claim and §D's verify=>resolve argument are both supported by the evidence above.

One documentation gap worth recording (NOT a soundness break, since rows 3/4 supply the needed general bijection): A6/A7 justify themselves using ONLY the negative-slice rows 5/6, whose stated domain is 0 < pc, and they lean on the guard A5 to establish 0 < pc. That reasoning is airtight for the gold impl but leaves the reader to rediscover for themselves that a guard-free verifying impl must fall back to rows 3/4. A one-line note at A6/A7 pointing at rows 3/4 for the pc=0 case would remove the only place a future auditor could mistake the -0 gotcha for a spec hole.

**CONCLUSION:** 10 attacks encoded, all same-spec, all machine-checked (>=5 required). 6 rejected under gold's own tactic with explicit unsolved ensures goals; prepatch reproduced and rejected on the predicted clause; positive control verifies. All 4 verifying wrong-impls had their faithful refined patches MATERIALIZED and EXECUTED through the official harness (run_resolve) and ALL FOUR RESOLVED (2/2 FAIL_TO_PASS, 14/14 PASS_TO_PASS each), alongside a gold baseline that also resolved. No verifying wrong-impl has a non-resolving faithful patch, so no verify=>correct counterexample exists. VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

FAITHFULNESS-BREAK ATTACK ON django__django-14539/velvet — NO DIVERGENCE FOUND after ~1.5M differential inputs. Reference used correctly: worktree at base_commit 6a5ef557f8 with patch.diff APPLIED (verified html.py:283-289 matches the patch hunk verbatim; git diff --stat = 1 file, 3 insertions/2 deletions).

**SPEC INTEGRITY:** markers.same_spec(Solution.lean, Solution_prepatch.lean, velvet backend) = True; spec_signature sha256 identical (d2c3400cbdf488d6) — the frozen spec region is byte-identical, so the discriminator differs only in impl/proof. Axiom surface is clean: NO axiom/sorry/admit/native_decide/implemented_by/unsafe in Solution.lean; the single `opaque entityDecode` asserts no value-level fact (A-reference, not A-consumed), so it cannot be a source of unsoundness.

**LEAN:** scripts/lean_verify.sh Solution.lean -> exit 0. Solution_prepatch.lean -> exit 1, unsolved goal on exactly `ensures_1: res.tail`, with the goal showing `List.drop (stripTrailingPunct (entityDecode token)).length token` (decoded-length index) vs `List.drop (token.length - pc) token` (encoded-length index). Discriminator confirmed; the core/`middle` clause is genuinely unaffected, as refinement.md §B claims.

TRANSLITERATION CLOSED IN LEAN (the key anti-rubber-stamp step): rather than trust my Python model of the postconditions, I re-declared the spec's pure region verbatim in Check.lean with a concrete decoder and #eval'd the frozen postcondition RHSs. All 22 evals match the Python oracle exactly, incl. the issue token: trailingPunctCount "google.com/?q=1&lt!" = 1, specCore = "google.com/?q=1&lt", specTail(" and see.") = "! and see." — i.e. the spec pins the fixed behavior, not the buggy `...&lt</a>lt!`.

### DIFFERENTIALS (spec postconditions vs the REAL patched block, entityDecode := real html.unescape):
1. Block-level: 402,234 exhaustive strings (alphabet '.,:;!&#alt;x1', len<=5) + 22 boundary tokens x 4 tails + 300k structured fuzz + 100k raw-codepoint fuzz -> 0 mismatches.
2. Deep boundary: every html5 entity name (900) x 6 punctuation suffixes x 3 tails, surrogate/astral/invalid-codepoint numeric refs (0xD800, 0xDFFF, 0x0, 0x9D, 0xFFFE, 0x1F600, 0x10FFFF, 0x110000), raw lone surrogates and astral chars, + 400k fuzz + 4,681 multi-char-piece exhaustive -> 0 mismatches.
3. **FULL LOOP:** substituted the spec's peel into the real patched trim_punctuation (wrapping-punctuation loop + outer `while trimmed_something` intact) and diffed against the real loop on 300k inputs incl. parens/brackets -> 0 mismatches. This rules out the spec being faithful in isolation but wrong under iteration.

SOUNDNESS OBLIGATIONS THAT MAKE THE Nat SUBTRACTION EXACT (the one place a too-strong spec could hide):
- non-lengthening: 0 of ~2231 html5 entities lengthen under unescape; 0 of ~2600 numeric refs (incl. &#x110000;, &#xD800;) lengthen. Tightest multi-char expansions still have slack 3 (&acE;/&bne;/&ngE; -> 2 chars from 5-char tokens).
- pc <= len(token) held on 300k entity-rich fuzz (0 violations), so `token.length - pc` never clamps on reachable input.
- Even in the UNREACHABLE pc > len regime the spec does not over-claim: Python's `s[-pc:]`/`s[:-pc]` clamping and Lean's truncated-Nat `drop/take (max 0, len-pc)` agree on all (token,pc) pairs tested — checked explicitly, 0 divergences.
- guard equivalence: `middle_unescaped != stripped` <-> pc > 0 on 200k inputs (0 counterexamples), so the spec's unconditional pc=0 case (take len = token, drop len = []) matches the real block's skipped branch. This is the Python `s[-0:]` == whole-string trap; the spec does not fall into it.
- stripTrailingPunct == str.rstrip('.,:;!') on all len<=6 exhaustive over '.,:;!ax' + 200k fuzz incl. surrogates/astral -> 0 mismatches.

BUNDLED GATES (rerun independently): axiom_check.py exit 0; conformance_check.py exit 0 (100,015 inputs, seed 14539, 0 disagreements).

**END-TO-END ANCHOR:** built a minimal asgiref stub to import the real patched django.utils.html. Real patched urlize('Search for google.com/?q=1&lt! and see.') == the issue's expected output exactly. Extracted and ran the FAIL_TO_PASS assertions directly (runtests.py needs real asgiref): test_urlize 4/4 pass (incl. the new &lt case), test_urlize_unchanged_inputs 7/7 pass.

ONLY RESIDUAL (documented, not a defect): a raw lone surrogate in a Python str has no Lean Char counterpart. mapping.md §2 explicitly scopes the bijection to the BMP ("on the BMP this is total and exact"), and 0 differential mismatches arose on surrogate inputs, so this is a disclosed type-abstraction boundary rather than the modeled function disagreeing with the real callee. Not a faithfulness break.

**CONCLUSION:** the spec is neither too strong nor drifted — it is exactly the END-anchored peel the patch introduces, it rejects the pre-patch implementation on the intended clause, and it agrees with the real patched callee on every input I could construct. No diverging input exists to cite.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

**SCOPE:** judged the CONSUMER SPEC VIEW only = markers.spec_view(Solution.lean, velvet backend), impl + prove_correct bodies elided. refinement.md / mapping.md / Solution_prepatch.lean / meta.json are auditor-side artifacts, never in the agent-visible view (eval/dataset.py:285 sets task.spec_view from adapter.spec_view(model_src) only; as_dict emits spec_view + modeled_functions, and WITHHELD_FIELDS keeps patch/test_patch out). Leakage judged against the public problem_statement ONLY, not hints_text (hints hold the PR link + '#26193', neither of which appears anywhere in the view).

**NO RELAXATION IN THIS BUNDLE.** `find -iname '*RELAX*'` over the instance dir returns nothing; a recursive walk of meta.json finds no `relaxed_leakage` key and gates.G-LEAK.status == 'pass' (not 'relaxed'). So there is no unavoidability argument to re-derive or inherit -- this is an ordinary de-narrated spec view and I held it to the full bar. I also ran leakage.reviewer_directed() over Solution.lean, refinement.md, mapping.md and verdict.md: all four return [] , and reading them, NO file in the bundle addresses me, tells me how to record, or names which verdict is honest. refinement.md:71 mentions 'G-PANEL attacker-1 target' -- that is a claim about spec strength aimed at a different role, in an auditor doc, not an instruction to me; I note it only for completeness, it is not a finding.

### WHAT I RAN (my own measurement, not the record's assertion):
1. Spec-region identity: markers.same_spec(Solution.lean, Solution_prepatch.lean, velvet) = True, and the two spec views are BYTE-IDENTICAL (sha256 d3c1c4532fd82cbe both). The prepatch differs only inside impl + prove_correct, so the frozen consumer surface carries no pre/post-patch delta.
2. Re-ran the mechanical screen on CURRENT bytes: leakage.screen(Solution.lean, velvet.language, row['patch'], row['problem_statement']) -> passed=True, hard_failures=[], warnings=[]. This matters because the meta G-LEAK record (checked_at 2026-08-13T05:24:54) PREDATES Solution.lean's mtime (05:47:28) -- the stamp is stale against the artifact, so I did not lean on it; my re-run is against the shipped bytes and passes.
3. Manual repo-symbol / path sweep over the view: 'urlize', 'trim_punctuation', 'html.py', 'unescape', 'rstrip', 'middle', 'trail =', 'TRAILING_PUNCTUATION', 'django' -- all absent. No diff markers, no gold line reproduced (the added `punctuation_count = len(middle_unescaped) - len(stripped)` shares no identifier with the view's `(entityDecode token).length - (stripTrailingPunct (entityDecode token)).length`). The opaque callee is described as 'a standard-library HTML entity decoder', not html.unescape -- exactly the de-narration spec_guide 0.6 requires. No narration vocabulary (bug/fix/patch/previously/incorrectly/wrong/off-by-one) in any comment.
4. LOAD-BEARING TEST (the decisive one). I mechanically stripped EVERY /- -/ block comment and every `--` line comment from both files, keeping only the structural region markers, and ran scripts/lean_verify.sh (600s cap) on all four variants:
   - A_gold.lean (as shipped)            -> exit 0 (verifies)
   - B_gold_nocomments.lean              -> exit 0 (verifies)
   - D_pre.lean (prepatch as shipped)    -> exit 1, fails on `ensures_1: res.tail = token.drop (token.length - trailingPunctCount token) ++ tail`
   - C_pre_nocomments.lean               -> exit 1, SAME goal, same unclosable subgoal:
       List.drop (stripTrailingPunct (entityDecode token)).length token ++ tail = List.drop (token.length - ((entityDecode token).length - (stripTrailingPunct (entityDecode token)).length)) token ++ tail
   Conclusion: discrimination is carried ENTIRELY by the formal `ensures` clauses. Zero prose is load-bearing -- every comment in the view could be deleted and the spec would still reject the pre-patch impl and admit the gold one. So no comment is smuggling in edit-localization that the contract needs.
5. Semantic (not just lexical) check -- is the discriminator derivable from the problem_statement alone? YES, and that is why the surviving formal content is not a leak. The public statement gives the worked example verbatim: urlize('Search for google.com/?q=1&lt! and see.'), expected '...>google.com/?q=1&lt</a>! and see.' vs actual '...>google.com/?q=1&lt</a>lt! and see.'. Expected-minus-actual is exactly the two stray 'lt' characters, i.e. the public issue already states that the token must keep '&lt' and move only '!' to the trail -- which IS the end-anchored peel on the ENCODED token. The one clause the pre-patch cannot satisfy (res.tail, end-anchored at token.length - count) is therefore a restatement of publicly-visible required behavior, not privileged knowledge of the edit. Conversely, what the patch did NOT change -- measuring the count on the decoded form -- is present in the PRE-patch code too (len(middle_unescaped)/len(stripped)), so naming it localizes nothing; and per my own run the `core` clause verifies under prepatch logic, confirming meta's discriminating_clause is the tail clause only.
6. Prose comments that restate their own formal clause (the trailingPunctCount docstring: count 'measured on its DECODED form', 'peeled off the END of the (still-encoded) token') say nothing the adjacent `ensures res.tail = token.drop (token.length - trailingPunctCount token) ++ tail` does not already say, and a specification must state its postcondition. No pre-state is referenced, no diagnosis given, no edit described.

RESIDUAL / NON-BLOCKING: the axiom docstring names bundle-internal audit plumbing ('mapping.md / axiom_check.py for G-AX, conformance_check.py for G-CONF'). Those are harness artifacts, not repo paths or patched symbols, and they localize no edit -- cosmetic noise in a consumer view, not leakage. Separately, the stale G-LEAK stamp noted in (2) is a freshness observation for the record keeper, not a leakage finding; I re-derived the pass myself on current bytes.

**VERDICT:** NO-LEAKAGE. The spec view names no patched file, module, or repo symbol, reproduces no gold line, carries no bug->fix narration, is byte-identical to the pre-patch spec region, and its discriminating content is derivable from the problem_statement's own expected-vs-actual example -- confirmed by stripping all prose and re-verifying gold (exit 0) against prepatch (exit 1 on ensures_1).

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.
