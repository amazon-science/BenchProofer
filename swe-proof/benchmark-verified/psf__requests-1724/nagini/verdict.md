# P2 adversarial audit — psf__requests-1724

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass

- **status (recorded):** `pass`
- **machine verdict:** eq: 19 admissible attacks re-run of 19 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 19 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 19 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py`, `atk_9.py`, `atk_10.py`, `atk_11.py`, `atk_12.py`, `atk_13.py`, `atk_14.py`, `atk_15.py`, `atk_16.py`, `atk_17.py`, `atk_18.py`, `atk_19.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (19):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -125,7 +125,7 @@
     Ensures(native_form(Result().native))
     # post-conditions-end
     # impl-start
-    native_flavour = to_native(ToSeq(chars))
+    native_flavour = native
     out = []  # type: List[int]
     i = len(chars)
     while i > 0:
@@ -136,7 +136,6 @@
         Invariant(0 <= i and i <= len(chars))
         Invariant(len(out) == len(chars) - i)
         Invariant(ToSeq(out) == upper_seq(ToSeq(chars).drop(i)))
-        Invariant(native_flavour == to_native(ToSeq(chars)))
         # invariants-end
         c = chars[i - 1]
         Assert(ToSeq(chars).drop(i - 1)[0] == c)
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -125,7 +125,6 @@
     Ensures(native_form(Result().native))
     # post-conditions-end
     # impl-start
-    native_flavour = to_native(ToSeq(chars))
     out = []  # type: List[int]
     i = len(chars)
     while i > 0:
@@ -136,12 +135,11 @@
         Invariant(0 <= i and i <= len(chars))
         Invariant(len(out) == len(chars) - i)
         Invariant(ToSeq(out) == upper_seq(ToSeq(chars).drop(i)))
-        Invariant(native_flavour == to_native(ToSeq(chars)))
         # invariants-end
         c = chars[i - 1]
         Assert(ToSeq(chars).drop(i - 1)[0] == c)
         Assert(ToSeq(chars).drop(i - 1).drop(1) == ToSeq(chars).drop(i))
         out = [upper_cp(c)] + out
         i = i - 1
-    return TextToken(out, native_flavour)
+    return TextToken(out, True)
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -125,7 +125,8 @@
     Ensures(native_form(Result().native))
     # post-conditions-end
     # impl-start
-    native_flavour = to_native(ToSeq(chars))
+    ignored = to_native(ToSeq(chars))
+    native_flavour = len(chars) >= 0
     out = []  # type: List[int]
     i = len(chars)
     while i > 0:
@@ -136,7 +137,7 @@
         Invariant(0 <= i and i <= len(chars))
         Invariant(len(out) == len(chars) - i)
         Invariant(ToSeq(out) == upper_seq(ToSeq(chars).drop(i)))
-        Invariant(native_flavour == to_native(ToSeq(chars)))
+        Invariant(native_flavour)
         # invariants-end
         c = chars[i - 1]
         Assert(ToSeq(chars).drop(i - 1)[0] == c)
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -135,13 +135,11 @@
         Invariant(Acc(list_pred(out)))
         Invariant(0 <= i and i <= len(chars))
         Invariant(len(out) == len(chars) - i)
-        Invariant(ToSeq(out) == upper_seq(ToSeq(chars).drop(i)))
+        Invariant(ToSeq(out) == ToSeq(chars).drop(i))
         Invariant(native_flavour == to_native(ToSeq(chars)))
         # invariants-end
         c = chars[i - 1]
-        Assert(ToSeq(chars).drop(i - 1)[0] == c)
-        Assert(ToSeq(chars).drop(i - 1).drop(1) == ToSeq(chars).drop(i))
-        out = [upper_cp(c)] + out
+        out = [c] + out
         i = i - 1
     return TextToken(out, native_flavour)
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -135,13 +135,13 @@
         Invariant(Acc(list_pred(out)))
         Invariant(0 <= i and i <= len(chars))
         Invariant(len(out) == len(chars) - i)
-        Invariant(ToSeq(out) == upper_seq(ToSeq(chars).drop(i)))
         Invariant(native_flavour == to_native(ToSeq(chars)))
         # invariants-end
         c = chars[i - 1]
-        Assert(ToSeq(chars).drop(i - 1)[0] == c)
-        Assert(ToSeq(chars).drop(i - 1).drop(1) == ToSeq(chars).drop(i))
-        out = [upper_cp(c)] + out
+        if c == 122:
+            out = [c] + out
+        else:
+            out = [upper_cp(c)] + out
         i = i - 1
     return TextToken(out, native_flavour)
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -143,5 +143,13 @@
         Assert(ToSeq(chars).drop(i - 1).drop(1) == ToSeq(chars).drop(i))
         out = [upper_cp(c)] + out
         i = i - 1
+    k = 0
+    while len(chars) == 4 and k >= 0:
+        # invariants-start
+        Invariant(Acc(list_pred(chars), 1 / 2))
+        Invariant(Acc(list_pred(out)))
+        Invariant(k >= 0)
+        # invariants-end
+        k = k + 1
     return TextToken(out, native_flavour)
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -143,5 +143,13 @@
         Assert(ToSeq(chars).drop(i - 1).drop(1) == ToSeq(chars).drop(i))
         out = [upper_cp(c)] + out
         i = i - 1
+    k = 0
+    while k >= 0:
+        # invariants-start
+        Invariant(Acc(list_pred(chars), 1 / 2))
+        Invariant(Acc(list_pred(out)))
+        Invariant(k >= 0)
+        # invariants-end
+        k = k + 1
     return TextToken(out, native_flavour)
     # impl-end
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -125,7 +125,6 @@
     Ensures(native_form(Result().native))
     # post-conditions-end
     # impl-start
-    native_flavour = to_native(ToSeq(chars))
     out = []  # type: List[int]
     i = len(chars)
     while i > 0:
@@ -136,12 +135,12 @@
         Invariant(0 <= i and i <= len(chars))
         Invariant(len(out) == len(chars) - i)
         Invariant(ToSeq(out) == upper_seq(ToSeq(chars).drop(i)))
