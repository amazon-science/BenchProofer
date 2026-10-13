# P2 adversarial audit — sympy__sympy-23824

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies (1 did not reach the verifier: the checker could not translate it, so it counts in neither tally)

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_7.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.py` |
| changed the specification rather than only the implementation, so it does not test the specification this bundle ships | 1 | `atk_5.py` |

**Non-vacuity.** The positive control `model_orig.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -32,7 +32,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -55,7 +54,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(leading), 1 / 2))
     Requires(Acc(list_pred(tail), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(leading), 1 / 2))
@@ -66,6 +64,17 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
+    j = 0
+    while j < len(tail):
+        # invariants-start
+        Invariant(Acc(list_pred(leading), 1 / 2))
+        Invariant(Acc(list_pred(tail), 1 / 2))
+        Invariant(Acc(list_pred(result)))
+        Invariant(0 <= j and j <= len(tail))
+        Invariant(ToSeq(result) == ToSeq(tail).take(j))
+        # invariants-end
+        result.append(tail[j])
+        j = j + 1
     i = 0
     while i < len(leading):
         # invariants-start
@@ -73,22 +82,9 @@
         Invariant(Acc(list_pred(tail), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(leading))
-        Invariant(ToSeq(result) == ToSeq(leading).take(i))
-        Invariant(MustTerminate(len(leading) - i + 1))
         # invariants-end
-        result.append(leading[i])
+        front = [leading[i]]  # type: List[int]
+        result = front + result
         i = i + 1
-    j = 0
-    while j < len(tail):
-        # invariants-start
-        Invariant(Acc(list_pred(leading), 1 / 2))
-        Invariant(Acc(list_pred(tail), 1 / 2))
-        Invariant(Acc(list_pred(result)))
-        Invariant(0 <= j and j <= len(tail))
-        Invariant(ToSeq(result) == ToSeq(leading) + ToSeq(tail).take(j))
-        Invariant(MustTerminate(len(tail) - j + 1))
-        # invariants-end
-        result.append(tail[j])
-        j = j + 1
     return result
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -32,7 +32,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -55,7 +54,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(leading), 1 / 2))
     Requires(Acc(list_pred(tail), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(leading), 1 / 2))
@@ -66,6 +64,16 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
+    j = 0
+    while j < len(tail):
+        # invariants-start
+        Invariant(Acc(list_pred(leading), 1 / 2))
+        Invariant(Acc(list_pred(tail), 1 / 2))
+        Invariant(Acc(list_pred(result)))
+        Invariant(0 <= j and j <= len(tail))
+        # invariants-end
+        result.append(tail[j])
+        j = j + 1
     i = 0
     while i < len(leading):
         # invariants-start
@@ -73,22 +81,8 @@
         Invariant(Acc(list_pred(tail), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(leading))
-        Invariant(ToSeq(result) == ToSeq(leading).take(i))
-        Invariant(MustTerminate(len(leading) - i + 1))
         # invariants-end
         result.append(leading[i])
         i = i + 1
-    j = 0
-    while j < len(tail):
-        # invariants-start
-        Invariant(Acc(list_pred(leading), 1 / 2))
-        Invariant(Acc(list_pred(tail), 1 / 2))
-        Invariant(Acc(list_pred(result)))
-        Invariant(0 <= j and j <= len(tail))
-        Invariant(ToSeq(result) == ToSeq(leading) + ToSeq(tail).take(j))
-        Invariant(MustTerminate(len(tail) - j + 1))
-        # invariants-end
-        result.append(tail[j])
-        j = j + 1
     return result
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -32,7 +32,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -55,7 +54,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(leading), 1 / 2))
     Requires(Acc(list_pred(tail), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(leading), 1 / 2))
@@ -67,14 +65,12 @@
     # impl-start
     result = []  # type: List[int]
     i = 0
