# P2 adversarial audit — sympy__sympy-13031

**Backend:** `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 14 admissible attacks re-run of 14 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 14 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 12 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_8.py`, `atk_9.py`, `atk_10.py`, `atk_11.py`, `atk_13.py`, `atk_14.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_7.py`, `atk_12.py` |

**Non-vacuity.** The positive control `pc_model.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE — no verify⇏correct witness found. 14 same-spec wrong impls were run through `adversary weakness nagini sympy__sympy-13031`; 12 were REJECTED by the frozen spec. The 2 that verified (atk_7, atk_12) had their faithful refined patches MATERIALIZED from the refinement.md/mapping.md R-map and EXECUTED through the official harness (run_resolve): BOTH RESOLVED (completed=True, resolved=True, attempts=1, flaky=False, FAIL_TO_PASS test_sparse_matrix success, PASS_TO_PASS 9/9 success, 0 failures, patch_successfully_applied=True). So neither is a spec weakness.

Materializer validated: re-deriving the GOLD patch from the same R-map produced patch_gold_control.diff, byte-identical to the bundle's patch.diff on every edit line (`diff` over all +/- lines: no output), and it itself resolves. A non-resolving attack patch would therefore have been a real signal, not a materialization artifact.

The 2 candidates are proven ECHOES, not weaknesses: echocheck.py executes gold, atk_7 and atk_12 as abstract functions over every carrier-admissible operand (1 942 five-facet tuples satisfying all Requires, i.e. non-negativity + zero-dimension⇒held==0 + held==0⇒rsum==csum==0 + realisability of the index sums), crossed pairwise = 3 771 364 operand pairs per function, comparing the full return tuple AND the raise/no-raise outcome: 0 differences from gold for either candidate on either function. atk_7 broadens the guard to the whole `a.cols == 0` domain and returns the pre-patch copy `type(self)(other)` with no recursion; atk_12 delegates the degenerate branch to the SIBLING callee with a transposed frame. Both are alternate spellings of the same abstract function — which is exactly what a TIGHT spec should admit.

Root cause of the strength: the postconditions are TOTAL over the five-facet carrier on EVERY returning path. `Result().held == a.held+b.held`, `Result().rsum`, and `Result().csum` (including the `a.cols*b.held` / `a.rows*b.held` placement offset) are unconditional; the degenerate branch is pinned to `(b.rows, b.cols)` by the now-unguarded `Implies(a.cols == 0, ...)`; the sum path FORCES `a.rows == b.rows` and pins `(a.rows, a.cols+b.cols)`; and the Exsures pins the raise to exactly `a.cols != 0 and a.rows != b.rows`. So a verifying same-spec impl cannot differ from gold on any modeled facet.

The defences are load-bearing, not lucky — each was measured by a rejected rival rather than assumed: MustTerminate rejects the broadened-guard-with-recursion diverger (atk_2); the placement clauses reject the wrong-operand offset (atk_4, the G-CONF control (f) re-encoded) and the transposed-coordinate relocation (atk_5); the content clause rejects the shape-correct cell-dropping fabrication (atk_10); the Exsures rejects the reject-before-normalise reordering (atk_6, the F2P symptom itself) and the too-eager raise; the per-site contracts reject the cross-site body swap (atk_14); and the fractional-permission preconditions reject the two identity-returning rivals (atk_8 `return b`, atk_11 `return a`) on permission discipline — these are the ones whose repo images would return an object of the wrong CLASS or alias the receiver, the one F2P observation (`type(a.row_join(b)) == type(a)`) outside the carrier.
```

**Attacks re-run (14):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -159,9 +159,8 @@
             and Acc(b.rsum, 1 / 2) and Acc(b.csum, 1 / 2)
             and a.cols != 0 and a.rows != b.rows)
     # impl-start
-    if a.cols == 0 and a.rows != b.rows:
-        base = Mat(b.rows, 0, 0, 0, 0)  # type: Mat
-        return concat_right(base, b)
+    if a.rows * a.cols == 0:
+        return Mat(b.rows, b.cols, b.held, b.rsum, b.csum)
     if a.rows != b.rows:
         raise ShapeMismatch()
     return Mat(a.rows, a.cols + b.cols, a.held + b.held,
@@ -231,9 +230,8 @@
             and Acc(b.rsum, 1 / 2) and Acc(b.csum, 1 / 2)
             and a.rows != 0 and a.cols != b.cols)
     # impl-start
-    if a.rows == 0 and a.cols != b.cols:
-        base = Mat(0, b.cols, 0, 0, 0)  # type: Mat
-        return concat_below(base, b)
+    if a.rows * a.cols == 0:
+        return Mat(b.rows, b.cols, b.held, b.rsum, b.csum)
     if a.cols != b.cols:
         raise ShapeMismatch()
     return Mat(a.rows + b.rows, a.cols, a.held + b.held,
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -159,7 +159,7 @@
             and Acc(b.rsum, 1 / 2) and Acc(b.csum, 1 / 2)
             and a.cols != 0 and a.rows != b.rows)
     # impl-start
-    if a.cols == 0 and a.rows != b.rows:
+    if a.cols == 0:
         base = Mat(b.rows, 0, 0, 0, 0)  # type: Mat
         return concat_right(base, b)
     if a.rows != b.rows:
@@ -231,7 +231,7 @@
             and Acc(b.rsum, 1 / 2) and Acc(b.csum, 1 / 2)
             and a.rows != 0 and a.cols != b.cols)
     # impl-start
-    if a.rows == 0 and a.cols != b.cols:
+    if a.rows == 0:
         base = Mat(0, b.cols, 0, 0, 0)  # type: Mat
         return concat_below(base, b)
     if a.cols != b.cols:
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -164,6 +164,9 @@
         return concat_right(base, b)
     if a.rows != b.rows:
         raise ShapeMismatch()
+    if a.cols == 1:
+        return Mat(a.rows, a.cols + b.cols, a.held + b.held,
+                   a.rsum + b.rsum, a.csum + b.csum)
     return Mat(a.rows, a.cols + b.cols, a.held + b.held,
                a.rsum + b.rsum, a.csum + b.csum + a.cols * b.held)
     # impl-end
@@ -236,6 +239,9 @@
         return concat_below(base, b)
     if a.cols != b.cols:
         raise ShapeMismatch()
