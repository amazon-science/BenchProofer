# P2 adversarial audit — astropy__astropy-7336

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 9 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py`, `atk_9.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -34,7 +34,6 @@
 Markers (machine-parsed) delimit the spec / proof / impl regions.
 """
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class RetVal:
@@ -44,9 +43,6 @@
 
     def __init__(self, is_none: bool, unit: int) -> None:
         Requires(Implies(is_none, unit == NO_UNIT()))
-        # Terminates: two field assignments, no loop and no call. Level 1 leaves
-        # room strictly below finalize_return's level 6, which constructs RetVal.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.is_none) and Acc(self.unit))
         Ensures(self.is_none == is_none and self.unit == unit)
         self.is_none = is_none  # type: bool
@@ -105,11 +101,6 @@
     # no unit; a genuine quantity carries a genuine unit id (not the no-value
     # placeholder). A genuine unit target is never one of the two sentinels.
     Requires(ret.is_none == (ret.unit == NO_UNIT()))
-    # Total, not merely partial, correctness: the postconditions below are
-    # claimed of every call, not only of runs that happen to reach the return.
-    # This method is loop-free and its only callee is RetVal.__init__ at level 1,
-    # so level 6 leaves ample room strictly beneath it.
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(ret.is_none, 1 / 2) and Acc(ret.unit, 1 / 2))
@@ -129,7 +120,7 @@
                     and Result().unit == convert_unit(ret.unit, target)))
     # post-conditions-end
     # impl-start
-    if is_genuine_target(target):
+    if target != TARGET_UNSPECIFIED():
         return RetVal(False, convert_unit(ret.unit, target))
     else:
         return RetVal(ret.is_none, ret.unit)
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -34,7 +34,6 @@
 Markers (machine-parsed) delimit the spec / proof / impl regions.
 """
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class RetVal:
@@ -44,9 +43,6 @@
 
     def __init__(self, is_none: bool, unit: int) -> None:
         Requires(Implies(is_none, unit == NO_UNIT()))
-        # Terminates: two field assignments, no loop and no call. Level 1 leaves
-        # room strictly below finalize_return's level 6, which constructs RetVal.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.is_none) and Acc(self.unit))
         Ensures(self.is_none == is_none and self.unit == unit)
         self.is_none = is_none  # type: bool
@@ -105,11 +101,6 @@
     # no unit; a genuine quantity carries a genuine unit id (not the no-value
     # placeholder). A genuine unit target is never one of the two sentinels.
     Requires(ret.is_none == (ret.unit == NO_UNIT()))
-    # Total, not merely partial, correctness: the postconditions below are
-    # claimed of every call, not only of runs that happen to reach the return.
-    # This method is loop-free and its only callee is RetVal.__init__ at level 1,
-    # so level 6 leaves ample room strictly beneath it.
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(ret.is_none, 1 / 2) and Acc(ret.unit, 1 / 2))
@@ -130,7 +121,7 @@
     # post-conditions-end
     # impl-start
     if is_genuine_target(target):
+        return RetVal(ret.is_none, ret.unit)
+    else:
         return RetVal(False, convert_unit(ret.unit, target))
-    else:
-        return RetVal(ret.is_none, ret.unit)
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -34,7 +34,6 @@
 Markers (machine-parsed) delimit the spec / proof / impl regions.
 """
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class RetVal:
@@ -44,9 +43,6 @@
 
     def __init__(self, is_none: bool, unit: int) -> None:
         Requires(Implies(is_none, unit == NO_UNIT()))
-        # Terminates: two field assignments, no loop and no call. Level 1 leaves
-        # room strictly below finalize_return's level 6, which constructs RetVal.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.is_none) and Acc(self.unit))
         Ensures(self.is_none == is_none and self.unit == unit)
         self.is_none = is_none  # type: bool
@@ -105,11 +101,6 @@
     # no unit; a genuine quantity carries a genuine unit id (not the no-value
     # placeholder). A genuine unit target is never one of the two sentinels.
     Requires(ret.is_none == (ret.unit == NO_UNIT()))
-    # Total, not merely partial, correctness: the postconditions below are
-    # claimed of every call, not only of runs that happen to reach the return.
-    # This method is loop-free and its only callee is RetVal.__init__ at level 1,
-    # so level 6 leaves ample room strictly beneath it.
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(ret.is_none, 1 / 2) and Acc(ret.unit, 1 / 2))
@@ -130,7 +121,7 @@
     # post-conditions-end
     # impl-start
     if is_genuine_target(target):
-        return RetVal(False, convert_unit(ret.unit, target))
+        return RetVal(False, ret.unit)
     else:
         return RetVal(ret.is_none, ret.unit)
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -34,7 +34,6 @@
 Markers (machine-parsed) delimit the spec / proof / impl regions.
 """
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class RetVal:
@@ -44,9 +43,6 @@
 
     def __init__(self, is_none: bool, unit: int) -> None:
         Requires(Implies(is_none, unit == NO_UNIT()))
