# P2 adversarial audit — sphinx-doc__sphinx-10323

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 22 admissible attacks re-run of 22 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 22 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 20 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py`, `atk_9.py`, `atk_10.py`, `atk_11b.py`, `atk_11c.py`, `atk_12.py`, `atk_13.py`, `atk_14.py`, `atk_15.py`, `atk_16.py`, `atk_18.py`, `atk_20.py`, `model_prepatch.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_17.py`, `atk_19.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NO SURVIVING COUNTEREXAMPLE. 21 same-spec wrong impls + the prepatch bug were run through `adversary weakness`; 19 were REJECTED by the spec, and the only 2 CANDIDATES (verify + same-spec) had their faithful refined patches materialized and EXECUTED through the official harness -- both RESOLVED, so neither breaks verify=>correct.

MOST IMPORTANT RESULT -- the prior pass's counterexample is CLOSED. verdict.md Role 1 recorded BROKEN on a PARTIAL-DOMAIN hole: the then-frozen spec had Requires(n >= 1) AND Requires(len(lead) >= 1) AND Requires(len(trail) >= 1), which made the absent-author-line regime unreachable, so an impl could make the ENTIRE trim stage contingent on an author line being present, verify, and still fail the dedent-only P2P tests (test_LiteralIncludeReader_dedent, test_LiteralIncludeReader_tabwidth_dedent, which set `dedent` and set NEITHER `prepend` NOR `append`). I re-encoded that exact impl as atk_1.py (guard `len(lead) == 0 or len(trail) == 0` -> trim-free return) and the one-sided variant as atk_2.py (guard `len(lead) == 0`).

BOTH ARE NOW REJECTED:
  atk_1.py -> exit 2, `atk_1.py:111:13: error: Postcondition of assemble might not hold. Assertion (Result() == ((emit(lead) + trim_block(included, n)) + emit(trail))) might not hold.`
  atk_2.py -> exit 2, same postcondition failure.

The repair is real and I proved the mechanism rather than reading it: the current spec's precondition is only `Requires(n >= 0)` + `Requires(MustTerminate(2))` and demands NOTHING of lead/trail, and the @Pure helper `emit` models the author-line presence rule (empty option -> no line) instead of excluding it. DEADNESS CONTROLS confirm the formerly-dead regions are now LIVE -- I replaced each guarded branch body with `Assert(False)` and every one FAILED, i.e. the branch is reachable and constrained:
  ctl_dead_lead0.py    (`if len(lead) == 0: Assert(False)`)                  -> FAILED: `Assert might fail. Assertion False might not hold.`
  ctl_dead_noauthor.py (`if len(lead) == 0 or len(trail) == 0: Assert(False)`) -> FAILED (same)
  ctl_dead_n0.py       (`if n == 0: Assert(False)`)                          -> FAILED (same)
  ctl_dead_inc0.py     (`if len(included) == 0: Assert(False)`)              -> FAILED (same)
and the meta-control ctl_live_true.py (`if n >= 0: Assert(False)`) also FAILED, proving the Assert(False) probe discriminates reachability rather than always failing. Contrast the prior audit, where ctl_dead_lead0 VERIFIED. Per my memory note `nagini-guarded-selfcall-can-go-vacuous`, Assert(False) is the right control and it is doing its job here.

The two CANDIDATES are both BENIGN, and I did not speculate -- I ran them:
  atk_17.py (`if n < 0: return included`): verifies (14.1s) ONLY because n<0 is excluded by the sole remaining domain restriction Requires(n >= 0). Faithful refinement = a read() pipeline that drops dedent/prepend/append when options['dedent'] < 0. That branch is UNREACHABLE from any real document because `optional_int` (sphinx/directives/__init__.py:36) raises ValueError('negative value; must be positive or zero') on a negative dedent, so the domain restriction is harmless. EXECUTED: run_resolve run_id sbu-eqaudit-s79o-atk_17 -> resolved=TRUE, completed=True, attempts=1, flaky=False.
  atk_19.py (A-reference echo: substitutes the deep model term `trim_block(included, n)` for the hand-rolled per-line fold): verifies (13.6s), but it is extensionally the gold value, and by the A2 A-reference leg (G-AX: trim_block == dedent_lines per line) its real-code counterpart IS a dedent_filter call in the gold position, i.e. its faithful patch is the gold reorder. EXECUTED: run_id sbu-eqaudit-s79o-atk_19 -> resolved=TRUE, completed=True, attempts=1, flaky=False. So the A-reference is load-bearing, not a place to hide a wrong impl.

