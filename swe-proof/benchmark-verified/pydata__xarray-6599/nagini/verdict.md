# P2 adversarial audit — pydata__xarray-6599

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk1_span_through_measure.py`, `atk2_point_offbyone.py`, `atk3_span_plus1.py`, `atk4_span_empty.py`, `atk5_point_identity.py`, `atk6_other_double.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk7_span_via_magread_correct.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk1_span_through_measure.py` → rejected (same spec, does not verify — good)

```diff
@@ -125,9 +125,7 @@
     Ensures(Implies(kind == OTHER, ToSeq(Result()) == ToSeq(values)))
     # post-conditions-end
     # impl-start
-    if kind == TIME_POINT:
-        # numeric via the instant-relative measurement (the unchanged callee):
-        # hold its result, the elapsed magnitudes since the reference instant
+    if kind == TIME_POINT or kind == TIME_SPAN:
         measured = elapsed_since(kind, ToSeq(values), reference)
         result = []  # type: List[int]
         i = 0
@@ -136,7 +134,6 @@
             Invariant(Acc(list_pred(values), 1 / 2))
             Invariant(Acc(list_pred(result)))
             Invariant(0 <= i and i <= len(values))
-            Invariant(well_defined_magnitudes(ToSeq(values)))
             Invariant(measured == elapsed_since(kind, ToSeq(values), reference))
             Invariant(len(measured) == len(values))
             Invariant(ToSeq(result) == measured.take(i))
@@ -146,25 +143,7 @@
         Assert(ToSeq(result) == measured.take(len(values)))
         Assert(measured.take(len(values)) == measured)
         return result
-    elif kind == TIME_SPAN:
-        # read each duration's magnitude directly (the new branch): the float
-        # magnitude equals the input magnitude in the base resolution
-        out = []  # type: List[int]
-        j = 0
-        while j < len(values):
-            # invariants-start
-            Invariant(Acc(list_pred(values), 1 / 2))
-            Invariant(Acc(list_pred(out)))
-            Invariant(0 <= j and j <= len(values))
-            Invariant(ToSeq(out) == ToSeq(values).take(j))
-            # invariants-end
-            out.append(values[j])
-            j = j + 1
-        Assert(ToSeq(out) == ToSeq(values).take(len(values)))
-        Assert(ToSeq(values).take(len(values)) == ToSeq(values))
-        return out
     else:
-        # already numeric: passthrough
         passthrough = []  # type: List[int]
         m = 0
         while m < len(values):
```

Attack 2 — `atk2_point_offbyone.py` → rejected (same spec, does not verify — good)

```diff
@@ -126,12 +126,10 @@
     # post-conditions-end
     # impl-start
     if kind == TIME_POINT:
-        # numeric via the instant-relative measurement (the unchanged callee):
-        # hold its result, the elapsed magnitudes since the reference instant
         measured = elapsed_since(kind, ToSeq(values), reference)
         result = []  # type: List[int]
         i = 0
-        while i < len(values):
+        while i < len(values) - 1:
             # invariants-start
             Invariant(Acc(list_pred(values), 1 / 2))
             Invariant(Acc(list_pred(result)))
@@ -143,12 +141,8 @@
             # invariants-end
             result.append(measured[i])
             i = i + 1
-        Assert(ToSeq(result) == measured.take(len(values)))
-        Assert(measured.take(len(values)) == measured)
         return result
     elif kind == TIME_SPAN:
-        # read each duration's magnitude directly (the new branch): the float
-        # magnitude equals the input magnitude in the base resolution
         out = []  # type: List[int]
         j = 0
         while j < len(values):
@@ -164,7 +158,6 @@
         Assert(ToSeq(values).take(len(values)) == ToSeq(values))
         return out
     else:
-        # already numeric: passthrough
         passthrough = []  # type: List[int]
         m = 0
         while m < len(values):
```

Attack 3 — `atk3_span_plus1.py` → rejected (same spec, does not verify — good)

```diff
@@ -126,8 +126,6 @@
     # post-conditions-end
     # impl-start
     if kind == TIME_POINT:
-        # numeric via the instant-relative measurement (the unchanged callee):
-        # hold its result, the elapsed magnitudes since the reference instant
         measured = elapsed_since(kind, ToSeq(values), reference)
         result = []  # type: List[int]
         i = 0
@@ -147,8 +145,6 @@
         Assert(measured.take(len(values)) == measured)
         return result
     elif kind == TIME_SPAN:
-        # read each duration's magnitude directly (the new branch): the float
-        # magnitude equals the input magnitude in the base resolution
         out = []  # type: List[int]
         j = 0
         while j < len(values):
@@ -156,15 +152,11 @@
             Invariant(Acc(list_pred(values), 1 / 2))
             Invariant(Acc(list_pred(out)))
             Invariant(0 <= j and j <= len(values))
-            Invariant(ToSeq(out) == ToSeq(values).take(j))
             # invariants-end
-            out.append(values[j])
+            out.append(values[j] + 1)
             j = j + 1
-        Assert(ToSeq(out) == ToSeq(values).take(len(values)))
-        Assert(ToSeq(values).take(len(values)) == ToSeq(values))
         return out
     else:
-        # already numeric: passthrough
         passthrough = []  # type: List[int]
         m = 0
         while m < len(values):
```

Attack 4 — `atk4_span_empty.py` → rejected (same spec, does not verify — good)

```diff
@@ -126,8 +126,6 @@
     # post-conditions-end
     # impl-start
     if kind == TIME_POINT:
-        # numeric via the instant-relative measurement (the unchanged callee):
-        # hold its result, the elapsed magnitudes since the reference instant
         measured = elapsed_since(kind, ToSeq(values), reference)
         result = []  # type: List[int]
         i = 0
@@ -147,24 +145,9 @@
         Assert(measured.take(len(values)) == measured)
         return result
     elif kind == TIME_SPAN:
-        # read each duration's magnitude directly (the new branch): the float
-        # magnitude equals the input magnitude in the base resolution
         out = []  # type: List[int]
-        j = 0
-        while j < len(values):
-            # invariants-start
-            Invariant(Acc(list_pred(values), 1 / 2))
-            Invariant(Acc(list_pred(out)))
-            Invariant(0 <= j and j <= len(values))
-            Invariant(ToSeq(out) == ToSeq(values).take(j))
-            # invariants-end
-            out.append(values[j])
-            j = j + 1
-        Assert(ToSeq(out) == ToSeq(values).take(len(values)))
-        Assert(ToSeq(values).take(len(values)) == ToSeq(values))
         return out
     else:
-        # already numeric: passthrough
         passthrough = []  # type: List[int]
         m = 0
         while m < len(values):
```

Attack 5 — `atk5_point_identity.py` → rejected (same spec, does not verify — good)

```diff
@@ -126,9 +126,6 @@
     # post-conditions-end
     # impl-start
     if kind == TIME_POINT:
-        # numeric via the instant-relative measurement (the unchanged callee):
-        # hold its result, the elapsed magnitudes since the reference instant
-        measured = elapsed_since(kind, ToSeq(values), reference)
         result = []  # type: List[int]
         i = 0
         while i < len(values):
@@ -136,19 +133,14 @@
             Invariant(Acc(list_pred(values), 1 / 2))
             Invariant(Acc(list_pred(result)))
             Invariant(0 <= i and i <= len(values))
-            Invariant(well_defined_magnitudes(ToSeq(values)))
-            Invariant(measured == elapsed_since(kind, ToSeq(values), reference))
-            Invariant(len(measured) == len(values))
-            Invariant(ToSeq(result) == measured.take(i))
+            Invariant(ToSeq(result) == ToSeq(values).take(i))
             # invariants-end
-            result.append(measured[i])
+            result.append(values[i])
             i = i + 1
-        Assert(ToSeq(result) == measured.take(len(values)))
-        Assert(measured.take(len(values)) == measured)
+        Assert(ToSeq(result) == ToSeq(values).take(len(values)))
+        Assert(ToSeq(values).take(len(values)) == ToSeq(values))
         return result
     elif kind == TIME_SPAN:
-        # read each duration's magnitude directly (the new branch): the float
-        # magnitude equals the input magnitude in the base resolution
         out = []  # type: List[int]
         j = 0
         while j < len(values):
@@ -164,7 +156,6 @@
         Assert(ToSeq(values).take(len(values)) == ToSeq(values))
         return out
     else:
-        # already numeric: passthrough
         passthrough = []  # type: List[int]
         m = 0
         while m < len(values):
```

Attack 6 — `atk6_other_double.py` → rejected (same spec, does not verify — good)

```diff
@@ -126,8 +126,6 @@
     # post-conditions-end
     # impl-start
     if kind == TIME_POINT:
-        # numeric via the instant-relative measurement (the unchanged callee):
-        # hold its result, the elapsed magnitudes since the reference instant
         measured = elapsed_since(kind, ToSeq(values), reference)
         result = []  # type: List[int]
         i = 0
@@ -147,8 +145,6 @@
         Assert(measured.take(len(values)) == measured)
         return result
     elif kind == TIME_SPAN:
-        # read each duration's magnitude directly (the new branch): the float
-        # magnitude equals the input magnitude in the base resolution
         out = []  # type: List[int]
         j = 0
         while j < len(values):
@@ -164,7 +160,6 @@
         Assert(ToSeq(values).take(len(values)) == ToSeq(values))
         return out
     else:
-        # already numeric: passthrough
         passthrough = []  # type: List[int]
         m = 0
         while m < len(values):
@@ -172,11 +167,8 @@
             Invariant(Acc(list_pred(values), 1 / 2))
             Invariant(Acc(list_pred(passthrough)))
             Invariant(0 <= m and m <= len(values))
-            Invariant(ToSeq(passthrough) == ToSeq(values).take(m))
             # invariants-end
-            passthrough.append(values[m])
+            passthrough.append(values[m] + values[m])
             m = m + 1
-        Assert(ToSeq(passthrough) == ToSeq(values).take(len(values)))
-        Assert(ToSeq(values).take(len(values)) == ToSeq(values))
         return passthrough
     # impl-end
