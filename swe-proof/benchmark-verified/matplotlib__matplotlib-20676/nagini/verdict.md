# P2 adversarial audit — matplotlib__matplotlib-20676

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 4 | `atk1.py`, `atk2.py`, `atk3.py`, `atk4.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk5.py`, `atk6.py`, `atk7.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk1.py` → rejected (same spec, does not verify — good)

```diff
@@ -31,7 +31,6 @@
 """
 from typing import List, Tuple
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 HORIZONTAL = 0
@@ -70,7 +69,6 @@
                             other_coords: Tuple[int, int]) -> List[int]:
     # pre-conditions-start
     Requires(direction == HORIZONTAL or direction == VERTICAL)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -92,16 +90,10 @@
                        y_bound[0], y_bound[1])))
     # post-conditions-end
     # impl-start
-    # Select the two endpoints of THIS orientation's current range as the
-    # reported coordinate values.
+    # WRONG: swap which bound each orientation selects.
     if direction == HORIZONTAL:
-        result = [x_bound[0], x_bound[1]]  # type: List[int]
+        result = [y_bound[0], y_bound[1]]  # type: List[int]
     else:
-        result = [y_bound[0], y_bound[1]]
-    # The selected values equal the orientation's range, which the
-    # position-reporting component then returns unchanged.
-    Assert(ToSeq(result) == selected_bound(
-        direction, x_bound[0], x_bound[1], y_bound[0], y_bound[1]))
-    Assert(reported_positions(ToSeq(result)) == ToSeq(result))
+        result = [x_bound[0], x_bound[1]]
     return result
     # impl-end
```

Attack 2 — `atk2.py` → rejected (same spec, does not verify — good)

```diff
@@ -31,7 +31,6 @@
 """
 from typing import List, Tuple
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 HORIZONTAL = 0
@@ -70,7 +69,6 @@
                             other_coords: Tuple[int, int]) -> List[int]:
     # pre-conditions-start
     Requires(direction == HORIZONTAL or direction == VERTICAL)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -92,16 +90,10 @@
                        y_bound[0], y_bound[1])))
     # post-conditions-end
     # impl-start
-    # Select the two endpoints of THIS orientation's current range as the
-    # reported coordinate values.
+    # WRONG: report the endpoints in reversed order.
     if direction == HORIZONTAL:
-        result = [x_bound[0], x_bound[1]]  # type: List[int]
+        result = [x_bound[1], x_bound[0]]  # type: List[int]
     else:
-        result = [y_bound[0], y_bound[1]]
-    # The selected values equal the orientation's range, which the
-    # position-reporting component then returns unchanged.
-    Assert(ToSeq(result) == selected_bound(
-        direction, x_bound[0], x_bound[1], y_bound[0], y_bound[1]))
-    Assert(reported_positions(ToSeq(result)) == ToSeq(result))
+        result = [y_bound[1], y_bound[0]]
     return result
     # impl-end
```

Attack 3 — `atk3.py` → rejected (same spec, does not verify — good)

```diff
@@ -31,7 +31,6 @@
 """
 from typing import List, Tuple
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 HORIZONTAL = 0
@@ -70,7 +69,6 @@
                             other_coords: Tuple[int, int]) -> List[int]:
     # pre-conditions-start
     Requires(direction == HORIZONTAL or direction == VERTICAL)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -92,16 +90,7 @@
                        y_bound[0], y_bound[1])))
     # post-conditions-end
     # impl-start
-    # Select the two endpoints of THIS orientation's current range as the
-    # reported coordinate values.
-    if direction == HORIZONTAL:
-        result = [x_bound[0], x_bound[1]]  # type: List[int]
-    else:
-        result = [y_bound[0], y_bound[1]]
-    # The selected values equal the orientation's range, which the
-    # position-reporting component then returns unchanged.
-    Assert(ToSeq(result) == selected_bound(
-        direction, x_bound[0], x_bound[1], y_bound[0], y_bound[1]))
-    Assert(reported_positions(ToSeq(result)) == ToSeq(result))
+    # WRONG: no branch on orientation; always pick the horizontal range.
+    result = [x_bound[0], x_bound[1]]  # type: List[int]
     return result
     # impl-end
```

Attack 4 — `atk4.py` → rejected (same spec, does not verify — good)

