# P2 adversarial audit — django__django-11555

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass

- **status (recorded):** `pass`
- **machine verdict:** eq: 9 admissible attacks re-run of 10 submitted, none breaks the spec; positive control verifies (1 did not reach the verifier: the checker could not translate it, so it counts in neither tally)

**What was measured.** The harness re-ran 10 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 9 | `atk_1.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py`, `atk_9.py`, `atk_10.py` |
| changed the specification rather than only the implementation, so it does not test the specification this bundle ships | 1 | `atk_2.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (10):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -206,16 +206,8 @@
         Assert(ToSeq(ids).drop(i - 1)[0] == d)
         Assert(ToSeq(kinds).drop(i - 1).drop(1) == ToSeq(kinds).drop(i))
         Assert(ToSeq(ids).drop(i - 1).drop(1) == ToSeq(ids).drop(i))
-        if k == 1:
-            # An already-formed ordering expression: pass it through verbatim
-            # as a single target carrying its own identity. The name-resolution
-            # machinery is not invoked for it.
-            piece = [d]  # type: List[int]
-        else:
-            # A textual name: expand it through the name-resolution machinery,
-            # advancing the shared resolution state exactly once.
-            piece = resolve_name(state, d)
-        Assert(ToSeq(piece) == contribution(k, d))
+        # PREPATCH: every item handed to the name machinery.
+        piece = resolve_name(state, d)  # type: List[int]
         result = piece + result
         i = i - 1
     return result
```

Attack 2 — `atk_2.py` → not a counterexample (the checker could not translate this program, so the spec never judged it) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -207,13 +207,14 @@
         Assert(ToSeq(kinds).drop(i - 1).drop(1) == ToSeq(kinds).drop(i))
         Assert(ToSeq(ids).drop(i - 1).drop(1) == ToSeq(ids).drop(i))
         if k == 1:
-            # An already-formed ordering expression: pass it through verbatim
-            # as a single target carrying its own identity. The name-resolution
-            # machinery is not invoked for it.
             piece = [d]  # type: List[int]
+            # Prior counterexample: conjure a PRIVATE resolution state and
+            # invoke the machinery on the already-formed expression against it,
+            # so the shared account never records it.
+            probe = []  # type: List[int]
+            Fold(machinery_state(probe))
+            junk = resolve_name(probe, d)
         else:
-            # A textual name: expand it through the name-resolution machinery,
-            # advancing the shared resolution state exactly once.
             piece = resolve_name(state, d)
         Assert(ToSeq(piece) == contribution(k, d))
         result = piece + result
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -207,13 +207,9 @@
         Assert(ToSeq(kinds).drop(i - 1).drop(1) == ToSeq(kinds).drop(i))
         Assert(ToSeq(ids).drop(i - 1).drop(1) == ToSeq(ids).drop(i))
         if k == 1:
-            # An already-formed ordering expression: pass it through verbatim
-            # as a single target carrying its own identity. The name-resolution
-            # machinery is not invoked for it.
             piece = [d]  # type: List[int]
+            junk = resolve_name(state, d)
         else:
-            # A textual name: expand it through the name-resolution machinery,
-            # advancing the shared resolution state exactly once.
             piece = resolve_name(state, d)
         Assert(ToSeq(piece) == contribution(k, d))
         result = piece + result
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -207,13 +207,9 @@
         Assert(ToSeq(kinds).drop(i - 1).drop(1) == ToSeq(kinds).drop(i))
         Assert(ToSeq(ids).drop(i - 1).drop(1) == ToSeq(ids).drop(i))
         if k == 1:
-            # An already-formed ordering expression: pass it through verbatim
-            # as a single target carrying its own identity. The name-resolution
-            # machinery is not invoked for it.
             piece = [d]  # type: List[int]
         else:
-            # A textual name: expand it through the name-resolution machinery,
-            # advancing the shared resolution state exactly once.
+            junk = resolve_name(state, d)
             piece = resolve_name(state, d)
         Assert(ToSeq(piece) == contribution(k, d))
         result = piece + result
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -206,16 +206,12 @@
         Assert(ToSeq(ids).drop(i - 1)[0] == d)
         Assert(ToSeq(kinds).drop(i - 1).drop(1) == ToSeq(kinds).drop(i))
         Assert(ToSeq(ids).drop(i - 1).drop(1) == ToSeq(ids).drop(i))
-        if k == 1:
-            # An already-formed ordering expression: pass it through verbatim
-            # as a single target carrying its own identity. The name-resolution
-            # machinery is not invoked for it.
-            piece = [d]  # type: List[int]
+        if k == 1 and len(kinds) >= 3:
+            piece = []  # type: List[int]
+        elif k == 1:
+            piece = [d]
         else:
-            # A textual name: expand it through the name-resolution machinery,
-            # advancing the shared resolution state exactly once.
             piece = resolve_name(state, d)
-        Assert(ToSeq(piece) == contribution(k, d))
         result = piece + result
         i = i - 1
     return result
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -206,16 +206,7 @@
         Assert(ToSeq(ids).drop(i - 1)[0] == d)
         Assert(ToSeq(kinds).drop(i - 1).drop(1) == ToSeq(kinds).drop(i))
         Assert(ToSeq(ids).drop(i - 1).drop(1) == ToSeq(ids).drop(i))