```

Attack 7 — `atk7_span_via_magread_correct.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -126,8 +126,6 @@
     # post-conditions-end
     # impl-start
     if kind == TIME_POINT:
-        # numeric via the instant-relative measurement (the unchanged callee):
-        # hold its result, the elapsed magnitudes since the reference instant
         measured = elapsed_since(kind, ToSeq(values), reference)
         result = []  # type: List[int]
         i = 0
@@ -147,8 +145,7 @@
         Assert(measured.take(len(values)) == measured)
         return result
     elif kind == TIME_SPAN:
-        # read each duration's magnitude directly (the new branch): the float
-        # magnitude equals the input magnitude in the base resolution
+        mags = magnitude_read(ToSeq(values))
         out = []  # type: List[int]
         j = 0
         while j < len(values):
@@ -156,15 +153,16 @@
             Invariant(Acc(list_pred(values), 1 / 2))
             Invariant(Acc(list_pred(out)))
             Invariant(0 <= j and j <= len(values))
-            Invariant(ToSeq(out) == ToSeq(values).take(j))
+            Invariant(mags == magnitude_read(ToSeq(values)))
+            Invariant(len(mags) == len(values))
+            Invariant(ToSeq(out) == mags.take(j))
             # invariants-end
-            out.append(values[j])
+            out.append(mags[j])
             j = j + 1
-        Assert(ToSeq(out) == ToSeq(values).take(len(values)))
-        Assert(ToSeq(values).take(len(values)) == ToSeq(values))
+        Assert(ToSeq(out) == mags.take(len(values)))
+        Assert(mags.take(len(values)) == mags)
         return out
     else:
-        # already numeric: passthrough
         passthrough = []  # type: List[int]
         m = 0
         while m < len(values):
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for pydata__xarray-6599.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A helper coerces the values held by one variable to floating-point numbers
  before a polynomial is evaluated over them. The coercion it performs is
  dispatched on the variable's value category ("kind"):

    * absolute-time values (a calendar timestamp, kind = TIME_POINT) are made
      numeric by measuring each timestamp as the elapsed amount since a chosen
      reference instant. This measurement is only meaningful for timestamps: it
      subtracts a reference *instant* from each value, an operation defined only
      when the values are themselves instants.

    * elapsed-duration values (a span of time, kind = TIME_SPAN) are made
      numeric by reading each duration directly as its magnitude in the base
      resolution; no reference instant is involved, because a duration is
      already a relative quantity. The resulting numbers equal the input
      magnitudes.

    * every other value category already carries numeric values and is returned
      unchanged.

The decisive property: a duration must be converted by reading its magnitude,
NOT by the instant-relative measurement reserved for timestamps -- applying the
instant-relative measurement to a duration is undefined (a span has no
reference instant to subtract). A correct helper therefore routes each kind to
the conversion defined for it.

Modelling: the underlying values are modelled as `List[int]` magnitudes in the
base resolution (the tested magnitudes are exact integers, so the
float-conversion is precision-independent; see refinement.md / mapping.md). The
value category is an `int` tag. The instant-relative measurement is the
UNCHANGED callee `elapsed_since` (axiomatized; defined only for TIME_POINT
inputs). The duration's direct magnitude read is the NEW branch, modelled
deeply as the identity on magnitudes.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *

# value-category tags
OTHER = 0       # already-numeric values: returned unchanged
TIME_POINT = 1  # absolute timestamps  (numpy datetime64; dtype.kind 'M')
TIME_SPAN = 2   # elapsed durations    (numpy timedelta64; dtype.kind 'm')


# axioms-start
@Pure
@ContractOnly
def elapsed_since(kind: int, values: PSeq[int], reference: int) -> PSeq[int]:
    """The instant-relative measurement (unchanged callee): measure each
    absolute timestamp as its elapsed magnitude since a chosen reference instant,
    i.e. the per-element subtraction of the reference. It is defined ONLY for
    timestamp inputs (kind == TIME_POINT); subtracting a reference instant from
    a value that is not itself an instant is undefined and rejected by the
    precondition. The per-element subtraction is the measurement's value only on
    well-defined magnitudes: a not-a-value sentinel magnitude (the int64 extremum
    -9223372036854775808, i.e. -2**63) is itself undefined, so the domain
    excludes it; likewise the magnitudes are within the exact-integer band of the
    base resolution (|magnitude| < 2**53) so the conversion is exact. Provenance +
    executable soundness check: mapping.md / axiom_check.py.
    """
    Requires(kind == TIME_POINT)
    # domain: well-defined, exact-integer magnitudes only -- exclude the
    # not-a-value sentinel (the int64 extremum -2**63), for which the
    # measurement is undefined (its value is not the per-element subtraction).
    Requires(well_defined_magnitudes(values))
    Ensures(len(Result()) == len(values))
    Ensures(Forall(int, lambda k:
        (Implies(0 <= k and k < len(values),
                 Result()[k] == values[k] - reference),
         [[Result()[k]]])))
# axioms-end