```diff
@@ -31,7 +31,6 @@
 """
 from typing import List, Tuple
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 HORIZONTAL = 0
@@ -70,7 +69,6 @@
                             other_coords: Tuple[int, int]) -> List[int]:
     # pre-conditions-start
     Requires(direction == HORIZONTAL or direction == VERTICAL)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -92,16 +90,10 @@
                        y_bound[0], y_bound[1])))
     # post-conditions-end
     # impl-start
-    # Select the two endpoints of THIS orientation's current range as the
-    # reported coordinate values.
+    # WRONG: collapse the pair to the lower endpoint twice.
     if direction == HORIZONTAL:
-        result = [x_bound[0], x_bound[1]]  # type: List[int]
+        result = [x_bound[0], x_bound[0]]  # type: List[int]
     else:
-        result = [y_bound[0], y_bound[1]]
-    # The selected values equal the orientation's range, which the
-    # position-reporting component then returns unchanged.
-    Assert(ToSeq(result) == selected_bound(
-        direction, x_bound[0], x_bound[1], y_bound[0], y_bound[1]))
-    Assert(reported_positions(ToSeq(result)) == ToSeq(result))
+        result = [y_bound[0], y_bound[0]]
     return result
     # impl-end
```

Attack 5 — `atk5.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -31,7 +31,6 @@
 """
 from typing import List, Tuple
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 HORIZONTAL = 0
@@ -70,7 +69,6 @@
                             other_coords: Tuple[int, int]) -> List[int]:
     # pre-conditions-start
     Requires(direction == HORIZONTAL or direction == VERTICAL)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -92,14 +90,10 @@
                        y_bound[0], y_bound[1])))
     # post-conditions-end
     # impl-start
-    # Select the two endpoints of THIS orientation's current range as the
-    # reported coordinate values.
-    if direction == HORIZONTAL:
-        result = [x_bound[0], x_bound[1]]  # type: List[int]
-    else:
-        result = [y_bound[0], y_bound[1]]
-    # The selected values equal the orientation's range, which the
-    # position-reporting component then returns unchanged.
+    # Equivalent: read the endpoints out of the deep-model selection oracle.
+    sel = selected_bound(direction, x_bound[0], x_bound[1],
+                         y_bound[0], y_bound[1])  # type: PSeq[int]
+    result = [sel[0], sel[1]]  # type: List[int]
     Assert(ToSeq(result) == selected_bound(
         direction, x_bound[0], x_bound[1], y_bound[0], y_bound[1]))
     Assert(reported_positions(ToSeq(result)) == ToSeq(result))
```

Attack 6 — `atk6.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -31,7 +31,6 @@
 """
 from typing import List, Tuple
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 HORIZONTAL = 0
@@ -70,7 +69,6 @@
                             other_coords: Tuple[int, int]) -> List[int]:
     # pre-conditions-start
     Requires(direction == HORIZONTAL or direction == VERTICAL)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -92,14 +90,14 @@
                        y_bound[0], y_bound[1])))
     # post-conditions-end
     # impl-start
-    # Select the two endpoints of THIS orientation's current range as the
-    # reported coordinate values.
+    # Equivalent refactor: build the list incrementally.
+    result = []  # type: List[int]
     if direction == HORIZONTAL:
-        result = [x_bound[0], x_bound[1]]  # type: List[int]
+        result.append(x_bound[0])
+        result.append(x_bound[1])
     else:
-        result = [y_bound[0], y_bound[1]]
-    # The selected values equal the orientation's range, which the
-    # position-reporting component then returns unchanged.
+        result.append(y_bound[0])
+        result.append(y_bound[1])
     Assert(ToSeq(result) == selected_bound(
         direction, x_bound[0], x_bound[1], y_bound[0], y_bound[1]))
     Assert(reported_positions(ToSeq(result)) == ToSeq(result))
```