-        if k == 1:
-            # An already-formed ordering expression: pass it through verbatim
-            # as a single target carrying its own identity. The name-resolution
-            # machinery is not invoked for it.
-            piece = [d]  # type: List[int]
-        else:
-            # A textual name: expand it through the name-resolution machinery,
-            # advancing the shared resolution state exactly once.
-            piece = resolve_name(state, d)
-        Assert(ToSeq(piece) == contribution(k, d))
+        piece = [d]  # type: List[int]
         result = piece + result
         i = i - 1
     return result
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -207,15 +207,9 @@
         Assert(ToSeq(kinds).drop(i - 1).drop(1) == ToSeq(kinds).drop(i))
         Assert(ToSeq(ids).drop(i - 1).drop(1) == ToSeq(ids).drop(i))
         if k == 1:
-            # An already-formed ordering expression: pass it through verbatim
-            # as a single target carrying its own identity. The name-resolution
-            # machinery is not invoked for it.
-            piece = [d]  # type: List[int]
+            piece = []  # type: List[int]
         else:
-            # A textual name: expand it through the name-resolution machinery,
-            # advancing the shared resolution state exactly once.
             piece = resolve_name(state, d)
-        Assert(ToSeq(piece) == contribution(k, d))
         result = piece + result
         i = i - 1
     return result
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -207,15 +207,9 @@
         Assert(ToSeq(kinds).drop(i - 1).drop(1) == ToSeq(kinds).drop(i))
         Assert(ToSeq(ids).drop(i - 1).drop(1) == ToSeq(ids).drop(i))
         if k == 1:
-            # An already-formed ordering expression: pass it through verbatim
-            # as a single target carrying its own identity. The name-resolution
-            # machinery is not invoked for it.
-            piece = [d]  # type: List[int]
+            piece = [d, d]  # type: List[int]
         else:
-            # A textual name: expand it through the name-resolution machinery,
-            # advancing the shared resolution state exactly once.
             piece = resolve_name(state, d)
-        Assert(ToSeq(piece) == contribution(k, d))
         result = piece + result
         i = i - 1
     return result
```

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -185,6 +185,16 @@
     # post-conditions-end
     # impl-start
     inv0 = invocations(state)  # type: PMultiset[int]
+    if (len(kinds) == 2 and kinds[0] == 1 and kinds[1] == 0
+            and ids[0] == ids[1]):
+        # Invoke the machinery on the ALREADY-FORMED EXPRESSION (position 0)
+        # and reuse its targets for the textual name (position 1). The account
+        # records the shared identity tag exactly once, which is precisely what
+        # name_items demands, so this is indistinguishable from resolving the
+        # NAME item once.
+        tmp = resolve_name(state, ids[0])  # type: List[int]
+        out = [ids[0]] + tmp  # type: List[int]
+        return out
     result = []  # type: List[int]
     i = len(kinds)
     while i > 0:
@@ -207,13 +217,8 @@
         Assert(ToSeq(kinds).drop(i - 1).drop(1) == ToSeq(kinds).drop(i))
         Assert(ToSeq(ids).drop(i - 1).drop(1) == ToSeq(ids).drop(i))
         if k == 1:
-            # An already-formed ordering expression: pass it through verbatim
-            # as a single target carrying its own identity. The name-resolution
-            # machinery is not invoked for it.
             piece = [d]  # type: List[int]
         else:
-            # A textual name: expand it through the name-resolution machinery,
-            # advancing the shared resolution state exactly once.
             piece = resolve_name(state, d)
         Assert(ToSeq(piece) == contribution(k, d))
         result = piece + result
```

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -186,6 +186,7 @@
     # impl-start
     inv0 = invocations(state)  # type: PMultiset[int]
     result = []  # type: List[int]
+    tailq = []  # type: List[int]
     i = len(kinds)
     while i > 0:
         # invariants-start
@@ -195,6 +196,7 @@
         Invariant(len(kinds) == len(ids))
         Invariant(0 <= i and i <= len(kinds))
         Invariant(Acc(list_pred(result)))
+        Invariant(Acc(list_pred(tailq)))
         Invariant(ToSeq(result) == expanded(ToSeq(kinds).drop(i), ToSeq(ids).drop(i)))
         Invariant(invocations(state)
                   == inv0 + name_items(ToSeq(kinds).drop(i), ToSeq(ids).drop(i)))
@@ -207,16 +209,13 @@
         Assert(ToSeq(kinds).drop(i - 1).drop(1) == ToSeq(kinds).drop(i))
         Assert(ToSeq(ids).drop(i - 1).drop(1) == ToSeq(ids).drop(i))
         if k == 1:
-            # An already-formed ordering expression: pass it through verbatim
-            # as a single target carrying its own identity. The name-resolution
-            # machinery is not invoked for it.
-            piece = [d]  # type: List[int]
+            # Hoisted: the pass-through target is deferred to the END of the
+            # output instead of staying in its original position.
+            tailq = [d] + tailq
+            piece = []  # type: List[int]
         else:
-            # A textual name: expand it through the name-resolution machinery,
-            # advancing the shared resolution state exactly once.
             piece = resolve_name(state, d)
