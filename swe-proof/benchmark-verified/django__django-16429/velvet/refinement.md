# refinement.md — django__django-16429

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`buildShiftedReference` `do` block and the deep model `shiftReference`/`monthLen`)
and `patch.diff` (the gold patch). Each step is tagged **R** (type refinement;
state the bijection), **A-consumed** (proof uses an axiom's `ensures`),
**A-reference** (deep model validated == real callee by G-AX), or **I**
(identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. This bundle has
**no A legs** (no foreign callee is axiomatized — §C), so G-CONF carries the
full mechanical burden and G-EQ audits only the narrative.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The reference-construction site — `timesince()` (`django/utils/timesince.py:87-102`)

Gold hunk:
```
             d.hour,
             d.minute,
             d.second,
+            tzinfo=d.tzinfo,
         )
```
i.e. the shifted-reference constructor
```python
pivot = datetime.datetime(
    pivot_year,
    pivot_month,
    min(MONTHS_DAYS[pivot_month - 1], d.day),
    d.hour,
    d.minute,
    d.second,
    tzinfo=d.tzinfo,        # gold-added
)
```
is reached inside `if years or months:`. Modeled method: `buildShiftedReference`,
deep model `shiftReference`.

| # | Solution.lean impl op (`buildShiftedReference`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `base : Instant` | the source datetime `d` | R | `datetime` ↔ `Instant` field-wise (mapping.md §2): `d.year↔.y … d.second↔.s`, `d.tzinfo↔.zone`. |
| A2 | parameters `years`, `months : Nat` | `years, months = divmod(total_months, 12)` | R | `Nat` ↔ non-negative int; `months ≤ 11` (`require`), site reached only when `years or months` (`require 0 < years ∨ 0 < months`). |
| A3 | `py := base.y + years` | `pivot_year = d.year + years` | I | identical integer addition. |
| A4 | `pm := base.mo + months`; `pm' = if pm>12 then pm-12 else pm`; `py' = if pm>12 then py+1 else py` | `pivot_month = d.month + months` then `if pivot_month > 12: pivot_month -= 12; pivot_year += 1` | I | identical month-overflow normalization; `pm ≤ 12+11 = 23`, one `-12` suffices. |
| A5 | `d := min (monthLen pm') base.d` | `min(MONTHS_DAYS[pivot_month - 1], d.day)` | I | `monthLen m = MONTHS_DAYS[m-1]` for `m∈1..12` (mapping.md §2; G-CONF imports the real `MONTHS_DAYS`); `min` over non-negative ints. |
| A6 | `h := base.h, mi := base.mi, s := base.s` | `d.hour, d.minute, d.second` | I | carried across verbatim. |
| A7 | `zone := base.zone` | `tzinfo=d.tzinfo` (**the gold-added line**) | I + R | the changed op: the constructed reference carries the source's time-zone designation. R: `tzinfo ↔ Option Nat` preserves identity/`None`-ness (mapping.md §2). This is the single behavioral change. |
| A8 | result `Instant` literal | the `datetime.datetime(...)` value | R | the `Instant` structure literal IS the constructor over the touched fields; `datetime.datetime(...)` is the language value constructor, not a foreign callee. |

## Discriminating clause / prepatch

The behavioral change lives entirely in **A7**. `Solution_prepatch.lean`
(byte-identical spec, G-DIFF) builds the reference with `zone := none` — the
pre-patch constructor with no `tzinfo` keyword, which defaults `tzinfo` to
`None`. It therefore fails `out = shiftReference base years months` precisely at
the `zone` field (`none ≠ base.zone` whenever `base.zone = some k`), i.e. when
the source is tz-aware. This is exactly the regression the F2P tests catch:
under `USE_TZ=True` a tz-aware `d` ≥ 1 month in the past produced a tz-naive
reference, and the downstream difference between the (aware) other instant and
the (naive) reference is undefined — the reported `TypeError`.

## C. No kind-3 (inexpressible-changed-op) steps; no A legs

Every step is R or I. The operation that genuinely changed — propagating the
source's time-zone designation onto the constructed reference (A7) — is modeled
**directly** in the impl and deep model, not behind an axiom. There is no
unchanged foreign callee the proof depends on: the reference is built field-by-
field from `base`, `years`, `months`, and the concrete `MONTHS_DAYS` table
(transliterated to `monthLen`). Hence **no consumed axiom and no deep-model
reference** (`axioms` region empty; `meta.json axioms=[]`,
`deep_model_references=[]`; **G-AX skips**). The time-zone designation is an R
refinement of the Python `tzinfo`/`None` distinction (mapping.md §2), checked by
G-CONF.

## D. verify(Solution) ⇒ resolved

`buildShiftedReference` verifies only if the constructed reference carries
`zone := base.zone` (A7) — i.e. only the gold data-flow satisfies the frozen
spec. By R (datetime↔Instant field bijection, `tzinfo`↔`Option Nat`) and the I
legs (the arithmetic, the `min`/`MONTHS_DAYS` clamp, the field carry-overs) the
verified reference equals the patched `datetime.datetime(..., tzinfo=d.tzinfo)`
on every input. G-CONF refutes any R/I infidelity over fuzzed `(d, now)` pairs —
including tz-aware sources, where it confirms the real patched `timesince`
output matches the shadow built with `shiftReference` and (separately) that the
pre-patch path raised. Therefore a model satisfying this spec, refined by the map
above, is the gold patch up to type refinement — and the gold patch resolves
(G-RESOLVE). The only trust point is refinement fidelity (this doc + G-CONF);
there is no axiom trust point for this bundle.