Attack 7 — `atk7.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -31,7 +31,6 @@
 """
 from typing import List, Tuple
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 HORIZONTAL = 0
@@ -70,7 +69,6 @@
                             other_coords: Tuple[int, int]) -> List[int]:
     # pre-conditions-start
     Requires(direction == HORIZONTAL or direction == VERTICAL)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -92,16 +90,13 @@
                        y_bound[0], y_bound[1])))
     # post-conditions-end
     # impl-start
-    # Select the two endpoints of THIS orientation's current range as the
-    # reported coordinate values.
+    # Equivalent: construct reversed, then swap back to lower-then-upper.
     if direction == HORIZONTAL:
-        result = [x_bound[0], x_bound[1]]  # type: List[int]
+        tmp = [x_bound[1], x_bound[0]]  # type: List[int]
     else:
-        result = [y_bound[0], y_bound[1]]
-    # The selected values equal the orientation's range, which the
-    # position-reporting component then returns unchanged.
+        tmp = [y_bound[1], y_bound[0]]
+    result = [tmp[1], tmp[0]]  # type: List[int]
     Assert(ToSeq(result) == selected_bound(
         direction, x_bound[0], x_bound[1], y_bound[0], y_bound[1]))
-    Assert(reported_positions(ToSeq(result)) == ToSeq(result))
     return result
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for matplotlib__matplotlib-20676.

Behavioural contract (the desired observable, stated abstractly):

  A range selector carries a binary orientation. On construction it reports a
  pair of coordinate values, in order. The contract: that reported pair equals
  the two endpoints, in order, of the orientation's CURRENT coordinate range —
  the horizontal range for a horizontal selector, the vertical range for a
  vertical selector. Because the reported values are exactly the endpoints of
  the range that already exists, they lie inside it and constructing the
  selector leaves that range unchanged.

  In other words: result[0] is the lower endpoint and result[1] the upper
  endpoint of the orientation's current range, grounded in the range supplied
  for that orientation (never in any unrelated coordinate pair).

A coordinate value is a `float` in the real implementation; the modelled
behaviour is a pure selection / pass-through of coordinate VALUES (no arithmetic
on their magnitudes), so each coordinate is modelled as an `int` (the equalities
the contract pins are preserved under an injective encoding; see refinement.md /
mapping.md §2). Orientation is the two-valued discriminant `0` (horizontal) /
`1` (vertical).

The position-reporting component returns the coordinate values it was given,
unchanged. That UNCHANGED component is modelled as the identity
`reported_positions` and validated == the real component by axiom_check.py
(G-AX), not consumed as a load-bearing axiom. Which two coordinate values are
selected is modelled directly.

Region markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Tuple
from nagini_contracts.contracts import *


HORIZONTAL = 0
VERTICAL = 1


# axioms-start
@Pure
@ContractOnly
def reported_positions(positions: PSeq[int]) -> PSeq[int]:
    """The position-reporting component returns the coordinate values it was
    constructed with, unchanged (one reported value per supplied coordinate).
    Provenance + executable soundness check: mapping.md §3.1 / axiom_check.py.
    Used inside an Ensures, hence @Pure."""
    Ensures(Result() == positions)
# axioms-end


# pure-start
@Pure
def selected_bound(direction: int, x_lo: int, x_hi: int,
                   y_lo: int, y_hi: int) -> PSeq[int]:
    """The two endpoints, in order, of the range for this orientation: the
    horizontal range for a horizontal selector, the vertical range for a
    vertical selector."""
    Requires(direction == HORIZONTAL or direction == VERTICAL)
    if direction == HORIZONTAL:
        return PSeq(x_lo, x_hi)
    return PSeq(y_lo, y_hi)
# pure-end


def selector_initial_coords(direction: int,
                            x_bound: Tuple[int, int],
                            y_bound: Tuple[int, int],
                            other_coords: Tuple[int, int]) -> List[int]:
    # pre-conditions-start
    Requires(direction == HORIZONTAL or direction == VERTICAL)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    # Exactly two reported values, lower then upper.
    Ensures(len(Result()) == 2)
    # The reported pair is the two endpoints of THIS orientation's current
    # range, in order — the horizontal range for a horizontal selector, the
    # vertical range for a vertical selector. Grounded in the range supplied
    # for that orientation.
    Ensures(Implies(direction == HORIZONTAL,
                    Result()[0] == x_bound[0] and Result()[1] == x_bound[1]))
    Ensures(Implies(direction == VERTICAL,
                    Result()[0] == y_bound[0] and Result()[1] == y_bound[1]))
    # Equivalent fold form: the reported pair equals the position-reporting
    # component's report of the orientation's range endpoints (the unchanged
    # component applied to the selected range).
    Ensures(ToSeq(Result()) == reported_positions(
        selected_bound(direction, x_bound[0], x_bound[1],
                       y_bound[0], y_bound[1])))
    # post-conditions-end
    # impl-start
    # Select the two endpoints of THIS orientation's current range as the
    # reported coordinate values.
    if direction == HORIZONTAL:
        result = [x_bound[0], x_bound[1]]  # type: List[int]
    else:
        result = [y_bound[0], y_bound[1]]
    # The selected values equal the orientation's range, which the
    # position-reporting component then returns unchanged.
    Assert(ToSeq(result) == selected_bound(
        direction, x_bound[0], x_bound[1], y_bound[0], y_bound[1]))
    Assert(reported_positions(ToSeq(result)) == ToSeq(result))
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. Spec fully pins the output for both orientations; no verifying wrong-impl found; every verifying candidate's faithful patch RESOLVES.

 Env: SBU_BENCHMARK_DIR=benchmark-verified, FSx HOME. Gold patch is a placeholder in meta.patch_diff; real gold read from data/swe_bench_verified/test.jsonl.

### Calibration
- positive_control.py (bundle model.py) -> nagini_verify.sh EXIT 0, 'Verification successful' 10.9s.
- atk_prepatch.py (model_prepatch.py, other_coords/self.extents source) -> nagini_verify.sh EXIT 1, 'Postcondition ... Implies(direction==HORIZONTAL, Result()[0]==x_bound[0] and Result()[1]==x_bound[1]) might not hold' => PREPATCH BUG REPRODUCED (spec senses the change, G-DIFF).
- GOLD patch via harness.run_resolve => resolved=True completed=True (harness positive control).
- axiom_check.py (G-AX A-reference) => EXIT 0, ToolLineHandles identity sound on 8 boundary + 2000 fuzz x2 dirs, end-to-end SpanSelector leaves bounds unchanged, prepatch (0,0) DOES expand bound.

SPEC ANALYSIS: postconditions fully constrain the result — len==2; Implies(HORIZONTAL, Result[0]==x_bound[0] and Result[1]==x_bound[1]); Implies(VERTICAL, Result[0]==y_bound[0] and Result[1]==y_bound[1]); fold form ToSeq(Result)==reported_positions(selected_bound(...)). Precondition restricts direction to exactly {0,1} — no free domain. Any verifying impl must return exactly the orientation's bound endpoints in order = gold behavior.

ATTACKS (all same-spec EXIT 0; command form: `python -m swebench_unified.adversary weakness nagini matplotlib__matplotlib-20676 <atk>.py`; run in parallel batches of 3):
- atk1.py WRONG-DIRECTION (horizontal->y_bound, vertical->x_bound): weakness EXIT 2 NOT-A-COUNTEREXAMPLE (does not verify). Spec REJECTS. GOOD.
- atk2.py SWAPPED-ORDER (endpoints reversed): weakness EXIT 2, does not verify. REJECTED. GOOD.
- atk3.py CONTROL-FLOW-EFFECT (no branch, always x_bound): weakness EXIT 2, does not verify. REJECTED. GOOD.
- atk4.py DEGENERATE/PARTIAL (lower endpoint twice): weakness EXIT 2, does not verify. REJECTED. GOOD.
- atk5.py UNGROUNDED-ORACLE ECHO (result read from selected_bound oracle): weakness EXIT 0 CANDIDATE (verifies 13.9s). Faithful patch = byte-identical to gold. run_resolve => resolved=True completed=True. RESOLVES.
- atk6.py EQUIVALENT REFACTOR (build list via append of bound[0],bound[1]): weakness EXIT 0 CANDIDATE (verifies 13.7s). Faithful patch (append form). run_resolve => resolved=True completed=True. RESOLVES.
- atk7.py EQUIVALENT via reversed-then-reversed (construct [hi,lo] then swap): weakness EXIT 0 CANDIDATE (verifies 13.7s). Faithful patch (tmp swap form). run_resolve => resolved=True completed=True. RESOLVES.

MATERIALIZED FAITHFUL PATCHES: 3 candidate patches (patch_atk5/6/7.diff) run through official harness (swebench_unified.harness.run_resolve, image swebench/sweb.eval.x86_64.matplotlib_1776_matplotlib-20676) => ALL resolved=True completed=True. First patch attempt failed to apply (mis-anchored context: the ToolLineHandles(positions) call must be an ADDED line since prepatch used self.extents); rebuilt to mirror gold hunk structure exactly, then all resolved. No verifying impl produced a non-resolving patch => NO spec weakness (verify=>correct holds).

REFINEMENT.MD LEG AUDIT: A1=R (direction str->0/1, check_in_list); A2=R (float->int endpoint-wise, get_xbound/get_ybound); A3=I(control-flow)+R(carrier) — the CHANGED op (which bound is selected) modeled DIRECTLY via structural postconditions + selected_bound, not behind an axiom; A4=A-reference (reported_positions == identity of unchanged ToolLineHandles.positions, validated by G-AX axiom_check.py PASS). Only @ContractOnly is reported_positions (A-reference). NO kind-3 (unexpressible-changed-op) legs. A-reference correspondence to real ToolLineHandles callee confirmed by axiom_check EXIT 0. Refinement fidelity holds.

CONCLUSION: 7 same-spec attacks executed (4 wrong-and-rejected across partial-domain/boundary/control-flow/degenerate; 3 equivalent verifying candidates all resolve). All required resolve runs completed. Spec admits only gold-equivalent implementations. VERDICT: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 4 | `atk1.py`, `atk2.py`, `atk3.py`, `atk4.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk5.py`, `atk6.py`, `atk7.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk5.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk6.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk7.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for matplotlib__matplotlib-20676.

