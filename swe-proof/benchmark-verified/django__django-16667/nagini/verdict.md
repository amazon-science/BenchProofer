# P2 adversarial audit — django__django-16667

**Backend:** `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk2_wrong_sentinel.py`, `atk3_swap_handlers.py`, `atk4_collapse_handler.py`, `atk5_notpresent_empty.py`, `atk6_oracle_echo.py`, `atk7_blank_raw.py`, `atk_prepatch.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk1_dispatch_on_kind.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The spec is not broken: no verifying same-spec impl has a faithful refined patch that fails to resolve.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk1_dispatch_on_kind.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -56,7 +56,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class DateOutOfRange(Exception):
@@ -121,7 +120,6 @@
     reject kinds (these two are the ONLY ways it can fail). Provenance +
     executable soundness check: mapping.md §3 / axiom_check.py."""
     Requires(kind == 0 or kind == 1 or kind == 2)
-    Requires(MustTerminate(2))
     Ensures(kind == 0)
     Exsures(DateOutOfRange, kind == 1)
     Exsures(DateCapacityOverflow, kind == 2)
@@ -133,7 +131,6 @@
     constructed date as a fresh code-point list (the unchanged success-path
     callee's return). Its content is EXACTLY `success_text()`. Used only in the
     implementation. Provenance: mapping.md §3 / axiom_check.py."""
-    Requires(MustTerminate(2))
     Ensures(Acc(list_pred(Result())))
     Ensures(ToSeq(Result()) == success_text())
 
@@ -144,7 +141,6 @@
     (the unchanged out-of-range-path callee's return). Its content is EXACTLY
     `out_of_range_text()`. Used only in the implementation. Provenance:
     mapping.md §3 / axiom_check.py."""
-    Requires(MustTerminate(2))
     Ensures(Acc(list_pred(Result())))
     Ensures(ToSeq(Result()) == out_of_range_text())
 
@@ -169,7 +165,6 @@
     """Materialise the raw-retrieval callee's value as a fresh code-point list
     (the unchanged not-all-present fallback's return). Its content is EXACTLY
     `raw_value()`. Used only in the implementation. Provenance: mapping.md §3."""
-    Requires(MustTerminate(2))
     Ensures(Acc(list_pred(Result())))
     Ensures(ToSeq(Result()) == raw_value())
 # axioms-end
@@ -201,7 +196,6 @@
     #                2 capacity-overflow.
     Requires(Implies(all_blank, all_present))
     Requires(kind == 0 or kind == 1 or kind == 2)
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     # The result is always a materialised code-point list.
@@ -235,13 +229,11 @@
         empty = []  # type: List[int]
         return empty
     if all_present:
-        try:
-            date_token = construct_date(kind)
+        if kind == 0:
             return render_success()
-        except DateOutOfRange:
+        if kind == 1:
             return render_out_of_range()
-        except DateCapacityOverflow:
-            result = [48, 45, 48, 45, 48]  # type: List[int]
-            return result
+        result = [48, 45, 48, 45, 48]  # type: List[int]
+        return result
     return retrieve_raw()
     # impl-end
```

Attack 2 — `atk2_wrong_sentinel.py` → rejected (same spec, does not verify — good)

```diff
@@ -56,7 +56,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class DateOutOfRange(Exception):
@@ -121,7 +120,6 @@
     reject kinds (these two are the ONLY ways it can fail). Provenance +
     executable soundness check: mapping.md §3 / axiom_check.py."""
     Requires(kind == 0 or kind == 1 or kind == 2)
-    Requires(MustTerminate(2))
     Ensures(kind == 0)
     Exsures(DateOutOfRange, kind == 1)
     Exsures(DateCapacityOverflow, kind == 2)
@@ -133,7 +131,6 @@
     constructed date as a fresh code-point list (the unchanged success-path
     callee's return). Its content is EXACTLY `success_text()`. Used only in the
     implementation. Provenance: mapping.md §3 / axiom_check.py."""
-    Requires(MustTerminate(2))
     Ensures(Acc(list_pred(Result())))
     Ensures(ToSeq(Result()) == success_text())
 
@@ -144,7 +141,6 @@
     (the unchanged out-of-range-path callee's return). Its content is EXACTLY
     `out_of_range_text()`. Used only in the implementation. Provenance:
     mapping.md §3 / axiom_check.py."""
-    Requires(MustTerminate(2))
     Ensures(Acc(list_pred(Result())))
     Ensures(ToSeq(Result()) == out_of_range_text())
 
@@ -169,7 +165,6 @@
     """Materialise the raw-retrieval callee's value as a fresh code-point list
     (the unchanged not-all-present fallback's return). Its content is EXACTLY
     `raw_value()`. Used only in the implementation. Provenance: mapping.md §3."""
-    Requires(MustTerminate(2))
     Ensures(Acc(list_pred(Result())))
     Ensures(ToSeq(Result()) == raw_value())
 # axioms-end
@@ -201,7 +196,6 @@
     #                2 capacity-overflow.
     Requires(Implies(all_blank, all_present))
     Requires(kind == 0 or kind == 1 or kind == 2)
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     # The result is always a materialised code-point list.
@@ -241,7 +235,7 @@
         except DateOutOfRange:
             return render_out_of_range()
         except DateCapacityOverflow:
-            result = [48, 45, 48, 45, 48]  # type: List[int]
+            result = [48, 45, 48, 45, 48, 45, 48]  # type: List[int]
             return result
     return retrieve_raw()
     # impl-end
```

Attack 3 — `atk3_swap_handlers.py` → rejected (same spec, does not verify — good)

