# refinement.md — operation correspondence (pytest-dev__pytest-5262)

Maps every op in `implementation_mode` to its `patch.diff` counterpart.
Tags: **R** type refinement · **A-consumed** proof uses axiom property ·
**A-reference** deep model validated == real callee (G-AX) · **I** identical op.

The post-patch Python is `return self.buffer.mode.replace("b", "")`. The single
transformation is `str.replace("b", "")`, which removes every occurrence of the
one binary-indicator character `'b'`; we model it deeply as `stripBinary` folded
over the input string by the `for` loop.

| # | Lean impl op | patch.diff counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `bufferMode : List Char` | `self.buffer.mode` (a `str`) | R | str ↔ List Char bijection (mapping.md); reading the underlying stream's mode attribute is the input |
| 2 | `let mut acc := []` | initial empty output of `str.replace` building its result | I | concrete empty-output init |
| 3 | `for c in bufferMode do` | `str.replace` scans the string code-point-wise | I | per-character iteration |
| 4 | `if c ≠ 'b' then acc := acc ++ [c]` | `str.replace("b", "")` — drop every `'b'`, keep all other characters in order | A-reference | the introduced transformation modeled deeply; validated == `str.replace("b", "")` by G-AX. NOT axiomatized. |
| 5 | `return acc` | `return ...` returns the transformed string | I | identity return |

No A-consumed rows: the proof discharges `stripBinary` directly; no UNCHANGED
callee property is assumed. No changed-inexpressible op.

The discriminating clause is row 4: the `c = 'b'` sub-case drops the character.
The prepatch impl keeps every character (no transformation), so for any input
containing `'b'` its result differs from `stripBinary bufferMode`; its
`correct_mode` cannot close against the frozen `problem_spec_mode` (which pins
`stripBinary`). That is the G-DIFF signal, and it is exactly the F2P
observation (`'b' not in` the reported mode).
