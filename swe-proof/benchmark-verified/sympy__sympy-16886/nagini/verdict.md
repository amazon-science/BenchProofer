# P2 adversarial audit — sympy__sympy-16886

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 16 admissible attacks re-run of 16 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 16 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 11 | `atk_1_prepatch_digit1_four_dash.py`, `atk_2_dead_branch_letter_A.py`, `atk_3_unrepresented_emits_signals.py`, `atk_4_wrong_punctuation_bang.py`, `atk_5_empty_word_emits_signals.py`, `atk_6_trailing_sep_single_symbol.py`, `atk_7_diverging_never_answers.py`, `atk_13_long_word_corruption.py`, +3 more |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 5 | `atk_8_dead_branch_word_space.py`, `atk_9_dead_branch_word_percent.py`, `atk_10_dead_branch_sep_letter_A.py`, `atk_11_dead_branch_sep_space.py`, `atk_12_dead_branch_word_tab.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (16):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_prepatch_digit1_four_dash.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -339,6 +339,8 @@
     Ensures(ToSeq(Result()) == morse_of(c))
     # post-conditions-end
     # impl-start
+    if c == 49:
+        return [dash(), dash(), dash(), dash()]
     if c == 65:
         return [dot(), dash()]
     if c == 66:
```

Attack 2 — `atk_2_dead_branch_letter_A.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -340,6 +340,8 @@
     # post-conditions-end
     # impl-start
     if c == 65:
+        return [dash(), dash()]
+    if c == 65:
         return [dot(), dash()]
     if c == 66:
         return [dash(), dot(), dot(), dot()]
```

Attack 3 — `atk_3_unrepresented_emits_signals.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -339,6 +339,8 @@
     Ensures(ToSeq(Result()) == morse_of(c))
     # post-conditions-end
     # impl-start
+    if c == 37:
+        return [dot(), dot()]
     if c == 65:
         return [dot(), dash()]
     if c == 66:
```

Attack 4 — `atk_4_wrong_punctuation_bang.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -339,6 +339,8 @@
     Ensures(ToSeq(Result()) == morse_of(c))
     # post-conditions-end
     # impl-start
+    if c == 33:
+        return [dash(), dot(), dash(), dot(), dash(), dot()]
     if c == 65:
         return [dot(), dash()]
     if c == 66:
```

Attack 5 — `atk_5_empty_word_emits_signals.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -293,7 +293,7 @@
     # impl-start
     n = len(msg)
     if n == 0:
-        empty = []  # type: List[int]
+        empty = [dot()]  # type: List[int]
         return empty
     result = morse_list(msg[n - 1])  # type: List[int]
     Assert(ToSeq(msg).drop(n - 1) == PSeq(msg[n - 1]))
```

Attack 6 — `atk_6_trailing_sep_single_symbol.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -292,6 +292,8 @@
     # post-conditions-end
     # impl-start
     n = len(msg)
+    if n == 1:
+        return morse_list(msg[0]) + [sep]
     if n == 0:
         empty = []  # type: List[int]
         return empty
```

Attack 7 — `atk_7_diverging_never_answers.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -292,35 +292,7 @@
     # post-conditions-end
     # impl-start
     n = len(msg)
-    if n == 0:
-        empty = []  # type: List[int]
-        return empty
-    result = morse_list(msg[n - 1])  # type: List[int]
-    Assert(ToSeq(msg).drop(n - 1) == PSeq(msg[n - 1]))
-    i = n - 1
-    while i > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(msg), 1 / 2))
-        Invariant(Acc(list_pred(result)))
-        Invariant(n == len(msg))
-        Invariant(0 <= i and i <= n - 1)
-        Invariant(sep != dot() and sep != dash())
-        Invariant(len(ToSeq(msg).drop(i)) == n - i)
-        Invariant(ToSeq(result) == encoded_seq(ToSeq(msg).drop(i), sep))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure i + 2 (headroom for the
-        # morse_list call and the list constructions in the body), discharging
-        # MustTerminate(3) from the precondition.
-        Invariant(MustTerminate(i + 2))
-        # invariants-end
-        c = msg[i - 1]
-        Assert(ToSeq(msg).drop(i - 1)[0] == c)
-        Assert(ToSeq(msg).drop(i - 1).drop(1) == ToSeq(msg).drop(i))
-        Assert(len(ToSeq(msg).drop(i - 1)) == n - i + 1)
-        result = morse_list(c) + [sep] + result
-        i = i - 1
-    Assert(ToSeq(msg).drop(0) == ToSeq(msg))
-    return result
+    return encode_morse(msg, sep)
     # impl-end
 
 
```

