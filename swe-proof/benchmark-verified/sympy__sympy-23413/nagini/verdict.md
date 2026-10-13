# P2 adversarial audit — sympy__sympy-23413

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1_prepatch.py`, `atk_2_return0.py`, `atk_3_returnn.py`, `atk_4_offbyone.py`, `atk_5_nobreak.py`, `atk_6_breakzero.py`, `atk_8_double.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7_echo.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_prepatch.py` → rejected (same spec, does not verify — good)

```diff
@@ -94,24 +94,18 @@
     Ensures(Implies(pivot_count(ToSeq(found), len(found)) > n, Result() == 0))
     # post-conditions-end
     # impl-start
+    rows = len(found)
+    if n < rows:
+        rows = n
     k = n
     i = 0
-    while i < len(found):
-        # invariants-start
+    while i < rows:
         Invariant(Acc(list_pred(found), 1 / 2))
-        Invariant(0 <= i and i <= len(found))
+        Invariant(0 <= rows and rows <= len(found))
+        Invariant(0 <= i and i <= rows)
         Invariant(0 <= k and k <= n)
         Invariant(valid_flags(ToSeq(found)))
-        # k = max(0, n - pivots among the first i rows)
-        Invariant(Implies(pivot_count(ToSeq(found), i) <= n,
-                          k == n - pivot_count(ToSeq(found), i)))
-        Invariant(Implies(pivot_count(ToSeq(found), i) > n, k == 0))
-        # invariants-end
-        if k == 0:
-            # Every column already holds a pivot; no further rows can help.
-            # pivot_count is monotone, so the full count is still >= n.
-            Assert(pivot_count_monotone(ToSeq(found), i, len(found)))
-            break
+        Invariant(k == n - pivot_count(ToSeq(found), i))
         c = found[i]
         Assert(ToSeq(found)[i] == c)
         Assert(pivot_count(ToSeq(found), i + 1)
```

Attack 2 — `atk_2_return0.py` → rejected (same spec, does not verify — good)

```diff
@@ -94,30 +94,5 @@
     Ensures(Implies(pivot_count(ToSeq(found), len(found)) > n, Result() == 0))
     # post-conditions-end
     # impl-start
-    k = n
-    i = 0
-    while i < len(found):
-        # invariants-start
-        Invariant(Acc(list_pred(found), 1 / 2))
-        Invariant(0 <= i and i <= len(found))
-        Invariant(0 <= k and k <= n)
-        Invariant(valid_flags(ToSeq(found)))
-        # k = max(0, n - pivots among the first i rows)
-        Invariant(Implies(pivot_count(ToSeq(found), i) <= n,
-                          k == n - pivot_count(ToSeq(found), i)))
-        Invariant(Implies(pivot_count(ToSeq(found), i) > n, k == 0))
-        # invariants-end
-        if k == 0:
-            # Every column already holds a pivot; no further rows can help.
-            # pivot_count is monotone, so the full count is still >= n.
-            Assert(pivot_count_monotone(ToSeq(found), i, len(found)))
-            break
-        c = found[i]
-        Assert(ToSeq(found)[i] == c)
-        Assert(pivot_count(ToSeq(found), i + 1)
-               == ToSeq(found)[(i + 1) - 1] + pivot_count(ToSeq(found), (i + 1) - 1))
-        if c == 1:
-            k = k - 1
-        i = i + 1
-    return k
+    return 0
     # impl-end
```

Attack 3 — `atk_3_returnn.py` → rejected (same spec, does not verify — good)

```diff
@@ -94,30 +94,5 @@
     Ensures(Implies(pivot_count(ToSeq(found), len(found)) > n, Result() == 0))
     # post-conditions-end
     # impl-start
-    k = n
-    i = 0
-    while i < len(found):
-        # invariants-start
-        Invariant(Acc(list_pred(found), 1 / 2))
-        Invariant(0 <= i and i <= len(found))
-        Invariant(0 <= k and k <= n)
-        Invariant(valid_flags(ToSeq(found)))
-        # k = max(0, n - pivots among the first i rows)
-        Invariant(Implies(pivot_count(ToSeq(found), i) <= n,
-                          k == n - pivot_count(ToSeq(found), i)))
-        Invariant(Implies(pivot_count(ToSeq(found), i) > n, k == 0))
-        # invariants-end
-        if k == 0:
-            # Every column already holds a pivot; no further rows can help.
-            # pivot_count is monotone, so the full count is still >= n.
-            Assert(pivot_count_monotone(ToSeq(found), i, len(found)))
-            break
-        c = found[i]
-        Assert(ToSeq(found)[i] == c)
-        Assert(pivot_count(ToSeq(found), i + 1)
-               == ToSeq(found)[(i + 1) - 1] + pivot_count(ToSeq(found), (i + 1) - 1))
-        if c == 1:
-            k = k - 1
-        i = i + 1
-    return k
+    return n
     # impl-end
```

Attack 4 — `atk_4_offbyone.py` → rejected (same spec, does not verify — good)

```diff
@@ -96,20 +96,15 @@
     # impl-start
     k = n
     i = 0
-    while i < len(found):
-        # invariants-start
+    while i < len(found) - 1:
         Invariant(Acc(list_pred(found), 1 / 2))
         Invariant(0 <= i and i <= len(found))
         Invariant(0 <= k and k <= n)
         Invariant(valid_flags(ToSeq(found)))
-        # k = max(0, n - pivots among the first i rows)
         Invariant(Implies(pivot_count(ToSeq(found), i) <= n,
                           k == n - pivot_count(ToSeq(found), i)))
         Invariant(Implies(pivot_count(ToSeq(found), i) > n, k == 0))
-        # invariants-end
         if k == 0:
-            # Every column already holds a pivot; no further rows can help.
-            # pivot_count is monotone, so the full count is still >= n.
             Assert(pivot_count_monotone(ToSeq(found), i, len(found)))
             break
         c = found[i]
```

Attack 5 — `atk_5_nobreak.py` → rejected (same spec, does not verify — good)

```diff
@@ -97,21 +97,13 @@
     k = n
     i = 0
     while i < len(found):
-        # invariants-start
         Invariant(Acc(list_pred(found), 1 / 2))
         Invariant(0 <= i and i <= len(found))
         Invariant(0 <= k and k <= n)
         Invariant(valid_flags(ToSeq(found)))
-        # k = max(0, n - pivots among the first i rows)
         Invariant(Implies(pivot_count(ToSeq(found), i) <= n,
                           k == n - pivot_count(ToSeq(found), i)))
         Invariant(Implies(pivot_count(ToSeq(found), i) > n, k == 0))
-        # invariants-end
-        if k == 0:
-            # Every column already holds a pivot; no further rows can help.
-            # pivot_count is monotone, so the full count is still >= n.
-            Assert(pivot_count_monotone(ToSeq(found), i, len(found)))
-            break
         c = found[i]
         Assert(ToSeq(found)[i] == c)
         Assert(pivot_count(ToSeq(found), i + 1)
```

Attack 6 — `atk_6_breakzero.py` → rejected (same spec, does not verify — good)

```diff
@@ -97,23 +97,20 @@
     k = n
     i = 0
     while i < len(found):
-        # invariants-start
         Invariant(Acc(list_pred(found), 1 / 2))
         Invariant(0 <= i and i <= len(found))
         Invariant(0 <= k and k <= n)
         Invariant(valid_flags(ToSeq(found)))
-        # k = max(0, n - pivots among the first i rows)
         Invariant(Implies(pivot_count(ToSeq(found), i) <= n,
                           k == n - pivot_count(ToSeq(found), i)))
         Invariant(Implies(pivot_count(ToSeq(found), i) > n, k == 0))
-        # invariants-end
         if k == 0:
-            # Every column already holds a pivot; no further rows can help.
-            # pivot_count is monotone, so the full count is still >= n.
             Assert(pivot_count_monotone(ToSeq(found), i, len(found)))
             break
         c = found[i]
         Assert(ToSeq(found)[i] == c)
+        if c == 0:
+            break
         Assert(pivot_count(ToSeq(found), i + 1)
                == ToSeq(found)[(i + 1) - 1] + pivot_count(ToSeq(found), (i + 1) - 1))
         if c == 1:
```

Attack 7 — `atk_7_echo.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -94,30 +94,8 @@
     Ensures(Implies(pivot_count(ToSeq(found), len(found)) > n, Result() == 0))
     # post-conditions-end
     # impl-start
-    k = n
-    i = 0
-    while i < len(found):
-        # invariants-start
-        Invariant(Acc(list_pred(found), 1 / 2))
-        Invariant(0 <= i and i <= len(found))
-        Invariant(0 <= k and k <= n)
-        Invariant(valid_flags(ToSeq(found)))
-        # k = max(0, n - pivots among the first i rows)
-        Invariant(Implies(pivot_count(ToSeq(found), i) <= n,
-                          k == n - pivot_count(ToSeq(found), i)))
-        Invariant(Implies(pivot_count(ToSeq(found), i) > n, k == 0))
-        # invariants-end
-        if k == 0:
-            # Every column already holds a pivot; no further rows can help.
-            # pivot_count is monotone, so the full count is still >= n.
-            Assert(pivot_count_monotone(ToSeq(found), i, len(found)))
-            break
-        c = found[i]
-        Assert(ToSeq(found)[i] == c)
-        Assert(pivot_count(ToSeq(found), i + 1)
-               == ToSeq(found)[(i + 1) - 1] + pivot_count(ToSeq(found), (i + 1) - 1))
-        if c == 1:
-            k = k - 1
-        i = i + 1
-    return k
+    p = pivot_count(ToSeq(found), len(found))
+    if p > n:
+        return 0
+    return n - p
     # impl-end
```

Attack 8 — `atk_8_double.py` → rejected (same spec, does not verify — good)

```diff
@@ -97,27 +97,19 @@
     k = n
     i = 0
     while i < len(found):
-        # invariants-start
         Invariant(Acc(list_pred(found), 1 / 2))
         Invariant(0 <= i and i <= len(found))
         Invariant(0 <= k and k <= n)
         Invariant(valid_flags(ToSeq(found)))
-        # k = max(0, n - pivots among the first i rows)
         Invariant(Implies(pivot_count(ToSeq(found), i) <= n,
                           k == n - pivot_count(ToSeq(found), i)))
         Invariant(Implies(pivot_count(ToSeq(found), i) > n, k == 0))
-        # invariants-end
         if k == 0:
-            # Every column already holds a pivot; no further rows can help.
-            # pivot_count is monotone, so the full count is still >= n.
             Assert(pivot_count_monotone(ToSeq(found), i, len(found)))
             break
         c = found[i]
-        Assert(ToSeq(found)[i] == c)
-        Assert(pivot_count(ToSeq(found), i + 1)
-               == ToSeq(found)[(i + 1) - 1] + pivot_count(ToSeq(found), (i + 1) - 1))
         if c == 1:
-            k = k - 1
+            k = k - 2
         i = i + 1
     return k
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for sympy__sympy-23413.

Behaviour under specification (stated as desired behaviour, not as an edit):

  An integer matrix is reduced column-by-column from the bottom row upward.
  A running marker `k` records the leftmost column in which a pivot has so far
  been placed; it starts at the column count `n` (no pivots yet placed). Every
  row of the matrix is given the opportunity to contribute one pivot: a row that
  yields a nonzero pivot consumes the next free column (the marker moves one
  column to the left), while a row that yields only zeros consumes no column
  (the marker is unchanged). The search stops as soon as the marker reaches the
  leftmost column 0, because once every column already holds a pivot no further
  pivots are possible and no further rows need be examined.

  The reduced matrix retained at the end consists of the columns from the marker
  position to the right edge, so the number of retained columns equals the
  number of rows that contributed a pivot, capped by the column count. Crucially,
  EVERY row participates in this search -- a row near the top of a tall matrix
  must be able to contribute its pivot just as a row near the bottom can; the
  count of retained columns must never undercount the pivots merely because of a
  row's position.

The matrix is abstracted to its per-row pivot outcomes: `found` is a `List[int]`
with one 0/1 flag per row, given in the bottom-to-top processing order, and `n`
is the column count. The modelled function returns the final marker `k`; the
retained column count is `n - k`.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *

# axioms-start
# (No @ContractOnly axioms: the changed behaviour is modelled DEEPLY by the
#  pure helpers below and the verified loop, validated against the real routine
#  out-of-band by axiom_check.py / G-AX. There is no opaque unchanged callee.)
# axioms-end

# pure-start
@Pure
def valid_flags(s: PSeq[int]) -> bool:
    """Every entry of `s` is a 0/1 pivot-outcome flag."""
    return Forall(int, lambda t: (Implies(0 <= t and t < len(s),
                                          s[t] == 0 or s[t] == 1),
                                  [[s[t]]]))

@Pure
def pivot_count(s: PSeq[int], upto: int) -> int:
    """Number of pivot-yielding rows among the first `upto` rows of the
    bottom-to-top sequence `s` (each entry 0 or 1). Front-recursive on the
    suffix so a single unfold is available per loop step."""
    Requires(0 <= upto and upto <= len(s))
    Requires(valid_flags(s))
    Ensures(0 <= Result() and Result() <= upto)
    if upto == 0:
        return 0
    return s[upto - 1] + pivot_count(s, upto - 1)

@Pure
def pivot_count_monotone(s: PSeq[int], a: int, b: int) -> bool:
    """Lemma: pivot_count is non-decreasing in its bound (a <= b)."""
    Requires(valid_flags(s))
    Requires(0 <= a and a <= b and b <= len(s))
    Ensures(Result())
    Ensures(pivot_count(s, a) <= pivot_count(s, b))
    if a == b:
        return True
    return pivot_count_monotone(s, a, b - 1)
# pure-end

def leftmost_pivot_column(found: List[int], n: int) -> int:
    # pre-conditions-start
    Requires(Acc(list_pred(found), 1 / 2))
    Requires(n >= 0)
    # `found` is a per-row pivot-outcome flag (0 or 1), bottom-to-top.
    Requires(valid_flags(ToSeq(found)))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(found), 1 / 2))
    # The pivot-outcome flags are unchanged (read-only input).
    Ensures(valid_flags(ToSeq(found)))
    # The marker stays a valid column index.
    Ensures(0 <= Result() and Result() <= n)
    # The marker equals the column count minus the number of pivots contributed
    # by EVERY row, floored at column 0. No row's pivot is missed because of its
    # position: all len(found) rows are counted (max(0, n - total pivots)).
    Ensures(Implies(pivot_count(ToSeq(found), len(found)) <= n,
                    Result() == n - pivot_count(ToSeq(found), len(found))))
    Ensures(Implies(pivot_count(ToSeq(found), len(found)) > n, Result() == 0))
    # post-conditions-end
    # impl-start
    k = n
    i = 0
    while i < len(found):
        Invariant(Acc(list_pred(found), 1 / 2))
        Invariant(0 <= i and i <= len(found))
        Invariant(0 <= k and k <= n)
        Invariant(valid_flags(ToSeq(found)))
        Invariant(Implies(pivot_count(ToSeq(found), i) <= n,
                          k == n - pivot_count(ToSeq(found), i)))
        Invariant(Implies(pivot_count(ToSeq(found), i) > n, k == 0))
        if k == 0:
            Assert(pivot_count_monotone(ToSeq(found), i, len(found)))
            break
        c = found[i]
        Assert(ToSeq(found)[i] == c)
        Assert(pivot_count(ToSeq(found), i + 1)
               == ToSeq(found)[(i + 1) - 1] + pivot_count(ToSeq(found), (i + 1) - 1))
        if c == 1:
            k = k - 1
        i = i + 1
    return k
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