GOLD CONTROL certified FIRST, in the same session: run_id sbu-eqaudit-s79o-gold -> resolved=TRUE, completed=True, attempts=1, flaky=False. All THREE resolve runs were executed STRICTLY ONE AT A TIME on this single instance -- no ImageNotFound, every run completed=True -- so the three TRUE verdicts are about the patches, not the environment.
```

**Attacks re-run (22):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -137,6 +137,8 @@
         [[Result()[i]]]))))
     # post-conditions-end
     # impl-start
+    if len(lead) == 0 or len(trail) == 0:
+        return (emit(lead) + included) + emit(trail)
     # Margin trim first — over the included text only, and unconditionally.
     # Build the trimmed block by a backward fold matching `trim_block`.
     trimmed = PSeq()  # type: PSeq[PSeq[int]]
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -137,6 +137,8 @@
         [[Result()[i]]]))))
     # post-conditions-end
     # impl-start
+    if len(lead) == 0:
+        return included + emit(trail)
     # Margin trim first — over the included text only, and unconditionally.
     # Build the trimmed block by a backward fold matching `trim_block`.
     trimmed = PSeq()  # type: PSeq[PSeq[int]]
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -137,6 +137,8 @@
         [[Result()[i]]]))))
     # post-conditions-end
     # impl-start
+    if n == 0:
+        return (emit(lead) + trim_block(included, 1)) + emit(trail)
     # Margin trim first — over the included text only, and unconditionally.
     # Build the trimmed block by a backward fold matching `trim_block`.
     trimmed = PSeq()  # type: PSeq[PSeq[int]]
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -137,6 +137,8 @@
         [[Result()[i]]]))))
     # post-conditions-end
     # impl-start
+    if len(lead) == 0 or len(trail) == 0:
+        return (PSeq(lead) + trim_block(included, n)) + PSeq(trail)
     # Margin trim first — over the included text only, and unconditionally.
     # Build the trimmed block by a backward fold matching `trim_block`.
     trimmed = PSeq()  # type: PSeq[PSeq[int]]
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -137,51 +137,5 @@
         [[Result()[i]]]))))
     # post-conditions-end
     # impl-start
-    # Margin trim first — over the included text only, and unconditionally.
-    # Build the trimmed block by a backward fold matching `trim_block`.
-    trimmed = PSeq()  # type: PSeq[PSeq[int]]
-    i = len(included)
-    while i > 0:
-        # invariants-start
-        Invariant(0 <= i and i <= len(included))
-        Invariant(trimmed == trim_block(included.drop(i), n))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure i, discharging
-        # MustTerminate(2) from the precondition.
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        Assert(included.drop(i - 1)[0] == included[i - 1])
-        Assert(included.drop(i - 1).drop(1) == included.drop(i))
-        trimmed = PSeq(included[i - 1].drop(n)) + trimmed
-        i = i - 1
-    Assert(trimmed == trim_block(included, n))
-    Assert(len(trimmed) == len(included))
-    # Then the leading and the trailing line, each emitted VERBATIM (untrimmed)
-    # and only when it has content.
-    result = (emit(lead) + trimmed) + emit(trail)  # type: PSeq[PSeq[int]]
-    # Discharge the per-included-line characterization of the trim via the
-    # lemma, index by index, in both author-line regimes.
-    j = 0
-    while j < len(included):
-        # invariants-start
-        Invariant(0 <= j and j <= len(included))
-        Invariant(result == (emit(lead) + trim_block(included, n)) + emit(trail))
-        Invariant(len(trim_block(included, n)) == len(included))
-        Invariant(Implies(len(lead) >= 1, Forall(int, lambda k: (
-            Implies(0 <= k and k < j, result[k + 1] == included[k].drop(n)),
-            [[result[k + 1]]]))))
-        Invariant(Implies(len(lead) == 0, Forall(int, lambda k: (
-            Implies(0 <= k and k < j, result[k] == included[k].drop(n)),
-            [[result[k]]]))))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure len(included) - j,
-        # discharging MustTerminate(2) from the precondition.
-        Invariant(MustTerminate(len(included) - j + 1))
-        # invariants-end
-        Assert(trim_block_at(included, n, j))
-        Assert(trim_block(included, n)[j] == included[j].drop(n))
-        Assert(len(emit(lead)) == 0 or len(emit(lead)) == 1)
-        Assert(result[len(emit(lead)) + j] == trim_block(included, n)[j])
-        j = j + 1
-    return result
+    return (emit(lead) + trim_block(included, n)) + emit(trail)
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -137,51 +137,15 @@
         [[Result()[i]]]))))
     # post-conditions-end
     # impl-start
-    # Margin trim first — over the included text only, and unconditionally.
-    # Build the trimmed block by a backward fold matching `trim_block`.
     trimmed = PSeq()  # type: PSeq[PSeq[int]]
-    i = len(included)
-    while i > 0:
+    i = 0
+    while i < len(included):
         # invariants-start
         Invariant(0 <= i and i <= len(included))
-        Invariant(trimmed == trim_block(included.drop(i), n))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure i, discharging
-        # MustTerminate(2) from the precondition.
-        Invariant(MustTerminate(i + 1))
+        Invariant(len(trimmed) == i)
+        Invariant(MustTerminate(len(included) - i + 1))
         # invariants-end
-        Assert(included.drop(i - 1)[0] == included[i - 1])
-        Assert(included.drop(i - 1).drop(1) == included.drop(i))
-        trimmed = PSeq(included[i - 1].drop(n)) + trimmed
-        i = i - 1
-    Assert(trimmed == trim_block(included, n))
-    Assert(len(trimmed) == len(included))
-    # Then the leading and the trailing line, each emitted VERBATIM (untrimmed)
-    # and only when it has content.
-    result = (emit(lead) + trimmed) + emit(trail)  # type: PSeq[PSeq[int]]
-    # Discharge the per-included-line characterization of the trim via the
-    # lemma, index by index, in both author-line regimes.
-    j = 0
-    while j < len(included):
-        # invariants-start
-        Invariant(0 <= j and j <= len(included))
-        Invariant(result == (emit(lead) + trim_block(included, n)) + emit(trail))
-        Invariant(len(trim_block(included, n)) == len(included))
-        Invariant(Implies(len(lead) >= 1, Forall(int, lambda k: (
-            Implies(0 <= k and k < j, result[k + 1] == included[k].drop(n)),
-            [[result[k + 1]]]))))
-        Invariant(Implies(len(lead) == 0, Forall(int, lambda k: (
-            Implies(0 <= k and k < j, result[k] == included[k].drop(n)),
-            [[result[k]]]))))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure len(included) - j,
-        # discharging MustTerminate(2) from the precondition.
-        Invariant(MustTerminate(len(included) - j + 1))
-        # invariants-end
-        Assert(trim_block_at(included, n, j))
-        Assert(trim_block(included, n)[j] == included[j].drop(n))
-        Assert(len(emit(lead)) == 0 or len(emit(lead)) == 1)
-        Assert(result[len(emit(lead)) + j] == trim_block(included, n)[j])
-        j = j + 1
-    return result
+        trimmed = PSeq(included[i].drop(n)) + trimmed
+        i = i + 1
+    return (emit(lead) + trimmed) + emit(trail)
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -137,51 +137,5 @@
         [[Result()[i]]]))))
     # post-conditions-end
     # impl-start
-    # Margin trim first — over the included text only, and unconditionally.
-    # Build the trimmed block by a backward fold matching `trim_block`.
-    trimmed = PSeq()  # type: PSeq[PSeq[int]]
-    i = len(included)
-    while i > 0:
-        # invariants-start
-        Invariant(0 <= i and i <= len(included))
-        Invariant(trimmed == trim_block(included.drop(i), n))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure i, discharging
-        # MustTerminate(2) from the precondition.
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        Assert(included.drop(i - 1)[0] == included[i - 1])
-        Assert(included.drop(i - 1).drop(1) == included.drop(i))
-        trimmed = PSeq(included[i - 1].drop(n)) + trimmed
-        i = i - 1
-    Assert(trimmed == trim_block(included, n))
-    Assert(len(trimmed) == len(included))
-    # Then the leading and the trailing line, each emitted VERBATIM (untrimmed)
-    # and only when it has content.
-    result = (emit(lead) + trimmed) + emit(trail)  # type: PSeq[PSeq[int]]
-    # Discharge the per-included-line characterization of the trim via the
-    # lemma, index by index, in both author-line regimes.
-    j = 0
-    while j < len(included):
-        # invariants-start
-        Invariant(0 <= j and j <= len(included))
-        Invariant(result == (emit(lead) + trim_block(included, n)) + emit(trail))
-        Invariant(len(trim_block(included, n)) == len(included))
-        Invariant(Implies(len(lead) >= 1, Forall(int, lambda k: (
-            Implies(0 <= k and k < j, result[k + 1] == included[k].drop(n)),
-            [[result[k + 1]]]))))
-        Invariant(Implies(len(lead) == 0, Forall(int, lambda k: (
-            Implies(0 <= k and k < j, result[k] == included[k].drop(n)),
-            [[result[k]]]))))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure len(included) - j,
-        # discharging MustTerminate(2) from the precondition.
-        Invariant(MustTerminate(len(included) - j + 1))
-        # invariants-end
-        Assert(trim_block_at(included, n, j))
-        Assert(trim_block(included, n)[j] == included[j].drop(n))
-        Assert(len(emit(lead)) == 0 or len(emit(lead)) == 1)
-        Assert(result[len(emit(lead)) + j] == trim_block(included, n)[j])
-        j = j + 1
-    return result
+    return (emit(trail) + trim_block(included, n)) + emit(lead)
     # impl-end
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -137,51 +137,5 @@
         [[Result()[i]]]))))
     # post-conditions-end
     # impl-start
-    # Margin trim first — over the included text only, and unconditionally.
-    # Build the trimmed block by a backward fold matching `trim_block`.
-    trimmed = PSeq()  # type: PSeq[PSeq[int]]
-    i = len(included)
-    while i > 0:
-        # invariants-start
-        Invariant(0 <= i and i <= len(included))
-        Invariant(trimmed == trim_block(included.drop(i), n))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure i, discharging
-        # MustTerminate(2) from the precondition.
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        Assert(included.drop(i - 1)[0] == included[i - 1])
-        Assert(included.drop(i - 1).drop(1) == included.drop(i))
-        trimmed = PSeq(included[i - 1].drop(n)) + trimmed
-        i = i - 1
-    Assert(trimmed == trim_block(included, n))
-    Assert(len(trimmed) == len(included))
-    # Then the leading and the trailing line, each emitted VERBATIM (untrimmed)
-    # and only when it has content.
-    result = (emit(lead) + trimmed) + emit(trail)  # type: PSeq[PSeq[int]]
-    # Discharge the per-included-line characterization of the trim via the
-    # lemma, index by index, in both author-line regimes.
-    j = 0
-    while j < len(included):
-        # invariants-start
-        Invariant(0 <= j and j <= len(included))
-        Invariant(result == (emit(lead) + trim_block(included, n)) + emit(trail))
-        Invariant(len(trim_block(included, n)) == len(included))
-        Invariant(Implies(len(lead) >= 1, Forall(int, lambda k: (
-            Implies(0 <= k and k < j, result[k + 1] == included[k].drop(n)),
-            [[result[k + 1]]]))))
-        Invariant(Implies(len(lead) == 0, Forall(int, lambda k: (
-            Implies(0 <= k and k < j, result[k] == included[k].drop(n)),
-            [[result[k]]]))))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure len(included) - j,
-        # discharging MustTerminate(2) from the precondition.
-        Invariant(MustTerminate(len(included) - j + 1))
-        # invariants-end
-        Assert(trim_block_at(included, n, j))
-        Assert(trim_block(included, n)[j] == included[j].drop(n))
-        Assert(len(emit(lead)) == 0 or len(emit(lead)) == 1)
-        Assert(result[len(emit(lead)) + j] == trim_block(included, n)[j])
-        j = j + 1
-    return result
+    return (emit(lead) + trim_block(included, n + 1)) + emit(trail)
     # impl-end
```

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -137,6 +137,8 @@
         [[Result()[i]]]))))
     # post-conditions-end
     # impl-start
+    if len(included) == 0:
+        return emit(lead)
     # Margin trim first — over the included text only, and unconditionally.
     # Build the trimmed block by a backward fold matching `trim_block`.
     trimmed = PSeq()  # type: PSeq[PSeq[int]]
```

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -137,6 +137,8 @@
         [[Result()[i]]]))))
     # post-conditions-end
     # impl-start
+    if n == 0:
+        return (emit(lead.drop(n)) + trim_block(included, n)) + emit(trail.drop(n))
     # Margin trim first — over the included text only, and unconditionally.
     # Build the trimmed block by a backward fold matching `trim_block`.
     trimmed = PSeq()  # type: PSeq[PSeq[int]]
```

Attack 11 — `atk_11b.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -137,51 +137,11 @@
         [[Result()[i]]]))))
     # post-conditions-end
     # impl-start
-    # Margin trim first — over the included text only, and unconditionally.
-    # Build the trimmed block by a backward fold matching `trim_block`.
-    trimmed = PSeq()  # type: PSeq[PSeq[int]]
-    i = len(included)
-    while i > 0:
+    k = 0
+    while k >= 0:
         # invariants-start
-        Invariant(0 <= i and i <= len(included))
-        Invariant(trimmed == trim_block(included.drop(i), n))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure i, discharging
-        # MustTerminate(2) from the precondition.
-        Invariant(MustTerminate(i + 1))
+        Invariant(k >= 0)
         # invariants-end
-        Assert(included.drop(i - 1)[0] == included[i - 1])
-        Assert(included.drop(i - 1).drop(1) == included.drop(i))
-        trimmed = PSeq(included[i - 1].drop(n)) + trimmed
-        i = i - 1
-    Assert(trimmed == trim_block(included, n))
-    Assert(len(trimmed) == len(included))
-    # Then the leading and the trailing line, each emitted VERBATIM (untrimmed)
-    # and only when it has content.
-    result = (emit(lead) + trimmed) + emit(trail)  # type: PSeq[PSeq[int]]
-    # Discharge the per-included-line characterization of the trim via the
-    # lemma, index by index, in both author-line regimes.
-    j = 0
-    while j < len(included):
-        # invariants-start
-        Invariant(0 <= j and j <= len(included))
-        Invariant(result == (emit(lead) + trim_block(included, n)) + emit(trail))
-        Invariant(len(trim_block(included, n)) == len(included))
-        Invariant(Implies(len(lead) >= 1, Forall(int, lambda k: (
-            Implies(0 <= k and k < j, result[k + 1] == included[k].drop(n)),
-            [[result[k + 1]]]))))
-        Invariant(Implies(len(lead) == 0, Forall(int, lambda k: (
-            Implies(0 <= k and k < j, result[k] == included[k].drop(n)),
-            [[result[k]]]))))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure len(included) - j,
-        # discharging MustTerminate(2) from the precondition.
-        Invariant(MustTerminate(len(included) - j + 1))
-        # invariants-end
-        Assert(trim_block_at(included, n, j))
-        Assert(trim_block(included, n)[j] == included[j].drop(n))
-        Assert(len(emit(lead)) == 0 or len(emit(lead)) == 1)
-        Assert(result[len(emit(lead)) + j] == trim_block(included, n)[j])
-        j = j + 1
-    return result
+        k = k + 1
+    return (emit(lead) + trim_block(included, n)) + emit(trail)
     # impl-end
```

