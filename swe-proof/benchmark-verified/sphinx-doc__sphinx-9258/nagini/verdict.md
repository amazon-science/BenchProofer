# P2 adversarial audit — sphinx-doc__sphinx-9258

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`

**Machine verdict**

eq: 14 admissible attacks re-run of 14 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 14 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 14 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py`, `atk_9.py`, `atk_10.py`, `atk_11.py`, `atk_12.py`, `atk_13.py`, `atk_14.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE — no attack reached CANDIDATE. All 14 same-spec wrong implementations were REJECTED by the frozen spec (adversary weakness exit 2 on every one), so no verifying wrong impl exists to materialize a faithful patch for and no resolve run was owed. Zero resolve runs were launched: a resolve is evidence only when a verifying wrong impl exists, and none did.
```

**Attacks re-run (14):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier. A `diff` block below is against that spec file, which the attack it belongs to is otherwise identical to.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -390,55 +390,7 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[bool]
-    n = len(target)
-    i = 0
-    while True:
-        # invariants-start
-        Invariant(Acc(list_pred(target), 1 / 2))
-        Invariant(Acc(list_pred(result)))
-        Invariant(0 <= i and i <= n)
-        Invariant(n == len(target))
-        Invariant(n == len(ToSeq(target)))
-        # telescoping fold: what is emitted, concatenated with the kinds of the
-        # remaining suffix, is the whole kind sequence.
-        Invariant(ToSeq(result) + marks(ToSeq(target), i) ==
-                  marks(ToSeq(target), 0))
-        # The condition is the constant `True`, so the bound comes from what the
-        # break counts down: the loop leaves via `break` as soon as no separator
-        # remains at or after i, and otherwise resumes at i = e, the end of a
-        # separator that starts at j >= i and ends strictly after it (sep_end's
-        # postcondition), so the scan index rises by at least one per pass and at
-        # most n - i + 1 passes remain. It strictly decreases because only i
-        # changes (n is a local fixed before the loop, pinned by
-        # Invariant(n == len(target))), and it stays >= 1 because
-        # Invariant(0 <= i and i <= n) holds on entry to every pass (so it never
-        # reaches the unsatisfiable 0); the pass on which no separator remains is
-        # the one that breaks.
-        Invariant(MustTerminate(n - i + 1))
-        # invariants-end
-        # `+ 0` reads the boundary as the plain integer it is; see `sep_end`.
-        j = next_sep_idx(target, i) + 0
-        if j >= n:
-            if i < n:
-                Assert(marks(ToSeq(target), i) == PSeq(True))
-                # the trailing text is one cross-reference.
-                result.append(True)
-            else:
-                Assert(marks(ToSeq(target), i) == PSeq(True).drop(1))
-            break
-        e = sep_end_idx(target, j) + 0
-        Assert(j < e and e <= n)
-        if j > i:
-            Assert(marks(ToSeq(target), i) ==
-                   (PSeq(True) + PSeq(False)) + marks(ToSeq(target), e))
-            # the text before the separator is one cross-reference.
-            result.append(True)
-        else:
-            Assert(marks(ToSeq(target), i) ==
-                   PSeq(False) + marks(ToSeq(target), e))
-        # the separator itself is one literal node.
-        result.append(False)
-        i = e
+    result.append(True)
     return result
     # impl-end
 
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -591,63 +591,10 @@
     # impl-start
     out = []  # type: List[int]
     n = len(target)
-    i = 0
-    while True:
-        # invariants-start
-        Invariant(Acc(list_pred(target), 1 / 2))
-        Invariant(Acc(list_pred(out)))
-        Invariant(0 <= i and i <= n)
-        Invariant(n == len(target))
-        Invariant(n == len(ToSeq(target)))
-        # telescoping fold: what has been emitted, concatenated with the node
-        # stream of the remaining suffix, is the whole node stream.
-        Invariant(ToSeq(out) + rendered(ToSeq(target), i) ==
-                  rendered(ToSeq(target), 0))
-        # The condition is the constant `True`, so the bound comes from what the
-        # break counts down: the loop leaves via `break` as soon as no separator
-        # remains at or after i, and otherwise resumes at i = e, the end of a
-        # separator that starts at j >= i and ends strictly after it (sep_end's
-        # postcondition), so the scan index rises by at least one per pass and at
-        # most n - i + 1 passes remain. It strictly decreases because only i
-        # changes (n is a local fixed before the loop, pinned by
-        # Invariant(n == len(target))), and it stays >= 1 because
-        # Invariant(0 <= i and i <= n) holds on entry to every pass (so it never
-        # reaches the unsatisfiable 0); the pass on which no separator remains is
-        # the one that breaks.
-        Invariant(MustTerminate(n - i + 1))
-        # invariants-end
-        # `+ 0` reads the boundary as the plain integer it is; see `sep_end`.
-        j = next_sep_idx(target, i) + 0
-        if j >= n:
-            if i < n:
-                Assert(rendered(ToSeq(target), i) ==
-                       (ToSeq(target).take(n).drop(i) + PSeq(-1)) + PSeq(-3))
-                # the trailing text is one cross-reference carrying it verbatim.
-                copy_span(out, target, i, n)
-                out.append(-1)
-            else:
-                Assert(rendered(ToSeq(target), i) == PSeq(-3))
-            out.append(-3)
-            break
-        e = sep_end_idx(target, j) + 0
-        Assert(j < e and e <= n)
-        if j > i:
-            Assert(rendered(ToSeq(target), i) ==
-                   ((ToSeq(target).take(j).drop(i) + PSeq(-1)) +
-                    (ToSeq(target).take(e).drop(j) + PSeq(-2))) +
-                   rendered(ToSeq(target), e))
-            # the text before the separator is one cross-reference carrying
-            # exactly the specification's characters over [i, j).
-            copy_span(out, target, i, j)
-            out.append(-1)
-        else:
-            Assert(rendered(ToSeq(target), i) ==
-                   (ToSeq(target).take(e).drop(i) + PSeq(-2)) +
-                   rendered(ToSeq(target), e))
-        # the separator itself is one literal node carrying [j, e) verbatim.
-        copy_span(out, target, j, e)
-        out.append(-2)
-        i = e
+    if n > 0:
+        copy_span(out, target, 0, n)
+        out.append(-1)
+    out.append(-3)
     return out
     # impl-end
 
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -589,6 +589,10 @@
     Ensures(ToSeq(Result()) == rendered(ToSeq(target), 0))
     # post-conditions-end
     # impl-start
+    if len(target) > 0 and target[0] == 91:
+        early = []  # type: List[int]
+        early.append(-3)
+        return early
     out = []  # type: List[int]
     n = len(target)
     i = 0
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -620,10 +620,8 @@
         j = next_sep_idx(target, i) + 0
         if j >= n:
             if i < n:
-                Assert(rendered(ToSeq(target), i) ==
-                       (ToSeq(target).take(n).drop(i) + PSeq(-1)) + PSeq(-3))
-                # the trailing text is one cross-reference carrying it verbatim.
-                copy_span(out, target, i, n)
+                # the trailing text is one cross-reference, shifted by one.
+                copy_span(out, target, i + 1, n)
                 out.append(-1)
             else:
                 Assert(rendered(ToSeq(target), i) == PSeq(-3))
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -589,6 +589,8 @@
     Ensures(ToSeq(Result()) == rendered(ToSeq(target), 0))
     # post-conditions-end
     # impl-start
+    if len(target) > 0:
+        target[0] = target[0]
     out = []  # type: List[int]
     n = len(target)
     i = 0
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -591,7 +591,7 @@
     # impl-start
     out = []  # type: List[int]
     n = len(target)
-    i = 0
+    i = next_sep_idx(target, 0) + 0
     while True:
         # invariants-start
         Invariant(Acc(list_pred(target), 1 / 2))
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -646,7 +646,7 @@
                    rendered(ToSeq(target), e))
         # the separator itself is one literal node carrying [j, e) verbatim.
         copy_span(out, target, j, e)
