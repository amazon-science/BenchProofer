# P2 adversarial audit — scikit-learn__scikit-learn-25973

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 15 admissible attacks re-run of 15 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 15 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 12 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_7.py`, `atk_9.py`, `atk_10.py`, `atk_11.py`, `atk_12.py`, `atk_13.py`, `atk_14.py`, `atk_15.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_5.py`, `atk_6.py`, `atk_8.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE — the spec was not broken. 15 same-spec wrong impls run through `adversary weakness`; 12 REJECTED, 3 CANDIDATES (atk_5, atk_6, atk_8), and all three candidates' materialized faithful patches RESOLVE under the official harness (run_resolve: resolved=True, completed=True, F2P 1/1, P2P 72/72, 0 PASS_TO_FAIL, patch_successfully_applied=True), so none is a verify=>correct witness.

All three candidates exploit the same real but BENIGN slack: the configured-source ledger postconditions `Ensures(Implies(src.reusable == False, scores_kept(src) == 0))` and `... draws_taken(src) == 1` are GUARDED, and `src.reusable` is a readable facet, so an impl may branch on it and take extra draw/keep operations on the CONFIGURED source in the `reusable == True` half where those clauses are vacuous. Crucially, my atk_3/atk_4 rejections establish that this slack is structurally CONFINED to a BALANCED PREFIX BEFORE the securing call: `secure_reusable_source` requires `draws_taken(src) == scores_kept(src)`, and for a reusable argument its Ensures leaves `draws_taken(src)` unconstrained (havocked), so no post-secure draw of `src` (atk_3) and no re-secure (atk_4) is provable. atk_6 takes a FULL n_scorings-long extra draw-and-keep pass over `src` before securing — literally the pre-patch consumption pattern the fix removed — and it still resolves.

Why this is not a spec defect, machine-confirmed rather than argued: refined faithfully (`src.reusable` == "the configured source re-presents its whole family on every draw" == `self.cv` is not a one-shot iterator, per mapping.md 2/4.3), each becomes one or n_scorings extra `cross_val_score(..., cv=self.cv, ...)` calls whose aggregate is DISCARDED. A re-presenting source cannot be depleted by being drawn again, so the extra draws are observationally inert: wasted work, not wrong behaviour. Narrowing this would make the spec UNFAITHFUL to check_cv's pass-through branch (an unconditional `draws_taken(src) == 1` is FALSE of KFold/int/list inputs, which check_cv either hands back or wraps, and whose later draws legitimately re-consume).

Decisively, the two UNGUARDED versions of the same shapes — the ones whose patches provably do NOT resolve — are both REJECTED by the spec: atk_15 (unguarded pre-secure draw+keep of `src`, which on the F2P one-shot generator exhausts it before check_cv wraps it) and atk_14 (re-secure `src` inside the scoring loop, i.e. hoisting check_cv back into the round loop). So the slack lives exactly and only in the half where it is inert.
```

**Attacks re-run (15):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -436,43 +436,27 @@
     Ensures(Implies(src.reusable == False, draws_taken(src) == 1))
     # post-conditions-end
     # impl-start
-    cv = secure_reusable_source(src)  # type: SplitSource
-    Assert(cv.size == src.size)
+    # PRE-PATCH skeleton: draw the configured source directly at every scoring
+    # step; never secure a source that presents its family afresh on every draw.
+    # The reported source carries the configured per-draw facet, not a forced one.
+    cv = SplitSource(src.size, src.reusable)  # type: SplitSource
     used = []  # type: List[int]
     i = 0
     while i < n_scorings:
         # invariants-start
         Invariant(Acc(src.size, 1 / 2) and Acc(src.reusable, 1 / 2))
         Invariant(Acc(cv.size, 1 / 2) and Acc(cv.reusable, 1 / 2))
-        Invariant(cv.size == src.size and cv.size > 0 and cv.reusable == True)
-        Invariant(presents_family(cv, src))
-        Invariant(has_ledger(cv))
-        Invariant(draws_taken(cv) == i)
-        Invariant(scores_kept(cv) == i)
-        Invariant(Forall(int, lambda k: Implies(0 <= k and k < scores_kept(cv),
-                score_from_draw(cv, k) == draw_count(cv.reusable, cv.size, k))))
-        # the configured source is untouched by the steps: when it is one-shot,
-        # its ledger still shows only the securing step's draw and no score kept
-        # from any draw of it.
-        Invariant(has_ledger(src))
-        Invariant(Implies(src.reusable == False, scores_kept(src) == 0))
-        Invariant(Implies(src.reusable == False, draws_taken(src) == 1))
+        Invariant(cv.size == src.size and cv.size > 0 and cv.reusable == src.reusable)
         Invariant(0 <= i and i <= n_scorings)
         Invariant(Acc(list_pred(used)))
         Invariant(len(used) == i)
         Invariant(Forall(int, lambda k: Implies(0 <= k and k < i,
                 used[k] == draw_count(cv.reusable, cv.size, k))))
-        Invariant(Forall(int, lambda k: Implies(0 <= k and k < i,
-                                                used[k] == src.size)))
-        # the measure: `n_scorings - i` steps remain, strictly fewer each pass;
-        # `+ 1` keeps it positive on the final pass (0 remaining).
+        # the measure: `n_scorings - i` steps remain, strictly fewer each pass.
         Invariant(MustTerminate(n_scorings - i + 1))
         # invariants-end
-        # step i draws the secured source (`i` draws preceded it) and keeps the
-        # score built from that draw before the next step draws.
-        c = draw_splits(cv)  # type: int
-        keep_score(cv, c)
-        used.append(c)
+        # step i draws the configured source directly; `i` draws preceded it.
+        used.append(draw_count(cv.reusable, cv.size, i))
         i = i + 1
     return SelectionResult(used, cv)
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -436,8 +436,9 @@
     Ensures(Implies(src.reusable == False, draws_taken(src) == 1))
     # post-conditions-end
     # impl-start
-    cv = secure_reusable_source(src)  # type: SplitSource
-    Assert(cv.size == src.size)
+    cv = SplitSource(src.size, True)  # type: SplitSource
+    Fold(presents_family(cv, src))
+    Fold(has_ledger(cv))
     used = []  # type: List[int]
     i = 0
     while i < n_scorings:
@@ -451,9 +452,6 @@
         Invariant(scores_kept(cv) == i)
         Invariant(Forall(int, lambda k: Implies(0 <= k and k < scores_kept(cv),
                 score_from_draw(cv, k) == draw_count(cv.reusable, cv.size, k))))
-        # the configured source is untouched by the steps: when it is one-shot,
-        # its ledger still shows only the securing step's draw and no score kept
-        # from any draw of it.
         Invariant(has_ledger(src))
         Invariant(Implies(src.reusable == False, scores_kept(src) == 0))
         Invariant(Implies(src.reusable == False, draws_taken(src) == 1))
@@ -464,12 +462,8 @@
                 used[k] == draw_count(cv.reusable, cv.size, k))))
         Invariant(Forall(int, lambda k: Implies(0 <= k and k < i,
                                                 used[k] == src.size)))
-        # the measure: `n_scorings - i` steps remain, strictly fewer each pass;
-        # `+ 1` keeps it positive on the final pass (0 remaining).
         Invariant(MustTerminate(n_scorings - i + 1))
         # invariants-end
-        # step i draws the secured source (`i` draws preceded it) and keeps the
-        # score built from that draw before the next step draws.
         c = draw_splits(cv)  # type: int
         keep_score(cv, c)
         used.append(c)
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -451,9 +451,6 @@
         Invariant(scores_kept(cv) == i)
         Invariant(Forall(int, lambda k: Implies(0 <= k and k < scores_kept(cv),
                 score_from_draw(cv, k) == draw_count(cv.reusable, cv.size, k))))
-        # the configured source is untouched by the steps: when it is one-shot,
-        # its ledger still shows only the securing step's draw and no score kept
-        # from any draw of it.
         Invariant(has_ledger(src))
         Invariant(Implies(src.reusable == False, scores_kept(src) == 0))
         Invariant(Implies(src.reusable == False, draws_taken(src) == 1))
@@ -464,15 +461,14 @@
                 used[k] == draw_count(cv.reusable, cv.size, k))))
         Invariant(Forall(int, lambda k: Implies(0 <= k and k < i,
                                                 used[k] == src.size)))
-        # the measure: `n_scorings - i` steps remain, strictly fewer each pass;
-        # `+ 1` keeps it positive on the final pass (0 remaining).
         Invariant(MustTerminate(n_scorings - i + 1))
         # invariants-end
-        # step i draws the secured source (`i` draws preceded it) and keeps the
-        # score built from that draw before the next step draws.
         c = draw_splits(cv)  # type: int
         keep_score(cv, c)
         used.append(c)
         i = i + 1
+    if src.reusable:
+        cx = draw_splits(src)  # type: int
+        keep_score(src, cx)
     return SelectionResult(used, cv)
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -451,9 +451,6 @@
         Invariant(scores_kept(cv) == i)
         Invariant(Forall(int, lambda k: Implies(0 <= k and k < scores_kept(cv),
                 score_from_draw(cv, k) == draw_count(cv.reusable, cv.size, k))))
-        # the configured source is untouched by the steps: when it is one-shot,
-        # its ledger still shows only the securing step's draw and no score kept
-        # from any draw of it.
         Invariant(has_ledger(src))
         Invariant(Implies(src.reusable == False, scores_kept(src) == 0))
         Invariant(Implies(src.reusable == False, draws_taken(src) == 1))
@@ -464,15 +461,12 @@
                 used[k] == draw_count(cv.reusable, cv.size, k))))
         Invariant(Forall(int, lambda k: Implies(0 <= k and k < i,
                                                 used[k] == src.size)))
-        # the measure: `n_scorings - i` steps remain, strictly fewer each pass;
-        # `+ 1` keeps it positive on the final pass (0 remaining).
         Invariant(MustTerminate(n_scorings - i + 1))
         # invariants-end
-        # step i draws the secured source (`i` draws preceded it) and keeps the
-        # score built from that draw before the next step draws.
         c = draw_splits(cv)  # type: int
         keep_score(cv, c)
         used.append(c)
         i = i + 1
+    junk = secure_reusable_source(cv)  # type: SplitSource
     return SelectionResult(used, cv)
     # impl-end
```

