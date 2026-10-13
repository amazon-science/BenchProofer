# mapping.md — sphinx-doc__sphinx-7454

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = aca3f825f2e4a8817190f3c885a242a285aa0dba`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records
callee provenance. The change is a pure dispatch, so there are **no axioms** and
**no A-reference deep models** (the node constructor is collapsed into the result
record); G-AX is therefore SKIP for this bundle.

Repo file under change: `sphinx/domains/python.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `referenceForName (name : List Char)` | the inner cross-reference builder of `_parse_annotation` — `sphinx/domains/python.py:73-75` (`def make_xref(text)`) | the modeled changed function: builds one `pending_xref` for one annotation name token |
| `RefKind.classRef` | the string literal `'class'` passed as `reftype=` | resolution kind for an ordinary type name |
| `RefKind.valueRef` | the string literal `'obj'` passed as `reftype=` (post-patch) | resolution kind for the `None` singleton name |
| `TypeReference` (record) | the `addnodes.pending_xref('', nodes.Text(text), refdomain='py', reftype=…, reftarget=text)` node | the reference node, reduced to its four observable fields |
| `TypeReference.kind` | the node's `reftype` attribute | which resolver runs |
| `TypeReference.domain` | the node's `refdomain` attribute (always `'py'`) | unchanged frame |
| `TypeReference.target` | the node's `reftarget` attribute (`= text`) | unchanged frame |
| `TypeReference.label` | the node's child `nodes.Text(text)` value (the shown link text) | unchanged frame |
| `desiredKind (name)` | the post-patch `if text == 'None': reftype = 'obj' else: reftype = 'class'` selection | pure spec: the resolution kind for one name |

The builder is a **nested** function inside `_parse_annotation(annotation: str)`.
For each text leaf the outer parser produces (the AST `Name`/`Attribute` text
nodes), `make_xref(text)` is applied (`python.py:115-117`). The modeled scope is
exactly one such per-token call: input is the token `text`, output is its node.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `text: str` (the token name argument of `make_xref`) | `List Char` | `s` (Python str) ↔ `s.toList`-shaped `List Char`; per-code-point on the BMP this is total and exact; `"None"` ↔ `"None".toList = ['N','o','n','e']` |
| `reftype` string `'class'` / `'obj'` | `RefKind.classRef` / `RefKind.valueRef` | finite 2-element bijection: `'class' ↔ classRef`, `'obj' ↔ valueRef` |
| `refdomain` string `'py'` | `domain : List Char = "py".toList` | `'py'` ↔ `['p','y']` |
| `reftarget` string (`= text`) | `target : List Char = name` | same `str ↔ List Char` bijection; identity on the token |
| the `pending_xref` node's shown text `nodes.Text(text)` | `label : List Char = name` | same `str ↔ List Char` bijection; identity on the token |

The four fields of `TypeReference` are exactly the four arguments the post-patch
`pending_xref('', nodes.Text(text), refdomain='py', reftype=reftype,
reftarget=text)` carries that the F2P test observes (`assert_node(doctree[0],
pending_xref, refdomain=…, reftype=…, reftarget=…)` and the `[pending_xref,
"<text>"]` shape check on the child text). No other node attribute is observed.

## 3. Callee provenance (kind-A)

**None.** The changed operation — choosing the `reftype` string from the token —
is modeled **deeply** by `desiredKind`/the dispatch in the `do` block; there is no
external callee whose behavior the proof relies on. `pending_xref` / `nodes.Text`
are constructors (their effect is captured structurally by the `TypeReference`
record fields), not callees with a contract owed. Hence: no `axiom`, no
A-reference, `G-AX = skip` (no `axiom_check.py`).

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`7454`** so the
consumer-side verdict is reproducible. The R/I shadow it builds transliterates
`desiredKind`/the dispatch to Python; the ORACLE drives the **patched** real
`_parse_annotation` at base_commit and reads back the resulting node's
`reftype`/`refdomain`/`reftarget`/text for a single-name annotation. The input
space includes `None`, ordinary type names (`int`, `str`, `List`, dotted names,
user identifiers), and fuzzed identifier strings.
