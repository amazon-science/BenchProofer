# mapping.md — sphinx-doc__sphinx-9602

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 6c38f68dae221e8cfc70c137974b8b88bd3baaab`, states the type
abstraction, and gives the provenance of every axiom / deep-model reference.

Repo file under change: `sphinx/domains/python.py`.
The changed function is `_parse_annotation(annotation, env)` and its nested
helper `unparse(node)` (`sphinx/domains/python.py:110-186`). The gold patch
touches three sites inside that one function:

* **Hunk 1** — the `ast.Constant` branch of `unparse` (`python.py:122-126`):
  `nodes.Text(node.value)` → `nodes.Text(repr(node.value))`.
* **Hunk 2** — the `ast.Subscript` branch of `unparse` (`python.py:147-152`):
  after assembling the bracketed `result`, if the subscript head text is
  `Literal`/`typing.Literal`, each `nodes.Text` child of the bracket body is
  wrapped in a `nodes.literal` node.
* **Hunk 3** — the final node-resolution loop of `_parse_annotation`
  (`python.py:178-184`): a `nodes.literal` node is replaced by its child
  (`node[0]`, i.e. the inner text node, left as plain text), and only a
  non-blank `nodes.Text` node is converted to a cross-reference via
  `type_to_xref`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `render_literal_value(value, is_str)` | the `ast.Constant` branch of `unparse` (`python.py:122-126`) — `nodes.Text(repr(node.value))` | modeled changed behaviour **B1**: the rendered text content of a literal/constant value (repr, so a string value carries its surrounding quotes) |
| `resolve_subscript(kinds, is_literal_head)` | the `ast.Subscript` wrapping (`python.py:147-152`, hunk 2) **followed by** the final resolution loop (`python.py:178-184`, hunk 3), as they execute in order on a subscript's node list | modeled changed behaviour **B2**: a value node inside a `Literal[...]` subscript is rendered as plain text, NOT as a class cross-reference, while the subscript head and every node of a non-`Literal` subscript still resolve to a cross-reference |
| `wrap_seq(ks, is_lit)` *(pure)* | hunk 2's wrap loop (`for i, subnode in enumerate(result[1:], start=1): if isinstance(subnode, nodes.Text): result[i] = nodes.literal('', '', subnode)`) | pure spec: per-node wrap of a subscript body |
| `resolve_seq(ks)` *(pure)* | hunk 3's resolution loop (`if isinstance(node, nodes.literal): result[i] = node[0]; elif isinstance(node, nodes.Text) and node.strip(): result[i] = type_to_xref(...)`) | pure spec: per-node final resolution |
| `wrap1` / `resolve1` *(pure)* | the per-node body of hunk 2's / hunk 3's loop | pure spec: one node's transform |

`type_to_xref` (`python.py:83-107`) is an **unchanged** callee invoked by the
final loop; it constructs a `pending_xref` from a text string. It is NOT
axiomatized as a `@ContractOnly` here because the modeled behaviour is the
*node-kind decision* (does this node become a cross-reference or stay plain
text), which the gold patch changes — see refinement.md (A-reference, validated
by axiom_check.py, not consumed). Its only relevant property is "turns a text
node into a cross-reference node", captured by the kind transition NAME→XREF.

## 2. Type abstraction (R-refinements)

A docutils annotation is a flat `List[Node]`. Each node is abstracted to a
small integer **kind code** carrying exactly the facet the patch decides on:

| repo node | model kind | meaning |
|---|---|---|
| non-blank `nodes.Text` (e.g. `"Literal"`, `"int"`, `"True"`, `"'abc'"`) | `1` (NAME) | a text node whose `.strip()` is truthy — a candidate for `type_to_xref` |
| `addnodes.desc_sig_punctuation` (`[`, `]`, `, `, `...`) | `2` (PUNCT) | structural punctuation; never resolved |
| `addnodes.pending_xref` | `3` (XREF) | a resolved cross-reference (the `py:class`/`py:obj` target) |
| `nodes.literal('', '', text)` wrapper | `4` (LIT) | a text node wrapped so the final loop leaves it as plain text |

| repo reality | model carrier | bijection |
|---|---|---|
| `str` text content of a constant node | `List[int]` of Unicode code points; spec over `PSeq[int]` via `ToSeq` | `s[k]` ↔ `value[k] == ord(s[k])`; `repr` of a `str` adds a leading and trailing apostrophe `'` (U+0027 = code point 39) |
| `repr(node.value)` for a `bool`/`int` value | identity on its textual form | `repr(True) == 'True' == str(True)`, `repr(0) == '0' == str(0)`; the rendered *content* is unchanged for non-`str` values — the change for them is only the *type* passed to `nodes.Text` (a real `str`), captured by B1's `is_str = False` branch returning the value's textual form unchanged |
| `result[0] in ('Literal', 'typing.Literal')` (hunk 2 guard) | boolean parameter `is_literal_head` | the model abstracts the head-text comparison to "is the subscript a Literal subscript" |
| list `result` | `List[int]` of kind codes; spec over `PSeq[int]` | element-wise; `len` ↔ `len`; index ↔ index; the head is index `0` |

