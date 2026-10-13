# P2 adversarial audit — scikit-learn__scikit-learn-14894

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_8.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -31,7 +31,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -55,7 +54,6 @@
     Requires(start == 0)
     Requires(Exists(int, lambda count: (count >= 1 and stop == count * step + 1,
                                         [[count * step]])))
-    Requires(MustTerminate(2))
     Ensures(Acc(list_pred(Result())))
     Ensures(len(Result()) >= 2)
     # The k-th enumerated boundary is the k-th multiple of the step.
@@ -78,7 +76,6 @@
     # pre-conditions-start
     Requires(width >= 0)
     Requires(n_rows >= 1)
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -103,20 +100,7 @@
     # post-conditions-end
     # impl-start
     size = width * n_rows
-    if width == 0:
-        # Empty per-row width: the layout stores nothing (a valid empty layout).
-        return [0, 0]
-    else:
-        step = width
-        Assert(step >= 1)
-        # The upper bound size+1 is one past the n_rows-th multiple of step.
-        Assert(size + 1 == n_rows * step + 1)
-        indptr = range_step(0, size + 1, step)
-        # From the axiom: (len-1)*step + 1 == size+1 == n_rows*step + 1, hence
-        # (len-1)*step == n_rows*step; with step >= 1 the lengths match.
-        Assert((len(indptr) - 1) * step == n_rows * step)
-        Assert(len(indptr) - 1 == n_rows)
-        Assert(indptr[0] == 0 * step)
-        Assert(indptr[len(indptr) - 1] == (len(indptr) - 1) * step)
-        return indptr
+    step = width
+    indptr = range_step(0, size + 1, step)
+    return indptr
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -31,7 +31,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -55,7 +54,6 @@
     Requires(start == 0)
     Requires(Exists(int, lambda count: (count >= 1 and stop == count * step + 1,
                                         [[count * step]])))
-    Requires(MustTerminate(2))
     Ensures(Acc(list_pred(Result())))
     Ensures(len(Result()) >= 2)
     # The k-th enumerated boundary is the k-th multiple of the step.
@@ -78,7 +76,6 @@
     # pre-conditions-start
     Requires(width >= 0)
     Requires(n_rows >= 1)
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -104,19 +101,9 @@
     # impl-start
     size = width * n_rows
     if width == 0:
-        # Empty per-row width: the layout stores nothing (a valid empty layout).
-        return [0, 0]
+        return [0, 0, 0]
     else:
         step = width
-        Assert(step >= 1)
-        # The upper bound size+1 is one past the n_rows-th multiple of step.
-        Assert(size + 1 == n_rows * step + 1)
         indptr = range_step(0, size + 1, step)
-        # From the axiom: (len-1)*step + 1 == size+1 == n_rows*step + 1, hence
-        # (len-1)*step == n_rows*step; with step >= 1 the lengths match.
-        Assert((len(indptr) - 1) * step == n_rows * step)
-        Assert(len(indptr) - 1 == n_rows)
-        Assert(indptr[0] == 0 * step)
-        Assert(indptr[len(indptr) - 1] == (len(indptr) - 1) * step)
         return indptr
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -31,7 +31,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -55,7 +54,6 @@
     Requires(start == 0)
     Requires(Exists(int, lambda count: (count >= 1 and stop == count * step + 1,
                                         [[count * step]])))
-    Requires(MustTerminate(2))
     Ensures(Acc(list_pred(Result())))
     Ensures(len(Result()) >= 2)
     # The k-th enumerated boundary is the k-th multiple of the step.
@@ -78,7 +76,6 @@
     # pre-conditions-start
     Requires(width >= 0)
     Requires(n_rows >= 1)
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -103,20 +100,5 @@
     # post-conditions-end
     # impl-start
     size = width * n_rows
-    if width == 0:
-        # Empty per-row width: the layout stores nothing (a valid empty layout).
-        return [0, 0]
-    else:
-        step = width
-        Assert(step >= 1)
-        # The upper bound size+1 is one past the n_rows-th multiple of step.
-        Assert(size + 1 == n_rows * step + 1)
-        indptr = range_step(0, size + 1, step)
-        # From the axiom: (len-1)*step + 1 == size+1 == n_rows*step + 1, hence
-        # (len-1)*step == n_rows*step; with step >= 1 the lengths match.
-        Assert((len(indptr) - 1) * step == n_rows * step)
-        Assert(len(indptr) - 1 == n_rows)
-        Assert(indptr[0] == 0 * step)
-        Assert(indptr[len(indptr) - 1] == (len(indptr) - 1) * step)
-        return indptr
+    return [0, 0]
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -31,7 +31,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -55,7 +54,6 @@
     Requires(start == 0)
     Requires(Exists(int, lambda count: (count >= 1 and stop == count * step + 1,
                                         [[count * step]])))
