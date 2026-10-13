# P2 adversarial audit — sphinx-doc__sphinx-7757

**Backend:** `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 15 admissible attacks re-run of 15 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 15 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 14 | `atk_1.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py`, `atk_9.py`, `atk_10.py`, `atk_11.py`, `atk_12.py`, `atk_13.py`, `atk_14.py`, `atk_15.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_2.py` |

**Non-vacuity.** The positive control `ctrl_gold.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE. Exactly one of 15 same-spec wrong-impl attacks came back a CANDIDATE (atk_2.py, the ungrounded-oracle echo that reads its result straight out of the deep spec function `resolved_default`). Protocol-required resolve run PERFORMED, not speculated: its faithful refined patch (patch_atk_2.diff, produced by real `git diff` against a fresh clone of repos/sphinx-doc_sphinx.git at base_commit 212fd67b9f0b4fae6a7c3501fdf1a9a5b2801329; a direct right-align on the UNPADDED args.defaults with no padded list, i.e. structurally different code from gold) => run_resolve('sphinx-doc__sphinx-7757', patch, run_id='sbu-eq-audit3-atk2') returned completed=True, RESOLVED=TRUE, note='resolved', patch_successfully_applied=True, F2P 1/1 success, P2P 33/33 success, PASS_TO_FAIL empty. So the only verifying rival is a CORRECT echo, not a weakness: verify=>correct holds on every impl I could construct. No verifying wrong impl exists.
```

**Attacks re-run (15):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -171,50 +171,43 @@
         [[ToSeq(Result())[p]]])))
     # post-conditions-end
     # impl-start
+    # PRE-PATCH skeleton (the bug): the positional-only prefix is handled by a
+    # separate pass that never assigns any default (so every positional-only
+    # parameter comes out EMPTY), and the ordinary parameters compute their
+    # default alignment over the ordinary-parameter count alone, ignoring the
+    # positional-only parameters that also consume supplied defaults.
     m = len(provided)
-    pad = positionals - m
+    regular = positionals - posonly
     result = []  # type: List[int]
     p = 0
     while p < positionals:
         # invariants-start
         Invariant(Acc(list_pred(provided), 1 / 2))
         Invariant(Acc(list_pred(result)))
-        Invariant(len(provided) == m and positionals - m == pad)
-        Invariant(0 <= pad and pad <= positionals)
+        Invariant(len(provided) == m)
+        Invariant(positionals - posonly == regular)
         Invariant(0 <= p and p <= positionals)
         Invariant(len(result) == p)
         Invariant(Forall(int, lambda j: (
             Implies(0 <= j and j < m, renderable(ToSeq(provided)[j])),
             [[ToSeq(provided)[j]]])))
-        Invariant(Forall(int, lambda q: (
-            Implies(0 <= q and q < p,
-                    ToSeq(result)[q] == resolved_default(
-                        q, positionals, m, ToSeq(provided))),
-            [[ToSeq(result)[q]]])))
         # decreasing measure discharging the method's MustTerminate obligation:
         # the number of positional parameters still to be resolved, +1 so the
         # last iteration still carries a positive level.
         Invariant(MustTerminate(positionals - p + 1))
         # invariants-end
-        old_seq = ToSeq(result)  # type: PSeq[int]
-        if p < pad:
-            Assert(resolved_default(p, positionals, m, ToSeq(provided))
-                   == EMPTY())
+        if p < posonly:
+            # positional-only parameter: pre-patch never sets a default
             result = result + [EMPTY()]
         else:
-            Assert(provided[p - pad] == ToSeq(provided)[p - pad])
-            Assert(renderable(ToSeq(provided)[p - pad]))
-            Assert(renderable(provided[p - pad]))
-            Assert(resolved_default(p, positionals, m, ToSeq(provided))
-                   == render(ToSeq(provided)[p - pad]))
-            result = result + [render(provided[p - pad])]
-        # the new sequence extends the old by one element at index p
-        Assert(len(ToSeq(result)) == p + 1)
-        Assert(Forall(int, lambda q: (
-            Implies(0 <= q and q < p, ToSeq(result)[q] == old_seq[q]),
-            [[ToSeq(result)[q]], [old_seq[q]]])))
-        Assert(ToSeq(result)[p] == resolved_default(
-            p, positionals, m, ToSeq(provided)))
+            i = p - posonly
+            if regular - i <= m:
+                Assert(provided[m - regular + i]
+                       == ToSeq(provided)[m - regular + i])
+                Assert(renderable(provided[m - regular + i]))
+                result = result + [render(provided[m - regular + i])]
+            else:
+                result = result + [EMPTY()]
         p = p + 1
     return result
     # impl-end
```

Attack 2 — `atk_2.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -171,16 +171,16 @@
         [[ToSeq(Result())[p]]])))
     # post-conditions-end
     # impl-start
+    # UNGROUNDED-ORACLE ECHO: the result is read straight out of the deep spec
+    # function `resolved_default`, computing nothing of its own.
     m = len(provided)
-    pad = positionals - m
     result = []  # type: List[int]
     p = 0
     while p < positionals:
         # invariants-start
         Invariant(Acc(list_pred(provided), 1 / 2))
         Invariant(Acc(list_pred(result)))
-        Invariant(len(provided) == m and positionals - m == pad)
-        Invariant(0 <= pad and pad <= positionals)
+        Invariant(len(provided) == m)
         Invariant(0 <= p and p <= positionals)
         Invariant(len(result) == p)
         Invariant(Forall(int, lambda j: (
@@ -191,30 +191,9 @@
                     ToSeq(result)[q] == resolved_default(
                         q, positionals, m, ToSeq(provided))),
             [[ToSeq(result)[q]]])))
-        # decreasing measure discharging the method's MustTerminate obligation:
-        # the number of positional parameters still to be resolved, +1 so the
-        # last iteration still carries a positive level.
         Invariant(MustTerminate(positionals - p + 1))
         # invariants-end
-        old_seq = ToSeq(result)  # type: PSeq[int]
-        if p < pad:
-            Assert(resolved_default(p, positionals, m, ToSeq(provided))
-                   == EMPTY())
-            result = result + [EMPTY()]
-        else:
-            Assert(provided[p - pad] == ToSeq(provided)[p - pad])
-            Assert(renderable(ToSeq(provided)[p - pad]))
-            Assert(renderable(provided[p - pad]))
-            Assert(resolved_default(p, positionals, m, ToSeq(provided))
-                   == render(ToSeq(provided)[p - pad]))
-            result = result + [render(provided[p - pad])]
-        # the new sequence extends the old by one element at index p
-        Assert(len(ToSeq(result)) == p + 1)
-        Assert(Forall(int, lambda q: (
-            Implies(0 <= q and q < p, ToSeq(result)[q] == old_seq[q]),
-            [[ToSeq(result)[q]], [old_seq[q]]])))
-        Assert(ToSeq(result)[p] == resolved_default(
-            p, positionals, m, ToSeq(provided)))
+        result = result + [resolved_default(p, positionals, m, ToSeq(provided))]
         p = p + 1
     return result
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -171,6 +171,10 @@
         [[ToSeq(Result())[p]]])))
     # post-conditions-end
     # impl-start
+    # POSONLY-CLAUSE-SATISFYING MISALIGNMENT: every positional-only parameter
+    # inside the trailing default block does get a NON-EMPTY default (so the
+    # `posonly is not exempt` clause is satisfied) but it is the WRONG one --
+    # always the first supplied default instead of its aligned share.
     m = len(provided)
     pad = positionals - m
     result = []  # type: List[int]
@@ -191,30 +195,21 @@
                     ToSeq(result)[q] == resolved_default(
                         q, positionals, m, ToSeq(provided))),
             [[ToSeq(result)[q]]])))
-        # decreasing measure discharging the method's MustTerminate obligation:
-        # the number of positional parameters still to be resolved, +1 so the
-        # last iteration still carries a positive level.
         Invariant(MustTerminate(positionals - p + 1))
         # invariants-end
-        old_seq = ToSeq(result)  # type: PSeq[int]
         if p < pad:
-            Assert(resolved_default(p, positionals, m, ToSeq(provided))
-                   == EMPTY())
             result = result + [EMPTY()]
         else:
-            Assert(provided[p - pad] == ToSeq(provided)[p - pad])
-            Assert(renderable(ToSeq(provided)[p - pad]))
-            Assert(renderable(provided[p - pad]))
-            Assert(resolved_default(p, positionals, m, ToSeq(provided))
-                   == render(ToSeq(provided)[p - pad]))
-            result = result + [render(provided[p - pad])]
-        # the new sequence extends the old by one element at index p
-        Assert(len(ToSeq(result)) == p + 1)
-        Assert(Forall(int, lambda q: (
-            Implies(0 <= q and q < p, ToSeq(result)[q] == old_seq[q]),
-            [[ToSeq(result)[q]], [old_seq[q]]])))
-        Assert(ToSeq(result)[p] == resolved_default(
-            p, positionals, m, ToSeq(provided)))
+            if p < posonly:
+                Assert(provided[0] == ToSeq(provided)[0])
+                Assert(renderable(ToSeq(provided)[0]))
+                Assert(renderable(provided[0]))
+                result = result + [render(provided[0])]
+            else:
+                Assert(provided[p - pad] == ToSeq(provided)[p - pad])
+                Assert(renderable(ToSeq(provided)[p - pad]))
+                Assert(renderable(provided[p - pad]))
+                result = result + [render(provided[p - pad])]
         p = p + 1
     return result
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -171,6 +171,9 @@
         [[ToSeq(Result())[p]]])))
     # post-conditions-end
     # impl-start
+    # BOUNDARY off-by-one: the trailing default block starts one position LATE
+    # (`p <= pad`), so the parameter at index `pad` loses its default and
+    # provided[0] is never consumed.
     m = len(provided)
     pad = positionals - m
     result = []  # type: List[int]
@@ -191,30 +194,15 @@
                     ToSeq(result)[q] == resolved_default(
                         q, positionals, m, ToSeq(provided))),
             [[ToSeq(result)[q]]])))
-        # decreasing measure discharging the method's MustTerminate obligation:
-        # the number of positional parameters still to be resolved, +1 so the
-        # last iteration still carries a positive level.
         Invariant(MustTerminate(positionals - p + 1))
         # invariants-end
-        old_seq = ToSeq(result)  # type: PSeq[int]
-        if p < pad:
-            Assert(resolved_default(p, positionals, m, ToSeq(provided))
-                   == EMPTY())
+        if p <= pad:
             result = result + [EMPTY()]
         else:
             Assert(provided[p - pad] == ToSeq(provided)[p - pad])
             Assert(renderable(ToSeq(provided)[p - pad]))
             Assert(renderable(provided[p - pad]))
-            Assert(resolved_default(p, positionals, m, ToSeq(provided))
-                   == render(ToSeq(provided)[p - pad]))
             result = result + [render(provided[p - pad])]
-        # the new sequence extends the old by one element at index p
-        Assert(len(ToSeq(result)) == p + 1)
-        Assert(Forall(int, lambda q: (
-            Implies(0 <= q and q < p, ToSeq(result)[q] == old_seq[q]),
-            [[ToSeq(result)[q]], [old_seq[q]]])))
-        Assert(ToSeq(result)[p] == resolved_default(
-            p, positionals, m, ToSeq(provided)))
         p = p + 1
     return result
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -171,6 +171,8 @@
         [[ToSeq(Result())[p]]])))
     # post-conditions-end
     # impl-start
+    # FRAME / CONTROL-FLOW EFFECT: the frozen gold loop verbatim, then the
+    # read-only supplied-defaults list is clobbered before returning.
     m = len(provided)
     pad = positionals - m
     result = []  # type: List[int]
@@ -216,5 +218,7 @@
         Assert(ToSeq(result)[p] == resolved_default(
             p, positionals, m, ToSeq(provided)))
         p = p + 1
+    if m > 0:
+        provided[0] = EMPTY()
     return result
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -171,50 +171,6 @@
         [[ToSeq(Result())[p]]])))
     # post-conditions-end
     # impl-start
-    m = len(provided)
-    pad = positionals - m
-    result = []  # type: List[int]
-    p = 0
-    while p < positionals:
-        # invariants-start
-        Invariant(Acc(list_pred(provided), 1 / 2))
-        Invariant(Acc(list_pred(result)))
-        Invariant(len(provided) == m and positionals - m == pad)
-        Invariant(0 <= pad and pad <= positionals)
-        Invariant(0 <= p and p <= positionals)
-        Invariant(len(result) == p)
-        Invariant(Forall(int, lambda j: (
-            Implies(0 <= j and j < m, renderable(ToSeq(provided)[j])),
-            [[ToSeq(provided)[j]]])))
-        Invariant(Forall(int, lambda q: (
-            Implies(0 <= q and q < p,
-                    ToSeq(result)[q] == resolved_default(
-                        q, positionals, m, ToSeq(provided))),
-            [[ToSeq(result)[q]]])))
-        # decreasing measure discharging the method's MustTerminate obligation:
-        # the number of positional parameters still to be resolved, +1 so the
-        # last iteration still carries a positive level.
-        Invariant(MustTerminate(positionals - p + 1))
-        # invariants-end
-        old_seq = ToSeq(result)  # type: PSeq[int]
-        if p < pad:
-            Assert(resolved_default(p, positionals, m, ToSeq(provided))
-                   == EMPTY())
-            result = result + [EMPTY()]
-        else:
-            Assert(provided[p - pad] == ToSeq(provided)[p - pad])
-            Assert(renderable(ToSeq(provided)[p - pad]))
-            Assert(renderable(provided[p - pad]))
-            Assert(resolved_default(p, positionals, m, ToSeq(provided))
-                   == render(ToSeq(provided)[p - pad]))
-            result = result + [render(provided[p - pad])]
-        # the new sequence extends the old by one element at index p
-        Assert(len(ToSeq(result)) == p + 1)
-        Assert(Forall(int, lambda q: (
-            Implies(0 <= q and q < p, ToSeq(result)[q] == old_seq[q]),
-            [[ToSeq(result)[q]], [old_seq[q]]])))
-        Assert(ToSeq(result)[p] == resolved_default(
-            p, positionals, m, ToSeq(provided)))
-        p = p + 1
-    return result
+    # DIVERGENCE / self-delegation: the prior audit pass's BREAK, re-encoded.
+    return resolve_positional_defaults(positionals, posonly, provided)
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -171,6 +171,11 @@
         [[ToSeq(Result())[p]]])))
     # post-conditions-end
     # impl-start
+    # PARTIAL-DOMAIN WRONGNESS pinned to EXACTLY the F2P signature
+    # `(a, b=0, /, c=1)` -> positionals=3, posonly=2, m=2: the defaulted
+    # positional-only parameter `b` (index 1) loses its default, which is the
+    # pre-patch bug narrowed to the one shape the hidden test exercises. Every
+    # other admissible input gets the gold answer.
     m = len(provided)
     pad = positionals - m
     result = []  # type: List[int]
@@ -191,30 +196,18 @@
                     ToSeq(result)[q] == resolved_default(
                         q, positionals, m, ToSeq(provided))),
             [[ToSeq(result)[q]]])))
-        # decreasing measure discharging the method's MustTerminate obligation:
-        # the number of positional parameters still to be resolved, +1 so the
-        # last iteration still carries a positive level.
         Invariant(MustTerminate(positionals - p + 1))
         # invariants-end
-        old_seq = ToSeq(result)  # type: PSeq[int]
         if p < pad:
-            Assert(resolved_default(p, positionals, m, ToSeq(provided))
-                   == EMPTY())
             result = result + [EMPTY()]
         else:
-            Assert(provided[p - pad] == ToSeq(provided)[p - pad])
-            Assert(renderable(ToSeq(provided)[p - pad]))
-            Assert(renderable(provided[p - pad]))
-            Assert(resolved_default(p, positionals, m, ToSeq(provided))
-                   == render(ToSeq(provided)[p - pad]))
-            result = result + [render(provided[p - pad])]
-        # the new sequence extends the old by one element at index p
-        Assert(len(ToSeq(result)) == p + 1)
-        Assert(Forall(int, lambda q: (
-            Implies(0 <= q and q < p, ToSeq(result)[q] == old_seq[q]),
-            [[ToSeq(result)[q]], [old_seq[q]]])))
-        Assert(ToSeq(result)[p] == resolved_default(
-            p, positionals, m, ToSeq(provided)))
+            if positionals == 3 and posonly == 2 and m == 2 and p == 1:
+                result = result + [EMPTY()]
+            else:
+                Assert(provided[p - pad] == ToSeq(provided)[p - pad])
+                Assert(renderable(ToSeq(provided)[p - pad]))
+                Assert(renderable(provided[p - pad]))
+                result = result + [render(provided[p - pad])]
         p = p + 1
     return result
     # impl-end
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -171,6 +171,8 @@
         [[ToSeq(Result())[p]]])))
     # post-conditions-end
     # impl-start
+    # RAISE-EXIT: the gold answer is computed and then thrown away by leaving
+    # through an exception instead of a return.
     m = len(provided)
     pad = positionals - m
     result = []  # type: List[int]
@@ -216,5 +218,5 @@
         Assert(ToSeq(result)[p] == resolved_default(
             p, positionals, m, ToSeq(provided)))
         p = p + 1
-    return result
+    raise Exception()
     # impl-end
```

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good)