```diff
@@ -56,7 +56,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class DateOutOfRange(Exception):
@@ -121,7 +120,6 @@
     reject kinds (these two are the ONLY ways it can fail). Provenance +
     executable soundness check: mapping.md §3 / axiom_check.py."""
     Requires(kind == 0 or kind == 1 or kind == 2)
-    Requires(MustTerminate(2))
     Ensures(kind == 0)
     Exsures(DateOutOfRange, kind == 1)
     Exsures(DateCapacityOverflow, kind == 2)
@@ -133,7 +131,6 @@
     constructed date as a fresh code-point list (the unchanged success-path
     callee's return). Its content is EXACTLY `success_text()`. Used only in the
     implementation. Provenance: mapping.md §3 / axiom_check.py."""
-    Requires(MustTerminate(2))
     Ensures(Acc(list_pred(Result())))
     Ensures(ToSeq(Result()) == success_text())
 
@@ -144,7 +141,6 @@
     (the unchanged out-of-range-path callee's return). Its content is EXACTLY
     `out_of_range_text()`. Used only in the implementation. Provenance:
     mapping.md §3 / axiom_check.py."""
-    Requires(MustTerminate(2))
     Ensures(Acc(list_pred(Result())))
     Ensures(ToSeq(Result()) == out_of_range_text())
 
@@ -169,7 +165,6 @@
     """Materialise the raw-retrieval callee's value as a fresh code-point list
     (the unchanged not-all-present fallback's return). Its content is EXACTLY
     `raw_value()`. Used only in the implementation. Provenance: mapping.md §3."""
-    Requires(MustTerminate(2))
     Ensures(Acc(list_pred(Result())))
     Ensures(ToSeq(Result()) == raw_value())
 # axioms-end
@@ -201,7 +196,6 @@
     #                2 capacity-overflow.
     Requires(Implies(all_blank, all_present))
     Requires(kind == 0 or kind == 1 or kind == 2)
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     # The result is always a materialised code-point list.
@@ -239,9 +233,9 @@
             date_token = construct_date(kind)
             return render_success()
         except DateOutOfRange:
-            return render_out_of_range()
-        except DateCapacityOverflow:
             result = [48, 45, 48, 45, 48]  # type: List[int]
             return result
+        except DateCapacityOverflow:
+            return render_out_of_range()
     return retrieve_raw()
     # impl-end
```

Attack 4 — `atk4_collapse_handler.py` → rejected (same spec, does not verify — good)

```diff
@@ -56,7 +56,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class DateOutOfRange(Exception):
@@ -121,7 +120,6 @@
     reject kinds (these two are the ONLY ways it can fail). Provenance +
     executable soundness check: mapping.md §3 / axiom_check.py."""
     Requires(kind == 0 or kind == 1 or kind == 2)
-    Requires(MustTerminate(2))
     Ensures(kind == 0)
     Exsures(DateOutOfRange, kind == 1)
     Exsures(DateCapacityOverflow, kind == 2)
@@ -133,7 +131,6 @@
     constructed date as a fresh code-point list (the unchanged success-path
     callee's return). Its content is EXACTLY `success_text()`. Used only in the
     implementation. Provenance: mapping.md §3 / axiom_check.py."""
-    Requires(MustTerminate(2))
     Ensures(Acc(list_pred(Result())))
     Ensures(ToSeq(Result()) == success_text())
 
@@ -144,7 +141,6 @@
     (the unchanged out-of-range-path callee's return). Its content is EXACTLY
     `out_of_range_text()`. Used only in the implementation. Provenance:
     mapping.md §3 / axiom_check.py."""
-    Requires(MustTerminate(2))
     Ensures(Acc(list_pred(Result())))
     Ensures(ToSeq(Result()) == out_of_range_text())
 
@@ -169,7 +165,6 @@
     """Materialise the raw-retrieval callee's value as a fresh code-point list
     (the unchanged not-all-present fallback's return). Its content is EXACTLY
     `raw_value()`. Used only in the implementation. Provenance: mapping.md §3."""
-    Requires(MustTerminate(2))
     Ensures(Acc(list_pred(Result())))
     Ensures(ToSeq(Result()) == raw_value())
 # axioms-end
@@ -201,7 +196,6 @@
     #                2 capacity-overflow.
     Requires(Implies(all_blank, all_present))
     Requires(kind == 0 or kind == 1 or kind == 2)
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     # The result is always a materialised code-point list.
@@ -241,7 +235,6 @@
         except DateOutOfRange:
             return render_out_of_range()
         except DateCapacityOverflow:
-            result = [48, 45, 48, 45, 48]  # type: List[int]
-            return result
+            return render_out_of_range()
     return retrieve_raw()
     # impl-end
```

Attack 5 — `atk5_notpresent_empty.py` → rejected (same spec, does not verify — good)

```diff
@@ -56,7 +56,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class DateOutOfRange(Exception):
@@ -121,7 +120,6 @@
     reject kinds (these two are the ONLY ways it can fail). Provenance +
     executable soundness check: mapping.md §3 / axiom_check.py."""
     Requires(kind == 0 or kind == 1 or kind == 2)
-    Requires(MustTerminate(2))
     Ensures(kind == 0)
     Exsures(DateOutOfRange, kind == 1)
     Exsures(DateCapacityOverflow, kind == 2)
@@ -133,7 +131,6 @@
     constructed date as a fresh code-point list (the unchanged success-path
     callee's return). Its content is EXACTLY `success_text()`. Used only in the
     implementation. Provenance: mapping.md §3 / axiom_check.py."""
-    Requires(MustTerminate(2))
     Ensures(Acc(list_pred(Result())))
     Ensures(ToSeq(Result()) == success_text())
 
@@ -144,7 +141,6 @@
     (the unchanged out-of-range-path callee's return). Its content is EXACTLY
     `out_of_range_text()`. Used only in the implementation. Provenance:
     mapping.md §3 / axiom_check.py."""
-    Requires(MustTerminate(2))
     Ensures(Acc(list_pred(Result())))
     Ensures(ToSeq(Result()) == out_of_range_text())
 
@@ -169,7 +165,6 @@
     """Materialise the raw-retrieval callee's value as a fresh code-point list
     (the unchanged not-all-present fallback's return). Its content is EXACTLY
     `raw_value()`. Used only in the implementation. Provenance: mapping.md §3."""
-    Requires(MustTerminate(2))
     Ensures(Acc(list_pred(Result())))
     Ensures(ToSeq(Result()) == raw_value())
 # axioms-end
@@ -201,7 +196,6 @@
     #                2 capacity-overflow.
     Requires(Implies(all_blank, all_present))
     Requires(kind == 0 or kind == 1 or kind == 2)
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     # The result is always a materialised code-point list.
@@ -243,5 +237,6 @@
         except DateCapacityOverflow:
             result = [48, 45, 48, 45, 48]  # type: List[int]
             return result
-    return retrieve_raw()
+    empty2 = []  # type: List[int]
+    return empty2
     # impl-end
```

Attack 6 — `atk6_oracle_echo.py` → rejected (same spec, does not verify — good)

