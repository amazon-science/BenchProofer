# refinement.md — django__django-13670

Correspondence between `Solution.lean`'s `twoDigitYear` impl and `patch.diff`
(the gold patch renders the abbreviated year as the last two digits, zero-padded
to width 2). `patch.diff` is the gold verbatim (applies at base_commit, resolves
— G-RESOLVE).

## A. The corrected rendering — `DateFormat.y`

Gold hunk:
```
     def y(self):
-        "Year, 2 digits; e.g. '99'"
-        return str(self.data.year)[2:]
+        """Year, 2 digits with leading zeros; e.g. '99'."""
+        return '%02d' % (self.data.year % 100)
```

| # | Solution.lean impl op (`twoDigitYear`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `year : Nat`, `require year ≤ 9999` | `self.data.year` (`int` in `1..9999`) | R | `int` ↔ `Nat`; the `require` matches the real upper bound `MAXYEAR = 9999`, so the modeled domain coincides with the reachable one. mapping.md §2. |
| A2 | `let n := year % 100` | `self.data.year % 100` | I | identical: integer remainder mod 100. `Nat.mod` ↔ Python `%`. The arithmetic heart of the fix. |
| A3 | `return [digitChar (n / 10 % 10), digitChar (n % 10)]` | `'%02d' % (…)` | I | identical: `'%02d'` writes a width-2 zero-padded decimal = tens digit then ones digit, leading '0' when `n < 10`. `digitChar d ↔ chr(48 + d%10)`. mapping.md §2. |

The `return` expression equals `twoDigitString (year % 100)` by definition (the
`ensures`), so A2+A3 together are the modeled-deeply rendering. No A (axiom)
steps; no kind-3 (changed inexpressible) steps. The full fix — reduce mod 100
AND zero-pad to two characters — is modeled deeply and tagged **I**.

## B. verify(Solution) ⇒ resolved

`twoDigitYear` verifies only if `out = twoDigitString (year % 100)` (A2–A3). By R
(mapping.md §2) the verified `List Char` is exactly the character sequence of the
patched `'%02d' % (self.data.year % 100)` on the real year. The F2P test
`test_year_before_1000` asserts `y` renders `476 -> '76'`, `42 -> '42'`,
`4 -> '04'` — i.e. the sub-hundred part reduced mod 100 and zero-padded to two
characters, exactly what the spec pins (`4 % 100 = 4`, tens digit `0`, ones
digit `4` ⇒ `['0','4']`).

The prepatch impl reproduces the real **string-slice** bug verbatim:
`str(self.data.year)[2:]` prints the WHOLE year in decimal and discards its first
two characters, instead of reducing mod 100 and zero-padding. So the result
inherits the decimal width of the full year: a year `< 100` prints ≤ 2 chars and
loses everything (`''`); a three-digit year keeps only its last char; only a
four-digit year keeps two. The prepatch skeleton models this by a decimal-width
case split — `[]` when `year < 100`, `[digitChar (year%10)]` when `year < 1000`,
`[digitChar (year/10%10), digitChar (year%10)]` otherwise — against the
byte-identical spec, leaving the unsolved goal
`(if year<100 then [] else if year<1000 then [_] else [_,_]) =
twoDigitString (year % 100)`, which fails on every year whose decimal width is
not four (G-DIFF). The prepatch fails precisely on the discriminating clause: all
three F2P inputs (`4 -> '' ≠ '04'`, `42 -> '' ≠ '42'`, `476 -> '6' ≠ '76'`), i.e.
every year below one thousand. (Verified: the spec equals `'%02d' % (year % 100)`
and the slice skeleton differs from it on the whole `year < 1000` band, where the
bug lives, and on `100 ≤ year < 1000` even beyond the leading-zero subcase —
exactly the years the issue reports.)

G-CONF differential-tests the R/I shadow (the modeled formula) against the
patched source expression EXHAUSTIVELY over every year `0..9999` plus fuzz (seed
13670). No trust points beyond the type bijection (mapping.md §2): there are no
axioms.
