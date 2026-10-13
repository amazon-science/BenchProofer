# mapping.md — django__django-10999

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 36300ef336e3f130a0dadc1143163ff3d23dc843`, states the type
abstraction, and gives the provenance of the deep-model reference (there are no
consumed `@ContractOnly` axioms in this bundle).

Repo file under change: `django/utils/dateparse.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `parse_clock_seconds(fields, leading_minus, inner_sign_seen)` | the standard-duration branch of `parse_duration(value)` — `django/utils/dateparse.py:124` (sign logic at 138–146) driven by `standard_duration_re` — `django/utils/dateparse.py:29` | the modeled changed behaviour: how a colon-form clock literal's leading sign and validity are interpreted, expressed as a signed total in the smallest unit (seconds) |
| `clock_value(fields)` *(deep model)* | the positional `H*3600 + M*60 + S` combination produced by feeding the regex's `hours`/`minutes`/`seconds` named groups into `datetime.timedelta(**kw)` (`dateparse.py:145–146`) | pure spec: the base-60 clock combination of 1..3 non-negative fields |
| `signed_total(fields, leading_minus)` *(deep model — A-reference)* | the whole-value sign application `sign * datetime.timedelta(**kw)` with `sign = -1 if kw.pop('sign','+')=='-' else 1` (`dateparse.py:139`,`146`) **using the post-patch `(?P<sign>-?)` group** | pure spec: the single leading sign negates the whole clock value; validated `== real` by axiom_check.py (G-AX), NOT consumed as an axiom |
| `pow60(k)` | the positional weights `3600 = 60**2`, `60 = 60**1`, `1 = 60**0` implicit in `timedelta(hours=, minutes=, seconds=)` | pure spec: clock-position weight |

The pre-patch repo construct the change removes (for the refinement audit, not
referenced from the consumer spec view): the per-field optional signs
`(?P<hours>-?\d+)`, `(?P<minutes>-?\d+)`, `(?P<seconds>-?\d+)` and the
sign-free lookahead `(?=\d+:\d+)` (`dateparse.py:32–34`), which attached the
minus to only the leading field and accepted a minus after a separator.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| the input `str` (a standard-duration literal) | decomposed into `fields: List[int]` (1..3 non-negative field magnitudes), `leading_minus: bool`, `inner_sign_seen: bool` | the regex's named groups `hours`/`minutes`/`seconds` ↔ the entries of `fields` (hours first when present); the leading `(?P<sign>-?)` capturing `'-'` ↔ `leading_minus`; a sign character appearing after a `:` separator (which the post-patch `\d+` fields refuse to match) ↔ `inner_sign_seen` |
| a regex-captured numeric field, e.g. `int(m.group('seconds'))` | a non-negative `int` entry of `fields` | unchanged decimal-digit run `\d+` read as a non-negative integer (the digit-scanning machinery is not changed by the patch); this is the R boundary — the model takes the already-extracted magnitudes |
| the produced `datetime.timedelta`, compared for equality in the tests | the signed integer total seconds returned (or `None`) | two `timedelta`s with no microsecond part are equal iff their total whole seconds are equal; the modeled literals have no fractional part, so `td.total_seconds()` is an integer and the bijection is exact (the tests compare `timedelta` objects) |
| no standard-duration match (regex fails) | `None` | the `Optional[int]` absent value |

`str` indexing/iteration is banned in Nagini; the carrier is therefore the
extracted `List[int]` of field magnitudes plus two boolean flags. The
specification is carried by `PSeq[int]` via `ToSeq`.

## 3. Deep-model reference (kind A-reference — checked by G-AX / axiom_check.py)

### 3.1 `signed_total` / `clock_value` / validity rule ↔ real post-patch pipeline (A-reference)

**Callee being modeled:** the post-patch standard-duration interpretation =
`standard_duration_re` (the gold patch's regex) feeding the sign logic of
`django.utils.dateparse.parse_duration`. The changed behaviour is modeled
**deeply** — `clock_value`, `signed_total`, and the `parse_clock_seconds`
validity rule in the `pure`/impl regions — so there is **no `@ContractOnly`
axiom the proof consumes**. The deep model is instead validated equal to the
real callee out-of-band by axiom_check.py (G-AX).

Post-patch regex (gold patch verbatim; `django/utils/dateparse.py:29`):
```python
standard_duration_re = re.compile(
    r'^'
    r'(?:(?P<days>-?\d+) (days?, )?)?'
    r'(?P<sign>-?)'
    r'((?:(?P<hours>\d+):)(?=\d+:\d+))?'
    r'(?:(?P<minutes>\d+):)?'
    r'(?P<seconds>\d+)'
    r'(?:\.(?P<microseconds>\d{1,6})\d{0,6})?'
    r'$'
)
```
and the sign application (`parse_duration`, `dateparse.py:138–146`):
```python
sign = -1 if kw.pop('sign', '+') == '-' else 1
...
return days + sign * datetime.timedelta(**kw)
```

Three observable consequences this encodes (all exercised by the F2P
`test_negative`):
1. the single leading `(?P<sign>-?)` multiplies the WHOLE `timedelta`, so
   `-H:M:S → -(H*3600+M*60+S)` and `-M:S → -(M*60+S)` — `signed_total`;
2. each field is `\d+` (non-negative), combined positionally as a base-60
   clock — `clock_value`;
3. a sign character after a `:` cannot be consumed by the `\d+` fields, so the
   literal has no standard match (`None`) — the `inner_sign_seen ⇒ None` rule.

**Flag/domain dependence (recorded for G-AX):** the `sign` group is `-?`
(minus only); a leading `+` is NOT a standard-duration sign and is outside the
modeled domain (the model carries only `leading_minus`). The model covers the
no-days, no-fractional colon form; days and microseconds are handled by
unchanged code paths the patch does not touch. axiom_check.py restricts its
comparison to this domain.

**Soundness check (G-AX):** `axiom_check.py` builds the real post-patch
`standard_duration_re` verbatim, runs it + the real `parse_duration` sign logic
on 25 boundary literals (each significant case: single field, `M:S`, `H:M:S`,
leading-minus forms, `-00:01:01`, `-01:01`, and inner-sign literals
`-01:-01`/`01:-01`/`15:-30`) plus 50 000 randomized fuzz literals, and asserts
the real total seconds equals `signed_total(fields, leading_minus)` for every
valid input and that every `inner_sign_seen` input produces no standard match.
It imports only the standard library (`re`, `datetime`, `random`) — `re` is
the engine the patch edits; nothing repo-specific. Exit 0 iff sound.
