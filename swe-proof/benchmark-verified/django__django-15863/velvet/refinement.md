# refinement.md — django__django-15863

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `floatFormat` `do` block and the pure `renderFixed` model) and `patch.diff`
(the gold patch). Each step is tagged **R** (type refinement), **A** (axiomatized
callee — **A-consumed** / **A-reference**), or **I** (identical concrete op).

This bundle is **axiom-free**: there are no A rows. The R/I legs are mechanically
refuted by **G-CONF** (`conformance_check.py`, §4.1); the narrative is audited by
G-EQ / G-PANEL. Claim: any impl verifying against this frozen spec, refined per
the map below, is behaviourally equal to the gold patch on the tested inputs
(within the modeled regime), so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## The change site — `floatformat()` (`django/template/defaultfilters.py:152`)

Gold hunk:
```
-        input_val = repr(text)
+        input_val = str(text)
         d = Decimal(input_val)
```

The single edit changes how the incoming `text` is converted to the string that
seeds `Decimal(input_val)`. For a `Decimal` argument, `repr(Decimal(x))` is
`"Decimal('x')"` → `InvalidOperation` → the `except` arm reconstructs through
`Decimal(str(float(text)))`, **routing the value through a binary float and
truncating every fractional digit past float's ~17 significant figures**. With
`str(text)`, `Decimal(str(Decimal(x)))` reproduces the numeral exactly, so the
low-order fractional digits survive. (For a value that already prints the same
under `repr` and `str`, e.g. an ordinary `str`/`int`, the two are observationally
identical — the bug bites only high-precision `Decimal`s, which is what the F2P
case `floatformat(Decimal("123456.123456789012345678901"), 21)` exercises.)

Everything downstream of `d` (the `quantize(exp, ROUND_HALF_UP, Context(prec))`,
the `as_tuple()` digit reversal, the zero-pad `while`, the `.` insertion, and
`number_format` under the default locale with no grouping) is, in the modeled
regime (mapping.md §2 — `p ≥` the numeral's fractional length, so nothing is
rounded off, default locale), the **identity** rendering: integer digits, a
`.`, the fractional digits, then trailing zeros out to width `p`. That is
`renderFixed`, and the gold's `while len(digits) <= abs(exponent): digits.append("0")`
is exactly the backward pad loop in `floatFormat`.

| # | Solution.lean impl op (`floatFormat`) | patch.diff / repo op | tag | justification |
|---|---|---|---|---|
| 1 | params `intDigits`, `fracDigits : List Char` | the digit runs of `d.as_tuple()` derived from `Decimal(str(text))` | R | a non-negative decimal numeral ↔ its integer/fractional digit runs (mapping.md §2). The bijection is the split at the `.`; G-CONF bridges via `str` ↔ digit chars. The *fix* is precisely that these are the numeral's **own** digits (str path), not float-round-trip artefacts (repr path). |
| 2 | `p : Nat` | `p = int(arg)` | R | the precision argument; modeled regime requires `p ≥ 1` and `p ≥ |fracDigits|` (mapping.md §2). |
| 3 | `digits := fracDigits`; pad `while k>0 do digits := digits ++ ['0']` for `k = p - |frac|` steps | `digits = [str(d) … reversed]`; `while len(digits) <= abs(exponent): digits.append("0")` | I | the zero-pad to the requested width; concrete `List` append loop transliterated by G-CONF. In the regime no rounding occurs, so the post-`quantize` digit run is the numeral's fractional run and the pad count is `p - |frac|`. |
| 4 | `return intDigits ++ ['.'] ++ digits` | `digits.insert(-exponent, "."); number = "".join(reversed(digits))`; then `number_format(number, abs(p), use_l10n, force_grouping)` | I + R | placing the decimal point and concatenating; `number_format` under the default locale with `force_grouping=False` is the identity on this character content (mapping.md §2). |

The discriminating content of the change — that the rendered fractional run is
the numeral's **verbatim** digits `fracDigits` (not values lost to a float
round-trip) — lives in the postcondition `out = renderFixed intDigits fracDigits p`
(which names `fracDigits` explicitly). `Solution_prepatch.lean` reproduces the
buggy regime (the fractional content collapsed to trailing zeros, the artefact
of the float round-trip dropping low-order digits) and **fails** that clause
(G-DIFF): its output is `intDigits ++ ['.'] ++ replicate p '0'`, which differs
from `renderFixed` whenever `fracDigits` carries a non-zero or simply different
digit.

## No kind-3 (inexpressible-changed-op) steps

Every step is R or I; there are no A rows. The operation that genuinely changed —
how the numeral is parsed into exact digits vs a float-truncated approximation —
is modeled **directly** as the identity of the fractional run with the numeral's
own digits (`renderFixed` reproduces `fracDigits` verbatim), not hidden behind an
axiom. No callee is axiomatized: `Decimal`, `quantize`, `number_format` are all
collapsed to identity within the proven regime and that collapse is mechanically
checked end-to-end by G-CONF against the real patched `floatformat`.

## verify(Solution) ⇒ resolved

`floatFormat` verifies only if its output equals `renderFixed intDigits
fracDigits p` — the integer run, a point, the numeral's fractional digits in
order, and trailing zeros to width `p`. By R (numeral ↔ digit runs; `number_format`/
default-locale identity) and I (the pad loop), the verified renderer equals the
patched `floatformat` on the modeled regime — exactly the regime the FAIL_TO_PASS
case occupies. G-CONF confirms the R/I transliteration agrees with `patch.diff`'s
behaviour on ≥10⁵ regime inputs (0 disagreements). Therefore a model satisfying
this spec, refined by the map above, is the gold patch up to type refinement, and
the gold patch resolves (G-RESOLVE). The sole trust point is refinement fidelity
(this doc + G-CONF); there is no axiom-soundness trust point (no axioms).
