# mapping.md — astropy__astropy-14365

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 7269fa3e33e8d02485a647da91a5a2a60a06af61`, states the type
abstraction, and gives the provenance of the deep-model references (there are no
consumed `@ContractOnly` axioms).

Repo file under change: `astropy/io/ascii/qdp.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `command_line(tok0, tok1, ncols)` | `_line_type(line, delimiter=None)` — `astropy/io/ascii/qdp.py:20` (the `command` branch of its classifier, regex `_command_re` at line 63, compiled at line 71) | modeled changed function #1: case-insensitive recognition of a `READ [ST]ERR <cols>` command line |
| `masked_field(field)` | the per-value missing-marker test in `_get_tables_from_qdp_file` — `astropy/io/ascii/qdp.py:308-310` (`for v in line.split(delimiter): if v == "NO": ...`) | modeled changed function #2: case-insensitive recognition of the masked sentinel `NO` |
| `reserved_data_token(field)` | the `data`/`new` branch reserved-token recognition of `_line_type` — `astropy/io/ascii/qdp.py:20` (the `(NO\|[-+]?nan)` alternative of `_data_re` at line 64 and the `NO` of `_new_re` at line 63, compiled at line 71) | modeled changed function #3: case-insensitive recognition of a reserved-word data token (`NO`/`nan`), the same `re.IGNORECASE` edit's effect on the `data`/`new` branches |
| `up(c)` *(deep model — A-reference 1)* | the per-code-point case identification the patch introduces: `v.upper()` (line 309 post-patch) and the letter-folding effect of `re.IGNORECASE` (line 71 post-patch). ASCII `a`..`z` (97..122) fold to `A`..`Z` (subtract 32); the long-s letterform ſ (U+017F, 383) folds to `S` (83) — it is the ONE code point outside ASCII that both `str.upper` and `re.IGNORECASE` identify with a keyword letter (`ſ`.upper() == `S`; `re.fullmatch("S", "ſ", re.IGNORECASE)` matches); every other code point is unchanged | pure spec: per-code-point upper fold |
| `upseq(s)` *(deep model — A-reference 1)* | the same fold over a whole field/word (`str.upper` / `re.IGNORECASE` letter identification) | pure spec: sequence case fold |
| `is_masked_field(s)` *(deep model — A-reference 2)* | `v.upper() == "NO"` (line 309 post-patch) | pure spec: masked iff case fold == `NO` |
| `is_command_tokens(t0,t1,n)` *(deep model — A-reference 3)* | `_line_type`'s `command` verdict under `re.IGNORECASE` (regex `READ [TS]ERR(\s+[0-9]+)+`, lines 63/70/71 post-patch) | pure spec: command iff folded words are `READ` + `SERR`/`TERR` with ≥1 column |
| `is_reserved_data_token(s)` *(deep model — A-reference 4)* | the `(NO\|[-+]?nan)` reserved-token alternative of `_data_re` (and the `NO` of `_new_re`) under `re.IGNORECASE` (lines 63/64/71 post-patch) | pure spec: a reserved data token iff folded field is `NO`, `NAN`, or signed `NAN` |
| `kw_NO / kw_READ / kw_SERR / kw_TERR / kw_NAN` | the literal reserved words `NO`, `READ`, `SERR`, `TERR`, `NAN` (upper-case code-point sequences) | pure spec: reserved-word tokens |