-        # Terminates: two field assignments, no loop and no call. Level 1 leaves
-        # room strictly below finalize_return's level 6, which constructs RetVal.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.is_none) and Acc(self.unit))
         Ensures(self.is_none == is_none and self.unit == unit)
         self.is_none = is_none  # type: bool
@@ -105,11 +101,6 @@
     # no unit; a genuine quantity carries a genuine unit id (not the no-value
     # placeholder). A genuine unit target is never one of the two sentinels.
     Requires(ret.is_none == (ret.unit == NO_UNIT()))
-    # Total, not merely partial, correctness: the postconditions below are
-    # claimed of every call, not only of runs that happen to reach the return.
-    # This method is loop-free and its only callee is RetVal.__init__ at level 1,
-    # so level 6 leaves ample room strictly beneath it.
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(ret.is_none, 1 / 2) and Acc(ret.unit, 1 / 2))
@@ -132,5 +123,5 @@
     if is_genuine_target(target):
         return RetVal(False, convert_unit(ret.unit, target))
     else:
-        return RetVal(ret.is_none, ret.unit)
+        return RetVal(False, ret.unit)
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -34,7 +34,6 @@
 Markers (machine-parsed) delimit the spec / proof / impl regions.
 """
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class RetVal:
@@ -44,9 +43,6 @@
 
     def __init__(self, is_none: bool, unit: int) -> None:
         Requires(Implies(is_none, unit == NO_UNIT()))
-        # Terminates: two field assignments, no loop and no call. Level 1 leaves
-        # room strictly below finalize_return's level 6, which constructs RetVal.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.is_none) and Acc(self.unit))
         Ensures(self.is_none == is_none and self.unit == unit)
         self.is_none = is_none  # type: bool
@@ -105,11 +101,6 @@
     # no unit; a genuine quantity carries a genuine unit id (not the no-value
     # placeholder). A genuine unit target is never one of the two sentinels.
     Requires(ret.is_none == (ret.unit == NO_UNIT()))
-    # Total, not merely partial, correctness: the postconditions below are
-    # claimed of every call, not only of runs that happen to reach the return.
-    # This method is loop-free and its only callee is RetVal.__init__ at level 1,
-    # so level 6 leaves ample room strictly beneath it.
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(ret.is_none, 1 / 2) and Acc(ret.unit, 1 / 2))
@@ -129,6 +120,8 @@
                     and Result().unit == convert_unit(ret.unit, target)))
     # post-conditions-end
     # impl-start
+    while True:
+        pass
     if is_genuine_target(target):
         return RetVal(False, convert_unit(ret.unit, target))
     else:
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -34,7 +34,6 @@
 Markers (machine-parsed) delimit the spec / proof / impl regions.
 """
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class RetVal:
@@ -44,9 +43,6 @@
 
     def __init__(self, is_none: bool, unit: int) -> None:
         Requires(Implies(is_none, unit == NO_UNIT()))
-        # Terminates: two field assignments, no loop and no call. Level 1 leaves
-        # room strictly below finalize_return's level 6, which constructs RetVal.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.is_none) and Acc(self.unit))
         Ensures(self.is_none == is_none and self.unit == unit)
         self.is_none = is_none  # type: bool
@@ -105,11 +101,6 @@
     # no unit; a genuine quantity carries a genuine unit id (not the no-value
     # placeholder). A genuine unit target is never one of the two sentinels.
     Requires(ret.is_none == (ret.unit == NO_UNIT()))
-    # Total, not merely partial, correctness: the postconditions below are
-    # claimed of every call, not only of runs that happen to reach the return.
-    # This method is loop-free and its only callee is RetVal.__init__ at level 1,
-    # so level 6 leaves ample room strictly beneath it.
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(ret.is_none, 1 / 2) and Acc(ret.unit, 1 / 2))
@@ -129,7 +120,7 @@
                     and Result().unit == convert_unit(ret.unit, target)))
     # post-conditions-end
     # impl-start
