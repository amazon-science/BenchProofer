# P2 adversarial audit — scikit-learn__scikit-learn-11310

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -45,7 +45,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -88,7 +87,6 @@
     # later reading is never earlier than the earlier one (timer monotonicity,
     # modelled by `clock_after`): `end >= start`.
     Requires(end >= start)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # (1) the duration is reported exactly when the final fit is performed, and
@@ -105,9 +103,7 @@
     # impl-start
     result = None  # type: Optional[float]
     if do_final_fit:
-        # the elapsed interval is the later reading minus the earlier one; the
-        # readings are ordered (end >= start), so the interval is a non-negative
-        # real value.
-        result = elapsed_between(start, end)
+        # ... the final fit happens here (opaque work) ... but no duration recorded
+        pass
     return result
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -45,7 +45,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -88,7 +87,6 @@
     # later reading is never earlier than the earlier one (timer monotonicity,
     # modelled by `clock_after`): `end >= start`.
     Requires(end >= start)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # (1) the duration is reported exactly when the final fit is performed, and
@@ -103,11 +101,6 @@
     Ensures(Implies(Result() is not None, Result() == elapsed_between(start, end)))
     # post-conditions-end
     # impl-start
-    result = None  # type: Optional[float]
-    if do_final_fit:
-        # the elapsed interval is the later reading minus the earlier one; the
-        # readings are ordered (end >= start), so the interval is a non-negative
-        # real value.
-        result = elapsed_between(start, end)
+    result = 0.0  # type: Optional[float]
     return result
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -45,7 +45,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -88,7 +87,6 @@
     # later reading is never earlier than the earlier one (timer monotonicity,
     # modelled by `clock_after`): `end >= start`.
     Requires(end >= start)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # (1) the duration is reported exactly when the final fit is performed, and
@@ -103,11 +101,6 @@
     Ensures(Implies(Result() is not None, Result() == elapsed_between(start, end)))
     # post-conditions-end
     # impl-start
-    result = None  # type: Optional[float]
-    if do_final_fit:
-        # the elapsed interval is the later reading minus the earlier one; the
-        # readings are ordered (end >= start), so the interval is a non-negative
-        # real value.
-        result = elapsed_between(start, end)
+    result = elapsed_between(start, end)  # type: Optional[float]
     return result
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -45,7 +45,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -88,7 +87,6 @@
     # later reading is never earlier than the earlier one (timer monotonicity,
     # modelled by `clock_after`): `end >= start`.
     Requires(end >= start)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # (1) the duration is reported exactly when the final fit is performed, and
@@ -105,9 +103,6 @@
     # impl-start
     result = None  # type: Optional[float]
     if do_final_fit:
-        # the elapsed interval is the later reading minus the earlier one; the
-        # readings are ordered (end >= start), so the interval is a non-negative
-        # real value.
-        result = elapsed_between(start, end)
+        result = elapsed_between(end, start)
     return result
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -45,7 +45,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -88,7 +87,6 @@
     # later reading is never earlier than the earlier one (timer monotonicity,
     # modelled by `clock_after`): `end >= start`.
     Requires(end >= start)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # (1) the duration is reported exactly when the final fit is performed, and
@@ -105,9 +103,7 @@
     # impl-start
     result = None  # type: Optional[float]
     if do_final_fit:
-        # the elapsed interval is the later reading minus the earlier one; the
-        # readings are ordered (end >= start), so the interval is a non-negative
-        # real value.
-        result = elapsed_between(start, end)
+        if end > start:
+            result = elapsed_between(start, end)
     return result
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -45,7 +45,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -88,7 +87,6 @@
     # later reading is never earlier than the earlier one (timer monotonicity,
     # modelled by `clock_after`): `end >= start`.
     Requires(end >= start)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # (1) the duration is reported exactly when the final fit is performed, and
@@ -105,9 +103,6 @@
     # impl-start
     result = None  # type: Optional[float]
     if do_final_fit:
-        # the elapsed interval is the later reading minus the earlier one; the
-        # readings are ordered (end >= start), so the interval is a non-negative
-        # real value.
-        result = elapsed_between(start, end)
+        result = elapsed_between(start, clock_after(end))
     return result
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -45,7 +45,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -88,7 +87,6 @@
     # later reading is never earlier than the earlier one (timer monotonicity,
     # modelled by `clock_after`): `end >= start`.
     Requires(end >= start)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # (1) the duration is reported exactly when the final fit is performed, and
