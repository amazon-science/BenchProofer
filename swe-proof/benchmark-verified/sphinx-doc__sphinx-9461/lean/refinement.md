# refinement.md — sphinx-doc__sphinx-9461

Operation-by-operation correspondence between `implementation_propertyPrefix`
(Solution.lean impl region) and `patch.diff` (the POST-PATCH
`PyProperty.get_signature_prefix`). Tags: **R** type refinement, **A-consumed**
proof uses an axiom, **A-reference** deep model validated == real callee, **I**
identical concrete op.

Post-patch Python (sphinx/domains/python.py):

```python
def get_signature_prefix(self, sig: str) -> str:
    prefix = []
    if 'abstractmethod' in self.options:
        prefix.append('abstract')
    if 'classmethod' in self.options:
        prefix.append('class')

    prefix.append('property')
    return ' '.join(prefix) + ' '
```

| # | Lean impl op | patch.diff / post-patch Python op | tag |
|---|---|---|---|
| 1 | `let mut words : List String := []` | `prefix = []` | I |
| 2 | `if isAbstract then words := words ++ ["abstract"]` | `if 'abstractmethod' in self.options: prefix.append('abstract')` | R |
| 3 | `if isClassLevel then words := words ++ ["class"]` | `if 'classmethod' in self.options: prefix.append('class')` | R |
| 4 | `words := words ++ ["property"]` | `prefix.append('property')` | I |
| 5 | `return String.intercalate " " words ++ " "` | `return ' '.join(prefix) + ' '` | I |

Notes:

- **Every step is R or I — no A.** No unchanged callee contract is consumed: the
  changed behavior (which words appear and in what order) is modeled DEEPLY as a
  pure `List String` build + `String.intercalate`. SPEC_GUIDE §3 forbids
  axiomatizing a deeply-modeled changed op. The `axioms` region is empty;
  **G-AX skips**.
- **R vs I.** Steps 2 and 3 are tagged **R**: the Python `'flag' in self.options`
  membership predicate is refined to the boolean input `isAbstract` /
  `isClassLevel` per the mapping.md bijection (`list.append` ↔ `++ [x]`). Steps 1,
  4, 5 are **I**: empty-list seed, the unconditional base-word append, and the
  space-join-with-trailing-space are literal transliterations
  (`[]`, `++ ["property"]`, `String.intercalate " " · ++ " "`).
- **The fix itself** is step 3 (+ the reordering captured by steps 1/4): pre-patch
  the list was *seeded* with `['property']` and only `abstract` was ever prepended
  (`prefix.insert(0, 'abstract')`); the `classmethod` flag did not exist and no
  `class` word was emitted. Post-patch the list starts empty, `abstract` then
  `class` are appended in order, and `property` is appended last. The pre-patch
  impl (`Solution_prepatch.lean`) keeps the `['property']` seed and ignores the
  class-level toggle, so for any `isClassLevel = true` input it renders
  `"property "`/`"abstract property "` instead of `"class property "`/
  `"abstract class property "`. Its carried `cases … <;> rfl` proof fails to
  typecheck on the `isClassLevel = true` cases (G-DIFF) — the discriminating
  clause.
- **G-CONF** mechanically refutes the R/I legs: a faithful in-process replica of
  the post-patch `get_signature_prefix` (oracle) is diffed byte-for-byte against
  the impl shadow over all 4 exhaustive inputs + 2e5 fuzzed inputs (seed 9461).
  No A legs.