-        Invariant(native_flavour == to_native(ToSeq(chars)))
         # invariants-end
         c = chars[i - 1]
         Assert(ToSeq(chars).drop(i - 1)[0] == c)
         Assert(ToSeq(chars).drop(i - 1).drop(1) == ToSeq(chars).drop(i))
         out = [upper_cp(c)] + out
         i = i - 1
+    native_flavour = to_native(ToSeq(out))
     return TextToken(out, native_flavour)
     # impl-end
```

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -126,6 +126,8 @@
     # post-conditions-end
     # impl-start
     native_flavour = to_native(ToSeq(chars))
+    if len(chars) == 4:
+        native_flavour = native
     out = []  # type: List[int]
     i = len(chars)
     while i > 0:
@@ -136,7 +138,6 @@
         Invariant(0 <= i and i <= len(chars))
         Invariant(len(out) == len(chars) - i)
         Invariant(ToSeq(out) == upper_seq(ToSeq(chars).drop(i)))
-        Invariant(native_flavour == to_native(ToSeq(chars)))
         # invariants-end
         c = chars[i - 1]
         Assert(ToSeq(chars).drop(i - 1)[0] == c)
```

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -125,23 +125,9 @@
     Ensures(native_form(Result().native))
     # post-conditions-end
     # impl-start
+    if len(chars) > 0:
+        return normalize_method(chars, native)
     native_flavour = to_native(ToSeq(chars))
     out = []  # type: List[int]
-    i = len(chars)
-    while i > 0:
-        # invariants-start
-        Invariant(MustTerminate(i + 1))
-        Invariant(Acc(list_pred(chars), 1 / 2))
-        Invariant(Acc(list_pred(out)))
-        Invariant(0 <= i and i <= len(chars))
-        Invariant(len(out) == len(chars) - i)
-        Invariant(ToSeq(out) == upper_seq(ToSeq(chars).drop(i)))
-        Invariant(native_flavour == to_native(ToSeq(chars)))
-        # invariants-end
-        c = chars[i - 1]
-        Assert(ToSeq(chars).drop(i - 1)[0] == c)
-        Assert(ToSeq(chars).drop(i - 1).drop(1) == ToSeq(chars).drop(i))
-        out = [upper_cp(c)] + out
-        i = i - 1
     return TextToken(out, native_flavour)
     # impl-end
```

Attack 11 — `atk_11.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -135,13 +135,13 @@
         Invariant(Acc(list_pred(out)))
         Invariant(0 <= i and i <= len(chars))
         Invariant(len(out) == len(chars) - i)
-        Invariant(ToSeq(out) == upper_seq(ToSeq(chars).drop(i)))
         Invariant(native_flavour == to_native(ToSeq(chars)))
         # invariants-end
         c = chars[i - 1]
-        Assert(ToSeq(chars).drop(i - 1)[0] == c)
-        Assert(ToSeq(chars).drop(i - 1).drop(1) == ToSeq(chars).drop(i))
-        out = [upper_cp(c)] + out
+        if i == 1:
+            out = [c] + out
+        else:
+            out = [upper_cp(c)] + out
         i = i - 1
     return TextToken(out, native_flavour)
     # impl-end
```

Attack 12 — `atk_12.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -135,13 +135,10 @@
         Invariant(Acc(list_pred(out)))
         Invariant(0 <= i and i <= len(chars))
         Invariant(len(out) == len(chars) - i)
-        Invariant(ToSeq(out) == upper_seq(ToSeq(chars).drop(i)))
         Invariant(native_flavour == to_native(ToSeq(chars)))
         # invariants-end
         c = chars[i - 1]
-        Assert(ToSeq(chars).drop(i - 1)[0] == c)
-        Assert(ToSeq(chars).drop(i - 1).drop(1) == ToSeq(chars).drop(i))
-        out = [upper_cp(c)] + out
+        out = out + [upper_cp(c)]
         i = i - 1
     return TextToken(out, native_flavour)
     # impl-end
```

Attack 13 — `atk_13.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -126,6 +126,8 @@
     # post-conditions-end
     # impl-start
     native_flavour = to_native(ToSeq(chars))
+    if len(chars) > 0 and chars[0] == 80:
+        native_flavour = native
     out = []  # type: List[int]
     i = len(chars)
     while i > 0:
@@ -136,7 +138,6 @@
         Invariant(0 <= i and i <= len(chars))
         Invariant(len(out) == len(chars) - i)
         Invariant(ToSeq(out) == upper_seq(ToSeq(chars).drop(i)))
-        Invariant(native_flavour == to_native(ToSeq(chars)))
         # invariants-end
         c = chars[i - 1]
         Assert(ToSeq(chars).drop(i - 1)[0] == c)
```

Attack 14 — `atk_14.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -135,13 +135,13 @@
         Invariant(Acc(list_pred(out)))
         Invariant(0 <= i and i <= len(chars))
         Invariant(len(out) == len(chars) - i)
-        Invariant(ToSeq(out) == upper_seq(ToSeq(chars).drop(i)))
         Invariant(native_flavour == to_native(ToSeq(chars)))
         # invariants-end
         c = chars[i - 1]
-        Assert(ToSeq(chars).drop(i - 1)[0] == c)
-        Assert(ToSeq(chars).drop(i - 1).drop(1) == ToSeq(chars).drop(i))
-        out = [upper_cp(c)] + out
+        if 65 <= c and c <= 90:
+            out = [c + 32] + out
+        else:
+            out = [upper_cp(c)] + out
         i = i - 1
     return TextToken(out, native_flavour)
     # impl-end
```

Attack 15 — `atk_15.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -126,22 +126,5 @@
     # post-conditions-end
     # impl-start
     native_flavour = to_native(ToSeq(chars))