Attack 5 — `atk_5.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -436,6 +436,11 @@
     Ensures(Implies(src.reusable == False, draws_taken(src) == 1))
     # post-conditions-end
     # impl-start
+    c0 = 0  # type: int
+    if src.reusable:
+        c0 = draw_splits(src)
+        keep_score(src, c0)
+        Assert(c0 == src.size)
     cv = secure_reusable_source(src)  # type: SplitSource
     Assert(cv.size == src.size)
     used = []  # type: List[int]
@@ -451,12 +456,10 @@
         Invariant(scores_kept(cv) == i)
         Invariant(Forall(int, lambda k: Implies(0 <= k and k < scores_kept(cv),
                 score_from_draw(cv, k) == draw_count(cv.reusable, cv.size, k))))
-        # the configured source is untouched by the steps: when it is one-shot,
-        # its ledger still shows only the securing step's draw and no score kept
-        # from any draw of it.
         Invariant(has_ledger(src))
         Invariant(Implies(src.reusable == False, scores_kept(src) == 0))
         Invariant(Implies(src.reusable == False, draws_taken(src) == 1))
+        Invariant(Implies(src.reusable == True, c0 == src.size))
         Invariant(0 <= i and i <= n_scorings)
         Invariant(Acc(list_pred(used)))
         Invariant(len(used) == i)
@@ -464,15 +467,14 @@
                 used[k] == draw_count(cv.reusable, cv.size, k))))
         Invariant(Forall(int, lambda k: Implies(0 <= k and k < i,
                                                 used[k] == src.size)))
-        # the measure: `n_scorings - i` steps remain, strictly fewer each pass;
-        # `+ 1` keeps it positive on the final pass (0 remaining).
         Invariant(MustTerminate(n_scorings - i + 1))
         # invariants-end
-        # step i draws the secured source (`i` draws preceded it) and keeps the
-        # score built from that draw before the next step draws.
         c = draw_splits(cv)  # type: int
         keep_score(cv, c)
-        used.append(c)
+        if src.reusable:
+            used.append(c0)
+        else:
+            used.append(c)
         i = i + 1
     return SelectionResult(used, cv)
     # impl-end
```

Attack 6 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -436,6 +436,20 @@
     Ensures(Implies(src.reusable == False, draws_taken(src) == 1))
     # post-conditions-end
     # impl-start
+    j = 0  # type: int
+    if src.reusable:
+        while j < n_scorings:
+            # invariants-start
+            Invariant(Acc(src.size, 1 / 2) and Acc(src.reusable, 1 / 2))
+            Invariant(src.size > 0 and src.reusable == True)
+            Invariant(has_ledger(src))
+            Invariant(0 <= j and j <= n_scorings)
+            Invariant(draws_taken(src) == j and scores_kept(src) == j)
+            Invariant(MustTerminate(n_scorings - j + 1))
+            # invariants-end
+            cj = draw_splits(src)  # type: int
+            keep_score(src, cj)
+            j = j + 1
     cv = secure_reusable_source(src)  # type: SplitSource
     Assert(cv.size == src.size)
     used = []  # type: List[int]
@@ -451,9 +465,6 @@
         Invariant(scores_kept(cv) == i)
         Invariant(Forall(int, lambda k: Implies(0 <= k and k < scores_kept(cv),
                 score_from_draw(cv, k) == draw_count(cv.reusable, cv.size, k))))
-        # the configured source is untouched by the steps: when it is one-shot,
-        # its ledger still shows only the securing step's draw and no score kept
-        # from any draw of it.
         Invariant(has_ledger(src))
         Invariant(Implies(src.reusable == False, scores_kept(src) == 0))
         Invariant(Implies(src.reusable == False, draws_taken(src) == 1))
@@ -464,12 +475,8 @@
                 used[k] == draw_count(cv.reusable, cv.size, k))))
         Invariant(Forall(int, lambda k: Implies(0 <= k and k < i,
                                                 used[k] == src.size)))
-        # the measure: `n_scorings - i` steps remain, strictly fewer each pass;
-        # `+ 1` keeps it positive on the final pass (0 remaining).
         Invariant(MustTerminate(n_scorings - i + 1))
         # invariants-end
-        # step i draws the secured source (`i` draws preceded it) and keeps the
-        # score built from that draw before the next step draws.
         c = draw_splits(cv)  # type: int
         keep_score(cv, c)
         used.append(c)
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -440,7 +440,7 @@
     Assert(cv.size == src.size)
     used = []  # type: List[int]
     i = 0
-    while i < n_scorings:
+    while i < n_scorings - 1:
         # invariants-start
         Invariant(Acc(src.size, 1 / 2) and Acc(src.reusable, 1 / 2))
         Invariant(Acc(cv.size, 1 / 2) and Acc(cv.reusable, 1 / 2))
@@ -451,9 +451,6 @@
         Invariant(scores_kept(cv) == i)
         Invariant(Forall(int, lambda k: Implies(0 <= k and k < scores_kept(cv),
                 score_from_draw(cv, k) == draw_count(cv.reusable, cv.size, k))))
-        # the configured source is untouched by the steps: when it is one-shot,
-        # its ledger still shows only the securing step's draw and no score kept
-        # from any draw of it.
         Invariant(has_ledger(src))
         Invariant(Implies(src.reusable == False, scores_kept(src) == 0))
         Invariant(Implies(src.reusable == False, draws_taken(src) == 1))
@@ -464,15 +461,13 @@
                 used[k] == draw_count(cv.reusable, cv.size, k))))
         Invariant(Forall(int, lambda k: Implies(0 <= k and k < i,
                                                 used[k] == src.size)))
-        # the measure: `n_scorings - i` steps remain, strictly fewer each pass;
-        # `+ 1` keeps it positive on the final pass (0 remaining).
         Invariant(MustTerminate(n_scorings - i + 1))
         # invariants-end
-        # step i draws the secured source (`i` draws preceded it) and keeps the
-        # score built from that draw before the next step draws.
         c = draw_splits(cv)  # type: int
         keep_score(cv, c)
         used.append(c)
         i = i + 1
+    # the final step reports a REMEMBERED number instead of drawing for itself
+    used.append(src.size)
     return SelectionResult(used, cv)
     # impl-end
```

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -451,9 +451,6 @@
         Invariant(scores_kept(cv) == i)
         Invariant(Forall(int, lambda k: Implies(0 <= k and k < scores_kept(cv),
                 score_from_draw(cv, k) == draw_count(cv.reusable, cv.size, k))))
-        # the configured source is untouched by the steps: when it is one-shot,
-        # its ledger still shows only the securing step's draw and no score kept
-        # from any draw of it.
         Invariant(has_ledger(src))
         Invariant(Implies(src.reusable == False, scores_kept(src) == 0))
         Invariant(Implies(src.reusable == False, draws_taken(src) == 1))
@@ -464,15 +461,11 @@
                 used[k] == draw_count(cv.reusable, cv.size, k))))
         Invariant(Forall(int, lambda k: Implies(0 <= k and k < i,
                                                 used[k] == src.size)))
-        # the measure: `n_scorings - i` steps remain, strictly fewer each pass;
-        # `+ 1` keeps it positive on the final pass (0 remaining).
         Invariant(MustTerminate(n_scorings - i + 1))
         # invariants-end
-        # step i draws the secured source (`i` draws preceded it) and keeps the
-        # score built from that draw before the next step draws.
         c = draw_splits(cv)  # type: int
         keep_score(cv, c)
-        used.append(c)
+        used.append(src.size)
         i = i + 1
     return SelectionResult(used, cv)
     # impl-end
```

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -447,13 +447,8 @@
         Invariant(cv.size == src.size and cv.size > 0 and cv.reusable == True)
         Invariant(presents_family(cv, src))
         Invariant(has_ledger(cv))
-        Invariant(draws_taken(cv) == i)
-        Invariant(scores_kept(cv) == i)
-        Invariant(Forall(int, lambda k: Implies(0 <= k and k < scores_kept(cv),
-                score_from_draw(cv, k) == draw_count(cv.reusable, cv.size, k))))
-        # the configured source is untouched by the steps: when it is one-shot,
-        # its ledger still shows only the securing step's draw and no score kept
-        # from any draw of it.
+        Invariant(draws_taken(cv) == 0)
+        Invariant(scores_kept(cv) == 0)
         Invariant(has_ledger(src))
         Invariant(Implies(src.reusable == False, scores_kept(src) == 0))
         Invariant(Implies(src.reusable == False, draws_taken(src) == 1))
@@ -461,18 +456,10 @@
         Invariant(Acc(list_pred(used)))
         Invariant(len(used) == i)
         Invariant(Forall(int, lambda k: Implies(0 <= k and k < i,
-                used[k] == draw_count(cv.reusable, cv.size, k))))
-        Invariant(Forall(int, lambda k: Implies(0 <= k and k < i,
                                                 used[k] == src.size)))
-        # the measure: `n_scorings - i` steps remain, strictly fewer each pass;
-        # `+ 1` keeps it positive on the final pass (0 remaining).
         Invariant(MustTerminate(n_scorings - i + 1))
         # invariants-end
-        # step i draws the secured source (`i` draws preceded it) and keeps the
-        # score built from that draw before the next step draws.
-        c = draw_splits(cv)  # type: int
-        keep_score(cv, c)
-        used.append(c)
+        used.append(src.size)
         i = i + 1
     return SelectionResult(used, cv)
     # impl-end
```

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -448,12 +448,7 @@
         Invariant(presents_family(cv, src))
         Invariant(has_ledger(cv))
         Invariant(draws_taken(cv) == i)
-        Invariant(scores_kept(cv) == i)
-        Invariant(Forall(int, lambda k: Implies(0 <= k and k < scores_kept(cv),
-                score_from_draw(cv, k) == draw_count(cv.reusable, cv.size, k))))
-        # the configured source is untouched by the steps: when it is one-shot,
-        # its ledger still shows only the securing step's draw and no score kept
-        # from any draw of it.
+        Invariant(scores_kept(cv) == 0)
         Invariant(has_ledger(src))
         Invariant(Implies(src.reusable == False, scores_kept(src) == 0))
         Invariant(Implies(src.reusable == False, draws_taken(src) == 1))
@@ -464,15 +459,34 @@
                 used[k] == draw_count(cv.reusable, cv.size, k))))
         Invariant(Forall(int, lambda k: Implies(0 <= k and k < i,
                                                 used[k] == src.size)))
-        # the measure: `n_scorings - i` steps remain, strictly fewer each pass;
-        # `+ 1` keeps it positive on the final pass (0 remaining).
         Invariant(MustTerminate(n_scorings - i + 1))
         # invariants-end
-        # step i draws the secured source (`i` draws preceded it) and keeps the
-        # score built from that draw before the next step draws.
         c = draw_splits(cv)  # type: int
-        keep_score(cv, c)
         used.append(c)
         i = i + 1
+    m = 0  # type: int
+    while m < n_scorings:
+        # invariants-start
+        Invariant(Acc(src.size, 1 / 2) and Acc(src.reusable, 1 / 2))
+        Invariant(Acc(cv.size, 1 / 2) and Acc(cv.reusable, 1 / 2))
+        Invariant(cv.size == src.size and cv.size > 0 and cv.reusable == True)
+        Invariant(presents_family(cv, src))
+        Invariant(has_ledger(cv))
+        Invariant(draws_taken(cv) == n_scorings)
+        Invariant(scores_kept(cv) == m)
+        Invariant(has_ledger(src))
+        Invariant(Implies(src.reusable == False, scores_kept(src) == 0))
+        Invariant(Implies(src.reusable == False, draws_taken(src) == 1))
+        Invariant(0 <= m and m <= n_scorings)
+        Invariant(Acc(list_pred(used)))
+        Invariant(len(used) == n_scorings)
+        Invariant(Forall(int, lambda k: Implies(0 <= k and k < n_scorings,
+                used[k] == draw_count(cv.reusable, cv.size, k))))
+        Invariant(Forall(int, lambda k: Implies(0 <= k and k < n_scorings,
+                                                used[k] == src.size)))
+        Invariant(MustTerminate(n_scorings - m + 1))
+        # invariants-end
+        keep_score(cv, used[m])
+        m = m + 1
     return SelectionResult(used, cv)
     # impl-end
```