-        out.append(-2)
+        out.append(-1)
         i = e
     return out
     # impl-end
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -589,65 +589,9 @@
     Ensures(ToSeq(Result()) == rendered(ToSeq(target), 0))
     # post-conditions-end
     # impl-start
+    Assert(False)
     out = []  # type: List[int]
-    n = len(target)
-    i = 0
-    while True:
-        # invariants-start
-        Invariant(Acc(list_pred(target), 1 / 2))
-        Invariant(Acc(list_pred(out)))
-        Invariant(0 <= i and i <= n)
-        Invariant(n == len(target))
-        Invariant(n == len(ToSeq(target)))
-        # telescoping fold: what has been emitted, concatenated with the node
-        # stream of the remaining suffix, is the whole node stream.
-        Invariant(ToSeq(out) + rendered(ToSeq(target), i) ==
-                  rendered(ToSeq(target), 0))
-        # The condition is the constant `True`, so the bound comes from what the
-        # break counts down: the loop leaves via `break` as soon as no separator
-        # remains at or after i, and otherwise resumes at i = e, the end of a
-        # separator that starts at j >= i and ends strictly after it (sep_end's
-        # postcondition), so the scan index rises by at least one per pass and at
-        # most n - i + 1 passes remain. It strictly decreases because only i
-        # changes (n is a local fixed before the loop, pinned by
-        # Invariant(n == len(target))), and it stays >= 1 because
-        # Invariant(0 <= i and i <= n) holds on entry to every pass (so it never
-        # reaches the unsatisfiable 0); the pass on which no separator remains is
-        # the one that breaks.
-        Invariant(MustTerminate(n - i + 1))
-        # invariants-end
-        # `+ 0` reads the boundary as the plain integer it is; see `sep_end`.
-        j = next_sep_idx(target, i) + 0
-        if j >= n:
-            if i < n:
-                Assert(rendered(ToSeq(target), i) ==
-                       (ToSeq(target).take(n).drop(i) + PSeq(-1)) + PSeq(-3))
-                # the trailing text is one cross-reference carrying it verbatim.
-                copy_span(out, target, i, n)
-                out.append(-1)
-            else:
-                Assert(rendered(ToSeq(target), i) == PSeq(-3))
-            out.append(-3)
-            break
-        e = sep_end_idx(target, j) + 0
-        Assert(j < e and e <= n)
-        if j > i:
-            Assert(rendered(ToSeq(target), i) ==
-                   ((ToSeq(target).take(j).drop(i) + PSeq(-1)) +
-                    (ToSeq(target).take(e).drop(j) + PSeq(-2))) +
-                   rendered(ToSeq(target), e))
-            # the text before the separator is one cross-reference carrying
-            # exactly the specification's characters over [i, j).
-            copy_span(out, target, i, j)
-            out.append(-1)
-        else:
-            Assert(rendered(ToSeq(target), i) ==
-                   (ToSeq(target).take(e).drop(i) + PSeq(-2)) +
-                   rendered(ToSeq(target), e))
-        # the separator itself is one literal node carrying [j, e) verbatim.
-        copy_span(out, target, j, e)
-        out.append(-2)
-        i = e
+    out.append(-3)
     return out
     # impl-end
 
```

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good)

```diff
@@ -623,7 +623,6 @@
                 Assert(rendered(ToSeq(target), i) ==
                        (ToSeq(target).take(n).drop(i) + PSeq(-1)) + PSeq(-3))
                 # the trailing text is one cross-reference carrying it verbatim.
-                copy_span(out, target, i, n)
                 out.append(-1)
             else:
                 Assert(rendered(ToSeq(target), i) == PSeq(-3))
@@ -638,14 +637,12 @@
                    rendered(ToSeq(target), e))
             # the text before the separator is one cross-reference carrying
             # exactly the specification's characters over [i, j).
-            copy_span(out, target, i, j)
             out.append(-1)
         else:
             Assert(rendered(ToSeq(target), i) ==
                    (ToSeq(target).take(e).drop(i) + PSeq(-2)) +
                    rendered(ToSeq(target), e))
         # the separator itself is one literal node carrying [j, e) verbatim.
-        copy_span(out, target, j, e)
         out.append(-2)
         i = e
     return out
```

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good)

```diff
@@ -624,7 +624,6 @@
                        (ToSeq(target).take(n).drop(i) + PSeq(-1)) + PSeq(-3))
                 # the trailing text is one cross-reference carrying it verbatim.
                 copy_span(out, target, i, n)
-                out.append(-1)
             else:
                 Assert(rendered(ToSeq(target), i) == PSeq(-3))
             out.append(-3)
```

Attack 11 — `atk_11.py` → rejected (same spec, does not verify — good)

```diff
@@ -716,8 +716,6 @@
     if (i < n and is_space(s[i]) and a + 2 < n and s[a] == 111 and
             s[a + 1] == 114 and is_space(s[a + 2])):
         return strip_left_idx(s, a + 2, n)
-    if a < n and s[a] == 124:
-        return strip_left_idx(s, a + 1, n)
     if i + 2 < n and s[i] == 46 and s[i + 1] == 46 and s[i + 2] == 46:
         return i + 3
     return -1
```

Attack 12 — `atk_12.py` → rejected (same spec, does not verify — good)

```diff
@@ -779,16 +779,22 @@
     # post-conditions-end
     # impl-start
     t = i
-    while t < j:
+    while t < j and is_space(s[t]):
         # invariants-start
         Invariant(Acc(list_pred(s), 1 / 2))
         Invariant(list_pred(out))
         Invariant(ToSeq(s) == Old(ToSeq(s)))
         Invariant(i <= t and t <= j and j <= len(s))
-        Invariant(ToSeq(out) == Old(ToSeq(out)) + ToSeq(s).take(t).drop(i))
-        # At most j - t + 1 passes remain: j is a parameter the loop never changes
-        # and t rises by exactly one per pass, so the bound strictly decreases; the
-        # guard t < j keeps it >= 2 on entry to a pass.
+        Invariant(ToSeq(out) == Old(ToSeq(out)))
+        Invariant(MustTerminate(j - t + 1))
+        # invariants-end
+        t = t + 1
+    while t < j:
+        # invariants-start
+        Invariant(Acc(list_pred(s), 1 / 2))
+        Invariant(list_pred(out))
+        Invariant(ToSeq(s) == Old(ToSeq(s)))
+        Invariant(i <= t and t <= j and j <= len(s))
         Invariant(MustTerminate(j - t + 1))
         # invariants-end
         out.append(s[t])
```

Attack 13 — `atk_13.py` → rejected (same spec, does not verify — good)

```diff
@@ -673,6 +673,17 @@
         Invariant(Acc(list_pred(s), 1 / 2))
         Invariant(ToSeq(s) == Old(ToSeq(s)))
         Invariant(i <= k and k <= len(s))
+        Invariant(MustTerminate(len(s) - k + 1))
+        # invariants-end
+        if s[k] == 91:
+            return len(s)
+        k = k + 1
+    k = i
+    while k < len(s):
+        # invariants-start
+        Invariant(Acc(list_pred(s), 1 / 2))
+        Invariant(ToSeq(s) == Old(ToSeq(s)))
+        Invariant(i <= k and k <= len(s))
         Invariant(next_sep(ToSeq(s), i) == next_sep(ToSeq(s), k))
         # At most len(s) - k + 1 passes remain: the sequence is held read-only by
         # the invariant above so its length cannot change, and k rises by exactly
```

Attack 14 — `atk_14.py` → rejected (same spec, does not verify — good)

```diff
@@ -497,62 +497,19 @@
     Ensures(ToSeq(Result()) == seg_text(ToSeq(s), i, j))
     # post-conditions-end
     # impl-start
-    a = i
-    while a < j and is_space(s[a]):
+    out = []  # type: List[int]
+    t = i
+    while t < j:
         # invariants-start
         Invariant(Acc(list_pred(s), 1 / 2))
         Invariant(ToSeq(s) == Old(ToSeq(s)))