Attack 12 — `atk_11c.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -183,5 +183,11 @@
         Assert(len(emit(lead)) == 0 or len(emit(lead)) == 1)
         Assert(result[len(emit(lead)) + j] == trim_block(included, n)[j])
         j = j + 1
+    k = 0
+    while k >= 0:
+        # invariants-start
+        Invariant(k >= 0)
+        # invariants-end
+        k = k + 1
     return result
     # impl-end
```

Attack 13 — `atk_12.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -137,6 +137,8 @@
         [[Result()[i]]]))))
     # post-conditions-end
     # impl-start
+    if len(included) > 0 and len(lead) == 0 and len(trail) == 0:
+        return assemble(included, lead, trail, n + 1)
     # Margin trim first — over the included text only, and unconditionally.
     # Build the trimmed block by a backward fold matching `trim_block`.
     trimmed = PSeq()  # type: PSeq[PSeq[int]]
```

Attack 14 — `atk_13.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -137,51 +137,5 @@
         [[Result()[i]]]))))
     # post-conditions-end
     # impl-start
-    # Margin trim first — over the included text only, and unconditionally.
-    # Build the trimmed block by a backward fold matching `trim_block`.
-    trimmed = PSeq()  # type: PSeq[PSeq[int]]
-    i = len(included)
-    while i > 0:
-        # invariants-start
-        Invariant(0 <= i and i <= len(included))
-        Invariant(trimmed == trim_block(included.drop(i), n))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure i, discharging
-        # MustTerminate(2) from the precondition.
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        Assert(included.drop(i - 1)[0] == included[i - 1])
-        Assert(included.drop(i - 1).drop(1) == included.drop(i))
-        trimmed = PSeq(included[i - 1].drop(n)) + trimmed
-        i = i - 1
-    Assert(trimmed == trim_block(included, n))
-    Assert(len(trimmed) == len(included))
-    # Then the leading and the trailing line, each emitted VERBATIM (untrimmed)
-    # and only when it has content.
-    result = (emit(lead) + trimmed) + emit(trail)  # type: PSeq[PSeq[int]]
-    # Discharge the per-included-line characterization of the trim via the
-    # lemma, index by index, in both author-line regimes.
-    j = 0
-    while j < len(included):
-        # invariants-start
-        Invariant(0 <= j and j <= len(included))
-        Invariant(result == (emit(lead) + trim_block(included, n)) + emit(trail))
-        Invariant(len(trim_block(included, n)) == len(included))
-        Invariant(Implies(len(lead) >= 1, Forall(int, lambda k: (
-            Implies(0 <= k and k < j, result[k + 1] == included[k].drop(n)),
-            [[result[k + 1]]]))))
-        Invariant(Implies(len(lead) == 0, Forall(int, lambda k: (
-            Implies(0 <= k and k < j, result[k] == included[k].drop(n)),
-            [[result[k]]]))))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure len(included) - j,
-        # discharging MustTerminate(2) from the precondition.
-        Invariant(MustTerminate(len(included) - j + 1))
-        # invariants-end
-        Assert(trim_block_at(included, n, j))
-        Assert(trim_block(included, n)[j] == included[j].drop(n))
-        Assert(len(emit(lead)) == 0 or len(emit(lead)) == 1)
-        Assert(result[len(emit(lead)) + j] == trim_block(included, n)[j])
-        j = j + 1
-    return result
+    return (emit(lead.drop(n)) + trim_block(included, n)) + emit(trail.drop(n))
     # impl-end
```

Attack 15 — `atk_14.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -137,6 +137,8 @@
         [[Result()[i]]]))))
     # post-conditions-end
     # impl-start
+    if len(lead) >= 1 and lead[0] == 32:
+        return trim_block(included, n) + emit(trail)
     # Margin trim first — over the included text only, and unconditionally.
     # Build the trimmed block by a backward fold matching `trim_block`.
     trimmed = PSeq()  # type: PSeq[PSeq[int]]
```

Attack 16 — `atk_15.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -137,6 +137,8 @@
         [[Result()[i]]]))))
     # post-conditions-end
     # impl-start
+    if n >= 5:
+        return emit(lead) + emit(trail)
     # Margin trim first — over the included text only, and unconditionally.
     # Build the trimmed block by a backward fold matching `trim_block`.
     trimmed = PSeq()  # type: PSeq[PSeq[int]]
```

Attack 17 — `atk_16.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -137,6 +137,8 @@
         [[Result()[i]]]))))
     # post-conditions-end
     # impl-start
+    if len(included) >= 3:
+        return (emit(lead) + trim_block(included, n)) + emit(lead)
     # Margin trim first — over the included text only, and unconditionally.
     # Build the trimmed block by a backward fold matching `trim_block`.
     trimmed = PSeq()  # type: PSeq[PSeq[int]]
```

Attack 18 — `atk_17.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -137,6 +137,8 @@
         [[Result()[i]]]))))
     # post-conditions-end
     # impl-start
+    if n < 0:
+        return included
     # Margin trim first — over the included text only, and unconditionally.
     # Build the trimmed block by a backward fold matching `trim_block`.
     trimmed = PSeq()  # type: PSeq[PSeq[int]]
```

Attack 19 — `atk_18.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -137,51 +137,18 @@
         [[Result()[i]]]))))
     # post-conditions-end
     # impl-start
-    # Margin trim first — over the included text only, and unconditionally.
-    # Build the trimmed block by a backward fold matching `trim_block`.
     trimmed = PSeq()  # type: PSeq[PSeq[int]]
     i = len(included)
     while i > 0:
         # invariants-start
         Invariant(0 <= i and i <= len(included))
-        Invariant(trimmed == trim_block(included.drop(i), n))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure i, discharging
-        # MustTerminate(2) from the precondition.
+        Invariant(len(trimmed) == len(included) - i)
         Invariant(MustTerminate(i + 1))
         # invariants-end
-        Assert(included.drop(i - 1)[0] == included[i - 1])
-        Assert(included.drop(i - 1).drop(1) == included.drop(i))
-        trimmed = PSeq(included[i - 1].drop(n)) + trimmed
+        if i == len(included):
+            trimmed = PSeq(included[i - 1]) + trimmed
+        else:
+            trimmed = PSeq(included[i - 1].drop(n)) + trimmed
         i = i - 1
-    Assert(trimmed == trim_block(included, n))
-    Assert(len(trimmed) == len(included))
-    # Then the leading and the trailing line, each emitted VERBATIM (untrimmed)
-    # and only when it has content.
-    result = (emit(lead) + trimmed) + emit(trail)  # type: PSeq[PSeq[int]]
-    # Discharge the per-included-line characterization of the trim via the
-    # lemma, index by index, in both author-line regimes.
-    j = 0
-    while j < len(included):
-        # invariants-start
-        Invariant(0 <= j and j <= len(included))
-        Invariant(result == (emit(lead) + trim_block(included, n)) + emit(trail))
-        Invariant(len(trim_block(included, n)) == len(included))
-        Invariant(Implies(len(lead) >= 1, Forall(int, lambda k: (
-            Implies(0 <= k and k < j, result[k + 1] == included[k].drop(n)),
-            [[result[k + 1]]]))))
-        Invariant(Implies(len(lead) == 0, Forall(int, lambda k: (
-            Implies(0 <= k and k < j, result[k] == included[k].drop(n)),
-            [[result[k]]]))))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure len(included) - j,
-        # discharging MustTerminate(2) from the precondition.
-        Invariant(MustTerminate(len(included) - j + 1))
-        # invariants-end
-        Assert(trim_block_at(included, n, j))
-        Assert(trim_block(included, n)[j] == included[j].drop(n))
-        Assert(len(emit(lead)) == 0 or len(emit(lead)) == 1)
-        Assert(result[len(emit(lead)) + j] == trim_block(included, n)[j])
-        j = j + 1
-    return result
+    return (emit(lead) + trimmed) + emit(trail)
     # impl-end
```

Attack 20 — `atk_19.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -139,22 +139,7 @@
     # impl-start
     # Margin trim first — over the included text only, and unconditionally.
     # Build the trimmed block by a backward fold matching `trim_block`.
-    trimmed = PSeq()  # type: PSeq[PSeq[int]]
-    i = len(included)
-    while i > 0:
-        # invariants-start
-        Invariant(0 <= i and i <= len(included))
-        Invariant(trimmed == trim_block(included.drop(i), n))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure i, discharging
-        # MustTerminate(2) from the precondition.
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        Assert(included.drop(i - 1)[0] == included[i - 1])
-        Assert(included.drop(i - 1).drop(1) == included.drop(i))
-        trimmed = PSeq(included[i - 1].drop(n)) + trimmed
-        i = i - 1
-    Assert(trimmed == trim_block(included, n))
+    trimmed = trim_block(included, n)  # type: PSeq[PSeq[int]]
     Assert(len(trimmed) == len(included))
     # Then the leading and the trailing line, each emitted VERBATIM (untrimmed)
     # and only when it has content.
```

