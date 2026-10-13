# refinement.md — pytest-dev__pytest-6202

Operation-by-operation correspondence between `implementation_getmodpath`
(Solution.lean impl region) and `patch.diff` (the POST-PATCH tail of
`PyobjMixin.getmodpath`: `parts.reverse()` then `return ".".join(parts)`).
Tags: **R** type refinement, **A-consumed** proof uses an axiom, **A-reference**
deep model validated == real callee, **I** identical concrete op.

| # | Lean impl op | patch.diff / post-patch Python op | tag |
|---|---|---|---|
| 1 | `let mut parts := parts` (take the gathered name list) | the local `parts` list as assembled by the `for node in chain` loop (`python.py:275-286`) — the unchanged input to the modeled tail | I |
| 2 | `parts := parts.reverse` | `parts.reverse()` (`python.py:287`) | I |
| 3 | `return String.intercalate "." parts` | `return ".".join(parts)` (post-patch `python.py:288`) | R |
| — | (ABSENT in post-patch impl) | `return s.replace(".[", "[")` (`python.py:289`, REMOVED by the patch) | R (the discriminating clause) |

Notes:

- **Op 3 is R (string-value refinement).** Python `str` and `".".join` are
  modeled as Lean `String` and `String.intercalate "."`; the bijection (same
  separator, same empty/singleton behaviour) is in mapping.md. The fix is a
  whole-string join, not a per-code-point transformation, so a value-level
  `String` model is faithful (SPEC_GUIDE §2). No deep `List Char` model is
  needed because no character-level decision changed.
- **The fix itself** is op-"—": the patch DELETES the trailing
  `s.replace(".[", "[")`. The post-patch result is exactly the join, so
  `problem_spec_getmodpath` pins `result = String.intercalate "." parts.reverse`
  — no rewrite. The pre-patch impl (`Solution_prepatch.lean`) re-adds the
  `.replace ".[" "["` step after the join, reproducing the bug exactly: whenever
  a name produces a `".["` boundary (e.g. the parametrize id `"[.["`, joined
  after a class name), the corrupted result differs from the spec. Its
  `correct_getmodpath` is therefore unclosable — exactly the signal G-DIFF
  wants. (Concretely the F2P input `["testmethod_two[.[]", "TestY"]` yields
  spec `"TestY.testmethod_two[.[]"` but prepatch `"TestY.testmethod_two[[]"`.)
- **No axioms, no deep-model references.** All ops are I or R over standard
  string/list operations with exact Lean counterparts; nothing is axiomatized,
  so the `axioms` region is empty and **G-AX skips**. The result is fully pinned
  by `problem_spec` to a structural function of the input `parts` (reverse +
  join) — no output component is left free, no ungrounded oracle is consulted
  (SPEC_GUIDE §0.5, §0.8).
- **G-CONF** mechanically refutes the R/I legs over ≥1e5 fuzzed inputs (no
  A-consumed legs): the Python shadow of the impl (`list(reversed(parts))` then
  `".".join(...)`) is diffed against the POST-PATCH `getmodpath` tail.