-        Invariant(i <= a and a <= j and j <= len(s))
-        Invariant(strip_left(ToSeq(s), i, j) == strip_left(ToSeq(s), a, j))
-        # At most j - a + 1 passes remain: the compound guard terminates on the
-        # counter alone (the whitespace test only makes the scan stop sooner), j is
-        # a parameter the loop never changes, and a rises by exactly one per pass,
-        # so the bound strictly decreases; the guard a < j keeps it >= 2 on entry to
-        # a pass.
-        Invariant(MustTerminate(j - a + 1))
-        # invariants-end
-        a = a + 1
-    Assert(strip_left(ToSeq(s), a, j) == a)
-    # `a` is now strip_left(s, i, j); reference that nested form directly so the
-    # final equality with seg_text needs no nested-application congruence.
-    b = j
-    while b > a and is_space(s[b - 1]):
-        # invariants-start
-        Invariant(Acc(list_pred(s), 1 / 2))
-        Invariant(ToSeq(s) == Old(ToSeq(s)))
-        Invariant(a <= b and b <= j and j <= len(s))
-        Invariant(a == strip_left(ToSeq(s), i, j))
-        Invariant(strip_right(ToSeq(s), strip_left(ToSeq(s), i, j), j) ==
-                  strip_right(ToSeq(s), strip_left(ToSeq(s), i, j), b))
-        # At most b - a + 1 passes remain: this scan counts DOWN, the compound
-        # guard terminates on the counter alone (the whitespace test only makes it
-        # stop sooner), a is fixed for the whole loop (it was settled by the previous
-        # scan), and b drops by exactly one per pass, so the bound strictly
-        # decreases; the guard b > a keeps it >= 2 on entry to a pass.
-        Invariant(MustTerminate(b - a + 1))
-        # invariants-end
-        b = b - 1
-    Assert(strip_right(ToSeq(s), strip_left(ToSeq(s), i, j), b) == b)
-    out = []  # type: List[int]
-    t = a
-    while t < b:
-        # invariants-start
-        Invariant(Acc(list_pred(s), 1 / 2))
-        Invariant(ToSeq(s) == Old(ToSeq(s)))
-        Invariant(a <= t and t <= b and b <= len(s))
-        Invariant(a == strip_left(ToSeq(s), i, j))
-        Invariant(b == strip_right(ToSeq(s), strip_left(ToSeq(s), i, j), j))
+        Invariant(i <= t and t <= j and j <= len(s))
         Invariant(Acc(list_pred(out)))
-        Invariant(ToSeq(out) == ToSeq(s).take(t).drop(a))
-        # At most b - t + 1 passes remain: b is fixed for the whole loop (settled
-        # by the trailing-space scan) and t rises by exactly one per pass, so the
-        # bound strictly decreases; the guard t < b keeps it >= 2 on entry to a
-        # pass.
-        Invariant(MustTerminate(b - t + 1))
+        Invariant(ToSeq(out) == ToSeq(s).take(t).drop(i))
+        Invariant(MustTerminate(j - t + 1))
         # invariants-end
         out.append(s[t])
         t = t + 1
-    Assert(ToSeq(out) == ToSeq(s).take(b).drop(a))
     return out
     # impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

**SOUND.** 14 attacks, all same-spec (byte-identical spec view, adversary same-spec exit 0 on each), all with unsound_evasions=none (no new @ContractOnly / Assume / axiom). Positive control = unmodified model.py: VERIFIED in 81.9s, so the rejections are not the artifact of an unsatisfiable spec.

**COMMANDS.** Build: gen.py/mk.py/mk2.py in the scratch dir splice ONE function's `# impl-start`/`# impl-end` body, leaving everything else byte-identical. Per attack N: `python -m swebench_unified.adversary same-spec nagini sphinx-doc__sphinx-9258 atk_N.py` (exit 0 on all 14) then `python -m swebench_unified.adversary weakness nagini sphinx-doc__sphinx-9258 atk_N.py` under SBU_ATTACK_VERIFY_TIMEOUT=900 SBN_VERIFY_TIMEOUT=900, run 3-at-a-time as background jobs (logs w_1..w_14.log). Control: `adversary verify ... pos_control.py`.

#### RESULTS (every one 'NOT-A-COUNTEREXAMPLE: attack does not verify', RC=2 — no timeouts, no no-verdicts):
- atk_1 PREPATCH BUG, kind reading: split_render returns [True] for every spec (model_prepatch's defect). Rejected by A7 (marks).
- atk_2 PREPATCH BUG, primary obligation: one cross-reference carrying the WHOLE string, bar+padding swallowed inside it. Rejected by P7 (rendered).
- atk_3 PARTIAL-DOMAIN: gold except renders nothing when the spec opens with '[' (the shape well_formed is false on). Rejected — P7 carries NO domain clause.
- atk_4 BOUNDARY: gold count/kinds/separator spans; trailing xref carries [i+1,n) ('int | str' -> 'int','tr'). Rejected by P7.
- atk_5 CONTROL-FLOW-EFFECT / frame mutation: gold body + `target[0] = target[0]`. Rejected by the permission system (half permission).
- atk_6 UNGROUNDED-ORACLE ECHO: does not compute its start, asks the spec's OWN boundary oracle next_sep_idx and renders from the first separator, dropping preceding text. Rejected — P7 is anchored at 0, so the telescoping invariant fails on ENTRY.
- atk_7 KIND SWAP: separator emitted with marker -1 instead of -2 (dropping `if delims_re.match(piece)`). Rejected by P7.
- atk_8 VACUITY CONTROL: `Assert(False)` + render nothing. Rejected — the frozen spec region hands the verifier no contradiction, so the obligations are not discharged for free.
- atk_9 MARKERS ONLY: gold boundaries/count/kinds, all three copy_span calls dropped (payload free). Rejected by P7 — the retained kind obligation alone would have admitted it.
- atk_10 NODE REMERGE: same characters in order, trailing name loses its own -1 marker (different node PARTITION). Rejected — the markers genuinely delimit nodes (injective encoding).
- atk_11 THE CHANGED LINE REVERTED, in the helper: render_nodes/split_render left gold verbatim; only sep_end_idx loses its `s[a] == 124` branch, i.e. patch.diff's added `\s*\|\s*` removed. Rejected by sep_end_idx's own Ensures — the change is carried at the helper contract, not only at the top.
- atk_12 PAYLOAD FREEDOM IN THE HELPER: copy_span skips leading whitespace, so every padded node's text is trimmed while count/kinds/boundaries stay gold. Rejected by copy_span's Ensures + P7.
- atk_13 PARTIAL-DOMAIN INSIDE THE BOUNDARY ORACLE: next_sep_idx reports 'no separator' once a '[' is seen; bar-only specs stay gold. Rejected by next_sep_idx's Ensures.
- atk_14 RETAINED-HELPER DRIFT: slice_trim returns the UNtrimmed slice. Rejected — the retained bar-only region is not inert.

WRONGNESS CONTROL (wrongness.py): each attack's rendering was simulated and compared against the REAL patched pipeline (re.split(delims)+filter(None,...)+delims_re.match). All 11 simulable attacks differ from the real result on an F2P/P2P input (e.g. atk_2/atk_11 -> [(True,'int | str')] vs real [(True,'int'),(False,' | '),(True,'str')]; atk_13 on '[a] | b' -> one whole-string xref vs real 5 nodes). So the 14 rejections are genuine refutations of wrong impls, not a too-strong spec rejecting correct ones.

A-LEG AUDIT (my lane). refinement.md has 16 legs, tags: R x3, I x2, R+I x6, A-reference x4, R+A-reference x1 — every leg is R / A-consumed / A-reference / I, NO kind-3, and no leg is untagged. No CONSUMED axiom: meta.json axioms==[], deep_model_references are all kind 'A-reference', and model.py's axioms region holds only a comment (the single '@ContractOnly' hit is that comment's own prose, not a declaration).
I re-derived the A-reference correspondence INDEPENDENTLY rather than trusting G-AX/G-CONF: aleg.py is a hand re-transcription of the pure region (is_space, strip_left, sep_end, next_sep, rendered, marks) from model.py's own definitions, compared against the real patched regex pipeline with the node kind read off the BRANCH taken (python.py:319 literal vs 321 xref, as P4/P5/A4/A5 bind it). Results, 0 divergences everywhere: exhaustive length<=5 over the delimiter-dense alphabet '| ,or[].a' (66,430 inputs); 250,000 random draws over an alphabet of 24 tokens incl. TAB/NL/VT/FF/U+001C-001F/NEL/NBSP/U+2000-200A/U+2028/U+202F/U+205F/U+3000; is_space == regex \s over the FULL Unicode range 0..0x10FFFF (0 mismatches in 1,114,112 code points); 18 named realistic specs incl. the F2P 'int | str', 'list[int] | None', 'Dict[str, str]', 'Tuple[str, ...]', 'str or int', '', '|', 'a||b', ' | '; and the marks kind-projection against the real kinds. So sep_end's hand-ordered 4-way alternation does reproduce the regex's leftmost-then-preference semantics, and P2/P3/A2/A3/A7 hold as stated.
Model<->patch correspondence spot-checked at the decode: P7 at target='int | str' decodes to [(True,'int'),(False,' | '),(True,'str')], which is exactly what the F2P test_info_field_list_piped_type asserts (two pending_xref carrying 'int'/'str' with literal_emphasis ' | ' between). Untrimmed payload confirmed against the real code, not against the doc.