Attack 8 — `atk_8_dead_branch_word_space.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -292,6 +292,9 @@
     # post-conditions-end
     # impl-start
     n = len(msg)
+    if n >= 1 and msg[0] == 32:
+        bad = [dot(), dot(), dot(), dot(), dot(), dot(), dot()]  # type: List[int]
+        return bad
     if n == 0:
         empty = []  # type: List[int]
         return empty
```

Attack 9 — `atk_9_dead_branch_word_percent.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -292,6 +292,9 @@
     # post-conditions-end
     # impl-start
     n = len(msg)
+    if n >= 1 and msg[0] == 37:
+        bad = [dot(), dot(), dot(), dot(), dot(), dot(), dot()]  # type: List[int]
+        return bad
     if n == 0:
         empty = []  # type: List[int]
         return empty
```

Attack 10 — `atk_10_dead_branch_sep_letter_A.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -292,6 +292,9 @@
     # post-conditions-end
     # impl-start
     n = len(msg)
+    if sep == 65:
+        bad = [dot(), dot(), dot(), dot(), dot(), dot(), dot()]  # type: List[int]
+        return bad
     if n == 0:
         empty = []  # type: List[int]
         return empty
```

Attack 11 — `atk_11_dead_branch_sep_space.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -292,6 +292,9 @@
     # post-conditions-end
     # impl-start
     n = len(msg)
+    if sep == 32:
+        bad = [dot(), dot(), dot(), dot(), dot(), dot(), dot()]  # type: List[int]
+        return bad
     if n == 0:
         empty = []  # type: List[int]
         return empty
```

Attack 12 — `atk_12_dead_branch_word_tab.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -292,6 +292,9 @@
     # post-conditions-end
     # impl-start
     n = len(msg)
+    if n >= 1 and msg[0] == 9:
+        bad = [dot(), dot(), dot(), dot(), dot(), dot(), dot()]  # type: List[int]
+        return bad
     if n == 0:
         empty = []  # type: List[int]
         return empty
```

Attack 13 — `atk_13_long_word_corruption.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -292,6 +292,9 @@
     # post-conditions-end
     # impl-start
     n = len(msg)
+    if n >= 8:
+        bad = [dot(), dot(), dot(), dot(), dot(), dot(), dot()]  # type: List[int]
+        return bad
     if n == 0:
         empty = []  # type: List[int]
         return empty
```

Attack 14 — `atk_14_sep_backquote_corruption.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -292,6 +292,9 @@
     # post-conditions-end
     # impl-start
     n = len(msg)
+    if sep == 96:
+        bad = [dot(), dot(), dot(), dot(), dot(), dot(), dot()]  # type: List[int]
+        return bad
     if n == 0:
         empty = []  # type: List[int]
         return empty
```

Attack 15 — `atk_15_frame_mutate_msg.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -292,6 +292,8 @@
     # post-conditions-end
     # impl-start
     n = len(msg)
+    if n >= 1:
+        msg[0] = 65
     if n == 0:
         empty = []  # type: List[int]
         return empty
```

Attack 16 — `atk_16_double_separator.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -317,7 +317,7 @@
         Assert(ToSeq(msg).drop(i - 1)[0] == c)
         Assert(ToSeq(msg).drop(i - 1).drop(1) == ToSeq(msg).drop(i))
         Assert(len(ToSeq(msg).drop(i - 1)) == n - i + 1)
-        result = morse_list(c) + [sep] + result
+        result = morse_list(c) + [sep, sep] + result
         i = i - 1
     Assert(ToSeq(msg).drop(0) == ToSeq(msg))
     return result
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit, nagini/sympy__sympy-16886. 16 same-spec attacks built by copying model.py and editing ONLY the impl regions (all 16 + positive control: `adversary same-spec` exit 0, spec byte-identical). Focused on the A legs (A3/A4 = the morse_of/morse_list deep-model table reference) and on model<->patch correspondence; R/I legs left to G-CONF.

**POSITIVE CONTROL:** bash scripts/nagini_verify.sh $S/pos_control.py -> Verification successful, 85.5s.
GOLD RESOLVE CONTROL (certified before any attack resolve was read): python $S/resolve.py $S/patch_gold.diff -> resolved=True completed=True applied=True F2P 1/1 P2P 42/42 attempts=1 flaky=False.

**COMMANDS:** each attack ran `python -m swebench_unified.adversary weakness nagini sympy__sympy-16886 $S/atk_N.py`; verifications were run 3 at a time as background jobs (each spawns JVM+Z3), resolves STRICTLY ONE AT A TIME via $S/resolve_all.sh (same instance -> harness deletes the image per run).

REFUTED (11) - spec rejected the wrong impl (exit 2):
- atk_1_prepatch_digit1_four_dash (PREPATCH BUG REPRODUCED: morse_list returns four dashes for c==49) -> verification failed. Confirms G-DIFF sensing.
- atk_2_dead_branch_letter_A: `if c == 65: return [dash(),dash()]`. THIS IS THE PRIOR PASS'S RECORDED BREAK, re-encoded -> now REFUTED. The spec was repaired since meta.json's G-EQ record (which is stamped against model.py sha 005d5788..., while the live file is 8f565948...): `Requires(48 <= c and c <= 57)` has been removed from morse_list, so the table is now pinned on the whole code space. The stale BROKEN record no longer describes this spec.
- atk_3_unrepresented_emits_signals (c==37 '%' given a representation) -> refuted; A4 totality is load-bearing.
- atk_4_wrong_punctuation_bang (c==33 '!' corrupted) -> refuted.
- atk_5_empty_word_emits_signals (empty word -> [dot()]) -> refuted; the E.3 widening is real.
- atk_6_trailing_sep_single_symbol (n==1 gets a trailing separator) -> refuted.
- atk_7_diverging_never_answers (bare self-recursion `return encode_morse(msg, sep)`) -> refuted; MustTerminate(3) is load-bearing.
- atk_13_long_word_corruption (corrupt only words of length >= 8; no F2P word is that long) -> refuted; length is not left free.
- atk_14_sep_backquote_corruption (corrupt on sep == 96 '`', an ACCEPTED separator F2P only passes with an empty word list) -> refuted; in-domain really means pinned.
- atk_15_frame_mutate_msg (`msg[0] = 65`) -> refuted; the 1/2 permission is load-bearing.
- atk_16_double_separator (emit sep twice between symbols) -> refuted; encoded_seq pins the join structure.
Note: atk_6 and atk_7 FIRST returned "Translation failed" (duplicate name `empty`; dead code after `while True`) - my own coding errors, NOT refutations. Both were repaired and re-run to a genuine `verification failed`; only the repaired measurement is reported.