Attack 11 — `atk_11.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -438,6 +438,8 @@
     # impl-start
     cv = secure_reusable_source(src)  # type: SplitSource
     Assert(cv.size == src.size)
+    if src.reusable == False:
+        keep_score(src, src.size)
     used = []  # type: List[int]
     i = 0
     while i < n_scorings:
@@ -451,9 +453,6 @@
         Invariant(scores_kept(cv) == i)
         Invariant(Forall(int, lambda k: Implies(0 <= k and k < scores_kept(cv),
                 score_from_draw(cv, k) == draw_count(cv.reusable, cv.size, k))))
-        # the configured source is untouched by the steps: when it is one-shot,
-        # its ledger still shows only the securing step's draw and no score kept
-        # from any draw of it.
         Invariant(has_ledger(src))
         Invariant(Implies(src.reusable == False, scores_kept(src) == 0))
         Invariant(Implies(src.reusable == False, draws_taken(src) == 1))
@@ -464,12 +463,8 @@
                 used[k] == draw_count(cv.reusable, cv.size, k))))
         Invariant(Forall(int, lambda k: Implies(0 <= k and k < i,
                                                 used[k] == src.size)))
-        # the measure: `n_scorings - i` steps remain, strictly fewer each pass;
-        # `+ 1` keeps it positive on the final pass (0 remaining).
         Invariant(MustTerminate(n_scorings - i + 1))
         # invariants-end
-        # step i draws the secured source (`i` draws preceded it) and keeps the
-        # score built from that draw before the next step draws.
         c = draw_splits(cv)  # type: int
         keep_score(cv, c)
         used.append(c)
```

Attack 12 — `atk_12.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -436,6 +436,8 @@
     Ensures(Implies(src.reusable == False, draws_taken(src) == 1))
     # post-conditions-end
     # impl-start
+    if n_scorings >= 1:
+        return select_features(src, n_scorings)
     cv = secure_reusable_source(src)  # type: SplitSource
     Assert(cv.size == src.size)
     used = []  # type: List[int]
@@ -451,9 +453,6 @@
         Invariant(scores_kept(cv) == i)
         Invariant(Forall(int, lambda k: Implies(0 <= k and k < scores_kept(cv),
                 score_from_draw(cv, k) == draw_count(cv.reusable, cv.size, k))))
-        # the configured source is untouched by the steps: when it is one-shot,
-        # its ledger still shows only the securing step's draw and no score kept
-        # from any draw of it.
         Invariant(has_ledger(src))
         Invariant(Implies(src.reusable == False, scores_kept(src) == 0))
         Invariant(Implies(src.reusable == False, draws_taken(src) == 1))
@@ -464,12 +463,8 @@
                 used[k] == draw_count(cv.reusable, cv.size, k))))
         Invariant(Forall(int, lambda k: Implies(0 <= k and k < i,
                                                 used[k] == src.size)))
-        # the measure: `n_scorings - i` steps remain, strictly fewer each pass;
-        # `+ 1` keeps it positive on the final pass (0 remaining).
         Invariant(MustTerminate(n_scorings - i + 1))
         # invariants-end
-        # step i draws the secured source (`i` draws preceded it) and keeps the
-        # score built from that draw before the next step draws.
         c = draw_splits(cv)  # type: int
         keep_score(cv, c)
         used.append(c)
```

Attack 13 — `atk_13.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -451,9 +451,6 @@
         Invariant(scores_kept(cv) == i)
         Invariant(Forall(int, lambda k: Implies(0 <= k and k < scores_kept(cv),
                 score_from_draw(cv, k) == draw_count(cv.reusable, cv.size, k))))
-        # the configured source is untouched by the steps: when it is one-shot,
-        # its ledger still shows only the securing step's draw and no score kept
-        # from any draw of it.
         Invariant(has_ledger(src))
         Invariant(Implies(src.reusable == False, scores_kept(src) == 0))
         Invariant(Implies(src.reusable == False, draws_taken(src) == 1))
@@ -464,15 +461,18 @@
                 used[k] == draw_count(cv.reusable, cv.size, k))))
         Invariant(Forall(int, lambda k: Implies(0 <= k and k < i,
                                                 used[k] == src.size)))
-        # the measure: `n_scorings - i` steps remain, strictly fewer each pass;
-        # `+ 1` keeps it positive on the final pass (0 remaining).
         Invariant(MustTerminate(n_scorings - i + 1))
         # invariants-end
-        # step i draws the secured source (`i` draws preceded it) and keeps the
-        # score built from that draw before the next step draws.
         c = draw_splits(cv)  # type: int
         keep_score(cv, c)
         used.append(c)
         i = i + 1
-    return SelectionResult(used, cv)
+    res = SelectionResult(used, cv)  # type: SelectionResult
+    spin = 0  # type: int
+    while spin >= 0:
+        # invariants-start
+        Invariant(spin >= 0)
+        # invariants-end
+        spin = spin + 1
+    return res
     # impl-end
```

Attack 14 — `atk_14.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -451,9 +451,6 @@
         Invariant(scores_kept(cv) == i)
         Invariant(Forall(int, lambda k: Implies(0 <= k and k < scores_kept(cv),
                 score_from_draw(cv, k) == draw_count(cv.reusable, cv.size, k))))
-        # the configured source is untouched by the steps: when it is one-shot,
-        # its ledger still shows only the securing step's draw and no score kept
-        # from any draw of it.
         Invariant(has_ledger(src))
         Invariant(Implies(src.reusable == False, scores_kept(src) == 0))
         Invariant(Implies(src.reusable == False, draws_taken(src) == 1))
@@ -464,15 +461,14 @@
                 used[k] == draw_count(cv.reusable, cv.size, k))))
         Invariant(Forall(int, lambda k: Implies(0 <= k and k < i,
                                                 used[k] == src.size)))
-        # the measure: `n_scorings - i` steps remain, strictly fewer each pass;
-        # `+ 1` keeps it positive on the final pass (0 remaining).
         Invariant(MustTerminate(n_scorings - i + 1))
         # invariants-end
-        # step i draws the secured source (`i` draws preceded it) and keeps the
-        # score built from that draw before the next step draws.
         c = draw_splits(cv)  # type: int
         keep_score(cv, c)
         used.append(c)
+        # RE-SECURE the configured source inside the loop and discard it:
+        # refines to calling check_cv(self.cv, ...) once per scoring round.
+        again = secure_reusable_source(src)  # type: SplitSource
         i = i + 1
     return SelectionResult(used, cv)
     # impl-end
```

Attack 15 — `atk_15.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -436,6 +436,8 @@
     Ensures(Implies(src.reusable == False, draws_taken(src) == 1))
     # post-conditions-end
     # impl-start
+    c0 = draw_splits(src)  # type: int
+    keep_score(src, c0)
     cv = secure_reusable_source(src)  # type: SplitSource
     Assert(cv.size == src.size)
     used = []  # type: List[int]
@@ -451,9 +453,6 @@
         Invariant(scores_kept(cv) == i)
         Invariant(Forall(int, lambda k: Implies(0 <= k and k < scores_kept(cv),
                 score_from_draw(cv, k) == draw_count(cv.reusable, cv.size, k))))
-        # the configured source is untouched by the steps: when it is one-shot,
-        # its ledger still shows only the securing step's draw and no score kept
-        # from any draw of it.
         Invariant(has_ledger(src))
         Invariant(Implies(src.reusable == False, scores_kept(src) == 0))
         Invariant(Implies(src.reusable == False, draws_taken(src) == 1))
@@ -464,12 +463,8 @@
                 used[k] == draw_count(cv.reusable, cv.size, k))))
         Invariant(Forall(int, lambda k: Implies(0 <= k and k < i,
                                                 used[k] == src.size)))
-        # the measure: `n_scorings - i` steps remain, strictly fewer each pass;
-        # `+ 1` keeps it positive on the final pass (0 remaining).
         Invariant(MustTerminate(n_scorings - i + 1))
         # invariants-end
-        # step i draws the secured source (`i` draws preceded it) and keeps the
-        # score built from that draw before the next step draws.
         c = draw_splits(cv)  # type: int
         keep_score(cv, c)
         used.append(c)
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial refinement-fidelity audit, instance scikit-learn__scikit-learn-25973 (nagini). Frozen model.py sha256 2239e1e637688c69860cf1e80faf357c082e362e03d81a44c24f78180c38308a — bundle NOT modified (verified sha + `git status --porcelain` clean at the end); Per instructions I concentrated on the A legs and the model<->patch correspondence (R/I mechanically covered by G-CONF).

**Attack construction:** every file was produced by build.py, which splices ONLY the lines strictly between `# impl-start` and `# impl-end` into a byte-for-byte copy of the frozen model.py, so the spec view is identical by construction. Confirmed mechanically: `python -m swebench_unified.adversary same-spec nagini scikit-learn__scikit-learn-25973 <f>` -> exit 0 for all 15 attacks, all 3 controls and the positive control.

### Positive control
pos_control.py (byte copy of frozen model.py). `bash scripts/nagini_verify.sh pos_control.py` -> "Verification successful", exit 0. same-spec exit 0.

#### ALL 15 ATTACKS — command pattern
`python -m swebench_unified.adversary weakness nagini scikit-learn__scikit-learn-25973 atk_N.py`
Run 3-at-a-time as detached background jobs (each Nagini check = JVM+Z3). Every attack ran to a verdict; no timeouts, no host-saturation no-verdicts.