The pre-patch repo expressions the change replaces (for the refinement audit,
not referenced from the consumer spec view): `re.compile(_type_re)` without a
flag (`qdp.py:71`, case-sensitive) and the bare `v == "NO"` test
(`qdp.py:309`, case-sensitive).

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `str` (a line, a whitespace-split word `v`/`command[i]`, a reserved word) | `List[int]` of Unicode code points | `s[k]` ↔ `field[k] == ord(s[k])`; `len(s)` ↔ `len(field)`; an empty `str` ↔ `[]` |
| `str` value inside a specification | `PSeq[int]` (pure Viper sequence) | `ToSeq(list)` materializes the list as a `PSeq`; `PSeq` `+`/`take`/`drop`/`len`/`[i]` mirror `str` `+`/slice/`len`/index |
| `str.upper()` (line 309 post-patch) / the letter fold of `re.IGNORECASE` (line 71 post-patch) | `upseq` (the per-code-point upper fold: ASCII `a`..`z` → `A`..`Z`, plus ſ (383) → `S` (83)) | `upseq(ToSeq(field))` ↔ the case identification the patched recognisers apply. The model's spec is total over `PSeq[int]` (there is no ASCII precondition), so the fold must agree with the real semantics on EVERY code point *as observed through equality with the reserved words*: for each reserved-word letter {R,E,A,D,S,T,N,O}, the set of code points Python's case-insensitive matching identifies with it is exactly its ASCII case pair — except `S`, which additionally gains the long-s ſ (383) (`ſ`.upper() == `"S"`, and ſ matches `S`/`s` under `re.IGNORECASE`). The fold therefore maps `a`..`z` up, maps 383 → 83, and leaves every other code point unchanged; a code point outside these orbits can never fold onto a reserved-word letter, so leaving it unchanged preserves the (in)equality verdict even when its full-Unicode `str.upper` image differs. Validated over ASCII + long-s boundary/fuzz by axiom_check.py / G-AX. |
| `line.split(delimiter)` field iteration (line 308) | the field is supplied directly to `masked_field` as the carrier `List[int]` | the splitting itself is case-irrelevant unchanged machinery; only the per-field `== "NO"` ↔ `.upper() == "NO"` test changed. |
| `_line_type`'s regex tokenizing of a command line (whitespace runs, the `(\s+[0-9]+)+` column tail) | the two leading words are supplied as `tok0`, `tok1` and the column count as `ncols` | the regex's whitespace/number structure is unchanged by the patch (the column numbers `[0-9]+` and the separators `\s+` are case-irrelevant); the changed effect of `re.IGNORECASE` on the `command` branch is that the keyword letters `READ`/`[TS]ERR` match case-insensitively, which the model captures by upper-folding the two keyword words. |
| `_line_type`'s regex tokenizing of a `data`/`new` line (the `(sep …)*` field repetition, the `_decimal_re` numeric tokens) | each reserved-word field is supplied directly to `reserved_data_token` as the carrier `List[int]`; the field-splitting and numeric tokens are case-irrelevant unchanged machinery | the changed effect of `re.IGNORECASE` on the `data`/`new` branches is that the reserved-token alternative `(NO\|[-+]?nan)` matches case-insensitively; the `_decimal_re` numbers (whose only letters are the case-symmetric exponent `[eE]`) are unaffected. The model captures the reserved-token recognition by upper-folding the field and comparing to `NO`/`NAN`/signed-`NAN`. |

`str` indexing/iteration is banned in Nagini, so the carrier is `List[int]`
throughout; the specification is phrased over `PSeq[int]` via `ToSeq`.

## 3. Deep-model references (kind-A-reference — checked by G-AX / axiom_check.py)

There are **no consumed `@ContractOnly` axioms**: the `axioms` region of
model.py is empty. The two changed behaviours are the case fold itself, modelled
deeply. Each deep model is validated equal to the real callee out-of-band.

### 3.1 `up` / `upseq` ↔ `str.upper` (A-reference 1)
**Callee:** CPython `str.upper`, the operation the patch introduces as
`v.upper()` (and the letter-folding effect of `re.IGNORECASE`). On the ASCII
token domain that QDP fields inhabit, `str.upper` maps `a`..`z` (97..122) to
`A`..`Z` (subtract 32) and leaves every other character unchanged — exactly
`up`/`upseq`. axiom_check.py asserts `upseq(s) == [ord(c) for c in s.upper()]`
over the ASCII letter/digit/punctuation alphabet, 17 boundary + 20 000 fuzz.

### 3.2 `is_masked_field` ↔ `v.upper() == "NO"` (A-reference 2)
**Callee:** the patched missing-value test `v.upper() == "NO"` (`qdp.py:309`).
axiom_check.py asserts `model_is_masked_field(field) == (field.upper() == "NO")`
over 17 boundary + 20 000 fuzz fields (including `NO`/`no`/`No`/`nO`, near-misses
`N0`/`NOO`/`ON`, numerics, and `nan`). This is an exact decision-equivalence,
asserted at the verdict level (no double-mask: the model's `upseq`/`NO` decision
and the real `.upper()/"NO"` decision are compared as booleans on the SAME raw
field).

