# refinement.md — django__django-14373

The operation-by-operation correspondence between `model.py`'s implementation
(the `render_year` impl region and the deep `four_field` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — split into **A-consumed**, where the proof uses an
axiom's `Ensures`, and **A-reference**, where a deep model is validated == the
real callee/operation by axiom_check.py / G-AX), or **I** (identical concrete
operation). The claim: *any implementation that verifies against this frozen
spec, refined per the map below, is behaviourally equal to the gold patch on
the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The single change site — `DateFormat.Y()` (`django/utils/dateformat.py:315`)

Gold hunk:
```
 def Y(self):
-    "Year, 4 digits; e.g. '1999'"
-    return self.data.year
+    """Year, 4 digits with leading zeros; e.g. '1999'."""
+    return '%04d' % self.data.year
```

| # | model.py impl op (`render_year`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `year: int`, `1 <= year <= 9999` | `self.data.year` (a `datetime.year`) | R | `int` ↔ `int`; the bound is the CPython `datetime` year domain `[MINYEAR=1, MAXYEAR=9999]` (mapping.md §2). |
| A2 | the result is `four_field(year)`, i.e. `[ '0'+thousands, '0'+hundreds, '0'+tens, '0'+units ]`, computed by the four `digit(place(year))` appends | `'%04d' % self.data.year` | A-reference | the changed rendering is modelled **deeply**: `four_field` (the spelled-out place-value decomposition in the `pure` region) and the four appends in `render_year` ARE the zero-padded four-digit field. There is no consumed axiom. The deep model is validated **== the real operation** out-of-band: G-AX (axiom_check.py) runs `'%04d' % year` over the full `1..9999` range and asserts equality (mapping.md §3.1). For `0 <= year <= 9999` the `'%04d'` field is exactly the four place-value digits, MS first, leading zeros retained — the same function the model loop computes. |
| A3 | `result` returned (a `List[int]` of code points) | the `str` returned by `Y`, later concatenated into the formatted output by `DateFormat.format` | R | `str` ↔ `List[int]` of ASCII code points (mapping.md §2); `DateFormat.format` concatenates the `Y` result into the output string, and the F2P test compares the rendered characters, which the carrier refinement preserves. |

The discriminating content of the change — a year **below 1000** must render
with its leading zeros (`1 -> '0001'`, `999 -> '0999'`) rather than as its bare
significant digits — lives in `four_field`'s **fixed length 4** and the
**leading-position** clause `Result()[0] == 48 + year // 1000` (model) ⇔ the
`0`/`4` flags of `'%04d'` (real). The pre-patch `Y` returned the bare integer
`self.data.year`, whose decimal rendering drops leading zeros;
`model_prepatch.py` reproduces that (the leading-zero-stripping skeleton) and
**fails** the postcondition `ToSeq(Result()) == four_field(year)` (and the
`len == 4` clause), which is exactly the spec sensing the change (G-DIFF).

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — the zero-padded fixed-width decimal rendering — is modelled
**deeply** (the spelled-out place-value decomposition `four_field` consumed in
`render_year`, step A2, an **A-reference**), not hidden behind an axiom about
the function under change: there is **no consumed axiom** in this bundle. The
changed rendering `'%04d' % year` appears only as the **A-reference** that G-AX
validates the deep model against.

## C. verify(model) ⇒ resolved

`render_year` verifies only if its output is the exact four-character
place-value field with leading zeros retained — `len == 4`, every character an
ASCII digit, the four digits reconstructing `year`, and the leading position
equal to `48 + year // 1000` (A2). By R (`int` ↔ `int`, `str` ↔ `List[int]`,
the `DateFormat.format` concatenation) the verified renderer equals
`'%04d' % self.data.year` on the supported years; by G-AX the deep model
`four_field` equals the real `'%04d'` rendering over the entire `1..9999`
domain (A-reference). Therefore a model satisfying this spec, refined by the
map above, is the gold patch up to type refinement and the audited
deep-model reference — and the gold patch resolves (G-RESOLVE). The trust
points are exactly the two of PLAN §1.1: reference soundness (G-AX, here the
A-reference deep-model equality) and refinement fidelity (this document, G-EQ).
