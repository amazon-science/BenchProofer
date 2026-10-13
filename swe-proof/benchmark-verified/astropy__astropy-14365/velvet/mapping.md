# mapping.md — astropy__astropy-14365

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 7269fa3e33e8d02485a647da91a5a2a60a06af61`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and gives
the provenance of each modeled callee.

Repo file under change: `astropy/io/ascii/qdp.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `lineType (line : List Char)` | `_line_type(line, delimiter=None)` — `astropy/io/ascii/qdp.py:20` (return path `:78-85`) | modeled changed function #1: the per-line classifier |
| `classify (fold) line` *(deep model — A-reference)* | the compiled-regex match in `_line_type`: `_line_type_re = re.compile(_type_re[, re.IGNORECASE])` (`qdp.py:71`) driving the `groupdict` dispatch (`qdp.py:78-85`) | pure spec: the line's classification. `fold=true` models the **post-patch** `re.IGNORECASE` compile; `fold=false` models the **pre-patch** flag-less compile. Validated `classify true == real(IGNORECASE)` and `classify false == real(no-flag)` by axiom_check.py (G-AX), NOT consumed as an axiom. |
| `maskFlags (tokens : List (List Char))` | the per-row value loop in `_get_tables_from_qdp_file` — `astropy/io/ascii/qdp.py:307-316` (the `for v in line.split(delimiter)` body) | modeled changed function #2: per-cell missing-value decision |
| `maskSeq (fold) tokens` *(deep model — A-reference)* | the masking test `v == "NO"` (pre) / `v.upper() == "NO"` (post), `qdp.py:309` | pure spec: the boolean "this cell is the masked sentinel" for each cell. `fold=true` models the **post-patch** `v.upper() == "NO"`; `fold=false` the **pre-patch** `v == "NO"`. Validated == real by axiom_check.py. |
| `isDecimal`, `decRun`/`decStep` *(deep model — A-reference)* | the numeric-literal alternative `_decimal_re` (`qdp.py:62`), used inside `_data_re` (`qdp.py:69`) | regex-free DFA for `[+-]?(\d+(\.\d*)?\|\.\d+)([eE][+-]?\d+)?`; validated == `re.fullmatch(_decimal_re, ·)` by axiom_check.py. |
| `isDirective`, `isMarkerTok`, `isNanTok`, `isDataTok`, `words`, `stripWs` | the sub-grammar of `_type_re` (`qdp.py:62-70`) — `_command_re`, `_new_re`, `_data_re`, the leading `\s*`/strip, the trailing `(\!comment)?` | the spelled-out alternation that `classify` composes; their joint behavior is validated only through `classify` (G-AX). |

There are **no consumed axioms** in this bundle: both changed operations
(`re.IGNORECASE` classification; `.upper()` masking) are modeled **deeply** and
validated == the real code, so they are A-references, not A-consumed liabilities.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `line : str` (the argument of `_line_type`; per-character) | `List Char` | `s` (Python str) ↔ `s` as a `List Char`; `ch` ↔ `Char.ofNat (ord ch)`, total/exact on the BMP; `len(s)` ↔ `l.length`; empty str ↔ `[]` |
| the classifier's `str` return (`"comment"`/`"command"`/`"new"`/`f"data,{n}"`/raise) | `LType` (`comment`/`command`/`newblock`/`data n`/`reject`) | `"comment"`↔`comment`; `"command"`↔`command`; `"new"`↔`newblock`; `f"data,{n}"`↔`data n`; `raise ValueError`↔`reject` |
| `v : str` (one cell of `line.split(delimiter)`) | `List Char` | as above |
| `v == "NO"` / `v.upper() == "NO"` → `np.ma.masked` vs append-number | `Bool` (one entry of `maskSeq`) | `True` (cell becomes `np.ma.masked`) ↔ `true`; `False` (cell parsed as a number) ↔ `false` |
| `line.split(delimiter)` with `delimiter=None` | `words : List Char → List (List Char)` | Python `str.split()` (no arg) splits on runs of whitespace and drops empties; `words` = `splitOnP isWs` then drop `[]`. Bijection holds for the **default delimiter** (mapping.md §3, scoping). |

