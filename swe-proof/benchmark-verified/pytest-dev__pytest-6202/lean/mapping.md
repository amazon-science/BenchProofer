# mapping.md — pytest-dev__pytest-6202

## Symbol binding (file:line @ base_commit 3a668ea6ff24b0c8f00498c3144c63bac561d925)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_getmodpath` / `problem_spec_getmodpath` / `correct_getmodpath` | `PyobjMixin.getmodpath` (its result-assembly tail) | `src/_pytest/python.py:271-289` |
| `parts : List String` | the local `parts` list assembled by the method | `python.py:275-286` (built by the `for node in chain` loop, then `parts.reverse()` at 287) |
| `result : String` | the method's return value (the dotted module path) | `python.py:288-289` (pre-patch) / `python.py:288` (post-patch) |

### What the patch changes (base_commit)

`getmodpath` (`python.py:271`) walks the node's `listchain()` (reversed),
skipping `Instance` nodes and stopping at the `Module`, collecting each scope's
`name` into the local list `parts` (inner-to-outer). It then does:

```python
parts.reverse()                 # python.py:287  -> outer-to-inner order
s = ".".join(parts)             # python.py:288  (REMOVED by patch)
return s.replace(".[", "[")     # python.py:289  (REMOVED by patch)
```

The gold patch (`src/_pytest/python.py`) replaces those two trailing lines with

```python
return ".".join(parts)          # post-patch
```

i.e. it drops the `.replace(".[", "[")` post-processing step. That substring
rewrite was a leftover from removed generator-style test collection; it
corrupts any path in which a scope name legitimately contains `"["` immediately
after a `.` join boundary (e.g. a parametrize id `"[.["`), turning
`"TestY.testmethod_two[.[]"` into `"TestY.testmethod_two[[]"`.

The everything-before-`parts.reverse()` portion (the `listchain` walk, the
`Instance`/`Module` filtering, the `stopatmodule`/`includemodule` flags) is
UNCHANGED by the patch. It only determines the *contents and order* of `parts`;
it is the input to the modeled tail. The bundle therefore takes `parts` (the
gathered inner-to-outer name list) as the input carrier and models the
result-assembly tail that the patch edits.

### Lean modeling

- `parts : List String` is the gathered scope-name list in the order the loop
  appended them (inner-to-outer), exactly the Python local `parts` immediately
  before `parts.reverse()`.
- The impl mirrors the post-patch tail: `parts := parts.reverse` then
  `String.intercalate "." parts` — i.e. `parts.reverse()` then `".".join(parts)`.
- `problem_spec_getmodpath` pins the result to `String.intercalate "."
  parts.reverse`: the names in reverse order, joined with `.`, with nothing
  added/removed/rewritten. This is the exact post-patch behaviour and is fully
  grounded in the input `parts` (no oracle).
- The pre-patch impl (`Solution_prepatch.lean`) appends the extra
  `.replace ".[" "["` step after the join — exactly the removed line — so its
  result differs from the spec whenever a name produces a `".["` boundary
  substring (the F2P parametrize id `"[.["`).

## Lean ↔ Python type bijection (used by G-CONF / G-AX)

| Python | Lean | bijection |
|---|---|---|
| `parts` (list of `str`, inner-to-outer) | `parts : List String` | element-wise identity; order preserved |
| `".".join(xs)` | `String.intercalate "." xs` | identical: `.` separator between consecutive elements, `""` for empty list, the lone element for a singleton |
| `xs.reverse()` (in place) then use | `xs.reverse` | identical list reversal |
| `s.replace(".[", "[")` (pre-patch only) | `String.replace s ".[" "["` | identical: every non-overlapping left-to-right occurrence of the substring `".["` rewritten to `"["` |
| return value (`str`) | `result : String` | identity |

Python `str` is modeled at the value level as Lean `String` (the fix is a
whole-string join/rewrite, not a per-code-point transformation), per
SPEC_GUIDE §2.

## Callee provenance + flag dependencies

- **No consumed callee axiom; no opaque decl.** The modeled tail uses only
  `str.join` / `list.reverse` / (pre-patch) `str.replace`, all standard
  string/list operations with exact Lean counterparts (`String.intercalate`,
  `List.reverse`, `String.replace`). They are modeled CONCRETELY (tag I / R),
  not axiomatized. The `axioms` region is therefore empty and **G-AX skips**.
- The unchanged upstream `listchain`/`Instance`/`Module`/flag logic is NOT
  modeled as a callee: it only produces the input `parts`, which the bundle
  takes as given. No flag dependency reaches the modeled tail (the
  `stopatmodule`/`includemodule` flags only affect which names land in `parts`).

## G-CONF fuzz seed

Pinned LCG seed: **6202** (see `conformance_check.py` `SEED`). Corpus:
randomized `parts` lists (0–6 names, each a random short string drawn from an
alphabet that includes `.`, `[`, `]` so the discriminating `".["` boundary is
exercised), ≥1e5 fuzzed inputs, plus hand-picked edge cases: the F2P scenario
(`["testmethod_two[.[]", "TestY"]` → `"TestY.testmethod_two[.[]"`), the other
F2P paths (`["testone"]`, `["testmethod_one","TestX"]`), an empty list, a
singleton, names containing literal `"["`/`"."`, and a name beginning with `"["`
preceded by a join boundary. The R/I shadow of `implementation_getmodpath`
(`reverse` then `".".join`) is diffed against the POST-PATCH Python tail.
