# P2 adversarial audit — django__django-16429

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -38,13 +38,11 @@
 """
 from typing import Optional, Tuple
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Moment:
     def __init__(self, year: int, month: int, day: int, hour: int,
                  minute: int, second: int, tz: Optional[int]) -> None:
-        Requires(MustTerminate(2))
         Ensures(Acc(self.year) and self.year == year)        # type: ignore
         Ensures(Acc(self.month) and self.month == month)     # type: ignore
         Ensures(Acc(self.day) and self.day == day)           # type: ignore
@@ -109,7 +107,6 @@
     Requires(Acc(now.tz, 1 / 2))
     Requires(Acc(pivot.tz, 1 / 2))
     Requires(same_disposition(now.tz, pivot.tz))
-    Requires(MustTerminate(6))
     Ensures(Acc(now.tz, 1 / 2))
     Ensures(Acc(pivot.tz, 1 / 2))
     Ensures(Result() == moment_span(now, pivot))
@@ -128,7 +125,6 @@
     # its time-zone disposition (offset-aware iff `d` is).
     Requires(Acc(now.tz, 1 / 2))
     Requires(same_disposition(now.tz, d.tz))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(d.year, 1 / 2) and Acc(d.month, 1 / 2) and Acc(d.day, 1 / 2))
@@ -156,18 +152,10 @@
     # post-conditions-end
     # impl-start
     pivot = Moment(
-        pivot_year,
-        pivot_month,
-        pivot_day,
-        d.hour,
-        d.minute,
-        d.second,
-        d.tz,
+        pivot_year, pivot_month, pivot_day,
+        d.hour, d.minute, d.second,
+        None,
     )
-    # The leftover span: requires now and pivot share a disposition. This call
-    # is provable only because pivot carries d.tz and now agrees with d; it
-    # measures the ordered difference of the current moment and the reference
-    # moment, which is returned alongside the constructed reference moment.
     remaining = well_defined_diff(now, pivot)
     return pivot, remaining
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -38,13 +38,11 @@
 """
 from typing import Optional, Tuple
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Moment:
     def __init__(self, year: int, month: int, day: int, hour: int,
                  minute: int, second: int, tz: Optional[int]) -> None:
-        Requires(MustTerminate(2))
         Ensures(Acc(self.year) and self.year == year)        # type: ignore
         Ensures(Acc(self.month) and self.month == month)     # type: ignore
         Ensures(Acc(self.day) and self.day == day)           # type: ignore
@@ -109,7 +107,6 @@
     Requires(Acc(now.tz, 1 / 2))
     Requires(Acc(pivot.tz, 1 / 2))
     Requires(same_disposition(now.tz, pivot.tz))
-    Requires(MustTerminate(6))
     Ensures(Acc(now.tz, 1 / 2))
     Ensures(Acc(pivot.tz, 1 / 2))
     Ensures(Result() == moment_span(now, pivot))
@@ -128,7 +125,6 @@
     # its time-zone disposition (offset-aware iff `d` is).
     Requires(Acc(now.tz, 1 / 2))
     Requires(same_disposition(now.tz, d.tz))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(d.year, 1 / 2) and Acc(d.month, 1 / 2) and Acc(d.day, 1 / 2))
@@ -156,18 +152,10 @@
     # post-conditions-end
     # impl-start
     pivot = Moment(
-        pivot_year,
-        pivot_month,
-        pivot_day,
-        d.hour,
-        d.minute,
-        d.second,
+        pivot_year, pivot_month, pivot_day,
+        d.hour, d.minute, d.second,
         d.tz,
     )
-    # The leftover span: requires now and pivot share a disposition. This call
-    # is provable only because pivot carries d.tz and now agrees with d; it
-    # measures the ordered difference of the current moment and the reference
-    # moment, which is returned alongside the constructed reference moment.
-    remaining = well_defined_diff(now, pivot)
+    remaining = well_defined_diff(pivot, now)
     return pivot, remaining
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -38,13 +38,11 @@
 """
 from typing import Optional, Tuple
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Moment:
     def __init__(self, year: int, month: int, day: int, hour: int,
                  minute: int, second: int, tz: Optional[int]) -> None:
-        Requires(MustTerminate(2))
         Ensures(Acc(self.year) and self.year == year)        # type: ignore
         Ensures(Acc(self.month) and self.month == month)     # type: ignore
         Ensures(Acc(self.day) and self.day == day)           # type: ignore
@@ -109,7 +107,6 @@
     Requires(Acc(now.tz, 1 / 2))
     Requires(Acc(pivot.tz, 1 / 2))
     Requires(same_disposition(now.tz, pivot.tz))
-    Requires(MustTerminate(6))
     Ensures(Acc(now.tz, 1 / 2))
     Ensures(Acc(pivot.tz, 1 / 2))
     Ensures(Result() == moment_span(now, pivot))
@@ -128,7 +125,6 @@
     # its time-zone disposition (offset-aware iff `d` is).
     Requires(Acc(now.tz, 1 / 2))
     Requires(same_disposition(now.tz, d.tz))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(d.year, 1 / 2) and Acc(d.month, 1 / 2) and Acc(d.day, 1 / 2))
@@ -156,18 +152,10 @@
     # post-conditions-end
     # impl-start
     pivot = Moment(
-        pivot_year,
-        pivot_month,
-        pivot_day,
-        d.hour,
-        d.minute,
-        d.second,
+        pivot_year, pivot_month, pivot_day,
+        d.hour, d.minute, d.second,
         d.tz,
     )
-    # The leftover span: requires now and pivot share a disposition. This call
-    # is provable only because pivot carries d.tz and now agrees with d; it
-    # measures the ordered difference of the current moment and the reference
-    # moment, which is returned alongside the constructed reference moment.
-    remaining = well_defined_diff(now, pivot)
+    remaining = well_defined_diff(now, d)
     return pivot, remaining
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -38,13 +38,11 @@
 """
 from typing import Optional, Tuple
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Moment:
     def __init__(self, year: int, month: int, day: int, hour: int,
                  minute: int, second: int, tz: Optional[int]) -> None:
-        Requires(MustTerminate(2))
         Ensures(Acc(self.year) and self.year == year)        # type: ignore
         Ensures(Acc(self.month) and self.month == month)     # type: ignore
         Ensures(Acc(self.day) and self.day == day)           # type: ignore
@@ -109,7 +107,6 @@
     Requires(Acc(now.tz, 1 / 2))
     Requires(Acc(pivot.tz, 1 / 2))
     Requires(same_disposition(now.tz, pivot.tz))
-    Requires(MustTerminate(6))
     Ensures(Acc(now.tz, 1 / 2))
     Ensures(Acc(pivot.tz, 1 / 2))
     Ensures(Result() == moment_span(now, pivot))
@@ -128,7 +125,6 @@
     # its time-zone disposition (offset-aware iff `d` is).
     Requires(Acc(now.tz, 1 / 2))
     Requires(same_disposition(now.tz, d.tz))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(d.year, 1 / 2) and Acc(d.month, 1 / 2) and Acc(d.day, 1 / 2))
@@ -156,18 +152,10 @@
     # post-conditions-end
     # impl-start
     pivot = Moment(
-        pivot_year,
-        pivot_month,
-        pivot_day,
-        d.hour,
-        d.minute,
-        d.second,
+        pivot_year, pivot_month, pivot_day,
+        d.hour, d.minute, d.second,
         d.tz,
     )
-    # The leftover span: requires now and pivot share a disposition. This call
-    # is provable only because pivot carries d.tz and now agrees with d; it
-    # measures the ordered difference of the current moment and the reference
-    # moment, which is returned alongside the constructed reference moment.
-    remaining = well_defined_diff(now, pivot)
+    remaining = 0
     return pivot, remaining
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -38,13 +38,11 @@
 """
 from typing import Optional, Tuple
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Moment:
     def __init__(self, year: int, month: int, day: int, hour: int,
                  minute: int, second: int, tz: Optional[int]) -> None:
-        Requires(MustTerminate(2))
         Ensures(Acc(self.year) and self.year == year)        # type: ignore
         Ensures(Acc(self.month) and self.month == month)     # type: ignore
         Ensures(Acc(self.day) and self.day == day)           # type: ignore
@@ -109,7 +107,6 @@
     Requires(Acc(now.tz, 1 / 2))
     Requires(Acc(pivot.tz, 1 / 2))
     Requires(same_disposition(now.tz, pivot.tz))
-    Requires(MustTerminate(6))
     Ensures(Acc(now.tz, 1 / 2))
     Ensures(Acc(pivot.tz, 1 / 2))
     Ensures(Result() == moment_span(now, pivot))
@@ -128,7 +125,6 @@
     # its time-zone disposition (offset-aware iff `d` is).
     Requires(Acc(now.tz, 1 / 2))
     Requires(same_disposition(now.tz, d.tz))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(d.year, 1 / 2) and Acc(d.month, 1 / 2) and Acc(d.day, 1 / 2))
@@ -156,18 +152,10 @@
     # post-conditions-end
     # impl-start
     pivot = Moment(
-        pivot_year,
-        pivot_month,
-        pivot_day,
-        d.hour,
-        d.minute,
-        d.second,
-        d.tz,
+        pivot_year, pivot_month, pivot_day,
+        d.hour, d.minute, d.second,
+        now.tz,
     )
-    # The leftover span: requires now and pivot share a disposition. This call
-    # is provable only because pivot carries d.tz and now agrees with d; it
-    # measures the ordered difference of the current moment and the reference
-    # moment, which is returned alongside the constructed reference moment.
     remaining = well_defined_diff(now, pivot)
     return pivot, remaining
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -38,13 +38,11 @@
 """
 from typing import Optional, Tuple
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Moment:
     def __init__(self, year: int, month: int, day: int, hour: int,
                  minute: int, second: int, tz: Optional[int]) -> None:
-        Requires(MustTerminate(2))
         Ensures(Acc(self.year) and self.year == year)        # type: ignore
         Ensures(Acc(self.month) and self.month == month)     # type: ignore
         Ensures(Acc(self.day) and self.day == day)           # type: ignore