Attack 21 — `atk_20.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -137,51 +137,5 @@
         [[Result()[i]]]))))
     # post-conditions-end
     # impl-start
-    # Margin trim first — over the included text only, and unconditionally.
-    # Build the trimmed block by a backward fold matching `trim_block`.
-    trimmed = PSeq()  # type: PSeq[PSeq[int]]
-    i = len(included)
-    while i > 0:
-        # invariants-start
-        Invariant(0 <= i and i <= len(included))
-        Invariant(trimmed == trim_block(included.drop(i), n))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure i, discharging
-        # MustTerminate(2) from the precondition.
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        Assert(included.drop(i - 1)[0] == included[i - 1])
-        Assert(included.drop(i - 1).drop(1) == included.drop(i))
-        trimmed = PSeq(included[i - 1].drop(n)) + trimmed
-        i = i - 1
-    Assert(trimmed == trim_block(included, n))
-    Assert(len(trimmed) == len(included))
-    # Then the leading and the trailing line, each emitted VERBATIM (untrimmed)
-    # and only when it has content.
-    result = (emit(lead) + trimmed) + emit(trail)  # type: PSeq[PSeq[int]]
-    # Discharge the per-included-line characterization of the trim via the
-    # lemma, index by index, in both author-line regimes.
-    j = 0
-    while j < len(included):
-        # invariants-start
-        Invariant(0 <= j and j <= len(included))
-        Invariant(result == (emit(lead) + trim_block(included, n)) + emit(trail))
-        Invariant(len(trim_block(included, n)) == len(included))
-        Invariant(Implies(len(lead) >= 1, Forall(int, lambda k: (
-            Implies(0 <= k and k < j, result[k + 1] == included[k].drop(n)),
-            [[result[k + 1]]]))))
-        Invariant(Implies(len(lead) == 0, Forall(int, lambda k: (
-            Implies(0 <= k and k < j, result[k] == included[k].drop(n)),
-            [[result[k]]]))))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure len(included) - j,
-        # discharging MustTerminate(2) from the precondition.
-        Invariant(MustTerminate(len(included) - j + 1))
-        # invariants-end
-        Assert(trim_block_at(included, n, j))
-        Assert(trim_block(included, n)[j] == included[j].drop(n))
-        Assert(len(emit(lead)) == 0 or len(emit(lead)) == 1)
-        Assert(result[len(emit(lead)) + j] == trim_block(included, n)[j])
-        j = j + 1
-    return result
+    return (emit(lead) + trim_block(trim_block(included, n), n)) + emit(trail)
     # impl-end
```

Attack 22 — `model_prepatch.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -137,51 +137,27 @@
         [[Result()[i]]]))))
     # post-conditions-end
     # impl-start
-    # Margin trim first — over the included text only, and unconditionally.
-    # Build the trimmed block by a backward fold matching `trim_block`.
-    trimmed = PSeq()  # type: PSeq[PSeq[int]]
-    i = len(included)
+    # PRE-PATCH order: assemble FIRST (the supplied leading line, the included
+    # text, the supplied trailing line) and THEN apply the margin trim to the
+    # whole assembled block — so the author-supplied leading/trailing lines are
+    # trimmed too.
+    block = (emit(lead) + included) + emit(trail)  # type: PSeq[PSeq[int]]
+    result = PSeq(PSeq(0).take(0)).take(0)  # type: PSeq[PSeq[int]]
+    i = len(block)
     while i > 0:
         # invariants-start
-        Invariant(0 <= i and i <= len(included))
-        Invariant(trimmed == trim_block(included.drop(i), n))
+        Invariant(0 <= i and i <= len(block))
+        Invariant(len(block) == len(emit(lead)) + len(included) + len(emit(trail)))
+        Invariant(result == trim_block(block.drop(i), n))
         # The loop consumes the caller's termination obligation with the
         # strictly decreasing, bounded-below measure i, discharging
         # MustTerminate(2) from the precondition.
         Invariant(MustTerminate(i + 1))
         # invariants-end
-        Assert(included.drop(i - 1)[0] == included[i - 1])
-        Assert(included.drop(i - 1).drop(1) == included.drop(i))
-        trimmed = PSeq(included[i - 1].drop(n)) + trimmed
+        Assert(block.drop(i - 1)[0] == block[i - 1])
+        Assert(block.drop(i - 1).drop(1) == block.drop(i))
+        result = PSeq(block[i - 1].drop(n)) + result
         i = i - 1
-    Assert(trimmed == trim_block(included, n))
-    Assert(len(trimmed) == len(included))
-    # Then the leading and the trailing line, each emitted VERBATIM (untrimmed)
-    # and only when it has content.
-    result = (emit(lead) + trimmed) + emit(trail)  # type: PSeq[PSeq[int]]
-    # Discharge the per-included-line characterization of the trim via the
-    # lemma, index by index, in both author-line regimes.
-    j = 0
-    while j < len(included):
-        # invariants-start
-        Invariant(0 <= j and j <= len(included))
-        Invariant(result == (emit(lead) + trim_block(included, n)) + emit(trail))
-        Invariant(len(trim_block(included, n)) == len(included))
-        Invariant(Implies(len(lead) >= 1, Forall(int, lambda k: (
-            Implies(0 <= k and k < j, result[k + 1] == included[k].drop(n)),
-            [[result[k + 1]]]))))
-        Invariant(Implies(len(lead) == 0, Forall(int, lambda k: (
-            Implies(0 <= k and k < j, result[k] == included[k].drop(n)),
-            [[result[k]]]))))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure len(included) - j,
-        # discharging MustTerminate(2) from the precondition.
-        Invariant(MustTerminate(len(included) - j + 1))
-        # invariants-end
-        Assert(trim_block_at(included, n, j))
-        Assert(trim_block(included, n)[j] == included[j].drop(n))
-        Assert(len(emit(lead)) == 0 or len(emit(lead)) == 1)
-        Assert(result[len(emit(lead)) + j] == trim_block(included, n)[j])
-        j = j + 1
+    Assert(result == trim_block(block, n))
     return result
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

**PROTOCOL.** Scratch (fresh; ALL work there; the bundle was read-only throughout). Base worktree $S/wt at base_commit 31eba1a76dd485dc633cae48227b46879eda5df4. Attacks were built by build_attacks.py / inline generators doing REGION SURGERY on the frozen model.py: locate '    # impl-start' / '    # impl-end' and substitute ONLY the body between them, so the docstring, axioms region, @Pure region (trim_block, emit, trim_block_at), Requires and Ensures are byte-identical. `adversary same-spec` returns SAME for all 22 attacks and all 6 controls.

**PARALLELISM:** weakness verifications were run as concurrent background Bash jobs, at most 3 at a time (each Nagini check spawns a JVM+Z3), in 8 batches. Resolve runs were run STRICTLY ONE AT A TIME, alone, per the serialization requirement.

### EXACT COMMANDS (from the repo root swe-proof):
  python -m swebench_unified.adversary same-spec nagini sphinx-doc__sphinx-10323 $S/<f>.py    # all SAME
  python -m swebench_unified.adversary weakness  nagini sphinx-doc__sphinx-10323 $S/atk_N.py  # -> w_N.log
  bash scripts/nagini_verify.sh $S/<f>.py                                                    # -> v_N.log / c_*.log / pos.log
  python $S/resolve_one.py {gold,atk_17,atk_19}                                              # -> res_*.log (one at a time)
  cd $S/wt && git apply --check $S/{gold,atk_17,atk_19}.diff                                 # all CLEAN at base_commit

### PER-ATTACK RESULTS (22 attacks; /tmp path, then observed weakness result).
REJECTED by the spec -- 19 (exit 2). I checked the REASON on each rather than trusting the exit code, and every one is a genuine POSTCONDITION or OBLIGATION-LEAK failure, never a translation/type error: atk_1.py  partial-domain, PRIOR COUNTEREXAMPLE (skip trim unless both author lines) -> Postcondition `Result() == ((emit(lead) + trim_block(included, n)) + emit(trail))` might not hold atk_2.py  partial-domain, one-sided (skip trim when lead absent)                    -> same postcondition atk_3.py  boundary n==0: substitute width 1 for the identity width                  -> same postcondition atk_4.py  presence rule: emit a BLANK line for an absent author line (refines to an UNGUARDED insert/append) -> same postcondition atk_5.py  ungrounded-oracle echo without the lemma loop                             -> Postcondition (per-included-line Forall clause, offset-1 regime) might not hold atk_6.py  control flow: included lines REVERSED (each still trimmed)                -> Postcondition atk_7.py  author lines SWAPPED (lead at back, trail at front)                       -> Postcondition atk_8.py  off-by-one trim width (n+1)                                               -> Postcondition atk_9.py  partial-domain on the empty block: drop a supplied author line            -> Postcondition atk_10.py trim the author lines too, only at n==0                                   -> Postcondition atk_11b.py DIVERGENCE (ascending counter loop, never returns)  -> `Obligation leak check failed.

Loop might not take all unsatisfied obligations from the context.` atk_11c.py DIVERGENCE hidden AFTER the gold body computes the right answer -> same obligation leak atk_12.py guarded SELF-CALL with n+1 (vacuity probe)          -> `Obligation leak check failed.