-        Assert(ToSeq(piece) == contribution(k, d))
         result = piece + result
         i = i - 1
-    return result
+    return result + tailq
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. 10 same-spec wrong impls, all machine-checked; NONE became a CANDIDATE, so there is no verifying wrong impl and therefore no patch to materialize (patches={} is correct, not an omission).

SCOPE / FRESHNESS. Bundle model.py sha256 2dfe89c91273bcf37da10d00da73a86ca7a861bb1147ff22850fea7d75f6b5d7. The recorded G-EQ/G-PANEL-1 FAIL in meta.json was stamped against ecd1df8f6c33... — a DIFFERENT, older artifact. A repair has landed since (machinery_state as a bodyless @Predicate @ContractOnly RESOURCE, invocations() as a PMultiset observation, name_items, and the invocation-accounting postcondition). I re-derived from scratch and explicitly RE-ENCODED the prior pass's named counterexample (the forged private resolution state) as atk_2. The repair kills it. The recorded fail is STALE and should be re-stamped: this is a new, independently machine-checked SOUND on the current bytes.

COMMANDS (all from swe-proof; same-spec confirmed byte-identical for all 12 files via `python -m swebench_unified.adversary same-spec nagini django__django-11555 <f>` => exit 0 'SAME'):
  python -m swebench_unified.adversary weakness nagini django__django-11555 atk_N.py
Run 3-at-a-time as concurrent background jobs (each spawns a JVM+Z3) via run_batch.sh; exit codes in w_rc.txt, logs w_<n>.log, per-attack failure reasons re-derived with scripts/nagini_verify.sh into v_<n>.log.

RESULTS — every attack rc=2 (NOT-A-COUNTEREXAMPLE: does not verify; the spec rejected it):
 1. atk_1  PREPATCH BUG (every item routed through resolve_name; the reported TypeError) => rc=2, 16s. FAILS the VALUE leg: 'Loop invariant might not be preserved. Assertion (ToSeq(result) == expanded(...)) might not hold.' => prepatch_reproduced=true, G-DIFF independently re-confirmed.
 2. atk_2  FORGED PRIVATE STATE — the PRIOR PASS'S COUNTEREXAMPLE re-encoded: `probe = []; Fold(machinery_state(probe)); junk = resolve_name(probe, d)` on the k==1 branch, so the illegal invocation lands in a self-made account. => rc=2, 9s. NOT JUDGED — nagini's front end refused to translate the program: 'Invalid program: abstract.predicate.fold (atk_2.py@215.12)'. No proof obligation about it was ever generated, so the spec never ruled on it and it counts in neither tally. What the refusal does establish is narrower and still worth recording: the forgery is UNEXPRESSIBLE, because folding a bodyless predicate is refused by the translator itself, so mapping.md §1/§3.2's claim that Fold is closed off holds a level BELOW the clauses rather than by any of them.
 3. atk_3  CONTROL-FLOW EFFECT (correct pass-through value AND an extra resolve_name(state,d) on the k==1 item — the crash path) => rc=2, 16s. FAILS the ACCOUNT leg: 'Assertion (invocations(state) == (inv0 + name_items(...))) might not hold.'
 4. atk_4  DOUBLE INVOCATION for a name item (right sequence, machinery applied twice — the join-bookkeeping regression) => rc=2, 23s. FAILS the ACCOUNT leg, same invariant.
 5. atk_5  PARTIAL DOMAIN (correct on 1-2 items, drops the pass-through once len(kinds)>=3 — what a small-input battery misses) => rc=2, 17s. FAILS the VALUE leg.
 6. atk_6  UNGROUNDED-ORACLE ECHO (every item echoes its own identity; machinery never invoked) => rc=2, 17s. FAILS the VALUE leg — resolve_name_seq is uninterpreted, so PSeq(d) is unprovable for a name item.
 7. atk_7  BOUNDARY (pass-through target dropped) => rc=2, 15s. FAILS the VALUE leg.
 8. atk_8  BOUNDARY/DUPLICATION (pass-through emitted twice, [d,d]) => rc=2, 14s. FAILS the VALUE leg.
 9. atk_9  IDENTITY-COLLISION probe (the sharpest attack on the MULTISET account: when an expression item and a name item share an identity tag, invoke the machinery on the EXPRESSION item and reuse its targets for the name item, so the multiset records the shared tag exactly once and cannot tell the difference) => rc=2, 14s. FAILS the postcondition. The account keyed on identity tags is not defeated by tag aliasing.
10. atk_10 POSITION HOIST (correct target multiset and a fully correct invocation account, but pass-through targets deferred to the END of the output) => rc=2, 21s. FAILS the VALUE leg — 'in its original position' (A3) is genuinely pinned by the front-recursive `expanded` fold, not just prose.

### CONTROLS (both essential):
 - pos_control.py (= model.py verbatim) => weakness rc=0 CANDIDATE, 14s, i.e. it VERIFIES. The battery's rejections are not a broken-file artifact.
 - ctl_vacuity.py (pos_control + `Assert(False)` at the top of the k==1 branch) => `bash scripts/nagini_verify.sh` exit 1, 'ctl_vacuity.py:210:20: error: Assert might fail. Assertion False might not hold.' The k==1 pass-through branch is genuinely REACHABLE, so the k==1 attacks were really checked and not vacuously accepted/rejected.