@@ -105,9 +103,6 @@
     # impl-start
     result = None  # type: Optional[float]
     if do_final_fit:
-        # the elapsed interval is the later reading minus the earlier one; the
-        # readings are ordered (end >= start), so the interval is a non-negative
-        # real value.
-        result = elapsed_between(start, end)
+        result = end - start
     return result
     # impl-end
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -45,7 +45,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -88,7 +87,6 @@
     # later reading is never earlier than the earlier one (timer monotonicity,
     # modelled by `clock_after`): `end >= start`.
     Requires(end >= start)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # (1) the duration is reported exactly when the final fit is performed, and
@@ -105,9 +103,7 @@
     # impl-start
     result = None  # type: Optional[float]
     if do_final_fit:
-        # the elapsed interval is the later reading minus the earlier one; the
-        # readings are ordered (end >= start), so the interval is a non-negative
-        # real value.
         result = elapsed_between(start, end)
+        result = None
     return result
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for scikit-learn__scikit-learn-11310.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A search procedure, after selecting the best configuration, may fit the chosen
  model once more on the whole data. When (and only when) this final fit is
  performed, the procedure must report the wall-clock duration of that final fit
  as a single real-valued measurement, obtained by reading the clock immediately
  before the fit begins and immediately after it ends and reporting the elapsed
  interval between the two readings (later reading minus earlier reading).

  The two readings are modelled as the inputs `start` (the reading taken before
  the fit) and `end` (the reading taken after it). Because wall-clock time does
  not run backwards, the later reading is never earlier than the earlier one;
  this is the precondition `end >= start`.

  The guarantees the issue demands:

    (1) the reported duration is present exactly when the final fit is performed
        (and is the absent marker, None, when it is not performed); and

    (2) whenever it is present it is precisely the elapsed real-valued interval
        between the two readings (the later reading minus the earlier reading) —
        a genuine real-valued measurement, not an arbitrary stand-in. As a
        consequence it is a non-negative real number, since the reading taken
        after the fit is never earlier than the reading taken before it,
        including the boundary where no measurable time passed.

Clock readings and the reported duration are interpreted real numbers (verified
with `--float-encoding=real`); whether the final fit happens is a bool, and the
absent marker is None (`Optional[float]`).

Two unchanged operations are axiomatized as `@Pure @ContractOnly` callees:

  * the wall-clock reading — the property modelled is its monotonicity across two
    sequential calls: a reading taken after a reference instant is never earlier
    than that instant (this is what justifies the precondition `end >= start`);
    and
  * the elapsed-interval (the difference of two readings) — the property
    consumed by the proof is that the difference of an ordered pair (the later
    minus the earlier reading) is a non-negative real value; the reported
    duration is pinned to exactly this real-valued difference.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *


# axioms-start
@Pure
@ContractOnly
def clock_after(reference: float) -> float:
    """Wall-clock reading (the unchanged stdlib timer) taken at or after a
    reference instant. The property modelled is monotonicity: wall-clock time
    does not run backwards, so a reading taken after `reference` is never earlier
    than it. This is what justifies the `end >= start` ordering of the two
    bracketed readings (the inputs of `recorded_refit_duration`).
    Provenance + executable soundness check: mapping.md / axiom_check.py.
    """
    Ensures(Result() >= reference)


@Pure
@ContractOnly
def elapsed_between(earlier: float, later: float) -> float:
    """The elapsed real-valued interval between two ordered clock readings (the
    later one minus the earlier one). The property the proof relies on is that,
    for an ordered pair, this difference is a non-negative real value. Weakest
    sound contract on real subtraction of two ordered readings.
    Provenance + executable soundness check: mapping.md / axiom_check.py.
    """
    Requires(later >= earlier)
    Ensures(Result() >= 0.0)
# axioms-end


# pure-start
# (no auxiliary pure spec functions are required for this behaviour.)
# pure-end