-    Requires(MustTerminate(2))
     Ensures(Acc(list_pred(Result())))
     Ensures(len(Result()) >= 2)
     # The k-th enumerated boundary is the k-th multiple of the step.
@@ -78,7 +76,6 @@
     # pre-conditions-start
     Requires(width >= 0)
     Requires(n_rows >= 1)
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -104,19 +101,10 @@
     # impl-start
     size = width * n_rows
     if width == 0:
-        # Empty per-row width: the layout stores nothing (a valid empty layout).
         return [0, 0]
     else:
         step = width
-        Assert(step >= 1)
-        # The upper bound size+1 is one past the n_rows-th multiple of step.
-        Assert(size + 1 == n_rows * step + 1)
         indptr = range_step(0, size + 1, step)
-        # From the axiom: (len-1)*step + 1 == size+1 == n_rows*step + 1, hence
-        # (len-1)*step == n_rows*step; with step >= 1 the lengths match.
-        Assert((len(indptr) - 1) * step == n_rows * step)
-        Assert(len(indptr) - 1 == n_rows)
-        Assert(indptr[0] == 0 * step)
-        Assert(indptr[len(indptr) - 1] == (len(indptr) - 1) * step)
+        indptr.append(size + step)
         return indptr
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -31,7 +31,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -55,7 +54,6 @@
     Requires(start == 0)
     Requires(Exists(int, lambda count: (count >= 1 and stop == count * step + 1,
                                         [[count * step]])))
-    Requires(MustTerminate(2))
     Ensures(Acc(list_pred(Result())))
     Ensures(len(Result()) >= 2)
     # The k-th enumerated boundary is the k-th multiple of the step.
@@ -78,7 +76,6 @@
     # pre-conditions-start
     Requires(width >= 0)
     Requires(n_rows >= 1)
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -103,20 +100,10 @@
     # post-conditions-end
     # impl-start
     size = width * n_rows
-    if width == 0:
-        # Empty per-row width: the layout stores nothing (a valid empty layout).
+    if width != 0:
         return [0, 0]
     else:
         step = width
-        Assert(step >= 1)
-        # The upper bound size+1 is one past the n_rows-th multiple of step.
-        Assert(size + 1 == n_rows * step + 1)
         indptr = range_step(0, size + 1, step)
-        # From the axiom: (len-1)*step + 1 == size+1 == n_rows*step + 1, hence
-        # (len-1)*step == n_rows*step; with step >= 1 the lengths match.
-        Assert((len(indptr) - 1) * step == n_rows * step)
-        Assert(len(indptr) - 1 == n_rows)
-        Assert(indptr[0] == 0 * step)
-        Assert(indptr[len(indptr) - 1] == (len(indptr) - 1) * step)
         return indptr
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -31,7 +31,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -55,7 +54,6 @@
     Requires(start == 0)
     Requires(Exists(int, lambda count: (count >= 1 and stop == count * step + 1,
                                         [[count * step]])))
-    Requires(MustTerminate(2))
     Ensures(Acc(list_pred(Result())))
     Ensures(len(Result()) >= 2)
     # The k-th enumerated boundary is the k-th multiple of the step.
@@ -78,7 +76,6 @@
     # pre-conditions-start
     Requires(width >= 0)
     Requires(n_rows >= 1)
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -104,19 +101,11 @@
     # impl-start
     size = width * n_rows
     if width == 0:
-        # Empty per-row width: the layout stores nothing (a valid empty layout).
         return [0, 0]
     else:
         step = width
-        Assert(step >= 1)
-        # The upper bound size+1 is one past the n_rows-th multiple of step.
-        Assert(size + 1 == n_rows * step + 1)
         indptr = range_step(0, size + 1, step)
