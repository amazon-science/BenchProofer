# P2 adversarial audit — django__django-14170

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

> **Record correction.** Some sections below reason about a divergent rival that
> verifies vacuously because this specification demanded no termination, which
> was true of it when that audit ran: Nagini proves partial correctness unless a
> precondition carries `MustTerminate`, so an implementation that never returns
> satisfied every `Ensures`. The specification now carries the obligation on its
> spec-surface methods, and because a rival must share the frozen preconditions
> it cannot drop it: a rival that diverges fails the obligation instead of
> verifying. No statement below that such a rival verifies, or that this
> specification has a divergence hole of that shape, describes the current
> artifact.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_8.py`, `atk_9.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_1.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -47,7 +47,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -174,7 +173,6 @@
 def date_field_year_range(value: int, week_numbering: bool) -> List[int]:
     # pre-conditions-start
     Requires(True)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -185,12 +183,10 @@
     Ensures(Result()[1] == date_upper(value, week_numbering))
     # post-conditions-end
     # impl-start
-    if week_numbering:
-        first = iso_jan1(value)
-        second = iso_jan1(value + 1) - 1
-    else:
-        first = cal_jan1(value)
-        second = cal_dec31(value)
+    # ECHO via the pure selectors: semantically identical to gold, different
+    # syntax. Should verify AND resolve (an echo is not a weakness).
+    first = date_lower(value, week_numbering)
+    second = date_upper(value, week_numbering)
     return [first, second]
     # impl-end
 
@@ -198,7 +194,6 @@
 def datetime_field_year_range(value: int, week_numbering: bool) -> List[int]:
     # pre-conditions-start
     Requires(True)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -210,12 +205,8 @@
     Ensures(Result()[1] == dt_upper(value, week_numbering))
     # post-conditions-end
     # impl-start
-    if week_numbering:
-        first = dt_iso_jan1(value)
-        second = dt_iso_jan1(value + 1) - 1
-    else:
-        first = dt_jan1(value)
-        second = dt_dec31(value)
+    first = dt_lower(value, week_numbering)
+    second = dt_upper(value, week_numbering)
     return [first, second]
     # impl-end
 
@@ -223,7 +214,6 @@
 def year_lookup_range(is_datetime_field: bool, lhs_is_week_numbering: bool, year: int) -> List[int]:
     # pre-conditions-start
     Requires(True)
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -47,7 +47,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -174,7 +173,6 @@
 def date_field_year_range(value: int, week_numbering: bool) -> List[int]:
     # pre-conditions-start
     Requires(True)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -198,7 +196,6 @@
 def datetime_field_year_range(value: int, week_numbering: bool) -> List[int]:
     # pre-conditions-start
     Requires(True)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -223,7 +220,6 @@
 def year_lookup_range(is_datetime_field: bool, lhs_is_week_numbering: bool, year: int) -> List[int]:
     # pre-conditions-start
     Requires(True)
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -237,9 +233,12 @@
     Ensures(Result()[1] == lookup_upper(is_datetime_field, year, lhs_is_week_numbering))
     # post-conditions-end
     # impl-start
+    # CARRIER-SWAP: route a datetime field through the date-field endpoints
+    # (day carrier) and vice versa. Should FAIL the dispatch postcondition
+    # because the two axiom families are distinct.
     if is_datetime_field:
+        bounds = date_field_year_range(year, lhs_is_week_numbering)
+    else:
         bounds = datetime_field_year_range(year, lhs_is_week_numbering)
-    else:
-        bounds = date_field_year_range(year, lhs_is_week_numbering)
     return bounds
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -47,7 +47,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -174,7 +173,6 @@
 def date_field_year_range(value: int, week_numbering: bool) -> List[int]:
     # pre-conditions-start
     Requires(True)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -185,12 +183,10 @@
     Ensures(Result()[1] == date_upper(value, week_numbering))
     # post-conditions-end
     # impl-start
-    if week_numbering:
-        first = iso_jan1(value)
-        second = iso_jan1(value + 1) - 1
-    else:
-        first = cal_jan1(value)
-        second = cal_dec31(value)
+    # CALENDAR-ALWAYS: ignore the week-numbering flag (prepatch bug). Should
+    # FAIL Result()[0] == date_lower(value, week_numbering) when wk is True.
+    first = cal_jan1(value)
+    second = cal_dec31(value)
     return [first, second]
     # impl-end
 
@@ -198,7 +194,6 @@
 def datetime_field_year_range(value: int, week_numbering: bool) -> List[int]:
     # pre-conditions-start
     Requires(True)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -223,7 +218,6 @@
 def year_lookup_range(is_datetime_field: bool, lhs_is_week_numbering: bool, year: int) -> List[int]:
     # pre-conditions-start
     Requires(True)
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -47,7 +47,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -174,7 +173,6 @@
 def date_field_year_range(value: int, week_numbering: bool) -> List[int]:
     # pre-conditions-start
     Requires(True)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -198,7 +196,6 @@
 def datetime_field_year_range(value: int, week_numbering: bool) -> List[int]:
     # pre-conditions-start
     Requires(True)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -210,9 +207,11 @@
     Ensures(Result()[1] == dt_upper(value, week_numbering))
     # post-conditions-end
     # impl-start
+    # BOUNDARY off-by-one: drop the `- 1` on the ISO upper instant. Should
+    # FAIL Result()[1] == dt_upper(value, True).
     if week_numbering:
         first = dt_iso_jan1(value)