Behavioural contract (the desired observable, stated abstractly):

  A range selector carries a binary orientation. On construction it reports a
  pair of coordinate values, in order. The contract: that reported pair equals
  the two endpoints, in order, of the orientation's CURRENT coordinate range —
  the horizontal range for a horizontal selector, the vertical range for a
  vertical selector. Because the reported values are exactly the endpoints of
  the range that already exists, they lie inside it and constructing the
  selector leaves that range unchanged.

  In other words: result[0] is the lower endpoint and result[1] the upper
  endpoint of the orientation's current range, grounded in the range supplied
  for that orientation (never in any unrelated coordinate pair).

A coordinate value is a `float` in the real implementation; the modelled
behaviour is a pure selection / pass-through of coordinate VALUES (no arithmetic
on their magnitudes), so each coordinate is modelled as an `int` (the equalities
the contract pins are preserved under an injective encoding; see refinement.md /
mapping.md §2). Orientation is the two-valued discriminant `0` (horizontal) /
`1` (vertical).

The position-reporting component returns the coordinate values it was given,
unchanged. That UNCHANGED component is modelled as the identity
`reported_positions` and validated == the real component by axiom_check.py
(G-AX), not consumed as a load-bearing axiom. Which two coordinate values are
selected is modelled directly.

Region markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Tuple
from nagini_contracts.contracts import *