```diff
@@ -171,6 +171,15 @@
         [[ToSeq(Result())[p]]])))
     # post-conditions-end
     # impl-start
+    # DECORATIVE MEASURE: an unbounded loop ahead of the gold work carrying a
+    # CONSTANT MustTerminate level, i.e. a measure that appears but does not
+    # decrease.
+    spin = 0
+    while spin >= 0:
+        Invariant(Acc(list_pred(provided), 1 / 2))
+        Invariant(0 <= spin)
+        Invariant(MustTerminate(1))
+        spin = spin + 1
     m = len(provided)
     pad = positionals - m
     result = []  # type: List[int]
```

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good)

```diff
@@ -171,6 +171,8 @@
         [[ToSeq(Result())[p]]])))
     # post-conditions-end
     # impl-start
+    # LEFT-ALIGN (mirror image of the required right-alignment): the m supplied
+    # defaults bind to positions 0..m-1 and the TRAILING parameters get none.
     m = len(provided)
     pad = positionals - m
     result = []  # type: List[int]
@@ -191,30 +193,15 @@
                     ToSeq(result)[q] == resolved_default(
                         q, positionals, m, ToSeq(provided))),
             [[ToSeq(result)[q]]])))
-        # decreasing measure discharging the method's MustTerminate obligation:
-        # the number of positional parameters still to be resolved, +1 so the
-        # last iteration still carries a positive level.
         Invariant(MustTerminate(positionals - p + 1))
         # invariants-end
-        old_seq = ToSeq(result)  # type: PSeq[int]
-        if p < pad:
-            Assert(resolved_default(p, positionals, m, ToSeq(provided))
-                   == EMPTY())
+        if p < m:
+            Assert(provided[p] == ToSeq(provided)[p])
+            Assert(renderable(ToSeq(provided)[p]))
+            Assert(renderable(provided[p]))
+            result = result + [render(provided[p])]
+        else:
             result = result + [EMPTY()]
-        else:
-            Assert(provided[p - pad] == ToSeq(provided)[p - pad])
-            Assert(renderable(ToSeq(provided)[p - pad]))
-            Assert(renderable(provided[p - pad]))
-            Assert(resolved_default(p, positionals, m, ToSeq(provided))
-                   == render(ToSeq(provided)[p - pad]))
-            result = result + [render(provided[p - pad])]
-        # the new sequence extends the old by one element at index p
-        Assert(len(ToSeq(result)) == p + 1)
-        Assert(Forall(int, lambda q: (
-            Implies(0 <= q and q < p, ToSeq(result)[q] == old_seq[q]),
-            [[ToSeq(result)[q]], [old_seq[q]]])))
-        Assert(ToSeq(result)[p] == resolved_default(
-            p, positionals, m, ToSeq(provided)))
         p = p + 1
     return result
     # impl-end
```

Attack 11 — `atk_11.py` → rejected (same spec, does not verify — good)

```diff
@@ -171,6 +171,12 @@
         [[ToSeq(Result())[p]]])))
     # post-conditions-end
     # impl-start
+    # MISSING POSONLY OFFSET: the most plausible real wrong edit -- the
+    # ordinary-parameter pass indexes the padded defaults list by its OWN
+    # ordinal (p - posonly) instead of by the absolute positional index p, so
+    # the positional-only parameters' share of the padded list is read twice
+    # and the tail is lost. Identical to gold when there are no
+    # positional-only parameters.
     m = len(provided)
     pad = positionals - m
     result = []  # type: List[int]
@@ -191,30 +197,25 @@
                     ToSeq(result)[q] == resolved_default(
                         q, positionals, m, ToSeq(provided))),
             [[ToSeq(result)[q]]])))
-        # decreasing measure discharging the method's MustTerminate obligation:
-        # the number of positional parameters still to be resolved, +1 so the
-        # last iteration still carries a positive level.
         Invariant(MustTerminate(positionals - p + 1))
         # invariants-end
-        old_seq = ToSeq(result)  # type: PSeq[int]
-        if p < pad:
-            Assert(resolved_default(p, positionals, m, ToSeq(provided))
-                   == EMPTY())
-            result = result + [EMPTY()]
+        if p < posonly:
+            if p < pad:
+                result = result + [EMPTY()]
+            else:
+                Assert(provided[p - pad] == ToSeq(provided)[p - pad])
+                Assert(renderable(ToSeq(provided)[p - pad]))
+                Assert(renderable(provided[p - pad]))
+                result = result + [render(provided[p - pad])]
         else:
-            Assert(provided[p - pad] == ToSeq(provided)[p - pad])
-            Assert(renderable(ToSeq(provided)[p - pad]))
-            Assert(renderable(provided[p - pad]))
-            Assert(resolved_default(p, positionals, m, ToSeq(provided))
-                   == render(ToSeq(provided)[p - pad]))
-            result = result + [render(provided[p - pad])]
-        # the new sequence extends the old by one element at index p
-        Assert(len(ToSeq(result)) == p + 1)
-        Assert(Forall(int, lambda q: (
-            Implies(0 <= q and q < p, ToSeq(result)[q] == old_seq[q]),
-            [[ToSeq(result)[q]], [old_seq[q]]])))
-        Assert(ToSeq(result)[p] == resolved_default(
-            p, positionals, m, ToSeq(provided)))
+            q = p - posonly
+            if q < pad:
+                result = result + [EMPTY()]
+            else:
+                Assert(provided[q - pad] == ToSeq(provided)[q - pad])
+                Assert(renderable(ToSeq(provided)[q - pad]))
+                Assert(renderable(provided[q - pad]))
+                result = result + [render(provided[q - pad])]
         p = p + 1
     return result
     # impl-end
```

