# mapping.md — pytest-dev__pytest-6202

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 3a668ea6ff24b0c8f00498c3144c63bac561d925`, states the type
abstraction, and gives the provenance of any callee.

Repo file under change: `src/_pytest/python.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `modpath_of(parts)` | `PyobjMixin.getmodpath(self, stopatmodule=True, includemodule=False)` — `src/_pytest/python.py:271` (body lines 287-289) | the modeled changed function (the dotted module path of a collected node) |
| `join_dot(parts)` *(pure spec)* | `".".join(parts)` — `src/_pytest/python.py:288` | the dot-join of the already-computed name parts; UNCHANGED by the patch |
| `replace_db(s)` *(pure spec, prepatch only)* | `s.replace(".[", "[")` — `src/_pytest/python.py:289` | the pre-patch post-join substitution that the fix REMOVES; modeled deeply to witness the bug |

The pre-patch repo code (the lines the change removes / rewrites):
```python
        s = ".".join(parts)        # python.py:288  (unchanged join)
        return s.replace(".[", "[")  # python.py:289 (removed by the fix)
```
post-patch:
```python
        return ".".join(parts)     # python.py:288  (join only; no substitution)
```

The earlier portion of `getmodpath` (lines 273-287) walks the node `listchain`,
skips `Instance` nodes, splits the module name at its extension, and accumulates
the surviving `node.name` strings into `parts`. That portion is UNCHANGED by the
patch and is upstream of the modeled delta: the modeled function `modpath_of`
takes the resulting `parts` (the list of name strings) as its input and models
only the join/substitution tail that the patch edits.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| each name string (a `node.name`, e.g. `"TestY"`, `"testmethod_two[.[]"`) | `PSeq[int]` of Unicode code points | `name[k]` ↔ `part[k] == ord(name[k])`; `len(name)` ↔ `len(part)` |
| `parts: List[str]` (the accumulated name parts) | `parts: PSeq[PSeq[int]]` (a sequence of code-point sequences) | `parts[j]` ↔ the j-th name; `len(parts)` ↔ number of parts |
| `".".join(parts)` (a `str`) | `join_dot(parts): PSeq[int]` | `str` concatenation ↔ `PSeq` `+`; the `"."` separator ↔ the single code point `46`; `"".join([])` ↔ empty sequence; `join([a]) == a` |
| `str` return value | `List[int]` of code points; specification carried by `PSeq[int]` via `ToSeq` | as above |
| `s.replace(".[", "[")` (a `str`) | `replace_db(s): PSeq[int]` | left-to-right non-overlapping replacement of the 2-code-point pattern `[46, 91]` (`".["`) by the single code point `91` (`"["`); see §3 |

`str` indexing/iteration is banned in Nagini, so names are carried as `PSeq[int]`
of code points and `parts` as `PSeq[PSeq[int]]`. The result is materialized as a
`List[int]` and the postcondition is phrased over `PSeq[int]` via `ToSeq`.

## 3. Operation provenance (no consumed axioms)

There is **no `@ContractOnly` axiom** in this bundle: every operation the patch
touches is a primitive sequence operation (`str.join`, `str.replace`) that is
modeled DEEPLY over `PSeq[int]`. The deep models are exercised executably by
`axiom_check.py` (G-AX) against the real CPython `str.join` / `str.replace`.

### 3.1 `join_dot` ↔ `".".join(parts)`
CPython `str.join(iterable)` concatenates the elements with the separator
between consecutive elements: for `n` parts there are `n-1` separators, the empty
iterable yields `""`, and a single-element iterable yields that element
unchanged. `join_dot` encodes exactly this with separator code point `46`
(`"."`). Docs: https://docs.python.org/3/library/stdtypes.html#str.join.

### 3.2 `replace_db` ↔ `s.replace(".[", "[")`  (prepatch only)
CPython `str.replace(old, new)` replaces every NON-overlapping occurrence of
`old`, scanning left to right. Here `old == ".["` (two distinct code points
`[46, 91]`) and `new == "["` (`[91]`). Because the two characters of the pattern
are distinct, non-overlapping left-to-right matching coincides with a simple
greedy scan: at each position, if the next two code points are `.` `[`, emit `[`
and advance two positions; otherwise copy one code point and advance one.
`replace_db` encodes exactly this. Docs:
https://docs.python.org/3/library/stdtypes.html#str.replace.

The substitution is the operation the fix DELETES, so it is the changed
operation and is NOT an axiom: it is modeled deeply only to witness the bug in
`model_prepatch.py`. The gold result is `join_dot(parts)` with no substitution.

**Soundness check (G-AX):** `axiom_check.py` runs the real `str.join` and
`str.replace` on boundary inputs (empty parts, single part, parts containing
`.`, `[`, `.[`, `..[`, `.[.[`, the F2P witness `["TestY","testmethod_two[.[]"]`)
plus randomized fuzz over the alphabet `{., [, ], a, b, T, 0}` and asserts the
deep models agree with the real callees. Exit 0 iff sound. It imports nothing
repo-specific (only `random`/`sys`).
