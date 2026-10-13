# mapping.md — symbol binding & type bijection (pytest-dev__pytest-7324)

## Modeled function
- **Lean** `implementation_resolveIdent : List Char → (List Char → Bool) → Option Bool`
- **Python** the resolution of one match-expression identifier — the
  `not_expr`-ident branch that turns an identifier into a name node
  (`src/_pytest/mark/expression.py:164 @ 19ad58893`,
  `return ast.Name(ident.value, ast.Load())`) together with the name-node
  lookup that the compiled expression performs at evaluation time
  (`MatcherAdapter.__getitem__`, `src/_pytest/mark/expression.py:174-175 @
  19ad58893`, `return self.matcher(key)`).

A match expression is parsed into a name node per identifier, the node is
`compile()`d to a code object, and `eval` resolves each name through the
matcher mapping. The single-identifier end-to-end behavior is: given an
identifier, produce the matcher's boolean verdict on it. The observable
behavior the F2P tests (`test_valid_idents[True/False/None]`) demand is that
*every* identifier — including ones spelled like the reserved boolean/none
constants — resolves to a genuine boolean verdict without aborting the
interpreter. The post-patch code achieves this by attaching a one-character
prefix to the name-node identifier (so it can never equal a reserved constant
and crash `compile()`), then removing that prefix again on lookup so the matcher
still sees the original identifier.

## Type bijection (used by G-CONF + G-AX)
| Python | Lean | notes |
|---|---|---|
| `str` (the identifier `ident.value` / `key`) | `List Char` | per-code-point; total/sound indexing |
| `Callable[[str], bool]` (the `matcher`) | `List Char → Bool` | pure boolean verdict on an identifier |
| outcome of resolving one identifier | `Option Bool` | `some b` = matcher verdict `b`; `none` = `compile()` aborts (the reserved-constant crash) |
| `IDENT_PREFIX = "$"` | `identPrefix = ['$']` | the prefix attached to the name-node identifier |
| `key[len(IDENT_PREFIX):]` | `key.drop identPrefix.length` | strip the prefix before consulting the matcher |
| reserved name-node constants `{"True","False","None"}` | `isReservedConst` finite set | a name node spelled as one of these makes `compile()` abort on a debug build |

The `Option Bool` carrier captures the crash-vs-verdict distinction at the type
level: pre-patch, a reserved-constant identifier yields `none` (abort); the
contract demands `some (matcher name)` for every identifier.

## Callee provenance
- The prefix-attach (`IDENT_PREFIX + ident.value`) and prefix-strip
  (`key[len(IDENT_PREFIX):]`) are the two operations the patch introduces; both
  are modeled deeply (`identPrefix ++ name`, `key.drop identPrefix.length`) — an
  **A-reference**, NOT axiomatized.
- The `compile()` guard that rejects a reserved-constant name node is an
  UNCHANGED behavior of the Python compiler; it is modeled deeply as the exact
  finite set `isReservedConst` (an **A-reference**, validated by G-AX against the
  real `compile(ast.Expression(ast.Name(id)), mode="eval")` outcome). It is NOT
  axiomatized — the set `{True, False, None}` is fully known and finite.
- `matcher` is the caller-supplied verdict function; it is a free parameter, not
  a callee, so no axiom is consumed. The axioms region is empty.

## Flag dependency
None on the modeled path. (The crash is debug-build-specific in CPython, but the
*name-node-rejection* set `{True, False, None}` is build-independent; G-AX
fuzzes identifiers and confirms exactly those three identifiers are the ones
`compile()` rejects as a bare `eval`-mode name.)

## G-CONF fuzz seed
Pinned seed: **7324**. ≥10^5 fuzzed identifiers over an identifier-flavoured
alphabet (`A-Za-z0-9_:+-.[]` plus the literal spellings `True`/`False`/`None`
oversampled) paired with random matcher truth-tables, comparing the R/I shadow
of `implementation_resolveIdent` against the post-patch Python behavior.