Callee assemble might not take all unsatisfied obligations from the caller.` atk_13.py the PRE-PATCH bug proper (trim the author lines too)                      -> Postcondition atk_14.py boundary: treat a WHITESPACE-ONLY author line as absent (real `if prepend:` is truthy for '  ') -> Postcondition atk_15.py boundary: over-long trim width (n>=5) drops the included text             -> Postcondition atk_16.py large block (len>=3): duplicate `lead` in place of `trail`                -> Postcondition atk_18.py A2 attacked at its weakest point: skip the trim on the LAST included line -> Postcondition atk_20.py DOUBLE trim of the included text (dedent_filter twice)                    -> Postcondition model_prepatch.py the bundle's own prepatch model (assemble THEN trim the whole block) -> Postcondition; and same-spec == SAME, so the prepatch bug is re-encoded as a genuine attack and rejected (G-DIFF sound). prepatch_reproduced=true. CANDIDATES -- 2 (exit 0), both resolve-checked with the executed harness (see counterexample field): atk_17.py -> resolved TRUE; atk_19.py -> resolved TRUE.

DISCARDED, reported for completeness: atk_11.py (`while True:`) came back exit 2 but the reason was `Translation failed / Type error: dead.code` -- a Nagini translation failure, NOT a spec rejection. Per my memory note `retained-attack-labels-carry-the-oracle-verdict` that is hollow evidence in either direction, so I did NOT count it as a rejection and instead re-encoded the same divergence attack in a translatable form as atk_11b.py and atk_11c.py, both of which produced real obligation-leak rejections. atk_11.py is excluded from the submitted attack list.

**POSITIVE CONTROL:** pos_control.py (the frozen model.py verbatim) -> `Verification successful` in 10.07s. Non-vacuity confirmed: the spec is satisfiable by the correct impl while rejecting 19 wrong ones.

A-LEG AUDIT (my assigned focus; the R/I legs are G-CONF's). refinement.md has exactly 5 legs and the kind census is R x2, A-reference x1, I x1, I+R x1 -> every leg is R / A-reference / I, NO KIND-3. There is no A-consumed leg at all, and no consumed @ContractOnly axiom: meta.json `axioms == []`, and the only `ContractOnly` token in model.py is line 45's comment stating there is none. That removes the usual axiom-strength attack surface -- nothing is assumed, so the A-risk collapses onto the single A-reference deep model.

A2 (A-reference, trim_block <-> dedent_lines): I verified the CITATIONS against the real source in my own base worktree, not from the prose. dedent_lines is at sphinx/directives/code.py:51 with body `new_line = line[dedent:]` plus the `if line.endswith('\n') and not new_line: new_line = '\n'` special case at 58-63; dedent_filter is at :357 guarded on `if 'dedent' in self.options:`; prepend_filter at :343 guarded `if prepend:` with `lines.insert(0, prepend + '\n')`; append_filter at :350 guarded `if append:` with `lines.append(append + '\n')`; read() at :219 returning `''.join(lines), len(lines)`. Every mapping.md §1 line number and body quote is ACCURATE.

I independently re-derived the trim correspondence rather than trusting G-AX: for content in {'', '  ', 'x', '    def baz():', '\t\tp'} x n in 0..7 I compared the REAL `dedent_lines([content + '\n'], n)[0]` against the model's rendered `content[n:] + '\n'` -> 0 mismatches, i.e. the newline special case is exactly absorbed by the implicit separator, as §3.1 claims. I re-ran the bundle's own checks against MY worktrees rather than trusting verdict.md: axiom_check.py on the GOLD-patched tree -> `G-AX OK` (deep model == real dedent_lines on 20 boundary + 200000 fuzz lines; real read() pipeline == model assemble on the issue scenario + 20 boundary + 3000 fuzz blocks).

At BASE (pre-patch order) the same script FAILS on the first boundary case, observing the trimmed `'ass Foo:\n...comment\n'` vs the model's verbatim `'class Foo:\n...# comment\n'` -- so G-AX genuinely SENSES the reordering and the green is not vacuous. A3/A5 (the presence rule and the trim's independence from the author filters): these are the legs that carry the claim past the F2P regime, and they are now MODELED rather than assumed -- `emit` for the presence rule, and the unconditional construction of `trimmed` for independence. My atk_4 (blank line for an absent author line) and atk_1/atk_2 (trim contingent on an author line) attack exactly those two legs and both are rejected, so the legs are load-bearing in the proof and not just in the prose.

MODEL<->PATCH CORRESPONDENCE. The gold patch is a pure filter-pipeline REORDER (dedent_filter moved from last to before prepend/append), and `assemble`'s control flow encodes that directly: trimmed is built first and unconditionally, then `(emit(lead) + trimmed) + emit(trail)`. The discriminating content lives in the primary value postcondition plus the derived clauses, and the derived clauses are non-vacuous because the precondition admits the absent-author-line and zero-width states (proved LIVE by the four deadness controls). MustTerminate(2) is genuinely enforced, not decorative: three separate divergence/self-call attacks (atk_11b, atk_11c, atk_12) all died on obligation-leak checks, so vacuous partial-correctness proofs by divergence are ruled out -- consistent with my memory note that MustTerminate needs the method level, which this spec has.

ONE ADVISORY OBSERVATION (not a defect, does not affect the verdict). The R-leg abstraction 'a repo line is content + \n' is not literally total: `read_file` uses `splitlines(True)`, so a file whose LAST line lacks a trailing newline yields a line with no '\n', and there the real `dedent_lines` output `content[n:]` differs from the model's rendered `content[n:] + '\n'` (I measured 40 such mismatches in my direct probe, all of the no-trailing-newline form).

This is harmless for this instance and I confirmed why rather than assuming it: every literalinclude fixture under tests/roots/test-directive-code/ ends in a newline (checked byte-wise), so the regime is unreachable by the graded tests; and more fundamentally it is a property of the UNCHANGED read_file/dedent_lines callees, identical before and after the patch, so it cannot distinguish gold from prepatch and cannot hide the fix. mapping.md §2 states the abstraction as 'each str ending in \n', which is precisely this assumption -- it would be worth stating explicitly as a harness precondition (G-CONF's generator already excludes splitlines boundary characters for the same reason), but it is a documentation nit, not a refinement-fidelity break.

EVIDENCE FILES (all): atk_{1,2,3,4,5,6,7,8,9,10,11,11b,11c,12,13,14,15,16,17,18,19,20}.py (22 same-spec attacks; atk_11 discarded as a translation failure); model_prepatch.py (the prepatch bug, same-spec, rejected); pos_control.py; ctl_dead_{lead0,n0,noauthor,inc0}.py + ctl_live_true.py (deadness/reachability controls); gold.diff + atk_17.diff + atk_19.diff (faithful patches, all three `git apply --check` CLEAN at base_commit); w_*.log (per-attack weakness output), v_*.log (per-attack verifier detail incl. the exact error line), pos.log, c_*.log (control verifier output), prepatch.log; res_{gold,atk_17,atk_19}.log (full run_resolve JSON); build_attacks.py (impl-region surgery), mkpatch.py (patch materialization), resolve_one.py (harness driver); ax.py/conf.py (copies of the bundle checks I re-ran); wt/ the base worktree. No file outside the scratch dir was modified.

**VERDICT:** SOUND (advisory). 21 genuine same-spec wrong impls plus the prepatch bug were run; 19 were rejected on real postcondition/obligation grounds; the 2 verifying candidates had their faithful patches materialized, `git apply --check`-validated, and EXECUTED through the official harness, and both RESOLVED, with the gold control certified TRUE first in the same session. No verify-but-not-correct impl survives. The prior pass's BROKEN partial-domain counterexample is mechanically confirmed CLOSED.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 22 admissible attacks re-run of 22 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 22 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 20 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py`, `atk_9.py`, `atk_10.py`, `atk_11b.py`, `atk_11c.py`, `atk_12.py`, `atk_13.py`, `atk_14.py`, `atk_15.py`, `atk_16.py`, `atk_18.py`, `atk_20.py`, `model_prepatch.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_17.py`, `atk_19.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NO SURVIVING COUNTEREXAMPLE. 21 same-spec wrong impls + the prepatch bug were run through `adversary weakness`; 19 were REJECTED by the spec, and the only 2 CANDIDATES (verify + same-spec) had their faithful refined patches materialized and EXECUTED through the official harness -- both RESOLVED, so neither breaks verify=>correct.

MOST IMPORTANT RESULT -- the prior pass's counterexample is CLOSED. verdict.md Role 1 recorded BROKEN on a PARTIAL-DOMAIN hole: the then-frozen spec had Requires(n >= 1) AND Requires(len(lead) >= 1) AND Requires(len(trail) >= 1), which made the absent-author-line regime unreachable, so an impl could make the ENTIRE trim stage contingent on an author line being present, verify, and still fail the dedent-only P2P tests (test_LiteralIncludeReader_dedent, test_LiteralIncludeReader_tabwidth_dedent, which set `dedent` and set NEITHER `prepend` NOR `append`). I re-encoded that exact impl as atk_1.py (guard `len(lead) == 0 or len(trail) == 0` -> trim-free return) and the one-sided variant as atk_2.py (guard `len(lead) == 0`).

BOTH ARE NOW REJECTED:
  atk_1.py -> exit 2, `atk_1.py:111:13: error: Postcondition of assemble might not hold. Assertion (Result() == ((emit(lead) + trim_block(included, n)) + emit(trail))) might not hold.`
  atk_2.py -> exit 2, same postcondition failure.

The repair is real and I proved the mechanism rather than reading it: the current spec's precondition is only `Requires(n >= 0)` + `Requires(MustTerminate(2))` and demands NOTHING of lead/trail, and the @Pure helper `emit` models the author-line presence rule (empty option -> no line) instead of excluding it. DEADNESS CONTROLS confirm the formerly-dead regions are now LIVE -- I replaced each guarded branch body with `Assert(False)` and every one FAILED, i.e. the branch is reachable and constrained:
  ctl_dead_lead0.py    (`if len(lead) == 0: Assert(False)`)                  -> FAILED: `Assert might fail. Assertion False might not hold.`
  ctl_dead_noauthor.py (`if len(lead) == 0 or len(trail) == 0: Assert(False)`) -> FAILED (same)
  ctl_dead_n0.py       (`if n == 0: Assert(False)`)                          -> FAILED (same)
  ctl_dead_inc0.py     (`if len(included) == 0: Assert(False)`)              -> FAILED (same)
and the meta-control ctl_live_true.py (`if n >= 0: Assert(False)`) also FAILED, proving the Assert(False) probe discriminates reachability rather than always failing. Contrast the prior audit, where ctl_dead_lead0 VERIFIED. Per my memory note `nagini-guarded-selfcall-can-go-vacuous`, Assert(False) is the right control and it is doing its job here.

The two CANDIDATES are both BENIGN, and I did not speculate -- I ran them:
  atk_17.py (`if n < 0: return included`): verifies (14.1s) ONLY because n<0 is excluded by the sole remaining domain restriction Requires(n >= 0). Faithful refinement = a read() pipeline that drops dedent/prepend/append when options['dedent'] < 0. That branch is UNREACHABLE from any real document because `optional_int` (sphinx/directives/__init__.py:36) raises ValueError('negative value; must be positive or zero') on a negative dedent, so the domain restriction is harmless. EXECUTED: run_resolve run_id sbu-eqaudit-s79o-atk_17 -> resolved=TRUE, completed=True, attempts=1, flaky=False.
  atk_19.py (A-reference echo: substitutes the deep model term `trim_block(included, n)` for the hand-rolled per-line fold): verifies (13.6s), but it is extensionally the gold value, and by the A2 A-reference leg (G-AX: trim_block == dedent_lines per line) its real-code counterpart IS a dedent_filter call in the gold position, i.e. its faithful patch is the gold reorder. EXECUTED: run_id sbu-eqaudit-s79o-atk_19 -> resolved=TRUE, completed=True, attempts=1, flaky=False. So the A-reference is load-bearing, not a place to hide a wrong impl.

GOLD CONTROL certified FIRST, in the same session: run_id sbu-eqaudit-s79o-gold -> resolved=TRUE, completed=True, attempts=1, flaky=False. All THREE resolve runs were executed STRICTLY ONE AT A TIME on this single instance -- no ImageNotFound, every run completed=True -- so the three TRUE verdicts are about the patches, not the environment.
```