def recorded_refit_duration(do_final_fit: bool, start: float, end: float) -> Optional[float]:
    # pre-conditions-start
    # `start` is the reading taken before the final fit may begin and `end` the
    # reading taken after it ends. Wall-clock time does not run backwards, so the
    # later reading is never earlier than the earlier one (timer monotonicity,
    # modelled by `clock_after`): `end >= start`.
    Requires(end >= start)
    # pre-conditions-end
    # post-conditions-start
    # (1) the duration is reported exactly when the final fit is performed, and
    # is the absent marker otherwise.
    Ensures(do_final_fit == (Result() is not None))
    # (2) whenever a duration is reported it is precisely the elapsed real-valued
    # interval between the two readings (the later reading minus the earlier
    # one). This pins the result to the genuine real-valued measurement, so it
    # cannot be discharged by an arbitrary non-real or constant stand-in; as a
    # consequence it is a non-negative real number (including a zero-length
    # interval).
    Ensures(Implies(Result() is not None, Result() == elapsed_between(start, end)))
    # post-conditions-end
    # impl-start
    result = None  # type: Optional[float]
    if do_final_fit:
        # the elapsed interval is the later reading minus the earlier one; the
        # readings are ordered (end >= start), so the interval is a non-negative
        # real value.
        result = elapsed_between(start, end)
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity adversarial audit for scikit-learn__scikit-learn-11310 (nagini). Spec models recorded_refit_duration(do_final_fit, start, end)->Optional[float] with Requires(end>=start), post(1) Ensures(do_final_fit == (Result() is not None)) [biconditional], post(2) Ensures(Implies(Result() is not None, Result()==elapsed_between(start,end))) [value pinned to the @Pure @ContractOnly callee]. float_encoding=real from meta.

TOOLING/ENV: project root, PY=python, SBU_BENCHMARK_DIR=benchmark-verified. Note the task-prompt paths (and patch.diff inside nagini/) were stale; actual root is /fsx and patch.diff sits at the instance root.

POSITIVE CONTROL: gold model.py -> `python -m swebench_unified.adversary weakness nagini scikit-learn__scikit-learn-11310 .../positive_control.py` => CANDIDATE-COUNTEREXAMPLE (shares spec AND verifies, 12.2s), exit 0. same-spec: SAME. (Gold verifies AND resolves, so not a weakness.)

### ATTACKS (each cmd: `... adversary weakness nagini scikit-learn__scikit-learn-11310 <path>`; all same-spec=SAME confirmed):
- atk_1 (PREPATCH BUG: `if do_final_fit: pass`, result stays None): NOT-A-COUNTEREXAMPLE, exit 2. verify => FAILED 12.3s, atk_1.py:94 Postcondition (do_final_fit == (Result() is not None)) might not hold. Prepatch bug reproduced.
- atk_2 (ungrounded const `result=0.0` unconditional): NOT-A-COUNTEREXAMPLE, exit 2 (fails post(1) when not refit).
- atk_3 (control-flow-effect: always record, ignore guard): NOT-A-COUNTEREXAMPLE, exit 2. verify => FAILED 11.9s, :94 post(1) fails.
- atk_4 (boundary/arg-swap: elapsed_between(end,start)): NOT-A-COUNTEREXAMPLE, exit 2 (Requires later>=earlier unprovable + wrong value).
- atk_5 (partial-domain: only record when end>start, misses end==start): NOT-A-COUNTEREXAMPLE, exit 2 (fails post(1) at zero-length boundary).
- atk_6 (ungrounded-oracle echo: elapsed_between(start, clock_after(end))): NOT-A-COUNTEREXAMPLE, exit 2 (value != elapsed_between(start,end)).
- atk_7 (uninterpreted-float probe: `result = end - start` real subtraction instead of the callee): NOT-A-COUNTEREXAMPLE, exit 2. verify => FAILED 11.2s, atk_7.py:101 Postcondition Implies((Result() is not None),(Result()==elapsed_between(start,end))) might not hold. CONFIRMS refinement.md/mapping.md claim that Nagini 1.2.0 leaves float subtraction uninterpreted even under real encoding, so post(2) is discharged ONLY by the exact elapsed_between(start,end) call -> grounding is real, not an echoable oracle.
- atk_8 (control-flow-effect: compute elapsed then clobber result=None): NOT-A-COUNTEREXAMPLE, exit 2 (fails post(1) when do_final_fit true).

RESULT: 0 of 8 wrong impls verified => NO verifying-wrong-impl CANDIDATE => no faithful refined patch to materialize/resolve-run (nothing to break the spec). All 8 are genuine spec rejections (real Postcondition errors, not timeout/infra; verify_completed).