### 3.3 `is_command_tokens` ↔ patched `_line_type` command verdict (A-reference 3)
**Callee:** the patched `_line_type` (`qdp.py:20`), whose command regex
`READ [TS]ERR(\s+[0-9]+)+` is compiled with `re.IGNORECASE` (`qdp.py:71`
post-patch). Docs: the QDP format is not case sensitive (problem statement;
`qdp` itself accepts lower-case commands). axiom_check.py runs the REAL
`_line_type` (preferring the in-container repo module; otherwise the gold-patched
source verbatim, stdlib `re` only) on every case combination of the keyword
words `{READ, read, Read, rEaD, ...}` × `{SERR, serr, TERR, terr, ERR, XERR,
...}` with and without column numbers, plus 5 000 randomized fuzz lines, and
asserts the real `"command"`/non-command verdict equals
`is_command_tokens(tok0, tok1, ncols)`. The decision-equivalence is asserted at
the verdict level (no double-mask). The whitespace/number structure of the line
(unchanged by the patch) is held fixed by building the line as the two keyword
words plus the integer column tokens, single-space separated — consistent with
the regex's literal single space between `READ` and `[TS]ERR`.

### 3.4 `is_reserved_data_token` ↔ patched `data`/`new` recognition (A-reference 4)
**Callee:** the patched `_line_type` (`qdp.py:20`), whose `_data_re` reserved
alternative `(NO|[-+]?nan)` and `_new_re` `NO(sep NO)+` are compiled with
`re.IGNORECASE` (`qdp.py:71` post-patch). This is the SAME hunk-1 edit, on the
`data`/`new` branches. axiom_check.py validates `is_reserved_data_token` two
ways, both at the verdict level (no double-mask):
  (i) against the patched regex reserved-token sub-pattern `re.compile(r"(NO|
      [-+]?nan)", re.IGNORECASE).fullmatch` — a VERBATIM slice of the
      gold-patched `_data_re` alternation — over 34 boundary + 20 000 fuzz
      fields (case variants of `NO`/`nan`, signs, near-misses `N0`/`NOO`/`naan`,
      numbers `1`/`0.5`/`1e3`/`-1.4e-5`);
  (ii) against the REAL patched `_line_type`'s `data`/`new` verdict on
      single-field lines, restricted to the **letter-bearing** field sub-domain
      (fields containing an ASCII letter other than the exponent `e`/`E`). That
      filter is an INPUT-domain property independent of the predicate under
      test (the data grammar admits letters only in the reserved words and in a
      number's exponent), so a letter-bearing field is accepted by `_line_type`
      as data iff it is exactly `(NO|[-+]?nan)` — not a double-mask. Decimal
      numbers (no non-exponent letters) are case-irrelevant unchanged machinery
      and out of this predicate's scope.
The `new` branch (≥2 `NO` tokens) is additionally cross-checked: the model
"every token case-folds to `NO` and there are ≥2" verdict is asserted equal to
the real `_line_type` `== "new"` verdict over 8 000 fuzz token rows. The exact
F2P discriminator — a single lower-case `no` field — is asserted recognised by
both the model and the real callee.

**Post-patch self-guard (DEFECT-3 fix):** the official base image is at
`base_commit` (PRE-patch). axiom_check.py prefers the in-container repo module
but then ASSERTS the imported `_line_type` is the POST-patch one (lower-case
`read serr 1` → `command` and lower-case `no` → `data,1`); if not, it exits
non-zero with an actionable message telling the operator to apply `patch.diff`
first. The G-AX harness therefore runs it with the gold patch applied
(`run_in_container(..., apply_gold=True, gold_patch_path=patch.diff)`); the host
fallback reconstructs the gold-patched source verbatim. Either way the checker
can never silently validate the unpatched function.

**Flag dependency (recorded for G-AX):** the command- and reserved-token
recognition references are sound only because the patch uses `re.IGNORECASE`;
the masking reference is sound for the default `str.upper` (no locale/Unicode
special-casing matters on the ASCII token domain). axiom_check.py imports only
stdlib `re`/`random` plus, when available, the repo's own
`astropy.io.ascii.qdp` — the very file the patch edits. Exit 0 iff every
obligation holds (in-container with gold applied: 164 boundary + 73 000 fuzz
observations, 0 violations).
