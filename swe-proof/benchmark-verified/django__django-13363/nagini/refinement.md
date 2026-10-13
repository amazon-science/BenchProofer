# refinement.md — django__django-13363

The operation-by-operation correspondence between `model.py`'s implementation
(the `date_cast_tzname` / `time_cast_tzname` impl regions and the deep
`selected_tzname` model) and `patch.diff` (the gold patch). Each step is tagged
**R** (type refinement), **A-consumed** (the proof uses an axiom's `Ensures`),
**A-reference** (a deep model validated == a real callee by axiom_check.py /
G-AX), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE). There are **no consumed axioms** (the
`axioms` region is empty); the selection logic is modelled deeply.

## A. The date-cast site — `TruncDate.as_sql` (`django/db/models/functions/datetime.py:292`)

Gold hunk:
```
-        tzname = timezone.get_current_timezone_name() if settings.USE_TZ else None
+        tzname = self.get_tzname()
```

| # | model.py impl op (`date_cast_tzname`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | params `use_tz: bool`, `tzinfo: Optional[List[int]]`, `current_name: List[int]` | `settings.USE_TZ`, `self.tzinfo`, `timezone.get_current_timezone_name()` | R | bool ↔ bool; a `tzinfo` object ↔ its name (`Optional[List[int]]`); the ambient name `str` ↔ `List[int]` (mapping.md §2). |
| A2 | `tzname = selected_tzname(use_tz, tzinfo, current_name)` computed inline as `None`/`current_name`/`tzinfo` by the nested `if` | `tzname = self.get_tzname()` | R + A-reference | `self.get_tzname()` (`TimezoneMixin.get_tzname`, `datetime.py:17-28`) is the unchanged method the fix delegates to; it is modeled **deeply** by `selected_tzname` (spelled-out in the `pure` region) and re-derived in the impl as the same nested `if`. No `@ContractOnly` is consumed; the deep model is validated **== the real `get_tzname` selection** by G-AX (axiom_check.py). The name-of-a-time-zone lookup `_get_timezone_name(self.tzinfo)` is the identity under the name abstraction (R, mapping.md §2/§3.1). |
| A3 | `return tzname` (an `Optional[List[int]]`) | `tzname` passed to `connection.ops.datetime_cast_date_sql(lhs, tzname)`; `sql, lhs_params` returned | R + I | the model returns the selected name; the real code feeds it to the UNCHANGED, deterministic cast-SQL builder (mapping.md §3.2). `lhs` (from `compiler.compile(self.lhs)`) is identical pre/post, so the emitted SQL differs iff `tzname` differs. Pinning `tzname` pins the only observable change. |

## B. The time-cast site — `TruncTime.as_sql` (`django/db/models/functions/datetime.py:305`)

Gold hunk (identical shape):
```
-        tzname = timezone.get_current_timezone_name() if settings.USE_TZ else None
+        tzname = self.get_tzname()
```

| # | model.py impl op (`time_cast_tzname`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | params (same three) | `settings.USE_TZ`, `self.tzinfo`, `timezone.get_current_timezone_name()` | R | as A1. |
| B2 | `tzname = selected_tzname(...)` inline | `tzname = self.get_tzname()` | R + A-reference | as A2 — same `get_tzname` delegation, same deep model. |
| B3 | `return tzname` | `tzname` passed to `connection.ops.datetime_cast_time_sql(lhs, tzname)`; returned | R + I | as A3, but the unchanged downstream consumer is `datetime_cast_time_sql` (mapping.md §3.2). |

## C. The discriminating behaviour and the two prepatch witnesses

The change makes both sites honour `self.tzinfo`. The discriminating clause
fires exactly when **time-zone support is on AND a time zone is supplied AND it
differs from the ambient one**: post-patch the selected name is the supplied
tz's name; pre-patch it is the ambient name (the supplied tz is discarded).
This is precisely the F2P assertion: `model.melb_date == melb_start_datetime.date()`
and `model.pacific_date == pacific_start_datetime.date()` (and the `_time`
analogues), where `melb`/`pacific` differ from the ambient zone.

`model_prepatch.py` reverts the **date** site to
`tzname = current_name if use_tz else None` (ignoring `tzinfo`) and **fails**
the postcondition `Result() is selected_tzname(use_tz, tzinfo, current_name)` of
`date_cast_tzname` (G-DIFF). `model_prepatch_2.py` reverts the **time** site and
fails the same postcondition of `time_cast_tzname`. The two sites are fixed by
two independent hunks and observed by two independent F2P assertion families, so
each gets its own failing witness.

## D. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The operation that genuinely *changed*
— the `tzname` selection — is modeled **deeply** (`selected_tzname` + the inline
`if`), not hidden behind an axiom about the function under change. There is no
consumed `@ContractOnly` axiom: the empty `axioms` region is honest. The
unchanged callee `get_tzname`'s selection is the **A-reference** that G-AX
validates the deep model against; the unchanged backend SQL builders are
downstream deterministic consumers of the modeled value (I/R, §3.2), not
referenced by the spec.

## E. verify(model) ⇒ resolved

`date_cast_tzname` / `time_cast_tzname` verify only if their result equals the
exact selection `selected_tzname` — i.e. the supplied time zone's name when one
is supplied (A2/B2). By R (bool/str↔List[int], the `_get_timezone_name` name
identity) the verified selection equals `self.get_tzname()` on the tested
inputs; by G-AX (axiom_check.py) the deep model equals the real `get_tzname`
selection (A-reference). The unchanged cast-SQL builders consume that name
deterministically with identical `lhs`, so equal `tzname` ⇒ equal SQL ⇒ the same
DB result the F2P tests observe. Therefore a model satisfying this spec, refined
by the map above, is the gold patch up to type refinement — and the gold patch
resolves (G-RESOLVE). The single trust point is refinement fidelity (this
document, G-EQ) plus the G-AX reference check; there is no consumed-axiom trust
point.