A-LEG / grounding audit: axiom_check.py => G-AX OK (clock_after: time.time() monotone over 200000 pairs, 0 violations, A-reference; elapsed_between: later-earlier>=0 over 2007 boundary + 200000 fuzz pairs, A-consumed). Correspondence holds: clock_after<->time.time() (A-reference, Ensures NOT consumed — readings are inputs), elapsed_between<->refit_end_time-refit_start_time real subtraction (A-consumed). refinement.md legs A0..A4 all R / A-consumed / A-reference / I; §C's no-kind-3 claim corroborated — the changed behaviour (recording bracketed duration when refit runs) is modeled deeply in the impl, only unchanged builtins are axiomatized. atk_7 empirically defeats the 'axiom echoes an oracle' concern: verify => impl must actually invoke the modeled subtraction on the genuine input carriers.

VERDICT: SOUND — >=5 (8) distinct wrong impls run, prepatch reproduced, none is a verifying counterexample; A-legs grounded and model<->patch correspondence holds. verify does NOT admit an incorrect impl for this spec.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for scikit-learn__scikit-learn-11310.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A search procedure, after selecting the best configuration, may fit the chosen
  model once more on the whole data. When (and only when) this final fit is
  performed, the procedure must report the wall-clock duration of that final fit
  as a single real-valued measurement, obtained by reading the clock immediately
  before the fit begins and immediately after it ends and reporting the elapsed
  interval between the two readings (later reading minus earlier reading).

  The two readings are modelled as the inputs `start` (the reading taken before
  the fit) and `end` (the reading taken after it). Because wall-clock time does
  not run backwards, the later reading is never earlier than the earlier one;
  this is the precondition `end >= start`.

  The guarantees the issue demands:

    (1) the reported duration is present exactly when the final fit is performed
        (and is the absent marker, None, when it is not performed); and

    (2) whenever it is present it is precisely the elapsed real-valued interval
        between the two readings (the later reading minus the earlier reading) —
        a genuine real-valued measurement, not an arbitrary stand-in. As a
        consequence it is a non-negative real number, since the reading taken
        after the fit is never earlier than the reading taken before it,
        including the boundary where no measurable time passed.

Clock readings and the reported duration are interpreted real numbers (verified
with `--float-encoding=real`); whether the final fit happens is a bool, and the
absent marker is None (`Optional[float]`).

Two unchanged operations are axiomatized as `@Pure @ContractOnly` callees:

  * the wall-clock reading — the property modelled is its monotonicity across two
    sequential calls: a reading taken after a reference instant is never earlier
    than that instant (this is what justifies the precondition `end >= start`);
    and
  * the elapsed-interval (the difference of two readings) — the property
    consumed by the proof is that the difference of an ordered pair (the later
    minus the earlier reading) is a non-negative real value; the reported
    duration is pinned to exactly this real-valued difference.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *


# axioms-start
@Pure
@ContractOnly
def clock_after(reference: float) -> float:
    """Wall-clock reading (the unchanged stdlib timer) taken at or after a
    reference instant. The property modelled is monotonicity: wall-clock time
    does not run backwards, so a reading taken after `reference` is never earlier
    than it. This is what justifies the `end >= start` ordering of the two
    bracketed readings (the inputs of `recorded_refit_duration`).
    Provenance + executable soundness check: mapping.md / axiom_check.py.
    """
    Ensures(Result() >= reference)


@Pure
@ContractOnly
def elapsed_between(earlier: float, later: float) -> float:
    """The elapsed real-valued interval between two ordered clock readings (the
    later one minus the earlier one). The property the proof relies on is that,
    for an ordered pair, this difference is a non-negative real value. Weakest
    sound contract on real subtraction of two ordered readings.
    Provenance + executable soundness check: mapping.md / axiom_check.py.
    """
    Requires(later >= earlier)
    Ensures(Result() >= 0.0)
# axioms-end


# pure-start
# (no auxiliary pure spec functions are required for this behaviour.)
# pure-end