ONE RECORDED IMPRECISION, not a finding at this gate: mapping.md §2 words the -1 marker as `isinstance(node, addnodes.pending_xref)`, but the real call sites pass rolename=None, under which docfields.py:68 short-circuits and the xref branch yields a plain emphasis — so that literal reading is degenerate. refinement.md P4/P5/A4/A5 bind the marker to the BRANCH (python.py:321 vs 319), and under the branch reading the correspondence is exact everywhere I measured. This is a bridge-wording issue in mapping.md's type table, already noted by G-PANEL-2; it does not affect any leg's tag or the model<->patch correspondence.

Zero resolve runs were launched because no attack verified — the resolve exception in the brief never became applicable, and there is no missing-evidence gap standing between these attacks and the verdict.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`

**Machine verdict**

panel_1: 14 admissible attacks re-run of 14 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 14 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 14 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py`, `atk_9.py`, `atk_10.py`, `atk_11.py`, `atk_12.py`, `atk_13.py`, `atk_14.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE — no attack reached CANDIDATE. All 14 same-spec wrong implementations were REJECTED by the frozen spec (adversary weakness exit 2 on every one), so no verifying wrong impl exists to materialize a faithful patch for and no resolve run was owed. Zero resolve runs were launched: a resolve is evidence only when a verifying wrong impl exists, and none did.
```

**Attacks re-run (14):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier. A `diff` block below is against that spec file, which the attack it belongs to is otherwise identical to.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -390,55 +390,7 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[bool]
-    n = len(target)
-    i = 0
-    while True:
-        # invariants-start
-        Invariant(Acc(list_pred(target), 1 / 2))
-        Invariant(Acc(list_pred(result)))
-        Invariant(0 <= i and i <= n)
-        Invariant(n == len(target))
-        Invariant(n == len(ToSeq(target)))
-        # telescoping fold: what is emitted, concatenated with the kinds of the
-        # remaining suffix, is the whole kind sequence.
-        Invariant(ToSeq(result) + marks(ToSeq(target), i) ==
-                  marks(ToSeq(target), 0))
-        # The condition is the constant `True`, so the bound comes from what the
-        # break counts down: the loop leaves via `break` as soon as no separator
-        # remains at or after i, and otherwise resumes at i = e, the end of a
-        # separator that starts at j >= i and ends strictly after it (sep_end's
-        # postcondition), so the scan index rises by at least one per pass and at
-        # most n - i + 1 passes remain. It strictly decreases because only i
-        # changes (n is a local fixed before the loop, pinned by
-        # Invariant(n == len(target))), and it stays >= 1 because
-        # Invariant(0 <= i and i <= n) holds on entry to every pass (so it never
-        # reaches the unsatisfiable 0); the pass on which no separator remains is
-        # the one that breaks.
-        Invariant(MustTerminate(n - i + 1))
-        # invariants-end
-        # `+ 0` reads the boundary as the plain integer it is; see `sep_end`.
-        j = next_sep_idx(target, i) + 0
-        if j >= n:
-            if i < n:
-                Assert(marks(ToSeq(target), i) == PSeq(True))
-                # the trailing text is one cross-reference.
-                result.append(True)
-            else:
-                Assert(marks(ToSeq(target), i) == PSeq(True).drop(1))
-            break
-        e = sep_end_idx(target, j) + 0
-        Assert(j < e and e <= n)
-        if j > i:
-            Assert(marks(ToSeq(target), i) ==
-                   (PSeq(True) + PSeq(False)) + marks(ToSeq(target), e))
-            # the text before the separator is one cross-reference.
-            result.append(True)
-        else:
-            Assert(marks(ToSeq(target), i) ==
-                   PSeq(False) + marks(ToSeq(target), e))
-        # the separator itself is one literal node.
-        result.append(False)
-        i = e
+    result.append(True)
     return result
     # impl-end
 
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -591,63 +591,10 @@
     # impl-start
     out = []  # type: List[int]
     n = len(target)
-    i = 0
-    while True:
-        # invariants-start
-        Invariant(Acc(list_pred(target), 1 / 2))
-        Invariant(Acc(list_pred(out)))
-        Invariant(0 <= i and i <= n)
-        Invariant(n == len(target))
-        Invariant(n == len(ToSeq(target)))
-        # telescoping fold: what has been emitted, concatenated with the node
-        # stream of the remaining suffix, is the whole node stream.
-        Invariant(ToSeq(out) + rendered(ToSeq(target), i) ==
-                  rendered(ToSeq(target), 0))
-        # The condition is the constant `True`, so the bound comes from what the
-        # break counts down: the loop leaves via `break` as soon as no separator
-        # remains at or after i, and otherwise resumes at i = e, the end of a
-        # separator that starts at j >= i and ends strictly after it (sep_end's
-        # postcondition), so the scan index rises by at least one per pass and at
-        # most n - i + 1 passes remain. It strictly decreases because only i
-        # changes (n is a local fixed before the loop, pinned by
-        # Invariant(n == len(target))), and it stays >= 1 because
-        # Invariant(0 <= i and i <= n) holds on entry to every pass (so it never
-        # reaches the unsatisfiable 0); the pass on which no separator remains is
-        # the one that breaks.
-        Invariant(MustTerminate(n - i + 1))
-        # invariants-end
-        # `+ 0` reads the boundary as the plain integer it is; see `sep_end`.
-        j = next_sep_idx(target, i) + 0
-        if j >= n:
-            if i < n:
-                Assert(rendered(ToSeq(target), i) ==
-                       (ToSeq(target).take(n).drop(i) + PSeq(-1)) + PSeq(-3))
-                # the trailing text is one cross-reference carrying it verbatim.
-                copy_span(out, target, i, n)
-                out.append(-1)
-            else:
-                Assert(rendered(ToSeq(target), i) == PSeq(-3))
-            out.append(-3)
-            break
-        e = sep_end_idx(target, j) + 0
-        Assert(j < e and e <= n)
-        if j > i:
-            Assert(rendered(ToSeq(target), i) ==
-                   ((ToSeq(target).take(j).drop(i) + PSeq(-1)) +
-                    (ToSeq(target).take(e).drop(j) + PSeq(-2))) +
-                   rendered(ToSeq(target), e))
-            # the text before the separator is one cross-reference carrying
-            # exactly the specification's characters over [i, j).
-            copy_span(out, target, i, j)
-            out.append(-1)
-        else:
-            Assert(rendered(ToSeq(target), i) ==
-                   (ToSeq(target).take(e).drop(i) + PSeq(-2)) +
-                   rendered(ToSeq(target), e))
-        # the separator itself is one literal node carrying [j, e) verbatim.
-        copy_span(out, target, j, e)
-        out.append(-2)
-        i = e
+    if n > 0:
+        copy_span(out, target, 0, n)
+        out.append(-1)
+    out.append(-3)
     return out
     # impl-end
 
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -589,6 +589,10 @@
     Ensures(ToSeq(Result()) == rendered(ToSeq(target), 0))
     # post-conditions-end
     # impl-start
