# mapping.md — django__django-14373

Binds `Solution.lean` symbols to the repo at
`base_commit = b1a4b1f0bdf05adbd3dc4dde14228e68da54c1a3`.

Repo file under change:
`django/utils/dateformat.py` (method `DateFormat.Y`).

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `fourDigitYear (year : Nat)` | the `def Y(self)` method body at `django/utils/dateformat.py:315` | the modeled full-year rendering |
| `year` | `self.data.year` — the calendar year of the wrapped `date`/`datetime` | the full year |
| `out` (result) | the 4-character string the patched `Y()` returns | the zero-padded 4-digit year |
| `fourDigitString (n : Nat)` | the pure renderer `'%04d' % n` for `0 ≤ n ≤ 9999` | width-4 zero-padded decimal |
| `digitChar (d : Nat)` | a single decimal digit's ASCII character (`chr(48 + d)`) | per-digit rendering |

`self.data.year` is read from the wrapped `datetime`/`date`; the stdlib bounds it
to `MINYEAR..MAXYEAR` = `1..9999`. The model takes `year : Nat` with
`require year ≤ 9999` — the exact upper bound of the real domain, which makes the
`'%04d'` ↔ fixed-width-4 list correspondence exact (for `year > 9999`, `'%04d'`
would emit more than four characters; the real `Y()` is never reached there).
No callee is invoked by the patched expression beyond integer `/`, `%` and
`%`-string formatting, all modeled directly — so there is NO axiom and no
`axiom_check.py`.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

| repo reality | Lean carrier | bijection |
|---|---|---|
| `self.data.year` : `int` in `1..9999` | `Nat` with `year ≤ 9999` | identity on the value; the `require` matches the real upper bound (`MAXYEAR = 9999`), and `Nat ⊇ {1..9999}` covers it |
| the returned `str` (always 4 chars) | `List Char` (`out`) | the Python `str` ↔ its list of characters; `out[0..3]` = thousands, hundreds, tens, ones chars |
| `'%04d' % m` (zero-padded width-4 decimal of `m`, `0 ≤ m ≤ 9999`) | `fourDigitString m` = `[digitChar (m/1000%10), digitChar (m/100%10), digitChar (m/10%10), digitChar (m%10)]` | identical: both write the four most-significant-first decimal digits, with leading '0's when `m < 1000`; `digitChar d ↔ chr(48 + d%10)` |
| `'%04d'` left-fill with '0' to width 4 | the fixed four-element list `[k3, k2, k1, k0]` | identical: when `m < 1000` the high digit `m/1000%10 = 0`, rendering '0' in slot 0 — the zero-pad IS the fixed-width list |

## 3. Callee provenance

The patched expression `'%04d' % self.data.year` calls no repo callee: it is
`%`-string formatting of an integer, a Python primitive modeled in full by
`fourDigitString` / `digitChar` (tagged **I** in refinement.md). There is
therefore no `axiom` and no `axiom_check.py` for this bundle.

## 4. G-CONF fuzz seed

`conformance_check.py` seeds with **14373**. The R/I shadow is the modeled
formula `four_digit_string(year)` (the Python bridge of
`fourDigitString year`); the oracle is the patched source expression
transliterated verbatim (`'%04d' % year`). SHADOW vs ORACLE are differential-
tested EXHAUSTIVELY over every year `0..9999` (the full `require`/stdlib domain)
plus the issue/F2P boundary years and a fuzz pass; exit 0 iff zero
disagreements.