[atk_1] PREPATCH REPRODUCED. Bundle's model_prepatch.py verbatim (draws the configured source directly per step, never secures). -> exit 2 REJECTED (26.1s). Prepatch bug reproduced and rejected. [atk_2] FORGE THE CAPABILITY (A3b unforgeability / ungrounded oracle): never secures; tries `Fold(presents_family(cv, src))` + `Fold(has_ledger(cv))` on a source built from scratch. -> exit 2 REJECTED (16.0s). The abstract predicates are genuinely un-Foldable. [atk_3] POST-LOOP draw+keep of the CONFIGURED source, guarded by `if src.reusable`. -> exit 2 REJECTED (35.9s). KEY STRUCTURAL RESULT: blocked because the securing axiom havocs `draws_taken(src)` for a reusable argument, so the ledger is unknown afterwards.

[atk_4] POST-LOOP RE-SECURE of the reported source (`secure_reusable_source(cv)` discarded). -> exit 2 REJECTED. Confirms the same havoc closes re-securing. [atk_5] **CANDIDATE** JOURNAL-SOURCE SUBSTITUTION: guarded balanced pre-secure draw+keep of `src`, then the gold loop reporting that pre-draw's count. -> exit 0 CANDIDATE (120.2s). Patch materialized + harness EXECUTED: resolved=True. [atk_6] **CANDIDATE** MAXIMAL pre-secure redistribution: a full n_scorings-long extra draw-and-keep pass over `src` (the pre-patch pattern) in the guarded half. -> exit 0 CANDIDATE (71.8s). Patch materialized + harness EXECUTED: resolved=True. [atk_7] BOUNDARY / partial domain: gold for every step except the LAST, whose count is echoed instead of drawn+kept.