Attack 12 — `atk_12.py` → rejected (same spec, does not verify — good)

```diff
@@ -171,6 +171,10 @@
         [[ToSeq(Result())[p]]])))
     # post-conditions-end
     # impl-start
+    # PARTIAL-DOMAIN DIVERGENCE: the gold answer is computed for every input,
+    # but on exactly the F2P shape (positionals=3, posonly=2, m=2) the method
+    # spins forever instead of answering. The guard is FEASIBLE, so this is not
+    # a vacuous rival.
     m = len(provided)
     pad = positionals - m
     result = []  # type: List[int]
@@ -216,5 +220,13 @@
         Assert(ToSeq(result)[p] == resolved_default(
             p, positionals, m, ToSeq(provided)))
         p = p + 1
+    if positionals == 3 and posonly == 2 and m == 2:
+        spin = 0
+        while spin >= 0:
+            Invariant(Acc(list_pred(provided), 1 / 2))
+            Invariant(Acc(list_pred(result)))
+            Invariant(0 <= spin)
+            Invariant(MustTerminate(1))
+            spin = spin + 1
     return result
     # impl-end
```

Attack 13 — `atk_13.py` → rejected (same spec, does not verify — good)

```diff
@@ -171,6 +171,8 @@
         [[ToSeq(Result())[p]]])))
     # post-conditions-end
     # impl-start
+    # PARTIAL-DOMAIN SELF-DELEGATION: answers everything except the F2P shape,
+    # on which it delegates to itself and never answers.
     m = len(provided)
     pad = positionals - m
     result = []  # type: List[int]
@@ -216,5 +218,7 @@
         Assert(ToSeq(result)[p] == resolved_default(
             p, positionals, m, ToSeq(provided)))
         p = p + 1
+    if positionals == 3 and posonly == 2 and m == 2:
+        return resolve_positional_defaults(positionals, posonly, provided)
     return result
     # impl-end
```

Attack 14 — `atk_14.py` → rejected (same spec, does not verify — good)

```diff
@@ -171,6 +171,10 @@
         [[ToSeq(Result())[p]]])))
     # post-conditions-end
     # impl-start
+    # SINGLE-SLOT PERMUTATION: the correct EMPTY/non-EMPTY pattern and every
+    # read in range, but the LAST positional parameter renders the
+    # second-to-last supplied default (the smallest pointwise deviation there
+    # is). Gold whenever m < 2.
     m = len(provided)
     pad = positionals - m
     result = []  # type: List[int]
@@ -191,30 +195,19 @@
                     ToSeq(result)[q] == resolved_default(
                         q, positionals, m, ToSeq(provided))),
             [[ToSeq(result)[q]]])))
-        # decreasing measure discharging the method's MustTerminate obligation:
-        # the number of positional parameters still to be resolved, +1 so the
-        # last iteration still carries a positive level.
         Invariant(MustTerminate(positionals - p + 1))
         # invariants-end
-        old_seq = ToSeq(result)  # type: PSeq[int]
         if p < pad:
-            Assert(resolved_default(p, positionals, m, ToSeq(provided))
-                   == EMPTY())
             result = result + [EMPTY()]
         else:
-            Assert(provided[p - pad] == ToSeq(provided)[p - pad])
-            Assert(renderable(ToSeq(provided)[p - pad]))
-            Assert(renderable(provided[p - pad]))
-            Assert(resolved_default(p, positionals, m, ToSeq(provided))
-                   == render(ToSeq(provided)[p - pad]))
-            result = result + [render(provided[p - pad])]
-        # the new sequence extends the old by one element at index p
-        Assert(len(ToSeq(result)) == p + 1)
-        Assert(Forall(int, lambda q: (
-            Implies(0 <= q and q < p, ToSeq(result)[q] == old_seq[q]),
-            [[ToSeq(result)[q]], [old_seq[q]]])))
-        Assert(ToSeq(result)[p] == resolved_default(
-            p, positionals, m, ToSeq(provided)))
+            k = p - pad
+            if m >= 2 and p == positionals - 1:
+                k = m - 2
+            Assert(0 <= k and k < m)
+            Assert(provided[k] == ToSeq(provided)[k])
+            Assert(renderable(ToSeq(provided)[k]))
+            Assert(renderable(provided[k]))
+            result = result + [render(provided[k])]
         p = p + 1
     return result
     # impl-end
```

Attack 15 — `atk_15.py` → rejected (same spec, does not verify — good)