AUDIT FOCUS: A-legs + model<->patch correspondence (R/I legs mechanically covered by G-CONF). Verdict SOUND.

SPEC TIGHTNESS: leftmost_pivot_column's postcondition UNIQUELY pins Result() for every valid input: valid_flags(ToSeq(found)) forces each entry to 0/1, and the two Implies clauses (pivot_count<=n => Result()==n-pivot_count; pivot_count>n => Result()==0) together define Result() == max(0, n - sum(found)) with no free case. Any verifying impl must return exactly the gold marker k, hence retained-column count n-k = gold. There is no admitted wrong value.

ENV NOTE: `python -m swebench_unified.adversary` requires the module env; the awsbatch pyenv python lacks it. Ran all commands with python (has swebench_unified) which shells out to scripts/nagini_verify.sh for the JVM+Z3 verifier. Verified positive_control verifies (17.0s) and prepatch does NOT.

ATTACKS (all confirmed same-spec byte-identical via `adversary same-spec`; impl region only edited). Commands:
  python -m swebench_unified.adversary weakness nagini sympy__sympy-23413 <file>
Run concurrently in 3 batches of 3 (each Nagini check = 1 JVM+Z3).
  atk_1_prepatch.py  (prepatch min(len,n) bound bug; PREPATCH REPRODUCED) -> rc=2 NOT-A-COUNTEREXAMPLE (does not verify; spec rejects: invariant k==n-pivot_count fails / postcondition fails on found with a top-row pivot, e.g. [1,0,1] n=2).
  atk_2_return0.py   (partial-domain: return 0)          -> rc=2 does not verify.
  atk_3_returnn.py   (partial-domain: return n)          -> rc=2 does not verify.
  atk_4_offbyone.py  (boundary: while i < len(found)-1, skip top row) -> rc=2 does not verify (undercounts pivots).
  atk_5_nobreak.py   (control-flow: drop k==0 break; k can go <0) -> rc=2 does not verify (0<=k invariant / postcondition floor fails).
  atk_6_breakzero.py (control-flow-effect: break on first zero row) -> rc=2 does not verify (stops early, undercounts).
  atk_8_double.py    (wrong value: k-=2 on pivot)        -> rc=2 does not verify (k mismatch).
  atk_7_echo.py      (ungrounded-oracle echo: p=pivot_count(ToSeq(found),len(found)); return 0 if p>n else n-p) -> rc=0 CANDIDATE-COUNTEREXAMPLE: shares spec AND verifies (19.9s).