```diff
@@ -56,7 +56,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class DateOutOfRange(Exception):
@@ -121,7 +120,6 @@
     reject kinds (these two are the ONLY ways it can fail). Provenance +
     executable soundness check: mapping.md §3 / axiom_check.py."""
     Requires(kind == 0 or kind == 1 or kind == 2)
-    Requires(MustTerminate(2))
     Ensures(kind == 0)
     Exsures(DateOutOfRange, kind == 1)
     Exsures(DateCapacityOverflow, kind == 2)
@@ -133,7 +131,6 @@
     constructed date as a fresh code-point list (the unchanged success-path
     callee's return). Its content is EXACTLY `success_text()`. Used only in the
     implementation. Provenance: mapping.md §3 / axiom_check.py."""
-    Requires(MustTerminate(2))
     Ensures(Acc(list_pred(Result())))
     Ensures(ToSeq(Result()) == success_text())
 
@@ -144,7 +141,6 @@
     (the unchanged out-of-range-path callee's return). Its content is EXACTLY
     `out_of_range_text()`. Used only in the implementation. Provenance:
     mapping.md §3 / axiom_check.py."""
-    Requires(MustTerminate(2))
     Ensures(Acc(list_pred(Result())))
     Ensures(ToSeq(Result()) == out_of_range_text())
 
@@ -169,7 +165,6 @@
     """Materialise the raw-retrieval callee's value as a fresh code-point list
     (the unchanged not-all-present fallback's return). Its content is EXACTLY
     `raw_value()`. Used only in the implementation. Provenance: mapping.md §3."""
-    Requires(MustTerminate(2))
     Ensures(Acc(list_pred(Result())))
     Ensures(ToSeq(Result()) == raw_value())
 # axioms-end
@@ -201,7 +196,6 @@
     #                2 capacity-overflow.
     Requires(Implies(all_blank, all_present))
     Requires(kind == 0 or kind == 1 or kind == 2)
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     # The result is always a materialised code-point list.
@@ -237,7 +231,7 @@
     if all_present:
         try:
             date_token = construct_date(kind)
-            return render_success()
+            return render_out_of_range()
         except DateOutOfRange:
             return render_out_of_range()
         except DateCapacityOverflow:
```

Attack 7 — `atk7_blank_raw.py` → rejected (same spec, does not verify — good)

```diff
@@ -56,7 +56,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class DateOutOfRange(Exception):
@@ -121,7 +120,6 @@
     reject kinds (these two are the ONLY ways it can fail). Provenance +
     executable soundness check: mapping.md §3 / axiom_check.py."""
     Requires(kind == 0 or kind == 1 or kind == 2)
-    Requires(MustTerminate(2))
     Ensures(kind == 0)
     Exsures(DateOutOfRange, kind == 1)
     Exsures(DateCapacityOverflow, kind == 2)
@@ -133,7 +131,6 @@
     constructed date as a fresh code-point list (the unchanged success-path
     callee's return). Its content is EXACTLY `success_text()`. Used only in the
     implementation. Provenance: mapping.md §3 / axiom_check.py."""
-    Requires(MustTerminate(2))
     Ensures(Acc(list_pred(Result())))
     Ensures(ToSeq(Result()) == success_text())
 
@@ -144,7 +141,6 @@
     (the unchanged out-of-range-path callee's return). Its content is EXACTLY
     `out_of_range_text()`. Used only in the implementation. Provenance:
     mapping.md §3 / axiom_check.py."""
-    Requires(MustTerminate(2))
     Ensures(Acc(list_pred(Result())))
     Ensures(ToSeq(Result()) == out_of_range_text())
 
@@ -169,7 +165,6 @@
     """Materialise the raw-retrieval callee's value as a fresh code-point list
     (the unchanged not-all-present fallback's return). Its content is EXACTLY
     `raw_value()`. Used only in the implementation. Provenance: mapping.md §3."""
-    Requires(MustTerminate(2))
     Ensures(Acc(list_pred(Result())))
     Ensures(ToSeq(Result()) == raw_value())
 # axioms-end
@@ -201,7 +196,6 @@
     #                2 capacity-overflow.
     Requires(Implies(all_blank, all_present))
     Requires(kind == 0 or kind == 1 or kind == 2)
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     # The result is always a materialised code-point list.
@@ -232,8 +226,7 @@
     # post-conditions-end
     # impl-start
     if all_blank:
-        empty = []  # type: List[int]
-        return empty
+        return retrieve_raw()
     if all_present:
         try:
             date_token = construct_date(kind)
```

Attack 8 — `atk_prepatch.py` → rejected (same spec, does not verify — good)