HORIZONTAL = 0
VERTICAL = 1


# axioms-start
@Pure
@ContractOnly
def reported_positions(positions: PSeq[int]) -> PSeq[int]:
    """The position-reporting component returns the coordinate values it was
    constructed with, unchanged (one reported value per supplied coordinate).
    Provenance + executable soundness check: mapping.md §3.1 / axiom_check.py.
    Used inside an Ensures, hence @Pure."""
    Ensures(Result() == positions)
# axioms-end


# pure-start
@Pure
def selected_bound(direction: int, x_lo: int, x_hi: int,
                   y_lo: int, y_hi: int) -> PSeq[int]:
    """The two endpoints, in order, of the range for this orientation: the
    horizontal range for a horizontal selector, the vertical range for a
    vertical selector."""
    Requires(direction == HORIZONTAL or direction == VERTICAL)
    if direction == HORIZONTAL:
        return PSeq(x_lo, x_hi)
    return PSeq(y_lo, y_hi)
# pure-end


def selector_initial_coords(direction: int,
                            x_bound: Tuple[int, int],
                            y_bound: Tuple[int, int],
                            other_coords: Tuple[int, int]) -> List[int]:
    # pre-conditions-start
    Requires(direction == HORIZONTAL or direction == VERTICAL)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    # Exactly two reported values, lower then upper.
    Ensures(len(Result()) == 2)
    # The reported pair is the two endpoints of THIS orientation's current
    # range, in order — the horizontal range for a horizontal selector, the
    # vertical range for a vertical selector. Grounded in the range supplied
    # for that orientation.
    Ensures(Implies(direction == HORIZONTAL,
                    Result()[0] == x_bound[0] and Result()[1] == x_bound[1]))
    Ensures(Implies(direction == VERTICAL,
                    Result()[0] == y_bound[0] and Result()[1] == y_bound[1]))
    # Equivalent fold form: the reported pair equals the position-reporting
    # component's report of the orientation's range endpoints (the unchanged
    # component applied to the selected range).
    Ensures(ToSeq(Result()) == reported_positions(
        selected_bound(direction, x_bound[0], x_bound[1],
                       y_bound[0], y_bound[1])))
    # post-conditions-end
    # impl-start
    # Select the two endpoints of THIS orientation's current range as the
    # reported coordinate values.
    if direction == HORIZONTAL:
        result = [x_bound[0], x_bound[1]]  # type: List[int]
    else:
        result = [y_bound[0], y_bound[1]]
    # The selected values equal the orientation's range, which the
    # position-reporting component then returns unchanged.
    Assert(ToSeq(result) == selected_bound(
        direction, x_bound[0], x_bound[1], y_bound[0], y_bound[1]))
    Assert(reported_positions(ToSeq(result)) == ToSeq(result))
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. Spec fully pins the output for both orientations; no verifying wrong-impl found; every verifying candidate's faithful patch RESOLVES.

 Env: SBU_BENCHMARK_DIR=benchmark-verified, FSx HOME. Gold patch is a placeholder in meta.patch_diff; real gold read from data/swe_bench_verified/test.jsonl.

