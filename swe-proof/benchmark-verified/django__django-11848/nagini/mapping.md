# mapping.md — django__django-11848

Binds every `model.py` symbol to its repository counterpart at
`base_commit = f0adf3b9b7a19cdee05368ff0c0c2d087f011180`, states the type
abstraction, and gives the provenance of the (unchanged) wall-clock source the
deep model abstracts.

Repo file under change: `django/utils/http.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `expand_two_digit_year(two_digit_year, reference_year)` | the two-digit-year branch of `parse_http_date(date)` — `django/utils/http.py:158`, body `178-182` (the `if year < 100:` block) | the modeled changed code: the expansion of a two-digit year to a full year |
| `resolved_year(t, r)` *(deep model — A-reference)* | the arithmetic the patch installs at `django/utils/http.py:178-186` (`current_century = current_year - (current_year % 100)`; `if year - (current_year % 100) > 50: year += current_century - 100; else: year += current_century`) | pure spec: the reference-relative two-digit-year expansion, modelled deeply; validated `== real arithmetic` by axiom_check.py (G-AX), NOT consumed as an axiom |
| `century_start(r)` | `current_century = current_year - (current_year % 100)` (patch) | pure spec: the century start of the reference year |
| `reference_year` (parameter) | `datetime.datetime.utcnow().year` — CPython stdlib `datetime`, called inside `parse_http_date` post-patch (`django/utils/http.py:180`) | the unchanged wall-clock source the new code consults; abstracted as an explicit integer parameter (its value, not the call) |

The pre-patch repo logic the change removes (for the refinement audit, not
referenced from the consumer spec view): the fixed cut-off
`if year < 70: year += 2000 else: year += 1900` at `django/utils/http.py:179-182`.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection / justification |
|---|---|---|
| `year = int(m.group('year'))` after the `year < 100` guard (i.e. a parsed two-digit year, 0..99) | `two_digit_year: int`, `Requires(0 <= two_digit_year and two_digit_year < 100)` | identity on the integer; the guard `if year < 100:` in the surrounding code establishes the domain the modeled branch runs on. The regex `(?P<year>\d{2})` of `RFC850_DATE` and the `year < 100` guard for the others ensure `0 <= year < 100`. |
| `datetime.datetime.utcnow().year` (the current UTC calendar year) | `reference_year: int`, `Requires(reference_year >= 1000)` | identity on the integer value the call returns; a real calendar year is a non-negative four-digit int (G-AX confirms `utcnow().year` is an `int >= 1000`). The exact call is unchanged by the patch — only *that* the year is now consulted is new. |
| the assembled `year` fed to `datetime.datetime(year, ...)` | `Result(): int` | identity: the model returns the same full year integer that the patched code assigns to `year` and passes to the `datetime` constructor. |

`%` (modulo) and integer arithmetic are expressible directly in Nagini, so the
whole computation is modelled concretely; no string handling is involved.

## 3. Provenance of the abstracted source (kind-A — checked by G-AX)

### 3.1 `reference_year` ↔ `datetime.datetime.utcnow().year` (A-reference, not consumed)
**Callee:** CPython `datetime.datetime.utcnow()` returns a naive `datetime`
giving the current Coordinated Universal Time; its `.year` attribute is the
proleptic-Gregorian calendar year (a positive `int`, `MINYEAR=1 .. MAXYEAR=9999`).
Docs: https://docs.python.org/3/library/datetime.html#datetime.datetime.utcnow
and `.year`. The patch reads only `.year`; no other attribute or behaviour of
the call is relied upon.

This source is **unchanged** by the patch and supplies a single integer. There
is therefore **no `@ContractOnly` axiom** to consume: the model takes the value
as a parameter and the changed arithmetic that consumes it (`resolved_year`) is
modelled deeply. G-AX (axiom_check.py) confirms (a) `utcnow().year` is a
plain `int >= 1000` in the real interpreter, and (b) the deep model
`resolved_year` equals the real expansion arithmetic on the full two-digit
domain across many reference years (boundary + exhaustive 0..99 + 200 000 fuzz).

### 3.2 No flag dependencies
The computation has no configuration flags. `utcnow()` is called with no
arguments; `.year` is unconditional. The only sensitivity is to the value of the
current year, which the spec quantifies over (`reference_year >= 1000`) and the
F2P tests pin via `mock.patch('django.utils.http.datetime.datetime')` with
`utcnow` returning fixed `datetime`s (2019/2020/2048).

**Soundness check (G-AX):** `axiom_check.py` re-runs the patch's exact arithmetic
(`current_century = ref - ref%100`; threshold `year - ref%100 > 50`) on every
two-digit year for representative + boundary + 200 000 fuzz reference years and
asserts the deep model `resolved_year` agrees on every observation, plus the
seven F2P-pinned (mocked-utcnow) cases, plus the three auxiliary postconditions.
It imports only the standard-library `datetime` module (the very module the patch
calls). Exit 0 iff sound.