-        # From the axiom: (len-1)*step + 1 == size+1 == n_rows*step + 1, hence
-        # (len-1)*step == n_rows*step; with step >= 1 the lengths match.
-        Assert((len(indptr) - 1) * step == n_rows * step)
-        Assert(len(indptr) - 1 == n_rows)
-        Assert(indptr[0] == 0 * step)
-        Assert(indptr[len(indptr) - 1] == (len(indptr) - 1) * step)
+        if len(indptr) >= 3:
+            indptr[1] = 0
         return indptr
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -31,7 +31,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -55,7 +54,6 @@
     Requires(start == 0)
     Requires(Exists(int, lambda count: (count >= 1 and stop == count * step + 1,
                                         [[count * step]])))
-    Requires(MustTerminate(2))
     Ensures(Acc(list_pred(Result())))
     Ensures(len(Result()) >= 2)
     # The k-th enumerated boundary is the k-th multiple of the step.
@@ -78,7 +76,6 @@
     # pre-conditions-start
     Requires(width >= 0)
     Requires(n_rows >= 1)
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -103,20 +100,5 @@
     # post-conditions-end
     # impl-start
     size = width * n_rows
-    if width == 0:
-        # Empty per-row width: the layout stores nothing (a valid empty layout).
-        return [0, 0]
-    else:
-        step = width
-        Assert(step >= 1)
-        # The upper bound size+1 is one past the n_rows-th multiple of step.
-        Assert(size + 1 == n_rows * step + 1)
-        indptr = range_step(0, size + 1, step)
-        # From the axiom: (len-1)*step + 1 == size+1 == n_rows*step + 1, hence
-        # (len-1)*step == n_rows*step; with step >= 1 the lengths match.
-        Assert((len(indptr) - 1) * step == n_rows * step)
-        Assert(len(indptr) - 1 == n_rows)
-        Assert(indptr[0] == 0 * step)
-        Assert(indptr[len(indptr) - 1] == (len(indptr) - 1) * step)
-        return indptr
+    return [0, size]
     # impl-end