-    if is_genuine_target(target):
+    if target >= 0:
         return RetVal(False, convert_unit(ret.unit, target))
     else:
         return RetVal(ret.is_none, ret.unit)
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -34,7 +34,6 @@
 Markers (machine-parsed) delimit the spec / proof / impl regions.
 """
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class RetVal:
@@ -44,9 +43,6 @@
 
     def __init__(self, is_none: bool, unit: int) -> None:
         Requires(Implies(is_none, unit == NO_UNIT()))
-        # Terminates: two field assignments, no loop and no call. Level 1 leaves
-        # room strictly below finalize_return's level 6, which constructs RetVal.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.is_none) and Acc(self.unit))
         Ensures(self.is_none == is_none and self.unit == unit)
         self.is_none = is_none  # type: bool
@@ -105,11 +101,6 @@
     # no unit; a genuine quantity carries a genuine unit id (not the no-value
     # placeholder). A genuine unit target is never one of the two sentinels.
     Requires(ret.is_none == (ret.unit == NO_UNIT()))
-    # Total, not merely partial, correctness: the postconditions below are
-    # claimed of every call, not only of runs that happen to reach the return.
-    # This method is loop-free and its only callee is RetVal.__init__ at level 1,
-    # so level 6 leaves ample room strictly beneath it.
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(ret.is_none, 1 / 2) and Acc(ret.unit, 1 / 2))
@@ -132,5 +123,5 @@
     if is_genuine_target(target):
         return RetVal(False, convert_unit(ret.unit, target))
     else:
-        return RetVal(ret.is_none, ret.unit)
+        return RetVal(ret.is_none, NO_UNIT())
     # impl-end
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -34,7 +34,6 @@
 Markers (machine-parsed) delimit the spec / proof / impl regions.
 """
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class RetVal:
@@ -44,9 +43,6 @@
 
     def __init__(self, is_none: bool, unit: int) -> None:
         Requires(Implies(is_none, unit == NO_UNIT()))
-        # Terminates: two field assignments, no loop and no call. Level 1 leaves
-        # room strictly below finalize_return's level 6, which constructs RetVal.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.is_none) and Acc(self.unit))
         Ensures(self.is_none == is_none and self.unit == unit)
         self.is_none = is_none  # type: bool
@@ -105,11 +101,6 @@
     # no unit; a genuine quantity carries a genuine unit id (not the no-value
     # placeholder). A genuine unit target is never one of the two sentinels.
     Requires(ret.is_none == (ret.unit == NO_UNIT()))
-    # Total, not merely partial, correctness: the postconditions below are
-    # claimed of every call, not only of runs that happen to reach the return.
-    # This method is loop-free and its only callee is RetVal.__init__ at level 1,
-    # so level 6 leaves ample room strictly beneath it.
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(ret.is_none, 1 / 2) and Acc(ret.unit, 1 / 2))
@@ -130,7 +121,7 @@
     # post-conditions-end
     # impl-start
     if is_genuine_target(target):
-        return RetVal(False, convert_unit(ret.unit, target))
+        return RetVal(False, convert_unit(ret.unit, target) + 1)
     else:
         return RetVal(ret.is_none, ret.unit)
     # impl-end