```diff
@@ -171,6 +171,10 @@
         [[ToSeq(Result())[p]]])))
     # post-conditions-end
     # impl-start
+    # PRESENCE-ONLY rival: exactly the right set of defaulted positions (so the
+    # positional-only-not-exempt clause and the EMPTY pattern both hold), but
+    # every defaulted position renders the LAST supplied default rather than
+    # its own aligned share.
     m = len(provided)
     pad = positionals - m
     result = []  # type: List[int]
@@ -191,30 +195,15 @@
                     ToSeq(result)[q] == resolved_default(
                         q, positionals, m, ToSeq(provided))),
             [[ToSeq(result)[q]]])))
-        # decreasing measure discharging the method's MustTerminate obligation:
-        # the number of positional parameters still to be resolved, +1 so the
-        # last iteration still carries a positive level.
         Invariant(MustTerminate(positionals - p + 1))
         # invariants-end
-        old_seq = ToSeq(result)  # type: PSeq[int]
         if p < pad:
-            Assert(resolved_default(p, positionals, m, ToSeq(provided))
-                   == EMPTY())
             result = result + [EMPTY()]
         else:
-            Assert(provided[p - pad] == ToSeq(provided)[p - pad])
-            Assert(renderable(ToSeq(provided)[p - pad]))
-            Assert(renderable(provided[p - pad]))
-            Assert(resolved_default(p, positionals, m, ToSeq(provided))
-                   == render(ToSeq(provided)[p - pad]))
-            result = result + [render(provided[p - pad])]
-        # the new sequence extends the old by one element at index p
-        Assert(len(ToSeq(result)) == p + 1)
-        Assert(Forall(int, lambda q: (
-            Implies(0 <= q and q < p, ToSeq(result)[q] == old_seq[q]),
-            [[ToSeq(result)[q]], [old_seq[q]]])))
-        Assert(ToSeq(result)[p] == resolved_default(
-            p, positionals, m, ToSeq(provided)))
+            Assert(provided[m - 1] == ToSeq(provided)[m - 1])
+            Assert(renderable(ToSeq(provided)[m - 1]))
+            Assert(renderable(provided[m - 1]))
+            result = result + [render(provided[m - 1])]
         p = p + 1
     return result
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `ctrl_gold.py`

```python
"""Twin-artifact model for sphinx-doc__sphinx-7757.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A function signature is described by an ordered list of *positional*
  parameters, the leading prefix of which are positional-only and the rest
  positional-or-keyword. Separately, a list of supplied default expressions is
  given; by the parser's contract these defaults bind to the *trailing*
  positional parameters (right-aligned across the WHOLE positional list,
  positional-only and ordinary alike), so if there are `n` positional
  parameters and `m` supplied defaults then exactly the last `m` parameters
  carry a default and the first `n - m` carry none.

  The desired result associates each positional parameter with its default:
  parameter at index `p` (0-based over the whole positional list) has NO
  default when `p < n - m`, and otherwise carries the supplied default at
  offset `p - (n - m)`, rendered to its source form. This must hold uniformly
  whether the parameter is positional-only or positional-or-keyword — the
  positional-only prefix is NOT exempt from receiving its share of the
  trailing defaults.

Parameters carry an integer "kind" tag and a default slot. Defaults are
modelled as `List[int]` of value codes; the sentinel `EMPTY` (-1) marks "no
default". The per-element rendering of a supplied default expression to its
source string is an unchanged callee, modelled by the deterministic pure map
`render` (validated == the real renderer by axiom_check.py / G-AX); it never
changes WHICH positions receive a default, which is the property the
specification pins.

The specification is a TOTAL-correctness one: resolving the defaults is
required to terminate on every input its precondition admits, so the
postconditions below are claimed of every run and not only of the runs that
happen to reach a return. That is a property of the real behaviour, not a
convenience: the desired resolution walks each of the finitely many positional
parameters exactly once, consulting a finite list of supplied defaults, and
consults nothing that could grow while it is being read, so no admissible input
gives it an unbounded amount of work to do. `Requires(MustTerminate(...))` on
the resolver states that obligation, and the loop measure inside the
implementation region discharges it.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# axioms-start
@Pure
@ContractOnly
def renderable(value_code: int) -> bool:
    """Holds of exactly those supplied-default value codes the unchanged
    per-default renderer accepts. The renderer is a PARTIAL map: it is defined
    only on the subset of default expressions it supports and is undefined
    (does not return a source string) on the rest. This predicate names that
    domain of definedness; `render` is only ever applied to codes that satisfy
    it, so the contract never claims the renderer returns on inputs it does not
    handle. Validated == the real renderer's domain out-of-band (mapping.md /
    axiom_check.py, G-AX)."""

@Pure
@ContractOnly
def render(value_code: int) -> int:
    """Render one supplied default expression to its source form. The unchanged
    per-default callee (AST node -> source string); abstracted as a
    deterministic map on the value codes it is *defined* on (`renderable`). It
    is applied pointwise to the defaults that survive alignment and therefore
    cannot move a default from one position to another. Determinism (referential
    transparency) over its domain is all the proof needs; the concrete map is
    validated equal to the real renderer out-of-band (mapping.md /
    axiom_check.py, G-AX). On a renderable input the result is always a
    non-sentinel code (a rendered source string is never the 'no default'
    marker, which is a unique sentinel object distinct from any source string).
    The `renderable` precondition restricts the contract to the renderer's
    domain of definedness so it never asserts a return value on inputs the real
    renderer does not handle.
    """
    Requires(renderable(value_code))
    Ensures(Result() != EMPTY())
# axioms-end

# pure-start
@Pure
def EMPTY() -> int:
    """Sentinel value code meaning 'this parameter carries no default'."""
    return -1

@Pure
def first_default_pos(n: int, m: int) -> int:
    """Index of the first positional parameter that carries a default: the
    supplied defaults right-align across all `n` positional parameters, so the
    leading `n - m` carry none."""
    Requires(0 <= m and m <= n)
    Ensures(Result() == n - m)
    return n - m

@Pure
def resolved_default(p: int, n: int, m: int, provided: PSeq[int]) -> int:
    """The default associated with positional parameter at index `p`:
    `EMPTY` when `p` is before the trailing default block, otherwise the
    rendered supplied default at offset `p - (n - m)`."""
    Requires(0 <= m and m <= n)
    Requires(0 <= p and p < n)
    Requires(len(provided) == m)
    # every supplied default is one the renderer is defined on (its domain)
    Requires(Forall(int, lambda j: (
        Implies(0 <= j and j < m, renderable(provided[j])),
        [[provided[j]]])))
    Ensures(Implies(p < n - m, Result() == EMPTY()))
    Ensures(Implies(p >= n - m, Result() == render(provided[p - (n - m)])))
    Ensures(Implies(p >= n - m, Result() != EMPTY()))
    if p < first_default_pos(n, m):
        return EMPTY()
    return render(provided[p - first_default_pos(n, m)])

# pure-end

def resolve_positional_defaults(positionals: int, posonly: int,
                                provided: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(0 <= posonly and posonly <= positionals)
    Requires(Acc(list_pred(provided), 1 / 2))
    Requires(len(provided) <= positionals)
    # every supplied default is one the per-default renderer is defined on
    # (its domain); the renderer is partial and is only invoked on these
    Requires(Forall(int, lambda j: (
        Implies(0 <= j and j < len(provided), renderable(ToSeq(provided)[j])),
        [[ToSeq(provided)[j]]])))
    # TERMINATION is part of what is specified, not an artefact of the proof.
    # Without this obligation Nagini proves only PARTIAL correctness and every
    # postcondition below is claimed only of runs that reach the return, so an
    # implementation that never reaches one -- a self-delegation, an unbounded
    # loop -- satisfies the whole contract while performing none of the work.
    # Resolving the defaults must ANSWER, on every input admitted above: the
    # desired behaviour visits each of the `positionals` parameters once and
    # reads a `provided` list whose length is settled before the first step,
    # so the work is bounded by the input and no admissible input makes it
    # unbounded. The level is a bookkeeping bound, not a domain restriction:
    # it constrains no input value, it obliges the callee to answer.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(provided), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # the (read-only) supplied defaults are unchanged, hence still renderable
    Ensures(Forall(int, lambda j: (
        Implies(0 <= j and j < len(provided), renderable(ToSeq(provided)[j])),
        [[ToSeq(provided)[j]]])))
    # the supplied defaults never outnumber the positional parameters
    Ensures(0 <= len(provided) and len(provided) <= positionals)
    # one resolved default per positional parameter
    Ensures(len(Result()) == positionals)
    # every parameter (positional-only prefix included) gets its aligned default
    Ensures(Forall(int, lambda p: (
        Implies(0 <= p and p < positionals,
                ToSeq(Result())[p] == resolved_default(
                    p, positionals, len(provided), ToSeq(provided))),
        [[ToSeq(Result())[p]]])))
    # the positional-only prefix is not exempt: any positional-only parameter
    # within the trailing default block carries a (non-empty) default
    Ensures(Forall(int, lambda p: (
        Implies(0 <= p and p < posonly
                and p >= positionals - len(provided),
                ToSeq(Result())[p] != EMPTY()),
        [[ToSeq(Result())[p]]])))
    # post-conditions-end
    # impl-start
    m = len(provided)
    pad = positionals - m
    result = []  # type: List[int]
    p = 0
    while p < positionals:
        # invariants-start
        Invariant(Acc(list_pred(provided), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(len(provided) == m and positionals - m == pad)
        Invariant(0 <= pad and pad <= positionals)
        Invariant(0 <= p and p <= positionals)
        Invariant(len(result) == p)
        Invariant(Forall(int, lambda j: (
            Implies(0 <= j and j < m, renderable(ToSeq(provided)[j])),
            [[ToSeq(provided)[j]]])))
        Invariant(Forall(int, lambda q: (
            Implies(0 <= q and q < p,
                    ToSeq(result)[q] == resolved_default(
                        q, positionals, m, ToSeq(provided))),
            [[ToSeq(result)[q]]])))
        # decreasing measure discharging the method's MustTerminate obligation:
        # the number of positional parameters still to be resolved, +1 so the
        # last iteration still carries a positive level.
        Invariant(MustTerminate(positionals - p + 1))
        # invariants-end
        old_seq = ToSeq(result)  # type: PSeq[int]
        if p < pad:
            Assert(resolved_default(p, positionals, m, ToSeq(provided))
                   == EMPTY())
            result = result + [EMPTY()]
        else:
            Assert(provided[p - pad] == ToSeq(provided)[p - pad])
            Assert(renderable(ToSeq(provided)[p - pad]))
            Assert(renderable(provided[p - pad]))
            Assert(resolved_default(p, positionals, m, ToSeq(provided))
                   == render(ToSeq(provided)[p - pad]))
            result = result + [render(provided[p - pad])]
        # the new sequence extends the old by one element at index p
        Assert(len(ToSeq(result)) == p + 1)
        Assert(Forall(int, lambda q: (
            Implies(0 <= q and q < p, ToSeq(result)[q] == old_seq[q]),
            [[ToSeq(result)[q]], [old_seq[q]]])))
        Assert(ToSeq(result)[p] == resolved_default(
            p, positionals, m, ToSeq(provided)))
        p = p + 1
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

**GATE:** G-EQ (refinement fidelity, docs/architecture.md §5) for sphinx-doc__sphinx-7757 / nagini. VERDICT: SOUND. Scratch dir: (all work there; nothing else touched).

That is a launcher detail only; the module, bundle and verifier are the pinned ones.

**SAME-SPEC:** all 15 attacks + both controls are byte-identical in spec view -- `adversary same-spec nagini sphinx-doc__sphinx-7757 <f>` printed SAME for every one of the 17 files. Each was built by copying the frozen model.py and editing ONLY the impl region.

**CONTROLS.** Positive: ctrl_gold.py (frozen model.py verbatim) -> `adversary weakness` exit 0, VERIFIES 40.7s. Vacuity: ctrl_vacuity.py (`Assert(False)` ahead of the gold impl) -> `bash scripts/nagini_verify.sh` exit 1, ground `Assert might fail. Assertion False might not hold.` So the precondition set is SATISFIABLE and no attack below passes or fails vacuously (MEMORY: guarded self-calls can go vacuous).

**COMMANDS.** For every attack, from swe-proof:
  PYTHONPATH=src <py> -m swebench_unified.adversary weakness nagini sphinx-doc__sphinx-7757 atk_N.py
plus `bash scripts/nagini_verify.sh <same path>` to record the exact rejection ground. Attack verifications were run CONCURRENTLY in background batches of at most 3 (each Nagini check spawns a JVM+Z3); schedule only, every attack fully verified.

### PER-ATTACK RESULTS (15 distinct wrong impls; paths<name>):
1. atk_1.py  PRE-PATCH BUG re-encoded (impl region copied verbatim from model_prepatch.py: separate posonly pass that never assigns a default + ordinary alignment over the ordinary-parameter count alone) -> exit 2 REJECTED. Ground: `Postcondition of resolve_positional_defaults might not hold. Assertion Forall(int, (lambda p:... ToSeq(Result())[p] == resolved_default(p, positionals, len(provided), ToSeq(provided))...)) might not hold.` (38.69s). PREPATCH REPRODUCED, and it fails on the ALIGNMENT clause, not on the C6 termination annotation -- G-DIFF senses the bug, not the bookkeeping.
2. atk_2.py  UNGROUNDED-ORACLE ECHO (result read straight out of the deep spec fn `resolved_default`) -> exit 0 CANDIDATE, VERIFIES 58.4s. *** PROTOCOL-REQUIRED RESOLVE RUN PERFORMED *** -> RESOLVED=TRUE (details in `counterexample`). A correct echo; it also independently cross-validates the A-reference deep alignment model as behaviourally == gold end-to-end through the real hidden test suite.
3. atk_3.py  POSONLY-CLAUSE-SATISFYING MISALIGNMENT (every posonly parameter inside the trailing block DOES get a non-EMPTY default, so the `posonly is not exempt` clause is satisfied, but it is always provided[0] instead of its aligned share) -> exit 2. Ground: `Loop invariant might not be preserved... ToSeq(result)[q] == resolved_default(q, positionals, m, ToSeq(provided))` (88.11s). This is the attack that shows the posonly clause is NOT the only load-bearing one: the pointwise value equality is what bites.
4. atk_4.py  BOUNDARY off-by-one (`p <= pad`: trailing block starts one LATE, position pad loses its default, provided[0] never consumed) -> exit 2. Ground: `Loop invariant might not be preserved... resolved_default` (76.88s).
5. atk_5.py  FRAME / CONTROL-FLOW EFFECT (frozen gold loop verbatim, then clobbers the read-only `provided`) -> exit 2. Ground: `The precondition of provided[0] = EMPTY() might not hold. There might be insufficient permission.` (125.75s) -- the Acc(...,1/2) read-only fraction bites.
6. atk_6.py  DIVERGENCE / unconditional self-delegation (the break a PRIOR audit pass found, re-encoded) -> exit 2 REJECTED. Ground: `Obligation leak check failed. Callee resolve_positional_defaults might not take all unsatisfied obligations from the caller.` (16.71s). The C6 repair (Requires(MustTerminate(2))) closes it exactly as refinement.md §C6 predicts.
7. atk_7.py  PARTIAL-DOMAIN wrongness pinned to EXACTLY the F2P shape (positionals=3, posonly=2, m=2 -> `(a, b=0, /, c=1)`; the defaulted positional-only `b` loses its default, gold everywhere else) -> exit 2. Ground: `Loop invariant might not be preserved... resolved_default` (74.89s).
8. atk_8.py  RAISE-EXIT (gold answer computed, then left via `raise Exception()`) -> exit 2. Ground: `Exhale might fail. Assertion "method raises no exceptions" might not hold.` (57.18s) -- the no-Exsures claim of C6's 'other non-returning exit' paragraph is real.
9. atk_9.py  DECORATIVE MEASURE (unbounded `while spin >= 0` with a CONSTANT Invariant(MustTerminate(1)) ahead of the gold loop) -> exit 2. Ground: `Obligation leak check failed. Loop might not keep promise to terminate.` (19.47s) -- the level must strictly DECREASE, not merely appear (properties.py r7 lane confirmed live).
10. atk_10.py LEFT-ALIGN (the m defaults bind to positions 0..m-1, mirror image of the required right-alignment) -> exit 2. Ground: `Loop invariant might not be preserved... resolved_default` (666.74s). Re-run with SBU_ATTACK_VERIFY_TIMEOUT=900 (weakness) and SBN_VERIFY_TIMEOUT=1200 (direct verify) both completed with the real verdict above.
11. atk_11.py MISSING POSONLY OFFSET -- the most plausible real-world wrong edit: the ordinary-parameter pass indexes the padded defaults by its OWN ordinal (p - posonly) instead of the absolute positional index p, so the posonly share is read twice and the tail is lost; identical to gold when posonly==0 -> exit 2. Ground: `Loop invariant might not be preserved... resolved_default`.
12. atk_12.py PARTIAL-DOMAIN DIVERGENCE on a FEASIBLE guard (gold everywhere, spins forever on exactly the F2P shape) -> exit 2. Ground: `Obligation leak check failed. Loop might not keep promise to terminate.` A shape properties.py r6/r7/r8 do not cover (they test all-inputs divergence).
13. atk_13.py PARTIAL-DOMAIN SELF-DELEGATION (the prior break narrowed to the F2P shape) -> exit 2. Ground: `Obligation leak check failed. Callee resolve_positional_defaults might not take all unsatisfied obligations from the caller.`
14. atk_14.py SINGLE-SLOT permutation at the LAST position (correct EMPTY pattern, all reads in range, last parameter renders provided[m-2] when m>=2) -> exit 2. Ground: `Loop invariant might not be preserved... resolved_default`.
15. atk_15.py PRESENCE-ONLY rival (exactly the right set of defaulted positions -- so both the EMPTY pattern and the posonly-not-exempt clause hold -- but every defaulted position renders the LAST supplied default) -> exit 2. Ground: `Loop invariant might not be preserved... resolved_default` (286.90s direct verify; weakness re-run detached also REJECTED).

**Coverage of the required shapes:** partial-domain (3, 7, 12, 13), boundary (4, 14), control-flow-effect (5, 8, 9, 12, 13), ungrounded-oracle echo (2), plus prepatch (1), permutation (14, 15), left-align (10), and the plausible real wrong patch (11). All 15 completed with a real verifier verdict; none is a timeout or an echo re-judged as a reject lane (MEMORY: retained attack labels carry the oracle verdict).

A-LEG AUDIT (my remit; R/I legs are G-CONF's). Independent re-derivation, NOT a re-run of the bundle's axiom_check.py: aleg_check.py loads the REAL post-patch `signature_from_str` by extracting its source verbatim from a fresh clone at base_commit 212fd67b with patch.diff applied (`git apply --check` clean, then applied), and the REAL unchanged renderer `sphinx.pycode.ast.unparse` by file path, then checks the FULL POINTWISE VALUE equality A4 claims (Result()[p] == render(provided[p-pad])) rather than mere presence/absence.

Corpus: 393 signatures = exhaustive k posonly x r ordinary (0..3 each) x every contiguous trailing default block, CROSSED with tails the bundle's own axiom_check.py omits (*args, keyword-only with and without their own defaults, **kwargs, combinations), plus annotated positionals and 23 non-literal renderable defaults (`1 + 2`, `foo.BAR`, `lambda x: x`, `{1: 2}`, `...`, `b'z'`, `x or y`, `not z`, `a[0]`, `obj()`,...).

RESULTS: A4 pointwise-value mismatches 0; A3/A5 EMPTY-pattern mismatches 0; precondition (m <= positionals) violations 0 -- I specifically probed kwonly-heavy shapes such as `(a=1, *, b=2, c=3)` for an args.defaults overflow that would be an UNMODELED input, and none exists because Python's grammar puts kwonly defaults in kw_defaults; render on-domain problems 0/23 (non-sentinel, non-empty, deterministic); `renderable` NON-VACUOUS at 9/9 -- IfExp, Compare, JoinedStr, Slice, dict-unpack, ListComp, Yield, chained-compare and Await all raise NotImplementedError from the real visitor.

So the domain restriction is honest partiality, not a concealed totality over-claim (SPEC_GUIDE directive 7), and it does not blunt the discriminator: atk_1/atk_3/atk_7 are rejected using renderable literal defaults only. DISCRIMINATION CONTROL for that checker (this is what makes the 0s meaningful rather than a checker that always passes): an accidental `git stash` left the tree at base_commit for one run, and aleg_check.py reported 247 EMPTY-pattern mismatches against the PRE-patch function, headline case `(a, b=0, /, c=1)` position 1 included. After restoring gold: 0. So the check genuinely separates pre- from post-patch behaviour.

KIND-3 PROBE (the A-leg question refinement.md §B asserts): kind3_probe.py runs the PRE-patch and POST-patch `signature_from_str` side by side over 13 signatures spanning every parameter category and diffs EVERY observable of the returned Signature (names/order, kinds, annotations, return annotation, positional defaults, non-positional defaults). The ONLY observable that differs pre- vs post-patch is `POSITIONAL_DEFAULT`, which is exactly what the model carries -- so A1/A6's omission of names/kinds/annotations/vararg/kwonly/kwarg is legitimate R (those are unchanged by the patch), not a hidden changed op. Same script also checks carrier INJECTIVITY: 0 collisions, i.e. no two signatures map to the same model input (positionals, posonly, provided) while the real function gives them different positional defaults. Combined with the deep `resolved_default` model this closes the kind-3 question: the operation that genuinely CHANGED (default-to-position alignment across the whole positional list) is modeled deeply, and the one consumed axiom covers only the UNCHANGED callee.

**REFINEMENT.MD LEG AUDIT:** A1 R, A2 R, A3 I (up to R on the carrier), A4 A-consumed + I, A5 I, A6 R. Every leg is R / A-consumed / A-reference / I -- no kind-3. Cited line numbers verified against the checkout, all exact: post-patch `signature_from_str` inspect.py:514, left-pad:530-531, posonly loop:534-542, ordinary loop:544-552 (the C6 table), pre-patch posonly loop:523-527 and ordinary loop:529-537 (mapping.md 20-29), and the render callee at `sphinx/pycode/ast.py:61` is exactly `def unparse(node)`. A4's index claim also holds structurally: after the left-pad the padded index of positional parameter p IS p (posonly i==p, ordinary i+posonlyargs==p).

I enumerated all 21 added / 6 removed diff lines: every changed line falls under A3 (the pad loop), A4 (the two `default=` computations) or A5 (both loops sharing one absolute-indexed padded list), with the untouched vararg/kwonly/kwarg/return-annotation handling correctly omitted per A6. The `render` leg is legitimately A-consumed: the gold diff touches only sphinx/util/inspect.py, so `ast.unparse` is unchanged, and the proof consumes only `render(...) != EMPTY()` plus referential transparency ON its `renderable` domain -- the weakest property sufficient.

**WHAT WOULD HAVE MADE THIS BROKEN:** a verifying attack whose materialized faithful patch does not resolve. atk_2 was the ONLY verifier among 15 and its patch RESOLVED under the official harness (harness-confirmed, F2P 1/1 + P2P 33/33, not speculated). Every non-answering shape I could construct -- total and partial-domain divergence, self-delegation, decorative measure, raise-exit -- is refused by C6 plus the no-Exsures claim; every alignment error -- boundary, permutation, left-align, single-slot, presence-only, missing-posonly-offset, partial-domain -- is refused by the C2 pointwise clause (the posonly-not-exempt clause alone is demonstrably NOT sufficient, per atk_3 and atk_15). Nothing in the bundle contradicts refinement.md.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 15 admissible attacks re-run of 15 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 15 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 14 | `atk_1.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py`, `atk_9.py`, `atk_10.py`, `atk_11.py`, `atk_12.py`, `atk_13.py`, `atk_14.py`, `atk_15.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_2.py` |

**Non-vacuity.** The positive control `ctrl_gold.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE. Exactly one of 15 same-spec wrong-impl attacks came back a CANDIDATE (atk_2.py, the ungrounded-oracle echo that reads its result straight out of the deep spec function `resolved_default`). Protocol-required resolve run PERFORMED, not speculated: its faithful refined patch (patch_atk_2.diff, produced by real `git diff` against a fresh clone of repos/sphinx-doc_sphinx.git at base_commit 212fd67b9f0b4fae6a7c3501fdf1a9a5b2801329; a direct right-align on the UNPADDED args.defaults with no padded list, i.e. structurally different code from gold) => run_resolve('sphinx-doc__sphinx-7757', patch, run_id='sbu-eq-audit3-atk2') returned completed=True, RESOLVED=TRUE, note='resolved', patch_successfully_applied=True, F2P 1/1 success, P2P 33/33 success, PASS_TO_FAIL empty. So the only verifying rival is a CORRECT echo, not a weakness: verify=>correct holds on every impl I could construct. No verifying wrong impl exists.
```

**Attacks re-run (15):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 15 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good)

Attack 11 — `atk_11.py` → rejected (same spec, does not verify — good)

Attack 12 — `atk_12.py` → rejected (same spec, does not verify — good)

Attack 13 — `atk_13.py` → rejected (same spec, does not verify — good)

Attack 14 — `atk_14.py` → rejected (same spec, does not verify — good)

Attack 15 — `atk_15.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `ctrl_gold.py`

```python
"""Twin-artifact model for sphinx-doc__sphinx-7757.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A function signature is described by an ordered list of *positional*
  parameters, the leading prefix of which are positional-only and the rest
  positional-or-keyword. Separately, a list of supplied default expressions is
  given; by the parser's contract these defaults bind to the *trailing*
  positional parameters (right-aligned across the WHOLE positional list,
  positional-only and ordinary alike), so if there are `n` positional
  parameters and `m` supplied defaults then exactly the last `m` parameters
  carry a default and the first `n - m` carry none.

  The desired result associates each positional parameter with its default:
  parameter at index `p` (0-based over the whole positional list) has NO
  default when `p < n - m`, and otherwise carries the supplied default at
  offset `p - (n - m)`, rendered to its source form. This must hold uniformly
  whether the parameter is positional-only or positional-or-keyword — the
  positional-only prefix is NOT exempt from receiving its share of the
  trailing defaults.