+    if len(target) > 0 and target[0] == 91:
+        early = []  # type: List[int]
+        early.append(-3)
+        return early
     out = []  # type: List[int]
     n = len(target)
     i = 0
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -620,10 +620,8 @@
         j = next_sep_idx(target, i) + 0
         if j >= n:
             if i < n:
-                Assert(rendered(ToSeq(target), i) ==
-                       (ToSeq(target).take(n).drop(i) + PSeq(-1)) + PSeq(-3))
-                # the trailing text is one cross-reference carrying it verbatim.
-                copy_span(out, target, i, n)
+                # the trailing text is one cross-reference, shifted by one.
+                copy_span(out, target, i + 1, n)
                 out.append(-1)
             else:
                 Assert(rendered(ToSeq(target), i) == PSeq(-3))
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -589,6 +589,8 @@
     Ensures(ToSeq(Result()) == rendered(ToSeq(target), 0))
     # post-conditions-end
     # impl-start
+    if len(target) > 0:
+        target[0] = target[0]
     out = []  # type: List[int]
     n = len(target)
     i = 0
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -591,7 +591,7 @@
     # impl-start
     out = []  # type: List[int]
     n = len(target)
-    i = 0
+    i = next_sep_idx(target, 0) + 0
     while True:
         # invariants-start
         Invariant(Acc(list_pred(target), 1 / 2))
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -646,7 +646,7 @@
                    rendered(ToSeq(target), e))
         # the separator itself is one literal node carrying [j, e) verbatim.
         copy_span(out, target, j, e)
-        out.append(-2)
+        out.append(-1)
         i = e
     return out
     # impl-end
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -589,65 +589,9 @@
     Ensures(ToSeq(Result()) == rendered(ToSeq(target), 0))
     # post-conditions-end
     # impl-start
+    Assert(False)
     out = []  # type: List[int]
-    n = len(target)
-    i = 0
-    while True:
-        # invariants-start
-        Invariant(Acc(list_pred(target), 1 / 2))
-        Invariant(Acc(list_pred(out)))
-        Invariant(0 <= i and i <= n)
-        Invariant(n == len(target))
-        Invariant(n == len(ToSeq(target)))
-        # telescoping fold: what has been emitted, concatenated with the node
-        # stream of the remaining suffix, is the whole node stream.
-        Invariant(ToSeq(out) + rendered(ToSeq(target), i) ==
-                  rendered(ToSeq(target), 0))
-        # The condition is the constant `True`, so the bound comes from what the
-        # break counts down: the loop leaves via `break` as soon as no separator
-        # remains at or after i, and otherwise resumes at i = e, the end of a
-        # separator that starts at j >= i and ends strictly after it (sep_end's
-        # postcondition), so the scan index rises by at least one per pass and at
-        # most n - i + 1 passes remain. It strictly decreases because only i
-        # changes (n is a local fixed before the loop, pinned by
-        # Invariant(n == len(target))), and it stays >= 1 because
-        # Invariant(0 <= i and i <= n) holds on entry to every pass (so it never
-        # reaches the unsatisfiable 0); the pass on which no separator remains is
-        # the one that breaks.
-        Invariant(MustTerminate(n - i + 1))
-        # invariants-end
-        # `+ 0` reads the boundary as the plain integer it is; see `sep_end`.
-        j = next_sep_idx(target, i) + 0
-        if j >= n:
-            if i < n:
-                Assert(rendered(ToSeq(target), i) ==
-                       (ToSeq(target).take(n).drop(i) + PSeq(-1)) + PSeq(-3))
-                # the trailing text is one cross-reference carrying it verbatim.
-                copy_span(out, target, i, n)
-                out.append(-1)
-            else:
-                Assert(rendered(ToSeq(target), i) == PSeq(-3))
-            out.append(-3)
-            break
-        e = sep_end_idx(target, j) + 0
-        Assert(j < e and e <= n)
-        if j > i:
-            Assert(rendered(ToSeq(target), i) ==
-                   ((ToSeq(target).take(j).drop(i) + PSeq(-1)) +
-                    (ToSeq(target).take(e).drop(j) + PSeq(-2))) +
-                   rendered(ToSeq(target), e))
-            # the text before the separator is one cross-reference carrying
-            # exactly the specification's characters over [i, j).
-            copy_span(out, target, i, j)
-            out.append(-1)
-        else:
-            Assert(rendered(ToSeq(target), i) ==
-                   (ToSeq(target).take(e).drop(i) + PSeq(-2)) +
-                   rendered(ToSeq(target), e))
-        # the separator itself is one literal node carrying [j, e) verbatim.
-        copy_span(out, target, j, e)
-        out.append(-2)
-        i = e
+    out.append(-3)
     return out
     # impl-end
 
```

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good)

```diff
@@ -623,7 +623,6 @@
                 Assert(rendered(ToSeq(target), i) ==
                        (ToSeq(target).take(n).drop(i) + PSeq(-1)) + PSeq(-3))
                 # the trailing text is one cross-reference carrying it verbatim.
-                copy_span(out, target, i, n)
                 out.append(-1)
             else:
                 Assert(rendered(ToSeq(target), i) == PSeq(-3))
@@ -638,14 +637,12 @@
                    rendered(ToSeq(target), e))
             # the text before the separator is one cross-reference carrying
             # exactly the specification's characters over [i, j).
-            copy_span(out, target, i, j)
             out.append(-1)
         else:
             Assert(rendered(ToSeq(target), i) ==
                    (ToSeq(target).take(e).drop(i) + PSeq(-2)) +
                    rendered(ToSeq(target), e))
         # the separator itself is one literal node carrying [j, e) verbatim.
-        copy_span(out, target, j, e)
         out.append(-2)
         i = e
     return out
```

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good)

```diff
@@ -624,7 +624,6 @@
                        (ToSeq(target).take(n).drop(i) + PSeq(-1)) + PSeq(-3))
                 # the trailing text is one cross-reference carrying it verbatim.
                 copy_span(out, target, i, n)
-                out.append(-1)
             else:
                 Assert(rendered(ToSeq(target), i) == PSeq(-3))
             out.append(-3)
```

Attack 11 — `atk_11.py` → rejected (same spec, does not verify — good)

```diff
@@ -716,8 +716,6 @@
     if (i < n and is_space(s[i]) and a + 2 < n and s[a] == 111 and
             s[a + 1] == 114 and is_space(s[a + 2])):
         return strip_left_idx(s, a + 2, n)
-    if a < n and s[a] == 124:
-        return strip_left_idx(s, a + 1, n)
     if i + 2 < n and s[i] == 46 and s[i + 1] == 46 and s[i + 2] == 46:
         return i + 3
     return -1
```

Attack 12 — `atk_12.py` → rejected (same spec, does not verify — good)

```diff
@@ -779,16 +779,22 @@
     # post-conditions-end
     # impl-start
     t = i
-    while t < j:
+    while t < j and is_space(s[t]):
         # invariants-start
         Invariant(Acc(list_pred(s), 1 / 2))
         Invariant(list_pred(out))
         Invariant(ToSeq(s) == Old(ToSeq(s)))
         Invariant(i <= t and t <= j and j <= len(s))
