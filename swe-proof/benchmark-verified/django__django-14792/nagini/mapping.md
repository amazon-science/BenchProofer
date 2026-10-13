# mapping.md — django__django-14792

Binds every `model.py` symbol to its repository counterpart at
`base_commit = d89f976bddb49fb168334960acc8979c3de991fa`, states the type
abstraction, and gives the provenance of the two unchanged object queries the
deep selection model is validated against by G-AX.

Repo file under change: `django/utils/timezone.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `resolve_timezone_name(tz)` | `_get_timezone_name(timezone)` — `django/utils/timezone.py:74-76` | the modeled changed function (resolves a single canonical name for a tzinfo object) |
| `TimeZone` (the `tz` argument) | the `timezone` argument — a `datetime.tzinfo` instance (`datetime.timezone`, `pytz` zone, or `zoneinfo.ZoneInfo`) | the time-zone object the helper inspects |
| `tz.short_label` *(field — A-reference)* | `timezone.tzname(None)` — `datetime.tzinfo.tzname(dt)` (CPython stdlib `Lib/datetime.py`; also `pytz`/`zoneinfo` overrides) | unchanged object query: the short per-instant abbreviation/offset label, `Optional[str]` (may be `None`) |
| `tz.full_name` *(field — A-reference)* | `str(timezone)` — `tzinfo.__str__` / `__repr__` (the full textual rendering) | unchanged object query: the full textual rendering, always a `str` |
| `present_and_nonempty(label)` | the Python truthiness of `timezone.tzname(None)` in the `or` expression | pure spec: a label is usable iff present and non-empty |
| `Result()` (the `PSeq[int]` returned) | the value of `timezone.tzname(None) or str(timezone)` (`timezone.py:76` post-patch) | the resolved canonical name |

The gold patch (the one change, `timezone.py:75-76`) replaces the body
`return str(timezone)` with `return timezone.tzname(None) or str(timezone)`:
prefer the short label when present and non-empty, else the full rendering.
Pre-patch, only `str(timezone)` (the full rendering) was returned.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `str` (the helper's return; `str(timezone)`) | `PSeq[int]` of Unicode code points | `s[k]` ↔ `Result()[k] == ord(s[k])`; `len(s)` ↔ `len(Result())`; the empty `str` `''` ↔ the empty `PSeq` |
| `Optional[str]` (`timezone.tzname(None)`) | `Optional[PSeq[int]]` (`tz.short_label`) | `None` ↔ `None` (no label); a `str` ↔ its code-point sequence; the empty `str` `''` ↔ the empty `PSeq` |
| truthiness of `timezone.tzname(None)` (an `Optional[str]`) | `present_and_nonempty(label)` = `label is not None and len(label) > 0` | Python `bool(s)` for an `Optional[str]` is `False` iff `s is None or s == ''`; the predicate is the exact negation of that — `True` iff present and non-empty |
| the `tzinfo` object | `TimeZone(short_label, full_name)` | a minimal class carrying only the two observations the helper reads; the object is never mutated (read-only) |

`str` indexing/iteration is banned in Nagini, so the carriers are
`PSeq[int]`/`Optional[PSeq[int]]`. The object is read-only, so both fields are
held at half permission (`Acc(..., 1/2)`), Required AND Ensured (directive 5).

## 3. Callee / observation provenance (A-reference — checked by G-AX / axiom_check.py)

The change introduces a *selection* between two unchanged textual observations
of the tzinfo object. There is **no consumed `@ContractOnly` axiom**: the two
observations carry opaque content, so they are modelled directly as the object's
two fields (the model's inputs) and the resolved name is pinned structurally to
be exactly one of them. The selection logic itself — the operation the patch
introduces — is modelled **deeply** (`resolve_timezone_name` +
`present_and_nonempty`). The fields' correspondence to the real queries is the
**A-reference** that G-AX validates; nothing is consumed as an axiom.

### 3.1 `tz.short_label` ↔ `timezone.tzname(None)` (A-reference)
**Query:** `datetime.tzinfo.tzname(dt)` invoked as `timezone.tzname(None)`.
Returns the time-zone's short name/offset label for the given instant, an
`Optional[str]`:
- `datetime.timezone(offset)` → `"UTC±HH:MM"` (and the constructor-supplied
  `name=` if given, e.g. `"Etc/GMT-10"`);
- `pytz` named zones → the IANA name (`"Europe/Madrid"`); `pytz` `Etc/GMT±N`
  fixed-offset zones → the offset label (`"+10"` for `Etc/GMT-10`);
- `zoneinfo` named zones with no fixed abbreviation → **`None`**;
  `zoneinfo` `Etc/GMT±N` → the offset label (`"+10"`).

The `None`/empty cases are exactly why the helper needs the `or` fallback. Docs:
https://docs.python.org/3/library/datetime.html#datetime.tzinfo.tzname.

### 3.2 `tz.full_name` ↔ `str(timezone)` (A-reference)
**Query:** `str(timezone)` (the tzinfo object's `__str__`). Always a non-empty
`str`: the IANA name for named `pytz`/`zoneinfo` zones (`"Europe/Madrid"`,
`"Etc/GMT-10"`), or `"UTC±HH:MM"` / the constructor `name` for
`datetime.timezone`. This is the pre-patch helper's entire behaviour and the
post-patch fallback.

**Soundness check (G-AX):** `axiom_check.py` builds real tzinfo objects from
every family the F2P test uses — `datetime.timezone` fixed offsets across the
dial (named and unnamed), `pytz` named zones and `Etc/GMT±N` fixed offsets, and
`zoneinfo` named zones and `Etc/GMT±N` — extracts the two real observations,
runs the model's deep selection over them, and asserts it equals the real gold
expression `timezone.tzname(None) or str(timezone)`. It additionally re-confirms
the exact F2P expectations (pytz/zoneinfo `Etc/GMT-10` → `"+10"`,
`datetime.timezone(+10h)` → `"UTC+10:00"`, `datetime.timezone(+10h,
name="Etc/GMT-10")` → `"Etc/GMT-10"`, named zones → their full name), then fuzzes
5000 randomized fixed-offset zones. It imports only stdlib + `pytz`/`zoneinfo`
(the very modules the helper and its test use); nothing repo-private. Exit 0 iff
sound.

The selection is **flag-independent**: `tzname(None) or str(timezone)` is the
same expression on every backend; G-AX exercises all three tzinfo families.