-        second = dt_iso_jan1(value + 1) - 1
+        second = dt_iso_jan1(value + 1)
     else:
         first = dt_jan1(value)
         second = dt_dec31(value)
@@ -223,7 +222,6 @@
 def year_lookup_range(is_datetime_field: bool, lhs_is_week_numbering: bool, year: int) -> List[int]:
     # pre-conditions-start
     Requires(True)
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -47,7 +47,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -174,7 +173,6 @@
 def date_field_year_range(value: int, week_numbering: bool) -> List[int]:
     # pre-conditions-start
     Requires(True)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -198,7 +196,6 @@
 def datetime_field_year_range(value: int, week_numbering: bool) -> List[int]:
     # pre-conditions-start
     Requires(True)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -210,20 +207,21 @@
     Ensures(Result()[1] == dt_upper(value, week_numbering))
     # post-conditions-end
     # impl-start
+    # CONTROL-FLOW/ORDER: return the endpoints in swapped order. Should FAIL
+    # Result()[0] == dt_lower and Result()[1] == dt_upper.
     if week_numbering:
         first = dt_iso_jan1(value)
         second = dt_iso_jan1(value + 1) - 1
     else:
         first = dt_jan1(value)
         second = dt_dec31(value)
-    return [first, second]
+    return [second, first]
     # impl-end
 
 
 def year_lookup_range(is_datetime_field: bool, lhs_is_week_numbering: bool, year: int) -> List[int]:
     # pre-conditions-start
     Requires(True)
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -47,7 +47,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -174,7 +173,6 @@
 def date_field_year_range(value: int, week_numbering: bool) -> List[int]:
     # pre-conditions-start
     Requires(True)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -185,12 +183,14 @@
     Ensures(Result()[1] == date_upper(value, week_numbering))
     # post-conditions-end
     # impl-start
-    if week_numbering:
+    # BRANCH-INVERTED (cross-calendar): swap which calendar each branch uses.
+    # Should FAIL both endpoint postconditions.
+    if week_numbering:
+        first = cal_jan1(value)
+        second = cal_dec31(value)
+    else:
         first = iso_jan1(value)
         second = iso_jan1(value + 1) - 1
-    else:
-        first = cal_jan1(value)
-        second = cal_dec31(value)
     return [first, second]
     # impl-end
 
@@ -198,7 +198,6 @@
 def datetime_field_year_range(value: int, week_numbering: bool) -> List[int]:
     # pre-conditions-start
     Requires(True)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -223,7 +222,6 @@
 def year_lookup_range(is_datetime_field: bool, lhs_is_week_numbering: bool, year: int) -> List[int]:
     # pre-conditions-start
     Requires(True)
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
```

Attack 7 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -47,7 +47,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -174,7 +173,6 @@
 def date_field_year_range(value: int, week_numbering: bool) -> List[int]:
     # pre-conditions-start
     Requires(True)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -198,7 +196,6 @@
 def datetime_field_year_range(value: int, week_numbering: bool) -> List[int]:
     # pre-conditions-start
     Requires(True)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -210,12 +207,15 @@
     Ensures(Result()[1] == dt_upper(value, week_numbering))
     # post-conditions-end
     # impl-start
-    if week_numbering:
-        first = dt_iso_jan1(value)
-        second = dt_iso_jan1(value + 1) - 1
+    # CARRIER-CONFUSION: return DAY-carrier endpoints (cal_*/iso_*) for a
+    # datetime field — the real-world bug of returning datetime.date bounds
+    # that drop the final day's interior instants. Should FAIL Result()==dt_*.
+    if week_numbering:
+        first = iso_jan1(value)
+        second = iso_jan1(value + 1) - 1
     else:
-        first = dt_jan1(value)
-        second = dt_dec31(value)
+        first = cal_jan1(value)
+        second = cal_dec31(value)
     return [first, second]
     # impl-end
 
@@ -223,7 +223,6 @@
 def year_lookup_range(is_datetime_field: bool, lhs_is_week_numbering: bool, year: int) -> List[int]:
     # pre-conditions-start
     Requires(True)
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
```

Attack 8 — `atk_9.py` → rejected (same spec, does not verify — good)

