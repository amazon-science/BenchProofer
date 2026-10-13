# refinement.md — astropy__astropy-14365

The operation-by-operation correspondence between `model.py`'s implementation
(the THREE contracted functions `command_line`, `masked_field`,
`reserved_data_token`, plus the deep case-fold models `up`/`upseq` and the
recognition predicates) and `patch.diff` (the gold patch, two hunks). Each step
is tagged **R** (type refinement), **A-consumed** (proof uses an axiom's
`Ensures`), **A-reference** (a deep model validated `==` the real callee by
axiom_check.py / G-AX, NOT consumed as an axiom), or **I** (identical concrete
operation). The claim: *any implementation that verifies against this frozen
spec, refined per the map below, is behaviourally equal to the gold patch on the
tested inputs, so it resolves.*

**Hunk 1 is a single edit to a SHARED construct** — adding `re.IGNORECASE` to
the one compiled regex used by `_line_type`'s classifier — and that single flag
changes the verdict on **three** alternation branches of that regex:
`command`, `new`, and `data`. All three must be modelled or A-reference
validated; modelling only the `command` branch (the one the problem statement
names) is insufficient, because the actual F2P input depends on the `data`
branch too (see §A0).

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

There are **no consumed `@ContractOnly` axioms** (the `axioms` region is empty);
the changed operation in both hunks IS the case fold (ASCII `a`..`z` up, plus
the long-s ſ (383) → `S` (83), the one non-ASCII code point Python's
case-insensitive matching identifies with a keyword letter), modelled deeply and
validated as an A-reference.

## A0. All behavioural effects of the hunk-1 `re.IGNORECASE` edit

Gold hunk 1:
```
- _line_type_re = re.compile(_type_re)
+ _line_type_re = re.compile(_type_re, re.IGNORECASE)
```

`_type_re` is an alternation `command | new | data | comment`. The single flag
makes every literal letter in the pattern match case-insensitively, changing the
verdict on the three letter-bearing branches:

| branch | regex (pre-patch literals) | effect of `re.IGNORECASE` | F2P-relevant? | modelled by |
|---|---|---|---|---|
| `command` | `READ [TS]ERR(\s+[0-9]+)+` | keyword words `READ`,`SERR`/`TERR` now match in any case | yes — `read terr 1`, `read serr 2` in the lower-cased F2P file | `command_line` (§A) |
| `data` | `(_decimal_re\|NO\|[-+]?nan)(sep …)*` | the reserved-word tokens `NO` and `nan` now match in any case (decimals are already case-irrelevant except `[eE]`, which the flag does not affect) | **yes** — the F2P data line `no … no` (lower-case `no` fields) | `reserved_data_token` (§C) |
| `new` | `NO(sep NO)+` | the `NO` tokens now match in any case | yes — a lower-case `no no …` row | per-token `is_masked_field` / `reserved_data_token` (§C) |

**F2P dependency (verified in the pinned container, both patch states):** after
`lowercase_header`, the real `example_qdp` contains the data line
`no 1.14467592592593e-05 … 0.000000 no`. Under the PRE-patch (case-sensitive)
regex this line is classified as `None` → `ValueError: Unrecognized QDP line` at
the line-classification stage — *before* `_get_tables_from_qdp_file` ever reaches
the masking loop. So `test_roundtrip[True]` cannot pass on the strength of the
`command` + masking deciders alone: it ALSO requires the `data`-branch (and, for
general QDP, `new`-branch) case-insensitive token recognition of the SAME edit.
All three branch effects are therefore modelled below; none is laundered as
"unchanged surrounding machinery."

## A. Command site — `_line_type` (`astropy/io/ascii/qdp.py:71`)

The behavioural effect of `re.IGNORECASE` on the `command` branch (regex
`READ [TS]ERR(\s+[0-9]+)+`) is that its keyword letters now match
case-insensitively; the whitespace runs and the `[0-9]+` column numbers are
case-irrelevant and unchanged.