### Calibration
- positive_control.py (bundle model.py) -> nagini_verify.sh EXIT 0, 'Verification successful' 10.9s.
- atk_prepatch.py (model_prepatch.py, other_coords/self.extents source) -> nagini_verify.sh EXIT 1, 'Postcondition ... Implies(direction==HORIZONTAL, Result()[0]==x_bound[0] and Result()[1]==x_bound[1]) might not hold' => PREPATCH BUG REPRODUCED (spec senses the change, G-DIFF).
- GOLD patch via harness.run_resolve => resolved=True completed=True (harness positive control).
- axiom_check.py (G-AX A-reference) => EXIT 0, ToolLineHandles identity sound on 8 boundary + 2000 fuzz x2 dirs, end-to-end SpanSelector leaves bounds unchanged, prepatch (0,0) DOES expand bound.

SPEC ANALYSIS: postconditions fully constrain the result — len==2; Implies(HORIZONTAL, Result[0]==x_bound[0] and Result[1]==x_bound[1]); Implies(VERTICAL, Result[0]==y_bound[0] and Result[1]==y_bound[1]); fold form ToSeq(Result)==reported_positions(selected_bound(...)). Precondition restricts direction to exactly {0,1} — no free domain. Any verifying impl must return exactly the orientation's bound endpoints in order = gold behavior.

ATTACKS (all same-spec EXIT 0; command form: `python -m swebench_unified.adversary weakness nagini matplotlib__matplotlib-20676 <atk>.py`; run in parallel batches of 3):
- atk1.py WRONG-DIRECTION (horizontal->y_bound, vertical->x_bound): weakness EXIT 2 NOT-A-COUNTEREXAMPLE (does not verify). Spec REJECTS. GOOD.
- atk2.py SWAPPED-ORDER (endpoints reversed): weakness EXIT 2, does not verify. REJECTED. GOOD.
- atk3.py CONTROL-FLOW-EFFECT (no branch, always x_bound): weakness EXIT 2, does not verify. REJECTED. GOOD.
- atk4.py DEGENERATE/PARTIAL (lower endpoint twice): weakness EXIT 2, does not verify. REJECTED. GOOD.
- atk5.py UNGROUNDED-ORACLE ECHO (result read from selected_bound oracle): weakness EXIT 0 CANDIDATE (verifies 13.9s). Faithful patch = byte-identical to gold. run_resolve => resolved=True completed=True. RESOLVES.
- atk6.py EQUIVALENT REFACTOR (build list via append of bound[0],bound[1]): weakness EXIT 0 CANDIDATE (verifies 13.7s). Faithful patch (append form). run_resolve => resolved=True completed=True. RESOLVES.
- atk7.py EQUIVALENT via reversed-then-reversed (construct [hi,lo] then swap): weakness EXIT 0 CANDIDATE (verifies 13.7s). Faithful patch (tmp swap form). run_resolve => resolved=True completed=True. RESOLVES.