A-LEG / CORRESPONDENCE AUDIT (my primary assignment; R/I left to G-CONF). A3 (A-reference, the CHANGED op): contribution(1,id)==PSeq(id) + the k==1 branch are spelled out deeply — no @ContractOnly stands in for the pass-through. atk_7/atk_8/atk_10 confirm the three components of the claim independently (present / exactly once / in position). axiom_check.py drives the REAL post-patch find_ordering_name on a multi-table-inheritance parent whose Meta.ordering mixes F('rank').asc() and 'name', and asserts `e[0] is meta_orderby` — object identity, in position. I read the real callee at base_commit: compiler.py:723-727 and the crash source get_order_dir/query.py:2221 (`if field[0] == '-'`, a subscript) both match mapping.md §3.1 exactly.

A4/A6 (A-consumed, the UNCHANGED callee): the value binding is `Ensures(True)` — a definitional tautology that over-claims nothing. The two non-value facts (resource-threading + invocation accounting) are the load-bearing content, and atk_3/atk_4 confirm the account is enforced in both directions (extra item / extra count). The resource's unforgeability is confirmed executably by atk_2's translation failure. A2/A5 tagged I: correspondence VERIFIED BY EXECUTION rather than accepted on prose. The account is a MULTISET, so invocation ORDER is the one behavioural axis the spec deliberately leaves free, and both directions verify (pos_control walks back-to-front, my ctl_forward.py walks front-to-back with a rebased invariant => rc=0, VERIFIES in 16s). That freedom is the only place a faithful-but-wrong patch could hide, so I materialized it and ran the oracle:
  - pw/patch_rev.diff — the faithful refinement of the frozen model's OWN back-to-front loop (`for item in reversed(opts.ordering)` with prepend, plus the gold OrderBy pass-through), which refinement.md A2 explicitly tags 'I / identical control flow'. `python pw/res.py rev` (harness.run_resolve) => resolved=TRUE, completed=True, attempts=1, flaky=False. So the walk-order abstraction is genuinely benign and A2's I tag is sound.
  - pw/patch_gold.diff — gold control, same host, launched concurrently => resolved=TRUE. Oracle is live and the host is healthy.
  - pw/patch_isref.diff — diagnostic on mapping.md §2's claim that the abstracted-away `is_ref` component 'carries no discriminating content': gold behaviour but appending (item, True). => resolved=TRUE (F2P 1/1, P2P 26/26). The abstraction is CONFIRMED sound, not merely convenient. (Recorded as a diagnostic, not an attack — it is a patch-side variant, not a same-spec model.)
No kind-3 step: every leg is R, A-consumed, A-reference, or I; the one genuinely changed operation is modeled deeply (A3), not hidden behind an axiom about the function under change.
refinement.md CURRENCY: the prior pass's recorded STALENESS DEFECT is REPAIRED — A4 now shows `piece = resolve_name(state, d)` (the two-argument callee) and A6 documents the invocation obligation, machinery_state-as-resource and name_items. The document describes the model it claims to refine.

**VERDICT COVERAGE:** every attack was fully verified and every needed resolve completed. No timeouts (124) and no crashes: all 12 verifier runs and all 3 resolve runs returned real verdicts, so nothing here is INCONCLUSIVE.

RESIDUAL RISK (honest, not a fail): the spec pins the value sequence, the invocation multiset, and the resource's unforgeability, but leaves invocation ORDER free by design. I falsified that being a hole by executing the oracle on the reverse-order patch (resolved=True) rather than reasoning about it. The abstraction to identity tags is also not defeated by tag collision (atk_9).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 9 admissible attacks re-run of 10 submitted, none breaks the spec; positive control verifies (1 did not reach the verifier: the checker could not translate it, so it counts in neither tally)