```diff
@@ -56,7 +56,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class DateOutOfRange(Exception):
@@ -121,7 +120,6 @@
     reject kinds (these two are the ONLY ways it can fail). Provenance +
     executable soundness check: mapping.md §3 / axiom_check.py."""
     Requires(kind == 0 or kind == 1 or kind == 2)
-    Requires(MustTerminate(2))
     Ensures(kind == 0)
     Exsures(DateOutOfRange, kind == 1)
     Exsures(DateCapacityOverflow, kind == 2)
@@ -133,7 +131,6 @@
     constructed date as a fresh code-point list (the unchanged success-path
     callee's return). Its content is EXACTLY `success_text()`. Used only in the
     implementation. Provenance: mapping.md §3 / axiom_check.py."""
-    Requires(MustTerminate(2))
     Ensures(Acc(list_pred(Result())))
     Ensures(ToSeq(Result()) == success_text())
 
@@ -144,7 +141,6 @@
     (the unchanged out-of-range-path callee's return). Its content is EXACTLY
     `out_of_range_text()`. Used only in the implementation. Provenance:
     mapping.md §3 / axiom_check.py."""
-    Requires(MustTerminate(2))
     Ensures(Acc(list_pred(Result())))
     Ensures(ToSeq(Result()) == out_of_range_text())
 
@@ -169,7 +165,6 @@
     """Materialise the raw-retrieval callee's value as a fresh code-point list
     (the unchanged not-all-present fallback's return). Its content is EXACTLY
     `raw_value()`. Used only in the implementation. Provenance: mapping.md §3."""
-    Requires(MustTerminate(2))
     Ensures(Acc(list_pred(Result())))
     Ensures(ToSeq(Result()) == raw_value())
 # axioms-end
@@ -201,7 +196,6 @@
     #                2 capacity-overflow.
     Requires(Implies(all_blank, all_present))
     Requires(kind == 0 or kind == 1 or kind == 2)
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     # The result is always a materialised code-point list.
@@ -240,8 +234,5 @@
             return render_success()
         except DateOutOfRange:
             return render_out_of_range()
-        except DateCapacityOverflow:
-            result = [48, 45, 48, 45, 48]  # type: List[int]
-            return result
     return retrieve_raw()
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-16667.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A composite widget reconstructs a single value from three independently
  submitted components (a year, a month and a day). It classifies the submitted
  components and produces an output as follows:

    * if all three components are submitted but BLANK, the widget reports an
      absent value;
    * if at least one of the three components was never submitted at all, the
      widget falls back to whatever raw value was submitted under the field's
      own (undecomposed) name — an unchanged retrieval callee whose result may
      be absent or arbitrary submitted text;
    * otherwise all three components carry text, and the widget hands them to
      the platform's calendar-date constructor inside a guarded region. That
      constructor can fail in two distinct ways:
        - it can reject the components as not forming a real calendar date
          (an out-of-range failure), or
        - it can reject the components because their magnitude is too large for
          the platform's native date representation (a capacity-overflow
          failure).

  The behaviour pinned here is that BOTH failure shapes are handled internally
  and converted into a normal textual result — NEITHER may escape as the
  constructor's own low-level error to crash the caller. Specifically:

    * an out-of-range failure yields a textual fallback derived from the
      submitted components (a permissive pseudo-date rendering); and
    * a capacity-overflow failure yields the constant textual sentinel "0-0-0"
      (the all-zero pseudo-date, code points [48,45,48,45,48]).

  A successfully constructed date is rendered to its canonical textual form.
  The not-all-present fallback and the two renderings are unchanged callees the
  widget invokes; each branch returns EXACTLY its callee's value.
  The discriminating obligation: on a capacity-overflow failure the result is
  EXACTLY the "0-0-0" sentinel and the operation returns normally, never
  propagating the low-level capacity error.

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing); the specification on the returned text is carried by `PSeq[int]` via
`ToSeq`. An absent value is modelled by the empty code-point list; every branch
that CAN yield text is pinned to its callee's exact text, and each such
rendering is non-empty, so emptiness ⇔ absent on every branch where the model
asserts emptiness. The not-all-present branch is pinned to the raw-retrieval
callee's value (which may itself be absent or arbitrary submitted text — the
model assumes NOTHING about it, not even emptiness or non-emptiness). The
calendar-date constructor is an unchanged callee the widget invokes; it is
axiomatised, and its two distinct rejections are user-defined exception classes
(a builtin exception in an `Exsures` crashes the translator). The renderings of
a successful date and of the out-of-range fallback, and the raw-retrieval
fallback, are unchanged callees, pinned to their own returned text/value
(never fabricated).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


class DateOutOfRange(Exception):
    """The calendar-date constructor's rejection of components that do not form
    a real calendar date (e.g. a day out of range for the month). User-defined
    stand-in for one low-level rejection class the constructor raises on some
    inputs (a builtin exception in an `Exsures` crashes the Nagini translator;
    mapping.md §2)."""
    pass


class DateCapacityOverflow(Exception):
    """The calendar-date constructor's rejection of components whose magnitude
    exceeds the platform's native date representation. User-defined stand-in for
    a second, distinct low-level rejection class the constructor raises on some
    inputs (a builtin exception in an `Exsures` crashes the Nagini translator;
    mapping.md §2)."""
    pass


# axioms-start
@Pure
@ContractOnly
def success_text() -> PSeq[int]:
    """The character content of the canonical textual rendering of a
    successfully constructed date (the unchanged success-path callee). Left
    ABSTRACT except that it is NON-EMPTY (a rendered date is never the empty
    string; this keeps the absent value, modelled as the empty list, distinct
    from every text-producing branch). The proof needs only that the success
    path returns EXACTLY this callee's text, never a value the proof fabricates.
    Provenance + executable soundness check: mapping.md §3 / axiom_check.py."""
    Ensures(len(Result()) > 0)


@Pure
@ContractOnly
def out_of_range_text() -> PSeq[int]:
    """The character content of the permissive textual fallback rendered from
    the submitted components on an out-of-range failure (the unchanged
    out-of-range-path callee). Left ABSTRACT except that it is NON-EMPTY (the
    fallback always renders three dash-separated component fields, so it is
    never the empty string). The proof needs only that the out-of-range path
    returns EXACTLY this callee's text, never a value the proof fabricates.
    Provenance + executable soundness check: mapping.md §3 / axiom_check.py."""
    Ensures(len(Result()) > 0)


@ContractOnly
def construct_date(kind: int) -> int:
    """The platform calendar-date constructor applied to the three submitted
    components (the unchanged callee the widget invokes when all components
    carry text). `kind` tags the construction outcome:

      * kind 0 — the constructor accepts the components and yields a date token;
      * kind 1 — the constructor rejects them as not forming a real calendar
        date (an out-of-range failure);
      * kind 2 — the constructor rejects them because their magnitude exceeds
        the platform's native date representation (a capacity-overflow failure).

    The weakest facts the proof needs: it returns normally on EXACTLY the
    accepted kind, and raises the matching distinct rejection on each of the two
    reject kinds (these two are the ONLY ways it can fail). Provenance +
    executable soundness check: mapping.md §3 / axiom_check.py."""
    Requires(kind == 0 or kind == 1 or kind == 2)
    Ensures(kind == 0)
    Exsures(DateOutOfRange, kind == 1)
    Exsures(DateCapacityOverflow, kind == 2)


@ContractOnly
def render_success() -> List[int]:
    """Materialise the canonical textual rendering of a successfully
    constructed date as a fresh code-point list (the unchanged success-path
    callee's return). Its content is EXACTLY `success_text()`. Used only in the
    implementation. Provenance: mapping.md §3 / axiom_check.py."""
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == success_text())


@ContractOnly
def render_out_of_range() -> List[int]:
    """Materialise the permissive textual fallback as a fresh code-point list
    (the unchanged out-of-range-path callee's return). Its content is EXACTLY
    `out_of_range_text()`. Used only in the implementation. Provenance:
    mapping.md §3 / axiom_check.py."""
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == out_of_range_text())


@Pure
@ContractOnly
def raw_value() -> PSeq[int]:
    """The raw value submitted under the field's own (undecomposed) name, as
    returned by the unchanged not-all-present retrieval callee. Left FULLY
    ABSTRACT: the real callee returns whatever was submitted under the bare
    field name — absent (the empty rendering) when nothing was posted under
    it, but possibly ARBITRARY NON-EMPTY text (e.g. a whole-date string posted
    under the bare name). The model assumes NOTHING about its content; the
    proof needs only that the not-all-present branch returns EXACTLY this
    callee's value, never a value the proof fabricates. Provenance:
    mapping.md §3."""
    Ensures(len(Result()) >= 0)


@ContractOnly
def retrieve_raw() -> List[int]:
    """Materialise the raw-retrieval callee's value as a fresh code-point list
    (the unchanged not-all-present fallback's return). Its content is EXACTLY
    `raw_value()`. Used only in the implementation. Provenance: mapping.md §3."""
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == raw_value())
# axioms-end


# pure-start
@Pure
def zero_zero_zero() -> PSeq[int]:
    """The constant all-zero pseudo-date sentinel "0-0-0" as Unicode code points:
    '0'(48) '-'(45) '0'(48) '-'(45) '0'(48)."""
    return PSeq(48, 45, 48, 45, 48)


@Pure
def absent_text() -> PSeq[int]:
    """The empty code-point sequence — the rendering of an absent value."""
    return PSeq(48).take(0)
# pure-end


def value_from_components(all_blank: bool, all_present: bool,
                          kind: int) -> List[int]:
    # pre-conditions-start
    # `all_blank`  — every submitted component is present but blank.
    # `all_present`— all three components were submitted (none absent); a blank
    #                component is still present, so all_blank implies all_present.
    # `kind`       — the date-construction outcome reached only when all
    #                components carry text: 0 accepted, 1 out-of-range,
    #                2 capacity-overflow.
    Requires(Implies(all_blank, all_present))
    Requires(kind == 0 or kind == 1 or kind == 2)
    # pre-conditions-end
    # post-conditions-start
    # The result is always a materialised code-point list.
    Ensures(Acc(list_pred(Result())))
    # The all-blank case reports an absent value (the empty rendering); the
    # not-all-present case returns EXACTLY the raw value submitted under the
    # field's own name (the unchanged retrieval callee — possibly absent,
    # possibly arbitrary text; nothing about its content is assumed). No date
    # is constructed and nothing is raised on either branch.
    Ensures(Implies(all_blank, ToSeq(Result()) == absent_text()))
    Ensures(Implies(not all_present, ToSeq(Result()) == raw_value()))
    # When all components carry text (all_present and not all_blank), the date
    # constructor runs and EVERY outcome returns a NON-EMPTY textual result —
    # NEITHER rejection escapes (no Exsures clause => this method never raises):
    Ensures(Implies(all_present and not all_blank, len(ToSeq(Result())) > 0))
    # A capacity-overflow failure (kind 2) yields EXACTLY the "0-0-0" sentinel —
    # the discriminating obligation the desired behaviour pins.
    Ensures(Implies(all_present and not all_blank and kind == 2,
                    ToSeq(Result()) == zero_zero_zero()))
    # A successfully constructed date (kind 0) renders to EXACTLY the success
    # callee's text; an out-of-range failure (kind 1) renders to EXACTLY the
    # out-of-range fallback callee's text. Both are pinned to their callee (not
    # fabricated).
    Ensures(Implies(all_present and not all_blank and kind == 0,
                    ToSeq(Result()) == success_text()))
    Ensures(Implies(all_present and not all_blank and kind == 1,
                    ToSeq(Result()) == out_of_range_text()))
    # post-conditions-end
    # impl-start
    if all_blank:
        empty = []  # type: List[int]
        return empty
    if all_present:
        try:
            date_token = construct_date(kind)
            return render_success()
        except DateOutOfRange:
            return render_out_of_range()
        except DateCapacityOverflow:
            result = [48, 45, 48, 45, 48]  # type: List[int]
            return result
    return retrieve_raw()
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

 All 8 attack files have BYTE-IDENTICAL spec regions to the frozen model (verified programmatically by splitting on impl-start/impl-end).

atk1_dispatch_on_kind.py => CANDIDATE (shares spec AND verifies, 15.9s). Dispatch on `kind` (0->render_success, 1->render_out_of_range, 2->[48,45,48,45,48]) without calling construct_date. This is a benign ECHO: to observe `kind` at runtime you must run datetime.date and catch its two exception classes, so its faithful refinement IS the gold control flow.
- atk2_wrong_sentinel.py => NOT-A-COUNTEREXAMPLE (does not verify). kind2 returns 7-codepoint '0-0-0-0'; violates Ensures(...==zero_zero_zero()).
- atk3_swap_handlers.py => NOT-A-COUNTEREXAMPLE (does not verify). kind1->sentinel, kind2->out_of_range text; violates the two kind-pinned postconditions.
- atk4_collapse_handler.py => NOT-A-COUNTEREXAMPLE (does not verify). Both rejections -> out_of_range text; on kind2 != zero_zero_zero.
- atk5_notpresent_empty.py => NOT-A-COUNTEREXAMPLE (does not verify). not-all-present returns []; raw_value() is fully abstract (may be non-empty) so ==raw_value() unprovable.
- atk6_oracle_echo.py => NOT-A-COUNTEREXAMPLE (does not verify). kind0 success path echoes out_of_range text; violates Ensures(...==success_text()).
- atk7_blank_raw.py => NOT-A-COUNTEREXAMPLE (does not verify). all-blank returns retrieve_raw(); may be non-empty so ==absent_text() unprovable.
- atk_prepatch.py => NOT-A-COUNTEREXAMPLE (does not verify) => PREPATCH BUG REPRODUCED. Omits `except DateCapacityOverflow`; on kind2 the constructor's DateCapacityOverflow escapes an Exsures-free method => 'method raises no exceptions' fails. Exactly the change the spec senses (G-DIFF).

MANDATORY RESOLVE OF THE ONE CANDIDATE (atk1): materialized its faithful refined patch = atk1_faithful_patch.diff (sha1[:10]=5ad2a44ae3, byte-identical to the gold patch.diff; confirmed by diff). Executed the OFFICIAL harness:
  python -c 'from swebench_unified.harness import run_resolve; r=run_resolve("django__django-16667", <patch>, run_id="sbu-audit-eq-16667-atk1", timeout=1800)'
fresh run_id sbu-audit-eq-16667-atk1-5ad2a44ae3-p1161142 => RESOLVED=True, COMPLETED=True (parsed ResolveResult printed before the harness deleted its single-use run dir per harness.py; a prior independent gold resolve report on disk also shows resolved=True). So the only verifying same-spec impl RESOLVES => verify=>correct holds; spec NOT broken.

**POSITIVE CONTROL:** positive_control.py (= frozen model.py) => `bash scripts/nagini_verify.sh` => Verification successful (14.48s), EXIT 0.

G-AX (A-consumed soundness): `python axiom_check.py` => exit 0; {OverflowError, ValueError} exhaustive for integer args over 9+11+6+9 boundary + 200000 fuzz triples (outcomes {0:118,1:25164,2:174718}), OverflowError precedes range ValueError (F2P sys.maxsize+1 => kind2), sentinel=='0-0-0'==[48,45,48,45,48], strftime/pseudo-ISO renderings non-empty.

**REFINEMENT.MD AUDIT:** legs A1(R), A2(R+I), A3(R+A-consumed), A4(A-consumed), A5(R+A-consumed), A6(R+A-consumed), A7(R+I). NO kind-3 (Section B explicitly: the changed op is the added except-clause, modeled DIRECTLY at A7 driven by A4's Exsures). A-legs correspond to real callees: construct_date<->datetime.date, render_success/success_text<->strftime, render_out_of_range/out_of_range_text<->'%s-%s-%s'%..., retrieve_raw/raw_value<->data.get(name) (fully abstract, faithful whether None or arbitrary text). Correspondence holds; G-AX validates the exhaustiveness/precedence crux.

Every reachable input class is pinned to an EXACT output (empty / raw_value / success_text / out_of_range_text / zero_zero_zero), which is why every semantic deviation is rejected and the only survivor is a behavior-preserving echo. VERDICT: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk2_wrong_sentinel.py`, `atk3_swap_handlers.py`, `atk4_collapse_handler.py`, `atk5_notpresent_empty.py`, `atk6_oracle_echo.py`, `atk7_blank_raw.py`, `atk_prepatch.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk1_dispatch_on_kind.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The spec is not broken: no verifying same-spec impl has a faithful refined patch that fails to resolve.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk1_dispatch_on_kind.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 2 — `atk2_wrong_sentinel.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk3_swap_handlers.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk4_collapse_handler.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk5_notpresent_empty.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk6_oracle_echo.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk7_blank_raw.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_prepatch.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-16667.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A composite widget reconstructs a single value from three independently
  submitted components (a year, a month and a day). It classifies the submitted
  components and produces an output as follows:

    * if all three components are submitted but BLANK, the widget reports an
      absent value;
    * if at least one of the three components was never submitted at all, the
      widget falls back to whatever raw value was submitted under the field's
      own (undecomposed) name — an unchanged retrieval callee whose result may
      be absent or arbitrary submitted text;
    * otherwise all three components carry text, and the widget hands them to
      the platform's calendar-date constructor inside a guarded region. That
      constructor can fail in two distinct ways:
        - it can reject the components as not forming a real calendar date
          (an out-of-range failure), or
        - it can reject the components because their magnitude is too large for
          the platform's native date representation (a capacity-overflow
          failure).

  The behaviour pinned here is that BOTH failure shapes are handled internally
  and converted into a normal textual result — NEITHER may escape as the
  constructor's own low-level error to crash the caller. Specifically:

    * an out-of-range failure yields a textual fallback derived from the
      submitted components (a permissive pseudo-date rendering); and
    * a capacity-overflow failure yields the constant textual sentinel "0-0-0"
      (the all-zero pseudo-date, code points [48,45,48,45,48]).

  A successfully constructed date is rendered to its canonical textual form.
  The not-all-present fallback and the two renderings are unchanged callees the
  widget invokes; each branch returns EXACTLY its callee's value.
  The discriminating obligation: on a capacity-overflow failure the result is
  EXACTLY the "0-0-0" sentinel and the operation returns normally, never
  propagating the low-level capacity error.

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing); the specification on the returned text is carried by `PSeq[int]` via
`ToSeq`. An absent value is modelled by the empty code-point list; every branch
that CAN yield text is pinned to its callee's exact text, and each such
rendering is non-empty, so emptiness ⇔ absent on every branch where the model
asserts emptiness. The not-all-present branch is pinned to the raw-retrieval
callee's value (which may itself be absent or arbitrary submitted text — the
model assumes NOTHING about it, not even emptiness or non-emptiness). The
calendar-date constructor is an unchanged callee the widget invokes; it is
axiomatised, and its two distinct rejections are user-defined exception classes
(a builtin exception in an `Exsures` crashes the translator). The renderings of
a successful date and of the out-of-range fallback, and the raw-retrieval
fallback, are unchanged callees, pinned to their own returned text/value
(never fabricated).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