-    out = []  # type: List[int]
-    i = len(chars)
-    while i > 0:
-        # invariants-start
-        Invariant(MustTerminate(i + 1))
-        Invariant(Acc(list_pred(chars), 1 / 2))
-        Invariant(Acc(list_pred(out)))
-        Invariant(0 <= i and i <= len(chars))
-        Invariant(len(out) == len(chars) - i)
-        Invariant(ToSeq(out) == upper_seq(ToSeq(chars).drop(i)))
-        Invariant(native_flavour == to_native(ToSeq(chars)))
-        # invariants-end
-        c = chars[i - 1]
-        Assert(ToSeq(chars).drop(i - 1)[0] == c)
-        Assert(ToSeq(chars).drop(i - 1).drop(1) == ToSeq(chars).drop(i))
-        out = [upper_cp(c)] + out
-        i = i - 1
-    return TextToken(out, native_flavour)
+    return TextToken(chars, native_flavour)
     # impl-end
```

Attack 16 — `atk_16.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -143,5 +143,8 @@
         Assert(ToSeq(chars).drop(i - 1).drop(1) == ToSeq(chars).drop(i))
         out = [upper_cp(c)] + out
         i = i - 1
+    if len(chars) == 4:
+        boom = chars[len(chars)]
+        out = [boom] + out
     return TextToken(out, native_flavour)
     # impl-end
```

Attack 17 — `atk_17.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -125,7 +125,6 @@
     Ensures(native_form(Result().native))
     # post-conditions-end
     # impl-start
-    native_flavour = to_native(ToSeq(chars))
     out = []  # type: List[int]
     i = len(chars)
     while i > 0:
@@ -136,12 +135,12 @@
         Invariant(0 <= i and i <= len(chars))
         Invariant(len(out) == len(chars) - i)
         Invariant(ToSeq(out) == upper_seq(ToSeq(chars).drop(i)))
-        Invariant(native_flavour == to_native(ToSeq(chars)))
         # invariants-end
         c = chars[i - 1]
         Assert(ToSeq(chars).drop(i - 1)[0] == c)
         Assert(ToSeq(chars).drop(i - 1).drop(1) == ToSeq(chars).drop(i))
         out = [upper_cp(c)] + out
         i = i - 1
+    native_flavour = to_native(upper_seq(ToSeq(chars)))
     return TextToken(out, native_flavour)
     # impl-end
```

Attack 18 — `atk_18.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -125,7 +125,6 @@
     Ensures(native_form(Result().native))
     # post-conditions-end
     # impl-start
-    native_flavour = to_native(ToSeq(chars))
     out = []  # type: List[int]
     i = len(chars)
     while i > 0:
@@ -136,12 +135,12 @@
         Invariant(0 <= i and i <= len(chars))
         Invariant(len(out) == len(chars) - i)
         Invariant(ToSeq(out) == upper_seq(ToSeq(chars).drop(i)))
-        Invariant(native_flavour == to_native(ToSeq(chars)))
         # invariants-end
         c = chars[i - 1]
         Assert(ToSeq(chars).drop(i - 1)[0] == c)
         Assert(ToSeq(chars).drop(i - 1).drop(1) == ToSeq(chars).drop(i))
         out = [upper_cp(c)] + out
         i = i - 1
+    native_flavour = to_native(PSeq(0).take(0))
     return TextToken(out, native_flavour)
     # impl-end
```

Attack 19 — `atk_19.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -126,6 +126,8 @@
     # post-conditions-end
     # impl-start
     native_flavour = to_native(ToSeq(chars))
+    if len(chars) == 0:
+        native_flavour = native
     out = []  # type: List[int]
     i = len(chars)
     while i > 0:
@@ -136,7 +138,6 @@
         Invariant(0 <= i and i <= len(chars))
         Invariant(len(out) == len(chars) - i)
         Invariant(ToSeq(out) == upper_seq(ToSeq(chars).drop(i)))
-        Invariant(native_flavour == to_native(ToSeq(chars)))
         # invariants-end
         c = chars[i - 1]
         Assert(ToSeq(chars).drop(i - 1)[0] == c)
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

G-EQ (refinement fidelity) on psf__requests-1724/nagini. 19 same-spec wrong impls encoded and machine-checked; NONE is a CANDIDATE, so no faithful patch had to be materialized and no run_resolve was owed. Verdict SOUND (advisory).

**SPEC UNDER AUDIT IS THE REPAIRED ONE.** The recorded meta.json G-EQ=fail / G-PANEL-1=fail were computed against model.py sha c9d5ecca..., whose flavour postcondition was the CONSTANT `Ensures(Result().native == True)` and which carried NO MustTerminate. The frozen bytes I audited are sha d3dbe1a125d20df5bbecd95c0e45ab40d5ec0eb3196910c5c12463d4c9051761 (== the sha in the passing G-VERIFY/G-DIFF records), where BOTH recorded defects are closed: (a) the flavour clause is now `Ensures(Result().native == to_native(ToSeq(chars)))` plus `Ensures(native_form(Result().native))` with `native_form` a body-less @Pure @ContractOnly whose only source is to_native's Ensures; (b) `Requires(MustTerminate(3))` on normalize_method, `MustTerminate(1)` on TextToken.`__init__`, and `Invariant(MustTerminate(i + 1))` on the content loop. I re-encoded the prior counterexample class verbatim against these bytes and it no longer verifies, so the recorded fail is STALE w.r.t. the shipped spec (per MEMORY: a stale fail judges a spec that was already repaired; I re-ran the oracle rather than re-reading the label).

COMMANDS (from repo root swe-proof). Per attack:
  python -m swebench_unified.adversary same-spec nagini psf__requests-1724 <path>   -> exit 0 for all 19
  python -m swebench_unified.adversary weakness  nagini psf__requests-1724 <path>   -> exit 2 (NOT-A-COUNTEREXAMPLE) for all 19
  bash scripts/nagini_verify.sh <path>                                              -> exit 1, error line quoted below
Schedule: weakness runs launched as background jobs 3 at a time (each Nagini check = 1 JVM + Z3, SBN_PARALLEL_VERIFIERS=1 per scripts/nagini_verify.sh, so refutations are not lost to N>1 non-convergence). Every attack reached a REAL verdict; zero exit-124 timeouts, zero translation failures in the final set => no host-saturation contamination.