+    if a.rows == 1:
+        return Mat(a.rows + b.rows, a.cols, a.held + b.held,
+                   a.rsum + b.rsum, a.csum + b.csum)
     return Mat(a.rows + b.rows, a.cols, a.held + b.held,
                a.rsum + b.rsum + a.rows * b.held, a.csum + b.csum)
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -165,7 +165,7 @@
     if a.rows != b.rows:
         raise ShapeMismatch()
     return Mat(a.rows, a.cols + b.cols, a.held + b.held,
-               a.rsum + b.rsum, a.csum + b.csum + a.cols * b.held)
+               a.rsum + b.rsum, a.csum + b.csum + b.cols * a.held)
     # impl-end
 
 
@@ -237,5 +237,5 @@
     if a.cols != b.cols:
         raise ShapeMismatch()
     return Mat(a.rows + b.rows, a.cols, a.held + b.held,
-               a.rsum + b.rsum + a.rows * b.held, a.csum + b.csum)
+               a.rsum + b.rsum + b.rows * a.held, a.csum + b.csum)
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -159,9 +159,8 @@
             and Acc(b.rsum, 1 / 2) and Acc(b.csum, 1 / 2)
             and a.cols != 0 and a.rows != b.rows)
     # impl-start
-    if a.cols == 0 and a.rows != b.rows:
-        base = Mat(b.rows, 0, 0, 0, 0)  # type: Mat
-        return concat_right(base, b)
+    if a.cols == 0:
+        return Mat(b.rows, b.cols, b.held, b.csum, b.rsum)
     if a.rows != b.rows:
         raise ShapeMismatch()
     return Mat(a.rows, a.cols + b.cols, a.held + b.held,
@@ -231,9 +230,8 @@
             and Acc(b.rsum, 1 / 2) and Acc(b.csum, 1 / 2)
             and a.rows != 0 and a.cols != b.cols)
     # impl-start
-    if a.rows == 0 and a.cols != b.cols:
-        base = Mat(0, b.cols, 0, 0, 0)  # type: Mat
-        return concat_below(base, b)
+    if a.rows == 0:
+        return Mat(b.rows, b.cols, b.held, b.csum, b.rsum)
     if a.cols != b.cols:
         raise ShapeMismatch()
     return Mat(a.rows + b.rows, a.cols, a.held + b.held,
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -159,9 +159,6 @@
             and Acc(b.rsum, 1 / 2) and Acc(b.csum, 1 / 2)
             and a.cols != 0 and a.rows != b.rows)
     # impl-start
-    if a.cols == 0 and a.rows != b.rows:
-        base = Mat(b.rows, 0, 0, 0, 0)  # type: Mat
-        return concat_right(base, b)
     if a.rows != b.rows:
         raise ShapeMismatch()
     return Mat(a.rows, a.cols + b.cols, a.held + b.held,
@@ -231,9 +228,6 @@
             and Acc(b.rsum, 1 / 2) and Acc(b.csum, 1 / 2)
             and a.rows != 0 and a.cols != b.cols)
     # impl-start