class DateOutOfRange(Exception):
    """The calendar-date constructor's rejection of components that do not form
    a real calendar date (e.g. a day out of range for the month). User-defined
    stand-in for one low-level rejection class the constructor raises on some
    inputs (a builtin exception in an `Exsures` crashes the Nagini translator;
    mapping.md §2)."""
    pass


class DateCapacityOverflow(Exception):
    """The calendar-date constructor's rejection of components whose magnitude
    exceeds the platform's native date representation. User-defined stand-in for
    a second, distinct low-level rejection class the constructor raises on some
    inputs (a builtin exception in an `Exsures` crashes the Nagini translator;
    mapping.md §2)."""
    pass


# axioms-start
@Pure
@ContractOnly
def success_text() -> PSeq[int]:
    """The character content of the canonical textual rendering of a
    successfully constructed date (the unchanged success-path callee). Left
    ABSTRACT except that it is NON-EMPTY (a rendered date is never the empty
    string; this keeps the absent value, modelled as the empty list, distinct
    from every text-producing branch). The proof needs only that the success
    path returns EXACTLY this callee's text, never a value the proof fabricates.
    Provenance + executable soundness check: mapping.md §3 / axiom_check.py."""
    Ensures(len(Result()) > 0)


@Pure
@ContractOnly
def out_of_range_text() -> PSeq[int]:
    """The character content of the permissive textual fallback rendered from
    the submitted components on an out-of-range failure (the unchanged
    out-of-range-path callee). Left ABSTRACT except that it is NON-EMPTY (the
    fallback always renders three dash-separated component fields, so it is
    never the empty string). The proof needs only that the out-of-range path
    returns EXACTLY this callee's text, never a value the proof fabricates.
    Provenance + executable soundness check: mapping.md §3 / axiom_check.py."""
    Ensures(len(Result()) > 0)


