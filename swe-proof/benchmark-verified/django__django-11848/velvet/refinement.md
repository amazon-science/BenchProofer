# refinement.md — django__django-11848

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `resolveAbbreviatedYear` `do` block and the deep `resolvedFullYear` model)
and `patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A-consumed** (proof uses an axiom's `ensures`), **A-reference** (deep model
validated == a real callee by G-AX), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. This bundle has
**no A legs**: the changed arithmetic is modeled deeply and validated entirely
by G-CONF (see §C). Claim: any impl verifying against this frozen spec, refined
per the map below, is behaviourally equal to the gold patch on the tested
inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The abbreviated-year resolution — `parse_http_date` (`django/utils/http.py:178-185`)

Gold hunk:
```
  year = int(m.group('year'))
  if year < 100:
-     if year < 70:
-         year += 2000
+     current_year = datetime.datetime.utcnow().year
+     current_century = current_year - (current_year % 100)
+     if year - (current_year % 100) > 50:
+         # year that appears to be more than 50 years in the future are
+         # interpreted as representing the past.
+         year += current_century - 100
      else:
-         year += 1900
+         year += current_century
```

| # | Solution.lean impl op (`resolveAbbreviatedYear`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `yy : Int`, `require 0 ≤ yy ∧ yy ≤ 99` | `year = int(m.group('year'))` under the `year < 100` guard | R | `int` ↔ `Int`; the RFC850 regex `(?P<year>\d{2})` forces `0..99` (mapping.md §1, §2). |
| A2 | parameter `cur : Int`, `require 0 ≤ cur` | `current_year = datetime.datetime.utcnow().year` | R | the current calendar year, modeled as a free non-negative input — **not** an axiomatized callee (mapping.md §3); `int` ↔ `Int`. |
| A3 | `let cc := cur % 100` | `current_year % 100` (inside `current_century` and the `>50` test) | I | identical concrete op; Python `%` and Lean `Int` `%` agree on the non-negative `cur` (mapping.md §2). |
| A4 | `let century := cur - cc` | `current_century = current_year - (current_year % 100)` | I | identical concrete op (the hundreds floor). |
| A5 | `if yy - cc > 50 then yy + century - 100 else yy + century` | `if year - (current_year % 100) > 50: year += current_century - 100 else: year += current_century` | I | identical concrete op: the `+=` accumulations `year += current_century - 100` / `year += current_century` equal `yy + century - 100` / `yy + century` because `year == yy` at this point; the guard `year - (current_year % 100) > 50` is `yy - cc > 50`. |
| A6 | `return out` (`Int`) | the mutated `year` flows on to `datetime.datetime(year, …)` then `calendar.timegm(...)` | R | the resolved full year `int` ↔ `Int`; the unchanged downstream (datetime construction + epoch conversion) is observationally the identity on the resolved year and is re-exercised end-to-end by G-CONF (mapping.md §1). |

Discriminating content of the change — a two-digit year is resolved **relative
to the current year** (rolling back a century when it would land more than 50
years in the future) rather than against a **fixed cutoff of 70** — lives in
`if yy - cc > 50 then yy + century - 100 else yy + century` (model) ⇔ the
patched branch (real). The pre-patch code used `if year < 70: +2000 else:
+1900`; `Solution_prepatch.lean` reproduces that fixed cutoff and **fails** the
clause `out = resolvedFullYear yy cur` (G-DIFF) — e.g. at `yy=70, cur=2020` the
fixed cutoff gives `1970` but the spec demands `2070`.

## B. The supporting (non-discriminating) postconditions

| # | Solution.lean construct | role | tag | justification |
|---|---|---|---|---|
| B1 | `ensures (out - yy) % 100 = 0` | the result keeps `yy`'s last two digits | I (spec-side) | structural invariant of the resolution (it adds whole centuries); grounds the postcondition in the input rather than an oracle (SPEC_GUIDE §0.8). |
| B2 | `ensures cur - 100 < out ∧ out ≤ cur + 50` | the result lies in the half-century window ending 50 years after the reference | I (spec-side) | encodes the RFC 7231 rule directly ("more than 50 years in the future ⇒ past"); pins behavior with an arithmetic relation on the actual inputs, not an answer key. |

B1/B2 are not separate impl ops; they are additional `ensures` clauses that the
single returned value must satisfy, tightening the spec so no wrong resolution
verifies (G-PANEL attacker 1 / G-MUT). They are provable from `resolvedFullYear`
by `omega`.

## C. No A legs; no kind-3 (inexpressible-changed-op) steps

Every step is R or I. There is **no consumed axiom** and **no A-reference**: the
one operation that genuinely *changed* — the abbreviated-year resolution — is
modeled **deeply** as plain integer arithmetic (`resolvedFullYear`), and the
only external value it reads, the current year, is a free input (`cur`), not a
callee with an assumed contract. Therefore nothing is audited by G-AX (G-AX
`skip`, no `axiom_check.py`); the deep model's fidelity to the real patched
`parse_http_date` is established end-to-end by **G-CONF** over ≥10⁵ fuzzed
`(yy, cur)` pairs.

## D. verify(Solution) ⇒ resolved

`resolveAbbreviatedYear` verifies only if its output equals the current-year-
relative resolution `resolvedFullYear yy cur` (A5), keeps the last two digits
(B1), and lands in the `(cur-100, cur+50]` window (B2). By R (`int ↔ Int`, the
`utcnow().year` free-input model, the unchanged downstream identity on the
resolved year) the verified arithmetic equals the patched
`year`-resolution inside `parse_http_date`; by G-CONF the R/I transliteration of
that arithmetic agrees with `patch.diff`'s observable behaviour (the resolved
full year recovered through `datetime`/`calendar.timegm`) on ≥10⁵ inputs,
including the seven F2P matrix rows and the cutoff edges. Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement — and the gold patch resolves (G-RESOLVE). The sole trust point is
refinement fidelity (this doc, G-EQ + G-CONF); there are no axioms to trust.