MATERIALIZED FAITHFUL PATCHES: 3 candidate patches (patch_atk5/6/7.diff) run through official harness (swebench_unified.harness.run_resolve, image swebench/sweb.eval.x86_64.matplotlib_1776_matplotlib-20676) => ALL resolved=True completed=True. First patch attempt failed to apply (mis-anchored context: the ToolLineHandles(positions) call must be an ADDED line since prepatch used self.extents); rebuilt to mirror gold hunk structure exactly, then all resolved. No verifying impl produced a non-resolving patch => NO spec weakness (verify=>correct holds).

REFINEMENT.MD LEG AUDIT: A1=R (direction str->0/1, check_in_list); A2=R (float->int endpoint-wise, get_xbound/get_ybound); A3=I(control-flow)+R(carrier) — the CHANGED op (which bound is selected) modeled DIRECTLY via structural postconditions + selected_bound, not behind an axiom; A4=A-reference (reported_positions == identity of unchanged ToolLineHandles.positions, validated by G-AX axiom_check.py PASS). Only @ContractOnly is reported_positions (A-reference). NO kind-3 (unexpressible-changed-op) legs. A-reference correspondence to real ToolLineHandles callee confirmed by axiom_check EXIT 0. Refinement fidelity holds.

CONCLUSION: 7 same-spec attacks executed (4 wrong-and-rejected across partial-domain/boundary/control-flow/degenerate; 3 equivalent verifying candidates all resolve). All required resolve runs completed. Spec admits only gold-equivalent implementations. VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack found no divergence. The spec pins: horizontal → Result()==[x_bound[0],x_bound[1]]; vertical → Result()==[y_bound[0],y_bound[1]]; plus the fold form ToSeq(Result())==reported_positions(selected_bound(...)) where reported_positions is the identity. The real repo at base_commit (lib/matplotlib/widgets.py:2381 _setup_edge_handles) does exactly this: 'if self.direction=="horizontal": positions=self.ax.get_xbound() else: positions=self.ax.get_ybound()' fed to ToolLineHandles(ax, positions, direction). ToolLineHandles.positions (widgets.py:2675) reads back get_xdata()[0]/get_ydata()[0] which equal the supplied p (axvline/axhline create Line2D([p,p],...)), i.e. the identity. Empirically verified against real matplotlib (Agg): (1) ToolLineHandles(ax,P,dir).positions==list(P) for P in {(10,20),(0,0),(-5.5,3.25),(20,10),(1e6,1e-6)} both directions; (2) real SpanSelector construction yields _edge_handles.positions==list(orientation bound) and leaves get_xbound()/get_ybound() unchanged, both directions. Model verifies (nagini exit 0, 12.8s) and shares exact spec (same-spec exit 0). float→int refinement is faithful: behavior is pure value selection/pass-through with no arithmetic, so injective encoding preserves the pinned equalities. No input found where the modeled function disagrees with the real callee. The spec is not too strong.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery).

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (model.py spec/pure/axiom regions + docstring) does NOT leak the gold edit beyond the public problem_statement. Verified: (1) mechanical G-LEAK screen passes (leakage.screen -> passed=True, no hard failures); no relaxed_leakage flag, so no semantic-deferral applies. (2) The gold edit swaps `self.extents` for `self.ax.get_xbound()/get_ybound()` (by direction) fed to `ToolLineHandles` inside `SpanSelector._setup_edge_handle` (widgets.py). None of those patched repo symbols appear in the spec view: model uses neutral names `selector_initial_coords`, `reported_positions`, `selected_bound`, `x_bound`, `y_bound`, and deliberately `other_coords` (the extents abstraction is neutrally named, not `extents`/`(0,0)`), so the diagnosis is not telegraphed. No diff markers, no patched file path, no narration terms (bug/fix/incorrectly/regression). (3) The postconditions encode the CORRECT observable — reported pair == the orientation's current range endpoints, so construction leaves the range unchanged. That is exactly what the public problem_statement already states (xlimits should remain at (10,20) rather than being forced to include 0), and a spec is required to state correct behavior. Horizontal/vertical generalization comes from the public SpanSelector direction API, not a leaked edit detail. Nothing in the spec view reveals the code location or the extents->get_xbound/get_ybound swap beyond the public statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, which ships in this bundle, so a reader can start there.
