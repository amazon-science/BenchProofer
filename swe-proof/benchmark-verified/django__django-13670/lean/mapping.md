# mapping.md — symbol binding & type bijection (django__django-13670)

## Modeled function
- **Lean** `implementation_twoDigitYear : Nat → List Char`
- **Python** `DateFormat.y(self)` — `django/utils/dateformat.py:328-330 @ c448e614`
  (post-patch: `return '%02d' % (self.data.year % 100)`).

The function under spec is the `y` format-character handler. It receives the
year via `self.data.year` (a `datetime`'s year, an `int` in `1..9999`) and
returns the two-digit short form. The patch replaces the buggy
`str(self.data.year)[2:]` (string-slice the last two characters of the decimal
rendering) with `'%02d' % (self.data.year % 100)` (reduce modulo 100, then
format as two zero-padded decimal digits). The observable behaviour change the
F2P test demands is for years below 1000: e.g. `476 → '76'`, `42 → '42'`,
`4 → '04'`, where the old code produced `'6'`, `''`, `''` respectively.

## Type bijection (used by G-CONF + G-AX)
| Python | Lean | notes |
|---|---|---|
| `self.data.year` : `int` (≥ 0; really `1..9999`) | `Nat` | non-negative whole number; the year |
| output `str` (two chars) | `List Char` | the rendered digit sequence; modeled as a bare char list |
| `'%02d' % n` | `twoDigitYear` (deep model) | two zero-padded decimal digits of `n` (here `n = year % 100 < 100`, so exactly two digits) |
| `self.data.year % 100` | `year % 100` | integer reduction modulo 100 |
| digit `d` → its character | `digitChar d = Char.ofNat (48 + d)` | ASCII `'0'..'9'` |

`self`/`self.data` are framing wrappers carrying the year; only `year` is
observed. The input year is always `≥ 0` (a real `datetime` year is `1..9999`),
so `Nat` is the faithful carrier and the precondition is vacuous over `Nat`.

## Callee provenance
- The two-digit rendering (`'%02d' % (year % 100)`) is the changed operation
  itself; it is modeled DEEPLY as `digitChar` / `twoDigitYear` (pure arithmetic
  + ASCII digit emission), NOT axiomatized. It calls no UNCHANGED repo callee:
  `%` (modulo) and the `%02d` string formatting are language primitives.
- No UNCHANGED callee is consumed as an axiom; the axioms region is empty. There
  is no A-reference (no external callee underlies the deep model — it is closed
  arithmetic).

## Flag dependency
None. `y` takes no flags; behaviour depends only on `self.data.year`.

## G-CONF fuzz seed
Pinned seed: **13670**. ≥10^5 fuzzed inputs over years sampled to oversample the
below-1000 range (where the fix is observable) plus the full `1..9999` range and
boundary values (0, 1, 4, 9, 10, 42, 99, 100, 476, 999, 1000, 1999, 2000, 9999).