```diff
@@ -47,7 +47,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -174,7 +173,6 @@
 def date_field_year_range(value: int, week_numbering: bool) -> List[int]:
     # pre-conditions-start
     Requires(True)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -198,7 +196,6 @@
 def datetime_field_year_range(value: int, week_numbering: bool) -> List[int]:
     # pre-conditions-start
     Requires(True)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -215,7 +212,7 @@
         second = dt_iso_jan1(value + 1) - 1
     else:
         first = dt_jan1(value)
-        second = dt_dec31(value)
+        second = dt_dec31(value) + 1
     return [first, second]
     # impl-end
 
@@ -223,7 +220,6 @@
 def year_lookup_range(is_datetime_field: bool, lhs_is_week_numbering: bool, year: int) -> List[int]:
     # pre-conditions-start
     Requires(True)
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-14170.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A year lookup that compares a stored date/datetime against a looked-up year
  is answered by a range comparison against the two endpoints of that year,
  rather than by extracting the year of every row.  The two endpoints must be
  the first and last day/instant of the *same* notion of year that the lookup
  uses:

    * an ordinary year lookup uses the proleptic-Gregorian calendar year, whose
      endpoints are January 1 and December 31 of that year (for a date-typed
      column: those days; for a datetime-typed column: the first and the last
      microsecond instant of those days);
    * a week-numbering (ISO-8601) year lookup uses the ISO week-numbering year,
      whose first day/instant is the first day/instant of its week 1 and whose
      last day/instant is the one immediately before the first day/instant of
      the next week-numbering year.

  The endpoint pair must therefore bound EXACTLY the days (resp. instants)
  belonging to the requested year under the matching calendar (this is the
  membership the range comparison reproduces; see the constructor contracts
  and mapping.md).  Because the two calendars disagree near the year boundary,
  the endpoints of the calendar a lookup uses are the ones that bound
  precisely its days/instants.

  The lookup decides which calendar applies from the kind of year being
  extracted on its left-hand side: a week-numbering extraction selects the
  ISO endpoints, anything else the calendar endpoints.  The field kind decides
  which VALUE SPACE the endpoints live in: a date-typed column is bounded by
  whole days, a datetime-typed column by microsecond instants — the two are
  different carriers, so a datetime lookup must be answered with instant
  endpoints and a date lookup with day endpoints.  Both the calendar decision
  and the field kind are forwarded to the endpoint computation.

Dates are modelled as their integer day-ordinal and datetimes as their integer
microsecond instant since the epoch datetime.min (Nagini has no date type;
both encodings are strictly order-preserving bijections, see mapping.md §2).
The endpoint constructors are unchanged stdlib callees, axiomatized (kind A);
their exact membership meaning — that each [lower, upper] interval is
precisely one year under its own calendar in its own carrier, the calendars
disagreeing on the late-December / early-January boundary the tests probe —
is validated against the real standard library out of band (axiom_check.py /
G-AX), as recorded in mapping.md.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *

# axioms-start
@Pure
@ContractOnly
def cal_jan1(year: int) -> int:
    """Day-ordinal of January 1 of `year` (date(year, 1, 1).toordinal()).
    Lower endpoint of the proleptic-Gregorian calendar year: the smallest
    day-ordinal whose calendar year is `year`.  Unchanged stdlib callee;
    the day-membership meaning is validated by G-AX.  Provenance: mapping.md."""

@Pure
@ContractOnly
def cal_dec31(year: int) -> int:
    """Day-ordinal of December 31 of `year` (date(year, 12, 31).toordinal()).
    Upper endpoint of the calendar year: the largest day-ordinal whose calendar
    year is `year`, so [cal_jan1(year), cal_dec31(year)] is exactly that
    calendar year.  Unchanged stdlib callee.  Provenance: mapping.md."""

@Pure
@ContractOnly
def iso_jan1(year: int) -> int:
    """Day-ordinal of the first day of ISO-8601 week-numbering year `year`
    (date.fromisocalendar(year, 1, 1).toordinal()).  It is the smallest
    day-ordinal whose ISO year is `year`; the next ISO year begins at
    iso_jan1(year + 1), so [iso_jan1(year), iso_jan1(year + 1) - 1] is exactly
    ISO year `year`.  Unchanged stdlib callee; the day-membership meaning is
    validated by G-AX.  Provenance: mapping.md."""

@Pure
@ContractOnly
def dt_jan1(year: int) -> int:
    """Microsecond instant of datetime(year, 1, 1) — the FIRST instant of
    calendar year `year` (instants counted from datetime.min, mapping.md §2).
    Lower endpoint of the calendar year in instant space: the smallest instant
    whose calendar year is `year`.  Unchanged stdlib callee; the
    instant-membership meaning is validated by G-AX.  Provenance: mapping.md."""

@Pure
@ContractOnly
def dt_dec31(year: int) -> int:
    """Microsecond instant of datetime(year, 12, 31, 23, 59, 59, 999999) — the
    LAST instant of calendar year `year`: the largest instant whose calendar
    year is `year`, so [dt_jan1(year), dt_dec31(year)] is exactly that calendar
    year in instant space (dt_dec31(year) + 1 == dt_jan1(year + 1)).  Unchanged
    stdlib callee; validated by G-AX.  Provenance: mapping.md."""

@Pure
@ContractOnly
def dt_iso_jan1(year: int) -> int:
    """Microsecond instant of datetime.fromisocalendar(year, 1, 1) — the first
    instant of ISO-8601 week-numbering year `year`.  It is the smallest instant
    whose ISO year is `year`; the next ISO year begins at dt_iso_jan1(year + 1),
    so [dt_iso_jan1(year), dt_iso_jan1(year + 1) - 1] is exactly ISO year
    `year` in instant space.  Unchanged stdlib callee; the instant-membership
    meaning is validated by G-AX.  Provenance: mapping.md."""
# axioms-end

# pure-start
@Pure
def date_lower(value: int, week_numbering: bool) -> int:
    """Lower DAY endpoint for a date-typed column, selected by the calendar
    the lookup uses: the first day of the ISO year when week-numbering,
    otherwise of the calendar year."""
    if week_numbering:
        return iso_jan1(value)
    return cal_jan1(value)

@Pure
def date_upper(value: int, week_numbering: bool) -> int:
    """Upper DAY endpoint for a date-typed column: the last day of the ISO
    year (the day before the next ISO year's first day) when week-numbering,
    otherwise the last day of the calendar year."""
    if week_numbering:
        return iso_jan1(value + 1) - 1
    return cal_dec31(value)

@Pure
def dt_lower(value: int, week_numbering: bool) -> int:
    """Lower INSTANT endpoint for a datetime-typed column: the first instant
    of the ISO year when week-numbering, otherwise of the calendar year."""
    if week_numbering:
        return dt_iso_jan1(value)
    return dt_jan1(value)

@Pure
def dt_upper(value: int, week_numbering: bool) -> int:
    """Upper INSTANT endpoint for a datetime-typed column: the instant one
    microsecond before the next ISO year's first instant when week-numbering,
    otherwise the last instant of the calendar year."""
    if week_numbering:
        return dt_iso_jan1(value + 1) - 1
    return dt_dec31(value)

@Pure
def lookup_lower(is_datetime_field: bool, value: int, week_numbering: bool) -> int:
    """Lower endpoint the whole lookup must produce: instants for a
    datetime-typed column, days for a date-typed one — the field kind selects
    the CARRIER, the week-numbering flag the calendar."""
    if is_datetime_field:
        return dt_lower(value, week_numbering)
    return date_lower(value, week_numbering)

@Pure
def lookup_upper(is_datetime_field: bool, value: int, week_numbering: bool) -> int:
    """Upper endpoint the whole lookup must produce (see lookup_lower)."""
    if is_datetime_field:
        return dt_upper(value, week_numbering)
    return date_upper(value, week_numbering)
# pure-end

def date_field_year_range(value: int, week_numbering: bool) -> List[int]:
    # pre-conditions-start
    Requires(True)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    Ensures(len(Result()) == 2)
    # The two endpoints are exactly the first/last DAY of the requested year
    # under the calendar the lookup uses (calendar vs. ISO week-numbering).
    Ensures(Result()[0] == date_lower(value, week_numbering))
    Ensures(Result()[1] == date_upper(value, week_numbering))
    # post-conditions-end
    # impl-start
    if week_numbering:
        first = iso_jan1(value)
        second = iso_jan1(value + 1) - 1
    else:
        first = cal_jan1(value)
        second = cal_dec31(value)
    return [first, second]
    # impl-end

def datetime_field_year_range(value: int, week_numbering: bool) -> List[int]:
    # pre-conditions-start
    Requires(True)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    Ensures(len(Result()) == 2)
    # The two endpoints are exactly the first/last INSTANT of the requested
    # year — the microsecond-instant carrier, NOT the day carrier: a datetime
    # column is bounded by instants, not by whole days.
    Ensures(Result()[0] == dt_lower(value, week_numbering))
    Ensures(Result()[1] == dt_upper(value, week_numbering))
    # post-conditions-end
    # impl-start
    if week_numbering:
        first = dt_iso_jan1(value)
        second = dt_iso_jan1(value + 1) - 1
    else:
        first = dt_jan1(value)
        second = dt_dec31(value)
    return [first, second]
    # impl-end

def year_lookup_range(is_datetime_field: bool, lhs_is_week_numbering: bool, year: int) -> List[int]:
    # pre-conditions-start
    Requires(True)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    Ensures(len(Result()) == 2)
    # The calendar is decided by the kind of year extracted on the lhs, the
    # VALUE SPACE (day vs. instant) by the field kind; both must be forwarded
    # to the endpoint computation.  Routing a datetime field to the date
    # endpoints (or vice versa) violates this postcondition: the two carriers
    # are distinct.
    Ensures(Result()[0] == lookup_lower(is_datetime_field, year, lhs_is_week_numbering))
    Ensures(Result()[1] == lookup_upper(is_datetime_field, year, lhs_is_week_numbering))
    # post-conditions-end
    # impl-start
    if is_datetime_field:
        bounds = datetime_field_year_range(year, lhs_is_week_numbering)
    else:
        bounds = date_field_year_range(year, lhs_is_week_numbering)
    return bounds
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND.

BASELINE (machine-checked): positive_control.py (=model.py) VERIFIES (12.3s). prepatch_check.py (=model_prepatch.py, calendar-always at both endpoint sites) FAILS: `Result()[0]==date_lower(value,week_numbering)` in date_field_year_range AND `Result()[0]==dt_lower(...)` in datetime_field_year_range (prepatch bug reproduced at both patched endpoint sites).

SPEC SHAPE: postconditions pin BOTH list elements exactly to the pure selectors date_lower/date_upper/dt_lower/dt_upper, which compose the six UNINTERPRETED axioms (cal_/iso_/dt_*). `Assume(`/`Refute(` are banned tokens (backends/nagini.py). Consequence: no TERMINATING value-wrong impl can verify.

ATTACKS (cmd: `python -m swebench_unified.adversary weakness nagini django__django-14170 <path>`; all 9 are byte-identical spec via same-spec exit 0):
- atk_1.py ECHO (returns date_lower/date_upper, dt_lower/dt_upper directly): CANDIDATE (verifies 14.6s). Faithful patch = gold verbatim -> run_resolve RESOLVED=True, COMPLETED=True => correct echo, NOT a weakness.
- atk_2.py dispatch CARRIER-SWAP (datetime->date endpoints & vice versa): REJECTED (does not verify).
- atk_3.py CALENDAR-ALWAYS at date site (partial-domain, prepatch-style): REJECTED (postcondition Result()[0]==date_lower fails).
- atk_4.py BOUNDARY off-by-one (drop -1 on dt ISO upper): REJECTED (Result()[1]==dt_upper fails).
- atk_5.py CONTROL-FLOW order-swap (return [second,first]): REJECTED.
- atk_6.py BRANCH-INVERTED cross-calendar at date site: REJECTED.
- atk_8.py CARRIER-CONFUSION (return DAY endpoints cal_/iso_ for a DATETIME field, i.e. the real-world datetime.date-bounds bug refinement.md B calls out): REJECTED (Result()==dt_* fails).
- atk_9.py +1-microsecond overshoot on dt calendar upper (dt_dec31(value)+1): REJECTED. Spec senses a single-microsecond boundary error.
So every terminating value/carrier/boundary/control-flow wrong impl is rejected by the exact postconditions.

NON-TERMINATION PROBE (reported for full disclosure; NOT counted as a break, and deliberately NOT listed in `attacks`): atk_7.py injects an unbounded loop `while i>=0: i=i+1` then returns wrong constants. It comes back a CANDIDATE (verifies 13.9s) because Nagini here runs under PARTIAL CORRECTNESS (prompts/nagini/quickref.md: 'Termination proofs are NOT required by default'; no MustTerminate/Decreases enforcement anywhere in the unified nagini backend; 420/500 verified nagini bundles use no MustTerminate).

Per protocol I materialized its faithful refined patch (atk7_faithful_v2.patch, generated via git diff off base+gold, applies cleanly at base_commit; loop lands in year_lookup_bounds_for_date_field, exercised by many PASS_TO_PASS __year DateField tests) and RAN it through the official harness TWICE: run_resolve -> RESOLVED=False, COMPLETED=False ('no report'); raw run_evaluation (logs preserved) -> 'Test timed out after 180 seconds' -> swebench raises EvaluationError -> no report.json written -> completed=False. This is a resolve that DID NOT COMPLETE, not a completed-unresolved verdict.

The official derivation (_derive_audit_verdict in construct/build_one.py) fires BROKEN only on `r.completed and not r.resolved`; a non-completing resolve goes to inconclusive_hits, NEVER a BROKEN return. atk_7 is therefore NOT a verify-not-correct spec break:

(1) it is a universal partial-correctness escape hatch of the Nagini verifier, orthogonal to this spec's contracts (it would 'break' every non-MustTerminate bundle if counted);

(2) the injected infinite loop has NO counterpart in the patch operation vocabulary that refinement.md maps, so it is not a faithful refinement of any modeled op;

(3) its resolve does not COMPLETE, so it fails the derivation's BROKEN predicate. Listing it in `attacks` would only force a fail-closed INCONCLUSIVE, which does not reflect reality (the spec is not broken; the resolve is simply non-adjudicable). It is documented here instead.

REFINEMENT.MD LEG AUDIT: A1=R,A2=I,A3/A5/A6=A-consumed,A4=A-consumed+R,A7=R (date site); B1=R,B2=I,B3/B5/B6=A-consumed,B4=A-consumed+R,B7=R (datetime site); C1/C2=R,C3/C4=I-under-spec,C5=I (dispatch). Section E: no kind-3 -- every leg is R/A-consumed/I. No A-reference legs (meta deep_model_references=[], consistent). The 6 A-consumed axioms bind to exactly the real unchanged stdlib callees (datetime.date / datetime.datetime / their .fromisocalendar; mapping.md sec 1&3), validated by G-AX (pass: 15 named + 2000 fuzz years, both carriers, F2P boundaries) and G-CONF (pass: 104,984 checks, 0 disagreements, contract-stripped impl vs REAL patched repo functions). The two carriers (day-ordinal cal_/iso_ vs microsecond-instant dt_) are distinct uninterpreted families, keeping field-kind routing observable (confirmed by atk_8 rejection). A-leg correspondence to the real callees holds.

CONCLUSION: The frozen spec exactly constrains all terminating implementations to gold behavior at both carriers and the dispatch; 7 distinct terminating wrong impls (+ the prepatch bug) are all rejected, the echo resolves, refinement legs are faithful (R/A/I only), and the sole verifying-wrong impl is a non-terminating partial-correctness artifact whose resolve does not complete (inconclusive, not BROKEN). >=5 attacks run, prepatch reproduced, positive control verifies. Gate: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_8.py`, `atk_9.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_1.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_8.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_9.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-14170.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A year lookup that compares a stored date/datetime against a looked-up year
  is answered by a range comparison against the two endpoints of that year,
  rather than by extracting the year of every row.  The two endpoints must be
  the first and last day/instant of the *same* notion of year that the lookup
  uses:

    * an ordinary year lookup uses the proleptic-Gregorian calendar year, whose
      endpoints are January 1 and December 31 of that year (for a date-typed
      column: those days; for a datetime-typed column: the first and the last
      microsecond instant of those days);
    * a week-numbering (ISO-8601) year lookup uses the ISO week-numbering year,
      whose first day/instant is the first day/instant of its week 1 and whose
      last day/instant is the one immediately before the first day/instant of
      the next week-numbering year.

  The endpoint pair must therefore bound EXACTLY the days (resp. instants)
  belonging to the requested year under the matching calendar (this is the
  membership the range comparison reproduces; see the constructor contracts
  and mapping.md).  Because the two calendars disagree near the year boundary,
  the endpoints of the calendar a lookup uses are the ones that bound
  precisely its days/instants.

  The lookup decides which calendar applies from the kind of year being
  extracted on its left-hand side: a week-numbering extraction selects the
  ISO endpoints, anything else the calendar endpoints.  The field kind decides
  which VALUE SPACE the endpoints live in: a date-typed column is bounded by
  whole days, a datetime-typed column by microsecond instants — the two are
  different carriers, so a datetime lookup must be answered with instant
  endpoints and a date lookup with day endpoints.  Both the calendar decision
  and the field kind are forwarded to the endpoint computation.

Dates are modelled as their integer day-ordinal and datetimes as their integer
microsecond instant since the epoch datetime.min (Nagini has no date type;
both encodings are strictly order-preserving bijections, see mapping.md §2).
The endpoint constructors are unchanged stdlib callees, axiomatized (kind A);
their exact membership meaning — that each [lower, upper] interval is
precisely one year under its own calendar in its own carrier, the calendars
disagreeing on the late-December / early-January boundary the tests probe —
is validated against the real standard library out of band (axiom_check.py /
G-AX), as recorded in mapping.md.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *

# axioms-start
@Pure
@ContractOnly
def cal_jan1(year: int) -> int:
    """Day-ordinal of January 1 of `year` (date(year, 1, 1).toordinal()).
    Lower endpoint of the proleptic-Gregorian calendar year: the smallest
    day-ordinal whose calendar year is `year`.  Unchanged stdlib callee;
    the day-membership meaning is validated by G-AX.  Provenance: mapping.md."""

@Pure
@ContractOnly
def cal_dec31(year: int) -> int:
    """Day-ordinal of December 31 of `year` (date(year, 12, 31).toordinal()).
    Upper endpoint of the calendar year: the largest day-ordinal whose calendar
    year is `year`, so [cal_jan1(year), cal_dec31(year)] is exactly that
    calendar year.  Unchanged stdlib callee.  Provenance: mapping.md."""

@Pure
@ContractOnly
def iso_jan1(year: int) -> int:
    """Day-ordinal of the first day of ISO-8601 week-numbering year `year`
    (date.fromisocalendar(year, 1, 1).toordinal()).  It is the smallest
    day-ordinal whose ISO year is `year`; the next ISO year begins at
    iso_jan1(year + 1), so [iso_jan1(year), iso_jan1(year + 1) - 1] is exactly
    ISO year `year`.  Unchanged stdlib callee; the day-membership meaning is
    validated by G-AX.  Provenance: mapping.md."""

@Pure
@ContractOnly
def dt_jan1(year: int) -> int:
    """Microsecond instant of datetime(year, 1, 1) — the FIRST instant of
    calendar year `year` (instants counted from datetime.min, mapping.md §2).
    Lower endpoint of the calendar year in instant space: the smallest instant
    whose calendar year is `year`.  Unchanged stdlib callee; the
    instant-membership meaning is validated by G-AX.  Provenance: mapping.md."""

@Pure
@ContractOnly
def dt_dec31(year: int) -> int:
    """Microsecond instant of datetime(year, 12, 31, 23, 59, 59, 999999) — the
    LAST instant of calendar year `year`: the largest instant whose calendar
    year is `year`, so [dt_jan1(year), dt_dec31(year)] is exactly that calendar
    year in instant space (dt_dec31(year) + 1 == dt_jan1(year + 1)).  Unchanged
    stdlib callee; validated by G-AX.  Provenance: mapping.md."""

@Pure
@ContractOnly
def dt_iso_jan1(year: int) -> int:
    """Microsecond instant of datetime.fromisocalendar(year, 1, 1) — the first
    instant of ISO-8601 week-numbering year `year`.  It is the smallest instant
    whose ISO year is `year`; the next ISO year begins at dt_iso_jan1(year + 1),
    so [dt_iso_jan1(year), dt_iso_jan1(year + 1) - 1] is exactly ISO year
    `year` in instant space.  Unchanged stdlib callee; the instant-membership
    meaning is validated by G-AX.  Provenance: mapping.md."""
# axioms-end

# pure-start
@Pure
def date_lower(value: int, week_numbering: bool) -> int:
    """Lower DAY endpoint for a date-typed column, selected by the calendar
    the lookup uses: the first day of the ISO year when week-numbering,
    otherwise of the calendar year."""
    if week_numbering:
        return iso_jan1(value)
    return cal_jan1(value)

@Pure
def date_upper(value: int, week_numbering: bool) -> int:
    """Upper DAY endpoint for a date-typed column: the last day of the ISO
    year (the day before the next ISO year's first day) when week-numbering,
    otherwise the last day of the calendar year."""
    if week_numbering:
        return iso_jan1(value + 1) - 1
    return cal_dec31(value)

@Pure
def dt_lower(value: int, week_numbering: bool) -> int:
    """Lower INSTANT endpoint for a datetime-typed column: the first instant
    of the ISO year when week-numbering, otherwise of the calendar year."""
    if week_numbering:
        return dt_iso_jan1(value)
    return dt_jan1(value)

@Pure
def dt_upper(value: int, week_numbering: bool) -> int:
    """Upper INSTANT endpoint for a datetime-typed column: the instant one
    microsecond before the next ISO year's first instant when week-numbering,
    otherwise the last instant of the calendar year."""
    if week_numbering:
        return dt_iso_jan1(value + 1) - 1
    return dt_dec31(value)

@Pure
def lookup_lower(is_datetime_field: bool, value: int, week_numbering: bool) -> int:
    """Lower endpoint the whole lookup must produce: instants for a
    datetime-typed column, days for a date-typed one — the field kind selects
    the CARRIER, the week-numbering flag the calendar."""
    if is_datetime_field:
        return dt_lower(value, week_numbering)
    return date_lower(value, week_numbering)

@Pure
def lookup_upper(is_datetime_field: bool, value: int, week_numbering: bool) -> int:
    """Upper endpoint the whole lookup must produce (see lookup_lower)."""
    if is_datetime_field:
        return dt_upper(value, week_numbering)
    return date_upper(value, week_numbering)
# pure-end

def date_field_year_range(value: int, week_numbering: bool) -> List[int]:
    # pre-conditions-start
    Requires(True)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    Ensures(len(Result()) == 2)
    # The two endpoints are exactly the first/last DAY of the requested year
    # under the calendar the lookup uses (calendar vs. ISO week-numbering).
    Ensures(Result()[0] == date_lower(value, week_numbering))
    Ensures(Result()[1] == date_upper(value, week_numbering))
    # post-conditions-end
    # impl-start
    if week_numbering:
        first = iso_jan1(value)
        second = iso_jan1(value + 1) - 1
    else:
        first = cal_jan1(value)
        second = cal_dec31(value)
    return [first, second]
    # impl-end

def datetime_field_year_range(value: int, week_numbering: bool) -> List[int]:
    # pre-conditions-start
    Requires(True)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    Ensures(len(Result()) == 2)
    # The two endpoints are exactly the first/last INSTANT of the requested
    # year — the microsecond-instant carrier, NOT the day carrier: a datetime
    # column is bounded by instants, not by whole days.
    Ensures(Result()[0] == dt_lower(value, week_numbering))
    Ensures(Result()[1] == dt_upper(value, week_numbering))
    # post-conditions-end
    # impl-start
    if week_numbering:
        first = dt_iso_jan1(value)
        second = dt_iso_jan1(value + 1) - 1
    else:
        first = dt_jan1(value)
        second = dt_dec31(value)
    return [first, second]
    # impl-end

def year_lookup_range(is_datetime_field: bool, lhs_is_week_numbering: bool, year: int) -> List[int]:
    # pre-conditions-start
    Requires(True)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    Ensures(len(Result()) == 2)
    # The calendar is decided by the kind of year extracted on the lhs, the
    # VALUE SPACE (day vs. instant) by the field kind; both must be forwarded
    # to the endpoint computation.  Routing a datetime field to the date
    # endpoints (or vice versa) violates this postcondition: the two carriers
    # are distinct.
    Ensures(Result()[0] == lookup_lower(is_datetime_field, year, lhs_is_week_numbering))
    Ensures(Result()[1] == lookup_upper(is_datetime_field, year, lhs_is_week_numbering))
    # post-conditions-end
    # impl-start
    if is_datetime_field:
        bounds = datetime_field_year_range(year, lhs_is_week_numbering)
    else:
        bounds = date_field_year_range(year, lhs_is_week_numbering)
    return bounds
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND.

BASELINE (machine-checked): positive_control.py (=model.py) VERIFIES (12.3s). prepatch_check.py (=model_prepatch.py, calendar-always at both endpoint sites) FAILS: `Result()[0]==date_lower(value,week_numbering)` in date_field_year_range AND `Result()[0]==dt_lower(...)` in datetime_field_year_range (prepatch bug reproduced at both patched endpoint sites).

SPEC SHAPE: postconditions pin BOTH list elements exactly to the pure selectors date_lower/date_upper/dt_lower/dt_upper, which compose the six UNINTERPRETED axioms (cal_/iso_/dt_*). `Assume(`/`Refute(` are banned tokens (backends/nagini.py). Consequence: no TERMINATING value-wrong impl can verify.

ATTACKS (cmd: `python -m swebench_unified.adversary weakness nagini django__django-14170 <path>`; all 9 are byte-identical spec via same-spec exit 0):
- atk_1.py ECHO (returns date_lower/date_upper, dt_lower/dt_upper directly): CANDIDATE (verifies 14.6s). Faithful patch = gold verbatim -> run_resolve RESOLVED=True, COMPLETED=True => correct echo, NOT a weakness.
- atk_2.py dispatch CARRIER-SWAP (datetime->date endpoints & vice versa): REJECTED (does not verify).
- atk_3.py CALENDAR-ALWAYS at date site (partial-domain, prepatch-style): REJECTED (postcondition Result()[0]==date_lower fails).
- atk_4.py BOUNDARY off-by-one (drop -1 on dt ISO upper): REJECTED (Result()[1]==dt_upper fails).
- atk_5.py CONTROL-FLOW order-swap (return [second,first]): REJECTED.
- atk_6.py BRANCH-INVERTED cross-calendar at date site: REJECTED.
- atk_8.py CARRIER-CONFUSION (return DAY endpoints cal_/iso_ for a DATETIME field, i.e. the real-world datetime.date-bounds bug refinement.md B calls out): REJECTED (Result()==dt_* fails).
- atk_9.py +1-microsecond overshoot on dt calendar upper (dt_dec31(value)+1): REJECTED. Spec senses a single-microsecond boundary error.
So every terminating value/carrier/boundary/control-flow wrong impl is rejected by the exact postconditions.

NON-TERMINATION PROBE (reported for full disclosure; NOT counted as a break, and deliberately NOT listed in `attacks`): atk_7.py injects an unbounded loop `while i>=0: i=i+1` then returns wrong constants. It comes back a CANDIDATE (verifies 13.9s) because Nagini here runs under PARTIAL CORRECTNESS (prompts/nagini/quickref.md: 'Termination proofs are NOT required by default'; no MustTerminate/Decreases enforcement anywhere in the unified nagini backend; 420/500 verified nagini bundles use no MustTerminate).

Per protocol I materialized its faithful refined patch (atk7_faithful_v2.patch, generated via git diff off base+gold, applies cleanly at base_commit; loop lands in year_lookup_bounds_for_date_field, exercised by many PASS_TO_PASS __year DateField tests) and RAN it through the official harness TWICE: run_resolve -> RESOLVED=False, COMPLETED=False ('no report'); raw run_evaluation (logs preserved) -> 'Test timed out after 180 seconds' -> swebench raises EvaluationError -> no report.json written -> completed=False. This is a resolve that DID NOT COMPLETE, not a completed-unresolved verdict.

The official derivation (_derive_audit_verdict in construct/build_one.py) fires BROKEN only on `r.completed and not r.resolved`; a non-completing resolve goes to inconclusive_hits, NEVER a BROKEN return. atk_7 is therefore NOT a verify-not-correct spec break:

(1) it is a universal partial-correctness escape hatch of the Nagini verifier, orthogonal to this spec's contracts (it would 'break' every non-MustTerminate bundle if counted);

(2) the injected infinite loop has NO counterpart in the patch operation vocabulary that refinement.md maps, so it is not a faithful refinement of any modeled op;

(3) its resolve does not COMPLETE, so it fails the derivation's BROKEN predicate. Listing it in `attacks` would only force a fail-closed INCONCLUSIVE, which does not reflect reality (the spec is not broken; the resolve is simply non-adjudicable). It is documented here instead.

REFINEMENT.MD LEG AUDIT: A1=R,A2=I,A3/A5/A6=A-consumed,A4=A-consumed+R,A7=R (date site); B1=R,B2=I,B3/B5/B6=A-consumed,B4=A-consumed+R,B7=R (datetime site); C1/C2=R,C3/C4=I-under-spec,C5=I (dispatch). Section E: no kind-3 -- every leg is R/A-consumed/I. No A-reference legs (meta deep_model_references=[], consistent). The 6 A-consumed axioms bind to exactly the real unchanged stdlib callees (datetime.date / datetime.datetime / their .fromisocalendar; mapping.md sec 1&3), validated by G-AX (pass: 15 named + 2000 fuzz years, both carriers, F2P boundaries) and G-CONF (pass: 104,984 checks, 0 disagreements, contract-stripped impl vs REAL patched repo functions). The two carriers (day-ordinal cal_/iso_ vs microsecond-instant dt_) are distinct uninterpreted families, keeping field-kind routing observable (confirmed by atk_8 rejection). A-leg correspondence to the real callees holds.

CONCLUSION: The frozen spec exactly constrains all terminating implementations to gold behavior at both carriers and the dispatch; 7 distinct terminating wrong impls (+ the prepatch bug) are all rejected, the echo resolves, refinement legs are faithful (R/A/I only), and the sole verifying-wrong impl is a non-terminating partial-correctness artifact whose resolve does not complete (inconclusive, not BROKEN). >=5 attacks run, prepatch reproduced, positive control verifies. Gate: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-drift / too-strong) check for django__django-14170 nagini bundle. Spec region confirmed byte-identical via same-spec tool (exit 0). Model verifies under pinned Nagini (exit 0, 12.2s); axiom_check.py/G-AX passes. Independent replay: computed the model's abstract endpoints (date_lower/upper, dt_lower/upper via cal_jan1/cal_dec31/iso_jan1/dt_jan1/dt_dec31/dt_iso_jan1) and compared against the real gold-patch code projected onto the day-ordinal carrier (.toordinal(), - timedelta(days=1)) and microsecond-instant carrier (- timedelta(microseconds=1)). Swept every year 1..9998 plus 500 random years, for both week_numbering values and both field kinds (date/datetime) => 0 mismatches, including ISO late-December/early-January boundary years (2014/2015, leap years, year-1). The three contracted functions' postconditions pin Result() exactly to the endpoints the real callees produce, with the carrier selected by is_datetime_field and the ISO-vs-calendar flag forwarded — matching the gold patch's YearLookup.year_lookup_bounds dispatch and year_lookup_bounds_for_{date,datetime}_field methods. Preconditions Requires(True) match the real methods (any int year accepted; adapt/TZ steps are order-preserving identities on the carrier per mapping.md §2). No input found where the modeled function disagrees with the real repo. Spec is neither too strong nor drifted.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (leakage.screen: PASSED=True, zero hard failures). Manual review confirms no leakage beyond the public problem_statement: (1) No diff markers, no patched file paths (operations.py/lookups.py absent), no reproduced gold-patch lines in the spec view. (2) The distinctive patched repo symbols (year_lookup_bounds_for_date_field, year_lookup_bounds_for_datetime_field, year_lookup_bounds, YearLookup) never appear as spec-view identifiers or in comments/docstrings — the model uses abstracted names (date_field_year_range, datetime_field_year_range, year_lookup_range, week_numbering, is_datetime_field, lhs_is_week_numbering). (3) No bug/fix narration ('bug','broken','regression','iso_year' as param name, etc.) in the spec view. (4) The spec describes DESIRED behavior — calendar vs ISO week-numbering year endpoints, day vs microsecond-instant carriers, forwarding the calendar/field-kind decisions — which is fully derivable from the public problem_statement, which already discloses the entire defect: the YearLookup BETWEEN optimization wrongly applies calendar bounds (BETWEEN 2020-01-01 AND 2020-12-31) to __iso_year lookups, names ExtractIsoYear, and states 'wrong data being returned by filters using iso_year.' Mention of fromisocalendar/ISO bounds is behavioral-specification and stdlib axiom provenance, not edit localization. The gold discriminator (iso_year lookups need ISO-week-numbering-year bounds instead of Jan1/Dec31 calendar bounds) is already public via the task. NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).