# mapping.md — django__django-13363

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 76e0151ea0e0f56dca66cee846a78b89346d2c4c`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and gives
the provenance of the deep-model reference.

Repo file under change: `django/db/models/functions/datetime.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `dateCastZoneName (tzAware) (explicitZone) (currentZone)` | `TruncDate.as_sql` — `django/db/models/functions/datetime.py:292` (changed line 295) | modeled changed function: the timezone-name selection a date cast uses |
| `timeCastZoneName (tzAware) (explicitZone) (currentZone)` | `TruncTime.as_sql` — `django/db/models/functions/datetime.py:305` (changed line 308) | modeled changed function: the timezone-name selection a time cast uses |
| `resolveZoneName` *(deep model — A-reference)* | `TimezoneMixin.get_tzname` — `django/db/models/functions/datetime.py:17` | pure spec: the zone-name resolution the fix delegates to; deep model of the **unchanged** callee `get_tzname`, validated `resolveZoneName == get_tzname` by axiom_check.py (G-AX), NOT consumed as an axiom |

The pre-patch repo code the change removes (refinement audit only, not in the
consumer spec view): the inline expression
`timezone.get_current_timezone_name() if settings.USE_TZ else None`
(`datetime.py:295` and `:308`), which ignores `self.tzinfo`.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types. A wrong entry surfaces as spurious
G-CONF disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `settings.USE_TZ` (the zone-awareness flag `get_tzname` reads) | `Bool` `tzAware` | `True ↔ true`, `False ↔ false` |
| a rendered timezone **name** (`str`, e.g. `'UTC'`, `'America/New_York'`) | `String` | Python `str` ↔ Lean `String`, identity on character content |
| a caller-supplied target zone, possibly absent (`self.tzinfo`: a `tzinfo` object or `None`) | `Option String` `explicitZone` | the zone's rendered name `_get_timezone_name(tzinfo)` when a zone was supplied ↔ `some name`; `tzinfo is None` ↔ `none` |
| the ambient/active zone, always present | `String` `currentZone` | `get_current_timezone_name()` (the active zone's rendered name) ↔ the `currentZone` string |
| the selected `tzname` result (`str | None` threaded into the cast callee) | `Option String` `out` | `None ↔ none`; a name `str` ↔ `some name` |

`get_tzname` consumes its two zone objects ONLY through the name renderers
`timezone.get_current_timezone_name()` and `timezone._get_timezone_name(·)`
(both `→ str`); the downstream cast callee uses only the resulting `tzname`
string (or `None`). So the relevant observable carrier of every zone is its
rendered **name** — modeled as `String` — and the bijection above is exact on
that carrier. Modeling the explicit zone as `Option String` (rather than
`Option (opaque tzinfo)`) is faithful because nothing downstream inspects the
zone beyond its rendered name.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `resolveZoneName` deep model ↔ `TimezoneMixin.get_tzname` (A-reference)
**Callee:** `django.db.models.functions.datetime.TimezoneMixin.get_tzname`
(`datetime.py:17`), an **unchanged** method (it already existed pre-patch; the
bug was that `TruncDate.as_sql`/`TruncTime.as_sql` did not call it). Source at
base_commit:

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

This is exactly the deep model `resolveZoneName(tzAware, explicitZone,
currentZone)`:
* `not tzAware` ⇒ `none`            (the `if settings.USE_TZ` guard fails)
* `tzAware`, `explicitZone = none`  ⇒ `some currentZone`   (`self.tzinfo is None` leg)
* `tzAware`, `explicitZone = some z` ⇒ `some z`             (the `else` leg — the fix)

with `currentZone = get_current_timezone_name()` and
`explicitZone = _get_timezone_name(self.tzinfo)` (or `none`). The deep model
spells out the **control flow** (the USE_TZ gate and the explicit-vs-ambient
selection); the two zone-name renderers are opaque sub-callees whose `str`
outputs are the model's `currentZone` / `explicitZone` inputs. There is **no
consumed axiom** — the proof needs none; the changed selection is modeled
concretely and the equality to the real `get_tzname` is the A-reference G-AX
validates.

**Soundness check (G-AX):** `axiom_check.py` runs the real
`TimezoneMixin.get_tzname` over `{USE_TZ on/off}` × `{explicit zone present/
absent}` × many ambient/explicit zone pairs (boundary: every pair from a 10-zone
set; plus 20 000 randomized fuzz), asserting `resolveZoneName == get_tzname` on
every observation. Imports only `django.*` (in-container) + `pytz`. Exit 0 iff
sound.

### 3.2 Downstream cast callees (UNCHANGED, not modeled)
`connection.ops.datetime_cast_date_sql(lhs, tzname)` /
`datetime_cast_time_sql(lhs, tzname)` and `compiler.compile(self.lhs)` are
UNCHANGED by the patch and deterministic in `tzname`. They carry no modeled
content; the gold change touches only the `tzname` value handed to them. G-CONF
captures exactly that `tzname` argument (intercepting the cast callee), so the
unchanged continuation needs no axiom.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` and `axiom_check.py` seed their `random.Random` with
**`13363`** so the consumer-side verdict (§11.3) is reproducible. The R/I shadow
transliterates `resolveZoneName` (R/I-tagged control flow) to Python and renders
the two opaque zone-name sub-callees with the real `get_current_timezone_name` /
`_get_timezone_name` (R-mapped values), then compares against the `tzname` the
real patched `as_sql` threads into the cast callee.