CANDIDATE (5) - shared spec AND verified; every one had its faithful patch materialized and RUN through the official harness:
- atk_8_dead_branch_word_space (guard `msg[0] == 32`), verifies 90.2s -> resolved=True, applied=True, F2P 1/1, P2P 42/42 (attempts=2, flaky: attempt 1 did not complete, attempt 2 resolved).
- atk_9_dead_branch_word_percent (`msg[0] == 37`), 84.9s -> resolved=True, applied=True, F2P 1/1, P2P 42/42, attempts=1.
- atk_12_dead_branch_word_tab (`msg[0] == 9`, a distinct whitespace class; '\t' is not even a char_morse key), 77.9s -> resolved=True, applied=True, F2P 1/1, P2P 42/42, attempts=1.
- atk_10_dead_branch_sep_letter_A (`sep == 65`, a REJECTED separator), 82.1s -> resolved=True, applied=True, F2P 1/1, P2P 42/42 (attempts=2, flaky as above).
- atk_11_dead_branch_sep_space (`sep == 32`; the sharpest narrowing, since the real encoder ACCEPTS ' ' on the FIRST call of a fresh process before mapping[" "] is installed - I re-derived that disagreement independently), 86.8s -> resolved=True, applied=True, F2P 1/1, P2P 42/42, attempts=1.
All five are exactly the residual narrowings refinement.md E.2 DECLARES, and all five resolve, so none is a break. Each faithful patch follows refinement.md E.1 literally: the branch is refined INSIDE the per-word loop body (crypto.py:1574-1580, `if <guard>: morsestring.append('.......'); continue`) rather than as a guard at the top of the repository function, alongside the gold table fix. All five checked with `git apply --check` in a detached base_commit worktree (c50643a498) before submission: all APPLY OK.

LOCAL TRIAGE WITH A LIVE CONTROL (advisory, run before spending serialized resolves): BASE (no patch) fails exactly F2P assertion 9 ('12345' -> '----|...'), gold passes 10/10 and test_decode_morse - so the triage harness discriminates; all five attack patches then passed 10/10 + decode_morse. (An earlier triage run showed gold ALSO failing 10/10 with NameError - my own split-globals exec bug, fixed to a single namespace; the gold row is what exposed it.)

A-LEG AUDIT (independent re-derivation, $S/aleg_check.py): I extracted morse_of/represented/sep_accepted/no_signals DIRECTLY out of model.py's pure region (executed under a PSeq shim) rather than trusting axiom_check.py's hand-maintained copy, and compared against the real post-patch char_morse parsed out of `git show base:crypto.py` with the gold one-line edit applied. Results: 52/52 keys match A-ref1; `represented` == the real key set over all 0x110000 code points and morse_of is [] on every other one (A-ref2); sep_accepted == the steady-state real guard on all 128 ASCII points with ZERO disagreements, and the single FIRST-CALL disagreement is cp 32 (' ') only - a NARROWING, exactly as mapping.md 2.1(4)/A-ref3 declares, never a claim the real code contradicts. axiom_check.py's `_MORSE_OF`/represented/sep_accepted copies are in lock-step with model.py's over the whole code space (no drift). morse_of(49) = '.----' == real char_morse['1']; prepatch would be '----'. Every digit is 5 signals. A-LEG CHECK OK.

