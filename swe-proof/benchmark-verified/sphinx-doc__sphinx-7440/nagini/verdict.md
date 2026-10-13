# P2 adversarial audit — sphinx-doc__sphinx-7440

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** G-EQ: 16 attacks re-verified from the retained audit evidence (verdict.md), none breaks the spec; positive control verifies. Re-derived at a higher verifier cap after a host-load timeout had made the original run inconclusive; same attacks, same derivation.

**What was measured.** The harness re-ran 16 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 16 | `atk_prepatch.py`, `atk_2_fold_forward.py`, `atk_3_oracle_echo.py`, `atk_4_partial_first_char.py`, `atk_5_partial_len5.py`, `atk_6_truncate.py`, `atk_7_dup_last.py`, `atk_8_nonterm_spin.py`, `atk_9_selfcall.py`, `atk_10_mutate_input.py`, `atk_11_bogus_measure.py`, `atk_12_raise.py`, `atk_16_upcase.py`, +3 more |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (16):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_prepatch.py` → rejected (same spec, does not verify — good)

```diff
@@ -83,23 +83,31 @@
                                    [[Result()[k]]])))
     # post-conditions-end
     # impl-start
-    # Build the registration key character by character, copying each code point
-    # of the term text unchanged. The loop invariant tracks that the prefix
-    # emitted equals the prefix of the term text verbatim.
+    # PRE-PATCH (buggy) skeleton: the registration folds the term text to lower
+    # case before storing it, so two terms differing only in case collide and
+    # the key reported back is the case-folded text rather than the original.
+    # This computes `casefold` and FAILS the verbatim postcondition on any input
+    # carrying an upper-case ASCII letter. The loop runs backward so that each
+    # step matches `casefold`'s front recursion (one unfold per step).
     result = []  # type: List[int]
-    i = 0
-    while i < len(termtext):
+    i = len(termtext)
+    while i > 0:
         # invariants-start
         Invariant(Acc(list_pred(termtext), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(termtext))
-        Invariant(ToSeq(result) == ToSeq(termtext).take(i))
-        Invariant(MustTerminate(len(termtext) - i + 1))
+        Invariant(ToSeq(result) == casefold(ToSeq(termtext).drop(i)))
+        Invariant(MustTerminate(i + 1))
         # invariants-end
-        c = termtext[i]
-        Assert(ToSeq(termtext).take(i + 1) == ToSeq(termtext).take(i) + PSeq(c))
-        result = result + [c]
-        i = i + 1
-    Assert(ToSeq(termtext).take(len(termtext)) == ToSeq(termtext))
+        c = termtext[i - 1]
+        Assert(ToSeq(termtext).drop(i - 1)[0] == c)
+        Assert(ToSeq(termtext).drop(i - 1).drop(1) == ToSeq(termtext).drop(i))
+        Assert(casefold(ToSeq(termtext).drop(i - 1))
+               == PSeq(fold_cp(c)) + casefold(ToSeq(termtext).drop(i)))
+        if 65 <= c and c <= 90:
+            result = [c + 32] + result
+        else:
+            result = [c] + result
+        i = i - 1
     return result
     # impl-end
```

Attack 2 — `atk_2_fold_forward.py` → rejected (same spec, does not verify — good)

```diff
@@ -83,9 +83,7 @@
                                    [[Result()[k]]])))
     # post-conditions-end
     # impl-start
-    # Build the registration key character by character, copying each code point
-    # of the term text unchanged. The loop invariant tracks that the prefix
-    # emitted equals the prefix of the term text verbatim.
+    # ATTACK: forward ASCII case fold -- the pre-patch behaviour, forward loop.
     result = []  # type: List[int]
     i = 0
     while i < len(termtext):
@@ -93,13 +91,13 @@
         Invariant(Acc(list_pred(termtext), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(termtext))
-        Invariant(ToSeq(result) == ToSeq(termtext).take(i))
         Invariant(MustTerminate(len(termtext) - i + 1))
         # invariants-end
         c = termtext[i]
-        Assert(ToSeq(termtext).take(i + 1) == ToSeq(termtext).take(i) + PSeq(c))
-        result = result + [c]
+        if 65 <= c and c <= 90:
+            result = result + [c + 32]
+        else:
+            result = result + [c]
         i = i + 1
-    Assert(ToSeq(termtext).take(len(termtext)) == ToSeq(termtext))
     return result
     # impl-end
```

Attack 3 — `atk_3_oracle_echo.py` → rejected (same spec, does not verify — good)

```diff
@@ -83,9 +83,8 @@
                                    [[Result()[k]]])))
     # post-conditions-end
     # impl-start
-    # Build the registration key character by character, copying each code point
-    # of the term text unchanged. The loop invariant tracks that the prefix
-    # emitted equals the prefix of the term text verbatim.
+    # ATTACK (ungrounded-oracle echo): emit fold_cp(c), i.e. echo the @Pure
+    # contrast model `casefold` instead of computing the verbatim key.
     result = []  # type: List[int]
     i = 0
     while i < len(termtext):
@@ -93,13 +92,11 @@
         Invariant(Acc(list_pred(termtext), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(termtext))
-        Invariant(ToSeq(result) == ToSeq(termtext).take(i))
         Invariant(MustTerminate(len(termtext) - i + 1))
         # invariants-end
-        c = termtext[i]
-        Assert(ToSeq(termtext).take(i + 1) == ToSeq(termtext).take(i) + PSeq(c))
+        c = fold_cp(termtext[i])
         result = result + [c]
         i = i + 1
-    Assert(ToSeq(termtext).take(len(termtext)) == ToSeq(termtext))
+    Assert(len(result) == len(termtext))
     return result
     # impl-end
```

Attack 4 — `atk_4_partial_first_char.py` → rejected (same spec, does not verify — good)

```diff
@@ -83,9 +83,8 @@
                                    [[Result()[k]]])))
     # post-conditions-end
     # impl-start
-    # Build the registration key character by character, copying each code point
-    # of the term text unchanged. The loop invariant tracks that the prefix
-    # emitted equals the prefix of the term text verbatim.
+    # ATTACK (partial domain): case-fold ONLY the first character, copy the
+    # rest verbatim -- wrong on "TERM2" (-> "tERM2") but right on "term1".
     result = []  # type: List[int]
     i = 0
     while i < len(termtext):
@@ -93,13 +92,13 @@
         Invariant(Acc(list_pred(termtext), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(termtext))
-        Invariant(ToSeq(result) == ToSeq(termtext).take(i))
         Invariant(MustTerminate(len(termtext) - i + 1))
         # invariants-end
         c = termtext[i]
-        Assert(ToSeq(termtext).take(i + 1) == ToSeq(termtext).take(i) + PSeq(c))
-        result = result + [c]
+        if i == 0 and 65 <= c and c <= 90:
+            result = result + [c + 32]
+        else:
+            result = result + [c]
         i = i + 1
-    Assert(ToSeq(termtext).take(len(termtext)) == ToSeq(termtext))
     return result
     # impl-end
```

Attack 5 — `atk_5_partial_len5.py` → rejected (same spec, does not verify — good)

```diff
@@ -83,9 +83,9 @@
                                    [[Result()[k]]])))
     # post-conditions-end
     # impl-start
-    # Build the registration key character by character, copying each code point
-    # of the term text unchanged. The loop invariant tracks that the prefix
-    # emitted equals the prefix of the term text verbatim.
+    # ATTACK (partial domain): verbatim EXCEPT on inputs of length 5, where the
+    # key is case-folded. len("TERM2") == 5, so the F2P input is exactly the
+    # folded case while every other tested term stays correct.
     result = []  # type: List[int]
     i = 0
     while i < len(termtext):