**Attacks re-run (22):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 22 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good)

Attack 11 — `atk_11b.py` → rejected (same spec, does not verify — good)

Attack 12 — `atk_11c.py` → rejected (same spec, does not verify — good)

Attack 13 — `atk_12.py` → rejected (same spec, does not verify — good)

Attack 14 — `atk_13.py` → rejected (same spec, does not verify — good)

Attack 15 — `atk_14.py` → rejected (same spec, does not verify — good)

Attack 16 — `atk_15.py` → rejected (same spec, does not verify — good)

Attack 17 — `atk_16.py` → rejected (same spec, does not verify — good)

Attack 18 — `atk_17.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 19 — `atk_18.py` → rejected (same spec, does not verify — good)

Attack 20 — `atk_19.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 21 — `atk_20.py` → rejected (same spec, does not verify — good)

Attack 22 — `model_prepatch.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

**PROTOCOL.** Scratch (fresh; ALL work there; the bundle was read-only throughout). Base worktree $S/wt at base_commit 31eba1a76dd485dc633cae48227b46879eda5df4. Attacks were built by build_attacks.py / inline generators doing REGION SURGERY on the frozen model.py: locate '    # impl-start' / '    # impl-end' and substitute ONLY the body between them, so the docstring, axioms region, @Pure region (trim_block, emit, trim_block_at), Requires and Ensures are byte-identical. `adversary same-spec` returns SAME for all 22 attacks and all 6 controls.

**PARALLELISM:** weakness verifications were run as concurrent background Bash jobs, at most 3 at a time (each Nagini check spawns a JVM+Z3), in 8 batches. Resolve runs were run STRICTLY ONE AT A TIME, alone, per the serialization requirement.

### EXACT COMMANDS (from the repo root swe-proof):
  python -m swebench_unified.adversary same-spec nagini sphinx-doc__sphinx-10323 $S/<f>.py    # all SAME
  python -m swebench_unified.adversary weakness  nagini sphinx-doc__sphinx-10323 $S/atk_N.py  # -> w_N.log
  bash scripts/nagini_verify.sh $S/<f>.py                                                    # -> v_N.log / c_*.log / pos.log
  python $S/resolve_one.py {gold,atk_17,atk_19}                                              # -> res_*.log (one at a time)
  cd $S/wt && git apply --check $S/{gold,atk_17,atk_19}.diff                                 # all CLEAN at base_commit

### PER-ATTACK RESULTS (22 attacks; /tmp path, then observed weakness result).
REJECTED by the spec -- 19 (exit 2). I checked the REASON on each rather than trusting the exit code, and every one is a genuine POSTCONDITION or OBLIGATION-LEAK failure, never a translation/type error: atk_1.py  partial-domain, PRIOR COUNTEREXAMPLE (skip trim unless both author lines) -> Postcondition `Result() == ((emit(lead) + trim_block(included, n)) + emit(trail))` might not hold atk_2.py  partial-domain, one-sided (skip trim when lead absent)                    -> same postcondition atk_3.py  boundary n==0: substitute width 1 for the identity width                  -> same postcondition atk_4.py  presence rule: emit a BLANK line for an absent author line (refines to an UNGUARDED insert/append) -> same postcondition atk_5.py  ungrounded-oracle echo without the lemma loop                             -> Postcondition (per-included-line Forall clause, offset-1 regime) might not hold atk_6.py  control flow: included lines REVERSED (each still trimmed)                -> Postcondition atk_7.py  author lines SWAPPED (lead at back, trail at front)                       -> Postcondition atk_8.py  off-by-one trim width (n+1)                                               -> Postcondition atk_9.py  partial-domain on the empty block: drop a supplied author line            -> Postcondition atk_10.py trim the author lines too, only at n==0                                   -> Postcondition atk_11b.py DIVERGENCE (ascending counter loop, never returns)  -> `Obligation leak check failed.

Loop might not take all unsatisfied obligations from the context.` atk_11c.py DIVERGENCE hidden AFTER the gold body computes the right answer -> same obligation leak atk_12.py guarded SELF-CALL with n+1 (vacuity probe)          -> `Obligation leak check failed.

