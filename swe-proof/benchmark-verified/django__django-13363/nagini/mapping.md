# mapping.md — django__django-13363

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 76e0151ea0e0f56dca66cee846a78b89346d2c4c`, states the type
abstraction, and records callee provenance.

Repo file under change: `django/db/models/functions/datetime.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `date_cast_tzname(use_tz, tzinfo, current_name)` | `TruncDate.as_sql` — `django/db/models/functions/datetime.py:292` (body line 295) | first modeled changed function: the time-zone-name selection performed by the date-cast SQL builder |
| `time_cast_tzname(use_tz, tzinfo, current_name)` | `TruncTime.as_sql` — `django/db/models/functions/datetime.py:305` (body line 308) | second modeled changed function: the same selection performed by the time-cast SQL builder |
| `selected_tzname(use_tz, tzinfo, current_name)` | `TimezoneMixin.get_tzname` — `django/db/models/functions/datetime.py:17-28` | pure spec for the (unchanged) mixin method the fix delegates to; under spec, NOT axiomatized (the changed functions now CALL it) |

The pre-patch repo expression the change removes (for the refinement audit, not
referenced from the consumer spec view): the inlined
`timezone.get_current_timezone_name() if settings.USE_TZ else None`
(`datetime.py:295` and `:308`), which ignores `self.tzinfo`.

### 1.1 Why two modeled functions, and what `selected_tzname` models

`TruncDate.as_sql` and `TruncTime.as_sql` are two separately-edited hunks (gold
patch has two hunks). Both compute a local `tzname` then pass it to a distinct,
unchanged backend routine (`connection.ops.datetime_cast_date_sql` /
`datetime_cast_time_sql`). The bug, and the fix, are entirely in how `tzname` is
selected — identical logic in both sites. The fix replaces the inline
expression with a call to `self.get_tzname()` (`TimezoneMixin.get_tzname`,
`datetime.py:17-28`), which is:

```python
def get_tzname(self):
    tzname = None
    if settings.USE_TZ:
        if self.tzinfo is None:
            tzname = timezone.get_current_timezone_name()
        else:
            tzname = timezone._get_timezone_name(self.tzinfo)
    return tzname
```

`selected_tzname` is the pure spec of exactly this method. The two modeled
functions return the selected `tzname` value (the only thing that differs
between pre- and post-patch); the downstream backend SQL builder is a
deterministic, unchanged consumer of that value (see refinement.md §C).

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `settings.USE_TZ` (bool flag) | `use_tz: bool` | identity |
| `self.tzinfo` (a `tzinfo` object, or `None`) | `tzinfo: Optional[List[int]]` | a supplied time zone is abstracted by its NAME string (`List[int]` of code points), since the value that flows into the SQL builder is the name `timezone._get_timezone_name(self.tzinfo) == self.tzinfo.tzname(None)`; `None` ↔ no time zone supplied |
| `timezone.get_current_timezone_name()` (a `str`) | `current_name: List[int]` of code points | the ambient/active time zone's name; the function is a deterministic 0-ary read of process state, abstracted as an input value |
| `timezone._get_timezone_name(self.tzinfo)` (a `str`) | the `tzinfo` carrier itself | identity under the name abstraction: `_get_timezone_name(tz) == tz.tzname(None)` IS the name; the model carries the name directly, so this lookup is the identity (refinement.md R-step) |
| the returned `tzname` (a `str` or `None`) | `Optional[List[int]]` | `str` ↔ `List[int]` code points; `None` ↔ `None` |

`str` indexing/iteration is banned in Nagini, so time-zone names are carried as
`List[int]`. The selection never indexes a name — it only chooses WHICH name (or
`None`) to return — so the name content is opaque and the choice is by object
identity (`Result() is selected_tzname(...)`), the tightest possible spec.

## 3. Callee provenance

No `@ContractOnly` axiom is used (the `axioms` region is empty). The two callee
families touched are handled as follows, and are checked by `axiom_check.py`
(G-AX) as reference behaviour, not consumed as axioms:

### 3.1 `timezone.get_tzname` / `_get_timezone_name` / `get_current_timezone_name`
**Callee:** `django.utils.timezone` (`django/utils/timezone.py:64-71`):
```python
def get_current_timezone_name():
    return _get_timezone_name(get_current_timezone())
def _get_timezone_name(timezone):
    return timezone.tzname(None)
```
`TimezoneMixin.get_tzname` (`datetime.py:17-28`) is modeled deeply by
`selected_tzname` (it is unchanged code the fix now delegates to; it is fully
expressible, so it is modeled under spec rather than axiomatized).
`_get_timezone_name(tz)` is the name-of-a-time-zone identity under the name
abstraction (§2). `axiom_check.py` validates that the real `get_tzname` logic
returns: `None` when `USE_TZ` is off; the supplied tz's name when supplied; the
ambient name otherwise — i.e. that `selected_tzname` == the real selection.

### 3.2 `connection.ops.datetime_cast_date_sql` / `datetime_cast_time_sql`
**Callee:** the database backend operations, e.g. SQLite
`django/db/backends/sqlite3/operations.py` `datetime_cast_date_sql(self, sql,
tzname)` / `datetime_cast_time_sql(self, sql, tzname)`. These are UNCHANGED by
the patch and are deterministic functions of `(sql, tzname)`. The pre- and
post-patch code differ ONLY in the `tzname` argument; `sql` (from
`compiler.compile(self.lhs)`) is identical. So the emitted SQL differs iff the
selected `tzname` differs. The model returns `tzname` directly; this downstream
consumer is therefore not referenced in the spec and needs no axiom
(refinement.md §C). `axiom_check.py` documents this determinism dependency.