@@ -93,13 +93,13 @@
         Invariant(Acc(list_pred(termtext), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(termtext))
-        Invariant(ToSeq(result) == ToSeq(termtext).take(i))
         Invariant(MustTerminate(len(termtext) - i + 1))
         # invariants-end
         c = termtext[i]
-        Assert(ToSeq(termtext).take(i + 1) == ToSeq(termtext).take(i) + PSeq(c))
-        result = result + [c]
+        if len(termtext) == 5 and 65 <= c and c <= 90:
+            result = result + [c + 32]
+        else:
+            result = result + [c]
         i = i + 1
-    Assert(ToSeq(termtext).take(len(termtext)) == ToSeq(termtext))
     return result
     # impl-end
```

Attack 6 — `atk_6_truncate.py` → rejected (same spec, does not verify — good)

```diff
@@ -83,23 +83,18 @@
                                    [[Result()[k]]])))
     # post-conditions-end
     # impl-start
-    # Build the registration key character by character, copying each code point
-    # of the term text unchanged. The loop invariant tracks that the prefix
-    # emitted equals the prefix of the term text verbatim.
+    # ATTACK (boundary): drop the last character of the key.
     result = []  # type: List[int]
     i = 0
-    while i < len(termtext):
+    while i + 1 < len(termtext):
         # invariants-start
         Invariant(Acc(list_pred(termtext), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(termtext))
-        Invariant(ToSeq(result) == ToSeq(termtext).take(i))
         Invariant(MustTerminate(len(termtext) - i + 1))
         # invariants-end
         c = termtext[i]
-        Assert(ToSeq(termtext).take(i + 1) == ToSeq(termtext).take(i) + PSeq(c))
         result = result + [c]
         i = i + 1
-    Assert(ToSeq(termtext).take(len(termtext)) == ToSeq(termtext))
     return result
     # impl-end
```

Attack 7 — `atk_7_dup_last.py` → rejected (same spec, does not verify — good)

```diff
@@ -83,9 +83,7 @@
                                    [[Result()[k]]])))
     # post-conditions-end
     # impl-start
-    # Build the registration key character by character, copying each code point
-    # of the term text unchanged. The loop invariant tracks that the prefix
-    # emitted equals the prefix of the term text verbatim.
+    # ATTACK (boundary): copy verbatim, then duplicate the last code point.
     result = []  # type: List[int]
     i = 0
     while i < len(termtext):
@@ -93,13 +91,12 @@
         Invariant(Acc(list_pred(termtext), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(termtext))
-        Invariant(ToSeq(result) == ToSeq(termtext).take(i))
         Invariant(MustTerminate(len(termtext) - i + 1))
         # invariants-end
         c = termtext[i]
-        Assert(ToSeq(termtext).take(i + 1) == ToSeq(termtext).take(i) + PSeq(c))
         result = result + [c]
         i = i + 1
-    Assert(ToSeq(termtext).take(len(termtext)) == ToSeq(termtext))
+    if len(termtext) > 0:
+        result = result + [termtext[len(termtext) - 1]]
     return result
     # impl-end
```

Attack 8 — `atk_8_nonterm_spin.py` → rejected (same spec, does not verify — good)

```diff
@@ -83,23 +83,18 @@
                                    [[Result()[k]]])))
     # post-conditions-end
     # impl-start
-    # Build the registration key character by character, copying each code point
-    # of the term text unchanged. The loop invariant tracks that the prefix
-    # emitted equals the prefix of the term text verbatim.
+    # ATTACK (re-encode of the recorded counterexample atk_nonterm2): verify
+    # vacuously via NON-TERMINATION. The loop's static exit branch carries the
+    # contradictory path condition i < 0 against the invariant i >= 0, so every
+    # postcondition discharges vacuously; at runtime the call never returns.
     result = []  # type: List[int]
     i = 0
-    while i < len(termtext):
+    while i >= 0:
         # invariants-start
         Invariant(Acc(list_pred(termtext), 1 / 2))
         Invariant(Acc(list_pred(result)))
-        Invariant(0 <= i and i <= len(termtext))
-        Invariant(ToSeq(result) == ToSeq(termtext).take(i))
-        Invariant(MustTerminate(len(termtext) - i + 1))
+        Invariant(i >= 0)
         # invariants-end
-        c = termtext[i]
-        Assert(ToSeq(termtext).take(i + 1) == ToSeq(termtext).take(i) + PSeq(c))
-        result = result + [c]
         i = i + 1
-    Assert(ToSeq(termtext).take(len(termtext)) == ToSeq(termtext))
     return result
     # impl-end
```

Attack 9 — `atk_9_selfcall.py` → rejected (same spec, does not verify — good)

```diff
@@ -83,23 +83,11 @@
                                    [[Result()[k]]])))
     # post-conditions-end
     # impl-start
-    # Build the registration key character by character, copying each code point
-    # of the term text unchanged. The loop invariant tracks that the prefix
-    # emitted equals the prefix of the term text verbatim.
+    # ATTACK (guarded self-call / non-termination): delegate to itself forever.
+    # The returned value is never computed; if the recursion's obligation is not
+    # checked the postcondition rides on the callee's own Ensures vacuously.
+    if len(termtext) >= 0:
+        return register_term_name(termtext)
     result = []  # type: List[int]
-    i = 0
-    while i < len(termtext):
-        # invariants-start
-        Invariant(Acc(list_pred(termtext), 1 / 2))
-        Invariant(Acc(list_pred(result)))
-        Invariant(0 <= i and i <= len(termtext))
-        Invariant(ToSeq(result) == ToSeq(termtext).take(i))
-        Invariant(MustTerminate(len(termtext) - i + 1))
-        # invariants-end
-        c = termtext[i]
-        Assert(ToSeq(termtext).take(i + 1) == ToSeq(termtext).take(i) + PSeq(c))
-        result = result + [c]
-        i = i + 1
-    Assert(ToSeq(termtext).take(len(termtext)) == ToSeq(termtext))
     return result
     # impl-end
```

Attack 10 — `atk_10_mutate_input.py` → rejected (same spec, does not verify — good)

```diff
@@ -83,23 +83,20 @@
                                    [[Result()[k]]])))
     # post-conditions-end
     # impl-start
-    # Build the registration key character by character, copying each code point
-    # of the term text unchanged. The loop invariant tracks that the prefix
-    # emitted equals the prefix of the term text verbatim.
-    result = []  # type: List[int]
+    # ATTACK (control-flow effect): case-fold the term text IN PLACE and return
+    # the same list. The returned key then equals the (mutated) input, but the
+    # caller's own termtext has been clobbered -- in the real code the index
+    # entry re-reads termtext, so this corrupts the index.
     i = 0
     while i < len(termtext):
         # invariants-start
-        Invariant(Acc(list_pred(termtext), 1 / 2))
-        Invariant(Acc(list_pred(result)))
+        Invariant(Acc(list_pred(termtext)))
         Invariant(0 <= i and i <= len(termtext))
-        Invariant(ToSeq(result) == ToSeq(termtext).take(i))
         Invariant(MustTerminate(len(termtext) - i + 1))
         # invariants-end
         c = termtext[i]
-        Assert(ToSeq(termtext).take(i + 1) == ToSeq(termtext).take(i) + PSeq(c))
-        result = result + [c]
+        if 65 <= c and c <= 90:
+            termtext[i] = c + 32
         i = i + 1
