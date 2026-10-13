# refinement.md — sphinx-doc__sphinx-10466

Maps every operation of `implementation_dedupSort` to its `patch.diff`
counterpart. Tags: **R** (type refinement), **A-consumed** (proof uses an
axiom), **A-reference** (deep model validated == real callee by G-AX), **I**
(identical concrete op). Every row is R, A, or I.

The modeled computation is the post-patch RHS of
`sphinx/builders/gettext.py:60`:
```python
positions = sorted(set((source, line) for source, line, uuid in self.metadata[message]))
```

| # | Lean op (`implementation_dedupSort`) | patch.diff op | tag | note |
|---|---|---|---|---|
| 1 | `triples : List (String × Int × String)` (input) | `self.metadata[message] : List[Tuple[str,int,str]]` | R | order-preserving list refinement; `str↔String`, `int↔Int` (see mapping.md) |
| 2 | `let mut pairs := []`; `for t in triples do pairs := pairs ++ [(t.1, t.2.1)]` | `(source, line) for source, line, uuid in self.metadata[message]` — the generator projecting each triple to its `(source, line)` | R | the comprehension's projection step; preserves order and multiplicity exactly like the `++ [..]` accumulator |
| 3 | `.dedup` | `set(...)` | R | both reduce to the distinct elements; `set` discards order, `List.dedup` keeps first-seen order — irrelevant because op 4 re-sorts. The *combined* `sorted(set(...))` and `dedup.mergeSort` produce byte-identical lists (G-CONF) |
| 4 | `.mergeSort lexLe` | `sorted(...)` | R | `sorted` on `(str,int)` tuples uses lexicographic tuple comparison; `lexLe` encodes exactly that (`source` `<`, tie-break `line` `≤`). `mergeSort` is a stable total sort — since op 3 already made elements distinct, the comparator's tie behavior is immaterial |
| 5 | `return pairs.dedup.mergeSort lexLe` | `positions = sorted(set(...))` | I | the produced value bound to `positions`/handed to `Message` |

Unchanged sibling output (NOT modeled): `uuids = [uuid for source, line, uuid
in self.metadata[message]]` (`gettext.py:61`) is untouched by the patch and is a
separate output component, so it is outside the modeled function. The spec's
frame discipline (directive 5) is satisfied because the modeled function's sole
output *is* `positions`; there is no other component of `implementation_dedupSort`
to pin.

No A-consumed and no A-reference rows: every op is an R/I refinement of a Python
builtin, modeled deeply. Hence `axiom_check.py` is a skip stub and
`conformance_check.py` differential-tests the all-R/I impl (`conf_skip=false`).
