# refinement.md — astropy__astropy-14365

Operation-by-operation correspondence between `Solution.lean`'s two impl regions
(`lineType` and `maskFlags`, plus the deep models `classify`/`maskSeq` they
compute) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement), **A** (axiomatized callee — **A-consumed** where the proof uses the
axiom's `ensures`, **A-reference** where a deep model is validated == the real
callee by G-AX), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. Claim: any impl
verifying against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## Overview — two independently-fixed behaviors

The issue is "this table format assumes its commands are upper case". The gold
patch makes recognition case-insensitive in **two** independent places, both on
the F2P (`test_roundtrip[True]`) code path:

1. **Site 1 — line classification.** `_line_type` compiles its grammar regex
   without flags pre-patch and with `re.IGNORECASE` post-patch (`qdp.py:71`). A
   lower-case header line (e.g. `read serr 1 2`) was `reject`ed (raised
   `ValueError`), now classifies as `command`.
2. **Site 2 — masked-value recognition.** `_get_tables_from_qdp_file` tested
   `v == "NO"` pre-patch and `v.upper() == "NO"` post-patch (`qdp.py:309`). A
   lower-case `no` cell was parsed as a number (crash / wrong value), now becomes
   the masked sentinel.

One failing prepatch per site (`Solution_prepatch.lean` = site 1,
`Solution_prepatch_2.lean` = site 2); each diverges from the frozen spec exactly
at the discriminating clause (G-DIFF).

## A. Site 1 — `lineType` ⇔ `_line_type` (`astropy/io/ascii/qdp.py:71`)

Gold hunk:
```
- _line_type_re = re.compile(_type_re)
+ _line_type_re = re.compile(_type_re, re.IGNORECASE)
```

| # | Solution.lean impl op (`lineType`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `line : List Char` | `line: str` arg | R | `str` ↔ `List Char` (mapping.md §2); G-CONF bridges via `ch ↔ Char.ofNat (ord ch)`. |
| A2 | result `classify true line` : `LType` | the `_line_type_re.match` + `groupdict` dispatch, **compiled with `re.IGNORECASE`** | A-reference | the changed classification is modeled **deeply** by `classify`; `fold=true` IS the `re.IGNORECASE` compile flag. No consumed axiom. The equality `classify true == real(IGNORECASE)` is the A-reference G-AX validates over >10⁶ lines (mapping.md §3.1). |
| A3 | `LType` constructors ↔ the `str`/raise outcomes | `"comment"`/`"command"`/`"new"`/`f"data,{n}"`/`raise ValueError` | R | result-type bijection (mapping.md §2). `reject ↔ raise` is observationally "this line is not accepted", which the caller `_get_type_from_list_of_lines` turns into the same `ValueError`. |

Discriminating content: a lower-case directive line. `classify true` accepts it
(`command`); `classify false` (the pre-patch flag-less compile) `reject`s it.
`Solution_prepatch.lean` computes `classify false line` and **fails**
`out = classify true line` at exactly that clause (G-DIFF). `fold` flips only the
letter-literal comparisons (`eqFold`); digit/sign/whitespace classes and the
case-irrelevant `isDecimal` are untouched — matching `re.IGNORECASE`'s semantics.

## B. Site 2 — `maskFlags` ⇔ the value loop (`astropy/io/ascii/qdp.py:309`)

Gold hunk:
```
- if v == "NO":
+ if v.upper() == "NO":
      values.append(np.ma.masked)
```

| # | Solution.lean impl op (`maskFlags`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | parameter `tokens : List (List Char)` | `line.split(delimiter)` over cells `v: str` | R | each `v` (str) ↔ `List Char`; the row of cells ↔ `List (List Char)` (mapping.md §2). The split itself is `words` for the default delimiter; G-CONF bridges it. |
| B2 | result `maskSeq true tokens` : `List Bool`, computed by the backward `while` fold | the per-cell `v.upper() == "NO"` test selecting `np.ma.masked` vs a parsed number | A-reference + I | the changed masking decision is modeled **deeply** by `maskSeq`/`isMarkerTok`; `fold=true` IS `v.upper() == "NO"`. The fold ops (`isMarkerTok true t`, `::`, the loop) are **I** (concrete, transliterated by G-CONF); the equality of the deep model to the real predicate is the **A-reference** G-AX validates. mapping.md §3.2. |
| B3 | each `true` entry ↔ "cell is masked" | `values.append(np.ma.masked)` | R | a `true` flag ↔ the masked sentinel; a `false` flag ↔ the number-parsing branch. The downstream numeric parse (`int`/`float`) is **unchanged** by the patch, so the only patch-observable per-cell datum is this boolean (mapping.md §2). |

Discriminating content: a lower-case `no` cell. `maskSeq true` flags it `true`
(masked); `maskSeq false` (pre-patch `v == "NO"`) flags it `false` (would be
number-parsed). `Solution_prepatch_2.lean` uses `isMarkerTok false` in the loop
body and **fails** the `result = maskSeq true (tokens.drop i)` invariant at that
clause (G-DIFF).

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, A-reference, or I. The two operations that genuinely *changed* —
the regex `IGNORECASE` flag (site 1) and the `.upper()` masking test (site 2) —
are each modeled **deeply** (the spelled-out `classify`/`maskSeq` with the `fold`
parameter capturing exactly the changed flag), not hidden behind an axiom about a
function under change. There are **no consumed axioms** at all; the only A rows
are A-references (deep models validated == the real code by G-AX). The numeric
DFA (`isDecimal`) is likewise an A-reference (validated == `re.fullmatch(_decimal_re)`).

## D. verify(Solution) ⇒ resolved

`lineType` verifies only if its output equals `classify true line` (the
case-insensitive classification, A2); `maskFlags` verifies only if its output
equals `maskSeq true tokens` (the case-insensitive masking, B2). By R
(`str ↔ List Char`, the result-type bijections) the verified functions equal the
gold-patched `_line_type` (compiled with `re.IGNORECASE`) and the gold-patched
`v.upper() == "NO"` masking on the tested inputs; by G-AX the deep models
`classify`/`maskSeq`/`isDecimal` equal the real code (A-references, both flags);
by G-CONF the R/I transliteration agrees with `patch.diff`'s behaviour on ≥10⁵
inputs. Therefore a model satisfying this spec, refined by the map above, is the
gold patch up to type refinement — and the gold patch resolves (G-RESOLVE). The
only trust point is refinement/deep-model fidelity (this doc + G-AX + G-CONF);
there are no axiom-soundness liabilities because no axiom is consumed.