```

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -31,7 +31,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -55,7 +54,6 @@
     Requires(start == 0)
     Requires(Exists(int, lambda count: (count >= 1 and stop == count * step + 1,
                                         [[count * step]])))
-    Requires(MustTerminate(2))
     Ensures(Acc(list_pred(Result())))
     Ensures(len(Result()) >= 2)
     # The k-th enumerated boundary is the k-th multiple of the step.
@@ -78,7 +76,6 @@
     # pre-conditions-start
     Requires(width >= 0)
     Requires(n_rows >= 1)
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -103,20 +100,14 @@
     # post-conditions-end
     # impl-start
     size = width * n_rows
-    if width == 0:
-        # Empty per-row width: the layout stores nothing (a valid empty layout).
+    if width <= 0:
         return [0, 0]
     else:
         step = width
         Assert(step >= 1)
-        # The upper bound size+1 is one past the n_rows-th multiple of step.
         Assert(size + 1 == n_rows * step + 1)
         indptr = range_step(0, size + 1, step)
-        # From the axiom: (len-1)*step + 1 == size+1 == n_rows*step + 1, hence
-        # (len-1)*step == n_rows*step; with step >= 1 the lengths match.
         Assert((len(indptr) - 1) * step == n_rows * step)
         Assert(len(indptr) - 1 == n_rows)
-        Assert(indptr[0] == 0 * step)
-        Assert(indptr[len(indptr) - 1] == (len(indptr) - 1) * step)
         return indptr
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for scikit-learn__scikit-learn-14894.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A compressed-sparse-row block layout places a constant number of stored
  entries in each of its rows. For `n_rows` rows each holding `width` consecutive
  entries, the row-pointer array — the boundaries that delimit each row's slice
  of the flat storage — is the arithmetic progression

      [0, width, 2*width, ..., n_rows*width],

  whose final entry is the total number of stored entries, `width*n_rows`. When
  a row is empty (`width == 0`) the layout stores nothing: its row-pointer is
  exactly the pair of boundaries `[0, 0]` (the canonical empty layout — one
  opening boundary and one closing boundary, both 0), and the layout is still
  well defined. Constructing it must not require a positive per-row width —
  the all-empty case is a valid layout.

  The row-pointer array is produced by the numeric range-builder
  `range_step(start, stop, step)`, which enumerates `start, start+step, ...`
  up to (but excluding) `stop`. That builder is defined only for a strictly
  positive step (it advances by `step` per element, so a zero step has no
  progression). The construction therefore must establish a positive step
  before invoking the builder; that step is the per-row width.

The row-pointer is modelled as a `List[int]`; the per-row width and row count
are non-negative integers. The number of stored entries (the observable that
distinguishes the empty layout) is the final row-pointer entry.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
@ContractOnly
def range_step(start: int, stop: int, step: int) -> List[int]:
    """Numeric range-builder: the contiguous progression
    `start, start+step, start+2*step, ...` taking every value strictly below
    `stop`. It advances by `step` per element, so it is defined only for a
    strictly positive step (a zero step has no progression — a non-advancing
    enumeration of a half-open interval is undefined). The weakest contract the
    construction consumes: with `start == 0`, a positive `step`, and an upper
    bound that is one past the `count`-th multiple of the step
    (`stop == count*step + 1` with `count >= 1`, so the multiples
    `0..count*step` lie below `stop` and the next one does not), the result is
    the `count+1` boundaries `[0, step, 2*step, ..., count*step]`, whose k-th
    element is `k*step`. The progression is keyed to the multiple `count`
    (here `>= 1`, the number of rows) that the upper bound encodes.
    Provenance + executable soundness check: mapping.md / axiom_check.py.
    """
    Requires(step >= 1)
    Requires(start == 0)
    Requires(Exists(int, lambda count: (count >= 1 and stop == count * step + 1,
                                        [[count * step]])))
    Ensures(Acc(list_pred(Result())))
    Ensures(len(Result()) >= 2)
    # The k-th enumerated boundary is the k-th multiple of the step.
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(Result()),
                                            Result()[k] == k * step),
                                   [[Result()[k]]])))
    # Exactly the multiples below `stop` are enumerated: the last one is < stop
    # and the next would reach or pass it. This pins the final boundary to the
    # number of stored entries without any integer division.
    Ensures((len(Result()) - 1) * step + 1 == stop)
# axioms-end


# pure-start
# (no pure helpers required)
# pure-end


def row_pointer_for_block_layout(width: int, n_rows: int) -> List[int]:
    # pre-conditions-start
    Requires(width >= 0)
    Requires(n_rows >= 1)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    # The row-pointer is non-empty; it opens at boundary 0 (the start of the
    # flat storage) and its final entry is the number of stored entries:
    # `width` per row across `n_rows` rows. The final entry is 0 exactly when
    # the per-row width is 0, which is the empty-layout observable.
    Ensures(len(Result()) >= 2)
    Ensures(Result()[0] == 0)
    Ensures(Result()[len(Result()) - 1] == width * n_rows)
    # The empty layout is pinned EXACTLY: its row-pointer is the canonical
    # two-boundary pair [0, 0] (with the opening/closing clauses above, the
    # length pin leaves no unconstrained interior entries).
    Ensures(Implies(width == 0, len(Result()) == 2))
    # For a non-empty layout the row-pointer is the full progression
    # [0, width, ..., n_rows*width]: one boundary per row plus the closing one.
    Ensures(Implies(width >= 1, len(Result()) == n_rows + 1))
    Ensures(Implies(width >= 1,
                    Forall(int, lambda k: (Implies(0 <= k and k <= n_rows,
                                                   Result()[k] == k * width),
                                           [[k * width]]))))
    # post-conditions-end
    # impl-start
    size = width * n_rows
    if width == 0:
        # Empty per-row width: the layout stores nothing (a valid empty layout).
        return [0, 0]
    else:
        step = width
        Assert(step >= 1)
        # The upper bound size+1 is one past the n_rows-th multiple of step.
        Assert(size + 1 == n_rows * step + 1)
        indptr = range_step(0, size + 1, step)
        # From the axiom: (len-1)*step + 1 == size+1 == n_rows*step + 1, hence
        # (len-1)*step == n_rows*step; with step >= 1 the lengths match.
        Assert((len(indptr) - 1) * step == n_rows * step)
        Assert(len(indptr) - 1 == n_rows)
        Assert(indptr[0] == 0 * step)
        Assert(indptr[len(indptr) - 1] == (len(indptr) - 1) * step)
        return indptr
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Scratch dir Project root (env:, SBU_PYTHON=python, PYTHONPATH=src). Commands: `python -m swebench_unified.adversary weakness nagini scikit-learn__scikit-learn-14894 <atk>` per attack; `bash scripts/nagini_verify.sh <pos_control>`; run_resolve via harness.run_resolve for the sole candidate. Attacks run concurrently in 3 batches of <=3 JVM+Z3 jobs.

POSITIVE CONTROL pos_control.py (gold impl): same-spec=SAME, verify exit=0 (verifies).

8 distinct same-spec attacks (impl region edited only; axioms/@Pure/Requires/Ensures byte-identical, confirmed by same-spec/weakness accepting them as SAME):
- atk_1 PREPATCH repro (no width==0 guard, unconditional range_step): weakness exit=2, verification FAILED — cannot discharge range_step Requires(step>=1) when width==0. Prepatch bug reproduced (matches G-DIFF).
- atk_2 boundary: empty branch returns padded [0,0,0]: exit=2, rejected (violates Implies(width==0, len(Result())==2)).
- atk_3 partial-domain: constant [0,0] for all widths: exit=2, rejected (fails width>=1 length pin len==n_rows+1 and Forall progression).
- atk_4 boundary/off-by-one: appends extra closing boundary: exit=2, rejected (breaks len==n_rows+1 and final-entry==width*n_rows).
- atk_5 control-flow-effect: INVERTED guard (empty via else, nonempty via [0,0]): exit=2, rejected.
- atk_6 interior corruption for width>=1 (indptr[1]=0, endpoints kept): exit=2, rejected (fails Forall Result()[k]==k*width).
- atk_7 ungrounded-oracle echo: [0,size] two boundaries all widths (endpoints correct): exit=2, rejected (fails width>=1 len==n_rows+1 / interior progression).
- atk_8 CANDIDATE: correct alternative construction (width<=0 empty branch, identical else). weakness exit=0 (shares spec AND verifies, 13.1s). Materialized faithful refined patch = gold patch (atk_8 is behaviourally identical to gold over the full Requires domain: width<=0 with width>=0 <=> width==0; else-branch byte-identical to gold). run_resolve => RESOLVED=True, completed=True, attempts=1, flaky=False. FAIL_TO_PASS test_sparse_fit_support_vectors_empty PASSED; all 80 PASS_TO_PASS passed. So the only verifying wrong/alternative impl's faithful patch DOES resolve — no verify-but-not-correct witness found.

REFINEMENT AUDIT (refinement.md): every leg is R (A1 width<-n_SV, A2 n_rows<-n_class, A3 size=width*n_rows, A4 width==0 guard<->`if not n_SV`, A6 return<->csr assembly), A-consumed (A5 range_step<->np.arange), or I. NO kind-3 (unexpressible-changed-op) legs; the genuinely-changed op (adding the guard) is modeled DEEPLY as the if width==0 branch, not hidden behind an axiom. NO A-reference deep-model equality in this bundle. The one A-consumed leg (A5): the construction invokes range_step(0, size+1, width) = arange(0, n_rows*width+1, width), matching the axiom's Requires family (start==0, step==width>=1, stop==count*step+1 with count==n_rows>=1); correspondence to the real callee holds and is validated by G-AX/axiom_check.py (meta G-AX exit=0: real numpy.arange satisfies len>=2, result[k]==k*step, (len-1)*step+1==stop on 50 boundary + 20000 fuzz inputs; step==0 confirmed to raise on 6 witnesses). Empty-case object correspondence (sp.csr_matrix([]) is a (1,0) CSR with indptr==[0,0]) is pinned EXACTLY by the spec, matching real gold (not merely the F2P observable).

The spec pins BOTH branches exactly (empty: len==2 + Result()[0]==0 + final==0; non-empty: len==n_rows+1 + Result()[0]==0 + Forall Result()[k]==k*width + final==width*n_rows), leaving no slack for a verifying-but-incorrect impl. All 8 attacks fully verified and reported; the sole candidate's patch resolved. Verdict SOUND (>=5 attacks run, none breaks the spec).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_8.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for scikit-learn__scikit-learn-14894.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A compressed-sparse-row block layout places a constant number of stored
  entries in each of its rows. For `n_rows` rows each holding `width` consecutive
  entries, the row-pointer array — the boundaries that delimit each row's slice
  of the flat storage — is the arithmetic progression

      [0, width, 2*width, ..., n_rows*width],

  whose final entry is the total number of stored entries, `width*n_rows`. When
  a row is empty (`width == 0`) the layout stores nothing: its row-pointer is
  exactly the pair of boundaries `[0, 0]` (the canonical empty layout — one
  opening boundary and one closing boundary, both 0), and the layout is still
  well defined. Constructing it must not require a positive per-row width —
  the all-empty case is a valid layout.

  The row-pointer array is produced by the numeric range-builder
  `range_step(start, stop, step)`, which enumerates `start, start+step, ...`
  up to (but excluding) `stop`. That builder is defined only for a strictly
  positive step (it advances by `step` per element, so a zero step has no
  progression). The construction therefore must establish a positive step
  before invoking the builder; that step is the per-row width.

The row-pointer is modelled as a `List[int]`; the per-row width and row count
are non-negative integers. The number of stored entries (the observable that
distinguishes the empty layout) is the final row-pointer entry.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
@ContractOnly
def range_step(start: int, stop: int, step: int) -> List[int]:
    """Numeric range-builder: the contiguous progression
    `start, start+step, start+2*step, ...` taking every value strictly below
    `stop`. It advances by `step` per element, so it is defined only for a
    strictly positive step (a zero step has no progression — a non-advancing
    enumeration of a half-open interval is undefined). The weakest contract the
    construction consumes: with `start == 0`, a positive `step`, and an upper
    bound that is one past the `count`-th multiple of the step
    (`stop == count*step + 1` with `count >= 1`, so the multiples
    `0..count*step` lie below `stop` and the next one does not), the result is
    the `count+1` boundaries `[0, step, 2*step, ..., count*step]`, whose k-th
    element is `k*step`. The progression is keyed to the multiple `count`
    (here `>= 1`, the number of rows) that the upper bound encodes.
    Provenance + executable soundness check: mapping.md / axiom_check.py.
    """
    Requires(step >= 1)
    Requires(start == 0)
    Requires(Exists(int, lambda count: (count >= 1 and stop == count * step + 1,
                                        [[count * step]])))
    Ensures(Acc(list_pred(Result())))
    Ensures(len(Result()) >= 2)
    # The k-th enumerated boundary is the k-th multiple of the step.
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(Result()),
                                            Result()[k] == k * step),
                                   [[Result()[k]]])))
    # Exactly the multiples below `stop` are enumerated: the last one is < stop
    # and the next would reach or pass it. This pins the final boundary to the
    # number of stored entries without any integer division.
    Ensures((len(Result()) - 1) * step + 1 == stop)
# axioms-end


# pure-start
# (no pure helpers required)
# pure-end


def row_pointer_for_block_layout(width: int, n_rows: int) -> List[int]:
    # pre-conditions-start
    Requires(width >= 0)
    Requires(n_rows >= 1)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    # The row-pointer is non-empty; it opens at boundary 0 (the start of the
    # flat storage) and its final entry is the number of stored entries:
    # `width` per row across `n_rows` rows. The final entry is 0 exactly when
    # the per-row width is 0, which is the empty-layout observable.
    Ensures(len(Result()) >= 2)
    Ensures(Result()[0] == 0)
    Ensures(Result()[len(Result()) - 1] == width * n_rows)
    # The empty layout is pinned EXACTLY: its row-pointer is the canonical
    # two-boundary pair [0, 0] (with the opening/closing clauses above, the
    # length pin leaves no unconstrained interior entries).
    Ensures(Implies(width == 0, len(Result()) == 2))
    # For a non-empty layout the row-pointer is the full progression
    # [0, width, ..., n_rows*width]: one boundary per row plus the closing one.
    Ensures(Implies(width >= 1, len(Result()) == n_rows + 1))
    Ensures(Implies(width >= 1,
                    Forall(int, lambda k: (Implies(0 <= k and k <= n_rows,
                                                   Result()[k] == k * width),
                                           [[k * width]]))))
    # post-conditions-end
    # impl-start
    size = width * n_rows
    if width == 0:
        # Empty per-row width: the layout stores nothing (a valid empty layout).
        return [0, 0]
    else:
        step = width
        Assert(step >= 1)
        # The upper bound size+1 is one past the n_rows-th multiple of step.
        Assert(size + 1 == n_rows * step + 1)
        indptr = range_step(0, size + 1, step)
        # From the axiom: (len-1)*step + 1 == size+1 == n_rows*step + 1, hence
        # (len-1)*step == n_rows*step; with step >= 1 the lengths match.
        Assert((len(indptr) - 1) * step == n_rows * step)
        Assert(len(indptr) - 1 == n_rows)
        Assert(indptr[0] == 0 * step)
        Assert(indptr[len(indptr) - 1] == (len(indptr) - 1) * step)
        return indptr
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Scratch dir Project root (env:, SBU_PYTHON=python, PYTHONPATH=src). Commands: `python -m swebench_unified.adversary weakness nagini scikit-learn__scikit-learn-14894 <atk>` per attack; `bash scripts/nagini_verify.sh <pos_control>`; run_resolve via harness.run_resolve for the sole candidate. Attacks run concurrently in 3 batches of <=3 JVM+Z3 jobs.

POSITIVE CONTROL pos_control.py (gold impl): same-spec=SAME, verify exit=0 (verifies).

8 distinct same-spec attacks (impl region edited only; axioms/@Pure/Requires/Ensures byte-identical, confirmed by same-spec/weakness accepting them as SAME):
- atk_1 PREPATCH repro (no width==0 guard, unconditional range_step): weakness exit=2, verification FAILED — cannot discharge range_step Requires(step>=1) when width==0. Prepatch bug reproduced (matches G-DIFF).
- atk_2 boundary: empty branch returns padded [0,0,0]: exit=2, rejected (violates Implies(width==0, len(Result())==2)).
- atk_3 partial-domain: constant [0,0] for all widths: exit=2, rejected (fails width>=1 length pin len==n_rows+1 and Forall progression).
- atk_4 boundary/off-by-one: appends extra closing boundary: exit=2, rejected (breaks len==n_rows+1 and final-entry==width*n_rows).
- atk_5 control-flow-effect: INVERTED guard (empty via else, nonempty via [0,0]): exit=2, rejected.
- atk_6 interior corruption for width>=1 (indptr[1]=0, endpoints kept): exit=2, rejected (fails Forall Result()[k]==k*width).
- atk_7 ungrounded-oracle echo: [0,size] two boundaries all widths (endpoints correct): exit=2, rejected (fails width>=1 len==n_rows+1 / interior progression).
- atk_8 CANDIDATE: correct alternative construction (width<=0 empty branch, identical else). weakness exit=0 (shares spec AND verifies, 13.1s). Materialized faithful refined patch = gold patch (atk_8 is behaviourally identical to gold over the full Requires domain: width<=0 with width>=0 <=> width==0; else-branch byte-identical to gold). run_resolve => RESOLVED=True, completed=True, attempts=1, flaky=False. FAIL_TO_PASS test_sparse_fit_support_vectors_empty PASSED; all 80 PASS_TO_PASS passed. So the only verifying wrong/alternative impl's faithful patch DOES resolve — no verify-but-not-correct witness found.

REFINEMENT AUDIT (refinement.md): every leg is R (A1 width<-n_SV, A2 n_rows<-n_class, A3 size=width*n_rows, A4 width==0 guard<->`if not n_SV`, A6 return<->csr assembly), A-consumed (A5 range_step<->np.arange), or I. NO kind-3 (unexpressible-changed-op) legs; the genuinely-changed op (adding the guard) is modeled DEEPLY as the if width==0 branch, not hidden behind an axiom. NO A-reference deep-model equality in this bundle. The one A-consumed leg (A5): the construction invokes range_step(0, size+1, width) = arange(0, n_rows*width+1, width), matching the axiom's Requires family (start==0, step==width>=1, stop==count*step+1 with count==n_rows>=1); correspondence to the real callee holds and is validated by G-AX/axiom_check.py (meta G-AX exit=0: real numpy.arange satisfies len>=2, result[k]==k*step, (len-1)*step+1==stop on 50 boundary + 20000 fuzz inputs; step==0 confirmed to raise on 6 witnesses). Empty-case object correspondence (sp.csr_matrix([]) is a (1,0) CSR with indptr==[0,0]) is pinned EXACTLY by the spec, matching real gold (not merely the F2P observable).

The spec pins BOTH branches exactly (empty: len==2 + Result()[0]==0 + final==0; non-empty: len==n_rows+1 + Result()[0]==0 + Forall Result()[k]==k*width + final==width*n_rows), leaving no slack for a verifying-but-incorrect impl. All 8 attacks fully verified and reported; the sole candidate's patch resolved. Verdict SOUND (>=5 attacks run, none breaks the spec).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness of the modeled function row_pointer_for_block_layout vs. the real callee (the dual-coef CSR row-pointer assembly in BaseLibSVM._sparse_fit, sklearn/svm/base.py:287-294 @ base_commit fdbaa58). 

Spec region confirmed byte-identical to model_prepatch.py (only the impl differs; intended G-DIFF setup). Model verifies with pinned Nagini: 'Verification successful' (12.57s).

Real repo behavior:
 - n_SV==0 (width 0): self.dual_coef_ = sp.csr_matrix([]) -> shape (1,0), data.size 0, indptr==[0,0] (verified empirically with scipy). Spec pins width==0 -> len==2, [0]==0, last==0, i.e. exactly [0,0]. MATCH (matches the real gold object's indptr, not just the F2P observable data.size==0).
 - n_SV>=1: np.arange(0, size+1, size/n_class) with size=n_SV*n_class, float step size/n_class==n_SV -> [0, n_SV, ..., n_class*n_SV], length n_class+1. Spec pins width>=1 -> len==n_rows+1 and [k]==k*width. MATCH.

Critical faithfulness concern examined: the REAL code uses a FLOAT step (dual_coef_indices.size / n_class), but the axiom/model use an integer step. Stress-tested the real float-step np.arange (numpy 1.26.4) against the integer spec over the entire REACHABLE domain (n_SV up to 1e7, n_class up to 1e3; hundreds of thousands of boundary+random draws): ZERO divergences in both length and rounded values. The only inputs where float np.arange diverges from the integer progression require width*n_rows > 2^53 (~9e15 stored coefficients) - a pure float64-precision artifact, physically unreachable for any fitted SVM (that many stored dual coefficients is impossible). No reachable (width>=0, n_rows>=1) input makes the spec disagree with the real callee.

Axiom (range_step<->np.arange) soundness: partiality at step==0 is correctly excluded (Requires step>=1); the real np.arange(0,stop,0) raises the very ZeroDivisionError the issue reports, so the exclusion is sound not over-restrictive (axiom_check.py confirms on 6 witnesses). The guard establishes step==width>=1 before the call, exactly as the gold patch's 'if not n_SV' guard does.

No spec-too-strong drift: every spec postcondition is met by the real repo on every reachable input. Verdict FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `axiom_check.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen (swebench_unified.leakage.screen over the spec_view) passes with zero hard failures; bundle is NOT relaxed (relaxed_leakage=None, no RELAXED_LEAKAGE.md). Independent judgment confirms NO-LEAKAGE.