`str` indexing/iteration is banned in Nagini, so text content uses `List[int]`
and node lists use `List[int]` of kind codes; specifications are phrased over
`PSeq[int]` via `ToSeq`.

## 3. Callee provenance (checked by G-AX / axiom_check.py)

### 3.1 `render_literal_value` deep model ↔ `repr` (A-reference)
**Callee:** the CPython built-in `repr`. Hunk 1 replaces `nodes.Text(node.value)`
with `nodes.Text(repr(node.value))`. The discriminating observation the F2P
test makes is on a **string** literal value: `repr('abc') == "'abc'"` (the
apostrophes are added), whereas the pre-patch `node.value` is the bare `abc`.
For a `bool`/`int` value `repr(v) == str(v)` so the rendered content is the
value's plain textual form. The deep model `render_literal_value` encodes
exactly this: `is_str ⇒ Result == [39] + value + [39]` (quoted);
`¬is_str ⇒ Result == value` (textual form unchanged).

**Domain restriction (the precise A-reference equality).** `repr(s) == "'" + s
+ "'"` holds **only** when every character of `s` is printable ASCII
(`0x20..0x7e`) AND is neither an apostrophe `'` (U+0027 = 39) nor a reverse
solidus `\` (U+005C = 92). Outside that domain `repr` either escapes the
character (e.g. `repr('a\\b') == "'a\\\\b'"`) or switches to double quotes (e.g.
`repr("a'b") == '"a\'b"'`), so the model's `[39] + value + [39]` would be
**wrong**. The model therefore encodes that domain as a `Requires` on the string
case:
`Requires(Implies(is_str, Forall(j: 0<=j<len(value) ⇒ 32<=value[j]<=126 and
value[j]!=39 and value[j]!=92)))`. This restriction is **sound** (a strict
subset of `repr`'s simple-quote domain — printable high code points like `é`,
`λ` are also simple-quote but the spec conservatively excludes them) and
**faithful to the repo reality**: the constant string values these parametrised
type annotations carry are short source tokens — `Literal['abc']`,
`Literal['read', 'write']`, enum-like identifiers — drawn from the printable
ASCII identifier/word domain, never containing an embedded apostrophe, backslash,
or control character. axiom_check.py runs the real `repr` on string values
**drawn from exactly the `Requires` domain** (printable ASCII 0x20..0x7e minus
39 and 92), asserts the precondition it fuzzes under (so the fuzz domain is
provably the spec-admitted domain — no silent narrowing), includes a **negative
control** confirming `model != repr` just outside the domain (so the `Requires`
is load-bearing), and additionally checks bool / int / float values (which carry
no restriction). Docs: https://docs.python.org/3/library/functions.html#repr .

### 3.2 `resolve_subscript` deep model ↔ the node-resolution pipeline (A-reference)
**Callee:** the unchanged `type_to_xref` (`python.py:83-107`) plus the docutils
`isinstance`/`nodes.literal` machinery. The changed node-kind decision is
modeled **deeply** by the two pure folds `wrap_seq` (hunk 2) and `resolve_seq`
(hunk 3) and the two verified loops in `resolve_subscript`; there is **no
consumed `@ContractOnly` axiom**. The encoded property:

* head (index 0) NAME → XREF always (the subscript head — `Literal`, `List`,
  `Tuple` — is a cross-reference, as the F2P test confirms `Literal` is a
  `pending_xref`);
* a NAME at index ≥ 1 inside a **Literal** subscript is wrapped to LIT (hunk 2)
  then unwrapped by hunk 3 to a plain NAME — it stays plain text, never a XREF;
* a NAME at index ≥ 1 inside a **non-Literal** subscript becomes a XREF (hunk 3
  resolves it via `type_to_xref`);
* PUNCT / XREF nodes pass through unchanged in both loops.

axiom_check.py re-implements `wrap1`/`resolve1` exactly as in model.py and
checks them against the gold patch's two loop bodies on every kind code and
both head positions and both `is_literal_head` values (exhaustive), plus a
randomized fuzz over node lists; it also asserts the end-to-end node-kind
sequence equals what the gold `_parse_annotation` pipeline produces on the
F2P inputs `Literal[True, False]` and `typing.Literal[0, 1, 'abc']`. The model
is validated **== the real pipeline**, not consumed as an axiom (A-reference).

There are **no A-consumed axioms** in this bundle: every changed operation is
modeled deeply; the only callees (`repr`, `type_to_xref`) are unchanged and are
validated as A-references by G-AX.
