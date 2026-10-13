# mapping.md — sphinx-doc__sphinx-10466

## Symbol binding (file:line @ base_commit `cab2d93076d0cca7c53fac885f927dde3e2a5fec`)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_dedupSort` | body of `Catalog.__iter__`, the `positions = …` computation | `sphinx/builders/gettext.py:58-62` |
| input `triples : List (String × Int × String)` | `self.metadata[message] : List[Tuple[str, int, str]]` | `sphinx/builders/gettext.py:46`, populated at `:56` |
| `result : List (String × Int)` | `positions : List[Tuple[str, int]]` (the value handed to `Message`) | `sphinx/builders/gettext.py:60` (post-patch `:60-61`) |

## The changed expression

Pre-patch (`base_commit`, line 60):
```python
positions = [(source, line) for source, line, uuid in self.metadata[message]]
```
Post-patch (gold):
```python
positions = sorted(set((source, line) for source, line, uuid
                       in self.metadata[message]))
```
The fix maps the triple list to `(source, line)` pairs, removes duplicates
(`set`), and orders the survivors ascending (`sorted`). `uuids` (line 61) is
unchanged and is NOT modeled (it is a separate, unaffected output component
read straight from the same triple list).

## Type bijection (used by G-CONF + G-AX)

| Python | Lean | encoding |
|---|---|---|
| `str` (source path) | `String` | value-identity |
| `int` (line number) | `Int` | value-identity (line `0` occurs in the bug report; negatives never arise but `Int` is a sound superset) |
| `str` (uuid hex) | `String` | value-identity; never inspected by the modeled computation |
| `Tuple[str,int,str]` | `String × Int × String` | componentwise |
| `Tuple[str,int]` | `String × Int` | componentwise |
| `list[...]` | `List ...` | order-preserving |
| `sorted(...)` on `(str,int)` tuples | `List.mergeSort lexLe` | Python tuple comparison is lexicographic: compare `source` (str `<`), tie-break on `line` (int `≤`); `lexLe` mirrors this |
| `set(...)` then `sorted` | `List.dedup` then `List.mergeSort lexLe` | both yield the distinct elements; final order is fixed by the sort, so the intermediate dedup order is irrelevant |

`lexLt` (the strict spec relation) is the irreflexive core of `lexLe`: it makes
`List.Sorted lexLt result` express *strictly ascending*, which simultaneously
pins both the ordering (`sorted`) and the absence of duplicates (`set`).

## Callee provenance / flag deps

None. The modeled computation calls only Python builtins (`set`, `sorted`, the
tuple constructor and lexicographic tuple comparison), all modeled deeply in
Lean (`List.dedup`, `List.mergeSort`, `lexLe`). No unchanged repo callee is
consumed, so there is **no `opaque`/`axiom` declaration** and `axiom_check.py`
is a skip stub. There are no configuration flags.

## G-CONF fuzz seed

Pinned seed: `1046620250630` (used by `conformance_check.py`).
