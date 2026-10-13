# mapping.md — django__django-11848

## Modeled function

| Lean | Python | file:line @ base_commit `f0adf3b9b7` |
|---|---|---|
| `implementation_expandYear` / `problem_spec_expandYear` / `correct_expandYear` | the two-digit-year expansion block inside `parse_http_date(date)` | `django/utils/http.py:177-186` (the `if year < 100:` branch) |

The modeled behavior is exactly the `if year < 100:` block of `parse_http_date`:
given the parsed integer `year` field and the current full year, it expands a
two-digit year to a full year. The surrounding parse (regex matching, month/day
lookup, `datetime`/`calendar.timegm` assembly) is unchanged by the patch and is
outside the modeled function — the gold diff touches only this block.

## Type bijection (Lean ↔ Python) — used by G-CONF + G-AX

| Python | Lean | notes |
|---|---|---|
| `year = int(m.group('year'))` (`int`, ≥ 0) | `year : Int` | parsed year field; a two-digit year is `0 … 99`; values `≥ 100` are already full years |
| `current_year = datetime.datetime.utcnow().year` (`int`) | `currentYear : Int` | the reference current year. Modeled as an explicit INPUT, not a callee (see below) |
| expanded `year` after the block (`int`) | `result : Int` | the full year the block produces |
| `current_year % 100` (Python `%`, non-negative for non-negative operands) | `currentYear % 100` (Lean `Int.emod`) | for `currentYear ≥ 0` both give the non-negative last-two-digits; bijection holds on the domain |
| `current_century = current_year - (current_year % 100)` | `cc := currentYear - currentYear % 100` | hundreds component of the current year |

## Callee provenance / flag deps

- The only call introduced by the patch is `datetime.datetime.utcnow().year`,
  read once to obtain the current full year. This is **not** axiomatized as a
  callee: its result is the reference point of the computation, supplied to the
  modeled function as the explicit input `currentYear`. The F2P test itself
  mocks `datetime.datetime.utcnow` to pin this to fixed years, confirming the
  expansion is a pure function of `(year, currentYear)`. Hence the `axioms`
  region declares no `opaque` and the proof needs no `_prop` axiom.
- No other UNCHANGED callee participates: the block is pure integer arithmetic
  (`+`, `-`, `%`, comparison). It is modeled deeply (I/R ops), G-CONF-checked.
- The `axioms` region is empty ⇒ **G-AX = skip** (no callee axiom to validate).

## Out-of-scope context (not modeled)

`parse_http_date` continues by building a `datetime` and calling
`calendar.timegm`. The gold patch does not touch any of that; it is unchanged
and is not part of the modeled function. No second triple / prepatch is needed —
there is a single independently-observable fixed behavior (the year expansion).

## G-CONF fuzz seed

`conf_seed = 11848` (pinned; see conformance_check.py and meta.json).