-        Invariant(ToSeq(out) == Old(ToSeq(out)) + ToSeq(s).take(t).drop(i))
-        # At most j - t + 1 passes remain: j is a parameter the loop never changes
-        # and t rises by exactly one per pass, so the bound strictly decreases; the
-        # guard t < j keeps it >= 2 on entry to a pass.
+        Invariant(ToSeq(out) == Old(ToSeq(out)))
+        Invariant(MustTerminate(j - t + 1))
+        # invariants-end
+        t = t + 1
+    while t < j:
+        # invariants-start
+        Invariant(Acc(list_pred(s), 1 / 2))
+        Invariant(list_pred(out))
+        Invariant(ToSeq(s) == Old(ToSeq(s)))
+        Invariant(i <= t and t <= j and j <= len(s))
         Invariant(MustTerminate(j - t + 1))
         # invariants-end
         out.append(s[t])
```

Attack 13 — `atk_13.py` → rejected (same spec, does not verify — good)

```diff
@@ -673,6 +673,17 @@
         Invariant(Acc(list_pred(s), 1 / 2))
         Invariant(ToSeq(s) == Old(ToSeq(s)))
         Invariant(i <= k and k <= len(s))
+        Invariant(MustTerminate(len(s) - k + 1))
+        # invariants-end
+        if s[k] == 91:
+            return len(s)
+        k = k + 1
+    k = i
+    while k < len(s):
+        # invariants-start
+        Invariant(Acc(list_pred(s), 1 / 2))
+        Invariant(ToSeq(s) == Old(ToSeq(s)))
+        Invariant(i <= k and k <= len(s))
         Invariant(next_sep(ToSeq(s), i) == next_sep(ToSeq(s), k))
         # At most len(s) - k + 1 passes remain: the sequence is held read-only by
         # the invariant above so its length cannot change, and k rises by exactly
```

Attack 14 — `atk_14.py` → rejected (same spec, does not verify — good)

```diff
@@ -497,62 +497,19 @@
     Ensures(ToSeq(Result()) == seg_text(ToSeq(s), i, j))
     # post-conditions-end
     # impl-start
-    a = i
-    while a < j and is_space(s[a]):
+    out = []  # type: List[int]
+    t = i
+    while t < j:
         # invariants-start
         Invariant(Acc(list_pred(s), 1 / 2))
         Invariant(ToSeq(s) == Old(ToSeq(s)))
-        Invariant(i <= a and a <= j and j <= len(s))
-        Invariant(strip_left(ToSeq(s), i, j) == strip_left(ToSeq(s), a, j))
-        # At most j - a + 1 passes remain: the compound guard terminates on the
-        # counter alone (the whitespace test only makes the scan stop sooner), j is
-        # a parameter the loop never changes, and a rises by exactly one per pass,
-        # so the bound strictly decreases; the guard a < j keeps it >= 2 on entry to
-        # a pass.
-        Invariant(MustTerminate(j - a + 1))
-        # invariants-end
-        a = a + 1
-    Assert(strip_left(ToSeq(s), a, j) == a)
-    # `a` is now strip_left(s, i, j); reference that nested form directly so the
-    # final equality with seg_text needs no nested-application congruence.
-    b = j
-    while b > a and is_space(s[b - 1]):
-        # invariants-start
-        Invariant(Acc(list_pred(s), 1 / 2))
-        Invariant(ToSeq(s) == Old(ToSeq(s)))
-        Invariant(a <= b and b <= j and j <= len(s))
-        Invariant(a == strip_left(ToSeq(s), i, j))
-        Invariant(strip_right(ToSeq(s), strip_left(ToSeq(s), i, j), j) ==
-                  strip_right(ToSeq(s), strip_left(ToSeq(s), i, j), b))
-        # At most b - a + 1 passes remain: this scan counts DOWN, the compound
-        # guard terminates on the counter alone (the whitespace test only makes it
-        # stop sooner), a is fixed for the whole loop (it was settled by the previous
-        # scan), and b drops by exactly one per pass, so the bound strictly
-        # decreases; the guard b > a keeps it >= 2 on entry to a pass.
-        Invariant(MustTerminate(b - a + 1))
-        # invariants-end
-        b = b - 1
-    Assert(strip_right(ToSeq(s), strip_left(ToSeq(s), i, j), b) == b)
-    out = []  # type: List[int]
-    t = a
-    while t < b:
-        # invariants-start
-        Invariant(Acc(list_pred(s), 1 / 2))
-        Invariant(ToSeq(s) == Old(ToSeq(s)))
-        Invariant(a <= t and t <= b and b <= len(s))
-        Invariant(a == strip_left(ToSeq(s), i, j))
-        Invariant(b == strip_right(ToSeq(s), strip_left(ToSeq(s), i, j), j))
+        Invariant(i <= t and t <= j and j <= len(s))
         Invariant(Acc(list_pred(out)))
-        Invariant(ToSeq(out) == ToSeq(s).take(t).drop(a))
-        # At most b - t + 1 passes remain: b is fixed for the whole loop (settled
-        # by the trailing-space scan) and t rises by exactly one per pass, so the
-        # bound strictly decreases; the guard t < b keeps it >= 2 on entry to a
-        # pass.
-        Invariant(MustTerminate(b - t + 1))
+        Invariant(ToSeq(out) == ToSeq(s).take(t).drop(i))
+        Invariant(MustTerminate(j - t + 1))
         # invariants-end
         out.append(s[t])
         t = t + 1
-    Assert(ToSeq(out) == ToSeq(s).take(b).drop(a))
     return out
     # impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

**SOUND.** 14 attacks, all same-spec (byte-identical spec view, adversary same-spec exit 0 on each), all with unsound_evasions=none (no new @ContractOnly / Assume / axiom). Positive control = unmodified model.py: VERIFIED in 81.9s, so the rejections are not the artifact of an unsatisfiable spec.

**COMMANDS.** Build: gen.py/mk.py/mk2.py in the scratch dir splice ONE function's `# impl-start`/`# impl-end` body, leaving everything else byte-identical. Per attack N: `python -m swebench_unified.adversary same-spec nagini sphinx-doc__sphinx-9258 atk_N.py` (exit 0 on all 14) then `python -m swebench_unified.adversary weakness nagini sphinx-doc__sphinx-9258 atk_N.py` under SBU_ATTACK_VERIFY_TIMEOUT=900 SBN_VERIFY_TIMEOUT=900, run 3-at-a-time as background jobs (logs w_1..w_14.log). Control: `adversary verify ... pos_control.py`.