@ContractOnly
def construct_date(kind: int) -> int:
    """The platform calendar-date constructor applied to the three submitted
    components (the unchanged callee the widget invokes when all components
    carry text). `kind` tags the construction outcome:

      * kind 0 — the constructor accepts the components and yields a date token;
      * kind 1 — the constructor rejects them as not forming a real calendar
        date (an out-of-range failure);
      * kind 2 — the constructor rejects them because their magnitude exceeds
        the platform's native date representation (a capacity-overflow failure).

    The weakest facts the proof needs: it returns normally on EXACTLY the
    accepted kind, and raises the matching distinct rejection on each of the two
    reject kinds (these two are the ONLY ways it can fail). Provenance +
    executable soundness check: mapping.md §3 / axiom_check.py."""
    Requires(kind == 0 or kind == 1 or kind == 2)
    Ensures(kind == 0)
    Exsures(DateOutOfRange, kind == 1)
    Exsures(DateCapacityOverflow, kind == 2)


@ContractOnly
def render_success() -> List[int]:
    """Materialise the canonical textual rendering of a successfully
    constructed date as a fresh code-point list (the unchanged success-path
    callee's return). Its content is EXACTLY `success_text()`. Used only in the
    implementation. Provenance: mapping.md §3 / axiom_check.py."""
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == success_text())