**REFINEMENT.MD LEG AUDIT:** 6 legs A1-A6, tags = 3x R, 1x R+I, 1x A-reference, 1x A-reference+I. No A-consumed leg and NO kind-3 - consistent with the empty `# axioms-start/# axioms-end` region in model.py and meta.axioms == []; no @ContractOnly anywhere in the bundle's .py files (only prose mentions). The one operation that genuinely changed (the table entry for '1') is modeled DEEPLY, not hidden behind an axiom, so the A-reference correspondence is the only table trust point and it is the one I re-derived above. Section C's claim holds. modeled_functions in meta.json binds encode_morse to crypto.py:1574-1580 and morse_list to :1536/:1577, agreeing with mapping.md 1, model.py's docstring and E.1 - the binding is stated consistently in all four places, which is what makes the E.1 refinement rule enforceable.

**VERDICT SOUND:** 16 attacks run to completion, positive control verifies, gold resolve control certified, prepatch reproduced, the prior pass's counterexample re-encoded and now REFUTED by the repaired spec, and all 5 verifying impls' materialized faithful patches RESOLVE under the official harness. No verify-but-does-not-resolve witness found.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 16 admissible attacks re-run of 16 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 16 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 11 | `atk_1_prepatch_digit1_four_dash.py`, `atk_2_dead_branch_letter_A.py`, `atk_3_unrepresented_emits_signals.py`, `atk_4_wrong_punctuation_bang.py`, `atk_5_empty_word_emits_signals.py`, `atk_6_trailing_sep_single_symbol.py`, `atk_7_diverging_never_answers.py`, `atk_13_long_word_corruption.py`, +3 more |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 5 | `atk_8_dead_branch_word_space.py`, `atk_9_dead_branch_word_percent.py`, `atk_10_dead_branch_sep_letter_A.py`, `atk_11_dead_branch_sep_space.py`, `atk_12_dead_branch_word_tab.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (16):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 16 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below._

Attack 1 — `atk_1_prepatch_digit1_four_dash.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_dead_branch_letter_A.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3_unrepresented_emits_signals.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4_wrong_punctuation_bang.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5_empty_word_emits_signals.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6_trailing_sep_single_symbol.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7_diverging_never_answers.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8_dead_branch_word_space.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 9 — `atk_9_dead_branch_word_percent.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 10 — `atk_10_dead_branch_sep_letter_A.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 11 — `atk_11_dead_branch_sep_space.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 12 — `atk_12_dead_branch_word_tab.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 13 — `atk_13_long_word_corruption.py` → rejected (same spec, does not verify — good)

Attack 14 — `atk_14_sep_backquote_corruption.py` → rejected (same spec, does not verify — good)

Attack 15 — `atk_15_frame_mutate_msg.py` → rejected (same spec, does not verify — good)

Attack 16 — `atk_16_double_separator.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit, nagini/sympy__sympy-16886. 16 same-spec attacks built by copying model.py and editing ONLY the impl regions (all 16 + positive control: `adversary same-spec` exit 0, spec byte-identical). Focused on the A legs (A3/A4 = the morse_of/morse_list deep-model table reference) and on model<->patch correspondence; R/I legs left to G-CONF.

**POSITIVE CONTROL:** bash scripts/nagini_verify.sh $S/pos_control.py -> Verification successful, 85.5s.
GOLD RESOLVE CONTROL (certified before any attack resolve was read): python $S/resolve.py $S/patch_gold.diff -> resolved=True completed=True applied=True F2P 1/1 P2P 42/42 attempts=1 flaky=False.

**COMMANDS:** each attack ran `python -m swebench_unified.adversary weakness nagini sympy__sympy-16886 $S/atk_N.py`; verifications were run 3 at a time as background jobs (each spawns JVM+Z3), resolves STRICTLY ONE AT A TIME via $S/resolve_all.sh (same instance -> harness deletes the image per run).

REFUTED (11) - spec rejected the wrong impl (exit 2):
- atk_1_prepatch_digit1_four_dash (PREPATCH BUG REPRODUCED: morse_list returns four dashes for c==49) -> verification failed. Confirms G-DIFF sensing.
- atk_2_dead_branch_letter_A: `if c == 65: return [dash(),dash()]`. THIS IS THE PRIOR PASS'S RECORDED BREAK, re-encoded -> now REFUTED. The spec was repaired since meta.json's G-EQ record (which is stamped against model.py sha 005d5788..., while the live file is 8f565948...): `Requires(48 <= c and c <= 57)` has been removed from morse_list, so the table is now pinned on the whole code space. The stale BROKEN record no longer describes this spec.
- atk_3_unrepresented_emits_signals (c==37 '%' given a representation) -> refuted; A4 totality is load-bearing.
- atk_4_wrong_punctuation_bang (c==33 '!' corrupted) -> refuted.
- atk_5_empty_word_emits_signals (empty word -> [dot()]) -> refuted; the E.3 widening is real.
- atk_6_trailing_sep_single_symbol (n==1 gets a trailing separator) -> refuted.
- atk_7_diverging_never_answers (bare self-recursion `return encode_morse(msg, sep)`) -> refuted; MustTerminate(3) is load-bearing.
- atk_13_long_word_corruption (corrupt only words of length >= 8; no F2P word is that long) -> refuted; length is not left free.
- atk_14_sep_backquote_corruption (corrupt on sep == 96 '`', an ACCEPTED separator F2P only passes with an empty word list) -> refuted; in-domain really means pinned.
- atk_15_frame_mutate_msg (`msg[0] = 65`) -> refuted; the 1/2 permission is load-bearing.
- atk_16_double_separator (emit sep twice between symbols) -> refuted; encoded_seq pins the join structure.
Note: atk_6 and atk_7 FIRST returned "Translation failed" (duplicate name `empty`; dead code after `while True`) - my own coding errors, NOT refutations. Both were repaired and re-run to a genuine `verification failed`; only the repaired measurement is reported.

