# mapping.md — django__django-14373

Binds every `model.py` symbol to its repository counterpart at
`base_commit = b1a4b1f0bdf05adbd3dc4dde14228e68da54c1a3`, states the type
abstraction, and gives the provenance of the deep-model reference (the real
operation the deep model is validated against by G-AX).

Repo file under change: `django/utils/dateformat.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `render_year(year)` | `DateFormat.Y(self)` — `django/utils/dateformat.py:315` (body line 317) | the modeled changed function (the `Y` format-specifier handler) |
| `four_field(year)` *(deep model — A-reference)* | the rendering `'%04d' % self.data.year` (the patched body, `dateformat.py:317` post-patch) | pure spec: the fixed-width zero-padded decimal field; deep model of the changed rendering, validated `four_field == '%04d' % year` by axiom_check.py (G-AX), NOT consumed as an axiom |
| `thousands/hundreds/tens/units(year)` | the per-place decimal digits of the `%04d` field | pure spec: place-value digits of the year |
| `digit(d)` | the ASCII decimal digit for a value 0..9 | pure spec: digit value → code point (48 + d) |

The pre-patch repo behaviour the change replaces (for the refinement audit, not
referenced from the consumer spec view): `Y` returned the bare integer
`self.data.year` (`dateformat.py:317`), whose string rendering drops
most-significant leading zeros, so a year below 1000 produced fewer than four
characters.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| the `Y` return value (a `str` of decimal digits, post-patch) | `List[int]` of ASCII code points | `result[k]` ↔ `ord(s[k])`; `len(result)` ↔ `len(s)`; an ASCII decimal digit `'0'..'9'` ↔ `48..57` |
| `self.data.year` (an `int`, `datetime.year`) | `int` parameter `year`, constrained `1 <= year <= 9999` | identity; the constraint is the CPython `datetime` year domain (`datetime.MINYEAR == 1`, `datetime.MAXYEAR == 9999`), so `%04d` is exactly four digits |
| `str` value inside a specification | `PSeq[int]` (pure Viper sequence) | `ToSeq(list)` materializes the list as a `PSeq`; `PSeq` `+`/`take`/`drop`/`len`/`[i]` mirror `str` `+`/slice/`len`/index |

`str` indexing/iteration is banned in Nagini, so the carrier is `List[int]`;
the specification is phrased over `PSeq[int]` via `ToSeq`. The pre-patch return
of a bare `int` is observably the integer's minimal-width decimal string (Django
renders the `Y` result into the output via string concatenation in
`DateFormat.format`); the prepatch skeleton models exactly that minimal-width
rendering.

## 3. Deep-model provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `four_field` deep model ↔ `'%04d' % year` (A-reference)
**Operation:** Python's `str.__mod__` with the `'%04d'` conversion. The changed
rendering is modelled **deeply** by the `@Pure` place-value decomposition
`four_field` (with `thousands/hundreds/tens/units/digit`) in the `pure` region;
there is **no consumed axiom**. `'%04d' % n` formats `n` in base ten and
left-pads with the zero character to a minimum field width of four. For
`0 <= n <= 9999` the field is **exactly** four characters: the thousands,
hundreds, tens and units decimal digits, most significant first, with leading
zeros retained for values below 1000. This is precisely

  `[ '0'+thousands, '0'+hundreds, '0'+tens, '0'+units ]`  (ASCII code points),

which is what `four_field` / `digit` encode. The patch sets
`Y` to `'%04d' % self.data.year`, and `self.data.year` lies in
`[datetime.MINYEAR=1, datetime.MAXYEAR=9999]`, so the field is always four
digits — exactly the deep model's `len == 4` and place-value reconstruction.
Python `printf`-style formatting docs:
https://docs.python.org/3/library/stdtypes.html#printf-style-string-formatting
(the `0` flag = zero-padding; the `4` = minimum field width).

**Soundness check (G-AX):** `axiom_check.py` runs the real `'%04d' % year`
over the explicit F2P boundary witnesses (`1 -> '0001'`, `999 -> '0999'`, plus
`4/42/476` from the sibling `y` test and `1000/1999/9999/10/100`) and over an
**exhaustive** sweep of the full supported range `1..9999`, asserting
code-point equality with the deep model `four_field` every time. Exit 0 iff
sound. It imports nothing repo-specific — `'%04d' % n` is a Python built-in,
the very operation the gold patch performs.
