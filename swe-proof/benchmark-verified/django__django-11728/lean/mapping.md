# mapping.md — django__django-11728

## Instance
- repo: django/django
- base_commit: 05457817647368be4b019314fcc655445a5b4c0c
- spec_provenance: cold (derived from problem_statement + gold patch + base-commit
  source only)

## The logical change
`replace_named_groups` and `replace_unnamed_groups`
(django/contrib/admindocs/utils.py:151, :190 @ base_commit) each contain an inner
scan that walks the characters of `pattern` AFTER a capture group's open
parenthesis, tracking `unmatched_open_brackets` (the open-parenthesis nesting
depth, initialised to `1` because the group's own `(` is already open) and
`prev_char` (to recognise escaped parentheses). The scan must find the index at
which the depth returns to `0` — the group's closing parenthesis — and record the
group's substring up to and including it.

At base_commit the depth-zero test sits at the TOP of the loop body:

```python
for idx, val in enumerate(pattern[end:]):           # (named) — analogous for unnamed
    if unmatched_open_brackets == 0:
        group_pattern_and_name.append((pattern[start:end + idx], group_name))
        break
    if val == '(' and prev_char != '\\': unmatched_open_brackets += 1
    elif val == ')' and prev_char != '\\': unmatched_open_brackets -= 1
    prev_char = val
```

Because the test is checked at the START of an iteration, it only fires on the
iteration AFTER the closing `)` was consumed — i.e. there must be at least one
more character following the closing parenthesis. When the closing `)` is the
LAST character of `pattern` (a regex with no trailing `/` or `$`), the loop ends
without ever re-entering the body, the depth-zero branch never runs, and the
trailing group is never recorded — so it is not replaced. This is the reported
bug ("doesn't replace trailing groups").

The gold patch moves the depth-zero test to the BOTTOM of the loop body, AFTER
the current character has updated the depth, and adjusts the slice/index by one
(`end + idx` → `end + idx + 1`; `start + 1 + idx` → `start + 2 + idx`):

```python
for idx, val in enumerate(pattern[end:]):
    if val == '(' and prev_char != '\\': unmatched_open_brackets += 1
    elif val == ')' and prev_char != '\\': unmatched_open_brackets -= 1
    prev_char = val
    if unmatched_open_brackets == 0:
        group_pattern_and_name.append((pattern[start:end + idx + 1], group_name))
        break
```

Now the closing position is detected on the SAME iteration that consumes the
closing `)`, so a group whose `)` is the final character is found at that final
index. Both functions carry the identical relocation; they differ only in
bookkeeping (named records `(substring, name)` and slices `pattern[start:end+idx+1]`;
unnamed records the index pair `(start, start + 2 + idx)`). The shared,
behaviour-changing core is the inner scan that returns the closing offset, which
is what the Lean triple models as `findGroupEnd`.

## Symbol binding
| Lean symbol | Python source @ base_commit |
|---|---|
| `implementation_findGroupEnd` | the inner `for idx, val in enumerate(...)` scan in both `replace_named_groups` (utils.py:169-181) and `replace_unnamed_groups` (utils.py:206-216), returning the offset (relative to the scan's first character) at which the open group closes |
| `problem_spec_findGroupEnd` | the post-condition that offset must satisfy |
| `stepBracket` / `depthAfter` | the per-character `unmatched_open_brackets` update (the `if '(' … elif ')' … prev_char = val` body) and the running depth after a prefix |
| `cs` (parameter) | the slice scanned: `pattern[end:]` (named) / `pattern[start+1:]` (unnamed) — the characters AFTER the group's already-open `(` |

## Type bijection (Lean ↔ Python) — used by G-CONF
| Lean | Python | notes |
|---|---|---|
| `cs : List Char` | the scanned slice `pattern[end:]` / `pattern[start+1:]` | per-code-point sequence; `List Char` is total/sound for indexing |
| result `some i : Option Nat` | the loop reaches `unmatched_open_brackets == 0` at enumerate index `i` (the `break`) | `i` is the 0-based offset of the closing position WITHIN the scanned slice; named records `pattern[start:end+i+1]`, unnamed records `start+2+i` |
| result `none` | the loop runs to exhaustion without the depth reaching `0` | the group is never closed (no recorded substring/index) |
| `depthAfter (cs.take (i+1))` | value of `unmatched_open_brackets` after consuming the first `i+1` characters of the slice | starts at `1` (the group's own `(`); `(` ⇒ +1, `)` ⇒ −1, escaped or other ⇒ unchanged |

The mapping from the Lean offset `i` to the real recorded slice/index is a fixed
+constant shift (`end + i + 1`, `start + 2 + i`); G-CONF applies that shift when
comparing against the real functions.

## Callee provenance / flag deps
- No unchanged repo callee is consumed as an axiom. The scan's only sub-operation
  is the per-character depth update (open/close/escape recognition), which is
  spelled out concretely as `stepBracket`/`depthAfter` over the input character
  sequence. There is no `opaque`/`axiom` callee in `Solution.lean`;
  `axiom_check.py` is a skip stub.
- The named/unnamed group START is located by the module regexes
  `named_group_matcher = re.compile(r'\(\?P(<\w+>)')` and
  `unnamed_group_matcher = re.compile(r'\(')` (utils.py:149-150). These are
  UNCHANGED by the patch and only fix the scan's STARTING offset; the modeled
  behaviour is the scan itself (where the group ends), so the regexes are
  consumed by G-CONF to set up the slice, not modeled in Lean.
- Escaping rule: a `(` or `)` is structural only when `prev_char != '\\'`. This is
  reproduced exactly by `stepBracket` (`prev != some '\\'`). No `re` flags affect
  the scan.

## G-CONF fuzz seed
- pinned seed: `11728`
- ≥10^5 fuzzed inputs, drawn to exercise: groups closing at the final character
  (the trailing-group bug), groups followed by trailing text (`$`, `/`, literal
  chars), nested groups `((x|y)\w+)`, escaped parentheses `\(` `\)`, never-closing
  fragments (depth never returns to 0), and the exact F2P patterns from
  `tests/admin_docs/test_views.py::test_simplify_regex`. Each fuzzed `pattern`
  is run through BOTH real patched functions; the Lean offset (with the constant
  index shift above) is compared against the real recorded closing index.