CANDIDATE (5) - shared spec AND verified; every one had its faithful patch materialized and RUN through the official harness:
- atk_8_dead_branch_word_space (guard `msg[0] == 32`), verifies 90.2s -> resolved=True, applied=True, F2P 1/1, P2P 42/42 (attempts=2, flaky: attempt 1 did not complete, attempt 2 resolved).
- atk_9_dead_branch_word_percent (`msg[0] == 37`), 84.9s -> resolved=True, applied=True, F2P 1/1, P2P 42/42, attempts=1.
- atk_12_dead_branch_word_tab (`msg[0] == 9`, a distinct whitespace class; '\t' is not even a char_morse key), 77.9s -> resolved=True, applied=True, F2P 1/1, P2P 42/42, attempts=1.
- atk_10_dead_branch_sep_letter_A (`sep == 65`, a REJECTED separator), 82.1s -> resolved=True, applied=True, F2P 1/1, P2P 42/42 (attempts=2, flaky as above).
- atk_11_dead_branch_sep_space (`sep == 32`; the sharpest narrowing, since the real encoder ACCEPTS ' ' on the FIRST call of a fresh process before mapping[" "] is installed - I re-derived that disagreement independently), 86.8s -> resolved=True, applied=True, F2P 1/1, P2P 42/42, attempts=1.
All five are exactly the residual narrowings refinement.md E.2 DECLARES, and all five resolve, so none is a break. Each faithful patch follows refinement.md E.1 literally: the branch is refined INSIDE the per-word loop body (crypto.py:1574-1580, `if <guard>: morsestring.append('.......'); continue`) rather than as a guard at the top of the repository function, alongside the gold table fix. All five checked with `git apply --check` in a detached base_commit worktree (c50643a498) before submission: all APPLY OK.

LOCAL TRIAGE WITH A LIVE CONTROL (advisory, run before spending serialized resolves): BASE (no patch) fails exactly F2P assertion 9 ('12345' -> '----|...'), gold passes 10/10 and test_decode_morse - so the triage harness discriminates; all five attack patches then passed 10/10 + decode_morse. (An earlier triage run showed gold ALSO failing 10/10 with NameError - my own split-globals exec bug, fixed to a single namespace; the gold row is what exposed it.)

A-LEG AUDIT (independent re-derivation, $S/aleg_check.py): I extracted morse_of/represented/sep_accepted/no_signals DIRECTLY out of model.py's pure region (executed under a PSeq shim) rather than trusting axiom_check.py's hand-maintained copy, and compared against the real post-patch char_morse parsed out of `git show base:crypto.py` with the gold one-line edit applied. Results: 52/52 keys match A-ref1; `represented` == the real key set over all 0x110000 code points and morse_of is [] on every other one (A-ref2); sep_accepted == the steady-state real guard on all 128 ASCII points with ZERO disagreements, and the single FIRST-CALL disagreement is cp 32 (' ') only - a NARROWING, exactly as mapping.md 2.1(4)/A-ref3 declares, never a claim the real code contradicts. axiom_check.py's `_MORSE_OF`/represented/sep_accepted copies are in lock-step with model.py's over the whole code space (no drift). morse_of(49) = '.----' == real char_morse['1']; prepatch would be '----'. Every digit is 5 signals. A-LEG CHECK OK.