-    Assert(ToSeq(termtext).take(len(termtext)) == ToSeq(termtext))
-    return result
+    return termtext
     # impl-end
```

Attack 11 — `atk_11_bogus_measure.py` → rejected (same spec, does not verify — good)

```diff
@@ -83,23 +83,17 @@
                                    [[Result()[k]]])))
     # post-conditions-end
     # impl-start
-    # Build the registration key character by character, copying each code point
-    # of the term text unchanged. The loop invariant tracks that the prefix
-    # emitted equals the prefix of the term text verbatim.
+    # ATTACK: diverging loop carrying a CONSTANT MustTerminate measure -- probes
+    # whether the measure is actually required to decrease.
     result = []  # type: List[int]
     i = 0
-    while i < len(termtext):
+    while i >= 0:
         # invariants-start
         Invariant(Acc(list_pred(termtext), 1 / 2))
         Invariant(Acc(list_pred(result)))
-        Invariant(0 <= i and i <= len(termtext))
-        Invariant(ToSeq(result) == ToSeq(termtext).take(i))
-        Invariant(MustTerminate(len(termtext) - i + 1))
+        Invariant(i >= 0)
+        Invariant(MustTerminate(1))
         # invariants-end
-        c = termtext[i]
-        Assert(ToSeq(termtext).take(i + 1) == ToSeq(termtext).take(i) + PSeq(c))
-        result = result + [c]
         i = i + 1
-    Assert(ToSeq(termtext).take(len(termtext)) == ToSeq(termtext))
     return result
     # impl-end
```

Attack 12 — `atk_12_raise.py` → rejected (same spec, does not verify — good)

```diff
@@ -83,23 +83,11 @@
                                    [[Result()[k]]])))
     # post-conditions-end
     # impl-start
-    # Build the registration key character by character, copying each code point
-    # of the term text unchanged. The loop invariant tracks that the prefix
-    # emitted equals the prefix of the term text verbatim.
+    # ATTACK (control-flow): never produce a key at all -- raise instead. Probes
+    # whether the spec's silence on exceptional exits admits an impl that
+    # registers nothing.
     result = []  # type: List[int]
-    i = 0
-    while i < len(termtext):
-        # invariants-start
-        Invariant(Acc(list_pred(termtext), 1 / 2))
-        Invariant(Acc(list_pred(result)))
-        Invariant(0 <= i and i <= len(termtext))
-        Invariant(ToSeq(result) == ToSeq(termtext).take(i))
-        Invariant(MustTerminate(len(termtext) - i + 1))
-        # invariants-end
-        c = termtext[i]
-        Assert(ToSeq(termtext).take(i + 1) == ToSeq(termtext).take(i) + PSeq(c))
-        result = result + [c]
-        i = i + 1
-    Assert(ToSeq(termtext).take(len(termtext)) == ToSeq(termtext))
+    if len(termtext) >= 0:
+        raise ValueError()
     return result
     # impl-end
```

Attack 13 — `atk_16_upcase.py` → rejected (same spec, does not verify — good)

```diff
@@ -83,9 +83,8 @@
                                    [[Result()[k]]])))
     # post-conditions-end
     # impl-start
-    # Build the registration key character by character, copying each code point
-    # of the term text unchanged. The loop invariant tracks that the prefix
-    # emitted equals the prefix of the term text verbatim.
+    # ATTACK: rewrite the key by UPPER-casing ASCII a-z (the opposite direction
+    # from the pre-patch fold) -- still not the verbatim term text.
     result = []  # type: List[int]
     i = 0
     while i < len(termtext):
@@ -93,13 +92,13 @@
         Invariant(Acc(list_pred(termtext), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(termtext))
-        Invariant(ToSeq(result) == ToSeq(termtext).take(i))
         Invariant(MustTerminate(len(termtext) - i + 1))
         # invariants-end
         c = termtext[i]
-        Assert(ToSeq(termtext).take(i + 1) == ToSeq(termtext).take(i) + PSeq(c))
-        result = result + [c]
+        if 97 <= c and c <= 122:
+            result = result + [c - 32]
+        else:
+            result = result + [c]
         i = i + 1
-    Assert(ToSeq(termtext).take(len(termtext)) == ToSeq(termtext))
     return result
     # impl-end
```

Attack 14 — `atk_17_swap_adjacent.py` → rejected (same spec, does not verify — good)

```diff
@@ -83,23 +83,29 @@
                                    [[Result()[k]]])))
     # post-conditions-end
     # impl-start
-    # Build the registration key character by character, copying each code point
-    # of the term text unchanged. The loop invariant tracks that the prefix
-    # emitted equals the prefix of the term text verbatim.
+    # ATTACK (permutation / trigger probe): copy the term text but swap each
+    # adjacent pair of code points. Same length and same multiset as the input,
+    # so only a genuinely positional postcondition rejects it.
     result = []  # type: List[int]
     i = 0
+    while i + 1 < len(termtext):
+        # invariants-start
+        Invariant(Acc(list_pred(termtext), 1 / 2))
+        Invariant(Acc(list_pred(result)))
+        Invariant(0 <= i and i <= len(termtext))
+        Invariant(MustTerminate(len(termtext) - i + 1))
+        # invariants-end
+        result = result + [termtext[i + 1]]
+        result = result + [termtext[i]]
+        i = i + 2
     while i < len(termtext):
         # invariants-start
         Invariant(Acc(list_pred(termtext), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(termtext))
-        Invariant(ToSeq(result) == ToSeq(termtext).take(i))
         Invariant(MustTerminate(len(termtext) - i + 1))
         # invariants-end
-        c = termtext[i]
-        Assert(ToSeq(termtext).take(i + 1) == ToSeq(termtext).take(i) + PSeq(c))
-        result = result + [c]
+        result = result + [termtext[i]]
         i = i + 1
-    Assert(ToSeq(termtext).take(len(termtext)) == ToSeq(termtext))
     return result
     # impl-end
```

Attack 15 — `atk_18_alias_return.py` → rejected (same spec, does not verify — good)

```diff
@@ -83,23 +83,9 @@
                                    [[Result()[k]]])))
     # post-conditions-end
     # impl-start
-    # Build the registration key character by character, copying each code point
-    # of the term text unchanged. The loop invariant tracks that the prefix
-    # emitted equals the prefix of the term text verbatim.
-    result = []  # type: List[int]
-    i = 0
-    while i < len(termtext):
-        # invariants-start
-        Invariant(Acc(list_pred(termtext), 1 / 2))
-        Invariant(Acc(list_pred(result)))
-        Invariant(0 <= i and i <= len(termtext))
-        Invariant(ToSeq(result) == ToSeq(termtext).take(i))
-        Invariant(MustTerminate(len(termtext) - i + 1))
-        # invariants-end
-        c = termtext[i]
-        Assert(ToSeq(termtext).take(i + 1) == ToSeq(termtext).take(i) + PSeq(c))
-        result = result + [c]
-        i = i + 1
-    Assert(ToSeq(termtext).take(len(termtext)) == ToSeq(termtext))
-    return result
+    # ATTACK (alias vacuity, re-encode of the prior pass's atk_alias_return):
+    # return the INPUT list itself rather than a fresh key. ToSeq(Result()) ==
+    # ToSeq(termtext) then holds trivially by aliasing, so this probes whether
+    # the fractional-permission framing really forces a genuine copy.
+    return termtext
     # impl-end