MANDATORY RESOLVE ON THE ONE CANDIDATE (atk_7 echo): the echo computes exactly max(0, n - sum(found)) = the gold marker law over EVERY row, so its FAITHFUL refined patch is the gold-behavior _hermite_normal_form (examine all rows, k==0 break, unchanged column reductions producing A[:, k:]). Materialized as atk_7_faithful_patch.diff and EXECUTED through the official harness (harness.run_resolve, image swebench/sweb.eval.x86_64.sympy_1776_sympy-23413:latest pulled from mirror.gcr.io + retagged). RESULT: RESOLVED = TRUE. report.json: patch_successfully_applied=true, resolved=true, FAIL_TO_PASS success=[test_hermite_normal], PASS_TO_PASS success=[test_smith_normal, test_smith_normal_deprecated], no failures. Saved to atk_7_resolve_report.json.

(First two run_resolve calls returned completed=False due to a `list_images` 404 ImageNotFound race caused by concurrent 'Cleaning cached images' during make_run_report AGGREGATION -- after this instance's grading report.json was already written. The authoritative per-instance report.json confirms resolved=true. Evaluation itself printed 'All instances run'. This is a contention artifact, not a non-resolve.) => atk_7 is a SOUND ECHO: verify => correct holds. NOT a weakness (consistent with the G-PANEL-1 echo policy: a same-spec verifying attack whose refined patch RESOLVES is not a break).

REFINEMENT.MD LEG AUDIT (A-legs + correspondence): A1 params found/n<->matrix+n = R (matrix abstracted to per-row pivot outcomes + col count, mapping.md 2); A2 k=n = I; A3 loop over ALL rows (range(m-1,-1,-1) vs prepatch range(m-1,m-1-min(m,n),-1)) = R; A4 k==0 break = I; A5 net decrement iff pivot (repo k-=1 then k+=1 if b==0) = R; A6 return k <-> return DomainMatrix.from_rep(A)[:, k:] with n-k=retained cols = R. B1 deep model pivot_count+verified loop <-> real _hermite_normal_form marker = A-REFERENCE (NOT a consumed @ContractOnly axiom -- axioms region is empty/comment-only). Section C explicitly asserts no kind-3 op: the one changed op (loop range + k==0 break) is modelled DEEPLY, not hidden behind an axiom. ALL legs are R / A-reference / I. No kind-3.

A-REFERENCE SOUNDNESS: axiom_check.py runs a faithful stdlib re-impl of the FIXED routine (Cohen 2.4.5) + cross-checks the REAL sympy _hermite_normal_form over 14 boundary + 60k fuzz, asserting model k == routine k == max(0, n-sum(found)) and n-k == real retained cols. conformance_check.py (G-CONF) independently bridges concrete matrices to (found,n) via the same unchanged per-row gcd arithmetic and asserts shadow n-k == real routine retained-col count over 14 boundary + 100k fuzz (seed 234131). The A-reference correspondence to the real callee HOLDS. Prepatch's min(m,n) bound is the exact reported bug (Matrix([[1,12],[0,8],[0,5]]) dropping the top pivot column); the spec's all-rows postcondition senses it (G-DIFF).

CONCLUSION: The frozen spec admits ONLY gold-equivalent implementations (postcondition uniquely determines the marker); the single verifying same-spec attack's faithful patch was EXECUTED through run_resolve and RESOLVED. No verifying wrong impl whose faithful patch fails to resolve was found across 8 distinct attacks (partial-domain, boundary, control-flow-effect, ungrounded-oracle echo). verify => correct is preserved. Verdict: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1_prepatch.py`, `atk_2_return0.py`, `atk_3_returnn.py`, `atk_4_offbyone.py`, `atk_5_nobreak.py`, `atk_6_breakzero.py`, `atk_8_double.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7_echo.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1_prepatch.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_return0.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3_returnn.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4_offbyone.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5_nobreak.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6_breakzero.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7_echo.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8_double.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for sympy__sympy-23413.

Behaviour under specification (stated as desired behaviour, not as an edit):

  An integer matrix is reduced column-by-column from the bottom row upward.
  A running marker `k` records the leftmost column in which a pivot has so far
  been placed; it starts at the column count `n` (no pivots yet placed). Every
  row of the matrix is given the opportunity to contribute one pivot: a row that
  yields a nonzero pivot consumes the next free column (the marker moves one
  column to the left), while a row that yields only zeros consumes no column
  (the marker is unchanged). The search stops as soon as the marker reaches the
  leftmost column 0, because once every column already holds a pivot no further
  pivots are possible and no further rows need be examined.

  The reduced matrix retained at the end consists of the columns from the marker
  position to the right edge, so the number of retained columns equals the
  number of rows that contributed a pivot, capped by the column count. Crucially,
  EVERY row participates in this search -- a row near the top of a tall matrix
  must be able to contribute its pivot just as a row near the bottom can; the
  count of retained columns must never undercount the pivots merely because of a
  row's position.

The matrix is abstracted to its per-row pivot outcomes: `found` is a `List[int]`
with one 0/1 flag per row, given in the bottom-to-top processing order, and `n`
is the column count. The modelled function returns the final marker `k`; the
retained column count is `n - k`.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *

# axioms-start
# (No @ContractOnly axioms: the changed behaviour is modelled DEEPLY by the
#  pure helpers below and the verified loop, validated against the real routine
#  out-of-band by axiom_check.py / G-AX. There is no opaque unchanged callee.)
# axioms-end

# pure-start
@Pure
def valid_flags(s: PSeq[int]) -> bool:
    """Every entry of `s` is a 0/1 pivot-outcome flag."""
    return Forall(int, lambda t: (Implies(0 <= t and t < len(s),
                                          s[t] == 0 or s[t] == 1),
                                  [[s[t]]]))

@Pure
def pivot_count(s: PSeq[int], upto: int) -> int:
    """Number of pivot-yielding rows among the first `upto` rows of the
    bottom-to-top sequence `s` (each entry 0 or 1). Front-recursive on the
    suffix so a single unfold is available per loop step."""
    Requires(0 <= upto and upto <= len(s))
    Requires(valid_flags(s))
    Ensures(0 <= Result() and Result() <= upto)
    if upto == 0:
        return 0
    return s[upto - 1] + pivot_count(s, upto - 1)

@Pure
def pivot_count_monotone(s: PSeq[int], a: int, b: int) -> bool:
    """Lemma: pivot_count is non-decreasing in its bound (a <= b)."""
    Requires(valid_flags(s))
    Requires(0 <= a and a <= b and b <= len(s))
    Ensures(Result())
    Ensures(pivot_count(s, a) <= pivot_count(s, b))
    if a == b:
        return True
    return pivot_count_monotone(s, a, b - 1)
# pure-end

def leftmost_pivot_column(found: List[int], n: int) -> int:
    # pre-conditions-start
    Requires(Acc(list_pred(found), 1 / 2))
    Requires(n >= 0)
    # `found` is a per-row pivot-outcome flag (0 or 1), bottom-to-top.
    Requires(valid_flags(ToSeq(found)))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(found), 1 / 2))
    # The pivot-outcome flags are unchanged (read-only input).
    Ensures(valid_flags(ToSeq(found)))
    # The marker stays a valid column index.
    Ensures(0 <= Result() and Result() <= n)
    # The marker equals the column count minus the number of pivots contributed
    # by EVERY row, floored at column 0. No row's pivot is missed because of its
    # position: all len(found) rows are counted (max(0, n - total pivots)).
    Ensures(Implies(pivot_count(ToSeq(found), len(found)) <= n,
                    Result() == n - pivot_count(ToSeq(found), len(found))))
    Ensures(Implies(pivot_count(ToSeq(found), len(found)) > n, Result() == 0))
    # post-conditions-end
    # impl-start
    k = n
    i = 0
    while i < len(found):
        Invariant(Acc(list_pred(found), 1 / 2))
        Invariant(0 <= i and i <= len(found))
        Invariant(0 <= k and k <= n)
        Invariant(valid_flags(ToSeq(found)))
        Invariant(Implies(pivot_count(ToSeq(found), i) <= n,
                          k == n - pivot_count(ToSeq(found), i)))
        Invariant(Implies(pivot_count(ToSeq(found), i) > n, k == 0))
        if k == 0:
            Assert(pivot_count_monotone(ToSeq(found), i, len(found)))
            break
        c = found[i]
        Assert(ToSeq(found)[i] == c)
        Assert(pivot_count(ToSeq(found), i + 1)
               == ToSeq(found)[(i + 1) - 1] + pivot_count(ToSeq(found), (i + 1) - 1))
        if c == 1:
            k = k - 1
        i = i + 1
    return k
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