# pure-start
@Pure
def well_defined_magnitudes(values: PSeq[int]) -> bool:
    """Every element is a well-defined magnitude: none is the not-a-value
    sentinel (the int64 extremum -2**63). The instant-relative measurement's
    per-element subtraction is its value only on such magnitudes; a not-a-value
    element is itself undefined, so it lies outside the measurement's domain."""
    return Forall(int, lambda k:
        (Implies(0 <= k and k < len(values),
                 values[k] != -9223372036854775808),
         [[values[k]]]))


@Pure
def magnitude_read(values: PSeq[int]) -> PSeq[int]:
    """The duration's direct magnitude read (the NEW branch), modelled deeply:
    a span is already relative, so its float magnitude equals the input
    magnitude in the base resolution. The identity on magnitudes."""
    return values
# pure-end


def coerce_values_to_float(kind: int, values: List[int], reference: int) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(values), 1 / 2))
    # the input carries exactly one value category (its dtype kind)
    Requires(kind == OTHER or kind == TIME_POINT or kind == TIME_SPAN)
    # for a timestamp input the magnitudes are well-defined instants: no
    # not-a-value sentinel (the int64 extremum -2**63), the domain on which the
    # instant-relative measurement is defined (mapping.md / axiom_check.py)
    Requires(Implies(kind == TIME_POINT, well_defined_magnitudes(ToSeq(values))))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(values), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # timestamps: numeric via the instant-relative measurement -- the input
    # magnitudes are well-defined (no not-a-value sentinel), preserved into the
    # post-state since the input is read-only, so the measurement is applicable
    Ensures(Implies(kind == TIME_POINT, well_defined_magnitudes(ToSeq(values))))
    Ensures(Implies(kind == TIME_POINT,
                    ToSeq(Result()) == elapsed_since(kind, ToSeq(values), reference)))
    # durations: numeric via the direct magnitude read (NOT the instant-relative
    # measurement) -- the result equals the input magnitudes
    Ensures(Implies(kind == TIME_SPAN,
                    ToSeq(Result()) == magnitude_read(ToSeq(values))))
    Ensures(Implies(kind == TIME_SPAN, ToSeq(Result()) == ToSeq(values)))
    # already-numeric values: unchanged
    Ensures(Implies(kind == OTHER, ToSeq(Result()) == ToSeq(values)))
    # post-conditions-end
    # impl-start
    if kind == TIME_POINT:
        # numeric via the instant-relative measurement (the unchanged callee):
        # hold its result, the elapsed magnitudes since the reference instant
        measured = elapsed_since(kind, ToSeq(values), reference)
        result = []  # type: List[int]
        i = 0
        while i < len(values):
            # invariants-start
            Invariant(Acc(list_pred(values), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(values))
            Invariant(well_defined_magnitudes(ToSeq(values)))
            Invariant(measured == elapsed_since(kind, ToSeq(values), reference))
            Invariant(len(measured) == len(values))
            Invariant(ToSeq(result) == measured.take(i))
            # invariants-end
            result.append(measured[i])
            i = i + 1
        Assert(ToSeq(result) == measured.take(len(values)))
        Assert(measured.take(len(values)) == measured)
        return result
    elif kind == TIME_SPAN:
        # read each duration's magnitude directly (the new branch): the float
        # magnitude equals the input magnitude in the base resolution
        out = []  # type: List[int]
        j = 0
        while j < len(values):
            # invariants-start
            Invariant(Acc(list_pred(values), 1 / 2))
            Invariant(Acc(list_pred(out)))
            Invariant(0 <= j and j <= len(values))
            Invariant(ToSeq(out) == ToSeq(values).take(j))
            # invariants-end
            out.append(values[j])
            j = j + 1
        Assert(ToSeq(out) == ToSeq(values).take(len(values)))
        Assert(ToSeq(values).take(len(values)) == ToSeq(values))
        return out
    else:
        # already numeric: passthrough
        passthrough = []  # type: List[int]
        m = 0
        while m < len(values):
            # invariants-start
            Invariant(Acc(list_pred(values), 1 / 2))
            Invariant(Acc(list_pred(passthrough)))
            Invariant(0 <= m and m <= len(values))
            Invariant(ToSeq(passthrough) == ToSeq(values).take(m))
            # invariants-end
            passthrough.append(values[m])
            m = m + 1
        Assert(ToSeq(passthrough) == ToSeq(values).take(len(values)))
        Assert(ToSeq(values).take(len(values)) == ToSeq(values))
        return passthrough
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Protocol executed with the correct env from project root. All attacks are byte-identical in spec (axioms/@Pure/Requires/Ensures untouched); only the impl region edited. same-spec exit=0 for all 7 attacks + prepatch + positive_control.

SPEC PINS RESULT EXACTLY in all three branches: TIME_POINT -> ToSeq(Result)==elapsed_since(kind,ToSeq(values),reference) (per-element values[k]-reference, and elapsed_since carries Requires(kind==TIME_POINT) + Requires(well_defined_magnitudes)); TIME_SPAN -> ToSeq(Result)==magnitude_read(ToSeq(values)) AND ==ToSeq(values); OTHER -> ToSeq(Result)==ToSeq(values). So any verifying impl equals gold on every input in-domain.

atk_prepatch.py (PREPATCH BUG repro; TIME_POINT or TIME_SPAN routed through elapsed_since): exit=2 NOT-A-COUNTEREXAMPLE, does not verify -> prepatch reproduced (elapsed_since precondition kind==TIME_POINT violated for TIME_SPAN).
- atk1_span_through_measure.py (control-flow-effect: single guard routes TIME_SPAN through the timestamp measurement): exit=2 rejected (precondition fail).
- atk2_point_offbyone.py (partial-domain: TIME_POINT drops last element): exit=2 rejected (postcondition / Result length & value fail).
- atk3_span_plus1.py (wrong-value: TIME_SPAN returns values[j]+1): exit=2 rejected (ToSeq(Result)==ToSeq(values) fails).
- atk4_span_empty.py (partial-domain: TIME_SPAN returns []): exit=2 rejected.
- atk5_point_identity.py (ungrounded-oracle echo: TIME_POINT returns input identity ignoring measurement/reference): exit=2 rejected (Result != elapsed_since when reference!=0).
- atk6_other_double.py (control-flow-effect: OTHER branch doubles each value): exit=2 rejected.
- atk7_span_via_magread_correct.py (behaviourally-CORRECT alternate impl: TIME_SPAN materializes magnitude_read via loop; gold on all branches): exit=0 CANDIDATE (shares spec AND verifies).

CANDIDATE -> MATERIALIZE+RESOLVE (protocol step 2): atk7 is a faithful gold-equivalent echo. Its faithful refined patch is the gold to_floatable split (kind=='M' -> datetime_to_numeric copy; kind=='m' -> astype(float); else return x). Materialized at atk7_faithful_patch.diff and RUN through the official harness via run_resolve('pydata__xarray-6599', patch, timeout=1800): COMPLETED=True, RESOLVED=True, NOTE='resolved'. A resolving echo of the gold is NOT a weakness (per 2026-08-06 G-PANEL-1/echo policy: same-spec verifying attack fails the gate ONLY if its refined patch does NOT resolve). No verifying wrong impl exists.

POSITIVE CONTROL: positive_control.py (= bundle model.py) VERIFIED in 19.3s (adversary verify exit=0).

REFINEMENT.MD AUDIT (plan §4): every leg is R / A-consumed / A-reference / I, NO kind-3. A1 (dtype-kind code<->int tag) R; A2 (numpy array<->List[int] ns magnitudes) R; A3 (timestamp branch datetime_to_numeric modeled by elapsed_since) A-consumed+R -- load-bearing content is the precondition Requires(kind==TIME_POINT) + Requires(well_defined_magnitudes) NaT-free domain, and axiom_check.py checks (a) per-element subtraction (ref=0) on NaT-free domain, (b) precondition honesty (real callee RAISES on timedelta), (c) check_sentinel_excluded (callee returns nan at -2**63, exclusion necessary); A4 (duration astype(float) modeled DEEPLY by @Pure magnitude_read identity, validated == real op by axiom_check.py, NOT a consumed axiom) A-reference; A5 (else return x) I. The genuinely-changed op (duration astype(float)) is modeled deeply (A4), not behind a consumed axiom; the only consumed axiom (elapsed_since, A3) covers the UNCHANGED callee. Callee correspondence holds (mapping.md §1 bindings at base_commit 6bb2b855; duck_array_ops.datetime_to_numeric at computation.py:1938; astype(float) the new 'm' branch). No kind-3, correspondence intact.

CONCLUSION: 8 verifications executed (prepatch + 6 distinct wrong impls all rejected + 1 correct echo candidate), the sole candidate's materialized faithful patch RESOLVED under run_resolve, positive control verifies, refinement A-legs sound with no kind-3. verify=>correct holds; no verifying wrong impl found. VERDICT: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk1_span_through_measure.py`, `atk2_point_offbyone.py`, `atk3_span_plus1.py`, `atk4_span_empty.py`, `atk5_point_identity.py`, `atk6_other_double.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk7_span_via_magread_correct.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk1_span_through_measure.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk2_point_offbyone.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk3_span_plus1.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk4_span_empty.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk5_point_identity.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk6_other_double.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk7_span_via_magread_correct.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for pydata__xarray-6599.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A helper coerces the values held by one variable to floating-point numbers
  before a polynomial is evaluated over them. The coercion it performs is
  dispatched on the variable's value category ("kind"):

    * absolute-time values (a calendar timestamp, kind = TIME_POINT) are made
      numeric by measuring each timestamp as the elapsed amount since a chosen
      reference instant. This measurement is only meaningful for timestamps: it
      subtracts a reference *instant* from each value, an operation defined only
      when the values are themselves instants.

    * elapsed-duration values (a span of time, kind = TIME_SPAN) are made
      numeric by reading each duration directly as its magnitude in the base
      resolution; no reference instant is involved, because a duration is
      already a relative quantity. The resulting numbers equal the input
      magnitudes.

    * every other value category already carries numeric values and is returned
      unchanged.

The decisive property: a duration must be converted by reading its magnitude,
NOT by the instant-relative measurement reserved for timestamps -- applying the
instant-relative measurement to a duration is undefined (a span has no
reference instant to subtract). A correct helper therefore routes each kind to
the conversion defined for it.

Modelling: the underlying values are modelled as `List[int]` magnitudes in the
base resolution (the tested magnitudes are exact integers, so the
float-conversion is precision-independent; see refinement.md / mapping.md). The
value category is an `int` tag. The instant-relative measurement is the
UNCHANGED callee `elapsed_since` (axiomatized; defined only for TIME_POINT
inputs). The duration's direct magnitude read is the NEW branch, modelled
deeply as the identity on magnitudes.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *

# value-category tags
OTHER = 0       # already-numeric values: returned unchanged
TIME_POINT = 1  # absolute timestamps  (numpy datetime64; dtype.kind 'M')
TIME_SPAN = 2   # elapsed durations    (numpy timedelta64; dtype.kind 'm')


# axioms-start
@Pure
@ContractOnly
def elapsed_since(kind: int, values: PSeq[int], reference: int) -> PSeq[int]:
    """The instant-relative measurement (unchanged callee): measure each
    absolute timestamp as its elapsed magnitude since a chosen reference instant,
    i.e. the per-element subtraction of the reference. It is defined ONLY for
    timestamp inputs (kind == TIME_POINT); subtracting a reference instant from
    a value that is not itself an instant is undefined and rejected by the
    precondition. The per-element subtraction is the measurement's value only on
    well-defined magnitudes: a not-a-value sentinel magnitude (the int64 extremum
    -9223372036854775808, i.e. -2**63) is itself undefined, so the domain
    excludes it; likewise the magnitudes are within the exact-integer band of the
    base resolution (|magnitude| < 2**53) so the conversion is exact. Provenance +
    executable soundness check: mapping.md / axiom_check.py.
    """
    Requires(kind == TIME_POINT)
    # domain: well-defined, exact-integer magnitudes only -- exclude the
    # not-a-value sentinel (the int64 extremum -2**63), for which the
    # measurement is undefined (its value is not the per-element subtraction).
    Requires(well_defined_magnitudes(values))
    Ensures(len(Result()) == len(values))
    Ensures(Forall(int, lambda k:
        (Implies(0 <= k and k < len(values),
                 Result()[k] == values[k] - reference),
         [[Result()[k]]])))
# axioms-end


# pure-start
@Pure
def well_defined_magnitudes(values: PSeq[int]) -> bool:
    """Every element is a well-defined magnitude: none is the not-a-value
    sentinel (the int64 extremum -2**63). The instant-relative measurement's
    per-element subtraction is its value only on such magnitudes; a not-a-value
    element is itself undefined, so it lies outside the measurement's domain."""
    return Forall(int, lambda k:
        (Implies(0 <= k and k < len(values),
                 values[k] != -9223372036854775808),
         [[values[k]]]))


@Pure
def magnitude_read(values: PSeq[int]) -> PSeq[int]:
    """The duration's direct magnitude read (the NEW branch), modelled deeply:
    a span is already relative, so its float magnitude equals the input
    magnitude in the base resolution. The identity on magnitudes."""
    return values
# pure-end


def coerce_values_to_float(kind: int, values: List[int], reference: int) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(values), 1 / 2))
    # the input carries exactly one value category (its dtype kind)
    Requires(kind == OTHER or kind == TIME_POINT or kind == TIME_SPAN)
    # for a timestamp input the magnitudes are well-defined instants: no
    # not-a-value sentinel (the int64 extremum -2**63), the domain on which the
    # instant-relative measurement is defined (mapping.md / axiom_check.py)
    Requires(Implies(kind == TIME_POINT, well_defined_magnitudes(ToSeq(values))))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(values), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # timestamps: numeric via the instant-relative measurement -- the input
    # magnitudes are well-defined (no not-a-value sentinel), preserved into the
    # post-state since the input is read-only, so the measurement is applicable
    Ensures(Implies(kind == TIME_POINT, well_defined_magnitudes(ToSeq(values))))
    Ensures(Implies(kind == TIME_POINT,
                    ToSeq(Result()) == elapsed_since(kind, ToSeq(values), reference)))
    # durations: numeric via the direct magnitude read (NOT the instant-relative
    # measurement) -- the result equals the input magnitudes
    Ensures(Implies(kind == TIME_SPAN,
                    ToSeq(Result()) == magnitude_read(ToSeq(values))))
    Ensures(Implies(kind == TIME_SPAN, ToSeq(Result()) == ToSeq(values)))
    # already-numeric values: unchanged
    Ensures(Implies(kind == OTHER, ToSeq(Result()) == ToSeq(values)))
    # post-conditions-end
    # impl-start
    if kind == TIME_POINT:
        # numeric via the instant-relative measurement (the unchanged callee):
        # hold its result, the elapsed magnitudes since the reference instant
        measured = elapsed_since(kind, ToSeq(values), reference)
        result = []  # type: List[int]
        i = 0
        while i < len(values):
            # invariants-start
            Invariant(Acc(list_pred(values), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(values))
            Invariant(well_defined_magnitudes(ToSeq(values)))
            Invariant(measured == elapsed_since(kind, ToSeq(values), reference))
            Invariant(len(measured) == len(values))
            Invariant(ToSeq(result) == measured.take(i))
            # invariants-end
            result.append(measured[i])
            i = i + 1
        Assert(ToSeq(result) == measured.take(len(values)))
        Assert(measured.take(len(values)) == measured)
        return result
    elif kind == TIME_SPAN:
        # read each duration's magnitude directly (the new branch): the float
        # magnitude equals the input magnitude in the base resolution
        out = []  # type: List[int]
        j = 0
        while j < len(values):
            # invariants-start
            Invariant(Acc(list_pred(values), 1 / 2))
            Invariant(Acc(list_pred(out)))
            Invariant(0 <= j and j <= len(values))
            Invariant(ToSeq(out) == ToSeq(values).take(j))
            # invariants-end
            out.append(values[j])
            j = j + 1
        Assert(ToSeq(out) == ToSeq(values).take(len(values)))
        Assert(ToSeq(values).take(len(values)) == ToSeq(values))
        return out
    else:
        # already numeric: passthrough
        passthrough = []  # type: List[int]
        m = 0
        while m < len(values):
            # invariants-start
            Invariant(Acc(list_pred(values), 1 / 2))
            Invariant(Acc(list_pred(passthrough)))
            Invariant(0 <= m and m <= len(values))
            Invariant(ToSeq(passthrough) == ToSeq(values).take(m))
            # invariants-end
            passthrough.append(values[m])
            m = m + 1
        Assert(ToSeq(passthrough) == ToSeq(values).take(len(values)))
        Assert(ToSeq(values).take(len(values)) == ToSeq(values))
        return passthrough
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Protocol executed with the correct env from project root. All attacks are byte-identical in spec (axioms/@Pure/Requires/Ensures untouched); only the impl region edited. same-spec exit=0 for all 7 attacks + prepatch + positive_control.

SPEC PINS RESULT EXACTLY in all three branches: TIME_POINT -> ToSeq(Result)==elapsed_since(kind,ToSeq(values),reference) (per-element values[k]-reference, and elapsed_since carries Requires(kind==TIME_POINT) + Requires(well_defined_magnitudes)); TIME_SPAN -> ToSeq(Result)==magnitude_read(ToSeq(values)) AND ==ToSeq(values); OTHER -> ToSeq(Result)==ToSeq(values). So any verifying impl equals gold on every input in-domain.

atk_prepatch.py (PREPATCH BUG repro; TIME_POINT or TIME_SPAN routed through elapsed_since): exit=2 NOT-A-COUNTEREXAMPLE, does not verify -> prepatch reproduced (elapsed_since precondition kind==TIME_POINT violated for TIME_SPAN).
- atk1_span_through_measure.py (control-flow-effect: single guard routes TIME_SPAN through the timestamp measurement): exit=2 rejected (precondition fail).
- atk2_point_offbyone.py (partial-domain: TIME_POINT drops last element): exit=2 rejected (postcondition / Result length & value fail).
- atk3_span_plus1.py (wrong-value: TIME_SPAN returns values[j]+1): exit=2 rejected (ToSeq(Result)==ToSeq(values) fails).
- atk4_span_empty.py (partial-domain: TIME_SPAN returns []): exit=2 rejected.
- atk5_point_identity.py (ungrounded-oracle echo: TIME_POINT returns input identity ignoring measurement/reference): exit=2 rejected (Result != elapsed_since when reference!=0).
- atk6_other_double.py (control-flow-effect: OTHER branch doubles each value): exit=2 rejected.
- atk7_span_via_magread_correct.py (behaviourally-CORRECT alternate impl: TIME_SPAN materializes magnitude_read via loop; gold on all branches): exit=0 CANDIDATE (shares spec AND verifies).

CANDIDATE -> MATERIALIZE+RESOLVE (protocol step 2): atk7 is a faithful gold-equivalent echo. Its faithful refined patch is the gold to_floatable split (kind=='M' -> datetime_to_numeric copy; kind=='m' -> astype(float); else return x). Materialized at atk7_faithful_patch.diff and RUN through the official harness via run_resolve('pydata__xarray-6599', patch, timeout=1800): COMPLETED=True, RESOLVED=True, NOTE='resolved'. A resolving echo of the gold is NOT a weakness (per 2026-08-06 G-PANEL-1/echo policy: same-spec verifying attack fails the gate ONLY if its refined patch does NOT resolve). No verifying wrong impl exists.

POSITIVE CONTROL: positive_control.py (= bundle model.py) VERIFIED in 19.3s (adversary verify exit=0).

REFINEMENT.MD AUDIT (plan §4): every leg is R / A-consumed / A-reference / I, NO kind-3. A1 (dtype-kind code<->int tag) R; A2 (numpy array<->List[int] ns magnitudes) R; A3 (timestamp branch datetime_to_numeric modeled by elapsed_since) A-consumed+R -- load-bearing content is the precondition Requires(kind==TIME_POINT) + Requires(well_defined_magnitudes) NaT-free domain, and axiom_check.py checks (a) per-element subtraction (ref=0) on NaT-free domain, (b) precondition honesty (real callee RAISES on timedelta), (c) check_sentinel_excluded (callee returns nan at -2**63, exclusion necessary); A4 (duration astype(float) modeled DEEPLY by @Pure magnitude_read identity, validated == real op by axiom_check.py, NOT a consumed axiom) A-reference; A5 (else return x) I. The genuinely-changed op (duration astype(float)) is modeled deeply (A4), not behind a consumed axiom; the only consumed axiom (elapsed_since, A3) covers the UNCHANGED callee. Callee correspondence holds (mapping.md §1 bindings at base_commit 6bb2b855; duck_array_ops.datetime_to_numeric at computation.py:1938; astype(float) the new 'm' branch). No kind-3, correspondence intact.

CONCLUSION: 8 verifications executed (prepatch + 6 distinct wrong impls all rejected + 1 correct echo candidate), the sole candidate's materialized faithful patch RESOLVED under run_resolve, positive control verifies, refinement A-legs sound with no kind-3. verify=>correct holds; no verifying wrong impl found. VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Real base_commit 6bb2b855 verified in worktree to_floatable dispatch checked branch-by-branch: TIME_POINT models datetime_to_numeric(offset=1970-01-01,unit=ns) with reference==0 => result==values on the well_defined_magnitudes domain; -2**63 NaT sentinel correctly excluded (real callee returns nan there); precondition kind==TIME_POINT honest (real callee raises UFuncTypeError on timedelta). G-AX/axiom_check.py executes the real callee and confirms including check_sentinel_excluded (exclusion NECESSARY). (2) TIME_SPAN models x.astype(float) as ns-magnitude identity — faithful for exact-integer magnitudes. (3) OTHER passthrough == real `return x`. On every test-reachable input the model is byte-for-behavior faithful. Spec region confirmed byte-identical (same-spec exit 0). The only modeled/real disagreement is the |mag|>=2**53 precision band, which is disclosed, bounded, and out of test domain — a sanctioned refinement, not spec drift. Verdict FAITHFUL. (Separately: the recorded G-EQ fail on this cell is a verify-not-resolve equivalence break, a distinct gate, not a faithfulness/spec-too-strong issue.)

Counterexample / evidence:

```
None that constitutes a genuine faithfulness defect. The single divergence above is a disclosed, bounded, non-test-reachable float-as-int precision abstraction (refinement.md §D 'MINOR 1'; mapping.md §2), explicitly permitted by SPEC_GUIDE §2 because precision-independence holds on the tested domain (F2P magnitudes 1000/2000/3000 ns and P2P magnitudes 0/1e9/2e9 ns are all < 2**53, exact). The resolution guarantee verify(model)=>resolves is unaffected.
```

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `axiom_check.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Reconstructed the consumer spec view via swebench_unified.markers.spec_view(model.py, nagini backend); its sha256 (1b52acada66221c40f7691118221232d651137e7cec96d80be929bb4f0a72011) matches meta.region_hashes.spec_view exactly, so this is the genuine view and the impl region is elided ('... implementation elided — supplied by the consumer'). Compared against the public problem_statement ONLY (hints_text excluded).

(1) Lexical scan: NONE of the gold-patch-specific tokens appear in the spec view — no 'mM', no '== "M"'/'== "m"' guard, no 'elif', no datetime_to_numeric, no astype, no x.copy, no '1970-01-01', no to_floatable/duck_array_ops/computation.py references, no UFuncTypeError, no polyval. The view is a fully abstracted MODEL (int kind-tags OTHER/TIME_POINT/TIME_SPAN, PSeq[int] magnitudes, an axiomatized callee elapsed_since + a deep model magnitude_read), not repo code and not the diff. No copy-pasteable fix.

(2) The only repo-adjacent tokens are the numpy dtype.kind codes 'M'/'m' in the two tag comments (TIME_POINT: datetime64 dtype.kind 'M'; TIME_SPAN: timedelta64 dtype.kind 'm'). These are standard numpy category codes for datetime64/timedelta64, both of which are named verbatim in the public problem_statement — a type-mapping annotation, NOT disclosure of the 'in "mM"' -> '== "M"' / 'elif == "m": x.astype(float)' split. They do not reveal the edit structure.

(3) The specified behavior (timedelta -> read numeric ns magnitude; datetime -> elapsed-since-reference measurement; other -> unchanged) is directly derivable from the public issue, which publishes the correct stable output (~4.4e6) vs the broken output (~1.6e30) for a timedelta64 coordinate and asserts both should match. Specifying correct behavior is required for verify=>resolve and is not leakage.

(4) The mechanistic rationale ('an instant-relative subtraction is undefined for a duration') overlaps with hints_text, but hints are excluded from the baseline and a spec is entitled to its own correctness rationale; the view reproduces no gold guard or diff hunk.

Conclusion: the spec view does not leak the gold edit beyond the public problem_statement. Concurs with recorded G-PANEL-3 (pass).

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, which ships in this bundle, so a reader can start there.