Every value clause holds (draw_count(True,size,k) is constant). -> exit 2 REJECTED. Only the ledgers can see the missing final draw (pin 2/3). [atk_8] **CANDIDATE** UNGROUNDED-ORACLE ECHO with honest ledgers: draws and keeps for real, but reports `src.size` echoed off the argument. -> exit 0 CANDIDATE (43.6s). Patch materialized + harness EXECUTED: resolved=True. (Under the spec's own forced facts `Result().cv.size == src.size`, the echoed number IS the drawn count, so the modelled observable is identical to gold — see the faithfulness note below.) [atk_9] DRAIN-THEN-ECHO / the named recorded counterexample ("hoist check_cv but do NOT thread it", mapping.md 4.2 row 3): secures once so `presents_family` IS held, but no step ever draws it. -> exit 2 REJECTED.

This is the shape whose patch is MEASURED non-resolving, and the spec rejects it. [atk_10] BATCH-THEN-REPORT: all n_scorings draws up front, then all n_scorings keeps. BOTH total tallies reach n_scorings and every value clause holds — only the alternation preconditions distinguish it. -> exit 2 REJECTED. Strongest test of pin 3; it holds. [atk_11] KEEP OFF THE CONFIGURED SOURCE'S OWN DRAW: in the one-shot half, securing leaves exactly one draw of `src` outstanding, making `keep_score(src, src.size)` alternation-LEGAL; aggregate that draw, then gold. -> exit 2 REJECTED (pin 4, `scores_kept(src) == 0`). [atk_12] TERMINATION A-LEG (A6): guarded SELF-CALL inheriting every postcondition verbatim, so ONLY the measure can reject it. -> exit 2 REJECTED.

MustTerminate is at the METHOD level and load-bearing. [atk_13] DIVERGENCE: gold work then an unbounded spin — never answers. -> exit 2 REJECTED (pin 5). [atk_14] **UNGUARDED RE-SECURE PER STEP** — the highest-value lane I could construct: `secure_reusable_source(src)` INSIDE the scoring loop for EVERY input. Faithful refinement = move `check_cv` back inside the round loop, which on the F2P one-shot generator re-wraps an already-exhausted generator -> IndexError -> would NOT resolve. -> exit 2 REJECTED. The lane is closed by the securing axiom's own precondition `draws_taken(src) == scores_kept(src)`, which the one-shot Ensures (`draws_taken(src) == Old(...) + 1`, `scores_kept` unchanged) permanently falsifies after the first securing.

[atk_15] **UNGUARDED pre-secure draw+keep** — atk_5's prefix with the `if src.reusable` guard REMOVED, so it also runs on the one-shot F2P input, consuming the generator before check_cv wraps it -> IndexError -> would NOT resolve. -> exit 2 REJECTED. Confirms the one-shot half of the configured-source ledger clauses is TIGHT: k balanced pre-pairs force draws=k+1/kept=k, and only k==0 satisfies `draws_taken(src) == 1 and scores_kept(src) == 0`.

atk_14 + atk_15 are the load-bearing negative result of this audit: the two shapes that would have BROKEN the spec are exactly the unguarded twins of the three that verify, and both are rejected. The slack is confined to the half where it is provably inert.

#### MATERIALIZED PATCHES + EXECUTED HARNESS (all 3 candidates)
Refinement dictionary applied mechanically (refinement.md A1-A4b, mapping.md 1/3.3): `src` -> `self.cv` (`_sequential`.py:186); `src.reusable` -> "self.cv re-presents its whole family on every draw" -> tested as `not hasattr(self.cv, "__next__")` (TRUE for None/int/KFold/list = every P2P config; FALSE for the F2P `LeaveOneGroupOut().split(...)` generator); `cv = secure_reusable_source(src)` -> `cv = check_cv(self.cv, y, classifier=is_classifier(self.estimator))`; one `draw_splits(S)` + `keep_score(S, c)` pair -> one `cross_val_score(..., cv=S, ...).mean()` (A4/A4b: one cross_val_score IS one draw and one kept score). Each patch was built by textual edit of a GOLD-patched base_commit worktree, so it contains the whole gold change plus exactly the attack's delta.

My gold reconstruction was diffed against the bundle's patch.diff and is content-identical (only hunk-header context strings differ). ALL THREE checked with `git apply --check <patch>` in a clean base_commit (10dbc142bd17ccf7bd38eec2ac04b52ce0d1009e) worktree -> all APPLY CLEANLY. Harness: `run_resolve("scikit-learn__scikit-learn-25973", <patch text>)`. patch_atk_5.diff -> resolved=True, completed=True, attempts=2, applied=True, F2P 1/0, P2P 72/0, PASS_TO_FAIL 0. JSON: resolve_patch_atk_5.json patch_atk_6.diff -> resolved=True, completed=True, attempts=2, applied=True, F2P 1/0, P2P 72/0, PASS_TO_FAIL 0. JSON: resolve_patch_atk_6.json patch_atk_8.diff -> resolved=True, completed=True, attempts=1, flaky=False, applied=True, F2P 1/0, P2P 72/0, PASS_TO_FAIL 0. JSON: resolve_patch_atk_8.json

FAITHFULNESS SELF-CORRECTION (disclosed because it changed what I submitted): my FIRST cut of patch_atk_5 and patch_atk_8 perturbed the VALUE stored into `scores[feature_idx]`. That is unfaithful — mapping.md line 43 and refinement.md A4b state the modelled observable is the per-scoring SPLIT COUNT, and that "the score VALUES are irrelevant to the tested behaviour... what is modelled is the split count the aggregation ran over". A patch that perturbs an unmodelled quantity grades nothing. I KILLED those two in-flight resolve runs before using their verdicts and rebuilt both faithfully: patch_atk_5 now materializes only the extra guarded consumption of self.cv; and for atk_8, since the spec forces `Result().cv.size == src.size` so the echoed number IS the drawn count (same draws, same keeps, same order, same reported numbers), the faithful refined patch IS the gold patch, which is what I submitted rather than fabricating a delta. Both rebuilt patches were re-checked with `git apply --check` and re-run through the harness to completion.

HOST-RACE HANDLING (would otherwise have been INCONCLUSIVE): patch_atk_5's first completed-run attempt returned resolved=False with **completed=False** — note "no report — harness error or image pull failure ... docker.errors.ImageNotFound", i.e. a host/image race, NOT a non-resolution. Per the rule that a cap or outage the HOST hit is not a measurement, I did not read that as a spec break; I preserved it as resolve_patch_atk_5.ATTEMPT1_nocomplete.json and RE-RAN, which completed with resolved=True. Every needed resolve run therefore has a completed verdict.

### NON-VACUITY CONTROLS (a CANDIDATE that resolves is only evidence if the exploit is real and my oracle can see failure)
(1) PRECONDITION SATISFIABILITY: ctl_pre_sat.py = gold impl with `Assert(False)` at the top. `bash scripts/nagini_verify.sh` -> exit 1, "Assert might fail. Assertion False might not hold." So the frozen precondition set is satisfiable and no attack "verified" vacuously.

(2) atk_6 GUARD FEASIBILITY: ctl_atk6_guard.py = atk_6 with `Assert(False)` inside `if src.reusable:` -> exit 1, assertion fails. The guarded branch is REACHABLE and its extra consumption genuinely happened (not an infeasible-guard vacuity).

(3) atk_11 GUARD FEASIBILITY: ctl_atk11_guard.py = `Assert(False)` inside `if src.reusable == False:` -> exit 1, assertion fails. A one-shot source IS admissible, so the one-shot lane the tight clauses govern is real and atk_11/atk_15's rejections are meaningful.

(4) RESOLVE-DETECTION CONTROL: patch_ctl_nothread.diff = the known non-resolving neighbour (hoist check_cv, do NOT thread it; = atk_9's refinement, mapping.md 4.2 row 3). `git apply --check` OK. run_resolve -> **resolved=False, completed=True**, attempts=3, flaky=False, note "patch did not resolve in 3 attempts (consistent — not flaky)", applied=True, F2P failure=[test_cv_generator_support], P2P 72/72. So my harness invocation DOES detect a real failure; the three resolved=True results are measurements, not false greens.

### A-LEG AUDIT (refinement.md C: every leg R / A-consumed / A-reference / I; no kind-3)
CONFIRMED no kind-3. Legs A1(R), A1b(A-consumed), A2(R+I), A3(A-consumed), A3b(A-consumed), A3c(A-consumed), A4(R+A-consumed+A-reference), A4b(R+A-consumed), A5(R), A6(R). No axiom is placed on the function under change — select_features is modelled deeply by the verified loop; the ledgers/journal are abstract readers only the modelled ops can advance, so there is no ungrounded answer-key oracle. CORRESPONDENCE TO THE REAL CALLEES, re-verified myself at base_commit 10dbc142bd17ccf7bd38eec2ac04b52ce0d1009e in a fresh worktree: A3 secure_reusable_source == check_cv: `def check_cv` at `_split`.py:2406 (exact); wrapping branch `return _CVIterableWrapper(cv)` :2460 (exact); pass-through `return cv  # New style...` :2462 (exact); Integral branch :2443-2451 (exact).

A1b materialisable == "not the pass-through branch" == `not hasattr(cv, "split")`: real guard `if not hasattr(cv, "split") or isinstance(cv, str):` at :2453 (docs cite :2459 — 6-line drift, quoted text correct). A3c one-draw consumption == `self.cv = list(cv)` at :2357 (docs cite :2360 — 3-line drift, text correct). One traversal => exactly +1 draw. A4 one draw per scoring == `indices = cv.split(X, y, groups)` at `_validation`.py:274 (exact). A4b aggregation == `results = _aggregate_score_dicts(results)` at `_validation`.py:309 (exact); stored score at `_sequential`.py:308-315 (exact).

A1 `self.cv = cv` at `_sequential`.py:186; gold call site :262; A2 round loop :276 / candidate loop :302; A6 `return self` :292 — all confirmed. patch.diff independently confirmed == the three-part change (import is_classifier/check_cv, hoist check_cv before the loop, thread cv into `_get_best_new_feature_score` to cv=cv). I reconstructed it by hand and diffed: content-identical.

A1b (`materialisable`) INDEPENDENTLY RE-MEASURED rather than trusted: I re-ran the real `check_cv` on all six realizations of mapping.md 4.3 and reproduced its table exactly — one-shot GENERATOR (no .split): passthrough=False, wraps to `_CVIterableWrapper`, 2 draws (3,3) [admissible, the F2P case]; one-shot object WITH .split: passthrough=True, (3,0) [inadmissible]; shrinking object WITH .split: passthrough=True, (3,2) [inadmissible]; KFold(3): passthrough=True, (3,3); list: wraps, (3,3); integer 3: StratifiedKFold, (3,3). So `materialisable(src)` == "the call does not merely hand this source back" is TRUE of exactly rows 1/5/6 and FALSE of rows 2-3, and `reusable` alone genuinely does not decide the branch. The narrowing costs the spec none of the behaviour under change.

### DOCS DEFECTS FOUND (advisory; neither is a spec hole — I tested every cited lane myself)
(a) refinement.md B cites FOUR properties.py reject cases by name — `scoring-draws-configured-source`, `keep-off-configured-draw`, `resecure-per-scoring`, `diverges-never-answers` — and NONE of the four exists in properties.py (0 occurrences each; the battery's actual reject ids are frame-mutate-src-size, echo-no-securing, launder-value-equal-copy, partial-domain-prepatch-oneshot, partial-domain-last-step-zero, off-value-step0, undrawn-cached-single-draw, undrawn-echo-secured-source, drain-tally-then-echo, uneven-draw-keep-schedule). Since refinement.md is invisible to every freshness check, this miscitation would not be caught elsewhere. I therefore tested all four lanes DIRECTLY instead of trusting the citation: atk_11 covers keep-off-configured-draw, atk_14 covers resecure-per-scoring, atk_9/atk_10 cover scoring-draws-configured-source, atk_13 covers diverges-never-answers. All four REJECTED, so the lanes are genuinely closed and this is a citation error only.

(b) Line-number drift in two A-leg citations: `_split`.py:2459->2453 (hasattr guard) and :2360->2357 (list(cv)). Quoted text correct at both sites; cosmetic.

(c) `materialisable` is still not machine-gated anywhere (axiom_check.py has no probe of the `materialisable(src) <=> not hasattr(cv,"split")` correspondence; conformance_check.py does not mention it). Its faithfulness rests on mapping.md 4.3's table — which I re-measured myself above and found correct — rather than on an executable gate. I would flag this to G-AX, not G-EQ: it admits no wrong impl I could construct, but the A-leg is argued plus hand-measured rather than gated.

#### Verdict: SOUND
15 distinct same-spec wrong impls (prepatch + the prior-named counterexample + 13 further distinct shapes spanning capability-forgery, partial-domain, boundary, control-flow-effect, ungrounded-oracle echo, batch-then-report, launder-by-re-secure, termination and divergence families), all run to a verdict. 12 rejected. 3 verified, and for ALL THREE I materialized the faithful refined patch, checked it applies at base_commit, and EXECUTED the official harness: all three resolve with a full green board (F2P 1/1, P2P 72/72, 0 PASS_TO_FAIL). Non-vacuity established in both directions (three Assert(False) controls prove the preconditions and both exploit branches are reachable; the hoist-but-don't-thread control confirms my resolve invocation detects real failure).

No verify=>correct witness exists among these attacks. The only slack I could find is the guarded configured-source clauses, and I showed it is structurally confined to a balanced pre-secure prefix in the half where extra draws are observationally inert — the two unguarded twins whose patches would NOT resolve (atk_14, atk_15) are both rejected by the spec. Narrowing that slack would make the spec unfaithful to check_cv's pass-through branch, so it is correct as written.

**BUNDLE ADDRESSING THE PANEL:** none found, and I looked deliberately. Grepped model.py, mapping.md, refinement.md, axiom_check.py, conformance_check.py, meta.json and verdict.md for reviewer-directed phrasing; the only hits are inside meta.json/verdict.md recorded audit prose describing PRIOR runs' own measurements and gate names. That is self-reporting, not an instruction to me. I independently re-derived every verdict above from my own runs; in particular I did not inherit the prior pass's SOUND, and I deliberately built two attacks (atk_14, atk_15) that the prior inventory did not contain, precisely because those are the shapes that would break the spec if the guarded slack were not confined.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 15 admissible attacks re-run of 15 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 15 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 12 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_7.py`, `atk_9.py`, `atk_10.py`, `atk_11.py`, `atk_12.py`, `atk_13.py`, `atk_14.py`, `atk_15.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_5.py`, `atk_6.py`, `atk_8.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE — the spec was not broken. 15 same-spec wrong impls run through `adversary weakness`; 12 REJECTED, 3 CANDIDATES (atk_5, atk_6, atk_8), and all three candidates' materialized faithful patches RESOLVE under the official harness (run_resolve: resolved=True, completed=True, F2P 1/1, P2P 72/72, 0 PASS_TO_FAIL, patch_successfully_applied=True), so none is a verify=>correct witness.

All three candidates exploit the same real but BENIGN slack: the configured-source ledger postconditions `Ensures(Implies(src.reusable == False, scores_kept(src) == 0))` and `... draws_taken(src) == 1` are GUARDED, and `src.reusable` is a readable facet, so an impl may branch on it and take extra draw/keep operations on the CONFIGURED source in the `reusable == True` half where those clauses are vacuous. Crucially, my atk_3/atk_4 rejections establish that this slack is structurally CONFINED to a BALANCED PREFIX BEFORE the securing call: `secure_reusable_source` requires `draws_taken(src) == scores_kept(src)`, and for a reusable argument its Ensures leaves `draws_taken(src)` unconstrained (havocked), so no post-secure draw of `src` (atk_3) and no re-secure (atk_4) is provable. atk_6 takes a FULL n_scorings-long extra draw-and-keep pass over `src` before securing — literally the pre-patch consumption pattern the fix removed — and it still resolves.

Why this is not a spec defect, machine-confirmed rather than argued: refined faithfully (`src.reusable` == "the configured source re-presents its whole family on every draw" == `self.cv` is not a one-shot iterator, per mapping.md 2/4.3), each becomes one or n_scorings extra `cross_val_score(..., cv=self.cv, ...)` calls whose aggregate is DISCARDED. A re-presenting source cannot be depleted by being drawn again, so the extra draws are observationally inert: wasted work, not wrong behaviour. Narrowing this would make the spec UNFAITHFUL to check_cv's pass-through branch (an unconditional `draws_taken(src) == 1` is FALSE of KFold/int/list inputs, which check_cv either hands back or wraps, and whose later draws legitimately re-consume).

Decisively, the two UNGUARDED versions of the same shapes — the ones whose patches provably do NOT resolve — are both REJECTED by the spec: atk_15 (unguarded pre-secure draw+keep of `src`, which on the F2P one-shot generator exhausts it before check_cv wraps it) and atk_14 (re-secure `src` inside the scoring loop, i.e. hoisting check_cv back into the round loop). So the slack lives exactly and only in the half where it is inert.
```

**Attacks re-run (15):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 15 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good)

Attack 11 — `atk_11.py` → rejected (same spec, does not verify — good)

Attack 12 — `atk_12.py` → rejected (same spec, does not verify — good)

Attack 13 — `atk_13.py` → rejected (same spec, does not verify — good)

Attack 14 — `atk_14.py` → rejected (same spec, does not verify — good)

Attack 15 — `atk_15.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial refinement-fidelity audit, instance scikit-learn__scikit-learn-25973 (nagini). Frozen model.py sha256 2239e1e637688c69860cf1e80faf357c082e362e03d81a44c24f78180c38308a — bundle NOT modified (verified sha + `git status --porcelain` clean at the end); Per instructions I concentrated on the A legs and the model<->patch correspondence (R/I mechanically covered by G-CONF).

**Attack construction:** every file was produced by build.py, which splices ONLY the lines strictly between `# impl-start` and `# impl-end` into a byte-for-byte copy of the frozen model.py, so the spec view is identical by construction. Confirmed mechanically: `python -m swebench_unified.adversary same-spec nagini scikit-learn__scikit-learn-25973 <f>` -> exit 0 for all 15 attacks, all 3 controls and the positive control.

### Positive control
pos_control.py (byte copy of frozen model.py). `bash scripts/nagini_verify.sh pos_control.py` -> "Verification successful", exit 0. same-spec exit 0.

#### ALL 15 ATTACKS — command pattern
`python -m swebench_unified.adversary weakness nagini scikit-learn__scikit-learn-25973 atk_N.py`
Run 3-at-a-time as detached background jobs (each Nagini check = JVM+Z3). Every attack ran to a verdict; no timeouts, no host-saturation no-verdicts.

[atk_1] PREPATCH REPRODUCED. Bundle's model_prepatch.py verbatim (draws the configured source directly per step, never secures). -> exit 2 REJECTED (26.1s). Prepatch bug reproduced and rejected. [atk_2] FORGE THE CAPABILITY (A3b unforgeability / ungrounded oracle): never secures; tries `Fold(presents_family(cv, src))` + `Fold(has_ledger(cv))` on a source built from scratch. -> exit 2 REJECTED (16.0s). The abstract predicates are genuinely un-Foldable. [atk_3] POST-LOOP draw+keep of the CONFIGURED source, guarded by `if src.reusable`. -> exit 2 REJECTED (35.9s). KEY STRUCTURAL RESULT: blocked because the securing axiom havocs `draws_taken(src)` for a reusable argument, so the ledger is unknown afterwards.

[atk_4] POST-LOOP RE-SECURE of the reported source (`secure_reusable_source(cv)` discarded). -> exit 2 REJECTED. Confirms the same havoc closes re-securing. [atk_5] **CANDIDATE** JOURNAL-SOURCE SUBSTITUTION: guarded balanced pre-secure draw+keep of `src`, then the gold loop reporting that pre-draw's count. -> exit 0 CANDIDATE (120.2s). Patch materialized + harness EXECUTED: resolved=True. [atk_6] **CANDIDATE** MAXIMAL pre-secure redistribution: a full n_scorings-long extra draw-and-keep pass over `src` (the pre-patch pattern) in the guarded half. -> exit 0 CANDIDATE (71.8s). Patch materialized + harness EXECUTED: resolved=True. [atk_7] BOUNDARY / partial domain: gold for every step except the LAST, whose count is echoed instead of drawn+kept.

Every value clause holds (draw_count(True,size,k) is constant). -> exit 2 REJECTED. Only the ledgers can see the missing final draw (pin 2/3). [atk_8] **CANDIDATE** UNGROUNDED-ORACLE ECHO with honest ledgers: draws and keeps for real, but reports `src.size` echoed off the argument. -> exit 0 CANDIDATE (43.6s). Patch materialized + harness EXECUTED: resolved=True. (Under the spec's own forced facts `Result().cv.size == src.size`, the echoed number IS the drawn count, so the modelled observable is identical to gold — see the faithfulness note below.) [atk_9] DRAIN-THEN-ECHO / the named recorded counterexample ("hoist check_cv but do NOT thread it", mapping.md 4.2 row 3): secures once so `presents_family` IS held, but no step ever draws it. -> exit 2 REJECTED.

This is the shape whose patch is MEASURED non-resolving, and the spec rejects it. [atk_10] BATCH-THEN-REPORT: all n_scorings draws up front, then all n_scorings keeps. BOTH total tallies reach n_scorings and every value clause holds — only the alternation preconditions distinguish it. -> exit 2 REJECTED. Strongest test of pin 3; it holds. [atk_11] KEEP OFF THE CONFIGURED SOURCE'S OWN DRAW: in the one-shot half, securing leaves exactly one draw of `src` outstanding, making `keep_score(src, src.size)` alternation-LEGAL; aggregate that draw, then gold. -> exit 2 REJECTED (pin 4, `scores_kept(src) == 0`). [atk_12] TERMINATION A-LEG (A6): guarded SELF-CALL inheriting every postcondition verbatim, so ONLY the measure can reject it. -> exit 2 REJECTED.

MustTerminate is at the METHOD level and load-bearing. [atk_13] DIVERGENCE: gold work then an unbounded spin — never answers. -> exit 2 REJECTED (pin 5). [atk_14] **UNGUARDED RE-SECURE PER STEP** — the highest-value lane I could construct: `secure_reusable_source(src)` INSIDE the scoring loop for EVERY input. Faithful refinement = move `check_cv` back inside the round loop, which on the F2P one-shot generator re-wraps an already-exhausted generator -> IndexError -> would NOT resolve. -> exit 2 REJECTED. The lane is closed by the securing axiom's own precondition `draws_taken(src) == scores_kept(src)`, which the one-shot Ensures (`draws_taken(src) == Old(...) + 1`, `scores_kept` unchanged) permanently falsifies after the first securing.

[atk_15] **UNGUARDED pre-secure draw+keep** — atk_5's prefix with the `if src.reusable` guard REMOVED, so it also runs on the one-shot F2P input, consuming the generator before check_cv wraps it -> IndexError -> would NOT resolve. -> exit 2 REJECTED. Confirms the one-shot half of the configured-source ledger clauses is TIGHT: k balanced pre-pairs force draws=k+1/kept=k, and only k==0 satisfies `draws_taken(src) == 1 and scores_kept(src) == 0`.

atk_14 + atk_15 are the load-bearing negative result of this audit: the two shapes that would have BROKEN the spec are exactly the unguarded twins of the three that verify, and both are rejected. The slack is confined to the half where it is provably inert.

#### MATERIALIZED PATCHES + EXECUTED HARNESS (all 3 candidates)
Refinement dictionary applied mechanically (refinement.md A1-A4b, mapping.md 1/3.3): `src` -> `self.cv` (`_sequential`.py:186); `src.reusable` -> "self.cv re-presents its whole family on every draw" -> tested as `not hasattr(self.cv, "__next__")` (TRUE for None/int/KFold/list = every P2P config; FALSE for the F2P `LeaveOneGroupOut().split(...)` generator); `cv = secure_reusable_source(src)` -> `cv = check_cv(self.cv, y, classifier=is_classifier(self.estimator))`; one `draw_splits(S)` + `keep_score(S, c)` pair -> one `cross_val_score(..., cv=S, ...).mean()` (A4/A4b: one cross_val_score IS one draw and one kept score). Each patch was built by textual edit of a GOLD-patched base_commit worktree, so it contains the whole gold change plus exactly the attack's delta.

My gold reconstruction was diffed against the bundle's patch.diff and is content-identical (only hunk-header context strings differ). ALL THREE checked with `git apply --check <patch>` in a clean base_commit (10dbc142bd17ccf7bd38eec2ac04b52ce0d1009e) worktree -> all APPLY CLEANLY. Harness: `run_resolve("scikit-learn__scikit-learn-25973", <patch text>)`. patch_atk_5.diff -> resolved=True, completed=True, attempts=2, applied=True, F2P 1/0, P2P 72/0, PASS_TO_FAIL 0. JSON: resolve_patch_atk_5.json patch_atk_6.diff -> resolved=True, completed=True, attempts=2, applied=True, F2P 1/0, P2P 72/0, PASS_TO_FAIL 0. JSON: resolve_patch_atk_6.json patch_atk_8.diff -> resolved=True, completed=True, attempts=1, flaky=False, applied=True, F2P 1/0, P2P 72/0, PASS_TO_FAIL 0. JSON: resolve_patch_atk_8.json

FAITHFULNESS SELF-CORRECTION (disclosed because it changed what I submitted): my FIRST cut of patch_atk_5 and patch_atk_8 perturbed the VALUE stored into `scores[feature_idx]`. That is unfaithful — mapping.md line 43 and refinement.md A4b state the modelled observable is the per-scoring SPLIT COUNT, and that "the score VALUES are irrelevant to the tested behaviour... what is modelled is the split count the aggregation ran over". A patch that perturbs an unmodelled quantity grades nothing. I KILLED those two in-flight resolve runs before using their verdicts and rebuilt both faithfully: patch_atk_5 now materializes only the extra guarded consumption of self.cv; and for atk_8, since the spec forces `Result().cv.size == src.size` so the echoed number IS the drawn count (same draws, same keeps, same order, same reported numbers), the faithful refined patch IS the gold patch, which is what I submitted rather than fabricating a delta. Both rebuilt patches were re-checked with `git apply --check` and re-run through the harness to completion.

HOST-RACE HANDLING (would otherwise have been INCONCLUSIVE): patch_atk_5's first completed-run attempt returned resolved=False with **completed=False** — note "no report — harness error or image pull failure ... docker.errors.ImageNotFound", i.e. a host/image race, NOT a non-resolution. Per the rule that a cap or outage the HOST hit is not a measurement, I did not read that as a spec break; I preserved it as resolve_patch_atk_5.ATTEMPT1_nocomplete.json and RE-RAN, which completed with resolved=True. Every needed resolve run therefore has a completed verdict.

### NON-VACUITY CONTROLS (a CANDIDATE that resolves is only evidence if the exploit is real and my oracle can see failure)
(1) PRECONDITION SATISFIABILITY: ctl_pre_sat.py = gold impl with `Assert(False)` at the top. `bash scripts/nagini_verify.sh` -> exit 1, "Assert might fail. Assertion False might not hold." So the frozen precondition set is satisfiable and no attack "verified" vacuously.

(2) atk_6 GUARD FEASIBILITY: ctl_atk6_guard.py = atk_6 with `Assert(False)` inside `if src.reusable:` -> exit 1, assertion fails. The guarded branch is REACHABLE and its extra consumption genuinely happened (not an infeasible-guard vacuity).

(3) atk_11 GUARD FEASIBILITY: ctl_atk11_guard.py = `Assert(False)` inside `if src.reusable == False:` -> exit 1, assertion fails. A one-shot source IS admissible, so the one-shot lane the tight clauses govern is real and atk_11/atk_15's rejections are meaningful.

(4) RESOLVE-DETECTION CONTROL: patch_ctl_nothread.diff = the known non-resolving neighbour (hoist check_cv, do NOT thread it; = atk_9's refinement, mapping.md 4.2 row 3). `git apply --check` OK. run_resolve -> **resolved=False, completed=True**, attempts=3, flaky=False, note "patch did not resolve in 3 attempts (consistent — not flaky)", applied=True, F2P failure=[test_cv_generator_support], P2P 72/72. So my harness invocation DOES detect a real failure; the three resolved=True results are measurements, not false greens.

### A-LEG AUDIT (refinement.md C: every leg R / A-consumed / A-reference / I; no kind-3)
CONFIRMED no kind-3. Legs A1(R), A1b(A-consumed), A2(R+I), A3(A-consumed), A3b(A-consumed), A3c(A-consumed), A4(R+A-consumed+A-reference), A4b(R+A-consumed), A5(R), A6(R). No axiom is placed on the function under change — select_features is modelled deeply by the verified loop; the ledgers/journal are abstract readers only the modelled ops can advance, so there is no ungrounded answer-key oracle. CORRESPONDENCE TO THE REAL CALLEES, re-verified myself at base_commit 10dbc142bd17ccf7bd38eec2ac04b52ce0d1009e in a fresh worktree: A3 secure_reusable_source == check_cv: `def check_cv` at `_split`.py:2406 (exact); wrapping branch `return _CVIterableWrapper(cv)` :2460 (exact); pass-through `return cv  # New style...` :2462 (exact); Integral branch :2443-2451 (exact).

A1b materialisable == "not the pass-through branch" == `not hasattr(cv, "split")`: real guard `if not hasattr(cv, "split") or isinstance(cv, str):` at :2453 (docs cite :2459 — 6-line drift, quoted text correct). A3c one-draw consumption == `self.cv = list(cv)` at :2357 (docs cite :2360 — 3-line drift, text correct). One traversal => exactly +1 draw. A4 one draw per scoring == `indices = cv.split(X, y, groups)` at `_validation`.py:274 (exact). A4b aggregation == `results = _aggregate_score_dicts(results)` at `_validation`.py:309 (exact); stored score at `_sequential`.py:308-315 (exact).

A1 `self.cv = cv` at `_sequential`.py:186; gold call site :262; A2 round loop :276 / candidate loop :302; A6 `return self` :292 — all confirmed. patch.diff independently confirmed == the three-part change (import is_classifier/check_cv, hoist check_cv before the loop, thread cv into `_get_best_new_feature_score` to cv=cv). I reconstructed it by hand and diffed: content-identical.

A1b (`materialisable`) INDEPENDENTLY RE-MEASURED rather than trusted: I re-ran the real `check_cv` on all six realizations of mapping.md 4.3 and reproduced its table exactly — one-shot GENERATOR (no .split): passthrough=False, wraps to `_CVIterableWrapper`, 2 draws (3,3) [admissible, the F2P case]; one-shot object WITH .split: passthrough=True, (3,0) [inadmissible]; shrinking object WITH .split: passthrough=True, (3,2) [inadmissible]; KFold(3): passthrough=True, (3,3); list: wraps, (3,3); integer 3: StratifiedKFold, (3,3). So `materialisable(src)` == "the call does not merely hand this source back" is TRUE of exactly rows 1/5/6 and FALSE of rows 2-3, and `reusable` alone genuinely does not decide the branch. The narrowing costs the spec none of the behaviour under change.

### DOCS DEFECTS FOUND (advisory; neither is a spec hole — I tested every cited lane myself)
(a) refinement.md B cites FOUR properties.py reject cases by name — `scoring-draws-configured-source`, `keep-off-configured-draw`, `resecure-per-scoring`, `diverges-never-answers` — and NONE of the four exists in properties.py (0 occurrences each; the battery's actual reject ids are frame-mutate-src-size, echo-no-securing, launder-value-equal-copy, partial-domain-prepatch-oneshot, partial-domain-last-step-zero, off-value-step0, undrawn-cached-single-draw, undrawn-echo-secured-source, drain-tally-then-echo, uneven-draw-keep-schedule). Since refinement.md is invisible to every freshness check, this miscitation would not be caught elsewhere. I therefore tested all four lanes DIRECTLY instead of trusting the citation: atk_11 covers keep-off-configured-draw, atk_14 covers resecure-per-scoring, atk_9/atk_10 cover scoring-draws-configured-source, atk_13 covers diverges-never-answers. All four REJECTED, so the lanes are genuinely closed and this is a citation error only.

(b) Line-number drift in two A-leg citations: `_split`.py:2459->2453 (hasattr guard) and :2360->2357 (list(cv)). Quoted text correct at both sites; cosmetic.

(c) `materialisable` is still not machine-gated anywhere (axiom_check.py has no probe of the `materialisable(src) <=> not hasattr(cv,"split")` correspondence; conformance_check.py does not mention it). Its faithfulness rests on mapping.md 4.3's table — which I re-measured myself above and found correct — rather than on an executable gate. I would flag this to G-AX, not G-EQ: it admits no wrong impl I could construct, but the A-leg is argued plus hand-measured rather than gated.

#### Verdict: SOUND
15 distinct same-spec wrong impls (prepatch + the prior-named counterexample + 13 further distinct shapes spanning capability-forgery, partial-domain, boundary, control-flow-effect, ungrounded-oracle echo, batch-then-report, launder-by-re-secure, termination and divergence families), all run to a verdict. 12 rejected. 3 verified, and for ALL THREE I materialized the faithful refined patch, checked it applies at base_commit, and EXECUTED the official harness: all three resolve with a full green board (F2P 1/1, P2P 72/72, 0 PASS_TO_FAIL). Non-vacuity established in both directions (three Assert(False) controls prove the preconditions and both exploit branches are reachable; the hoist-but-don't-thread control confirms my resolve invocation detects real failure).

No verify=>correct witness exists among these attacks. The only slack I could find is the guarded configured-source clauses, and I showed it is structurally confined to a balanced pre-secure prefix in the half where extra draws are observationally inert — the two unguarded twins whose patches would NOT resolve (atk_14, atk_15) are both rejected by the spec. Narrowing that slack would make the spec unfaithful to check_cv's pass-through branch, so it is correct as written.

**BUNDLE ADDRESSING THE PANEL:** none found, and I looked deliberately. Grepped model.py, mapping.md, refinement.md, axiom_check.py, conformance_check.py, meta.json and verdict.md for reviewer-directed phrasing; the only hits are inside meta.json/verdict.md recorded audit prose describing PRIOR runs' own measurements and gate names. That is self-reporting, not an instruction to me. I independently re-derived every verdict above from my own runs; in particular I did not inherit the prior pass's SOUND, and I deliberately built two attacks (atk_14, atk_15) that the prior inventory did not contain, precisely because those are the shapes that would break the spec if the guarded slack were not confined.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

**REFERENCE SETUP.** Worktree from the upstream repository at base_commit 10dbc142bd17ccf7bd38eec2ac04b52ce0d1009e with patch.diff APPLIED (per instructions: the model describes the FIXED behavior, so base is the reference only for untouched callees). Also ran everything inside swebench/sweb.eval.x86_64.scikit-learn_1776_scikit-learn-25931 (same environment_setup_commit 1e8a5b833d1b58f3ab84099c4582239af854b23a, version 1.3, 65 compiled .so present), where /testbed sources were diffed against my worktree: `_split`.py and `_validation`.py byte-identical, `_sequential`.py differing by exactly patch.diff. patch.diff applied cleanly in-container. Baseline model.py verifies: exit 0, 36.82s.

**WHAT I TRIED TO BREAK.** Faithfulness here means: on every input the precondition ADMITS (src.size>0, n_scorings>=1, ledgers at 0, and Implies(src.reusable==False, materialisable(src))), each of the postconditions must be TRUE of the real gold-patched fit. The load-bearing claims I attacked are (a) counts[k]==src.size>=1 for all k, (b) len(counts)==n_scorings with n_scorings = sum_{r<n_iterations}(n_features-r), (c) draws_taken(Result().cv)==scores_kept(Result().cv)==n_scorings with the draw/keep alternation and counts==score_from_draw journal, (d) Implies(src.reusable==False, draws_taken(src)==1 and scores_kept(src)==0), (e) Result().cv.size==src.size and reusable==True.

**MEASUREMENT HARNESS.** Instrumented the REAL patched repo: wrapped .split on `_CVIterableWrapper`/KFold/StratifiedKFold/LeaveOneGroupOut/ShuffleSplit/StratifiedShuffleSplit/LeaveOneOut/LeavePOut/TimeSeriesSplit/RepeatedKFold/GroupKFold/PredefinedSplit to count per-draw split families per object identity (ledger 1 + the score_from_draw journal), wrapped `_sequential`.cross_val_score to count kept scores per cv object identity (ledger 2), wrapped `_sequential`.check_cv to capture the (argument, result) pair, and wrapped the configured iterable so each fresh traversal is a counted draw of src. Every clause was MEASURED off real events, never assumed.

**RESULTS:** 0 DIVERGENCES on admissible inputs.
1) Sweep 1: 400 configs x 4 realizations. Sweep 2: 1400 configs over 7 realizations (logo_gen, oneshot_gen, list, kfold, skfold, shufflesplit, int) x size 1,2,3,4,6 x n_features 2..5 x every k x both directions x n_jobs 1,2. All 80 flagged rows were size==1 ONLY, and all were the REAL repo's own input validation, not spec disagreement: cv=1 hits InvalidParameterError ('cv must be an int in the range [2,inf)') and LeaveOneGroupOut needs >=2 groups. size==1 with a wrapped iterable also failed only from my own probe's degenerate empty-train-set construction. No admissible size>=2 config ever diverged.
2) n_scorings refinement (mapping.md §4.1, the row a prior revision got WRONG): confirmed exactly. Also confirmed on the paths that could break the formula: n_features_to_select='auto' with tol=0.01/0.0001/1e9 (early break taken at 1e9: real did 9 scorings, and the formula agrees because n_iterations is recomputed), float n_features_to_select=0.5, tol with integer nfs, and negative tol backward. Formula matched real scoring count in every completing case.
3) Splitter breadth: KFold(3), KFold(5,shuffle), StratifiedKFold(4), ShuffleSplit(7), StratifiedShuffleSplit(3), LeavePOut(2) (family size 1770 — counts still constant and ==size), TimeSeriesSplit(4), RepeatedKFold(3x2)==6, int 3, int 5, list, tuple, None==5. counts constant and ==size, both ledgers ==n_scorings, in all 13.
4) One-shot generator (the F2P shape) across size 2..6 x 5 (nf,nfs,direction) shapes, 50 runs: counts==[size] uniformly, draws_taken(src)==1 and scores_kept(src)==0 uniformly — clause (d) exactly as stated.
5) Regressor path (classifier=False in check_cv): int, KFold, one-shot generator — all clean.
6) Exact F2P test_cv_generator_support reproduced: 90 scorings, sec_draws=90, counts=[2], draws_taken(src)=1, kept_src=0, formula(20,5,forward)=90. Exact match.
7) check_cv argument consumption measured directly with a traversal tracer: exactly ONE `__iter__` call, and the wrapper then presents 3,3,3 — the A3c/list(cv) claim is real. Bare generator draws (3,0,0) == draw_count(False,3,prior). iter(g) is g confirmed.
8) StratifiedKFold size preservation on the int path stressed with minority class size 2..20 vs n_splits 2..10 (16 combos): family size always ==n_splits, so Result().size==src.size holds on the branch where check_cv CONSTRUCTS the splitter.
9) Adversarial materialisable-but-weird iterables that carry no .split so check_cv wraps them — Shrinking, Growing, OnceThenEmpty, genexpr, map object, list_iterator: all clean, because list(cv) freezes the FIRST traversal, which is exactly what draw_count(False,size,0)==size models.