def recorded_refit_duration(do_final_fit: bool, start: float, end: float) -> Optional[float]:
    # pre-conditions-start
    # `start` is the reading taken before the final fit may begin and `end` the
    # reading taken after it ends. Wall-clock time does not run backwards, so the
    # later reading is never earlier than the earlier one (timer monotonicity,
    # modelled by `clock_after`): `end >= start`.
    Requires(end >= start)
    # pre-conditions-end
    # post-conditions-start
    # (1) the duration is reported exactly when the final fit is performed, and
    # is the absent marker otherwise.
    Ensures(do_final_fit == (Result() is not None))
    # (2) whenever a duration is reported it is precisely the elapsed real-valued
    # interval between the two readings (the later reading minus the earlier
    # one). This pins the result to the genuine real-valued measurement, so it
    # cannot be discharged by an arbitrary non-real or constant stand-in; as a
    # consequence it is a non-negative real number (including a zero-length
    # interval).
    Ensures(Implies(Result() is not None, Result() == elapsed_between(start, end)))
    # post-conditions-end
    # impl-start
    result = None  # type: Optional[float]
    if do_final_fit:
        # the elapsed interval is the later reading minus the earlier one; the
        # readings are ordered (end >= start), so the interval is a non-negative
        # real value.
        result = elapsed_between(start, end)
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity adversarial audit for scikit-learn__scikit-learn-11310 (nagini). Spec models recorded_refit_duration(do_final_fit, start, end)->Optional[float] with Requires(end>=start), post(1) Ensures(do_final_fit == (Result() is not None)) [biconditional], post(2) Ensures(Implies(Result() is not None, Result()==elapsed_between(start,end))) [value pinned to the @Pure @ContractOnly callee]. float_encoding=real from meta.

TOOLING/ENV: project root, PY=python, SBU_BENCHMARK_DIR=benchmark-verified. Note the task-prompt paths (and patch.diff inside nagini/) were stale; actual root is /fsx and patch.diff sits at the instance root.

POSITIVE CONTROL: gold model.py -> `python -m swebench_unified.adversary weakness nagini scikit-learn__scikit-learn-11310 .../positive_control.py` => CANDIDATE-COUNTEREXAMPLE (shares spec AND verifies, 12.2s), exit 0. same-spec: SAME. (Gold verifies AND resolves, so not a weakness.)

### ATTACKS (each cmd: `... adversary weakness nagini scikit-learn__scikit-learn-11310 <path>`; all same-spec=SAME confirmed):
- atk_1 (PREPATCH BUG: `if do_final_fit: pass`, result stays None): NOT-A-COUNTEREXAMPLE, exit 2. verify => FAILED 12.3s, atk_1.py:94 Postcondition (do_final_fit == (Result() is not None)) might not hold. Prepatch bug reproduced.
- atk_2 (ungrounded const `result=0.0` unconditional): NOT-A-COUNTEREXAMPLE, exit 2 (fails post(1) when not refit).
- atk_3 (control-flow-effect: always record, ignore guard): NOT-A-COUNTEREXAMPLE, exit 2. verify => FAILED 11.9s, :94 post(1) fails.
- atk_4 (boundary/arg-swap: elapsed_between(end,start)): NOT-A-COUNTEREXAMPLE, exit 2 (Requires later>=earlier unprovable + wrong value).
- atk_5 (partial-domain: only record when end>start, misses end==start): NOT-A-COUNTEREXAMPLE, exit 2 (fails post(1) at zero-length boundary).
- atk_6 (ungrounded-oracle echo: elapsed_between(start, clock_after(end))): NOT-A-COUNTEREXAMPLE, exit 2 (value != elapsed_between(start,end)).
- atk_7 (uninterpreted-float probe: `result = end - start` real subtraction instead of the callee): NOT-A-COUNTEREXAMPLE, exit 2. verify => FAILED 11.2s, atk_7.py:101 Postcondition Implies((Result() is not None),(Result()==elapsed_between(start,end))) might not hold. CONFIRMS refinement.md/mapping.md claim that Nagini 1.2.0 leaves float subtraction uninterpreted even under real encoding, so post(2) is discharged ONLY by the exact elapsed_between(start,end) call -> grounding is real, not an echoable oracle.
- atk_8 (control-flow-effect: compute elapsed then clobber result=None): NOT-A-COUNTEREXAMPLE, exit 2 (fails post(1) when do_final_fit true).

RESULT: 0 of 8 wrong impls verified => NO verifying-wrong-impl CANDIDATE => no faithful refined patch to materialize/resolve-run (nothing to break the spec). All 8 are genuine spec rejections (real Postcondition errors, not timeout/infra; verify_completed).