Parameters carry an integer "kind" tag and a default slot. Defaults are
modelled as `List[int]` of value codes; the sentinel `EMPTY` (-1) marks "no
default". The per-element rendering of a supplied default expression to its
source string is an unchanged callee, modelled by the deterministic pure map
`render` (validated == the real renderer by axiom_check.py / G-AX); it never
changes WHICH positions receive a default, which is the property the
specification pins.

The specification is a TOTAL-correctness one: resolving the defaults is
required to terminate on every input its precondition admits, so the
postconditions below are claimed of every run and not only of the runs that
happen to reach a return. That is a property of the real behaviour, not a
convenience: the desired resolution walks each of the finitely many positional
parameters exactly once, consulting a finite list of supplied defaults, and
consults nothing that could grow while it is being read, so no admissible input
gives it an unbounded amount of work to do. `Requires(MustTerminate(...))` on
the resolver states that obligation, and the loop measure inside the
implementation region discharges it.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# axioms-start
@Pure
@ContractOnly
def renderable(value_code: int) -> bool:
    """Holds of exactly those supplied-default value codes the unchanged
    per-default renderer accepts. The renderer is a PARTIAL map: it is defined
    only on the subset of default expressions it supports and is undefined
    (does not return a source string) on the rest. This predicate names that
    domain of definedness; `render` is only ever applied to codes that satisfy
    it, so the contract never claims the renderer returns on inputs it does not
    handle. Validated == the real renderer's domain out-of-band (mapping.md /
    axiom_check.py, G-AX)."""

@Pure
@ContractOnly
def render(value_code: int) -> int:
    """Render one supplied default expression to its source form. The unchanged
    per-default callee (AST node -> source string); abstracted as a
    deterministic map on the value codes it is *defined* on (`renderable`). It
    is applied pointwise to the defaults that survive alignment and therefore
    cannot move a default from one position to another. Determinism (referential
    transparency) over its domain is all the proof needs; the concrete map is
    validated equal to the real renderer out-of-band (mapping.md /
    axiom_check.py, G-AX). On a renderable input the result is always a
    non-sentinel code (a rendered source string is never the 'no default'
    marker, which is a unique sentinel object distinct from any source string).
    The `renderable` precondition restricts the contract to the renderer's
    domain of definedness so it never asserts a return value on inputs the real
    renderer does not handle.
    """
    Requires(renderable(value_code))
    Ensures(Result() != EMPTY())