**REFINEMENT.MD LEG AUDIT:** 6 legs A1-A6, tags = 3x R, 1x R+I, 1x A-reference, 1x A-reference+I. No A-consumed leg and NO kind-3 - consistent with the empty `# axioms-start/# axioms-end` region in model.py and meta.axioms == []; no @ContractOnly anywhere in the bundle's .py files (only prose mentions). The one operation that genuinely changed (the table entry for '1') is modeled DEEPLY, not hidden behind an axiom, so the A-reference correspondence is the only table trust point and it is the one I re-derived above. Section C's claim holds. modeled_functions in meta.json binds encode_morse to crypto.py:1574-1580 and morse_list to :1536/:1577, agreeing with mapping.md 1, model.py's docstring and E.1 - the binding is stated consistently in all four places, which is what makes the E.1 refinement rule enforceable.

**VERDICT SOUND:** 16 attacks run to completion, positive control verifies, gold resolve control certified, prepatch reproduced, the prior pass's counterexample re-encoded and now REFUTED by the repaired spec, and all 5 verifying impls' materialized faithful patches RESOLVE under the official harness. No verify-but-does-not-resolve witness found.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

FAITHFULNESS-BREAK attack on sympy__sympy-16886/nagini. Reference = fresh base worktree at c50643a498 with the gold patch APPLIED (morse_char '----':'1' -> '.----':'1'), per role instructions. No divergence found between the modelled function and the real callee on any input in the modelled domain.

WHAT THE SPEC CLAIMS (modelled unit): the per-word encoding step of sympy.crypto.crypto.encode_morse, crypto.py:1574-1580, i.e. word -> sep.join(mapping[letter] for letter in word), over msg: List[int] of code points all `represented`, and sep a single accepted code point. Deep model morse_of pins char_morse (crypto.py:1536) totally on int; encoded_seq specifies the join.

### EVIDENCE (machine-checked, all run from /tmp; bundle untouched):

1. Deep-model table identity, all keys. Extracted the pure region from model.py into an executable shim (PSeq -> tuple) and compared morse_of(ord(ch)) against [ord(s) for s in char_morse[ch]] for all 52 keys of the PATCHED table: 0 mismatches, 52 keys. char_morse['1'] == '.----'; all ten digit codes are length 5.

2. `represented` == the real key set, EXHAUSTIVELY over the whole Unicode space. {c : represented(c)} over range(0x110000) equals {ord(k) for k in char_morse}: symmetric difference EMPTY. And morse_of(c) == no_signals() for every one of the other 1,114,060 code points: 0 code points off the key set emit signals. So the totalization is exact, not an over-claim.

3. Totalization justified observationally against the real encoder. 20,000 random messages built by inserting 1-3 unrepresented non-whitespace characters into a base word of represented characters: real encode_morse(mixed) == encode_morse(base) in 20,000/20,000 cases. The "contributes no signals" claim is what crypto.py:1570's translate() actually does.

4. `sep_accepted` is an EXACT bi-implication with the real guard, swept over the FULL code space (not just ASCII as G-AX does). For all 1,114,059 code points the model ACCEPTS: real encode_morse('A1Z', sep=chr(c)) raised 0 times and mismatched the spec 0 times. Converse direction: of the code points the model REJECTS, 0 returned normally in the real encoder. This was the most likely place for a too-strong spec (a model-accepted separator that the real `assert sep not in mapping` rejects, or a multi-char/whitespace/surrogate separator behaving differently) and it is clean, including whitespace 9/10/11/12/13/0x85/0xA0/0x2028/0x2029, surrogates 0xD800/0xDFFF, 0xFEFF, 0x1F600, NUL, and 0x10FFFF.

5. Differential sweep of the join. Spec encoded_seq vs (a) the real per-word step and (b) the whole real encode_morse: 5,757 words (empty, all 52 singletons, all 2,704 length-2 pairs, 3,000 random length 3-12) x 20 accepted separators = 0 failures. Plus EXHAUSTIVE length-3: all 140,608 words over the 52 represented characters x 3 separators (421,824 cases) = 0 mismatches on the per-word step, and 0 mismatches against the full real encoder at the default sep. Empty word -> '' matches (widening, only adds obligations).

6. Bundle checkers reproduced with a live control. axiom_check.py exit 0 at gold; conformance_check.py exit 0 (shadow == real on 102,664 inputs). NON-VACUITY: on a second, unpatched worktree at base, axiom_check.py exits 1 with "morse_of deep model unsound on '1' (cp 49): real char_morse gives [45,45,45,45], deep model gives [46,45,45,45,45]" -- so the checkers bite, and the only base-vs-gold delta is exactly the patch's one line, which is the delta the spec is SUPPOSED to encode. I did not report that as a divergence.

7. Spec integrity / discrimination. same_spec(model.py, model_prepatch.py) exit 0 (spec region byte-identical, only impl differs). nagini_verify.sh on the bundle model.py: "Verification successful" (78.8s). On model_prepatch.py (the '1' -> four-dash pre-patch table): "Verification failed -- Postcondition of morse_list might not hold. Assertion (ToSeq(Result()) == morse_of(c)) might not hold" (76.0s). The spec is strong enough to reject the buggy behaviour and satisfied by the gold behaviour.

