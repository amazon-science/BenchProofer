# P2 adversarial audit — mwaskom__seaborn-3069

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_8.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -42,7 +42,6 @@
 """
 from typing import Tuple
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -78,7 +77,6 @@
     # specification, identical before and after it, so it sits outside the
     # modeled slice (mapping.md §2).
     Requires(Implies(has_explicit, user_lo != user_hi))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # A categorical axis WITHOUT an explicit caller range gets the categorical
@@ -130,18 +128,8 @@
     lo = user_lo
     hi = user_hi
     if has_explicit:
-        # Caller pinned the range explicitly: use it verbatim. The categorical
-        # special-casing below is skipped.
         lo = user_lo
         hi = user_hi
-    elif is_categorical:
-        n = slot_count()
-        lo = -0.5
-        hi = n - 0.5
-        if is_vertical:
-            tmp = lo
-            lo = hi
-            hi = tmp
     return (lo, hi)
     # impl-end
 
@@ -149,7 +137,6 @@
 def finalize_axis_grid(is_categorical: bool, pre_visible: bool) -> bool:
     # pre-conditions-start
     # No mutable reference inputs; both parameters are read-only booleans.
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     # A categorical axis has its grid turned off, whatever visibility it had
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -42,7 +42,6 @@
 """
 from typing import Tuple
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -78,7 +77,6 @@
     # specification, identical before and after it, so it sits outside the
     # modeled slice (mapping.md §2).
     Requires(Implies(has_explicit, user_lo != user_hi))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # A categorical axis WITHOUT an explicit caller range gets the categorical
@@ -130,14 +128,12 @@
     lo = user_lo
     hi = user_hi
     if has_explicit:
-        # Caller pinned the range explicitly: use it verbatim. The categorical
-        # special-casing below is skipped.
         lo = user_lo
         hi = user_hi
     elif is_categorical:
         n = slot_count()
         lo = -0.5
-        hi = n - 0.5
+        hi = n + 0.5
         if is_vertical:
             tmp = lo
             lo = hi
@@ -149,7 +145,6 @@
 def finalize_axis_grid(is_categorical: bool, pre_visible: bool) -> bool:
     # pre-conditions-start
     # No mutable reference inputs; both parameters are read-only booleans.
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     # A categorical axis has its grid turned off, whatever visibility it had
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -42,7 +42,6 @@
 """
 from typing import Tuple
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -78,7 +77,6 @@
     # specification, identical before and after it, so it sits outside the
     # modeled slice (mapping.md §2).
     Requires(Implies(has_explicit, user_lo != user_hi))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # A categorical axis WITHOUT an explicit caller range gets the categorical
@@ -130,18 +128,12 @@
     lo = user_lo
     hi = user_hi
     if has_explicit:
-        # Caller pinned the range explicitly: use it verbatim. The categorical
-        # special-casing below is skipped.
         lo = user_lo
         hi = user_hi
     elif is_categorical:
         n = slot_count()
         lo = -0.5
         hi = n - 0.5
-        if is_vertical:
-            tmp = lo
-            lo = hi
-            hi = tmp
     return (lo, hi)
     # impl-end
 
@@ -149,7 +141,6 @@
 def finalize_axis_grid(is_categorical: bool, pre_visible: bool) -> bool:
     # pre-conditions-start
     # No mutable reference inputs; both parameters are read-only booleans.
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     # A categorical axis has its grid turned off, whatever visibility it had
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -42,7 +42,6 @@
 """
 from typing import Tuple
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -78,7 +77,6 @@
     # specification, identical before and after it, so it sits outside the
     # modeled slice (mapping.md §2).
     Requires(Implies(has_explicit, user_lo != user_hi))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # A categorical axis WITHOUT an explicit caller range gets the categorical
@@ -130,11 +128,9 @@
     lo = user_lo
     hi = user_hi
     if has_explicit:
-        # Caller pinned the range explicitly: use it verbatim. The categorical
-        # special-casing below is skipped.
         lo = user_lo
         hi = user_hi
-    elif is_categorical:
+    else:
         n = slot_count()
         lo = -0.5
         hi = n - 0.5