#### RESULTS (every one 'NOT-A-COUNTEREXAMPLE: attack does not verify', RC=2 — no timeouts, no no-verdicts):
- atk_1 PREPATCH BUG, kind reading: split_render returns [True] for every spec (model_prepatch's defect). Rejected by A7 (marks).
- atk_2 PREPATCH BUG, primary obligation: one cross-reference carrying the WHOLE string, bar+padding swallowed inside it. Rejected by P7 (rendered).
- atk_3 PARTIAL-DOMAIN: gold except renders nothing when the spec opens with '[' (the shape well_formed is false on). Rejected — P7 carries NO domain clause.
- atk_4 BOUNDARY: gold count/kinds/separator spans; trailing xref carries [i+1,n) ('int | str' -> 'int','tr'). Rejected by P7.
- atk_5 CONTROL-FLOW-EFFECT / frame mutation: gold body + `target[0] = target[0]`. Rejected by the permission system (half permission).
- atk_6 UNGROUNDED-ORACLE ECHO: does not compute its start, asks the spec's OWN boundary oracle next_sep_idx and renders from the first separator, dropping preceding text. Rejected — P7 is anchored at 0, so the telescoping invariant fails on ENTRY.
- atk_7 KIND SWAP: separator emitted with marker -1 instead of -2 (dropping `if delims_re.match(piece)`). Rejected by P7.
- atk_8 VACUITY CONTROL: `Assert(False)` + render nothing. Rejected — the frozen spec region hands the verifier no contradiction, so the obligations are not discharged for free.
- atk_9 MARKERS ONLY: gold boundaries/count/kinds, all three copy_span calls dropped (payload free). Rejected by P7 — the retained kind obligation alone would have admitted it.
- atk_10 NODE REMERGE: same characters in order, trailing name loses its own -1 marker (different node PARTITION). Rejected — the markers genuinely delimit nodes (injective encoding).
- atk_11 THE CHANGED LINE REVERTED, in the helper: render_nodes/split_render left gold verbatim; only sep_end_idx loses its `s[a] == 124` branch, i.e. patch.diff's added `\s*\|\s*` removed. Rejected by sep_end_idx's own Ensures — the change is carried at the helper contract, not only at the top.
- atk_12 PAYLOAD FREEDOM IN THE HELPER: copy_span skips leading whitespace, so every padded node's text is trimmed while count/kinds/boundaries stay gold. Rejected by copy_span's Ensures + P7.
- atk_13 PARTIAL-DOMAIN INSIDE THE BOUNDARY ORACLE: next_sep_idx reports 'no separator' once a '[' is seen; bar-only specs stay gold. Rejected by next_sep_idx's Ensures.
- atk_14 RETAINED-HELPER DRIFT: slice_trim returns the UNtrimmed slice. Rejected — the retained bar-only region is not inert.

WRONGNESS CONTROL (wrongness.py): each attack's rendering was simulated and compared against the REAL patched pipeline (re.split(delims)+filter(None,...)+delims_re.match). All 11 simulable attacks differ from the real result on an F2P/P2P input (e.g. atk_2/atk_11 -> [(True,'int | str')] vs real [(True,'int'),(False,' | '),(True,'str')]; atk_13 on '[a] | b' -> one whole-string xref vs real 5 nodes). So the 14 rejections are genuine refutations of wrong impls, not a too-strong spec rejecting correct ones.

A-LEG AUDIT (my lane). refinement.md has 16 legs, tags: R x3, I x2, R+I x6, A-reference x4, R+A-reference x1 — every leg is R / A-consumed / A-reference / I, NO kind-3, and no leg is untagged. No CONSUMED axiom: meta.json axioms==[], deep_model_references are all kind 'A-reference', and model.py's axioms region holds only a comment (the single '@ContractOnly' hit is that comment's own prose, not a declaration).
I re-derived the A-reference correspondence INDEPENDENTLY rather than trusting G-AX/G-CONF: aleg.py is a hand re-transcription of the pure region (is_space, strip_left, sep_end, next_sep, rendered, marks) from model.py's own definitions, compared against the real patched regex pipeline with the node kind read off the BRANCH taken (python.py:319 literal vs 321 xref, as P4/P5/A4/A5 bind it). Results, 0 divergences everywhere: exhaustive length<=5 over the delimiter-dense alphabet '| ,or[].a' (66,430 inputs); 250,000 random draws over an alphabet of 24 tokens incl. TAB/NL/VT/FF/U+001C-001F/NEL/NBSP/U+2000-200A/U+2028/U+202F/U+205F/U+3000; is_space == regex \s over the FULL Unicode range 0..0x10FFFF (0 mismatches in 1,114,112 code points); 18 named realistic specs incl. the F2P 'int | str', 'list[int] | None', 'Dict[str, str]', 'Tuple[str, ...]', 'str or int', '', '|', 'a||b', ' | '; and the marks kind-projection against the real kinds. So sep_end's hand-ordered 4-way alternation does reproduce the regex's leftmost-then-preference semantics, and P2/P3/A2/A3/A7 hold as stated.
Model<->patch correspondence spot-checked at the decode: P7 at target='int | str' decodes to [(True,'int'),(False,' | '),(True,'str')], which is exactly what the F2P test_info_field_list_piped_type asserts (two pending_xref carrying 'int'/'str' with literal_emphasis ' | ' between). Untrimmed payload confirmed against the real code, not against the doc.

ONE RECORDED IMPRECISION, not a finding at this gate: mapping.md §2 words the -1 marker as `isinstance(node, addnodes.pending_xref)`, but the real call sites pass rolename=None, under which docfields.py:68 short-circuits and the xref branch yields a plain emphasis — so that literal reading is degenerate. refinement.md P4/P5/A4/A5 bind the marker to the BRANCH (python.py:321 vs 319), and under the branch reading the correspondence is exact everywhere I measured. This is a bridge-wording issue in mapping.md's type table, already noted by G-PANEL-2; it does not affect any leg's tag or the model<->patch correspondence.

Zero resolve runs were launched because no attack verified — the resolve exception in the brief never became applicable, and there is no missing-evidence gap standing between these attacks and the verdict.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

**ATTACK GOAL:** find an input where the modeled function disagrees with the REAL repo callee (patch.diff APPLIED, per the brief). Result: no such input found across ~490k machine-checked inputs, including exhaustive coverage of every string up to length 5 over a delimiter-dense alphabet. Verdict FAITHFUL.

SETUP. Worktree at base_commit 06107f838 with patch.diff applied -- confirmed `git diff` is exactly the one-line delims change and `grep` shows python.py:307 carries `\s*\|\s*`. Built  (python3.10 + docutils 0.23) and a `types.Union` shim (the repo guards on sys.version_info > (3,10)) so the REAL sphinx.domains.python module IMPORTS and its real method is CALLED -- not transliterated. Startup guards replicated: `inspect.getsource` contains the patched alternative, and `PyField.make_xrefs is PyXrefMixin.make_xrefs`. I independently re-transcribed model.py's whole pure region (is_space, strip_left/right, seg_text, first_bar, no_other_sep, well_formed, kinds, sep_end, next_sep, rendered, marks) into mdl.py rather than reusing the bundle's conformance_check.py shadow, so the comparison does not inherit a mis-copy from the bundle's own harness.

**ORACLE:** node text is OBSERVED, not assumed -- a recording stand-in is passed as `innernode` and the k-th node's text is read off the k-th call, with `len(calls) == len(nodes)` asserted on EVERY input (never tripped). Node kind read from the source branch actually taken (python.py:319 literal vs 321 xref).

