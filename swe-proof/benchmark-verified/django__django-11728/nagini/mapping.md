# mapping.md — django__django-11728

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 05457817647368be4b019314fcc655445a5b4c0c`, states the type
abstraction, and records provenance.

Repo file under change: `django/contrib/admindocs/utils.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `named_group_pattern_end(region, prev0)` | the inner depth-scan loop of `replace_named_groups(pattern)` — `django/contrib/admindocs/utils.py:153` (loop body lines 168-182) | modeled changed function #1: computes the end of a named capture group's pattern span |
| `unnamed_group_pattern_end(region, prev0)` | the inner depth-scan loop of `replace_unnamed_groups(pattern)` — `django/contrib/admindocs/utils.py:190` (loop body lines 201-214) | modeled changed function #2: computes the end of an unnamed capture group's span |
| `close_off(s, bal, prev)` *(deep model — A-reference)* | the `unmatched_open_brackets` accounting in BOTH inner loops (lines 169-182 and 203-214): `+1` on unescaped `(`, `-1` on unescaped `)`, the matching close being where it returns to 0 | pure spec: offset of the matching closing parenthesis. Validated against the real Python scan by axiom_check.py (G-AX), NOT consumed as a `@ContractOnly` axiom. |
| `step_bal(c, prev, bal)` | the per-character `if val == '(' and prev_char != '\\': ... elif val == ')' and prev_char != '\\': ...` update (lines 178-181 / 210-213) | pure spec: one depth-update step (escape-aware) |

The capture-group opening `(` is consumed *before* the scan in the real code:
the named scan iterates `pattern[end:]` where `end = m.end(0)` is just past the
`(?P<name>` prefix (already one level deep); the unnamed scan iterates
`pattern[start + 1:]` where `start` is the index of the group's `(` (so `+ 1`
skips it). Both therefore begin already at depth 1 — modeled by the `bal = 1`
initial state and the `close_off(..., 1, ...)` calls.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `pattern` (`str`) and the scanned slice `pattern[end:]` / `pattern[start+1:]` | `region: List[int]` of Unicode code points | `region[k]` ↔ `ord(slice[k])`; `len(region)` ↔ `len(slice)`; `str` indexing is banned in Nagini so the carrier is a code-point list |
| `str` value inside a specification | `PSeq[int]` (pure Viper sequence) via `ToSeq(region)` | `PSeq` `len`/`[i]`/`drop` mirror `str` `len`/index/suffix-slice |
| `prev_char` (a `str` char or `None` at scan start) | `prev0: int` code point (the character immediately before the scan region; any value `!= 92` for the named scan's first char, since `(?P<...>` ends with `>` not `\`) | escape state carried into the scan; `'\\'` ↔ code 92 |
| `'('` / `')'` / `'\\'` | code points 40 / 41 / 92 | literal characters |
| absolute capture index returned to the caller: `end + idx + 1` (named) / `start + 2 + idx` (unnamed) | `Result()` = scan-relative span end `= close_off(...) + 1`; the caller adds the constant base offset (`end` resp. `start + 1`) | `Result()` is the slice end *relative to the region start*; `end + (idx+1)` ↔ `end + Result()` and `start + 2 + idx = (start+1) + (idx+1)` ↔ `(start+1) + Result()`. The base offsets `end` / `start+1` are pure index bookkeeping outside the changed scan. |

`idx` in the real loops is the enumerate index over the scanned slice; the
matching-close character sits at `idx == close_off(region) == k`, and the
fixed capture end is `idx + 1` past the region start — exactly `Result()`.

## 3. The changed operation, modeled deeply (A-reference, G-AX)

The single behavioural change (identical in both functions) is **when** the
depth-zero condition is recorded relative to processing the closing
parenthesis. The scan itself — the `close_off` / `step_bal` depth accounting —
is modeled **deeply** (spelled out over `PSeq[int]`), not behind a consumed
axiom; there is **no `@ContractOnly` axiom the proof consumes**. The deep model
is validated equal to the real Python scan out-of-band by `axiom_check.py`
(G-AX).

### 3.1 `close_off` / `step_bal` deep model ↔ the real inner scan (A-reference)
**Reference behaviour:** the depth-tracking loop in CPython/Django:
```python
unmatched_open_brackets, prev_char = 1, None
for idx, val in enumerate(slice):
    if val == '(' and prev_char != '\\':
        unmatched_open_brackets += 1
    elif val == ')' and prev_char != '\\':
        unmatched_open_brackets -= 1
    prev_char = val
    if unmatched_open_brackets == 0:   # POST-PATCH position (after the update)
        <record span end = idx + 1>
        break
```
`close_off(slice, 1, prev0)` is the `idx` of the first character whose
processing drives `unmatched_open_brackets` to 0 (the matching `)`); the fixed
span end is `idx + 1`, i.e. `close_off(...) + 1` — what `Result()` pins. The
escape rule `prev_char != '\\'` is `step_bal`'s `prev != 92` guard.

The pre-patch placement of the `if unmatched_open_brackets == 0:` check at the
**top** of the loop (lines 172-174 / 204-206) only records the span on the
*next* iteration after the close, so a group whose `)` is the final character
of the scanned slice is never recorded — that is the bug. `model_prepatch.py`
(named site) and `model_prepatch_2.py` (unnamed site) reproduce the top-check
placement and FAIL the `Result() == close_off(...) + 1` postcondition exactly
when `close_off(region) == len(region) - 1` (the close is the last character).

**Soundness check (G-AX):** `axiom_check.py` runs the real Python scan (the
exact byte-for-byte inner loop, post-patch) on boundary patterns (group ending
the string, group followed by `/`/`$`, nested groups, escaped parens `\(`/`\)`,
the literal F2P test patterns) plus tens of thousands of randomized fuzz
patterns over the alphabet `( ) \ a / | ? P < > w +`, and asserts that the deep
model `close_off`/`step_bal` reproduces the real `idx`+span-end on every input
whose group's matching close exists. It also asserts the discriminating
trailing-group cases (F2P) are recorded post-patch and dropped pre-patch.
Imports only the standard library `re` (used solely to locate group starts as
the real code does); the scan itself is pure Python. Exit 0 iff sound.

## 4. No consumed axioms

`# axioms-start/end` is intentionally empty: the proof depends on no
`@ContractOnly` callee. `re.finditer` (used by the real functions only to
enumerate group *start* positions) is outside the modeled span computation —
the model takes the already-isolated `region` as input — so it is neither
consumed nor referenced by the proof; its role is documented here for
completeness, not axiomatized.
