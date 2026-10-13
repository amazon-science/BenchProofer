# mapping.md — django__django-11728

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 05457817647368be4b019314fcc655445a5b4c0c`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and gives
the provenance of the genuinely-unchanged callees the bundle leans on.

Repo file under change: `django/contrib/admindocs/utils.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `scanGroupEnd (rest : List Char)` | the inner bracket-balancing `for idx, val in enumerate(...)` scan, shared verbatim by `replace_named_groups` (`django/contrib/admindocs/utils.py:169-182`) and `replace_unnamed_groups` (`utils.py:203-216`) | the modeled changed operation: locate the bracket that balances an already-open group |
| `nextBal (prev) (bal) (c)` | the body's depth update: `if val == '(' and prev_char != '\\': unmatched_open_brackets += 1; elif val == ')' and prev_char != '\\': unmatched_open_brackets -= 1` (`utils.py:177-181`, `211-214`) | pure spec: the running unmatched-bracket count after one character |
| `scanLen (prev) (bal) (rest)` *(deep model)* | the whole scan loop's input→consumed-length relation | pure spec: characters consumed up to and including the balancing bracket, or `none` |

The match-position **producer** (`named_group_matcher`/`unnamed_group_matcher`
`.finditer`, `utils.py:149-150,162-165,198`) and the downstream textual
**substitution** (`pattern.replace(...)`, the `final_pattern` reassembly,
`utils.py:184-187,217-237`) are genuinely-unchanged callees: the patch touches
ONLY the inner scan. They are bridged/transliterated by the executable checks
(§3, conformance_check.py), not modeled in Lean.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types. A wrong entry surfaces as spurious
G-CONF disagreements (the falsifiability the plan §4 trust statement refers to).

| repo reality | Lean carrier | bijection |
|---|---|---|
| `pattern[end:]` / `pattern[start+1:]` — the suffix string the scan iterates (a `str`) | `rest : List Char` | `s` (Python str) ↔ `s.toList`-shaped `List Char`; `len(s)` ↔ `l.length`; empty `str` ↔ `[]`; `s[k]` ↔ `l[k]!` |
| a single Python character `ch` | Lean `Char` | `Char.ofNat (ord ch)` ↔ `ch`; on the BMP this is total and exact |
| `unmatched_open_brackets` (a Python `int`, only ever ≥ 0 along the scan) | `bal : Nat` | identity on non-negative integers; the scan starts at `1` (`unmatched_open_brackets, prev_char = 1, None`) |
| `prev_char` (a `str` char or `None`) | `prev : Option Char` | `None` ↔ `none`; a char `ch` ↔ `some (Char.ofNat (ord ch))` |
| the reported end offset (`idx` in the original; `idx+1`/`idx+2` arithmetic in the patched slice index) | `Option Nat` (chars consumed, incl. the balancing bracket) | `none` ↔ "never balanced (no append happened)"; `some k` ↔ the balancing bracket is the `k`-th character of `rest`, i.e. patched slice end `end + k` (named) / `start + 1 + k` (unnamed). See §3.1 for the index reconciliation. |

Lean `List Char` indexing is total and sound; the carrier is `List Char`
because the operation is a per-code-point scan.

### 2.1 escape semantics (`prev_char`)

The repo guards `val == '(' and prev_char != '\\'` (and the `)` case): a bracket
immediately preceded by a backslash is escaped and does NOT change the depth.
`nextBal` reproduces this exactly with `prev ≠ some '\\'`. `prev` is the
character read on the PREVIOUS step (`prev_char = val` at the end of the body),
which `scanGroupEnd` threads as `prev := some c` and `scanLen` threads as the
`some c` argument of its recursive call. The very first character has `prev =
none ≠ some '\\'`, matching the repo's initial `prev_char = None`.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

This bundle consumes **no axioms**. The changed operation is modeled DEEPLY
(`scanLen`/`nextBal` in the `pure` region + the verified forward loop). G-AX
validates two A-reference facts against the REAL repo code at base_commit and at
patch:

### 3.1 `scanLen`/`nextBal` deep model ↔ the patched inner scan (A-reference)

The patched scan (gold, `utils.py` after `patch.diff`) for the named case is:

```python
unmatched_open_brackets, prev_char = 1, None
for idx, val in enumerate(pattern[end:]):
    if val == '(' and prev_char != '\\':
        unmatched_open_brackets += 1
    elif val == ')' and prev_char != '\\':
        unmatched_open_brackets -= 1
    prev_char = val
    if unmatched_open_brackets == 0:
        group_pattern_and_name.append((pattern[start:end + idx + 1], group_name))
        break
```

i.e. for each character it FIRST folds the depth (`nextBal`), THEN tests
`== 0`, and on success records the end slice index `end + idx + 1` — exactly one
past the balancing bracket. `scanLen none 1 rest` returns the count `k = idx + 1`
of characters consumed up to and including that bracket, so the patched slice end
`end + idx + 1 = end + k`. The unnamed case is identical with base `start + 1`
and recorded end `start + 2 + idx = (start + 1) + (idx + 1) = (start+1) + k`.
G-AX (axiom_check.py) confirms, on a boundary corpus + fuzz, that for every
suffix the deep model `scan_len(rest)` equals the offset the REAL patched loop
reports (`idx + 1`, or `None` when it never breaks).

### 3.2 `nextBal` ↔ the per-character depth update (A-reference)

G-AX separately checks the single-character transition: for every `(prev, bal,
c)` over the alphabet `( ) \ <ordinary>`, `next_bal(prev, bal, c)` equals the
repo's `unmatched_open_brackets` update (`+1` on unescaped `(`, `-1` on
unescaped `)`, else unchanged). This is the only behavioral primitive; pinning it
pins the whole scan.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`11728`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates `nextBal`/`scanLen` and the verified loop to Python, then embeds
that shadow scan inside the rest of the two real (unchanged) host functions
(match producer + substitution) and diffs the whole `replace_named_groups` /
`replace_unnamed_groups` output against `patch.diff`'s behaviour over ≥10⁵ fuzzed
regex-like patterns. Exit 0 iff zero disagreements.
