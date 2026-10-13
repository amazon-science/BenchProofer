# mapping.md — sphinx-doc__sphinx-7462

Binds every `model.py` symbol to its repository counterpart at
`base_commit = b3e26a6c851133b82b50f4b68b53692076574d13`, states the type
abstraction, and gives the provenance of each deep-model reference (the real
callee it is validated against by axiom_check.py / G-AX).

Repo files under change (two independent sites, the same `ast.Tuple` branch in
two different `unparse` helpers):

- `sphinx/domains/python.py` — the nested `unparse(node)` inside
  `_parse_annotation`, which renders a parsed annotation into a list of docutils
  display nodes (the TOKEN surface).
- `sphinx/pycode/ast.py` — the module-level `unparse(node)`, which renders a
  parsed AST node into a source-text string (the TEXT surface).

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `tuple_tokens(elts)` | `ast.Tuple` branch of `unparse` in `sphinx/domains/python.py:116-122` (inside `_parse_annotation`, `python.py:91`) | the modeled changed function, site A (token surface) |
| `tuple_text(elts)` | `ast.Tuple` branch of `unparse` in `sphinx/pycode/ast.py:116-117` | the modeled changed function, site B (text surface) |
| `join_tokens(parts)` *(deep model — A-reference)* | the upstream non-empty token loop `for elem in node.elts: result.extend(unparse(elem)); result.append(desc_sig_punctuation('', ', ')); … result.pop()` (`python.py:117-121`) | pure spec: the members interleaved with a single ', ' separator token, trailing separator dropped; validated == the real loop by axiom_check.py (G-AX), NOT a consumed axiom |
| `join_comma(parts)` *(deep model — A-reference)* | the call `", ".join(unparse(e) for e in node.elts)` (`ast.py:117`) | pure spec: the comma-and-space join of the members; validated == the real `', '.join` by axiom_check.py (G-AX), NOT a consumed axiom |
| `sep_token()` / `open_paren()` / `close_paren()` | the punctuation literals `', '`, `'('`, `')'` in both branches | pure spec: separator and bracket symbols as code-point sequences |

The element renderings `unparse(elem)` / `unparse(e)` are **unchanged upstream
computations**: the patch does not alter how a single member is rendered, only
how the surrounding group is assembled. They are therefore taken as
already-rendered inputs (the members of `elts`), not modeled or axiomatized.

The pre-patch repo behaviour the change repairs (for the refinement audit):
both branches assembled the group with **no special case for an empty
`node.elts`** — site A then executed `result.pop()` on an empty `result`
(raising `IndexError: pop from empty list`, the crash in the bug report), and
site B returned `", ".join(())` == `""`. The gold adds an `if node.elts:`
guard, emitting `[desc_sig_punctuation('', '('), desc_sig_punctuation('', ')')]`
(site A) / `"()"` (site B) for the empty group.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| a member's rendered TEXT (`str`, e.g. `unparse(e)`) | `PSeq[int]` of Unicode code points | `s[k]` ↔ code point; `str` concatenation ↔ `+`; the empty `str` ↔ the empty `PSeq` |
| the list of rendered members (`unparse(e) for e in node.elts`) | `PSeq[PSeq[int]]` | `node.elts[i]` rendered ↔ `elts[i]`; `len(node.elts)` ↔ `len(elts)`; the empty tuple `()` ↔ `len(elts) == 0` |
| a docutils display TOKEN (e.g. `desc_sig_punctuation('', ', ')`, a member's `nodes.Text`) | `PSeq[int]` = the token's display text as code points | a token is identified by its rendered text; the F2P `assert_node` compares the punctuation tokens `'('`, `')'`, `', '` and the member sub-nodes positionally, i.e. by their text content and order, which the carrier preserves exactly |
| the list of display tokens (the `List[Node]` returned by site A) | `PSeq[PSeq[int]]` = the sequence of token texts | order- and content-preserving; `result.pop()` removing the last `', '` token ↔ `join_tokens` not emitting a trailing separator |

`str` indexing/iteration is banned in Nagini, so members/tokens are carried as
`PSeq[int]` and member lists as `PSeq[PSeq[int]]`; the specification is phrased
over these pure Viper sequences.

Site A's real output is a `List[docutils.nodes.Node]`; only the punctuation
tokens (`'('`, `')'`, `', '`) and the relative order of member sub-nodes are
observed by the F2P `assert_node`, so modeling the output as the **sequence of
token texts** is exact for the tested observation. The `make_xref` wrapping of
member text into `pending_xref` nodes (`python.py:82-89,129-132`) is an
unchanged downstream step applied after `unparse` returns; it does not touch the
`'('`/`')'`/`', '` punctuation tokens the empty-tuple fix introduces.

## 3. Deep-model references (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `join_tokens` deep model ↔ the real token loop (A-reference)
**Callee:** the upstream non-empty token-assembly loop in `python.py`'s
`unparse` Tuple branch:

```python
result = []
for elem in node.elts:
    result.extend(unparse(elem))
    result.append(addnodes.desc_sig_punctuation('', ', '))
result.pop()
```

For a non-empty group this is exactly: the members in order with one ', '
separator token between consecutive members and no trailing separator — which
is what `join_tokens` encodes (front-recursive, separator `sep_token()` ==
`PSeq(44, 32)`). G-AX asserts `join_tokens(parts) == real_loop(parts)` for
every non-empty `parts` over boundary + fuzz inputs, and that the real loop
RAISES `IndexError` on the empty group (the bug). The CHANGED behaviour — the
empty group rendering `[desc_sig_punctuation('', '('), desc_sig_punctuation('',
')')]` == `PSeq(open_paren(), close_paren())` — is concrete in both model and
patch and is the discriminating clause of `tuple_tokens`.

### 3.2 `join_comma` deep model ↔ `', '.join` (A-reference)
**Callee:** CPython `str.join` via `", ".join(unparse(e) for e in node.elts)`
(`ast.py:117`). For a non-empty group this concatenates the rendered members
with a single `', '` between consecutive members — exactly `join_comma`
(front-recursive, separator `sep_token()` == `PSeq(44, 32)`). Docs:
https://docs.python.org/3/library/stdtypes.html#str.join. G-AX asserts
`join_comma(parts) == ', '.join(parts)` over boundary + fuzz inputs and that
`', '.join(())` == `""` (the bug). The CHANGED behaviour — the empty group
rendering `"()"` == `PSeq(40, 41)` — is concrete in both model and patch and is
the discriminating clause of `tuple_text`.

**Soundness check (G-AX):** `axiom_check.py` runs the real `', '.join` and a
faithful transcription of the real token loop on the F2P witnesses
(`Tuple[int, int]`, `(1, 2, 3)`, `Tuple[()]`, `()`) plus 30 000 randomized
non-empty member lists over a punctuation-rich alphabet, asserting both deep
models equal their real callees on the unchanged non-empty case, that the real
loop crashes / the real join returns `""` on the empty group, and that the gold
empty-group rendering differs from the pre-patch one at BOTH sites. It imports
only the standard library (`random`, `sys`). Exit 0 iff sound.