-    while i < len(leading):
+    while i < len(leading) - 1:
         # invariants-start
         Invariant(Acc(list_pred(leading), 1 / 2))
         Invariant(Acc(list_pred(tail), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(leading))
-        Invariant(ToSeq(result) == ToSeq(leading).take(i))
-        Invariant(MustTerminate(len(leading) - i + 1))
         # invariants-end
         result.append(leading[i])
         i = i + 1
@@ -85,8 +81,6 @@
         Invariant(Acc(list_pred(tail), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= j and j <= len(tail))
-        Invariant(ToSeq(result) == ToSeq(leading) + ToSeq(tail).take(j))
-        Invariant(MustTerminate(len(tail) - j + 1))
         # invariants-end
         result.append(tail[j])
         j = j + 1
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -32,7 +32,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -55,7 +54,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(leading), 1 / 2))
     Requires(Acc(list_pred(tail), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(leading), 1 / 2))
@@ -66,18 +64,6 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    i = 0
-    while i < len(leading):
-        # invariants-start
-        Invariant(Acc(list_pred(leading), 1 / 2))
-        Invariant(Acc(list_pred(tail), 1 / 2))
-        Invariant(Acc(list_pred(result)))
-        Invariant(0 <= i and i <= len(leading))
-        Invariant(ToSeq(result) == ToSeq(leading).take(i))
-        Invariant(MustTerminate(len(leading) - i + 1))
-        # invariants-end
-        result.append(leading[i])
-        i = i + 1
     j = 0
     while j < len(tail):
         # invariants-start
@@ -85,8 +71,6 @@
         Invariant(Acc(list_pred(tail), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= j and j <= len(tail))
-        Invariant(ToSeq(result) == ToSeq(leading) + ToSeq(tail).take(j))
-        Invariant(MustTerminate(len(tail) - j + 1))
         # invariants-end
         result.append(tail[j])
         j = j + 1
```

Attack 5 — `atk_5.py` → not a counterexample (the checker could not translate this program, so the spec never judged it)

```diff
@@ -32,7 +32,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -55,7 +54,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(leading), 1 / 2))
     Requires(Acc(list_pred(tail), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(leading), 1 / 2))
@@ -66,29 +64,12 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    i = 0
-    while i < len(leading):
+    while True:
         # invariants-start
         Invariant(Acc(list_pred(leading), 1 / 2))
         Invariant(Acc(list_pred(tail), 1 / 2))
         Invariant(Acc(list_pred(result)))
-        Invariant(0 <= i and i <= len(leading))
-        Invariant(ToSeq(result) == ToSeq(leading).take(i))
-        Invariant(MustTerminate(len(leading) - i + 1))
         # invariants-end
-        result.append(leading[i])
-        i = i + 1
-    j = 0
-    while j < len(tail):
-        # invariants-start
-        Invariant(Acc(list_pred(leading), 1 / 2))
-        Invariant(Acc(list_pred(tail), 1 / 2))
-        Invariant(Acc(list_pred(result)))
-        Invariant(0 <= j and j <= len(tail))
-        Invariant(ToSeq(result) == ToSeq(leading) + ToSeq(tail).take(j))
-        Invariant(MustTerminate(len(tail) - j + 1))
-        # invariants-end
-        result.append(tail[j])
-        j = j + 1
+        result = result
     return result
     # impl-end