@ContractOnly
def render_out_of_range() -> List[int]:
    """Materialise the permissive textual fallback as a fresh code-point list
    (the unchanged out-of-range-path callee's return). Its content is EXACTLY
    `out_of_range_text()`. Used only in the implementation. Provenance:
    mapping.md §3 / axiom_check.py."""
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == out_of_range_text())


@Pure
@ContractOnly
def raw_value() -> PSeq[int]:
    """The raw value submitted under the field's own (undecomposed) name, as
    returned by the unchanged not-all-present retrieval callee. Left FULLY
    ABSTRACT: the real callee returns whatever was submitted under the bare
    field name — absent (the empty rendering) when nothing was posted under
    it, but possibly ARBITRARY NON-EMPTY text (e.g. a whole-date string posted
    under the bare name). The model assumes NOTHING about its content; the
    proof needs only that the not-all-present branch returns EXACTLY this
    callee's value, never a value the proof fabricates. Provenance:
    mapping.md §3."""
    Ensures(len(Result()) >= 0)


@ContractOnly
def retrieve_raw() -> List[int]:
    """Materialise the raw-retrieval callee's value as a fresh code-point list
    (the unchanged not-all-present fallback's return). Its content is EXACTLY
    `raw_value()`. Used only in the implementation. Provenance: mapping.md §3."""
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == raw_value())
# axioms-end


# pure-start
@Pure
def zero_zero_zero() -> PSeq[int]:
    """The constant all-zero pseudo-date sentinel "0-0-0" as Unicode code points:
    '0'(48) '-'(45) '0'(48) '-'(45) '0'(48)."""
    return PSeq(48, 45, 48, 45, 48)


@Pure
def absent_text() -> PSeq[int]:
    """The empty code-point sequence — the rendering of an absent value."""
    return PSeq(48).take(0)
# pure-end


def value_from_components(all_blank: bool, all_present: bool,
                          kind: int) -> List[int]:
    # pre-conditions-start
    # `all_blank`  — every submitted component is present but blank.
    # `all_present`— all three components were submitted (none absent); a blank
    #                component is still present, so all_blank implies all_present.
    # `kind`       — the date-construction outcome reached only when all
    #                components carry text: 0 accepted, 1 out-of-range,
    #                2 capacity-overflow.
    Requires(Implies(all_blank, all_present))
    Requires(kind == 0 or kind == 1 or kind == 2)
    # pre-conditions-end
    # post-conditions-start
    # The result is always a materialised code-point list.
    Ensures(Acc(list_pred(Result())))
    # The all-blank case reports an absent value (the empty rendering); the
    # not-all-present case returns EXACTLY the raw value submitted under the
    # field's own name (the unchanged retrieval callee — possibly absent,
    # possibly arbitrary text; nothing about its content is assumed). No date
    # is constructed and nothing is raised on either branch.
    Ensures(Implies(all_blank, ToSeq(Result()) == absent_text()))
    Ensures(Implies(not all_present, ToSeq(Result()) == raw_value()))
    # When all components carry text (all_present and not all_blank), the date
    # constructor runs and EVERY outcome returns a NON-EMPTY textual result —
    # NEITHER rejection escapes (no Exsures clause => this method never raises):
    Ensures(Implies(all_present and not all_blank, len(ToSeq(Result())) > 0))
    # A capacity-overflow failure (kind 2) yields EXACTLY the "0-0-0" sentinel —
    # the discriminating obligation the desired behaviour pins.
    Ensures(Implies(all_present and not all_blank and kind == 2,
                    ToSeq(Result()) == zero_zero_zero()))
    # A successfully constructed date (kind 0) renders to EXACTLY the success
    # callee's text; an out-of-range failure (kind 1) renders to EXACTLY the
    # out-of-range fallback callee's text. Both are pinned to their callee (not
    # fabricated).
    Ensures(Implies(all_present and not all_blank and kind == 0,
                    ToSeq(Result()) == success_text()))
    Ensures(Implies(all_present and not all_blank and kind == 1,
                    ToSeq(Result()) == out_of_range_text()))
    # post-conditions-end
    # impl-start
    if all_blank:
        empty = []  # type: List[int]
        return empty
    if all_present:
        try:
            date_token = construct_date(kind)
            return render_success()
        except DateOutOfRange:
            return render_out_of_range()
        except DateCapacityOverflow:
            result = [48, 45, 48, 45, 48]  # type: List[int]
            return result
    return retrieve_raw()
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

 All 8 attack files have BYTE-IDENTICAL spec regions to the frozen model (verified programmatically by splitting on impl-start/impl-end).

atk1_dispatch_on_kind.py => CANDIDATE (shares spec AND verifies, 15.9s). Dispatch on `kind` (0->render_success, 1->render_out_of_range, 2->[48,45,48,45,48]) without calling construct_date. This is a benign ECHO: to observe `kind` at runtime you must run datetime.date and catch its two exception classes, so its faithful refinement IS the gold control flow.
- atk2_wrong_sentinel.py => NOT-A-COUNTEREXAMPLE (does not verify). kind2 returns 7-codepoint '0-0-0-0'; violates Ensures(...==zero_zero_zero()).
- atk3_swap_handlers.py => NOT-A-COUNTEREXAMPLE (does not verify). kind1->sentinel, kind2->out_of_range text; violates the two kind-pinned postconditions.
- atk4_collapse_handler.py => NOT-A-COUNTEREXAMPLE (does not verify). Both rejections -> out_of_range text; on kind2 != zero_zero_zero.
- atk5_notpresent_empty.py => NOT-A-COUNTEREXAMPLE (does not verify). not-all-present returns []; raw_value() is fully abstract (may be non-empty) so ==raw_value() unprovable.
- atk6_oracle_echo.py => NOT-A-COUNTEREXAMPLE (does not verify). kind0 success path echoes out_of_range text; violates Ensures(...==success_text()).
- atk7_blank_raw.py => NOT-A-COUNTEREXAMPLE (does not verify). all-blank returns retrieve_raw(); may be non-empty so ==absent_text() unprovable.
- atk_prepatch.py => NOT-A-COUNTEREXAMPLE (does not verify) => PREPATCH BUG REPRODUCED. Omits `except DateCapacityOverflow`; on kind2 the constructor's DateCapacityOverflow escapes an Exsures-free method => 'method raises no exceptions' fails. Exactly the change the spec senses (G-DIFF).

