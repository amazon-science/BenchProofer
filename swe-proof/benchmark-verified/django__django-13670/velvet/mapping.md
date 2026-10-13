# mapping.md — django__django-13670

Binds `Solution.lean` symbols to the repo at
`base_commit = c448e614c60cc97c6194c62052363f4f501e0953`.

Repo file under change:
`django/utils/dateformat.py` (method `DateFormat.y`).

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `twoDigitYear (year : Nat)` | the `def y(self)` method body at `django/utils/dateformat.py:324` | the modeled short-year rendering |
| `year` | `self.data.year` — the calendar year of the wrapped `date`/`datetime` | the full year |
| `out` (result) | the 2-character string returned by `y()` | the abbreviated 2-digit year |
| `twoDigitString (n : Nat)` | the pure renderer `'%02d' % n` for `n` already reduced mod 100 | width-2 zero-padded decimal |
| `digitChar (d : Nat)` | a single decimal digit's ASCII character (`chr(48 + d)`) | per-digit rendering |

`self.data.year` is read from the wrapped `datetime`/`date`; the stdlib bounds it
to `MINYEAR..MAXYEAR` = `1..9999`. The model takes `year : Nat` with
`require year ≤ 9999` — the exact upper bound of the real domain. This bound is
what makes the pre-patch slice skeleton (`str(year)[2:]`, modeled by a
decimal-width case split) faithful: the number of decimal characters of the full
year is determined by which of the bands `<100 / <1000 / ≤9999` it falls in, and
that case split is sound only because the year never exceeds four digits. No
callee is invoked by the patched expression beyond integer `%` and `%`-string
formatting, both modeled directly — so there is NO axiom and no `axiom_check.py`.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

| repo reality | Lean carrier | bijection |
|---|---|---|
| `self.data.year` : `int` in `1..9999` | `Nat` with `year ≤ 9999` | identity on the value; the `require` matches the real upper bound (`MAXYEAR = 9999`), and `Nat ⊇ {1..9999}` covers it |
| the returned `str` (always 2 chars) | `List Char` (`out`) | the Python `str` ↔ its list of characters; `out[0]` = tens char, `out[1]` = ones char |
| `'%02d' % m` (zero-padded width-2 decimal of `m`, `0 ≤ m < 100`) | `twoDigitString m` = `[digitChar (m/10%10), digitChar (m%10)]` | identical: both write the tens digit then the ones digit, with a leading '0' when `m < 10`; `digitChar d ↔ chr(48 + d%10)` |
| `self.data.year % 100` | `year % 100` | identical: integer remainder mod 100 (`Nat.mod`) |
| `'%02d'` left-fill with '0' to width 2 | the fixed two-element list `[tens, ones]` | identical: when `m < 10` the tens digit `m/10%10 = 0`, rendering '0' in slot 0 — the zero-pad IS the fixed-width list |

## 3. Callee provenance

The patched expression `'%02d' % (self.data.year % 100)` calls no repo callee:
it is integer remainder plus `%`-string formatting, both Python primitives
modeled in full by `twoDigitString` / `digitChar` (tagged **I** in
refinement.md). There is therefore no `axiom` and no `axiom_check.py` for this
bundle.

## 4. G-CONF fuzz seed

`conformance_check.py` seeds with **13670**. The R/I shadow is the modeled
formula `two_digit_string(year % 100)` (the Python bridge of
`twoDigitString (year % 100)`); the oracle is the patched source expression
transliterated verbatim (`'%02d' % (year % 100)`). SHADOW vs ORACLE are
differential-tested EXHAUSTIVELY over every year `0..9999` (the full
`require`/stdlib-constructible range) plus the issue/F2P boundary years and a
fuzz pass; exit 0 iff zero disagreements.