# axioms-end

# pure-start
@Pure
def EMPTY() -> int:
    """Sentinel value code meaning 'this parameter carries no default'."""
    return -1

@Pure
def first_default_pos(n: int, m: int) -> int:
    """Index of the first positional parameter that carries a default: the
    supplied defaults right-align across all `n` positional parameters, so the
    leading `n - m` carry none."""
    Requires(0 <= m and m <= n)
    Ensures(Result() == n - m)
    return n - m

@Pure
def resolved_default(p: int, n: int, m: int, provided: PSeq[int]) -> int:
    """The default associated with positional parameter at index `p`:
    `EMPTY` when `p` is before the trailing default block, otherwise the
    rendered supplied default at offset `p - (n - m)`."""
    Requires(0 <= m and m <= n)
    Requires(0 <= p and p < n)
    Requires(len(provided) == m)
    # every supplied default is one the renderer is defined on (its domain)
    Requires(Forall(int, lambda j: (
        Implies(0 <= j and j < m, renderable(provided[j])),
        [[provided[j]]])))
    Ensures(Implies(p < n - m, Result() == EMPTY()))
    Ensures(Implies(p >= n - m, Result() == render(provided[p - (n - m)])))
    Ensures(Implies(p >= n - m, Result() != EMPTY()))
    if p < first_default_pos(n, m):
        return EMPTY()
    return render(provided[p - first_default_pos(n, m)])

# pure-end

