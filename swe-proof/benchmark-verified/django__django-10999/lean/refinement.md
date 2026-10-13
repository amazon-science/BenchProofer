# refinement.md — django__django-10999

Maps every op in `implementation_durationFromText` to its `patch.diff`
counterpart. Tags: **R** type-refinement, **A-consumed** proof uses a callee
axiom, **A-reference** op left as the real repo callee in G-CONF (not
axiomatized), **I** identical concrete op.

## The patch
The gold patch edits the module-level constant `standard_duration_re`
(`django/utils/dateparse.py:28-37`), consumed by `parse_duration` (`:128-149`):

```diff
-    r'((?:(?P<hours>-?\d+):)(?=\d+:\d+))?'
-    r'(?:(?P<minutes>-?\d+):)?'
-    r'(?P<seconds>-?\d+)'
+    r'(?P<sign>-?)'
+    r'((?:(?P<hours>\d+):)(?=\d+:\d+))?'
+    r'(?:(?P<minutes>\d+):)?'
+    r'(?P<seconds>\d+)'
```

Two coupled behavior changes:
1. a NEW single `sign` group `(?P<sign>-?)` is introduced just before the clock,
   and the existing `sign`-multiplies-the-whole-`timedelta` arithmetic in the
   (unchanged) body now applies it — so one leading `-` negates the WHOLE clock;
2. the inner clock fields lose their `-?`, so hours/minutes/seconds are now
   NON-negative — an inner-field minus (`-01:-01`) no longer matches the standard
   format (and is rejected overall, as the other notations don't match either).

The `parse_duration` BODY is unchanged; the model reflects the regex change as a
change in WHICH `(days, sign, h, m, s, µs)` decomposition the standard branch
produces.

## Modeling decision
`parse_duration` is modeled as `durationFromText : List Char → Option Int`
(microseconds; the timedelta↔µs bijection is in mapping.md). The CHANGED standard
clock branch is modeled DEEPLY as `primaryFormatMicros`; the UNCHANGED
ISO-8601 + PostgreSQL alternative branches are one A-reference
`fallbackFormatMicros`. The spec pins
`result = (primaryFormatMicros v).orElse (fallbackFormatMicros v)` exactly
(directive 5/8: no free output component; grounded structurally in the input
text, not an oracle).

## Domain of the model (the two side conditions on the obligation)

`problem_spec_durationFromText` is asserted under two hypotheses, stated in
`Solution.lean`'s header and mirrored by `conformance_check.py`
(`ascii_text` / `primary_in_range`). They exist because two things the real
callee does are not values of `Option Int`:

1. `asciiText v` — the model's digit class is the ASCII run `0`-`9`; Python's
   `\d` and Python's numeric conversions both accept the whole Unicode `Nd`
   repertoire, so `parse_duration("٥")` (U+0665) is `timedelta(seconds=5)` while
   `digitsToNat?` reads no digit at all. That repertoire is a host character
   table, not a property of the notation this bundle models, and it is identical
   pre- and post-patch (so it is not the patch delta). Restricting to code points
   below 128 is exactly where the two digit classes coincide.
2. `primaryInRange v` — `parse_duration` builds `datetime.timedelta(float(days))`,
   then `sign * datetime.timedelta(**kw)`, then their sum, and each of the three
   raises `OverflowError` outside `[-999999999 days, 999999999 days,
   23:59:59.999999]`. `usMin`/`usMax`/`inUsRange` bound the same three quantities
   (day part, signed clock part, sum), so the claim is made exactly where the real
   callee returns a duration rather than raising. Also identical pre- and
   post-patch.

Both conditions are TRUE at every F2P/P2P input and at every witness point in
`properties.py`, so nothing the task turns on is outside the claim; G-CONF counts
the excluded families instead of merely avoiding them, and refuses to pass if
either condition stops selecting anything.

## Operation correspondence
| # | Lean op (`implementation_durationFromText` / `primaryFormatMicros` & helpers) | patch.diff op | tag | note |
|---|---|---|---|---|
| 1 | `splitFirstSpace v` + `signedIntToInt? before`; `d * 86400 * 10^6` | `(?:(?P<days>-?\d+) (days?, )?)?` group + `days = timedelta(float(days or 0))` | R | optional signed day count, space-delimited, optional unit word; days contribute OUTSIDE the clock sign (own sign). UNCHANGED by patch but part of the standard branch. |
| 2 | `match rest with '-' :: t => (true,t)` (the `neg` flag in `parseClockMicros?`) | NEW `(?P<sign>-?)` group + `sign = -1 if sign=='-' else 1`; `days + sign*timedelta(...)` | **R (the fix)** | the single leading minus becomes a whole-clock sign. This is the changed token: pre-patch had no such group. |
| 3 | `splitOnChar ':' body` → 1/2/3 fields; `digitsToNat?` on h/m | `((?:(?P<hours>\d+):)(?=\d+:\d+))?` and `(?:(?P<minutes>\d+):)?` with `\d+` (no `-?`) | **R (the fix)** | hours/minutes are now NON-negative digit runs; `digitsToNat?` rejects a leading `-`, matching the dropped `-?`. The 2-vs-3 field disambiguation mirrors the `(?=\d+:\d+)` lookahead (hours only when two more colon groups follow). |
| 4 | `parseSecMicro? a`: `digitsToNat?` seconds + optional `.frac` | `(?P<seconds>\d+)` (no `-?`) and `(?:\.(?P<microseconds>\d{1,6})\d{0,6})?` | **R (the fix)** | seconds non-negative; fractional part is 1–12 digits, first ≤6 kept and right-padded to six → µs; surplus digits dropped (`\d{1,6}\d{0,6}`). With seconds now `\d+`, the pre-patch `seconds.startswith('-')` µs-sign hack is dead. |
| 5 | `clockUs h m s us` + `applySign neg` | `sign * timedelta(hours=h, minutes=m, seconds=s, microseconds=µs)` | I | fixed arithmetic h·3600·10⁶ + m·60·10⁶ + s·10⁶ + µs, negated as a whole iff `neg`. |
| 6 | `match primaryFormatMicros v with | some us => some us | none => fallbackFormatMicros v` | `standard_duration_re.match(v) or iso8601_duration_re.match(v) or postgres_interval_re.match(v)` | R + A-reference | first-match-wins: standard branch (deep, ops 1–5) else the unchanged ISO-8601/PostgreSQL arms, left as the REAL parsing in G-CONF (A-reference `fallbackFormatMicros`). |

## R/I legs ⇒ G-CONF; A legs ⇒ G-AX
Ops 1–6 are R/I (deep model of the standard branch). The sole A-reference is
`fallbackFormatMicros` (op 6 fallback) — G-CONF leaves it as the real
ISO-8601 / PostgreSQL parsing and differential-tests the whole shadow against the
post-patch `parse_duration` over 150k fuzzed inputs (0 disagreements, seed
10999). No consumed axiom ⇒ G-AX is a skip stub.

## Prepatch (G-DIFF)
`Solution_prepatch.lean` keeps the spec byte-identical and swaps the impl to a
PRE-FIX skeleton (`primaryFormatMicrosBug`): no single leading `sign` group, every
clock field independently signed (`signedIntToInt?`), µs inheriting the seconds
sign — the exact pre-patch regex semantics. The carried gold proof
(`cases … <;> rfl`) fails to typecheck against it (the pre-fix decomposition is
not definitionally the post-fix one), so the prepatch fails G-VERIFY. This is the
real bug: `-15:30` → `-15min +30s` (pre) vs `-(15min+30s)` (post); `-01:-01`
accepted (pre) vs rejected (post).