AUDIT FOCUS: A-legs + model<->patch correspondence (R/I legs mechanically covered by G-CONF). Verdict SOUND.

SPEC TIGHTNESS: leftmost_pivot_column's postcondition UNIQUELY pins Result() for every valid input: valid_flags(ToSeq(found)) forces each entry to 0/1, and the two Implies clauses (pivot_count<=n => Result()==n-pivot_count; pivot_count>n => Result()==0) together define Result() == max(0, n - sum(found)) with no free case. Any verifying impl must return exactly the gold marker k, hence retained-column count n-k = gold. There is no admitted wrong value.

ENV NOTE: `python -m swebench_unified.adversary` requires the module env; the awsbatch pyenv python lacks it. Ran all commands with python (has swebench_unified) which shells out to scripts/nagini_verify.sh for the JVM+Z3 verifier. Verified positive_control verifies (17.0s) and prepatch does NOT.

ATTACKS (all confirmed same-spec byte-identical via `adversary same-spec`; impl region only edited). Commands:
  python -m swebench_unified.adversary weakness nagini sympy__sympy-23413 <file>
Run concurrently in 3 batches of 3 (each Nagini check = 1 JVM+Z3).
  atk_1_prepatch.py  (prepatch min(len,n) bound bug; PREPATCH REPRODUCED) -> rc=2 NOT-A-COUNTEREXAMPLE (does not verify; spec rejects: invariant k==n-pivot_count fails / postcondition fails on found with a top-row pivot, e.g. [1,0,1] n=2).
  atk_2_return0.py   (partial-domain: return 0)          -> rc=2 does not verify.
  atk_3_returnn.py   (partial-domain: return n)          -> rc=2 does not verify.
  atk_4_offbyone.py  (boundary: while i < len(found)-1, skip top row) -> rc=2 does not verify (undercounts pivots).
  atk_5_nobreak.py   (control-flow: drop k==0 break; k can go <0) -> rc=2 does not verify (0<=k invariant / postcondition floor fails).
  atk_6_breakzero.py (control-flow-effect: break on first zero row) -> rc=2 does not verify (stops early, undercounts).
  atk_8_double.py    (wrong value: k-=2 on pivot)        -> rc=2 does not verify (k mismatch).
  atk_7_echo.py      (ungrounded-oracle echo: p=pivot_count(ToSeq(found),len(found)); return 0 if p>n else n-p) -> rc=0 CANDIDATE-COUNTEREXAMPLE: shares spec AND verifies (19.9s).