@@ -149,7 +145,6 @@
 def finalize_axis_grid(is_categorical: bool, pre_visible: bool) -> bool:
     # pre-conditions-start
     # No mutable reference inputs; both parameters are read-only booleans.
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     # A categorical axis has its grid turned off, whatever visibility it had
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -42,7 +42,6 @@
 """
 from typing import Tuple
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -78,7 +77,6 @@
     # specification, identical before and after it, so it sits outside the
     # modeled slice (mapping.md §2).
     Requires(Implies(has_explicit, user_lo != user_hi))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # A categorical axis WITHOUT an explicit caller range gets the categorical
@@ -130,8 +128,6 @@
     lo = user_lo
     hi = user_hi
     if has_explicit:
-        # Caller pinned the range explicitly: use it verbatim. The categorical
-        # special-casing below is skipped.
         lo = user_lo
         hi = user_hi
     elif is_categorical:
@@ -149,7 +145,6 @@
 def finalize_axis_grid(is_categorical: bool, pre_visible: bool) -> bool:
     # pre-conditions-start
     # No mutable reference inputs; both parameters are read-only booleans.
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     # A categorical axis has its grid turned off, whatever visibility it had
@@ -163,8 +158,6 @@
     Ensures(Implies(not is_categorical, Result() == pre_visible))
     # post-conditions-end
     # impl-start
-    grid_visible = pre_visible
-    if is_categorical:
-        grid_visible = False
+    grid_visible = False
     return grid_visible
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -42,7 +42,6 @@
 """
 from typing import Tuple
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -78,7 +77,6 @@
     # specification, identical before and after it, so it sits outside the
     # modeled slice (mapping.md §2).
     Requires(Implies(has_explicit, user_lo != user_hi))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # A categorical axis WITHOUT an explicit caller range gets the categorical
@@ -130,8 +128,6 @@
     lo = user_lo
     hi = user_hi
     if has_explicit:
-        # Caller pinned the range explicitly: use it verbatim. The categorical
-        # special-casing below is skipped.
         lo = user_lo
         hi = user_hi
     elif is_categorical:
@@ -149,7 +145,6 @@
 def finalize_axis_grid(is_categorical: bool, pre_visible: bool) -> bool:
     # pre-conditions-start
     # No mutable reference inputs; both parameters are read-only booleans.
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     # A categorical axis has its grid turned off, whatever visibility it had
@@ -165,6 +160,6 @@
     # impl-start
     grid_visible = pre_visible
     if is_categorical:
-        grid_visible = False
+        grid_visible = True
     return grid_visible
     # impl-end