@@ -109,7 +107,6 @@
     Requires(Acc(now.tz, 1 / 2))
     Requires(Acc(pivot.tz, 1 / 2))
     Requires(same_disposition(now.tz, pivot.tz))
-    Requires(MustTerminate(6))
     Ensures(Acc(now.tz, 1 / 2))
     Ensures(Acc(pivot.tz, 1 / 2))
     Ensures(Result() == moment_span(now, pivot))
@@ -128,7 +125,6 @@
     # its time-zone disposition (offset-aware iff `d` is).
     Requires(Acc(now.tz, 1 / 2))
     Requires(same_disposition(now.tz, d.tz))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(d.year, 1 / 2) and Acc(d.month, 1 / 2) and Acc(d.day, 1 / 2))
@@ -156,18 +152,15 @@
     # post-conditions-end
     # impl-start
     pivot = Moment(
-        pivot_year,
-        pivot_month,
-        pivot_day,
-        d.hour,
-        d.minute,
-        d.second,
+        pivot_year, pivot_month, pivot_day,
+        d.hour, d.minute, d.second,
         d.tz,
     )
-    # The leftover span: requires now and pivot share a disposition. This call
-    # is provable only because pivot carries d.tz and now agrees with d; it
-    # measures the ordered difference of the current moment and the reference
-    # moment, which is returned alongside the constructed reference moment.
-    remaining = well_defined_diff(now, pivot)
+    other = Moment(
+        pivot_year, pivot_month, pivot_day,
+        d.hour, d.minute, d.second,
+        d.tz,
+    )
+    remaining = well_defined_diff(now, other)
     return pivot, remaining
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -38,13 +38,11 @@
 """
 from typing import Optional, Tuple
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Moment:
     def __init__(self, year: int, month: int, day: int, hour: int,
                  minute: int, second: int, tz: Optional[int]) -> None:
-        Requires(MustTerminate(2))
         Ensures(Acc(self.year) and self.year == year)        # type: ignore
         Ensures(Acc(self.month) and self.month == month)     # type: ignore
         Ensures(Acc(self.day) and self.day == day)           # type: ignore
@@ -109,7 +107,6 @@
     Requires(Acc(now.tz, 1 / 2))
     Requires(Acc(pivot.tz, 1 / 2))
     Requires(same_disposition(now.tz, pivot.tz))
-    Requires(MustTerminate(6))
     Ensures(Acc(now.tz, 1 / 2))
     Ensures(Acc(pivot.tz, 1 / 2))
     Ensures(Result() == moment_span(now, pivot))
@@ -128,7 +125,6 @@
     # its time-zone disposition (offset-aware iff `d` is).
     Requires(Acc(now.tz, 1 / 2))
     Requires(same_disposition(now.tz, d.tz))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(d.year, 1 / 2) and Acc(d.month, 1 / 2) and Acc(d.day, 1 / 2))
@@ -156,18 +152,10 @@
     # post-conditions-end
     # impl-start
     pivot = Moment(
-        pivot_year,
-        pivot_month,
-        pivot_day,
-        d.hour,
-        d.minute,
-        d.second,
+        pivot_year, pivot_month, d.day,
+        d.hour, d.minute, d.second,
         d.tz,
     )
-    # The leftover span: requires now and pivot share a disposition. This call
-    # is provable only because pivot carries d.tz and now agrees with d; it
-    # measures the ordered difference of the current moment and the reference
-    # moment, which is returned alongside the constructed reference moment.
     remaining = well_defined_diff(now, pivot)
     return pivot, remaining
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-16429.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A human-readable elapsed-time string is computed by first shifting the source
  moment forward by a whole number of years and months to an intermediate
  reference moment, then measuring the leftover span between the current moment
  and that reference. The current moment is established with the SAME
  time-zone disposition as the source moment: it is offset-aware exactly when
  the source moment is offset-aware, and offset-naive otherwise.

  The leftover span is the difference between the current moment and the
  intermediate reference moment, in that order (the current moment minus the
  reference moment). That difference is only well-defined when the two operands
  share a time-zone disposition: subtracting an offset-naive moment from an
  offset-aware one (or vice versa) is undefined. The measured span is consumed
  downstream to render the residual portion of the elapsed-time string, so the
  behaviour observes BOTH the constructed reference moment and the measured
  span; the span's magnitude is abstract here, but which ordered pair of
  moments it measures is observed.

  Therefore the intermediate reference moment built from the source's calendar
  and clock fields must carry the SAME time-zone disposition as the source
  moment, so that — the current moment already agreeing with the source — the
  leftover-span difference is well-defined for every source moment, whether
  offset-aware or offset-naive.

A moment is modelled as a minimal class carrying only the touched fields: the
calendar/clock components (ints) and a time-zone disposition. The disposition
is modelled as `Optional[int]`: an offset (in minutes) when offset-aware, and
`None` when offset-naive (Nagini bans real `tzinfo` objects; only the
aware/naive distinction and the carried offset are observed here). The
difference of two moments is modelled as a domain-restricted operation that is
defined only when both operands share a disposition and whose value is the
abstract ordered span of exactly those two operands.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional, Tuple
from nagini_contracts.contracts import *


class Moment:
    def __init__(self, year: int, month: int, day: int, hour: int,
                 minute: int, second: int, tz: Optional[int]) -> None:
        Ensures(Acc(self.year) and self.year == year)        # type: ignore
        Ensures(Acc(self.month) and self.month == month)     # type: ignore
        Ensures(Acc(self.day) and self.day == day)           # type: ignore
        Ensures(Acc(self.hour) and self.hour == hour)        # type: ignore
        Ensures(Acc(self.minute) and self.minute == minute)  # type: ignore
        Ensures(Acc(self.second) and self.second == second)  # type: ignore
        Ensures(Acc(self.tz) and self.tz is tz)              # type: ignore
        self.year = year
        self.month = month
        self.day = day
        self.hour = hour
        self.minute = minute
        self.second = second
        self.tz = tz


# pure-start
@Pure
def is_offset_aware(tz: Optional[int]) -> bool:
    """A disposition is offset-aware exactly when an offset is carried."""
    return tz is not None


@Pure
def same_disposition(a: Optional[int], b: Optional[int]) -> bool:
    """Two moments share a disposition when they are both offset-aware or both
    offset-naive. This is exactly the condition under which their difference is
    defined."""
    return is_offset_aware(a) == is_offset_aware(b)
# pure-end


# axioms-start
# The leftover-span measure between two moments, as an ABSTRACT (uninterpreted)
# quantity: moment_span(a, b) names the value of the ordered difference
# "a minus b". Its magnitude is deliberately unconstrained (no numeric value is
# pinned inside this slice), but the value is a function of the two operands IN
# ORDER — the difference of a and b is not interchangeable with the difference
# of b and a, nor with the difference of any other pair of moments.
@Pure
@ContractOnly
def moment_span(a: Moment, b: Moment) -> int:
    Requires(Acc(a.tz, 1 / 2))
    Requires(Acc(b.tz, 1 / 2))


# The guarded leftover-span difference of two moments. Its load-bearing content
# is twofold: (1) the DOMAIN restriction — the difference is defined only when
# the two operands share a time-zone disposition (an aware/naive mix is
# undefined); (2) the VALUE claim — the returned value is exactly the abstract
# ordered span of its two operands, moment_span(now, pivot), i.e. the current
# moment minus the reference moment, so a caller must invoke the difference on
# precisely that ordered pair to obtain the measured span.
#
# This is an A-reference: the domain rule and the ordered-difference semantics
# are the real moment-subtraction behaviour, validated == this contract by
# axiom_check.py (G-AX). The behaviour under specification ensures the
# intermediate reference moment shares the source's disposition so the domain
# restriction is always honoured.
@ContractOnly
def well_defined_diff(now: Moment, pivot: Moment) -> int:
    Requires(Acc(now.tz, 1 / 2))
    Requires(Acc(pivot.tz, 1 / 2))
    Requires(same_disposition(now.tz, pivot.tz))
    Ensures(Acc(now.tz, 1 / 2))
    Ensures(Acc(pivot.tz, 1 / 2))
    Ensures(Result() == moment_span(now, pivot))
# axioms-end


def pivot_remaining(d: Moment, now: Moment,
                    pivot_year: int, pivot_month: int,
                    pivot_day: int) -> Tuple[Moment, int]:
    # pre-conditions-start
    # `d` is the read-only source moment.
    Requires(Acc(d.year, 1 / 2) and Acc(d.month, 1 / 2) and Acc(d.day, 1 / 2))
    Requires(Acc(d.hour, 1 / 2) and Acc(d.minute, 1 / 2) and Acc(d.second, 1 / 2))
    Requires(Acc(d.tz, 1 / 2))
    # `now` is the read-only current moment, established to agree with `d` on
    # its time-zone disposition (offset-aware iff `d` is).
    Requires(Acc(now.tz, 1 / 2))
    Requires(same_disposition(now.tz, d.tz))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(d.year, 1 / 2) and Acc(d.month, 1 / 2) and Acc(d.day, 1 / 2))
    Ensures(Acc(d.hour, 1 / 2) and Acc(d.minute, 1 / 2) and Acc(d.second, 1 / 2))
    Ensures(Acc(d.tz, 1 / 2))
    Ensures(Acc(now.tz, 1 / 2))
    # The intermediate reference moment is the source advanced to the supplied
    # calendar position (year/month/day), carrying the source's clock fields
    # unchanged and, crucially, the source's time-zone disposition — so the
    # leftover-span difference against the current moment is well-defined and
    # measures only the residual span beyond that advanced position.
    Ensures(Acc(Result()[0].year) and Result()[0].year == pivot_year)
    Ensures(Acc(Result()[0].month) and Result()[0].month == pivot_month)
    Ensures(Acc(Result()[0].day) and Result()[0].day == pivot_day)
    Ensures(Acc(Result()[0].hour) and Result()[0].hour == d.hour)
    Ensures(Acc(Result()[0].minute) and Result()[0].minute == d.minute)
    Ensures(Acc(Result()[0].second) and Result()[0].second == d.second)
    Ensures(Acc(Result()[0].tz))
    Ensures(Result()[0].tz is d.tz)
    # The measured leftover span is the ordered difference "current moment
    # minus the constructed reference moment" — this pins WHICH difference the
    # behaviour measures (its operands and their order), while leaving the
    # abstract magnitude to the difference operation itself.
    Ensures(Result()[1] == moment_span(now, Result()[0]))
    # post-conditions-end
    # impl-start
    pivot = Moment(
        pivot_year,
        pivot_month,
        pivot_day,
        d.hour,
        d.minute,
        d.second,
        d.tz,
    )
    remaining = well_defined_diff(now, pivot)
    return pivot, remaining
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit for django__django-16429 (nagini). commands run as `SBU_BENCHMARK_DIR=benchmark-verified python -m swebench_unified.adversary <cmd> nagini django__django-16429 <atk>`.

SPEC SHAPE: pivot_remaining pins EVERY observed pivot field (year==pivot_year, month==pivot_month, day==pivot_day, hour/minute/second==d.*, and tz IS d.tz) AND pins the measured span to Result()[1]==moment_span(now, Result()[0]) where moment_span is @Pure @ContractOnly (uninterpreted). well_defined_diff Requires(same_disposition(now.tz,pivot.tz)) and Ensures Result()==moment_span(now,pivot). Zero consumed axioms; single A-reference (datetime subtraction definedness+ordered-span) validated by axiom_check.py.

POSITIVE CONTROL pos_control.py (gold impl, tz=d.tz, well_defined_diff(now,pivot)): VERIFIED 13.1s (exit 0).
G-AX axiom_check.py: exit 0 (36 disposition pairs + 30 boundary + 20000 fuzz; fix carries source disposition, prepatch breaks for every aware source; ordered-span deterministic+order-sensitive). A-reference correspondence to real datetime.__sub__ holds.
PREPATCH model_prepatch.py: FAILS (exit 1) at well_defined_diff precond `same_disposition(now.tz,pivot.tz) might not hold` @167 — bug sensed; prepatch reproduced.

ATTACK BATTERY (7 distinct wrong impls, ONLY impl region edited; all same-spec exit 0; all weakness exit 2 = FAILED verification, no timeouts; run in parallel batches of 3):
- atk_1 partial-domain (prepatch naive tz=None): FAIL precond same_disposition(now.tz,pivot.tz) @159, 13.4s.
- atk_2 ungrounded-oracle / operand-reversal (well_defined_diff(pivot,now)): FAIL postcond Result()[1]==moment_span(now,Result()[0]) @151, 18.1s.
- atk_3 control-flow-effect (span measured vs source d: well_defined_diff(now,d)): FAIL postcond Result()[0].tz is d.tz @146, 13.1s.
- atk_4 ungrounded-oracle (drop measurement, remaining=0 constant): FAIL postcond Result()[1]==moment_span(now,Result()[0]) @151, 15.4s.
- atk_5 control-flow-effect / boundary (pivot tz=now.tz instead of d.tz): FAIL postcond Result()[0].tz is d.tz @146, 12.9s.
- atk_6 ungrounded-oracle ECHO (build a field-identical but DISTINCT Moment object and pass THAT to well_defined_diff, return original pivot): FAIL postcond Result()[1]==moment_span(now,Result()[0]) @151, 29.7s. Confirms Nagini's uninterpreted moment_span is object/snapshot-identity-sensitive, not merely a function of the .tz value it reads — the span clause forces the diff onto the exact returned pivot object.
- atk_7 boundary/control-flow (pivot day=d.day instead of pivot_day): FAIL postcond Result()[0].day==pivot_day @141, 13.6s.

No attack returned CANDIDATE (none shares-spec AND verifies), so there is NO verifying wrong impl and thus no faithful refined patch requiring a run_resolve execution (patches={}). Every attack was rejected by exactly the postcondition/precondition clause that closes its refinement leg (A3 tz-carry pin, A4 ordered-span pin, A5 field pins, G-DIFF disposition guard).

REFINEMENT.md AUDIT: legs A1/A2/A3/A5 are R/R+I; A4 is A-reference (validated by G-AX, exit 0). Section C confirms no kind-3 unexpressible-changed-op step (the whole delta is the one tzinfo constructor argument + its effect on subtraction definedness, both modelled deeply). meta.json: changed_files=[timesince.py], additional_change_sites=[], modeled_functions=1, axioms=[] (no consumed axiom) — consistent with refinement.md. A-reference callee correspondence (well_defined_diff/same_disposition/moment_span <-> datetime.__sub__) holds per mapping.md §3 and G-AX.

VERDICT: SOUND. >=5 distinct attacks (7 run) covering partial-domain, boundary, control-flow-effect, and ungrounded-oracle-echo classes; positive control verifies; G-AX + prepatch confirm the spec senses the bug; no verifying wrong impl exists.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-16429.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A human-readable elapsed-time string is computed by first shifting the source
  moment forward by a whole number of years and months to an intermediate
  reference moment, then measuring the leftover span between the current moment
  and that reference. The current moment is established with the SAME
  time-zone disposition as the source moment: it is offset-aware exactly when
  the source moment is offset-aware, and offset-naive otherwise.

  The leftover span is the difference between the current moment and the
  intermediate reference moment, in that order (the current moment minus the
  reference moment). That difference is only well-defined when the two operands
  share a time-zone disposition: subtracting an offset-naive moment from an
  offset-aware one (or vice versa) is undefined. The measured span is consumed
  downstream to render the residual portion of the elapsed-time string, so the
  behaviour observes BOTH the constructed reference moment and the measured
  span; the span's magnitude is abstract here, but which ordered pair of
  moments it measures is observed.

  Therefore the intermediate reference moment built from the source's calendar
  and clock fields must carry the SAME time-zone disposition as the source
  moment, so that — the current moment already agreeing with the source — the
  leftover-span difference is well-defined for every source moment, whether
  offset-aware or offset-naive.

A moment is modelled as a minimal class carrying only the touched fields: the
calendar/clock components (ints) and a time-zone disposition. The disposition
is modelled as `Optional[int]`: an offset (in minutes) when offset-aware, and
`None` when offset-naive (Nagini bans real `tzinfo` objects; only the
aware/naive distinction and the carried offset are observed here). The
difference of two moments is modelled as a domain-restricted operation that is
defined only when both operands share a disposition and whose value is the
abstract ordered span of exactly those two operands.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional, Tuple
from nagini_contracts.contracts import *


class Moment:
    def __init__(self, year: int, month: int, day: int, hour: int,
                 minute: int, second: int, tz: Optional[int]) -> None:
        Ensures(Acc(self.year) and self.year == year)        # type: ignore
        Ensures(Acc(self.month) and self.month == month)     # type: ignore
        Ensures(Acc(self.day) and self.day == day)           # type: ignore
        Ensures(Acc(self.hour) and self.hour == hour)        # type: ignore
        Ensures(Acc(self.minute) and self.minute == minute)  # type: ignore
        Ensures(Acc(self.second) and self.second == second)  # type: ignore
        Ensures(Acc(self.tz) and self.tz is tz)              # type: ignore
        self.year = year
        self.month = month
        self.day = day
        self.hour = hour
        self.minute = minute
        self.second = second
        self.tz = tz


# pure-start
@Pure
def is_offset_aware(tz: Optional[int]) -> bool:
    """A disposition is offset-aware exactly when an offset is carried."""
    return tz is not None


@Pure
def same_disposition(a: Optional[int], b: Optional[int]) -> bool:
    """Two moments share a disposition when they are both offset-aware or both
    offset-naive. This is exactly the condition under which their difference is
    defined."""
    return is_offset_aware(a) == is_offset_aware(b)
# pure-end


# axioms-start
# The leftover-span measure between two moments, as an ABSTRACT (uninterpreted)
# quantity: moment_span(a, b) names the value of the ordered difference
# "a minus b". Its magnitude is deliberately unconstrained (no numeric value is
# pinned inside this slice), but the value is a function of the two operands IN
# ORDER — the difference of a and b is not interchangeable with the difference
# of b and a, nor with the difference of any other pair of moments.
@Pure
@ContractOnly
def moment_span(a: Moment, b: Moment) -> int:
    Requires(Acc(a.tz, 1 / 2))
    Requires(Acc(b.tz, 1 / 2))


# The guarded leftover-span difference of two moments. Its load-bearing content
# is twofold: (1) the DOMAIN restriction — the difference is defined only when
# the two operands share a time-zone disposition (an aware/naive mix is
# undefined); (2) the VALUE claim — the returned value is exactly the abstract
# ordered span of its two operands, moment_span(now, pivot), i.e. the current
# moment minus the reference moment, so a caller must invoke the difference on
# precisely that ordered pair to obtain the measured span.
#
# This is an A-reference: the domain rule and the ordered-difference semantics
# are the real moment-subtraction behaviour, validated == this contract by
# axiom_check.py (G-AX). The behaviour under specification ensures the
# intermediate reference moment shares the source's disposition so the domain
# restriction is always honoured.
@ContractOnly
def well_defined_diff(now: Moment, pivot: Moment) -> int:
    Requires(Acc(now.tz, 1 / 2))
    Requires(Acc(pivot.tz, 1 / 2))
    Requires(same_disposition(now.tz, pivot.tz))
    Ensures(Acc(now.tz, 1 / 2))
    Ensures(Acc(pivot.tz, 1 / 2))
    Ensures(Result() == moment_span(now, pivot))
# axioms-end


def pivot_remaining(d: Moment, now: Moment,
                    pivot_year: int, pivot_month: int,
                    pivot_day: int) -> Tuple[Moment, int]:
    # pre-conditions-start
    # `d` is the read-only source moment.
    Requires(Acc(d.year, 1 / 2) and Acc(d.month, 1 / 2) and Acc(d.day, 1 / 2))
    Requires(Acc(d.hour, 1 / 2) and Acc(d.minute, 1 / 2) and Acc(d.second, 1 / 2))
    Requires(Acc(d.tz, 1 / 2))
    # `now` is the read-only current moment, established to agree with `d` on
    # its time-zone disposition (offset-aware iff `d` is).
    Requires(Acc(now.tz, 1 / 2))
    Requires(same_disposition(now.tz, d.tz))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(d.year, 1 / 2) and Acc(d.month, 1 / 2) and Acc(d.day, 1 / 2))
    Ensures(Acc(d.hour, 1 / 2) and Acc(d.minute, 1 / 2) and Acc(d.second, 1 / 2))
    Ensures(Acc(d.tz, 1 / 2))
    Ensures(Acc(now.tz, 1 / 2))
    # The intermediate reference moment is the source advanced to the supplied
    # calendar position (year/month/day), carrying the source's clock fields
    # unchanged and, crucially, the source's time-zone disposition — so the
    # leftover-span difference against the current moment is well-defined and
    # measures only the residual span beyond that advanced position.
    Ensures(Acc(Result()[0].year) and Result()[0].year == pivot_year)
    Ensures(Acc(Result()[0].month) and Result()[0].month == pivot_month)
    Ensures(Acc(Result()[0].day) and Result()[0].day == pivot_day)
    Ensures(Acc(Result()[0].hour) and Result()[0].hour == d.hour)
    Ensures(Acc(Result()[0].minute) and Result()[0].minute == d.minute)
    Ensures(Acc(Result()[0].second) and Result()[0].second == d.second)
    Ensures(Acc(Result()[0].tz))
    Ensures(Result()[0].tz is d.tz)
    # The measured leftover span is the ordered difference "current moment
    # minus the constructed reference moment" — this pins WHICH difference the
    # behaviour measures (its operands and their order), while leaving the
    # abstract magnitude to the difference operation itself.
    Ensures(Result()[1] == moment_span(now, Result()[0]))
    # post-conditions-end
    # impl-start
    pivot = Moment(
        pivot_year,
        pivot_month,
        pivot_day,
        d.hour,
        d.minute,
        d.second,
        d.tz,
    )
    remaining = well_defined_diff(now, pivot)
    return pivot, remaining
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit for django__django-16429 (nagini). commands run as `SBU_BENCHMARK_DIR=benchmark-verified python -m swebench_unified.adversary <cmd> nagini django__django-16429 <atk>`.

SPEC SHAPE: pivot_remaining pins EVERY observed pivot field (year==pivot_year, month==pivot_month, day==pivot_day, hour/minute/second==d.*, and tz IS d.tz) AND pins the measured span to Result()[1]==moment_span(now, Result()[0]) where moment_span is @Pure @ContractOnly (uninterpreted). well_defined_diff Requires(same_disposition(now.tz,pivot.tz)) and Ensures Result()==moment_span(now,pivot). Zero consumed axioms; single A-reference (datetime subtraction definedness+ordered-span) validated by axiom_check.py.

POSITIVE CONTROL pos_control.py (gold impl, tz=d.tz, well_defined_diff(now,pivot)): VERIFIED 13.1s (exit 0).
G-AX axiom_check.py: exit 0 (36 disposition pairs + 30 boundary + 20000 fuzz; fix carries source disposition, prepatch breaks for every aware source; ordered-span deterministic+order-sensitive). A-reference correspondence to real datetime.__sub__ holds.
PREPATCH model_prepatch.py: FAILS (exit 1) at well_defined_diff precond `same_disposition(now.tz,pivot.tz) might not hold` @167 — bug sensed; prepatch reproduced.

ATTACK BATTERY (7 distinct wrong impls, ONLY impl region edited; all same-spec exit 0; all weakness exit 2 = FAILED verification, no timeouts; run in parallel batches of 3):
- atk_1 partial-domain (prepatch naive tz=None): FAIL precond same_disposition(now.tz,pivot.tz) @159, 13.4s.
- atk_2 ungrounded-oracle / operand-reversal (well_defined_diff(pivot,now)): FAIL postcond Result()[1]==moment_span(now,Result()[0]) @151, 18.1s.
- atk_3 control-flow-effect (span measured vs source d: well_defined_diff(now,d)): FAIL postcond Result()[0].tz is d.tz @146, 13.1s.
- atk_4 ungrounded-oracle (drop measurement, remaining=0 constant): FAIL postcond Result()[1]==moment_span(now,Result()[0]) @151, 15.4s.
- atk_5 control-flow-effect / boundary (pivot tz=now.tz instead of d.tz): FAIL postcond Result()[0].tz is d.tz @146, 12.9s.
- atk_6 ungrounded-oracle ECHO (build a field-identical but DISTINCT Moment object and pass THAT to well_defined_diff, return original pivot): FAIL postcond Result()[1]==moment_span(now,Result()[0]) @151, 29.7s. Confirms Nagini's uninterpreted moment_span is object/snapshot-identity-sensitive, not merely a function of the .tz value it reads — the span clause forces the diff onto the exact returned pivot object.
- atk_7 boundary/control-flow (pivot day=d.day instead of pivot_day): FAIL postcond Result()[0].day==pivot_day @141, 13.6s.

No attack returned CANDIDATE (none shares-spec AND verifies), so there is NO verifying wrong impl and thus no faithful refined patch requiring a run_resolve execution (patches={}). Every attack was rejected by exactly the postcondition/precondition clause that closes its refinement leg (A3 tz-carry pin, A4 ordered-span pin, A5 field pins, G-DIFF disposition guard).

REFINEMENT.md AUDIT: legs A1/A2/A3/A5 are R/R+I; A4 is A-reference (validated by G-AX, exit 0). Section C confirms no kind-3 unexpressible-changed-op step (the whole delta is the one tzinfo constructor argument + its effect on subtraction definedness, both modelled deeply). meta.json: changed_files=[timesince.py], additional_change_sites=[], modeled_functions=1, axioms=[] (no consumed axiom) — consistent with refinement.md. A-reference callee correspondence (well_defined_diff/same_disposition/moment_span <-> datetime.__sub__) holds per mapping.md §3 and G-AX.

VERDICT: SOUND. >=5 distinct attacks (7 run) covering partial-domain, boundary, control-flow-effect, and ungrounded-oracle-echo classes; positive control verifies; G-AX + prepatch confirm the spec senses the bug; no verifying wrong impl exists.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / spec-drift) audit of the nagini bundle for django__django-16429. No diverging input exists: the modeled pivot_remaining agrees with the real callee (django/utils/timesince.py timesince, the `if years or months:` branch at lines 87-103, base_commit 6c86495bce) on every input.

### SETUP VERIFIED (from repo project root):
- same-spec on model.py => exit 0 (SAME); same-spec on model_prepatch.py => exit 0. The twin differs ONLY in the impl region (line 161: `d.tz` in model vs `None` in prepatch); the spec regions (Requires/Ensures of pivot_remaining, is_offset_aware, same_disposition, moment_span, well_defined_diff) are byte-identical.
- nagini_verify.sh model.py => Verification successful (11.09s).
- nagini_verify.sh model_prepatch.py => Verification FAILED at line 167: 'precondition of well_defined_diff might not hold: same_disposition(now.tz, pivot.tz)'. So the spec is non-vacuous and senses the exact bug (aware source -> aware now -> naive pivot -> undefined subtraction).

### FAITHFULNESS REASONING (no over-strong obligation):
1. Precondition same_disposition(now.tz, d.tz) is NOT too strong. In the real code the pivot branch is only reached AFTER `delta = now - d` (timesince.py:70) already succeeded; datetime subtraction raises TypeError unless both operands share aware/naive disposition. Thus the real reachable domain is EXACTLY same-disposition (now, d) pairs. The precondition matches the reachable domain rather than narrowing it, so it cannot cause spec-model-passes / real-fails divergence. `now` is itself established aware-iff-d-aware (timesince.py:66), consistent with the precondition.
2. Postconditions match the real construction field-for-field: Result()[0].year/month/day == the passed pivot_year/pivot_month/pivot_day; pivot_day is an abstracted input parameter modeling min(MONTHS_DAYS[pivot_month-1], d.day) with NO extra claim tying it to d.day, so no divergence there. hour/minute/second == d.* (matches). tz is d.tz (matches gold `tzinfo=d.tzinfo`). Span Result()[1] == moment_span(now, Result()[0]) with moment_span uninterpreted and order-sensitive, matching `(now - pivot).total_seconds()` in operand order; magnitude left abstract (sound — the bug is a crash, not a wrong number).
3. Satisfiability witness: the impl region is the faithful translation of the gold code and it VERIFIES against these exact postconditions. A spec-too-strong postcondition would make the gold-faithful impl fail to verify; it does not. This directly refutes spec-drift.
4. G-AX (axiom_check.py) independently validates the deep model of subtraction (same_disposition == real datetime __sub__ definedness over 36 disposition pairs; fix carries source disposition on 30 boundary + 20000 fuzz moments; ordered-span deterministic + order-sensitive) — the A-reference is sound, not an over-claim.

CONCLUSION: FAITHFUL. Cannot exhibit any input where the modeled function disagrees with the real repo callee; the precondition equals the reachable domain and every postcondition is honored by the gold-faithful impl. (Note: the bundle's G-PANEL-1/G-EQ fail is a separate 'verify-but-patch-does-not-resolve' spec-too-WEAK concern for the eq/panel-1 role, not a faithfulness/too-strong defect — orthogonal to this gate.)

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (no diff markers, no reproduced gold line, no patched file/module path, no spec-view identifier embedding a patched symbol, no narration in comments). Semantically: the gold edit is a single line — add `tzinfo=d.tzinfo` to the pivot datetime.datetime(...) constructor so the pivot carries the source's tz disposition and `now - pivot` stays defined. The public problem_statement ALREADY discloses this fix verbatim: 'the pivot ... does not take into account the datetime object's tzinfo. Adding 0, d.tzinfo arguments to the datetime.datetime call seems to fix this.' The spec view's prose ('the intermediate reference moment ... must carry the SAME time-zone disposition as the source moment') is a faithful restatement of an already-public fix, not disclosure beyond the problem_statement. The spec view does not even name tzinfo/pivot/timesince or the file path; its Moment / Optional[int] disposition / well_defined_diff constructs are modeling abstractions, not repo-specific leaks. No line leaks the gold edit beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