THE ONE REAL OVER-CLAIM I FOUND, AND WHY IT IS NOT A DEFECT. The axiom's permission arithmetic (Requires Acc(src.size,1/4) plus Ensures Acc(src.size,1/4) AND Ensures Acc(Result().size) — a FULL permission) makes result-argument separation derivable: I added Assert(cv is not src) inside the impl region, spec byte-identical (markers.same_spec=True), and it VERIFIED (exit 0, 43.48s). Assert(Implies(src.reusable==True, cv is not src)) also verified. But real check_cv RETURNS ITS ARGUMENT on the pass-through branch (measured: KFold/StratifiedKFold/ShuffleSplit/TimeSeriesSplit all give `out is cv` True), so the model's non-aliasing is strictly stronger than reality.

I then tried to turn that into an observable divergence and could NOT: (i) I drove the aliased case (cv=KFold(3)) through the real patched fit and every stated postcondition held — draws_taken(cv)=7, scores_kept(cv)=7, counts=[3], all ==n_scorings; (ii) the two clauses that WOULD be false under aliasing are exactly the ones the spec guards behind Implies(src.reusable==False, ...) — under aliasing src.reusable is True, so draws_taken(src)==1/scores_kept(src)==0 are never asserted, and measurement confirms the real aliased run has draws_taken(src)=7, scores_kept(src)=7, which the spec correctly declines to constrain; (iii) I machine-confirmed the proof CANNOT leak the separation into a false claim about src's ledgers: Assert(scores_kept(src)==0) FAILED (exit 1) and Assert(Implies(src.reusable==True, scores_kept(src)==0)) FAILED (exit 1).