```

Attack 16 — `atk_19_empty.py` → rejected (same spec, does not verify — good)

```diff
@@ -83,23 +83,7 @@
                                    [[Result()[k]]])))
     # post-conditions-end
     # impl-start
-    # Build the registration key character by character, copying each code point
-    # of the term text unchanged. The loop invariant tracks that the prefix
-    # emitted equals the prefix of the term text verbatim.
+    # ATTACK (degenerate constant): register the EMPTY key for every term.
     result = []  # type: List[int]
-    i = 0
-    while i < len(termtext):
-        # invariants-start
-        Invariant(Acc(list_pred(termtext), 1 / 2))
-        Invariant(Acc(list_pred(result)))
-        Invariant(0 <= i and i <= len(termtext))
-        Invariant(ToSeq(result) == ToSeq(termtext).take(i))
-        Invariant(MustTerminate(len(termtext) - i + 1))
-        # invariants-end
-        c = termtext[i]
-        Assert(ToSeq(termtext).take(i + 1) == ToSeq(termtext).take(i) + PSeq(c))
-        result = result + [c]
-        i = i + 1
-    Assert(ToSeq(termtext).take(len(termtext)) == ToSeq(termtext))
     return result
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for sphinx-doc__sphinx-7440.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A glossary term is registered under a cross-reference key derived from the
  term's text. The registration key must preserve the term text EXACTLY as
  written, character for character, including the letter case the author chose.
  Two terms whose texts differ only in case are therefore distinct keys and do
  not collide; the key reported back for a term is the original text itself.

  In particular the registration is NOT case-folding: an author who writes a
  term with an upper-case letter has that upper-case letter retained in the
  registered key, rather than being silently rewritten to its lower-case form.

Text is modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing); the specification is carried over `PSeq[int]`. The contrast behaviour
that the registration must NOT perform — ASCII case folding (each code point in
the inclusive range 65..90 shifted by +32, every other code point unchanged) —
is modelled deeply as the pure front-recursive fold `casefold`, against which the
identity-preserving registration is differentiated. `casefold` is validated
equal to the real per-character lower-casing out-of-band by axiom_check.py
(G-AX); it is not consumed as an axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# axioms-start
# (No axiomatized callees. The registration key is the term text itself —
# computed deeply — and the contrast operation it must NOT apply, ASCII
# case-folding, is also modelled deeply by `casefold` in the pure region. There
# is no @ContractOnly the proof consumes; `casefold` is an A-reference validated
# against the real lower-casing by axiom_check.py / G-AX.)
# axioms-end

# pure-start
@Pure
def fold_cp(c: int) -> int:
    """ASCII case fold of a single code point: an upper-case Latin letter
    (code points 65..90, i.e. 'A'..'Z') is shifted by +32 to its lower-case
    form; every other code point is returned unchanged."""
    if 65 <= c and c <= 90:
        return c + 32
    return c

@Pure
def casefold(s: PSeq[int]) -> PSeq[int]:
    """The ASCII case fold of a whole sequence: each code point independently
    mapped by `fold_cp`. Front-recursive so a single unfold is available to a
    matching forward loop. This is the operation the registration must NOT
    apply; the identity-preserving registration differs from it on any input
    carrying an upper-case ASCII letter."""
    if len(s) == 0:
        return PSeq(0).take(0)
    return PSeq(fold_cp(s[0])) + casefold(s.drop(1))
# pure-end