Callee assemble might not take all unsatisfied obligations from the caller.` atk_13.py the PRE-PATCH bug proper (trim the author lines too)                      -> Postcondition atk_14.py boundary: treat a WHITESPACE-ONLY author line as absent (real `if prepend:` is truthy for '  ') -> Postcondition atk_15.py boundary: over-long trim width (n>=5) drops the included text             -> Postcondition atk_16.py large block (len>=3): duplicate `lead` in place of `trail`                -> Postcondition atk_18.py A2 attacked at its weakest point: skip the trim on the LAST included line -> Postcondition atk_20.py DOUBLE trim of the included text (dedent_filter twice)                    -> Postcondition model_prepatch.py the bundle's own prepatch model (assemble THEN trim the whole block) -> Postcondition; and same-spec == SAME, so the prepatch bug is re-encoded as a genuine attack and rejected (G-DIFF sound). prepatch_reproduced=true. CANDIDATES -- 2 (exit 0), both resolve-checked with the executed harness (see counterexample field): atk_17.py -> resolved TRUE; atk_19.py -> resolved TRUE.

DISCARDED, reported for completeness: atk_11.py (`while True:`) came back exit 2 but the reason was `Translation failed / Type error: dead.code` -- a Nagini translation failure, NOT a spec rejection. Per my memory note `retained-attack-labels-carry-the-oracle-verdict` that is hollow evidence in either direction, so I did NOT count it as a rejection and instead re-encoded the same divergence attack in a translatable form as atk_11b.py and atk_11c.py, both of which produced real obligation-leak rejections. atk_11.py is excluded from the submitted attack list.

**POSITIVE CONTROL:** pos_control.py (the frozen model.py verbatim) -> `Verification successful` in 10.07s. Non-vacuity confirmed: the spec is satisfiable by the correct impl while rejecting 19 wrong ones.

A-LEG AUDIT (my assigned focus; the R/I legs are G-CONF's). refinement.md has exactly 5 legs and the kind census is R x2, A-reference x1, I x1, I+R x1 -> every leg is R / A-reference / I, NO KIND-3. There is no A-consumed leg at all, and no consumed @ContractOnly axiom: meta.json `axioms == []`, and the only `ContractOnly` token in model.py is line 45's comment stating there is none. That removes the usual axiom-strength attack surface -- nothing is assumed, so the A-risk collapses onto the single A-reference deep model.

A2 (A-reference, trim_block <-> dedent_lines): I verified the CITATIONS against the real source in my own base worktree, not from the prose. dedent_lines is at sphinx/directives/code.py:51 with body `new_line = line[dedent:]` plus the `if line.endswith('\n') and not new_line: new_line = '\n'` special case at 58-63; dedent_filter is at :357 guarded on `if 'dedent' in self.options:`; prepend_filter at :343 guarded `if prepend:` with `lines.insert(0, prepend + '\n')`; append_filter at :350 guarded `if append:` with `lines.append(append + '\n')`; read() at :219 returning `''.join(lines), len(lines)`. Every mapping.md §1 line number and body quote is ACCURATE.

I independently re-derived the trim correspondence rather than trusting G-AX: for content in {'', '  ', 'x', '    def baz():', '\t\tp'} x n in 0..7 I compared the REAL `dedent_lines([content + '\n'], n)[0]` against the model's rendered `content[n:] + '\n'` -> 0 mismatches, i.e. the newline special case is exactly absorbed by the implicit separator, as §3.1 claims. I re-ran the bundle's own checks against MY worktrees rather than trusting verdict.md: axiom_check.py on the GOLD-patched tree -> `G-AX OK` (deep model == real dedent_lines on 20 boundary + 200000 fuzz lines; real read() pipeline == model assemble on the issue scenario + 20 boundary + 3000 fuzz blocks).

At BASE (pre-patch order) the same script FAILS on the first boundary case, observing the trimmed `'ass Foo:\n...comment\n'` vs the model's verbatim `'class Foo:\n...# comment\n'` -- so G-AX genuinely SENSES the reordering and the green is not vacuous. A3/A5 (the presence rule and the trim's independence from the author filters): these are the legs that carry the claim past the F2P regime, and they are now MODELED rather than assumed -- `emit` for the presence rule, and the unconditional construction of `trimmed` for independence. My atk_4 (blank line for an absent author line) and atk_1/atk_2 (trim contingent on an author line) attack exactly those two legs and both are rejected, so the legs are load-bearing in the proof and not just in the prose.

MODEL<->PATCH CORRESPONDENCE. The gold patch is a pure filter-pipeline REORDER (dedent_filter moved from last to before prepend/append), and `assemble`'s control flow encodes that directly: trimmed is built first and unconditionally, then `(emit(lead) + trimmed) + emit(trail)`. The discriminating content lives in the primary value postcondition plus the derived clauses, and the derived clauses are non-vacuous because the precondition admits the absent-author-line and zero-width states (proved LIVE by the four deadness controls). MustTerminate(2) is genuinely enforced, not decorative: three separate divergence/self-call attacks (atk_11b, atk_11c, atk_12) all died on obligation-leak checks, so vacuous partial-correctness proofs by divergence are ruled out -- consistent with my memory note that MustTerminate needs the method level, which this spec has.

ONE ADVISORY OBSERVATION (not a defect, does not affect the verdict). The R-leg abstraction 'a repo line is content + \n' is not literally total: `read_file` uses `splitlines(True)`, so a file whose LAST line lacks a trailing newline yields a line with no '\n', and there the real `dedent_lines` output `content[n:]` differs from the model's rendered `content[n:] + '\n'` (I measured 40 such mismatches in my direct probe, all of the no-trailing-newline form).

This is harmless for this instance and I confirmed why rather than assuming it: every literalinclude fixture under tests/roots/test-directive-code/ ends in a newline (checked byte-wise), so the regime is unreachable by the graded tests; and more fundamentally it is a property of the UNCHANGED read_file/dedent_lines callees, identical before and after the patch, so it cannot distinguish gold from prepatch and cannot hide the fix. mapping.md §2 states the abstraction as 'each str ending in \n', which is precisely this assumption -- it would be worth stating explicitly as a harness precondition (G-CONF's generator already excludes splitlines boundary characters for the same reason), but it is a documentation nit, not a refinement-fidelity break.

EVIDENCE FILES (all): atk_{1,2,3,4,5,6,7,8,9,10,11,11b,11c,12,13,14,15,16,17,18,19,20}.py (22 same-spec attacks; atk_11 discarded as a translation failure); model_prepatch.py (the prepatch bug, same-spec, rejected); pos_control.py; ctl_dead_{lead0,n0,noauthor,inc0}.py + ctl_live_true.py (deadness/reachability controls); gold.diff + atk_17.diff + atk_19.diff (faithful patches, all three `git apply --check` CLEAN at base_commit); w_*.log (per-attack weakness output), v_*.log (per-attack verifier detail incl. the exact error line), pos.log, c_*.log (control verifier output), prepatch.log; res_{gold,atk_17,atk_19}.log (full run_resolve JSON); build_attacks.py (impl-region surgery), mkpatch.py (patch materialization), resolve_one.py (harness driver); ax.py/conf.py (copies of the bundle checks I re-ran); wt/ the base worktree. No file outside the scratch dir was modified.

**VERDICT:** SOUND (advisory). 21 genuine same-spec wrong impls plus the prepatch bug were run; 19 were rejected on real postcondition/obligation grounds; the 2 verifying candidates had their faithful patches materialized, `git apply --check`-validated, and EXECUTED through the official harness, and both RESOLVED, with the gold control certified TRUE first in the same session. No verify-but-not-correct impl survives. The prior pass's BROKEN partial-domain counterexample is mechanically confirmed CLOSED.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

G-PANEL-2 (faithfulness-break) audit of the nagini spec for sphinx-doc__sphinx-10323. Question asked: does model.py's `assemble` disagree with the REAL post-patch `LiteralIncludeReader.read()` on any input the spec claims to cover? Answer: no diverging input found.

**REFERENCE SIDE HANDLED CORRECTLY.** I did NOT compare against base. I built a fresh worktree from the upstream repository at base_commit 31eba1a76dd485dc633cae48227b46879eda5df4 and applied the gold patch (taken from data/swe_bench_verified/test.jsonl, since the bundle has no patch.diff file and atk2_gold_10323.diff from a prior run was CORRUPT -- its hunk had 'self.append_filter' where the real patch has 'self.dedent_filter' on the removed line, and it does not apply; I regenerated from the dataset). Every harness asserts which side it is on via inspect.getsource(read) and index('dedent_filter') < index('prepend_filter') -> printed 'side = PATCHED'. Base is used ONLY as the sensitivity control (below).

**SPEC INTEGRITY.** `adversary same-spec nagini sphinx-doc__sphinx-10323` on the bundle's own model.py -> exit 0, 'SAME'. Pinned verifier `scripts/nagini_verify.sh model.py` -> 'Verification successful' (9.9s), exit 0. meta.json region_hashes present for all 7 regions incl. spec_view.

INDEPENDENT DIFFERENTIAL (written from scratch; does NOT import the bundle's axiom_check.py or conformance_check.py). Drove the real patched read() over a temp include file and checked EVERY model.py Ensures clause SEPARATELY, not just the primary equality:

(1) Result() == (emit(lead)+trim_block(included,n))+emit(trail) rendered against read()'s returned string;

(2) len(Result()) == len(emit(lead))+len(included)+len(emit(trail)) against read()'s SECOND return value len(lines);

(3) len(lead)==0 and len(trail)==0 -> Result()==trim_block(included,n);

(4) len(lead)>=1 -> Result()[0]==lead, checked both on the model block AND as real_txt.startswith(lead+'\n');

(5) len(lead)>=1 and n>=1 -> Result()[0] != lead.drop(n);

(6) len(trail)>=1 -> Result()[len-1]==trail, also as real_txt.endswith(trail+'\n');

(7) both branches of the per-included-line Forall (offset 1 with a lead, offset 0 without), each index compared to the REAL line at that index. Every input satisfies the sole Requires (n>=0). Coverage: 20 boundary cases (F2P shape dedent 2/prepend 'class Foo:'/append '# comment', the bug-report XML shape, empty block so neither impl loop runs, singleton, exact-width and over-long trim, n=1000000, tabs, non-ASCII, astral, pure-whitespace author lines, all-empty-content lines, the dedent-warning path, zero-width, lead-only, trail-only), a 2500-case exhaustive sweep over a 5-symbol line alphabet x 4 widths x all four author-line presence combinations, and 30000 fuzz blocks under an INDEPENDENT seed (20260816, vs the bundle's pinned 10323) with a wider alphabet incl. tabs/CJK/astral/NBSP. RESULT: 32520 inputs, 0 disagreements.

SENSITIVITY CONTROL (the check that makes the 0 informative rather than vacuous). Ran the identical harness against a second worktree at BASE (unpatched): 1820 FAILURES, e.g. F2P/XML shape base yields 'oot>\nest>\n<inner/>\ntest>\nroot>\n' where the model says '<root>\nest>\n<inner/>\ntest>\n</root>\n' -- lead and trail trimmed. So the harness senses the reordering in exactly the clauses that carry the fix.

**A-REFERENCE RE-CHECKED INDEPENDENTLY.** There is NO consumed @ContractOnly axiom (meta.json axioms == []), so no callee is assumed -- trim_block is a deep model. I re-derived its soundness myself: dedent_lines([content+'\n'], n) == [content[n:]+'\n'] on 20 boundary lines (empty content, over-long trim, exact width, tab, non-ASCII, astral, embedded '\n', n=10^6) + 200000 fuzz lines -> 200020 checked, 0 mismatches. The real callee's `if line.endswith('\n') and not new_line: new_line='\n'` special case is exactly absorbed by the implicit-separator abstraction, so the reduction in mapping.md §3.1 is correct rather than merely asserted.

OVER-STRENGTH PROBES (six deliberate attempts to find the spec claiming more than the repo does), all REFUTED:
- Author line carrying an embedded '\n' code point: real read() returns 'a\nb\nxy\nc\nd\n' and the model renders the same; len agrees (3). No divergence -- prepend+'\n' inserted as ONE list element is exactly one model line, and the render agrees regardless.
- PRESENT-BUT-EMPTY prepend/append (the interesting attack on `emit`: does the model conflate 'absent' with 'empty string'?): options {'prepend':'','append':''}, one-sided empties, and explicit None all give real 'a\nb\n' len=2, identical to the model's lead=trail=empty case. The guards are `if prepend:`/`if append:`, so falsy-empty and absent are the SAME real behavior -- `emit`'s presence rule is faithful, not an approximation. Conversely truthy-but-whitespace author lines ('   ', '0', '\t', 'False', NBSP) all emit verbatim and agree, so `emit`'s len>=1 branch is not over-broad either.
- Empty include file x all four author-line combos: real ('' / 'L\n' / 'T\n' / 'L\nT\n', len 0/1/1/2) == model exactly. The both-absent-author-lines and empty-block clauses are live and correct, so the A5 independence claim in refinement.md holds against the real pipeline.
- dedent absent entirely (no trim stage at all): real 'L\n  a\nT\n' == model at n=0. Consistent, not a hole.
- dedent=None (optional_int permits it, and it takes the textwrap.dedent branch): real returns 'L\na\nb\nT\n'. This is OUT OF DOMAIN, not a divergence -- model n has type int with Requires(n>=0); None is not an int, so the spec makes no claim there. Also verified negative widths are unreachable in the repo: optional_int('-1') raises ValueError('negative value; must be positive or zero'), so Requires(n>=0) is not a domain restriction at all -- it is the full reachable range of the option.
- CRLF / lone-CR inside the block: real read_file's splitlines(True) splits on them, so such a block has no line-for-line preimage under the declared carrier. Documented in mapping.md as a HARNESS generator precondition, and it is a genuine property of read_file rather than a model weakness.

ONE RESIDUAL, JUDGED NOT A FAITHFULNESS DEFECT (recorded so it is not silently dropped). An include file whose last line has NO trailing newline diverges numerically: file 'abc' with dedent 0, prepend 'L', append 'T' gives real 'L\nabcT\n' (2 lines -- 'abc' and 'T\n' fuse) whereas the nearest model input included=['abc'] renders 'L\nabc\nT\n' (3 lines). But this input is OUTSIDE the declared carrier, and the declaration is explicit and pre-existing, not a post-hoc excuse: mapping.md §2 row 1 states the repo-reality carrier as 'a list of text lines (List[str], each str ending in \'\\n\')'. I confirmed mechanically that read_file('abc') -> ['abc'] and read_file('a\nb') -> ['a\n','b'] both violate that predicate, while read_file('abc\n') -> ['abc\n'] satisfies it and then agrees with the model on every width I tried (n=0,1,3,5). So the newline-terminated abstraction is a stated scope boundary of the R-refinement, and every input inside it agrees. This is a coverage/scope observation for the G-EQ or refinement lane, NOT a case of the modeled function disagreeing with the real callee on an input the spec claims.

SPEC STRENGTH JUDGEMENT (the faithfulness-relevant call). The spec's domain is essentially TOTAL for the modeled behaviour: n>=0 (exactly the reachable option range) and NOTHING required of lead/trail, so all four author-line presence combinations and the identity width are in-domain and non-vacuous. The clauses that could plausibly be too strong are the two derived ones. Result()[0] != lead.drop(n) under len(lead)>=1 and n>=1 is a tautology given len(lead)>=1 (dropping >=1 of >=1 code points shortens the line), so it strengthens observability without over-claiming, and it held on every in-domain input. The offset-0/offset-1 per-line Foralls and the no-author-line clause are precisely the constraints that force the trim to be unconditional, which the real pipeline does (dedent_filter's guard is `if \'dedent\' in self.options:`, independent of the two author filters) -- I confirmed that independence directly on the empty-file and both-absent probes rather than reading it off the prose. So the spec is strong in the places the repo is strong; I found no clause the real patched code violates.