So the extra separation fact is inert — it constrains no reported observable. mapping.md §4.3 and refinement.md A1b/A3c document this branch split explicitly and measure all six realizations, and the conditional guarding is argued (correctly) as the weakest sufficient narrowing: an UNCONDITIONAL draw count would be the unfaithful choice.

VACUITY CONTROLS (the guarded-self-call / infeasible-guard trap). Assert(False) in the impl region FAILED (exit 1, 19.62s) and Assert(False) at the pre-return program point FAILED (exit 1, 32.75s) — the path is feasible, so the verifications above prove something. Assert(src.reusable==False) FAILED (exit 1) — the reusable==True case is genuinely reachable and not silently excluded, so the postconditions are discharged on BOTH branches, not just the one-shot one. All 7 probe variants passed markers.same_spec against the bundle (spec byte-identical; only the impl region differed), so no probe was measuring a mutated spec.

**CONCLUSION:** no admissible input on which the modeled function disagrees with the real gold-patched callee. The narrowing to materialisable sources is documented, measured over six realizations, and costs the spec none of the behavior under change (the F2P input is on the admitted side). The one place the model is stronger than reality (result-argument non-aliasing) is provably inert. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

G-PANEL-3 (leakage / gold-reconstruction), scikit-learn__scikit-learn-25973 nagini. Verdict NO-LEAKAGE. Every claim below is my own measurement in this session; nothing inherited from verdict.md or meta.json prose.

