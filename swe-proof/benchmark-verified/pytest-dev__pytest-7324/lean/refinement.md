# refinement.md — operation correspondence (pytest-dev__pytest-7324)

Maps every op in `implementation_resolveIdent` to its `patch.diff` counterpart.
Tags: **R** type refinement · **A-consumed** proof uses axiom property ·
**A-reference** deep model validated == real callee (G-AX) · **I** identical op.

Post-patch Python (the two changed lines + the unchanged compile/eval path):
- `not_expr`: `return ast.Name(IDENT_PREFIX + ident.value, ast.Load())`
- `MatcherAdapter.__getitem__`: `return self.matcher(key[len(IDENT_PREFIX):])`
- unchanged: `compile(ast.Expression(name_node), mode="eval")` then `eval`,
  which aborts iff the name-node identifier is `True`/`False`/`None`.

We model the end-to-end single-identifier resolution: build the name-node
identifier, (deeply-modeled) compile guard, then strip the prefix and consult
the matcher.

| # | Lean impl op | patch.diff counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `name : List Char` | `ident.value` (a `str`) | R | str ↔ List Char bijection (mapping.md) — the input identifier |
| 2 | `matcher : List Char → Bool` | `self.matcher` (`Callable[[str], bool]`) | R | free verdict function; Callable ↔ `List Char → Bool` |
| 3 | `identPrefix := ['$']` | `IDENT_PREFIX = "$"` | I | the literal prefix constant |
| 4 | `let key := identPrefix ++ name` | `IDENT_PREFIX + ident.value` | A-reference | prefix-attach modeled deeply; `++` on `List Char` == `str` concatenation |
| 5 | `if isReservedConst key then return none` | `compile()` aborts iff the name-node identifier is `True`/`False`/`None` | A-reference | the UNCHANGED compile guard modeled deeply as the exact finite set; validated == real `compile()` outcome by G-AX. NOT axiomatized. |
| 6 | `key.drop identPrefix.length` | `key[len(IDENT_PREFIX):]` | A-reference | prefix-strip modeled deeply; `List.drop n` == Python slice `[n:]` |
| 7 | `return some (matcher …)` | `return self.matcher(…)` wrapped in successful eval | A-reference | the matcher verdict is returned; `Option`-`some` marks successful resolution |

No A-consumed rows: the proof discharges `identPrefix`, `isReservedConst`, and
the `drop` directly; no UNCHANGED-callee property is *assumed*. No
changed-inexpressible op.

## Discriminating clause (G-DIFF)
The fix's force is the prefix: post-patch, `key = '$' ++ name` is **never** a
reserved constant (it starts with `$`), so op 5's guard never fires and every
identifier resolves to `some (matcher name)` (op 6 strips the `$` so the matcher
sees the original `name`). The pre-patch skeleton uses `key := name` verbatim
(no prefix, no strip): for `name ∈ {True, False, None}` the guard fires and it
returns `none`, contradicting `problem_spec_resolveIdent` which demands
`some (matcher name)`. Hence `correct_resolveIdent` cannot close on the prepatch
— exactly the F2P observation (`test_valid_idents[True/False/None]` must resolve,
not crash). For every non-reserved identifier both legs already agree, so the
prepatch differs *only* on the three reserved spellings — a tight, faithful
discriminator.
