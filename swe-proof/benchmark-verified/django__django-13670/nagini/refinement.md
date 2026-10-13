# refinement.md — django__django-13670

The operation-by-operation correspondence between `model.py`'s implementation
(the `abbreviated_year` impl region and the deep `tens_digit`/`units_digit`
model) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement), **A** (axiomatized callee — split into **A-consumed**, the proof
uses the axiom's `Ensures`, and **A-reference**, a deep model validated == the
real callee by axiom_check.py / G-AX), or **I** (identical concrete operation).
The claim: *any implementation that verifies against this frozen spec, refined
per the map below, is behaviourally equal to the gold patch on the tested
inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## The changed renderer — `DateFormat.y()` (`django/utils/dateformat.py:327`)

Gold hunk:
```
-        "Year, 2 digits; e.g. '99'"
-        return str(self.data.year)[2:]
+        """Year, 2 digits with leading zeros; e.g. '99'."""
+        return '%02d' % (self.data.year % 100)
```

| # | model.py impl op (`abbreviated_year`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| 1 | parameter `year: int` (`Requires(1 <= year <= 9999)`) | `self.data.year` (the `int` calendar year read by the method) | R | `self.data.year` ↔ the `int` `year`; the datetime year range 1..9999 is the precondition (mapping.md §2). |
| 2 | `v = year % 100` | `self.data.year % 100` | I | the identical integer modulo operation. |
| 3 | `tens_digit(v) == 48 + v // 10` (the most-significant of the two characters) | the tens position of `'%02d' % v` | A-reference | the changed string operation is modelled **deeply**: `tens_digit`/`units_digit` (spelled-out integer arithmetic in the `pure` region) ARE the two-digit decimal emission. There is no consumed format axiom. The deep model is validated **== the real `'%02d' % (year%100)`** out-of-band by G-AX (axiom_check.py) over all 9999 admitted years (mapping.md §3). For `0 <= v <= 99`, `'%02d' % v` is exactly `chr(48 + v//10) + chr(48 + v%10)`. |
| 4 | `units_digit(v) == 48 + v % 10` (the least-significant character) | the units position of `'%02d' % v` | A-reference | as #3: the units digit of the two-character zero-padded rendering. |
| 5 | `result = [tens_digit(v), units_digit(v)]`; `len(Result()) == 2`, each in `0x30..0x39` | the two-character `str` returned (the `'%02d'` produces exactly two zero-padded decimal characters) | R | `str` ↔ `List[int]` code points (mapping.md §2); `'%02d'` is fixed-width 2 ⇒ the postcondition's `len(Result()) == 2`; the leading-zero supply for `v < 10` is the tens character `chr(48 + 0) == '0'`. |

The discriminating content of the change — a year below one hundred renders as
two characters **with a leading zero** (`year % 100` then `'%02d'`) rather than
the empty/short tail of the year's decimal string (`str(year)[2:]`) — lives in
the postcondition `len(Result()) == 2` together with the element-wise
`Result()[k] == {tens,units}_digit(year % 100)`. The pre-patch body computed
`str(year)[2:]`; `model_prepatch.py` reproduces that slice deeply (build the
1..4 decimal digits of the year, then drop the first two) and **fails** the
postcondition `len(Result()) == 2` for years below one hundred (the slice is
empty) — exactly the spec sensing the change (G-DIFF). The F2P
`test_year_before_1000` (years 476→`76`, 42→`42`, 4→`04`) is precisely this
discriminator: 42 and 4 fall in the sub-100 regime where the old slice is empty.

## No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — the two-digit decimal rendering of `year % 100` — is modelled
**deeply** (`tens_digit`/`units_digit` consumed in `abbreviated_year`, steps
3–4, an **A-reference**), not hidden behind an axiom about a library callee:
there is **no consumed axiom** (the rendering invokes no library function;
Python's `%`-formatting is the language operator, modelled deeply). The deep
model is validated == the real `'%02d' % (year%100)` by G-AX (A-reference).

## verify(model) ⇒ resolved

`abbreviated_year` verifies only if its output is exactly two decimal-digit
characters equal to the tens-then-units digit of `year % 100` (steps 2–5) —
including the leading zero for years below ten. By R (`int` year ↔
`self.data.year`, `str` ↔ `List[int]`) the verified renderer equals
`'%02d' % (self.data.year % 100)` on every admitted year; by G-AX the deep
model `tens_digit`/`units_digit` equals the real `'%02d'` formatting
(A-reference) over the full domain. Therefore a model satisfying this spec,
refined by the map above, is the gold patch up to type refinement — and the
gold patch resolves (G-RESOLVE). The trust points reduce to one: deep-model
fidelity (G-AX); there is no axiom and no refinement step beyond R/I.