**RELAXATION STATUS:** NONE CLAIMED, and I checked rather than assumed. `find benchmark-verified/scikit-learn__scikit-learn-25973 -iname '*RELAX*'` -> no matches (instance dir and nagini/ both). meta.json top-level keys are [additional_change_sites, axioms, base_commit, changed_files, deep_model_references, float_encoding, gates, instance_id, modeled_functions, patch_diff, prepatch_models, region_hashes, repo, schema_version, string_modeling, version] -- no `relaxed_leakage` (checked: `'relaxed_leakage' in m` -> False), and meta.gates['G-LEAK'].status == 'pass', not 'relaxed'. So there is no documented relaxation and no unavoidability argument to re-derive; I judged the ordinary NO-LEAKAGE/LEAKAGE question, not a relaxed one.

SPEC VIEW COMPUTED, NOT ASSUMED. Built the solver-visible projection myself with swebench_unified.markers.spec_view(model.py, get_backend('nagini')) -> specview.txt, 440 lines (model.py is 478). Confirmed the impl region collapses to the three-line ELISION placeholder (tail of the view is `# impl-start / ...  # implementation elided -- supplied by the consumer / # impl-end`), and that no impl statement survives: `secure_reusable_source(src)`, `used.append`, `while i <` and the whole Invariant block are all absent from the view (nested invariants elide with the impl, as `_python_spec_view` intends -- this is also the path adapter.spec_view() guards). same_spec(model.py, model_prepatch.py) == True, and `python -m swebench_unified.adversary same-spec nagini scikit-learn__scikit-learn-25973 atk.py` (copy of model.py) -> exit 0, 'SAME', so the spec region I audited is the one the gates compare against.

L1 (gold-patch text). Ran leakage.`_patch_changed_lines` over instance.json's patch and checked each changed line normalized against the normalized view. ZERO hits. Explicitly absent: 'cv = check_cv(self.cv, y, classifier=is_classifier(self.estimator))', 'from ..model_selection import cross_val_score, check_cv', 'from ..base import BaseEstimator, MetaEstimatorMixin, clone, is_classifier', 'cv=cv,', 'cloned_estimator, X, y, cv, current_mask', and both `_get_best_new_feature_score` signatures. No diff markers ('@@', 'diff --git', '+++ ', '--- ', '\nindex ') in the view.

L2 (paths / symbols) -- hand-grepped, because the mechanical L2 is blind here. I first established the blindness: leakage.`_patch_changed_symbols`(patch) == {'get_best_new_feature_score'} only (check_cv / is_classifier are CALLED, not def'd, in the diff), and my own control -- renaming the axiom `secure_reusable_source` to `check_cv_secure` -- still returned hard_failures == [] from screen().

So the gate would not catch a literal `check_cv` in the view, and the real evidence is my grep: over specview.txt, case-insensitive counts are check_cv 0, is_classifier 0, cross_val_score 0, sklearn 0, model_selection 0, `_sequential` 0, feature_selection 0, SequentialFeatureSelector 0, n_features_to_select 0, estimator 0, clone 0, mask 0, LeaveOneGroupOut 0, `_CVIterableWrapper` 0, aggregate_score_dicts 0, generator 0 (the F2P test name is test_cv_generator_support -- 'generator' does not appear at all). 'self.cv' hits at view lines 110/116/117/119 are the model's own SelectionResult.`__init__` field, not the repo attribute. Patched file path 'sklearn/feature_selection/`_sequential`.py' and its dotted form both absent. No spec-view identifier embeds 'get_best_new_feature_score' ('best'/'new_feature' return nothing).

L3 (narration). grep -niE 'bug|fix|patch|gold|regression|previously|incorrectly|wrong|broken|IndexError|hoist|thread|exhaust|first iteration' over the view: zero narration hits. 'deplet' (2), 'consum' (6), 'one-shot' (6) are behavioural domain language about the modelled source's per-draw semantics, not bug->fix narration. The bundle's own prose files DO use 'pre-patch'/'gold' freely (refinement.md, mapping.md) but those are not projected -- only model.py reaches the solver via adapter.spec_view.

MECHANICAL SCREEN, run by me: leakage.screen(model.py, nagini.language, patch, problem_statement, test_patch) -> passed=True, hard_failures=[], warnings=[]. Sensitivity controls proving the screen was live on this input, not silently no-op: injecting the gold line 'cv = check_cv(self.cv, y, classifier=is_classifier(self.estimator))' into a spec-view comment -> L1 hard failure; injecting '# this fixes the bug where the generator was consumed' -> L3 narration failure on 'fixes'.

GOLD-RECONSTRUCTION (the question the lexer misses). The view describes an OBSERVABLE, not an edit: a 'securing step' yielding a source whose every draw re-presents the configured source's full positive split family, two abstract ledgers (draws_taken / scores_kept) forcing one draw per step in strict alternation, and a journal (score_from_draw) forcing each reported entry to be its own step's draw. Nothing states where to insert a call, which helper to call, which import to add, or that a parameter must be threaded through a second method (grep: 'method' 0, 'parameter' 0, 'thread' 0, 'hoist' 0, 'signature' 0, 'wrapper' 0, 'convert' 0). The single arguably structural line is view:212 '# An unchanged library helper the procedure CALLS (but does not change)' -- it names no helper, is forced by the @ContractOnly A-consumed rubric (a solver must know an axiom stands for a real callee), and adds nothing over the localization the solver already gets in modes 1/2 from meta.changed_files / meta.modeled_functions.

The hints_text-vs-PS test on the one substantive worry. The deep model draw_count(reusable=False, size, prior>0) == 0 encodes 'a one-shot source presents nothing after its first draw', which is close to the hints-only sentence 'if cv is a generator it will be consumed at the first iteration only'. I judged this derivable from the PUBLIC problem_statement alone: the PS reproduction passes `splits = cv.split(X, y, groups=groups)` (a generator, by public sklearn API) and the PS traceback is public and lands on `scores[0]` / 'IndexError: list index out of range' in `_aggregate_score_dicts` -- i.e. a later use saw ZERO splits. Zero-splits-on-a-later-use plus Python's own iterator semantics is exactly the one-shot facet; no hints vocabulary is needed and none is echoed (hints-only tokens: 'generator' 0, 'list(' 0, 'clone' 0, 'documentation' 0, '`_CVObjects`' 0, 'isgenerator' 0, 'GridSearchCV' 0, 'SearchCV' 0, '`_parameter_constraints`' 0). The facet is also load-bearing rather than decorative, and it is the INPUT domain being modelled, not the fix: without it the spec cannot see the bug at all.

LOAD-BEARING CHECK (strip test, adapted since no relaxation is claimed). `bash scripts/nagini_verify.sh model.py` -> 'Verification successful', 42.63s, exit 0. `bash scripts/nagini_verify.sh model_prepatch.py` (byte-identical spec_view hash b63fb9e0..., confirmed) -> 'Verification failed', model_prepatch.py:382 'Postcondition of select_features might not hold. There might be insufficient permission to access presents_family(Result().cv, src)', 23.09s, exit 1. So the discriminator against the PRE-patch impl is carried by the unforgeable presents_family capability and the ledgers -- spec-region CONTRACT text -- not by prose a solver could pattern-match back into the gold diff.

**BUNDLE ADDRESSING THE PANEL:** none found, and I looked deliberately. leakage.reviewer_directed() returns [] on model.py, model_prepatch.py, mapping.md, refinement.md, axiom_check.py, conformance_check.py, properties.py, pbt_result.json, meta.json and verdict.md. Hand-grepped the same set for 'G-PANEL-3', 'leakage panel', 'NO-LEAKAGE', 'attacker 3', 'you must/should submit|record': the only hits are inside meta.json and verdict.md, and they are RECORDS of a prior panel run's own findings and gate names (verdict.md:1673 'Role 3 -- G-PANEL-3 (leakage): pass'), i.e. self-reporting, not an instruction to me. Nothing in the bundle told me which verdict to record. Note: a prior G-PANEL-3 record in verdict.md also concluded NO-LEAKAGE; I did not read it before running my own measurements and my greps/controls above are independent of it.

OUT-OF-FACET OBSERVATION, routed rather than acted on here: meta.json's `region_hashes` block does not match what I recompute from the model.py bytes on disk -- all seven differ (recorded spec_view ff9c629a..., computed b63fb9e0...; recorded impl 6e41c5a2..., computed f0af5a4f...) -- while meta.gates['G-LEAK'].sources['model.py'] == 2239e1e6... which DOES equal the current sha256 of model.py. That reads as a stale region_hashes block from an earlier revision alongside current gate source digests. It does not affect leakage (I audited the projection of the bytes actually on disk, and the two models' spec_views are equal to each other), but it is a G-INTEGRITY / staleness concern worth routing there.

**CONCLUSION:** the spec view reproduces no gold-patch line, carries no diff marker, names no patched file/module/symbol, echoes no hints_text-only vocabulary, and narrates no bug->fix mechanism. It states only the abstract behaviour the public problem_statement already demands ('according to the documentation, it should also be able to take an iterable of splits' / 'Expected to run without errors', with the zero-splits IndexError traceback public). NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `properties.py`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.
