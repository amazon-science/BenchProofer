# refinement.md — pytest-dev__pytest-7324

Maps every operation in `evalBareIdent`'s `do` block to its `patch.diff`
counterpart. Every row is **R** (type refinement), **A-reference** (deep model
validated == real callee by G-AX), or **I** (identical concrete op). No row is
a *changed op Velvet cannot express* (no kind-3).

The gold patch is one logical change with a shared knob `IDENT_PREFIX = "$"`,
realized at two sites:

- **site A** (`src/_pytest/mark/expression.py:169`, `not_expr`): the name fed to
  the compiler changes from `ident.value` to `IDENT_PREFIX + ident.value`.
- **site B** (`src/_pytest/mark/expression.py:181`, `MatcherAdapter.__getitem__`):
  the key passed to the matcher changes from `key` to `key[len(IDENT_PREFIX):]`.

`evalBareIdent` threads both: it prefixes (site A) before `compileName`, then
drops the prefix (site B) before consulting `matcher`.

| # | `do`-block op (Solution.lean) | patch.diff / repo counterpart | tag | bijection / justification |
|---|---|---|---|---|
| 1 | `let identPrefix : List Char := ['$']` | `IDENT_PREFIX = "$"` (added module constant, expression.py:132) | R | Python `str` `"$"` ↔ `List Char` `['$']`. The concrete sentinel is an internal choice; spec asserts only that prefixing avoids reserved spellings. |
| 2 | `let name := identPrefix ++ ident` | `ast.Name(IDENT_PREFIX + ident.value, …)` (site A, expression.py:169) | R | Python `str` `+` ↔ `List Char` `++`; `ident.value` ↔ `ident`. |
| 3 | `let compiled := compileName name` | `compile(ast.Expression(ast.Name(name, Load())), …, "eval")` (expression.py:201-203) — UNCHANGED callee, on the node from site A | A-reference | `compileName` is the deep model of the unchanged `compile`-of-`Name`; validated == real callee by axiom_check.py (G-AX). Outcome `Except CompileErr Unit` per mapping.md §2. |
| 4 | `let key := name.drop identPrefix.length` | `key[len(IDENT_PREFIX):]` (site B, expression.py:181) | R | Python slice-from-`len(prefix)` ↔ `List.drop prefix.length`; on a prefixed name this recovers the original `ident`. |
| 5 | `let out := compiled.map (fun _ => matcher key)` | `MatcherAdapter.__getitem__(key)` → `self.matcher(stripped_key)` during `eval` (expression.py:181, 216) | R | `eval` consults the matcher on the stripped key iff compilation succeeded; `matcher` is a free input. `Except.map` carries the compile failure through (none occurs for a prefixed name). |
| 6 | `return out` | `Expression.evaluate` returns the `eval` result `bool` | I | identity on the carrier `Except CompileErr Bool`. |

## Pre-patch correspondence (Solution_prepatch.lean)
The prepatch skeleton drops site A and site B: `name := ident` (no prefix) and
`key := name` (no strip). Then op 3 (`compileName name`) is
`compileName ident`, which is `Except.error .reservedConstant` exactly when
`ident ∈ {True, False, None}`. The shared `ensures out = Except.ok (matcher
ident)` is then unsatisfiable for those idents, so `prove_correct` cannot close
(G-DIFF: the unsolved goal is precisely `¬ident = True ∧ ¬ident = False ∧
¬ident = None`). This is the exact bug the issue and the three F2P
`test_valid_idents[True|False|None]` cases exercise.

## Audit
- No A-consumed axioms. The only callee leg (#3) is an **A-reference** (deep
  model, G-AX-validated), not a dead axiom.
- `matcher` is a free input; no behavioral claim, no axiom (mapping.md §3.2).
- Read-only inputs: `ident`, `matcher` are not `mut` (directive 5). The method
  has no mutable state and no loop.
- No kind-3 rows.