| # | model.py impl op (`command_line`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | params `tok0, tok1: List[int]`, `ncols: int` | the two leading whitespace-separated words and the count of trailing column numbers of `line`, tokenized by the regex | R | `str` ↔ `List[int]` code points; the regex's whitespace/number tokenizing is the unchanged machinery surrounding the changed flag (mapping.md §2). |
| A2 | the case fold of `tok0`/`tok1` via the verified loops, i.e. `upseq(ToSeq(tok0))` / `upseq(ToSeq(tok1))` | the letter-case-insensitive matching the `re.IGNORECASE` flag gives the keyword sub-patterns `READ`, `[TS]ERR` | A-reference | the changed operation (case-insensitive keyword matching) is modelled **deeply** as the per-code-point upper fold (ASCII `a`..`z` up; ſ (383) → `S` (83), matching `re.IGNORECASE`'s identification of the long-s with `S`/`s`); there is no consumed axiom. G-AX (axiom_check.py) validates the deep recognition `is_command_tokens` `==` the REAL patched `_line_type` command verdict on every keyword-case combination + fuzz (mapping.md §3.3). |
| A3 | `upseq(tok0) == kw_READ()` and (`upseq(tok1) == kw_SERR()` or `== kw_TERR()`) and `ncols >= 1` | the regex requiring the first word be `READ`, the second `SERR`/`TERR`, and `(\s+[0-9]+)+` at least one column number | I (under R) | identical literal token structure: `READ`/`SERR`/`TERR` literals and "≥1 column" are the same concrete conditions, lifted to the folded code-point sequences. |
| A4 | returns a `bool` | the `_line_type` classifier returns `"command"` (else this branch does not fire) | R | the model's boolean ↔ the classifier's `"command"`/not-`"command"` verdict (the only distinction this site's change observes). |

Pre-patch (`re.compile(_type_re)`, no flag) makes a lower-case `read serr 1 2`
fail to match → `ValueError`. `model_prepatch_2.py` reproduces that by deciding
the command with the RAW (case-sensitive) words and **fails** the postcondition
`Result() == is_command_tokens(ToSeq(tok0), ToSeq(tok1), ncols)` — exactly the
spec sensing the change (G-DIFF).

## B. Missing-value site — `_get_tables_from_qdp_file` (`qdp.py:309`)

Gold hunk 2:
```
- if v == "NO":
+ if v.upper() == "NO":
```

| # | model.py impl op (`masked_field`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | param `field: List[int]` | the per-row field `v` from `line.split(delimiter)` | R | `str` ↔ `List[int]` code points; the splitting is unchanged, case-irrelevant machinery (mapping.md §2). |
| B2 | the case fold via the verified loop, `upseq(ToSeq(field))` | `v.upper()` | A-reference | the changed operation IS the case fold, modelled deeply as the upper fold (ASCII `a`..`z` up; ſ (383) → `S` (83), agreeing with `str.upper` on the long-s); no consumed axiom. G-AX validates `upseq == str.upper` and `is_masked_field == (v.upper() == "NO")` over boundary + 20 000 fuzz (mapping.md §3.1, §3.2). |
| B3 | `upseq(field) == kw_NO()` | `... == "NO"` | I (under R) | identical literal comparison to the reserved word `NO`, lifted to the folded code-point sequence. |
| B4 | returns a `bool` (the masked decision) | the `if` deciding `values.append(np.ma.masked)` vs the numeric parse | R | the model's boolean ↔ the branch taken; the downstream `np.ma.masked` append / numeric parse is unchanged and case-irrelevant. |

Pre-patch (`v == "NO"`) makes a lower-case `no` field NOT masked (it falls into
the numeric parse and raises / mis-types). `model_prepatch.py` reproduces that by
deciding maskedness with the RAW (case-sensitive) field and **fails** the
postcondition `Result() == is_masked_field(ToSeq(field))` (G-DIFF).

## C. Data/new line-classification site — `_line_type` (`qdp.py:71`, same edit)

The SAME `re.IGNORECASE` edit (hunk 1) also governs the `data` and `new`
branches: a reserved-word data token — the missing-value word `NO` or the
not-a-number word `nan` (optionally signed) — must now be recognised
case-insensitively, so a row containing a lower-case `no` field is classified as
`data` instead of raising `ValueError`. This is the F2P-load-bearing effect of
A0's `data` row. `reserved_data_token` models this token-recognition decision.

| # | model.py impl op (`reserved_data_token`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| C1 | param `field: List[int]` | a single whitespace-split field of a candidate data/new line, tokenized by the regex's `sep` | R | `str` ↔ `List[int]` code points; the field-splitting (whitespace runs / the `(sep …)*` repetition) is unchanged, case-irrelevant machinery (mapping.md §2). |
| C2 | the case fold via the verified loop, `upseq(ToSeq(field))` | the letter-case-insensitive matching `re.IGNORECASE` gives the reserved-word sub-pattern `(NO\|[-+]?nan)` | A-reference | the changed operation (case-insensitive reserved-token matching) is modelled **deeply** as the upper fold (ASCII `a`..`z` up; ſ (383) → `S` (83)); no consumed axiom. G-AX validates `is_reserved_data_token` `==` the patched regex sub-pattern `(NO\|[-+]?nan)` AND `==` the real patched `_line_type` `data`/`new` verdict on the letter-bearing field sub-domain + fuzz (mapping.md §3.4). |
| C3 | `upseq(field) == kw_NO()` or `== kw_NAN()` or signed-`NAN` | the regex alternative `NO\|[-+]?nan` (the only letter-bearing data tokens) | I (under R) | identical literal alternation `NO`/`NAN`/signed-`NAN`, lifted to the folded code-point sequence. The decimal-number alternative `_decimal_re` has no non-exponent letters, is case-irrelevant, and is the unchanged numeric machinery (out of this decision's scope). |
| C4 | returns a `bool` (is this a recognised reserved data token) | whether `_line_type` accepts the field as part of a `data`/`new` line (vs `ValueError`) | R | the model's boolean ↔ "the line is recognised, not rejected"; the downstream `data,N`/`new` tag and the numeric parse are unchanged and case-irrelevant. |

Pre-patch (`re.compile(_type_re)`, no flag) recognises the reserved data tokens
only in their exact source spellings (`NO` upper-case; `nan` lower-case,
optionally signed), so a lower-case `no` field is unrecognised → the whole data
line raises `ValueError`. `model_prepatch_3.py` reproduces that by deciding the
token with the RAW exact-spelling comparison and **fails** the postcondition
`Result() == is_reserved_data_token(ToSeq(field))` on lower-case `no` (G-DIFF).
This is exactly the adversarial counterexample G-EQ flagged: a partial patch
that fixes only the `command` branch + `v.upper()` masking still raises on the
F2P data line; `model_prepatch_3` now makes that gap fail to verify.

## D. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* across both hunks — case-insensitive recognition of a reserved word —
is modelled **deeply** (the spelled-out upper fold `up`/`upseq` — ASCII letters plus the long-s → `S` identification — consumed in
all three verified loops), not hidden behind an axiom about the function under
change. There is **no consumed axiom**; the real callees (`str.upper`, the
patched regex / `_line_type`) appear only as **A-references** that G-AX validates
the deep models against.

## E. verify(model) ⇒ resolved

`command_line` verifies only if its verdict equals `is_command_tokens` (A2/A3);
`masked_field` verifies only if its verdict equals `is_masked_field` (B2/B3);
`reserved_data_token` verifies only if its verdict equals
`is_reserved_data_token` (C2/C3). By R (`str` ↔ `List[int]`, the unchanged
split/regex/number machinery) and by G-AX (the deep folds `==` the real
`str.upper`, the patched regex `(NO|[-+]?nan)`, and the patched `_line_type`
`command`/`data`/`new` verdicts), the three verified deciders equal the
gold-patched behaviour on every tested input.

The F2P test `test_roundtrip[True]` lower-cases the QDP file and round-trips it.
Its load-bearing recognition decisions are: lower-case `read [st]err …` lines
recognised as commands (modelled by `command_line`); lower-case `no` fields in a
data row recognised so the row classifies as `data` rather than raising at
line-classification (modelled by `reserved_data_token`); and lower-case `no`
fields then masked in the data loop (modelled by `masked_field`). These three
deciders cover every behavioural effect of the two gold hunks that the test
exercises; the equivalence claim is scoped to this modelled set plus the
A-reference-validated regex/`_line_type` remainder. The gold patch resolves
(G-RESOLVE). The trust points are exactly the two of PLAN §1.1: deep-model
soundness (G-AX, four A-references) and refinement fidelity (this document,
G-EQ).