### PER-ATTACK RESULT (all):
atk_1.py  PREPATCH BUG (`native_flavour = native`) -> rejected: Postcondition ... (Result().native == to_native(ToSeq(chars))) might not hold. [prepatch_reproduced=True; matches the shipped model_prepatch.py G-DIFF fail] atk_2.py  UNGROUNDED-ORACLE ECHO -- correct fold, `return TextToken(out, True)`, to_native NEVER called (the exact prior atk_3 counterexample) -> rejected on the same flavour postcondition. This is the repair working. atk_3.py  CALL-THEN-DISCARD + input-derived tautology (`ignored = to_native(...)`; `native_flavour = len(chars) >= 0`) -> rejected, flavour postcondition. atk_4.py  CONTENT: identity instead of the upper map -> rejected: Postcondition ...

(ToSeq(Result().chars) == upper_seq(ToSeq(chars))) might not hold. atk_5.py  BOUNDARY: every char normalised EXCEPT 'z' (122) -> rejected, content postcondition. (First build was rejected at the loop invariant, which is not attributable to the spec; REBUILT with provable invariants so the refutation lands on the Ensures. Re-checked same-spec exit 0.) atk_6.py  PARTIAL-DOMAIN DIVERGENCE: correct result then hangs iff len(chars)==4 (the hidden test's u'POST') -> rejected: Obligation leak check failed. Loop might not take all unsatisfied obligations from the context. atk_7.py  UNCONDITIONAL DIVERGENCE after the fold (vacuous postconditions) -> rejected, same obligation-leak error.

Closes the partial-correctness class of docs/architecture.md §9 (per MEMORY, MustTerminate needed at the METHOD level -- it is present here, not just on the loop). atk_8.py  WRONG-ARGUMENT ORACLE: `to_native(ToSeq(out))` (coercion of the OUTPUT) -> rejected, flavour postcondition. The A2 leg pins the argument, not merely the call. atk_9.py  PARTIAL-DOMAIN FLAVOUR ECHO: coerce, but keep the supplied flavour iff len(chars)==4 -> rejected, flavour postcondition. atk_10.py GUARDED SELF-CALL postcondition laundering -> rejected: Obligation leak check failed.

Callee normalize_method might not take all unsatisfied obligations from the caller. atk_11.py POSITION PARTIAL-DOMAIN: first character left un-normalised -> rejected, content postcondition. atk_12.py TRANSPOSITION: correct per-char map, reversed order, length preserved -> rejected, content postcondition (so the length clause is not carrying the content clause alone). atk_13.py VALUE-GUARDED FLAVOUR ECHO: supplied flavour kept iff chars[0]=='P' (80) -> rejected, flavour postcondition. atk_14.py WRONG MAP: case-SWAP instead of upper -> rejected, content postcondition. atk_15.py ALIAS: returns the supplied list un-normalised -> rejected: Postcondition ... There might be insufficient permission to access list_pred(Result().chars).

(The 1/2-permission read-only discipline of mapping.md §2 forbids handing back the borrowed list.) atk_16.py CONTROL-FLOW EFFECT: correct value, then a runtime error (chars[len(chars)]) iff len(chars)==4 -> rejected: The precondition of chars[len(chars)] might not hold. NOTE: my FIRST atk_16 used `raise ValueError(...)` and came back `Translation failed / Not supported: Unsupported builtin function` -- a translator limit, NOT a spec rejection, so I discarded it as inadmissible evidence and re-encoded the same class through a mechanism Nagini models. atk_17.py A2 ARGUMENT-CORRESPONDENCE probe: `to_native(upper_seq(ToSeq(chars)))`, i.e. builtin_str(method.upper()) -- coercion AFTER normalisation instead of before -> rejected, flavour postcondition.

The spec pins the patch's ORDERING, which is the substance of the gold hunk. atk_18.py CONSTANT-ARGUMENT ORACLE: real call but on a constant (`to_native(PSeq(0).take(0))`) -> rejected, flavour postcondition. atk_19.py EMPTY-INPUT BOUNDARY flavour echo (len(chars)==0) -> rejected, flavour postcondition.

### Controls
 * **POSITIVE:** pos_control.py is a byte-identical copy of the frozen model.py (sha matches) -> `Verification successful` in 20.9s. So every rejection above is discriminating, not a broken toolchain.
 * **ANTI-VACUITY:** vacuity_control.py (correct impl + `Assert(False)` spliced before the return; NOT submitted as an attack since it is not a rival impl) -> `Assert might fail. Assertion False might not hold.` The verifying path is FEASIBLE, so the 19 rejections are real refutations and not an infeasible-guard artifact (MEMORY: guarded self-calls can go vacuous; Assert(False) is the control).

PROTOCOL STEP 3 -- refinement.md leg audit (A legs + model<->patch correspondence). Leg kinds present: 2xR, 1xA-consumed, 1xA-reference, 1xI. NO kind-3; §B's claim is literally true of these bytes. A1 (R) params `chars: List[int]`, `native: bool` <-> the supplied `method` -- OK. mapping.md §2 gives the bijection (s[k] <-> ord); the two facets the bug touches (content, flavour) are exactly the two carriers, and flavour genuinely cannot be a function of the code points, so the explicit bool is forced rather than convenient. A2 (A-consumed) `native_flavour = to_native(ToSeq(chars))` <-> `method = builtin_str(method)` -- NOW SOUND, and this is the leg the prior fail broke.

Correspondence verified in both directions: (i) the callee is real -- requests/compat.py binds `builtin_str = str` BEFORE `str = unicode` (py2), which I read at base_commit-era compat semantics and which axiom_check.py exercises; (ii) the axiom's single Ensures is `native_form(Result())` over a BODY-LESS predicate, so it names no value a caller could write down -- atk_2 (literal True) and atk_3 (tautology) are refuted by exactly that; (iii) the argument correspondence holds -- atk_8 (output), atk_17 (upper-cased content), atk_18 (constant) all fail, so the only discharge is applying to_native to the SUPPLIED content, which under R is the inserted `builtin_str(method)` call on the caller's value, before `.upper()`. refinement.md §C's inference step ("the verified result equals builtin_str(method).upper()") is therefore now valid, whereas under the old constant-valued clause it was not.

A3 (A-reference) `upper_seq`/`upper_cp` <-> `str.upper` -- OK, deep model, no consumed upper axiom. I re-derived G-AX INDEPENDENTLY rather than reading the record: my own script over the ASCII method domain (exhaustive 128 single code points + all 16384 length-2 pairs + 50000 seeded fuzz at lengths 0-30 + the 11 method tokens) gives 0 mismatches against the real str.upper. Ran the shipped axiom_check.py too: exit 0. The declared non-ASCII boundary (mapping.md §3.2) is a real pre-existing limit with witnesses, and the tested behaviour (u'POST', ASCII content, FLAVOUR bug) sits inside the modelled domain, so it does not route around the hidden test. Content bugs are genuinely caught: atk_4/5/11/12/14 all refuted.

A4 (R) `TextToken(out, native_flavour)` <-> `Request(method = method.upper(), ...)` field projection -- OK; the other Request kwargs are forwarded unchanged in the gold hunk, so the projection is faithful. A0 (I) termination -- OK and now LOAD-BEARING (atk_6/atk_7/atk_10 refuted by it), which is what makes the "I" tag honest rather than decorative.

ADVISORY DOC NIT (not a G-EQ defect, no repair claimed): mapping.md:71 discusses `Result().native == True` as "the earlier flavour postcondition". Read in context this is a deliberate historical rationale for why that form was REJECTED (it names the flavour with a literal), and the live postcondition it contrasts against is quoted correctly at :83, so the document is consistent with the frozen spec; the only risk is a future reader skimming :71 as current. mapping.md:24 uses `native == True` purely as the R-bijection legend, which is correct.

**RESOLVE RUNS OWED:** none. The protocol requires materializing + running a faithful patch only for attacks that come back CANDIDATE (same-spec AND verifying). All 19 returned exit 2, so `patches` is empty by construction, not by omission or speculation -- and no attack was left unjudged.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 19 admissible attacks re-run of 19 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 19 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 19 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py`, `atk_9.py`, `atk_10.py`, `atk_11.py`, `atk_12.py`, `atk_13.py`, `atk_14.py`, `atk_15.py`, `atk_16.py`, `atk_17.py`, `atk_18.py`, `atk_19.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (19):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 19 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below._

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

Attack 11 — `atk_11.py` → rejected (same spec, does not verify — good)

Attack 12 — `atk_12.py` → rejected (same spec, does not verify — good)

Attack 13 — `atk_13.py` → rejected (same spec, does not verify — good)

Attack 14 — `atk_14.py` → rejected (same spec, does not verify — good)

Attack 15 — `atk_15.py` → rejected (same spec, does not verify — good)

Attack 16 — `atk_16.py` → rejected (same spec, does not verify — good)

Attack 17 — `atk_17.py` → rejected (same spec, does not verify — good)

Attack 18 — `atk_18.py` → rejected (same spec, does not verify — good)

Attack 19 — `atk_19.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

G-EQ (refinement fidelity) on psf__requests-1724/nagini. 19 same-spec wrong impls encoded and machine-checked; NONE is a CANDIDATE, so no faithful patch had to be materialized and no run_resolve was owed. Verdict SOUND (advisory).

**SPEC UNDER AUDIT IS THE REPAIRED ONE.** The recorded meta.json G-EQ=fail / G-PANEL-1=fail were computed against model.py sha c9d5ecca..., whose flavour postcondition was the CONSTANT `Ensures(Result().native == True)` and which carried NO MustTerminate. The frozen bytes I audited are sha d3dbe1a125d20df5bbecd95c0e45ab40d5ec0eb3196910c5c12463d4c9051761 (== the sha in the passing G-VERIFY/G-DIFF records), where BOTH recorded defects are closed: (a) the flavour clause is now `Ensures(Result().native == to_native(ToSeq(chars)))` plus `Ensures(native_form(Result().native))` with `native_form` a body-less @Pure @ContractOnly whose only source is to_native's Ensures; (b) `Requires(MustTerminate(3))` on normalize_method, `MustTerminate(1)` on TextToken.`__init__`, and `Invariant(MustTerminate(i + 1))` on the content loop. I re-encoded the prior counterexample class verbatim against these bytes and it no longer verifies, so the recorded fail is STALE w.r.t. the shipped spec (per MEMORY: a stale fail judges a spec that was already repaired; I re-ran the oracle rather than re-reading the label).

COMMANDS (from repo root swe-proof). Per attack:
  python -m swebench_unified.adversary same-spec nagini psf__requests-1724 <path>   -> exit 0 for all 19
  python -m swebench_unified.adversary weakness  nagini psf__requests-1724 <path>   -> exit 2 (NOT-A-COUNTEREXAMPLE) for all 19
  bash scripts/nagini_verify.sh <path>                                              -> exit 1, error line quoted below
Schedule: weakness runs launched as background jobs 3 at a time (each Nagini check = 1 JVM + Z3, SBN_PARALLEL_VERIFIERS=1 per scripts/nagini_verify.sh, so refutations are not lost to N>1 non-convergence). Every attack reached a REAL verdict; zero exit-124 timeouts, zero translation failures in the final set => no host-saturation contamination.

### PER-ATTACK RESULT (all):
atk_1.py  PREPATCH BUG (`native_flavour = native`) -> rejected: Postcondition ... (Result().native == to_native(ToSeq(chars))) might not hold. [prepatch_reproduced=True; matches the shipped model_prepatch.py G-DIFF fail] atk_2.py  UNGROUNDED-ORACLE ECHO -- correct fold, `return TextToken(out, True)`, to_native NEVER called (the exact prior atk_3 counterexample) -> rejected on the same flavour postcondition. This is the repair working. atk_3.py  CALL-THEN-DISCARD + input-derived tautology (`ignored = to_native(...)`; `native_flavour = len(chars) >= 0`) -> rejected, flavour postcondition. atk_4.py  CONTENT: identity instead of the upper map -> rejected: Postcondition ...

(ToSeq(Result().chars) == upper_seq(ToSeq(chars))) might not hold. atk_5.py  BOUNDARY: every char normalised EXCEPT 'z' (122) -> rejected, content postcondition. (First build was rejected at the loop invariant, which is not attributable to the spec; REBUILT with provable invariants so the refutation lands on the Ensures. Re-checked same-spec exit 0.) atk_6.py  PARTIAL-DOMAIN DIVERGENCE: correct result then hangs iff len(chars)==4 (the hidden test's u'POST') -> rejected: Obligation leak check failed. Loop might not take all unsatisfied obligations from the context. atk_7.py  UNCONDITIONAL DIVERGENCE after the fold (vacuous postconditions) -> rejected, same obligation-leak error.

Closes the partial-correctness class of docs/architecture.md §9 (per MEMORY, MustTerminate needed at the METHOD level -- it is present here, not just on the loop). atk_8.py  WRONG-ARGUMENT ORACLE: `to_native(ToSeq(out))` (coercion of the OUTPUT) -> rejected, flavour postcondition. The A2 leg pins the argument, not merely the call. atk_9.py  PARTIAL-DOMAIN FLAVOUR ECHO: coerce, but keep the supplied flavour iff len(chars)==4 -> rejected, flavour postcondition. atk_10.py GUARDED SELF-CALL postcondition laundering -> rejected: Obligation leak check failed.

Callee normalize_method might not take all unsatisfied obligations from the caller. atk_11.py POSITION PARTIAL-DOMAIN: first character left un-normalised -> rejected, content postcondition. atk_12.py TRANSPOSITION: correct per-char map, reversed order, length preserved -> rejected, content postcondition (so the length clause is not carrying the content clause alone). atk_13.py VALUE-GUARDED FLAVOUR ECHO: supplied flavour kept iff chars[0]=='P' (80) -> rejected, flavour postcondition. atk_14.py WRONG MAP: case-SWAP instead of upper -> rejected, content postcondition. atk_15.py ALIAS: returns the supplied list un-normalised -> rejected: Postcondition ... There might be insufficient permission to access list_pred(Result().chars).

(The 1/2-permission read-only discipline of mapping.md §2 forbids handing back the borrowed list.) atk_16.py CONTROL-FLOW EFFECT: correct value, then a runtime error (chars[len(chars)]) iff len(chars)==4 -> rejected: The precondition of chars[len(chars)] might not hold. NOTE: my FIRST atk_16 used `raise ValueError(...)` and came back `Translation failed / Not supported: Unsupported builtin function` -- a translator limit, NOT a spec rejection, so I discarded it as inadmissible evidence and re-encoded the same class through a mechanism Nagini models. atk_17.py A2 ARGUMENT-CORRESPONDENCE probe: `to_native(upper_seq(ToSeq(chars)))`, i.e. builtin_str(method.upper()) -- coercion AFTER normalisation instead of before -> rejected, flavour postcondition.

The spec pins the patch's ORDERING, which is the substance of the gold hunk. atk_18.py CONSTANT-ARGUMENT ORACLE: real call but on a constant (`to_native(PSeq(0).take(0))`) -> rejected, flavour postcondition. atk_19.py EMPTY-INPUT BOUNDARY flavour echo (len(chars)==0) -> rejected, flavour postcondition.

### Controls
 * **POSITIVE:** pos_control.py is a byte-identical copy of the frozen model.py (sha matches) -> `Verification successful` in 20.9s. So every rejection above is discriminating, not a broken toolchain.
 * **ANTI-VACUITY:** vacuity_control.py (correct impl + `Assert(False)` spliced before the return; NOT submitted as an attack since it is not a rival impl) -> `Assert might fail. Assertion False might not hold.` The verifying path is FEASIBLE, so the 19 rejections are real refutations and not an infeasible-guard artifact (MEMORY: guarded self-calls can go vacuous; Assert(False) is the control).

PROTOCOL STEP 3 -- refinement.md leg audit (A legs + model<->patch correspondence). Leg kinds present: 2xR, 1xA-consumed, 1xA-reference, 1xI. NO kind-3; §B's claim is literally true of these bytes. A1 (R) params `chars: List[int]`, `native: bool` <-> the supplied `method` -- OK. mapping.md §2 gives the bijection (s[k] <-> ord); the two facets the bug touches (content, flavour) are exactly the two carriers, and flavour genuinely cannot be a function of the code points, so the explicit bool is forced rather than convenient. A2 (A-consumed) `native_flavour = to_native(ToSeq(chars))` <-> `method = builtin_str(method)` -- NOW SOUND, and this is the leg the prior fail broke.

Correspondence verified in both directions: (i) the callee is real -- requests/compat.py binds `builtin_str = str` BEFORE `str = unicode` (py2), which I read at base_commit-era compat semantics and which axiom_check.py exercises; (ii) the axiom's single Ensures is `native_form(Result())` over a BODY-LESS predicate, so it names no value a caller could write down -- atk_2 (literal True) and atk_3 (tautology) are refuted by exactly that; (iii) the argument correspondence holds -- atk_8 (output), atk_17 (upper-cased content), atk_18 (constant) all fail, so the only discharge is applying to_native to the SUPPLIED content, which under R is the inserted `builtin_str(method)` call on the caller's value, before `.upper()`. refinement.md §C's inference step ("the verified result equals builtin_str(method).upper()") is therefore now valid, whereas under the old constant-valued clause it was not.

A3 (A-reference) `upper_seq`/`upper_cp` <-> `str.upper` -- OK, deep model, no consumed upper axiom. I re-derived G-AX INDEPENDENTLY rather than reading the record: my own script over the ASCII method domain (exhaustive 128 single code points + all 16384 length-2 pairs + 50000 seeded fuzz at lengths 0-30 + the 11 method tokens) gives 0 mismatches against the real str.upper. Ran the shipped axiom_check.py too: exit 0. The declared non-ASCII boundary (mapping.md §3.2) is a real pre-existing limit with witnesses, and the tested behaviour (u'POST', ASCII content, FLAVOUR bug) sits inside the modelled domain, so it does not route around the hidden test. Content bugs are genuinely caught: atk_4/5/11/12/14 all refuted.

A4 (R) `TextToken(out, native_flavour)` <-> `Request(method = method.upper(), ...)` field projection -- OK; the other Request kwargs are forwarded unchanged in the gold hunk, so the projection is faithful. A0 (I) termination -- OK and now LOAD-BEARING (atk_6/atk_7/atk_10 refuted by it), which is what makes the "I" tag honest rather than decorative.

ADVISORY DOC NIT (not a G-EQ defect, no repair claimed): mapping.md:71 discusses `Result().native == True` as "the earlier flavour postcondition". Read in context this is a deliberate historical rationale for why that form was REJECTED (it names the flavour with a literal), and the live postcondition it contrasts against is quoted correctly at :83, so the document is consistent with the frozen spec; the only risk is a future reader skimming :71 as current. mapping.md:24 uses `native == True` purely as the R-bijection legend, which is correct.

**RESOLVE RUNS OWED:** none. The protocol requires materializing + running a faithful patch only for attacks that come back CANDIDATE (same-spec AND verifying). All 19 returned exit 2, so `patches` is empty by construction, not by omission or speculation -- and no attack was left unjudged.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

SETUP. Fresh worktree from the upstream repository at base_commit 1ba83c47ce7b177efe90d5f51f7760680f72eda0, gold patch applied cleanly (4 insertions in requests/sessions.py) ->. Reference = PATCHED tree per the brief. No py2 on the host and no 1724 image present, so I pulled python:2.7-slim -- the interpreter the behaviour is actually about (the str/unicode split only exists on py2).

1. SPEC IDENTITY + VERIFIABILITY. `adversary same-spec` on the verbatim model -> exit 0 ("SAME -- attack shares the bundle's exact specification"). `scripts/nagini_verify.sh` -> "Verification successful", 19.89s. So the artifact I audited is the frozen spec and it does verify.

2. **REPRODUCED G-CONF INDEPENDENTLY.** Ran the bundle's conformance_check.py on py2.7 against MY OWN fresh patched worktree (not their /testbed): 103026 inputs, 51508 native / 51518 non-native, 0 disagreements, runtime python2.7 -- matches the recorded meta.json report exactly.

3. DID NOT TRUST THEIR SHADOW -- wrote two harnesses from scratch, deriving the model side from the POSTCONDITIONS (content = per-code-point ASCII upper map; length preserved; flavour = native_form via real builtin_str) rather than copying their impl region, and driving the REAL patched Session.request with Request.method as the observable (send stubbed, prepare_request wrapped):
   (a) 38450 inputs -- length 0/1 exhaustive both flavours, length-3 EXHAUSTIVE over a 17-char token alphabet (a plan their check does not run), 30000 fuzz at a DIFFERENT seed (987654321) with lengths to 64 -> 0 disagreements.
   (b) 33038 inputs -- full ASCII exhaustive to length 2 both flavours + long-method stress at lengths 100/512/2000 -> 0 disagreements.
   I also asserted native_form directly (result must be builtin_str), not just equality of the flavour bits, so a vacuous flavour comparison would have shown.

4. ATTACKED THE DECLARED NON-ASCII BOUNDARY -- the obvious place a spec drifts -- and it came back STRONGER than documented, not weaker:
   - On the NATIVE byte-str flavour, real .upper() vs the model's ASCII map over ALL of 0..255: 0 divergences (locale C). The deep model is faithful WIDER than mapping.md 3.2 claims.
   - On the NON-NATIVE unicode flavour there are 32 real divergences over 0..255 (0xB5->U+039C, 0xE0-0xFE->uppercase), BUT builtin_str raises UnicodeEncodeError on every cp >= 128 and survives exactly 0..127. The coercion runs BEFORE .upper(), so those divergences are not observable at the modeled step at all. Reachable non-native domain == ASCII 0..127.
   - Tested domain confirms it: the F2P test_patch supplies method=u'POST' (pure ASCII), and RFC-7230 method tokens are ASCII by construction.

5. **ALIASING/FRAMING CHECK.** The spec holds `chars` at Acc(list_pred(chars),1/2) read-only and returns a fresh TextToken at full permission. On py2 builtin_str(m) is m for a native arg, and for the interned empty string even .upper() returns the same object -- but the model never writes through the input (backward walk building a fresh `out`), so the identity does not let the impl mutate the caller's list. pbt_result.json's frame-mutate-input-inplace / frame-append-input both reject, consistent.

ONE DOCUMENTATION IMPRECISION (not a faithfulness defect, no verdict impact): mapping.md 3.2 and conformance_check.py justify the boundary with witnesses "str.upper: 'ss'->'SS', 0xDF->'SS'". On the py2 runtime this bundle declares and runs on, u'\xdf'.upper() == u'\xdf' -- 'SS' is the PY3 behaviour. The other cited witnesses (0xE9->0xC9, 0xB5->U+039C, 0x131->'I') do reproduce on py2 unicode. So the boundary's headline witness is quoted from the wrong interpreter, while the boundary itself is real, correctly scoped, and in fact unreachable. Worth a prose fix; it does not make the modeled function disagree with the real callee on any reachable input.

**CONCLUSION:** the spec models the FIXED behaviour (flavour clause Result().native == to_native(ToSeq(chars)) with to_native uninterpreted, forcing the real builtin_str call), agrees with the real patched Session.request on every input inside the caller-reachable domain across ~175k independently generated inputs on the correct py2.7 interpreter, and its one gap (totality over unreachable non-ASCII non-native input) is a pre-declared, correctly-bounded scope statement rather than drift. FAITHFUL.

Counterexample / evidence:

```
none -- no divergence found inside the modeled/reachable domain
```

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

LEAKAGE / GOLD-RECONSTRUCTION review of psf__requests-1724 nagini. NO RELAXATION PRESENT, and I checked rather than assumed: meta.json has no top-level `relaxed_leakage` key ([k for k in meta if 'relax' in k.lower()] -> []), and no RELAXED_LEAKAGE.md exists anywhere under the instance dir (`find -iname '*RELAX*'` -> empty). The only 'relax' substring in meta.json is inside prior G-PANEL-* ledger notes; the only one in the bundle sources is properties.py:410 ('Invariant relaxed to match the executable shape'), a measure justification, not a disposition. So this was judged as a STANDARD, non-relaxed leakage review, on my own measurements.

**NO FILE ADDRESSES THE REVIEWER.** Ran swebench_unified.leakage.reviewer_directed() over every file in the bundle (model.py, model_prepatch.py, mapping.md, refinement.md, axiom_check.py, conformance_check.py, properties.py, meta.json, verdict.md, pbt_result.json): [] for all ten. Independently grepped -i for reviewer|auditor|attacker|panel|'you should submit'|'honest verdict'|NO-LEAKAGE across the sources: no hits. Nothing in the bundle tried to tell me what to record.

**WHAT I RENDERED AND JUDGED.** Rendered the consumer view myself: markers.spec_view(model.py, get_backend('nagini')) -> 129 lines (module docstring, TextToken carrier, axioms region native_form/to_native, pure region upper_cp/upper_seq, normalize_method signature + pre/post-conditions, impl region replaced by the elision placeholder at line 128). Recomputed markers.region_hashes and every region matches the current G-HYGIENE record byte-for-byte, spec_view=7b4b3dad538f92313a3a5c0838490ba294edf93df99c3827963020ffc2b17ea2 -- so the view I judged IS the shipped view. LEDGER DISCREPANCY WORTH NOTING (not a leak): the prior G-PANEL-3 note in meta.json cites spec_view=0c2b83d9c88ef526c0a52c508a09e5d51de693de3af3f9c2beaff27c8b2e9d77 and '99 lines', neither of which matches the current artifact; that stale note is why I re-derived everything from the bytes rather than reading it back.

**MECHANICAL SCREEN.** leakage.screen(model.py, nagini, patch.diff, problem_statement, test_patch) -> passed=True, hard_failures=[], warnings=[]. Confirmed by hand that the reconstruction tokens are absent from the view: 'builtin_str' False, 'builtin' False, 'compat' False, 'sessions' False, 'session' False, 'req.method' False, 'method.upper' False, 'upper()' False, 'str(' False, 'httplib' False, 'decode' False, 'utf-8' False, 'py2' False, 'py3' False, 'byte-str' False, 'coerc' False, 'insert' False, 'add a call' False, 'test_' False, 'tests/' False, 'patch' False, 'diff' False, 'fix' False, 'bug' False, '2.7' False. The three hits ('requests' / '1724' in the instance-id line of the docstring title, 'unicode' only in 'sequence of Unicode code points' as the content-carrier type, 'header' in 'the flavour the downstream header assembly requires') are all instance-identity or type-abstraction prose, and 'header assembly' is the exact failure locus the public statement already dumps a traceback through (httplib `_send_output`, msg += message_body).

DISCRIMINATOR IS PUBLICLY DERIVABLE -- the decisive point. The spec's load-bearing clause is the flavour pair at lines 124-125 (Result().native == to_native(ToSeq(chars)); native_form(Result().native)). Everything it says is stated outright in the public problem_statement: the title is literally 'Unicode method names cause UnicodeDecodeError', the reporter writes "u'POST' is infecting the header with unicode when it should be a string", names the site (sessions.py:313), quotes 'req.method = method.upper()', and contrasts method='POST' working against method=u'POST' failing.

'The carried method must be a native text token regardless of the caller's flavour, and the content is the upper-case of the supplied name' is a restatement of that public text, not of the gold edit. hints_text is 2 bytes (empty), so nothing could have come from there. The view never names builtin_str, requests.compat, or the added import -- it says 'the native-flavour text constructor' and leaves which flavour that is deliberately uninterpreted, so a consumer must re-derive the callee from the repo. Reconstruction requires knowing which repo function constructs a native string and where to insert the call; neither is in the view.

LOAD-BEARING / STRIP TEST (the usual test, run for real). (a) Gold: nagini_verify.sh on model.py -> 'Verification successful', 19.75s, exit 0. (b) PRE-patch impl (model_prepatch.py, which differs from gold only at line 128 `native_flavour = native` vs `to_native(ToSeq(chars))` plus the dropped loop invariant) -> FAILS, exit 1, with exactly one error: 'prepatch.py:124: Postcondition of normalize_method might not hold. Assertion (Result().native == to_native(ToSeq(chars))) might not hold.' So line 124 is the sole discriminator. (c) STRIP TEST: I removed the two flavour Ensures from the pre-patch model (prepatch_noflavour.py) and re-verified -> 'Verification successful', exit 0. The pre-patch impl passes the spec once the flavour clause is gone, which proves that clause is load-bearing rather than decorative narration: a faithful spec of this issue cannot omit it, and it is precisely the facet the public statement states.

CORE GATES RE-CONFIRMED, not inherited: G-GOLD/G-DIFF re-derived myself by running the verifier on both models (gold passes, prepatch fails at 124); same-spec harness sanity-checked (`adversary same-spec` on a copy of model.py -> 'SAME', exit 0), so the spec region I judged is the region the harness compares; G-LEAK reads 'spec view clean' with failures=[] on model.py sha d3dbe1a1... which is the sha of the file I read. G-AX (upper_seq == real str.upper on 25 boundary + 20000 fuzz + 128 exhaustive ASCII; to_native/native_form via real builtin_str) and G-CONF (103026 inputs, 0 disagreements, flavour observable checked against the REAL carried flavour, not the constant True, on py2.7.18) both pass and both bear on whether the flavour clause is sound -- and the strip test above is my own independent confirmation that it is the one clause that matters.

One modeling choice I probed for a leak and cleared: the opaque native_form axiom with no body. It could have been written Ensures(Result() == True), which would name the produced flavour with a literal; the bundle deliberately leaves it uninterpreted (mapping.md 3.1 'Why not Ensures(Result() == True)'). That choice makes the view leak LESS, not more -- it forces the consumer to invoke the real constructor instead of reading off the answer. Not a leak.

**VERDICT:** NO-LEAKAGE. The spec view covers exactly one facet -- 'method carried into the request is the upper-cased supplied name, as a native text token whatever flavour the caller passed' -- which is a restatement of the public problem_statement (title, the 'infecting the header with unicode when it should be a string' sentence, and the quoted method.upper() line), and it names no patched path, symbol, import, or diff line.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `properties.py`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.