A-LEG / grounding audit: axiom_check.py => G-AX OK (clock_after: time.time() monotone over 200000 pairs, 0 violations, A-reference; elapsed_between: later-earlier>=0 over 2007 boundary + 200000 fuzz pairs, A-consumed). Correspondence holds: clock_after<->time.time() (A-reference, Ensures NOT consumed — readings are inputs), elapsed_between<->refit_end_time-refit_start_time real subtraction (A-consumed). refinement.md legs A0..A4 all R / A-consumed / A-reference / I; §C's no-kind-3 claim corroborated — the changed behaviour (recording bracketed duration when refit runs) is modeled deeply in the impl, only unchanged builtins are axiomatized. atk_7 empirically defeats the 'axiom echoes an oracle' concern: verify => impl must actually invoke the modeled subtraction on the genuine input carriers.

VERDICT: SOUND — >=5 (8) distinct wrong impls run, prepatch reproduced, none is a verifying counterexample; A-legs grounded and model<->patch correspondence holds. verify does NOT admit an incorrect impl for this spec.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Modeled function recorded_refit_duration(do_final_fit, start, end) -> Optional[float] with Requires(end>=start), Ensures(do_final_fit==(Result() is not None)), Ensures(Implies(Result() is not None, Result()==elapsed_between(start,end))). Models the refit-timing branch of BaseSearchCV.fit (sklearn/model_selection/_search.py, PR #11310). Gold patch adds refit_start_time=time.time() before the fit, refit_end_time=time.time() after, self.refit_time_=refit_end_time-refit_start_time inside `if self.refit:`; attribute unset when refit falsy.

Machine facts: gold model.py verifies with --float-encoding=real (exit 0, 11.8s); same-spec on gold copy = SAME (spec region byte-identical); model_prepatch (bare pass in the if body) fails post(1) do_final_fit==(Result() is not None), so the modeled diff is genuine.

Spec-vs-real on modeled domain: post(1) biconditional matches gold exactly (attribute present iff self.refit truthy; absent->None, matching P2P test_no_refit). post(2) pins Result to elapsed_between(start,end), a @Pure @ContractOnly model of the REAL builtin subtraction end-start (Requires discharged by end>=start) — exactly the gold assignment refit_end_time-refit_start_time, not an oracle. The Requires(end>=start) precondition is a DOMAIN RESTRICTION (spec-too-weak flavor, out of this gate's scope) reflecting timer monotonicity validated by axiom_check.py over 200k real time.time() pairs; the real code would itself violate the F2P `>= 0` assertion on a backwards clock, so excluding that region is a faithful modeling boundary, not drift/over-strength. No in-domain input yields a modeled result diverging from gold behavior. The spec is not too strong and does not drift. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (leakage.screen -> passed=True, hard_failures=[]); no relaxed_leakage flag, meta G-LEAK status=pass. Semantic review of the full spec_view confirms no leak of the gold edit beyond the public problem_statement.

Public problem_statement already discloses: (a) refitting the best model on the full data after grid/random search; (b) desire for an attribute giving 'the time it took to refit the best model'; (c) the timing-by-subtraction mechanism ('time the whole search procedure and subtract the time it took to fit the single folds'). The gold patch adds `import time`, brackets the refit with `refit_start_time = time.time()` / `refit_end_time = time.time()`, and sets `self.refit_time_ = refit_end_time - refit_start_time`, plus two docstring Attributes entries.

The spec view describes ONLY this publicly-requested behavior in abstract terms: a final fit on the whole data, reporting its wall-clock duration as (later reading - earlier reading), present exactly when the final fit occurs. It does NOT reveal any gold-edit specifics beyond the public statement:
- No patched file path (sklearn/model_selection/_search.py), no diff markers, no module path.
- No verbatim patched repo symbols: uses abstract identifiers recorded_refit_duration / clock_after / elapsed_between; never names refit_time_, time.time(), refit_start_time/refit_end_time, GridSearchCV, RandomizedSearchCV, or _store. (Changed symbols GridSearchCV/RandomizedSearchCV/store do not appear in the spec view.)
- No bug/fix/patch narration; framed as 'desired behaviour, not as an edit'.

The clock-reading/subtraction framing does not exceed the problem_statement, which itself invokes timing and subtraction; it is the obvious mechanism for 'time it took to refit' and localizes no edit site. The two @ContractOnly axioms model unchanged stdlib operations (clock monotonicity, ordered-difference non-negativity), not the behaviour under change. Spec view is a faithful restatement of the public feature request; NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