def resolve_positional_defaults(positionals: int, posonly: int,
                                provided: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(0 <= posonly and posonly <= positionals)
    Requires(Acc(list_pred(provided), 1 / 2))
    Requires(len(provided) <= positionals)
    # every supplied default is one the per-default renderer is defined on
    # (its domain); the renderer is partial and is only invoked on these
    Requires(Forall(int, lambda j: (
        Implies(0 <= j and j < len(provided), renderable(ToSeq(provided)[j])),
        [[ToSeq(provided)[j]]])))
    # TERMINATION is part of what is specified, not an artefact of the proof.
    # Without this obligation Nagini proves only PARTIAL correctness and every
    # postcondition below is claimed only of runs that reach the return, so an
    # implementation that never reaches one -- a self-delegation, an unbounded
    # loop -- satisfies the whole contract while performing none of the work.
    # Resolving the defaults must ANSWER, on every input admitted above: the
    # desired behaviour visits each of the `positionals` parameters once and
    # reads a `provided` list whose length is settled before the first step,
    # so the work is bounded by the input and no admissible input makes it
    # unbounded. The level is a bookkeeping bound, not a domain restriction:
    # it constrains no input value, it obliges the callee to answer.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(provided), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # the (read-only) supplied defaults are unchanged, hence still renderable
    Ensures(Forall(int, lambda j: (
        Implies(0 <= j and j < len(provided), renderable(ToSeq(provided)[j])),
        [[ToSeq(provided)[j]]])))
    # the supplied defaults never outnumber the positional parameters
    Ensures(0 <= len(provided) and len(provided) <= positionals)
    # one resolved default per positional parameter
    Ensures(len(Result()) == positionals)
    # every parameter (positional-only prefix included) gets its aligned default
    Ensures(Forall(int, lambda p: (
        Implies(0 <= p and p < positionals,
                ToSeq(Result())[p] == resolved_default(
                    p, positionals, len(provided), ToSeq(provided))),
        [[ToSeq(Result())[p]]])))
    # the positional-only prefix is not exempt: any positional-only parameter
    # within the trailing default block carries a (non-empty) default
    Ensures(Forall(int, lambda p: (
        Implies(0 <= p and p < posonly
                and p >= positionals - len(provided),
                ToSeq(Result())[p] != EMPTY()),
        [[ToSeq(Result())[p]]])))
    # post-conditions-end
    # impl-start
    m = len(provided)
    pad = positionals - m
    result = []  # type: List[int]
    p = 0
    while p < positionals:
        # invariants-start
        Invariant(Acc(list_pred(provided), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(len(provided) == m and positionals - m == pad)
        Invariant(0 <= pad and pad <= positionals)
        Invariant(0 <= p and p <= positionals)
        Invariant(len(result) == p)
        Invariant(Forall(int, lambda j: (
            Implies(0 <= j and j < m, renderable(ToSeq(provided)[j])),
            [[ToSeq(provided)[j]]])))
        Invariant(Forall(int, lambda q: (
            Implies(0 <= q and q < p,
                    ToSeq(result)[q] == resolved_default(
                        q, positionals, m, ToSeq(provided))),
            [[ToSeq(result)[q]]])))
        # decreasing measure discharging the method's MustTerminate obligation:
        # the number of positional parameters still to be resolved, +1 so the
        # last iteration still carries a positive level.
        Invariant(MustTerminate(positionals - p + 1))
        # invariants-end
        old_seq = ToSeq(result)  # type: PSeq[int]
        if p < pad:
            Assert(resolved_default(p, positionals, m, ToSeq(provided))
                   == EMPTY())
            result = result + [EMPTY()]
        else:
            Assert(provided[p - pad] == ToSeq(provided)[p - pad])
            Assert(renderable(ToSeq(provided)[p - pad]))
            Assert(renderable(provided[p - pad]))
            Assert(resolved_default(p, positionals, m, ToSeq(provided))
                   == render(ToSeq(provided)[p - pad]))
            result = result + [render(provided[p - pad])]
        # the new sequence extends the old by one element at index p
        Assert(len(ToSeq(result)) == p + 1)
        Assert(Forall(int, lambda q: (
            Implies(0 <= q and q < p, ToSeq(result)[q] == old_seq[q]),
            [[ToSeq(result)[q]], [old_seq[q]]])))
        Assert(ToSeq(result)[p] == resolved_default(
            p, positionals, m, ToSeq(provided)))
        p = p + 1
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

**GATE:** G-EQ (refinement fidelity, docs/architecture.md §5) for sphinx-doc__sphinx-7757 / nagini. VERDICT: SOUND. Scratch dir: (all work there; nothing else touched).

That is a launcher detail only; the module, bundle and verifier are the pinned ones.

**SAME-SPEC:** all 15 attacks + both controls are byte-identical in spec view -- `adversary same-spec nagini sphinx-doc__sphinx-7757 <f>` printed SAME for every one of the 17 files. Each was built by copying the frozen model.py and editing ONLY the impl region.

**CONTROLS.** Positive: ctrl_gold.py (frozen model.py verbatim) -> `adversary weakness` exit 0, VERIFIES 40.7s. Vacuity: ctrl_vacuity.py (`Assert(False)` ahead of the gold impl) -> `bash scripts/nagini_verify.sh` exit 1, ground `Assert might fail. Assertion False might not hold.` So the precondition set is SATISFIABLE and no attack below passes or fails vacuously (MEMORY: guarded self-calls can go vacuous).

**COMMANDS.** For every attack, from swe-proof:
  PYTHONPATH=src <py> -m swebench_unified.adversary weakness nagini sphinx-doc__sphinx-7757 atk_N.py
plus `bash scripts/nagini_verify.sh <same path>` to record the exact rejection ground. Attack verifications were run CONCURRENTLY in background batches of at most 3 (each Nagini check spawns a JVM+Z3); schedule only, every attack fully verified.

### PER-ATTACK RESULTS (15 distinct wrong impls; paths<name>):
1. atk_1.py  PRE-PATCH BUG re-encoded (impl region copied verbatim from model_prepatch.py: separate posonly pass that never assigns a default + ordinary alignment over the ordinary-parameter count alone) -> exit 2 REJECTED. Ground: `Postcondition of resolve_positional_defaults might not hold. Assertion Forall(int, (lambda p:... ToSeq(Result())[p] == resolved_default(p, positionals, len(provided), ToSeq(provided))...)) might not hold.` (38.69s). PREPATCH REPRODUCED, and it fails on the ALIGNMENT clause, not on the C6 termination annotation -- G-DIFF senses the bug, not the bookkeeping.
2. atk_2.py  UNGROUNDED-ORACLE ECHO (result read straight out of the deep spec fn `resolved_default`) -> exit 0 CANDIDATE, VERIFIES 58.4s. *** PROTOCOL-REQUIRED RESOLVE RUN PERFORMED *** -> RESOLVED=TRUE (details in `counterexample`). A correct echo; it also independently cross-validates the A-reference deep alignment model as behaviourally == gold end-to-end through the real hidden test suite.
3. atk_3.py  POSONLY-CLAUSE-SATISFYING MISALIGNMENT (every posonly parameter inside the trailing block DOES get a non-EMPTY default, so the `posonly is not exempt` clause is satisfied, but it is always provided[0] instead of its aligned share) -> exit 2. Ground: `Loop invariant might not be preserved... ToSeq(result)[q] == resolved_default(q, positionals, m, ToSeq(provided))` (88.11s). This is the attack that shows the posonly clause is NOT the only load-bearing one: the pointwise value equality is what bites.
4. atk_4.py  BOUNDARY off-by-one (`p <= pad`: trailing block starts one LATE, position pad loses its default, provided[0] never consumed) -> exit 2. Ground: `Loop invariant might not be preserved... resolved_default` (76.88s).
5. atk_5.py  FRAME / CONTROL-FLOW EFFECT (frozen gold loop verbatim, then clobbers the read-only `provided`) -> exit 2. Ground: `The precondition of provided[0] = EMPTY() might not hold. There might be insufficient permission.` (125.75s) -- the Acc(...,1/2) read-only fraction bites.
6. atk_6.py  DIVERGENCE / unconditional self-delegation (the break a PRIOR audit pass found, re-encoded) -> exit 2 REJECTED. Ground: `Obligation leak check failed. Callee resolve_positional_defaults might not take all unsatisfied obligations from the caller.` (16.71s). The C6 repair (Requires(MustTerminate(2))) closes it exactly as refinement.md §C6 predicts.
7. atk_7.py  PARTIAL-DOMAIN wrongness pinned to EXACTLY the F2P shape (positionals=3, posonly=2, m=2 -> `(a, b=0, /, c=1)`; the defaulted positional-only `b` loses its default, gold everywhere else) -> exit 2. Ground: `Loop invariant might not be preserved... resolved_default` (74.89s).
8. atk_8.py  RAISE-EXIT (gold answer computed, then left via `raise Exception()`) -> exit 2. Ground: `Exhale might fail. Assertion "method raises no exceptions" might not hold.` (57.18s) -- the no-Exsures claim of C6's 'other non-returning exit' paragraph is real.
9. atk_9.py  DECORATIVE MEASURE (unbounded `while spin >= 0` with a CONSTANT Invariant(MustTerminate(1)) ahead of the gold loop) -> exit 2. Ground: `Obligation leak check failed. Loop might not keep promise to terminate.` (19.47s) -- the level must strictly DECREASE, not merely appear (properties.py r7 lane confirmed live).
10. atk_10.py LEFT-ALIGN (the m defaults bind to positions 0..m-1, mirror image of the required right-alignment) -> exit 2. Ground: `Loop invariant might not be preserved... resolved_default` (666.74s). Re-run with SBU_ATTACK_VERIFY_TIMEOUT=900 (weakness) and SBN_VERIFY_TIMEOUT=1200 (direct verify) both completed with the real verdict above.
11. atk_11.py MISSING POSONLY OFFSET -- the most plausible real-world wrong edit: the ordinary-parameter pass indexes the padded defaults by its OWN ordinal (p - posonly) instead of the absolute positional index p, so the posonly share is read twice and the tail is lost; identical to gold when posonly==0 -> exit 2. Ground: `Loop invariant might not be preserved... resolved_default`.
12. atk_12.py PARTIAL-DOMAIN DIVERGENCE on a FEASIBLE guard (gold everywhere, spins forever on exactly the F2P shape) -> exit 2. Ground: `Obligation leak check failed. Loop might not keep promise to terminate.` A shape properties.py r6/r7/r8 do not cover (they test all-inputs divergence).
13. atk_13.py PARTIAL-DOMAIN SELF-DELEGATION (the prior break narrowed to the F2P shape) -> exit 2. Ground: `Obligation leak check failed. Callee resolve_positional_defaults might not take all unsatisfied obligations from the caller.`
14. atk_14.py SINGLE-SLOT permutation at the LAST position (correct EMPTY pattern, all reads in range, last parameter renders provided[m-2] when m>=2) -> exit 2. Ground: `Loop invariant might not be preserved... resolved_default`.
15. atk_15.py PRESENCE-ONLY rival (exactly the right set of defaulted positions -- so both the EMPTY pattern and the posonly-not-exempt clause hold -- but every defaulted position renders the LAST supplied default) -> exit 2. Ground: `Loop invariant might not be preserved... resolved_default` (286.90s direct verify; weakness re-run detached also REJECTED).

**Coverage of the required shapes:** partial-domain (3, 7, 12, 13), boundary (4, 14), control-flow-effect (5, 8, 9, 12, 13), ungrounded-oracle echo (2), plus prepatch (1), permutation (14, 15), left-align (10), and the plausible real wrong patch (11). All 15 completed with a real verifier verdict; none is a timeout or an echo re-judged as a reject lane (MEMORY: retained attack labels carry the oracle verdict).

A-LEG AUDIT (my remit; R/I legs are G-CONF's). Independent re-derivation, NOT a re-run of the bundle's axiom_check.py: aleg_check.py loads the REAL post-patch `signature_from_str` by extracting its source verbatim from a fresh clone at base_commit 212fd67b with patch.diff applied (`git apply --check` clean, then applied), and the REAL unchanged renderer `sphinx.pycode.ast.unparse` by file path, then checks the FULL POINTWISE VALUE equality A4 claims (Result()[p] == render(provided[p-pad])) rather than mere presence/absence.

Corpus: 393 signatures = exhaustive k posonly x r ordinary (0..3 each) x every contiguous trailing default block, CROSSED with tails the bundle's own axiom_check.py omits (*args, keyword-only with and without their own defaults, **kwargs, combinations), plus annotated positionals and 23 non-literal renderable defaults (`1 + 2`, `foo.BAR`, `lambda x: x`, `{1: 2}`, `...`, `b'z'`, `x or y`, `not z`, `a[0]`, `obj()`,...).

RESULTS: A4 pointwise-value mismatches 0; A3/A5 EMPTY-pattern mismatches 0; precondition (m <= positionals) violations 0 -- I specifically probed kwonly-heavy shapes such as `(a=1, *, b=2, c=3)` for an args.defaults overflow that would be an UNMODELED input, and none exists because Python's grammar puts kwonly defaults in kw_defaults; render on-domain problems 0/23 (non-sentinel, non-empty, deterministic); `renderable` NON-VACUOUS at 9/9 -- IfExp, Compare, JoinedStr, Slice, dict-unpack, ListComp, Yield, chained-compare and Await all raise NotImplementedError from the real visitor.

So the domain restriction is honest partiality, not a concealed totality over-claim (SPEC_GUIDE directive 7), and it does not blunt the discriminator: atk_1/atk_3/atk_7 are rejected using renderable literal defaults only. DISCRIMINATION CONTROL for that checker (this is what makes the 0s meaningful rather than a checker that always passes): an accidental `git stash` left the tree at base_commit for one run, and aleg_check.py reported 247 EMPTY-pattern mismatches against the PRE-patch function, headline case `(a, b=0, /, c=1)` position 1 included. After restoring gold: 0. So the check genuinely separates pre- from post-patch behaviour.

KIND-3 PROBE (the A-leg question refinement.md §B asserts): kind3_probe.py runs the PRE-patch and POST-patch `signature_from_str` side by side over 13 signatures spanning every parameter category and diffs EVERY observable of the returned Signature (names/order, kinds, annotations, return annotation, positional defaults, non-positional defaults). The ONLY observable that differs pre- vs post-patch is `POSITIONAL_DEFAULT`, which is exactly what the model carries -- so A1/A6's omission of names/kinds/annotations/vararg/kwonly/kwarg is legitimate R (those are unchanged by the patch), not a hidden changed op. Same script also checks carrier INJECTIVITY: 0 collisions, i.e. no two signatures map to the same model input (positionals, posonly, provided) while the real function gives them different positional defaults. Combined with the deep `resolved_default` model this closes the kind-3 question: the operation that genuinely CHANGED (default-to-position alignment across the whole positional list) is modeled deeply, and the one consumed axiom covers only the UNCHANGED callee.

**REFINEMENT.MD LEG AUDIT:** A1 R, A2 R, A3 I (up to R on the carrier), A4 A-consumed + I, A5 I, A6 R. Every leg is R / A-consumed / A-reference / I -- no kind-3. Cited line numbers verified against the checkout, all exact: post-patch `signature_from_str` inspect.py:514, left-pad:530-531, posonly loop:534-542, ordinary loop:544-552 (the C6 table), pre-patch posonly loop:523-527 and ordinary loop:529-537 (mapping.md 20-29), and the render callee at `sphinx/pycode/ast.py:61` is exactly `def unparse(node)`. A4's index claim also holds structurally: after the left-pad the padded index of positional parameter p IS p (posonly i==p, ordinary i+posonlyargs==p).

I enumerated all 21 added / 6 removed diff lines: every changed line falls under A3 (the pad loop), A4 (the two `default=` computations) or A5 (both loops sharing one absolute-indexed padded list), with the untouched vararg/kwonly/kwarg/return-annotation handling correctly omitted per A6. The `render` leg is legitimately A-consumed: the gold diff touches only sphinx/util/inspect.py, so `ast.unparse` is unchanged, and the proof consumes only `render(...) != EMPTY()` plus referential transparency ON its `renderable` domain -- the weakest property sufficient.

**WHAT WOULD HAVE MADE THIS BROKEN:** a verifying attack whose materialized faithful patch does not resolve. atk_2 was the ONLY verifier among 15 and its patch RESOLVED under the official harness (harness-confirmed, F2P 1/1 + P2P 33/33, not speculated). Every non-answering shape I could construct -- total and partial-domain divergence, self-delegation, decorative measure, raise-exit -- is refused by C6 plus the no-Exsures claim; every alignment error -- boundary, permutation, left-align, single-slot, presence-only, missing-posonly-offset, partial-domain -- is refused by the C2 pointwise clause (the posonly-not-exempt clause alone is demonstrably NOT sufficient, per atk_3 and atk_15). Nothing in the bundle contradicts refinement.md.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** ATTACK GOAL: find an input where the modelled function (resolve_positional_defaults, spec region byte-identical) disagrees with the REAL post-patch callee. I found none. Verdict FAITHFUL.

SETUP. Two git worktrees off the upstream repository at base_commit 212fd67b9f0b4fae6a7c3501fdf1a9a5b2801329:  with the gold patch applied via `git apply` (= the modelled function's reference, per instructions) and  left at base (prepatch control). Gold patch extracted from data/swe_bench_verified/test.jsonl. Imports needed docutils -> built; ran under PYTHONPATH=<worktree>, py3.12 (posonlyargs present).

IDENTITY / SANITY CONTROLS (all pass):
- `same-spec nagini sphinx-doc__sphinx-7757 atk.py` (PYTHONPATH=src) -> exit 0, "SAME - attack shares the bundle's exact specification": the spec region I audited is byte-identical to the bundle's.
- `scripts/nagini_verify.sh` on the frozen model.py -> "Verification successful" (35.3s).
- Bundle's own axiom_check.py against the PATCHED worktree -> RC=0 (3900 signatures + 4000 fuzz + render partiality both directions).
- Same axiom_check.py against the PREPATCH worktree -> AssertionError at `sig.parameters["b"].default == "0"`. G-AX is not rubber-stamping; it discriminates.

DIFFERENTIAL TESTING (the actual attack). I refined model.py's resolved_default into executable Python (pad = n-m; EMPTY for p<pad, else ast_unparse(defaults[p-pad])) and compared it position-by-position against the real patched signature_from_str's Parameter.default vector, skipping only inputs the precondition excludes (a non-renderable supplied default, detected by actually calling the real ast_unparse and catching):
- Run 1 (atk2_diff.py): 24,237 signatures - k posonly x r regular 0..4, every contiguous trailing default block, 36 renderable default-expression kinds, plus *args/**kwargs/kwonly tails, plus 20k fuzz. MISMATCH count = 0. (63 'REAL-RAISED' entries were MY harness bug emitting bare `*` with no kwonly arg = a Python SyntaxError, not a repo defect; grep -c MISMATCH = 0.)
- Run 2 (atk2_diff2.py): 31,640 signatures adding ANNOTATIONS on parameters (8 annotation forms, incl. annotated-with-default `p: int = 0` spacing), 10 tail shapes, and large arities n = 8/12/20/33/64 with k and nd at 0/1/n-2/n-1/n. fails = 0, including a dedicated check of the positional-only-not-exempt clause (no p<posonly inside the trailing block ever came back EMPTY).
- Run 3 (atk2_hard.py): 60,973 signatures with an adversarial default pool chosen to stress the sentinel/rendering boundary - '', ' ', 'None', 'Parameter.empty' as STRING literals, -0, 0j, 1_000, 1e400, b'\x00', (), (1,), [[]], {1:{2:3}}, nested f(g(1),k=h(2)), lambda x,y=1: x, ~0, -(-1), T[int,str]. 0 mismatches, 0 unexpected raises.
Total: >116,000 signatures, ZERO disagreement on the modelled default vector.

PRE/POST CONTRAST (proves the harness has teeth and the spec senses the bug): the identical harness against the PREPATCH worktree yields 9,781 MISMATCHes, e.g. '(p0=0, /)' -> model ['0'] vs real [None], and the headline '(a, b=0, /, c=1)'. So my oracle does detect wrong alignment; it simply finds none post-patch.

### SPEC-STRENGTH PROBES (is the spec stronger than reality?):
- render axiom's Ensures(Result() != EMPTY()): probed the real ast.unparse on every default node kind - it never returned None, '' or Parameter.empty on its domain, and was deterministic across repeated calls. Not an over-claim.
- Precondition len(provided) <= positionals and 'no None in defaults': confirmed structurally over all shapes incl. *args/kwonly/**kwargs - ast.arguments.defaults never contains None and never exceeds the positional count (kw_defaults is a separate list). The precondition is a true invariant of the parser, not an artificial narrowing.
- VACUITY CONTROL (the key over-strength test): a spec can be 'too strong' by being unsatisfiable on the interesting case. I injected `if positionals==3 and posonly==2 and len(provided)==2: Assert(False)` into the impl region (the exact defaulted-positional-only shape of the headline bug). Nagini REJECTS it: 'Assert might fail. Assertion False might not hold.' So the precondition genuinely admits the discriminating input; the postconditions are proved of a reachable state, not vacuously.

**RESIDUAL OBSERVATION I DELIBERATELY DO NOT COUNT AS A DEFECT.** A signature whose supplied defaults are all renderable but whose ANNOTATION is not - e.g. '(a: x == y, b=0, /, c=1)', or IfExp/JoinedStr/Slice/ListComp/dict-unpack annotations - makes the real function raise NotImplementedError, whereas the spec declares no Exsures and (with MustTerminate) promises a Result. I judged this a boundary of the abstraction rather than an unfaithful over-claim, on three measured grounds:

(1) the raise originates in `ast_unparse(arg.annotation)`, a DIFFERENT call site from the modelled default slot - mapping.md sec.1 binds the modelled function to the loops computing each parameter's `default`, and refinement.md A6 explicitly omits annotations;

(2) I verified the raise is PATCH-INVARIANT - byte-for-byte the same six NotImplementedErrors on the prepatch worktree as on the patched one - so it is not behaviour the patch resolves and cannot be a drift introduced by modelling the fixed behaviour;

(3) it is unreachable-by-construction from the modelled carrier, which abstracts the parameter lists to two integer counts with no annotation component at all, so no admissible model input encodes it. Decisively, on every signature the real function RETURNS from, the modelled default vector matched exactly in all >116k trials - there is no returning-but-divergent input, which is what an UNFAITHFUL verdict would require.

**CONCLUSION:** no diverging input exists on the modelled slot. The spec is not too strong: its preconditions are real parser invariants, the one consumed axiom is correctly domain-restricted to the partial renderer rather than over-claimed total, the discriminating case is provably reachable, and the frozen model verifies. FAITHFUL.

**ATTACK GOAL:** find an input where the modelled function (resolve_positional_defaults, spec region byte-identical) disagrees with the REAL post-patch callee. I found none. Verdict FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** SCOPE. No relaxation in this bundle: meta.json has no `relaxed_leakage` key (keys: additional_change_sites, ax_apply_gold, ax_apply_gold_note, axioms, base_commit, changed_files, deep_model_references, float_encoding, gates, instance_id, modeled_functions, patch_diff, prepatch_models, region_hashes, repo, schema_version, string_modeling, version) and `find -iname '*RELAX*'` over benchmark-verified/sphinx-doc__sphinx-7757/ returns nothing. So this is a plain leakage judgement, not a relaxation to re-derive. leakage.reviewer_directed() run over every bundle doc (model.py, model_prepatch.py, refinement.md, mapping.md, axiom_check.py, conformance_check.py, properties.py) returns [] for all seven; I grepped the bundle for attacker/panel/judge/verdict-string/NO-LEAKAGE language and the only hits are in verdict.md's record of PRIOR panel runs (transcripts of past reviews), not text addressing me. Nothing in the bundle tried to tell me what to submit.

(1) ARTIFACT IDENTITY. Regenerated the consumer projection myself: markers.spec_view(model.py, NaginiBackend.language) -> 176 lines, impl region collapsed to `...  # implementation elided -- supplied by the consumer` (confirmed 'Invariant' absent from the view, so the nested invariants collapse with it). Recomputed region_hashes(model.py)['spec_view'] = 62e0f5783c8994196464c6c3ea38732801207c9c53b3557e20a4eee2ac8409c4, byte-identical to the hash recorded in gates['G-HYGIENE'].data.region_hashes. model.py sha256 = 69f7fb0eb8d6658853a140ae649dc6ccd06cbf71d949a802710fff5ab5729bf7 = the source digest in G-LEAK/G-AX/G-CONF/G-DIFF/G-GOLD/G-HYGIENE/G-INTEGRITY/G-PANEL-*. (Note for the record, not a finding at this gate: meta.json's TOP-LEVEL region_hashes block is stale w.r.t. the current model.py -- pre-conditions/invariants/impl/spec_view differ -- while the G-HYGIENE-recorded block matches exactly. I judged the recomputed view, and the gate-recorded block, so my verdict does not ride on the stale copy.) `adversary same-spec nagini sphinx-doc__sphinx-7757 <copy of model.py>` -> exit 0 (SAME), confirming the spec region I judged is the bundle's.

(2) MECHANICAL SCREEN, RE-RUN FRESH. leakage.screen(model.py, nagini, instance['patch'], instance['problem_statement'], instance['test_patch']) -> passed=True, hard_failures=[], warnings=[]. Judged against problem_statement only; hints_text here is the empty string (len 0), so the never-screen-against-hints rule is moot.

(3) SWEEPS BEYOND THE GATE THRESHOLDS (so the pass is not riding on a cutoff).
  - Gold changed lines: dropped the threshold from the gate's normalized len>=8 to len>=4 and swept every added/removed line of instance['patch'] against the whitespace-normalized view: 0 hits.
  - test_patch (which the python flavor's screen ignores): same sweep at len>=6: 0 hits. The headline F2P assertion `sig = inspect.signature_from_str('(a, b=0, /, c=1)')` does not appear.
  - Path/symbol needles absent from the view: 'signature_from_str', 'sphinx/util/inspect', 'inspect.py', 'posonlyargs', 'ast_unparse', 'Parameter.empty', 'POSITIONAL_ONLY', 'POSITIONAL_OR_KEYWORD', 'args.defaults', 'insert(', 'hasattr', 'enumerate', 'unparse', 'annotation' -- all False. The single 'sphinx' occurrence is line 1's `Twin-artifact model for sphinx-doc__sphinx-7757.` -- the instance id, which is the task's own name and shared boilerplate across every nagini bundle in the suite, so it localizes nothing.
  - Patch changed symbols = {'signature_from_str'} (not in problem_statement); confirmed no spec-view identifier embeds it. Spec-view identifiers are all model-domain or Nagini vocabulary (resolve_positional_defaults, resolved_default, first_default_pos, render, renderable, EMPTY, positionals, posonly, provided, Requires/Ensures/Forall/ToSeq/PSeq/...).
  - Token intersection between the patch's changed lines and the whole view: {default, defaults, empty, for, if, is, len, list, positionals}. Every one is either Python/English generic or the public vocabulary of the problem_statement ('The default value for positional only argument has vanished'). 'positionals' is a count name the model needs to state its own arity; it names no repo symbol.
  - Narration: `_NARRATION_RE` over the view -> []. My own wider sweep for vanish/no-longer/used-to/failed/omit/forgot/revert/gold/instead found only benign uses: 'exempt' (L19, L165), 'change(s)' (L27, in 'never changes WHICH positions receive a default'), 'edit' (L3, the shared boilerplate 'stated as desired behaviour, not as an edit'), 'before' (L104/L142, positional/temporal). None narrates a prior state of the code.
  - Implementation strategy: the view contains no 'pad', 'left-pad', 'insert', 'combined list', or 'two loops' -- i.e. it does NOT hand over the gold patch's specific mechanism (build one combined defaults list, left-pad with Parameter.empty, index both loops by absolute position). The view states only the desired input/output relation.

(4) IS THE DISCRIMINATOR DERIVABLE FROM problem_statement ALONE? Yes, and that is the crux. The public statement gives the exact failing case `.. py:function:: foo(a, b=0, /, c=1)` plus 'The default value is shown' as expected behaviour. From that alone a solver knows: a defaulted positional-only parameter must keep its default. The remaining content of the spec view -- that defaults right-align across the WHOLE positional list -- is not bundle knowledge but public Python grammar, which I verified directly: `ast.parse('def foo(a, b=0, /, c=1)')` gives posonlyargs=[a,b], args=[c], defaults=[0,1], i.e. 2 defaults right-aligned over 3 positional parameters. Any solver reading the AST sees this.

So the view's two load-bearing clauses -- the alignment postcondition `ToSeq(Result())[p] == resolved_default(p,...)` and the not-exempt clause `p < posonly and p >= positionals - len(provided) ==> ToSeq(Result())[p] != EMPTY()` -- restate the publicly-stated expected behaviour in the model's carrier. They tell the solver WHAT must hold, not WHERE to edit or HOW; the file, the function, the padded-list mechanism, and the pre-patch mis-indexing all stay in refinement.md/mapping.md, which are audit-side and (per eval/dataset.py) not part of task.spec_view.

(5) CORE GATES I LEANED ON, RE-MEASURED MYSELF. `bash scripts/nagini_verify.sh model.py` -> 'Verification successful', 33.62s, exit 0 (G-VERIFY/G-GOLD live). `bash scripts/nagini_verify.sh model_prepatch.py` -> 'Verification failed', 41.51s, and the single error is exactly the alignment postcondition -- 'Postcondition of resolve_positional_defaults might not hold. Assertion Forall(int, (lambda p: (Implies(((0 <= p) and (p < positionals)), (ToSeq(Result())[p] == resolved_default(...))' -- i.e. G-DIFF senses the BUG and not the MustTerminate annotation, matching the recorded G-DIFF and refinement.md C6's claim. Recorded gates re-read: G-LEAK pass (failures=[]), G-HYGIENE pass, G-AX pass (3900 signatures, domain-restricted render axiom validated both on- and off-domain), G-CONF pass (103696 checked, 0 disagreements), G-PBT pass (10 cases SOUND), G-RESOLVE pass (flaky: resolved on attempt 2/3 -- flagged as a durability note, not a leakage finding, since it bears on the oracle's stability rather than on the spec view).

**CONCLUSION.** Every clause of the spec view is either (a) the model's own carrier/contract vocabulary, (b) a restatement of behaviour the public problem_statement already specifies, or (c) public Python-grammar semantics a solver can read off `ast.parse`. Nothing in the view names the patched file, the patched function, the AST field names, the sentinel's real identity, the renderer's real name, or the gold mechanism, and nothing narrates the pre-patch state. NO-LEAKAGE.

**SCOPE.** No relaxation in this bundle: meta.json has no `relaxed_leakage` key (keys: additional_change_sites, ax_apply_gold, ax_apply_gold_note, axioms, base_commit, changed_files, deep_model_references, float_encoding, gates, instance_id, modeled_functions, patch_diff, prepatch_models, region_hashes, repo, schema_version, string_modeling, version) and `find -iname '*RELAX*'` over benchmark-verified/sphinx-doc__sphinx-7757/ returns nothing. So this is a plain leakage judgement, not a relaxation to re-derive. leakage.reviewer_directed() run over every bundle doc (model.py, model_prepatch.py, refinement.md, mapping.md, axiom_check.py, conformance_check.py, properties.py) returns [] for all seven; I grepped the bundle for attacker/panel/judge/verdict-string/NO-LEAKAGE language and the only hits are in verdict.md's record of PRIOR panel runs (transcripts of past reviews), not text addressing me. Nothing in the bundle tried to tell me what to submit.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `properties.py`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.