```

Attack 6 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -32,7 +32,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -55,7 +54,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(leading), 1 / 2))
     Requires(Acc(list_pred(tail), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(leading), 1 / 2))
@@ -65,30 +63,6 @@
     Ensures(ToSeq(Result()) == ToSeq(leading) + ToSeq(tail))
     # post-conditions-end
     # impl-start
-    result = []  # type: List[int]
-    i = 0
-    while i < len(leading):
-        # invariants-start
-        Invariant(Acc(list_pred(leading), 1 / 2))
-        Invariant(Acc(list_pred(tail), 1 / 2))
-        Invariant(Acc(list_pred(result)))
-        Invariant(0 <= i and i <= len(leading))
-        Invariant(ToSeq(result) == ToSeq(leading).take(i))
-        Invariant(MustTerminate(len(leading) - i + 1))
-        # invariants-end
-        result.append(leading[i])
-        i = i + 1
-    j = 0
-    while j < len(tail):
-        # invariants-start
-        Invariant(Acc(list_pred(leading), 1 / 2))
-        Invariant(Acc(list_pred(tail), 1 / 2))
-        Invariant(Acc(list_pred(result)))
-        Invariant(0 <= j and j <= len(tail))
-        Invariant(ToSeq(result) == ToSeq(leading) + ToSeq(tail).take(j))
-        Invariant(MustTerminate(len(tail) - j + 1))
-        # invariants-end
-        result.append(tail[j])
-        j = j + 1
+    result = leading + tail  # type: List[int]
     return result
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -32,7 +32,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -55,7 +54,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(leading), 1 / 2))
     Requires(Acc(list_pred(tail), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(leading), 1 / 2))
@@ -66,29 +64,6 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    i = 0
-    while i < len(leading):
-        # invariants-start
-        Invariant(Acc(list_pred(leading), 1 / 2))
-        Invariant(Acc(list_pred(tail), 1 / 2))
-        Invariant(Acc(list_pred(result)))
-        Invariant(0 <= i and i <= len(leading))
-        Invariant(ToSeq(result) == ToSeq(leading).take(i))
-        Invariant(MustTerminate(len(leading) - i + 1))
-        # invariants-end
-        result.append(leading[i])
-        i = i + 1
-    j = 0
-    while j < len(tail):
-        # invariants-start
-        Invariant(Acc(list_pred(leading), 1 / 2))
-        Invariant(Acc(list_pred(tail), 1 / 2))
-        Invariant(Acc(list_pred(result)))
-        Invariant(0 <= j and j <= len(tail))
-        Invariant(ToSeq(result) == ToSeq(leading) + ToSeq(tail).take(j))
-        Invariant(MustTerminate(len(tail) - j + 1))
-        # invariants-end
-        result.append(tail[j])
-        j = j + 1
+    Assert(False)
     return result
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `model_orig.py`

```python
"""Twin-artifact model for sympy__sympy-23824.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A product of gamma matrices may begin with a run of leading uncontracted
  ("free") factors before the first contracted factor. The simplification
  algorithm sets those leading factors aside while it rewrites the contracted
  part, then must restore them in front of each resulting term. Restoring them
  must PRESERVE their original left-to-right order: a result term is the leading
  run, in its original order, followed by the term the core rewrite produced.

  Concretely, given the leading run `leading = [g_0, g_1, ..., g_{k-1}]` (the
  factors that precede the first contracted factor, in their original order) and
  a core-result term `tail`, the restored term is the concatenation

      leading[0], leading[1], ..., leading[k-1],  tail[0], tail[1], ...

  i.e. `leading ++ tail`, with the leading factors in the SAME left-to-right
  order in which they appeared in the input.

Gamma-matrix factors are identified by their integer index labels, so a term is
modelled as a `List[int]` (Nagini bans `str` indexing; the same `List` carrier
is the natural model for the algorithm's list-of-index-labels). The
specification is carried by `PSeq[int]` via `ToSeq`, and `+` is sequence
concatenation.

The two read-only inputs (`leading`, `tail`) carry fractional permission; the
operation builds and returns a fresh list. No callee is axiomatized: the entire
modelled operation is sequence concatenation, spelled out deeply in the impl.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (no axioms: the modelled operation is the order-preserving prepend of the
# leading run onto a core-result term — pure sequence concatenation, spelled
# out deeply in the impl region. The factors set aside / the core-result term
# are read-only inputs, an R-refinement of the unchanged surrounding algorithm.)
# axioms-end


# pure-start
# (no pure helpers: the specification is stated directly over PSeq[int]
# concatenation via ToSeq.)
# pure-end


def restore_leading(leading: List[int], tail: List[int]) -> List[int]:
    """Restore the leading run in front of a core-result term, preserving the
    leading factors' original left-to-right order: `leading ++ tail`."""
    # pre-conditions-start
    Requires(Acc(list_pred(leading), 1 / 2))
    Requires(Acc(list_pred(tail), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(leading), 1 / 2))
    Ensures(Acc(list_pred(tail), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The result is the leading run, in its original order, followed by `tail`.
    Ensures(ToSeq(Result()) == ToSeq(leading) + ToSeq(tail))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    i = 0
    while i < len(leading):
        # invariants-start
        Invariant(Acc(list_pred(leading), 1 / 2))
        Invariant(Acc(list_pred(tail), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(leading))
        Invariant(ToSeq(result) == ToSeq(leading).take(i))
        # invariants-end
        result.append(leading[i])
        i = i + 1
    j = 0
    while j < len(tail):
        # invariants-start
        Invariant(Acc(list_pred(leading), 1 / 2))
        Invariant(Acc(list_pred(tail), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(tail))
        Invariant(ToSeq(result) == ToSeq(leading) + ToSeq(tail).take(j))
        # invariants-end
        result.append(tail[j])
        j = j + 1
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial audit of nagini bundle sympy__sympy-23824 (restore_leading). Spec postcondition pins the EXACT return value: Ensures(ToSeq(Result()) == ToSeq(leading) + ToSeq(tail)). All 7 attacks are byte-identical in the spec region (same-spec exit 0 for all). Env: swebench-lean venv; SBU_BENCHMARK_DIR=benchmark-verified; SBU_BENCHMARK=swe_bench_verified.

### ATTACKS (cmd: `python -m swebench_unified.adversary weakness nagini sympy__sympy-23824 <path>`; run in batches of 3, JVM+Z3 each):
- atk_1.py (prepatch bug: reversed leading via `front + result` front-insert loop) -> exit 2, does NOT verify. PREPATCH REPRODUCED (matches model_prepatch.py; postcondition unprovable once leading run has >=2 distinct factors).
- atk_2.py (order swap: tail ++ leading) -> exit 2, does NOT verify (wrong value).
- atk_3.py (boundary/off-by-one: first loop bound `len(leading)-1`, drops last leading factor) -> exit 2, does NOT verify.
- atk_4.py (partial-domain: copies tail only, drops leading entirely) -> exit 2, does NOT verify.
- atk_5.py (control-flow-effect: `while True` non-termination, wrong empty return) -> exit 2, NOT JUDGED. Verbose verify (`bash scripts/nagini_verify.sh`) reports `Type error: dead.code @74` -> the wrong return is unreachable, and the front end refuses the program on that ground, so it never reached the verifier and the spec never ruled on it (it counts in neither tally). What this establishes is narrower: the attack shape is unexpressible in nagini's fragment, so this file did not test the spec's method-level MustTerminate, and whether that clause would reject a TRANSLATABLE diverging rival is a separate question this attack does not settle.
- atk_7.py (control-flow-effect: `Assert(False)` then wrong empty return) -> exit 2, does NOT verify (assertion unprovable; no infeasible-path vacuity).
- atk_6.py (ungrounded-oracle echo / behaviorally-correct alt algorithm: `result = leading + tail`) -> exit 0, CANDIDATE (shares spec AND verifies, 13.7s). Per 2026-08-06 echo-attack policy, materialized faithful refined patch (== gold hunk verbatim, per refinement.md A5) and RAN run_resolve on swe_bench_verified: RESOLVED=True, completed=True, attempts=1, non-flaky; FAIL_TO_PASS test_kahane_simplify1 PASS, PASS_TO_PASS {test_kahane_algorithm, test_gamma_matrix_class} PASS. A resolving echo is NOT a weakness.

POSITIVE CONTROL: bundle model.py (model_orig.py) verifies (Verification successful, 13.24s).

A-LEG / MODEL-CORRESPONDENCE AUDIT: refinement.md declares NO axioms and NO A-legs; this is HONEST. model.py has exactly one def (restore_leading), no @ContractOnly, no @Pure helper, and no axiom_check.py exists (G-AX vacuously skip). The gold patch is pure list concatenation `resulting_indices = list(free_pos[0:first_dum_pos] + ri for ri in resulting_indices)`. Every leg A1-A5 is R (list-of-index-labels <-> List[int]; list `+` <-> PSeq `+`) or I (identical concatenation, order-preserving); no kind-3 (unexpressible-changed-op). The single-representative-term modeling is faithful: the gold comprehension applies the same per-term transform uniformly (unchanged map wrapper), so modeling one `ri` captures the entire observable change. mapping.md bindings check out (free_pos[0:first_dum_pos]<->leading, ri<->tail, len(leading)<->first_dum_pos). G-CONF present and passes (100201 inputs, 0 disagreements, real AST-located statement oracle + full-pipeline grounding leg).

VERDICT: SOUND. >=5 distinct wrong impls (prepatch, swap, boundary, partial-domain, control-flow-effect via `Assert(False)`) all correctly REJECTED by the value-pinning postcondition; the only verifying candidate is a behaviorally-correct echo whose materialized faithful patch RESOLVES under the official harness. No verifying wrong-impl's faithful patch fails to resolve => no verify-but-not-correct gap. The spec neither admits an incorrect implementation nor rests on any axiom trust point.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies (1 did not reach the verifier: the checker could not translate it, so it counts in neither tally)

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_7.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.py` |
| changed the specification rather than only the implementation, so it does not test the specification this bundle ships | 1 | `atk_5.py` |

**Non-vacuity.** The positive control `model_orig.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → not a counterexample (the checker could not translate this program, so the spec never judged it)

Attack 6 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `model_orig.py`

```python
"""Twin-artifact model for sympy__sympy-23824.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A product of gamma matrices may begin with a run of leading uncontracted
  ("free") factors before the first contracted factor. The simplification
  algorithm sets those leading factors aside while it rewrites the contracted
  part, then must restore them in front of each resulting term. Restoring them
  must PRESERVE their original left-to-right order: a result term is the leading
  run, in its original order, followed by the term the core rewrite produced.

  Concretely, given the leading run `leading = [g_0, g_1, ..., g_{k-1}]` (the
  factors that precede the first contracted factor, in their original order) and
  a core-result term `tail`, the restored term is the concatenation

      leading[0], leading[1], ..., leading[k-1],  tail[0], tail[1], ...

  i.e. `leading ++ tail`, with the leading factors in the SAME left-to-right
  order in which they appeared in the input.

Gamma-matrix factors are identified by their integer index labels, so a term is
modelled as a `List[int]` (Nagini bans `str` indexing; the same `List` carrier
is the natural model for the algorithm's list-of-index-labels). The
specification is carried by `PSeq[int]` via `ToSeq`, and `+` is sequence
concatenation.

The two read-only inputs (`leading`, `tail`) carry fractional permission; the
operation builds and returns a fresh list. No callee is axiomatized: the entire
modelled operation is sequence concatenation, spelled out deeply in the impl.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (no axioms: the modelled operation is the order-preserving prepend of the
# leading run onto a core-result term — pure sequence concatenation, spelled
# out deeply in the impl region. The factors set aside / the core-result term
# are read-only inputs, an R-refinement of the unchanged surrounding algorithm.)
# axioms-end


# pure-start
# (no pure helpers: the specification is stated directly over PSeq[int]
# concatenation via ToSeq.)
# pure-end


def restore_leading(leading: List[int], tail: List[int]) -> List[int]:
    """Restore the leading run in front of a core-result term, preserving the
    leading factors' original left-to-right order: `leading ++ tail`."""
    # pre-conditions-start
    Requires(Acc(list_pred(leading), 1 / 2))
    Requires(Acc(list_pred(tail), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(leading), 1 / 2))
    Ensures(Acc(list_pred(tail), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The result is the leading run, in its original order, followed by `tail`.
    Ensures(ToSeq(Result()) == ToSeq(leading) + ToSeq(tail))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    i = 0
    while i < len(leading):
        # invariants-start
        Invariant(Acc(list_pred(leading), 1 / 2))
        Invariant(Acc(list_pred(tail), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(leading))
        Invariant(ToSeq(result) == ToSeq(leading).take(i))
        # invariants-end
        result.append(leading[i])
        i = i + 1
    j = 0
    while j < len(tail):
        # invariants-start
        Invariant(Acc(list_pred(leading), 1 / 2))
        Invariant(Acc(list_pred(tail), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(tail))
        Invariant(ToSeq(result) == ToSeq(leading) + ToSeq(tail).take(j))
        # invariants-end
        result.append(tail[j])
        j = j + 1
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial audit of nagini bundle sympy__sympy-23824 (restore_leading). Spec postcondition pins the EXACT return value: Ensures(ToSeq(Result()) == ToSeq(leading) + ToSeq(tail)). All 7 attacks are byte-identical in the spec region (same-spec exit 0 for all). Env: swebench-lean venv; SBU_BENCHMARK_DIR=benchmark-verified; SBU_BENCHMARK=swe_bench_verified.

### ATTACKS (cmd: `python -m swebench_unified.adversary weakness nagini sympy__sympy-23824 <path>`; run in batches of 3, JVM+Z3 each):
- atk_1.py (prepatch bug: reversed leading via `front + result` front-insert loop) -> exit 2, does NOT verify. PREPATCH REPRODUCED (matches model_prepatch.py; postcondition unprovable once leading run has >=2 distinct factors).
- atk_2.py (order swap: tail ++ leading) -> exit 2, does NOT verify (wrong value).
- atk_3.py (boundary/off-by-one: first loop bound `len(leading)-1`, drops last leading factor) -> exit 2, does NOT verify.
- atk_4.py (partial-domain: copies tail only, drops leading entirely) -> exit 2, does NOT verify.
- atk_5.py (control-flow-effect: `while True` non-termination, wrong empty return) -> exit 2, NOT JUDGED. Verbose verify (`bash scripts/nagini_verify.sh`) reports `Type error: dead.code @74` -> the wrong return is unreachable, and the front end refuses the program on that ground, so it never reached the verifier and the spec never ruled on it (it counts in neither tally). What this establishes is narrower: the attack shape is unexpressible in nagini's fragment, so this file did not test the spec's method-level MustTerminate, and whether that clause would reject a TRANSLATABLE diverging rival is a separate question this attack does not settle.
- atk_7.py (control-flow-effect: `Assert(False)` then wrong empty return) -> exit 2, does NOT verify (assertion unprovable; no infeasible-path vacuity).
- atk_6.py (ungrounded-oracle echo / behaviorally-correct alt algorithm: `result = leading + tail`) -> exit 0, CANDIDATE (shares spec AND verifies, 13.7s). Per 2026-08-06 echo-attack policy, materialized faithful refined patch (== gold hunk verbatim, per refinement.md A5) and RAN run_resolve on swe_bench_verified: RESOLVED=True, completed=True, attempts=1, non-flaky; FAIL_TO_PASS test_kahane_simplify1 PASS, PASS_TO_PASS {test_kahane_algorithm, test_gamma_matrix_class} PASS. A resolving echo is NOT a weakness.

POSITIVE CONTROL: bundle model.py (model_orig.py) verifies (Verification successful, 13.24s).

A-LEG / MODEL-CORRESPONDENCE AUDIT: refinement.md declares NO axioms and NO A-legs; this is HONEST. model.py has exactly one def (restore_leading), no @ContractOnly, no @Pure helper, and no axiom_check.py exists (G-AX vacuously skip). The gold patch is pure list concatenation `resulting_indices = list(free_pos[0:first_dum_pos] + ri for ri in resulting_indices)`. Every leg A1-A5 is R (list-of-index-labels <-> List[int]; list `+` <-> PSeq `+`) or I (identical concatenation, order-preserving); no kind-3 (unexpressible-changed-op). The single-representative-term modeling is faithful: the gold comprehension applies the same per-term transform uniformly (unchanged map wrapper), so modeling one `ri` captures the entire observable change. mapping.md bindings check out (free_pos[0:first_dum_pos]<->leading, ri<->tail, len(leading)<->first_dum_pos). G-CONF present and passes (100201 inputs, 0 disagreements, real AST-located statement oracle + full-pipeline grounding leg).

VERDICT: SOUND. >=5 distinct wrong impls (prepatch, swap, boundary, partial-domain, control-flow-effect via `Assert(False)`) all correctly REJECTED by the value-pinning postcondition; the only verifying candidate is a behaviorally-correct echo whose materialized faithful patch RESOLVES under the official harness. No verifying wrong-impl's faithful patch fails to resolve => no verify-but-not-correct gap. The spec neither admits an incorrect implementation nor rests on any axiom trust point.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness confirmed for sympy__sympy-23824 nagini bundle. (1) Model verifies under pinned Nagini (Verification successful, 16.45s). (2) The single spec postcondition ToSeq(Result()) == ToSeq(leading) + ToSeq(tail) models order-preserving concatenation leading ++ tail. (3) Gold patch hunk in bundle matches the real worktree's applied diff exactly: `resulting_indices = list( free_pos[0:first_dum_pos] + ri for ri in resulting_indices )`, i.e. plain Python list concatenation applied per term. (4) Differential test of the modeled function vs. the real repo operation over 200,000 random inputs (lengths 0-6, duplicates, negatives, empty runs) yields 0 mismatches — the modeled function agrees with the real callee on every input. (5) Type refinement (index labels -> int) is exact: positions before first_dum_pos are all free/uncontracted, so free_pos[0:first_dum_pos] contains only integer labels (never None), matching List[int]. (6) Live repo run reproduces the witness kahane_simplify(G(rho)*G(sigma)*G(mu)*G(-mu)) -> 4*G(rho)*G(sigma), consistent with the order-preserving spec. The spec is neither too strong nor drifting; no diverging input exists.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function).

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (docstring + signature + pre/post; impl elided via same-spec/spec_view over the nagini backend) encodes exactly one property: order-preserving prepend of the leading run onto the core term — docstring 'Restoring them must PRESERVE their original left-to-right order' / 'leading ++ tail' and postcondition Ensures(ToSeq(Result()) == ToSeq(leading) + ToSeq(tail)). This is ALREADY fully disclosed by the PUBLIC problem_statement: title 'incorrectly reverses order of leading uncontracted gamma matrices', body 'a bug causes such leading terms to be prepended in reverse order', and the reporter's own fix diagnosis 'the insertion loop is just backward' — i.e. the gold edit is precisely to restore the original left-to-right order. hints_text is empty. The spec view therefore adds nothing beyond problem_statement. Repo-specific reconstruction details (free_pos, first_dum_pos, resulting_indices, gamma_matrices.py:697-698, the concrete gold hunk `list(free_pos[0:first_dum_pos] + ri for ri in resulting_indices)`) appear ONLY in refinement.md / mapping.md / meta.json — audit artifacts not part of the consumer spec view — and were confirmed absent from the computed spec view (token scan: free_pos/first_dum_pos/resulting_indices/kahane/gamma_matrices/697/698/insert/reverse all False). same-spec exit 0 confirms the spec region is byte-identical to the frozen bundle. No spec-view line leaks the gold edit beyond the public problem_statement. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