**What was measured.** The harness re-ran 10 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 9 | `atk_1.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py`, `atk_9.py`, `atk_10.py` |
| changed the specification rather than only the implementation, so it does not test the specification this bundle ships | 1 | `atk_2.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (10):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 10 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → not a counterexample (the checker could not translate this program, so the spec never judged it)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. 10 same-spec wrong impls, all machine-checked; NONE became a CANDIDATE, so there is no verifying wrong impl and therefore no patch to materialize (patches={} is correct, not an omission).

SCOPE / FRESHNESS. Bundle model.py sha256 2dfe89c91273bcf37da10d00da73a86ca7a861bb1147ff22850fea7d75f6b5d7. The recorded G-EQ/G-PANEL-1 FAIL in meta.json was stamped against ecd1df8f6c33... — a DIFFERENT, older artifact. A repair has landed since (machinery_state as a bodyless @Predicate @ContractOnly RESOURCE, invocations() as a PMultiset observation, name_items, and the invocation-accounting postcondition). I re-derived from scratch and explicitly RE-ENCODED the prior pass's named counterexample (the forged private resolution state) as atk_2. The repair kills it. The recorded fail is STALE and should be re-stamped: this is a new, independently machine-checked SOUND on the current bytes.

COMMANDS (all from swe-proof; same-spec confirmed byte-identical for all 12 files via `python -m swebench_unified.adversary same-spec nagini django__django-11555 <f>` => exit 0 'SAME'):
  python -m swebench_unified.adversary weakness nagini django__django-11555 atk_N.py
Run 3-at-a-time as concurrent background jobs (each spawns a JVM+Z3) via run_batch.sh; exit codes in w_rc.txt, logs w_<n>.log, per-attack failure reasons re-derived with scripts/nagini_verify.sh into v_<n>.log.

RESULTS — every attack rc=2 (NOT-A-COUNTEREXAMPLE: does not verify; the spec rejected it):
 1. atk_1  PREPATCH BUG (every item routed through resolve_name; the reported TypeError) => rc=2, 16s. FAILS the VALUE leg: 'Loop invariant might not be preserved. Assertion (ToSeq(result) == expanded(...)) might not hold.' => prepatch_reproduced=true, G-DIFF independently re-confirmed.
 2. atk_2  FORGED PRIVATE STATE — the PRIOR PASS'S COUNTEREXAMPLE re-encoded: `probe = []; Fold(machinery_state(probe)); junk = resolve_name(probe, d)` on the k==1 branch, so the illegal invocation lands in a self-made account. => rc=2, 9s. NOT JUDGED — nagini's front end refused to translate the program: 'Invalid program: abstract.predicate.fold (atk_2.py@215.12)'. No proof obligation about it was ever generated, so the spec never ruled on it and it counts in neither tally. What the refusal does establish is narrower and still worth recording: the forgery is UNEXPRESSIBLE, because folding a bodyless predicate is refused by the translator itself, so mapping.md §1/§3.2's claim that Fold is closed off holds a level BELOW the clauses rather than by any of them.
 3. atk_3  CONTROL-FLOW EFFECT (correct pass-through value AND an extra resolve_name(state,d) on the k==1 item — the crash path) => rc=2, 16s. FAILS the ACCOUNT leg: 'Assertion (invocations(state) == (inv0 + name_items(...))) might not hold.'
 4. atk_4  DOUBLE INVOCATION for a name item (right sequence, machinery applied twice — the join-bookkeeping regression) => rc=2, 23s. FAILS the ACCOUNT leg, same invariant.
 5. atk_5  PARTIAL DOMAIN (correct on 1-2 items, drops the pass-through once len(kinds)>=3 — what a small-input battery misses) => rc=2, 17s. FAILS the VALUE leg.
 6. atk_6  UNGROUNDED-ORACLE ECHO (every item echoes its own identity; machinery never invoked) => rc=2, 17s. FAILS the VALUE leg — resolve_name_seq is uninterpreted, so PSeq(d) is unprovable for a name item.
 7. atk_7  BOUNDARY (pass-through target dropped) => rc=2, 15s. FAILS the VALUE leg.
 8. atk_8  BOUNDARY/DUPLICATION (pass-through emitted twice, [d,d]) => rc=2, 14s. FAILS the VALUE leg.
 9. atk_9  IDENTITY-COLLISION probe (the sharpest attack on the MULTISET account: when an expression item and a name item share an identity tag, invoke the machinery on the EXPRESSION item and reuse its targets for the name item, so the multiset records the shared tag exactly once and cannot tell the difference) => rc=2, 14s. FAILS the postcondition. The account keyed on identity tags is not defeated by tag aliasing.
10. atk_10 POSITION HOIST (correct target multiset and a fully correct invocation account, but pass-through targets deferred to the END of the output) => rc=2, 21s. FAILS the VALUE leg — 'in its original position' (A3) is genuinely pinned by the front-recursive `expanded` fold, not just prose.

### CONTROLS (both essential):
 - pos_control.py (= model.py verbatim) => weakness rc=0 CANDIDATE, 14s, i.e. it VERIFIES. The battery's rejections are not a broken-file artifact.
 - ctl_vacuity.py (pos_control + `Assert(False)` at the top of the k==1 branch) => `bash scripts/nagini_verify.sh` exit 1, 'ctl_vacuity.py:210:20: error: Assert might fail. Assertion False might not hold.' The k==1 pass-through branch is genuinely REACHABLE, so the k==1 attacks were really checked and not vacuously accepted/rejected.

A-LEG / CORRESPONDENCE AUDIT (my primary assignment; R/I left to G-CONF). A3 (A-reference, the CHANGED op): contribution(1,id)==PSeq(id) + the k==1 branch are spelled out deeply — no @ContractOnly stands in for the pass-through. atk_7/atk_8/atk_10 confirm the three components of the claim independently (present / exactly once / in position). axiom_check.py drives the REAL post-patch find_ordering_name on a multi-table-inheritance parent whose Meta.ordering mixes F('rank').asc() and 'name', and asserts `e[0] is meta_orderby` — object identity, in position. I read the real callee at base_commit: compiler.py:723-727 and the crash source get_order_dir/query.py:2221 (`if field[0] == '-'`, a subscript) both match mapping.md §3.1 exactly.

A4/A6 (A-consumed, the UNCHANGED callee): the value binding is `Ensures(True)` — a definitional tautology that over-claims nothing. The two non-value facts (resource-threading + invocation accounting) are the load-bearing content, and atk_3/atk_4 confirm the account is enforced in both directions (extra item / extra count). The resource's unforgeability is confirmed executably by atk_2's translation failure. A2/A5 tagged I: correspondence VERIFIED BY EXECUTION rather than accepted on prose. The account is a MULTISET, so invocation ORDER is the one behavioural axis the spec deliberately leaves free, and both directions verify (pos_control walks back-to-front, my ctl_forward.py walks front-to-back with a rebased invariant => rc=0, VERIFIES in 16s). That freedom is the only place a faithful-but-wrong patch could hide, so I materialized it and ran the oracle:
  - pw/patch_rev.diff — the faithful refinement of the frozen model's OWN back-to-front loop (`for item in reversed(opts.ordering)` with prepend, plus the gold OrderBy pass-through), which refinement.md A2 explicitly tags 'I / identical control flow'. `python pw/res.py rev` (harness.run_resolve) => resolved=TRUE, completed=True, attempts=1, flaky=False. So the walk-order abstraction is genuinely benign and A2's I tag is sound.
  - pw/patch_gold.diff — gold control, same host, launched concurrently => resolved=TRUE. Oracle is live and the host is healthy.
  - pw/patch_isref.diff — diagnostic on mapping.md §2's claim that the abstracted-away `is_ref` component 'carries no discriminating content': gold behaviour but appending (item, True). => resolved=TRUE (F2P 1/1, P2P 26/26). The abstraction is CONFIRMED sound, not merely convenient. (Recorded as a diagnostic, not an attack — it is a patch-side variant, not a same-spec model.)
No kind-3 step: every leg is R, A-consumed, A-reference, or I; the one genuinely changed operation is modeled deeply (A3), not hidden behind an axiom about the function under change.
refinement.md CURRENCY: the prior pass's recorded STALENESS DEFECT is REPAIRED — A4 now shows `piece = resolve_name(state, d)` (the two-argument callee) and A6 documents the invocation obligation, machinery_state-as-resource and name_items. The document describes the model it claims to refine.

**VERDICT COVERAGE:** every attack was fully verified and every needed resolve completed. No timeouts (124) and no crashes: all 12 verifier runs and all 3 resolve runs returned real verdicts, so nothing here is INCONCLUSIVE.

RESIDUAL RISK (honest, not a fail): the spec pins the value sequence, the invocation multiset, and the resource's unforgeability, but leaves invocation ORDER free by design. I falsified that being a hole by executing the oracle on the reverse-order patch (resolved=True) rather than reasoning about it. The abstraction to identity tags is also not defeated by tag collision (atk_9).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

ATTACK (2) faithfulness-break, django__django-11555/nagini. No diverging input found; spec is not too strong.

REFERENCE CORRECTNESS: used  (base 8dd5877f58) with patch.diff APPLIED -- git diff --stat = compiler.py +3, the `if isinstance(item, OrderBy): results.append((item, False)); continue` guard present at compiler.py:725-727. So the model was compared against POST-patch gold, not base; I did not report the patch delta as a divergence.

SPEC CLAIMS CHECKED: (P1) ToSeq(Result()) == expanded(kinds,ids), the in-order concat of contributions, with contribution(1,id)==PSeq(id) (OrderBy item passed through verbatim as ONE target, own identity) and contribution(0,id)==resolve_name_seq(id). (P2) invocations(state) == Old(...) + name_items(...) -- machinery applied to exactly the textual-name items, once each, never to an OrderBy item.

EVIDENCE 1 (main): direct differential vs real gold over 399 in-domain inputs, 0 disagreements. MTI parent/child; Parent.Meta.ordering set to every ordering of length 1..3 over {2 distinct OrderBy exprs, 'name','rank','-name','rel__label','rel_id'}; drove real patched find_ordering_name('parent_ptr',...) with depth-1 instrumentation capturing both calls made and each call's returned list. P2 checked as multiset of depth-1 args; P1 checked by assembling the reference from the ACTUAL captured depth-1 returns. Pass-through identity compared with `is`, is_ref compared to False. Result: cases=399 ok=399 fails=0 raised=0. (My FIRST attempt built the reference on a fresh compiler and reported 141 'P1-output' fails -- all pure alias artifacts, parent vs child alias from a second query. Self-caught and corrected; not a finding.)

EVIDENCE 2 (walk order, the sharpest attack): the spec deliberately weakens P2 to a MULTISET and model.py's impl walks BACK-TO-FRONT while gold walks front-to-back. I implemented the back-to-front gold variant in a real tree copy and swept 2457 inputs (items incl. 2 OrderBy exprs, plain/prefixed names, multi-hop rel__label, rel2__other, relation items 'rel'/'rel2'; 3 leaf Meta.ordering variants; lengths 1..3), comparing alias-DECODED ORDER BY semantics (each term mapped back through the JOIN map to rel_id/rel2_id, so alias renaming cannot masquerade as a difference). Result: 0 semantic divergences. Raw SQL showed 2 'DIFF's on ('rel__label','rel2__label') and ('rel','rel2') -- I decoded both and they are pure alias RENAMING (A_leaf<->T4 swap with the join map swapped in step): gold and b2f both mean ['rel_id.label ASC','rel2_id.label ASC']. An earlier 693-divergence count was my own normalization bug (app_label leaking into the NULLS term); fixed -> 0. Confirmed behaviourally: the back-to-front tree passes ordering (26/26) and ordering+queries+model_inheritance+expressions (566 tests, OK, skipped=10, xfail=2). So the multiset abstraction is genuinely sound, not an over-weakening.

EVIDENCE 3 (state-dependence of resolve_name_seq): within one expansion, duplicate name items (rel__label x2 and x3, rel__deep__tag x2, rel_id x2, '-rel__label'+'rel__label', with filter()/select_related() variants) always returned the SAME target sequence -- 0 state-dependence violations, so pinning resolve_name to a pure per-item sequence does not over-claim on the modeled path. NOTE: across DIFFERENT inputs the same name can resolve to a different alias (rel__label -> A_leaf in ordering ('rel__label','rel2__label') vs T4 in the reversed one). This is NOT a defect: resolve_name_seq is uninterpreted (Ensures(True)) and the ids are per-expansion identity tags, so no cross-input constancy is claimed; and the difference is alias naming only, semantically identical (verified by decode).

EVIDENCE 4 (domain boundary): mapping.md pins kinds[k]==1 <-> isinstance(item, OrderBy). Confirmed on the real tree that OrderBy instances (F().asc(), desc(nulls_last), Lower().asc(), OrderBy(Lower())) all pass through with identity preserved, while NON-OrderBy expression items (bare F(), bare Lower()) raise TypeError 'not subscriptable' -- i.e. they are outside the modeled kind-1 domain by the same isinstance test the patch uses, so the refinement is not silently widened.

RESIDUAL / considered and rejected as findings: (a) resolve_name carries no Exsures, but real gold DOES raise on some in-domain orderings -- FieldError 'Infinite loop caused by ordering.' for duplicate relation items ('rel','rel') with an ordered leaf, and FieldError for a bogus name or '?'. Under the walk-order freedom the multiset permits, gold and b2f can even raise DIFFERENT FieldError messages on the same input (('rel','rel','bogus'): gold=infinite-loop, b2f=cannot-resolve-keyword). This does NOT make the spec too strong -- it makes it partial: Nagini's Ensures constrain only normally-returning executions, so raising inputs are simply not claimed, and the model over-claims nothing about them. It would only matter for a too-weak (attack-1) framing, and even then both variants raise FieldError and the suite passes. (b) is_ref abstracted away -- verified uniformly False on every produced entry in all 399 cases.

BUNDLE GATES independently re-run by me: axiom_check.py exit 0 on the patched tree (G-AX OK); conformance_check.py exit 0, 100010 inputs, 0 disagreements (G-CONF); scripts/nagini_verify.sh model.py = 'Verification successful' (13.35s); same-spec on the unmodified model = SAME, exit 0 (spec region byte-identical baseline confirmed).

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

**SCOPE/DISPOSITION:** NO RELAXATION IN THIS BUNDLE — I re-derived this rather than inheriting it. `find . -iname '*RELAX*'` over the instance dir returns nothing; meta.json has no `relaxed_leakage` key (`'relaxed_leakage' in meta` -> False, value None); meta.gates['G-LEAK'].status == 'pass' with detail 'spec view clean', not 'relaxed'. The strings 'relaxed'/'relaxed_leakage' that DO grep out of meta.json occur only inside the *prose of the prior G-PANEL-3 note*, which itself says no relaxation exists — i.e. a grep artifact of the previous reviewer quoting the key name, not a live relaxation. So this is a plain strict-mode leakage judgement with no relaxation argument to audit or credit.

I did NOT inherit the prior G-PANEL-3 'pass'. Its note stamps model.py as sha256 ecd1df8f6c33..., but the artifact on disk is now 2dfe89c91273bcf37da10d00da73a86ca7a861bb1147ff22850fea7d75f6b5d7 — the model was revised after that note, so the prior measurement describes a different byte sequence and is stale. Every number below is my own re-measurement against the current digest, which matches the stamps on G-LEAK/G-GOLD/G-DIFF/G-AX/G-CONF/G-HYGIENE (all 2dfe89c91273).

**CONSUMER SURFACE I ACTUALLY RENDERED:** swebench_unified.markers.spec_view(model.py, get_backend('nagini')) — the exact artifact eval/prompts.py::`_spec_block` inlines — PLUS the `modeled_functions` line that same function renders. mapping.md / refinement.md / verdict.md / meta.json / properties.py are audit-only and never reach the solver, so they are out of the leak surface (and I confirmed prompts.py renders only model_symbol ↔ repo_symbol, NOT carrier_type and NOT repo_location:723-729 — the line-range locator does not reach the consumer).

1) GOLD-EDIT RECONSTRUCTION — ABSENT. The gold patch adds exactly three lines: `if isinstance(item, OrderBy):`, `results.append((item, False))`, `continue`. Searching the rendered surface: 'isinstance' False, 'results.append' False, 'continue' False, 'OrderBy' False. Also absent: find_ordering_name, get_order_dir, opts.ordering, Meta.ordering, compiler, order_by, TypeError, ptr, multi-table, inherit, patch/fix/bug/copy. The only 'django' hit is the instance id in the docstring title ('Twin-artifact model for django__django-11555') — the task identifier the solver already holds, not an edit locator. The spec view names nothing but abstract carriers (kinds/ids/state, PSeq/PMultiset, kind 1 vs 0).

2) **ASYMMETRY RUNS THE SAFE WAY.** The PUBLIC problem_statement is strictly MORE revealing than the spec view: it states outright 'the field is an OrderBy object, not a string, during get_order_dir', plus order_by(), Meta.ordering, multi-table inheritance, and links a reproducing repo and stacktrace. The spec view mentions none of those symbols. The discriminator (an already-formed ordering expression must not be handed to the name-resolution machinery) is directly derivable from the public statement alone, so there is no facet on which the spec view could exceed it.

3) MECHANICAL SCREEN, RE-RUN NOT TRUSTED: leakage.screen(model.py, nagini, instance.patch, instance.problem_statement, instance.test_patch) -> passed=True, hard_failures=[], warnings=[]. leakage.reviewer_directed(model.py) -> [] (empty).

4) LOAD-BEARING TEST (the decisive one — is the discriminator in the FORMAL spec or smuggled in the prose?). I built narration-stripped twins: every triple-quoted docstring collapsed to `""" """` and every non-marker comment deleted (region markers and `# type:` hints preserved so the file still parses and the regions still delimit). Residual 'ordering/machinery' hits are identifier names only (machinery_state, expand_default_ordering), zero prose. Ran the pinned verifier, scripts/nagini_verify.sh:
   - np_model.py (gold impl, narration stripped): 'Verification successful', exit 0 (15.80s)
   - np_model_prepatch.py (pre-patch impl, SAME stripped spec): 'Verification failed', exit 1 (16.76s) — 'Loop invariant might not be preserved. Assertion (ToSeq(result) == expanded(ToSeq(kinds).drop(i), ToSeq(ids).drop(i))) might not hold' at np_model_prepatch.py:98
   Identical outcomes to the unstripped pair, which I also ran fresh: model.py exit 0 (17.08s), model_prepatch.py exit 1 (20.08s), same invariant error at line 198. So the prose is NOT load-bearing — the discriminator lives entirely in the formal contracts (`expanded`/`contribution`'s kind==1 -> PSeq(item_id)` branch and the `invocations == Old(...) + name_items(...)` postcondition). Removing the narration does not make the spec accept the pre-patch impl. That is the correct direction: the prose narrates a discriminator the contracts already enforce, rather than carrying it.

5) **SPEC-REGION IDENTITY:** markers.same_spec(model.py, model_prepatch.py, nagini) -> True — the two differ only in the impl region, so the exit-0/exit-1 split above is a property of one shared spec and not of two different specs.