-    if a.rows == 0 and a.cols != b.cols:
-        base = Mat(0, b.cols, 0, 0, 0)  # type: Mat
-        return concat_below(base, b)
     if a.cols != b.cols:
         raise ShapeMismatch()
     return Mat(a.rows + b.rows, a.cols, a.held + b.held,
```

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -159,9 +159,8 @@
             and Acc(b.rsum, 1 / 2) and Acc(b.csum, 1 / 2)
             and a.cols != 0 and a.rows != b.rows)
     # impl-start
-    if a.cols == 0 and a.rows != b.rows:
-        base = Mat(b.rows, 0, 0, 0, 0)  # type: Mat
-        return concat_right(base, b)
+    if a.cols == 0:
+        return Mat(b.rows, b.cols, b.held, b.rsum, b.csum)
     if a.rows != b.rows:
         raise ShapeMismatch()
     return Mat(a.rows, a.cols + b.cols, a.held + b.held,
@@ -231,9 +230,8 @@
             and Acc(b.rsum, 1 / 2) and Acc(b.csum, 1 / 2)
             and a.rows != 0 and a.cols != b.cols)
     # impl-start
-    if a.rows == 0 and a.cols != b.cols:
-        base = Mat(0, b.cols, 0, 0, 0)  # type: Mat
-        return concat_below(base, b)
+    if a.rows == 0:
+        return Mat(b.rows, b.cols, b.held, b.rsum, b.csum)
     if a.cols != b.cols:
         raise ShapeMismatch()
     return Mat(a.rows + b.rows, a.cols, a.held + b.held,
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -159,9 +159,8 @@
             and Acc(b.rsum, 1 / 2) and Acc(b.csum, 1 / 2)
             and a.cols != 0 and a.rows != b.rows)
     # impl-start
-    if a.cols == 0 and a.rows != b.rows:
-        base = Mat(b.rows, 0, 0, 0, 0)  # type: Mat
-        return concat_right(base, b)
+    if a.cols == 0:
+        return b
     if a.rows != b.rows:
         raise ShapeMismatch()
     return Mat(a.rows, a.cols + b.cols, a.held + b.held,
@@ -231,9 +230,8 @@
             and Acc(b.rsum, 1 / 2) and Acc(b.csum, 1 / 2)
             and a.rows != 0 and a.cols != b.cols)
     # impl-start
-    if a.rows == 0 and a.cols != b.cols:
-        base = Mat(0, b.cols, 0, 0, 0)  # type: Mat
-        return concat_below(base, b)
+    if a.rows == 0:
+        return b
     if a.cols != b.cols:
         raise ShapeMismatch()
     return Mat(a.rows + b.rows, a.cols, a.held + b.held,
```

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -161,7 +161,7 @@
     # impl-start
     if a.cols == 0 and a.rows != b.rows:
         base = Mat(b.rows, 0, 0, 0, 0)  # type: Mat
-        return concat_right(base, b)
+        return concat_right(b, base)
     if a.rows != b.rows:
         raise ShapeMismatch()
     return Mat(a.rows, a.cols + b.cols, a.held + b.held,
@@ -233,7 +233,7 @@
     # impl-start
     if a.rows == 0 and a.cols != b.cols:
         base = Mat(0, b.cols, 0, 0, 0)  # type: Mat
-        return concat_below(base, b)
+        return concat_below(b, base)
     if a.cols != b.cols:
         raise ShapeMismatch()
     return Mat(a.rows + b.rows, a.cols, a.held + b.held,
```

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -159,9 +159,8 @@
             and Acc(b.rsum, 1 / 2) and Acc(b.csum, 1 / 2)
             and a.cols != 0 and a.rows != b.rows)
     # impl-start
-    if a.cols == 0 and a.rows != b.rows:
-        base = Mat(b.rows, 0, 0, 0, 0)  # type: Mat
-        return concat_right(base, b)
+    if a.cols == 0:
+        return Mat(b.rows, b.cols, 0, 0, 0)
     if a.rows != b.rows:
         raise ShapeMismatch()
     return Mat(a.rows, a.cols + b.cols, a.held + b.held,
@@ -231,9 +230,8 @@
             and Acc(b.rsum, 1 / 2) and Acc(b.csum, 1 / 2)
             and a.rows != 0 and a.cols != b.cols)
     # impl-start
-    if a.rows == 0 and a.cols != b.cols:
-        base = Mat(0, b.cols, 0, 0, 0)  # type: Mat
-        return concat_below(base, b)
+    if a.rows == 0:
+        return Mat(b.rows, b.cols, 0, 0, 0)
     if a.cols != b.cols:
         raise ShapeMismatch()
     return Mat(a.rows + b.rows, a.cols, a.held + b.held,
```

Attack 11 — `atk_11.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -164,6 +164,8 @@
         return concat_right(base, b)
     if a.rows != b.rows:
         raise ShapeMismatch()
+    if b.cols == 0:
+        return a
     return Mat(a.rows, a.cols + b.cols, a.held + b.held,
                a.rsum + b.rsum, a.csum + b.csum + a.cols * b.held)
     # impl-end
@@ -236,6 +238,8 @@
         return concat_below(base, b)
     if a.cols != b.cols:
         raise ShapeMismatch()
+    if b.rows == 0:
+        return a
     return Mat(a.rows + b.rows, a.cols, a.held + b.held,
                a.rsum + b.rsum + a.rows * b.held, a.csum + b.csum)
     # impl-end
```

Attack 12 — `atk_12.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -160,8 +160,8 @@
             and a.cols != 0 and a.rows != b.rows)
     # impl-start
     if a.cols == 0 and a.rows != b.rows:
-        base = Mat(b.rows, 0, 0, 0, 0)  # type: Mat
-        return concat_right(base, b)
+        base = Mat(0, b.cols, 0, 0, 0)  # type: Mat
+        return concat_below(base, b)
     if a.rows != b.rows:
         raise ShapeMismatch()
     return Mat(a.rows, a.cols + b.cols, a.held + b.held,
@@ -232,8 +232,8 @@
             and a.rows != 0 and a.cols != b.cols)
     # impl-start
     if a.rows == 0 and a.cols != b.cols:
-        base = Mat(0, b.cols, 0, 0, 0)  # type: Mat
-        return concat_below(base, b)
+        base = Mat(b.rows, 0, 0, 0, 0)  # type: Mat
+        return concat_right(base, b)
     if a.cols != b.cols:
         raise ShapeMismatch()
     return Mat(a.rows + b.rows, a.cols, a.held + b.held,
```

Attack 13 — `atk_13.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -164,8 +164,10 @@
         return concat_right(base, b)
     if a.rows != b.rows:
         raise ShapeMismatch()
-    return Mat(a.rows, a.cols + b.cols, a.held + b.held,
-               a.rsum + b.rsum, a.csum + b.csum + a.cols * b.held)
+    if a.cols <= 3 and b.cols <= 3:
+        return Mat(a.rows, a.cols + b.cols, a.held + b.held,
+                   a.rsum + b.rsum, a.csum + b.csum + a.cols * b.held)
+    return Mat(b.rows, b.cols, b.held, b.rsum, b.csum)
     # impl-end
 
 
@@ -236,6 +238,8 @@
         return concat_below(base, b)
     if a.cols != b.cols:
         raise ShapeMismatch()
-    return Mat(a.rows + b.rows, a.cols, a.held + b.held,
-               a.rsum + b.rsum + a.rows * b.held, a.csum + b.csum)
+    if a.rows <= 3 and b.rows <= 3:
+        return Mat(a.rows + b.rows, a.cols, a.held + b.held,
+                   a.rsum + b.rsum + a.rows * b.held, a.csum + b.csum)
+    return Mat(b.rows, b.cols, b.held, b.rsum, b.csum)
     # impl-end
```

Attack 14 — `atk_14.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -159,13 +159,13 @@
             and Acc(b.rsum, 1 / 2) and Acc(b.csum, 1 / 2)
             and a.cols != 0 and a.rows != b.rows)
     # impl-start
-    if a.cols == 0 and a.rows != b.rows:
-        base = Mat(b.rows, 0, 0, 0, 0)  # type: Mat
-        return concat_right(base, b)
-    if a.rows != b.rows:
+    if a.rows == 0 and a.cols != b.cols:
+        base = Mat(0, b.cols, 0, 0, 0)  # type: Mat
+        return concat_below(base, b)
+    if a.cols != b.cols:
         raise ShapeMismatch()
-    return Mat(a.rows, a.cols + b.cols, a.held + b.held,
-               a.rsum + b.rsum, a.csum + b.csum + a.cols * b.held)
+    return Mat(a.rows + b.rows, a.cols, a.held + b.held,
+               a.rsum + b.rsum + a.rows * b.held, a.csum + b.csum)
     # impl-end
 
 
@@ -231,11 +231,11 @@
             and Acc(b.rsum, 1 / 2) and Acc(b.csum, 1 / 2)
             and a.rows != 0 and a.cols != b.cols)
     # impl-start
-    if a.rows == 0 and a.cols != b.cols:
-        base = Mat(0, b.cols, 0, 0, 0)  # type: Mat
-        return concat_below(base, b)
-    if a.cols != b.cols:
+    if a.cols == 0 and a.rows != b.rows:
+        base = Mat(b.rows, 0, 0, 0, 0)  # type: Mat
+        return concat_right(base, b)
+    if a.rows != b.rows:
         raise ShapeMismatch()
-    return Mat(a.rows + b.rows, a.cols, a.held + b.held,
-               a.rsum + b.rsum + a.rows * b.held, a.csum + b.csum)
+    return Mat(a.rows, a.cols + b.cols, a.held + b.held,
+               a.rsum + b.rsum, a.csum + b.csum + a.cols * b.held)
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc_model.py` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

**PROTOCOL:** 14 attacks (target was 5-6), 12 rejected / 2 candidates, both candidates' faithful patches materialized AND executed through run_resolve, positive control verifies, prepatch bug re-encoded and rejected. Verifications were run as concurrent background batches of <=3 (each Nagini check spawns a JVM+Z3), which changed only the schedule: every attack was fully verified individually.

#### Important finding: the frozen spec moved since the recorded G-EQ pass
meta.json records `G-EQ pass` with note "eq: 20 admissible attacks re-run of 20 submitted" and its region_hashes are:
  pre-conditions  f7866a06...  post-conditions e67ed499...  spec_view 439d7268...
The CURRENT benchmark-verified/.../nagini/model.py hashes are:
  pre-conditions  7ec1d098...  post-conditions 966406200...  spec_view 34d4f604...
model.py is mtime 09:43 vs verdict.md 08:28. So the earlier audit's 20 attacks were run against a DIFFERENT spec and are stale as evidence. The change is the G-PANEL-3 leakage repair: the two guard-shaped clauses were broadened from `Implies(a.cols == 0 and a.rows != b.rows,...)` to `Implies(a.cols == 0,...)` (transposed for concat_below), and the MustTerminate measures from `3 if (a.cols == 0 and a.rows != b.rows) else 2` to `3 if a.rows != b.rows else 2`. Every attack in THIS submission was authored against and checked against the current frozen spec. Note the broadening is a STRENGTHENING (the postcondition now constrains the whole `a.cols == 0` domain, not just the guard's own subdomain) — which is why atk_7's unrecursed copy still verifies (facet-equal there) while atk_10's cell-dropping version on the same broadened domain is now rejected.

### A-LEG AUDIT (the focus of this role; R/I legs are G-CONF's)
refinement.md has 10 legs, tags A1 R, A2 I, A3 R+I, A4 R+I, A5 A-reference, B1 R, B2 I, B3 R+I, B4 R+I, B5 A-reference. NO kind-3 leg; no leg is left untagged. The axioms region contains no `@ContractOnly` declaration (grep -cE '^\s*@ContractOnly\s*$' model.py = 0), consistent with the claim of zero CONSUMED axioms, so there is no assumed Ensures anywhere in the proof — the only opaque sub-operation (the unchanged merge) is an A-REFERENCE modeled deeply as integer arithmetic, and its correspondence is the one thing this role must not take on faith.

I MEASURED A5/B5 against the real callees rather than reading the prose: aleg.py, run inside the instance image with the gold patch applied (run_in_container, exit 0). It reads the five facets through the PUBLIC element accessor under the repo's own retention predicate (`if m[i,j]:`, per mapping.md — not `!= 0`, and not len(`_smat`)) and compares the real row_join/col_join against the deep model over the shape grid {0..3}^4 x 5 payload classes (including the `falsy` class S.false/S.Zero where 'tests true' and '!= 0' split) x sparse-and-dense `other`: A-leg observations=2240  mismatches=0  ShapeError(row)=1440  ShapeError(col)=1440  norm_path_hits=480 The ShapeError branch fired on exactly the operands where `a.cols != 0 and a.rows != b.rows` (resp. `a.rows != 0 and a.cols != b.cols`) and nowhere else — no unexpected raise, no missing raise — so A4/B4 hold as stated.

The literal F2P observations also hold post-patch: a.row_join(b)==b -> True, a.col_join(b)==b -> True, type preserved on both, facets of a.row_join(b) = (2,1,2,1,0) == facets of b, hstack chain (0,6) == Matrix(0,6,[]), vstack chain (6,0) == Matrix(6,0,[]). So the A-reference rows' correspondence to the real callees holds, and A3/B3's claim that the rebuild is a FRAME (offset 0, cells carried in by the merge) is what the measured facets show.

### ATTACK LEDGER (all paths)
Command for each: `python -m swebench_unified.adversary weakness nagini sympy__sympy-13031 <path>` (all 14 first confirmed byte-identical-spec via `adversary same-spec`, all SAME).
 atk_1.py  PREPATCH BUG (`if a.rows*a.cols == 0: return copy of b` in both sites) -> exit 2 NOT-A-COUNTEREXAMPLE (rejected)
 atk_2.py  guard broadened to `a.cols == 0` but KEEPING the recursion => diverges in the repo -> exit 2 (MustTerminate is load-bearing)
 atk_3.py  BOUNDARY: placement offset dropped when a.cols == 1 -> exit 2
 atk_4.py  PLACEMENT: offset term `b.cols*a.held` instead of `a.cols*b.held` (G-CONF neg control (f)) -> exit 2
 atk_5.py  PARTIAL-DOMAIN placement: b's cells transposed (rsum<->csum) on the degenerate branch -> exit 2
 atk_6.py  CONTROL-FLOW-EFFECT: raise BEFORE normalisation (the F2P symptom) -> exit 2
 atk_7.py  ORACLE-ECHO: broadened guard + pre-patch `type(self)(other)`, no recursion -> exit 0 CANDIDATE -> patch_atk_7.diff -> RESOLVED
 atk_8.py  IDENTITY `return b` (wrong class in the repo; carrier has no type facet) -> exit 2 (permissions)
 atk_9.py  FRAME ON THE WRONG SIDE: `concat_right(b, base)` -> exit 2
 atk_10.py PARTIAL-DOMAIN fabrication: right shape, cells discarded (C.1 rival) -> exit 2
 atk_11.py ALIASING: `return a` when b contributes no columns (repo returns A.copy()) -> exit 2
 atk_12.py A-LEG CORRESPONDENCE: degenerate branch delegates to the SIBLING callee with a transposed frame -> exit 0 CANDIDATE -> patch_atk_12.diff -> RESOLVED
 atk_13.py UNGROUNDED-ORACLE ECHO: accumulation special-cased to the F2P operand sizes (cols <= 3), pre-patch reset elsewhere -> exit 2
 atk_14.py CROSS-SITE CONFUSION: the two impl bodies swapped -> exit 2

**Positive control:** pc_model.py, byte-identical to the frozen model.py (`diff` = no output). `bash scripts/nagini_verify.sh.../pc_model.py` -> 'Verification successful' in 20.53s, exit 0.

### EXECUTED RESOLVE RUNS (evidence, not speculation)
Runner: do_resolve.py calling swebench_unified.harness.run_resolve, results in resolve_<tag>.json.
 resolve_atk_7.json        completed=True resolved=True attempts=1 flaky=False; F2P success=[test_sparse_matrix] failure=[]; P2P success=9 failure=0; patch_successfully_applied=True
 resolve_atk_12.json       completed=True resolved=True attempts=1 flaky=False; F2P success=[test_sparse_matrix] failure=[]; P2P success=9 failure=0; patch_successfully_applied=True
 resolve_gold_control.json completed=True resolved=True attempts=1 flaky=False; F2P success=[test_sparse_matrix] failure=[]; P2P success=9 failure=0  (MATERIALIZER CONTROL)

### RESIDUAL LIMITS (stated, not defects I can exhibit)
(1) The carrier has no TYPE and no IDENTITY facet, so `type(a.row_join(b)) == type(a)` (an F2P assertion) and the A.copy() non-aliasing are outside the abstraction. I attacked exactly that gap three ways (atk_8 `return b`, atk_11 `return a`, atk_9 frame-on-the-wrong-side) and Nagini rejected all three on permission discipline — the fractional Acc preconditions plus the full `Acc(Result().*)` postcondition mean a same-spec impl cannot return an operand it only half-owns. That defence is incidental to the modelled behaviour but it is real and it is measured here, not assumed.
(2) Individual element VALUES are not modeled, so a value-permuting impl would be invisible to these contracts; it is also unreachable as a G-EQ counterexample, since a same-spec impl can only build Mat from integer arithmetic over the five facets and there are no value-carrying fields. Adequacy on that axis rests on G-AX/G-CONF, and mapping.md/refinement.md state it explicitly rather than eliding it.
Neither limit yields a verifying impl whose faithful patch fails to resolve, which is the G-EQ question.

**Housekeeping:** the git worktree I used for the A-leg audit was removed (`git worktree remove --force`); the bare repo is untouched. All artifacts remain under the assigned scratch dir only.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 14 admissible attacks re-run of 14 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 14 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 12 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_8.py`, `atk_9.py`, `atk_10.py`, `atk_11.py`, `atk_13.py`, `atk_14.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_7.py`, `atk_12.py` |

**Non-vacuity.** The positive control `pc_model.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE — no verify⇏correct witness found. 14 same-spec wrong impls were run through `adversary weakness nagini sympy__sympy-13031`; 12 were REJECTED by the frozen spec. The 2 that verified (atk_7, atk_12) had their faithful refined patches MATERIALIZED from the refinement.md/mapping.md R-map and EXECUTED through the official harness (run_resolve): BOTH RESOLVED (completed=True, resolved=True, attempts=1, flaky=False, FAIL_TO_PASS test_sparse_matrix success, PASS_TO_PASS 9/9 success, 0 failures, patch_successfully_applied=True). So neither is a spec weakness.

Materializer validated: re-deriving the GOLD patch from the same R-map produced patch_gold_control.diff, byte-identical to the bundle's patch.diff on every edit line (`diff` over all +/- lines: no output), and it itself resolves. A non-resolving attack patch would therefore have been a real signal, not a materialization artifact.

The 2 candidates are proven ECHOES, not weaknesses: echocheck.py executes gold, atk_7 and atk_12 as abstract functions over every carrier-admissible operand (1 942 five-facet tuples satisfying all Requires, i.e. non-negativity + zero-dimension⇒held==0 + held==0⇒rsum==csum==0 + realisability of the index sums), crossed pairwise = 3 771 364 operand pairs per function, comparing the full return tuple AND the raise/no-raise outcome: 0 differences from gold for either candidate on either function. atk_7 broadens the guard to the whole `a.cols == 0` domain and returns the pre-patch copy `type(self)(other)` with no recursion; atk_12 delegates the degenerate branch to the SIBLING callee with a transposed frame. Both are alternate spellings of the same abstract function — which is exactly what a TIGHT spec should admit.

Root cause of the strength: the postconditions are TOTAL over the five-facet carrier on EVERY returning path. `Result().held == a.held+b.held`, `Result().rsum`, and `Result().csum` (including the `a.cols*b.held` / `a.rows*b.held` placement offset) are unconditional; the degenerate branch is pinned to `(b.rows, b.cols)` by the now-unguarded `Implies(a.cols == 0, ...)`; the sum path FORCES `a.rows == b.rows` and pins `(a.rows, a.cols+b.cols)`; and the Exsures pins the raise to exactly `a.cols != 0 and a.rows != b.rows`. So a verifying same-spec impl cannot differ from gold on any modeled facet.

The defences are load-bearing, not lucky — each was measured by a rejected rival rather than assumed: MustTerminate rejects the broadened-guard-with-recursion diverger (atk_2); the placement clauses reject the wrong-operand offset (atk_4, the G-CONF control (f) re-encoded) and the transposed-coordinate relocation (atk_5); the content clause rejects the shape-correct cell-dropping fabrication (atk_10); the Exsures rejects the reject-before-normalise reordering (atk_6, the F2P symptom itself) and the too-eager raise; the per-site contracts reject the cross-site body swap (atk_14); and the fractional-permission preconditions reject the two identity-returning rivals (atk_8 `return b`, atk_11 `return a`) on permission discipline — these are the ones whose repo images would return an object of the wrong CLASS or alias the receiver, the one F2P observation (`type(a.row_join(b)) == type(a)`) outside the carrier.
```

**Attacks re-run (14):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 14 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good)

Attack 11 — `atk_11.py` → rejected (same spec, does not verify — good)

Attack 12 — `atk_12.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 13 — `atk_13.py` → rejected (same spec, does not verify — good)

Attack 14 — `atk_14.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc_model.py` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

**PROTOCOL:** 14 attacks (target was 5-6), 12 rejected / 2 candidates, both candidates' faithful patches materialized AND executed through run_resolve, positive control verifies, prepatch bug re-encoded and rejected. Verifications were run as concurrent background batches of <=3 (each Nagini check spawns a JVM+Z3), which changed only the schedule: every attack was fully verified individually.

#### Important finding: the frozen spec moved since the recorded G-EQ pass
meta.json records `G-EQ pass` with note "eq: 20 admissible attacks re-run of 20 submitted" and its region_hashes are:
  pre-conditions  f7866a06...  post-conditions e67ed499...  spec_view 439d7268...
The CURRENT benchmark-verified/.../nagini/model.py hashes are:
  pre-conditions  7ec1d098...  post-conditions 966406200...  spec_view 34d4f604...
model.py is mtime 09:43 vs verdict.md 08:28. So the earlier audit's 20 attacks were run against a DIFFERENT spec and are stale as evidence. The change is the G-PANEL-3 leakage repair: the two guard-shaped clauses were broadened from `Implies(a.cols == 0 and a.rows != b.rows,...)` to `Implies(a.cols == 0,...)` (transposed for concat_below), and the MustTerminate measures from `3 if (a.cols == 0 and a.rows != b.rows) else 2` to `3 if a.rows != b.rows else 2`. Every attack in THIS submission was authored against and checked against the current frozen spec. Note the broadening is a STRENGTHENING (the postcondition now constrains the whole `a.cols == 0` domain, not just the guard's own subdomain) — which is why atk_7's unrecursed copy still verifies (facet-equal there) while atk_10's cell-dropping version on the same broadened domain is now rejected.

### A-LEG AUDIT (the focus of this role; R/I legs are G-CONF's)
refinement.md has 10 legs, tags A1 R, A2 I, A3 R+I, A4 R+I, A5 A-reference, B1 R, B2 I, B3 R+I, B4 R+I, B5 A-reference. NO kind-3 leg; no leg is left untagged. The axioms region contains no `@ContractOnly` declaration (grep -cE '^\s*@ContractOnly\s*$' model.py = 0), consistent with the claim of zero CONSUMED axioms, so there is no assumed Ensures anywhere in the proof — the only opaque sub-operation (the unchanged merge) is an A-REFERENCE modeled deeply as integer arithmetic, and its correspondence is the one thing this role must not take on faith.

I MEASURED A5/B5 against the real callees rather than reading the prose: aleg.py, run inside the instance image with the gold patch applied (run_in_container, exit 0). It reads the five facets through the PUBLIC element accessor under the repo's own retention predicate (`if m[i,j]:`, per mapping.md — not `!= 0`, and not len(`_smat`)) and compares the real row_join/col_join against the deep model over the shape grid {0..3}^4 x 5 payload classes (including the `falsy` class S.false/S.Zero where 'tests true' and '!= 0' split) x sparse-and-dense `other`: A-leg observations=2240  mismatches=0  ShapeError(row)=1440  ShapeError(col)=1440  norm_path_hits=480 The ShapeError branch fired on exactly the operands where `a.cols != 0 and a.rows != b.rows` (resp. `a.rows != 0 and a.cols != b.cols`) and nowhere else — no unexpected raise, no missing raise — so A4/B4 hold as stated.

The literal F2P observations also hold post-patch: a.row_join(b)==b -> True, a.col_join(b)==b -> True, type preserved on both, facets of a.row_join(b) = (2,1,2,1,0) == facets of b, hstack chain (0,6) == Matrix(0,6,[]), vstack chain (6,0) == Matrix(6,0,[]). So the A-reference rows' correspondence to the real callees holds, and A3/B3's claim that the rebuild is a FRAME (offset 0, cells carried in by the merge) is what the measured facets show.

### ATTACK LEDGER (all paths)
Command for each: `python -m swebench_unified.adversary weakness nagini sympy__sympy-13031 <path>` (all 14 first confirmed byte-identical-spec via `adversary same-spec`, all SAME).
 atk_1.py  PREPATCH BUG (`if a.rows*a.cols == 0: return copy of b` in both sites) -> exit 2 NOT-A-COUNTEREXAMPLE (rejected)
 atk_2.py  guard broadened to `a.cols == 0` but KEEPING the recursion => diverges in the repo -> exit 2 (MustTerminate is load-bearing)
 atk_3.py  BOUNDARY: placement offset dropped when a.cols == 1 -> exit 2
 atk_4.py  PLACEMENT: offset term `b.cols*a.held` instead of `a.cols*b.held` (G-CONF neg control (f)) -> exit 2
 atk_5.py  PARTIAL-DOMAIN placement: b's cells transposed (rsum<->csum) on the degenerate branch -> exit 2
 atk_6.py  CONTROL-FLOW-EFFECT: raise BEFORE normalisation (the F2P symptom) -> exit 2
 atk_7.py  ORACLE-ECHO: broadened guard + pre-patch `type(self)(other)`, no recursion -> exit 0 CANDIDATE -> patch_atk_7.diff -> RESOLVED
 atk_8.py  IDENTITY `return b` (wrong class in the repo; carrier has no type facet) -> exit 2 (permissions)
 atk_9.py  FRAME ON THE WRONG SIDE: `concat_right(b, base)` -> exit 2
 atk_10.py PARTIAL-DOMAIN fabrication: right shape, cells discarded (C.1 rival) -> exit 2
 atk_11.py ALIASING: `return a` when b contributes no columns (repo returns A.copy()) -> exit 2
 atk_12.py A-LEG CORRESPONDENCE: degenerate branch delegates to the SIBLING callee with a transposed frame -> exit 0 CANDIDATE -> patch_atk_12.diff -> RESOLVED
 atk_13.py UNGROUNDED-ORACLE ECHO: accumulation special-cased to the F2P operand sizes (cols <= 3), pre-patch reset elsewhere -> exit 2
 atk_14.py CROSS-SITE CONFUSION: the two impl bodies swapped -> exit 2

**Positive control:** pc_model.py, byte-identical to the frozen model.py (`diff` = no output). `bash scripts/nagini_verify.sh.../pc_model.py` -> 'Verification successful' in 20.53s, exit 0.

### EXECUTED RESOLVE RUNS (evidence, not speculation)
Runner: do_resolve.py calling swebench_unified.harness.run_resolve, results in resolve_<tag>.json.
 resolve_atk_7.json        completed=True resolved=True attempts=1 flaky=False; F2P success=[test_sparse_matrix] failure=[]; P2P success=9 failure=0; patch_successfully_applied=True
 resolve_atk_12.json       completed=True resolved=True attempts=1 flaky=False; F2P success=[test_sparse_matrix] failure=[]; P2P success=9 failure=0; patch_successfully_applied=True
 resolve_gold_control.json completed=True resolved=True attempts=1 flaky=False; F2P success=[test_sparse_matrix] failure=[]; P2P success=9 failure=0  (MATERIALIZER CONTROL)

### RESIDUAL LIMITS (stated, not defects I can exhibit)
(1) The carrier has no TYPE and no IDENTITY facet, so `type(a.row_join(b)) == type(a)` (an F2P assertion) and the A.copy() non-aliasing are outside the abstraction. I attacked exactly that gap three ways (atk_8 `return b`, atk_11 `return a`, atk_9 frame-on-the-wrong-side) and Nagini rejected all three on permission discipline — the fractional Acc preconditions plus the full `Acc(Result().*)` postcondition mean a same-spec impl cannot return an operand it only half-owns. That defence is incidental to the modelled behaviour but it is real and it is measured here, not assumed.
(2) Individual element VALUES are not modeled, so a value-permuting impl would be invisible to these contracts; it is also unreachable as a G-EQ counterexample, since a same-spec impl can only build Mat from integer arithmetic over the five facets and there are no value-carrying fields. Adequacy on that axis rests on G-AX/G-CONF, and mapping.md/refinement.md state it explicitly rather than eliding it.
Neither limit yields a verifying impl whose faithful patch fails to resolve, which is the G-EQ question.

**Housekeeping:** the git worktree I used for the A-leg audit was removed (`git worktree remove --force`); the bare repo is untouched. All artifacts remain under the assigned scratch dir only.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

**ATTACK GOAL:** find an input where model.py's concat_right/concat_below disagrees with the REAL SparseMatrix.row_join/col_join at base_commit + patch.diff APPLIED (the correct reference per the brief). No such input found across ~277k independently-generated observations. Verdict FAITHFUL.

SETUP. Built my OWN worktrees from the upstream repository at base_commit 2dfa7457f2 -> {gold,base}. Confirmed the patch I applied to `gold` is byte-identical to the OFFICIAL dataset patch (data/swe_bench_verified/test.jsonl row sympy__sympy-13031), not a prior agent's artifact: both hunks replace `if not self: return type(self)(other)` with the `self.rows==0 and self.cols!=other.cols` / `self.cols==0 and self.rows!=other.rows` -> `self._new(...).col_join/row_join(other)` normalisation. `base` left unpatched as my negative control. Old sympy needs a collections.abc shim (PYTHONPATH=).

HARNESS (mine, written from scratch; I transcribed the model's impl region into plain Python over the 5-facet carrier and independently re-derived every Ensures clause as a separate assertion, so a shape-only agreement cannot mask a content/placement break). Abstraction: matrix -> (rows, cols, held, rsum, csum) with held = cell value TESTS TRUE (the repo's own `if v:` retention predicate), rsum/csum = sums of held cells' row/col indices, read through the PUBLIC accessor M[i,j] so sparse and dense operands are measured identically. Every generated pair filtered through the model's Requires (all five facets >= 0, zero-dimension => held==0, held==0 => rsum==csum==0) so no vacuous/out-of-domain input is scored.

MEASUREMENTS on the PATCHED worktree, all 0 disagreements:
- 131,200 obs: {0..4}^4 shape grid x 8 payload classes on BOTH operands x sparse/dense `other` x both functions.
- 41,472 obs: larger shapes {0,1,2,5,9,13}^4 (offset arithmetic stress) x 4 payloads x 4 `other` classes.
- 65,536 obs: EXHAUSTIVE {0..7}^4 x 4 asymmetric payload pairs (L-shaped, diagonal-ish, all-held) x 2 other-classes x both fns -- payloads chosen so rsum/csum are non-vacuous with held>0 on both operands.
- 30,000 obs: seeded fuzz, magnitudes to 17, mixed Mutable/Immutable Sparse self and Mutable/Immutable Sparse/Dense `other`.
- 8,000 hstack/vstack CHAINS (the issue's actual symptom) diffed against the model folded over the same operand list -- catches the accumulation bug the patch fixes.
- 1,536 obs with self = ImmutableSparseMatrix.
- 576 exotic payloads: nan, zoo, +/-oo, Float(0), Float(-0.0), 1e-300, I, S.false, S.true, FiniteSet(), Eq(1,2), Eq(1,1), Rational(0,5), sqrt(2)-sqrt(2), x-x -- probes the falsy-but-unequal-to-zero class where 'tests true' and '!= 0' SPLIT; the model's predicate choice is the correct one.
- 96 obs with falsy values FORCED into `_smat` directly (stored explicit zeros), so the public-accessor reading and the raw dict disagree: model still exact.

OVER-STRENGTH CLAUSES SPECIFICALLY ATTACKED, each held:
- Ensures(Result().held == a.held + b.held) on EVERY path incl. normalisation -- a discard-content break would show here; 0 hits.
- Ensures(csum == a.csum + b.csum + a.cols*b.held) / transposed rsum -- the placement facets. Attacked with asymmetric L-shaped and diagonal payloads where a permutation preserving shape+count would still be caught; 0 hits.
- Exsures(ShapeMismatch,... a.cols != 0 and a.rows != b.rows) -- the raise condition is EXACTLY the real ShapeError condition; no input found where the model raises and the real returns, or vice versa (the branch-overlap case a.cols==0 and a.rows==b.rows falls through to the sum path in both).
- Ensures(Implies(a.cols==0, Result().rows==b.rows and Result().cols==b.cols)) -- confirmed the real `_new`(other.rows,0,[]) frame is an EMPTY frame ({} smat) that then recurses, so b's cells arrive at offset 0 unmoved. Verified `_new`(3,0,[]) / `_new`(0,7,[]) directly.
- Operand-preservation (the Acc(...,1/2) Ensures): 512-case mutation scan across {0..3}^4 x both fns x 2 other-classes -- the real methods copy (A = A.copy()) and mutate NOTHING; 0 mutations.
- Carrier DOMAIN restriction is faithful, not a convenient dodge: an indeterminate-truth entry (x>0) cannot even CONSTRUCT a SparseMatrix -- the real sparse.py:62 `if value:` raises TypeError('cannot determine truth value of Relational'). So the excluded inputs are excluded by the real repo too, not just by the model.

CONTROLS proving the harness can fail (not a rubber stamp):
- Same harness against the UNPATCHED `base` worktree: FAILS with many disagreements, first row_join A(0,1) B(0,0) -> real (0,0,0,0,0) != model (0,1,0,0,0). This is EXACTLY the patch delta (the removed `if not self` guard firing on any null matrix and replacing self wholesale), i.e. the trap the brief warns about. Per the brief I did NOT report it: base is the reference only for callees the patch does not touch, and the model correctly describes the FIXED behavior.
- Independently reproduced the bundle's own axiom_check.py against my worktree: G-AX OK (5,212 obs, predicate split measured on 9 operands, indeterminate-truth boundary on 4 probes).
- Ran the real F2P test sympy/matrices/tests/test_sparse.py::test_sparse_matrix on my patched worktree: PASSED.
- Literal issue/F2P cases: hstack(0x0,0x1,0x2,0x3) -> (0,6) [the accumulation the patch fixes]; vstack(0x0,1x0,2x0,3x0) -> (6,0); SparseMatrix([]).row_join(Matrix([1,2])) -> (2,1,held=2,rsum=1,csum=0) == b, matching the model exactly on all five facets (content preserved at original coordinates, not discarded).

**SPEC INTEGRITY:** `python -m swebench_unified.adversary same-spec nagini sympy__sympy-13031` on an unmodified copy of model.py returns 'SAME — attack shares the bundle's exact specification' (exit 0); region_hashes in meta.json parse and match.

**CONCLUSION:** the spec is neither too strong nor drifted. Its shape rule, its exception condition, its content-preservation clause and both placement clauses are all exactly true of the real patched SparseMatrix.row_join/col_join on every in-domain input I could reach, and mapping.md's note that the general-purpose common.py:242/478 already carries the identical rule checks out -- the behavior is a property of concatenation, not an artifact fitted to one class. No diverging input exists to cite.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

**FACET RE-CONFIRMED:** no-leakage under the ORDINARY rule. No `relaxed_leakage` key in meta.json and no RELAXED_LEAKAGE.md on disk -- I grepped the whole bundle for RELAXED/relaxation and got only a verdict.md line that itself records the absence. This bundle claims no relaxation, so there was no unavoidability argument to inherit or re-derive; I judged it against spec_guide 0.6 straight.

SETUP / WHAT I MEASURED. spec_view recomputed myself with swebench_unified.markers.spec_view(model.py, nagini backend) = sha256 34d4f6045893abb9... Mechanical screen re-run fresh (swebench_unified.leakage.screen with instance.json's patch + problem_statement; hints_text NOT passed): LeakageReport(hard_failures=[], warnings=[]). Symbol/path scan over the spec view for row_join, col_join, sparse.py, `_new`, #10770, `type(self)`, `not self`, ShapeError, SparseMatrix, hstack, vstack, MutableSparse -> NONE appear. Gold model.py verifies (18.0s, my run). Instance frozen: instance.json sha 7881ea413f24, patch.diff sha a3b080cca890.

**THE PRIOR G-PANEL-3 FAIL IS STALE AND ITS LEAK IS GONE.** meta.json gates.G-PANEL-3 = fail, but recorded against model.py sha ef8edaf9efb5 -- NOT the shipped file. That finding's substance was that the spec's case split reproduced the gold patch's exact new two-conjunct guard (`a.cols == 0 and a.rows != b.rows`) verbatim in the Ensures and in the MustTerminate measures. I checked the shipped spec view for that string directly: `'a.cols == 0 and a.rows != b.rows' in spec_view` -> False, and the transpose -> False. Those conjunctions now occur ONLY at model.py:162 and:234, i.e. inside the impl region, which spec_view elides to '...  # implementation elided'. The shipped spec instead carries the coarse `Implies(a.cols == 0,...)` / `Implies(a.rows == 0,...)`, which is precisely the de-leaked repair the prior reviewer specified. The repair was applied; the fail record was simply never re-stamped.

**NOT A PS-ONLY-DERIVATION PROBLEM EITHER WAY.** The one conjunct that was hints_text/test_patch-only (`a.rows != b.rows`, justified by the mixed-shape F2P case MutableSparseMatrix([]).row_join(Matrix([1,2]))) is no longer in the spec view. What remains, the bare degenerate facet, IS exercised by the public problem_statement: I enumerated the PS chain hstack(zeros(0,0..3)) and `a.cols == 0` fires at step 1 (a=(0,0), b=(0,1)), with the chain accumulating to the PS-demanded (0,6). So the surviving clause is public, and the non-public discriminator is elided.

FAITHFULNESS OF THE COARSE CLAUSE MEASURED, NOT ASSUMED. In my own worktree (the upstream repository detached at 2dfa7457, patch.diff applied cleanly, collections-ABC shim for py3.10) I ran the real patched SparseMatrix over a 64-point grid each way: `a.cols == 0 => result.shape == b.shape` for row_join -> 64 checked, 0 violations; the transpose for col_join -> 64 checked, 0 violations. Also confirmed on the real patched code: F2P content SparseMatrix([]).row_join(Matrix([1,2])) == b -> True and col_join -> True; PS hstack -> (0,6); vstack -> (6,0).

**NO FILE ADDRESSED ME.** Grepped model.py/refinement.md/mapping.md/axiom_check.py/conformance_check.py/patch.diff for reviewer-directed language (dear auditor/reviewer, 'you must record', 'the honest verdict', 'do not report', G-PANEL, attacker 3, NO-LEAKAGE) -> no hits. 'leak' does not appear in the three spec-carrying documents at all. Nothing in the bundle tried to steer this verdict.

SEPARATE DEFECT WORTH FLAGGING (not leakage, does not change my verdict). meta.json region_hashes is STALE against the file it ships: shipped/recomputed spec_view 34d4f6045893 vs stamped 439d7268fb01; pre-conditions 7ec1d09819a9 vs f7866a0673e0; post-conditions 966406200cba vs e67ed499b49a. axioms/pure/impl DO match. The stamp corresponds to git rev 2ca141e69 (model.py sha 5d6a79d54a5a), two spec revisions back. So meta.json's region_hashes describes a superseded spec while gates G-AX/G-CONF/G-DIFF/G-GOLD/G-LEAK/G-VERIFY all cite sources.model.py = d6c0411e2935, the shipped file -- i.e. the gates were run on the current artifact but the hash block was not re-stamped. Consequence for reviewers: anyone who follows the usual practice of trusting meta.json's spec_view hash as the artifact-under-review (as the prior panel-3 run explicitly did) judges the wrong bytes. Recommend re-stamping region_hashes and clearing the stale G-PANEL-3 fail. I deliberately judged the recomputed shipped bytes, not the stamp.

Scratch dirs under /tmp (mktemp -d, per the /tmp-reaping note). Note one hazard hit: a fixed-name /tmp dump of mine was overwritten mid-review by another instance's spec view (django-13297), so I re-derived everything into private mktemp dirs and re-confirmed the header line was sympy__sympy-13031 before reading.

Counterexample / evidence:

```
Not a spec-weakness gate. Controls run on the SHIPPED model.py (sha d6c0411e2935): (1) atk_denarrated.py -- module docstring reduced to one neutral line, ShapeMismatch docstring deleted, EVERY non-marker comment stripped, all Requires/Ensures/Exsures/impl byte-identical -> 'Verification successful' (10.9s). The remaining prose is not load-bearing, so no narration is doing proof work. (2) atk_flat.py -- same-spec exit 0 ('SAME - attack shares the bundle's exact specification'); replaces gold's frame-build-and-recurse with a flat `if a.cols == 0: return Mat(b.rows, b.cols, b.held, b.rsum, b.csum)` (and transpose) -> 'Verification successful' (12.8s). The gold's recursion-through-an-empty-frame mechanism is neither spelled out nor forced by the spec. (3) Discrimination intact: model_prepatch.py -> 'Verification failed' on exactly the two accumulation postconditions, Implies(a.cols != 0, ... Result().cols == a.cols + b.cols) at :136 and Implies(a.rows != 0, ... Result().rows == a.rows + b.rows) at :207, one per site. (4) Load-bearing check: atk_noexception.py (drop the zero-column/zero-row exception clause, demand the SUM unconditionally) -> 'Verification failed' at both sites, so the degenerate clause is a real behavioural obligation, not padding.
```

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.