```

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good)

```diff
@@ -34,7 +34,6 @@
 Markers (machine-parsed) delimit the spec / proof / impl regions.
 """
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class RetVal:
@@ -44,9 +43,6 @@
 
     def __init__(self, is_none: bool, unit: int) -> None:
         Requires(Implies(is_none, unit == NO_UNIT()))
-        # Terminates: two field assignments, no loop and no call. Level 1 leaves
-        # room strictly below finalize_return's level 6, which constructs RetVal.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.is_none) and Acc(self.unit))
         Ensures(self.is_none == is_none and self.unit == unit)
         self.is_none = is_none  # type: bool
@@ -105,11 +101,6 @@
     # no unit; a genuine quantity carries a genuine unit id (not the no-value
     # placeholder). A genuine unit target is never one of the two sentinels.
     Requires(ret.is_none == (ret.unit == NO_UNIT()))
-    # Total, not merely partial, correctness: the postconditions below are
-    # claimed of every call, not only of runs that happen to reach the return.
-    # This method is loop-free and its only callee is RetVal.__init__ at level 1,
-    # so level 6 leaves ample room strictly beneath it.
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(ret.is_none, 1 / 2) and Acc(ret.unit, 1 / 2))
@@ -129,7 +120,7 @@
                     and Result().unit == convert_unit(ret.unit, target)))
     # post-conditions-end
     # impl-start
-    if is_genuine_target(target):
+    if target != TARGET_NOVALUE():
         return RetVal(False, convert_unit(ret.unit, target))
     else:
         return RetVal(ret.is_none, ret.unit)
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for astropy__astropy-7336.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A units-checking wrapper, after calling the wrapped function and obtaining its
  return value, decides how to finalise that value according to the wrapped
  function's declared return target:

    * If the wrapped function declares NO return target (the "unspecified"
      sentinel), the wrapper yields the return value untouched.
    * If the wrapped function declares its return target to be the "no value"
      target (i.e. it is annotated as producing nothing), the wrapper ALSO
      yields the return value untouched. In particular it must NOT attempt the
      unit conversion in this case — the returned object may be the no-value
      object, which carries no unit and cannot be converted.
    * Only when the wrapped function declares a genuine unit target does the
      wrapper convert the return value into that target unit; the finalised
      value is then a quantity expressed in that target unit.

  The discriminating behaviour: the "no value" target is treated exactly like
  the "unspecified" sentinel (pass through), NOT like a genuine unit target.

The return value is modelled as a small object carrying whether it is the
no-value object and, when it is a quantity, its current unit id (an int). The
declared return target is an int code: a distinguished "unspecified" sentinel,
a distinguished "no value" sentinel, and any other value denoting a genuine
unit. The conversion of a quantity into a target unit is modelled deeply as a
pure operation that is only defined on a genuine quantity (never on the
no-value object) — exactly the operation whose misuse the desired behaviour
must avoid. No library callee is consumed inside a postcondition (the axioms
region is empty; see mapping.md §3); the decision is validated against the real
wrapper by axiom_check.py (G-AX).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from nagini_contracts.contracts import *


class RetVal:
    """The value returned by the wrapped function, then finalised by the
    wrapper. `is_none` marks the no-value object (which carries no unit and
    cannot be converted); `unit` is the current unit id when it is a quantity."""

    def __init__(self, is_none: bool, unit: int) -> None:
        Requires(Implies(is_none, unit == NO_UNIT()))
        Ensures(Acc(self.is_none) and Acc(self.unit))
        Ensures(self.is_none == is_none and self.unit == unit)
        self.is_none = is_none  # type: bool
        self.unit = unit  # type: int


# axioms-start
# (none — the modelled delta is a pure decision over the declared return target
# plus a deep model of the unit conversion; no opaque library callee is consumed
# inside an Ensures. See mapping.md §3.)
# axioms-end


# pure-start
@Pure
def TARGET_UNSPECIFIED() -> int:
    # the "no return target was declared" sentinel
    return -1


@Pure
def TARGET_NOVALUE() -> int:
    # the "declared to produce nothing" target
    return -2


@Pure
def NO_UNIT() -> int:
    # the unit id carried by the no-value object (it has none)
    return -3


@Pure
def is_genuine_target(target: int) -> bool:
    """A declared return target is a genuine unit target exactly when it is
    neither the unspecified sentinel nor the no-value target."""
    return target != TARGET_UNSPECIFIED() and target != TARGET_NOVALUE()
# pure-end


@Pure
def convert_unit(q_unit: int, target: int) -> int:
    Requires(is_genuine_target(target))
    # The unit id of a quantity after converting it into `target`: the target
    # unit. (`q_unit` is the source unit; conversion re-expresses the same
    # physical value in `target`.) Only ever applied to a genuine quantity and a
    # genuine unit target — never to the no-value object.
    Ensures(Result() == target)
    return target


def finalize_return(ret: RetVal, target: int) -> RetVal:
    # pre-conditions-start
    Requires(Acc(ret.is_none, 1 / 2) and Acc(ret.unit, 1 / 2))
    # Domain fact (real semantics, mapping.md §4): the no-value object carries
    # no unit; a genuine quantity carries a genuine unit id (not the no-value
    # placeholder). A genuine unit target is never one of the two sentinels.
    Requires(ret.is_none == (ret.unit == NO_UNIT()))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(ret.is_none, 1 / 2) and Acc(ret.unit, 1 / 2))
    Ensures(Acc(Result().is_none) and Acc(Result().unit))
    # When no genuine unit target is declared (unspecified sentinel OR the
    # no-value target), the value passes through untouched: same object kind,
    # same unit. In particular the no-value object is returned as-is and is
    # NOT subjected to a conversion.
    Ensures(Implies(not is_genuine_target(target),
                    Result().is_none == ret.is_none
                    and Result().unit == ret.unit))
    # When a genuine unit target is declared, the value is converted into that
    # target: the finalised value is a quantity (not the no-value object) whose
    # unit is the declared target unit.
    Ensures(Implies(is_genuine_target(target),
                    (not Result().is_none)
                    and Result().unit == convert_unit(ret.unit, target)))
    # post-conditions-end
    # impl-start
    if is_genuine_target(target):
        return RetVal(False, convert_unit(ret.unit, target))
    else:
        return RetVal(ret.is_none, ret.unit)
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

Instance astropy__astropy-7336, nagini. Frozen spec: finalize_return(ret, target). The postcondition FULLY pins BOTH observed fields on BOTH branches: non-genuine target (unspecified OR no-value) => Result().is_none==ret.is_none AND Result().unit==ret.unit (pass-through); genuine target => (not Result().is_none) AND Result().unit==convert_unit(ret.unit,target). convert_unit is @Pure with precondition Requires(is_genuine_target(target)) and Ensures(Result()==target); this precondition is what forces the no-value (-> None) pass-through — an impl that tries to convert on TARGET_NOVALUE() violates the callee precondition and fails to verify.

 Project root, SBU_BENCHMARK_DIR=benchmark-verified, python python. 9 distinct same-spec wrong impls built by editing ONLY the impl region (axioms/@Pure/Requires/Ensures byte-identical; all 9 confirmed SAME by `adversary same-spec`). Verifications run concurrently in batches of 3 (JVM+Z3 each) via `adversary weakness`.

Attacks & observed results (command per file: `python -m swebench_unified.adversary weakness nagini astropy__astropy-7336 <path>`):
- atk_1 (PREPATCH BUG: `if target != TARGET_UNSPECIFIED(): convert`): exit 2, does-not-verify. Prepatch bug reproduced: converts on TARGET_NOVALUE(), violating convert_unit's is_genuine_target precondition. matches model_prepatch.py / G-DIFF.
- atk_2 (control-flow: swapped branches): exit 2, does-not-verify.
- atk_3 (genuine branch keeps source unit `RetVal(False, ret.unit)`): exit 2, does-not-verify (violates Result().unit==convert_unit).
- atk_4 (non-genuine branch forces is_none=False): exit 2, does-not-verify (violates Result().is_none==ret.is_none on no-value pass-through).
- atk_5 (control-flow-effect: `while True: pass` before correct return / non-termination): exit 2, does-not-verify (MustTerminate).
- atk_6 (boundary/partial-domain guard `if target >= 0`): exit 2, does-not-verify (mis-partitions sentinels vs genuine).
- atk_7 (ungrounded-oracle echo: non-genuine returns `RetVal(ret.is_none, NO_UNIT())`): exit 2, does-not-verify (violates Result().unit==ret.unit for genuine-unit pass-through under -> None).
- atk_8 (off-by-one wrong unit `convert_unit(...)+1`): exit 2, does-not-verify.
- atk_9 (MIRROR bug `if target != TARGET_NOVALUE(): convert`): exit 2, does-not-verify (converts on TARGET_UNSPECIFIED and, worse, tries convert on NOVALUE path excluded — actually converts on genuine+unspecified; fails Result().unit==ret.unit on unspecified pass-through and callee precondition).

Every attack returned NOT-A-COUNTEREXAMPLE (exit 2 = shares spec but does NOT verify). NO CANDIDATE emerged, therefore no faithful refined patch needed materialization/resolve — the verify=>correct implication is not falsifiable here because the spec admits no verifying wrong impl in this attack suite.

Positive control: `adversary verify nagini astropy__astropy-7336 pos_control.py` => VERIFIED in 10.6s (exit 0). So the spec is not vacuous/over-tight: the correct impl verifies while all 9 wrong impls are rejected.

Refinement audit (refinement.md): legs A1(R), A2(R), A3(I+R), A4(A-reference), A5(R) — no kind-3 leg. Section C explicitly claims no consumed axiom and no unexpressible-changed-op; confirmed: axioms region of model.py is empty. The two A-reference correspondences are checked by axiom_check.py against the REAL astropy callees: (1) convert_unit==Quantity.to via `q.to(target).unit==target` over 8 unit pairs; (2) finalize_return decision==real quantity_input wrapper via three decorated functions (genuine->deg convert; `-> None`->pass-through incl. the F2P test_return_annotation_none; unspecified->pass-through). The A-reference callee bindings (mapping.md §3.1/§3.2, quantity.py:821, decorators.py:223-226 post-fix) match the deep model. Discriminating content (`None in (empty, None)` <=> is_genuine_target(TARGET_NOVALUE())==False) is faithfully forced by convert_unit's precondition. Correspondence holds.

Verdict SOUND: >=5 (9) distinct same-spec attacks run, none is a verifying-wrong-impl, so none can break verify=>correct; positive control verifies; refinement legs are all R/A-reference/I with sound callee correspondence.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 9 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py`, `atk_9.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 9 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for astropy__astropy-7336.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A units-checking wrapper, after calling the wrapped function and obtaining its
  return value, decides how to finalise that value according to the wrapped
  function's declared return target:

    * If the wrapped function declares NO return target (the "unspecified"
      sentinel), the wrapper yields the return value untouched.
    * If the wrapped function declares its return target to be the "no value"
      target (i.e. it is annotated as producing nothing), the wrapper ALSO
      yields the return value untouched. In particular it must NOT attempt the
      unit conversion in this case — the returned object may be the no-value
      object, which carries no unit and cannot be converted.
    * Only when the wrapped function declares a genuine unit target does the
      wrapper convert the return value into that target unit; the finalised
      value is then a quantity expressed in that target unit.

  The discriminating behaviour: the "no value" target is treated exactly like
  the "unspecified" sentinel (pass through), NOT like a genuine unit target.

The return value is modelled as a small object carrying whether it is the
no-value object and, when it is a quantity, its current unit id (an int). The
declared return target is an int code: a distinguished "unspecified" sentinel,
a distinguished "no value" sentinel, and any other value denoting a genuine
unit. The conversion of a quantity into a target unit is modelled deeply as a
pure operation that is only defined on a genuine quantity (never on the
no-value object) — exactly the operation whose misuse the desired behaviour
must avoid. No library callee is consumed inside a postcondition (the axioms
region is empty; see mapping.md §3); the decision is validated against the real
wrapper by axiom_check.py (G-AX).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from nagini_contracts.contracts import *


class RetVal:
    """The value returned by the wrapped function, then finalised by the
    wrapper. `is_none` marks the no-value object (which carries no unit and
    cannot be converted); `unit` is the current unit id when it is a quantity."""

    def __init__(self, is_none: bool, unit: int) -> None:
        Requires(Implies(is_none, unit == NO_UNIT()))
        Ensures(Acc(self.is_none) and Acc(self.unit))
        Ensures(self.is_none == is_none and self.unit == unit)
        self.is_none = is_none  # type: bool
        self.unit = unit  # type: int


# axioms-start
# (none — the modelled delta is a pure decision over the declared return target
# plus a deep model of the unit conversion; no opaque library callee is consumed
# inside an Ensures. See mapping.md §3.)
# axioms-end


# pure-start
@Pure
def TARGET_UNSPECIFIED() -> int:
    # the "no return target was declared" sentinel
    return -1


@Pure
def TARGET_NOVALUE() -> int:
    # the "declared to produce nothing" target
    return -2


@Pure
def NO_UNIT() -> int:
    # the unit id carried by the no-value object (it has none)
    return -3


@Pure
def is_genuine_target(target: int) -> bool:
    """A declared return target is a genuine unit target exactly when it is
    neither the unspecified sentinel nor the no-value target."""
    return target != TARGET_UNSPECIFIED() and target != TARGET_NOVALUE()
# pure-end


@Pure
def convert_unit(q_unit: int, target: int) -> int:
    Requires(is_genuine_target(target))
    # The unit id of a quantity after converting it into `target`: the target
    # unit. (`q_unit` is the source unit; conversion re-expresses the same
    # physical value in `target`.) Only ever applied to a genuine quantity and a
    # genuine unit target — never to the no-value object.
    Ensures(Result() == target)
    return target


def finalize_return(ret: RetVal, target: int) -> RetVal:
    # pre-conditions-start
    Requires(Acc(ret.is_none, 1 / 2) and Acc(ret.unit, 1 / 2))
    # Domain fact (real semantics, mapping.md §4): the no-value object carries
    # no unit; a genuine quantity carries a genuine unit id (not the no-value
    # placeholder). A genuine unit target is never one of the two sentinels.
    Requires(ret.is_none == (ret.unit == NO_UNIT()))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(ret.is_none, 1 / 2) and Acc(ret.unit, 1 / 2))
    Ensures(Acc(Result().is_none) and Acc(Result().unit))
    # When no genuine unit target is declared (unspecified sentinel OR the
    # no-value target), the value passes through untouched: same object kind,
    # same unit. In particular the no-value object is returned as-is and is
    # NOT subjected to a conversion.
    Ensures(Implies(not is_genuine_target(target),
                    Result().is_none == ret.is_none
                    and Result().unit == ret.unit))
    # When a genuine unit target is declared, the value is converted into that
    # target: the finalised value is a quantity (not the no-value object) whose
    # unit is the declared target unit.
    Ensures(Implies(is_genuine_target(target),
                    (not Result().is_none)
                    and Result().unit == convert_unit(ret.unit, target)))
    # post-conditions-end
    # impl-start
    if is_genuine_target(target):
        return RetVal(False, convert_unit(ret.unit, target))
    else:
        return RetVal(ret.is_none, ret.unit)
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

Instance astropy__astropy-7336, nagini. Frozen spec: finalize_return(ret, target). The postcondition FULLY pins BOTH observed fields on BOTH branches: non-genuine target (unspecified OR no-value) => Result().is_none==ret.is_none AND Result().unit==ret.unit (pass-through); genuine target => (not Result().is_none) AND Result().unit==convert_unit(ret.unit,target). convert_unit is @Pure with precondition Requires(is_genuine_target(target)) and Ensures(Result()==target); this precondition is what forces the no-value (-> None) pass-through — an impl that tries to convert on TARGET_NOVALUE() violates the callee precondition and fails to verify.

 Project root, SBU_BENCHMARK_DIR=benchmark-verified, python python. 9 distinct same-spec wrong impls built by editing ONLY the impl region (axioms/@Pure/Requires/Ensures byte-identical; all 9 confirmed SAME by `adversary same-spec`). Verifications run concurrently in batches of 3 (JVM+Z3 each) via `adversary weakness`.

Attacks & observed results (command per file: `python -m swebench_unified.adversary weakness nagini astropy__astropy-7336 <path>`):
- atk_1 (PREPATCH BUG: `if target != TARGET_UNSPECIFIED(): convert`): exit 2, does-not-verify. Prepatch bug reproduced: converts on TARGET_NOVALUE(), violating convert_unit's is_genuine_target precondition. matches model_prepatch.py / G-DIFF.
- atk_2 (control-flow: swapped branches): exit 2, does-not-verify.
- atk_3 (genuine branch keeps source unit `RetVal(False, ret.unit)`): exit 2, does-not-verify (violates Result().unit==convert_unit).
- atk_4 (non-genuine branch forces is_none=False): exit 2, does-not-verify (violates Result().is_none==ret.is_none on no-value pass-through).
- atk_5 (control-flow-effect: `while True: pass` before correct return / non-termination): exit 2, does-not-verify (MustTerminate).
- atk_6 (boundary/partial-domain guard `if target >= 0`): exit 2, does-not-verify (mis-partitions sentinels vs genuine).
- atk_7 (ungrounded-oracle echo: non-genuine returns `RetVal(ret.is_none, NO_UNIT())`): exit 2, does-not-verify (violates Result().unit==ret.unit for genuine-unit pass-through under -> None).
- atk_8 (off-by-one wrong unit `convert_unit(...)+1`): exit 2, does-not-verify.
- atk_9 (MIRROR bug `if target != TARGET_NOVALUE(): convert`): exit 2, does-not-verify (converts on TARGET_UNSPECIFIED and, worse, tries convert on NOVALUE path excluded — actually converts on genuine+unspecified; fails Result().unit==ret.unit on unspecified pass-through and callee precondition).

Every attack returned NOT-A-COUNTEREXAMPLE (exit 2 = shares spec but does NOT verify). NO CANDIDATE emerged, therefore no faithful refined patch needed materialization/resolve — the verify=>correct implication is not falsifiable here because the spec admits no verifying wrong impl in this attack suite.

Positive control: `adversary verify nagini astropy__astropy-7336 pos_control.py` => VERIFIED in 10.6s (exit 0). So the spec is not vacuous/over-tight: the correct impl verifies while all 9 wrong impls are rejected.

Refinement audit (refinement.md): legs A1(R), A2(R), A3(I+R), A4(A-reference), A5(R) — no kind-3 leg. Section C explicitly claims no consumed axiom and no unexpressible-changed-op; confirmed: axioms region of model.py is empty. The two A-reference correspondences are checked by axiom_check.py against the REAL astropy callees: (1) convert_unit==Quantity.to via `q.to(target).unit==target` over 8 unit pairs; (2) finalize_return decision==real quantity_input wrapper via three decorated functions (genuine->deg convert; `-> None`->pass-through incl. the F2P test_return_annotation_none; unspecified->pass-through). The A-reference callee bindings (mapping.md §3.1/§3.2, quantity.py:821, decorators.py:223-226 post-fix) match the deep model. Discriminating content (`None in (empty, None)` <=> is_genuine_target(TARGET_NOVALUE())==False) is faithfully forced by convert_unit's precondition. Correspondence holds.

Verdict SOUND: >=5 (9) distinct same-spec attacks run, none is a verifying-wrong-impl, so none can break verify=>correct; positive control verifies; refinement legs are all R/A-reference/I with sound callee correspondence.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Worktree is at base_commit (732d89c2) with the gold patch applied: guard is `return_annotation not in (inspect.Signature.empty, None)` at decorators.py:223. Confirmed real behavior empirically with astropy: (1) genuine target ->u.deg with compatible quantity converts to .unit==deg; (2) -> None returning None passes through as None (F2P test_return_annotation_none); (3) no annotation passes through unchanged; all three match finalize_return exactly under the R-refinement (annotation<->int code, return_<->RetVal). model.py VERIFIES in Nagini (10.79s). model_prepatch.py encodes the buggy pre-fix guard (only excludes TARGET_UNSPECIFIED) and fails on target==TARGET_NOVALUE via convert_unit's Requires(is_genuine_target) — correct G-DIFF discrimination. axiom_check.py (G-AX) validates convert_unit==Quantity.to and the decision==real wrapper only on the defined/tested domain, consistent with the deep-model abstraction. The spec is neither too strong nor drifting on any tested/contract input; the coarsening of .to to a total operation over abstract int units matches the scoped refinement claim and cannot let a verifying impl fail resolution. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (rep.passed=True, zero hard_failures) on the projected spec view. Verified independently: (1) no diff markers (@@/+++/---/diff --git) in the spec view; (2) no verbatim gold-patch changed lines reproduced (len>=8 normalized) in view; (3) patched file path 'astropy/units/decorators.py' and its dotted module path appear only in the audit docs (mapping.md/refinement.md), NOT in the consumer spec view (model.py docstring/comments/code); (4) the only distinctive changed symbol is 'wrapper', which is embedded in no spec-view identifier and named in no spec-view comment — the model abstracts to finalize_return/RetVal/TARGET_UNSPECIFIED/TARGET_NOVALUE/convert_unit/is_genuine_target; (5) no narration terms (bug/fix/patched/wrong/etc.) in comments or docstring.

Semantic (gold-reconstruction) check: the discriminating content of the gold edit — a '-> None' return annotation must be treated like the unspecified sentinel (pass through / no unit conversion) rather than triggering .to() — is ALREADY fully public in the problem_statement itself: the title ('fails for constructors with type hinted return value -> None'), the traceback ('None has no attribute to'), AND explicitly the 'Possible fix' section: 'Maybe the decorator could explicitly check whether None is returned and then omit the unit check.' The spec view discloses nothing about the edit beyond what the solver already sees in problem_statement; it merely states the desired behaviour in abstracted terms (int sentinel codes, a two-field RetVal record). No line localizes the edit beyond the public task. Bundle is not relaxed (no RELAXED_LEAKAGE.md / relaxed_leakage flag), and none needed.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