def register_term_name(termtext: List[int]) -> List[int]:
    # pre-conditions-start
    # The source term text is read-only (registration never mutates it):
    # fractional permission, required AND ensured, so no implementation can
    # satisfy a postcondition vacuously by overwriting the input.
    Requires(Acc(list_pred(termtext), 1 / 2))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(termtext), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The registered key is the term text EXACTLY: same length, same code point
    # at every position — the author's letter case is preserved verbatim.
    Ensures(ToSeq(Result()) == ToSeq(termtext))
    # Equivalently, element-wise: the key never rewrites a character (in
    # particular it never case-folds an upper-case ASCII letter to lower case).
    Ensures(len(Result()) == len(termtext))
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(termtext),
                                           Result()[k] == termtext[k]),
                                   [[Result()[k]]])))
    # post-conditions-end
    # impl-start
    # Build the registration key character by character, copying each code point
    # of the term text unchanged. The loop invariant tracks that the prefix
    # emitted equals the prefix of the term text verbatim.
    result = []  # type: List[int]
    i = 0
    while i < len(termtext):
        # invariants-start
        Invariant(Acc(list_pred(termtext), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(termtext))
        Invariant(ToSeq(result) == ToSeq(termtext).take(i))
        Invariant(MustTerminate(len(termtext) - i + 1))
        # invariants-end
        c = termtext[i]
        Assert(ToSeq(termtext).take(i + 1) == ToSeq(termtext).take(i) + PSeq(c))
        result = result + [c]
        i = i + 1
    Assert(ToSeq(termtext).take(len(termtext)) == ToSeq(termtext))
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit, instance sphinx-doc__sphinx-7440 (nagini). Verdict SOUND (advisory). 16 in-bounds same-spec wrong impls encoded, all confirmed spec-byte-identical, all REJECTED by the verifier; positive control verifies. NOTE: the bundle's recorded G-EQ=fail ('INCONCLUSIVE - 1 attack(s) inconclusive') is STALE relative to the current model.py, which has since been REPAIRED with a termination obligation; my independent pass reproduces no inconclusive hit. Evidence below; all commands run with SBU_BENCHMARK_DIR=benchmark-verified.

SAME-SPEC: all 16 attacks + positive_control -> `python -m swebench_unified.adversary same-spec nagini sphinx-doc__sphinx-7440 <f>` exit 0 (spec byte-identical). Attacks edit ONLY the impl region; axioms/@Pure(fold_cp,casefold)/Requires/Ensures byte-identical. positive_control.py is byte-identical to bundle model.py (cmp) and distinct from every attack.

positive_control.py       -> nagini_verify.sh exit 0, VERIFIES (13.2s) atk_prepatch.py           -> exit 2 rejected (PREPATCH BUG re-encoded: backward loop emitting c+32 for A-Z; G-DIFF reproduced) atk_2_fold_forward.py     -> exit 2 rejected (pre-patch fold, forward direction) atk_3_oracle_echo.py      -> exit 2 rejected (UNGROUNDED-ORACLE ECHO: emits fold_cp(c), i.e. echoes the @Pure contrast model) atk_4_partial_first_char.py-> exit 2 rejected (PARTIAL DOMAIN: folds only index 0; 'TERM2'->'tERM2', 'term1' correct) atk_5_partial_len5.py     -> exit 2 rejected (PARTIAL DOMAIN keyed on len==5==len('TERM2'): wrong on exactly the F2P input, right elsewhere) atk_6_truncate.py         -> exit 2 rejected (BOUNDARY: drops last char) atk_7_dup_last.py         -> exit 2 rejected (BOUNDARY: duplicates last char) atk_8_nonterm_spin.py     -> exit 2 rejected -- THE PRIOR PASS'S NAMED COUNTEREXAMPLE, re-encoded verbatim ('i=0; while i>=0: Invariant(i>=0); i=i+1').

Direct verify exit 1: 'Obligation leak check failed. Loop might not take all unsatisfied obligations from the context.' The Requires(MustTerminate(2)) now in the frozen pre-conditions CLOSES the recorded hole. atk_9_selfcall.py         -> exit 2 rejected (GUARDED SELF-CALL vacuity; 'Callee register_term_name might not take all unsatisfied obligations from the caller') atk_10_mutate_input.py    -> exit 2 rejected (CONTROL-FLOW EFFECT: folds termtext in place and returns the alias; 'insufficient permission to access list_pred(termtext)' -- the 1/2 fractional framing holds) atk_11_bogus_measure.py   -> exit 2 rejected (diverging loop with CONSTANT MustTerminate(1); direct verify exit 1: 'Loop might not keep promise to terminate' -- the measure must genuinely decrease) atk_12_raise.py           -> exit 2 rejected (exceptional exit; translation refuses) atk_16_upcase.py          -> exit 2 rejected (OPPOSITE fold a-z->A-Z: spec senses any rewrite, not just the patched direction) atk_17_swap_adjacent.py   -> exit 2 rejected (PERMUTATION, same length AND same multiset -- confirms the element-wise Forall with its [[Result()[k]]] trigger really pins POSITIONS) atk_18_alias_return.py    -> exit 2 rejected (ALIAS VACUITY, re-encode of prior pass's atk_alias_return: `return termtext`) atk_19_empty.py           -> exit 2 rejected (degenerate constant empty key)

NO IN-BOUNDS CANDIDATE => no attack patch needed a resolve run; patches={} is correct, not an omission.

OUT-OF-BOUNDS CANDIDATES (reported for completeness, deliberately NOT submitted as attacks): atk_13_assume_false.py and atk_14_assume_post.py (weakness exit 0 = CANDIDATE, 19.9s/15.3s) compute the PRE-PATCH case-folded key and discharge the postcondition with Assume(False) / Assume(<the postcondition>). I materialized their faithful refined patch (patch_assume_faithful.diff -- keeps termtext.lower() at std.py:308, takes only the XRefRole hunk) and RAN it through the official harness: run_resolve => {resolved: FALSE, completed: TRUE, f2p_failure: ['tests/test_domain_std.py::test_glossary']}. So these ARE verifying-wrong impls whose faithful patch demonstrably does not resolve.

They are nevertheless NOT a defect of THIS spec: `Assume(` is on the nagini backend's banned_tokens (src/swebench_unified/backends/nagini.py:28, ('Assume(', 'Refute(')), enforced as an AST-call check by G-HYGIENE (gates/hygiene.py:154-159), and forbidden to consumers by prompts/nagini/quickref.md ('No Assume/Refute') and spec_guide.md:170. I machine-confirmed the discrimination with hygiene's own _banned_calls: bundle model.py and all 16 submitted attacks -> banned_calls=[] (pass); atk_13/14/15 -> ['Assume'] (would FAIL G-HYGIENE).

Assume is the exact analogue of lean/velvet's banned `sorry`: it is a universal verifier escape that defeats EVERY Nagini spec identically, so counting it would make no spec anywhere passable and would carry zero information about this bundle's refinement fidelity. Also note atk_15_infeasible_guard.py used Assume yet still FAILED to verify (exit 2), so even the escape is not blanket-effective here.

### REFINEMENT.MD AUDIT (every leg R / A-consumed / A-reference / I -- no kind-3):
A1 param termtext:List[int] <-> termtext=term.astext() at std.py:284/308 -- R (str<->List[int] code points). Verified against the repo at base_commit 9bb204dc: make_glossary_term does compute termtext=term.astext() and pass it to note_object. A2 verbatim identity copy <-> note_object 2nd arg with .lower() removed -- I+R. Confirmed: base_commit std.py:308 reads `std.note_object('term', termtext.lower(), ...)`; patch.diff replaces it with `termtext`. note_object stores self.objects[objtype,name] and get_objects re-emits `yield (name, name, type, ...)` verbatim (std.py:974-975 read at base_commit), so the modeled key IS what the F2P assertion ('TERM2','TERM2','term','index','term-TERM2',-1) reads back. A3 casefold deep model <-> the REMOVED str.lower() -- A-REFERENCE, correspondence HOLDS.

Structurally confirmed NOT consumed: the axioms region body is EMPTY (zero non-comment lines), there is no @ContractOnly, and casefold/fold_cp appear in NO non-comment line of pre-conditions, post-conditions, invariants or impl -- the proof never cites the reference, so no oracle can smuggle the answer in. G-AX re-run: axiom_check.py exit 0 (casefold == ASCII str.lower over all 128 ASCII points + 29 boundary + 20000 fuzz; identity differs from the fold exactly on upper-case input). Attack atk_3 confirms the echo direction is closed operationally. B1 dropping lowercase=True from roles['term'] -- R/consistency, claimed to have NO independently-observable behaviour in the F2P/P2P set. I did not take this claim on trust; I MACHINE-CHECKED it.

(a) The F2P/P2P test file at base_commit contains ZERO ':term:' occurrences (grep count 0), so the read path is never exercised. (b) Decisively, I built the hunk-1-ONLY patch -- exactly what a consumer refining this model (which models only the write side) would produce -- and ran the official harness: patch_hunk1_only.diff => run_resolve {resolved: TRUE, completed: TRUE}, F2P test_glossary PASS, all 12 P2P PASS. So the model's coverage boundary is faithful: what the model specifies is sufficient to resolve, and the unmodeled hunk 2 is genuinely inert on the tested inputs. This is the strongest form of the B1 claim and it holds. XRefRole.lowercase provenance also checked at roles.py create_xref_node ('if self.lowercase: target = target.lower()'). Section C (no kind-3): upheld. The changed operation is the REMOVAL of a fold, modelled deeply as the identity copy plus a spelled-out contrast fold, grounded element-wise in the real input carrier.

WHY SOUND: the postcondition is a COMPLETE functional spec (ToSeq(Result())==ToSeq(termtext) + len + positional Forall) over a read-only 1/2-permission input, now backed by Requires(MustTerminate(2)). Content attacks (folds either direction, oracle echo, partial domains incl. one keyed exactly on the F2P input), positional attacks (permutation with identical multiset), boundary attacks, aliasing/mutation vacuity, and all four termination/vacuity escapes (spin loop, self-recursion, bogus constant measure, exceptional exit) are each rejected. The one axis that does admit a non-resolving impl requires a BANNED verifier escape (Assume), which is out of bounds by the framework's own hygiene gate and consumer rules. Attack floor met: 16 >= 5, prepatch reproduced, positive control verifies and is distinct. Host was loaded (load avg ~59-78 on the available cores) but every verification and both resolve runs COMPLETED -- zero timeouts, zero inconclusive hits.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** G-PANEL-1: 16 attacks re-verified from the retained audit evidence (verdict.md), none breaks the spec; positive control verifies. Re-derived at a higher verifier cap after a host-load timeout had made the original run inconclusive; same attacks, same derivation.

**What was measured.** The harness re-ran 16 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 16 | `atk_prepatch.py`, `atk_2_fold_forward.py`, `atk_3_oracle_echo.py`, `atk_4_partial_first_char.py`, `atk_5_partial_len5.py`, `atk_6_truncate.py`, `atk_7_dup_last.py`, `atk_8_nonterm_spin.py`, `atk_9_selfcall.py`, `atk_10_mutate_input.py`, `atk_11_bogus_measure.py`, `atk_12_raise.py`, `atk_16_upcase.py`, +3 more |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (16):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 16 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_prepatch.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_fold_forward.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3_oracle_echo.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4_partial_first_char.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5_partial_len5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6_truncate.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7_dup_last.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8_nonterm_spin.py` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9_selfcall.py` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10_mutate_input.py` → rejected (same spec, does not verify — good)

Attack 11 — `atk_11_bogus_measure.py` → rejected (same spec, does not verify — good)

Attack 12 — `atk_12_raise.py` → rejected (same spec, does not verify — good)

Attack 13 — `atk_16_upcase.py` → rejected (same spec, does not verify — good)

Attack 14 — `atk_17_swap_adjacent.py` → rejected (same spec, does not verify — good)

Attack 15 — `atk_18_alias_return.py` → rejected (same spec, does not verify — good)

Attack 16 — `atk_19_empty.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for sphinx-doc__sphinx-7440.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A glossary term is registered under a cross-reference key derived from the
  term's text. The registration key must preserve the term text EXACTLY as
  written, character for character, including the letter case the author chose.
  Two terms whose texts differ only in case are therefore distinct keys and do
  not collide; the key reported back for a term is the original text itself.

  In particular the registration is NOT case-folding: an author who writes a
  term with an upper-case letter has that upper-case letter retained in the
  registered key, rather than being silently rewritten to its lower-case form.

Text is modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing); the specification is carried over `PSeq[int]`. The contrast behaviour
that the registration must NOT perform — ASCII case folding (each code point in
the inclusive range 65..90 shifted by +32, every other code point unchanged) —
is modelled deeply as the pure front-recursive fold `casefold`, against which the
identity-preserving registration is differentiated. `casefold` is validated
equal to the real per-character lower-casing out-of-band by axiom_check.py
(G-AX); it is not consumed as an axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# axioms-start
# (No axiomatized callees. The registration key is the term text itself —
# computed deeply — and the contrast operation it must NOT apply, ASCII
# case-folding, is also modelled deeply by `casefold` in the pure region. There
# is no @ContractOnly the proof consumes; `casefold` is an A-reference validated
# against the real lower-casing by axiom_check.py / G-AX.)
# axioms-end

# pure-start
@Pure
def fold_cp(c: int) -> int:
    """ASCII case fold of a single code point: an upper-case Latin letter
    (code points 65..90, i.e. 'A'..'Z') is shifted by +32 to its lower-case
    form; every other code point is returned unchanged."""
    if 65 <= c and c <= 90:
        return c + 32
    return c

@Pure
def casefold(s: PSeq[int]) -> PSeq[int]:
    """The ASCII case fold of a whole sequence: each code point independently
    mapped by `fold_cp`. Front-recursive so a single unfold is available to a
    matching forward loop. This is the operation the registration must NOT
    apply; the identity-preserving registration differs from it on any input
    carrying an upper-case ASCII letter."""
    if len(s) == 0:
        return PSeq(0).take(0)
    return PSeq(fold_cp(s[0])) + casefold(s.drop(1))
# pure-end

def register_term_name(termtext: List[int]) -> List[int]:
    # pre-conditions-start
    # The source term text is read-only (registration never mutates it):
    # fractional permission, required AND ensured, so no implementation can
    # satisfy a postcondition vacuously by overwriting the input.
    Requires(Acc(list_pred(termtext), 1 / 2))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(termtext), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The registered key is the term text EXACTLY: same length, same code point
    # at every position — the author's letter case is preserved verbatim.
    Ensures(ToSeq(Result()) == ToSeq(termtext))
    # Equivalently, element-wise: the key never rewrites a character (in
    # particular it never case-folds an upper-case ASCII letter to lower case).
    Ensures(len(Result()) == len(termtext))
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(termtext),
                                           Result()[k] == termtext[k]),
                                   [[Result()[k]]])))
    # post-conditions-end
    # impl-start
    # Build the registration key character by character, copying each code point
    # of the term text unchanged. The loop invariant tracks that the prefix
    # emitted equals the prefix of the term text verbatim.
    result = []  # type: List[int]
    i = 0
    while i < len(termtext):
        # invariants-start
        Invariant(Acc(list_pred(termtext), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(termtext))
        Invariant(ToSeq(result) == ToSeq(termtext).take(i))
        Invariant(MustTerminate(len(termtext) - i + 1))
        # invariants-end
        c = termtext[i]
        Assert(ToSeq(termtext).take(i + 1) == ToSeq(termtext).take(i) + PSeq(c))
        result = result + [c]
        i = i + 1
    Assert(ToSeq(termtext).take(len(termtext)) == ToSeq(termtext))
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit, instance sphinx-doc__sphinx-7440 (nagini). Verdict SOUND (advisory). 16 in-bounds same-spec wrong impls encoded, all confirmed spec-byte-identical, all REJECTED by the verifier; positive control verifies. NOTE: the bundle's recorded G-EQ=fail ('INCONCLUSIVE - 1 attack(s) inconclusive') is STALE relative to the current model.py, which has since been REPAIRED with a termination obligation; my independent pass reproduces no inconclusive hit. Evidence below; all commands run with SBU_BENCHMARK_DIR=benchmark-verified.

SAME-SPEC: all 16 attacks + positive_control -> `python -m swebench_unified.adversary same-spec nagini sphinx-doc__sphinx-7440 <f>` exit 0 (spec byte-identical). Attacks edit ONLY the impl region; axioms/@Pure(fold_cp,casefold)/Requires/Ensures byte-identical. positive_control.py is byte-identical to bundle model.py (cmp) and distinct from every attack.

positive_control.py       -> nagini_verify.sh exit 0, VERIFIES (13.2s) atk_prepatch.py           -> exit 2 rejected (PREPATCH BUG re-encoded: backward loop emitting c+32 for A-Z; G-DIFF reproduced) atk_2_fold_forward.py     -> exit 2 rejected (pre-patch fold, forward direction) atk_3_oracle_echo.py      -> exit 2 rejected (UNGROUNDED-ORACLE ECHO: emits fold_cp(c), i.e. echoes the @Pure contrast model) atk_4_partial_first_char.py-> exit 2 rejected (PARTIAL DOMAIN: folds only index 0; 'TERM2'->'tERM2', 'term1' correct) atk_5_partial_len5.py     -> exit 2 rejected (PARTIAL DOMAIN keyed on len==5==len('TERM2'): wrong on exactly the F2P input, right elsewhere) atk_6_truncate.py         -> exit 2 rejected (BOUNDARY: drops last char) atk_7_dup_last.py         -> exit 2 rejected (BOUNDARY: duplicates last char) atk_8_nonterm_spin.py     -> exit 2 rejected -- THE PRIOR PASS'S NAMED COUNTEREXAMPLE, re-encoded verbatim ('i=0; while i>=0: Invariant(i>=0); i=i+1').

Direct verify exit 1: 'Obligation leak check failed. Loop might not take all unsatisfied obligations from the context.' The Requires(MustTerminate(2)) now in the frozen pre-conditions CLOSES the recorded hole. atk_9_selfcall.py         -> exit 2 rejected (GUARDED SELF-CALL vacuity; 'Callee register_term_name might not take all unsatisfied obligations from the caller') atk_10_mutate_input.py    -> exit 2 rejected (CONTROL-FLOW EFFECT: folds termtext in place and returns the alias; 'insufficient permission to access list_pred(termtext)' -- the 1/2 fractional framing holds) atk_11_bogus_measure.py   -> exit 2 rejected (diverging loop with CONSTANT MustTerminate(1); direct verify exit 1: 'Loop might not keep promise to terminate' -- the measure must genuinely decrease) atk_12_raise.py           -> exit 2 rejected (exceptional exit; translation refuses) atk_16_upcase.py          -> exit 2 rejected (OPPOSITE fold a-z->A-Z: spec senses any rewrite, not just the patched direction) atk_17_swap_adjacent.py   -> exit 2 rejected (PERMUTATION, same length AND same multiset -- confirms the element-wise Forall with its [[Result()[k]]] trigger really pins POSITIONS) atk_18_alias_return.py    -> exit 2 rejected (ALIAS VACUITY, re-encode of prior pass's atk_alias_return: `return termtext`) atk_19_empty.py           -> exit 2 rejected (degenerate constant empty key)

NO IN-BOUNDS CANDIDATE => no attack patch needed a resolve run; patches={} is correct, not an omission.

OUT-OF-BOUNDS CANDIDATES (reported for completeness, deliberately NOT submitted as attacks): atk_13_assume_false.py and atk_14_assume_post.py (weakness exit 0 = CANDIDATE, 19.9s/15.3s) compute the PRE-PATCH case-folded key and discharge the postcondition with Assume(False) / Assume(<the postcondition>). I materialized their faithful refined patch (patch_assume_faithful.diff -- keeps termtext.lower() at std.py:308, takes only the XRefRole hunk) and RAN it through the official harness: run_resolve => {resolved: FALSE, completed: TRUE, f2p_failure: ['tests/test_domain_std.py::test_glossary']}. So these ARE verifying-wrong impls whose faithful patch demonstrably does not resolve.

They are nevertheless NOT a defect of THIS spec: `Assume(` is on the nagini backend's banned_tokens (src/swebench_unified/backends/nagini.py:28, ('Assume(', 'Refute(')), enforced as an AST-call check by G-HYGIENE (gates/hygiene.py:154-159), and forbidden to consumers by prompts/nagini/quickref.md ('No Assume/Refute') and spec_guide.md:170. I machine-confirmed the discrimination with hygiene's own _banned_calls: bundle model.py and all 16 submitted attacks -> banned_calls=[] (pass); atk_13/14/15 -> ['Assume'] (would FAIL G-HYGIENE).

Assume is the exact analogue of lean/velvet's banned `sorry`: it is a universal verifier escape that defeats EVERY Nagini spec identically, so counting it would make no spec anywhere passable and would carry zero information about this bundle's refinement fidelity. Also note atk_15_infeasible_guard.py used Assume yet still FAILED to verify (exit 2), so even the escape is not blanket-effective here.

### REFINEMENT.MD AUDIT (every leg R / A-consumed / A-reference / I -- no kind-3):
A1 param termtext:List[int] <-> termtext=term.astext() at std.py:284/308 -- R (str<->List[int] code points). Verified against the repo at base_commit 9bb204dc: make_glossary_term does compute termtext=term.astext() and pass it to note_object. A2 verbatim identity copy <-> note_object 2nd arg with .lower() removed -- I+R. Confirmed: base_commit std.py:308 reads `std.note_object('term', termtext.lower(), ...)`; patch.diff replaces it with `termtext`. note_object stores self.objects[objtype,name] and get_objects re-emits `yield (name, name, type, ...)` verbatim (std.py:974-975 read at base_commit), so the modeled key IS what the F2P assertion ('TERM2','TERM2','term','index','term-TERM2',-1) reads back. A3 casefold deep model <-> the REMOVED str.lower() -- A-REFERENCE, correspondence HOLDS.

Structurally confirmed NOT consumed: the axioms region body is EMPTY (zero non-comment lines), there is no @ContractOnly, and casefold/fold_cp appear in NO non-comment line of pre-conditions, post-conditions, invariants or impl -- the proof never cites the reference, so no oracle can smuggle the answer in. G-AX re-run: axiom_check.py exit 0 (casefold == ASCII str.lower over all 128 ASCII points + 29 boundary + 20000 fuzz; identity differs from the fold exactly on upper-case input). Attack atk_3 confirms the echo direction is closed operationally. B1 dropping lowercase=True from roles['term'] -- R/consistency, claimed to have NO independently-observable behaviour in the F2P/P2P set. I did not take this claim on trust; I MACHINE-CHECKED it.

(a) The F2P/P2P test file at base_commit contains ZERO ':term:' occurrences (grep count 0), so the read path is never exercised. (b) Decisively, I built the hunk-1-ONLY patch -- exactly what a consumer refining this model (which models only the write side) would produce -- and ran the official harness: patch_hunk1_only.diff => run_resolve {resolved: TRUE, completed: TRUE}, F2P test_glossary PASS, all 12 P2P PASS. So the model's coverage boundary is faithful: what the model specifies is sufficient to resolve, and the unmodeled hunk 2 is genuinely inert on the tested inputs. This is the strongest form of the B1 claim and it holds. XRefRole.lowercase provenance also checked at roles.py create_xref_node ('if self.lowercase: target = target.lower()'). Section C (no kind-3): upheld. The changed operation is the REMOVAL of a fold, modelled deeply as the identity copy plus a spelled-out contrast fold, grounded element-wise in the real input carrier.

WHY SOUND: the postcondition is a COMPLETE functional spec (ToSeq(Result())==ToSeq(termtext) + len + positional Forall) over a read-only 1/2-permission input, now backed by Requires(MustTerminate(2)). Content attacks (folds either direction, oracle echo, partial domains incl. one keyed exactly on the F2P input), positional attacks (permutation with identical multiset), boundary attacks, aliasing/mutation vacuity, and all four termination/vacuity escapes (spin loop, self-recursion, bogus constant measure, exceptional exit) are each rejected. The one axis that does admit a non-resolving impl requires a BANNED verifier escape (Assume), which is out of bounds by the framework's own hygiene gate and consumer rules. Attack floor met: 16 >= 5, prepatch reproduced, positive control verifies and is distinct. Host was loaded (load avg ~59-78 on the available cores) but every verification and both resolve runs COMPLETED -- zero timeouts, zero inconclusive hits.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** ATTACK: faithfulness-break on sphinx-doc__sphinx-7440 (nagini). Searched for an input where the modeled function `register_term_name` disagrees with the real callee. FOUND NONE.

SETUP: worktree at base_commit 9bb204dca from the upstream repository; oracle run in the pinned image swebench/sweb.eval.x86_64.sphinx-doc_1776_sphinx-7440 (sphinx 3.0.1, docutils 0.21.2, py3.9.20).

BOUNDARY ESTABLISHED. mapping.md §1 binds `register_term_name(termtext) -> key` to: input = `termtext = term.astext()` (std.py:284), output = the name stored by `note_object('term', ...)` (std.py:308) and re-emitted by `get_objects()` (std.py:974-975, `yield (name, name, ...)`). I confirmed by grep that std.py:308 is the ONLY `note_object('term', ...)` site in sphinx/, so the boundary is complete.

DIFFERENTIAL AT THE EXACT MODELED BOUNDARY (my own harness, not the bundle's). I monkeypatched `nodes.term.astext` to return the probe string verbatim, so docutils rendering can never mask a divergence and `termtext` is fed in exactly. Gold patch applied. 30,028 inputs: boundary set ("", NUL, "\x00abc", "a\x00b", lone surrogate \ud800, \r\n, leading/trailing spaces, U+00AD, U+FEFF, U+2028, dotted-I 'İ', ligature 'ﬁ', 'ß', 'Σ', 'ΑΣ', DEL, ESC, emoji U+1F600, 1000 chars) + 30k fuzz over the full plane 1..0x10FFFF minus surrogates. ZERO divergences: stored key == input, and get_objects() re-read == stored key on every input. Also reproduced the bundle's own conformance_check.py: 100,039 inputs, 0 disagreements.

The spec is `ToSeq(Result()) == ToSeq(termtext)` + len + element-wise. Real post-patch behavior is literal identity (`termtext` passed through unchanged, dict-stored, re-yielded). Identity cannot be over-strong against identity — there is no room for a diverging input. Spec is not too strong.

ORACLE CONFIRMED: F2P tests/test_domain_std.py::test_glossary passes with gold; all 12 P2P pass. E2E real glossary directive parse of MySQL/mysql/"AbC-DeF 1" yields keys ['AbC-DeF 1','MySQL','mysql'] — original case verbatim, no collision (the reported bug). G-DIFF live: model_prepatch.py shares the spec byte-identically (same_spec=True) and FAILS with exactly 'Postcondition ... ToSeq(Result()) == ToSeq(termtext) might not hold'; model.py verifies in 13.2s. axiom_check.py exits 0.

### NON-DEFECT OBSERVATIONS (probed as attacks, each died):
1. `casefold` is ASCII-only and genuinely disagrees with real str.lower() off-ASCII (I measured 243 disagreements in U+0300..U+0600, e.g. U+037F Ϳ->U+03F3 real vs U+037F model). This is NOT a spec defect: I checked the pre/post regions textually and `casefold`/`fold_cp` appear in NEITHER. It is inert in the proof — no consumed axiom, used only to drive the prepatch skeleton. An A-reference that is unreachable from the contract cannot weaken or over-strengthen the spec, and mapping.md §3.1 explicitly scopes it to ASCII and records why.
2. NUL: feeding "\x00abc" through a real docutils Text node yields astext()=="abc", so the registered key is "abc" != "\x00abc". This is NOT a divergence of the modeled function — the stripping happens in docutils UPSTREAM of the boundary, and `termtext = term.astext()` is the model's INPUT, not its pre-image. At the true boundary NUL is identity-preserved (verified above). The bundle's harness asserts rendering identity rather than silently shrinking the domain.
3. Unmodeled hunk 2 (`XRefRole(lowercase=True)` -> `XRefRole()`): I tested this hardest. Applying hunk 1 ALONE breaks 5 tests in tests/test_intl.py (test_gettext_glossary_terms, test_text_glossary_term, test_text_inconsistency_warnings, test_xml_role_xref, test_xml_warnings; 4 failed -> 9 failed vs base); the FULL gold patch restores the exact base_commit failure set. So hunk 2 does have a real observable — but refinement.md §B's claim is narrower and precisely worded: 'no independently-observable behaviour in the F2P/P2P set'. I verified that claim directly: hunk 1 alone passes all 13 F2P+P2P tests (13 passed). tests/test_intl.py is in neither F2P nor P2P. The claim as written is accurate and the scoping is disclosed, not hidden. Flagging for the record that the read-side hunk is observable in the wider suite, which is a completeness note about model coverage rather than a faithfulness break of the modeled function.
4. BOOKKEEPING (not a spec defect, no verdict impact): under the canonical swebench_unified.markers.region_hashes API, meta.json's recorded hashes match live model.py for axioms/pure/post-conditions but NOT for pre-conditions/impl/invariants/spec_view. model.py and model_prepatch.py agree on the pre-conditions hash and same_spec()=True, so the frozen spec is internally consistent across the twin; the recorded pre-conditions/spec_view entries in meta.json look stale relative to the current files (meta.json mtime 19:50, model.py 19:38). Recommend a meta refresh; it does not change the faithfulness verdict.

CONCLUSION: FAITHFUL. No diverging input exists — the spec pins the modeled function to identity and the real patched repo implements identity at that boundary, confirmed on ~130k inputs including every adversarial Unicode class I could construct.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical screen (leakage.screen, python flavor) passes on the CURRENT on-disk bytes: no hard failures, no diff markers, no reproduced gold line, no patched file/module path. Verified spec-view projection is idempotent and `adversary same-spec` exits 0 on a copy of the bundle model.

GOLD EDIT: hunk1 std.py:308 note_object('term', termtext.lower(), ...) -> note_object('term', termtext, ...); hunk2 std.py:568 XRefRole(lowercase=True, ...) -> XRefRole(...). Checked every token of both changed lines against the spec view. ABSENT from spec view: note_object, lowercase, XRefRole, astext, make_glossary_term, StandardDomain, '.lower()', 'sphinx/domains/std.py', dotted module path, and the whole F2P discriminator (TERM2, term-TERM2, test_glossary, mysql, MySQL). Spec-view identifiers register_term_name / casefold / fold_cp have 0 occurrences in the repo at base_commit 9bb204dca, so no identifier echoes a patched repo symbol.

STRONGEST CANDIDATE CONSIDERED AND REJECTED - `termtext`: it is a spec-view parameter name that DOES appear verbatim on the gold changed line and occurs in exactly one repo file (sphinx/domains/std.py), and the lexical screen structurally cannot catch it because _patch_changed_symbols scopes 'patched repo symbol' to def/class names only (locals are invisible to it). I therefore measured its MARGINAL localization power over the public problem_statement instead of assuming. It is zero, because the PS localizes the edit MORE tightly than `termtext` does: (1) the PS quotes the literal warning 'duplicate term description of mysql, other instance in glossary'; grepping that format string over code excluding locale/ returns exactly ONE hit, std.py:657; (2) the PS token 'glossary' in that same file reaches make_glossary_term; (3) there is exactly ONE .lower() inside make_glossary_term - line 308, which IS gold hunk 1. So the PS alone uniquely reconstructs the gold edit; `termtext` only re-derives 'the file is std.py', which the PS already gives. Not a leak beyond problem_statement.

BEHAVIORAL PROSE IS PUBLIC: the PS title is 'glossary duplicate term with a different case' and its Expected behavior is 'MySQL != mysql term right ?'. The docstring's 'preserve the term text EXACTLY / registration is NOT case-folding' is a restatement of that public expectation, not a diagnosis of the edit mechanism. The word 'lower' appears only as generic prose ('lower-case form', 'lower-casing'), never as .lower() or lowercase=True. Narration screen clean (no bug/fix/patched/previously/incorrectly vocabulary). Judged against problem_statement ONLY; hints_text ('Indeed, this must be a bug. I'll take a look this later.') contributes no vocabulary and was not credited.

RESIDUAL OBSERVATIONS (recorded, not escalated; neither leaks beyond the PS): (a) HYGIENE SMELL - the @Pure helpers casefold/fold_cp are NOT referenced by any contract; I confirmed the pre-conditions and post-conditions regions never mention them. They are consumed only by model_prepatch.py's impl, so they sit in the consumer spec view as a dead helper that spells out the contrast operation (ASCII 65..90 -> +32). This is the closest thing to a semantic hint in the view, but it points only at case-folding, which the PS's 'MySQL != mysql' already establishes as the contrast; it does not reveal WHERE or that the edit is a REMOVAL of a call. (b) INTEGRITY - on-disk region hashes for pre-conditions, invariants, impl and spec_view differ from meta.json (recorded spec_view 97023b32..., current acd62cc0...); git diff shows the delta is an uncommitted MustTerminate hardening (import + Requires(MustTerminate(2)) + loop Invariant(MustTerminate(...))) with no spec-prose change. The leak screen is clean on the current bytes either way. This is a G-INTEGRITY re-stamp concern, outside this gate.

No relaxed-leakage flag is present or needed (meta.relaxed_leakage absent, gates.G-LEAK.status = pass); this instance is not a PS<->gold mismatch since the discriminator (case-distinctness) is fully public in the PS.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