```

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -42,7 +42,6 @@
 """
 from typing import Tuple
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -78,7 +77,6 @@
     # specification, identical before and after it, so it sits outside the
     # modeled slice (mapping.md §2).
     Requires(Implies(has_explicit, user_lo != user_hi))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # A categorical axis WITHOUT an explicit caller range gets the categorical
@@ -127,29 +125,22 @@
                     Result()[1] == user_hi))
     # post-conditions-end
     # impl-start
-    lo = user_lo
-    hi = user_hi
     if has_explicit:
-        # Caller pinned the range explicitly: use it verbatim. The categorical
-        # special-casing below is skipped.
-        lo = user_lo
-        hi = user_hi
-    elif is_categorical:
-        n = slot_count()
-        lo = -0.5
-        hi = n - 0.5
-        if is_vertical:
-            tmp = lo
-            lo = hi
-            hi = tmp
-    return (lo, hi)
+        return (user_lo, user_hi)
+    if not is_categorical:
+        return (user_lo, user_hi)
+    n = slot_count()
+    low = -0.5
+    high = slot_count() - 0.5
+    if is_vertical:
+        return (high, low)
+    return (low, high)
     # impl-end
 
 
 def finalize_axis_grid(is_categorical: bool, pre_visible: bool) -> bool:
     # pre-conditions-start
     # No mutable reference inputs; both parameters are read-only booleans.
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     # A categorical axis has its grid turned off, whatever visibility it had
@@ -163,8 +154,7 @@
     Ensures(Implies(not is_categorical, Result() == pre_visible))
     # post-conditions-end
     # impl-start
-    grid_visible = pre_visible
     if is_categorical:
-        grid_visible = False
-    return grid_visible
+        return False
+    return pre_visible
     # impl-end
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -42,7 +42,6 @@
 """
 from typing import Tuple
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -78,7 +77,6 @@
     # specification, identical before and after it, so it sits outside the
     # modeled slice (mapping.md §2).
     Requires(Implies(has_explicit, user_lo != user_hi))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # A categorical axis WITHOUT an explicit caller range gets the categorical
@@ -130,8 +128,6 @@
     lo = user_lo
     hi = user_hi
     if has_explicit:
-        # Caller pinned the range explicitly: use it verbatim. The categorical
-        # special-casing below is skipped.
         lo = user_lo
         hi = user_hi
     elif is_categorical:
@@ -139,9 +135,8 @@
         lo = -0.5
         hi = n - 0.5
         if is_vertical:
-            tmp = lo
-            lo = hi
-            hi = tmp
+            lo = -0.5
+            hi = n - 0.5
     return (lo, hi)
     # impl-end
 
@@ -149,7 +144,6 @@
 def finalize_axis_grid(is_categorical: bool, pre_visible: bool) -> bool:
     # pre-conditions-start
     # No mutable reference inputs; both parameters are read-only booleans.
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     # A categorical axis has its grid turned off, whatever visibility it had
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for mwaskom__seaborn-3069.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a figure is finalized, each coordinate axis carries a scale that is
  either categorical (a discrete, unordered scale whose positions are the
  integer slots 0, 1, ..., n-1 of its n categories) or ordinary (continuous).
  An axis whose scale is categorical must be drawn like the established
  categorical axes:

    (1) the visible data range is pinned to exactly half a slot beyond the
        first and last category position, i.e. the closed interval whose lower
        edge sits half a slot below position 0 and whose upper edge sits half a
        slot above the last position n-1 (so for n categories the span is from
        -0.5 to n-0.5), rather than the ordinary automatic-margin range;

    (2) when the axis is the vertical one, that range is reversed (top edge
        first), so the first category appears at the top;

    (3) the grid lines are turned off for such an axis, whatever visibility
        they had before finalization.

  The range tweaks (1)-(2) apply ONLY when the caller has not pinned an
  explicit range for that axis: if the caller supplied an explicit (lo, hi)
  range, that range is used verbatim and the categorical range/inversion is
  NOT applied. The grid tweak (3) applies to every categorical axis,
  explicit range or not. An ordinary (non-categorical) axis is left entirely
  alone by the finalizer: it keeps the ordinary automatic-margin range AND
  whatever grid visibility it already had going into finalization.

The axis range is a pair of interpreted real numbers (verified with
`--float-encoding=real`) because the behaviour at stake — edges sitting exactly
half a slot beyond the extreme category positions, and that pair reversed on the
vertical axis — is a real-valued relation the tests probe to floating tolerance.
The half-slot offset enters as the literal 0.5; the number of category slots `n`
is supplied by the unchanged tick-counting routine the finalizer queries, which
is axiomatized with the weakest sufficient contract (it returns the count of
category positions, at least one) and validated against the real routine
out-of-band by axiom_check.py (G-AX).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Tuple
from nagini_contracts.contracts import *


# axioms-start
@Pure
@ContractOnly
def slot_count() -> int:
    """The number of category slots on a categorical axis: the count of major
    tick positions the unchanged tick-querying routine reports for the axis.
    A categorical axis always has at least one category, so the count is
    positive. The weakest contract the proof needs (a positive count).
    Provenance + executable soundness check: mapping.md / axiom_check.py.
    """
    Ensures(Result() >= 1)
# axioms-end


# pure-start
# (no pure helpers — the half-slot edges are pinned by their linear defining
# equations in the postcondition.)
# pure-end


def finalize_axis_range(is_categorical: bool, has_explicit: bool, is_vertical: bool,
                        user_lo: float, user_hi: float) -> Tuple[float, float]:
    # pre-conditions-start
    # No mutable reference inputs; all parameters are read-only scalars.
    # The caller-supplied edges are genuine numbers (reflexivity excludes NaN).
    Requires(user_lo == user_lo and user_hi == user_hi)
    # An explicit caller range is modeled only when it is non-singular
    # (lo != hi). A singular pair is reshaped by the unchanged, pre-existing
    # range-sanitization machinery of the underlying axis object before it
    # lands as the visible range — behaviour orthogonal to the change under
    # specification, identical before and after it, so it sits outside the
    # modeled slice (mapping.md §2).
    Requires(Implies(has_explicit, user_lo != user_hi))
    # pre-conditions-end
    # post-conditions-start
    # A categorical axis WITHOUT an explicit caller range gets the categorical
    # range: edges exactly half a slot beyond the extreme category positions.
    # n = slot_count() >= 1; positions run 0 .. n-1; the lower edge sits half a
    # slot below position 0 (i.e. -0.5) and the upper edge half a slot above
    # position n-1 (i.e. n-1 + 0.5 == n - 0.5). On the horizontal axis the pair
    # is (low, high); on the vertical axis it is reversed (high first).
    #
    # Pin the two edges by their linear defining equations grounded in the slot
    # count, then pin orientation, so the result must be PRODUCED by the
    # categorical branch, not merely equal to a constant.
    Ensures(Implies(is_categorical and not has_explicit and not is_vertical,
                    Result()[0] + 0.5 == 0.0))
    Ensures(Implies(is_categorical and not has_explicit and not is_vertical,
                    Result()[1] + 0.5 == slot_count()))
    # Horizontal categorical range is increasing: low edge below high edge.
    Ensures(Implies(is_categorical and not has_explicit and not is_vertical,
                    Result()[0] < Result()[1]))
    # Vertical categorical range is the same pair reversed: high edge first,
    # so the range is decreasing (inverted axis, first category at the top).
    Ensures(Implies(is_categorical and not has_explicit and is_vertical,
                    Result()[1] + 0.5 == 0.0))
    Ensures(Implies(is_categorical and not has_explicit and is_vertical,
                    Result()[0] + 0.5 == slot_count()))
    Ensures(Implies(is_categorical and not has_explicit and is_vertical,
                    Result()[0] > Result()[1]))
    # The two orientations are exact reflections of one another.
    # When an explicit caller range is present it is used verbatim, REGARDLESS
    # of whether the axis is categorical — the categorical range/inversion is
    # NOT applied. This is what makes the categorical tweak conditional on the
    # absence of a caller-pinned range.
    Ensures(Implies(has_explicit, Result()[0] == user_lo))
    Ensures(Implies(has_explicit, Result()[1] == user_hi))
    # An ORDINARY (non-categorical) axis without an explicit caller range is
    # left entirely alone: the finalizer never touches its range, so the
    # pre-existing automatic-margin range (carried in as user_lo/user_hi) is
    # returned unchanged. This clause closes the non-categorical sub-domain:
    # an implementation that applies the categorical range to EVERY
    # non-explicit axis (dropping the is_categorical gate) would clobber
    # ordinary axes (e.g. log-scaled ones) and break passing tests, so the
    # spec must reject it.
    Ensures(Implies(not is_categorical and not has_explicit,
                    Result()[0] == user_lo))
    Ensures(Implies(not is_categorical and not has_explicit,
                    Result()[1] == user_hi))
    # post-conditions-end
    # impl-start
    lo = user_lo
    hi = user_hi
    if has_explicit:
        # Caller pinned the range explicitly: use it verbatim. The categorical
        # special-casing below is skipped.
        lo = user_lo
        hi = user_hi
    elif is_categorical:
        n = slot_count()
        lo = -0.5
        hi = n - 0.5
        if is_vertical:
            tmp = lo
            lo = hi
            hi = tmp
    return (lo, hi)
    # impl-end


def finalize_axis_grid(is_categorical: bool, pre_visible: bool) -> bool:
    # pre-conditions-start
    # No mutable reference inputs; both parameters are read-only booleans.
    # pre-conditions-end
    # post-conditions-start
    # A categorical axis has its grid turned off, whatever visibility it had
    # going into finalization. An ordinary (non-categorical) axis is left
    # alone: the finalizer never touches its grid, so the pre-finalization
    # visibility (carried in as pre_visible) is returned unchanged. This
    # identity clause matters: an implementation that FORCES a grid state on
    # ordinary axes (on or off) would change behaviour the finalizer must not
    # touch, so the spec must reject it.
    Ensures(Implies(is_categorical, not Result()))
    Ensures(Implies(not is_categorical, Result() == pre_visible))
    # post-conditions-end
    # impl-start
    grid_visible = pre_visible
    if is_categorical:
        grid_visible = False
    return grid_visible
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. Adversarial G-EQ (refinement-fidelity) audit of nagini bundle mwaskom__seaborn-3069, focused on A-legs + model<->patch correspondence (R/I legs covered by G-CONF). adversary run via python -m swebench_unified.adversary with, SBU_BENCHMARK_DIR=benchmark-verified, meta float_encoding=real.

SPEC SHAPE: model.py has two functions. finalize_axis_range pins the return in ALL domain cases: has_explicit -> (user_lo,user_hi); ~explicit&categorical&~vertical -> (-0.5, slot_count()-0.5) with lo<hi; ~explicit&categorical&vertical -> (slot_count()-0.5, -0.5) with lo>hi; ~explicit&~categorical -> (user_lo,user_hi) identity clause. finalize_axis_grid: categorical -> False; else -> pre_visible. Both functions are fully output-determined, so only a behavioral echo can verify.

POSITIVE CONTROL: pos_control.py (byte-identical to model.py) -> `adversary verify` VERIFIED in 18.6s (exit 0). [Note: scripts/nagini_verify.sh alone does NOT pass --float-encoding=real and thus fails the vertical postcondition; the adversary/gate path reads real from meta and verifies. This is a harness-invocation detail, not a spec defect.]

atk_1 (prepatch bug: categorical range branch removed) -> NOT-A-COUNTEREXAMPLE (does not verify). Reproduces the recorded prepatch failure. prepatch_reproduced=true.
- atk_2 (boundary: hi = n+0.5 instead of n-0.5) -> NOT-A-COUNTEREXAMPLE (does not verify).
- atk_3 (control-flow: drop vertical inversion) -> NOT-A-COUNTEREXAMPLE (does not verify; vertical clauses reject).
- atk_4 (dropped is_categorical gate -> categorical range on EVERY non-explicit axis, the exact recorded G-EQ log-scale break) -> NOT-A-COUNTEREXAMPLE (does not verify; identity clause A4b rejects it). Spec correctly closes this sub-domain.
- atk_5 (grid forced False even on ordinary axes) -> NOT-A-COUNTEREXAMPLE (does not verify; grid identity clause rejects).
- atk_6 (grid turned ON for categorical, wrong direction) -> NOT-A-COUNTEREXAMPLE (does not verify).
- atk_7 (ECHO: early-return restructuring, behaviorally identical outputs in all 8 range cases + identical grid) -> CANDIDATE-COUNTEREXAMPLE (shares spec AND verifies, 17.4s).
- atk_8 (partial-domain: vertical branch returns (-0.5,n-0.5) unreversed) -> NOT-A-COUNTEREXAMPLE (does not verify; vertical reversal clause Result[0]>Result[1] rejects).

MANDATORY RESOLVE OF THE VERIFYING CANDIDATE (atk_7): atk_7's impl is a byte-for-byte behavioral clone of the gold impl, so its faithful refined patch IS the gold patch verbatim (patch.diff). Materialized and executed through the official harness: swebench_unified.harness.run_resolve("mwaskom__seaborn-3069", <gold patch>, timeout=1800) -> RESOLVED=True, COMPLETED=True (per-instance report resolved). The only verifying wrong-impl candidate therefore RESOLVES -> not a weakness (per 2026-08-06 policy: a resolving echo of the gold is NOT a G-EQ break). No verifying impl produced a non-resolving faithful patch.

REFINEMENT.MD AUDIT: every leg is R / A-consumed / A-reference / I; no kind-3 (unexpressible-changed-op). The two genuinely-changed ops (categorical range, grid-off) are modeled DEEPLY as A-reference (spelled-out branches), not hidden behind an axiom-of-the-changed-function. The single consumed axiom (slot_count>=1, A-consumed, A5) covers the UNCHANGED matplotlib get_major_ticks callee. A-legs correspondence holds: axiom_check.py validates slot_count>=1 (and ==n) against real len(get_major_ticks()); range deep model == real get_xlim()/get_ylim() over the 4 F2P witnesses + n=1..12 sweep + verbatim explicit ranges + continuous/log identity clauses; grid deep model == real gridline visibility under both grid rc themes + ordinary-axis pass-through. mapping.md binds every symbol at base_commit and justifies the singular-pair precondition (Implies(has_explicit,user_lo!=user_hi)) as excluding orthogonal, unchanged matplotlib nonsingular sanitization.

CONCLUSION: 8 distinct wrong impls (prepatch, boundary, two control-flow-effect, partial-domain, two grid-effect/over-broad, ungrounded/gate-drop, echo) run through the official adversary; 7 correctly rejected by the spec, the 1 that verifies is a behavioral echo whose materialized faithful patch RESOLVES under the official harness. verify=>correct holds on this evidence. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_8.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for mwaskom__seaborn-3069.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a figure is finalized, each coordinate axis carries a scale that is
  either categorical (a discrete, unordered scale whose positions are the
  integer slots 0, 1, ..., n-1 of its n categories) or ordinary (continuous).
  An axis whose scale is categorical must be drawn like the established
  categorical axes:

    (1) the visible data range is pinned to exactly half a slot beyond the
        first and last category position, i.e. the closed interval whose lower
        edge sits half a slot below position 0 and whose upper edge sits half a
        slot above the last position n-1 (so for n categories the span is from
        -0.5 to n-0.5), rather than the ordinary automatic-margin range;

    (2) when the axis is the vertical one, that range is reversed (top edge
        first), so the first category appears at the top;

    (3) the grid lines are turned off for such an axis, whatever visibility
        they had before finalization.

  The range tweaks (1)-(2) apply ONLY when the caller has not pinned an
  explicit range for that axis: if the caller supplied an explicit (lo, hi)
  range, that range is used verbatim and the categorical range/inversion is
  NOT applied. The grid tweak (3) applies to every categorical axis,
  explicit range or not. An ordinary (non-categorical) axis is left entirely
  alone by the finalizer: it keeps the ordinary automatic-margin range AND
  whatever grid visibility it already had going into finalization.

The axis range is a pair of interpreted real numbers (verified with
`--float-encoding=real`) because the behaviour at stake — edges sitting exactly
half a slot beyond the extreme category positions, and that pair reversed on the
vertical axis — is a real-valued relation the tests probe to floating tolerance.
The half-slot offset enters as the literal 0.5; the number of category slots `n`
is supplied by the unchanged tick-counting routine the finalizer queries, which
is axiomatized with the weakest sufficient contract (it returns the count of
category positions, at least one) and validated against the real routine
out-of-band by axiom_check.py (G-AX).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Tuple
from nagini_contracts.contracts import *


# axioms-start
@Pure
@ContractOnly
def slot_count() -> int:
    """The number of category slots on a categorical axis: the count of major
    tick positions the unchanged tick-querying routine reports for the axis.
    A categorical axis always has at least one category, so the count is
    positive. The weakest contract the proof needs (a positive count).
    Provenance + executable soundness check: mapping.md / axiom_check.py.
    """
    Ensures(Result() >= 1)
# axioms-end


# pure-start
# (no pure helpers — the half-slot edges are pinned by their linear defining
# equations in the postcondition.)
# pure-end


def finalize_axis_range(is_categorical: bool, has_explicit: bool, is_vertical: bool,
                        user_lo: float, user_hi: float) -> Tuple[float, float]:
    # pre-conditions-start
    # No mutable reference inputs; all parameters are read-only scalars.
    # The caller-supplied edges are genuine numbers (reflexivity excludes NaN).
    Requires(user_lo == user_lo and user_hi == user_hi)
    # An explicit caller range is modeled only when it is non-singular
    # (lo != hi). A singular pair is reshaped by the unchanged, pre-existing
    # range-sanitization machinery of the underlying axis object before it
    # lands as the visible range — behaviour orthogonal to the change under
    # specification, identical before and after it, so it sits outside the
    # modeled slice (mapping.md §2).
    Requires(Implies(has_explicit, user_lo != user_hi))
    # pre-conditions-end
    # post-conditions-start
    # A categorical axis WITHOUT an explicit caller range gets the categorical
    # range: edges exactly half a slot beyond the extreme category positions.
    # n = slot_count() >= 1; positions run 0 .. n-1; the lower edge sits half a
    # slot below position 0 (i.e. -0.5) and the upper edge half a slot above
    # position n-1 (i.e. n-1 + 0.5 == n - 0.5). On the horizontal axis the pair
    # is (low, high); on the vertical axis it is reversed (high first).
    #
    # Pin the two edges by their linear defining equations grounded in the slot
    # count, then pin orientation, so the result must be PRODUCED by the
    # categorical branch, not merely equal to a constant.
    Ensures(Implies(is_categorical and not has_explicit and not is_vertical,
                    Result()[0] + 0.5 == 0.0))
    Ensures(Implies(is_categorical and not has_explicit and not is_vertical,
                    Result()[1] + 0.5 == slot_count()))
    # Horizontal categorical range is increasing: low edge below high edge.
    Ensures(Implies(is_categorical and not has_explicit and not is_vertical,
                    Result()[0] < Result()[1]))
    # Vertical categorical range is the same pair reversed: high edge first,
    # so the range is decreasing (inverted axis, first category at the top).
    Ensures(Implies(is_categorical and not has_explicit and is_vertical,
                    Result()[1] + 0.5 == 0.0))
    Ensures(Implies(is_categorical and not has_explicit and is_vertical,
                    Result()[0] + 0.5 == slot_count()))
    Ensures(Implies(is_categorical and not has_explicit and is_vertical,
                    Result()[0] > Result()[1]))
    # The two orientations are exact reflections of one another.
    # When an explicit caller range is present it is used verbatim, REGARDLESS
    # of whether the axis is categorical — the categorical range/inversion is
    # NOT applied. This is what makes the categorical tweak conditional on the
    # absence of a caller-pinned range.
    Ensures(Implies(has_explicit, Result()[0] == user_lo))
    Ensures(Implies(has_explicit, Result()[1] == user_hi))
    # An ORDINARY (non-categorical) axis without an explicit caller range is
    # left entirely alone: the finalizer never touches its range, so the
    # pre-existing automatic-margin range (carried in as user_lo/user_hi) is
    # returned unchanged. This clause closes the non-categorical sub-domain:
    # an implementation that applies the categorical range to EVERY
    # non-explicit axis (dropping the is_categorical gate) would clobber
    # ordinary axes (e.g. log-scaled ones) and break passing tests, so the
    # spec must reject it.
    Ensures(Implies(not is_categorical and not has_explicit,
                    Result()[0] == user_lo))
    Ensures(Implies(not is_categorical and not has_explicit,
                    Result()[1] == user_hi))
    # post-conditions-end
    # impl-start
    lo = user_lo
    hi = user_hi
    if has_explicit:
        # Caller pinned the range explicitly: use it verbatim. The categorical
        # special-casing below is skipped.
        lo = user_lo
        hi = user_hi
    elif is_categorical:
        n = slot_count()
        lo = -0.5
        hi = n - 0.5
        if is_vertical:
            tmp = lo
            lo = hi
            hi = tmp
    return (lo, hi)
    # impl-end


def finalize_axis_grid(is_categorical: bool, pre_visible: bool) -> bool:
    # pre-conditions-start
    # No mutable reference inputs; both parameters are read-only booleans.
    # pre-conditions-end
    # post-conditions-start
    # A categorical axis has its grid turned off, whatever visibility it had
    # going into finalization. An ordinary (non-categorical) axis is left
    # alone: the finalizer never touches its grid, so the pre-finalization
    # visibility (carried in as pre_visible) is returned unchanged. This
    # identity clause matters: an implementation that FORCES a grid state on
    # ordinary axes (on or off) would change behaviour the finalizer must not
    # touch, so the spec must reject it.
    Ensures(Implies(is_categorical, not Result()))
    Ensures(Implies(not is_categorical, Result() == pre_visible))
    # post-conditions-end
    # impl-start
    grid_visible = pre_visible
    if is_categorical:
        grid_visible = False
    return grid_visible
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. Adversarial G-EQ (refinement-fidelity) audit of nagini bundle mwaskom__seaborn-3069, focused on A-legs + model<->patch correspondence (R/I legs covered by G-CONF). adversary run via python -m swebench_unified.adversary with, SBU_BENCHMARK_DIR=benchmark-verified, meta float_encoding=real.

SPEC SHAPE: model.py has two functions. finalize_axis_range pins the return in ALL domain cases: has_explicit -> (user_lo,user_hi); ~explicit&categorical&~vertical -> (-0.5, slot_count()-0.5) with lo<hi; ~explicit&categorical&vertical -> (slot_count()-0.5, -0.5) with lo>hi; ~explicit&~categorical -> (user_lo,user_hi) identity clause. finalize_axis_grid: categorical -> False; else -> pre_visible. Both functions are fully output-determined, so only a behavioral echo can verify.

POSITIVE CONTROL: pos_control.py (byte-identical to model.py) -> `adversary verify` VERIFIED in 18.6s (exit 0). [Note: scripts/nagini_verify.sh alone does NOT pass --float-encoding=real and thus fails the vertical postcondition; the adversary/gate path reads real from meta and verifies. This is a harness-invocation detail, not a spec defect.]

atk_1 (prepatch bug: categorical range branch removed) -> NOT-A-COUNTEREXAMPLE (does not verify). Reproduces the recorded prepatch failure. prepatch_reproduced=true.
- atk_2 (boundary: hi = n+0.5 instead of n-0.5) -> NOT-A-COUNTEREXAMPLE (does not verify).
- atk_3 (control-flow: drop vertical inversion) -> NOT-A-COUNTEREXAMPLE (does not verify; vertical clauses reject).
- atk_4 (dropped is_categorical gate -> categorical range on EVERY non-explicit axis, the exact recorded G-EQ log-scale break) -> NOT-A-COUNTEREXAMPLE (does not verify; identity clause A4b rejects it). Spec correctly closes this sub-domain.
- atk_5 (grid forced False even on ordinary axes) -> NOT-A-COUNTEREXAMPLE (does not verify; grid identity clause rejects).
- atk_6 (grid turned ON for categorical, wrong direction) -> NOT-A-COUNTEREXAMPLE (does not verify).
- atk_7 (ECHO: early-return restructuring, behaviorally identical outputs in all 8 range cases + identical grid) -> CANDIDATE-COUNTEREXAMPLE (shares spec AND verifies, 17.4s).
- atk_8 (partial-domain: vertical branch returns (-0.5,n-0.5) unreversed) -> NOT-A-COUNTEREXAMPLE (does not verify; vertical reversal clause Result[0]>Result[1] rejects).

MANDATORY RESOLVE OF THE VERIFYING CANDIDATE (atk_7): atk_7's impl is a byte-for-byte behavioral clone of the gold impl, so its faithful refined patch IS the gold patch verbatim (patch.diff). Materialized and executed through the official harness: swebench_unified.harness.run_resolve("mwaskom__seaborn-3069", <gold patch>, timeout=1800) -> RESOLVED=True, COMPLETED=True (per-instance report resolved). The only verifying wrong-impl candidate therefore RESOLVES -> not a weakness (per 2026-08-06 policy: a resolving echo of the gold is NOT a G-EQ break). No verifying impl produced a non-resolving faithful patch.

REFINEMENT.MD AUDIT: every leg is R / A-consumed / A-reference / I; no kind-3 (unexpressible-changed-op). The two genuinely-changed ops (categorical range, grid-off) are modeled DEEPLY as A-reference (spelled-out branches), not hidden behind an axiom-of-the-changed-function. The single consumed axiom (slot_count>=1, A-consumed, A5) covers the UNCHANGED matplotlib get_major_ticks callee. A-legs correspondence holds: axiom_check.py validates slot_count>=1 (and ==n) against real len(get_major_ticks()); range deep model == real get_xlim()/get_ylim() over the 4 F2P witnesses + n=1..12 sweep + verbatim explicit ranges + continuous/log identity clauses; grid deep model == real gridline visibility under both grid rc themes + ordinary-axis pass-through. mapping.md binds every symbol at base_commit and justifies the singular-pair precondition (Implies(has_explicit,user_lo!=user_hi)) as excluding orthogonal, unchanged matplotlib nonsingular sanitization.

CONCLUSION: 8 distinct wrong impls (prepatch, boundary, two control-flow-effect, partial-domain, two grid-effect/over-broad, ungrounded/gate-drop, echo) run through the official adversary; 7 correctly rejected by the spec, the 1 that verifies is a behavioral echo whose materialized faithful patch RESOLVES under the official harness. verify=>correct holds on this evidence. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack failed: the deep models finalize_axis_range and finalize_axis_grid agree with the real seaborn callee (Plotter._finalize_figure Nominal special-casing block) on every input in the modeled domain.

Method: no CPU env had matplotlib+seaborn, so I ran validation inside the instance's own harness Docker image (swebench/sweb.eval.x86_64.mwaskom_1776_seaborn-3069) with the gold patch applied (git apply of the verbatim gold hunk; confirmed 'Nominal scale special-casing' present at plot.py:1647).

(1) Ran the bundle's axiom_check.py (G-AX) against the REAL patched repo (mpl 3.7.2 / sns 0.12.1dev). Result: 'G-AX OK ... 0 violations' — deep range/grid models == real get_xlim/get_ylim and real gridline visibility on the 4 F2P witnesses + 96 categorical axes (n=1..12, x&y) + verbatim explicit ranges + both grid rc themes + identity clauses (continuous & log axes untouched, both pre_visible truth values).

(2) Independent probes for cases axiom_check does NOT cover, all on the patched container: continuous+explicit x -> (-1.0,5.0) verbatim; continuous+explicit y -> (2.0,40.0) verbatim; categorical+string-explicit ('a','c') -> (-0.5,2.5) (matches, because user_lo/user_hi model the post-unit-conversion lo,hi per mapping.md §2); categorical n=10 -> (-0.5,9.5). All match the model exactly.

Spec-strength / drift analysis clause by clause:
- has_explicit -> Result==(user_lo,user_hi) REGARDLESS of is_categorical: faithful because the gold's inner 'if axis_key not in p._limits' gates the categorical range OUT when a limit exists, so both categorical and continuous explicit axes get the caller pair verbatim. Confirmed for cat & cont, x & y, numeric & string.
- categorical/no-explicit -> (-0.5,n-0.5) inverted on y: matches real across n=1..12.
- non-categorical/no-explicit identity (range and grid pass-through): matches real, including log-scale, under both grid themes.
- grid: categorical->off (both themes), non-categorical->pre_visible: matches real gridline visibility.

Domain scoping is legitimate, not over-strong: the one-sided limit (None,5.0) yields real (0.0,5.0) but None is not a float and is excluded by the float carrier + Requires(user_lo==user_lo, user_lo!=user_hi) precondition and mapping.md §2 (singular/None pairs handled by unchanged matplotlib nonsingular machinery, outside the modeled slice). This is a faithful modeling boundary, not a divergence.

Spec region byte-identity was not the attack vector here (faithfulness, not same-spec), but the model's postconditions are all discriminating (pin edges by linear defining equations grounded in slot_count, plus orientation), so the spec is neither too weak nor drifting from real behavior. No diverging input exists within the modeled domain.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Solver-facing spec view = model.py with impl regions elided (bundle.solution_src(); confirmed via markers.spec_view — both impl regions become '... elided'). Verified the spec regions are the frozen spec (region hashes / same-spec model). Compared the spec view against the PUBLIC problem_statement (not hints).

The problem_statement is unusually explicit and already discloses all three behaviors publicly: (1) 'The scale is drawn to +/- 0.5 from the first and last tick, rather than using the normal margin logic'; (2) 'A grid is not shown, even when it otherwise would be with the active style'; (3) 'If on the y axis, the axis is inverted'. It even names so.Nominal scales and Plotter._finalize_figure as the implementation site.

The spec view re-states ONLY these three behaviors at the abstraction level of booleans + a real-valued (lo,hi) range relation: categorical range = (-0.5, n-0.5), reversed on the vertical axis, grid off. It adds the natural correctness constraints that an explicit caller range is honored verbatim and that ordinary/non-categorical axes are left untouched — these are obvious well-formedness conditions, not disclosures of the gold mechanism, and they are weaker than the problem_statement's own framing (the PS already implies only categorical/Nominal axes get this treatment).

Mechanical grep of the spec view for edit-revealing identifiers finds NONE: Nominal, _finalize_figure, p._limits/_limits, isinstance, get_major_ticks, set_xlim/set_ylim/set_lim, axis_key, _scales, nticks, plot.py, scales.py, auto=None, which= — all absent. Every gold-edit specific (the isinstance(self._scales.get(axis_key), Nominal) gate, the 'axis_key not in p._limits' guard, len(axis_obj.get_major_ticks()), file:line numbers, callee names) lives exclusively in mapping.md / refinement.md, which are auditor-derivation documents OUTSIDE the spec view. G-LEAK mechanical screen passes (spec view clean). No RELAXED_LEAKAGE.md and none needed. The spec view does not leak the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