**Scope of the model (delimiter).** The model fixes `delimiter=None` (whitespace
delimiter), the configuration the F2P test (`test_roundtrip`, default QDP) and the
issue's reproducer exercise. The patched behavior — case-insensitive recognition —
is orthogonal to the delimiter; G-AX/G-CONF fuzz the default delimiter, matching
the tested code path. (The `delimiter=","` path is unchanged by the patch and not
on the F2P path.)

Lean `List Char` indexing is total and sound; the carrier is `List Char`
throughout because both operations are per-code-point / per-token.

## 3. Callee provenance (A-reference — checked by G-AX / axiom_check.py)

### 3.1 `classify` deep model ↔ the `_line_type` regex (A-reference)
**Modeled code:** the compiled regex `_line_type_re` and the `groupdict` dispatch
in `_line_type` (`qdp.py:62-85`). The single behavioral change is the compile
flag: `re.compile(_type_re)` (pre) → `re.compile(_type_re, re.IGNORECASE)` (post).
`classify`'s `fold` parameter is exactly that flag:

- `classify true line`  models `re.compile(_type_re, re.IGNORECASE)` then dispatch;
- `classify false line` models `re.compile(_type_re)` then dispatch.

The dispatch reproduces `_line_type`'s control flow verbatim: strip the line;
empty ⇒ `"comment"`; `match is None` ⇒ raise (`reject`); else the first non-`None`
named group in `{command, new, data}` order wins, and `data` yields
`f"data,{len(val.split(delimiter))}"`. Group precedence (`command` before `new`
before `data`), the literal single space in `READ [TS]ERR`, the `\s+`-separated
integer operands, the optional trailing `(\!comment)?`, and the `data`-token
alternation `(_decimal_re|NO|[-+]?nan)` are each transcribed
(`isDirective`/`isMarkerTok`/`isDataTok`/`isDecimal`). `re.IGNORECASE` folds only
the **letter** literals of the pattern (`READ`,`SERR`,`TERR`,`NO`,`nan`,`eE`);
digit/sign/`\s` classes are unaffected — captured by `eqFold` applying
`Char.toUpper` to the reserved-word comparisons only, and by `isDecimal` being
case-irrelevant (both `e`/`E` accepted regardless of the flag).

**Soundness check (G-AX):** `axiom_check.py` rebuilds the real `_type_re` verbatim
and runs both `re.compile(_type_re, re.IGNORECASE)` and `re.compile(_type_re)`
through the genuine `_line_type` dispatch, asserting `classify true == real(IGNORECASE)`
and `classify false == real(no-flag)` over boundary cases + ≥10⁶ fuzzed lines.
Imports only stdlib `re`. Exit 0 iff sound.

### 3.2 `maskSeq` deep model ↔ the `v == "NO"` / `v.upper() == "NO"` test (A-reference)
**Modeled code:** the masking decision in `_get_tables_from_qdp_file`'s value loop
(`qdp.py:307-316`). Pre-patch a cell is masked iff `v == "NO"`; post-patch iff
`v.upper() == "NO"`. `maskSeq fold` maps each token to that boolean: `fold=true`
⇒ `v.upper() == "NO"`, `fold=false` ⇒ `v == "NO"`. `axiom_check.py` runs the real
predicate on boundary + fuzzed cells and asserts agreement for both flags.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`14365`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates `classify`/`maskSeq` (with `fold=true`, the post-patch flag) to
Python and diffs them against the gold-patched repo behaviour — the patched
`_line_type` classification and the patched `v.upper() == "NO"` masking — over
≥10⁵ fuzzed lines/cells. No A-tagged callee is left as a stub here (the impl
region is pure R/I: both modeled ops are deep models, not consumed axioms), so
`conf_skip=false`.