### EVIDENCE (0 divergences everywhere):
1. `is_space` == regex `\s` over the FULL Unicode range 0..0x10FFFF: 0 mismatches (1,114,112 code points). This was the previously-recorded divergence class (non-ASCII whitespace beside a bar); it is genuinely closed at the source, not excluded from the domain.
2. Exhaustive length 0..3 over 14 chars + 200k random over a 29-token alphabet incl. TAB/NL/VT/FF/U+001C/U+001D/U+001E/U+001F/NEL/NBSP/U+2000-200A/U+2028/U+202F/U+205F/IDEOGRAPHIC SPACE: 202,955 inputs, 0 bad on BOTH `rendered` (stream: node count + per-node kind + per-node exact text) and `marks` (kinds).
3. Exhaustive length 0..5 over the delimiter-dense alphabet {| , space, o, r, [, ',', '.', a}: 37,449 inputs, 0 bad. This is total coverage of the tokeniser's interaction space at small length -- adjacent/overlapping delimiters, ' or ' straddling a bar, '..' vs '...', bracket+optional-`or`, leading/trailing/doubled bars.
4. Dot/tilde stratum: 82,801 inputs with 34,470 carrying a '.'/'~'-prefixed piece, 0 bad. The `make_xref` callee's display rewrite (python.py:293-301) is a genuine DOWNSTREAM rewrite of the piece, disclosed in mapping.md; the modeled observable (the piece handed to the branch) is unaffected, which I confirmed by measurement, not by taking the doc's word.
5. Long-token stress: 120,000 inputs built from 34 multi-char tokens up to 18 tokens deep, 0 bad.
6. Argument-configuration sweep: 24,716 inputs x 3 field classes actually registered in PyObject.doc_field_types (PyField, PyTypedField, PyGroupedField) x 4 innernode factories actually passed at the real docfields.py call sites (nodes.emphasis, nodes.Text, literal_strong, literal_emphasis) x contnode in {None, Text(target)} = 24 configurations, 0 bad in all 24. So the model being a function of `target` ALONE is not an over-abstraction: `split_contnode`/`innernode` do not perturb the tokenisation the spec pins.

### TOO-STRONG CHECKS (the specific ways this spec could over-claim, each probed and each clean):
- The two obligations are domain-FREE (no `well_formed` precondition on render_nodes or split_render). A domain-free postcondition is the strongest place a faithfulness break can hide, so I fuzzed the off-shape region hardest: brackets, commas, `or`, `...`, bare/leading/trailing/doubled bars, whitespace-only segments, empty string. `rendered`/`marks` hold there too. Confirmed the docs' own worked example: 'list[int] | None' -> real 6 nodes [T,F,T,F,F,T], and `marks` gives exactly that (the bar-only `kinds` gives 3, which is why `kinds` is correctly NOT any postcondition -- de-gating it WOULD have been unfaithful, and the bundle does not do that).
- `sep_end`'s hand-ordered 4-way alternation could mis-model the regex's leftmost-then-preference semantics. Exhaustive length<=5 over {|,space,o,r,[,',','.',a} is precisely the stress case for this and finds nothing.
- Separator payload: the spec models each literal node as the UNTRIMMED span with padding. Verified against the real node text ('x  |  y' -> literal carries '  |  '; '[ a ]' -> '[ ' and ' ]'). The refinement.md note that the old `seg_text`-equals-carried-text comparison was REMOVED because it is false, and replaced by the untrimmed span, matches what the real function does -- that is a correctly-repaired model, not a drifted one.
- One narrow observation, NOT a defect: mapping.md §2 words the -1 marker as `isinstance(node, addnodes.pending_xref)`. The real call sites pass rolename=None (PyField.rolename and PyTypedField.rolename are both None), and under rolename=None docfields.py:68 short-circuits so the xref branch returns a plain emphasis, making the isinstance test degenerate (measured: 4836/5000 mismatches under that literal reading). This does NOT make the spec unfaithful: mapping.md and refinement.md both bind the marker to the BRANCH ("the `make_xref` branch, python.py:321" / "the `contnode or innernode` branch, python.py:319"), and under that branch reading the stream is exact at rolename in {'class', None, ''} -- 44,681 inputs each, 0 bad. The real change under specification is which pieces reach which branch, and the spec pins that correctly. The isinstance phrasing is a bridge-wording imprecision in the conformance harness's type bridge, not an input on which the modeled function disagrees with the real callee.

DIRECTION-OF-COMPARISON GUARD (per the brief): I did NOT report the patch delta as a divergence. Confirmed the model describes the FIXED behavior by re-running against the BASE (unpatched) delims: model != base on 'int | str', 'a|b', 'list[int] | None'. So the spec senses the change (G-DIFF holds) and the reference I compared against was the patched worktree throughout.

**CONCLUSION:** no diverging input exists that I could find; the spec is neither too strong nor drifted from real repo behavior. Note that a FAITHFUL verdict here bounds only this gate -- I did not assess spec strength/weakness (G-PANEL-1's lane), and the refinement.md admission that the meta.json G-CONF stamp predates the domain-free kind obligation and is due a re-run is a records-freshness matter for the gate, orthogonal to faithfulness. My independent re-measurement above supersedes it on the substance: the obligations hold on the full domain.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

**SCOPE:** no relaxation to inherit. I checked directly rather than trusting verdict.md's narration: `'relaxed_leakage' in json.load(nagini/meta.json)` -> False (key list is additional_change_sites/axioms/base_commit/changed_files/deep_model_references/float_encoding/gates/instance_id/modeled_functions/patch_diff/prepatch_models/region_hashes/repo/schema_version/string_modeling/version), and `find benchmark-verified/sphinx-doc__sphinx-9258/ -iname '*RELAX*'` -> empty. So there is no unavoidability argument to re-derive and no disposition asserted at me; this is a plain leakage judgement. (Note: verdict.md contains the string 'relaxed_leakage' only inside its own prior SCOPE paragraph, duplicated three times -- an appended-record artifact, not a relaxation claim.)

DECISIVE MEASUREMENT -- spec views coincide across the patch boundary. I built both views myself with markers.spec_view(src, get_backend('nagini')): model.py -> 549 lines, model_prepatch.py -> 549 lines, and `diff` reports them BYTE-IDENTICAL (sha256 5c31a88a40bef25e...). markers.same_spec(model.py, model_prepatch.py, nagini) -> True and markers.spec_signature equality -> True. A spec view that is bit-for-bit the same on the gold and pre-patch models carries zero bits discriminating one from the other, so there is no line that could be pointed at as leaking the edit. The whole gold/prepatch delta lives inside elided `# impl-start/# impl-end` regions.

GOLD-LINE / PATH / SYMBOL SCREEN, run with a live control. leakage.screen(model.py, nagini backend, instance.patch, instance.problem_statement, instance.test_patch) -> passed=True, hard_failures=[], warnings=[]. Control: I injected the gold line `delims = r'(\s*[\[\]\(\),](?:\s*or\s)?\s*|\s+or\s+|\s*\|\s*|\.\.\.)'` into the module docstring (spec region) and re-ran -> passed=False, hard_failures=['L1: gold-patch line reproduced: ...'], so the screen is actually sensitive on this bundle and its pass is a measurement, not a default. Independently, whitespace-normalized containment of BOTH the added and the removed patch line against the view -> False/False. Token counts in the 549-line view: sphinx/domains/python.py 0, sphinx.domains.python 0, make_xrefs 0, make_xref 0, delims 0, delims_re 0, sub_targets 0, innernode 0, contnode 0, rolename 0, TextlikeNode 0, re.split 0, re.compile 0, '(?:' 0, '\s*' 0, pending_xref 0, emphasis 0.

**EDIT-FRAMING:** grep -iE over the view for added|adding|newly|no longer|used to|previously|regression|bug|fix(ed|es)|patch|broken|incorrectly|wrongly|prior to -> ZERO hits. The docstring states the bar behaviour as a required property ('must produce ... k cross-references interleaved with k-1 literal separators') and states the forbidden reading as a property of the spec, not as a before/after. model_prepatch.py's defect-narrating comments sit inside impl regions and are elided -- which is exactly why the two views coincide.

WHY NAMING THE BAR IS NOT BEYOND problem_statement. The bar is the public ask verbatim: the problem_statement is titled '[RFE] Support union types specification using | (vertical bar/pipe)' and shows ':type text: bytes | str'. Omitting it would make the spec unfaithful, not discreet. I then checked that the view's other three separator tokens are not gold-only knowledge: `git show 06107f838c28ab6ca6bfc2cc208e15997fcb2146:sphinx/domains/python.py` from the upstream repository (read-only, no worktree written) shows the PRE-patch line 307 already carries the bracket/comma-with-optional-`or`, whitespace-bounded `or`, and three-dot tokens. So `sep_end`'s documented four-token try-order names one public-from-the-issue token and three public-from-base_commit tokens, with no ordering privilege marking which is the one to add.

**NO BUNDLE-DIRECTED-AT-REVIEWER TEXT:** leakage.reviewer_directed() over every .md/.json/.py in nagini/ -> zero hits, and a manual grep of refinement.md, mapping.md, axiom_check.py, conformance_check.py, model.py for auditor|reviewer|panel|G-PANEL|honest verdict|do not submit|recording convention|attacker -> nothing. No file attempts to tell me what to record.

One observation, not a finding at this layer: refinement.md:25-26 and :81-82 quote the raw before/after `delims` regex, i.e. the gold edit in full. That is expected for a refinement/mapping document (the human-facing proof-obligation mapping) and it is NOT part of the spec view a solver consumes -- spec_view is computed from model.py alone, and refinement.md is read by the audit/score/integrity paths, not handed to the implementer. Flagging it so the record shows I looked at it rather than only at model.py.

**CONCLUSION:** NO-LEAKAGE. Byte-identical pre/post spec views is the decisive fact; the mechanical screen passes with a demonstrated-sensitive control; every separator fact in the view is derivable from problem_statement plus the base_commit source. hints_text was never consulted (I confirmed its length only, 1450 chars, and did not read it).

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.
