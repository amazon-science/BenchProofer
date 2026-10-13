# mapping.md — django__django-10999

## Symbol binding (@ base_commit 36300ef336e3f130a0dadc1143163ff3d23dc843)
- Modeled function: `parse_duration(value)` — `django/utils/dateparse.py:128-149`.
  The fix edits the module-level regex constant `standard_duration_re`
  (`django/utils/dateparse.py:28-37`) that `parse_duration` consumes via its
  first match arm; the body of `parse_duration` is unchanged.
- Lean modeled name: `durationFromText` (does NOT echo the repo symbol;
  describes the behavior — interpret a textual duration into microseconds).

## Behavior under model
`parse_duration` tries three text formats, in order:
1. the standard `[D ](H:)?(M:)?S(.f)?` format (`standard_duration_re`) — **the
   changed format**, modeled deeply as `standardFormatMicros`;
2. the ISO-8601 alternative (`iso8601_duration_re`) — unchanged;
3. the PostgreSQL day-time interval alternative (`postgres_interval_re`) — unchanged.

The first format that matches wins; the matched groups feed a fixed arithmetic
(`days + sign*timedelta(hours,minutes,seconds,microseconds)`) producing a
`datetime.timedelta`. Formats 2+3 are the unchanged tail, modeled together as a
single opaque reference `extendedFormatMicros` (A-reference; G-CONF substitutes
the real `iso8601`/`postgres` parsing, no consumed axiom).

The A-reference name in `Solution.lean` is `fallbackFormatMicros` (this document's
`extendedFormatMicros` is the same symbol under its earlier name).

## Domain of the claim
The Lean obligation carries two hypotheses (`asciiText v`, `primaryInRange v`);
`refinement.md` §"Domain of the model" gives the derivation. In bridge terms: the
`str → List Char` mapping is per-code-point and total, but the DIGIT class is not
bijective outside ASCII (Python `\d` and `float()` accept all Unicode `Nd`), and
`datetime.timedelta` is a BOUNDED carrier while `Int` is not (`OverflowError` is
not an inhabitant of `Option Int`). The two conditions restrict the claim to where
the bridge above is exact.

## Type bijection (Lean ↔ Python) — used by G-CONF and G-AX
| Python | Lean | bridge |
|---|---|---|
| input `value : str` | `v : List Char` | per-code-point; `String.toList` |
| `datetime.timedelta` value | `Int` = total microseconds | `td.total_seconds()*10**6`, rounded to exact int (timedelta has µs resolution); equality of timedeltas ⇔ equality of total microseconds |
| `parse_duration` returns `None` | `none : Option Int` | regex no-match / value error |
| `parse_duration` returns a `timedelta` | `some (µs : Int)` | as above |
| days group `(-?\d+)` | `Int` (sign embedded) | `days * 86400 * 10^6` µs, added OUTSIDE the time sign |
| post-patch `sign` group `(-?)` | `neg : Bool` | multiplies the whole H:M:S µs quantity |
| `hours`/`minutes`/`seconds` groups `(\d+)` | `Nat` (non-negative, post-patch) | h*3600·10⁶ + m*60·10⁶ + s·10⁶ |
| `microseconds` group `\d{1,6}\d{0,6}` | `Nat` (first ≤6 digits, right-padded to 6) | `int(g[:6].ljust(6,'0'))`; ≥1 and ≤12 fractional digits, else no match |

## Standard-format grammar (post-patch, what `standardFormatMicros` decodes)
```
input        := daysPrefix? sign timePart frac?
daysPrefix   := '-'? DIGITS ' ' ('days, ' | 'day, ')?      -- greedy, optional
sign         := '-'?                                        -- the NEW group; negates the whole timePart
timePart     := DIGITS (':' DIGITS (':' DIGITS)?)?          -- 1..3 colon-separated non-negative fields
                -- 1 field = seconds; 2 = minutes:seconds; 3 = hours:minutes:seconds
frac         := '.' DIGITS                                  -- on the seconds field; 1..12 digits, first 6 kept
```
Every numeric field except the optional days count is **non-negative** post-patch;
the single leading `sign` minus negates the whole H:M:S(.f) quantity. The days
count keeps its own independent sign.

## Callee provenance / flag deps
- `extendedFormatMicros` (A-reference) = the unchanged `iso8601_duration_re` +
  `postgres_interval_re` parsing arms of `parse_duration`. No flags. Validated by
  G-CONF (left as the real parsing in the shadow). No consumed axiom → G-AX is a
  skip stub.

## G-CONF fuzz seed
Pinned seed: `10999` (see conformance_check.py). ≥10^5 fuzzed inputs spanning:
days-prefix present/absent and both unit spellings, leading sign present/absent,
1/2/3 colon fields, inner-negative fields (must reject), 0..14 fractional digits,
boundary/empty/garbage strings, plus the ISO-8601 / PostgreSQL alternative forms.
