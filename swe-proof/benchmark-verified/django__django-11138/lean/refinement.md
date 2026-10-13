# refinement.md — django__django-11138

Maps every operation in `implementation_tzConvertSql` to its `patch.diff`
counterpart in `mysql/operations.py::_convert_field_to_tz` (the modeled
representative — see mapping.md). Tags: **R** type-refinement, **A-consumed**
proof uses a callee axiom, **A-reference** deep-modeled changed op validated ==
real callee, **I** identical concrete op.

## Patch (post-patch mysql `_convert_field_to_tz`)
```python
def _convert_field_to_tz(self, field_name, tzname):
    if settings.USE_TZ and self.connection.timezone_name != tzname:
        field_name = "CONVERT_TZ(%s, '%s', '%s')" % (field_name, self.connection.timezone_name, tzname)
    return field_name
```

## Operation correspondence
| # | Lean op (`implementation_tzConvertSql`) | patch.diff op | tag | note |
|---|---|---|---|---|
| 1 | `let mut field := fieldName` | `field_name` parameter, returned unchanged by default | I | initialize accumulator to the column expression |
| 2 | `if useTz && connTz != tzname then` | `if settings.USE_TZ and self.connection.timezone_name != tzname:` | R | `settings.USE_TZ : bool ↔ useTz : Bool`; `self.connection.timezone_name : str ↔ connTz : String`; `tzname : str ↔ tzname : String`; Python `and`/`!=` ↔ Lean `&&`/`!=` (string `bne`). Type bijection in mapping.md. |
| 3 | `field := convertTzFragment field connTz tzname` | `field_name = "CONVERT_TZ(%s, '%s', '%s')" % (field_name, self.connection.timezone_name, tzname)` | I | `%`-formatting modeled as exact string concatenation (`convertTzFragment` in the `pure` region produces the identical bytes). |
| 4 | `return field` | `return field_name` | I | return the (possibly wrapped) expression. |

Every op is R or I; **no A row** (no axiom consumed, no deep-model reference).
Therefore `meta.json axioms = []`, `deep_model_references = []`, and
`axiom_check.py` is a skip stub.

## R/I legs ⇒ G-CONF
The whole impl is R/I, so `conformance_check.py` mechanically differential-tests
the impl shadow against `patch.diff` behavior over ≥10^5 fuzzed inputs.
`conf_skip = false`.

## Sibling sites (NOT separately modeled — same logical change)
`patch.diff` also fixes the oracle and sqlite backends. They apply the IDENTICAL
decision rule (*source = connection time zone; convert only when source ≠ target,
and only under TZ support*) in their own SQL/callback dialects:

- oracle `_convert_field_to_tz`: emits `CAST((FROM_TZ(%s, '<src>') AT TIME ZONE
  '<dst>') AS TIMESTAMP)` and likewise skips the cast when `src == dst`. Same
  predicate, different wrapper string.
- sqlite `_convert_tznames_to_sql` + `_sqlite_datetime_parse`: threads the
  connection time-zone name as an extra callback argument; the parse routine
  stamps the source time zone and converts only when `tzname != conn_tzname`.
  Same predicate, expressed at runtime in Python rather than in SQL text.

These are behavior-identical instances of the modeled predicate; `patch.diff`
(gold verbatim) fixes all three so the official harness resolves. The single
F2P test (`test_query_convert_timezones`) exercises the predicate (equal-tz ⇒ no
conversion; unequal-tz ⇒ conversion) — exactly what `problem_spec_tzConvertSql`
pins.