MANDATORY RESOLVE OF THE ONE CANDIDATE (atk1): materialized its faithful refined patch = atk1_faithful_patch.diff (sha1[:10]=5ad2a44ae3, byte-identical to the gold patch.diff; confirmed by diff). Executed the OFFICIAL harness:
  python -c 'from swebench_unified.harness import run_resolve; r=run_resolve("django__django-16667", <patch>, run_id="sbu-audit-eq-16667-atk1", timeout=1800)'
fresh run_id sbu-audit-eq-16667-atk1-5ad2a44ae3-p1161142 => RESOLVED=True, COMPLETED=True (parsed ResolveResult printed before the harness deleted its single-use run dir per harness.py; a prior independent gold resolve report on disk also shows resolved=True). So the only verifying same-spec impl RESOLVES => verify=>correct holds; spec NOT broken.

**POSITIVE CONTROL:** positive_control.py (= frozen model.py) => `bash scripts/nagini_verify.sh` => Verification successful (14.48s), EXIT 0.

G-AX (A-consumed soundness): `python axiom_check.py` => exit 0; {OverflowError, ValueError} exhaustive for integer args over 9+11+6+9 boundary + 200000 fuzz triples (outcomes {0:118,1:25164,2:174718}), OverflowError precedes range ValueError (F2P sys.maxsize+1 => kind2), sentinel=='0-0-0'==[48,45,48,45,48], strftime/pseudo-ISO renderings non-empty.

**REFINEMENT.MD AUDIT:** legs A1(R), A2(R+I), A3(R+A-consumed), A4(A-consumed), A5(R+A-consumed), A6(R+A-consumed), A7(R+I). NO kind-3 (Section B explicitly: the changed op is the added except-clause, modeled DIRECTLY at A7 driven by A4's Exsures). A-legs correspond to real callees: construct_date<->datetime.date, render_success/success_text<->strftime, render_out_of_range/out_of_range_text<->'%s-%s-%s'%..., retrieve_raw/raw_value<->data.get(name) (fully abstract, faithful whether None or arbitrary text). Correspondence holds; G-AX validates the exhaustiveness/precedence crux.

Every reachable input class is pinned to an EXACT output (empty / raw_value / success_text / out_of_range_text / zero_zero_zero), which is why every semantic deviation is rejected and the only survivor is a behavior-preserving echo. VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (G-PANEL-2) audit of the modeled function value_from_components vs the real patched callee SelectDateWidget.value_from_datadict (django/forms/widgets.py, base_commit 02c356f2..., gold patch adds `except OverflowError: return "0-0-0"`).

**Method:** applied patch.diff to a fresh /tmp copy of the repo, then ran a differential harness computing the model's predicted output per the spec's Ensures (with the abstract callees bound to the same real repo functions the spec pins them to: datetime.date, strftime with repo input-format derivation, %-format fallback, data.get(name)) against the REAL patched widget. Covered a 10,285-input boundary cross-product (years/months/days incl. None, "", 0, valid, month 13, day 32, negatives, sys.maxsize, sys.maxsize+1, -sys.maxsize-2, `2**200`, non-numeric, unicode/whitespace, plus raw-name datadict variants) AND 200,000 fuzz probes (seed 16667). Result: 0 mismatches on all 210,285 probes; the real widget never escaped with an uncaught exception.

Per-obligation check — every concrete spec claim matches reality: all_blank→empty ↔ None; kind==2 (OverflowError, e.g. sys.maxsize+1 / `2**200`)→[48,45,48,45,48] ↔ "0-0-0"; kind==0→success render, kind==1→pseudo-ISO fallback (both abstract, pinned to real non-empty callees); not-all-present→raw_value() FULLY ABSTRACT ↔ data.get(name) (None or arbitrary text — model over-claims nothing). The 'never raises' contract (no Exsures) holds: every int()/datetime.date failure is caught; no uncaught exception observed, including ٤, 1_0, whitespace, huge magnitudes. Preconditions Implies(all_blank,all_present) and kind∈{0,1,2} match reality (blank is non-None; integer-arg datetime.date fails only via ValueError/OverflowError, overflow preceding range). Spec region confirmed byte-identical across the recorded attacks. The spec is neither too strong nor drifting: no input where the modeled function disagrees with the real callee. Verdict FAITHFUL.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery).
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec-view leakage screen for django__django-16667 (nagini). The consumer spec view = model.py with the impl region elided. Mechanical G-LEAK screen returns passed=True (0 hard failures): no diff markers, no gold-patch line reproduced, no patched file path/module, no spec-view identifier or comment echoing a patched repo symbol, no narration.

Public problem_statement already discloses the FULL localization of the gold edit: class SelectDateWidget, method value_from_datadict, file django/forms/widgets.py, the exact crashing line `date_value = datetime.date(int(y), int(m), int(d))`, that it raises OverflowError, and the sys.maxsize+1 trigger. So where/what/which-exception is entirely public.

The spec view is STRICTLY LESS localizing than the public issue: it names NONE of those repo symbols (checked: no SelectDateWidget, value_from_datadict, widgets.py, datetime, OverflowError, ValueError, strftime, data.get, sys.maxsize, input_format). It abstracts to 'composite widget', 'calendar-date constructor', 'capacity-overflow failure', 'out-of-range failure'. The only 'django'/'.py' hits are the instance-id header (django__django-16667) and bundle-file citations (axiom_check.py, mapping.md) — neither leaks the edit.

The one thing the spec adds beyond the problem statement is the behavioral TARGET value: capacity-overflow => the '0-0-0' sentinel, returning normally. Pinning the desired output is the definition of the specification task, not a leak of the gold edit — it reveals no diff, no file, no symbol, and no mechanism (never says 'add an except handler'); a solver still must localize and construct the fix. This does not trip the lexical screen and is not a semantic leak beyond what a faithful behavioral contract must state. relaxed_leakage flag is absent/None; no relaxation is needed or claimed. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.
