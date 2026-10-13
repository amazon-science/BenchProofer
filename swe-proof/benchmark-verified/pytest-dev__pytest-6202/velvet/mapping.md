# mapping.md — pytest-dev__pytest-6202

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 3a668ea6ff24b0c8f00498c3144c63bac561d925`, states the type
abstraction, and gives the provenance of any callee.

Repo file under change: `src/_pytest/python.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `joinPath (parts)` | `PyobjMixin.getmodpath(self, stopatmodule=True, includemodule=False)` — `src/_pytest/python.py:271` (body lines 287–289) | the modeled changed function (the dotted module path of a collected node) |
| `joinDot (parts)` *(pure spec)* | `".".join(parts)` — `src/_pytest/python.py:288` | the separator-join of the already-computed name parts; UNCHANGED by the patch |
| `replaceWindow (s)` *(pure spec, prepatch only)* | `s.replace(".[", "[")` — `src/_pytest/python.py:289` | the pre-patch post-join substitution that the fix REMOVES; modeled deeply to witness the bug |
| `sep` *(pure spec)* | the literal `"."` separator in `".".join(parts)` | the single separator code point placed between consecutive parts |

The pre-patch repo code (the lines the change removes / rewrites):
```python
        s = ".".join(parts)          # python.py:288  (the join, unchanged)
        return s.replace(".[", "[")  # python.py:289  (removed by the fix)
```
post-patch:
```python
        return ".".join(parts)       # python.py:288  (join only; no substitution)
```

The earlier portion of `getmodpath` (lines 273–287) walks the node `listchain`,
skips `Instance` nodes, splits the module name at its extension, and accumulates
the surviving `node.name` strings into `parts`, then `parts.reverse()`. That
portion is UNCHANGED by the patch and is upstream of the modeled delta: the
modeled function `joinPath` takes the resulting `parts` (the ordered list of name
strings) as its input and models only the join/substitution tail that the patch
edits.

## 2. Type abstraction (R-refinements)

| repo reality | Lean carrier | bijection |
|---|---|---|
| each name string (a `node.name`, e.g. `"TestY"`, `"testmethod_two[.[]"`) | `List Char` | `name[k]` ↔ `part[k]`; `len(name)` ↔ `part.length` (Lean `List Char` indexing is total and sound — no `List Int` workaround) |
| `parts: List[str]` (the accumulated, reversed name parts) | `parts: List (List Char)` | `parts[j]` ↔ the j-th name; `len(parts)` ↔ `parts.length` |
| `".".join(parts)` (a `str`) | `joinDot parts : List Char` | `str` concatenation ↔ `List` `++`; the `"."` separator ↔ the single char `sep = '.'`; `"".join([])` ↔ `[]`; `"".join([a]) == a` ↔ `joinDot [a] = a` |
| `str` return value | `List Char` | as above |
| `s.replace(".[", "[")` (a `str`) | `replaceWindow s : List Char` | left-to-right non-overlapping replacement of the 2-char pattern `['.','[']` by the single char `'['`; see §3.2 |

`str` is carried as `List Char` (per-code-point). The result is a `List Char`
and the postcondition is the exact equality `out = joinDot parts`.

## 3. Operation provenance (no consumed axioms)

There is **no consumed `axiom`** in this bundle: every operation the patch
touches is a primitive string operation (`str.join`, `str.replace`) modeled
DEEPLY over `List Char`. The deep models are exercised executably by
`axiom_check.py` (G-AX) against the real CPython `str.join` / `str.replace`.

### 3.1 `joinDot` ↔ `".".join(parts)`
CPython `str.join(iterable)` concatenates the elements with the separator
between consecutive elements: for `n` parts there are `n-1` separators, the empty
iterable yields `""`, and a single-element iterable yields that element
unchanged. `joinDot` encodes exactly this with separator `sep = '.'`. It is
front-recursive (one unfold per part) so the backward `while` loop in `joinPath`
discharges the value equality via one drop-step lemma. Docs:
https://docs.python.org/3/library/stdtypes.html#str.join.

### 3.2 `replaceWindow` ↔ `s.replace(".[", "[")`  (prepatch only)
CPython `str.replace(old, new)` replaces every NON-overlapping occurrence of
`old`, scanning left to right. Here `old == ".["` (two distinct chars `'.'`,`'['`)
and `new == "["` (`'['`). Because the two pattern characters are distinct,
non-overlapping left-to-right matching coincides with a simple greedy scan: at
each position, if the next two chars are `'.'` then `'['`, emit `'['` and advance
two positions; otherwise copy one char and advance one. `replaceWindow` encodes
exactly this. Docs:
https://docs.python.org/3/library/stdtypes.html#str.replace.

The substitution is the operation the fix DELETES, so it is the changed
operation and is NOT an axiom: it is modeled deeply only to witness the bug in
`Solution_prepatch.lean`. The gold result is `joinDot parts` with no substitution.

**Soundness check (G-AX):** `axiom_check.py` runs the real `str.join` and
`str.replace` on boundary inputs (empty parts, single part, parts containing
`.`, `[`, `.[`, `..[`, `.[.[`, the F2P witness `["TestY","testmethod_two[.[]"]`)
plus randomized fuzz over the alphabet `{., [, ], a, b, T, 0}` and asserts the
deep models agree with the real callees. Exit 0 iff sound. It imports nothing
repo-specific (only `random`/`sys`).

## 4. Conformance fuzz seed (G-CONF)
`conformance_check.py` is pinned to `SEED = 6202`, `N_FUZZ = 100_000`. The R/I
shadow of `joinPath` (the backward fold = `".".join`) is differentially tested
against the patched repo `getmodpath` join behaviour (`".".join(parts)`).