6) LOCALIZATION AFFORDANCE (noted, NOT a finding): the rendered line is 'Modeled function(s): expand_default_ordering (↔ django.db.models.sql.compiler.SQLCompiler.find_ordering_name (related-model default-ordering expansion block))'. This names the function and block to edit. I judged it non-leaking because (a) it is a uniform harness affordance emitted for every bundle by `_spec_block`'s design, not bundle-specific narration; (b) it discloses WHERE, never WHAT — the three added lines remain absent; and (c) the public problem_statement already localizes to this call path via get_order_dir and the linked stacktrace. The narrower repo_location line range 723-729 would be a sharper locator and it is NOT rendered.

**NO FILE ADDRESSES THE REVIEWER.** grep -niE 'reviewer|panel|auditor|attacker|submit_result|NO-LEAKAGE|LEAKAGE|G-PANEL|do not flag|should record|honest verdict' over model.py, mapping.md, refinement.md, axiom_check.py, conformance_check.py -> zero hits; a second pass for 'you (should|must) (submit|record)|record (NO-LEAKAGE|pass)|the honest verdict|dear (reviewer|auditor)|note to (the )?(reviewer|auditor|panel)' across *.py *.md *.json -> zero hits. Nothing in the bundle tried to tell me what to submit.

OUT-OF-SCOPE OBSERVATIONS for other layers (they do not affect this verdict, since with no relaxation my disposition leans on no other gate): meta.gates['G-EQ'].status == 'fail' and G-PANEL role 1 == 'fail', both reading 'atk_5.py verifies but its patch does not resolve — FAIL_TO_PASS fails 1/1: test_order_by_ptr_field_with_default_ordering_by_expression'. BOTH are stamped against model.py ecd1df8f6c33..., i.e. the SAME superseded model as the stale panel note, whereas every strict gate re-run against the current 2dfe89c91273 passes (G-GOLD, G-DIFF, G-AX, G-CONF seed 11555 100010 checked / 0 disagreements, G-MUT 20/20 killed, G-HYGIENE, G-INTEGRITY, G-LEAK). Those two fails should be re-run against the current model rather than read as live weakness findings.

**VERDICT:** NO-LEAKAGE. The consumer-visible spec view reconstructs none of the gold edit's three lines, is strictly less revealing than the public problem_statement, passes the mechanical screen on the current digest, and survives the load-bearing test with the discriminator located in the contracts rather than the prose.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `properties.py`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.
