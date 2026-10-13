# mapping.md — symbol binding & type bijection (django__django-13363)

## Modeled functions
Two changed functions, identical edit, same `Solution.lean`:

- **Lean** `implementation_truncDateCast : String → Bool → Option String → String → String`
  **Python** `TruncDate.as_sql(self, compiler, connection)` —
  `django/db/models/functions/datetime.py:292-297 @ base_commit`.
- **Lean** `implementation_truncTimeCast : String → Bool → Option String → String → String`
  **Python** `TruncTime.as_sql(self, compiler, connection)` —
  `django/db/models/functions/datetime.py:305-310 @ base_commit`.

Both methods compile the inner expression to a SQL fragment, then return the SQL
produced by a per-flavour database cast applied to that fragment together with a
*conversion zone name*. The conversion zone name is the only thing the fix
changes; the cast and the inner-fragment compilation are unchanged.

### The changed op (the conversion-zone selection)
Pre-patch both methods compute the zone name as:

```python
tzname = timezone.get_current_timezone_name() if settings.USE_TZ else None
```

i.e. when timezone support is on, the *ambient* zone name is used
unconditionally and any caller-supplied zone is discarded. Post-patch both
methods compute it via the shared mixin helper
(`TimezoneMixin.get_tzname`, `datetime.py:17-28`, UNCHANGED):

```python
tzname = None
if settings.USE_TZ:
    if self.tzinfo is None:
        tzname = timezone.get_current_timezone_name()
    else:
        tzname = timezone._get_timezone_name(self.tzinfo)
return tzname
```

so a caller-supplied zone (`self.tzinfo`) takes precedence over the ambient one.
This is the F2P discriminator: with `USE_TZ` on and a non-ambient `tzinfo`, the
pre-patch result uses the wrong zone.

## Type bijection (used by G-CONF + G-AX)
| Python | Lean | notes |
|---|---|---|
| compiled inner SQL fragment (`lhs`, output of `compiler.compile(self.lhs)`) | `lhs : String` | unchanged passthrough; pinned in spec (frame) |
| `settings.USE_TZ` | `useTz : Bool` | timezone-support flag |
| `self.tzinfo` (a tzinfo object, or `None`) | `requestedZone : Option String` | the tzinfo modeled BY the zone name `timezone._get_timezone_name` extracts from it; `none` ⟺ no tzinfo supplied (A-reference bijection below) |
| `timezone.get_current_timezone_name()` | `currentZone : String` | the ambient zone name; UNCHANGED nullary callee, modeled as a universally-quantified input (so the contract holds for every ambient zone) |
| `timezone._get_timezone_name(self.tzinfo)` | `requestedZone.get` (the carried name) | A-reference: the extraction is the identity on the carried zone name (G-AX) |
| `connection.ops.datetime_cast_date_sql(lhs, tzname)` | `castDate lhs zone` | UNCHANGED cast callee; `opaque` signature, applied identically on both sides (I) |
| `connection.ops.datetime_cast_time_sql(lhs, tzname)` | `castTime lhs zone` | UNCHANGED cast callee; `opaque` signature, applied identically on both sides (I) |
| returned `sql` string | `String` | the modeled observable |
| returned `lhs_params` list | — | unaffected by the fix; out of model scope (cf. django-10880 params) |

The conversion-zone selection is modeled deeply as the pure helper
`conversionZoneName useTz requestedZone currentZone`
(`= if useTz then some (requestedZone.getD currentZone) else none`), which is the
closed form of the `get_tzname` control flow.

## Callee provenance & flag deps
- `connection.ops.datetime_cast_date_sql` / `datetime_cast_time_sql`
  (`django/db/backends/base/operations.py`, backend overrides): UNCHANGED by the
  patch. Declared `opaque castDate` / `opaque castTime` (signatures only). They
  are applied to the SAME `lhs` and the selected zone on both the spec and impl
  sides, so they are tagged **I** and consume NO axiom — a wrong zone yields a
  syntactically different application that the proof cannot equate.
- `timezone.get_current_timezone_name()` (`django/utils/timezone.py`): UNCHANGED
  nullary callee. Its value is modeled as the free input `currentZone`
  (universally quantified), so no axiom is needed.
- `timezone._get_timezone_name(tzinfo)` (`django/utils/timezone.py`): UNCHANGED.
  It extracts a zone NAME string from a tzinfo object. We model `self.tzinfo` by
  that very name (`requestedZone : Option String`), so the extraction is the
  identity on the carried name — an **A-reference** validated by G-AX
  (`axiom_check.py`): for the F2P zones it returns exactly the zone name.
- **Flag dependency:** the conversion zone is computed only when `settings.USE_TZ`
  is true; the caller-vs-ambient precedence only matters then. G-CONF fuzzes both
  `USE_TZ` values and both `tzinfo`-present / `tzinfo`-absent configurations.

## Scope note
`TruncDate` and `TruncTime` apply the identical zone-selection fix at two call
sites that differ only in which (unchanged) cast wraps the result; both are
modeled, each with its own cast callee, sharing the `conversionZoneName` helper.
`convert_value` and `resolve_expression` are unchanged and orthogonal.

## G-CONF fuzz seed
Pinned seed: **13363**. ≥10^5 fuzzed inputs over `USE_TZ` ∈ {True, False},
`tzinfo` ∈ {None} ∪ a set of named zones, against the post-patch reference
(`TimezoneMixin.get_tzname`, which is exactly what patched `as_sql` delegates to).