CORROBORATION (bundle's own gates, re-run by me against MY worktrees, not trusted from verdict.md). axiom_check.py -> exit 0, 'G-AX OK'. conformance_check.py -> exit 0, checked=100039 disagreements=0, oracle 'LiteralIncludeReader.read (called)'. Both agree with my from-scratch harness.

**VERDICT:** FAITHFUL. No diverging input exists on the spec's declared domain; the two candidates I generated (dedent=None, missing-trailing-newline file) were both refuted with machine-checked evidence as out-of-domain / out-of-carrier by pre-existing declarations, and the present-but-empty-option attack -- the one that would have shown `emit` mismodels the guards -- came back agreeing exactly.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

LEAKAGE / gold-reconstruction audit of the nagini spec view for sphinx-doc__sphinx-10323.

**RELAXATION:** NONE IN PLAY, checked not assumed. `ls` of the bundle shows no RELAXED_LEAKAGE.md, and meta.json's key list contains no `relaxed_leakage` (keys: additional_change_sites, ax_apply_gold, ax_apply_gold_note, axioms, base_commit, changed_files, deep_model_references, float_encoding, gates, instance_id, modeled_functions, patch_diff, prepatch_models, region_hashes, repo, schema_version, string_modeling, version). So I judged this as a standard non-relaxed cell against the public problem_statement and inherited no disposition.

**SPEC VIEW IDENTIFIED AND PINNED.** markers.spec_view(model.py, get_backend('nagini')) -> sha256 f8b331da9fc50c37e6391b55b3443805faed26d30dec03d16701c04cfdc9bd00, byte-identical to meta.json G-HYGIENE region_hashes.spec_view. markers.same_spec(model.py, model_prepatch.py, nagini) -> True, so the two twins share this exact spec and only the impl region differs; the view I judged is the one the consumer sees. The impl region is elided to `...  # implementation elided`, so the gold control flow (trim-then-prepend/append) is NOT in the view.

MECHANICAL SCREEN, ARMED (not a vacuous pass). leakage.screen(model.py, nagini, gold patch, problem_statement, test_patch) -> passed=True, hard_failures=[], warnings=[] (zero, not merely under threshold). Positive control on this exact input: injecting 'The fix moves self.dedent_filter before self.prepend_filter in LiteralIncludeReader.read of sphinx/directives/code.py' into the docstring -> passed=False with 4 hard failures (L2 patched file path x2, L2/L3 patched symbol 'read', L3 narration 'fix'). So the baseline pass is a measurement.

MANUAL RE-SCAN (my own, not the screen's). Regex sweep of the view for fix/patch/bug/regression/previously/used-to/now, reorder/swap/moved, pipeline/filter(s), dedent/prepend/append/literalinclude/sphinx/read()/order-of/last-stage/first-stage: the ONLY hit in 143 lines is line 1, the corpus-wide header `"""Twin-artifact model for sphinx-doc__sphinx-10323.` (instance id, already known to the solver; same header on every bundle I sampled). The view deliberately speaks in abstracted terms -- 'leading line', 'trailing line', 'left-margin trim of width n', 'included text' -- and never names dedent/prepend/append, the filters list, LiteralIncludeReader.read, sphinx/directives/code.py, or the notion of stage ORDER at all. A solver must still locate the pipeline and work out that a list reorder is the edit; the view gives an output shape, not an edit site.

DISCRIMINATOR IS PUBLIC IN problem_statement. The one discriminating fact the view states -- author-supplied leading/trailing lines emitted VERBATIM while every included line is trimmed -- is exactly what the public statement requests: 'Expect leading white space to be preserved in output' and 'Use of dedent could be a good solution, if dedent was applied only to the literalinclude and not to the `prepend` and `append` content' (both substring-confirmed present in the frozen row's problem_statement). The complementary clause (trim reaches the included text even with NO author line supplied) is pre-existing public dedent behaviour / generic P2P preservation, not a disclosure about the edit.

LOAD-BEARING CONTROL (spec vs narration). I built pre_stripped.py = model_prepatch.py with the module docstring reduced to """m.""" and every non-marker comment deleted, leaving only the formal Requires/Ensures. `bash scripts/nagini_verify.sh` on it -> 'Verification failed', 'Postcondition of assemble might not hold. Assertion (Result() == ((emit(lead) + trim_block(included, n)) + emit(trail))) might not hold.' (7.96s, exit 1). So the pre-patch impl is rejected by the FORMAL clause alone: the discrimination lives in the Ensures, and the prose narration carries no information the formal spec does not already carry -- there is nothing to strip that would turn the view into a hint.

ARTIFACT-STEERING CHECK, reported as its own finding per the brief. leakage.reviewer_directed over every file in the bundle -> ZERO hits. My independent grep for attacker/reviewer/G-PANEL/'you should submit'/'honest verdict'/'record this'/NO-LEAKAGE over model.py, refinement.md and mapping.md -> no hits. verdict.md DOES contain a prior G-PANEL-3 note that ends '**VERDICT NO-LEAKAGE**', but that is the bundle's audit ledger recording a past role, not text addressed to me or arguing a disposition; I did not read it before forming my own conclusion and my verdict rests solely on the spec_view hash match, the armed screen, the manual sweep, the problem_statement substring checks, and the stripped-prepatch verifier run above. No file in this bundle instructs this panel. Out of scope but noted for completeness: refinement.md and mapping.md discuss the gold hunk and the reorder explicitly (author-side documents, not part of the solver-visible spec view), and meta.json's modeled_functions/localization channel names LiteralIncludeReader.read -- the harness's deliberate 'where to edit' channel, gated separately, outside this role's view.

**VERDICT NO-LEAKAGE:** the spec view discloses nothing about the gold edit beyond what the public problem_statement already requests.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
