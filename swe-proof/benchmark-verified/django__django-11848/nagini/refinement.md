# refinement.md — django__django-11848

The operation-by-operation correspondence between `model.py`'s implementation
(the `expand_two_digit_year` impl region, plus the deep `resolved_year` /
`century_start` model in the `pure` region) and `patch.diff` (the gold patch).
Each step is tagged **R** (type refinement), **A** (axiomatized callee — split
into **A-consumed**, where the proof uses an axiom's `Ensures`, and
**A-reference**, where a deep model is validated `==` the real callee by
axiom_check.py / G-AX), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The two-digit-year expansion site — `parse_http_date` (`django/utils/http.py:178-186`)

Gold hunk:
```
         year = int(m.group('year'))
         if year < 100:
-            if year < 70:
-                year += 2000
+            current_year = datetime.datetime.utcnow().year
+            current_century = current_year - (current_year % 100)
+            if year - (current_year % 100) > 50:
+                # year that appears to be more than 50 years in the future are
+                # interpreted as representing the past.
+                year += current_century - 100
             else:
-                year += 1900
+                year += current_century
```

| # | model.py impl op (`expand_two_digit_year`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `two_digit_year: int` (`0 <= _ < 100`) | `year = int(m.group('year'))` under the `if year < 100:` guard | R | identity on the integer; the guard fixes the 0..99 domain (mapping.md §2). |
| A2 | parameter `reference_year: int` (`>= 1000`) | `current_year = datetime.datetime.utcnow().year` | A-reference | the unchanged wall-clock source is abstracted to its returned integer value. There is NO consumed axiom: the model carries the value as a parameter. G-AX confirms `utcnow().year` is a real four-digit `int` (mapping.md §3.1). |
| A3 | `base = reference_year - (reference_year % 100)` | `current_century = current_year - (current_year % 100)` | I | identical integer arithmetic (`%`, `-`). |
| A4 | `if two_digit_year - (reference_year % 100) > 50:` | `if year - (current_year % 100) > 50:` | I | identical guard. |
| A5 | `result = two_digit_year + base - 100` | `year += current_century - 100` | I | identical arithmetic (the future-rollback branch). |
| A6 | `result = two_digit_year + base` (else) | `year += current_century` | I | identical arithmetic (the same-century branch). |
| A7 | `return result` | the assembled `year` flows into `datetime.datetime(year, ...)` then `calendar.timegm(...)` | R | identity on the full-year integer; the surrounding date assembly is unchanged by the patch and observes only this integer (mapping.md §2). |

The deep model `resolved_year` (consumed by the postcondition
`Result() == resolved_year(two_digit_year, reference_year)`) is the spelled-out
form of A3–A6; it is an **A-reference**, validated `== ` the real patch
arithmetic by axiom_check.py / G-AX over the full two-digit domain × many
reference years (boundary + exhaustive + 200 000 fuzz). It is NOT a consumed
`@ContractOnly` axiom — the bundle ships no `@ContractOnly`.

## B. The discriminating behaviour (G-DIFF)

The pre-patch code expands the two-digit year against a FIXED cut-off (`year <
70 → +2000`, else `+1900`) that ignores the current year. `model_prepatch.py`
reproduces exactly that skeleton (`if two_digit_year < 70: +2000 else: +1900`)
under the byte-identical spec and **fails** the postcondition
`Result() == resolved_year(two_digit_year, reference_year)` — the spec demands
the reference-relative result for every `reference_year >= 1000`, and the fixed
cut-off disagrees whenever the reference century's last two digits differ from
70 (e.g. `reference_year=2020, year=70`: spec ⇒ 2070, fixed cut-off ⇒ 1970).
That is precisely the spec sensing the change. (Confirmed: prepatch fails at
`model_prepatch.py:66` on the `resolved_year` clause.)

The two F2P tests:
* `test_parsing_rfc850` (rewritten by the test_patch to mock `utcnow` at 2019 /
  2020 / 2048) pins the seven reference-relative cases — all reproduced by
  `resolved_year` (axiom_check.py §pinned) and all *broken* by the fixed cut-off.
* `test_parsing_year_less_than_70` (`'... 0037'`, `year=37`) expects `2037`;
  `resolved_year(37, ref)` for any real `ref` in `[2000, 2087]` gives `2037`
  (`37 - ref%100 <= 50` ⇒ `37 + current_century`), matching.

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The operation that genuinely changed
— the two-digit-year expansion — is modelled **deeply** as exact integer
arithmetic (`resolved_year` / `century_start`, A3–A6), not hidden behind an
axiom about the changed function. The only abstracted entity is the **unchanged**
wall-clock value `utcnow().year` (A2, an A-reference whose provenance G-AX
checks); no `@ContractOnly` axiom is consumed.

## D. verify(model) ⇒ resolved

`expand_two_digit_year` verifies only if its output equals
`resolved_year(two_digit_year, reference_year)` (A3–A6, exact integer
arithmetic) for every two-digit year and every reference year `>= 1000`. By the
R-refinements (integer identities on `year` and on `utcnow().year`, and the
unchanged surrounding date assembly) the verified result equals the full year
the gold patch assigns. By G-AX the deep model equals the real patch arithmetic
(A-reference) and `utcnow().year` is the real four-digit reference year.
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement and the audited wall-clock abstraction — and the
gold patch resolves (G-RESOLVE). The trust points are exactly those of PLAN
§1.1: the A-reference soundness (G-AX) and refinement fidelity (this document,
G-EQ).
