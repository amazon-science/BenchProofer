# refinement.md — django__django-11728

Maps every operation in `implementation_findGroupEnd` to its `patch.diff`
counterpart in the inner scan of `replace_named_groups` /
`replace_unnamed_groups` (django/contrib/admindocs/utils.py). Tags: **R**
type-refinement, **A-consumed** proof uses a callee axiom, **A-reference** op left
as the real repo callee in G-CONF (not axiomatized), **I** identical concrete op.

## Patch (post-patch scan — both functions, identical relocation)
```python
for idx, val in enumerate(pattern[end:]):                 # named (unnamed: pattern[start+1:])
    if val == '(' and prev_char != '\\': unmatched_open_brackets += 1
    elif val == ')' and prev_char != '\\': unmatched_open_brackets -= 1
    prev_char = val
    if unmatched_open_brackets == 0:                      # <-- moved to BOTTOM
        group_pattern_and_name.append((pattern[start:end + idx + 1], group_name))
        break
```
At base_commit the `if unmatched_open_brackets == 0:` block sat at the TOP of the
loop and used `end + idx` (named) / `start + 1 + idx` (unnamed). The fix moves
the depth-zero check below the depth update and bumps the recorded index by one.

## Modeling decision
The behaviour-changing core shared by both functions is the inner scan that, given
the characters after a group's already-open `(`, returns the offset at which the
group closes (depth back to `0`). It is modeled DEEPLY as `findGroupEnd`:

- the per-character depth update (`(` ⇒ +1, `)` ⇒ −1 when unescaped; `prev_char`
  bookkeeping) is `stepBracket`; the running depth over a prefix is `depthAfter`
  (starts at `1`, the group's own open paren);
- `problem_spec_findGroupEnd` pins the closing offset to be the FIRST index whose
  `+1`-length prefix brings the depth to `0` (and `none` iff no prefix does).

The bug is precisely that the pre-patch loop detects depth-zero one iteration
late, so it misses the case where the closing `)` is the LAST character. The spec
requires `some i` with `i = cs.length - 1` permitted (closing at the final
character), which the post-patch scan satisfies and the pre-patch scan cannot.

## Operation correspondence
| # | Lean op (`implementation_findGroupEnd`) | patch.diff op | tag | note |
|---|---|---|---|---|
| 1 | `let mut depth : Int := 1` | `unmatched_open_brackets = 1` | I | both initialise the depth to 1 (the group's own `(` is already open). |
| 2 | `let mut prev : Option Char := none` | `prev_char = None` | R | `None` ↔ `none`; used only for the escape test. |
| 3 | `for val in cs do …` | `for idx, val in enumerate(pattern[end:]):` | R | `cs` ↔ the scanned slice `pattern[end:]` / `pattern[start+1:]` (chars after the open paren); `idx` ↔ the loop counter `idx`. |
| 4 | `if val == '(' && prev != some '\\' then depth := depth + 1` | `if val == '(' and prev_char != '\\': unmatched_open_brackets += 1` | I | unescaped open paren increments depth. |
| 5 | `else if val == ')' && prev != some '\\' then depth := depth - 1` | `elif val == ')' and prev_char != '\\': unmatched_open_brackets -= 1` | I | unescaped close paren decrements depth. |
| 6 | `prev := some val` | `prev_char = val` | I | record current char as previous (for next escape test). |
| 7 | `if depth == 0 then return some idx` | `if unmatched_open_brackets == 0: …append((pattern[start:end+idx+1], group_name)); break` | R | the relocated (post-patch) depth-zero check, AFTER the update; `return some idx` ↔ recording the close at the current index. The Lean offset `idx` maps to the real recorded slice/index by the constant shift `end+idx+1` / `start+2+idx` (G-CONF applies it). This is THE behaviour-changing op. |
| 8 | `idx := idx + 1` (loop advance) | `enumerate` advancing `idx` | I | index bookkeeping. |
| 9 | `return none` (loop exhausted) | loop ends with no `break` ⇒ nothing recorded for this group | R | group never closed ⇒ no recorded substring/index ↔ `none`. |

The behaviour-changing op is #7: pre-patch the depth-zero test ran at the TOP of
the body (recording `end+idx`, requiring one extra trailing character), post-patch
it runs at the BOTTOM (recording `end+idx+1`), detecting a close at the final
character. The prepatch impl puts the `if depth == 0 then return some idx` at the
TOP of the loop body (before the depth update), exactly the pre-patch control flow.

## R/I legs ⇒ G-CONF
All ops are R or I (no axiom): the impl is fully concrete. `conf_skip = false`.
G-CONF transliterates `implementation_findGroupEnd` op-for-op into a Python
shadow, runs it on the scanned slice of each fuzzed `pattern`, applies the
constant index shift (#7), and compares against the closing index that the REAL
patched `replace_named_groups` / `replace_unnamed_groups` compute, over ≥10^5
inputs.

## No A-consumed / A-reference row
The scan has no unchanged outside callee: the only sub-operation is the
per-character depth update, spelled out as `stepBracket`. The group-start regexes
(`named_group_matcher`, `unnamed_group_matcher`) are unchanged and only set the
scan's starting offset — they are used by G-CONF to build the slice, not modeled
or axiomatized. Hence `meta.json axioms = []`, `deep_model_references = []`, and
`axiom_check.py` is a skip stub.

## F2P alignment
- `test_simplify_regex` adds patterns with NO trailing `/` or `$` whose final
  group must still be replaced, e.g.
  `r'^(?P<a>\w+)/b/(?P<c>\w+)' → '/<a>/b/<c>'`,
  `r'^(?P<a>\w+)/b/(\w+)' → '/<a>/b/<var>'`,
  `r'^(?P<a>(x|y))/b/(?P<c>\w+)' → '/<a>/b/<c>'`. For each, the trailing group's
  closing `)` is the final character; the spec requires `some (cs.length-1)`,
  which the prepatch impl (top-of-loop check) reports as `none`, so it cannot
  satisfy the discriminating clause. (`test_app_not_found` is an unrelated F2P
  swept in by the shared test module; not modeled.)
`patch.diff` (gold verbatim) makes the harness resolve.
