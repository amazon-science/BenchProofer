# refinement.md — django__django-14373

Correspondence between `Solution.lean`'s `fourDigitYear` impl and `patch.diff`
(the gold patch renders the full year as a four-digit decimal, zero-padded to
width 4). `patch.diff` is the gold verbatim (applies at base_commit, resolves
— G-RESOLVE).

## A. The corrected rendering — `DateFormat.Y`

Gold hunk:
```
     def Y(self):
-        "Year, 4 digits; e.g. '1999'"
-        return self.data.year
+        """Year, 4 digits with leading zeros; e.g. '1999'."""
+        return '%04d' % self.data.year
```

| # | Solution.lean impl op (`fourDigitYear`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `year : Nat`, `require year ≤ 9999` | `self.data.year` (`int` in `1..9999`) | R | `int` ↔ `Nat`; the `require` matches the real upper bound `MAXYEAR = 9999`, so the modeled domain coincides with the reachable one. mapping.md §2. |
| A2 | `return [digitChar (year/1000%10), digitChar (year/100%10), digitChar (year/10%10), digitChar (year%10)]` | `'%04d' % self.data.year` | I | identical: `'%04d'` writes a width-4 zero-padded decimal = thousands, hundreds, tens, ones digit, most significant first, with leading '0's when `year < 1000`. `digitChar d ↔ chr(48 + d%10)`. mapping.md §2. |

The `return` expression equals `fourDigitString year` by definition (the
`ensures`), so A2 is the modeled-deeply rendering. No A (axiom) steps; no kind-3
(changed inexpressible) steps. The full fix — render the year as a fixed-width
four-character zero-padded decimal — is modeled deeply and tagged **I**.

## B. verify(Solution) ⇒ resolved

`fourDigitYear` verifies only if `out = fourDigitString year` (A2). By R
(mapping.md §2) the verified `List Char` is exactly the character sequence of the
patched `'%04d' % self.data.year` on the real year. The F2P test
`test_Y_format_year_before_1000` asserts `Y` renders `datetime(1,…) -> '0001'`
and `datetime(999,…) -> '0999'` — i.e. the year written as four characters with
the high-order slots zero-filled, exactly what the spec pins
(`1 ⇒ ['0','0','0','1']`, `999 ⇒ ['0','9','9','9']`).

The prepatch impl reproduces the **bare-int / missing-zero-pad** bug:
`return self.data.year` emits the year as its plain decimal value (Django's
`Formatter.format` later `str()`s it), so a year below one thousand keeps only as
many characters as its magnitude needs — no left-fill (e.g. year 1 → `'1'`,
year 999 → `'999'`, instead of `'0001'`/`'0999'`). The prepatch skeleton renders
a variable-width decimal (1, 2, or 3 chars for `year < 1000`) against the
byte-identical spec, leaving the unsolved goal
`(if year<10 then [_] else …) = fourDigitString year`, which fails on every
`year < 1000` case (G-DIFF). The prepatch fails precisely on the discriminating
clause: a year below one thousand (the F2P `1 -> '0001'`, `999 -> '0999'`).

G-CONF differential-tests the R/I shadow (the modeled formula) against the
patched source expression EXHAUSTIVELY over every year `0..9999` plus fuzz (seed
14373). No trust points beyond the type bijection (mapping.md §2): there are no
axioms.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The one operation that genuinely *changed* — rendering the
year as a fixed-width four-character zero-padded decimal instead of a bare
integer — is modeled **deeply** (the spelled-out `fourDigitString`, step A2,
tagged **I**), not hidden behind an axiom. There are no consumed axioms.