MANDATORY RESOLVE ON THE ONE CANDIDATE (atk_7 echo): the echo computes exactly max(0, n - sum(found)) = the gold marker law over EVERY row, so its FAITHFUL refined patch is the gold-behavior _hermite_normal_form (examine all rows, k==0 break, unchanged column reductions producing A[:, k:]). Materialized as atk_7_faithful_patch.diff and EXECUTED through the official harness (harness.run_resolve, image swebench/sweb.eval.x86_64.sympy_1776_sympy-23413:latest pulled from mirror.gcr.io + retagged). RESULT: RESOLVED = TRUE. report.json: patch_successfully_applied=true, resolved=true, FAIL_TO_PASS success=[test_hermite_normal], PASS_TO_PASS success=[test_smith_normal, test_smith_normal_deprecated], no failures. Saved to atk_7_resolve_report.json.

(First two run_resolve calls returned completed=False due to a `list_images` 404 ImageNotFound race caused by concurrent 'Cleaning cached images' during make_run_report AGGREGATION -- after this instance's grading report.json was already written. The authoritative per-instance report.json confirms resolved=true. Evaluation itself printed 'All instances run'. This is a contention artifact, not a non-resolve.) => atk_7 is a SOUND ECHO: verify => correct holds. NOT a weakness (consistent with the G-PANEL-1 echo policy: a same-spec verifying attack whose refined patch RESOLVES is not a break).

REFINEMENT.MD LEG AUDIT (A-legs + correspondence): A1 params found/n<->matrix+n = R (matrix abstracted to per-row pivot outcomes + col count, mapping.md 2); A2 k=n = I; A3 loop over ALL rows (range(m-1,-1,-1) vs prepatch range(m-1,m-1-min(m,n),-1)) = R; A4 k==0 break = I; A5 net decrement iff pivot (repo k-=1 then k+=1 if b==0) = R; A6 return k <-> return DomainMatrix.from_rep(A)[:, k:] with n-k=retained cols = R. B1 deep model pivot_count+verified loop <-> real _hermite_normal_form marker = A-REFERENCE (NOT a consumed @ContractOnly axiom -- axioms region is empty/comment-only). Section C explicitly asserts no kind-3 op: the one changed op (loop range + k==0 break) is modelled DEEPLY, not hidden behind an axiom. ALL legs are R / A-reference / I. No kind-3.

A-REFERENCE SOUNDNESS: axiom_check.py runs a faithful stdlib re-impl of the FIXED routine (Cohen 2.4.5) + cross-checks the REAL sympy _hermite_normal_form over 14 boundary + 60k fuzz, asserting model k == routine k == max(0, n-sum(found)) and n-k == real retained cols. conformance_check.py (G-CONF) independently bridges concrete matrices to (found,n) via the same unchanged per-row gcd arithmetic and asserts shadow n-k == real routine retained-col count over 14 boundary + 100k fuzz (seed 234131). The A-reference correspondence to the real callee HOLDS. Prepatch's min(m,n) bound is the exact reported bug (Matrix([[1,12],[0,8],[0,5]]) dropping the top pivot column); the spec's all-rows postcondition senses it (G-DIFF).

CONCLUSION: The frozen spec admits ONLY gold-equivalent implementations (postcondition uniquely determines the marker); the single verifying same-spec attack's faithful patch was EXECUTED through run_resolve and RESOLVED. No verifying wrong impl whose faithful patch fails to resolve was found across 8 distinct attacks (partial-domain, boundary, control-flow-effect, ungrounded-oracle echo). verify => correct is preserved. Verdict: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec faithful to the real patched repo behavior. The modeled leftmost_pivot_column(found, n) pins the final HNF column marker k = max(0, n - pivot_count(found, len(found))), abstracting the integer matrix to per-row pivot-outcome flags. Verified byte-identical spec-region intent via the bundle's own same-spec reification (found derived by the exact stdlib extended-gcd trace G-AX/G-CONF use).

Empirical faithfulness against the REAL sympy.polys.matrices.normalforms._hermite_normal_form at base_commit+patch (run with mpmath-enabled interpreter):
- 30,000 small fuzz matrices (entries -4..4, shapes 1x1..6x6): 0 mismatches of (n - model_k) vs real result column count.
- 20,000 larger fuzz (entries -50..50, shapes up to 9x9): 0 mismatches.
- 15,000 extreme tall/wide shapes (exercising the k==0 early break): 0 mismatches.
- All 14 structured boundary matrices (reported issue matrix [[1,12],[0,8],[0,5]], tall/wide/zero/rank-deficient, negative pivots, marker-hits-zero): all match.
- Bundle axiom_check.py passes (14 boundary + 60k fuzz vs faithful reimplementation).

The `found` flag abstraction is well-defined by construction and the trace itself was confirmed to agree with real sympy directly. The pivot_count(found, len) > n -> 0 postcondition branch is a harmless generalization that real inputs never trigger (the k==0 break caps sum(found) at n). No input was found where the modeled function disagrees with the real callee; the spec is neither too strong nor drifted. No divergence => FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `axiom_check.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view confirmed byte-identical to recorded region hash (spec_view sha256 = b23e01ea3fc3ee423d2e407b1bd6a851f5c89dc29724110271938054c109f5f3), so this is the true solver-visible view. The view = docstring (framed 'as desired behaviour, not as an edit') + empty axioms region + pure helpers (valid_flags/pivot_count/pivot_count_monotone) + pre/post-conditions on leftmost_pivot_column; impl region correctly elided.

Public problem_statement (NOT hints): HNF 'removing rows' / 'falsely identifying my matrix as rank-deficient and removing the row' for a tall matrix where a top pivot is wrongly dropped (expected [[5,8,0],[0,0,1]], got [[5,8,0]]).

No gold-edit mechanics leak: the spec discloses NONE of the diff specifics -- no `min(m,n)`, no `rows` variable, no `range(m-1, m-1-rows, -1)` vs `range(m-1,-1,-1)`, no `_hermite_normal_form` symbol, no base-vs-fixed / diff framing. All such edit-level content resides only in refinement.md / mapping.md / meta.json / model_prepatch.py, which are NOT part of spec_view.

The two phrasings that could look suspicious are both derivable from the public statement and stated as abstract desired behavior, not as the edit: (1) 'EVERY row participates ... a row near the top of a tall matrix must be able to contribute its pivot ... count of retained columns must never undercount the pivots merely because of a row's position' is a WHAT-not-HOW restatement of the exact publicly reported symptom (a top-row pivot dropped as rank-deficient). (2) 'The search stops as soon as the marker reaches the leftmost column 0' (the k==0 stop) is given as an algorithmic invariant ('once every column already holds a pivot no further pivots are possible'), not as the `if k == 0: break` line's provenance vs the gold diff. Neither goes beyond the public problem_statement into revealing the code change; the postcondition max(0, n - pivot_count) is a legitimate behavioral spec. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.