RESIDUAL NARROWINGS EXAMINED, none is a faithfulness break (each is a WEAKENING of the domain, which cannot make the spec too strong -- the failure mode this attack lane hunts):
- sep is a single int, the real parameter is an arbitrary str. Declared in mapping.md §2 / refinement.md §D. A model impl branching on an int cannot observe '|' vs '||', and the F2P calls with a multi-char separator have an empty word list.
- Whitespace and unrepresented symbols excluded from the word. Justified by crypto.py:1570 (translate deletes) and :1573 (split never yields whitespace inside a piece); I confirmed #3 observationally rather than by reading.
- Empty word admitted though str.split() never yields one -- a widening; it pins encoded_seq('')==no_signals() and the real step agrees.

**CONCLUSION:** no input in the modelled domain on which the modelled function disagrees with the real (patched) callee. The spec does not over-claim: it neither promises a normal return where the repo raises (#4) nor a signal where the repo emits none (#2, #3). FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

Leakage / gold-reconstruction review of nagini bundle sympy__sympy-16886. Every fact below is my own measurement from a fresh worktree; I did not inherit the recorded G-PANEL-3 note (its sources.model.py sha does not match the current model.py, so it audits an older spec and I treated it as stale ledger, not as a disposition).

**RELAXATION:** NONE PRESENT, verified rather than assumed. json.load(meta.json).keys() = [additional_change_sites, ax_apply_gold, ax_apply_gold_note, axioms, base_commit, changed_files, deep_model_references, float_encoding, gates, instance_id, modeled_functions, patch_diff, prepatch_models, region_hashes, repo, schema_version, string_modeling, version] -- no `relaxed_leakage` key. `find` over benchmark-verified/sympy__sympy-16886 -name 'RELAXED*' -> nothing (only ears/lean/nagini/velvet subdirs). So there is no unavoidability argument to re-derive and this is a standard, non-relaxed judgement. (The bundle's own gate note in verdict.md/meta.json asserts the same; I re-derived it independently rather than reading it off.)

**GOLD EDIT:** instance.json['patch'] is a single line, sympy/crypto/crypto.py:1523 (confirmed by sed on the base-commit worktree at c50643a498): `"-----": "0", "----": "1",` -> `"-----": "0", ".----": "1",`. The entire discriminator is the Morse code of digit '1' (morse_char key, hence char_morse['1']).

**PUBLIC BASELINE:** the problem_statement publishes BOTH sides of the edit verbatim. Containment on instance.json: '"----": "1"' in ps -> True (the pre-state) and '".----": "1"' in ps -> True ("The correct mapping is `\".----\": \"1\"`."). hints_text is '' (repr checked) and was not consulted as a disclosure source. So the post-state value the spec must pin is already solver-visible text; there is essentially nothing a faithful spec could add.

**SPEC VIEW EXTRACTED CANONICALLY:** markers.spec_view(model.py, get_backend('nagini')) -> 314 lines, sha256 559bacb0b6c9159007f628c5cbca53b0e5d529c65095be9cb5fee2ed7816bdd1, byte-identical to meta.json gates['G-HYGIENE'].data.region_hashes.spec_view, and markers.region_hashes() live == both the G-HYGIENE data block AND the top-level meta.json region_hashes (pure fc4e239b, pre 15f2f5f6, post 5cc9ce24, invariants db8d7b15, impl 40c87c1e) -- no stale mirror in the current meta. So I audited exactly the region the gates audited. Both impl regions render as `...  # implementation elided`; the edit site (morse_list's c==49 branch) is NOT in the spec view.

LINE-BY-LINE SCAN OF ALL 314 SPEC-VIEW LINES:
- Leak-vocabulary regex over (bug|fix|patch|gold|incorrect|wrong|should have|used to|instead of|no longer|regress|prepatch|pre-patch|previously|four dash|four-dash|missing dot|leading dot|change|broken|off-by-one|error|typo|corrected|before|after): the ONLY word-boundary hit is line 93's "deleted before the per-word encoding step runs" -- temporal ordering of the surrounding pass, not before/after edit framing. The module docstring says explicitly "stated as desired behaviour, not as an edit".
- Pre-patch literal: `'----' in spec_view` -> False. The four-dash old value appears nowhere, in no notation.
- Edit-site pointers: `'1523' in sv` -> False, `'morse_char' in sv` -> False, `'sympy/crypto' in sv` -> False, `'diff --git'/'@@'/'patch' in sv` -> False. The six repo citations in the view (lines 46, 104, 118, 262, 263, 270) point only at crypto.py:1536 (char_morse construction), 1559-1560 (`mapping = mapping or char_morse` / `assert sep not in mapping`), 1570 (`translate(...)`) and 1573 (`msg.split()`) -- I checked each line number against the base-commit file and all four are accurate and all four are code the gold patch does not touch. The patched line 1523 is never cited.
- Discriminator surface: it appears only as the deep table -- docstring row `1  dot dash dash dash dash` and `morse_of`'s `if c == 49: return PSeq(dot(), dash(), dash(), dash(), dash())`. I parsed all 52 morse_of branches out of the spec view programmatically; the ten digits come out {0:'-----',1:'.----',2:'..---',3:'...--',4:'....-',5:'.....',6:'-....',7:'--...',8:'---..',9:'----.'} = exactly standard International Morse, and digit 1 is '.----', EQUAL to the string the problem_statement publishes as correct, not beyond it. The other 51 entries are untouched by the gold patch, so spelling the whole table out dilutes rather than localizes.
- Strongest candidate leak, examined explicitly: docstring lines 22-24 "every digit's representation is exactly five signals long" plus the closed form "d dots then (5-d) dashes for d in 0..5; (d-5) dashes then (10-d) dots for 6..9", and line 277's "the discriminating symbol lengths are observable". I re-derived the closed form in Python: it reproduces all ten standard digit codes exactly, i.e. it is a lossless restatement of already-public data. And the 5-signal / leading-dot property is derivable from the problem_statement alone, which prints both '----' (4) and '.----' (5) for the same digit. So this narration stays inside the public facet; it is not a problem_statement-independent disclosure.
- sep_accepted's reject set, the sep != dot()/dash() precondition, and MustTerminate(3)/(2) are orthogonal modelling-boundary machinery on a code path the patch does not touch.
- Test leakage: 'test_encode_morse'/'test_crypto' in sv -> False; no test_patch added line (both `assert encode_morse('12345') == ...` witnesses) is reproduced in the normalized spec view.

**MECHANICAL SCREEN:** leakage.screen(model.py, nagini language, gold patch, test_patch, problem_statement) -> LeakageReport(hard_failures=[], warnings=[]) -- clean. leakage.reviewer_directed() -> [] on refinement.md, mapping.md, verdict.md, model.py, model_prepatch.py, axiom_check.py, conformance_check.py, properties.py, meta.json.

**RECONSTRUCTION CONTROL:** `diff model.py model_prepatch.py` is a SINGLE impl line (397: `[dot(), dash(), dash(), dash(), dash()]` -> `[dash(), dash(), dash(), dash()]`); the spec is untouched. markers.same_spec(model, prepatch, nagini) -> True and `python -m swebench_unified.adversary same-spec nagini sympy__sympy-16886 atk.py` -> exit 0 "SAME -- attack shares the bundle's exact specification". So the spec view is invariant between the buggy and fixed impl apart from the value already published in the issue.

CORE GATES RE-RUN, NOT INHERITED: `bash scripts/nagini_verify.sh .../nagini/model.py` -> "Verification successful", 77.10s, exit 0 (positive control alive, so the spec is not vacuous-by-unsatisfiability). `adversary weakness nagini sympy__sympy-16886 <prepatch>` -> exit 2 "NOT-A-COUNTEREXAMPLE: attack does not verify -- the spec rejected this impl", so the G-DIFF/G-GOLD discrimination on the gold discriminator is live rather than a stale record. Live G-LEAK screen re-run above. G-AX/G-CONF/G-HYGIENE/G-INTEGRITY/G-MUT/G-PBT are recorded pass against the CURRENT model.py sha (8f565948...).

OBSERVED BUT OUT OF MY FACET (recorded for the panel rollup, not a leakage finding): gates G-EQ and G-PANEL-1 are recorded fail -- "atk_7_dead_branch_letter_A.py verifies but its patch does not resolve" (a spec-too-weak claim), both against an older model.py sha. No relaxation rests on those gates here, so their state does not undermine the leakage disposition; they are the G-PANEL-1 lane's business.

**BUNDLE-ADDRESSES-REVIEWER CHECK:** grepped model.py, model_prepatch.py, refinement.md, mapping.md, axiom_check.py, conformance_check.py, properties.py for attacker/auditor/reviewer-directed language, recording instructions, or claims about which verdict is honest -> the only hits are axiom_check.py:240 and :331 mentioning "the G-PANEL-2 witness" as internal code cross-references in comments, not addressed to any reviewer. meta.json and verdict.md carry the prior recorded G-PANEL-3 note; that is a gate ledger entry, and although it states its own conclusion ("NO-LEAKAGE") it issues me no instruction. I relied on none of it -- every number above is my own run.

**CONCLUSION:** no spec-view line reveals the gold edit beyond the solver-visible problem_statement, which already contains both sides of the one-line edit verbatim. NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `properties.py`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.