Gold edit: adds `if not n_SV: self.dual_coef_ = sp.csr_matrix([])` guard around `np.arange(0, dual_coef_indices.size + 1, dual_coef_indices.size / n_class)` in BaseLibSVM._sparse_fit, avoiding ZeroDivisionError when n_SV==0.

The spec view (impl elided to `...`) is stated in fully repo-neutral vocabulary (CSR block layout, width/n_rows, range_step, row_pointer_for_block_layout). Token scan finds none of: n_SV, n_class, csr_matrix, _sparse_fit, dual_coef, np.arange, support_vectors, sklearn, base.py, `if not`. The one changed repo symbol per _patch_changed_symbols is `sparse_fit` — it does not appear anywhere in the spec view. The discriminating gold content (the `if width==0` guard) lives entirely in the elided impl region and is not shown.

Critically, the PUBLIC problem_statement already discloses the whole fix: title 'ZeroDivisionError in _sparse_fit for SVM with empty support_vectors_', the failing division `dual_coef_indices.size / n_class` -> ZeroDivisionError, and Expected Results explicitly '`self.dual_coef_ = sp.csr_matrix([])`'. The only spec-view lines touching the fix are (a) the empty case pinned to [0,0] (a paraphrase of the public expected sp.csr_matrix([])) and (b) 'must establish a positive step before invoking the builder / a zero step has no progression' (a paraphrase of the public zero-division). Both reveal nothing beyond problem_statement. No spec-view line leaks the gold edit beyond the public problem_statement (hints_text is empty and not consulted).

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
